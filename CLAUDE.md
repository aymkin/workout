# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal, single-page workout tracker for Alex — used on a phone in the gym to log sets/reps/RPE during a session and export the result as text. Published via **GitHub Pages** at https://aymkin.github.io/workout/ (public repo, branch `master`). It is a **PWA**: installs to the home screen, runs full-screen standalone, works offline.

All entered data lives in the browser (`localStorage`) and never leaves the device. The repo is the *published artifact*; the canonical training program and the logged history live in a separate **private** repo (`aymkin/assistant`, under `fitness-project/`). The whole point of the Export button is to produce text that gets pasted into a Claude chat, where Claude logs it into `fitness-project/logs/training/`.

## Architecture (the big picture)

`index.html` carries the CSS + engine JS inline (**no build step, no dependencies, no CDN**); the workout data lives in a separate **`workouts.json`** fetched at startup. Two conceptually separate layers:

1. **Data** — `workouts.json`, shape `{footer:[…], workouts:[…]}`, fetched once on load by `boot()` (`fetch("workouts.json", {cache:"no-store"})`). This is the *only* file that changes between sessions/cycles — `index.html` is not touched for a new session. Each `workouts[]` entry is one session: `{id, day, date, title, subtitle, location, groups}` (a per-session `footer` may override the shared top-level one). A `group` has `{name, hint?, exercises[]}`. An `exercise` carries display fields (`code, name, logName, weight, reps, rpe, sets`), a `def:{w,r,rpe}` prefill, and flags: `isNew` (⚙️ calibration badge), `dropset` + `drops:[…]`, `bodyweight`. Engine init is async — handlers (`setInterval`, button `onclick`) guard against `state`/`W` being undefined until `boot()` resolves; a fetch failure shows an error in `#main`.

2. **Engine** — the IIFE in `index.html` is fully generic and never hardcodes exercise data (it starts with empty `WORKOUTS`/`FOOTER`, filled by `boot`). It renders the selected workout, handles logging, timing, rest, and export. Key pieces:
   - **Session switcher** (`selectWorkout`/`renderSelector`): chips for each session in `WORKOUTS`; the active `id` is stored under `localStorage["workout-current"]`. Switching = how you view another day's plan or a past session's data ("history" is implicit, since each session persists separately).
   - **Per-session state** in `localStorage["workout-<id>"]`: `{sets:{<code>:[{w,r,rpe,t}]}, footer:{}, startedAt, finishedAt}`. Bodyweight exercises store `{t}`; dropsets store an array of `{w,r}` with `t` on element 0. `t` is a `Date.now()` timestamp stamped on every save.
   - **Row order** (`buildRows`): within a group, rows are emitted **round-major** — for supersets this interleaves `1A,1B,1A,1B,…` (execution order), not all-A-then-all-B. Each *set* is its own tappable row.
   - **Session clock**: a single Start button cycles Старт → «Завершить тренировку» → Возобновить. The **Export button is hidden until the session is finished**.
   - **Rest timer**: auto-starts 90s after logging a set; presets 30/45/60/90/120s; `buzz()` does best-effort vibrate + WebAudio beep at zero.
   - **Export** (`buildExport`): groups output by exercise (matching the fitness log template), prefixes the exercise `code`, marks empty sets `_×_`, and adds a timing header (`Старт · Финиш · N мин`) plus a `[mm:ss]` start-offset per exercise derived from timestamps.

3. **PWA layer**: `manifest.webmanifest` (`display: standalone`, icons), `sw.js` (service worker), and PNG icons. The SW is **network-first for navigations and `workouts.json`** (so the latest data always loads online) and cache-first for the rest, with an offline fallback to the cached copies. Both `index.html` and `workouts.json` are precached on install.

## Common tasks & commands

- **Edit a session / new cycle**: change `workouts.json` (ids, exercises, `def` prefills — taken from the session plan / prior calibration in the assistant repo). No need to touch `index.html`. A new `id` = a fresh `localStorage` key, so an unfinished prior session is never clobbered.
- **Bump the SW cache when JS/CSS/data logic changes**: edit `const CACHE = "workout-vN"` in `sw.js` (currently `v5`). Skipping this can serve stale assets to installed PWAs. (A pure `workouts.json` content edit doesn't strictly need a bump — it's network-first — but bump when changing engine code or the JSON *shape*.)
- **Deploy**: `git add -A && git commit && git push` (branch `master`). Pages rebuilds in ~1 min; URL is unchanged.
- **Verify the deploy is live** (Pages lags the push): poll the URL with a cache-busting query and grep for a string you just added, e.g.
  `curl -s "https://aymkin.github.io/workout/?v=1" | grep -c 'Day 2 Upper B'`
- **Regenerate icons**: `python3 make-icons.py` (needs Pillow). Produces `icon-{192,512}.png` (+ `-mask` maskable variants) and `icon-180.png` (apple-touch-icon). Edit the drawing in the script to change the design.

## Validation (there are no automated tests)

Validate by syntax-checking the embedded scripts and simulating logic with Node before deploying:

- `workouts.json`: `JSON.parse` it and check the shape (`footer` + `workouts[].groups[].exercises`).
- Syntax: extract each `<script>` and `new Function(code)` it — catches parse errors without a browser.
- Export format: pull `buildExport` and the timestamp helpers, feed a mock `state`, and print the output to confirm it still matches the log template (timing header, `code` prefix, `_×_` for empty, dropset `8×5 → …`).

Browser automation (claude-in-chrome) is usually not connected in these sessions, so tap/modal behavior is verified by the user on the live page after deploy.

## Conventions that aren't obvious

- `logName` (not `name`) is what appears in the export — keep it aligned with how sessions are written in the assistant repo's training log.
- Export must stay parseable as the "Шаблон фиксации" used in `fitness-project/logs/training/` — don't reformat it casually; Claude reads it back to log the session.
- Keep the file dependency-free and single-file. The repo intentionally does **not** use the Vite/React scaffold that exists in the assistant repo's `fitness-project/dashboard/`.
