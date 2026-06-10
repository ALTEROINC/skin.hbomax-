import json
import sqlite3
import zlib
import xbmc
import xbmcgui
import xbmcvfs

DB_PATH = xbmcvfs.translatePath(
    'special://userdata/addon_data/plugin.video.themoviedb.helper/database_v6/ItemBuilder.db'
)


def run():
    dialog = xbmcgui.DialogProgress()
    dialog.create('Refresh All Artwork', 'Reading cache...')

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT id, data FROM simplecache')
        rows = cur.fetchall()
    except Exception as e:
        dialog.close()
        xbmcgui.Dialog().ok('Refresh All Artwork', f'Could not open cache database:\n{e}')
        return

    total = len(rows)
    deleted = 0
    preserved = 0
    skipped = 0

    for i, (row_id, data) in enumerate(rows):
        if dialog.iscanceled():
            break

        dialog.update(
            int(i * 90 / total) if total else 0,
            f'Processing {i + 1} of {total}...'
        )

        try:
            decoded = json.loads(zlib.decompress(data).decode('utf-8'))
        except Exception:
            skipped += 1
            continue

        if not isinstance(decoded, dict) or 'artwork' not in decoded:
            skipped += 1
            continue

        artwork = decoded['artwork']
        has_manual = bool(artwork.get('manual'))

        if has_manual:
            # Keep manual selections — just clear fanarttv so TMDB Helper re-fetches it
            artwork['fanarttv'] = {}
            decoded['artwork'] = artwork
            new_data = zlib.compress(
                json.dumps(decoded, separators=(',', ':')).encode('utf-8')
            )
            cur.execute('UPDATE simplecache SET data = ? WHERE id = ?', (new_data, row_id))
            preserved += 1
        else:
            # No manual art — delete so TMDB Helper re-fetches everything fresh with FanartTV
            cur.execute('DELETE FROM simplecache WHERE id = ?', (row_id,))
            deleted += 1

    conn.commit()
    conn.close()

    dialog.update(95, 'Rebuilding library index...')
    xbmc.executebuiltin('RunScript(plugin.video.themoviedb.helper,recache_kodidb)', True)

    dialog.close()

    lines = [f'{deleted} items queued for full re-fetch']
    if preserved:
        lines.append(f'{preserved} manual selections preserved')
    xbmcgui.Dialog().notification(
        'HBO Max Skin',
        '  |  '.join(lines),
        time=5000
    )


if __name__ == '__main__':
    run()
