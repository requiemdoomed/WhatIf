# Anthology Edition — verification report

Author: Swayam Shakya  
Date: October 23, 2026

## Content and route verification

| Measure | Verified result |
|---|---:|
| Playable scenarios | 105 |
| Scenes | 955 |
| Reachable endings | 315 |
| Complete decision routes | 2,135 |
| Decisions exercised across those routes | 8,670 |
| Original bundled instrumental scores | 11 |

Every route was traversed by the pure engine and also executed through the Flask decision endpoints. Each resulting snapshot and ending was compared with the expected result. The validator rejects missing targets, duplicate choice IDs, invalid conditions, cycles, unreachable scenes/endings, unusable choices and reachable states with no available action.

`ROUTE_MANIFEST.json` contains a content hash and one executable choice sequence for every ending of every scenario. `CATALOGUE.md` lists all 105 titles, genres, structures and route counts. The original five stories' definitions were compared with the previous release: existing rules and content are unchanged; only metadata was added.

The 100 additional episodes have distinct authored openings and ending prose. They use three shared structures: investigation, negotiation and countdown. This is an anthology of short interactive episodes, not a claim that every story uses a unique engine or unrelated graph topology.

## Automated backend checks

**40 tests passed**, including a second complete run from the notebook's executable cells. Coverage includes:

- Catalogue uniqueness, every reachable route, ending witnesses and current manifest hashes.
- Time-sensitive outcomes, cooperation requirements, evidence, bounded state and input immutability.
- Session ownership, request verification, malformed input and invalid transitions.
- Duplicate and concurrent submissions: exactly one decision is committed.
- Checkpoints, replay, branch creation, later divergence and original-route preservation.
- Actual discoveries, achievements and inherited hint use.
- Persistent progress after restart, repeatable initialisation, local signing keys and profile-scoped reset.
- Compact catalogue responses, complete on-demand journey detail and static audio delivery.
- Real loopback HTTP server start, repeated start, stop, restart and occupied-port errors.
- All audio files: valid stereo PCM, expected duration/sample rate, nonzero signal, distinct bytes, unclipped samples and quiet loop boundaries.

The regression suite takes longer than the application startup because it writes and verifies every supported route in temporary databases.

## Browser checks

Both `tests/browser_smoke.py` and `tests/browser_anthology.py` passed in headless Chromium 134 with Playwright 1.51.0.

The baseline workflow checks desktop and mobile navigation, search, category filtering, sorting, a completed original story, a different alternate route, locked choices, comparison, checkpoints, reload/resume, hints, restart cancellation, achievements, themes, readability, reset confirmation and keyboard activation.

The anthology workflow additionally checks:

- All 105 distinct scenario cards across nine pages, with no duplicates or missing titles.
- Murder-mystery content notes and saved favourites that survive reloads.
- The opening score after an explicit entrance click.
- All ten genre scores loaded and decoded in the browser.
- Measurable nonzero Web Audio output, volume-zero silence, volume restoration, pause and restart.
- Crossfade cleanup and a decoded-buffer cache limited to three scores.
- Audio suspend/resume under a simulated document-visibility event.
- All three endings in a representative story from each new structure: nine completed browser routes.
- A deliberately failed audio request: music pauses honestly and story play remains available.
- A narrow mobile player and graph without page-width overflow.

A saved-favourite/filter timing issue was found during testing and fixed by updating bookmarks synchronously without reloading the catalogue. Audio-load failure handling was also tightened so controls cannot indicate silence while an old track continues playing.

No uncaught page errors occurred during the successful workflows. Digital audio output was measured; subjective listening quality and physical speaker/headphone behavior were not assessed. Mobile emulation and simulated visibility are not physical-device tests.

## Performance measurements

`PERFORMANCE.json` records one local run with 105 saved journeys:

- Complete engine traversal: about **155 ms** for 8,670 transitions.
- Cold application creation: about **143 ms**.
- Median compact bootstrap response: about **4.8 ms** over 15 requests.
- Equivalent JSON payload reduced from **218,451** to **96,314 bytes**, approximately **55.9%**, by loading history on demand.

