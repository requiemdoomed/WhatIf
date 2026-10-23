# WhatIf — The Alternate Reality Engine

**One Decision. Infinite Possibilities.**  
Created by **Swayam Shakya**.

WhatIf: Anthology Edition is a local narrative game about revisiting decisions. Enter a fictional world, gather evidence, manage limited resources and follow a route to its ending. Then branch before an earlier choice and compare the two journeys without losing the original.

## What is included

- 105 playable short stories, 955 scenes, 315 endings and 2,135 verified complete routes.
- Server-validated choices, conditional routes, evidence, consequences and bounded state.
- Automatic saving, manual checkpoints, replay and independent alternate journeys.
- A route graph, a readable decision journal and side-by-side comparisons.
- Six achievements calculated from recorded progress.
- Searchable, filterable scenario library and discovered-ending collection.
- Light and dark themes, reduced motion, larger story text and optional decision sounds.
- An original 32-second opening score and ten 24-second genre scores, with crossfades, volume and pause controls.
- Twelve-card catalogue pages, saved favourites, genre/progress filters and a surprise-world button.
- Compact progress summaries with route details loaded only when opened.
- A genuine Jupyter launch notebook, Flask server, SQLite database, route manifest and automated tests.
- Local operation with no accounts, external services, analytics or remote assets.

Music starts with the first tap, click or keypress, without a selection screen. The interface uses a restrained violet accent, orbital line artwork and clear story cards. The player places the narrative beside a compact state panel. On small screens, panels and comparisons stack vertically; the graph can be scrolled horizontally and has a text alternative.

## Start here

1. Extract the **entire** ZIP into a writable folder.
2. Install Python 3.10 or newer if it is not already installed.
3. **Windows:** double-click `START_WINDOWS.bat`. **macOS/Linux:** open Terminal in the project folder and run `bash START_MAC_LINUX.sh`.
4. The launcher prepares `.venv`, installs Flask if needed, starts the server and opens **index.html** in your browser. Keep the terminal open; press Ctrl+C to stop.

The first setup needs internet access. Later launches reuse the environment and saved database. No Node.js or separate build command is needed.

You may also run `python run.py` on Windows or `python3 run.py` on macOS/Linux. To choose another port: `python run.py --port 5051`. To print the URL without opening a browser: `python run.py --no-browser`.

**Opening index.html directly:** it displays a local startup page with instructions and an **Open running game** link. HTML cannot execute Python or a notebook by itself. Once the server starts, the same root `index.html` becomes the complete interactive game at `http://127.0.0.1:5050/index.html` (or the port printed by the launcher).

**Notebook workflow:** run `python run.py --notebook` (use `python3` on macOS/Linux). This installs Jupyter if necessary and opens the original `whatif_notebook.ipynb`. Run its launch cells and use the game link. Both workflows use the same Python engine, SQLite database and assets. Do not launch both servers on the same port.

### How the files work together

- `index.html` is the main browser interface, served at both `/` and `/index.html`.
- `static/js/entry.js` distinguishes a local file from the running website, then loads audio and game controls in order.
- `static/js/app.js` calls Flask routes in `app.py`; Python checks choices and saves progress in SQLite.
- `stories/` and `engine/` supply all scenarios and branching rules.
- `static/` contains the music, artwork, themes and interface scripts.
- `run.py` and the platform launchers handle startup. The notebook remains an alternative launch and development workspace.
- `templates/index.html` is retained as a compatibility redirect; the root `index.html` is authoritative.

Copy the complete project when moving it. Keep `database/` to preserve saves and use the same browser profile and hostname. A plain static server or GitHub Pages cannot execute Flask; use the supplied launcher.

## Requirements

Python **3.10 or newer**, a recent browser and a writable project folder. Python 3.12.14 and Flask 3.1.3 were used for the included verification. Installation needs an internet connection; normal play does not.

