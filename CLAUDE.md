# CLAUDE.md

This file explains how this Kodi skin project is actually built and synced, and documents hard-won lessons from real debugging sessions so future work doesn't re-discover the same Kodi quirks the hard way.

## Project Identity

- Addon id: `skin.hbomax.dev` (name: "HBO Max Skin Dev")
- Kodi target: Omega 21.x
- This is the **real, active** project. Version is bumped automatically by CI on every push to `main` (see `.github/workflows/release.yml`, which bumps the patch version in `addon.xml` and commits `chore: bump version to X.Y.Z [skip ci]`). Do not hand-edit the version — just commit your actual change and push.

### Important: there is another, unrelated project directory

`/Users/michaelhernandez/Coding Projects/HBO Max Skin` (note the spaces, and no git repo) is a **stale, disconnected copy** with a different addon id (`skin.hbomax`) and a completely different `CLAUDE.md` describing a different architecture (pill/tab navigation model). It is NOT what Kodi actually runs and is not kept in sync with this repo. If a session ends up working in that directory, the changes will not reach the running skin. Always confirm you're in `HBOMAXSKIN` before editing.

## Build / Sync Workflow

Kodi reads the addon from:
```
~/Library/Application Support/Kodi/addons/skin.hbomax.dev/
```

After any edit, sync with the project's own script:
```bash
cd "/Users/michaelhernandez/Coding Projects/HBOMAXSKIN"
./sync.sh
```

**`sync.sh` only rsyncs specific file extensions** (currently `.xml`, `.png`, `.svg`, `.py`). If you add a new resource type (fonts, `.json`, etc.) and it isn't being picked up by the installed addon, check `sync.sh`'s `--include` list first — this bit us once already: a new Python script (`hero_rotate.py`) silently never reached the installed addon because `.py` wasn't in the include list, and `AlarmClock` kept firing an action against a file that didn't exist there, with no error until we found `ExecuteAsync - Not executing non-existing script ...` buried in the log.

After syncing, reload the skin in Kodi. Some changes (window `<onload>`/`<onunload>` timers like `AlarmClock`) may need a full Kodi restart, not just a skin reload, to re-register cleanly.

Kodi's log on this machine is at `~/Library/Logs/kodi.log`. It is the single most reliable source of truth for skin bugs — prefer checking it directly over guessing, especially for anything involving boolean expressions, actions, or scripts. Grep for `error`, `Keymapping error`, `Error parsing boolean expression`, or your own `xbmc.log(...)` output.

## Architecture Notes (as observed)

- `xml/Home.xml` is the main hub window. The active hub (Home / TV Shows / Movies / Live TV / My List) is tracked via `Skin.String(HBM.HomeActivePage)` (values: `home`, `tvshows`, `movies`, `livetv`, `mylist`).
- `Skin.String(HBM.ActiveRow)` tracks whether the hero is focused (`0`) or a specific row container id is focused (matches a container id like `701`).
- The hero area is a shared include, `HBM_Home_HeroShell` (defined in `xml/Includes.xml`), used across all hubs. Each hub has its own hero carousel panel: home=620, tvshows=621, movies=622, livetv=623, mylist=624. These panels are always mounted; the hero's backdrop/clearlogo/title/plot read from `Container(<id>).ListItem` for whichever hub is active.
- Rows use a shared include, `HBM_Row_Landscape_Large` (defined in `xml/Includes.xml`), instantiated per row per hub in `Home.xml` with container ids 701–710 and `label_key`/`widget_key`/`visible_key`/`style_key` params pointing at skin strings like `hbm_homecfg_<hub>_row0N_label`. Row up/down navigation does **not** use per-instance `nav_up`/`nav_down` params anymore — see lesson #12.
- `xml/Variables.xml` computes hero/row backdrop, clearlogo, title, plot, and section-label variables per hub/row — this is the most sensitive file for hero/row display logic.
- Widget/row configuration is done via `Custom_1111_HomepageConfig.xml` / `Custom_1112_HomeSlotEditor.xml` / `Custom_1113_WidgetSourcePicker.xml`, writing to `hbm_homecfg_*` skin strings (persisted in `userdata/addon_data/skin.hbomax.dev/settings.xml`).
- The search hub is `xml/Custom_1114_Search.xml` (window id 1114), with its own on-screen keyboard (not the OS/Kodi virtual keyboard).

## Hard-Won Kodi Lessons

These were each found via real debugging in this repo — don't re-litigate them.

### 1. Nested `grouplist` breaks D-pad navigation, even with explicit onup/ondown set

A vertical `grouplist` containing horizontal `grouplist` rows (a common "keyboard grid" pattern) will silently break navigation between rows, even when every button already has explicit `onup`/`ondown`/`onleft`/`onright` set. Kodi's automatic grouplist navigation conflicts with the explicit ids and the observed symptom is: only the first and last row are reachable, everything in between gets skipped.

