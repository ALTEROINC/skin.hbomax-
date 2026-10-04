import time

import xbmc
import xbmcgui

# Continuous scroll for the genre browser (window 1116).
#
# The grid's list is TMDb Helper's genre listing asking for HBM.GenreLen pages merged into one list
# (20 items each; see HBM_GenreSource). This poller grows HBM.GenreLen by STEP pages when focus
# gets within TRIGGER items of the end, so more titles appear below as you scroll and nothing beyond
# what you reach is ever requested. TMDb Helper caches each page, so growing only fetches the new ones.
#
# Growing changes the list's URL and Kodi reloads it. Kodi normally keeps the selected position, but if
# the selection snapped back toward the top the poller puts it back.

HOME = 10000
PANEL = 800
PER_PAGE = 20
STEP = 2             # pages added per growth
MAX_LEN = 20         # at most 400 titles per genre (keeps the list light on this device)
TRIGGER = 13         # grow when this close to the last item (a bit over two rows of six)
MISSING_OK = 4       # a page can come back a few items short without meaning "no more pages"
POLL_SECONDS = 0.3
LOAD_TIMEOUT = 25    # give up waiting for a growth to arrive after this long
CLOSED_GRACE = 2.0
PROP = 'HBM.GenrePoller'


def log(msg):
    xbmc.log('[genre_scroll] ' + msg, level=xbmc.LOGINFO)


def num(info, default=0):
    try:
        return int(xbmc.getInfoLabel(info))
    except ValueError:
        return default


def main():
    win = xbmcgui.Window(HOME)
    beat = win.getProperty(PROP)
    if beat and time.time() - float(beat) < 2:
        return  # one poller at a time

    monitor = xbmc.Monitor()
    closed_since = None
    pending = None   # (target item count, started, position before growth)
    try:
        while not monitor.abortRequested():
            win.setProperty(PROP, str(time.time()))

            if not xbmc.getCondVisibility('Window.IsActive(1116)'):
                closed_since = closed_since or time.time()
                if time.time() - closed_since > CLOSED_GRACE:
                    break
                if monitor.waitForAbort(POLL_SECONDS):
                    break
                continue
            closed_since = None

            length = num('Skin.String(HBM.GenreLen)', 2)
            total = num('Container(%d).NumItems' % PANEL)
            cur = num('Container(%d).CurrentItem' % PANEL)   # 1-based

            if pending:
                target, started, saved = pending
                if total >= target - MISSING_OK or time.time() - started > LOAD_TIMEOUT:
                    if saved and cur < saved - 2:
                        xbmc.executebuiltin('SetFocus(%d,%d,absolute)' % (PANEL, saved - 1))
                        log('selection had reset to %d, restored to %d' % (cur, saved))
                    pending = None
            elif total and length < MAX_LEN and total >= length * PER_PAGE - MISSING_OK and cur >= total - TRIGGER:
                length = min(MAX_LEN, length + STEP)
                xbmc.executebuiltin('Skin.SetString(HBM.GenreLen,%d)' % length)
                pending = (length * PER_PAGE, time.time(), cur)
                log('near the end (%d of %d): now requesting %d pages' % (cur, total, length))

            if monitor.waitForAbort(POLL_SECONDS):
                break
    finally:
        win.clearProperty(PROP)


main()
