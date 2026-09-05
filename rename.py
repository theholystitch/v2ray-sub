import base64
import json
import urllib.parse

BRAND = "Stitch"

def make_name(flag, index, is_gpt=False, country=""):
    """
    Naming with Iran + GPT/Gemini tags
    - Normal: Stitch #001 🇩🇪
    - GPT:    Stitch #001 🇺🇸 🤖 GPT-GEMINI
    """
    base = f"{BRAND} #{index:03d} {flag}"
    if is_gpt:
        # Tag for ChatGPT/Gemini suitable configs - clean IP in allowed country
        base += " 🤖 GPT-GEMINI"
    return base

def rename(info, flag, index, is_gpt=False, country=""):
    new_name = make_name(flag, index, is_gpt=is_gpt, country=country)
    raw = info['raw']
    
    if info['protocol'] == 'vmess':
        try:
            b64 = raw.replace("vmess://", "").split('#')[0].strip()
            padded = b64 + "=" * (-len(b64) % 4)
            decoded = base64.b64decode(padded).decode('utf-8', errors='ignore')
            data = json.loads(decoded)
            data['ps'] = new_name
            encoded = base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode()
            return f"vmess://{encoded}"
        except:
            # fallback to plain
            pass
    
    link = raw
    if '#' in link:
        link = link.split('#')[0]
    return f"{link}#{urllib.parse.quote(new_name)}"
