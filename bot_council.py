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
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
LATEST_BOT = DATA / 'latest_bot.json'
OUT_JSON = DATA / 'main_speaking_bot_feed.json'
OUT_JS = DATA / 'main_speaking_bot_feed.js'
WATCH_STATES = ['KY','TN','IN','OH','MO','IL','TX','OK','KS','FL','LA','GA','AL','NC','SC','CO','NE','IA','AR','MS']
STORM_RX = re.compile(r'tornado|thunderstorm|hail|flood|hurricane|tropical|high wind|wind warning|storm', re.I)


def now_human():
    return dt.datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')


def load_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return fallback


def ensure_marketing_scan():
    if LATEST_BOT.exists():
        return
    subprocess.run(['python3', 'marketing_bot.py'], cwd=str(ROOT), timeout=90)


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
    for st in WATCH_STATES[:20]:
        url = f'https://api.weather.gov/alerts/active?area={urllib.parse.quote(st)}'
        req = urllib.request.Request(url, headers={'User-Agent':'HancockMarketingBot/1.0','Accept':'application/geo+json'})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            for f in data.get('features',[]):
                p = f.get('properties') or {}
                if STORM_RX.search(p.get('event','')):
                    alerts.append({
                        'state': st,
                        'event': p.get('event','Weather Alert'),
                        'severity': p.get('severity','Unknown'),
                        'headline': p.get('headline',''),
                        'areas': p.get('areaDesc',''),
                        'expires': p.get('expires',''),
                    })
        except Exception:
            failed.append(st)
    severe = sorted(alerts, key=lambda a: {'Extreme':0,'Severe':1,'Moderate':2,'Minor':3}.get(a.get('severity'),4))[:8]
    if severe:
        action = 'If threat is active, recommend safety-first messaging only. After expiration, suggest post-storm documentation guidance.'
    else:
        action = 'No severe watched-state alerts found. Recommend pre-loss and roof-condition education instead.'
    return {
        'bot': 'Storm Watch Bot',
        'status': 'active_alerts' if severe else 'quiet',
        'summary': f'{len(severe)} relevant active weather alerts found across watched states.',
        'recommendations': severe,
        'next_prompt_for_main_bot': action,
        'failed_states': failed[:8]
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
    if storm.get('status') == 'active_alerts':
        lead = 'Start with Storm Watch. If the threat is active, keep messaging safety-first and avoid selling.'
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
