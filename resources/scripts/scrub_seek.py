import sys

import xbmc

STEP_SECONDS = 5


def log(msg):
    xbmc.log("[scrub_seek] " + msg, level=xbmc.LOGINFO)


def format_time(seconds):
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return "%d:%02d:%02d" % (h, m, s)
    return "%d:%02d" % (m, s)


def main():
    if len(sys.argv) < 2:
        return
    direction = sys.argv[1]

    player = xbmc.Player()
    if not player.isPlayingVideo():
        return

    total = player.getTotalTime()
    if total <= 0:
        return

    scrubbing = xbmc.getCondVisibility(
        "String.IsEqual(Skin.String(HBM.Scrubbing),1)"
    )
    if scrubbing:
        target = float(xbmc.getInfoLabel("Skin.String(HBM.ScrubTargetSeconds)") or 0)
    else:
        target = player.getTime()

    target += STEP_SECONDS if direction == "right" else -STEP_SECONDS
    target = max(0, min(total, target))
    percent = (target / total) * 100.0

    xbmc.executebuiltin("Skin.SetString(HBM.Scrubbing,1)")
    xbmc.executebuiltin("Skin.SetString(HBM.ScrubTargetSeconds,%.2f)" % target)
    xbmc.executebuiltin("Skin.SetString(HBM.ScrubPercent,%.4f)" % percent)
    xbmc.executebuiltin(
        "Skin.SetString(HBM.ScrubTimeLabel,%s / %s)"
        % (format_time(target), format_time(total))
    )

    # Debounce: (re)arm a short one-shot alarm on every press. Only the
    # LAST press in a burst actually fires the alarm and commits the real
    # seek — this is what turns per-press hard seeking into a smooth
    # preview-then-commit scrub instead.
    xbmc.executebuiltin(
        "AlarmClock(HBMScrubCommit,RunScript(special://skin/resources/scripts/scrub_commit.py),00:00:01,silent)"
    )


main()
