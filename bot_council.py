#!/usr/bin/env python3
"""
Hancock Bot Council
===================
Runs scanner bots and prepares one concise feedback feed for the Main Speaking Bot.

Outputs:
  data/main_speaking_bot_feed.json
  data/main_speaking_bot_feed.js

Inputs:
  data/latest_bot.json from marketing_bot.py
  National Weather Service API for storm alerts
"""
import datetime as dt
import csv
import io
import json
import os
import re
import subprocess
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
PLAYBOOK = ROOT / 'Ryan_Knight_Inspection_Industry_Playbook.md'
LATEST_BOT = DATA / 'latest_bot.json'
OUT_JSON = DATA / 'main_speaking_bot_feed.json'
OUT_JS = DATA / 'main_speaking_bot_feed.js'
WATCH_STATES = ['TX','OK','KS','NE','CO','MO','IA','IL','IN','OH','KY','TN','AR','MS','AL','GA','NC','SC','FL','LA','MN','WI','SD','ND','WY','NM','PA','WV','VA']
STORM_RX = re.compile(r'tornado|thunderstorm|hail|flood|hurricane|tropical|high wind|wind warning|storm|derecho|red flag|wildfire|fire weather|excessive rainfall', re.I)
EXCLUDED_ALERT_RX = re.compile(r'air quality|heat advisory|excessive heat|dense fog|freezing fog|frost|freeze|beach hazards|rip current|small craft|gale warning|lake wind|dust advisory', re.I)
CORE_HAZARD_GROUPS = {'tornado','hail_wind','derecho','hurricane'}
CONTENTS_HAZARD_GROUPS = {'water_contents','fire_contents'}
REPORT_HAZARD_GROUPS = {'tornado_report','hail_report','wind_report'}
SEVERITY_RANK = {'Extreme':0,'Severe':1,'Moderate':2,'Minor':3}
NHC_FEEDS = [
    ('Atlantic', 'https://www.nhc.noaa.gov/index-at.xml'),
    ('Eastern Pacific', 'https://www.nhc.noaa.gov/index-ep.xml'),
]
SPC_OUTLOOK_FEEDS = [
    ('Day 1', 'Tornado', 'tornado_outlook', 'https://www.spc.noaa.gov/products/outlook/day1otlk_torn.nolyr.geojson'),
    ('Day 1', 'Hail', 'hail_wind', 'https://www.spc.noaa.gov/products/outlook/day1otlk_hail.nolyr.geojson'),
    ('Day 1', 'Wind', 'hail_wind', 'https://www.spc.noaa.gov/products/outlook/day1otlk_wind.nolyr.geojson'),
    ('Day 1', 'Categorical', 'convective_outlook', 'https://www.spc.noaa.gov/products/outlook/day1otlk_cat.nolyr.geojson'),
    ('Day 2', 'Tornado', 'tornado_outlook', 'https://www.spc.noaa.gov/products/outlook/day2otlk_torn.nolyr.geojson'),
    ('Day 2', 'Hail', 'hail_wind', 'https://www.spc.noaa.gov/products/outlook/day2otlk_hail.nolyr.geojson'),
    ('Day 2', 'Wind', 'hail_wind', 'https://www.spc.noaa.gov/products/outlook/day2otlk_wind.nolyr.geojson'),
    ('Day 2', 'Categorical', 'convective_outlook', 'https://www.spc.noaa.gov/products/outlook/day2otlk_cat.nolyr.geojson'),
]
SPC_REPORT_FEEDS = [
    ('today', 'https://www.spc.noaa.gov/climo/reports/today.csv'),
    ('yesterday', 'https://www.spc.noaa.gov/climo/reports/yesterday.csv'),
]


def now_human():
    return dt.datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')


def load_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return fallback
def playbook_status():
    return {
        'source': PLAYBOOK.name,
        'loaded': PLAYBOOK.exists(),
        'authority': "Ryan Knight's Inspection Industry Playbook",
        'role': 'Foundational operating model',
        'rule': 'New learning must be traceable, current, relevant, and clearly labeled by confidence.'
    }


def ensure_marketing_scan():
    if LATEST_BOT.exists():
        return
    subprocess.run(['python3', 'marketing_bot.py'], cwd=str(ROOT), timeout=90)