This is a Python application with a browser interface. **GitHub can host the source, but GitHub Pages cannot run its Flask backend.** Download and run the complete project locally. Opening `index.html` directly shows startup guidance; playing requires the included server. Do not upload only the notebook.

## Install

Extract the ZIP, then open a terminal inside `WhatIf`.

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m notebook whatif_notebook.ipynb
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m notebook whatif_notebook.ipynb
```

Using the environment's executable directly avoids shell activation-policy problems. On macOS/Linux, a newly installed Python distribution may be needed if `venv` is unavailable.

## Launch from Jupyter

Open `whatif_notebook.ipynb` and run sections 1–4 in order. The notebook locates the extracted files, checks Flask, validates all story routes, initialises SQLite and starts the server in a background thread. Open the printed address, normally **http://127.0.0.1:5050**.

Leave the kernel running while you play. Re-running the start cell reuses the existing server. Run section 7 to stop it; run section 4 again to restart. Section 6 optionally runs all automated tests against temporary databases.

**Do not run the final stop cell until you have finished playing.** “Run All” intentionally completes the entire start/test/stop lifecycle and leaves the website stopped.

Hosted notebooks are not the intended environment. If their localhost cannot be reached from your browser, run the extracted project on your own computer with the commands below.

## Launch directly

After installation, run:

```bash
python app.py
```

Use the virtual environment's Python executable from the installation examples if it is not activated. Open the printed localhost address. Stop with **Ctrl+C** in the terminal. The normal server has debugging disabled and binds only to `127.0.0.1`.

If port 5050 is occupied:

```bash
python app.py --port 5051
```

The notebook has an equivalent `PORT` variable. Port `0` asks the operating system for a free port.

## A quick demonstration

1. Enter **The Last Signal**.
2. Listen to the old recordings, copy the coordinates, open the hatch and build the relay.
3. Review the discovered ending, then open **Timeline Lab**.
4. Branch before the first decision. Inspect the generator, bridge the breaker, climb to the transmitter and launch the flare.
5. Compare both routes. The original remains intact, while the alternate has a different reserve level, evidence collection and ending.

Choices with unmet requirements remain visible but disabled. A checkpoint restores into a new branch; it never rewinds or overwrites the original. Outcomes only count as discoveries once the corresponding ending is reached. A fork that repeats the original decision does not earn the alternate-route achievement.

## Project structure

```text
WhatIf/
├── whatif_notebook.ipynb
├── app.py
├── launcher.py
├── requirements.txt
├── README.md
├── engine/
│   ├── decision_engine.py
│   └── story_validator.py
├── stories/
│   ├── scenarios.py
│   ├── anthology.py
│   └── packs/ (ten authored story collections)
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   ├── js/{theme.js,audio.js,app.js}
│   └── audio/ (eleven original WAV scores)
├── tools/ (catalogue verification, benchmarking and audio composition)
├── database/.gitkeep
├── tests/
│   ├── test_engine.py
│   ├── test_routes.py
│   ├── test_launcher.py
│   ├── test_anthology.py
│   ├── browser_smoke.py
│   └── browser_anthology.py
└── docs/
    ├── ARCHITECTURE.md
    ├── TEST_REPORT.md
    ├── CATALOGUE.md
    ├── ROUTE_MANIFEST.json
    └── PERFORMANCE.json
