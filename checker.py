import asyncio
import socket

async def check_tcp(host, port, timeout=2.0):
    """تست اتصال با تایم‌اوت پایین‌تر و آسان‌گیرتر"""
    try:
        try:
            ip = socket.gethostbyname(host)
        except socket.gaierror:
            # اگر دی‌ان‌اس حل نشد، باز هم یک‌بار دیگر شانس می‌دهیم یا رد می‌کنیم
            return False
        
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        
        await asyncio.wait_for(
            loop.sock_connect(sock, (ip, int(port))),
            timeout=timeout
        )
        sock.close()
        return True
    except:
        # در حالت آسان‌گیر، حتی اگر اتصال کامل برقرار نشد اما هاست فرمت درستی داشت، 
        # می‌توانید اینجا روی True تنظیم کنید تا هیچ‌کدام رد نشوند! 
        # (اما فعلاً برای اینکه فقط کانفیگ‌های کاملا مرده حذف شوند، تایم‌اوت را کم کردیم)
        return False

async def check_config(info, semaphore, timeout=2.0):
    if not info.get('host') or not info.get('port'):
        return False
    
    async with semaphore:
        return await check_tcp(info['host'], info['port'], timeout)

async def check_all(parsed_list, max_check=6000, timeout=2.0):
    print(f"Testing up to {min(max_check, len(parsed_list))} configs (Easy mode)...")
    
    to_check = parsed_list[:max_check]
    
    # افزایش شدید سرعت و هم‌زمانی برای اینکه تست‌ها سریع‌تر رد شوند
    semaphore = asyncio.Semaphore(500)
    
    tasks = [check_config(info, semaphore, timeout) for info in to_check]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    working = []
    for info, ok in zip(to_check, results):
        # در حالت آسان‌گیر، اگر تست هم موفق نبود اما خواستید تعداد بالا بماند، 
        # می‌توانید شرط را بردارید یا همه را قبول کنید. 
        # فعلا کانفیگ‌هایی که جواب مثبت دادند یا سرعت بالایی داشتند را برمی‌گردانیم.
        if ok is True:
            working.append(info)
            
    # اگر تعداد سالم‌ها خیلی کم بود، به طور خودکار از کل لیست اولیه بدون تستِ سخت‌گیرانه استفاده می‌کنیم
    if len(working) < 50:
        print("  Warning: Too few working configs found. Falling back to relaxed mode (taking top configs directly)...")
        return to_check[:500]  # مستقیماً ۵۰۰ کانفیگ اول از لیست‌های گیت‌هاب را برمی‌گرداند تا همیشه ساب پر باشد!

    print(f"  Working: {len(working)} out of {len(to_check)}")
    return working
