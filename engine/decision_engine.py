"""Pure story rules; no browser or database dependencies."""
from copy import deepcopy

LIMITS = {'time': (0, 6), 'resources': (0, 3), 'trust': (0, 3)}

class StoryError(ValueError):
    pass


def initial(story):
    return {'scene': story['initial'], 'state': dict(story['initial_state']), 'evidence': [], 'history': []}


def available(choice, snapshot):
    for key, value in choice['requires'].items():
        if key == 'evidence':
            if value not in snapshot['evidence']:
                return False
        elif snapshot['state'][key] < value:
            return False
    return True


def advance(story, snapshot, choice_id):
    node = story['scenes'].get(snapshot['scene'])
    if not node or node['ending']:
        raise StoryError('This scene cannot accept another decision.')
    choice = next((c for c in node['choices'] if c['id'] == choice_id), None)
    if not choice or not available(choice, snapshot):
        raise StoryError('That choice is not available at this point.')
    result = deepcopy(snapshot)
    before = dict(result['state'])
    for key, delta in choice['delta'].items():
        low, high = LIMITS[key]
        result['state'][key] = max(low, min(high, result['state'][key] + delta))
    if choice['evidence'] and choice['evidence'] not in result['evidence']:
        result['evidence'].append(choice['evidence'])
    result['history'].append({'scene': snapshot['scene'], 'choice': choice_id,
        'label': choice['label'], 'consequence': choice['consequence'],
        'before': before, 'after': dict(result['state']), 'target': choice['target']})
    result['scene'] = choice['target']
    return result


def replay(story, history):
    result = initial(story)
    for event in history:
        if event['scene'] != result['scene']:
            raise StoryError('The saved route does not match this story version.')
        result = advance(story, result, event['choice'])
    return result


def present(story, snapshot):
    node = deepcopy(story['scenes'][snapshot['scene']])
    for choice in node['choices']:
        choice['available'] = available(choice, snapshot)
    return node
