import os
import sys

import xbmc
import xbmcgui
import xbmcvfs

# Kodi shows its startup splash from special://home/media/splash.jpg (or .png) when present, before any
# skin loads, so a skin can't draw it. This keeps that file in sync so the *next* launch shows it.
#
#   (no argument)  on Home load: install the skin's own media/splash.png, unless the user picked their
#                  own image in Skin Settings (HBM.SplashImage), which is left alone.
#   apply          copy the image picked in Skin Settings.
#   reset          drop the picked image and go back to the skin's own splash.

BUNDLED = 'special://skin/media/splash.png'
TARGET_DIR = 'special://home/media/'
TARGETS = (TARGET_DIR + 'splash.jpg', TARGET_DIR + 'splash.png')   # Kodi checks .jpg first


def log(msg):
    xbmc.log('[install_splash] ' + msg, level=xbmc.LOGINFO)


def notify(msg):
    xbmcgui.Dialog().notification('HBO Max Skin', msg, xbmcgui.NOTIFICATION_INFO, 5000)


def remove_targets():
    for target in TARGETS:
        if xbmcvfs.exists(target):
            xbmcvfs.delete(target)


def install(source):
    """Make `source` the splash (named by its own extension). Returns True on success."""
    ext = '.jpg' if os.path.splitext(source)[1].lower() in ('.jpg', '.jpeg') else '.png'
    target = TARGET_DIR + 'splash' + ext
    if xbmcvfs.exists(target) and xbmcvfs.exists(source):
        if xbmcvfs.Stat(source).st_size() == xbmcvfs.Stat(target).st_size() \
                and all(not xbmcvfs.exists(t) for t in TARGETS if t != target):
            return True   # already installed
    xbmcvfs.mkdirs(TARGET_DIR)
    remove_targets()
    ok = xbmcvfs.copy(source, target)
    log('%s -> %s: %s' % (source, target, 'ok' if ok else 'FAILED'))
    return bool(ok)


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ''
    chosen = xbmc.getInfoLabel('Skin.String(HBM.SplashImage)')

    try:
        if action == 'apply':
            if chosen and xbmcvfs.exists(chosen) and install(chosen):
                notify('Splash saved. It shows the next time Kodi starts.')
            else:
                notify('Could not use that image.')
        elif action == 'reset':
            xbmc.executebuiltin('Skin.Reset(HBM.SplashImage)', True)
            remove_targets()
            if xbmcvfs.exists(BUNDLED) and install(BUNDLED):
                notify('Default splash restored. It shows the next time Kodi starts.')
            else:
                notify('Splash removed. Kodi\'s own splash will show.')
        elif not chosen and xbmcvfs.exists(BUNDLED):
            install(BUNDLED)
    except Exception as e:
        log('failed: %s' % e)


main()
