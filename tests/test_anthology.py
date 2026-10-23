import hashlib
import json
from pathlib import Path
import unittest
import wave
from engine.decision_engine import initial, advance, present
from engine.story_validator import validate
from stories.scenarios import SCENARIOS
from tools.verify_catalogue import build_report

ROOT = Path(__file__).resolve().parents[1]


class AnthologyTests(unittest.TestCase):
    def test_catalogue_size_and_unique_content(self):
        self.assertEqual(len(SCENARIOS),105)
        self.assertEqual(len({s['title'] for s in SCENARIOS.values()}),105)
        self.assertEqual(len({s['scenes'][s['initial']]['text'] for s in SCENARIOS.values()}),105)
        endings=[n['text'] for s in SCENARIOS.values() for n in s['scenes'].values() if n['ending']]
        self.assertEqual(len(endings),315)
        self.assertEqual(len(set(endings)),315)
        self.assertGreaterEqual(len({s['category'] for s in SCENARIOS.values()}),10)

    def test_manifest_matches_current_definitions(self):
        current=build_report()
        saved=json.loads((ROOT/'docs/ROUTE_MANIFEST.json').read_text(encoding='utf-8'))
        self.assertEqual(saved,current)
        self.assertEqual(current['totals'],{'scenarios':105,'scenes':955,'endings':315,'routes':2135})

    def test_countdown_requires_time_as_well_as_evidence(self):
        story=next(s for s in SCENARIOS.values() if s['structure']=='countdown')
        def follow(choices):
            state=initial(story)
            for c in choices:state=advance(story,state,c)
            return state
        ready=follow(['investigate','verify','review'])
        self.assertEqual(ready['state']['time'],2)
        self.assertEqual(advance(story,ready,'resolve')['scene'],'resolved')
        late=follow(['respond','prepare','verify','review'])
        self.assertEqual(late['state']['time'],1)
        self.assertFalse(next(c for c in present(story,late)['choices'] if c['id']=='resolve')['available'])
        self.assertEqual(advance(story,late,'contain')['scene'],'contained')
        efficient=follow(['respond','prepare','copy','review'])
        self.assertEqual(advance(story,efficient,'resolve')['scene'],'resolved')

    def test_negotiation_needs_cooperation(self):
        story=next(s for s in SCENARIOS.values() if s['structure']=='negotiation')
        state=initial(story)
        for c in ['investigate','share','alone']:state=advance(story,state,c)
        self.assertTrue(state['evidence'])
        self.assertFalse(present(story,state)['choices'][0]['available'])
        self.assertEqual(advance(story,state,'contain')['scene'],'contained')

    def test_every_audio_assignment_exists(self):
        manifest=json.loads((ROOT/'static/audio/scores.json').read_text())
        self.assertEqual(len(manifest),11)
        for story in SCENARIOS.values():self.assertIn(story['audio'],manifest)
        self.assertEqual(len({s['audio'] for s in SCENARIOS.values()}),10)

    def test_audio_files_are_complete_distinct_and_unclipped(self):
        fingerprints=set()
        manifest=json.loads((ROOT/'static/audio/scores.json').read_text())
        for key,meta in manifest.items():
            with self.subTest(score=key):
                path=ROOT/'static/audio'/meta['file']
                with wave.open(str(path)) as wav:
                    self.assertEqual(wav.getnchannels(),2)
                    self.assertEqual(wav.getsampwidth(),2)
                    self.assertEqual(wav.getframerate(),22050)
                    self.assertEqual(wav.getnframes(),meta['seconds']*22050)
                    raw=wav.readframes(wav.getnframes())
                    self.assertEqual(len(raw),meta['seconds']*22050*4)
                    from array import array
                    samples=array('h',raw)
                    peak=max(abs(x) for x in samples)/32767
                    self.assertLess(peak,.66)
                    self.assertGreater(peak,.05)
                    self.assertAlmostEqual(peak,meta['peak'],places=4)
                    self.assertLess(abs(samples[0]),5)
                    self.assertLess(abs(samples[-1]),5)
                fingerprints.add(hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(len(fingerprints),11)
