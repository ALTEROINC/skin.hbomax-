import xbmc


def log(msg):
    xbmc.log("[dialoginfo_trailer_start] " + msg, level=xbmc.LOGINFO)


def main():
    # The 7s wait elapsed — if the dialog was already closed, there's nothing
    # to start.
    if not xbmc.getCondVisibility("Window.IsActive(movieinformation)"):
        return

    # Don't stomp on something the user actually pressed Play/Trailer/Restart on.
    if xbmc.Player().isPlaying():
        return

    if not xbmc.getCondVisibility("System.HasAddon(slyguy.trailers)"):
        log("slyguy.trailers not installed, skipping")
        return

    imdb_id = xbmc.getInfoLabel("ListItem.UniqueID(imdb)")
    if not imdb_id:
        imdb_id = xbmc.getInfoLabel("ListItem.IMDBNumber")
    if not imdb_id:
        log("no imdb id available")
        return

    xbmc.executebuiltin("Skin.SetString(HBM.InfoTrailerReadyTicks,0)")
    xbmc.executebuiltin(
        "PlayMedia(plugin://slyguy.trailers/imdb/?video_id=%s,1)" % imdb_id
    )
    xbmc.executebuiltin(
        "AlarmClock(HBMInfoTrailerReady,RunScript(special://skin/resources/scripts/dialoginfo_trailer_ready_poll.py),00:00:01,silent,loop)"
    )
    log("resolving trailer imdb=%s" % imdb_id)


main()
