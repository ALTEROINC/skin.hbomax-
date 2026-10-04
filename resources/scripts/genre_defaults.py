import xbmc

# One-time: give the TV Shows and Movies hubs a dedicated 11th row (id 711) showing genres. It is a
# fixed extra row below the ten configurable ones, so no existing row is touched. Its settings can
# be edited later like any other row's skin strings.

PLUGIN = 'plugin://plugin.video.themoviedb.helper/?info=genres&tmdb_type=%s'
HUBS = (('tvshows', 'tv'), ('movies', 'movie'))


def main():
    for hub, tmdb_type in HUBS:
        key = 'hbm_homecfg_%s_row11' % hub
        for name, value in (('label', 'Genres'), ('widget', PLUGIN % tmdb_type),
                            ('visible', 'Visible'), ('style', 'Square')):
            xbmc.executebuiltin('Skin.SetString(%s_%s,%s)' % (key, name, value))
        xbmc.log('[genre_defaults] %s: Genres row set in row 11' % hub, level=xbmc.LOGINFO)
    xbmc.executebuiltin('Skin.SetBool(hbm_genre_row11_v1)')


main()
