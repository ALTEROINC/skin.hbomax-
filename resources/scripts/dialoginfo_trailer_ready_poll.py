import xbmc

POLL_INTERVAL = "00:00:05"
MAX_TICKS = 20


def log(msg):
    xbmc.log("[dialoginfo_trailer_ready_poll] " + msg, level=xbmc.LOGINFO)


def main():
    if not xbmc.getCondVisibility("Window.IsActive(movieinformation)"):
        xbmc.executebuiltin("CancelAlarm(HBMInfoTrailerReady,silent)")
        return

    if xbmc.Player().isPlaying():
        xbmc.executebuiltin("CancelAlarm(HBMInfoTrailerReady,silent)")
        xbmc.executebuiltin("Skin.SetString(HBM.InfoTrailerPlaying,1)")
        xbmc.executebuiltin(
            "AlarmClock(HBMInfoTrailerPoll,RunScript(special://skin/resources/scripts/dialoginfo_trailer_poll.py),%s,silent,loop)"
            % POLL_INTERVAL
        )
        log("trailer actually playing, revealing")
        return

    ticks = xbmc.getInfoLabel("Skin.String(HBM.InfoTrailerReadyTicks)")
    try:
        ticks = int(ticks) if ticks else 0
    except ValueError:
        ticks = 0
    ticks += 1

    if ticks >= MAX_TICKS:
        log("gave up waiting for trailer to start")
        xbmc.executebuiltin("CancelAlarm(HBMInfoTrailerReady,silent)")
        if xbmc.Player().isPlaying():
            xbmc.Player().stop()
        return

    xbmc.executebuiltin("Skin.SetString(HBM.InfoTrailerReadyTicks,%d)" % ticks)


main()