```

## How it works

The browser requests scenes from Flask using same-origin JSON requests. The server reads the saved journey, verifies its scene and revision, evaluates the requested choice and updates its state using the pure Python engine. SQLite commits the snapshot, decision event and any discoveries or achievements in one transaction. A stale or repeated decision receives an HTTP 409 response instead of being applied twice.

Branching replays the original decision prefix into a new journey. The original is not modified. The graph is built from real scenario edges; it does not generate speculative story content. See [the architecture notes](docs/ARCHITECTURE.md) for the schema and request contract.

### State meanings

| Variable | Range | Meaning |
|---|---|---|
| Time | 0–6 | Remaining intervals; coordinated endings in countdown stories require at least two |
| Resources | 0–3 | Spare equipment, workers, relays or coolant reserves |
| Trust | 0–3 | Team cooperation; required for the coordinated evidence route |
| Evidence | Named items | Discoveries that unlock a specific route |

Time records investigation, travel and consultation. Countdown stories make it an actual prerequisite: a coordinated ending requires two remaining intervals. Negotiation stories reward cooperation, while investigation stories allow a later consultation to recover missing trust. Time is never a live countdown, and reading slowly has no penalty. Values are clamped to their documented limits.

## Sound before and during play

Tap, click or press a key anywhere to unlock *Between Possibilities* on the homepage. Entering a scenario automatically selects its music. The header's ♫ button starts or pauses music, and the persistent bottom control changes volume. A fresh page load may require another click before a browser permits playback.

Each genre has its own original instrumental score: orbital ambience, warm retro tones, restrained noir, mystery, neon electronics, modern city, quantum bells, time-travel motifs, wilderness texture and uncanny atmosphere. Every scenario selects the appropriate genre score and applies a stable starting offset and small playback-rate variation. Lower remaining time slightly increases pacing. These are **11 composed scores with scenario variations**, not 105 separately recorded songs or voice narration.

Music crossfades between worlds. Background tabs suspend audio, and the decoded buffer cache holds at most three scores. There are no remote audio requests or copyrighted song samples. The optional decision/ending cues can be enabled in Settings. Use **Preview atmosphere** on a story card to listen without starting a journey.

The WAV files are bundled under `static/audio/`. Playback needs no extra Python packages. To regenerate the scores, optionally install NumPy and run `python tools/compose_audio.py`. Sound levels have been checked for clipping; comfortable listening volume still depends on your device.

## Upgrading from the five-story edition

Stop the old server, back up its `database` folder, and replace the application files with this edition. Keep the original database folder and `.session-key`, then use the same browser and hostname. The original five scenario IDs and rules are unchanged. The server adds the new catalogue entries without deleting your journeys. Theme and reading preferences remain in the browser. Browser bookmarks under **Saved for later** are local preferences, separate from database progress.

## Progress and privacy

`database/whatif.sqlite3` stores scenario definitions, journeys, decision events, checkpoints, discovered endings and achievement records. `database/.session-key` holds the locally generated signing key. Neither is included in the archive or intended for Git.

A signed, HTTP-only browser cookie holds an anonymous profile identifier and a request-verification token. Progress is filtered by that profile. Use the **same browser and hostname** each time: `localhost` and `127.0.0.1` have separate cookies. Clearing cookies, using a private window or changing the signing key creates a different profile. Existing rows are not automatically reassigned.

To back up progress, stop the server and copy the **whole database folder**; retain your browser cookie too. Settings are saved in browser localStorage. Reset in Settings deletes only the current profile's progress and requires typing `RESET`. Theme and reading preferences remain.

This is a single-computer project, not a public multi-user hosting service. Cookie transport is HTTP on loopback. Do not expose the development server to the internet.

## Testing

Run these commands **inside the WhatIf folder**:

```bash
python -m unittest discover -s tests -v
python -m engine.story_validator
python tools/verify_catalogue.py
```

Tests cover all 2,135 complete routes through both the pure engine and Flask, validation failures, locked choices, replay, original preservation, checkpoint idempotency, achievements, hints, malformed requests, ownership, reset, concurrent duplicates, database restart and server lifecycle.

See [TEST_REPORT.md](docs/TEST_REPORT.md) for executed results and environment limitations. Test success is evidence for the cases checked, not a guarantee that no defect can exist.

## Add a scenario

Add an entry to `SCENARIOS` in `stories/scenarios.py`. Use a unique ID, metadata, `initial`, `initial_state`, and a `scenes` mapping. Each scene has a title, narrative, choices and an ending flag. Use the `scene()` and `choice()` helpers already in the file.

A choice contains a unique ID within its scene, visible label, target scene, consequence, optional numeric state deltas, optional prerequisite thresholds, and an optional evidence item. A condition such as `{'resources': 2}` means at least two resources; `{'evidence': 'Item name'}` requires that exact discovered item. Choices cannot specify arbitrary Python code.

Keep the graph acyclic and give every reachable non-ending state at least one available choice. Endings have no choices. Run the validator to check missing targets, unreachable scenes/endings, impossible choices, invalid conditions and cycles. Then add an appropriate regression test and update catalogue-count expectations in existing tests.

The additional 100 episodes live in ten UTF-8 files in `stories/packs/`. Each line has eleven pipe-separated fields: title, opening, evidence name, discovery, pressure, coordinated action, coordinated ending, compromise action, compromise ending, immediate action and its ending. `stories/anthology.py` turns these authored records into three shared branching structures. They are compact episodes, not 100 independently coded engines. Each has unique opening and ending prose.

After editing a pack, run `python tools/verify_catalogue.py` to rebuild the catalogue and ending witnesses. No downloaded model, training data or training step is involved: the decision model is deterministic Python logic. Improving its quality means validating content, testing conditions and profiling requests.

Structural edits to an existing story can invalidate saved histories. Back up progress and reset the affected development database before changing scene or choice IDs. This version has no story-version migration tool.

## Troubleshooting

| Problem | What to do |
|---|---|
| Connection refused | Run the notebook start cell again; make sure its stop cell has not run. |
| Port unavailable | Stop the other process or choose `--port 5051` / `PORT = 5051`. |
| Flask cannot be imported | Install requirements using the same Python environment as the notebook kernel. |
| Missing project files | Extract the entire archive, not just the notebook. |
| “Journey has moved on” | Another tab submitted a decision. Refresh to load the saved version. |
| Session verification failed | Refresh the page. Enable cookies for the local address. |
| Progress appears empty | Check the browser profile, hostname and original database/signing-key files. |
| Database cannot be saved | Move the project to a writable folder and close duplicate server processes. |
| Remote notebook link will not open | Run Jupyter or the direct Flask launcher on your own computer. |

For a full title-by-title list, see [CATALOGUE.md](docs/CATALOGUE.md). [ROUTE_MANIFEST.json](docs/ROUTE_MANIFEST.json) includes a current story-content hash and a reproducible choice sequence reaching each ending. [PERFORMANCE.json](docs/PERFORMANCE.json) records local measurements, not promises about other computers.

Optional browser tests:

```bash
python -m pip install playwright
python -m playwright install chromium
python tests/browser_smoke.py
python tests/browser_anthology.py
```

## Scope

The stories are short authored narratives with fixed decision graphs and three shared anthology structures. Fictional murder scenarios are non-graphic and display a content note. There is no model to train, random story generation, real-time clock, account recovery or cloud sync. Development is intentionally lightweight. The launch paths use portable Python APIs, but Windows and macOS native execution must still be checked on those operating systems.

**Author: Swayam Shakya**

## Atmosphere edition

The opening music unlocks automatically on your first tap, click or keypress anywhere on the page. There is no sound-selection popup. Scenario music changes automatically when you enter each story. Pause and volume controls remain available throughout play. Quiet play is fully supported.

All 105 scenarios use matching genre artwork on their cards, illustrated story banners and page backgrounds. Ten genre sound worlds use original synthesized rain, city textures, tape hiss, clockwork, woodland wind and birds, orbital machinery or drifting harmonics as appropriate. Each story has a stable playback variation. These are ten genre arrangements, not 105 individually recorded soundtracks. Tension opens the music's filter gradually; decision cues follow the score's key. Stereo reflections, crossfades and a bounded buffer cache keep transitions smooth.

Reading surfaces remain opaque in both light and dark modes. No external artwork, samples, music service, account or model download is required. Author: Swayam Shakya.

Music unlocks once per page load. After you pause it, other clicks will not restart it; use the music toggle to resume. Audio-load failures leave the game playable and show a retry message.
