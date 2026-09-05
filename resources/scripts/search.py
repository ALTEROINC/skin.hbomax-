import sys
import xbmc

DEBOUNCE_MS = 600


def commit():
    term_before = xbmc.getInfoLabel('Skin.String(HBM.SearchTerm)')
    xbmc.sleep(DEBOUNCE_MS)
    term_after = xbmc.getInfoLabel('Skin.String(HBM.SearchTerm)')
    if term_before != term_after:
        return
    if term_after:
        xbmc.executebuiltin('Skin.SetString(HBM.SearchTermCommitted,"' + term_after + '")')
    else:
        xbmc.executebuiltin('Skin.Reset(HBM.SearchTermCommitted)')


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
        commit()
    elif action == 'space':
        if current:
            xbmc.executebuiltin('Skin.SetString(HBM.SearchTerm,"' + current + ' ")')
        commit()
    elif action == 'schedule':
        commit()


main()
