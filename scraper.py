import httpx
import re
from bs4 import BeautifulSoup

CHANNELS = [
    "ConfigsHUB",
    "ConfigsHUB2",
    "ConfigsHubPlus",
    "AR14N24B",
    "SOSkeyNET",
    "persianvpnhub",
    "filembad",
]

PATTERNS = {
    'vmess': re.compile(r'vmess://[A-Za-z0-9+/=]+'),
    'vless': re.compile(r'vless://[^\s<>"]+'),
    'trojan': re.compile(r'trojan://[^\s<>"]+'),
    'ss':    re.compile(r'ss://[^\s<>"]+'),
}

def scrape_channel(channel, limit=100):
    url = f"https://t.me/s/{channel}"
    found_links = {k: set() for k in PATTERNS}
    
    try:
        print(f"  Scraping {channel}...")
        r = httpx.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        if r.status_code != 200:
            print(f"    Failed: {r.status_code}")
            return found_links
        
        soup = BeautifulSoup(r.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message_text')
        
        for msg in messages[:limit]:
            text = msg.get_text()
            for proto, pattern in PATTERNS.items():
                found = pattern.findall(text)
                found_links[proto].update(found)
    
    except Exception as e:
        print(f"    Error: {e}")
    
    return found_links

def scrape_all():
    print("Scraping channels...")
    all_results = {k: set() for k in PATTERNS}
    
    for channel in CHANNELS:
        result = scrape_channel(channel)
        for proto, links in result.items():
            all_results[proto].update(links)
    
    total = sum(len(v) for v in all_results.values())
    print(f"Total found: {total}")
    for proto, links in all_results.items():
        print(f"  {proto}: {len(links)}")
    
    return all_results
