import requests
import base64

def scrape_all():
    url = "https://raw.githubusercontent.com/patterniha/Free-Configs/main/configs.txt"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        print(f"Fetching from target source: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            content = response.text
            # اگر محتوا بیس۶۴ بود دیکود می‌کند، در غیر این صورت متن خام برمی‌گرداند
            try:
                decoded = base64.b64decode(content.strip()).decode('utf-8')
                return {"raw": decoded}
            except:
                return {"raw": content}
    except Exception as e:
        print(f"Error fetching source: {e}")
        
    return {"raw": ""}
