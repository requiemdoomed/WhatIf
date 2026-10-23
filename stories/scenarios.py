"""Original short stories for WhatIf. Author: Swayam Shakya."""

def choice(key, label, target, consequence, delta=None, requires=None, evidence=None):
    return dict(id=key, label=label, target=target, consequence=consequence,
                delta=delta or {}, requires=requires or {}, evidence=evidence)


def scene(title, text, choices=None, ending=False, hint='Careful observation can reveal a route that speed alone cannot.'):
    return dict(title=title, text=text, choices=choices or [], ending=ending, hint=hint)


SCENARIOS = {
 'signal': {
  'id': 'signal', 'title': 'The Last Signal', 'category': 'Science fiction', 'difficulty': 'Moderate', 'minutes': 5,
  'description': 'An Antarctic receiver speaks after the station goes dark. Someone has heard this signal before.',
  'symbol': '◎', 'initial': 'arrival', 'initial_state': {'time': 6, 'resources': 3, 'trust': 1},
  'scenes': {
   'arrival': scene('03:17 · Blackout', 'The lights die halfway through a weather report. Below the floor, the receiver keeps tapping: three short pulses, one long. Mara reaches for the evacuation keys. The emergency battery gives you six working intervals before the station freezes.', [
    choice('listen', 'Listen to the old recordings', 'archive', 'You spend an interval looking for a pattern.', {'time': -1}),
    choice('power', 'Go straight to the generator', 'generator', 'You take the remaining battery pack downstairs.', {'time': -1})]),
   'archive': scene('A voice beneath the static', 'A recording from eleven years ago contains the same rhythm. In the margin, a technician wrote: NOT A VOICE. A POSITION. Mara recognises her father’s handwriting. The coordinates point beneath the ice, not toward the sky.', [
    choice('map', 'Copy the buried coordinates', 'junction', 'The archive yields a location key. Mara agrees to stay.', {'time': -1, 'trust': 1}, evidence='Buried coordinates'),
    choice('leave', 'Leave the recording and move on', 'junction', 'You save time, but the location key remains behind.')]),
   'generator': scene('A dangerous shortcut', 'The generator is intact. Its coolant line is not. You can isolate the damaged loop, or bridge the breaker and accept the heat. Mara waits upstairs for your decision.', [
    choice('repair', 'Isolate the coolant loop', 'junction', 'A spare cartridge makes the generator safe.', {'resources': -1, 'trust': 1}),
    choice('bridge', 'Bridge the breaker', 'junction', 'Power returns briefly, but the spare pack burns out.', {'resources': -2})]),
   'junction': scene('The sealed hatch', 'With emergency lights restored, a hatch appears behind a sliding shelf. Its keypad asks for a location. Outside, the storm briefly parts. The receiver’s pulses grow closer together.', [
    choice('hatch', 'Use the coordinates to open the hatch', 'chamber', 'The lock accepts the archive coordinates.', {'time': -1}, {'evidence': 'Buried coordinates'}),
    choice('mast', 'Climb to the rescue transmitter', 'mast', 'You choose the visible world above the ice.', {'time': -1}),
    choice('evacuate', 'Leave with Mara now', 'safe', 'You abandon the receiver and reach the storm shelter.')]),
   'chamber': scene('The other station', 'The chamber holds a rescue beacon, still transmitting from an expedition presumed lost. Its cable is severed. A small service lift descends farther into the ice. The signal was never asking to be understood. It was asking to be found.', [
    choice('relay', 'Build a relay and send the position', 'truth', 'A clean signal reaches the coastal rescue team.', {'resources': -1}, {'resources': 1, 'trust': 2}),
    choice('withdraw', 'Record the location and withdraw', 'safe', 'You preserve the coordinates for a return expedition.')]),
   'mast': scene('Wind on the ladder', 'The transmitter can send one burst before the battery shuts down. A narrowband call needs a spare cartridge. The old distress flare is less precise, but it may still be visible from the coast.', [
    choice('call', 'Power the narrowband call', 'safe', 'A rescue crew confirms your position.', {'resources': -2}, {'resources': 2}),
    choice('flare', 'Launch the flare into the wind', 'cost', 'The flare disappears into snow. You wait out the storm.')]),
   'truth': scene('Ending · A signal answered', 'The rescue team reaches the buried outpost at dawn. Two survivors have been rationing heat for weeks. Your archive work turned an unexplained signal into a rescue; Mara leaves with her father’s notebook and a reason to keep listening.', ending=True),
   'safe': scene('Ending · Above the ice', 'You and Mara reach safety. The station is sealed until summer. You chose a survivable exit over certainty, and the unanswered pulses travel home with you.', ending=True),
   'cost': scene('Ending · The long night', 'You survive in the mast shelter, but frost destroys the receiver before help arrives. The team comes home; the only copy of the signal does not. Speed kept you moving, but left you without a dependable way to call.', ending=True)
  }},
 'developer': {
  'id': 'developer', 'title': 'The Missing Developer', 'category': 'Technology', 'difficulty': 'Moderate', 'minutes': 5,
  'description': 'Production is down. The release owner is missing. The easiest rollback may erase the answer.',
  'symbol': '⌘', 'initial': 'arrival', 'initial_state': {'time': 6, 'resources': 3, 'trust': 1},
  'scenes': {
   'arrival': scene('09:02 · Red across the board', 'The checkout graph falls to zero. Nila, who prepared the release, is not answering. A director wants the database rolled back immediately. Your on-call partner, Jules, asks whether you want evidence or uptime first.', [
    choice('logs', 'Capture the deployment logs', 'archive', 'You reserve an interval for a clean incident record.', {'time': -1}),
    choice('restore', 'Inspect the rollback tooling', 'generator', 'You head directly to the recovery console.', {'time': -1})]),
   'archive': scene('An unfinished handover', 'Nila’s last note says the migration completed but a feature flag did not. The log includes a signed configuration hash. Her emergency contact confirms she left to help a family member. The unexplained absence was not evidence of wrongdoing.', [
    choice('copy', 'Preserve the hash and tell Jules', 'junction', 'You keep the configuration proof and earn Jules’s support.', {'time': -1, 'trust': 1}, evidence='Signed configuration hash'),
    choice('skip', 'Return to the incident without a snapshot', 'junction', 'You save time but leave the volatile record exposed.')]),
   'generator': scene('Recovery has a price', 'The rollback script would overwrite orders placed after deployment. A staged restore needs one spare worker; a full reset is faster but consumes two and loses the new transactions.', [
    choice('stage', 'Prepare a staged recovery', 'junction', 'Jules agrees to the careful restore plan.', {'resources': -1, 'trust': 1}),
    choice('reset', 'Prepare the full reset', 'junction', 'Two recovery workers are tied up rebuilding the database.', {'resources': -2})]),
   'junction': scene('The incident room', 'The director asks for a decision. Jules has located the flag service, but changing production configuration requires a verified baseline. A maintenance page is already available if you need a safer holding pattern.', [
    choice('verify', 'Compare the flag against the signed hash', 'chamber', 'The preserved hash identifies the exact configuration drift.', {'time': -1}, {'evidence': 'Signed configuration hash'}),
    choice('rollback', 'Proceed with database recovery', 'mast', 'You begin recovery with the workers still available.', {'time': -1}),
    choice('hold', 'Enable maintenance and preserve orders', 'safe', 'Customers see an honest outage notice while orders remain intact.')]),
   'chamber': scene('One flag, two systems', 'The payment service expects the old format while checkout emits the new one. Jules can review a narrow configuration change. A worker can replay queued payments without touching the database.', [
    choice('fix', 'Review the flag change and replay the queue', 'truth', 'The verified correction restores checkout without losing orders.', {'resources': -1}, {'resources': 1, 'trust': 2}),
    choice('pause', 'Keep maintenance on for a full review', 'safe', 'You protect the queue and hand over a precise diagnosis.')]),
   'mast': scene('The recovery window', 'A staged restore needs two workers to reconcile old and new orders. A bulk rollback fits on one, but customers will have to submit recent orders again.', [
    choice('reconcile', 'Reconcile the orders during restore', 'safe', 'The service returns slowly, with the transaction record intact.', {'resources': -2}, {'resources': 2}),
    choice('bulk', 'Accept the bulk rollback', 'cost', 'The site returns, but recent orders are lost.')]),
   'truth': scene('Ending · A blameless recovery', 'Checkout recovers. The incident report documents configuration drift, not a missing colleague’s supposed mistake. Preserving evidence and inviting review let you repair the failure without inventing a culprit.', ending=True),
   'safe': scene('Ending · An honest outage', 'Orders are preserved and the next shift receives a usable handover. The outage lasts longer than anyone wanted. Your decision protects customers while leaving room for a careful repair.', ending=True),
   'cost': scene('Ending · Green graphs, missing orders', 'The dashboard turns green. Support spends the afternoon helping customers reconstruct purchases. Recovery solved the visible outage, but the cost was hidden in records the rollback replaced.', ending=True)
  }},
 'zero': {
  'id': 'zero', 'title': 'Zero Hour', 'category': 'Survival', 'difficulty': 'Challenging', 'minutes': 5,
  'description': 'A mountain crossing closes behind you. Six intervals of daylight, three supply packs, one team.',
  'symbol': '△', 'initial': 'arrival', 'initial_state': {'time': 6, 'resources': 3, 'trust': 1},
  'scenes': {
   'arrival': scene('14:10 · The ridge gives way', 'A slide buries the trail back to camp. Snow is moving across the western ridge. Ishan has twisted an ankle; the others want to descend before the light fades. Your map marks a survey hut nearby, though nobody knows if it still stands.', [
    choice('hut', 'Search the survey hut', 'archive', 'The detour costs one interval of daylight.', {'time': -1}),
    choice('gear', 'Reorganise the team’s equipment', 'generator', 'You stop to inspect the gear before moving.', {'time': -1})]),
   'archive': scene('A surveyor’s last route', 'The hut leans under the snow. A grease-pencil map marks a sheltered ravine and a cable anchor installed that summer. Ishan remembers seeing the same anchor on the approach.', [
    choice('map', 'Trace the ravine route and listen to Ishan', 'junction', 'You record the safe approach and restore confidence in the group.', {'time': -1, 'trust': 1}, evidence='Surveyor’s ravine map'),
    choice('rush', 'Leave before the snow deepens', 'junction', 'You return quickly without a reliable ravine route.')]),
   'generator': scene('Weight and warmth', 'Three supply packs remain. You can use one to splint Ishan’s ankle, or abandon two bulky packs to move faster. He is quiet, waiting to learn whether the team will move at his pace.', [
    choice('splint', 'Make a splint and share the load', 'junction', 'Ishan can walk with support. The team stays together.', {'resources': -1, 'trust': 1}),
    choice('drop', 'Discard the bulky packs', 'junction', 'You travel lighter, with little reserve for shelter.', {'resources': -2})]),
   'junction': scene('The fork in the snow', 'The ridge trail is exposed. A ravine descends out of the wind, but its entrance is hidden behind a cornice. A shallow rock shelter offers another option: stop moving and wait for rescue.', [
    choice('ravine', 'Follow the mapped ravine entrance', 'chamber', 'The survey notes guide you around the cornice.', {'time': -1}, {'evidence': 'Surveyor’s ravine map'}),
    choice('ridge', 'Attempt the exposed ridge', 'mast', 'You commit to the direct crossing.', {'time': -1}),
    choice('shelter', 'Shelter together and signal your location', 'safe', 'The team settles in for a cold but protected night.')]),
   'chamber': scene('The cable anchor', 'The anchor is sound. A short rope traverse will get everyone to the valley road. It needs one supply pack for a harness and a team willing to move together. Ishan offers to check every knot.', [
    choice('cross', 'Build a shared rope traverse', 'truth', 'Everyone crosses under the team’s careful supervision.', {'resources': -1}, {'resources': 1, 'trust': 2}),
    choice('camp', 'Make camp beside the sheltered anchor', 'safe', 'You choose a protected position over the final crossing.')]),
   'mast': scene('No margin on the ridge', 'Wind makes every step uncertain. Two packs can become a windbreak while you wait for the gusts to fall. Without them, the team must retreat through loose snow.', [
    choice('windbreak', 'Use two packs to build a windbreak', 'safe', 'The team shelters until rescuers reach the ridge.', {'resources': -2}, {'resources': 2}),
    choice('retreat', 'Retreat down the loose slope', 'cost', 'You reach lower ground, but scattered equipment is lost.')]),
   'truth': scene('Ending · Everyone comes home', 'At the valley road, the team counts heads before counting equipment. Every person is present. A forgotten map, a patient conversation and a shared rope mattered more than being fastest.', ending=True),
   'safe': scene('Ending · A night together', 'Rescuers find the group huddled behind a windbreak at first light. Nobody reaches the valley on schedule, but nobody is left behind. Choosing to stop was a decision, too.', ending=True),
   'cost': scene('Ending · The price of haste', 'The descent ends at an abandoned road. Everyone survives, though exposure and a second injury require evacuation. With fewer reserves, a small setback became a much larger one.', ending=True)
  }},
 'city': {
  'id': 'city', 'title': 'The Silent City', 'category': 'Mystery', 'difficulty': 'Moderate', 'minutes': 5,
  'description': 'A city loses its voice. The emergency network works, but the official explanation does not.',
  'symbol': '▥', 'initial': 'arrival', 'initial_state': {'time': 6, 'resources': 3, 'trust': 1},
  'scenes': {
   'arrival': scene('18:40 · No replies', 'Street screens go blank. Phones show full reception but nothing leaves them. The council calls it a cable fault. At a neighbourhood radio desk, Ren receives a paper message: the hospital’s private line still works.', [
    choice('records', 'Visit the municipal routing archive', 'archive', 'You spend an interval checking the council’s account.', {'time': -1}),
    choice('mesh', 'Help Ren build a neighbourhood relay', 'generator', 'You begin with the network people can see and trust.', {'time': -1})]),
   'archive': scene('An instruction, not a fault', 'The network log shows a deliberate quarantine command issued after a sensor error. Its authorisation ticket is still signed. Publishing it without context might start a panic; preserving it would make a targeted correction possible.', [
    choice('ticket', 'Copy the ticket and explain it to Ren', 'junction', 'Ren helps interpret the record without spreading a rumour.', {'time': -1, 'trust': 1}, evidence='Quarantine authorisation ticket'),
    choice('leave', 'Return without copying the ticket', 'junction', 'You avoid a delay, but lose the exact command identifier.')]),
   'generator': scene('A network made of neighbours', 'Ren has three portable relays. One can connect the clinic to the food depot. Using two for a central broadcast would reach more people immediately, but leave little capacity for local requests.', [
    choice('local', 'Connect the clinic and food depot first', 'junction', 'Residents see useful communication return.', {'resources': -1, 'trust': 1}),
    choice('broadcast', 'Use two relays for a central broadcast', 'junction', 'The announcement reaches the district; relay capacity shrinks.', {'resources': -2})]),
   'junction': scene('The switch room', 'A city engineer offers access to the network controls. She needs the exact authorisation ticket to cancel only the mistaken quarantine. Alternatively, a general restart could restore traffic, or you could keep the smaller local network running.', [
    choice('target', 'Present the signed ticket', 'chamber', 'The engineer isolates the mistaken quarantine.', {'time': -1}, {'evidence': 'Quarantine authorisation ticket'}),
    choice('restart', 'Prepare a general network restart', 'mast', 'You prepare to interrupt the remaining private lines.', {'time': -1}),
    choice('local', 'Keep the neighbourhood network running', 'safe', 'Essential local messages continue to move.')]),
   'chamber': scene('A public correction', 'The engineer can cancel the command while Ren publishes a clear explanation. A relay must remain online during the change so the clinic is not cut off. Residents wait outside for something more useful than reassurance.', [
    choice('correct', 'Restore the network and publish the record', 'truth', 'The correction is visible, documented and backed by a working relay.', {'resources': -1}, {'resources': 1, 'trust': 2}),
    choice('defer', 'Defer the central change and support local links', 'safe', 'The neighbourhood keeps its dependable fallback.')]),
   'mast': scene('The restart dilemma', 'Two relays could bridge the hospital’s line during the restart. Without that bridge, the network might return quickly while emergency calls disappear for several minutes.', [
    choice('bridge', 'Bridge the hospital before restarting', 'safe', 'Critical messages survive the interruption.', {'resources': -2}, {'resources': 2}),
    choice('cut', 'Restart without a bridge', 'cost', 'General traffic returns after a gap in emergency communication.')]),
   'truth': scene('Ending · A city heard', 'The screens return with a plain explanation and a public incident record. Residents keep the neighbourhood relays as a backup. Restoring trust required making the error visible, not merely making the lights work.', ending=True),
   'safe': scene('Ending · Small signals', 'Essential messages move again, though parts of the city remain disconnected. Neighbours carry paper notices between relay points. You build a slower recovery around the people most affected.', ending=True),
   'cost': scene('Ending · The missing minutes', 'The city reconnects. At the hospital, staff reconstruct calls that vanished during the restart. The network’s recovery time looks impressive; its human consequences are harder to fit on a screen.', ending=True)
  }},
 'protocol': {
  'id': 'protocol', 'title': 'The Final Protocol', 'category': 'Ethics', 'difficulty': 'Challenging', 'minutes': 5,
  'description': 'A research prototype begins to overheat. Protect the team, preserve the evidence, or race the clock.',
  'symbol': '◇', 'initial': 'arrival', 'initial_state': {'time': 6, 'resources': 3, 'trust': 1},
  'scenes': {
   'arrival': scene('21:06 · The red threshold', 'A thermal-storage prototype climbs past its permitted temperature. The automatic shutdown reports success, but the temperature keeps rising. Team lead Sol is already at the exit. The last test record may explain why the shutdown failed.', [
    choice('record', 'Inspect the independent test recorder', 'archive', 'You use one interval to check a separate source.', {'time': -1}),
    choice('cool', 'Inspect the emergency cooling rig', 'generator', 'You head to the manual safety equipment.', {'time': -1})]),
   'archive': scene('Two readings', 'The independent recorder shows a sensor calibration error. The shutdown closed the wrong valve. Its signed wiring diagram identifies the correct circuit. Sol admits that the demonstration deadline pushed the final review aside.', [
    choice('diagram', 'Keep the diagram and include Sol in the plan', 'junction', 'The team has both a verified circuit and a shared account of the failure.', {'time': -1, 'trust': 1}, evidence='Verified valve diagram'),
    choice('leave', 'Leave the recorder and clear the room', 'junction', 'You move faster, without the circuit reference.')]),
   'generator': scene('The cooling rig', 'Three coolant cartridges remain. One can stabilise the system long enough to organise a controlled response. Dumping two now brings the temperature down faster but leaves less reserve for the final shutdown.', [
    choice('steady', 'Apply one cartridge and brief the team', 'junction', 'The temperature steadies and Sol agrees to a deliberate plan.', {'resources': -1, 'trust': 1}),
    choice('dump', 'Apply two cartridges immediately', 'junction', 'The temperature drops, consuming most of the reserve.', {'resources': -2})]),
   'junction': scene('The final authority', 'The safety panel offers a manual circuit override, a bulk cooling shutdown, or remote isolation after evacuation. Only the verified wiring diagram makes the circuit override safe to attempt.', [
    choice('circuit', 'Use the verified manual circuit', 'chamber', 'You identify the correct valve without guessing.', {'time': -1}, {'evidence': 'Verified valve diagram'}),
    choice('bulk', 'Prepare the bulk cooling shutdown', 'mast', 'The remaining cartridges become the limiting factor.', {'time': -1}),
    choice('isolate', 'Evacuate and isolate the lab remotely', 'safe', 'The team leaves before the containment doors close.')]),
   'chamber': scene('A two-person check', 'Sol reads the circuit reference aloud while you verify the valve position. One cartridge will absorb the remaining heat. The recorder can keep running if everyone follows the same sequence.', [
    choice('check', 'Complete the shared shutdown checklist', 'truth', 'The correct valve closes and the recorder captures the full event.', {'resources': -1}, {'resources': 1, 'trust': 2}),
    choice('exit', 'Stop the intervention and evacuate', 'safe', 'You place the team’s safety above recovering the prototype.')]),
   'mast': scene('The last reserve', 'A controlled cooling shutdown needs two cartridges. The destructive suppression system works without them, but floods the test chamber and destroys the recorder.', [
    choice('cool', 'Use two cartridges for controlled cooling', 'safe', 'The system settles with the team outside the chamber.', {'resources': -2}, {'resources': 2}),
    choice('flood', 'Activate destructive suppression', 'cost', 'The heat falls while water destroys the test equipment.')]),
   'truth': scene('Ending · The record remains', 'The team is safe and the investigation has a complete record. The prototype will not be demonstrated tomorrow. The signed report names the missed review and changes the procedure before another team repeats it.', ending=True),
   'safe': scene('Ending · A closed laboratory', 'Everyone leaves safely. The prototype remains isolated until an independent inspection. You accept delay and uncertainty instead of gambling with the people responsible for finding the answer.', ending=True),
   'cost': scene('Ending · Safety without answers', 'Suppression contains the overheating. Nobody is hurt, but the test recorder is ruined. The team must reconstruct the cause from incomplete notes, and rebuilding takes far longer than the cancelled demonstration.', ending=True)
  }}
}

# Existing IDs and rules remain unchanged so earlier journeys can still be resumed.
from stories.anthology import load_anthology
SCENARIOS.update(load_anthology(scene, choice))
for _sid, _sound in {'signal': 'orbital', 'developer': 'neon', 'zero': 'wilderness',
                     'city': 'mystery', 'protocol': 'quantum'}.items():
    SCENARIOS[_sid].update(audio=_sound, structure='classic', content_note='',
                          tags=[SCENARIOS[_sid]['category'], 'classic'])
