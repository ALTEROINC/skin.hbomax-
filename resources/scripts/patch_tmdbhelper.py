import glob
import os

import xbmc
import xbmcaddon

MARKER = "# HBM_SETPROPS_FIX"


def main():
    try:
        addon_path = xbmcaddon.Addon("plugin.video.themoviedb.helper").getAddonInfo("path")
    except Exception:
        return

    listitem_path = os.path.join(
        addon_path, "resources", "tmdbhelper", "lib", "items", "listitem.py"
    )
    if not os.path.exists(listitem_path):
        return

    with open(listitem_path, "r") as f:
        content = f.read()

    if MARKER in content:
        return  # already patched

    old = "listitem.setProperties(self.infoproperties)"
    if old not in content:
        xbmc.log("[hbm_patch] setProperties line not found — TMDb Helper may have updated", xbmc.LOGINFO)
        return

    # Stringify every value so Kodi 21's strict str-only setProperties doesn't crash.
    new = (
        'listitem.setProperties({k: str(v) if v is not None else "" '
        "for k, v in (self.infoproperties or {}).items()})  " + MARKER
    )
    content = content.replace(old, new)

    try:
        with open(listitem_path, "w") as f:
            f.write(content)
    except Exception as e:
        xbmc.log("[hbm_patch] write failed: %s" % e, xbmc.LOGERROR)
        return

    # Clear compiled bytecode so the patched source is picked up on next start.
    cache_dir = os.path.join(os.path.dirname(listitem_path), "__pycache__")
    for pyc in glob.glob(os.path.join(cache_dir, "listitem*.pyc")):
        try:
            os.remove(pyc)
        except Exception:
            pass

    xbmc.log("[hbm_patch] patched TMDb Helper setProperties — restart Kodi to apply", xbmc.LOGINFO)
    xbmc.executebuiltin(
        "Notification(HBO Max Skin,TMDb Helper patched. Please restart Kodi.,8000)"
    )


main()