def clean_text(value, limit=None):
    text = re.sub(r'<[^>]+>', ' ', value or '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:limit].rstrip() if limit else text


def fetch_json(url, accept='application/json'):
    req = urllib.request.Request(url, headers={'User-Agent':'HancockMarketingBot/1.0','Accept':accept})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read())


def fetch_text(url, accept='text/plain'):
    req = urllib.request.Request(url, headers={'User-Agent':'HancockMarketingBot/1.0','Accept':accept})
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.read().decode('utf-8', errors='replace')


def alert_blob(properties):
    fields = (
        properties.get('event'),
        properties.get('headline'),
        properties.get('description'),
        properties.get('instruction'),
        properties.get('areaDesc'),
    )
    return ' '.join(str(part or '') for part in fields).lower()


def numeric_value(value):
    try:
        return float(str(value or '').strip())
    except ValueError:
        return None


def geometry_bbox(geometry):
    coords = []

    def walk(node):
        if isinstance(node, (list, tuple)) and len(node) == 2 and all(isinstance(x, (int, float)) for x in node):
            coords.append((float(node[0]), float(node[1])))
        elif isinstance(node, (list, tuple)):
            for child in node:
                walk(child)

    walk((geometry or {}).get('coordinates') or [])
    if not coords:
        return ''
    lons = [lon for lon, _ in coords]
    lats = [lat for _, lat in coords]
    return f"bbox lon {min(lons):.1f} to {max(lons):.1f}, lat {min(lats):.1f} to {max(lats):.1f}"


def spc_outlook_priority(day, hazard_name, properties):
    label = str(properties.get('LABEL2') or properties.get('LABEL') or '')
    dn = numeric_value(properties.get('DN')) or 0
    text = f'{hazard_name} {label}'.lower()
    if dn <= 0 or 'less than' in text or 'tstm' in text or 'general thunder' in text:
        return 0
    day_penalty = 0 if day == 'Day 1' else 7
    priority = 45
    if hazard_name in ('Hail', 'Wind'):
        priority = 65 + min(int(dn), 60) // 2
        if 'sig' in text or 'significant' in text:
            priority += 10
    elif hazard_name == 'Tornado':
        priority = 70 + min(int(dn), 45) // 2
        if 'sig' in text or 'significant' in text:
            priority += 12
    elif hazard_name == 'Categorical':
        priority = {
            'mrgl': 52,
            'slgt': 66,
            'enh': 78,
            'mdt': 90,
            'high': 98,
        }.get(str(properties.get('LABEL') or '').lower(), 0)
    return max(priority - day_penalty, 0)


def spc_outlook_signals():
    signals = []
    failed = []
    for day, hazard_name, group, url in SPC_OUTLOOK_FEEDS:
        try:
            data = fetch_json(url, 'application/geo+json, application/json')
        except Exception:
            failed.append(f'{day} {hazard_name}')
            continue
        for feature in data.get('features') or []:
            props = feature.get('properties') or {}
            priority = spc_outlook_priority(day, hazard_name, props)
            if priority <= 0:
                continue
            label = clean_text(props.get('LABEL2') or props.get('LABEL') or f'{hazard_name} Risk')
            if hazard_name == 'Categorical':
                hazard = f'SPC {day} Severe Thunderstorm Outlook'
                service = 'Storm / CAT Damage'
                angle = 'Use this as a forecast signal. Watch for later hail, damaging wind, and tornado reports before treating it as post-storm volume.'
            elif hazard_name == 'Tornado':
                hazard = f'SPC {day} Tornado Risk'
                service = 'Storm / CAT Damage'
                angle = 'Forecast signal for rotating storms. Prepare safety-first content now and post-event structural, roof, exterior, and contents documentation guidance later.'
            elif hazard_name == 'Hail':
                hazard = f'SPC {day} Hail Risk'
                service = 'Storm / CAT Damage'
                angle = 'Forecast signal for Hancock core volume. Prepare roof, siding, exterior, openings, hail-size, and original-photo documentation guidance.'
            else:
                hazard = f'SPC {day} Damaging Wind Risk'
                service = 'Storm / CAT Damage'
                angle = 'Forecast signal for straight-line wind and roof/exterior damage. Prepare wind documentation and post-event inspection readiness content.'
            areas = geometry_bbox(feature.get('geometry') or {}) or f'{day} SPC outlook area'
            signals.append({
                'state': 'SPC',
                'event': f'{day} {hazard_name} Outlook',
                'severity': 'Moderate' if priority < 80 else 'Severe',
                'headline': f'{hazard}: {label}',
                'areas': areas,
                'expires': props.get('EXPIRE_ISO') or '',
                'sent': props.get('ISSUE_ISO') or '',
                'effective': props.get('VALID_ISO') or '',
                'onset': props.get('VALID_ISO') or '',
                'ends': props.get('EXPIRE_ISO') or '',
                'description': f"Official SPC {day.lower()} {hazard_name.lower()} outlook: {label}. Forecaster: {props.get('FORECASTER') or 'SPC'}.",
                'hazard': hazard,
                'hazard_group': 'tornado' if group == 'tornado_outlook' else group,
                'hancock_priority': priority,
                'service_line': service,
                'volume_signal': 'High' if priority >= 80 else 'Medium',
                'content_angle': angle,
                'posture': 'Forecast signal. Do not imply damage occurred until reports or safe post-event observations support it.',
                'source': 'Storm Prediction Center outlook',
                'url': url,
            })
    return signals, failed


