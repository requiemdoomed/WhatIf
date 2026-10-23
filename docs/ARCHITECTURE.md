# Technical notes

Author: Swayam Shakya

## Responsibilities

- `templates/index.html`: semantic shell, navigation, confirmation dialog and notification region.
- `static/js/theme.js`: apply saved appearance before the page renders.
- `static/js/app.js`: hash navigation, safe DOM construction, requests, story controls and SVG graph.
- `static/css/style.css`: two color systems, focus styling, responsive layouts and motion preferences.
- `app.py`: request validation, anonymous profile isolation, database transactions and JSON responses.
- `engine/decision_engine.py`: deterministic prerequisites, state changes, history and replay.
- `engine/story_validator.py`: structural validation and exhaustive path traversal.
- `stories/scenarios.py`: story content and declarative rules.
- `launcher.py`: loopback server lifecycle, duplicate-start handling and useful port errors.

## Decision sequence

1. The frontend sends a choice ID, current scene and expected integer version.
2. Flask verifies the session token and reads the journey owned by that browser.
3. `BEGIN IMMEDIATE` serialises writers. A stale scene or version returns 409.
4. The engine locates the choice and checks every requirement against saved state.
5. A copy receives bounded state updates, new evidence and one history event.
6. SQLite stores the snapshot and unique `(journey, step)` event and increments the revision.
7. Earned discoveries and achievements are recorded within the same transaction.
8. The frontend receives the resulting scene and redraws the player.

The client cannot submit state deltas, arbitrary scene targets or story code. Invalid operations roll back. All SQL values use parameters; the reset table list is a fixed server-owned tuple.

## Tables

| Table | Role |
|---|---|
| scenarios | Separate catalogue definitions indexed by scenario ID |
| journeys | Profile owner, scenario, state/history snapshot, revision, parent, branch point, hint count and timestamps |
| decisions | Ordered decision events with a unique journey/step key |
| checkpoints | Named by generated ID; one position per journey and decision count |
| discoveries | Unique profile/scenario/ending combinations |
| achievements | Unique profile/achievement with first-earned timestamp |

Foreign keys connect the catalogue, journeys and child records. Cascades clean up decisions and checkpoints. Profile and timestamp indexes support the journey list. Each request opens its own SQLite connection; WAL mode and a ten-second busy timeout support multiple local browser tabs.

Snapshots contain history as well as state so replay and presentation stay straightforward. The separate event table provides a transactional record and uniqueness constraint. The current implementation loads the small local history collection into memory; it is not optimised for millions of journeys.

## Branches and checkpoints

A branch accepts a prefix length, replays that many events and inserts a separate journey linked to its parent. It may start at zero, at an earlier decision, or at the current saved position. Replaying a prefix does not award new achievements. A recorded decision that differs from the parent route earns the alternate achievement, including a later divergence after an initially repeated choice. Hint use is conservatively inherited from the parent, even if the hint was requested after the selected branch point.

A checkpoint stores the journey ID and prefix length. Restoring uses the same branch mechanism. The graph marks actually visited edges from history, locked immediate destinations from current prerequisites, and parent-only scenes in a separate color. Gray nodes are topology, not predictions that a route is currently reachable. Undiscovered ending descriptions are never presented as completed outcomes.

## Main endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/bootstrap` | Catalogue, journeys, achievements and verification token |
| POST | `/api/journeys` | Start a journey with `scenario` |
| GET | `/api/journeys/<id>` | Read state, choices and graph |
| POST | `/api/journeys/<id>/choose` | Apply `choice`, `scene`, `version` |
| POST | `/api/journeys/<id>/fork` | Copy history before `step` |
| POST | `/api/journeys/<id>/checkpoint` | Save current position |
| POST | `/api/journeys/<id>/hint` | Record hint use and return a hint |
| POST | `/api/reset` | Delete current profile after `confirm: "RESET"` |

Mutations require `X-CSRF-Token` from bootstrap. Missing or malformed bodies receive 400; missing journeys receive 404; session failures receive 403; stale decisions receive 409. Database failures return a generic 503 without filesystem paths or SQL details.

