import asyncio
import os
import json
import base64
from datetime import datetime
from collections import Counter

from scraper import scrape_all
from parser import parse_all
from geo import get_country, get_flag
from checker import check_all
from rename import rename

OUTPUT_DIR = "output"
MAX_CONFIGS = 200

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 50)
    print("V2Ray Sub Bot - Starting")
    print("=" * 50)
    
    raw_results = scrape_all()
    
    unique = parse_all(raw_results)
    
    if not unique:
        print("No configs found!")
        return
    
    print("Finding countries...")
    tasks = [get_country(info['host']) for info in unique[:500]]
    countries = await asyncio.gather(*tasks, return_exceptions=True)
    
    with_country = []
    for info, c in zip(unique[:500], countries):
        if isinstance(c, Exception):
            c = 'UN'
        with_country.append((info, c))
    
    to_test = [info for info, _ in with_country]
    working = await check_all(to_test, max_check=500, timeout=4)
    
    if not working:
        print("No working configs found!")
        return
    
    working_keys = set(f"{info['protocol']}://{info['host']}:{info['port']}" for info in working)
    final_list = []
    for info, country in with_country:
        key = f"{info['protocol']}://{info['host']}:{info['port']}"
        if key in working_keys:
            final_list.append((info, country))
    
    print(f"Working + geolocated: {len(final_list)}")
    
    cnt = Counter(c for _, c in final_list)
    final_list.sort(key=lambda x: 100 - cnt[x[1]], reverse=True)
    selected = final_list[:MAX_CONFIGS]
    
    print(f"Renaming {len(selected)} configs...")
    renamed = []
    for i, (info, country) in enumerate(selected, 1):
        flag = get_flag(country)
        renamed.append(rename(info, flag, i))
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    with open(f"{OUTPUT_DIR}/sub.txt", "w") as f:
        f.write("\n".join(renamed))
    
    b64_content = base64.b64encode("\n".join(renamed).encode()).decode()
    with open(f"{OUTPUT_DIR}/sub.b64", "w") as f:
        f.write(b64_content)
    
    json_data = {
        "name": "Stitch",
        "updated": timestamp,
        "total": len(renamed),
        "countries": dict(Counter(c for _, c in selected).most_common(20)),
        "links": renamed
    }
    with open(f"{OUTPUT_DIR}/sub.json", "w") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    proto_stats = Counter(info['protocol'] for info, _ in selected)
    country_stats = Counter(c for _, c in selected)
    md = f"""# V2Ray Sub - Stitch

**Updated:** {timestamp}
**Total configs:** {len(renamed)} (all tested)

## Subscription Links
- Text: `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.txt`
- Base64: `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.b64`
- JSON: `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.json`

## Protocols
"""
    for proto, count in proto_stats.most_common():
        md += f"- `{proto.upper()}`: {count}\n"
    
    md += "\n## Countries\n"
    for country, count in country_stats.most_common(15):
        flag = get_flag(country)
        md += f"- {flag} `{country}`: {count}\n"
    
    md += "\n---\nAuto-updated every 2 hours via GitHub Actions.\n"
    
    with open(f"{OUTPUT_DIR}/README.md", "w") as f:
        f.write(md)
    
    print("=" * 50)
    print(f"Done! {len(renamed)} configs saved.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
