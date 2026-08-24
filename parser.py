import urllib.parse

def parse_vless(link):
    try:
        rest = link.replace("vless://", "")
        name = ""
        if '#' in rest:
            rest, name = rest.split('#', 1)
            name = urllib.parse.unquote(name)
        
        # جدا کردن مشخصات اتصال
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
    print("Parsing all Vless configs from source...")
    
    if isinstance(raw_results, dict):
        raw_text = raw_results.get("raw", "")
    else:
        raw_text = str(raw_results)
    
    lines = raw_text.splitlines()
    parsed = []
    
    for line in lines:
        line = line.strip()
        # بررسی خطوطی که با vless شروع می‌شوند
        if line.startswith("vless://"):
            info = parse_vless(line)
            if info and info.get('host') and info.get('port'):
                parsed.append(info)
            
    print(f"Valid Vless configs found: {len(parsed)}")
    
    # حذف موارد تکراری
    seen = set()
    unique = []
    for info in parsed:
        key = f"{info['protocol']}://{info['host']}:{info['port']}"
        if key not in seen:
            seen.add(key)
            unique.append(info)
    
    print(f"Unique Vless configs: {len(unique)}")
    return unique
