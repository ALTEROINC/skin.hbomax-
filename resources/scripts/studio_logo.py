import json
import re
import time
import urllib.error
import urllib.request

import xbmc
import xbmcgui
import xbmcvfs

# Shows the focused title's original network (TV) or studio (movies) as a logo in the hero.
#
# One poller, started from Home's onload. About every 0.25s it looks at the focused title (a row item, or the
# hero carousel item while the hero is focused). When the title has stayed the same for DEBOUNCE seconds it
# resolves the network/studio name and maps it to one of the bundled logos (media/studios/<key>.png). The
# result is published as Window(Home) property HBM.StudioLogo, which Home.xml draws. The property is cleared
# the moment focus moves, so a stale logo never lingers.
#
# Name lookup:
#   1. the focused item's own data, if it already has it (Property network / studio, or ListItem.Studio);
#   2. otherwise TMDb Helper's details route through JSON-RPC (its own API key and cache; no key needed here).
# TV uses the first network only. Movies use the first production company that has a bundled logo.
# The names found are cached on disk so each title is looked up once (the logo is re-picked from them, so
# adding aliases or logos later takes effect without clearing the cache).

HOME = 10000
PROP = 'HBM.StudioLogo'
BADGE_PROP = 'HBM.StudioLogoBadge'   # set when the logo is TMDb's (drawn on a light badge)
POLLER_PROP = 'HBM.StudioPoller'
LOGO_DIR = 'special://skin/media/studios/'
CACHE_FILE = 'special://profile/addon_data/skin.hbomax.dev/studio_cache.json'
HERO_CONTAINER = {'home': '620', 'tvshows': '621', 'movies': '622'}
POLL_SECONDS = 0.25
DEBOUNCE = 0.35
CLOSED_GRACE = 3.0
DETAILS = 'plugin://plugin.video.themoviedb.helper/?info=details&tmdb_type=%s&tmdb_id=%s'

# Normalised TMDb name -> bundled logo key. Normalising = lowercase, letters/digits only.
ALIASES = {
    'ae': 'ae', 'aande': 'ae', 'a24': 'a24', 'abc': 'abc', 'abcsignature': 'abc', 'abcstudios': 'abc',
    'amc': 'amc', 'amcplus': 'amc', 'appletv': 'appletv', 'appletvplus': 'appletv', 'appletvstudios': 'appletv',
    'appleoriginalfilms': 'appletv', 'apple': 'appletv', 'bbcstudios': 'bbcstudios', 'bet': 'bet', 'betplus': 'bet',
    'bravo': 'bravo', 'cbs': 'cbs', 'cbsstudios': 'cbs', 'cnn': 'cnn', 'cartoonnetwork': 'cartoonnetwork',
    'cinemax': 'cinemax', 'comedycentral': 'comedycentral', 'discoveryplus': 'discoveryplus',
    'disneyplus': 'disneyplus', 'disney': 'disneyplus',
    'waltdisneypictures': 'disneyplus', 'disneychannel': 'disneyplus', 'espn': 'espn', 'fox': 'fox',
    'foxbroadcastingcompany': 'fox', 'twentiethcenturyfox': 'fox', 'freeform': 'freeform',
    'history': 'history', 'thehistorychannel': 'history', 'historychannel': 'history', 'hulu': 'hulu',
    'lifetime': 'lifetime', 'max': 'max', 'hbomax': 'max', 'hbo': 'max', 'mgm': 'mgm',
    'metrogoldwynmayer': 'mgm', 'metrogoldwynmayerpictures': 'mgm', 'mgmplus': 'mgm', 'marvelstudios': 'marvel',
    'marveltelevision': 'marvel', 'marvelentertainment': 'marvel', 'marvel': 'marvel', 'nbc': 'nbc',
    'nationalgeographic': 'nationalgeographic', 'natgeo': 'nationalgeographic', 'netflix': 'netflix',
    'paramountplus': 'paramountplus', 'paramount': 'paramount', 'paramountpictures': 'paramount',
    'paramountnetwork': 'paramountnetwork', 'peacock': 'peacock', 'primevideo': 'primevideo', 'amazon': 'primevideo',
    'amazonprimevideo': 'primevideo', 'amazonstudios': 'primevideo', 'amazonmgmstudios': 'primevideo',
    'starz': 'starz', 'tlc': 'tlc', 'universalpictures': 'universal', 'universalstudios': 'universal',
    'universaltelevision': 'universal', 'universal': 'universal', 'vicetv': 'vicetv', 'viceland': 'vicetv',
    'warnerbros': 'wb', 'warnerbrospictures': 'wb', 'warnerbrostelevision': 'wb', 'warnerbrosentertainment': 'wb',
    'warnerbrosanimation': 'wb', 'wb': 'wb',
}


