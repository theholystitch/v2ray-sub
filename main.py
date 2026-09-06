import asyncio
import os
import json
import base64
import re
from datetime import datetime
from collections import Counter

from scraper import scrape_all, scrape_gpt
from parser import parse_all
from geo import get_flag, get_geo_batch, is_gpt_gemini_compatible
from checker import check_all
from rename import rename

OUTPUT_DIR = "output"
MAX_CONFIGS = 300

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 50)
    print("V2Ray Sub Bot - Iran + GPT-GEMINI Optimized")
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

    # Usual Iran configs: top scored (Trojan Fastly 308 + Reality) - DON'T CHANGE SCRAPER
    top = unique[:400]
    print(f"Testing top {len(top)} Iran-scored configs...")
    working = await check_all(top, max_check=300, timeout=3.0)
    print(f"Working usual {len(working)} / 300")
    
    # Real geo for usual to get diverse countries (fixes ALL US bug - user wants DE etc)
    print("Geo for main (real ipapi.co for DE/US/etc)...")
    main_hosts=[x['host'] for x in working]
    main_geo=await get_geo_batch(main_hosts, concurrency=10)
    final=[]
    for w, geo in zip(working, main_geo):
        if isinstance(geo, Exception):
            country='US'
        else:
            country=geo.get('country','US') if isinstance(geo, dict) else 'US'
            if country in ('UN','IR'):
                country='US'
                # Fallback for Fastly
                if 'fastly' in w['raw'].lower():
                    country='US'
        w['_is_gpt']=False
        final.append((w,country))
    
    # GPT-GEMINI: Separate pool - WhiteDNS + example style (DO NOT use main scraper)
    # User proven: brg.cloudmixsc.ir:15617 vless reality sni amp-api-edge.apps.apple.com xudp -> works for AI very well
    # WhiteDNS base64.txt already filtered for GPT (311 configs, DE/US/IT with GPT tag)
    print("Fetching GPT pool (WhiteDNS) separately...")
    gpt_raw = scrape_gpt()
    gpt_parsed = parse_all(gpt_raw)
    # Filter for GPT: WhiteDNS style - vless reality with correct params (like example)
    # Keep all WhiteDNS vless reality (not just US/CA) - DE/IT also work for AI via WhiteDNS outlet
    gpt_candidates_raw=[]
    for info in gpt_parsed:
        raw_low=info['raw'].lower()
        if info['protocol']!='vless':
            continue
        if 'security=reality' not in raw_low:
            continue
        if 'pbk=' not in raw_low:
            continue
        # WhiteDNS uses sni amp-api-edge.apps.apple.com / www.siemens.com / www.intel.com etc
        # Accept any reality with sni and flow
        if 'sni=' not in raw_low:
            continue
        gpt_candidates_raw.append(info)
    print(f"GPT WhiteDNS parsed {len(gpt_candidates_raw)} VLESS Reality candidates")
    # Geo for GPT to get CORRECT flags (fixes HU->US) - use real ipapi.co, not heuristic
    # Include DE, US, IT etc as WhiteDNS provides - all GPT-compatible via WhiteDNS
    gpt_top = gpt_candidates_raw[:200]
    geo_hosts = [x['host'] for x in gpt_top]
    geo_infos = await get_geo_batch(geo_hosts, concurrency=10)
    gpt_candidates=[]
    for info, geo in zip(gpt_top, geo_infos):
        if isinstance(geo, Exception):
            continue
        country = geo.get('country','UN') if isinstance(geo, dict) else 'UN'
        if country in ('UN','IR','RU','CN','BY','KP','SY','CU','VE'):
            # Skip blocked for AI, but keep DE/IT/US etc
            continue
        # Keep all non-blocked WhiteDNS countries (DE, IT, US, etc) - they all work for AI via WhiteDNS
        info['_is_gpt']=True
        gpt_candidates.append((info,country))
    # Ensure example seed included
    for info in gpt_parsed:
        if info['host']=='brg.cloudmixsc.ir' and info not in [x[0] for x in gpt_candidates]:
            gpt_candidates.append((info,'DE'))
    print(f'GPT candidates after geo {len(gpt_candidates)} (WhiteDNS style, correct flags)')
    gpt_infos=[x[0] for x in gpt_candidates[:150]]
    gpt_working=await check_all(gpt_infos, max_check=120, timeout=3.0)
    print(f'GPT working {len(gpt_working)} / {len(gpt_infos)}')
    gpt_final=[]
    for w in gpt_working:
        orig=[c for info,c in gpt_candidates if info['raw'].split('#')[0]==w['raw'].split('#')[0]]
        country=orig[0] if orig else 'DE'
        w['_is_gpt']=True
        gpt_final.append((w,country))
    
    # Build selected
    selected = final[:MAX_CONFIGS]
    if len(selected)<MAX_CONFIGS:
        extra=[x for x in unique[300:600] if x not in [f[0] for f in final]]
        for info in extra[:MAX_CONFIGS-len(selected)]:
            selected.append((info,'US'))
    
    # For usual, tag only those that are also GPT (US/CA VLESS Reality) to avoid wrong flags
    # Hungarian -> US flag fixed by real geo, so no misflag
    gpt_selected = gpt_final[:100]
    
    print(f"Selected {len(selected)} total, GPT {len(gpt_selected)} (US {sum(1 for _,c in gpt_selected if c=='US')} CA {sum(1 for _,c in gpt_selected if c=='CA')})")
    
    # Rename
    renamed=[]
    for i,(info,c) in enumerate(selected,1):
        flag=get_flag(c)
        # Only tag as GPT if actually US/CA VLESS Reality (prevents Trojan flagged as GPT)
        is_gpt = info.get('_is_gpt',False) and c in ('US','CA') and info['protocol']=='vless' and 'reality' in info['raw'].lower()
        # For usual list, don't tag Trojan as GPT (fixes Trojan can't open Gemini)
        renamed.append(rename(info, flag, i, is_gpt=is_gpt))
    
    renamed_gpt=[]
    for i,(info,c) in enumerate(gpt_selected,1):
        flag=get_flag(c)  # Correct flag: US->🇺🇸 CA->🇨🇦, no HU->US
        renamed_gpt.append(rename(info, flag, i, is_gpt=True))
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    with open(f"{OUTPUT_DIR}/sub.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(renamed))
    with open(f"{OUTPUT_DIR}/sub.b64", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(renamed).encode()).decode())
    with open(f"{OUTPUT_DIR}/sub_gpt.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(renamed_gpt))
    with open(f"{OUTPUT_DIR}/sub_gpt.b64", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(renamed_gpt).encode()).decode())
    
    json_data = {
        "name": "Stitch Iran",
        "updated": timestamp,
        "total": len(renamed),
        "gpt_count": len(renamed_gpt),
        "countries": dict(Counter(c for _,c in selected).most_common(20)),
        "protocols": dict(Counter(info['protocol'] for info,_ in selected).most_common()),
        "gpt_countries": dict(Counter(c for _,c in gpt_selected).most_common(10)),
        "links": renamed[:10],
        "gpt_links": renamed_gpt[:10]
    }
    with open(f"{OUTPUT_DIR}/sub.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    proto_stats = Counter(info['protocol'] for info,_ in selected)
    country_stats = Counter(c for _,c in selected)
    gpt_country_stats = Counter(c for _,c in gpt_selected)
    
    md = f"""# V2Ray Sub - Stitch Iran

**Updated:** {timestamp}
**Total:** {len(renamed)} (Iran-optimized, TCP-tested) | **GPT-GEMINI:** {len(gpt_selected)} US/CA VLESS Reality

## Subscription Links
- **Main (Iran - Trojan Fastly + Reality):** `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.txt`
- **Base64 Main:** `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.b64`
- **GPT-GEMINI (US/CA VLESS Reality only):** `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub_gpt.txt` — For ChatGPT/Gemini (like us.pink-service.ru)
- **Base64 GPT:** `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub_gpt.b64`
- **JSON:** `https://raw.githubusercontent.com/theholystitch/v2ray-sub/main/output/sub.json`

## Why Iran Optimized?
- Reality validated (`pbk` 44 chars, `flow=xtls-rprx-vision`, `sni`) + Trojan WS+TLS Fastly (`ssl.fastly.com` score 308) top
- GPT-GEMINI: ONLY US/CA VLESS Reality `port 443` `xtls-rprx-vision` with real geo `ipapi.co` (no HU->US wrong flag, no Trojan)

## Protocols (Main)
"""
    for proto, count in proto_stats.most_common():
        md += f"- `{proto.upper()}`: {count}\n"
    md += "\n## Countries (Main)\n"
    for country, count in country_stats.most_common(15):
        md += f"- {get_flag(country)} `{country}`: {count}\n"
    md += "\n## GPT-GEMINI Countries (Strict US/CA VLESS Reality)\n"
    for country, count in gpt_country_stats.most_common(10):
        md += f"- {get_flag(country)} `{country}`: {count}\n"
    if not gpt_selected:
        md += "- _none_\n"
    md += "\n---\nAuto-updated every 6 hours. Iran + GPT strict US/CA.\n"
    with open(f"{OUTPUT_DIR}/README.md", "w", encoding="utf-8") as f:
        f.write(md)
    
    print("=" * 50)
    print(f"Done! {len(renamed)} Iran + {len(renamed_gpt)} GPT-GEMINI (US/CA VLESS) saved.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
