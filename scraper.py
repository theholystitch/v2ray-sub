import requests
import base64
import re

# Iran-optimized sources: yebekhe-style - prioritize Reality/HY2 splitted + large aggregators
# yebekhe collects from 20+ Iranian Telegram channels (VlessConfig, FreeIranT, etc.) and splits by protocol
FILE_SOURCES = [
    # yebekhe - direct splitted (most Iran-tested, like original yebekhe)
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/reality",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/vless",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/vmess",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/trojan",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/hysteria2",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/tuic",
    # barry-far Splitted-By-Protocol (good for Iran)
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/Splitted-By-Protocol/reality.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/Splitted-By-Protocol/hysteria2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_Sub.txt",
    # Large aggregators
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/sub/mixed",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vless.txt",
    # Fallback
    "https://raw.githubusercontent.com/ALIILAPRO/v2ray-configs/main/sub/mixed",
]

def smart_decode(text):
    text = text.strip()
    if not text or len(text) < 10:
        return []
    results = [text]
    if "://" not in text[:200] and len(text) > 100:
        try:
            if re.match(r'^[A-Za-z0-9+/=\n\r\s]+$', text.strip()):
                padded = text.strip() + "=" * (-len(text.strip()) % 4)
                decoded = base64.b64decode(padded).decode('utf-8', errors='ignore')
                if "://" in decoded:
                    results.append(decoded)
        except:
            pass
    else:
        try:
            padded = text.strip() + "=" * (-len(text.strip()) % 4)
            decoded = base64.b64decode(padded).decode('utf-8', errors='ignore')
            if "://" in decoded and decoded != text:
                results.append(decoded)
        except:
            pass
    return results

def scrape_all():
    all_texts = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/plain,*/*"
    }
    
    success = 0
    for url in FILE_SOURCES:
        try:
            print(f"Fetching: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200 and response.text.strip():
                content = response.text
                if "<html" in content.lower()[:500] and "://" not in content:
                    print(f"  -> skipped (html)")
                    continue
                decoded_list = smart_decode(content)
                all_texts.extend(decoded_list)
                success += 1
                print(f"  -> {len(content)} chars, {len(decoded_list)} decoded")
            else:
                print(f"  -> failed {response.status_code}")
        except Exception as e:
            print(f"Error with {url}: {e}")
    
    print(f"Fetched {success}/{len(FILE_SOURCES)} sources successfully")
    
    # SEED: User's proven working configs - DO NOT CHANGE for usual configs scraper
    # Trojan Fastly for Iran general + VLESS Reality US for GPT/Gemini (user requires US/CA VLESS)
    SEED_CONFIGS = [
        "trojan://MiTiVPN@151.101.56.7:443?path=%40mehrosaboran&security=tls&alpn=http%2F1.1&insecure=0&host=mitivpn-mitivpn-mitivpn--mitivpn-mitivpn--mitivpn.global.ssl.fastly.net&fp=firefox&type=ws&allowInsecure=0&sni=ssl.fastly.com#%40prrofile_purple%20%7C%20FAST%20%F0%9F%92%9A",
        # US VLESS Reality proven for Gemini/GPT - like us.pink-service.ru
        "vless://ee965abe-a647-48b9-83ea-951306e70503@us.pink-service.ru:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=us.pink-service.ru&pbk=2fgsbEAn-ALVpjnE4ZTPrzaZY70vVplYwldCnslInE0&sid=86b80f1e713a33ad&packetEncoding=xudp#US-Gemini-GPT",
        # Additional US/CA Reality seeds to ensure GPT pool
        "vless://ee965abe-a647-48b9-83ea-951306e70503@ca.pink-service.ru:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=ca.pink-service.ru&pbk=2fgsbEAn-ALVpjnE4ZTPrzaZY70vVplYwldCnslInE0&sid=86b80f1e713a33ad#CA-Gemini-GPT",
    ]
    all_texts.extend(SEED_CONFIGS)
    print(f"Added {len(SEED_CONFIGS)} proven seed configs (Fastly Trojan + US/CA VLESS Reality for GPT)")
    
    combined = "\n".join(all_texts)
    for proto in ['vless', 'vmess', 'trojan', 'ss://', 'hysteria2', 'hy2://', 'tuic', 'reality', 'fastly']:
        cnt = combined.lower().count(proto.lower())
        if cnt:
            print(f"  {proto}: {cnt} occurrences in raw")
    
    return {"raw": combined}

# GPT-specific sources - DO NOT affect main Iran scraper (user request)
GPT_SOURCES = [
    "https://raw.githubusercontent.com/iampedii/whitedns-sub/refs/heads/main/base64.txt",
    # Fallback for GPT - also include main reality for US
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/Splitted-By-Protocol/vless.txt",
]

# Example proven GPT config (WhiteDNS style - DE with amp-api-edge.apps.apple.com, xudp, reality)
GPT_SEED = "vless://c9c64c4b-c12a-4673-be52-21c080ac07a1@brg.cloudmixsc.ir:15617?encryption=none&flow=xtls-rprx-vision&security=reality&sni=amp-api-edge.apps.apple.com&fp=chrome&pbk=zAjmD7mwpdYpvo5W5iZvSJAJ1xnuXnFNEZAQ-NoSXwg&sid=8cf95f839e46a5c3&packetEncoding=xudp&type=tcp#DE-GPT-FI"

def scrape_gpt():
    """Separate GPT pool - WhiteDNS + example config style (DE/US with apple.com SNI, xudp, reality)"""
    all_texts=[]
    headers={"User-Agent":"Mozilla/5.0"}
    success=0
    for url in GPT_SOURCES:
        try:
            print(f"[GPT] Fetching: {url}")
            r=requests.get(url, headers=headers, timeout=15)
            if r.status_code==200 and r.text.strip():
                if "<html" in r.text.lower()[:500] and "://" not in r.text:
                    continue
                decoded=smart_decode(r.text)
                all_texts.extend(decoded)
                success+=1
                print(f"  [GPT] -> {len(r.text)} chars")
            else:
                print(f"  [GPT] failed {r.status_code}")
        except Exception as e:
            print(f"[GPT] Error {url}: {e}")
    # Add proven WhiteDNS example
    all_texts.append(GPT_SEED)
    print(f"[GPT] Fetched {success}/{len(GPT_SOURCES)} + 1 seed (WhiteDNS DE example)")
    combined="\n".join(all_texts)
    for proto in ['vless','reality','whitedns','gpt']:
        cnt=combined.lower().count(proto)
        if cnt:
            print(f"  [GPT] {proto}: {cnt}")
    return {"raw": combined}
