import sys
import xbmc


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
    elif action == 'space':
        if current:
            xbmc.executebuiltin('Skin.SetString(HBM.SearchTerm,"' + current + ' ")')


main()