These measurements describe this environment, not guaranteed timings on another computer. Browser rendering is bounded to twelve catalogue cards and fifteen journey rows per batch. Scenario validation is cached per process, and unchanged catalogue definitions do not incur replacement writes at every startup.

## Notebook and portability

The notebook passes `nbformat` validation. Every code cell executed successfully in order in one Python namespace: locate files, check dependencies, initialise the expanded catalogue, start the real server, run all 40 tests and stop cleanly.

A full Jupyter-kernel launch was attempted but blocked by this environment's kernel socket restrictions. Consequently, the notebook frontend/kernel combination remains unverified here. The server and browser workflows use the same launch helper and were exercised independently.

Native Windows and macOS runs were not available. Installation instructions use portable Python APIs and explicit virtual-environment executables. Safari, Firefox, physical mobile devices, long-running soak tests and recovery from externally corrupted databases were not tested.

## Reproduce

```bash
python -m unittest discover -s tests -v
python -m engine.story_validator
python tools/verify_catalogue.py
python tools/benchmark.py
```

Optional browser tools are separate from the application requirements:

```bash
python -m pip install playwright
python -m playwright install chromium
python tests/browser_smoke.py
python tests/browser_anthology.py
```

Passing these checks establishes the tested behavior; it is not a claim that software can be universally error-free.

## Atmosphere edition regression

The expanded suite passed **43 tests**, including artwork coverage for every scenario, valid standalone SVG assets, absence of active/remote SVG content, and distinct genre illustrations. The original 40-test suite also passed after recomposing the audio. The full route checks still cover 2,135 endings-reaching paths.

Chromium gameplay and anthology regressions passed again: desktop/mobile gameplay, bookmarks, audio output, actual mute/volume, pause/resume, all ten genre scores, failed-audio recovery, and bounded audio cache. A separate browser pass loads the matching banner for all 105 scenarios and checks ten profiles in light/dark mode at 1440px and 390px widths for horizontal overflow and browser errors. Visual review covers the updated home and player screens. Audio checks establish decoded signal and control behavior; perceived immersion is subjective and was not a listening-panel assessment.

Additional command: `python tests/browser_atmosphere.py`.

## First-interaction music update

The browser regression now checks music unlocking from an ordinary page click, touchscreen tap and keyboard input, with no entrance dialog. It also checks that an ordinary click after manual pause leaves audio paused, and that initial audio download failure leaves the homepage usable. The previous entrance-dialog checks are superseded by these checks.

## Root index and complete-project launcher edition

**51 Python tests passed**, including eight new checks for `/index.html`, the canonical document, entry assets, platform environment paths, browser-launch arguments, notebook launch arguments, custom ports, setup failure and invalid-port handling. All 2,135 routes remain covered by the backend regression suite. Four dependency-free JavaScript entry-loader checks passed: local-file startup guidance, HTTP and HTTPS script order, and missing-script recovery. Shell syntax and JavaScript syntax checks passed; the notebook passes structural validation.

The real launcher was exercised on Linux: it created `.venv`, installed Flask, started the server and subsequently reused that environment. A live HTTP integration check loaded `/` and `/index.html`, every entry script, CSS, opening music and artwork, then read the 105-story catalogue, made a decision and reloaded the saved journey successfully. The server was stopped after verification.

A new managed browser preview was attempted but its runtime did not expose Python. Consequently, this edition's visual browser behavior was not freshly verified; the preceding audio/theme editions' browser results above are historical. Native Windows/macOS execution and a full Jupyter frontend/kernel launch remain unverified. Windows/macOS launch argument construction is covered by automated tests. Opening a local HTML file intentionally shows guidance rather than attempting to execute Python inside the browser.

Reproduce the additional entry checks with `node tests/test_entry.js` (Node.js is optional and needed only for this developer test). Normal play needs only Python and a browser.
