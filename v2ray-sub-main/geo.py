import httpx
import asyncio

# Cache to avoid duplicate lookups + respect ip-api rate limit (45/min)
_country_cache = {}

async def get_country(host):
    clean_host = host.split(':')[0].split('/')[0].strip().lower()
    if not clean_host or clean_host in ('127.0.0.1', 'localhost'):
        return "UN"
    
    if clean_host in _country_cache:
        return _country_cache[clean_host]
    
    # ip-api free: 45 req/min, http only. We use longer timeout and retry
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"http://ip-api.com/json/{clean_host}?fields=status,countryCode,query")
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success":
                    cc = data.get("countryCode", "UN").upper()
                    # Filter Iran IPs - useless for Iran users (need foreign)
                    # Keep but mark as UN to deprioritize
                    if cc == "IR":
                        cc = "IR"  # keep but will be filtered in main.py
                    _country_cache[clean_host] = cc
                    return cc
                else:
                    _country_cache[clean_host] = "UN"
                    return "UN"
            elif res.status_code == 429:
                # Rate limited
                await asyncio.sleep(1.5)
                _country_cache[clean_host] = "UN"
                return "UN"
    except:
        pass
    _country_cache[clean_host] = "UN"
    return "UN"

def get_flag(country_code):
    if not country_code or country_code == "UN" or len(country_code) != 2:
        return "🌍"
    # Handle IR specially - show warning
    if country_code == "IR":
        return "🇮🇷"
    try:
        return chr(127397 + ord(country_code[0])) + chr(127397 + ord(country_code[1]))
    except:
        return "🌍"

# For batch lookup with semaphore to avoid rate limit
async def get_countries_batch(hosts, concurrency=10):
    """Batch lookup with rate limiting for Iran project (45/min -> ~0.7/sec, so concurrency 10 with delay is safe)"""
    semaphore = asyncio.Semaphore(concurrency)
    async def _get(h):
        async with semaphore:
            # small delay to respect rate limit
            await asyncio.sleep(0.15)
            return await get_country(h)
    tasks = [_get(h) for h in hosts]
    return await asyncio.gather(*tasks, return_exceptions=True)