## Local safety and limitations

Only loopback hostnames are accepted. Debugging is off. Cookies are HTTP-only and SameSite Strict. The page has a self-only content policy and uses text nodes for dynamic content. The application does not execute user-supplied code or accept uploads. Browser settings are local preferences rather than trusted game state.

The current catalogue is authoritative. Scenario ID/choice changes require a development progress reset; there is no automatic migration of existing story histories. A single launcher thread is reused within one Python process; separate processes still receive a clear occupied-port error.

## Anthology and runtime efficiency

`stories/anthology.py` reads 100 authored records from ten UTF-8 packs. Each record supplies its premise, clue, discovery, dilemma, three final actions and three ending paragraphs. The builder applies an explicit investigation, negotiation or countdown graph. The original five story IDs and definitions remain compatible with their saved journeys.

The resulting 105 scenarios are validated once per process. Catalogue metadata carries real scene, ending and route counts. The startup upsert changes a stored definition only when its bytes differ. Restart the application after editing content; the catalogue is intentionally not hot-reloaded during a game.

Bootstrap returns state and decision counts, but omits decision history. It loads all checkpoint summaries in a single query rather than one query per journey. Opening a journey, route or comparison fetches the full saved history. The browser renders twelve scenario cards per page and appends journeys in batches of fifteen. Genre, search, discovery status and favourites filter the metadata before rendering.

## Soundtrack lifecycle

`static/js/audio.js` owns one AudioContext and a master volume stage. Eleven locally bundled PCM loops are composed by `tools/compose_audio.py`: an opening theme and ten genre themes. Scenario IDs determine a stable offset and a small rate variation, while remaining time modestly affects pacing. An ending can trigger a short optional cue. There is no narration or network music service.

The first trusted page interaction unlocks audio without a selection screen. Navigation requests the correct desired score, and a generation counter prevents stale loads from replacing a more recent selection. Tracks crossfade through separate gain nodes; ended voices disconnect. The decoded-buffer cache retains at most three genre scores. A failed current load pauses playback and reports the error without blocking the story.

A background visibility event suspends the context. Returning resumes only previously enabled playback. Closing the page closes the context. A browser may require another user gesture after reload. Volume and sound-effect preferences live in localStorage; actual playback state is reported from the current context rather than assumed from a saved preference.

Technical references for playback behavior:

- [MDN: Web Audio API best practices](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Best_practices)
- [MDN: autoplay and Web Audio](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay)

### Illustrated atmosphere and revised sound

Local SVG scenery is keyed by each scenario's existing audio profile, ensuring every catalogue card, story banner and page background resolves to a bundled asset. Opaque surfaces preserve reading contrast. The opening score is explicitly accessible on the homepage. Stereo environmental textures are synthesized by `tools/compose_audio.py`; no third-party recordings are used. Each playback voice owns a low-pass filter that opens gradually with tension without changing pitch mid-scene. Disposing a voice also disconnects its filter. Small story-specific playback offsets/rates remain stable, and decision cues use the genre's tonal root.

The entrance dialog has been replaced by trusted click, touchend and keydown listeners. The first gesture synchronously resumes the audio context and removes these listeners. The dedicated music toggle handles its own activation to avoid a double toggle. Later interactions do not override a manual pause.

## Main HTML and launch workflow

The canonical document is the project-root `index.html`, returned by Flask at `/` and `/index.html`. Relative stylesheet and bootstrap-script paths also work when opened as a local file. `entry.js` shows local startup guidance for `file:` URLs; for HTTP/HTTPS it loads the audio engine followed by the interface. It never attempts to execute arbitrary local programs from the browser.

`run.py` creates a project-local virtual environment, checks the required package major versions and installs missing dependencies. It then launches `app.py --open-browser`, or the original notebook when `--notebook` is selected. Notebook and direct launches share the existing backend, stories and database. The server stays on loopback with the same CSRF, ownership and host protections. No authentication or database logic was moved into the HTML.