def spc_report_priority(report_type, row):
    if report_type == 'tornado':
        scale = str(row.get('F_Scale') or 'UNK')
        return 98 if scale.upper() != 'UNK' else 94
    if report_type == 'wind':
        speed = numeric_value(row.get('Speed'))
        if speed is None:
            return 84
        if speed >= 75:
            return 94
        if speed >= 65:
            return 90
        if speed >= 58:
            return 86
        return 78
    if report_type == 'hail':
        size = numeric_value(row.get('Size'))
        if size is None:
            return 78
        if size >= 275:
            return 96
        if size >= 200:
            return 92
        if size >= 175:
            return 89
        if size >= 100:
            return 84
        return 76
    return 0


def spc_report_signals():
    signals = []
    failed = []
    for label, url in SPC_REPORT_FEEDS:
        try:
            text = fetch_text(url, 'text/csv')
        except Exception:
            failed.append(label)
            continue
        section = None
        fieldnames = []
        for raw_row in csv.reader(io.StringIO(text)):
            if not raw_row:
                continue
            if raw_row[0] == 'Time':
                fieldnames = raw_row
                if 'F_Scale' in raw_row:
                    section = 'tornado'
                elif 'Speed' in raw_row:
                    section = 'wind'
                elif 'Size' in raw_row:
                    section = 'hail'
                else:
                    section = None
                continue
            if not section or not fieldnames:
                continue
            row = {fieldnames[i]: raw_row[i] if i < len(raw_row) else '' for i in range(len(fieldnames))}
            state = row.get('State') or ''
            location = row.get('Location') or ''
            county = row.get('County') or ''
            comments = clean_text(row.get('Comments') or '', 500)
            priority = spc_report_priority(section, row)
            if priority <= 0:
                continue
            if section == 'tornado':
                hazard = 'SPC Preliminary Tornado Report'
                event = 'Preliminary Tornado Report'
                group = 'tornado_report'
                service = 'Storm / CAT Damage'
                angle = 'Actual tornado report. Build safety-first follow-up and post-event structural, roof, exterior, debris impact, and contents documentation guidance.'
                measure = row.get('F_Scale') or 'UNK'
            elif section == 'wind':
                hazard = 'SPC Preliminary Damaging Wind Report'
                event = 'Preliminary Wind Report'
                group = 'wind_report'
                service = 'Storm / CAT Damage'
                angle = 'Actual damaging wind report. Prioritize roof edge, exterior elevations, openings, trees/debris impact, and file documentation guidance.'
                measure = f"{row.get('Speed') or 'UNK'} mph"
            else:
                hazard = 'SPC Preliminary Hail Report'
                event = 'Preliminary Hail Report'
                group = 'hail_report'
                service = 'Storm / CAT Damage'
                angle = 'Actual hail report. Prioritize roof, soft metals, siding, elevations, hail size, and original-photo preservation guidance.'
                size = numeric_value(row.get('Size'))
                measure = f"{size / 100:.2f} in" if size is not None else 'UNK size'
            signals.append({
                'state': state,
                'event': event,
                'severity': 'Severe',
                'headline': f'{hazard}: {measure} near {location}, {state}',
                'areas': ', '.join(part for part in (location, county, state) if part),
                'expires': '',
                'sent': '',
                'effective': '',
                'onset': row.get('Time') or '',
                'ends': '',
                'description': comments,
                'hazard': hazard,
                'hazard_group': group,
                'hancock_priority': priority,
                'service_line': service,
                'volume_signal': 'High' if priority >= 86 else 'Medium',
                'content_angle': angle,
                'posture': 'Preliminary SPC report. Treat as a strong signal, but label it preliminary and avoid property-specific claims.',
                'source': 'Storm Prediction Center preliminary storm reports',
                'url': url,
            })
    return signals, failed


