import sys

import xbmc


# Starts the in-page trailer (the same backdrop animation as before: the video plays behind the page content,
# the clear logo centres at the top, the buttons fade out). It no longer starts on its own: it is run by the
# Trailer button on the info page, and a second press stops the trailer again.

STOP = "RunScript(special://skin/resources/scripts/dialoginfo_trailer_stop.py)"


def log(msg):
    xbmc.log("[dialoginfo_trailer_start] " + msg, level=xbmc.LOGINFO)


def notify(msg):
    xbmc.executebuiltin("Notification(Trailer,%s,3000)" % msg)


def main():
    if not xbmc.getCondVisibility("Window.IsActive(movieinformation)"):
        return

    # Button pressed while a trailer is already running (or still resolving): stop it.
    if xbmc.getCondVisibility("String.IsEqual(Skin.String(HBM.InfoTrailerPlaying),1)") or xbmc.Player().isPlaying():
        xbmc.executebuiltin(STOP)
        log("trailer stopped by button")
        return

    if not xbmc.getCondVisibility("System.HasAddon(slyguy.trailers)"):
        notify("The SlyGuy Trailers add-on is not installed")
        return

    imdb_id = xbmc.getInfoLabel("ListItem.UniqueID(imdb)") or xbmc.getInfoLabel("ListItem.IMDBNumber")
    if not imdb_id:
        notify("No trailer available for this title")
        return

    xbmc.executebuiltin("Skin.SetString(HBM.InfoTrailerReadyTicks,0)")
    # The trailing 1 plays it windowed, so it shows behind the page instead of opening the full-screen player.
    xbmc.executebuiltin("PlayMedia(plugin://slyguy.trailers/imdb/?video_id=%s,1)" % imdb_id)
    xbmc.executebuiltin(
        "AlarmClock(HBMInfoTrailerReady,RunScript(special://skin/resources/scripts/dialoginfo_trailer_ready_poll.py),00:00:01,silent,loop)"
    )
    log("resolving trailer imdb=%s" % imdb_id)


main()
