import sys

import xbmc

HUB_BY_CONTAINER = {
    "620": "home",
    "621": "tvshows",
    "622": "movies",
    "623": "livetv",
    "624": "mylist",
}

def log(msg):
    xbmc.log("[hero_trailer_start] " + msg, level=xbmc.LOGINFO)


def main():
    if len(sys.argv) < 2:
        return
    container_id = sys.argv[1]

    # The 7s wait elapsed — if the user already moved on (nav, row focus,
    # left the hub) TrailerCycleActive will have been cleared by whatever did
    # that, and there's nothing to start.
    if xbmc.getInfoLabel("Skin.String(HBM.TrailerCycleActive)") != "1":
        return

    # Only start a preview if the hero is still the thing on screen (not scrolled
    # into rows, not on a different hub than when this was triggered).
    if xbmc.getInfoLabel("Skin.String(HBM.ActiveRow)") != "0":
        xbmc.executebuiltin("Skin.SetString(HBM.TrailerCycleActive,0)")
        return
    expected_hub = HUB_BY_CONTAINER.get(container_id)
    if expected_hub is None or xbmc.getInfoLabel("Skin.String(HBM.HomeActivePage)") != expected_hub:
        xbmc.executebuiltin("Skin.SetString(HBM.TrailerCycleActive,0)")
        return

    # Don't stomp on something the user actually pressed Play on.
    if xbmc.Player().isPlaying():
        xbmc.executebuiltin("Skin.SetString(HBM.TrailerCycleActive,0)")
        return

    imdb_id = ""
    if xbmc.getCondVisibility("System.HasAddon(slyguy.trailers)"):
        imdb_id = xbmc.getInfoLabel("Container(%s).ListItem.UniqueID(imdb)" % container_id)
        if not imdb_id:
            imdb_id = xbmc.getInfoLabel("Container(%s).ListItem.IMDBNumber" % container_id)

    if not imdb_id:
        # No trailer available for this item — don't hold the hero hostage,
        # let the normal 14s auto-rotate loop carry on as if trailers didn't
        # exist for this one.
        log("no trailer available for container=%s, skipping" % container_id)
        xbmc.executebuiltin("Skin.SetString(HBM.TrailerCycleActive,0)")
        return

    # Kick off resolution/playback now, but don't reveal anything yet — the
    # native busy spinner (top-right, via our DialogBusy.xml override) is the
    # only thing that shows during resolution. hero_trailer_ready_poll.py
    # watches for playback to actually start and does the reveal at that
    # exact moment, not before.
    xbmc.executebuiltin("Skin.SetString(HBM.TrailerReadyTicks,0)")
    xbmc.executebuiltin(
        "PlayMedia(plugin://slyguy.trailers/imdb/?video_id=%s,1)" % imdb_id
    )
    xbmc.executebuiltin(
        "AlarmClock(HBMTrailerReady%s,RunScript(special://skin/resources/scripts/hero_trailer_ready_poll.py,%s),00:00:01,silent,loop)"
        % (container_id, container_id)
    )
    log("resolving trailer imdb=%s container=%s" % (imdb_id, container_id))


main()
