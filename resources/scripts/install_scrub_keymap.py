import xbmc
import xbmcvfs

SRC = "special://skin/resources/keymaps/skin.hbomax.dev-scrub.xml"
DEST_DIR = "special://userdata/keymaps/"
DEST = DEST_DIR + "skin.hbomax.dev-scrub.xml"


def log(msg):
    xbmc.log("[install_scrub_keymap] " + msg, level=xbmc.LOGINFO)


def main():
    # Always overwrite — the outer onload gate (Skin.String flag) controls
    # whether this runs at all, so once it does run it should unconditionally
    # sync the bundled keymap, otherwise future edits to this file would
    # never reach devices that already installed an older version.
    if not xbmcvfs.exists(DEST_DIR):
        xbmcvfs.mkdirs(DEST_DIR)

    ok = xbmcvfs.copy(SRC, DEST)
    if ok:
        xbmc.executebuiltin("Skin.SetString(HBM.ScrubKeymapInstalledV2,1)")
        xbmc.executebuiltin(
            "Notification(HBO Max Skin,Smooth scrubbing updated - restart Kodi once to activate,8000)"
        )
        log("installed keymap to " + DEST)
    else:
        log("FAILED to copy keymap to " + DEST)


main()
