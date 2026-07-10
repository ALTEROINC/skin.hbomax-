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
- Rows use a shared include, `HBM_Row_Landscape`, instantiated per row per hub in `Home.xml` with container ids 701–710 and `label_key`/`widget_key`/`visible_key`/`style_key` params pointing at skin strings like `hbm_homecfg_<hub>_row0N_label`.
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
