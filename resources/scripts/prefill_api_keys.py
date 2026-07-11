import json
import os

import xbmc
import xbmcaddon
import xbmcvfs

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "api_keys.local.json"
)


def log(msg):
    xbmc.log("[prefill_api_keys] " + msg, level=xbmc.LOGINFO)


def main():
    if not xbmcvfs.exists(CONFIG_PATH):
        log("no api_keys.local.json found, skipping")
        return

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    for addon_id, keys in config.items():
        try:
            addon = xbmcaddon.Addon(addon_id)
        except RuntimeError:
            log("%s not installed, skipping" % addon_id)
            continue

        for setting_id, value in keys.items():
            if not value:
                continue
            addon.setSettingString(setting_id, value)
            log("set %s.%s" % (addon_id, setting_id))

    xbmc.executebuiltin("Skin.SetString(HBM.APIKeysPrefilled,1)")
    log("done")


main()
