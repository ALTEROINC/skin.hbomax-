import sys

import xbmc

HUB_BY_CONTAINER = {
    '620': 'home',
    '621': 'tvshows',
    '622': 'movies',
    '623': 'livetv',
    '624': 'mylist',
}

# Matches the <content limit="6"> on each hero panel. Some widget sources report
# one extra trailing item beyond the requested limit (seen empirically: limit=6
# but Container(id).NumItems reported 7) which renders blank — never rotate into it.
CONTENT_LIMIT = 6


def log(msg):
    xbmc.log('[hero_rotate] ' + msg, level=xbmc.LOGINFO)


def main():
    if len(sys.argv) < 2:
        return

    container_id = sys.argv[1]
    expected_page = HUB_BY_CONTAINER.get(container_id)
    if expected_page is None:
        return

    active_row = xbmc.getInfoLabel('Skin.String(HBM.ActiveRow)')
    active_page = xbmc.getInfoLabel('Skin.String(HBM.HomeActivePage)')

    if active_row != '0' or active_page != expected_page:
        return

    current_raw = xbmc.getInfoLabel('Container(%s).CurrentItem' % container_id)
    total_raw = xbmc.getInfoLabel('Container(%s).NumItems' % container_id)

    try:
        current = int(current_raw)
        total = int(total_raw)
    except ValueError:
        log('container=%s could not parse current=%r total=%r' % (container_id, current_raw, total_raw))
        return

    total = min(total, CONTENT_LIMIT)

    if total < 2:
        log('container=%s total=%d, nothing to rotate' % (container_id, total))
        return

    # Container(id).CurrentItem is 1-based, but SetFocus(id,position) takes a
    # 0-based index — confirmed empirically (asking for 1-based position N landed
    # on 1-based item N+1). Convert before passing it to SetFocus.
    next_pos_1based = (current % total) + 1
    next_pos_0based = next_pos_1based - 1

    return_to = '626' if xbmc.getCondVisibility('Control.HasFocus(626)') else '625'

    xbmc.executebuiltin('SetFocus(%s,%d)' % (container_id, next_pos_0based))
    xbmc.executebuiltin('SetFocus(%s)' % return_to)

    # Kodi's own itemlayout/focusedlayout dot highlight only renders while the
    # panel holds real GUI focus, which we immediately hand back above — so the
    # dots need their own focus-independent driver instead of relying on that.
    xbmc.executebuiltin('Skin.SetString(HBM.HeroDot.%s,%d)' % (container_id, next_pos_1based))

    log('container=%s current=%d total=%d next(1-based)=%d next(0-based)=%d focus restored to %s' % (
        container_id, current, total, next_pos_1based, next_pos_0based, return_to))


main()
