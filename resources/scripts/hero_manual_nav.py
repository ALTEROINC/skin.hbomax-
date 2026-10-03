import sys

import xbmc

# Matches hero_rotate.py's CONTENT_LIMIT — some widget sources report one extra
# trailing item beyond the requested <content limit="6"> which renders blank.
CONTENT_LIMIT = 6


def log(msg):
    xbmc.log('[hero_manual_nav] ' + msg, level=xbmc.LOGINFO)


def main():
    if len(sys.argv) < 3:
        return

    container_id = sys.argv[1]
    direction = sys.argv[2]

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
        return

    # Container(id).CurrentItem is 1-based, SetFocus(id,position) is 0-based —
    # same conversion hero_rotate.py uses.
    if direction == 'next':
        next_pos_1based = (current % total) + 1
    else:
        next_pos_1based = ((current - 2) % total) + 1
    next_pos_0based = next_pos_1based - 1

    return_to = '626' if xbmc.getCondVisibility('Control.HasFocus(626)') else '625'

    xbmc.executebuiltin('SetFocus(%s,%d)' % (container_id, next_pos_0based))
    xbmc.executebuiltin('SetFocus(%s)' % return_to)
    xbmc.executebuiltin('Skin.SetString(HBM.HeroDot.%s,%d)' % (container_id, next_pos_1based))

    log('container=%s direction=%s current=%d total=%d next(1-based)=%d' % (
        container_id, direction, current, total, next_pos_1based))


main()
