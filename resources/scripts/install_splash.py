import xbmc
import xbmcvfs

# Kodi shows its startup splash from special://home/media/splash.png (or .jpg) when present, before any skin
# loads, so a skin can't draw it. This copies the skin's own media/splash.png there so the *next* launch
# shows it. It only acts when the skin ships that file, and only copies when the image has changed.

SOURCE = 'special://skin/media/splash.png'
TARGET_DIR = 'special://home/media/'
TARGET = TARGET_DIR + 'splash.png'


def log(msg):
    xbmc.log('[install_splash] ' + msg, level=xbmc.LOGINFO)


def main():
    if not xbmcvfs.exists(SOURCE):
        return

    try:
        if xbmcvfs.exists(TARGET):
            same = xbmcvfs.Stat(SOURCE).st_size() == xbmcvfs.Stat(TARGET).st_size()
            if same:
                return
        xbmcvfs.mkdirs(TARGET_DIR)
        if xbmcvfs.copy(SOURCE, TARGET):
            log('splash installed; it shows from the next Kodi launch')
        else:
            log('could not copy splash to ' + TARGET)
    except Exception as e:
        log('failed: %s' % e)


main()
