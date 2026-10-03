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
#   - they differ  -> loading: HBM.EpLoading=1 (list fades out) and HBM.EpBar=1
#                     (line shown); HBM.EpBarN (segments lit) creeps toward full
#   - they match   -> loaded: HBM.EpLoading is cleared at once so the list fades
#                     in with no added delay, while the line sweeps the rest of
#                     the way to full and then fades out (HBM.EpBar cleared).
#
# The creep adapts to this device: the time the last loads took is remembered
# (HBM.EpExpected) and the line is paced to reach ~90% in about that long, so it
# fills across a quick load and a slow one alike instead of using a fixed speed.
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
TICK = 0.05
BAR_FULL = 240        # px; the line is BAR_FULL / SEGMENT_PX segments in DialogVideoInfo.xml
SEGMENT_PX = 6        # px per segment; must match the segment images in DialogVideoInfo.xml
CREEP_MAX = 0.92      # share of the bar the creep may reach before data arrives
EXPECTED_DEFAULT = 1.5   # seconds a load is assumed to take until we've seen one
EXPECTED_MIN = 0.4
EXPECTED_MAX = 8.0
TIMEOUT = 90          # give up (and reveal whatever is there) after this long
RAMP_SECONDS = 0.3    # final sweep to a full bar once the list has arrived
FINISH_HOLD = 0.15    # full bar stays this long before it fades
CLOSED_GRACE = 2.0    # dialog may flicker between windows; exit after this long


def log(msg):
    xbmc.log('[episodes_loading] ' + msg, level=xbmc.LOGINFO)


def requested_season():
    if xbmc.getInfoLabel('Skin.String(HBM.SeasonChosen)') == '1':
        return xbmc.getInfoLabel('Skin.String(HBM.CurrentSeason)')
    up_next = xbmc.getInfoLabel('Container(510).ListItemAbsolute(0).Season')
    return up_next or xbmc.getInfoLabel('Skin.String(HBM.CurrentSeason)')


def load_expected(win):
    try:
        return min(EXPECTED_MAX, max(EXPECTED_MIN, float(win.getProperty('HBM.EpExpected'))))
    except ValueError:
        return EXPECTED_DEFAULT


def remember_duration(win, expected, took):
    """Blend how long this load took into the pace for the next one."""
    expected = min(EXPECTED_MAX, max(EXPECTED_MIN, 0.5 * expected + 0.5 * took))
    win.setProperty('HBM.EpExpected', '%.2f' % expected)
    return expected


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
    expected = load_expected(win)
    bar_on = False
    strip_synced = None  # season the strip is already positioned on
    gave_up = None  # (requested, have) we already timed out on; don't restart the line for it

    def heartbeat():
        win.setProperty('HBM.EpPoller', str(time.time()))

    def set_width(w):
        nonlocal last_w
        w = int(w)
        if w != last_w:
            win.setProperty('HBM.EpBarN', str(w // SEGMENT_PX))
            last_w = w

    def end_bar():
        nonlocal bar_on
        win.clearProperty('HBM.EpBar')
        bar_on = False

    def finish():
        """List is here: reveal it immediately, let the line sweep to full and fade."""
        nonlocal loading
        win.clearProperty('HBM.EpLoading')
        loading = False
        start_w = last_w or 0
        steps = max(1, int(RAMP_SECONDS / TICK))
        for i in range(1, steps + 1):
            set_width(start_w + (BAR_FULL - start_w) * (i / steps))
            if monitor.waitForAbort(TICK):
                return
        monitor.waitForAbort(FINISH_HOLD)
        end_bar()

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
                if bar_on:
                    end_bar()
            else:
                req = requested_season()
                have = xbmc.getInfoLabel('Container(501).ListItemAbsolute(0).Season')
                loaded = bool(req) and have == req

                if loaded:
                    if loading:
                        expected = remember_duration(win, expected, time.time() - started)
                        finish()
                elif (req, have) == gave_up:
                    pass
                else:
                    if not loading:
                        loading = True
                        started = time.time()
                        set_width(0)
                        win.setProperty('HBM.EpBar', '1')
                        bar_on = True
                        win.setProperty('HBM.EpLoading', '1')
                    elapsed = time.time() - started
                    if elapsed > TIMEOUT:
                        log('gave up waiting for season %r (list shows %r)' % (req, have))
                        gave_up = (req, have)
                        finish()
                        monitor.waitForAbort(TICK)
                        continue
                    # 1 - e^-2.3 is ~0.9: reach ~90% of the creep range in `expected` seconds
                    set_width(BAR_FULL * CREEP_MAX * (1 - math.exp(-2.3 * elapsed / expected)))

            if monitor.waitForAbort(TICK):
                break
    finally:
        win.clearProperty('HBM.EpLoading')
        win.clearProperty('HBM.EpBar')
        win.clearProperty('HBM.EpBarN')
        win.clearProperty('HBM.EpPoller')
        win.clearProperty('HBM.EpSync')


main()
