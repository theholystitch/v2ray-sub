import asyncio
import socket
import time

async def check_tcp(host, port, timeout=3.5):
    """
    Standard strict TCP checker
    - Validates port range
    - Async DNS via getaddrinfo
    - TCP connect with timeout
    - Proper socket cleanup
    - Returns (ok: bool, latency_ms: float | None)
    """
    # Validate port
    try:
        port = int(port)
        if not 1 <= port <= 65535:
            return False, None
    except:
        return False, None

    if not host or len(host) > 253:
        return False, None

    clean_host = host.strip().split(':')[0].split('/')[0]
    if not clean_host:
        return False, None

    sock = None
    start = time.perf_counter()
    try:
        loop = asyncio.get_running_loop()
        
        # Async DNS resolve - respects timeout
        infos = await asyncio.wait_for(
            loop.getaddrinfo(clean_host, port, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM),
            timeout=timeout
        )
        if not infos:
            return False, None

        # Try each resolved addr (handles IPv4/IPv6)
        last_exc = None
        for family, socktype, proto, _, sockaddr in infos:
            sock = socket.socket(family, socktype, proto)
            sock.setblocking(False)
            try:
                await asyncio.wait_for(
                    loop.sock_connect(sock, sockaddr),
                    timeout=timeout
                )
                latency = (time.perf_counter() - start) * 1000
                return True, latency
            except Exception as e:
                last_exc = e
                try:
                    sock.close()
                except:
                    pass
                sock = None
                # try next addr if exists
                continue
        
        return False, None

    except (socket.gaierror, asyncio.TimeoutError, OSError, ValueError):
        return False, None
    except Exception:
        return False, None
    finally:
        if sock is not None:
            try:
                sock.close()
            except:
                pass


async def check_config(info, semaphore, timeout=3.5):
    if not info.get('host') or not info.get('port'):
        return (False, None)
    async with semaphore:
        ok, latency = await check_tcp(info['host'], info['port'], timeout)
        return (ok, latency)


async def check_all(parsed_list, max_check=500, timeout=3.5):
    """
    Standard checker with latency sorting
    - Strict filtering (only TCP-success passes)
    - Concurrency 100 (not 500) to avoid fd/ratelimit false-negatives
    - Sorted by latency (fastest first)
    """
    print(f"Processing configs in Strict Mode (timeout={timeout}s)...")
    
    to_check = parsed_list[:max_check]
    if not to_check:
        return []

    semaphore = asyncio.Semaphore(100)
    tasks = [check_config(info, semaphore, timeout) for info in to_check]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    passed = []
    for info, res in zip(to_check, results):
        if isinstance(res, Exception):
            continue
        ok, latency = res
        if ok is True:
            # store latency for sorting
            info['_latency'] = latency
            passed.append(info)
    
    # Sort by latency (fastest first) - standard for good subs
    passed.sort(key=lambda x: x.get('_latency', 9999))

    # cleanup temp key if you don't want it in output
    for info in passed:
        info.pop('_latency', None)
            
    print(f"  Passed (Strict): {len(passed)} out of {len(to_check)} ({len(passed)/len(to_check)*100:.1f}%)")
    return passed
