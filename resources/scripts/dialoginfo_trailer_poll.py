import xbmc


def log(msg):
    xbmc.log("[dialoginfo_trailer_poll] " + msg, level=xbmc.LOGINFO)


def main():
    if not xbmc.getCondVisibility("String.IsEqual(Skin.String(HBM.InfoTrailerPlaying),1)"):
        xbmc.executebuiltin("CancelAlarm(HBMInfoTrailerPoll,silent)")
        return

    if not xbmc.getCondVisibility("Window.IsActive(movieinformation)"):
        # Dialog closed mid-play — onunload's stop script handles cleanup.
        xbmc.executebuiltin("CancelAlarm(HBMInfoTrailerPoll,silent)")
        return

    if xbmc.Player().isPlaying():
        # Still going — loop's own AlarmClock re-fires this.
        return

    # Trailer finished naturally. Single fixed item, nothing to advance to —
    # just drop back to the static fanart backdrop and stay there.
    xbmc.executebuiltin("CancelAlarm(HBMInfoTrailerPoll,silent)")
    xbmc.executebuiltin("Skin.SetString(HBM.InfoTrailerPlaying,0)")
    log("trailer ended naturally")


main()
