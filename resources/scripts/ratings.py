import json
import time
import urllib.error
import urllib.request

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

# IMDb and Rotten Tomatoes scores for the title on the info page (DialogVideoInfo), shown on the line above the
# Watch button. Started from the dialog's onload; fetches once, publishes Window(Home) properties
#   HBM.RateIMDb  e.g. "8.3"       HBM.RateRT  e.g. "94%"
# and does nothing if the keys are missing. Keys are the ones already set in TMDb Helper's settings
# (mdblist_apikey, omdb_apikey); they are never logged.
#
#   1. MDBList (one request by TMDb id gives both scores);
#   2. OMDb (by IMDb id) for whatever MDBList did not provide.
# Scores are cached on disk for a week.

HOME = 10000
PROP_IMDB = 'HBM.RateIMDb'
PROP_RT = 'HBM.RateRT'
CACHE_FILE = 'special://profile/addon_data/skin.hbomax.dev/ratings_cache.json'
CACHE_DAYS = 7
TIMEOUT = 6
TMDB_HELPER = 'plugin.video.themoviedb.helper'


def log(msg):
    xbmc.log('[ratings] ' + msg, level=xbmc.LOGINFO)


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
        log('could not save cache: %s' % type(e).__name__)


def get_json(url, what):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'Accept': 'application/json'}),
                                    timeout=TIMEOUT) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        log('%s request failed: HTTP %s' % (what, e.code))
    except Exception as e:
        log('%s request failed: %s' % (what, type(e).__name__))
    return None


def setting(name):
    try:
        return xbmcaddon.Addon(TMDB_HELPER).getSetting(name).strip()
    except Exception:
        return ''


def fmt_imdb(value):
    try:
        v = float(str(value).replace(',', '.'))
        return '%.1f' % v if v > 0 else ''
    except (TypeError, ValueError):
        return ''


def fmt_rt(value):
    try:
        v = int(float(str(value).replace('%', '')))
        return '%d%%' % v if v > 0 else ''
    except (TypeError, ValueError):
        return ''


def from_mdblist(tmdb_id, media):
    key = setting('mdblist_apikey')
    if not key or not tmdb_id:
        return {}
    data = get_json('https://mdblist.com/api/?apikey=%s&tm=%s&m=%s' % (key, tmdb_id, media), 'MDBList')
    out = {}
    for rating in (data or {}).get('ratings') or []:
        source = (rating.get('source') or '').lower()
        if source == 'imdb':
            out['imdb'] = fmt_imdb(rating.get('value'))
        elif source == 'tomatoes':
            out['rt'] = fmt_rt(rating.get('value'))
    if data and data.get('imdbid'):
        out['imdbid'] = data['imdbid']
    return out


def from_omdb(imdb_id):
    key = setting('omdb_apikey')
    if not key or not imdb_id:
        return {}
    data = get_json('https://www.omdbapi.com/?apikey=%s&i=%s' % (key, imdb_id), 'OMDb')
    if not data or data.get('Response') == 'False':
        return {}
    out = {'imdb': fmt_imdb(data.get('imdbRating'))}
    for rating in data.get('Ratings') or []:
        if rating.get('Source') == 'Rotten Tomatoes':
            out['rt'] = fmt_rt(rating.get('Value'))
    return out


def lookup(tmdb_id, media, imdb_id):
    scores = from_mdblist(tmdb_id, media)
    imdb_id = imdb_id or scores.get('imdbid', '')
    if not (scores.get('imdb') and scores.get('rt')):
        extra = from_omdb(imdb_id)
        for k in ('imdb', 'rt'):
            if not scores.get(k) and extra.get(k):
                scores[k] = extra[k]
    return {'imdb': scores.get('imdb', ''), 'rt': scores.get('rt', '')}


def main():
    win = xbmcgui.Window(HOME)
    win.clearProperty(PROP_IMDB)
    win.clearProperty(PROP_RT)

    tmdb_id = xbmc.getInfoLabel('ListItem.UniqueID(tmdb)')
    media = 'movie' if xbmc.getInfoLabel('ListItem.DBTYPE') == 'movie' else 'show'
    imdb_id = xbmc.getInfoLabel('ListItem.UniqueID(imdb)') or xbmc.getInfoLabel('ListItem.IMDBNumber')
    if not tmdb_id and not imdb_id:
        return

    key = '%s:%s' % (media, tmdb_id or imdb_id)
    cache = load_cache()
    entry = cache.get(key)
    if entry and time.time() - entry.get('t', 0) < CACHE_DAYS * 86400:
        scores = entry
    else:
        scores = lookup(tmdb_id, media, imdb_id)
        if scores['imdb'] or scores['rt']:
            cache[key] = dict(scores, t=time.time())
            save_cache(cache)
        log('%s -> imdb=%s rt=%s' % (key, scores['imdb'] or '-', scores['rt'] or '-'))

    # Only publish if the dialog is still open on the same title.
    if xbmc.getCondVisibility('Window.IsActive(movieinformation)') \
            and xbmc.getInfoLabel('ListItem.UniqueID(tmdb)') == tmdb_id:
        if scores.get('imdb'):
            win.setProperty(PROP_IMDB, scores['imdb'])
        if scores.get('rt'):
            win.setProperty(PROP_RT, scores['rt'])


main()
