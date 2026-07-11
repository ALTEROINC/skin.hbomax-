import xbmc


def log(msg):
    xbmc.log("[scrub_commit] " + msg, level=xbmc.LOGINFO)


def main():
    if not xbmc.getCondVisibility("String.IsEqual(Skin.String(HBM.Scrubbing),1)"):
        return

    target = float(xbmc.getInfoLabel("Skin.String(HBM.ScrubTargetSeconds)") or 0)
    xbmc.executebuiltin("Skin.SetString(HBM.Scrubbing,0)")

    player = xbmc.Player()
    if not player.isPlayingVideo():
        return

    player.seekTime(target)
    log("committed seek to %.2f" % target)


main()
