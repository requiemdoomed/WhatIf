"""Short-story anthology. Three explicit structures, with authored scenes and outcomes.

Author: Swayam Shakya. Pack files are editable UTF-8 story records, not executable code.
"""
from pathlib import Path
import re

PACKS = {
    'futuristic': ('Futuristic', '◎', 'orbital'),
    'retro': ('Retro', '▣', 'tape'),
    'murder': ('Murder mystery', '◈', 'noir'),
    'mystery': ('Mystery', '⌕', 'mystery'),
    'cyberpunk': ('Cyberpunk', '▥', 'neon'),
    'modern': ('Modern life', '◷', 'city'),
    'quantum': ('Quantum', '⟡', 'quantum'),
    'time': ('Time travel', '◴', 'clock'),
    'survival': ('Survival', '△', 'wilderness'),
    'uncanny': ('Uncanny', '☽', 'uncanny'),
}
FIELDS = ('title', 'opening', 'evidence', 'discovery', 'pressure', 'solution',
          'resolved', 'compromise', 'contained', 'risk', 'fallout')


def load_anthology(scene, choice):
    stories = {}
    for pack, (category, symbol, sound) in PACKS.items():
        source = Path(__file__).parent / 'packs' / (pack + '.txt')
        for number, line in enumerate(source.read_text(encoding='utf-8').splitlines()):
            if not line.strip():
                continue
            values = line.split('|')
            if len(values) != len(FIELDS):
                raise ValueError(f'{source.name}, line {number + 1}: expected {len(FIELDS)} fields')
            text = dict(zip(FIELDS, values))
            sid = pack + '-' + re.sub(r'[^a-z0-9]+', '-', text['title'].lower()).strip('-')
            if sid in stories:
                raise ValueError('Repeated scenario ID: ' + sid)
            structure = ('investigation', 'negotiation', 'countdown')[number % 3]
            nodes = build_nodes(text, structure, scene, choice)
            stories[sid] = dict(id=sid, title=text['title'], category=category,
                description=text['opening'].split('. ')[0] + '.',
                difficulty='Challenging' if structure == 'countdown' else 'Moderate',
                minutes=5, symbol=symbol, initial='opening',
                initial_state={'time': 6, 'resources': 3, 'trust': 1}, scenes=nodes,
                audio=sound, structure=structure,
                content_note='Fictional death and investigation; no graphic descriptions.' if pack == 'murder' else '',
                tags=[category, structure, 'short story'])
    return stories


