import base64
import json
import urllib.parse

def parse_vmess(link):
    try:
        raw = link.replace("vmess://", "")
        decoded = base64.b64decode(raw + "=" * (-len(raw) % 4)).decode('utf-8', errors='ignore')
        data = json.loads(decoded)
        return {
            'protocol': 'vmess',
            'host': data.get('add', ''),
            'port': int(data.get('port', 0)),
            'name': data.get('ps', ''),
            'raw': link
        }
    except:
        return None

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

def parse_trojan(link):
    try:
        rest = link.replace("trojan://", "")
        name = ""
        if '#' in rest:
            rest, name = rest.split('#', 1)
            name = urllib.parse.unquote(name)
        creds, host_part = rest.split('@', 1)
        host, port = host_part.split(':', 1)
        port = int(port.split('?')[0])
        return {
            'protocol': 'trojan',
            'host': host,
            'port': port,
            'name': name,
            'raw': link
        }
    except:
        return None

def parse_ss(link):
    try:
        rest = link.replace("ss://", "")
        name = ""
        if '#' in rest:
            rest, name = rest.split('#', 1)
            name = urllib.parse.unquote(name)
        if '@' in rest:
            creds, host_part = rest.split('@', 1)
            host, port = host_part.split(':', 1)
            port = int(port.split('?')[0])
        else:
            decoded = base64.b64decode(rest + "=" * (-len(rest) % 4)).decode()
            method_pass, host_port = decoded.split('@', 1)
            host, port = host_port.split(':', 1)
            port = int(port)
        return {
            'protocol': 'ss',
            'host': host,
            'port': port,
            'name': name,
            'raw': link
        }
    except:
        return None

PARSERS = {
    'vmess': parse_vmess,
    'vless': parse_vless,
    'trojan': parse_trojan,
    'ss': parse_ss,
}

def parse_link(link):
    for proto, parser in PARSERS.items():
        if link.startswith(proto + '://'):
            return parser(link)
    return None

def parse_all(raw_results):
    print("Parsing configs...")
    all_links = []
    for proto, links in raw_results.items():
        all_links.extend([(proto, l) for l in links])
    
    parsed = []
    for proto, link in all_links:
        info = parse_link(link)
        if info and info.get('host') and info.get('port'):
            parsed.append(info)
    
    print(f"Valid configs: {len(parsed)}")
    
    seen = set()
    unique = []
    for info in parsed:
        key = f"{info['protocol']}://{info['host']}:{info['port']}"
        if key not in seen:
            seen.add(key)
            unique.append(info)
    
    print(f"Unique configs: {len(unique)}")
    return unique
