import re
import urllib.parse

def parse_vless(link):
    try:
        # پاک کردن کاراکترهای اضافی احتمالی در انتهای لینک
        link = link.strip().split()[0]
        if not link.startswith("vless://"):
            return None
            
        rest = link.replace("vless://", "")
        name = ""
        if '#' in rest:
            rest, name = rest.split('#', 1)
            name = urllib.parse.unquote(name.strip())
        
        if '@' in rest:
            creds, host_part = rest.split('@', 1)
        else:
            host_part = rest
            
        if ':' in host_part:
            host, port_part = host_part.split(':', 1)
            port = int(port_part.split('?')[0].split('/')[0])
        else:
            return None
            
        return {
            'protocol': 'vless',
            'host': host,
            'port': port,
            'name': name,
            'raw': link
        }
    except:
        return None

def parse_all(raw_results):
    print("Parsing all Vless configs using pattern matching...")
    
    if isinstance(raw_results, dict):
        raw_text = raw_results.get("raw", "")
    else:
        raw_text = str(raw_results)
    
    # استفاده از Regular Expression برای پیدا کردن تمام الگوهای vless:// در هر کجای متن
    # این روش حتی اگر لینک‌ها به هم چسبیده یا در متن ریخته شده باشند را پیدا می‌کند
    vless_links = re.findall(r'vless://[^\s<>"\'%]+', raw_text)
    
    parsed = []
    for link in vless_links:
        info = parse_vless(link)
        if info and info.get('host') and info.get('port'):
            parsed.append(info)
            
    print(f"Valid Vless configs found: {len(parsed)}")
    
    seen = set()
    unique = []
    for info in parsed:
        key = f"{info['protocol']}://{info['host']}:{info['port']}"
        if key not in seen:
            seen.add(key)
            unique.append(info)
    
    print(f"Unique Vless configs: {len(unique)}")
    return unique
