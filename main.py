import asyncio
import os
import json
import base64
from datetime import datetime
from collections import Counter

from scraper import scrape_all
from parser import parse_all
from geo import get_flag, get_countries_batch
from checker import check_all
from rename import rename

OUTPUT_DIR = "output"
MAX_CONFIGS = 300  # Iran: more configs = more chance

# For Iran: prefer foreign servers, closest to Iran with good speed
# TR, DE, NL, FR, GB, US, AE, FI, SE are best for Iran latency
IRAN_GOOD_COUNTRIES = {"DE", "NL", "TR", "FR", "GB", "US", "FI", "SE", "PL", "AE", "CA", "SG", "AE"}

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 50)
    print("V2Ray Sub Bot - Iran Optimized 🇮🇷")
    print("=" * 50)
    
    raw_results = scrape_all()
    
    unique = parse_all(raw_results)
    
    if not unique:
        print("No configs found!")
        return
    
    # Iran: Filter out obviously bad hosts early
    filtered = []
    for info in unique:
        host = info['host'].lower()
        # skip private/local
        if host.startswith("10.") or host.startswith("192.168.") or host.startswith("172."):
            continue
        filtered.append(info)
    print(f"After Iran pre-filter: {len(filtered)} (from {len(unique)})")
    unique = filtered

    if not unique:
        print("No configs after filter!")
        return

    # For Iran we check TOP scored configs first (Reality/HY2 first)
    # So sort already done in parser, take top 800 for testing
    to_test = unique[:800]
    print(f"Testing top {len(to_test)} Iran-scored configs...")
    
    # Geo lookup with rate limiting (10 concurrency to avoid 429)
    print("Finding countries (rate-limited for ip-api.com)...")
    hosts = [info['host'] for info in to_test]
    countries = await get_countries_batch(hosts, concurrency=10)
    
    with_country = []
    for info, c in zip(to_test, countries):
        if isinstance(c, Exception):
            c = 'UN'
        if not c or c == "":
            c = 'UN'
        with_country.append((info, c))
    
    # Filter IR country - Iran servers are useless for Iranians to bypass filtering
    # Keep them but deprioritize heavily
    non_ir = [(info, c) for info, c in with_country if c != "IR"]
    ir_count = len(with_country) - len(non_ir)
    if ir_count:
        print(f"Filtered {ir_count} IR servers (useless for Iran bypass)")
    with_country = non_ir
    if not with_country:
        print("All servers were IR - nothing to offer!")
        return
    
    to_test_filtered = [info for info, _ in with_country]
    
    # TCP check - strict
    working = await check_all(to_test_filtered, max_check=600, timeout=4)
    
    if not working:
        print("No working configs found!")
        return
    
    # Re-associate countries after check (checker sorts by latency)
    working_keys = set(f"{info['host']}:{info['port']}" for info in working)
    final_list = []
    for info, country in with_country:
        key = f"{info['host']}:{info['port']}"
        if key in working_keys:
            # find working info with latency
            w_info = next((w for w in working if f"{w['host']}:{w['port']}" == key), info)
            final_list.append((w_info, country))
    
    print(f"Working + geolocated: {len(final_list)}")
    
    # Iran-specific sorting:
    # 1. Iran score (Reality/HY2 highest)  2. Good countries for Iran  3. Latency already sorted by checker
    def iran_sort_key(item):
        info, country = item
        score = info.get('_iran_score', 0)
        # Bonus for countries with low latency to Iran
        country_bonus = 15 if country in IRAN_GOOD_COUNTRIES else 0
        # Reality configs already 120, so they stay top
        return score + country_bonus

    final_list.sort(key=iran_sort_key, reverse=True)
    
    # Country diversity for Iran: don't give 100x DE only, mix it
    # But keep Reality on top regardless
    reality_top = [x for x in final_list if x[0].get('_iran_score',0) >= 100][:80]
    rest = [x for x in final_list if x not in reality_top]
    # Sort rest by country frequency to ensure diversity
    cnt_rest = Counter(c for _, c in rest)
    rest.sort(key=lambda x: cnt_rest[x[1]])
    final_sorted = reality_top + rest
    selected = final_sorted[:MAX_CONFIGS]
    
    print(f"Selected {len(selected)} for Iran (Reality: {len([x for x in selected if x[0].get('_iran_score',0)>=100])}, HY2: {len([x for x in selected if 'hysteria' in x[0]['protocol']])})")
    
    print(f"Renaming {len(selected)} configs...")
    renamed = []
    for i, (info, country) in enumerate(selected, 1):
        flag = get_flag(country)
        renamed.append(rename(info, flag, i))
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    with open(f"{OUTPUT_DIR}/sub.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(renamed))
    
    b64_content = base64.b64encode("\n".join(renamed).encode()).decode()
    with open(f"{OUTPUT_DIR}/sub.b64", "w", encoding="utf-8") as f:
        f.write(b64_content)
    
    json_data = {
        "name": "Stitch Iran 🇮🇷",
        "updated": timestamp,
        "total": len(renamed),
        "optimized_for": "Iran",
        "countries": dict(Counter(c for _, c in selected).most_common(20)),
        "protocols": dict(Counter(info['protocol'] for info, _ in selected).most_common()),
        "reality_count": len([x for x in selected if x[0].get('_iran_score',0) >= 100]),
        "links": renamed
    }
    with open(f"{OUTPUT_DIR}/sub.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    proto_stats = Counter(info['protocol'] for info, _ in selected)
    country_stats = Counter(c for _, c in selected)
    md = f"""# V2Ray Sub - Stitch Iran 🇮🇷

**Updated:** {timestamp}
**Total configs:** {len(renamed)} (TCP-tested, Iran-optimized)
**Optimized for:** Iran Internet (Reality/HY2 prioritized, IR filtered)

## Subscription Links
- Text: `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.txt`
- Base64: `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.b64`
- JSON: `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.json`

## Why Iran Optimized?
- ✅ Reality (120pts) & Hysteria2 (90pts) on top - most effective vs Iran DPI
- ✅ Port 443/2053/2083 prioritized (hardest to block)
- ✅ Iran servers (IR) removed, foreign low-latency preferred (DE/NL/TR/US)
- ✅ TLS+443 bonus, plain configs penalized

## Protocols
"""
    for proto, count in proto_stats.most_common():
        md += f"- `{proto.upper()}`: {count}\n"
    
    md += "\n## Countries (closest to Iran first)\n"
    for country, count in country_stats.most_common(15):
        flag = get_flag(country)
        md += f"- {flag} `{country}`: {count}\n"
    
    md += "\n---\nAuto-updated every 6 hours via GitHub Actions. Optimized for Iran.\n"
    
    with open(f"{OUTPUT_DIR}/README.md", "w", encoding="utf-8") as f:
        f.write(md)
    
    print("=" * 50)
    print(f"Done! {len(renamed)} Iran-optimized configs saved.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
