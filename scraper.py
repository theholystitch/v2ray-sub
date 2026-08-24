import requests
import base64
import re

FILE_SOURCES = [
    "https://raw.githubusercontent.com/patterniha/Free-Configs/main/configs.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_base64_Sub.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs_no5.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt"
]

def smart_decode(text):
    text = text.strip()
    # اگر متن خودش لینک ساب است یا بیس۶۴ است، تلاش می‌کنیم محتوایش را بگیریم
    results = [text]
    try:
        # تست بیس۶۴
        padded = text + "=" * (-len(text) % 4)
        decoded = base64.b64decode(padded).decode('utf-8', errors='ignore')
        results.append(decoded)
    except:
        pass
    return results

def scrape_all():
    all_texts = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for url in FILE_SOURCES:
        try:
            print(f"Fetching: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                content = response.text
                decoded_list = smart_decode(content)
                all_texts.extend(decoded_list)
                
                # بررسی اینکه آیا درون متن لینک‌های ساب دیگر (http) وجود دارد که باید دانلود شوند
                sub_links = re.findall(r'https?://[^\s<>"]+', content)
                for sub_url in sub_links[:3]: # حداکثر ۳ لینک داخلی برای هر منبع
                    try:
                        sub_res = requests.get(sub_url, headers=headers, timeout=10)
                        if sub_res.status_code == 200:
                            all_texts.extend(smart_decode(sub_res.text))
                    except:
                        pass
        except Exception as e:
            print(f"Error with {url}: {e}")
            
    combined = "\n".join(all_texts)
    return {"raw": combined}