def hancock_storm_classification(properties):
    blob = alert_blob(properties)
    event = str(properties.get('event') or '').lower()
    classification = {
        'hazard': 'Weather / Monitoring',
        'hazard_group': 'monitor',
        'hancock_priority': 25,
        'service_line': 'Storm / CAT Damage',
        'volume_signal': 'Monitor',
        'content_angle': 'Monitor official updates and prepare documentation-first guidance if property conditions change.',
        'posture': 'Monitor only unless official guidance or local conditions warrant a safety-first update.',
    }
    if EXCLUDED_ALERT_RX.search(blob):
        classification['hancock_priority'] = 0
        return classification
    if not STORM_RX.search(blob):
        classification['hancock_priority'] = 0
        return classification
    if re.search(r'tornado emergency|particularly dangerous situation', blob):
        classification.update({
            'hazard': 'Tornado Emergency / PDS',
            'hazard_group': 'tornado',
            'hancock_priority': 100,
            'volume_signal': 'Extreme',
            'content_angle': 'Safety-first now. After the warning expires, shift to structural, roof, exterior, and contents documentation guidance.',
            'posture': 'Active life-safety messaging only until the warning clears.',
        })
    elif re.search(r'tornado warning|tornado watch|\btornado\b', blob):
        classification.update({
            'hazard': 'Tornado',
            'hazard_group': 'tornado',
            'hancock_priority': 95 if 'warning' in event else 82,
            'volume_signal': 'High',
            'content_angle': 'Prepare post-event inspection content around roof, exterior envelope, structural indicators, debris impact, and contents documentation.',
            'posture': 'Safety-first while active; documentation guidance after authorities say it is safe.',
        })
    elif re.search(r'derecho', blob):
        classification.update({
            'hazard': 'Derecho / Widespread Straight-line Wind',
            'hazard_group': 'derecho',
            'hancock_priority': 94,
            'volume_signal': 'High',
            'content_angle': 'Lead with widespread wind damage documentation: roofs, elevations, openings, trees/debris, and consistent file intake.',
            'posture': 'Safety-first during the event; post-event inspection readiness once the line passes.',
        })
    elif re.search(r'severe thunderstorm warning|destructive thunderstorm|considerable damage|damaging wind|straight[- ]line|wind damage|\b[6-9]\d\s*mph|1\d{2}\s*mph|hail|\b[1-9](?:\.\d+)?\s*inch hail|quarter size hail|golf ball', blob):
        classification.update({
            'hazard': 'Hail / Damaging Thunderstorm Wind',
            'hazard_group': 'hail_wind',
            'hancock_priority': 90,
            'volume_signal': 'High',
            'content_angle': 'This is the core Hancock storm signal: roof, siding, exterior, openings, and photo documentation before files pile up.',
            'posture': 'Safety-first while active; move quickly to post-storm documentation and inspection education afterward.',
        })
    elif re.search(r'extreme wind warning|high wind warning|high wind watch|wind advisory|damaging winds|straight[- ]line', blob):
        classification.update({
            'hazard': 'High Wind / Straight-line Wind',
            'hazard_group': 'hail_wind',
            'hancock_priority': 86,
            'volume_signal': 'High',
            'content_angle': 'Focus on wind-created exterior damage, roof edge conditions, openings, trees/debris impact, and defensible documentation.',
            'posture': 'Safety-first while active; post-event inspection education once safe.',
        })
    elif re.search(r'hurricane warning|hurricane watch|tropical storm warning|tropical storm watch|potential tropical cyclone|storm surge|hurricane|tropical storm', blob):
        classification.update({
            'hazard': 'Hurricane / Tropical Wind',
            'hazard_group': 'hurricane',
            'hancock_priority': 84,
            'volume_signal': 'High',
            'content_angle': 'Track wind, roof, opening, exterior, storm surge, and contents documentation needs before CAT volume arrives.',
            'posture': 'Preparedness before impact, safety-first during impact, documentation guidance after impact.',
        })
    elif re.search(r'severe thunderstorm watch', blob):
        classification.update({
            'hazard': 'Severe Thunderstorm Watch',
            'hazard_group': 'hail_wind',
            'hancock_priority': 72,
            'volume_signal': 'Medium',
            'content_angle': 'Use as a readiness signal for hail/wind education and post-storm documentation reminders.',
            'posture': 'Preparedness messaging; do not imply damage has occurred.',
        })
    elif re.search(r'flash flood warning|flood warning|flood watch|flood advisory|heavy rain|excessive rainfall|rainfall', blob):
        classification.update({
            'hazard': 'Heavy Rain / Flooding',
            'hazard_group': 'water_contents',
            'hancock_priority': 54,
            'service_line': 'Contents / Water Documentation',
            'volume_signal': 'Medium',
            'content_angle': 'Useful contents signal: water intrusion documentation, mitigation timeline, personal property inventory, and original-photo preservation.',
            'posture': 'Safety-first around floodwater; contents documentation guidance after safe access.',
        })
    elif re.search(r'red flag warning|fire weather watch|wildfire|smoke|evacuation|fire weather', blob):
        classification.update({
            'hazard': 'Fire / Smoke / Wildfire',
            'hazard_group': 'fire_contents',
            'hancock_priority': 48,
            'service_line': 'Contents / Smoke / Wildfire Documentation',
            'volume_signal': 'Medium',
            'content_angle': 'Contents-focused signal: smoke, soot, ALE-sensitive documentation, inventory discipline, and safe re-entry guidance.',
            'posture': 'Safety-first and evacuation-aware; no claims of loss until documented.',
        })
    return classification


