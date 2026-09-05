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
    
    combined = "\n".join(all_texts)
    for proto in ['vless', 'vmess', 'trojan', 'ss://', 'hysteria2', 'hy2://', 'tuic', 'reality']:
        cnt = combined.lower().count(proto.lower())
        if cnt:
            print(f"  {proto}: {cnt} occurrences in raw")
    
    return {"raw": combined}
