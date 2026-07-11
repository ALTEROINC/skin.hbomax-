import xbmc
import xbmcvfs

SRC = "special://skin/resources/keymaps/skin.hbomax.dev-scrub.xml"
DEST_DIR = "special://userdata/keymaps/"
DEST = DEST_DIR + "skin.hbomax.dev-scrub.xml"


def log(msg):
    xbmc.log("[install_scrub_keymap] " + msg, level=xbmc.LOGINFO)


def main():
    if xbmcvfs.exists(DEST):
        xbmc.executebuiltin("Skin.SetString(HBM.ScrubKeymapInstalled,1)")
        log("already installed")
        return

    if not xbmcvfs.exists(DEST_DIR):
        xbmcvfs.mkdirs(DEST_DIR)

    ok = xbmcvfs.copy(SRC, DEST)
    if ok:
        xbmc.executebuiltin("Skin.SetString(HBM.ScrubKeymapInstalled,1)")
        xbmc.executebuiltin(
            "Notification(HBO Max Skin,Smooth scrubbing installed - restart Kodi once to activate,8000)"
        )
        log("installed keymap to " + DEST)
    else:
        log("FAILED to copy keymap to " + DEST)


main()
