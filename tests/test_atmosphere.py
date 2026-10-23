"""Coverage and integrity checks for the illustrated sound worlds."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from stories.scenarios import SCENARIOS

ROOT = Path(__file__).resolve().parents[1]

class AtmosphereTests(unittest.TestCase):
    def test_every_scenario_has_matching_art(self):
        for story in SCENARIOS.values():
            path = ROOT / 'static/art' / (story['audio'] + '.svg')
            with self.subTest(story=story['id']):
                root = ET.parse(path).getroot()
                self.assertEqual(root.attrib['viewBox'], '0 0 1200 440')
                self.assertGreater(len(list(root.iter())), 8)

    def test_art_contains_no_scripts_or_remote_dependencies(self):
        for path in (ROOT / 'static/art').glob('*.svg'):
            for node in ET.parse(path).getroot().iter():
                self.assertNotIn(node.tag.split('}')[-1], ('script','foreignObject','image'))
                self.assertFalse(any(k.startswith('on') for k in node.attrib))

    def test_each_profile_has_a_distinct_composition(self):
        art = list((ROOT / 'static/art').glob('*.svg'))
        self.assertEqual(len(art), 11)
        self.assertEqual(len({p.read_bytes() for p in art}), 11)

if __name__ == '__main__': unittest.main()
