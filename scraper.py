import requests
import base64
from bs4 import BeautifulSoup

# منابع فایل‌های خام گیت‌هاب
FILE_SOURCES = [
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no5.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no7.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_base64_Sub.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/V2RAY_RAW.txt"
]

# منابع کانال‌های تلگرامی (به صورت پیش‌نمایش وب t.me/s/)
TELEGRAM_SOURCES = [
    "https://t.me/s/ConfigsHUB",
    "https://t.me/s/ConfigsHUB2",
    "https://t.me/s/ConfigsHubPlus",
    "https://t.me/s/AR14N24B",
    "https://t.me/s/SOSkeyNET",
    "https://t.me/s/persianvpnhub",
    "https://t.me/s/filembad",
    "https://t.me/s/v2ray_configs_pools"
]

def decode_if_base64(data):
    """اگر محتوا Base64 باشد، آن را دیکود می‌کند."""
    try:
        decoded = base64.b64decode(data.strip()).decode('utf-8')
        return decoded
    except:
        return data

def scrape_telegram_channel(url):
    """استخراج متن کانفیگ‌ها از پیش‌نمایش وب کانال تلگرام"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            messages = soup.find_all('div', class_='tgme_widget_message_text')
            return "\n".join([msg.get_text(separator="\n") for msg in messages])
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return ""

def scrape_all():
    all_content = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # دریافت از فایل‌های گیت‌هاب
    for url in FILE_SOURCES:
        try:
            print(f"Fetching file from: {url.split('/')[-1]}")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                content = response.text
                all_content.append(decode_if_base64(content))
            else:
                print(f"Failed to fetch {url}: Status {response.status_code}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            
    # دریافت از کانال‌های تلگرام
    for url in TELEGRAM_SOURCES:
        print(f"Scraping Telegram: {url.split('/')[-1]}")
        tg_content = scrape_telegram_channel(url)
        if tg_content:
            all_content.append(tg_content)
            
    combined_text = "\n".join(all_content)
    return {"raw": combined_text}
