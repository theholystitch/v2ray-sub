import httpx
import asyncio

# Cache to avoid duplicate lookups + respect ip-api rate limit (45/min)
_country_cache = {}
_geo_cache = {}

# For GPT/Gemini: countries where OpenAI & Google Gemini are officially available
# Based on 2025-2026 allow lists: blocked = IR, RU, CN, BY, KP, SY, CU, VE, SD, IQ
GPT_GEMINI_ALLOWED = {
    "US","CA","GB","DE","FR","NL","IT","ES","PT","IE","CH","AT","BE",
    "PL","SE","NO","DK","FI","AU","JP","KR","SG","NZ","TR","AE","IL",
    "CZ","HU","RO","GR","BR","MX","AR","CL","CO","PE","ZA","TH","MY",
    "PH","VN","ID","UA","KZ","SA","QA","KW","BH","OM","JO","LB","CY"
}
BLOCKED_FOR_AI = {"IR","RU","CN","BY","KP","SY","CU","VE","IQ","SD","BY","AF","MM"}

def is_gpt_gemini_compatible(country):
    """Check if country IP is likely to work for ChatGPT/Gemini - like yebekhe's clean IP logic"""
    if not country or country == "UN" or country in BLOCKED_FOR_AI:
        return False
    # If in allowed list or any non-blocked foreign, consider compatible
    # But strictly: must be in allowed for best guarantee
    return country in GPT_GEMINI_ALLOWED

async def get_geo_info(host):
    """Extended geo: returns dict with country, hosting, proxy for AI compatibility check - like yebekhe cf-clean-ip logic"""
    clean_host = host.split(':')[0].split('/')[0].strip().lower()
    if not clean_host or clean_host in ('127.0.0.1', 'localhost'):
        return {"country": "UN", "hosting": False, "proxy": False, "org": ""}
    
    if clean_host in _geo_cache:
        return _geo_cache[clean_host]
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # hosting/proxy helps detect datacenter VPN IPs that Gemini blocks
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
                else:
                    info = {"country": "UN", "hosting": False, "proxy": False, "org": ""}
                    _geo_cache[clean_host] = info
                    return info
            elif res.status_code == 429:
                await asyncio.sleep(1.5)
                info = {"country": "UN", "hosting": False, "proxy": False, "org": ""}
                _geo_cache[clean_host] = info
                return info
    except:
        pass
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
