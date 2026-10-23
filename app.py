"""WhatIf — The Alternate Reality Engine. Author: Swayam Shakya."""
import json
import os
from pathlib import Path
import secrets
import sqlite3
from functools import lru_cache
from uuid import uuid4
from flask import Flask, jsonify, request, session, send_file, g
from werkzeug.exceptions import HTTPException
from engine.decision_engine import initial, advance, replay, present, StoryError
from engine.story_validator import validate
from stories.scenarios import SCENARIOS

ROOT = Path(__file__).resolve().parent

SCHEMA = '''
CREATE TABLE IF NOT EXISTS scenarios (id TEXT PRIMARY KEY, definition TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS journeys (
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, scenario TEXT NOT NULL REFERENCES scenarios(id),
 snapshot TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 0, hints INTEGER NOT NULL DEFAULT 0,
 parent TEXT REFERENCES journeys(id), fork_index INTEGER,
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 updated TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS journeys_owner ON journeys(owner, updated);
CREATE TABLE IF NOT EXISTS decisions (
 journey TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
 step INTEGER NOT NULL, event TEXT NOT NULL, PRIMARY KEY(journey,step)
);
CREATE TABLE IF NOT EXISTS checkpoints (
 id TEXT PRIMARY KEY, journey TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
 step INTEGER NOT NULL, created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 UNIQUE(journey,step)
);
CREATE TABLE IF NOT EXISTS discoveries (
 owner TEXT NOT NULL, scenario TEXT NOT NULL REFERENCES scenarios(id), ending TEXT NOT NULL,
 PRIMARY KEY(owner,scenario,ending)
);
CREATE TABLE IF NOT EXISTS achievements (
 owner TEXT NOT NULL, code TEXT NOT NULL, earned TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 PRIMARY KEY(owner,code)
);
'''

ACHIEVEMENTS = {
 'first': ('First steps', 'Complete a story.'),
 'many': ('Another ending', 'Discover two distinct endings in a scenario.'),
 'evidence': ('Look closer', 'Find hidden evidence.'),
 'alternate': ('What if?', 'Make a different decision in an alternate journey.'),
 'unassisted': ('Your own compass', 'Finish a journey without a hint.'),
 'all': ('Every possibility', 'Discover every ending in one scenario.')
}


@lru_cache(maxsize=1)
def catalogue_stats():
    """Validate once per process; restart after editing the authored catalogue."""
    result = {}
    for story in SCENARIOS.values():
        paths = validate(story)
        result[story['id']] = {'routes': len(paths), 'scenes': len(story['scenes']),
                               'endings': len({p['scene'] for p in paths})}
    return result


