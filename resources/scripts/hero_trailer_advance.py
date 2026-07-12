import sys

import xbmc


def log(msg):
    xbmc.log("[hero_trailer_advance] " + msg, level=xbmc.LOGINFO)


def main():
    if xbmc.getCondVisibility("String.IsEqual(Skin.String(HBM.TrailerPlaying),1)"):
        xbmc.Player().stop()
    xbmc.executebuiltin("Skin.SetString(HBM.TrailerPlaying,0)")
    xbmc.executebuiltin("Skin.SetString(HBM.TrailerCycleActive,0)")

    if len(sys.argv) < 2:
        return
    container_id = sys.argv[1]
    xbmc.executebuiltin("CancelAlarm(HBMTrailerStart%s,silent)" % container_id)
    xbmc.executebuiltin("CancelAlarm(HBMTrailerReady%s,silent)" % container_id)
    xbmc.executebuiltin("CancelAlarm(HBMTrailerPoll%s,silent)" % container_id)
    xbmc.executebuiltin("CancelAlarm(HBMTrailerAdvance%s,silent)" % container_id)
    log("advancing container=%s after trailer cycle ended" % container_id)
    # hero_rotate.py's own TrailerCycleActive check was paused for the
    # whole 7s-wait + trailer + 10s-hold cycle — force one rotation now
    # instead of waiting for the next natural 14s tick. hero_rotate.py
    # itself sets TrailerCycleActive again and schedules the next 7s wait.
    xbmc.executebuiltin(
        "RunScript(special://skin/resources/scripts/hero_rotate.py,%s)" % container_id
    )


main()
