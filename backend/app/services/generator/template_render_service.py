import json
import re
from html import escape as _e


def _get_theme(category: str, types: str) -> dict:
    text = f"{category or ''} {types or ''}".lower()
    if re.search(r'גריל|פיצ|קפה|מאפ|אוכל|מסעד|restaurant|food|bakery|cafe', text):
        return {'primary': '#dc2626', 'secondary': '#f97316', 'gradient': 'linear-gradient(135deg,#7f1d1d 0%,#dc2626 50%,#f97316 100%)', 'emoji': '🍽️', 'label': 'מסעדנות ואוכל'}
    if re.search(r'ספר|יופי|ציפור|עיצוב שיער|barber|beauty|hair|salon|nail', text):
        return {'primary': '#9333ea', 'secondary': '#ec4899', 'gradient': 'linear-gradient(135deg,#4a1d96 0%,#9333ea 50%,#ec4899 100%)', 'emoji': '✂️', 'label': 'יופי ואסתטיקה'}
    if re.search(r'מוסך|מכונא|שרברב|plumber|mechanic|garage|auto', text):
        return {'primary': '#b45309', 'secondary': '#d97706', 'gradient': 'linear-gradient(135deg,#451a03 0%,#b45309 50%,#d97706 100%)', 'emoji': '🔩', 'label': 'תיקונים ורכב'}
    if re.search(r'חשמל|electrician|electric', text):
        return {'primary': '#1d4ed8', 'secondary': '#0ea5e9', 'gradient': 'linear-gradient(135deg,#1e3a5f 0%,#1d4ed8 50%,#0ea5e9 100%)', 'emoji': '⚡', 'label': 'שירותי חשמל'}
    if re.search(r'מזגן|שיפוץ|ניקיון|hvac|cleaning|renovation', text):
        return {'primary': '#0369a1', 'secondary': '#0284c7', 'gradient': 'linear-gradient(135deg,#082f49 0%,#0369a1 50%,#0284c7 100%)', 'emoji': '🔧', 'label': 'שיפוץ ואחזקה'}
    if re.search(r'גנן|גינ|landscap|garden', text):
        return {'primary': '#15803d', 'secondary': '#16a34a', 'gradient': 'linear-gradient(135deg,#052e16 0%,#15803d 50%,#4ade80 100%)', 'emoji': '🌿', 'label': 'גינון ונוף'}
    if re.search(r'פיזיוטרפ|יוגה|פילאטיס|וטרינר|בריא|gym|fitness|health|yoga|pilates', text):
        return {'primary': '#0f766e', 'secondary': '#059669', 'gradient': 'linear-gradient(135deg,#042f2e 0%,#0f766e 50%,#34d399 100%)', 'emoji': '💪', 'label': 'בריאות וכושר'}
    if re.search(r'גן ילד|ילד|חינוך|kindergarten|school|education', text):
        return {'primary': '#0284c7', 'secondary': '#a21caf', 'gradient': 'linear-gradient(135deg,#0c4a6e 0%,#0284c7 50%,#a21caf 100%)', 'emoji': '🌈', 'label': 'חינוך וילדים'}
    return {'primary': '#7c3aed', 'secondary': '#6366f1', 'gradient': 'linear-gradient(135deg,#1e1b4b 0%,#7c3aed 50%,#6366f1 100%)', 'emoji': '⭐', 'label': 'שירותים מקצועיים'}


def _stars_html(rating: float) -> str:
    if not rating:
        return ''
    full = int(rating)
    half = (rating - full) >= 0.5
    stars = '★' * full + ('½' if half else '') + '☆' * max(0, 5 - full - (1 if half else 0))
    return f'<span style="color:#f59e0b;font-size:20px;letter-spacing:2px">{stars}</span>'


def _clean_phone(phone: str) -> str:
    return re.sub(r'\D', '', phone or '')


