import re
import json
import base64
import urllib.parse

# Ports that work best in Iran (TLS/CDN + Reality)
IRAN_FAV_PORTS = {443, 8443, 2053, 2083, 2087, 2096, 2086, 2095, 8080, 80}

def iran_score(info):
    """Score configs for Iran internet - yebekhe-style: Reality params validated"""
    raw = info['raw']
    raw_low = raw.lower()
    port = info.get('port', 0)
    score = 0

    # 1. REALITY - king in Iran 2024-2026 - validate params like yebekhe does
    # yebekhe Reality configs always have: security=reality, pbk= (44 chars), fp=, sni=
    has_reality = 'security=reality' in raw_low
    has_pbk = 'pbk=' in raw_low
    has_fp = 'fp=' in raw_low or 'fingerprint=' in raw_low
    has_sni = 'sni=' in raw_low or 'servername=' in raw_low
    
    if has_reality and has_pbk:
        score += 120
        # Validate pbk length (44 chars base64) - real reality has proper key
        m = re.search(r'pbk=([^&]+)', raw, re.IGNORECASE)
        if m and 40 <= len(m.group(1)) <= 50:
            score += 5
        # Flow xtls-rprx-vision is standard for reality
        if 'xtls-rprx-vision' in raw_low:
            score += 5
        # Good SNI (yebekhe uses google.com, yahoo, microsoft)
        if any(s in raw_low for s in ['google.com', 'microsoft.com', 'yahoo.com', 'apple.com', 'cloudflare.com']):
            score += 10
        # Fingerprint chrome = best for Iran
        if 'fp=chrome' in raw_low or 'fingerprint=chrome' in raw_low:
            score += 5
        # sni must be present for reality to work
        if has_sni:
            score += 5
        else:
            score -= 30  # reality without sni is broken
    elif has_reality and not has_pbk:
        # fake reality
        score -= 40

    # 2. Hysteria2 / TUIC - UDP based, very effective in Iran
    if info['protocol'] in ('hysteria2', 'hy2', 'tuic'):
        score += 90
        # hy2 with obfs is better
        if 'obfs=' in raw_low or 'salamander' in raw_low:
            score += 5

    # 3. Trojan + TLS on 443 - still works well in Iran
    if info['protocol'] == 'trojan':
        score += 55
        if port == 443:
            score += 15
        if 'tls' in raw_low:
            score += 10

    # 4. VLESS TLS is better than plain
    if 'tls' in raw_low or 'security=tls' in raw_low:
        score += 25
        if port == 443:
            score += 15
        # WS + TLS + CDN is common in yebekhe
        if 'ws' in raw_low and port in (443, 8443, 2053):
            score += 10

    # 5. Favored ports for Iran DPI bypass (like yebekhe & barry-far)
    if port in IRAN_FAV_PORTS:
        score += 18

    # 6. Penalize plain non-TLS on random ports (easily blocked by Iran GFW)
    if 'security=none' in raw_low and port not in IRAN_FAV_PORTS:
        score -= 20

    # 7. GRPC + Reality combo bonus
    if 'grpc' in raw_low and 'reality' in raw_low:
        score += 10

    # 8. Penalize configs with empty sni or bad dest for reality
    if has_reality and 'sni=' in raw_low:
        sni_m = re.search(r'sni=([^&]+)', raw, re.IGNORECASE)
        if sni_m and len(sni_m.group(1)) < 4:
            score -= 20

    return score

def parse_vless(link):
    try:
        link = link.strip().split()[0]
        if not link.startswith("vless://"):
            return None
        rest = link.replace("vless://", "")
        name = ""
        if '#' in rest:
            rest, name = rest.split('#', 1)
            name = urllib.parse.unquote(name.strip())
        if '@' not in rest:
            return None
        creds, host_part = rest.split('@', 1)
        if ':' not in host_part:
            return None
        host, port_part = host_part.split(':', 1)
        port = int(port_part.split('?')[0].split('/')[0].split('#')[0])
        host = host.strip().lower()
        if not host or host in ('127.0.0.1', 'localhost') or '..' in host:
            return None
        # Filter invalid vless like yebekhe does - must have host length
        if len(host) > 253:
            return None
        return {'protocol': 'vless', 'host': host, 'port': port, 'name': name, 'raw': link}
    except:
        return None

def parse_vmess(link):
    try:
        link = link.strip().split()[0]
        if not link.startswith("vmess://"):
            return None
        b64 = link.replace("vmess://", "").split('#')[0].split('?')[0].strip()
        padded = b64 + "=" * (-len(b64) % 4)
        decoded = base64.b64decode(padded).decode('utf-8', errors='ignore')
        data = json.loads(decoded)
        host = str(data.get('add', '')).strip().lower()
        port = int(str(data.get('port', 0)).split('?')[0])
        if not host or not port or host in ('127.0.0.1', 'localhost') or '..' in host:
            return None
        return {'protocol': 'vmess', 'host': host, 'port': port, 'name': data.get('ps',''), 'raw': link}
    except:
        return None

def parse_trojan(link):
    try:
        link = link.strip().split()[0]
        if not link.startswith("trojan://"):
            return None
        rest = link.replace("trojan://", "")
        if '#' in rest:
            rest = rest.split('#', 1)[0]
        if '@' not in rest:
            return None
        _, host_part = rest.split('@', 1)
        if ':' not in host_part:
            return None
        host, port_part = host_part.split(':', 1)
        port = int(port_part.split('?')[0].split('/')[0])
        host = host.strip().lower()
        if not host or host in ('127.0.0.1', 'localhost'):
            return None
        return {'protocol': 'trojan', 'host': host, 'port': port, 'name': '', 'raw': link}
    except:
        return None

