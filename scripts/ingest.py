#!/usr/bin/env python3
"""Fetch official PIB RSS records and write a normalized static JSON dataset."""
import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEEDS = [
    {
        "id": "reserve-bank-press-releases",
        "name": "Reserve Bank of India — Press Releases",
        "url": "https://rbi.org.in/pressreleases_rss.xml",
        "publisher": "Reserve Bank of India",
    },
    {
        "id": "sebi-regulatory-updates",
        "name": "SEBI — Press Releases, Circulars and Orders",
        "url": "https://www.sebi.gov.in/sebirss.xml",
        "publisher": "Securities and Exchange Board of India",
    },
]
USER_AGENT = "IndiaCivicPulse/1.0 (+https://github.com/Aaqibhafeezkhan/India-Civic-Pulse)"
CENTER = [22.9734, 78.6569]
CITIES = {
    "mumbai": ("Mumbai, Maharashtra", [19.076, 72.8777]),
    "new delhi": ("New Delhi, Delhi", [28.6139, 77.209]),
    "delhi": ("Delhi", [28.6139, 77.209]),
    "bengaluru": ("Bengaluru, Karnataka", [12.9716, 77.5946]),
    "bangalore": ("Bengaluru, Karnataka", [12.9716, 77.5946]),
    "chennai": ("Chennai, Tamil Nadu", [13.0827, 80.2707]),
    "kolkata": ("Kolkata, West Bengal", [22.5726, 88.3639]),
    "hyderabad": ("Hyderabad, Telangana", [17.385, 78.4867]),
    "pune": ("Pune, Maharashtra", [18.5204, 73.8567]),
    "jaipur": ("Jaipur, Rajasthan", [26.9124, 75.7873]),
    "lucknow": ("Lucknow, Uttar Pradesh", [26.8467, 80.9462]),
    "bhopal": ("Bhopal, Madhya Pradesh", [23.2599, 77.4126]),
    "patna": ("Patna, Bihar", [25.5941, 85.1376]),
}
STATES = {
    "maharashtra": ("Maharashtra", [19.7515, 75.7139]),
    "karnataka": ("Karnataka", [15.3173, 75.7139]),
    "tamil nadu": ("Tamil Nadu", [11.1271, 78.6569]),
    "uttar pradesh": ("Uttar Pradesh", [26.8467, 80.9462]),
    "rajasthan": ("Rajasthan", [27.0238, 74.2179]),
    "gujarat": ("Gujarat", [22.2587, 71.1924]),
    "kerala": ("Kerala", [10.8505, 76.2711]),
    "west bengal": ("West Bengal", [22.9868, 87.855]),
    "telangana": ("Telangana", [18.1124, 79.0193]),
    "bihar": ("Bihar", [25.0961, 85.3131]),
    "madhya pradesh": ("Madhya Pradesh", [22.9734, 78.6569]),
    "odisha": ("Odisha", [20.9517, 85.0985]),
    "assam": ("Assam", [26.2006, 92.9376]),
    "punjab": ("Punjab", [31.1471, 75.3412]),
    "haryana": ("Haryana", [29.0588, 76.0856]),
    "andhra pradesh": ("Andhra Pradesh", [15.9129, 79.74]),
    "jharkhand": ("Jharkhand", [23.6102, 85.2799]),
    "chhattisgarh": ("Chhattisgarh", [21.2787, 81.8661]),
    "himachal pradesh": ("Himachal Pradesh", [31.1048, 77.1734]),
    "uttarakhand": ("Uttarakhand", [30.0668, 79.0193]),
    "goa": ("Goa", [15.2993, 74.124]),
    "delhi": ("Delhi", [28.6139, 77.209]),
}

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def clean_text(value):
    value = value or ""
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def parse_date(value):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    except (TypeError, ValueError, OverflowError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        except (TypeError, ValueError, OverflowError):
            return None

def category_for(text):
    text = text.casefold()
    rules = [
        ("Environment", ("environment", "pollution", "climate", "forest", "wildlife", "air quality", "water quality", "renewable energy")),
        ("Parliament", ("parliament", "lok sabha", "rajya sabha", "question hour", "standing committee", "parliamentary")),
        ("Civic", ("municipal", "public grievance", "civic", "sanitation", "drinking water", "district administration")),
        ("Policy", ("policy", "scheme", "notification", "guidelines", "rules", "cabinet", "budget", "ministry", "government launches", "government announces", "circular", "regulatory", "reserve bank", "securities and exchange", "monetary", "repo rate", "inflation", "banking regulation")),
    ]
    for category, words in rules:
        if any(word in text for word in words):
            return category
    return "Government"

def resolve_location(text):
    text = text.casefold()
    for key in sorted(CITIES, key=len, reverse=True):
        if re.search(r"(?<!\w)" + re.escape(key) + r"(?!\w)", text):
            name, coords = CITIES[key]
            return {"location": name, "coords": coords, "locationScope": "city",
                    "locationConfidence": "City name mentioned in source text; not independently verified as event location"}
    for key in sorted(STATES, key=len, reverse=True):
        if re.search(r"(?<!\w)" + re.escape(key) + r"(?!\w)", text):
            name, coords = STATES[key]
            return {"location": name, "coords": coords, "locationScope": "state",
                    "locationConfidence": "State mention detected; marker uses approximate state centroid"}
    return {"location": "India — national update", "coords": CENTER, "locationScope": "national",
            "locationConfidence": "National source; no event location inferred"}

def parse_feed(payload, source):
    root = ET.fromstring(payload)
    records = []
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    for item in items:
        def get(*names):
            for name in names:
                node = item.find(name)
                if node is not None and node.text:
                    return node.text.strip()
            return ""
        title = clean_text(get("title"))
        link = get("link")
        if not link and item.tag.endswith("entry"):
            node = item.find("{http://www.w3.org/2005/Atom}link")
            if node is not None:
                link = node.attrib.get("href", "")
        if not title or not link.startswith("https://"):
            continue
        summary = clean_text(get("description", "summary", "{http://www.w3.org/2005/Atom}summary"))
        published = parse_date(get("pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published"))
        if not published:
            continue
        content = title + " " + summary
        location = resolve_location(content)
        guid = get("guid", "id") or link
        identifier = re.sub(r"[^a-zA-Z0-9_-]+", "-", guid).strip("-")[-100:] or link
        category = category_for(content)
        records.append({
            "id": identifier, "category": category, "topic": category,
            "date": published, "publishedAt": published, "retrievedAt": utc_now(),
            "title": title, "summary": summary[:420] or "Open the original source for the full press release.",
            **location, "institution": source["publisher"], "publisher": source["publisher"],
            "source": link, "sourceLabel": source["name"], "sourceId": source["id"],
            "sourceType": "official-rss", "verification": "Publisher feed record; independently unverified",
        })
    return records

def fetch_feed(source):
    request = urllib.request.Request(source["url"], headers={
        "User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.5"
    })
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = response.read(5_000_000)
            if response.status != 200:
                raise RuntimeError("HTTP status " + str(response.status))
        records = parse_feed(payload, source)
        if not records:
            raise RuntimeError("Feed returned no parseable dated records")
        return records, {"id": source["id"], "name": source["name"], "url": source["url"],
                         "status": "ok", "items": len(records), "durationMs": round((time.monotonic()-started)*1000)}
    except (urllib.error.URLError, TimeoutError, ET.ParseError, RuntimeError, OSError, ValueError) as exc:
        return [], {"id": source["id"], "name": source["name"], "url": source["url"],
                    "status": "error", "items": 0, "error": str(exc)[:240],
                    "durationMs": round((time.monotonic()-started)*1000)}

def build_dataset():
    all_records, statuses = [], []
    for source in FEEDS:
        records, status = fetch_feed(source)
        all_records.extend(records)
        statuses.append(status)
    unique = {}
    for record in all_records:
        unique.setdefault(record["source"].split("#", 1)[0].rstrip("/"), record)
    stories = sorted(unique.values(), key=lambda item: item["publishedAt"], reverse=True)[:100]
    return {"schemaVersion": 1, "generatedAt": utc_now(), "storyCount": len(stories),
            "sources": statuses, "stories": stories,
            "notice": "Official publisher feed items are shown as published. Category and place labels are automated discovery aids, not independent verification."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/stories.json")
    args = parser.parse_args()
    dataset = build_dataset()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote {} stories to {}".format(dataset["storyCount"], output))
    for source in dataset["sources"]:
        print("{}: {} ({} items){}".format(source["name"], source["status"], source["items"], " — " + source["error"] if source.get("error") else ""))
    return 0 if any(source["status"] == "ok" for source in dataset["sources"]) else 1

if __name__ == "__main__":
    sys.exit(main())
