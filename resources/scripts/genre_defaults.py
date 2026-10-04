import xbmc

# One-time: give the TV Shows and Movies hubs a Genres row in their first empty slot, using the
# existing row settings (label / widget / visible / style), so it can be changed or removed in the
# normal homepage settings afterwards. Rows that already have a widget are never touched.

PLUGIN = 'plugin://plugin.video.themoviedb.helper/?info=genres&tmdb_type=%s'
HUBS = (('tvshows', 'tv'), ('movies', 'movie'))
ROWS = range(1, 11)


def skin_string(name):
    return xbmc.getInfoLabel('Skin.String(%s)' % name)


def main():
    for hub, tmdb_type in HUBS:
        keys = ['hbm_homecfg_%s_row%02d' % (hub, n) for n in ROWS]
        if any(skin_string(k + '_widget') == PLUGIN % tmdb_type for k in keys):
            continue  # already has one
        for key in keys:
            if skin_string(key + '_widget'):
                continue
            xbmc.executebuiltin('Skin.SetString(%s_label,Genres)' % key)
            xbmc.executebuiltin('Skin.SetString(%s_widget,%s)' % (key, PLUGIN % tmdb_type))
            xbmc.executebuiltin('Skin.SetString(%s_visible,Visible)' % key)
            xbmc.executebuiltin('Skin.SetString(%s_style,Square)' % key)
            xbmc.log('[genre_defaults] %s: Genres row set in %s' % (hub, key), level=xbmc.LOGINFO)
            break
    xbmc.executebuiltin('Skin.SetBool(hbm_genre_rows_v1)')


main()
