import xbmc
import xbmcaddon


def log(msg):
    xbmc.log("[fix_mdblist_token] " + msg, level=xbmc.LOGINFO)


def main():
    try:
        addon = xbmcaddon.Addon("plugin.video.umbrella")
    except RuntimeError:
        log("umbrella not installed, skipping")
        xbmc.executebuiltin("Skin.SetString(HBM.MDBListTokenFixed,1)")
        return

    # mdblist.token/mdblist.refresh.token are an authenticated session pair
    # (set via Umbrella's own mdblistAuth login flow), not a plain static
    # API key. An earlier version of the API-key prefill incorrectly wrote
    # the plain MDBList API key into mdblist.token, which made Umbrella
    # think it had a valid session and caused "session expired" failures.
    # Clear both so Umbrella falls back to its normal unauthenticated
    # MDBList flow until the user runs the real login through its UI.
    addon.setSettingString("mdblist.token", "")
    addon.setSettingString("mdblist.refresh.token", "")
    xbmc.executebuiltin("Skin.SetString(HBM.MDBListTokenFixed,1)")
    log("cleared mdblist.token / mdblist.refresh.token")


main()
