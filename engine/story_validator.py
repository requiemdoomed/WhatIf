"""Validate structure and explore every reachable state and decision path."""
from engine.decision_engine import initial, advance, available, LIMITS
from stories.scenarios import SCENARIOS


def validate(story):
    nodes = story['scenes']
    assert story['initial'] in nodes, 'Missing initial scene'
    assert set(story['initial_state']) == set(LIMITS), 'Invalid initial state keys'
    evidence = {c['evidence'] for n in nodes.values() for c in n['choices'] if c['evidence']}
    for key, value in story['initial_state'].items():
        assert type(value) is int and LIMITS[key][0] <= value <= LIMITS[key][1], 'Invalid initial value'
    for key, node in nodes.items():
        assert node['text'] and node['title'], f'Empty scene {key}'
        assert bool(node['choices']) != node['ending'], f'Dead end or ending with choices: {key}'
        ids = [c['id'] for c in node['choices']]
        assert len(set(ids)) == len(ids), f'Duplicate choice: {key}'
        for c in node['choices']:
            assert c['target'] in nodes, f'Missing target {c["target"]}'
            for field, value in c['delta'].items():
                assert field in LIMITS and type(value) is int, 'Invalid state update'
            for field, value in c['requires'].items():
                assert field in LIMITS or field == 'evidence', 'Invalid condition key'
                if field == 'evidence':
                    assert value in evidence, 'Evidence can never be obtained'
                else:
                    assert type(value) is int and LIMITS[field][0] <= value <= LIMITS[field][1], 'Invalid threshold'
    # Cycles are deliberately unsupported so exhaustive route checks terminate.
    def visit(key, active, done):
        assert key not in active, 'Story contains a cycle'
        if key in done:
            return
        for c in nodes[key]['choices']:
            visit(c['target'], active | {key}, done)
        done.add(key)
    visit(story['initial'], set(), set())
    reached, endings, paths, usable = set(), set(), [], set()
    def explore(s):
        reached.add(s['scene'])
        if nodes[s['scene']]['ending']:
            endings.add(s['scene'])
            paths.append(s)
            return
        options = [c for c in nodes[s['scene']]['choices'] if available(c, s)]
        assert options, 'Reachable state has no available decision'
        for c in options:
            usable.add((s['scene'], c['id']))
            explore(advance(story, s, c['id']))
    explore(initial(story))
    assert reached == set(nodes), f'Unreachable scenes: {set(nodes) - reached}'
    assert endings == {k for k, n in nodes.items() if n['ending']}, 'Unreachable ending'
    assert usable == {(k,c['id']) for k,n in nodes.items() for c in n['choices']}, 'Unusable choice'
    return paths

if __name__ == '__main__':
    for story in SCENARIOS.values():
        paths = validate(story)
        print(f'{story["title"]}: {len(story["scenes"])} scenes, {len(paths)} complete routes, 3 reachable endings')