**Fix:** flatten nested `grouplist`s into plain `group` containers with explicit `left`/`top` positions and full explicit `onup`/`ondown`/`onleft`/`onright` on every control. `group` (unlike `grouplist`) has no automatic navigation to conflict with. Applied in both `Custom_1114_Search.xml` and `DialogKeyboard.xml`.

### 2. `$VAR[...]` cannot be used inside a boolean condition function in `<visible>`/`<condition>`

Something like `<visible>!String.IsEmpty($VAR[HBM_Hero_Logo])</visible>` will fail to parse — confirmed directly via `kodi.log`: `Error parsing boolean expression !string.isempty($var[hbm_hero_logo])`. This is true regardless of which function wraps it (`String.IsEmpty`, `String.IsEqual`, etc.) and regardless of whether it's the only term or combined with `+`/`|`. An unparseable condition silently evaluates to `false` — so both a control gated on the condition AND its "opposite" fallback control (gated on the negation) can end up hidden simultaneously, which looks like "nothing renders" with no error visible in the UI.

`$VAR[...]` **does** work fine as: plain `<label>`/`<texture>` content, and nested inside another variable's own `<value condition="...">` in `Variables.xml`.

**Fix:** when you need to gate visibility on whether a variable's value is empty, inline the actual underlying info-label logic directly into the `<visible>` tag instead of wrapping the variable. Verbose, but it's the reliable path — matches the project's existing "explicit over generic" pattern for row visibility.

### 3. `Container(id).GoNext` / `Container.Next(id)` are not real Kodi actions

