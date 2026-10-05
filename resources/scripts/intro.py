import xbmc
import xbmcvfs

# Startup intro (called from Startup.xml, once per Kodi launch). Plays the video chosen in Skin Settings
# if there is one, otherwise the video shipped in the skin zip (media/intro/intro.mp4), if present.

BUNDLED = 'special://skin/media/intro/intro.mp4'


def main():
    if xbmc.getCondVisibility('Skin.HasSetting(hbm_intro_off)'):
        return

    path = xbmc.getInfoLabel('Skin.String(HBM.IntroVideo)')
    if not path or not xbmcvfs.exists(path):
        path = BUNDLED
        if not xbmcvfs.exists(path):
            return

    xbmc.executebuiltin('PlayMedia("%s",noresume)' % path)


main()
