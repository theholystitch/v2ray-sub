import requests
import base64

# فقط منابع معتبر و قدرتمند گیت‌هاب
FILE_SOURCES = [
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no5.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no7.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_base64_Sub.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/V2RAY_RAW.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_pools"
]

def decode_if_base64(data):
    """اگر محتوا Base64 باشد، آن را دیکود می‌کند."""
    try:
        decoded = base64.b64decode(data.strip()).decode('utf-8')
        return decoded
    except:
        return data

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
            
    combined_text = "\n".join(all_content)
    return {"raw": combined_text}
