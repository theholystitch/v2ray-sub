import requests
import base64

SOURCES = [
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no5.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no7.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_base64_Sub.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/V2RAY_RAW.txt"
]

def decode_if_base64(data):
    """اگر محتوا Base64 باشد، آن را دیکود می‌کند."""
    try:
        # حذف کاراکترهای اضافه و دیکود کردن
        decoded = base64.b64decode(data.strip()).decode('utf-8')
        return decoded
    except:
        return data

def scrape_all():
    all_content = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for url in SOURCES:
        try:
            print(f"Fetching from: {url.split('/')[-1]}")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                content = response.text
                # بررسی اینکه آیا محتوا Base64 است یا متن عادی
                processed_content = decode_if_base64(content)
                all_content.append(processed_content)
            else:
                print(f"Failed to fetch {url}: Status {response.status_code}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            
    return "\n".join(all_content)
