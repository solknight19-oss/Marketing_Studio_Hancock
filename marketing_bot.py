#!/usr/bin/env python3
"""
Hancock Marketing Bot
=====================
Runs the live scan layer for the approved Hancock Marketing Studio without
rewriting the Studio design.

Outputs:
  data/latest_bot.json  - readable archive
  data/latest_bot.js    - loaded by Hancock_Marketing_Studio.html
  data/bot_YYYY-MM-DD.json

Optional AI drafting:
  Set ANTHROPIC_API_KEY in the environment, or place it in anthropic_key.txt.
  The key is read locally and is never written to output files.
"""
import datetime as dt
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
LATEST_JSON = os.path.join(DATA_DIR, "latest_bot.json")
LATEST_JS = os.path.join(DATA_DIR, "latest_bot.js")
LOOKBACK_DAYS = 21
PER_QUERY = 6
MAX_STORIES = 18
MAX_LIBRARY = 4
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"

QUERIES = [
    "residential property insurance inspection",
    "commercial property insurance inspection",
    "roof damage insurance claim inspection",
    "property underwriting inspection carrier",
    "insurance catastrophe CAT claims response",
    "hail storm damage roof claims",
    "Xactimate Verisk property claims",
    "Hover EagleView roof measurement claims",
    "drone roof inspection insurance",
    "AI property claims adjusting",
    "property claims adjuster technology",
    "homeowners insurance roof inspection requirement",
    "4-point home inspection insurance",
    "loss control commercial property inspection",
    "ladder assist property inspection",
    "direct inspection property claims",
    "contents inventory insurance claim",
    "repairability roof shingles insurance",
]

STOP = set("""the a an and or of for to in on at by with from as is are be this that
it its their they we our you your has have will can not but if so than then now new
amid into over under out up down more most less least about after before during
inc llc says say said report reveals revealed top best how why what when who which
2025 2026 q1 q2 q3 q4 u.s us usa update guide released share shares insurance claim claims""".split())

SERVICE_RULES = {
    "Storm / CAT Damage": ["storm", "hail", "wind", "catastrophe", "tornado", "hurricane", "cat ", "severe weather"],
    "Underwriting Inspection": ["underwriting", "renewal", "risk", "nonrenew", "pre-loss", "roof age", "loss control"],
    "Roofing": ["roof", "shingle", "roofing", "slope", "hail damage"],
    "Technology & Imagery": ["ai", "drone", "xactimate", "verisk", "hover", "eagleview", "cotality", "satellite", "imagery"],
    "Commercial": ["commercial", "business property"],
    "Residential / 4-Point": ["residential", "homeowner", "4-point", "four point"],
    "Contents": ["contents", "inventory", "personal property"],
    "Carrier / Market": ["carrier", "premium", "rate", "policy", "coverage", "reinsurance"],
}

ANGLE_BY_LINE = {
    "Storm / CAT Damage": "Connect the trend to fast CAT response, clear communication, and documentation that holds up after the storm surge of files arrives.",
    "Underwriting Inspection": "Tie the signal to pre-loss risk identification. The cheapest claim is the one that never happens.",
    "Roofing": "Bring it back to full roof-system documentation, original photo files, and repairability that is tested rather than assumed.",
    "Technology & Imagery": "Technology should support field operations, not replace them. Hancock can pair better tools with trained inspection judgment.",
    "Commercial": "Frame this around lifecycle property intelligence for carrier and commercial risk teams.",
    "Residential / 4-Point": "Focus on clear documentation, communication with the insured, and consistent reporting for residential property decisions.",
    "Contents": "Position contents work as documentation, valuation support, and defensible reconstruction of personal property information.",
    "Carrier / Market": "Relate the market pressure to trust, consistency, defensibility, and reduced claim cycle time.",
}

