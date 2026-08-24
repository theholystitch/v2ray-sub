import requests
import base64

def scrape_all():
    url = "https://raw.githubusercontent.com/patterniha/Free-Configs/main/configs.txt"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        print(f"Fetching from target source: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text.strip()
            print(f"Raw content length fetched: {len(content)}")
            
            # اگر محتوا بیس۶۴ باشد
            try:
                padded = content + "=" * (-len(content) % 4)
                decoded_bytes = base64.b64decode(padded)
                decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
                print(f"Decoded text length: {len(decoded_text)}")
                return {"raw": decoded_text}
            except Exception as e:
                print(f"Not base64, using plain text. Error: {e}")
                return {"raw": content}
        else:
            print(f"Failed to fetch. Status code: {response.status_code}")
    except Exception as e:
        print(f"Connection Error fetching source: {e}")
        
    return {"raw": ""}