def build_nodes(t, structure, scene, choice):
    proof = {'evidence': t['evidence']}
    endings = {
        'resolved': scene('Ending · A considered answer', t['resolved'], ending=True),
        'contained': scene('Ending · A different kind of victory', t['contained'], ending=True),
        'fallout': scene('Ending · What follows', t['fallout'], ending=True),
    }
    nodes = dict(endings)
    nodes['opening'] = scene('Chapter 1 · The interruption', t['opening'], [
        choice('investigate', 'Examine the ' + t['evidence'].lower(), 'evidence',
               'You follow a specific lead instead of acting on the first explanation.', {'time': -1}),
        choice('respond', 'Meet the people affected before choosing a plan',
               'discussion' if structure == 'negotiation' else 'pressure',
               'You begin with the people who will live with your decision.', {'time': -1})],
        hint='The ' + t['evidence'].lower() + ' is the lead that can unlock a third outcome.')
    if structure == 'negotiation':
        nodes['evidence'] = scene('Chapter 2 · What the record says', t['discovery'], [
            choice('share', 'Bring the verified finding to the discussion', 'discussion',
                   'You preserve the finding and make it available for a shared decision.',
                   {'time': -1}, evidence=t['evidence']),
            choice('withhold', 'Leave the finding unverified and discuss the immediate problem', 'discussion',
                   'You save an interval, but cannot rely on an unverified record as evidence.')],
            hint='Verification preserves the evidence. You will still need cooperation at the discussion.')
        nodes['discussion'] = scene('Chapter 3 · A place at the table', t['pressure'], [
            choice('listen', 'Reserve time and one resource for a shared plan', 'decision',
                   'People affected by the outcome help check your plan.', {'time': -1, 'resources': -1, 'trust': 1}),
            choice('support', 'Commit two resources to independent support', 'decision',
                   'Independent support earns cooperation while using most of your reserve.', {'resources': -2, 'trust': 2}),
            choice('alone', 'Keep your reserve and decide without consultation', 'decision',
                   'You retain supplies but lose the cooperation needed for a coordinated solution.', {'trust': -1})],
            hint='Either a shared plan or independent support builds trust. Acting alone does not.')
        nodes['decision'] = scene('Chapter 4 · The decision belongs to you',
            t['pressure'] + '\n\nWhat you can justify now depends on what you verified and whose cooperation you earned.', [
            choice('resolve', t['solution'], 'resolved', 'The verified finding and shared plan support a coordinated response.',
                   {'resources': -1}, {**proof, 'trust': 2, 'resources': 1}),
            choice('contain', t['compromise'], 'contained', 'You choose a limited, explicit response instead of claiming certainty.'),
            choice('risk', t['risk'], 'fallout', 'You commit to an immediate action before resolving the disputed facts.')],
            hint='The coordinated outcome needs verified evidence, trust of at least 2 and one resource.')
        return nodes

    target = 'decision'
    fast = structure == 'countdown'
    nodes['evidence'] = scene('Chapter 2 · The detail that changes things', t['discovery'], [
        choice('verify', 'Verify the finding and explain it to those involved', target,
               'The evidence is preserved and the people involved understand why it matters.',
               {'time': -2 if fast else -1, 'trust': 1}, evidence=t['evidence']),
        choice('copy', 'Preserve a quick copy without discussing the implications', target,
               'You retain the evidence and save time, but have not built support for using it.',
               {'time': -1} if fast else {}, evidence=t['evidence'])],
        hint='Verification builds trust. A quick copy preserves the clue but may require a later consultation.')
    nodes['pressure'] = scene('Chapter 2 · An immediate demand', t['pressure'], [
        choice('prepare', 'Use one resource to prepare a measured response',
               'evidence' if fast else target,
               'The immediate pressure eases. There is still a chance to examine the facts.',
               {'resources': -1, 'trust': 1, 'time': -1} if fast else {'resources': -1, 'trust': 1}),
        choice('rush', 'Commit two resources to an immediate response', target,
               'You spend most of the reserve before verifying the underlying explanation.', {'resources': -2})],
        hint='In a countdown route, preparation reaches the evidence later and leaves less time for verification.' if fast else 'An immediate response can preserve options, but it does not recover the evidence you passed over.')
    nodes['decision'] = scene('Chapter 3 · The turning point', t['pressure'], [
        choice('review', 'Use the verified evidence to review a coordinated solution', 'review',
               'You bring the finding into the final review.', {'time': -1}, proof),
        choice('contain', t['compromise'], 'contained', 'You choose the limited response and accept what it leaves unresolved.'),
        choice('shortcut', 'Consider the immediate action: ' + t['risk'].lower(), 'shortcut',
               'You approach a choice that is difficult to take back once made.')],
        hint='The evidence opens the review. The limited response remains available even when a fuller solution is locked.')
    needs = {'trust': 2, 'resources': 1, **({'time': 2} if fast else {})}
    nodes['review'] = scene('Chapter 4 · Before you commit',
        t['discovery'] + '\n\n' + t['pressure'] +
        ('\n\nThe remaining time now matters: a coordinated response requires two intervals.' if fast else ''), [
        choice('resolve', t['solution'], 'resolved', 'You act on the finding with the cooperation and reserves the plan requires.', {'resources': -1}, needs),
        choice('consult', 'Spend an interval checking the plan with those affected', 'consultation',
               'A final conversation earns cooperation, but uses another interval.', {'time': -1, 'trust': 1}),
        choice('contain', t['compromise'], 'contained', 'You choose a defensible compromise rather than force an unsupported plan.')],
        hint='A quick evidence copy can be followed by consultation. In countdown stories, check that two intervals will still remain.')
    nodes['consultation'] = scene('Chapter 5 · What the conversation changes',
        'You lay out the finding without pretending it answers every concern. ' + t['pressure'] +
        '\n\nThe choice is now informed by that conversation; any remaining limits still apply.', [
        choice('resolve', t['solution'], 'resolved', 'The revised plan proceeds with support from the people affected.', {'resources': -1}, needs),
        choice('contain', t['compromise'], 'contained', 'You keep the response within the time and resources that remain.')],
        hint='Cooperation cannot replace missing time or resources. The compromise is a complete ending, not a failed save.')
    nodes['shortcut'] = scene('Chapter 4 · The price of speed',
        t['pressure'] + '\n\nThe immediate action is still possible. You can also spend your remaining reserve to step back before committing.', [
        choice('reconsider', t['compromise'], 'contained', 'You use the reserve to arrange the limited response instead.', {'resources': -2}, {'resources': 2}),
        choice('risk', t['risk'], 'fallout', 'You take the immediate action and accept the consequences that follow.')],
        hint='Two remaining resources let you step back to the compromise; spending them early removes that option.')
    return nodes
