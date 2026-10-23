import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from app import create_app
from stories.scenarios import SCENARIOS
from engine.story_validator import validate


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'progress.sqlite3'
        self.app=create_app(self.path,testing=True)
        self.client=self.app.test_client()
        self.csrf=self.client.get('/api/bootstrap').json['csrf']

    def tearDown(self):self.temp.cleanup()

    def post(self,path,data=None,client=None,csrf=None):
        return (client or self.client).post('/api/'+path,json={} if data is None else data,headers={'X-CSRF-Token':csrf or self.csrf})

    def start(self,sid='signal'):
        response=self.post('journeys',{'scenario':sid});self.assertEqual(response.status_code,201);return response.json

    def choose(self,j,c):
        return self.post('journeys/'+j['id']+'/choose',{'choice':c,'scene':j['snapshot']['scene'],'version':j['version']})

    def route(self, choices):
        j=self.start()
        for c in choices:
            response=self.choose(j,c);self.assertEqual(response.status_code,200);j=response.json
        return j

    def codes(self):return {a['code'] for a in self.client.get('/api/bootstrap').json['achievements'] if a['earned']}

    def test_bootstrap_html_and_headers(self):
        self.assertEqual(len(self.client.get('/api/bootstrap').json['scenarios']),105)
        response=self.client.get('/')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'Swayam Shakya',response.data)
        self.assertIn("default-src 'self'",response.headers['Content-Security-Policy'])
        for url in ['/static/css/style.css','/static/js/app.js','/static/js/theme.js']:
            r=self.client.get(url);self.assertEqual(r.status_code,200);r.close()

    def test_initialization_repeatable(self):
        j=self.start();create_app(self.path,testing=True)
        self.assertEqual(self.client.get('/api/journeys/'+j['id']).json['version'],0)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM scenarios').fetchone()[0],105)

    def test_choices_and_duplicate_protection(self):
        j=self.start();r=self.choose(j,'listen');self.assertEqual(r.status_code,200)
        self.assertEqual(self.choose(j,'listen').status_code,409)
        latest=self.client.get('/api/journeys/'+j['id']).json
        self.assertEqual(latest['version'],1);self.assertEqual(len(latest['snapshot']['history']),1)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM decisions').fetchone()[0],1)

    def test_invalid_choices_do_not_modify_progress(self):
        j=self.start();before=self.client.get('/api/journeys/'+j['id']).json
        self.assertEqual(self.choose(j,'fake').status_code,400)
        self.assertEqual(self.client.get('/api/journeys/'+j['id']).json,before)
        self.assertEqual(self.post('journeys/'+j['id']+'/choose',{'choice':'listen','scene':'fake','version':0}).status_code,409)

    def test_locked_choice_cannot_be_forced(self):
        j=self.route(['power','bridge'])
        self.assertEqual(self.choose(j,'hatch').status_code,400)
        self.assertEqual(self.client.get('/api/journeys/'+j['id']).json['version'],2)

    def test_fork_preserves_original_and_replays_state(self):
        original=self.route(['listen','map','hatch','relay'])
        fork=self.post('journeys/'+original['id']+'/fork',{'step':1}).json
        self.assertEqual(fork['snapshot']['scene'],'archive')
        self.assertEqual(fork['snapshot']['evidence'],[])
        self.assertEqual(fork['snapshot']['state']['trust'],1)
        changed=self.choose(fork,'leave');self.assertEqual(changed.status_code,200)
        self.assertIn('alternate',self.codes())
        self.assertEqual(self.client.get('/api/journeys/'+original['id']).json,original)

    def test_identical_fork_does_not_earn_alternate(self):
        j=self.route(['listen','map'])
        fork=self.post('journeys/'+j['id']+'/fork',{'step':1}).json
        self.choose(fork,'map');self.assertNotIn('alternate',self.codes())

    def test_later_divergence_earns_alternate(self):
        j=self.route(['listen','map'])
        fork=self.post('journeys/'+j['id']+'/fork',{'step':0}).json
        fork=self.choose(fork,'listen').json
        self.assertNotIn('alternate',self.codes())
        self.choose(fork,'leave')
        self.assertIn('alternate',self.codes())

    def test_checkpoint_is_idempotent_and_restore_is_new_branch(self):
        j=self.route(['listen','map'])
        self.post('journeys/'+j['id']+'/checkpoint')
        result=self.post('journeys/'+j['id']+'/checkpoint').json
        self.assertEqual(len(result['checkpoints']),1)
        f=self.post('journeys/'+j['id']+'/fork',{'step':result['checkpoints'][0]['step']}).json
        self.assertNotEqual(f['id'],j['id']);self.assertEqual(f['snapshot'],j['snapshot'])

    def test_achievements_use_real_endings(self):
        self.assertEqual(self.codes(),set())
        self.route(['listen','map','hatch','relay'])
        self.assertEqual(self.codes(),{'first','evidence','unassisted'})
        self.route(['power','bridge','evacuate'])
        self.assertIn('many',self.codes());self.assertNotIn('all',self.codes())
        self.route(['power','bridge','mast','flare'])
        self.assertIn('all',self.codes())

    def test_hint_and_inheritance(self):
        j=self.start();self.post('journeys/'+j['id']+'/hint')
        for c in ['listen','leave','evacuate']:j=self.choose(j,c).json
        self.assertNotIn('unassisted',self.codes())
        f=self.post('journeys/'+j['id']+'/fork',{'step':2}).json
        self.assertEqual(f['hints'],1)
        self.choose(f,'evacuate');self.assertNotIn('unassisted',self.codes())

    def test_malformed_payloads(self):
        j=self.start()
        for body in [None,[],{}, {'scenario':[]},{'scenario':'unknown'}]:
            r=self.client.post('/api/journeys',data=json.dumps(body),content_type='application/json',headers={'X-CSRF-Token':self.csrf})
            self.assertEqual(r.status_code,400)
        for body in [{},{'step':-1},{'step':True},{'step':99},{'step':[]}]:
            self.assertEqual(self.post('journeys/'+j['id']+'/fork',body).status_code,400)
        self.assertEqual(self.post('journeys/'+j['id']+'/choose',{'version':True,'scene':'arrival','choice':'listen'}).status_code,400)
        self.assertEqual(self.client.get('/api/journeys/no-such-journey').status_code,404)

    def test_csrf_and_owner_isolation(self):
        j=self.start();other=self.app.test_client();token=other.get('/api/bootstrap').json['csrf']
        self.assertEqual(self.client.post('/api/journeys',json={'scenario':'signal'}).status_code,403)
        self.assertEqual(other.get('/api/journeys/'+j['id']).status_code,404)
        self.assertEqual(self.post('journeys/'+j['id']+'/fork',{'step':0},other,token).status_code,404)
        self.assertEqual(self.client.get('/',headers={'Host':'attacker.example'}).status_code,400)

    def test_reset_only_current_owner(self):
        j=self.start();self.post('journeys/'+j['id']+'/checkpoint');self.post('journeys/'+j['id']+'/fork',{'step':0})
        other=self.app.test_client();token=other.get('/api/bootstrap').json['csrf']
        other_j=self.post('journeys',{'scenario':'city'},other,token).json
        self.assertEqual(self.post('reset',{'confirm':'no'}).status_code,400)
        self.assertEqual(self.post('reset',{'confirm':'RESET'}).status_code,200)
        self.assertEqual(self.client.get('/api/bootstrap').json['journeys'],[])
        self.assertEqual(other.get('/api/journeys/'+other_j['id']).status_code,200)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM checkpoints').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM decisions').fetchone()[0],0)

    def test_progress_survives_restart(self):
        j=self.route(['listen','map'])
        cookie=self.client.get_cookie('session').value
        new=create_app(self.path,testing=True).test_client();new.set_cookie('session',cookie)
        self.assertEqual(new.get('/api/journeys/'+j['id']).json['snapshot'],j['snapshot'])

    def test_real_secret_persists(self):
        first=create_app(self.path);second=create_app(self.path)
        self.assertEqual(first.secret_key,second.secret_key)
        self.assertTrue((self.path.parent/'.session-key').exists())

    def test_parallel_submissions_commit_once(self):
        j=self.start();cookie=self.client.get_cookie('session').value
        def send(_):
            c=self.app.test_client();c.set_cookie('session',cookie)
            return self.post('journeys/'+j['id']+'/choose',{'scene':'arrival','choice':'listen','version':0},c).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(send,range(2)))
        self.assertEqual(sorted(statuses),[200,409])

    def test_every_story_path_through_http(self):
        count=0
        for story in SCENARIOS.values():
            for path in validate(story):
                j=self.start(story['id'])
                for event in path['history']:
                    response=self.choose(j,event['choice']);self.assertEqual(response.status_code,200);j=response.json
                self.assertEqual(j['snapshot'],path);self.assertTrue(j['completed'])
                self.assertEqual(self.choose(j,'anything').status_code,400)
                count+=1
        self.assertEqual(count,2135)

    def test_compact_bootstrap_and_catalogue_metadata(self):
        j=self.route(['listen','map'])
        payload=self.client.get('/api/bootstrap').json
        self.assertEqual(payload['totals'],{'scenarios':105,'scenes':955,'endings':315,'routes':2135})
        self.assertNotIn('history',payload['journeys'][0]['snapshot'])
        self.assertEqual(payload['journeys'][0]['decision_count'],2)
        self.assertEqual(len(self.client.get('/api/journeys/'+j['id']).json['snapshot']['history']),2)
        self.assertEqual(len({s['id'] for s in payload['scenarios']}),105)
        self.assertTrue(all(s['routes']>0 and s['audio'] and s['endings']==3 for s in payload['scenarios']))

    def test_audio_static_assets(self):
        for name in ['main','orbital','neon','quantum','noir']:
            response=self.client.get('/static/audio/'+name+'.wav')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.data[:4],b'RIFF')
            response.close()

    def test_database_error_is_sanitized(self):
        with sqlite3.connect(self.path) as db:db.execute('DROP TABLE achievements')
        response=self.client.get('/api/bootstrap')
        self.assertEqual(response.status_code,503)
        self.assertNotIn(str(self.path),response.get_data(as_text=True))
