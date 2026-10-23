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

### State meanings

| Variable | Range | Meaning |
|---|---|---|
| Time | 0–6 | Remaining intervals; coordinated endings in countdown stories require at least two |
| Resources | 0–3 | Spare equipment, workers, relays or coolant reserves |
| Trust | 0–3 | Team cooperation; required for the coordinated evidence route |
| Evidence | Named items | Discoveries that unlock a specific route |

Time records investigation, travel and consultation. Countdown stories make it an actual prerequisite: a coordinated ending requires two remaining intervals. Negotiation stories reward cooperation, while investigation stories allow a later consultation to recover missing trust. Time is never a live countdown, and reading slowly has no penalty. Values are clamped to their documented limits.

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