class TemplateRenderService:
    def render(self, context: dict) -> str:
        c = context
        name = c.get('site_title') or c.get('hero_title') or 'עסק'
        # Strip " Draft Site" suffix if present
        name = re.sub(r'\s*Draft Site$', '', name)
        hero = c.get('hero_title') or name
        about = c.get('about_text') or ''
        phone = c.get('phone') or ''
        phone_clean = _clean_phone(phone)
        address = c.get('address') or c.get('city') or ''
        rating = c.get('rating')
        reviews_count = c.get('reviews_count') or 0
        website = c.get('website') or ''
        maps_url = c.get('maps_url') or (f'https://www.google.com/maps/search/{phone_clean}' if phone_clean else '')
        opening_hours: list = c.get('opening_hours') or []
        top_review = c.get('top_review') or ''
        services: list = c.get('services') or []
        tagline = c.get('tagline') or ''
        wa_phone = c.get('wa_admin_phone') or '972546363350'
        category = c.get('category') or ''
        types = c.get('business_types') or ''
        is_demo = c.get('is_demo', True)

        # ── XSS sanitisation: escape all user-supplied text before HTML insertion ──
        name        = _e(name)
        hero        = _e(hero)
        about       = _e(about)
        address     = _e(address)
        tagline     = _e(tagline)
        top_review  = _e(top_review)
        services    = [_e(s) for s in services]
        opening_hours = [_e(h) for h in opening_hours]
        # phone_clean already stripped to digits only — safe
        # website / maps_url / wa_url are URL-typed — kept as-is (not reflected into text nodes)

        theme = _get_theme(category, types)
        primary = theme['primary']
        gradient = theme['gradient']
        emoji = theme['emoji']

        # —— WA message ——
        wa_msg = f"שלום! ראיתי את האתר הדמו שלכם עבור \"{name}\" 🌐\nהאתר נראה מדהים! אשמח לשמוע פרטים על בניית האתר המלא ⭐"
        wa_url = f"https://wa.me/{wa_phone}?text={wa_msg.replace(' ', '%20').replace('\n', '%0A')}"

        # —— Demo banner ——
        banner = (
            f'<div style="background:#f59e0b;color:#111;padding:12px 20px;text-align:center;font-size:14px;font-weight:700;direction:rtl">'
            f'⚠️ זהו אתר הדגמה — הכל כאן הוא לצורכי תצוגה בלבד | '
            f'<a href="{wa_url}" target="_blank" style="color:#111;text-decoration:underline">לבניית האתר האמיתי — לחץ כאן</a>'
            f'</div>'
        ) if is_demo else ''

        # —— Services HTML ——
        services_html = ''
        if services:
            items_html = ''.join(
                f'<div style="background:rgba(255,255,255,0.12);border-radius:14px;padding:20px;text-align:center;font-size:15px;font-weight:600;color:white">'
                f'<div style="font-size:28px;margin-bottom:8px">✓</div>{s}</div>'
                for s in services[:6]
            )
            services_html = f'''
            <section style="padding:60px 0;background:{primary}">
              <div style="max-width:900px;margin:0 auto;padding:0 20px">
                <h2 style="text-align:center;color:white;font-size:28px;margin-bottom:36px;font-weight:800">השירותים שלנו</h2>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px">
                  {items_html}
                </div>
              </div>
            </section>'''

        # —— Rating HTML ——
        rating_html = ''
        if rating:
            stars = _stars_html(rating)
            rating_html = f'''
            <section style="padding:60px 0;background:#fffbeb">
              <div style="max-width:700px;margin:0 auto;padding:0 20px;text-align:center">
                <h2 style="font-size:26px;font-weight:800;color:#111827;margin-bottom:8px">דירוג לקוחות</h2>
                <div style="font-size:52px;font-weight:900;color:#111827;margin:12px 0">{rating}</div>
                <div style="margin-bottom:8px">{stars}</div>
                <div style="color:#6b7280;font-size:15px">מבוסס על {reviews_count} ביקורות בגוגל</div>
                {f'<blockquote style="margin:24px auto;max-width:560px;background:white;border-right:4px solid {primary};padding:16px 20px;border-radius:12px;text-align:right;color:#374151;font-style:italic;box-shadow:0 2px 8px rgba(0,0,0,0.06)">&ldquo;{top_review}&rdquo;</blockquote>' if top_review else ''}
              </div>
            </section>''' if rating else ''

        # —— Hours HTML ——
        hours_html = ''
        if opening_hours:
            rows = ''.join(
                f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9;font-size:14px">'
                f'<span style="color:#6b7280">{h.split(":")[0].strip() if ":" in h else h}</span>'
                f'<span style="font-weight:600;color:#111827">{":".join(h.split(":")[1:]).strip() if ":" in h else ""}</span>'
                f'</div>'
                for h in opening_hours[:7]
            )
            hours_html = f'<div style="background:#f8fafc;border-radius:14px;padding:20px">{rows}</div>'

        # —— Tagline ——
        tagline_line = f'<p style="font-size:18px;color:rgba(255,255,255,0.85);margin:10px 0 0;font-weight:500">{tagline}</p>' if tagline else ''

        return f'''<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <meta name="robots" content="noindex,nofollow"/>
  <title>{name}</title>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:"Segoe UI",Arial,"Helvetica Neue",sans-serif;color:#111827;background:#f8fafc;direction:rtl}}
    a{{text-decoration:none;color:inherit}}
    img{{max-width:100%}}
    @media(max-width:640px){{
      .hero-title{{font-size:30px!important}}
      .cta-row{{flex-direction:column!important;align-items:stretch!important}}
      .cta-row a{{text-align:center}}
    }}
  </style>
</head>
<body>
{banner}

<!-- ── HERO ──────────────────────────────────────────── -->
<section style="background:{gradient};padding:80px 20px 60px;text-align:center;position:relative;overflow:hidden">
  <div style="position:absolute;inset:0;background:rgba(0,0,0,0.25)"></div>
  <div style="position:relative;max-width:800px;margin:0 auto">
    <div style="font-size:56px;margin-bottom:16px">{emoji}</div>
    <h1 class="hero-title" style="font-size:42px;font-weight:900;color:white;line-height:1.25;text-shadow:0 2px 12px rgba(0,0,0,0.3);margin-bottom:12px">{name}</h1>
    {tagline_line}
    {f'<p style="font-size:16px;color:rgba(255,255,255,0.75);margin-top:10px">📍 {address}</p>' if address else ''}
    {f'<div style="margin-top:16px">{_stars_html(rating)}<span style="color:rgba(255,255,255,0.85);font-size:15px;margin-right:8px">{rating} ({reviews_count} ביקורות)</span></div>' if rating else ''}
    <div class="cta-row" style="display:flex;gap:16px;justify-content:center;margin-top:32px;flex-wrap:wrap">
      {f'<a href="tel:{phone_clean}" style="display:inline-flex;align-items:center;gap:10px;background:#16a34a;color:white;border-radius:50px;padding:16px 36px;font-size:18px;font-weight:700;box-shadow:0 8px 24px rgba(22,163,74,0.45)">📞 {phone}</a>' if phone else ''}
      <a href="{wa_url}" target="_blank" style="display:inline-flex;align-items:center;gap:10px;background:#25d366;color:white;border-radius:50px;padding:16px 36px;font-size:17px;font-weight:700;box-shadow:0 8px 24px rgba(37,211,102,0.45)">💬 יצירת קשר</a>
    </div>
  </div>
</section>

{services_html}

<!-- ── ABOUT ──────────────────────────────────────────── -->
<section style="padding:64px 20px;background:white">
  <div style="max-width:760px;margin:0 auto">
    <h2 style="font-size:28px;font-weight:800;color:#111827;margin-bottom:20px;text-align:center">אודותינו</h2>
    <p style="font-size:17px;line-height:1.85;color:#374151;text-align:center">{about}</p>
  </div>
</section>

{rating_html}

<!-- ── CONTACT + HOURS ────────────────────────────────── -->
<section id="contact" style="padding:64px 20px;background:#f8fafc">
  <div style="max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr{' 1fr' if opening_hours else ''};gap:32px">
    <!-- Contact card -->
    <div style="background:white;border-radius:20px;padding:32px;box-shadow:0 4px 16px rgba(0,0,0,0.07)">
      <h2 style="font-size:22px;font-weight:800;color:#111827;margin-bottom:20px">📞 פרטי קשר</h2>
      {f'<div style="display:flex;align-items:center;gap:12px;padding:14px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:20px">📱</span><a href="tel:{phone_clean}" style="font-size:17px;font-weight:700;color:{primary}">{phone}</a></div>' if phone else ''}
      {f'<div style="display:flex;align-items:center;gap:12px;padding:14px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:20px">📍</span><span style="font-size:15px;color:#374151">{address}</span></div>' if address else ''}
      {f'<div style="display:flex;align-items:center;gap:12px;padding:14px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:20px">🌐</span><a href="{website}" target="_blank" style="font-size:15px;color:{primary}">{website}</a></div>' if website else ''}
      {f'<div style="display:flex;align-items:center;gap:12px;padding:14px 0"><span style="font-size:20px">🗺️</span><a href="{maps_url}" target="_blank" style="font-size:15px;font-weight:600;color:{primary}">הצג במפות גוגל</a></div>' if maps_url else ''}
      <div style="margin-top:24px;display:flex;flex-direction:column;gap:12px">
        {f'<a href="tel:{phone_clean}" style="display:flex;align-items:center;justify-content:center;gap:10px;background:#16a34a;color:white;border-radius:50px;padding:14px 20px;font-size:16px;font-weight:700">📞 התקשר עכשיו</a>' if phone else ''}
        <a href="{wa_url}" target="_blank" style="display:flex;align-items:center;justify-content:center;gap:10px;background:#25d366;color:white;border-radius:50px;padding:14px 20px;font-size:16px;font-weight:700">💬 שלח הודעת WhatsApp</a>
      </div>
    </div>
    {f'''<div style="background:white;border-radius:20px;padding:32px;box-shadow:0 4px 16px rgba(0,0,0,0.07)">
      <h2 style="font-size:22px;font-weight:800;color:#111827;margin-bottom:20px">🕐 שעות פתיחה</h2>
      {hours_html}
    </div>''' if opening_hours else ''}
  </div>
</section>

<!-- ── FOOTER ──────────────────────────────────────────── -->
<footer style="background:#111827;color:rgba(255,255,255,0.6);text-align:center;padding:28px 20px;font-size:13px">
  <div style="color:white;font-size:16px;font-weight:700;margin-bottom:6px">{name}</div>
  {f'<div>{address}</div>' if address else ''}
  {f'<div style="margin-top:4px"><a href="tel:{phone_clean}" style="color:rgba(255,255,255,0.7)">{phone}</a></div>' if phone else ''}
  {'<div style="margin-top:12px;font-size:11px;color:rgba(255,255,255,0.3)">אתר זה הוא הדגמה בלבד — נוצר על ידי TAZO-WEB</div>' if is_demo else ''}
</footer>

</body>
</html>'''
