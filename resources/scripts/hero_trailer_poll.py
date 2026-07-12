import sys

import xbmc

# How long to hold on the item (static backdrop, description back on screen)
# after its trailer finishes before auto-scrolling to the next one.
HOLD_DELAY = "00:00:10"


def log(msg):
    xbmc.log("[hero_trailer_poll] " + msg, level=xbmc.LOGINFO)


def main():
    if len(sys.argv) < 2:
        return
    container_id = sys.argv[1]

    if not xbmc.getCondVisibility("String.IsEqual(Skin.String(HBM.TrailerPlaying),1)"):
        # Already stopped by something else (nav away, manual Play, etc.) —
        # stop polling.
        xbmc.executebuiltin("CancelAlarm(HBMTrailerPoll%s,silent)" % container_id)
        return

    if xbmc.Player().isPlaying():
        # Still going — let the loop's own AlarmClock re-fire this in POLL_INTERVAL.
        return

    # Playback ended naturally (trailer finished). Drop back to the static
    # backdrop/description and hold there for HOLD_DELAY before scrolling on —
    # TrailerCycleActive (already 1) keeps hero_rotate.py's own 14s loop
    # paused during that hold so it can't independently rotate out from
    # under this.
    xbmc.executebuiltin("CancelAlarm(HBMTrailerPoll%s,silent)" % container_id)
    xbmc.executebuiltin("Skin.SetString(HBM.TrailerPlaying,0)")
    log("trailer ended naturally for container=%s, holding %s before advance" % (container_id, HOLD_DELAY))
    xbmc.executebuiltin(
        "AlarmClock(HBMTrailerAdvance%s,RunScript(special://skin/resources/scripts/hero_trailer_advance.py,%s),%s,silent)"
        % (container_id, container_id, HOLD_DELAY)
    )


main()
