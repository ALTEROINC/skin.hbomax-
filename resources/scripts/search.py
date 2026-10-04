import sys
import time

import xbmc
import xbmcgui

# Search screen helper.
#
# `poll` (started when the search window opens) is one long-running process that
#   - applies Backspace (the key only raises HBM.SearchBackspace, so no process is
#     spawned per key press), and
#   - commits the typed term to the results panels shortly after typing pauses.
# Letters and Space are appended by the XML itself, so they are instant.
#
# `commit` and `backspace` remain as fallbacks the XML uses only when the poller
# isn't running (HBM.SearchPoller empty), so search still works if it ever dies.

TERM = 'HBM.SearchTerm'
# One committed string per results panel so TV and movie searches start a moment
# apart instead of as two plugin calls at the same instant.
COMMITTED = ('HBM.SearchTermCommitted', 'HBM.SearchTermCommittedMovie')

HOME = 10000
POLLER_PROP = 'HBM.SearchPoller'
POLL_SECONDS = 0.1
DEBOUNCE_SECONDS = 0.4     # quiet time after the last key before searching
MIN_CHARS = 2              # one-letter searches are slow and rarely useful
STAGGER_SECONDS = 0.3      # gap between the TV and movie requests
CLOSED_GRACE = 2.0         # search window may flicker (dialogs); exit after this long


def log(msg):
    xbmc.log('[search] ' + msg, level=xbmc.LOGINFO)


def label(name):
    return xbmc.getInfoLabel('Skin.String(%s)' % name)


def term():
    return label(TERM)


def run(command):
    # wait=True so the next read sees the change (builtins are otherwise queued).
    xbmc.executebuiltin(command, True)


def set_string(name, value):
    run('Skin.SetString(%s,"%s")' % (name, value.replace('"', '')))


def reset_committed():
    for name in COMMITTED:
        run('Skin.Reset(%s)' % name)


def apply_backspace():
    current = term()
    if current:
        trimmed = current[:-1]
        if trimmed:
            set_string(TERM, trimmed)
        else:
            run('Skin.Reset(%s)' % TERM)


def commit(monitor, current):
    """Request TV, then movies, for `current`. Stops early if more is typed meanwhile."""
    query = current.strip()
    for i, name in enumerate(COMMITTED):
        if i:
            if monitor.waitForAbort(STAGGER_SECONDS) or term() != current:
                return False
        if label(name) != query:
            set_string(name, query)
    return True


def poll():
    win = xbmcgui.Window(HOME)

    beat = win.getProperty(POLLER_PROP)
    if beat and time.time() - float(beat) < 2:
        return  # one poller at a time

    monitor = xbmc.Monitor()
    last_seen = term()
    last_change = time.time()
    closed_since = None
    try:
        while not monitor.abortRequested():
            win.setProperty(POLLER_PROP, str(time.time()))

            if not xbmc.getCondVisibility('Window.IsActive(1114)'):
                closed_since = closed_since or time.time()
                if time.time() - closed_since > CLOSED_GRACE:
                    break
                if monitor.waitForAbort(POLL_SECONDS):
                    break
                continue
            closed_since = None

            if label('HBM.SearchBackspace') == '1':
                run('Skin.Reset(HBM.SearchBackspace)')
                apply_backspace()

            current = term()
            now = time.time()
            if current != last_seen:
                last_seen = current
                last_change = now
            elif now - last_change >= DEBOUNCE_SECONDS:
                query = current.strip()
                if not query:
                    if label(COMMITTED[0]) or label(COMMITTED[1]):
                        reset_committed()
                elif len(query) >= MIN_CHARS and (label(COMMITTED[0]) != query or label(COMMITTED[1]) != query):
                    commit(monitor, current)

            if monitor.waitForAbort(POLL_SECONDS):
                break
    finally:
        win.clearProperty(POLLER_PROP)


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ''

    if action == 'poll':
        poll()
    elif action == 'backspace':   # fallback when the poller isn't running
        apply_backspace()
        xbmc.executebuiltin(
            'AlarmClock(hbmsearchdebounce,RunScript(special://skin/resources/scripts/search.py,commit),00:00:01,silent,true)'
        )
    elif action == 'commit':      # fallback when the poller isn't running
        current = term()
        if not current.strip():
            reset_committed()
        else:
            commit(xbmc.Monitor(), current)


main()
