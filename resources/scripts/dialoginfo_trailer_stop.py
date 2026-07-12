import xbmc


def log(msg):
    xbmc.log("[dialoginfo_trailer_stop] " + msg, level=xbmc.LOGINFO)


def main():
    if xbmc.getCondVisibility("String.IsEqual(Skin.String(HBM.InfoTrailerPlaying),1)"):
        if xbmc.Player().isPlaying():
            xbmc.Player().stop()
        log("stopped trailer preview")
    xbmc.executebuiltin("Skin.SetString(HBM.InfoTrailerPlaying,0)")
    xbmc.executebuiltin("CancelAlarm(HBMInfoTrailerStart,silent)")
    xbmc.executebuiltin("CancelAlarm(HBMInfoTrailerReady,silent)")
    xbmc.executebuiltin("CancelAlarm(HBMInfoTrailerPoll,silent)")


main()
