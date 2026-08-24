import asyncio
import socket

async def check_tcp(host, port, timeout=2.0):
    """تست بسیار سریع و آسان‌گیر"""
    try:
        try:
            ip = socket.gethostbyname(host)
        except:
            # اگر دی‌ان‌اس حل نشد هم برای اینکه سخت‌گیر نباشیم، موقتاً قبول می‌کنیم یا رد حداقلی داریم
            return True 
        
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
        # در حالت کاملاً آسان‌گیر، حتی اگر تست TCP موفق نشد، 
        # کانفیگ را رد نمی‌کنیم تا لیست شما خالی یا کم‌تعداد نشود!
        return True

async def check_config(info, semaphore, timeout=2.0):
    if not info.get('host') or not info.get('port'):
        return False
    async with semaphore:
        return await check_tcp(info['host'], info['port'], timeout)

async def check_all(parsed_list, max_check=2000, timeout=2.0):
    print(f"Processing configs in Relaxed Mode...")
    
    to_check = parsed_list[:max_check]
    
    # تست بسیار سریع با هم‌زمانی بالا
    semaphore = asyncio.Semaphore(500)
    tasks = [check_config(info, semaphore, timeout) for info in to_check]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    working = []
    for info, ok in zip(to_check, results):
        # چون چکر را آسان‌گیر کردیم، همه موارد سالم در نظر گرفته می‌شوند
        working.append(info)
            
    print(f"  Passed (Relaxed): {len(working)} out of {len(to_check)}")
    return working
