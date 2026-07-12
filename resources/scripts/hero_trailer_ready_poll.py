import sys

import xbmc

POLL_INTERVAL = "00:00:05"

# Safety cap — if playback never actually starts (resolve failure, network
# error) don't leave the hero stuck waiting on a spinner forever.
MAX_TICKS = 20


def log(msg):
    xbmc.log("[hero_trailer_ready_poll] " + msg, level=xbmc.LOGINFO)


def main():
    if len(sys.argv) < 2:
        return
    container_id = sys.argv[1]

    if xbmc.getInfoLabel("Skin.String(HBM.TrailerCycleActive)") != "1":
        xbmc.executebuiltin("CancelAlarm(HBMTrailerReady%s,silent)" % container_id)
        return

    if xbmc.Player().isPlaying():
        xbmc.executebuiltin("CancelAlarm(HBMTrailerReady%s,silent)" % container_id)
        xbmc.executebuiltin("Skin.SetString(HBM.TrailerPlaying,1)")
        xbmc.executebuiltin(
            "AlarmClock(HBMTrailerPoll%s,RunScript(special://skin/resources/scripts/hero_trailer_poll.py,%s),%s,silent,loop)"
            % (container_id, container_id, POLL_INTERVAL)
        )
        log("trailer actually playing, revealing container=%s" % container_id)
        return

    ticks = xbmc.getInfoLabel("Skin.String(HBM.TrailerReadyTicks)")
    try:
        ticks = int(ticks) if ticks else 0
    except ValueError:
        ticks = 0
    ticks += 1

    if ticks >= MAX_TICKS:
        log("gave up waiting for trailer to start on container=%s" % container_id)
        xbmc.executebuiltin("CancelAlarm(HBMTrailerReady%s,silent)" % container_id)
        xbmc.executebuiltin("Skin.SetString(HBM.TrailerCycleActive,0)")
        if xbmc.Player().isPlaying():
            xbmc.Player().stop()
        return

    xbmc.executebuiltin("Skin.SetString(HBM.TrailerReadyTicks,%d)" % ticks)


main()
