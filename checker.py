import asyncio
import socket

# پورت‌های محبوب و پایدارتر در ایران (TLS و پورت‌های رایج کلودفلر)
PREFERRED_PORTS = {443, 80, 2053, 2083, 2096, 8443, 2087}

async def check_tcp(host, port, timeout=3.5):
    try:
        # استفاده از آی‌پی عمومی یا لوکال با قابلیت هندل کردن خطای دامین
        try:
            ip = socket.gethostbyname(host)
        except socket.gaierror:
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
        return False

async def check_config(info, semaphore, timeout=3.5):
    if not info.get('host') or not info.get('port'):
        return False
    
    async with semaphore:
        return await check_tcp(info['host'], info['port'], timeout)

async def check_all(parsed_list, max_check=2000, timeout=3.5):
    print(f"Testing up to {min(max_check, len(parsed_list))} configs with Iran-optimized checker...")
    
    # اولویت‌بندی کانفیگ‌ها بر اساس پورت‌های پایدارتر (مثل 443)
    sorted_list = sorted(
        parsed_list[:max_check], 
        key=lambda x: 0 if int(x.get('port', 0)) in PREFERRED_PORTS else 1
    )
    
    # کنترل تعداد درخواست‌های هم‌زمان برای جلوگیری از خطای شبکه و بالارفتن دقت
    semaphore = asyncio.Semaphore(150)
    
    tasks = [check_config(info, semaphore, timeout) for info in sorted_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    working = []
    for info, ok in zip(sorted_list, results):
        if ok is True:
            working.append(info)
    
    print(f"  Working: {len(working)} out of {len(sorted_list)}")
    return working
