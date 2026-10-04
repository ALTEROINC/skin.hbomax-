import xbmc

# Tag existing TMDb Helper row widgets with hbm_seeall=True so every row ends with a See All
# tile (see the HBM_SEEALL patch in patch_tmdbhelper.py). Genre rows and hero widgets are left alone.
# Runs on every Home load (idempotent) so widgets picked later get tagged too.

HUBS = ('home', 'tvshows', 'movies', 'mylist')
FLAG = 'hbm_seeall=True'


def main():
    for hub in HUBS:
        for n in range(1, 11):
            key = 'hbm_homecfg_%s_row%02d_widget' % (hub, n)
            url = xbmc.getInfoLabel('Skin.String(%s)' % key)
            if not url or 'plugin.video.themoviedb.helper' not in url:
                continue
            if 'info=genres' in url or FLAG in url:
                continue
            xbmc.executebuiltin('Skin.SetString(%s,"%s&%s")' % (key, url.replace('"', ''), FLAG), True)


main()