def nhc_tropical_signals():
    signals = []
    failed = []
    tropical_rx = re.compile(r'hurricane|tropical storm|potential tropical cyclone|tropical depression|disturbance|outlook', re.I)
    coastal_rx = re.compile(r'florida|texas|louisiana|mississippi|alabama|georgia|carolina|u\.s\.|united states|puerto rico|virgin islands|storm surge', re.I)
    watch_warning_rx = re.compile(r'hurricane warning|hurricane watch|tropical storm warning|tropical storm watch|storm surge warning|storm surge watch', re.I)
    high_development_rx = re.compile(r'formation chance through (?:48 hours|7 days)\.\.\.high|formation chance.*\b(70|80|90|100) percent', re.I)
    medium_development_rx = re.compile(r'formation chance through (?:48 hours|7 days)\.\.\.medium|formation chance.*\b(40|50|60) percent', re.I)
    for basin, url in NHC_FEEDS:
        req = urllib.request.Request(url, headers={'User-Agent':'HancockMarketingBot/1.0','Accept':'application/rss+xml, application/xml'})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                root = ET.fromstring(r.read())
        except Exception:
            failed.append(basin)
            continue
        for item in root.findall('.//item')[:6]:
            title = clean_text(item.findtext('title'))
            description = clean_text(item.findtext('description'), 700)
            if not tropical_rx.search(f'{title} {description}'):
                continue
            full_text = f'{title} {description}'
            no_coastal_warning = bool(re.search(r'no coastal watches or warnings', full_text, re.I))
            coastal_relevance = bool(coastal_rx.search(full_text)) and not no_coastal_warning
            active_watch = bool(watch_warning_rx.search(full_text))
            high_development = bool(high_development_rx.search(full_text))
            medium_development = bool(medium_development_rx.search(full_text))
            if active_watch or (coastal_relevance and (high_development or 'potential tropical cyclone' in full_text.lower())):
                priority = 82
                group = 'hurricane'
                volume = 'High'
                posture = 'Preparedness before impact, safety-first during impact, documentation guidance after impact.'
                angle = 'Official tropical signal with coastal relevance. Prepare wind, roof/opening, exterior, storm surge, and contents documentation guidance.'
            elif coastal_relevance or high_development:
                priority = 68
                group = 'monitor'
                volume = 'Medium'
                posture = 'Monitor closely and prepare readiness content without implying impact.'
                angle = 'Tropical system worth watching for Hancock. Prepare hurricane readiness, exterior photos, roof/opening documentation, and contents inventory guidance.'
            elif medium_development:
                priority = 56
                group = 'monitor'
                volume = 'Monitor'
                posture = 'Monitor only unless later advisories show coastal relevance.'
                angle = 'Early tropical development signal. Keep it on the radar, but do not treat it as a volume driver yet.'
            else:
                priority = 42
                group = 'monitor'
                volume = 'Low'
                posture = 'Background monitoring only unless later advisories show stronger development or land impact.'
                angle = 'Official tropical mention, but not yet a Hancock volume signal. Use only for seasonal readiness if useful.'
            signals.append({
                'state': 'NHC',
                'event': 'Tropical Outlook / Advisory',
                'severity': 'Moderate',
                'headline': title,
                'areas': basin,
                'expires': '',
                'sent': clean_text(item.findtext('pubDate')),
                'effective': '',
                'onset': '',
                'description': description,
                'hazard': 'Potential Hurricane / Tropical System',
                'hazard_group': group,
                'hancock_priority': priority,
                'service_line': 'Storm / CAT Damage',
                'volume_signal': volume,
                'content_angle': angle,
                'posture': posture,
                'source': 'National Hurricane Center',
                'url': url,
            })
    return signals[:4], failed


