import base64
import json
import urllib.parse

BRAND = "Stitch"

def make_name(flag, index):
    return f"{BRAND} #{index:03d} {flag}"

def rename(info, flag, index):
    new_name = make_name(flag, index)
    raw = info['raw']
    
    if info['protocol'] == 'vmess':
        b64 = raw.replace("vmess://", "")
        decoded = base64.b64decode(b64 + "=" * (-len(b64) % 4)).decode('utf-8', errors='ignore')
        data = json.loads(decoded)
        data['ps'] = new_name
        encoded = base64.b64encode(json.dumps(data).encode()).decode()
        return f"vmess://{encoded}"
    
    link = raw
    if '#' in link:
        link = link.split('#')[0]
    return f"{link}#{urllib.parse.quote(new_name)}"