Both look plausible and one is even already used elsewhere in this codebase (Play button's manual hero browsing) — but neither is a real Kodi built-in. Confirmed via `kodi.log`: `Keymapping error: no such action 'container(621).gonext' defined`. There is no built-in skin action to advance a specific container's selection by id without it holding focus.

### 4. `<autoscroll>` on a panel/list does not run for a container that never holds real GUI focus

The official Kodi wiki example uses `!Control.HasFocus(id)` as the enabling condition, which looks like proof it works while unfocused — but that's for controls that are *sometimes* focused and pause autoscroll only while a user is actively browsing them. A container that is designed to *never* receive real focus (e.g. a background hero carousel) does not autoscroll at all, confirmed by polling `Container(id).ListItem.Label` every cycle across 30+ seconds with zero change.

### 5. The working pattern for auto-rotating a carousel that must never visibly steal focus

See `resources/scripts/hero_rotate.py`, driven by `AlarmClock(...,RunScript(...),00:00:14,silent,loop)` in `Home.xml`'s `<onload>`:
1. Read `Container(id).CurrentItem` and `Container(id).NumItems` via `xbmc.getInfoLabel(...)` — reliable, reads through the same info manager the skin itself uses.
2. Compute the next position.
3. `xbmc.executebuiltin('SetFocus(id,position)')` to move the selection — **`position` is 0-based**, while `Container(id).CurrentItem` is 1-based. Convert between them.
4. Immediately `xbmc.executebuiltin('SetFocus(<whatever had focus before, e.g. Play/More Info button id>)')` to restore focus, so nothing visibly steals input from the user.

Do **not** use `xbmcgui.Window(id).getControl(id).size()`/`.selectItem()` from a `RunScript`-invoked Python script to read or drive a skin's own natively-defined content-bound container — it reliably reports `size()==0` even when the container demonstrably has real, visible content. Use `xbmc.getInfoLabel('Container(id).XXX')` instead.

### 6. `itemlayout`/`focusedlayout` template swap requires real focus too

The same focus dependency from #4/#5 applies to a panel's `itemlayout` vs `focusedlayout` template selection — it only shows the "focused" template while the container holds real GUI focus, and does not persist a "last selected" visual once focus moves elsewhere. If you need to show "which item is current" while real focus intentionally lives elsewhere (e.g. carousel dots while focus stays on Play/More Info), don't rely on `itemlayout`/`focusedlayout` at all — drive it explicitly with a `Skin.String` your script sets, and per-position `<visible>String.IsEqual(Skin.String(...),N)</visible>` checks, same "explicit over automatic" pattern as everywhere else in this file.

### 7. `<content limit="N">` can still yield more than N items

Observed: `limit="6"` on a hero panel's `<content>`, but `Container(id).NumItems` reported `7`, with the trailing item rendering blank. Don't trust `NumItems` blindly for bounds — cap any position math to the intended limit explicitly.

### 8. Panels/lists inside a hidden parent `<group>` do not load their `<content>`

Wrapping a `<control type="panel">` or `<control type="list">` in a parent `<control type="group">` with a `<visible>` condition prevents the container from initializing its content if the group starts invisible. The panel physically disappears from the render tree until the group becomes visible, by which point the content fetch may never have started. This means the hero carousel panels (620–624) **must keep their own individual `<visible>` tags** — do not try to consolidate their visibility check into a parent group as a performance optimization. Plain `<group>` controls containing only images/labels are safe to consolidate.

### 9. Debouncing rapid keystrokes: use `AlarmClock`, never a `RunScript` per keystroke

The on-screen search keyboard (`Custom_1114_Search.xml`) originally fired a plugin search query on every single keypress, making live TMDB search feel extremely slow (multiple network calls per letter typed). The fix is to debounce: only commit the search term after a pause in typing. The **wrong** way to do this is spawning a `RunScript` per keystroke that itself sleeps ~600ms before committing — this still launches one new Python interpreter *per key*, and on a weak Android box, spawning that many interpreters back-to-back is itself slow enough to reproduce the exact same symptom you were trying to fix.

**Fix:** call the native `AlarmClock(name,command,time,silent,loop)` builtin directly from each key's `onclick` (no Python involved at all for resetting the timer — re-arming an alarm with the same name cancels and replaces the pending one, for free, in C++). Only when the alarm actually *fires* (i.e., typing has paused) does it run `RunScript(...)`, so a burst of N keystrokes spawns at most one script process, not N. See `resources/scripts/search.py` and the `AlarmClock(hbmsearchdebounce,...)` calls in `Custom_1114_Search.xml`.

### 10. `plugin.video.themoviedb.helper`'s `RunScript` route names must match its routing table exactly, or it crashes

`RunScript(plugin.video.themoviedb.helper, <token>, key=value, ...)` parses bare (non-`key=value`) tokens as boolean flags (`self.params[token] = True`), then does `route_taken = set.intersection(routes_available, params_given).pop()`. If **none** of the params you passed (bare tokens or keys) are a real route name, that intersection is empty and `.pop()` throws `KeyError: pop from an empty set` — this crashed on *every* return from full-screen video (see `xml/VideoFullScreen.xml`), because `open_info` was never a valid route. There is no such thing as a "soft fail" here — an invalid route name is a guaranteed crash, logged as a Python traceback in `kodi.log`, not a silent no-op.

Known-bad → known-good route names found so far in this codebase:
- `open_info` → not a route at all. To reopen the (skinned) native video info dialog for a known TMDb id/type, use `add_tmdb=<id>,tmdb_type=<type>,call_auto=12003` (`12003` = Kodi's native `WINDOW_DIALOG_VIDEO_INFO`, which `DialogVideoInfo.xml` restyles — no explicit `id` attribute needed in that XML file since Kodi maps the reserved filename to the window id automatically).
- `configure_players` → real route is `customise_players` (British spelling).

Before wiring up any new `RunScript(plugin.video.themoviedb.helper, ...)` call, verify the route name against the addon's actual `resources/tmdbhelper/lib/script/router.py` routing table (or its GitHub source) rather than guessing from older docs/examples.

### 11. Kodi's boolean expression parser silently fails on deeply nested `+`/`|` mixes — and there's no XML-validity signal for it

A `<visible>`/`<condition>` expression like `(A + (B | C | D)) | (E + (F | G | H)) | ...` (enumerating many parenthesized AND-of-OR groups joined by `|`) is syntactically fine as XML and *looks* like valid boolean algebra, but Kodi's parser can throw `unmatched parentheses in ...` and/or `Misplaced !` on it even when parens are provably balanced — confirmed via `kodi.log`, not guessable from the XML alone. A failed condition parse evaluates to `false` silently — there is no in-UI indicator, so the symptom is just "this control/logo never shows."

The same failure shows up in miniature as `A | (!B + !C)` (a single `!`-led parenthesized group as one side of a top-level `|`).

**Fixes that are proven to work in this codebase, in order of preference:**
1. Simplify the underlying logic so each expression is a **flat chain of one operator type** — either all `+` or all `|`, never mixed with nested parens (this is the pattern every working `<value condition="...">` in `Variables.xml` already uses, e.g. `HBM_Row_Logo`). If you're checking "the currently-focused row/container's item has property X," you often don't need to enumerate every possible container id at all — unqualified `ListItem.*` already refers to whichever container currently holds real GUI focus (see lesson #4/#5 on what "real focus" means), matching the existing `HBM_Hero_Backdrop`-style fallback-art variables.
2. If you must combine `+` and `|` in one expression, use **square-bracket grouping instead of parentheses** for the `|`-joined clauses (e.g. `A | [!B + !C]`) — this is a real, documented Kodi grouping syntax distinct from `()`, and it parses correctly where the parenthesized equivalent did not. Used in `DialogVideoInfo.xml`'s resumable/season checks.

### 12. Multiple conditioned `<onup>`/`<ondown>` tags do **not** reliably pick "the first true condition" when their content is a builtin call

`onclick`/`onfocus` support multiple tags with different `condition` attributes, evaluated in order, and this is used successfully all over this codebase. It is tempting to assume `onup`/`ondown`/`onleft`/`onright` behave the same way — they parse the same way (`GetActions`, same `CGUIAction` list) — but **real on-device testing showed navigation resolution does not honor the first true condition** when each entry's content is a builtin call like `Control.SetFocus(...)` rather than a bare control id: navigation consistently fell through to the *last* (usually the unconditioned fallback) entry regardless of which earlier condition was actually true. Symptom: a cascading "skip to the next visible row" scheme via several conditioned `<ondown>` tags on one row control made every row's down-press self-loop, and every row's up-press jump straight to the fallback target.

**Fix:** don't branch inside `onup`/`ondown` at all. Precompute the correct target as a single value in `Variables.xml` (using the flat, proven-safe condition style from lesson #11), then give the control exactly **one** plain `onup`/`ondown` that references it: `<ondown>Control.SetFocus($VAR[HBM_RowDownTarget_$PARAM[id]],...)</ondown>`. `$VAR[...]` works fine here because it's a plain builtin parameter, not a boolean condition (that restriction is lesson #2, and it doesn't apply to this position). See `HBM_RowDownTarget_701`..`_710` / `HBM_RowUpTarget_701`..`_710` in `Variables.xml`, which is what actually makes Home-hub row navigation skip past rows that are hidden or have no widget configured yet.

### 13. Native Kodi windows (`AddonBrowser.xml`, `DialogAddonInfo.xml`, `DialogSelect.xml`) route clicks by control **id**, not by `onclick`

For windows Kodi implements in C++ (the Add-on Browser, the Add-on Info dialog, the generic Select dialog, etc.), the skin does not need — and in several cases must not rely on — an `onclick` attribute for the control to do anything. Kodi's C++ window class reads fixed, documented control ids and wires up their behavior natively at runtime. Concretely:
- `AddonBrowser.xml`: id `9` = trigger `CServiceBroker::GetRepositoryUpdater().CheckForUpdates()` ("Check for Updates"), `7`/`8` = the foreign/broken addon filter toggles, `5` = addon settings. A skin that reinvents this sidebar with its own arbitrary ids (as this project's did, before it was fixed) silently loses access to update-checking entirely — the buttons render and are focusable, but clicking them does nothing, because Kodi is listening for `5`/`7`/`8`/`9`, not whatever ids the skin invented.
- `DialogAddonInfo.xml`: ids `6`/`7`/`8`/`9`/`10`/`12`/`13`/`14` are Kodi-managed action buttons (Kodi sets their label/visibility/selected-state at dialog-open time); they need no `onclick`.
- `DialogSelect.xml`: control id `3` is the plain single-line list; id `6` is a *second*, independently-toggled list for two-line items (`Label`/`Label2`) — used for things like the addon "Versions" picker. Kodi shows/hides `3` vs `6` internally based on whether the current selection needs two lines; **don't make `id="6"` a `textbox`** (it must be `type="list"`) or that picker silently renders as a blank box for every addon.

When customizing one of these reserved-filename windows, check Kodi's own `skin.estuary` source for the control ids it uses before inventing new ones — matching Estuary's ids is what makes the C++ side's native behavior work at all.

## Known Issues / Open Investigations

- **TV show info dialog is slow to show the correct season/episode, and season/episode lists are slow to populate.** Root cause: this skin has no local Kodi video library for this content — `DialogVideoInfo.xml` sources seasons/episodes/"next up" live from `plugin.video.themoviedb.helper` (TMDB + Trakt) on every dialog open, unlike stock Estuary's typical flow which reads from a local scraped library DB and is therefore near-instant regardless of skin. `kodi.log` has shown `TraktSyncLastActivities.Locked Timeout!` (TMDb Helper's own periodic background Trakt resync colliding with the on-demand lookup) and a one-time `Trakt authorization check took ~15s` per session. A known upstream TMDb Helper issue (Android-specific) attributes slow list population specifically to its fanart.tv lookup feature; disabling TMDb Helper's own **"fanart.tv – use for plugin artwork"** setting (Addon settings, not this skin's XML) is the current best lead and testing suggested it removes the live-network log activity that used to show up around `DialogVideoInfo.xml` opens. Not fully confirmed yet — still need a test run with matched wall-clock timestamps (when the dialog opened vs. when it visibly corrected from S1E1 to the real episode) to prove the fix and rule out the "only populates after scrolling into the seasons panel" behavior being a separate lazy-load quirk.