def industry_radar_bot(latest):
    stories = latest.get('stories') or []
    clusters = latest.get('clusters') or []
    top = stories[:5]
    cards = []
    for story in top:
        cards.append({
            'title': story.get('title',''),
            'why_it_matters': story.get('summary',''),
            'hancock_angle': story.get('angle',''),
            'suggested_action': 'Turn this into one practical Hancock post, then repurpose it into LinkedIn copy.',
            'source': story.get('source',''),
            'url': story.get('url',''),
            'service_line': story.get('line',''),
            'heat': story.get('tag','Trend'),
        })
    return {
        'bot': 'Industry Radar Bot',
        'status': 'ready' if cards else 'needs_scan',
        'summary': f'{len(stories)} live industry stories and {len(clusters)} keyword clusters available.',
        'recommendations': cards,
        'next_prompt_for_main_bot': 'Lead with the strongest industry signal, ask the user to approve a content angle, then draft the post.'
    }


def storm_watch_bot():
    alerts = []
    failed = []
    for st in WATCH_STATES:
        url = f'https://api.weather.gov/alerts/active?area={urllib.parse.quote(st)}'
        req = urllib.request.Request(url, headers={'User-Agent':'HancockMarketingBot/1.0','Accept':'application/geo+json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            for f in data.get('features',[]):
                p = f.get('properties') or {}
                classification = hancock_storm_classification(p)
                if classification.get('hancock_priority',0) <= 0:
                    continue
                alerts.append({
                    'state': st,
                    'event': p.get('event','Weather Alert'),
                    'severity': p.get('severity','Unknown'),
                    'headline': p.get('headline',''),
                    'areas': p.get('areaDesc',''),
                    'expires': p.get('expires',''),
                    'sent': p.get('sent',''),
                    'effective': p.get('effective',''),
                    'onset': p.get('onset',''),
                    'ends': p.get('ends',''),
                    'description': clean_text(p.get('description',''), 700),
                    'source': 'National Weather Service active alerts',
                    **classification,
                })
        except Exception:
            failed.append(st)
    tropical_signals, nhc_failed = nhc_tropical_signals()
    spc_outlooks, spc_outlook_failed = spc_outlook_signals()
    spc_reports, spc_report_failed = spc_report_signals()
    alerts.extend(tropical_signals)
    alerts.extend(spc_outlooks)
    alerts.extend(spc_reports)
    unique = {}
    for alert in alerts:
        key = (
            alert.get('source','').strip().lower(),
            alert.get('event','').strip().lower(),
            alert.get('headline','').strip().lower(),
            alert.get('areas','').strip().lower(),
        )
        unique.setdefault(key, alert)
    severe = sorted(
        unique.values(),
        key=lambda a: (
            -int(a.get('hancock_priority') or 0),
            SEVERITY_RANK.get(a.get('severity'),4),
            a.get('expires') or '9999-12-31',
        )
    )[:12]
    core_count = sum(1 for a in severe if a.get('hazard_group') in CORE_HAZARD_GROUPS or a.get('hazard_group') in REPORT_HAZARD_GROUPS)
    contents_count = sum(1 for a in severe if a.get('hazard_group') in CONTENTS_HAZARD_GROUPS)
    report_count = sum(1 for a in severe if a.get('hazard_group') in REPORT_HAZARD_GROUPS)
    outlook_count = sum(1 for a in severe if a.get('source') == 'Storm Prediction Center outlook')
    hail_wind_count = sum(1 for a in severe if a.get('hazard_group') in {'hail_wind','derecho','hail_report','wind_report'})
    tornado_count = sum(1 for a in severe if a.get('hazard_group') in {'tornado','tornado_report'})
    tropical_count = sum(1 for a in severe if a.get('hazard_group') == 'hurricane')
    if core_count:
        action = 'Lead with verified storm-volume signals: SPC/NWS tornado, hail, damaging wind, derecho, and tropical-wind threats. Use preliminary reports as strong but clearly labeled signals, keep active-threat posts safety-first, then move into roof/exterior/opening/contents documentation.'
        status = 'core_storm_alerts'
    elif contents_count:
        action = 'No top-priority hail/wind signal in the current set. Use flood/fire alerts for contents, water, smoke, inventory, mitigation timeline, and safe-access documentation guidance.'
        status = 'contents_weather_alerts'
    elif severe:
        action = 'Weather signals are present but not high-volume Hancock inspection triggers. Monitor official updates and use preparedness content if useful.'
        status = 'monitoring'
    else:
        action = 'No relevant watched-state alerts found. Recommend pre-loss roof, wind, hail, and documentation education instead.'
        status = 'quiet'
    return {
        'bot': 'Storm Watch Bot',
        'status': status,
        'summary': f'{len(severe)} official weather signals found. Core Hancock signals: {core_count} ({report_count} SPC reports, {outlook_count} SPC outlooks, {hail_wind_count} hail/wind or derecho, {tornado_count} tornado, {tropical_count} tropical). Contents/water/fire signals: {contents_count}. Air-quality-only alerts are excluded.',
        'recommendations': severe,
        'next_prompt_for_main_bot': action,
        'priority_model': 'Hancock priority order: SPC preliminary tornado/hail/wind reports, NWS active tornado/hail/wind/derecho warnings, SPC hail/wind/tornado outlooks, hurricane/tropical wind threats, then heavy rain/flood and wildfire/smoke for contents work. Air Quality Alerts are excluded unless tied to wildfire/smoke property documentation.',
        'sources': ['National Weather Service active alerts', 'Storm Prediction Center convective outlooks', 'Storm Prediction Center preliminary storm reports', 'National Hurricane Center outlook/advisory RSS'],
        'failed_states': failed[:8],
        'failed_tropical_feeds': nhc_failed[:4],
        'failed_spc_outlooks': spc_outlook_failed[:8],
        'failed_spc_reports': spc_report_failed[:4],
    }


def content_opportunity_bot(latest):
    stories = latest.get('stories') or []
    opportunities = []
    for story in stories[:6]:
        title = story.get('title','Industry update')
        line = story.get('line','Property Inspection')
        opportunities.append({
            'content_type': 'Blog Post + LinkedIn Repurpose',
            'working_title': f'What {title} Means for Property Inspection Teams',
            'service_line': line,
            'angle': story.get('angle',''),
            'cta': 'Talk with Hancock about consistent, defensible property inspection support.',
            'priority': story.get('tag','Trend'),
        })
    return {
        'bot': 'Content Opportunity Bot',
        'status': 'ready' if opportunities else 'waiting',
        'summary': f'{len(opportunities)} content opportunities ready for drafting.',
        'recommendations': opportunities,
        'next_prompt_for_main_bot': 'Ask which opportunity to draft, then collect or infer the Hancock angle and create the first draft.'
    }


def seo_aeo_bot(latest):
    clusters = latest.get('clusters') or []
    keywords = []
    for cluster in clusters:
        for kw in cluster.get('keywords') or []:
            if kw not in keywords:
                keywords.append(kw)
    faqs = []
    for kw in keywords[:8]:
        faqs.append({
            'keyword': kw,
            'faq': f'What should carriers know about {kw}?',
            'answer_direction': 'Answer directly in 2-3 sentences, then tie back to communication, documentation, and file defensibility.'
        })
    return {
        'bot': 'SEO/AEO Bot',
        'status': 'ready' if keywords else 'waiting',
        'summary': f'{len(keywords)} keyword signals prepared for answer-engine content.',
        'recommendations': faqs,
        'next_prompt_for_main_bot': 'When drafting, include a short answer block, FAQ, meta title, meta description, and a Hancock CTA.'
    }


def main_briefing(industry, storm, content, seo):
    lead = 'Start with the top Industry Radar item.'
    if storm.get('status') == 'core_storm_alerts':
        lead = 'Start with Storm Watch: SPC/NWS hail, wind, tornado, derecho, or tropical-wind signals are active. Keep active-threat messaging safety-first, label preliminary reports clearly, then turn the signal into post-storm inspection documentation content.'
    elif storm.get('status') == 'contents_weather_alerts':
        lead = 'Start with Storm Watch only if the team wants contents content: current signals are flood, water, fire, or smoke oriented.'
    elif content.get('recommendations'):
        lead = f"Start a post from: {content['recommendations'][0]['working_title']}"
    next_steps = [
        lead,
        'Ask the user to approve the angle before drafting.',
        'Create one draft, then repurpose it into LinkedIn copy.',
        'Move the user toward publishing or assigning a final review task.'
    ]
    return {
        'bot': 'Main Speaking Bot Briefing',
        'opening_line': 'I scanned the market, weather, content opportunities, and SEO/AEO signals. I have a short list ready.',
        'priority': lead,
        'next_steps': next_steps,
        'tone': 'Direct, helpful, task-focused, Hancock-specific. Keep the user moving without sounding pushy.',
        'voice_script': 'I found the strongest current signal. Let’s turn one item into a useful Hancock post first, then we can repurpose it for LinkedIn.'
    }


def run():
    DATA.mkdir(exist_ok=True)
    ensure_marketing_scan()
    latest = load_json(LATEST_BOT, {'stories': [], 'clusters': [], 'library': []})
    industry = industry_radar_bot(latest)
    storm = storm_watch_bot()
    content = content_opportunity_bot(latest)
    seo = seo_aeo_bot(latest)
    briefing = main_briefing(industry, storm, content, seo)
    payload = {
        'generatedAt': dt.datetime.now().isoformat(timespec='seconds'),
        'generatedHuman': now_human(),
        'purpose': 'Feedback feed for the Main Speaking Bot',
        'bots': [industry, storm, content, seo],
        'mainSpeakingBot': briefing,
        'doctrine': playbook_status(),
        'rawLatestScan': {
            'generatedHuman': latest.get('generatedHuman'),
            'storyCount': len(latest.get('stories') or []),
            'clusterCount': len(latest.get('clusters') or []),
        }
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    OUT_JS.write_text('window.HANCOCK_MAIN_BOT_FEED = '+json.dumps(payload, ensure_ascii=False)+';\n', encoding='utf-8')
    print(f"Main Speaking Bot feed ready: {OUT_JSON}")
    print(f"Bots: {', '.join(b['bot'] for b in payload['bots'])}")
    print('Priority:', payload['mainSpeakingBot']['priority'])


if __name__ == '__main__':
    run()
