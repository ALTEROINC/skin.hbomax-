import xbmc
import xbmcvfs

# Startup (called from Startup.xml, once per Kodi launch). Startup.xml shows a black screen while this runs
# so the hub never flashes before the intro.
#
#   - Intro video chosen in Skin Settings, else the one shipped in the skin (media/intro/intro.mp4).
#   - Wait for the video to finish (or be skipped with Back), show the splash image for a moment, then open the
#     startup window. Until then the black Startup screen is what's behind the video, so nothing flashes.
#   - No video, or it fails to start: open the startup window straight away.

BUNDLED = 'special://skin/media/intro/intro.mp4'
START_TIMEOUT = 8      # seconds to wait for the video to appear before giving up on it
POLL_SECONDS = 0.05
SPLASH_SECONDS = 2.0    # how long the splash image shows after the video
MAX_PLAY_SECONDS = 120  # never hold the hub back longer than this


def log(msg):
    xbmc.log('[intro] ' + msg, level=xbmc.LOGINFO)


def show_splash(monitor):
    """Hold the splash image on the Startup screen for a moment before the hub opens."""
    xbmc.executebuiltin('SetProperty(HBM.StartupSplash,1,home)')
    monitor.waitForAbort(SPLASH_SECONDS)
    xbmc.executebuiltin('ClearProperty(HBM.StartupSplash,home)')


def open_startup_window():
    xbmc.executebuiltin('ReplaceWindow(%s)' % xbmc.getInfoLabel('System.StartupWindow'))


def intro_path():
    if xbmc.getCondVisibility('Skin.HasSetting(hbm_intro_off)'):
        return None
    path = xbmc.getInfoLabel('Skin.String(HBM.IntroVideo)')
    if path and xbmcvfs.exists(path):
        return path
    if xbmcvfs.exists(BUNDLED):
        return BUNDLED
    return None


def main():
    path = intro_path()
    monitor = xbmc.Monitor()
    if not path:
        show_splash(monitor)
        open_startup_window()
        return

    player = xbmc.Player()
    player.play(path, windowed=False)

    waited = 0.0
    while waited < START_TIMEOUT and not monitor.abortRequested():
        if xbmc.getCondVisibility('Window.IsActive(fullscreenvideo)') and player.isPlayingVideo():
            break
        if monitor.waitForAbort(POLL_SECONDS):
            return
        waited += POLL_SECONDS
    else:
        log('intro did not start within %ds, continuing to the hub' % START_TIMEOUT)

    played = 0.0
    while player.isPlayingVideo() and played < MAX_PLAY_SECONDS and not monitor.abortRequested():
        if monitor.waitForAbort(0.1):
            return
        played += 0.1

    show_splash(monitor)
    open_startup_window()


main()
