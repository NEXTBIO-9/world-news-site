#!/usr/bin/env python3
"""Conservative, verifiable NEXT BIO emergency feed.

Automatic coverage: USGS significant large earthquakes (M>=7.0).
Other incident types require verified, timestamped editorial records in
 data/emergency-reviewed.json. RSS publication dates never establish event time.
"""
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'emergency-news.json'
REVIEWED = DATA / 'emergency-reviewed.json'
USGS = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson'
AGE = 30 * 60
ALLOWED = {'war', 'disaster', 'terror', 'emergency', 'battle'}


def utc(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat().replace('+00:00', 'Z')


def safe_url(value, hosts=None):
    try:
        p = urlparse(str(value))
        if p.scheme != 'https' or not p.hostname or p.username or p.password:
            return False
        return hosts is None or p.hostname.lower() in hosts
    except (TypeError, ValueError):
        return False


def load(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def verified_editorial(now):
    """Only explicitly reviewed events with two corroborating source links."""
    raw = load(REVIEWED, {'events': []})
    items = raw.get('events', []) if isinstance(raw, dict) else []
    result = []
    for e in items if isinstance(items, list) else []:
        if not isinstance(e, dict) or e.get('reviewed') is not True:
            continue
        if e.get('type') not in ALLOWED:
            continue
        try:
            when = datetime.fromisoformat(str(e['event_time']).replace('Z', '+00:00'))
            if when.tzinfo is None:
                continue
            seconds = when.timestamp()
        except (ValueError, TypeError, KeyError, OverflowError):
            continue
        if not 0 <= now - seconds <= AGE:
            continue
        sources = e.get('sources')
        if not isinstance(sources, list) or len(sources) < 2 or not all(safe_url(s) for s in sources[:2]):
            continue
        if len({urlparse(s).hostname.lower() for s in sources[:2]}) < 2:
            continue
        title = str(e.get('title_ko') or '').strip()
        if not 12 <= len(title) <= 180 or len(re.findall('[가-힣]', title)) < 6:
            continue
        result.append({'id': str(e.get('id') or sources[0])[:200], 'type': e['type'],
                       'title_ko': title, 'event_time': utc(seconds),
                       'url': sources[0], 'source': '편집 검증', 'verified': True})
    return result


def usgs_events(now):
    req = urllib.request.Request(USGS, headers={'User-Agent': 'NEXTBIO-Emergency/1.0 (public USGS feed)', 'Accept': 'application/geo+json, application/json'})
    with urllib.request.urlopen(req, timeout=18) as response:
        if response.status != 200:
            raise RuntimeError('USGS status ' + str(response.status))
        payload = json.loads(response.read(1_000_000))
    results = []
    for feature in payload.get('features', []):
        if not isinstance(feature, dict):
            continue
        props = feature.get('properties') or {}
        try:
            magnitude = float(props.get('mag'))
            event_seconds = float(props['time']) / 1000
        except (TypeError, ValueError, KeyError):
            continue
        if magnitude < 7.0 or not 0 <= now - event_seconds <= AGE:
            continue
        url = props.get('url')
        if not safe_url(url, {'earthquake.usgs.gov'}):
            continue
        place = re.sub(r'[\r\n<>]', '', str(props.get('place') or '위치 확인 중'))[:100]
        title = f'규모 {magnitude:.1f} 강진 발생 · {place}'
        results.append({'id': 'usgs:' + str(feature.get('id') or url), 'type': 'disaster',
                        'title_ko': title, 'event_time': utc(event_seconds), 'url': url,
                        'source': '미국 지질조사국(USGS)', 'verified': True})
    return results


def main():
    now = datetime.now(timezone.utc).timestamp()
    previous = load(OUT, {})
    old = previous.get('events', []) if isinstance(previous, dict) else []
    existing = [e for e in old if isinstance(e, dict) and e.get('verified') is True and
                e.get('source') == '미국 지질조사국(USGS)' and safe_url(e.get('url'), {'earthquake.usgs.gov'})]
    try:
        fresh = usgs_events(now)
        status = 'ok'
    except Exception as exc:
        fresh = existing  # On an outage, keep only still-fresh previously verified events.
        status = 'source_unavailable_' + type(exc).__name__
        print('USGS unavailable:', type(exc).__name__)
    all_events = fresh + verified_editorial(now)
    dedup = {}
    for e in all_events:
        try:
            ts = datetime.fromisoformat(e['event_time'].replace('Z', '+00:00')).timestamp()
        except (ValueError, KeyError, TypeError):
            continue
        if 0 <= now - ts <= AGE and safe_url(e.get('url')):
            dedup[e['id']] = e
    selected = sorted(dedup.values(), key=lambda e: e['event_time'], reverse=True)[:30]
    # Avoid committing unchanged data every five minutes (and rebuilding Pages).
    previous_events = previous.get('events', []) if isinstance(previous, dict) else []
    if selected == previous_events:
        print('No change in verified emergency events; no commit needed.')
        return
    result = {'updated': utc(now), 'status': status, 'events': selected}
    DATA.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Verified emergency events:', len(result['events']), 'source:', status)


if __name__ == '__main__':
    main()
