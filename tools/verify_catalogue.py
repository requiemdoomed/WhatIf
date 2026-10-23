"""Write a reproducible route manifest for every story. Author: Swayam Shakya."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stories.scenarios import SCENARIOS
from engine.story_validator import validate


def build_report():
    report = {'scenarios': [], 'totals': {'scenarios': 0, 'scenes': 0, 'endings': 0, 'routes': 0}}
    for story in SCENARIOS.values():
        paths = validate(story)
        witnesses = {}
        for path in paths:
            witnesses.setdefault(path['scene'], [event['choice'] for event in path['history']])
        encoded = json.dumps(story, sort_keys=True, ensure_ascii=False).encode('utf-8')
        report['scenarios'].append({'id': story['id'], 'title': story['title'], 'genre': story['category'],
            'structure': story['structure'], 'audio': story['audio'], 'sha256': hashlib.sha256(encoded).hexdigest(),
            'scenes': len(story['scenes']), 'endings': len(witnesses), 'routes': len(paths),
            'ending_witnesses': witnesses})
        for key, count in [('scenarios',1),('scenes',len(story['scenes'])),('endings',len(witnesses)),('routes',len(paths))]:
            report['totals'][key] += count
    return report


if __name__ == '__main__':
    report = build_report()
    target = ROOT / 'docs' / 'ROUTE_MANIFEST.json'
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    lines = ['# Scenario catalogue', '', 'Author: Swayam Shakya', '',
             'All listed endings and routes were reached by exhaustive traversal. These are short, authored episodes using three shared anthology structures plus the original stories.', '',
             '| Scenario | Genre | Structure | Scenes | Endings | Routes |',
             '|---|---|---|---:|---:|---:|']
    for entry in report['scenarios']:
        lines.append(f"| {entry['title']} | {entry['genre']} | {entry['structure']} | {entry['scenes']} | {entry['endings']} | {entry['routes']} |")
    (ROOT / 'docs' / 'CATALOGUE.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(report['totals']))
