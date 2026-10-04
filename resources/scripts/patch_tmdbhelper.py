import glob
import os

import xbmc
import xbmcaddon

# Small compatibility patches applied to the installed TMDb Helper. Each is idempotent (a marker comment
# in the patched line) and silently skipped if the code it targets has changed in a TMDb Helper update.
# Kodi needs a restart afterwards for TMDb Helper to load the patched source.

LISTITEM_MARKER = "# HBM_SETPROPS_FIX"
SEEALL_MARKER = "# HBM_SEEALL"


def log(msg, level=xbmc.LOGINFO):
    xbmc.log("[hbm_patch] " + msg, level=level)


def patch_file(path, marker, old, new, label):
    """Replace `old` with `new` in `path` once. Returns True if the file was changed."""
    if not os.path.exists(path):
        return False

    with open(path, "r") as f:
        content = f.read()

    if marker in content:
        return False  # already patched

    if old not in content:
        log("%s: target line not found - TMDb Helper may have updated" % label)
        return False

    try:
        with open(path, "w") as f:
            f.write(content.replace(old, new, 1))
    except Exception as e:
        log("%s: write failed: %s" % (label, e), xbmc.LOGERROR)
        return False

    # Clear compiled bytecode so the patched source is picked up on next start.
    cache_dir = os.path.join(os.path.dirname(path), "__pycache__")
    stem = os.path.splitext(os.path.basename(path))[0]
    for pyc in glob.glob(os.path.join(cache_dir, stem + "*.pyc")):
        try:
            os.remove(pyc)
        except Exception:
            pass

    log("patched TMDb Helper: %s" % label)
    return True


def main():
    try:
        addon_path = xbmcaddon.Addon("plugin.video.themoviedb.helper").getAddonInfo("path")
    except Exception:
        return

    lib = os.path.join(addon_path, "resources", "tmdbhelper", "lib")
    changed = False

    # Kodi 21's setProperties only accepts str values: stringify every value so it doesn't crash.
    changed |= patch_file(
        os.path.join(lib, "items", "listitem.py"),
        LISTITEM_MARKER,
        "listitem.setProperties(self.infoproperties)",
        'listitem.setProperties({k: str(v) if v is not None else "" '
        "for k, v in (self.infoproperties or {}).items()})  " + LISTITEM_MARKER,
        "setProperties",
    )

    # See All: when a list URL carries hbm_seeall=True and the list has no "Next page" item of its own
    # (single page, Trakt/sync lists, random lists...), append one so every row ends with the same tile.
    changed |= patch_file(
        os.path.join(lib, "items", "container.py"),
        SEEALL_MARKER,
        "        return item_queue\n\n    def add_items",
        "        if self.pagination and self.params.get('hbm_seeall') and item_queue and not any(  " + SEEALL_MARKER + "\n"
        "                li.next_page for li in item_queue if li):\n"
        "            try:\n"
        "                _seeall = self._make_item(self.ib.get_listitem({'next_page': 2}, use_iterprops=self.is_detailed))\n"
        "                if _seeall:\n"
        "                    item_queue.append(_seeall)\n"
        "            except Exception:\n"
        "                pass\n"
        "        return item_queue\n\n    def add_items",
        "See All item",
    )

    if changed:
        xbmc.executebuiltin("Notification(HBO Max Skin,TMDb Helper patched. Please restart Kodi.,8000)")


main()
