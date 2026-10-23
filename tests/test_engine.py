import copy
import unittest
from engine.decision_engine import StoryError, advance, initial, replay, available, present
from engine.story_validator import validate
from stories.scenarios import SCENARIOS


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.story = SCENARIOS['signal']

    def test_all_routes_and_endings(self):
        total = 0
        for story in SCENARIOS.values():
            with self.subTest(story=story['id']):
                paths = validate(story)
                total += len(paths)
                self.assertEqual({p['scene'] for p in paths}, {key for key,node in story['scenes'].items() if node['ending']})
                for path in paths:
                    self.assertEqual(replay(story,path['history']),path)
        self.assertEqual(total,2135)

    def test_no_input_mutation(self):
        original = initial(self.story)
        backup = copy.deepcopy(original)
        updated = advance(self.story,original,'listen')
        self.assertEqual(original,backup)
        self.assertEqual(updated['state']['time'],5)
        self.assertEqual(updated['scene'],'archive')

    def test_conditions_and_evidence(self):
        s = advance(self.story,initial(self.story),'listen')
        skipped = advance(self.story,s,'leave')
        with self.assertRaises(StoryError):
            advance(self.story,skipped,'hatch')
        discovered = advance(self.story,s,'map')
        self.assertEqual(discovered['evidence'],['Buried coordinates'])
        chamber = advance(self.story,discovered,'hatch')
        self.assertEqual(advance(self.story,chamber,'relay')['scene'],'truth')
        chamber['state']['trust']=1
        self.assertFalse(available(self.story['scenes']['chamber']['choices'][0],chamber))

    def test_invalid_scene_choice_and_ending(self):
        for scene, choice in [('arrival','fake'),('absent','listen'),('truth','relay')]:
            s=initial(self.story);s['scene']=scene
            with self.subTest(scene=scene),self.assertRaises(StoryError):advance(self.story,s,choice)

    def test_presentation_does_not_change_story(self):
        original=copy.deepcopy(self.story)
        node=present(self.story,initial(self.story))
        self.assertTrue(node['choices'][0]['available'])
        self.assertEqual(original,self.story)

    def test_replay_rejects_wrong_scene(self):
        with self.assertRaises(StoryError):replay(self.story,[{'scene':'archive','choice':'listen'}])

    def test_validator_rejects_bad_target(self):
        story=copy.deepcopy(self.story);story['scenes']['arrival']['choices'][0]['target']='absent'
        with self.assertRaises(AssertionError):validate(story)

    def test_validator_rejects_invalid_conditions(self):
        for condition in ({'unknown':1},{'trust':9},{'evidence':'missing'}):
            story=copy.deepcopy(self.story);story['scenes']['arrival']['choices'][0]['requires']=condition
            with self.subTest(condition=condition),self.assertRaises(AssertionError):validate(story)

    def test_validator_rejects_cycles(self):
        story=copy.deepcopy(self.story);story['scenes']['archive']['choices'][0]['target']='arrival'
        with self.assertRaises(AssertionError):validate(story)

    def test_validator_rejects_unreachable_node_and_choice(self):
        story=copy.deepcopy(self.story);story['scenes']['unused']=copy.deepcopy(story['scenes']['truth'])
        with self.assertRaises(AssertionError):validate(story)
        story=copy.deepcopy(self.story);story['scenes']['arrival']['choices'][0]['requires']={'trust':3}
        with self.assertRaises(AssertionError):validate(story)