def log(msg):
    xbmc.log('[studio_logo] ' + msg, level=xbmc.LOGINFO)


def norm(name):
    return re.sub(r'[^a-z0-9]', '', (name or '').lower().replace('&', 'and').replace('+', 'plus'))


def logo_key(name):
    n = norm(name)
    key = ALIASES.get(n)
    if key and xbmcvfs.exists('%s%s.png' % (LOGO_DIR, key)):
        return key
    return None


def load_cache():
    try:
        f = xbmcvfs.File(CACHE_FILE)
        try:
            return json.loads(f.read() or '{}')
        finally:
            f.close()
    except Exception:
        return {}


def save_cache(cache):
    try:
        xbmcvfs.mkdirs('special://profile/addon_data/skin.hbomax.dev/')
        f = xbmcvfs.File(CACHE_FILE, 'w')
        try:
            f.write(json.dumps(cache))
        finally:
            f.close()
    except Exception as e:
        log('could not save cache: %s' % e)


def tmdb_logo(tmdb_type, tmdb_id):
    """TMDb's own logo URL for the original network (TV) or first studio with a logo (movies), or ''.
    Needs the key from Skin Settings (a v3 API key, or a v4 read access token). Returns None when there is no key or the
    request failed, so the caller doesn't remember it."""
    key = xbmc.getInfoLabel('Skin.String(HBM.TMDbKey)').strip()
    if not key:
        return None          # no key yet: don't remember an answer
    url = 'https://api.themoviedb.org/3/%s/%s' % (tmdb_type, tmdb_id)
    headers = {'Accept': 'application/json'}
    if key.startswith('eyJ'):
        headers['Authorization'] = 'Bearer ' + key
    else:
        url += '?api_key=' + key
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=6) as r:
            data = json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        log('TMDb request for %s %s failed: HTTP %s' % (tmdb_type, tmdb_id, e.code))
        return None
    except Exception as e:
        log('TMDb request for %s %s failed: %s' % (tmdb_type, tmdb_id, type(e).__name__))
        return None
    if tmdb_type == 'tv':
        entries = (data.get('networks') or [])[:1]          # original network only
    else:
        entries = data.get('production_companies') or []
    for entry in entries:
        if entry.get('logo_path'):
            return 'https://image.tmdb.org/t/p/w300' + entry['logo_path']
    return ''


def info(prefix, field):
    return xbmc.getInfoLabel('%s.%s' % (prefix, field))


def names_from_item(prefix, tmdb_type):
    """Names the focused item already carries, if any."""
    if tmdb_type == 'tv':
        network = info(prefix, 'Property(network)')
        if network:
            return [network.split(' / ')[0]]
    studio = info(prefix, 'Studio')
    if studio:
        return [s.strip() for s in studio.split(' / ') if s.strip()]
    return []


def names_from_details(tmdb_type, tmdb_id):
    request = {
        'jsonrpc': '2.0', 'id': 1, 'method': 'Files.GetDirectory',
        'params': {'directory': DETAILS % (tmdb_type, tmdb_id), 'media': 'video', 'properties': ['studio']},
    }
    try:
        reply = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
        files = reply.get('result', {}).get('files') or []
        for item in files:
            studio = item.get('studio') or []
            if isinstance(studio, str):
                studio = [studio]
            if studio:
                return studio
    except Exception as e:
        log('details lookup failed for %s %s: %s' % (tmdb_type, tmdb_id, e))
    return []


