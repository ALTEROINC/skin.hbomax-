import math
import time

import xbmc
import xbmcgui

# Drives the thin loading line in DialogVideoInfo's episode section.
#
# The episode list (panel 501) is fetched from TMDb Helper for whichever season
# HBM_Dlg_EpSeason resolves to. Kodi keeps showing the previous list until the
# new one arrives, so this script compares the season that is *requested* with
# the season of the list that is actually *there*:
#   - they differ  -> loading: HBM.EpLoading=1 and HBM.EpBarW creeps toward full
#   - they match   -> loaded: bar snaps to full, then HBM.EpLoading is cleared
#                     and the XML fades the line out and the list in.
#
# HBM.EpPoller is the fail-safe: the XML only hides the list / shows the line
# while it is set, and it is cleared on exit, so a dead script can never leave
# the episodes hidden.
#
# It also keeps the season strip (panel 502) positioned on the requested season,
# so focusing the strip lands on the season the list is showing. Kodi only moves
# a container's selection by giving it focus, so this briefly focuses the strip
# and hands focus straight back (same trick as hero_rotate.py). HBM.EpSync is set
# around that so 502's onfocus side effects (ReturnFocus, stopping the trailer)
# are skipped.
#
# Requested season mirrors the HBM_Dlg_EpSeason variable in Variables.xml —
# keep the two in sync.

HOME = 10000
TICK = 0.1
BAR_FULL = 200        # px; must match the line's width in DialogVideoInfo.xml
CREEP_MAX = 0.92      # share of the bar the creep may reach before data arrives
CREEP_TAU = 4.0       # seconds; larger = slower creep
TIMEOUT = 90          # give up (and reveal whatever is there) after this long
FINISH_HOLD = 0.25    # let the full bar show briefly before it fades
CLOSED_GRACE = 2.0    # dialog may flicker between windows; exit after this long


def log(msg):
    xbmc.log('[episodes_loading] ' + msg, level=xbmc.LOGINFO)


def requested_season():
    if xbmc.getInfoLabel('Skin.String(HBM.SeasonChosen)') == '1':
        return xbmc.getInfoLabel('Skin.String(HBM.CurrentSeason)')
    up_next = xbmc.getInfoLabel('Container(510).ListItemAbsolute(0).Season')
    return up_next or xbmc.getInfoLabel('Skin.String(HBM.CurrentSeason)')


def strip_position(season):
    """0-based position of `season` in the season strip, or None if not there (yet)."""
    try:
        total = int(xbmc.getInfoLabel('Container(502).NumItems'))
    except ValueError:
        return None
    for i in range(min(total, 60)):
        if xbmc.getInfoLabel('Container(502).ListItemAbsolute(%d).Season' % i) == season:
            return i
    return None


def sync_strip(season):
    """Select `season` in the strip without leaving the user's focus moved.
    Returns True once the strip is on that season (or the user is driving it)."""
    if xbmc.getCondVisibility('Control.HasFocus(502)'):
        return True  # user is browsing seasons; don't fight them
    if not xbmc.getCondVisibility('Control.IsVisible(502)'):
        return False
    pos = strip_position(season)
    if pos is None:
        return False  # strip hasn't loaded yet; try again next tick
    if xbmc.getInfoLabel('Container(502).CurrentItem') == str(pos + 1):
        return True
    previous = xbmc.getInfoLabel('System.CurrentControlID')
    if not previous:
        return False
    # Queued in order on the GUI thread, so EpSync is still set when 502's
    # onfocus handlers run and is cleared only after focus is handed back.
    xbmc.executebuiltin('SetProperty(HBM.EpSync,1,home)')
    xbmc.executebuiltin('SetFocus(502,%d)' % pos)
    xbmc.executebuiltin('SetFocus(%s)' % previous)
    xbmc.executebuiltin('ClearProperty(HBM.EpSync,home)')
    log('strip moved to season %s (position %d), focus back on %s' % (season, pos, previous))
    return True


def main():
    win = xbmcgui.Window(HOME)

    # Only one poller at a time (the dialog's onload fires on every open).
    beat = win.getProperty('HBM.EpPoller')
    if beat and time.time() - float(beat) < 2:
        return

    monitor = xbmc.Monitor()
    loading = False
    started = 0.0
    closed_since = None
    last_w = None
    strip_synced = None  # season the strip is already positioned on
    gave_up = None  # (requested, have) we already timed out on; don't restart the line for it

    def heartbeat():
        win.setProperty('HBM.EpPoller', str(time.time()))

    def set_width(w):
        nonlocal last_w
        w = int(w)
        if w != last_w:
            win.setProperty('HBM.EpBarW', str(w))
            last_w = w

    def finish():
        nonlocal loading
        set_width(BAR_FULL)
        monitor.waitForAbort(FINISH_HOLD)
        win.clearProperty('HBM.EpLoading')
        loading = False

    heartbeat()
    try:
        while not monitor.abortRequested():
            heartbeat()

            if not xbmc.getCondVisibility('Window.IsActive(movieinformation)'):
                closed_since = closed_since or time.time()
                if time.time() - closed_since > CLOSED_GRACE:
                    break
                if monitor.waitForAbort(TICK):
                    break
                continue
            closed_since = None

            want = requested_season()
            if want and want != strip_synced and sync_strip(want):
                strip_synced = want

            if not xbmc.getCondVisibility('Control.IsVisible(501)'):
                # Movie, or the "You May Also Like" tab is showing instead.
                if loading:
                    win.clearProperty('HBM.EpLoading')
                    loading = False
            else:
                req = requested_season()
                have = xbmc.getInfoLabel('Container(501).ListItemAbsolute(0).Season')
                loaded = bool(req) and have == req

                if loaded:
                    if loading:
                        finish()
                elif (req, have) == gave_up:
                    pass
                else:
                    if not loading:
                        loading = True
                        started = time.time()
                        set_width(0)
                        win.setProperty('HBM.EpLoading', '1')
                    elapsed = time.time() - started
                    if elapsed > TIMEOUT:
                        log('gave up waiting for season %r (list shows %r)' % (req, have))
                        gave_up = (req, have)
                        finish()
                        monitor.waitForAbort(TICK)
                        continue
                    set_width(BAR_FULL * CREEP_MAX * (1 - math.exp(-elapsed / CREEP_TAU)))

            if monitor.waitForAbort(TICK):
                break
    finally:
        win.clearProperty('HBM.EpLoading')
        win.clearProperty('HBM.EpBarW')
        win.clearProperty('HBM.EpPoller')
        win.clearProperty('HBM.EpSync')


main()
