import requests
import base64

def scrape_all():
    url = "https://raw.githubusercontent.com/patterniha/Free-Configs/main/configs.txt"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        print(f"Fetching from target source: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            content = response.text.strip()
            
            # تلاش برای دیکود کردن به عنوان Base64 (چون خیلی از ساب‌ها بیس۶۴ هستند)
            try:
                # اصلاح پدینگ base64 اگر نیاز باشد
                padded = content + "=" * (-len(content) % 4)
                decoded_bytes = base64.b64decode(padded)
                decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
                print("Successfully decoded Base64 content from source.")
                return {"raw": decoded_text}
            except Exception as e:
                # اگر بیس۶۴ نبود، همان متن خام را برمی‌گرداند
                print("Content is plain text.")
                return {"raw": content}
                
    except Exception as e:
        print(f"Error fetching source: {e}")
        
    return {"raw": ""}
