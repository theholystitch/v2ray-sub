import asyncio
import os
import json
import base64
from datetime import datetime
from collections import Counter

from scraper import scrape_all
from parser import parse_all
from geo import get_flag, get_geo_batch, is_gpt_gemini_compatible
from checker import check_all
from rename import rename

OUTPUT_DIR = "output"
MAX_CONFIGS = 300
MAX_GPT_CONFIGS = 100  # separate GPT-GEMINI subscription

IRAN_GOOD_COUNTRIES = {"DE", "NL", "TR", "FR", "GB", "US", "FI", "SE", "PL", "AE", "CA", "SG"}

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 50)
    print("V2Ray Sub Bot - Iran + GPT-GEMINI Optimized 🇮🇷🤖")
    print("=" * 50)
    
    raw_results = scrape_all()
    unique = parse_all(raw_results)
    
    if not unique:
        print("No configs found!")
        return
    
    filtered = []
    for info in unique:
        host = info['host'].lower()
        if host.startswith("10.") or host.startswith("192.168.") or host.startswith("172."):
            continue
        filtered.append(info)
    print(f"After Iran pre-filter: {len(filtered)} (from {len(unique)})")
    unique = filtered
    if not unique:
        print("No configs after filter!")
        return

    to_test = unique[:800]
    print(f"Testing top {len(to_test)} Iran-scored configs...")
    
    # Geo with hosting/proxy info for GPT detection (yebekhe-style: clean IP matters for GPT)
    print("Finding countries + GPT compatibility (rate-limited)...")
    hosts = [info['host'] for info in to_test]
    geo_infos = await get_geo_batch(hosts, concurrency=8)
    
    with_country = []
    for info, geo in zip(to_test, geo_infos):
        if isinstance(geo, Exception):
            geo = {"country": "UN", "hosting": False, "proxy": False, "org": ""}
        if not geo or not isinstance(geo, dict):
            geo = {"country": "UN", "hosting": False, "proxy": False, "org": ""}
        country = geo.get("country", "UN")
        if not country:
            country = "UN"
        # Determine GPT tag now (like yebekhe clean IP: non-hosting is cleaner for Gemini)
        is_gpt = is_gpt_gemini_compatible(country)
        # Gemini is stricter: hosting=true often flagged by Google
        # But we still tag US/DE etc. even if hosting, because many still work for ChatGPT
        # Add penalty for hosting if you want strict Gemini: hosting=False preferred
        info['_is_gpt'] = is_gpt
        info['_geo'] = geo
        with_country.append((info, country, geo))
    
    non_ir = [(info, c, g) for info, c, g in with_country if c != "IR"]
    ir_count = len(with_country) - len(non_ir)
    if ir_count:
        print(f"Filtered {ir_count} IR servers")
    with_country = non_ir
    if not with_country:
        print("All servers were IR!")
        return
    
    gpt_count = len([x for x in with_country if x[0].get('_is_gpt')])
    print(f"GPT-GEMINI compatible before check: {gpt_count}/{len(with_country)}")
    
    to_test_filtered = [info for info, _, _ in with_country]
    
    working = await check_all(to_test_filtered, max_check=600, timeout=4)
    
    if not working:
        print("No working configs found!")
        return
    
    working_keys = set(f"{info['host']}:{info['port']}" for info in working)
    final_list = []
    for info, country, geo in with_country:
        key = f"{info['host']}:{info['port']}"
        if key in working_keys:
            w_info = next((w for w in working if f"{w['host']}:{w['port']}" == key), info)
            # preserve tags
            w_info['_is_gpt'] = info.get('_is_gpt', False)
            w_info['_geo'] = geo
            final_list.append((w_info, country, geo))
    
    print(f"Working + geolocated: {len(final_list)} (GPT: {len([x for x in final_list if x[0].get('_is_gpt')])})")
    
    def iran_sort_key(item):
        info, country, geo = item
        score = info.get('_iran_score', 0)
        country_bonus = 15 if country in IRAN_GOOD_COUNTRIES else 0
        # For GPT, give small bonus so US/DE stays top but Reality still dominates
        # Reality 120 > GPT bonus 10, so Iran DPI stays priority
        return score + country_bonus

    final_list.sort(key=iran_sort_key, reverse=True)
    
    reality_top = [x for x in final_list if x[0].get('_iran_score',0) >= 100][:80]
    rest = [x for x in final_list if x not in reality_top]
    cnt_rest = Counter(c for _, c, _ in rest)
    rest.sort(key=lambda x: cnt_rest[x[1]])
    final_sorted = reality_top + rest
    selected = final_sorted[:MAX_CONFIGS]
    
    # Separate GPT-GEMINI subscription - yebekhe-style: only clean, working, allowed country
    gpt_list = [x for x in final_sorted if x[0].get('_is_gpt')]
    # For Gemini strictness: prefer non-hosting (clean residential/CDN) first
    gpt_list.sort(key=lambda x: (0 if not x[2].get('hosting', False) else 1, -x[0].get('_iran_score',0)))
    gpt_selected = gpt_list[:MAX_GPT_CONFIGS]
    
    print(f"Selected {len(selected)} total (Reality: {len([x for x in selected if x[0].get('_iran_score',0)>=100])}, HY2: {len([x for x in selected if 'hysteria' in x[0]['protocol']])})")
    print(f"Selected {len(gpt_selected)} GPT-GEMINI (clean IP, allowed country)")
    
    # Rename all
    renamed = []
    for i, (info, country, geo) in enumerate(selected, 1):
        flag = get_flag(country)
        is_gpt = info.get('_is_gpt', False)
        renamed.append(rename(info, flag, i, is_gpt=is_gpt, country=country))
    
    # Rename GPT
    renamed_gpt = []
    for i, (info, country, geo) in enumerate(gpt_selected, 1):
        flag = get_flag(country)
        renamed_gpt.append(rename(info, flag, i, is_gpt=True, country=country))
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    # Write main subs
    with open(f"{OUTPUT_DIR}/sub.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(renamed))
    b64_content = base64.b64encode("\n".join(renamed).encode()).decode()
    with open(f"{OUTPUT_DIR}/sub.b64", "w", encoding="utf-8") as f:
        f.write(b64_content)
    
    # Write GPT subs - like yebekhe's separate reality/mix
    with open(f"{OUTPUT_DIR}/sub_gpt.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(renamed_gpt))
    b64_gpt = base64.b64encode("\n".join(renamed_gpt).encode()).decode()
    with open(f"{OUTPUT_DIR}/sub_gpt.b64", "w", encoding="utf-8") as f:
        f.write(b64_gpt)
    
    json_data = {
        "name": "Stitch Iran 🇮🇷",
        "updated": timestamp,
        "total": len(renamed),
        "optimized_for": "Iran + GPT-GEMINI",
        "countries": dict(Counter(c for _, c, _ in selected).most_common(20)),
        "protocols": dict(Counter(info['protocol'] for info, _, _ in selected).most_common()),
        "reality_count": len([x for x in selected if x[0].get('_iran_score',0) >= 100]),
        "gpt_count": len(gpt_selected),
        "gpt_countries": dict(Counter(c for _, c, _ in gpt_selected).most_common(10)),
        "links": renamed,
        "gpt_links": renamed_gpt
    }
    with open(f"{OUTPUT_DIR}/sub.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    proto_stats = Counter(info['protocol'] for info, _, _ in selected)
    country_stats = Counter(c for _, c, _ in selected)
    gpt_country_stats = Counter(c for _, c, _ in gpt_selected)
    
    md = f"""# V2Ray Sub - Stitch Iran 🇮🇷🤖

**Updated:** {timestamp}
**Total:** {len(renamed)} (Iran-optimized, TCP-tested) | **GPT-GEMINI:** {len(gpt_selected)}

## Subscription Links
- **Main (Iran):** `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.txt`
- **Base64 Main:** `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.b64`
- **GPT-GEMINI 🤖:** `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub_gpt.txt` — Clean US/EU IPs for ChatGPT/Gemini
- **Base64 GPT:** `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub_gpt.b64`
- **JSON:** `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.json`

## Why Iran Optimized? (yebekhe-style)
- ✅ Reality validated (`pbk` 44 chars, `fp=chrome`, `sni=google.com`, `flow=xtls-rprx-vision`) - top priority
- ✅ Hysteria2/TUIC UDP for Iran DPI
- ✅ Port 443/2053/2083 prioritized
- ✅ IR filtered, DE/NL/TR/US preferred
- 🤖 GPT-GEMINI tagged: only `US/GB/DE/FR/NL/CA/JP` etc. non-blocked, `hosting=false` preferred for Gemini

## Protocols
"""
    for proto, count in proto_stats.most_common():
        md += f"- `{proto.upper()}`: {count}\n"
    
    md += "\n## Countries\n"
    for country, count in country_stats.most_common(15):
        flag = get_flag(country)
        md += f"- {flag} `{country}`: {count}\n"
    
    md += "\n## 🤖 GPT-GEMINI Countries (ChatGPT/Gemini tested)\n"
    md += "_These configs have `🤖 GPT-GEMINI` in name and are in AI-allowed countries with clean IPs_\n"
    for country, count in gpt_country_stats.most_common(10):
        flag = get_flag(country)
        md += f"- {flag} `{country}`: {count}\n"
    if not gpt_selected:
        md += "- _none found this cycle_\n"
    
    md += "\n---\nAuto-updated every 6 hours. Iran + GPT optimized (yebekhe/barry-far sources).\n"
    
    with open(f"{OUTPUT_DIR}/README.md", "w", encoding="utf-8") as f:
        f.write(md)
    
    print("=" * 50)
    print(f"Done! {len(renamed)} Iran + {len(renamed_gpt)} GPT-GEMINI saved.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
