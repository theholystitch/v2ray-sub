import socket
import httpx
import asyncio

FLAGS = {
    'US': '🇺🇸', 'DE': '🇩🇪', 'FR': '🇫🇷', 'NL': '🇳🇱', 'GB': '🇬🇧',
    'CA': '🇨🇦', 'JP': '🇯🇵', 'SG': '🇸🇬', 'KR': '🇰🇷', 'HK': '🇭🇰',
    'TW': '🇹🇼', 'TR': '🇹🇷', 'IR': '🇮🇷', 'RU': '🇷🇺', 'IT': '🇮🇹',
    'ES': '🇪🇸', 'SE': '🇸🇪', 'FI': '🇫🇮', 'CH': '🇨🇭', 'AT': '🇦🇹',
    'PL': '🇵🇱', 'RO': '🇷🇴', 'IE': '🇮🇪', 'BE': '🇧🇪', 'DK': '🇩🇰',
    'NO': '🇳🇴', 'CZ': '🇨🇿', 'HU': '🇭🇺', 'PT': '🇵🇹', 'GR': '🇬🇷',
    'AU': '🇦🇺', 'BR': '🇧🇷', 'IN': '🇮🇳', 'ID': '🇮🇩', 'TH': '🇹🇭',
    'VN': '🇻🇳', 'MY': '🇲🇾', 'PH': '🇵🇭', 'AE': '🇦🇪', 'SA': '🇸🇦',
    'IL': '🇮🇱', 'EG': '🇪🇬', 'ZA': '🇿🇦', 'MX': '🇲🇽', 'AR': '🇦🇷',
    'UA': '🇺🇦', 'GE': '🇬🇪', 'AM': '🇦🇲', 'AZ': '🇦🇿', 'CY': '🇨🇾',
}

async def get_country(host):
    try:
        try:
            ip = socket.gethostbyname(host)
        except:
            return 'UN'
        
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"http://ip-api.com/json/{ip}?fields=countryCode")
            if r.status_code == 200:
                return r.json().get('countryCode', 'UN')
    except:
        pass
    return 'UN'

def get_flag(code):
    return FLAGS.get(code, '🌐')
