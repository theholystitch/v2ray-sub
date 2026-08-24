import urllib.parse

def parse_vless(link):
    try:
        rest = link.replace("vless://", "")
        name = ""
        if '#' in rest:
            rest, name = rest.split('#', 1)
            name = urllib.parse.unquote(name)
        creds, host_part = rest.split('@', 1)
        host, port = host_part.split(':', 1)
        port = int(port.split('?')[0])
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
    print("Parsing Vless configs from raw text...")
    
    if isinstance(raw_results, dict):
        raw_text = raw_results.get("raw", "")
    else:
        raw_text = str(raw_results)
    
    lines = raw_text.splitlines()
    
    parsed = []
    for line in lines:
        line = line.strip()
        # فقط لینک‌های vless را قبول کن
        if not line or not line.startswith("vless://"):
            continue
        
        info = parse_vless(line)
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
