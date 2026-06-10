import xbmc
import xbmcgui
import xbmcvfs
import os
import glob

try:
    import xml.etree.ElementTree as ET
    _ET_OK = True
except ImportError:
    _ET_OK = False

_WIN_HOME = 10000


def _set(win, key, value):
    win.setProperty(key, str(value))


def _clear(win, key):
    win.clearProperty(key)


def run():
    win = xbmcgui.Window(_WIN_HOME)

    if not _ET_OK:
        _set(win, 'HBM.IPTV.Error', 'xml module unavailable')
        return

    profile_path = xbmcvfs.translatePath('special://userdata/addon_data/pvr.iptvsimple/')
    pattern = os.path.join(profile_path, 'instance-settings-*.xml')
    files = sorted(glob.glob(pattern))

    # Clear previous data (up to 10 slots)
    for i in range(10):
        _clear(win, 'HBM.IPTV.{}.Name'.format(i))
        _clear(win, 'HBM.IPTV.{}.URL'.format(i))
        _clear(win, 'HBM.IPTV.{}.URLFull'.format(i))
        _clear(win, 'HBM.IPTV.{}.ID'.format(i))
        _clear(win, 'HBM.IPTV.{}.Enabled'.format(i))
        _clear(win, 'HBM.IPTV.{}.SourceType'.format(i))

    instances = []
    for filepath in files:
        instance_id = (os.path.basename(filepath)
                       .replace('instance-settings-', '')
                       .replace('.xml', ''))
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            s = {}
            for node in root.findall('setting'):
                sid = node.get('id', '')
                s[sid] = (node.text or '').strip()

            name = s.get('kodi_addon_instance_name') or 'Instance {}'.format(instance_id)
            enabled = s.get('kodi_addon_instance_enabled', 'true').lower()

            path_type = s.get('m3uPathType', '0')
            if path_type == '1':          # remote URL
                url_full = s.get('m3uUrl', '')
                source_type = 'Remote URL'
            elif path_type == '0':        # local file
                url_full = s.get('m3uPath', '')
                source_type = 'Local file'
            else:
                url_full = s.get('m3uUrl', '') or s.get('m3uPath', '')
                source_type = 'Unknown'

            if not url_full:
                url_full = 'No source configured'
                source_type = 'Not set'

            # Short display version — keep up to 72 chars
            url_display = url_full if len(url_full) <= 72 else url_full[:69] + '...'

            instances.append({
                'id': instance_id,
                'name': name,
                'url_full': url_full,
                'url_display': url_display,
                'enabled': 'true' if enabled == 'true' else 'false',
                'source_type': source_type,
            })
        except Exception as exc:
            xbmc.log('HBM iptv_info: error reading {}: {}'.format(filepath, exc), xbmc.LOGERROR)

    _set(win, 'HBM.IPTV.Count', len(instances))

    for i, inst in enumerate(instances):
        _set(win, 'HBM.IPTV.{}.Name'.format(i), inst['name'])
        _set(win, 'HBM.IPTV.{}.URL'.format(i), inst['url_display'])
        _set(win, 'HBM.IPTV.{}.URLFull'.format(i), inst['url_full'])
        _set(win, 'HBM.IPTV.{}.ID'.format(i), inst['id'])
        _set(win, 'HBM.IPTV.{}.Enabled'.format(i), inst['enabled'])
        _set(win, 'HBM.IPTV.{}.SourceType'.format(i), inst['source_type'])

    xbmc.log('HBM iptv_info: loaded {} instance(s)'.format(len(instances)), xbmc.LOGINFO)


run()
