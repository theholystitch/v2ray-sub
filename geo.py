import httpx
import asyncio

# Cache to avoid duplicate lookups + respect ip-api rate limit (45/min)
_country_cache = {}
_geo_cache = {}

# For GPT/Gemini: ONLY US/CA work reliably for Gemini+GPT per user (Trojan Fastly fails for Gemini)
# User proven: vless://...@us.pink-service.ru:443?security=reality&sni=us.pink-service.ru (US) works for Gemini
GPT_GEMINI_ALLOWED = {"US", "CA"}
BLOCKED_FOR_AI = {"IR","RU","CN","BY","KP","SY","CU","VE","IQ","SD","BY","AF","MM"}

def is_gpt_gemini_compatible(country):
    """Strict US/CA only for Gemini/GPT - user requires US/CA VLESS Reality (Trojan fails)"""
    if not country or country == "UN" or country in BLOCKED_FOR_AI:
        return False
    return country in GPT_GEMINI_ALLOWED

async def get_geo_info(host):
    """Extended geo: returns dict with country, hosting, proxy - uses ipapi.co fallback (ip-api.com blocked in Iran)"""
    clean_host = host.split(':')[0].split('/')[0].strip().lower()
    if not clean_host or clean_host in ('127.0.0.1', 'localhost'):
        return {"country": "UN", "hosting": False, "proxy": False, "org": ""}
    
    if clean_host in _geo_cache:
        return _geo_cache[clean_host]
    
    # Try ipapi.co first (works in Iran, 1000/day free)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"https://ipapi.co/{clean_host}/json/")
            if res.status_code == 200:
                data = res.json()
                cc = data.get("country_code", data.get("country", "")).upper() if isinstance(data, dict) else ""
                if cc and len(cc)==2 and cc not in ("UN",):
                    # ipapi.co doesn't give hosting, infer via org
                    org = data.get("org", data.get("asn",""))
                    hosting = any(x in org.lower() for x in ["hosting","datacenter","vps","server","cloud","digitalocean","ovh","hetzner"]) if org else False
                    info = {"country": cc, "hosting": hosting, "proxy": False, "org": org}
                    _geo_cache[clean_host] = info
                    _country_cache[clean_host] = cc
                    return info
    except:
        pass
    # Fallback to ipwho.is
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"https://ipwho.is/{clean_host}")
            if res.status_code == 200:
                data = res.json()
                if data.get("success"):
                    cc = data.get("country_code", "UN").upper()
                    org = data.get("connection", {}).get("org", "") if isinstance(data.get("connection"), dict) else data.get("org","")
                    hosting = data.get("connection", {}).get("hosting", False) if isinstance(data.get("connection"), dict) else False
                    info = {"country": cc, "hosting": hosting, "proxy": False, "org": org}
                    _geo_cache[clean_host] = info
                    _country_cache[clean_host] = cc
                    return info
    except:
        pass
    # Fallback ip-api.com (may be blocked)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"http://ip-api.com/json/{clean_host}?fields=status,countryCode,hosting,proxy,org,query")
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success":
                    cc = data.get("countryCode", "UN").upper()
                    hosting = data.get("hosting", False)
                    proxy = data.get("proxy", False)
                    org = data.get("org", "")
                    info = {"country": cc, "hosting": hosting, "proxy": proxy, "org": org}
                    _geo_cache[clean_host] = info
                    _country_cache[clean_host] = cc
                    return info
    except:
        pass
    # Final heuristic for known CDN
    if any(x in clean_host for x in ["fastly"]) or clean_host.startswith("151.101.") or clean_host.startswith("199.232.") or clean_host.startswith("140.248."):
        info = {"country": "US", "hosting": False, "proxy": False, "org": "Fastly"}
        _geo_cache[clean_host] = info
        return info
    # Heuristic for pink-service US/CA
    if "us.pink" in clean_host or clean_host=="us.pink-service.ru":
        info = {"country": "US", "hosting": False, "proxy": False, "org": "pink-service US"}
        _geo_cache[clean_host] = info
        return info
    if "ca.pink" in clean_host:
        info = {"country": "CA", "hosting": False, "proxy": False, "org": "pink-service CA"}
        _geo_cache[clean_host] = info
        return info
    info = {"country": "UN", "hosting": False, "proxy": False, "org": ""}
    _geo_cache[clean_host] = info
    return info

async def get_country(host):
    info = await get_geo_info(host)
    return info["country"]

def get_flag(country_code):
    if not country_code or country_code == "UN" or len(country_code) != 2:
        return "🌍"
    if country_code == "IR":
        return "🇮🇷"
    try:
        return chr(127397 + ord(country_code[0])) + chr(127397 + ord(country_code[1]))
    except:
        return "🌍"

async def get_countries_batch(hosts, concurrency=10):
    """Batch lookup with rate limiting"""
    semaphore = asyncio.Semaphore(concurrency)
    async def _get(h):
        async with semaphore:
            await asyncio.sleep(0.15)
            return await get_country(h)
    tasks = [_get(h) for h in hosts]
    return await asyncio.gather(*tasks, return_exceptions=True)

async def get_geo_batch(hosts, concurrency=8):
    """Batch geo with hosting/proxy info for GPT detection - slower to respect limit"""
    semaphore = asyncio.Semaphore(concurrency)
    async def _get(h):
        async with semaphore:
            await asyncio.sleep(0.20)
            return await get_geo_info(h)
    tasks = [_get(h) for h in hosts]
    return await asyncio.gather(*tasks, return_exceptions=True)