def create_app(database=None, testing=False):
    app = Flask(__name__)
    path = Path(database) if database else ROOT / 'database' / 'whatif.sqlite3'
    path.parent.mkdir(parents=True, exist_ok=True)
    secret_path = path.parent / '.session-key'
    if testing:
        secret = 'isolated-test-session-key'
    else:
        # Exclusive creation keeps a second process from replacing an existing key.
        try:
            fd = os.open(secret_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as f:
                f.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        secret = secret_path.read_text().strip()
        if not secret:
            raise RuntimeError('Session key is empty. Stop the server and remove database/.session-key.')
    app.config.update(SECRET_KEY=secret, TESTING=testing, DATABASE=str(path),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
        MAX_CONTENT_LENGTH=16384, PERMANENT_SESSION_LIFETIME=60*60*24*365)
    stats = catalogue_stats()
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript(SCHEMA)
        for story in SCENARIOS.values():
            db.execute('INSERT INTO scenarios VALUES (?,?) ON CONFLICT(id) DO UPDATE SET definition=excluded.definition WHERE definition != excluded.definition',
                       (story['id'], json.dumps(story)))

    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'], timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys=ON')
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        connection = g.pop('db', None)
        if connection:
            connection.close()

    @app.before_request
    def secure_request():
        if request.host.split(':')[0] not in ('127.0.0.1', 'localhost'):
            return jsonify(error='Use the localhost address printed by the launcher.'), 400
        if 'owner' not in session:
            session['owner'] = uuid4().hex
            session['csrf'] = secrets.token_hex(24)
            session.permanent = True
        if request.method in ('POST', 'DELETE', 'PATCH'):
            token = request.headers.get('X-CSRF-Token', '')
            if not secrets.compare_digest(token, session['csrf']):
                return jsonify(error='Session verification failed. Refresh the page and try again.'), 403

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(StoryError)
    def story_error(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(sqlite3.Error)
    def database_error(error):
        app.logger.error('Database operation failed: %s', type(error).__name__)
        return jsonify(error='Progress could not be saved. Close other running copies and retry.'), 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    def payload():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise StoryError('Send a JSON object with the required fields.')
        return data

    def get_journey(jid):
        row = db().execute('SELECT * FROM journeys WHERE id=? AND owner=?', (jid, session['owner'])).fetchone()
        if not row:
            from flask import abort
            abort(404, description='Journey not found in this browser profile.')
        return row

    def story_for(row):
        # Scenario code is authoritative; structural edits require a progress reset.
        return SCENARIOS[row['scenario']]

    def serialize(row, full=False, compact=False, saved_checkpoints=None):
        snap = json.loads(row['snapshot'])
        story = story_for(row)
        result = {k: row[k] for k in ('id','scenario','version','hints','parent','fork_index','created','updated')}
        result.update(title=story['title'], snapshot=snap, completed=story['scenes'][snap['scene']]['ending'],
                      decision_count=len(snap['history']), audio=story['audio'], structure=story['structure'])
        result['checkpoints'] = saved_checkpoints if saved_checkpoints is not None else [dict(r) for r in db().execute('SELECT * FROM checkpoints WHERE journey=? ORDER BY step', (row['id'],))]
        if compact:
            result['snapshot'] = {k: v for k, v in snap.items() if k != 'history'}
        if full:
            result['node'] = present(story, snap)
            visited = {h['scene'] for h in snap['history']} | {snap['scene']}
            # Expose topology, never undiscovered ending text.
            result['graph'] = [{'id': k, 'title': n['title'] if k in visited else ('Undiscovered ending' if n['ending'] else n['title']),
                 'ending': n['ending'], 'visited': k in visited,
                 'edges': [c['target'] for c in n['choices']]} for k,n in story['scenes'].items()]
        return result

    def record(row, snap, alternate=False):
        owner, story = row['owner'], story_for(row)
        codes = set()
        if snap['evidence']:
            codes.add('evidence')
        if alternate:
            codes.add('alternate')
        if story['scenes'][snap['scene']]['ending']:
            db().execute('INSERT OR IGNORE INTO discoveries VALUES (?,?,?)', (owner, story['id'], snap['scene']))
            codes.add('first')
            if not row['hints']:
                codes.add('unassisted')
        counts = list(db().execute('SELECT scenario, count(*) AS n FROM discoveries WHERE owner=? GROUP BY scenario', (owner,)))
        if any(r['n'] >= 2 for r in counts):
            codes.add('many')
        if any(r['n'] == sum(n['ending'] for n in SCENARIOS[r['scenario']]['scenes'].values()) for r in counts):
            codes.add('all')
        for code in codes:
            db().execute('INSERT OR IGNORE INTO achievements(owner,code) VALUES (?,?)', (owner,code))

    def insert_journey(story, snap, parent=None, index=None, hints=0):
        jid = uuid4().hex
        db().execute('INSERT INTO journeys(id,owner,scenario,snapshot,version,parent,fork_index,hints) VALUES (?,?,?,?,?,?,?,?)',
            (jid,session['owner'],story['id'],json.dumps(snap),len(snap['history']),parent,index,hints))
        for step, event in enumerate(snap['history']):
            db().execute('INSERT INTO decisions VALUES (?,?,?)', (jid,step,json.dumps(event)))
        return jid

    @app.get('/')
    @app.get('/index.html')
    def index():
        return send_file(ROOT / 'index.html')

    @app.get('/api/bootstrap')
    def bootstrap():
        found = [dict(r) for r in db().execute('SELECT scenario, ending FROM discoveries WHERE owner=?', (session['owner'],))]
        catalogue = []
        for story in SCENARIOS.values():
            meta = {k: story[k] for k in ('id','title','description','category','difficulty','minutes','symbol','audio','structure','content_note','tags')}
            meta.update(stats[story['id']])
            meta['discovered'] = [SCENARIOS[d['scenario']]['scenes'][d['ending']]['title'] for d in found if d['scenario'] == story['id']]
            catalogue.append(meta)
        earned = {r['code']: r['earned'] for r in db().execute('SELECT * FROM achievements WHERE owner=?', (session['owner'],))}
        checkpoints = {}
        for checkpoint in db().execute('SELECT c.* FROM checkpoints c JOIN journeys j ON c.journey=j.id WHERE j.owner=? ORDER BY c.step', (session['owner'],)):
            checkpoints.setdefault(checkpoint['journey'], []).append(dict(checkpoint))
        return jsonify(csrf=session['csrf'], scenarios=catalogue,
            totals={'scenarios': len(catalogue), 'endings': sum(x['endings'] for x in stats.values()),
                    'routes': sum(x['routes'] for x in stats.values()), 'scenes': sum(x['scenes'] for x in stats.values())},
            journeys=[serialize(r, compact=True, saved_checkpoints=checkpoints.get(r['id'], [])) for r in db().execute('SELECT * FROM journeys WHERE owner=? ORDER BY updated DESC,id', (session['owner'],))],
            achievements=[dict(code=k,title=v[0],description=v[1],earned=earned.get(k)) for k,v in ACHIEVEMENTS.items()])

    @app.post('/api/journeys')
    def start():
        sid = payload().get('scenario')
        if not isinstance(sid, str) or sid not in SCENARIOS:
            raise StoryError('Unknown scenario.')
        with db():
            jid = insert_journey(SCENARIOS[sid], initial(SCENARIOS[sid]))
        return jsonify(serialize(get_journey(jid), True)), 201

    @app.get('/api/journeys/<jid>')
    def journey(jid):
        return jsonify(serialize(get_journey(jid), True))

    @app.post('/api/journeys/<jid>/choose')
    def choose(jid):
        data = payload()
        if type(data.get('version')) is not int or not isinstance(data.get('choice'), str) or not isinstance(data.get('scene'), str):
            raise StoryError('A scene, choice and integer version are required.')
        with db():
            db().execute('BEGIN IMMEDIATE')
            row = get_journey(jid)
            snap = json.loads(row['snapshot'])
            if row['version'] != data['version'] or snap['scene'] != data['scene']:
                return jsonify(error='This journey has moved on. Reload it to see the latest decision.'), 409
            updated = advance(story_for(row), snap, data['choice'])
            db().execute('INSERT INTO decisions VALUES (?,?,?)', (jid,len(snap['history']),json.dumps(updated['history'][-1])))
            db().execute("UPDATE journeys SET snapshot=?,version=version+1,updated=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?", (json.dumps(updated),jid))
            alternate = False
            if row['parent']:
                original = json.loads(get_journey(row['parent'])['snapshot'])['history']
                alternate = any(a['choice'] != b['choice'] or a['scene'] != b['scene']
                                for a, b in zip(original, updated['history']))
            record(row, updated, alternate)
        return jsonify(serialize(get_journey(jid), True))

    @app.post('/api/journeys/<jid>/fork')
    def fork(jid):
        data = payload()
        with db():
            db().execute('BEGIN IMMEDIATE')
            row = get_journey(jid)
            history = json.loads(row['snapshot'])['history']
            step = data.get('step')
            if type(step) is not int or not 0 <= step <= len(history):
                raise StoryError('Choose a valid decision point.')
            snap = replay(story_for(row), history[:step])
            new_id = insert_journey(story_for(row), snap, jid, step, row['hints'])
        return jsonify(serialize(get_journey(new_id), True)), 201

    @app.post('/api/journeys/<jid>/checkpoint')
    def checkpoint(jid):
        with db():
            row = get_journey(jid)
            step = len(json.loads(row['snapshot'])['history'])
            db().execute('INSERT OR IGNORE INTO checkpoints(id,journey,step) VALUES (?,?,?)', (uuid4().hex,jid,step))
        return jsonify(serialize(get_journey(jid), True))

    @app.post('/api/journeys/<jid>/hint')
    def hint(jid):
        with db():
            row = get_journey(jid)
            db().execute('UPDATE journeys SET hints=hints+1 WHERE id=?', (jid,))
        snap = json.loads(row['snapshot'])
        return jsonify(hint=story_for(row)['scenes'][snap['scene']]['hint'])

    @app.post('/api/reset')
    def reset():
        if payload().get('confirm') != 'RESET':
            raise StoryError('Type RESET to confirm deletion of this browser profile’s progress.')
        with db():
            db().execute('UPDATE journeys SET parent=NULL WHERE owner=?', (session['owner'],))
            for table in ('journeys','discoveries','achievements'):
                db().execute(f'DELETE FROM {table} WHERE owner=?', (session['owner'],))
        return jsonify(ok=True)

    return app


if __name__ == '__main__':
    import argparse
    from launcher import start_server
    parser = argparse.ArgumentParser(description='Run WhatIf locally.')
    parser.add_argument('--port', type=int, default=5050)
    parser.add_argument('--open-browser', action='store_true')
    args = parser.parse_args()
    try:
        server = start_server(args.port)
        if args.open_browser:
            import webbrowser
            webbrowser.open(f'http://127.0.0.1:{server.port}/index.html')
        server.thread.join()
    except KeyboardInterrupt:
        from launcher import stop_server
        stop_server()
    except (OSError, RuntimeError, ValueError) as error:
        print(f'Cannot start WhatIf: {error}')
        raise SystemExit(1)
