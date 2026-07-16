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
CORE_HAZARD_GROUPS = {'tornado','hail_wind','derecho','hurricane'}
CONTENTS_HAZARD_GROUPS = {'water_contents','fire_contents'}
SEVERITY_RANK = {'Extreme':0,'Severe':1,'Moderate':2,'Minor':3}
NHC_FEEDS = [
    ('Atlantic', 'https://www.nhc.noaa.gov/index-at.xml'),
    ('Eastern Pacific', 'https://www.nhc.noaa.gov/index-ep.xml'),
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


def alert_blob(properties):
    fields = (
        properties.get('event'),
        properties.get('headline'),
        properties.get('description'),
        properties.get('instruction'),
        properties.get('areaDesc'),
    )
    return ' '.join(str(part or '') for part in fields).lower()


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
    alerts.extend(tropical_signals)
    unique = {}
    for alert in alerts:
        key = (
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
    core_count = sum(1 for a in severe if a.get('hazard_group') in CORE_HAZARD_GROUPS)
    contents_count = sum(1 for a in severe if a.get('hazard_group') in CONTENTS_HAZARD_GROUPS)
    hail_wind_count = sum(1 for a in severe if a.get('hazard_group') in {'hail_wind','derecho'})
    tornado_count = sum(1 for a in severe if a.get('hazard_group') == 'tornado')
    tropical_count = sum(1 for a in severe if a.get('hazard_group') == 'hurricane')
    if core_count:
        action = 'Lead with hail, wind, tornado, derecho, and tropical-wind inspection signals. Keep active-threat posts safety-first, then move into roof/exterior/opening/contents documentation after the alert passes.'
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
        'summary': f'{len(severe)} official weather signals found. Core Hancock signals: {core_count} ({hail_wind_count} hail/wind or derecho, {tornado_count} tornado, {tropical_count} tropical). Contents/water/fire signals: {contents_count}.',
        'recommendations': severe,
        'next_prompt_for_main_bot': action,
        'priority_model': 'Hancock priority order: tornado, hail, damaging wind, straight-line wind, derecho, hurricane/tropical wind, then heavy rain/flood and fire/smoke for contents work.',
        'sources': ['National Weather Service active alerts', 'National Hurricane Center outlook/advisory RSS'],
        'failed_states': failed[:8],
        'failed_tropical_feeds': nhc_failed[:4],
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
        lead = 'Start with Storm Watch: hail, wind, tornado, derecho, or tropical-wind signals are active. Keep active-threat messaging safety-first, then turn the signal into post-storm inspection documentation content.'
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
