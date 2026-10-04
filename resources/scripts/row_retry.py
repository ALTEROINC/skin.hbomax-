import time

import xbmc
import xbmcgui

# One-shot retry for Trakt-backed rows that missed the startup token refresh.
#
# At launch every row requests its content right away. If the saved Trakt
# token has expired, TMDb Helper needs several seconds to refresh it, and any
# Trakt row requested in that window comes back empty. Kodi never re-requests
# a failed row on its own, so it stays empty.
#
# A row is retried (once per Kodi session) only when, on the page being viewed:
#   - every non-Trakt row that is configured and visible has items, and
#   - one or more Trakt rows have none.
# If other rows are still empty or still loading, nothing is retried, so a
# slow load is never mistaken for a Trakt failure.
#
# The retry changes the row's content URL by setting a non-persistent Home
# window property, which Includes.xml appends to the widget path. Kodi
# re-requests a container whenever its content URL changes.

POLL_SECONDS = 3
MAX_SECONDS = 300
STABLE_POLLS = 2   # condition must hold this many polls in a row
HUBS = ('home', 'tvshows', 'movies', 'mylist')
ROWS = range(1, 12)
HOME = 10000
RUN_PROP = 'HBM.RowRetryStarted'


def log(msg):
    xbmc.log('[row_retry] ' + msg, level=xbmc.LOGINFO)


def skin_string(name):
    return xbmc.getInfoLabel('Skin.String(%s)' % name)


def num_items(container_id):
    try:
        return int(xbmc.getInfoLabel('Container(%s).NumItems' % container_id))
    except ValueError:
        return None


def page_rows(hub):
    """(row_number, container_id, widget_key, is_trakt) for each configured, visible row."""
    rows = []
    for n in ROWS:
        base = 'hbm_homecfg_%s_row%02d' % (hub, n)
        widget_key = base + '_widget'
        widget = skin_string(widget_key)
        if not widget or skin_string(base + '_visible') != 'Visible':
            continue
        rows.append((n, 700 + n, widget_key, 'trakt' in widget.lower()))
    return rows


def failed_trakt_rows(hub):
    """Trakt rows to retry on this hub, or [] if the retry condition isn't met."""
    rows = page_rows(hub)
    trakt = [r for r in rows if r[3]]
    others = [r for r in rows if not r[3]]
    if not trakt or not others:
        return []

    for _, cid, _, _ in others:
        count = num_items(cid)
        if not count:  # 0 = empty/still loading, None = control not found
            return []

    return [r for r in trakt if num_items(r[1]) == 0]


def main():
    win = xbmcgui.Window(HOME)

    # Home's onload fires every time the window opens; only one poller at a time.
    started = win.getProperty(RUN_PROP)
    if started and time.time() - float(started) < MAX_SECONDS + 30:
        return
    win.setProperty(RUN_PROP, str(time.time()))

    monitor = xbmc.Monitor()
    deadline = time.time() + MAX_SECONDS
    stable = {}  # hub -> consecutive polls the condition has held

    while time.time() < deadline and not monitor.abortRequested():
        if monitor.waitForAbort(POLL_SECONDS):
            break
        if not xbmc.getCondVisibility('Window.IsVisible(home)'):
            continue

        hub = skin_string('HBM.HomeActivePage')
        if hub not in HUBS:
            continue

        pending = [r for r in failed_trakt_rows(hub)
                   if not win.getProperty('HBM.RowRetryDone.' + r[2])]
        if not pending:
            stable[hub] = 0
            continue

        stable[hub] = stable.get(hub, 0) + 1
        if stable[hub] < STABLE_POLLS:
            continue

        for n, cid, widget_key, _ in pending:
            log('hub=%s row=%02d container=%d empty while other rows loaded, retrying' % (hub, n, cid))
            win.setProperty('HBM.RowRetryDone.' + widget_key, '1')
            win.setProperty(widget_key + '_retry', '&hbm_retry=1')
        stable[hub] = 0

    win.clearProperty(RUN_PROP)


main()
