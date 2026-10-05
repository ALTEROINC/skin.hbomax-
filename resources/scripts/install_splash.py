import xbmc
import xbmcvfs

# Kodi shows its own startup splash from special://home/media/splash.jpg (or .png) before any skin loads, so a
# skin can't draw it. The skin wants that first splash to be plain black (the real splash image is shown by
# Startup.xml after the intro video), so this keeps a black image there. Runs on Home load; only copies when needed.

BLACK = 'special://skin/media/splash_black.png'
TARGET_DIR = 'special://home/media/'
TARGET = TARGET_DIR + 'splash.png'
OTHER = TARGET_DIR + 'splash.jpg'     # Kodi checks .jpg first, so a leftover one would hide ours


def log(msg):
    xbmc.log('[install_splash] ' + msg, level=xbmc.LOGINFO)


def main():
    if not xbmcvfs.exists(BLACK):
        return
    try:
        if not xbmcvfs.exists(OTHER) and xbmcvfs.exists(TARGET) \
                and xbmcvfs.Stat(BLACK).st_size() == xbmcvfs.Stat(TARGET).st_size():
            return
        xbmcvfs.mkdirs(TARGET_DIR)
        if xbmcvfs.exists(OTHER):
            xbmcvfs.delete(OTHER)
        if xbmcvfs.exists(TARGET):
            xbmcvfs.delete(TARGET)
        ok = xbmcvfs.copy(BLACK, TARGET)
        log('black native splash installed: %s (takes effect next launch)' % ('ok' if ok else 'FAILED'))
    except Exception as e:
        log('failed: %s' % e)


main()
