import concurrent.futures
import datetime as dt
import json
import os
import re
import urllib.request
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANDS_DIR = os.path.join(ROOT, "src", "content", "brands")
DEALS_DIR = os.path.join(ROOT, "src", "content", "deals")
WATCHLIST_PATH = os.path.join(ROOT, "src", "data", "brandsWatchlist.json")

NOW = dt.datetime.now(dt.timezone.utc)
NOW_ISO = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")

AI_SIGNAL_RE = re.compile(
    r"(?:free\s+trial|free\s+plan|free\s+tier|free\s+credits|start\s+for\s+free|try\s+free|student\s+discount|\d{1,2}%\s*off|annual\s+discount|open\s+source|forever\s+free)",
    re.IGNORECASE,
)
PCT_RE = re.compile(r"(?:(?:save|up\s+to)\s+(\d{1,2})\s*%|\b(\d{1,2})\s*%\s*off)", re.IGNORECASE)

AI_GROUP_RULES = [
    (("video", "muse", "kling", "runway", "pika", "luma", "sora", "veo", "hailuo", "heygen", "synthesia"), ["video", "trial"]),
    (("image", "flux", "midjourney", "ideogram", "recraft", "krea", "leonardo", "freepik"), ["image", "free"]),
    (("voice", "audio", "suno", "udio", "elevenlabs", "murf"), ["voice", "trial"]),
    (("3d", "meshy", "tripo", "spline", "rodin"), ["3d", "trial"]),
    (("code", "cursor", "windsurf", "copilot", "devin", "replit", "v0", "bolt", "lovable"), ["coding", "trial"]),
    (("write", "jasper", "copy", "claude", "gemini", "chatgpt", "perplexity", "notion"), ["writing", "productivity", "trial"]),
]


def get_domain(url):
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else (host or "example.com")
    except Exception:
        return "example.com"


def infer_ai_tags(name, url):
    t = f"{name} {url}".lower()
    for kws, tags in AI_GROUP_RULES:
        if any(k in t for k in kws):
            return tags
    return ["productivity", "trial"]


def check_ai_url(item):
    url = item.get("url") or ""
    if not url.startswith("http"):
        return None
    for target in (url, url.rstrip("/") + "/pricing"):
        try:
            req = urllib.request.Request(
                target,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            with urllib.request.urlopen(req, timeout=7) as resp:
                if resp.status != 200:
                    continue
                html = resp.read(140_000).decode("utf-8", errors="ignore")
                html = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
                text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
                m = AI_SIGNAL_RE.findall(text)
                if not m:
                    continue
                pcts = [int(p or q) for p, q in PCT_RE.findall(text[:5000]) if 10 <= int(p or q) <= 80]
                return {
                    "item": item,
                    "signal": m[0].strip(),
                    "pct": max(pcts) if pcts else 0,
                    "is_free": bool(re.search(r"free\s+(?:plan|tier|forever)|start\s+for\s+free", text[:5000], re.I)),
                    "url": target,
                }
        except Exception:
            continue
    return None


def main():
    if not os.path.exists(WATCHLIST_PATH):
        return
    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        wl = json.load(f)

    existing_deals = {fn.replace("-live-offer.json", "").replace(".json", "") for fn in os.listdir(DEALS_DIR)}
    ai_candidates = [b for b in wl if b.get("category") == "ai-tools" and b["id"] not in existing_deals and f"{b['id']}-live-offer" not in existing_deals]

    print(f"[ai-bot] scanning {len(ai_candidates)} AI tools for free plans, trials, and discounts...")
    added = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        for res in pool.map(check_ai_url, ai_candidates):
            if not res:
                continue
            b = res["item"]
            bid = b["id"]
            dom = get_domain(res["url"])
            bpath = os.path.join(BRANDS_DIR, f"{bid}.json")
            if not os.path.exists(bpath):
                with open(bpath, "w", encoding="utf-8") as bf:
                    json.dump({
                        "id": bid,
                        "name": b["name"],
                        "slug": bid,
                        "logo_url": f"https://www.google.com/s2/favicons?domain={dom}&sz=128",
                        "website_url": b["url"],
                        "country": "GLOBAL",
                        "categories": ["ai-tools"],
                        "short_bio": f"{b['name']} is an AI platform offering {res['signal'].lower()} and creative/developer workflows worldwide.",
                        "known_for": ["AI software", "Free tier & trials", "Annual discounts"],
                    }, bf, indent=2)

            pct = res["pct"]
            kind = "free" if res["is_free"] and not pct else "trial"
            badge = f"Free + {pct}% Off Annual" if pct else ("Free Plan" if res["is_free"] else "Free Trial")
            disc_val = f"UP TO {pct}% OFF" if pct else ("FREE PLAN" if res["is_free"] else "FREE TRIAL")
            dpath = os.path.join(DEALS_DIR, f"{bid}-live-offer.json")
            with open(dpath, "w", encoding="utf-8") as df:
                json.dump({
                    "id": f"{bid}-live-offer",
                    "slug": f"{bid}-live-offer",
                    "title": f"{b['name']}: {badge} & Starter Credits",
                    "short_description": f"Verified active AI offer on {b['name']} ({res['signal']}). Confirm plan limits and billing terms on the official pricing page.",
                    "brand_id": bid,
                    "country": "GLOBAL",
                    "cities": [],
                    "areas": [],
                    "branch_info": [],
                    "category": "ai-tools",
                    "deal_type": "online",
                    "channels": ["online"],
                    "discount_type": "percentage" if pct else "freebie",
                    "discount_value": disc_val,
                    "badge_text": badge,
                    "numeric_discount_percent": pct,
                    "terms_and_conditions": [
                        f"Auto-verified from {b['name']} official pricing/home page.",
                        "Confirm current credit limits and renewal terms before upgrading."
                    ],
                    "start_date": NOW_ISO,
                    "end_date": (NOW + dt.timedelta(days=7)).strftime("%Y-%m-%dT23:59:00Z"),
                    "source_url": res["url"],
                    "affiliate_url": res["url"],
                    "last_verified_at": NOW_ISO,
                    "status": "active",
                    "is_trending": False,
                    "is_coming_soon": False,
                    "limited_time": True,
                    "offer_kind": kind,
                    "image": {"src": f"https://www.google.com/s2/favicons?domain={dom}&sz=128", "alt": b["name"]},
                    "tags": infer_ai_tags(b["name"], res["url"]),
                }, df, indent=2)
            added += 1

    print(f"[ai-bot] discovered {added} new AI tool offers.")


if __name__ == "__main__":
    main()
