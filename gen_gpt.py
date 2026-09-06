import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from scraper import scrape_all
from parser import parse_all
from checker import check_all
from rename import rename
from geo import get_flag, is_gpt_gemini_compatible
import base64, os, re
from datetime import datetime
import asyncio

async def gen():
    r=scrape_all()
    u=parse_all(r)
    print(f'Unique {len(u)}')
    top=u[:400]
    working=await check_all(top, max_check=300, timeout=3.0)
    print(f'Working usual {len(working)}')
    final=[]
    for w in working:
        host=w['host']
        raw=w['raw'].lower()
        if 'fastly' in raw or host.startswith('151.101.') or host.startswith('199.232.'):
            country='US'
        else:
            country='US' if 'us.' in host else 'DE' if 'de.' in host else 'US'
        w['_is_gpt']= is_gpt_gemini_compatible(country)
        final.append((w,country))
    # GPT strict: Use REAL geo (ipapi.co) to find US/CA VLESS Reality - fixes HU->US wrong flag
    from geo import get_geo_batch
    vless_reality_all = [x for x in u if x['protocol']=='vless' and 'security=reality' in x['raw'].lower() and 'pbk=' in x['raw'].lower() and x['port']==443 and 'xtls-rprx-vision' in x['raw'].lower()]
    print(f'VLESS Reality total {len(vless_reality_all)}, checking geo for top 150...', flush=True)
    vless_top = vless_reality_all[:150]
    geo_hosts = [x['host'] for x in vless_top]
    geo_infos = await get_geo_batch(geo_hosts, concurrency=10)
    gpt_candidates=[]
    for info, geo in zip(vless_top, geo_infos):
        if isinstance(geo, Exception):
            continue
        country = geo.get('country','UN') if isinstance(geo, dict) else 'UN'
        if country in ('US','CA'):
            # Validate correct flag - only US/CA via real geo, not heuristic
            info['_is_gpt']=True
            info['_gpt_country']=country
            gpt_candidates.append((info,country))
    print(f'GPT candidates found {len(gpt_candidates)} (VLESS Reality US/CA via real geo ipapi.co)')
    # Ensure seed US is included even if geo failed
    seed_hosts = ['us.pink-service.ru','ca.pink-service.ru']
    for info in u:
        if info['host'] in seed_hosts and info not in [x[0] for x in gpt_candidates]:
            c='US' if 'us.' in info['host'] else 'CA'
            gpt_candidates.append((info,c))
    print(f'GPT candidates after seed {len(gpt_candidates)}')
    gpt_infos=[x[0] for x in gpt_candidates[:150]]
    gpt_working=await check_all(gpt_infos, max_check=120, timeout=3.0)
    print(f'GPT working {len(gpt_working)}')
    gpt_final=[]
    for w in gpt_working:
        # Use real geo country for flag, not heuristic
        orig=[c for info,c in gpt_candidates if info['raw'].split('#')[0]==w['raw'].split('#')[0]]
        country=orig[0] if orig else 'US'
        w['_is_gpt']=True
        gpt_final.append((w,country))
    print(f'gpt_final {len(gpt_final)}')
    selected=final[:300]
    if len(selected)<300:
        extra=[x for x in u[300:600] if x not in [f[0] for f in final]]
        for info in extra[:300-len(selected)]:
            c='US'
            selected.append((info,c))
    gpt_selected=gpt_final[:100]
    print(f'Selected usual {len(selected)}, gpt {len(gpt_selected)}')
    for info,c in gpt_selected[:5]:
        print(f"GPT {c} {repr(get_flag(c))} {info['host']} {info['raw'][:80]}")
    renamed=[]
    for i,(info,c) in enumerate(selected,1):
        flag=get_flag(c)
        is_gpt= info.get('_is_gpt',False) and c in ('US','CA') and info['protocol']=='vless' and 'reality' in info['raw'].lower()
        renamed.append(rename(info, flag, i, is_gpt=is_gpt))
    renamed_gpt=[]
    for i,(info,c) in enumerate(gpt_selected,1):
        flag=get_flag(c)
        renamed_gpt.append(rename(info, flag, i, is_gpt=True))
    os.makedirs('output',exist_ok=True)
    with open('output/sub.txt','w',encoding='utf-8') as f:
        f.write('\n'.join(renamed))
    with open('output/sub.b64','w',encoding='utf-8') as f:
        f.write(base64.b64encode('\n'.join(renamed).encode()).decode())
    with open('output/sub_gpt.txt','w',encoding='utf-8') as f:
        f.write('\n'.join(renamed_gpt))
    with open('output/sub_gpt.b64','w',encoding='utf-8') as f:
        f.write(base64.b64encode('\n'.join(renamed_gpt).encode()).decode())
    print(f'Wrote sub.txt {len(renamed)}, sub_gpt.txt {len(renamed_gpt)}')
    print('Check HU in gpt?', any(c=='HU' for _,c in gpt_selected))
    print('Check US count', sum(1 for _,c in gpt_selected if c=='US'), 'CA', sum(1 for _,c in gpt_selected if c=='CA'))

asyncio.run(gen())