DOCTRINE = """You write marketing intelligence and draft content for Hancock Claims Consultants using Ryan Knight's inspection industry philosophy. Core doctrine: trust, documentation, defensibility, communication, consistency, reduced cycle time, reduced indemnity leakage. The inspection is only part of the service; the real product is accurate documentation, defensible findings, clear communication, consistent reporting, and carrier-ready files. Use property lifecycle management: pre-loss underwriting/risk, during-loss damage inspection/scope/estimate, and post-loss verification/reinspection. Signature ideas: Nobody should ever wonder where our technician is. Documentation should answer questions before they are asked. The cheapest claim is the one that never happens. Repairability must be tested, not assumed. Price matters; trust matters more. Standards: front/right/rear/left elevations, full roof-system documentation, 10x10 test squares every slope, interior dimensions when reported, original uncompressed photos, captions and annotations, narrative flow Overview -> Exterior -> Roofing -> Damage -> Interior -> Evidence."""


def clean(value):
    return html.unescape(re.sub(r"<[^>]+>", "", value or "")).strip()


def parse_date(value):
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return dt.datetime.strptime(value, fmt).replace(tzinfo=None)
        except Exception:
            pass
    return None


def fetch_rss(query):
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=en-US&gl=US&ceid=US:en"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read()


def parse_items(xml_bytes):
    items = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items
    for node in root.iter("item"):
        title = clean(node.findtext("title"))
        link = (node.findtext("link") or "").strip()
        desc = clean(node.findtext("description"))
        pub = (node.findtext("pubDate") or "").strip()
        source_node = node.find("source")
        source = clean(source_node.text) if source_node is not None else "Google News"
        if " - " in title:
            head, tail = title.rsplit(" - ", 1)
            if tail.lower().strip() == source.lower().strip():
                title = head
        if title and link:
            items.append({"title": title, "url": link, "summary": desc or title, "source": source, "when": parse_date(pub)})
    return items


def term_hit(blob, term):
    term = term.strip().lower()
    if not term:
        return False
    if len(term) <= 3 or " " in term or "-" in term:
        return re.search(r"\b" + re.escape(term) + r"\b", blob) is not None
    return term in blob


def service_line(title, summary):
    blob = (" " + title + " " + summary + " ").lower()
    scores = []
    for line, words in SERVICE_RULES.items():
        score = sum(1 for word in words if term_hit(blob, word))
        if score:
            scores.append((score, line))
    # Preserve SERVICE_RULES order on ties instead of alphabetical accidents.
    if not scores:
        return "Carrier / Market"
    order = {line: i for i, line in enumerate(SERVICE_RULES)}
    return sorted(scores, key=lambda x: (-x[0], order[x[1]]))[0][1]


def heat(when):
    if not when:
        return "Trending"
    age = (dt.datetime.utcnow() - when).days
    if age <= 2:
        return "Hot"
    if age <= 7:
        return "Rising"
    return "Trending"


def tokenize(text):
    return [w for w in re.findall(r"[a-z][a-z\-]{2,}", text.lower()) if w not in STOP]


def extract_clusters(stories):
    clusters = []
    for line in sorted({s["line"] for s in stories}):
        counts = Counter()
        for story in stories:
            if story["line"] == line:
                counts.update(tokenize(story["title"] + " " + story["summary"]))
        terms = [word for word, _ in counts.most_common(10)][:6]
        if terms:
            clusters.append({"category": line, "keywords": terms})
    all_words = tokenize(" ".join(s["title"] + " " + s["summary"] for s in stories))
    bigrams = Counter(zip(all_words, all_words[1:]))
    hot_terms = [f"{a} {b}" for (a, b), n in bigrams.most_common(20) if n >= 2]
    if hot_terms:
        clusters.insert(0, {"category": "Trending Keywords", "keywords": hot_terms[:8]})
    return clusters[:6]


def api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    key_file = os.path.join(HERE, "anthropic_key.txt")
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def anthropic(system, prompt, key, max_tokens=900):
    body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read())
        return "".join(part.get("text", "") for part in data.get("content", [])).strip()
    except Exception as exc:
        print("  ! AI draft skipped:", exc)
        return ""