def pick(names, tmdb_type):
    """Bundled logo key for the original network (TV: first only) or studio (movies: first with a logo)."""
    if tmdb_type == 'tv':
        return logo_key(names[0]) if names else None
    for name in names:
        key = logo_key(name)
        if key:
            return key
    return None


def focused_title():
    """(prefix, tmdb_type, tmdb_id) for the focused title, or None."""
    page = xbmc.getInfoLabel('Skin.String(HBM.HomeActivePage)')
    if page not in HERO_CONTAINER:
        return None
    row = xbmc.getInfoLabel('Skin.String(HBM.ActiveRow)')
    prefix = 'ListItem' if row not in ('', '0') else 'Container(%s).ListItem' % HERO_CONTAINER[page]
    tmdb_id = info(prefix, 'Property(tmdb_id)')
    tmdb_type = info(prefix, 'Property(tmdb_type)')
    if not tmdb_type:
        tmdb_type = {'movie': 'movie', 'tvshow': 'tv', 'season': 'tv', 'episode': 'tv'}.get(info(prefix, 'DBType'), '')
    if not tmdb_id or tmdb_type not in ('movie', 'tv'):
        return None
    return prefix, tmdb_type, tmdb_id


def clear(win):
    win.clearProperty(PROP)
    win.clearProperty(BADGE_PROP)


def main():
    win = xbmcgui.Window(HOME)
    beat = win.getProperty(POLLER_PROP)
    if beat and time.time() - float(beat) < 2:
        return  # one poller at a time

    monitor = xbmc.Monitor()
    cache = load_cache()
    current = None        # (type, id) of the title the published logo belongs to
    pending = None        # (type, id, prefix, since) waiting out the debounce
    closed_since = None
    try:
        while not monitor.abortRequested():
            win.setProperty(POLLER_PROP, str(time.time()))

            if not xbmc.getCondVisibility('Window.IsVisible(home)'):
                closed_since = closed_since or time.time()
                if time.time() - closed_since > CLOSED_GRACE:
                    break
                if monitor.waitForAbort(POLL_SECONDS):
                    break
                continue
            closed_since = None

            title = focused_title()
            if not title:
                if current is not None or pending is not None:
                    clear(win)
                current = pending = None
            else:
                prefix, tmdb_type, tmdb_id = title
                ident = (tmdb_type, tmdb_id)
                if ident != current and (pending is None or pending[:2] != ident):
                    clear(win)                         # focus moved: drop the old logo now
                    current = None
                    pending = (tmdb_type, tmdb_id, prefix, time.time())
                elif pending is not None and time.time() - pending[3] >= DEBOUNCE:
                    key = '%s:%s' % (tmdb_type, tmdb_id)
                    names = cache.get(key)
                    if names is None:
                        names = names_from_item(prefix, tmdb_type) or names_from_details(tmdb_type, tmdb_id)
                        if names:   # an empty answer may just be a failed lookup: don't remember it
                            cache[key] = names
                            save_cache(cache)
                    logo = pick(names, tmdb_type) or ''
                    remote = ''
                    if not logo:
                        remote = cache.get('logo:' + key)
                        if remote is None:
                            remote = tmdb_logo(tmdb_type, tmdb_id)
                            if remote is not None:        # None = request failed; try again next time
                                cache['logo:' + key] = remote
                                save_cache(cache)
                    log('%s -> %s (names: %s)' % (key, logo or ('TMDb logo' if remote else 'no logo'), ', '.join(names[:4])))
                    # Only publish if focus is still on this title.
                    again = focused_title()
                    if again and (again[1], again[2]) == (tmdb_type, tmdb_id):
                        if logo:
                            win.setProperty(PROP, '%s%s.png' % (LOGO_DIR, logo))
                        elif remote:
                            win.setProperty(BADGE_PROP, '1')
                            win.setProperty(PROP, remote)
                        current = (tmdb_type, tmdb_id)
                    pending = None

            if monitor.waitForAbort(POLL_SECONDS):
                break
    finally:
        clear(win)
        win.clearProperty(POLLER_PROP)


main()
