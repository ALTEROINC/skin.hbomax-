import sys
import xbmc

TERM = 'HBM.SearchTerm'
# One committed string per results panel so each search is requested at a
# different moment instead of all three plugin calls starting together.
COMMITTED = ('HBM.SearchTermCommitted', 'HBM.SearchTermCommittedMovie', 'HBM.SearchTermCommittedPerson')
STAGGER_SECONDS = 0.8


def schedule_commit():
    xbmc.executebuiltin(
        'AlarmClock(hbmsearchdebounce,RunScript(special://skin/resources/scripts/search.py,commit),00:00:01,silent,true)'
    )


def term():
    return xbmc.getInfoLabel('Skin.String(%s)' % TERM)


def reset_committed():
    for name in COMMITTED:
        xbmc.executebuiltin('Skin.Reset(%s)' % name)


def commit():
    """Request TV, then movies, then people for the typed term, one at a time.

    Each is a TMDb Helper plugin call (a Python process plus network requests), so
    firing all three at once on a slow device made the first results wait on the
    last. Staggering them lets TV results appear first. If more is typed meanwhile
    the remaining stages are skipped; the newer debounce alarm takes over.
    """
    current = term()
    if not current:
        reset_committed()
        return

    monitor = xbmc.Monitor()
    for i, name in enumerate(COMMITTED):
        if i:
            if monitor.waitForAbort(STAGGER_SECONDS) or term() != current:
                return
        if xbmc.getInfoLabel('Skin.String(%s)' % name) != current:
            xbmc.executebuiltin('Skin.SetString(%s,"%s")' % (name, current))


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ''
    current = term()

    if action == 'backspace':
        if current:
            new_val = current[:-1]
            if new_val:
                xbmc.executebuiltin('Skin.SetString(%s,"%s")' % (TERM, new_val))
            else:
                xbmc.executebuiltin('Skin.Reset(%s)' % TERM)
        schedule_commit()
    elif action == 'commit':
        commit()


main()
