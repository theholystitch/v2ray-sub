import requests
import base64
import re

# Iran-optimized sources: mix of large aggregators + sources known to have Reality/HY2
# Tested for Iran users - includes Splitted-By-Protocol for better Reality coverage
FILE_SOURCES = [
    # Large aggregators (mixed)
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/Splitted-By-Protocol/vmess.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/Splitted-By-Protocol/trojan.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/Splitted-By-Protocol/shadowsocks.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/mixed",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/sub/mixed",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vless.txt",
    # Fallbacks that still work but smaller
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/v2ray-configs/main/sub/mixed",
]

def smart_decode(text):
    text = text.strip()
    if not text or len(text) < 10:
        return []
    results = [text]
    # Only try base64 if text looks like base64 (no :// and long)
    if "://" not in text[:200] and len(text) > 100:
        try:
            # quick base64 char check
            if re.match(r'^[A-Za-z0-9+/=\n\r\s]+$', text.strip()):
                padded = text.strip() + "=" * (-len(text.strip()) % 4)
                decoded = base64.b64decode(padded).decode('utf-8', errors='ignore')
                if "://" in decoded:
                    results.append(decoded)
        except:
            pass
    else:
        # also try whole text as base64 if it doesn't contain :// in first chunk but has it after decode
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
                # skip html error pages
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
    # Basic stats for Iran debugging
    for proto in ['vless', 'vmess', 'trojan', 'ss://', 'hysteria2', 'hy2://', 'tuic']:
        cnt = combined.lower().count(proto.lower())
        if cnt:
            print(f"  {proto}: {cnt} occurrences in raw")
    
    return {"raw": combined}
