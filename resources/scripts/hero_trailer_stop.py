import xbmc


def log(msg):
    xbmc.log("[hero_trailer_stop] " + msg, level=xbmc.LOGINFO)


def main():
    if xbmc.getCondVisibility("String.IsEqual(Skin.String(HBM.TrailerPlaying),1)"):
        if xbmc.Player().isPlaying():
            xbmc.Player().stop()
        log("stopped trailer preview")
    xbmc.executebuiltin("Skin.SetString(HBM.TrailerPlaying,0)")
    xbmc.executebuiltin("Skin.SetString(HBM.TrailerCycleActive,0)")
    # Prevent a stale start/poll/advance timer from firing later against
    # whatever item happens to be current by then.
    for container_id in ("620", "621", "622", "623", "624"):
        xbmc.executebuiltin("CancelAlarm(HBMTrailerStart%s,silent)" % container_id)
        xbmc.executebuiltin("CancelAlarm(HBMTrailerReady%s,silent)" % container_id)
        xbmc.executebuiltin("CancelAlarm(HBMTrailerPoll%s,silent)" % container_id)
        xbmc.executebuiltin("CancelAlarm(HBMTrailerAdvance%s,silent)" % container_id)


main()
