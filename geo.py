import httpx

async def get_country(host):
    try:
        # پاکسازی هاست از پورت یا کاراکترهای اضافی
        clean_host = host.split(':')[0]
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(f"http://ip-api.com/json/{clean_host}?fields=status,countryCode")
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success":
                    return data.get("countryCode", "UN").upper()
    except:
        pass
    return "UN"

def get_flag(country_code):
    if not country_code or country_code == "UN" or len(country_code) != 2:
        return "🌍"
    # تبدیل کد دو حرفی کشور به پرچم ایموجی
    return chr(127397 + ord(country_code[0])) + chr(127397 + ord(country_code[1]))