def build_stories():
    seen = set()
    raw = []
    print("Scanning industry sources through Google News RSS...")
    for query in QUERIES:
        try:
            found = parse_items(fetch_rss(query))[:PER_QUERY]
            print(f"  - {query[:48]:48s} {len(found)}")
        except Exception as exc:
            print(f"  ! {query[:48]:48s} skipped ({exc})")
            found = []
        for item in found:
            key = re.sub(r"[^a-z0-9]", "", item["title"].lower())[:70]
            if key in seen:
                continue
            seen.add(key)
            raw.append(item)
        time.sleep(0.25)
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=LOOKBACK_DAYS)
    raw = [item for item in raw if item["when"] is None or item["when"] >= cutoff]
    raw.sort(key=lambda item: item["when"] or dt.datetime.min, reverse=True)
    stories = []
    for item in raw[:MAX_STORIES]:
        summary = item["summary"]
        if len(summary) > 260:
            summary = summary[:257] + "..."
        line = service_line(item["title"], summary)
        stories.append({
            "title": item["title"],
            "tag": heat(item["when"]),
            "summary": summary,
            "angle": ANGLE_BY_LINE.get(line, ANGLE_BY_LINE["Carrier / Market"]),
            "keywords": tokenize(item["title"] + " " + summary)[:5],
            "source": item["source"],
            "url": item["url"],
            "date": item["when"].strftime("%b %d, %Y") if item["when"] else "",
            "line": line,
        })
    return stories


def build_library(stories, key):
    picks = stories[:MAX_LIBRARY]
    library = []
    for i, story in enumerate(picks):
        if key:
            prompt = f"Write a 250-350 word publish-ready blog post for Hancock Claims Consultants reacting to this industry signal. Title: {story['title']}. Source summary: {story['summary']}. Service line: {story['line']}. Hancock angle: {story['angle']}. Include SEO title, meta description, short intro, two sections, FAQ, and CTA. Return Markdown only."
            body = anthropic(DOCTRINE, prompt, key, 1000)
        else:
            body = ""
        if not body:
            body = f"# {story['title']}\n\n{story['summary']}\n\n## Hancock angle\n{story['angle']}\n\n## Draft direction\nBuild this into a useful carrier-facing post around communication, documentation, consistency, and file defensibility.\n\n*Bot stub. Add an Anthropic key for full auto-drafting.*"
        title_match = re.search(r"^#\s+(.+)", body, re.M)
        library.append({
            "title": title_match.group(1) if title_match else story["title"],
            "type": "Bot Draft" if key else "Bot Stub",
            "body": body,
            "date": dt.datetime.now().strftime("%b %d, %Y %I:%M %p"),
            "source": story["source"],
            "url": story["url"],
        })
    return library


def write_outputs(payload):
    os.makedirs(DATA_DIR, exist_ok=True)
    today = dt.datetime.now().strftime("%Y-%m-%d")
    with open(LATEST_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA_DIR, f"bot_{today}.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    js = "window.HANCOCK_BOT_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    with open(LATEST_JS, "w", encoding="utf-8") as f:
        f.write(js)


def main():
    stories = build_stories()
    clusters = extract_clusters(stories)
    key = api_key()
    if key:
        print("Anthropic key found - building AI drafts...")
    else:
        print("No Anthropic key found - writing draft stubs only.")
    library = build_library(stories, key) if stories else []
    now = dt.datetime.now()
    payload = {
        "generatedAt": now.isoformat(timespec="seconds"),
        "generatedHuman": now.strftime("%A, %B %d, %Y at %I:%M %p"),
        "source": "Google News RSS + Hancock Marketing Bot",
        "stories": stories,
        "clusters": clusters,
        "library": library,
    }
    write_outputs(payload)
    print(f"Done. {len(stories)} stories, {len(clusters)} clusters, {len(library)} drafts written to data/latest_bot.js")


if __name__ == "__main__":
    main()