def parse_ss(link):
    try:
        link = link.strip().split()[0]
        if not link.startswith("ss://"):
            return None
        raw = link.replace("ss://", "")
        if '#' in raw:
            raw = raw.split('#', 1)[0]
        try:
            if '@' not in raw:
                padded = raw + "=" * (-len(raw) % 4)
                decoded = base64.b64decode(padded).decode('utf-8', errors='ignore')
                if '@' in decoded and ':' in decoded:
                    _, host_part = decoded.rsplit('@', 1)
                    if ':' in host_part:
                        host, port_part = host_part.rsplit(':', 1)
                        port = int(port_part.split('?')[0])
                        host = host.strip().lower()
                        if host and host not in ('127.0.0.1', 'localhost'):
                            return {'protocol': 'ss', 'host': host, 'port': port, 'name': '', 'raw': link}
        except:
            pass
        if '@' in raw:
            _, host_part = raw.rsplit('@', 1)
            if ':' in host_part:
                host, port_part = host_part.rsplit(':', 1)
                port = int(port_part.split('?')[0].split('/')[0])
                host = host.strip().lower()
                if host and host not in ('127.0.0.1', 'localhost'):
                    return {'protocol': 'ss', 'host': host, 'port': port, 'name': '', 'raw': link}
        return None
    except:
        return None

def parse_hy2(link):
    try:
        link = link.strip().split()[0]
        if not (link.startswith("hysteria2://") or link.startswith("hy2://") or link.startswith("hysteria://")):
            return None
        for prefix in ("hysteria2://", "hy2://", "hysteria://"):
            if link.startswith(prefix):
                rest = link.replace(prefix, "")
                break
        if '#' in rest:
            rest = rest.split('#', 1)[0]
        if '@' not in rest:
            return None
        _, host_part = rest.split('@', 1)
        if ':' not in host_part:
            return None
        host, port_part = host_part.split(':', 1)
        port = int(port_part.split('?')[0].split('/')[0])
        host = host.strip().lower()
        if not host or host in ('127.0.0.1', 'localhost'):
            return None
        proto = 'hysteria2' if 'hysteria2' in link or 'hy2' in link else 'hysteria'
        return {'protocol': proto, 'host': host, 'port': port, 'name': '', 'raw': link}
    except:
        return None

def parse_tuic(link):
    try:
        link = link.strip().split()[0]
        if not link.startswith("tuic://"):
            return None
        rest = link.replace("tuic://", "")
        if '#' in rest:
            rest = rest.split('#', 1)[0]
        if '@' not in rest:
            return None
        _, host_part = rest.split('@', 1)
        if ':' not in host_part:
            return None
        host, port_part = host_part.split(':', 1)
        port = int(port_part.split('?')[0].split('/')[0])
        host = host.strip().lower()
        if not host or host in ('127.0.0.1', 'localhost'):
            return None
        return {'protocol': 'tuic', 'host': host, 'port': port, 'name': '', 'raw': link}
    except:
        return None

def parse_all(raw_results):
    print("Parsing configs for Iran (yebekhe-style: vless/vmess/trojan/ss/hy2/tuic)...")
    
    if isinstance(raw_results, dict):
        raw_text = raw_results.get("raw", "")
    else:
        raw_text = str(raw_results)
    
    patterns = {
        'vless': re.findall(r'vless://[^\s<>"\'`]+', raw_text, re.IGNORECASE),
        'vmess': re.findall(r'vmess://[^\s<>"\'`]+', raw_text, re.IGNORECASE),
        'trojan': re.findall(r'trojan://[^\s<>"\'`]+', raw_text, re.IGNORECASE),
        'ss': re.findall(r'ss://[^\s<>"\'`]+', raw_text, re.IGNORECASE),
        'hy2': re.findall(r'hysteria2://[^\s<>"\'`]+', raw_text, re.IGNORECASE) + re.findall(r'hy2://[^\s<>"\'`]+', raw_text, re.IGNORECASE) + re.findall(r'hysteria://[^\s<>"\'`]+', raw_text, re.IGNORECASE),
        'tuic': re.findall(r'tuic://[^\s<>"\'`]+', raw_text, re.IGNORECASE),
    }
    
    parsers = {
        'vless': parse_vless,
        'vmess': parse_vmess,
        'trojan': parse_trojan,
        'ss': parse_ss,
        'hy2': parse_hy2,
        'tuic': parse_tuic,
    }
    
    parsed = []
    for proto, links in patterns.items():
        parser_fn = parsers[proto]
        for link in links:
            info = parser_fn(link)
            if info and info.get('host') and info.get('port'):
                if len(info['host']) > 253 or '..' in info['host']:
                    continue
                info['_iran_score'] = iran_score(info)
                parsed.append(info)
    
    for proto, links in patterns.items():
        cnt = len([p for p in parsed if p['protocol']==proto or (proto=='hy2' and p['protocol'] in ('hysteria2','hysteria'))])
        print(f"  {proto}: {len(links)} raw -> {cnt} valid")
    print(f"Total valid configs found: {len(parsed)}")
    
    seen = set()
    unique = []
    for info in parsed:
        key = f"{info['host']}:{info['port']}"
        if key not in seen:
            seen.add(key)
            unique.append(info)
    
    unique.sort(key=lambda x: x.get('_iran_score', 0), reverse=True)
    
    print(f"Unique configs: {len(unique)} (sorted by Iran yebekhe suitability)")
    # Log reality stats like yebekhe
    reality_cnt = len([x for x in unique if 'security=reality' in x['raw'].lower() and 'pbk=' in x['raw'].lower()])
    hy2_cnt = len([x for x in unique if x['protocol'] in ('hysteria2','hysteria')])
    print(f"  Reality valid: {reality_cnt}, HY2: {hy2_cnt}")
    return unique
