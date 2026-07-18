import asyncio
import socket

async def check_tcp(host, port, timeout=4):
    try:
        try:
            ip = socket.gethostbyname(host)
        except:
            return False
        
        loop = asyncio.get_event_loop()
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

async def check_config(info, timeout=4):
    if not info.get('host') or not info.get('port'):
        return False
    return await check_tcp(info['host'], info['port'], timeout)

async def check_all(parsed_list, max_check=500, timeout=4):
    print(f"Testing {min(max_check, len(parsed_list))} configs (1-2 minutes)...")
    
    to_check = parsed_list[:max_check]
    
    tasks = [check_config(info, timeout) for info in to_check]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    working = []
    for info, ok in zip(to_check, results):
        if ok is True:
            working.append(info)
    
    print(f"  Working: {len(working)} out of {len(to_check)}")
    return working
