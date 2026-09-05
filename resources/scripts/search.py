import sys
import xbmc


def schedule_commit():
    xbmc.executebuiltin(
        'AlarmClock(hbmsearchdebounce,RunScript(special://skin/resources/scripts/search.py,commit),00:00:01,silent,true)'
    )


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ''
    current = xbmc.getInfoLabel('Skin.String(HBM.SearchTerm)')

    if action == 'backspace':
        if current:
            new_val = current[:-1]
            if new_val:
                xbmc.executebuiltin('Skin.SetString(HBM.SearchTerm,"' + new_val + '")')
            else:
                xbmc.executebuiltin('Skin.Reset(HBM.SearchTerm)')
        schedule_commit()
    elif action == 'space':
        if current:
            xbmc.executebuiltin('Skin.SetString(HBM.SearchTerm,"' + current + ' ")')
        schedule_commit()
    elif action == 'commit':
        if current:
            xbmc.executebuiltin('Skin.SetString(HBM.SearchTermCommitted,"' + current + '")')
        else:
            xbmc.executebuiltin('Skin.Reset(HBM.SearchTermCommitted)')


main()
