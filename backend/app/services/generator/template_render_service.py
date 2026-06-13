import re

from app.services.generator import premium_templates as _premium_templates


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


import re as _re

_FOOD_RE = _re.compile(r'פיצ|גריל|שוורמ|פלאפל|המבורגר|מסעד|סושי|אוכל|קפה|מאפ|restaurant|food|pizza|grill|burger|bakery|cafe', _re.I)

def _is_food(category: str, types: str) -> bool:
    return bool(_FOOD_RE.search(f"{category or ''} {types or ''}"))

def _food_menu(category: str, types: str) -> list:
    txt = f"{category or ''} {types or ''}".lower()
    if re.search(r'פיצ|pizza', txt):
        return [
            {"cat": "🍕 פיצות", "items": [
                {"name": "מרגריטה", "desc": "עגבניות, גבינה, בזיל", "price": 45},
                {"name": "ארבע גבינות", "desc": "ריקוטה, מוצרלה, גאודה, עיזים", "price": 58},
                {"name": "ירקות", "desc": "פלפל, פטריות, זיתים, בצל", "price": 52},
                {"name": "פפרוני", "desc": "פפרוני, מוצרלה, רוטב עגבניות", "price": 62},
                {"name": "טורקית", "desc": "בשר טחון, פיקנטי, ירקות", "price": 55},
                {"name": "מיקס", "desc": "חצי מרגריטה + חצי ירקות", "price": 68},
            ]},
            {"cat": "🥤 שתיות", "items": [
                {"name": "קולה / דיאט", "desc": "330 מ'ל", "price": 10},
                {"name": "ספריט", "desc": "330 מ'ל", "price": 10},
                {"name": "מים", "desc": "500 מ'ל", "price": 6},
                {"name": "מיץ תפוזים", "desc": "טרי, 300 מ'ל", "price": 12},
            ]},
            {"cat": "🍰 קינוחים", "items": [
                {"name": "עוגיות שוקולד", "desc": "6 יחידות", "price": 18},
                {"name": "בראוני", "desc": "חמים עם גלידה", "price": 22},
            ]},
        ]
    elif re.search(r'גריל|שוורמ|grill|shawarma', txt):
        return [
            {"cat": "🥩 מנות עיקריות", "items": [
                {"name": "שוורמה בפיתה", "desc": "ירקות, טחינה, חריף", "price": 42},
                {"name": "שוורמה בלחמנייה", "desc": "ירקות, חמוצים", "price": 45},
                {"name": "אנטריקוט 250 גרם", "desc": "על הפחמים", "price": 89},
                {"name": "קבב", "desc": "3 שיפודים, צ'יפס, סלט", "price": 68},
                {"name": "עוף גריל", "desc": "חצי עוף, ירקות", "price": 65},
            ]},
            {"cat": "🥗 תוספות", "items": [
                {"name": "צ'יפס", "desc": "גדול", "price": 18},
                {"name": "סלט ירקות", "desc": "טרי", "price": 14},
                {"name": "חמוצים", "desc": "מנה", "price": 8},
                {"name": "לחם שאור", "desc": "2 יחידות", "price": 10},
            ]},
            {"cat": "🥤 שתיות", "items": [
                {"name": "שתייה קרה", "desc": "330 מ'ל", "price": 10},
                {"name": "מים", "desc": "500 מ'ל", "price": 6},
            ]},
        ]
    else:
        return [
            {"cat": "🍽️ תפריט ראשי", "items": [
                {"name": "מנת פתיחה", "desc": "לפי בחירת השף", "price": 45},
                {"name": "מנה עיקרית", "desc": "עם תוספות ביתיות", "price": 68},
                {"name": "מנה ילדים", "desc": "מנה קטנה ומיוחדת", "price": 35},
            ]},
            {"cat": "🥤 שתיות", "items": [
                {"name": "שתייה קרה", "desc": "330 מ'ל", "price": 10},
                {"name": "מים", "desc": "500 מ'ל", "price": 6},
            ]},
        ]

_SUPPORT_FLOAT_BTN = (
    '<a href="tel:+972533889859" title="שירות לקוחות AI 24/7" '
    'style="position:fixed;bottom:20px;left:16px;z-index:9990;'
    'background:linear-gradient(135deg,#0f172a,#1d4ed8);color:white;'
    'border-radius:50px;padding:10px 18px;font-size:13px;font-weight:700;'
    'box-shadow:0 4px 20px rgba(0,0,0,.4);text-decoration:none;'
    'display:flex;align-items:center;gap:8px;direction:rtl">'
    '📞 תמיכה 24/7</a>'
)


def _build_site_banner(is_demo: bool, phase: str = 'beta') -> str:
    """Return sticky top banner HTML. Beta sites get a BETA tag + claim CTA."""
    if not is_demo:
        return ''
    beta_tag = (
        '<span style="background:#f59e0b;color:#000;border-radius:4px;padding:1px 7px;font-size:11px;font-weight:900;letter-spacing:1px;margin-left:8px">BETA</span>'
        if phase == 'beta' else ''
    )
    banner = (
        f'<div style="background:#0f172a;color:#f8fafc;padding:9px 16px;text-align:center;'
        f'font-size:13px;font-weight:700;position:sticky;top:0;z-index:9999;display:flex;'
        f'align-items:center;justify-content:center;gap:8px;border-bottom:2px solid #f59e0b">'
        f'{beta_tag}'
        f'אתר זה בגרסת BETA — מידע עשוי להיות חלקי &nbsp;'
        f'<a href="https://tazo-web.com/claim" target="_blank" rel="noopener" '
        f'style="color:#f59e0b;text-decoration:underline;font-weight:900">שדרג לגרסה מלאה ←</a>'
        f'</div>'
    ) if phase == 'beta' else (
        f'<div style="background:#f8fafc;color:#111827;padding:10px 16px;text-align:center;'
        f'font-size:13px;font-weight:800;border-bottom:1px solid rgba(15,23,42,.08)">'
        f'בעל/ת העסק? <a href="https://tazo-sync.com/dashboard?action=claim&source=tazo-web" '
        f'target="_blank" rel="noopener" style="color:#111827;text-decoration:underline">תבעו בעלות וערכו באתר</a></div>'
    )
    return banner + _SUPPORT_FLOAT_BTN


def _render_food(c: dict) -> str:
    from html import escape as _e
    import re as _re
    import json as _json
    from urllib.parse import quote as _quote

    name_raw = _re.sub(r"\s*Draft Site$", "", c.get("site_title") or c.get("hero_title") or "העסק")
    name = _e(name_raw)
    phone = _re.sub(r"\D", "", c.get("phone") or "")
    wa_phone = c.get("wa_admin_phone") or "972546363350"
    category = c.get("category") or ""
    types = c.get("business_types") or ""
    city = _e(c.get("city") or "")
    about = _e(c.get("about_text") or "")
    tagline = _e(c.get("tagline") or "")
    hero_image_url = c.get("hero_image_url") or ""
    gallery_images: list = c.get("gallery_images") or []
    rating = c.get("rating") or 0
    reviews_count = c.get("reviews_count") or 0
    maps_url = _e(c.get("maps_url") or "")

    menu = c.get("menu_items") or _food_menu(category, types)
    menu_json = _json.dumps(menu, ensure_ascii=False)

    biz_phone_attr = f'data-biz-phone="{phone}"' if phone else ""
    claim_url = (
        "https://tazo-sync.com/dashboard?action=claim"
        f"&phone={_quote(phone)}&business={_quote(name_raw)}&source=tazo-web"
    )
    phase = c.get('phase', 'beta')
    beta_bar = _build_site_banner(True, phase) if phase == 'beta' else ''
    owner_bar = (
        f'{beta_bar}'
        f'<div class="owner-claim" role="region" aria-label="תביעת בעלות">'
        f'<span>בעל/ת העסק?</span>'
        f'<a href="{claim_url}" target="_blank" rel="noopener">תבעו בעלות וערכו תפריט, תמונות ומחירים</a>'
        f'</div>'
    )

    return f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="robots" content="index,follow"/>
<title>{name}</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Heebo","Segoe UI",Arial,sans-serif;background:#111;color:#f5f5f5;direction:rtl;min-height:100vh}}
a{{text-decoration:none;color:inherit}}
button{{font-family:inherit;cursor:pointer;border:none}}
input,textarea{{font-family:inherit}}
.owner-claim{{position:sticky;top:0;z-index:260;display:flex;align-items:center;justify-content:center;gap:10px;padding:9px 14px;background:#f8fafc;color:#111827;border-bottom:1px solid rgba(15,23,42,.08);font-size:13px;font-weight:800;direction:rtl}}
.owner-claim a{{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;background:#111827;color:#fff;padding:7px 14px;font-weight:900;box-shadow:0 8px 22px rgba(15,23,42,.18)}}
/* HEADER */
.hdr{{position:sticky;top:39px;z-index:200;background:rgba(17,17,17,.95);backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,.08);padding:12px 20px;display:flex;align-items:center;justify-content:space-between;gap:12px}}
.hdr-title{{font-size:18px;font-weight:800}}
.hdr-sub{{font-size:12px;color:rgba(255,255,255,.5)}}
.cart-btn{{background:linear-gradient(135deg,#dc2626,#f97316);border-radius:50px;padding:10px 18px;color:white;font-weight:700;font-size:14px;display:flex;align-items:center;gap:8px;position:relative}}
.cart-badge{{background:white;color:#dc2626;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:900;min-width:20px}}
/* HERO */
.hero{{position:relative;background:linear-gradient(135deg,#7f1d1d,#dc2626,#f97316);padding:36px 20px;text-align:center;overflow:hidden}}
.hero-bg{{position:absolute;inset:0;object-fit:cover;width:100%;height:100%;opacity:.25;pointer-events:none}}
.hero-content{{position:relative;z-index:1}}
.hero h1{{font-size:clamp(26px,5vw,42px);font-weight:900;margin-bottom:8px}}
.hero p{{color:rgba(255,255,255,.8);font-size:15px;margin-bottom:20px}}
.order-type{{display:flex;gap:0;border-radius:10px;overflow:hidden;border:2px solid rgba(255,255,255,.3);display:inline-flex}}
.order-type-btn{{padding:10px 24px;font-size:14px;font-weight:700;cursor:pointer;transition:all .2s;font-family:inherit;color:white;background:transparent}}
.order-type-btn.active{{background:white;color:#dc2626}}
/* RATING STRIP */
.rating-strip{{display:flex;align-items:center;justify-content:center;gap:10px;padding:10px 20px;background:rgba(0,0,0,.25);font-size:13px;font-weight:700}}
.rating-stars{{color:#fbbf24;font-size:16px;letter-spacing:1px}}
/* MENU */
.menu-wrap{{max-width:900px;margin:0 auto;padding:20px}}
.cat-tabs{{display:flex;gap:8px;overflow-x:auto;padding-bottom:12px;margin-bottom:20px;scrollbar-width:none}}
.cat-tabs::-webkit-scrollbar{{display:none}}
.cat-tab{{white-space:nowrap;padding:8px 18px;border-radius:50px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);color:rgba(255,255,255,.6);font-size:14px;font-weight:600;cursor:pointer;transition:all .2s;font-family:inherit}}
.cat-tab.active{{background:linear-gradient(135deg,#dc2626,#f97316);color:white;border-color:transparent}}
.menu-section{{margin-bottom:32px}}
.menu-section-title{{font-size:17px;font-weight:800;margin-bottom:14px;color:rgba(255,255,255,.8);padding:0 4px}}
.item-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}}
.item-card{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:16px;overflow:hidden;display:flex;flex-direction:column;transition:all .2s}}
.item-card:hover{{background:rgba(255,255,255,.09);border-color:rgba(255,255,255,.16)}}
.item-img{{width:100%;height:140px;object-fit:cover;display:block}}
.item-img-placeholder{{width:100%;height:100px;background:linear-gradient(135deg,rgba(220,38,38,.25),rgba(249,115,22,.25));display:flex;align-items:center;justify-content:center;font-size:32px}}
.item-body{{padding:14px;display:flex;flex-direction:column;gap:6px;flex:1}}
.item-name{{font-size:15px;font-weight:700}}
.item-desc{{font-size:13px;color:rgba(255,255,255,.5);line-height:1.5}}
.item-footer{{display:flex;align-items:center;justify-content:space-between;margin-top:auto;padding-top:8px}}
.item-price{{font-size:18px;font-weight:800;color:#f97316}}
.qty-ctrl{{display:flex;align-items:center;gap:10px}}
.qty-btn{{width:30px;height:30px;border-radius:50%;background:rgba(255,255,255,.1);color:white;font-size:16px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-family:inherit;transition:background .2s}}
.qty-btn:hover{{background:rgba(255,255,255,.2)}}
.qty-num{{font-size:15px;font-weight:700;min-width:16px;text-align:center}}
/* CART DRAWER */
.cart-overlay{{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:400;opacity:0;pointer-events:none;transition:opacity .3s}}
.cart-overlay.open{{opacity:1;pointer-events:all}}
.cart-drawer{{position:fixed;top:0;left:-100%;width:min(400px,100vw);height:100%;background:#1a1a1a;z-index:500;display:flex;flex-direction:column;box-shadow:-8px 0 40px rgba(0,0,0,.6);transition:left .35s cubic-bezier(.4,0,.2,1)}}
.cart-drawer.open{{left:0}}
.cart-hdr{{padding:20px;border-bottom:1px solid rgba(255,255,255,.1);display:flex;justify-content:space-between;align-items:center}}
.cart-hdr h3{{font-size:20px;font-weight:800}}
.close-btn{{width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,.08);color:white;font-size:20px;display:flex;align-items:center;justify-content:center;cursor:pointer}}
.cart-items{{flex:1;overflow-y:auto;padding:16px}}
.cart-item{{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid rgba(255,255,255,.06)}}
.cart-item-info{{flex:1}}
.cart-item-name{{font-size:14px;font-weight:600}}
.cart-item-price{{font-size:13px;color:#f97316}}
.cart-footer{{padding:20px;border-top:1px solid rgba(255,255,255,.1)}}
.cart-total{{font-size:20px;font-weight:800;margin-bottom:16px;display:flex;justify-content:space-between}}
.checkout-btn{{width:100%;padding:16px;border-radius:14px;background:linear-gradient(135deg,#dc2626,#f97316);color:white;font-size:16px;font-weight:700;cursor:pointer;font-family:inherit}}
/* CHECKOUT OVERLAY */
.checkout-overlay{{position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:600;display:none;align-items:center;justify-content:center;padding:20px}}
.checkout-overlay.open{{display:flex}}
.checkout-box{{background:#1e1e1e;border-radius:24px;padding:28px;width:100%;max-width:480px;max-height:90vh;overflow-y:auto}}
.checkout-box h2{{font-size:22px;font-weight:800;margin-bottom:20px}}
.form-group{{margin-bottom:16px}}
.form-group label{{font-size:13px;color:rgba(255,255,255,.6);display:block;margin-bottom:6px}}
.form-group input,.form-group textarea{{width:100%;padding:12px 16px;border-radius:12px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.06);color:white;font-size:15px;outline:none;direction:rtl}}
.form-group textarea{{resize:vertical;min-height:80px}}
.wa-order-btn{{width:100%;padding:16px;border-radius:14px;background:linear-gradient(135deg,#25d366,#128c7e);color:white;font-size:16px;font-weight:700;cursor:pointer;font-family:inherit;margin-top:8px}}
.empty-cart{{text-align:center;padding:40px 20px;color:rgba(255,255,255,.4)}}
.empty-cart div:first-child{{font-size:48px;margin-bottom:12px}}
</style>
</head>
<body {biz_phone_attr}>
{owner_bar}

<header class="hdr">
  <div>
    <div class="hdr-title">{name}</div>
    {f'<div class="hdr-sub">{city}</div>' if city else ''}
  </div>
  <button class="cart-btn" onclick="toggleCart()">
    🛒 סל הזמנה
    <span class="cart-badge" id="cart-count">0</span>
  </button>
</header>

<section class="hero">
  {f'<img class="hero-bg" src="{_e(hero_image_url)}" alt="" loading="eager"/>' if hero_image_url else ''}
  <div class="hero-content">
    <h1>{name}</h1>
    {f'<p>{tagline}</p>' if tagline else ('<p>הזמנה מהירה לדלת שלך 🚀</p>')}
    <div class="order-type">
      <button class="order-type-btn active" onclick="setOrderType(this,'delivery')">🛵 משלוח</button>
      <button class="order-type-btn" onclick="setOrderType(this,'pickup')">🏃 איסוף עצמי</button>
    </div>
  </div>
</section>
{f'<div class="rating-strip"><span class="rating-stars">{"★" * int(float(rating))}{"☆" * (5 - int(float(rating)))}</span><span>{rating} דירוג ({reviews_count} ביקורות)</span>{"<a href=" + chr(34) + maps_url + chr(34) + " target=_blank style=color:#fbbf24;font-size:12px>&#128205; ראה בגוגל</a>" if maps_url else ""}</div>' if rating else ''}

<div class="menu-wrap">
  <div class="cat-tabs" id="cat-tabs"></div>
  <div id="menu-sections"></div>
</div>

{f'<section style="padding:40px 20px;max-width:700px;margin:0 auto"><h2 style="font-size:20px;font-weight:800;margin-bottom:12px">אודות</h2><p style="color:rgba(255,255,255,.6);line-height:1.8;font-size:15px">{about}</p></section>' if about else ''}

{f'<div style="text-align:center;padding:20px 20px 40px"><a href="tel:{phone}" style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:50px;padding:14px 28px;font-weight:700;color:white">📞 {phone}</a></div>' if phone else ''}

<!-- Cart Overlay -->
<div class="cart-overlay" id="cart-overlay" onclick="toggleCart()"></div>

<!-- Cart Drawer -->
<div class="cart-drawer" id="cart-drawer">
  <div class="cart-hdr">
    <h3>🛒 סל הזמנה</h3>
    <button class="close-btn" onclick="toggleCart()">✕</button>
  </div>
  <div class="cart-items" id="cart-items-list"></div>
  <div class="cart-footer">
    <div class="cart-total">
      <span>סה"כ</span>
      <span id="cart-total-price">₪0</span>
    </div>
    <button class="checkout-btn" onclick="openCheckout()">המשך לתשלום →</button>
  </div>
</div>

<!-- Checkout -->
<div class="checkout-overlay" id="checkout-overlay">
  <div class="checkout-box">
    <h2>פרטי ההזמנה</h2>
    <div class="form-group">
      <label>שם מלא *</label>
      <input type="text" id="c-name" placeholder="ישראל ישראלי"/>
    </div>
    <div class="form-group">
      <label>טלפון *</label>
      <input type="tel" id="c-phone" placeholder="05X-XXXXXXX"/>
    </div>
    <div class="form-group" id="delivery-address-group">
      <label>כתובת למשלוח *</label>
      <input type="text" id="c-address" placeholder="רחוב, מספר, עיר"/>
    </div>
    <div class="form-group">
      <label>הערות</label>
      <textarea id="c-notes" placeholder="ללא גלוטן, פיצוי... כל הערה שתרצה"></textarea>
    </div>
    <button class="wa-order-btn" id="submit-order-btn" onclick="startOtpFlow()">
      &#x1f4ac; שלח הזמנה
    </button>
    <button onclick="document.getElementById('checkout-overlay').classList.remove('open')" style="width:100%;padding:12px;border-radius:12px;background:rgba(255,255,255,.06);color:white;font-size:14px;margin-top:10px;cursor:pointer;font-family:inherit">
      &#x2190; חזרה לתפריט
    </button>
  </div>
</div>

<!-- OTP Verification Overlay -->
<div id="otp-overlay" style="position:fixed;inset:0;background:rgba(0,0,0,0.88);z-index:1100;display:none;align-items:center;justify-content:center;padding:20px">
  <div style="background:linear-gradient(135deg,#0f1723,#1a2744);border:1px solid rgba(14,230,208,0.25);border-radius:24px;padding:36px 28px;max-width:340px;width:100%;text-align:center">
    <div style="font-size:44px;margin-bottom:12px">📲</div>
    <h2 style="font-size:20px;font-weight:900;color:white;margin-bottom:8px">אימות מספר טלפון</h2>
    <p id="otp-desc" style="color:rgba(255,255,255,0.55);font-size:14px;margin-bottom:24px">שלחנו קוד בן 4 ספרות ל-WhatsApp שלך</p>
    <input id="otp-input"
      type="text" inputmode="numeric" autocomplete="one-time-code"
      maxlength="4" pattern="\\d{{4}}"
      placeholder="• • • •"
      style="width:100%;text-align:center;font-size:36px;font-weight:900;letter-spacing:16px;
             background:rgba(255,255,255,0.07);border:2px solid rgba(14,230,208,0.3);
             border-radius:16px;padding:18px 12px;color:#22d3ee;outline:none;
             font-family:monospace;margin-bottom:18px"
      oninput="if(this.value.length===4) verifyOtp()"
    />
    <button onclick="verifyOtp()" id="otp-confirm-btn"
      style="width:100%;padding:14px;border-radius:50px;border:none;cursor:pointer;
             background:linear-gradient(135deg,#0284c7,#22d3ee);color:white;
             font-weight:800;font-size:15px;font-family:inherit;margin-bottom:10px">
      אמת ושלח הזמנה ✓
    </button>
    <p id="otp-error" style="color:#f87171;font-size:13px;min-height:20px;margin-bottom:8px"></p>
    <button id="otp-sms-btn" onclick="resendViaSms()"
      style="width:100%;padding:10px;border-radius:12px;border:1px solid rgba(255,255,255,0.15);
             background:transparent;color:rgba(255,255,255,0.5);font-size:13px;cursor:pointer;
             font-family:inherit;margin-bottom:6px">
      📱 אין לי WhatsApp — שלח SMS במקום
    </button>
    <button onclick="document.getElementById('otp-overlay').style.display='none'"
      style="width:100%;padding:8px;border:none;background:transparent;color:rgba(255,255,255,0.3);
             font-size:12px;cursor:pointer;font-family:inherit">
      ← ביטול
    </button>
  </div>
</div>

<!-- Order Confirmation Overlay -->
<div id="confirm-overlay" style="position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:1000;display:none;align-items:center;justify-content:center;padding:20px">
  <div style="background:linear-gradient(135deg,#0f1723,#1a2744);border:1px solid rgba(34,211,238,0.2);border-radius:24px;padding:36px 28px;max-width:360px;width:100%;text-align:center">
    <div style="font-size:54px;margin-bottom:12px">&#x2705;</div>
    <h2 style="font-size:22px;font-weight:900;color:white;margin-bottom:8px">ההזמנה נשלחה!</h2>
    <p style="color:rgba(255,255,255,0.55);font-size:14px;margin-bottom:22px">ההזמנה שלך הועברה. מספר מעקב:</p>
    <div style="background:rgba(34,211,238,0.1);border:1px solid rgba(34,211,238,0.3);border-radius:14px;padding:16px;margin-bottom:18px">
      <div style="font-size:28px;font-weight:900;color:#22d3ee;letter-spacing:3px" id="confirm-code">—</div>
      <div style="color:rgba(255,255,255,0.4);font-size:11px;margin-top:4px">שמרו מספר זה למעקב</div>
    </div>
    <a id="confirm-track-link" href="#" target="_blank" style="display:none;align-items:center;justify-content:center;gap:8px;background:linear-gradient(135deg,#0284c7,#22d3ee);border-radius:50px;padding:13px 28px;color:white;font-weight:800;font-size:14px;margin-bottom:14px">&#x1f4e6; עקוב אחר ההזמנה</a>
    <button onclick="document.getElementById('confirm-overlay').style.display='none'" style="width:100%;padding:12px;border-radius:50px;background:rgba(255,255,255,0.07);border:none;color:rgba(255,255,255,0.6);font-size:14px;cursor:pointer;font-family:inherit">סגור</button>
  </div>
</div>
<script>
document.getElementById('confirm-overlay').addEventListener('click', function(e){{
  if(e.target===this) this.style.display='none';
}});
</script>

<script>
const MENU = {menu_json};
const BIZ_PHONE = "{phone}";
const BIZ_NAME = "{name}";
const TAZO_API = "https://api.tazo-web.com/api/v1";

let cart = {{}};
let orderType = "delivery";

function setOrderType(btn, type) {{
  document.querySelectorAll(".order-type-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  orderType = type;
  const da = document.getElementById("delivery-address-group");
  if (da) da.style.display = type === "delivery" ? "block" : "none";
}}

function renderMenu() {{
  const tabsEl = document.getElementById("cat-tabs");
  const sectionsEl = document.getElementById("menu-sections");
  tabsEl.innerHTML = "";
  sectionsEl.innerHTML = "";
  MENU.forEach((section, si) => {{
    const tab = document.createElement("button");
    tab.className = "cat-tab" + (si === 0 ? " active" : "");
    tab.textContent = section.cat;
    tab.onclick = () => {{
      document.querySelectorAll(".cat-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById("ms-" + si)?.scrollIntoView({{behavior:"smooth",block:"start"}});
    }};
    tabsEl.appendChild(tab);

    const sec = document.createElement("div");
    sec.className = "menu-section";
    sec.id = "ms-" + si;
    sec.innerHTML = '<div class="menu-section-title">' + section.cat + '</div>';
    const grid = document.createElement("div");
    grid.className = "item-grid";
    section.items.forEach((item, ii) => {{
      const id = si + "-" + ii;
      const card = document.createElement("div");
      card.className = "item-card";
      const imgHtml = item.image_url
        ? `<img class="item-img" src="${{item.image_url}}" alt="${{item.name}}" loading="lazy" onerror="this.style.display='none'">`
        : (ii === 0 && si === 0 ? `<div class="item-img-placeholder">🍽️</div>` : "");
      card.innerHTML = `
        ${{imgHtml}}
        <div class="item-body">
          <div class="item-name">${{item.name}}</div>
          ${{item.desc ? `<div class="item-desc">${{item.desc}}</div>` : ""}}
          <div class="item-footer">
            <div class="item-price">₪${{item.price || "—"}}</div>
            <div class="qty-ctrl">
              <button class="qty-btn" onclick="changeQty('${{id}}',${{si}},${{ii}},-1)">−</button>
              <span class="qty-num" id="qty-${{id}}">0</span>
              <button class="qty-btn" onclick="changeQty('${{id}}',${{si}},${{ii}},1)">+</button>
            </div>
          </div>
        </div>
      `;
      grid.appendChild(card);
    }});
    sec.appendChild(grid);
    sectionsEl.appendChild(sec);
  }});
}}

function changeQty(id, si, ii, delta) {{
  const item = MENU[si].items[ii];
  const key = item.name;
  const prev = (cart[key]?.qty || 0) + delta;
  if (prev <= 0) {{
    delete cart[key];
  }} else {{
    cart[key] = {{name: item.name, price: item.price, qty: prev}};
  }}
  document.getElementById("qty-" + id).textContent = Math.max(0, prev);
  updateCartBadge();
}}

function updateCartBadge() {{
  const total = Object.values(cart).reduce((s,i) => s + i.qty, 0);
  document.getElementById("cart-count").textContent = total;
}}

function toggleCart() {{
  const d = document.getElementById("cart-drawer");
  const o = document.getElementById("cart-overlay");
  const open = d.classList.toggle("open");
  o.classList.toggle("open", open);
  if (open) renderCartItems();
}}

function renderCartItems() {{
  const el = document.getElementById("cart-items-list");
  const items = Object.values(cart);
  if (!items.length) {{
    el.innerHTML = '<div class="empty-cart"><div>🛒</div><div>הסל ריק</div></div>';
    document.getElementById("cart-total-price").textContent = "₪0";
    return;
  }}
  let html = "", total = 0;
  items.forEach(i => {{
    const sub = i.price * i.qty;
    total += sub;
    html += `<div class="cart-item"><div class="cart-item-info"><div class="cart-item-name">${{i.name}} x${{i.qty}}</div><div class="cart-item-price">₪${{sub}}</div></div><button onclick="removeItem('${{i.name}}')" style="background:rgba(255,100,100,.15);color:#f87171;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:14px">✕</button></div>`;
  }});
  el.innerHTML = html;
  document.getElementById("cart-total-price").textContent = "₪" + total;
}}

function removeItem(name) {{
  delete cart[name];
  updateCartBadge();
  renderCartItems();
}}

function openCheckout() {{
  if (!Object.keys(cart).length) return;
  document.getElementById("cart-drawer").classList.remove("open");
  document.getElementById("cart-overlay").classList.remove("open");
  document.getElementById("checkout-overlay").classList.add("open");
}}

// ── OTP Flow ──────────────────────────────────────────────────────────────
let _otpPhone = "";
let _otpChannel = ""; // "whatsapp" or "sms"

async function startOtpFlow() {{
  const name = document.getElementById("c-name").value.trim();
  const phone = document.getElementById("c-phone").value.trim();
  if (!name || !phone) {{ alert("נא למלא שם וטלפון"); return; }}
  const items = Object.values(cart);
  if (!items.length) {{ alert("הסל ריק"); return; }}

  _otpPhone = phone.replace(/\D/g,"");
  if (_otpPhone.startsWith("0") && _otpPhone.length === 10)
    _otpPhone = "972" + _otpPhone.slice(1);

  // Show OTP overlay immediately
  document.getElementById("otp-input").value = "";
  document.getElementById("otp-error").textContent = "";
  document.getElementById("otp-desc").textContent = "שולח קוד...";
  document.getElementById("otp-overlay").style.display = "flex";
  document.getElementById("otp-sms-btn").style.display = "";

  await _sendOtp("whatsapp");
}}

async function _sendOtp(channel) {{
  _otpChannel = channel;
  const btn = document.getElementById("otp-sms-btn");
  const desc = document.getElementById("otp-desc");
  const errEl = document.getElementById("otp-error");
  errEl.textContent = "";
  document.getElementById("otp-input").value = "";
  document.getElementById("otp-input").focus();

  if (channel === "sms") {{
    btn.style.display = "none";
    desc.textContent = "שלחנו קוד ב-SMS — הקוד ימולא אוטומטית";
  }} else {{
    desc.textContent = "שלחנו קוד ב-WhatsApp — מלא אותו כאן";
    btn.style.display = "";
  }}

  try {{
    const resp = await fetch(TAZO_API + "/public/sms-otp/send", {{
      method: "POST",
      headers: {{"Content-Type":"application/json"}},
      body: JSON.stringify({{ phone: _otpPhone, lang: "he" }})
    }});
    if (!resp.ok) {{
      errEl.textContent = "שגיאה בשליחת הקוד. נסה שנית.";
      return;
    }}
    // Android Web OTP API — auto-fill when SMS arrives
    if (channel === "sms" && "OTPCredential" in window) {{
      try {{
        const credential = await navigator.credentials.get({{ otp: {{ transport: ["sms"] }}, signal: AbortSignal.timeout(60000) }});
        if (credential && credential.code) {{
          document.getElementById("otp-input").value = credential.code;
          await verifyOtp();
        }}
      }} catch(_) {{ /* user dismissed or timed out — manual entry still works */ }}
    }}
  }} catch(e) {{
    errEl.textContent = "שגיאת רשת — נסה שנית.";
  }}
}}

async function resendViaSms() {{
  document.getElementById("otp-desc").textContent = "שולח SMS...";
  await _sendOtp("sms");
}}

async function verifyOtp() {{
  const code = document.getElementById("otp-input").value.trim();
  const errEl = document.getElementById("otp-error");
  if (code.length !== 4) {{ errEl.textContent = "הכנס 4 ספרות"; return; }}
  errEl.textContent = "";
  const btn = document.getElementById("otp-confirm-btn");
  btn.disabled = true; btn.textContent = "מאמת...";

  try {{
    const resp = await fetch(TAZO_API + "/public/sms-otp/verify", {{
      method: "POST",
      headers: {{"Content-Type":"application/json"}},
      body: JSON.stringify({{ phone: _otpPhone, code }})
    }});
    const data = await resp.json();
    if (!resp.ok || !data.ok) {{
      errEl.textContent = data.detail || "קוד שגוי. נסה שנית.";
      btn.disabled = false; btn.textContent = "אמת ושלח הזמנה ✓";
      return;
    }}
    // ✅ Phone verified — close OTP overlay, send order
    document.getElementById("otp-overlay").style.display = "none";
    await sendOrder();
  }} catch(e) {{
    errEl.textContent = "שגיאת רשת.";
    btn.disabled = false; btn.textContent = "אמת ושלח הזמנה ✓";
  }}
}}

async function sendOrder() {{
  const name = document.getElementById("c-name").value.trim();
  const phone = document.getElementById("c-phone").value.trim();
  const address = document.getElementById("c-address")?.value.trim() || "";
  const notes = document.getElementById("c-notes").value.trim();
  const items = Object.values(cart);
  const total = items.reduce((s,i) => s + i.price*i.qty, 0);

  // Close checkout, clear cart
  document.getElementById("checkout-overlay").classList.remove("open");
  cart = {{}};
  updateCartBadge();

  // Send to TAZO-SYNC and show tracking code
  try {{
    const resp = await fetch(TAZO_API + "/public/site-order", {{
      method: "POST",
      headers: {{"Content-Type":"application/json"}},
      body: JSON.stringify({{
        business_name: BIZ_NAME, customer_name: name, customer_phone: phone,
        items: items, total: total, order_type: orderType,
        notes: notes, business_phone: BIZ_PHONE
      }})
    }});
    const data = await resp.json();
    if (data.deliveryCode) {{
      document.getElementById("confirm-code").textContent = data.deliveryCode;
      if (data.trackingUrl) {{
        const link = document.getElementById("confirm-track-link");
        link.href = data.trackingUrl; link.style.display = "inline-flex";
      }}
      document.getElementById("confirm-overlay").style.display = "flex";
    }}
  }} catch(e) {{}}
}}

renderMenu();
</script>
  <!-- FAQ -->
  <section style="padding:52px 20px 64px;max-width:680px;margin:0 auto">
    <div style="text-align:center;margin-bottom:32px">
      <div style="display:inline-block;background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.3);border-radius:50px;padding:4px 14px;font-size:12px;color:#ef4444;margin-bottom:12px;font-weight:700">&#10067; &#1513;&#1488;&#1500;&#1493;&#1514; &#1504;&#1508;&#1493;&#1510;&#1493;&#1514;</div>
      <h2 style="font-size:clamp(20px,4vw,30px);font-weight:900;margin:0;color:white">&#1499;&#1500; &#1502;&#1492; &#1513;&#1512;&#1510;&#1497;&#1514; &#1500;&#1491;&#1506;&#1514;</h2>
    </div>
    <div id="food-faq"></div>
    <script>
    (function(){{
      var qq=[
        ["&#1488;&#1497;&#1498; &#1502;&#1489;&#1510;&#1506;&#1497;&#1501; &#1492;&#1494;&#1502;&#1504;&#1492;?","&#1489;&#1495;&#1512;&#1493; &#1508;&#1512;&#1497;&#1496;&#1497;&#1501; &#1502;&#1492;&#1514;&#1508;&#1512;&#1497;&#1496; &#x2192; &#1492;&#1493;&#1505;&#1497;&#1508;&#1493; &#1500;&#1505;&#1500; &#x2192; &#1500;&#1495;&#1509; &#39;&#1500;&#1505;&#1497;&#1493;&#1501;&#39;. &#1502;&#1500;&#1488;&#1493; &#1513;&#1501;+&#1496;&#1500;&#1508;&#1493;&#1503; &#1493;&#1513;&#1500;&#1495;&#1493; &#x2014; &#1492;&#1494;&#1502;&#1504;&#1492; &#1502;&#1490;&#1497;&#1506;&#1492; &#1489;-WhatsApp &#1502;&#1497;&#1497;&#1491;."],
        ["&#1502;&#1513;&#1500;&#1493;&#1495;, &#1488;&#1497;&#1505;&#1493;&#1507; &#1506;&#1510;&#1502;&#1497; &#1488;&#1493; &#1497;&#1513;&#1497;&#1489;&#1492;?","&#1489;&#1496;&#1493;&#1508;&#1505; &#1492;&#1492;&#1494;&#1502;&#1504;&#1492; &#1504;&#1497;&#1514;&#1503; &#1500;&#1489;&#1495;&#1493;&#1512;: &#x1F697; &#1502;&#1513;&#1500;&#1493;&#1495; &#1500;&#1489;&#1497;&#1514; | &#x1F3C3; &#1488;&#1497;&#1505;&#1493;&#1507; &#1506;&#1510;&#1502;&#1497; | &#x1FA91; &#1497;&#1513;&#1497;&#1489;&#1492;. &#1494;&#1502;&#1503; &#1502;&#1513;&#1500;&#1493;&#1495;: 40-60 &#1491;&#1511;&#1493;&#1514;."],
        ["&#1489;&#1488;&#1497;&#1494;&#1492; &#1488;&#1502;&#1510;&#1506;&#1497; &#1514;&#1513;&#1500;&#1493;&#1501; &#1504;&#1497;&#1514;&#1503; &#1500;&#1513;&#1500;&#1501;?","&#x1F4B5; &#1502;&#1494;&#1493;&#1502;&#1503; | &#x1F4F1; Bit | &#x1F4F1; PayBox | &#x1F4B3; &#1499;&#1512;&#1496;&#1497;&#1505; &#1488;&#1513;&#1512;&#1488;&#1497;."],
        ["&#1497;&#1513; &#1506;&#1500;&#1493;&#1514; &#1502;&#1513;&#1500;&#1493;&#1495;?","&#1506;&#1500;&#1493;&#1514; &#1492;&#1502;&#1513;&#1500;&#1493;&#1495; &#1514;&#1493;&#1508;&#1497;&#1506; &#1489;&#1492;&#1493;&#1491;&#1506;&#1514; &#1492;&#1488;&#1497;&#1513;&#1493;&#1512;. &#1489;&#1491;&#1512;&#1498; &#1499;&#1500;&#1500; 10-20 &#x20AA;. &#1502;&#1506;&#1500; 150 &#x20AA; &#x2014; &#1502;&#1513;&#1500;&#1493;&#1495; &#1495;&#1497;&#1504;&#1501;!"],
        ["&#1512;&#1493;&#1510;&#1492; &#1500;&#1489;&#1496;&#1500; &#1488;&#1493; &#1500;&#1513;&#1504;&#1493;&#1514; &#1492;&#1494;&#1502;&#1504;&#1492;?","&#1513;&#1500;&#1495;&#1493; WhatsApp &#1506;&#1501; &#1502;&#1505;&#1508;&#1512; &#1492;&#1492;&#1494;&#1502;&#1504;&#1492;. &#1504;&#1497;&#1514;&#1503; &#1500;&#1489;&#1496;&#1500; &#1506;&#1491; 10 &#1491;&#1511;&#1493;&#1514; &#1500;&#1488;&#1495;&#1512; &#1489;&#1497;&#1510;&#1493;&#1506;."],
        ["&#1499;&#1502;&#1492; &#1494;&#1502;&#1503; &#1502;&#1513;&#1500;&#1493;&#1495;?","&#1489;&#1491;&#1512;&#1498; &#1499;&#1500;&#1500; 40-60 &#1491;&#1511;&#1493;&#1514;. &#1489;&#1513;&#1506;&#1493;&#1514; &#1506;&#1493;&#1502;&#1505; &#1492;&#1494;&#1502;&#1503; &#1506;&#1500;&#1493;&#1500; &#1500;&#1492;&#1497;&#1493;&#1514; &#1488;&#1512;&#1493;&#1498;."],
        ["&#1488;&#1504;&#1497; &#1489;&#1506;&#1500; &#1492;&#1506;&#1505;&#1511; &#x2014; &#1488;&#1497;&#1498; &#1502;&#1504;&#1492;&#1500;?","&#1492;&#1497;&#1499;&#1504;&#1505;&#1493; &#1500;-tazo-sync.com &#x2192; &#1492;&#1497;&#1512;&#1513;&#1502;&#1493; &#1506;&#1501; &#1502;&#1505;&#1508;&#1512; &#1492;&#1496;&#1500;&#1508;&#1493;&#1503; &#1513;&#1500; &#1492;&#1506;&#1505;&#1511; &#x2192; &#1504;&#1492;&#1500;&#1493; &#1514;&#1508;&#1512;&#1497;&#1496;, &#1513;&#1506;&#1493;&#1514; &#1508;&#1506;&#1497;&#1500;&#1493;&#1514; &#1493;&#1492;&#1494;&#1502;&#1504;&#1493;&#1514; &#1489;&#1494;&#1502;&#1503; &#1488;&#1502;&#1514;."],
      ];
      var el=document.getElementById('food-faq');
      qq.forEach(function(it,i){{
        var d=document.createElement('div');
        d.style.cssText='border:1px solid rgba(255,255,255,0.08);border-radius:13px;margin-bottom:9px;overflow:hidden;';
        var ans='<div id="fqa'+i+'" style="display:none;padding:0 18px 16px;color:rgba(255,255,255,0.6);font-size:13px;line-height:1.8">'+it[1]+'</div>';
        var btn='<button onclick="var a=document.getElementById(\'fqa'+i+'\'),ar=this.querySelector(\'.farr\');if(!a)return;var op=a.style.display!==\'none\';a.style.display=op?\'none\':'block\';ar.style.transform=op?\'rotate(0)\':'rotate(180deg)\'" style="width:100%;text-align:right;padding:16px 18px;display:flex;justify-content:space-between;align-items:center;gap:10px;background:none;border:none;color:white;font-weight:700;font-size:14px;cursor:pointer;font-family:inherit"><span>'+it[0]+'</span><span class="farr" style="flex-shrink:0;width:20px;height:20px;border-radius:50%;background:rgba(255,255,255,0.07);display:flex;align-items:center;justify-content:center;font-size:10px;transition:transform .3s">&#9660;</span></button>';
        d.innerHTML=btn+ans;
        el.appendChild(d);
      }});
    }})();
    </script>
  </section>
</body></html>"""



_BEAUTY_RE = _re.compile(r'hair_care|beauty_salon|spa|nail|massage|aesthetic|cosmetic|barber|salon|ספר|שיער|יופי|נייל|עיצוב|סלון|מספרה|פדיקור|מניקור', _re.I)

def _is_beauty(category: str, types: str) -> bool:
    return bool(_BEAUTY_RE.search(f"{category or ''} {types or ''}"))

def _beauty_services(category: str, types: str) -> list:
    txt = f"{category or ''} {types or ''}".lower()
    if re.search(r'hair|barber|salon|שיער|ספר|מספרה', txt):
        return [
            {'name': 'תספורת גברים', 'desc': 'כולל שטיפה וסטיילינג', 'price': '60–80'},
            {'name': 'תספורת נשים', 'desc': 'כולל שטיפה וייבוש', 'price': '120–180'},
            {'name': 'צביעת שיער', 'desc': 'בלייאז׳ / אומברה / צביעה מלאה', 'price': '200–400'},
            {'name': 'החלקה קרטין', 'desc': 'החלקה ארוכת טווח', 'price': '350–600'},
            {'name': 'פן + סטיילינג', 'desc': 'לאירועים ומצגות', 'price': '150–250'},
            {'name': 'תספורת ילדים', 'desc': 'עד גיל 12', 'price': '40–60'},
        ]
    elif re.search(r'nail|ציפור|נייל|מניקור|פדיקור', txt):
        return [
            {'name': 'מניקור קלאסי', 'desc': 'עיצוב ולכה', 'price': '80'},
            {'name': 'מניקור ג\'ל', 'desc': 'לכה ג\'ל עמידה', 'price': '120'},
            {'name': 'פדיקור קלאסי', 'desc': 'טיפוח מלא + לכה', 'price': '120'},
            {'name': 'תוספות ציפורניים', 'desc': 'ג\'ל / אקריל', 'price': '200–350'},
            {'name': 'עיצוב + אמנות', 'desc': 'דגמים מותאמים אישית', 'price': 'לפי בקשה'},
        ]
    else:
        return [
            {'name': 'עיסוי רקמות עמוקות', 'desc': '60 דקות', 'price': '250'},
            {'name': 'טיפול פנים', 'desc': 'ניקוי + לחות', 'price': '200'},
            {'name': 'עיצוב גבות', 'desc': 'ניקוי + עיצוב', 'price': '60'},
            {'name': 'הסרת שיער', 'desc': 'שעווה / IPL', 'price': 'לפי בקשה'},
            {'name': 'מסכת פנים', 'desc': 'הזנה ולחות', 'price': '150'},
        ]

def _render_beauty(c: dict) -> str:
    from html import escape as _e
    import re as _r
    name_raw = (c.get('site_title') or c.get('hero_title') or 'סלון יופי')
    name_raw = _r.sub(r'\s*Draft Site$', '', name_raw)
    name     = _e(name_raw)
    phone    = _e(c.get('phone') or '')
    phone_c  = _r.sub(r'\D', '', phone)
    city     = _e(c.get('city') or '')
    tagline  = _e(c.get('tagline') or 'מגע אישי. תוצאות מרהיבות.')
    about    = _e(c.get('about_text') or 'ברוכים הבאים לסלון שלנו! אנו מספקים שירותי יופי מקצועיים ברמה הגבוהה ביותר.')
    rating   = c.get('rating')
    reviews  = c.get('reviews_count') or 0
    maps_url = _e(c.get('maps_url') or '')
    is_demo  = c.get('is_demo', True)
    category = c.get('category') or ''
    types    = c.get('business_types') or ''
    services = _beauty_services(category, types)
    wa_phone = phone_c or '972546363350'
    wa_msg   = f'שלום! אשמח לקבוע תור ב{name_raw}'
    wa_url   = f'https://wa.me/{wa_phone}?text={wa_msg.replace(" ", "%20")}'
    demo_banner = _build_site_banner(is_demo, c.get('phase', 'beta'))
    stars_str = ('★' * int(rating) + '☆' * (5 - int(rating))) if rating else ''
    svcs_html = ''.join(
        f'<div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);'
        f'border-radius:16px;padding:20px 24px;display:flex;justify-content:space-between;align-items:center">'
        f'<div><div style="font-weight:700;font-size:15px;color:white">{_e(s["name"])}</div>'
        f'<div style="color:rgba(255,255,255,0.5);font-size:13px;margin-top:4px">{_e(s["desc"])}</div></div>'
        f'<div style="font-size:17px;font-weight:800;color:#f9a8d4;white-space:nowrap">&#x20aa;{_e(s["price"])}</div>'
        f'</div>'
        for s in services
    )
    return f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{name}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800;900&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Heebo,sans-serif;background:#0a0a0f;color:white;direction:rtl}}
a{{text-decoration:none;color:inherit}}
.book-btn{{background:linear-gradient(135deg,#9333ea,#ec4899);border:none;border-radius:50px;padding:16px 36px;color:white;font-weight:800;font-size:16px;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:10px;box-shadow:0 8px 32px rgba(147,51,234,0.4)}}
</style>
</head>
<body>
{demo_banner}
<section style="min-height:95vh;background:linear-gradient(135deg,#0a0a0f 0%,#1a0527 50%,#2d0b3e 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:80px 24px;position:relative;overflow:hidden">
  <div style="position:absolute;top:-80px;right:-80px;width:380px;height:380px;background:radial-gradient(circle,rgba(147,51,234,0.18),transparent);border-radius:50%"></div>
  <div style="position:absolute;bottom:-80px;left:-80px;width:420px;height:420px;background:radial-gradient(circle,rgba(236,72,153,0.13),transparent);border-radius:50%"></div>
  <div style="position:relative;max-width:700px">
    <div style="font-size:64px;margin-bottom:16px">💅</div>
    <h1 style="font-size:clamp(36px,6vw,68px);font-weight:900;line-height:1.1;margin-bottom:14px;background:linear-gradient(135deg,#fff,#f9a8d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{name}</h1>
    <p style="font-size:19px;color:rgba(255,255,255,0.6);margin-bottom:10px">{tagline}</p>
    {f'<p style="color:rgba(255,255,255,0.35);margin-bottom:28px;font-size:14px">&#128205; {city}</p>' if city else '<div style="margin-bottom:28px"></div>'}
    {f'<div style="color:#f9a8d4;letter-spacing:3px;font-size:20px;margin-bottom:28px">{stars_str} <span style="color:rgba(255,255,255,0.6);font-size:13px">{rating} ({reviews} ביקורות)</span></div>' if rating else ''}
    <div style="display:flex;flex-wrap:wrap;gap:14px;justify-content:center">
      <a href="{wa_url}" target="_blank" class="book-btn">&#x1f4ac; קביעת תור ב-WhatsApp</a>
      {f'<a href="tel:{phone_c}" style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);border-radius:50px;padding:16px 28px;color:white;font-weight:700;font-size:15px;display:inline-flex;align-items:center;gap:8px">&#128222; {phone}</a>' if phone else ''}
    </div>
  </div>
</section>
<section style="padding:72px 24px;max-width:720px;margin:0 auto">
  <h2 style="font-size:30px;font-weight:900;text-align:center;margin-bottom:10px">השירותים שלנו</h2>
  
  <div style="display:flex;flex-direction:column;gap:12px">{svcs_html}</div>
  <div style="text-align:center;margin-top:40px"><a href="{wa_url}" target="_blank" class="book-btn">&#x2728; קביעת תור עכשיו</a></div>
</section>
<section style="padding:56px 24px;background:rgba(255,255,255,0.02);border-top:1px solid rgba(255,255,255,0.06);border-bottom:1px solid rgba(255,255,255,0.06)">
  <div style="max-width:680px;margin:0 auto;text-align:center">
    <h2 style="font-size:24px;font-weight:800;margin-bottom:18px">&#x2728; אודותינו</h2>
    <p style="color:rgba(255,255,255,0.6);font-size:15px;line-height:1.9">{about}</p>
  </div>
</section>
<section style="padding:72px 24px;text-align:center;background:linear-gradient(135deg,#1a0527,#2d0b3e)">
  <h2 style="font-size:26px;font-weight:900;margin-bottom:10px">מוכנים? &#x1f485;</h2>
  <p style="color:rgba(255,255,255,0.45);margin-bottom:28px;font-size:14px">שלחו הודעה ונחזור אליכם מיד</p>
  <a href="{wa_url}" target="_blank" class="book-btn" style="font-size:17px;padding:18px 44px">&#x1f4ac; שלחו הודעה עכשיו</a>
</section>
{f'<section style="padding:40px 24px;text-align:center"><a href="{maps_url}" target="_blank" style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:50px;padding:12px 28px;color:rgba(255,255,255,0.7);font-size:14px">&#128205; הצג במפות גוגל</a></section>' if maps_url else ''}
<footer style="background:#050508;color:rgba(255,255,255,0.3);text-align:center;padding:24px 20px;font-size:12px;border-top:1px solid rgba(255,255,255,0.05)">
  <div style="color:rgba(255,255,255,0.5);font-size:13px;font-weight:700;margin-bottom:4px">{name}</div>
  {f'<div style="margin-bottom:2px">&#128205; {city}</div>' if city else ''}
  {f'<div><a href="tel:{phone_c}" style="color:rgba(255,255,255,0.35)">{phone}</a></div>' if phone else ''}
  <div style="margin-top:10px">&#169; 2026 <a href="https://tazo-web.com" style="color:#9333ea;font-weight:700">TAZO</a> | כל הזכויות שמורות | אריאל אביב עוסק מורשה</div>
  {'<div style="margin-top:4px;font-size:10px;color:rgba(255,255,255,0.2)"></div>' if is_demo else ''}
</footer>
</body></html>"""

# ──────────────────────────────────────────────────────────────────────────────
# PREMIUM CATEGORY TEMPLATES
# ──────────────────────────────────────────────────────────────────────────────

import re as _re_cat

_HEALTH_RE  = _re_cat.compile(r'פיזיותרפ|יוגה|פילאטיס|כושר|ספורט|רפואה|רופא|שיניים|אופטיק|קליניק|gym|fitness|health|yoga|pilates|physio|clinic|dentist|optic', _re_cat.I)
_VEHICLE_RE = _re_cat.compile(r'מוסך|מכונא|צמיג|רכב|גרר|שטיפת רכב|ביטוח רכב|חלקי חילוף|garage|auto|mechanic|tire|car repair|car wash', _re_cat.I)
_REPAIR_RE  = _re_cat.compile(r'חשמלאי|שרברב|מזגן|שיפוץ|נגר|צביעה|ריצוף|גבס|אחזקה|plumber|electrician|hvac|renovation|carpenter|contractor', _re_cat.I)
_EVENTS_RE  = _re_cat.compile(r'אירוע|חתונה|קייטרינג|צלם|דיג\'יי|הופעה|אולם|event|wedding|catering|photographer|dj|venue|ceremony', _re_cat.I)
_EDUCATION_RE = _re_cat.compile(r'גן ילד|חינוך|בית ספר|לימוד|קורס|אנגלית|מורה|שיעור|kindergarten|school|education|tutor|lessons|course', _re_cat.I)

def _is_health(cat, types):  return bool(_HEALTH_RE.search(f"{cat} {types}"))
def _is_vehicle(cat, types): return bool(_VEHICLE_RE.search(f"{cat} {types}"))
def _is_repair(cat, types):  return bool(_REPAIR_RE.search(f"{cat} {types}"))
def _is_events(cat, types):  return bool(_EVENTS_RE.search(f"{cat} {types}"))
def _is_education(cat, types): return bool(_EDUCATION_RE.search(f"{cat} {types}"))


# ── Health / Fitness / Clinic ──────────────────────────────────────────────────
def _health_services(cat, types):
    txt = f"{cat} {types}".lower()
    if _re_cat.search(r'שיניים|dentist', txt):
        return [
            {'name':'בדיקת שיניים שגרתית','desc':'בדיקה מקיפה + ייעוץ','price':'150'},
            {'name':'לבנת שיניים','desc':'מערכת מקצועית','price':'800–1,200'},
            {'name':'טיפול שורש','desc':'שמירה על השן','price':'800–1,500'},
            {'name':'קראון פורצלן','desc':'כתר אחרי טיפול','price':'1,500–2,500'},
            {'name':'יישור שקוף','desc':'Invisalign / אורתו','price':'לפי הצעה'},
        ]
    if _re_cat.search(r'פיזיותרפ|physio', txt):
        return [
            {'name':'הערכה ראשונית','desc':'בדיקה ותוכנית טיפול','price':'300'},
            {'name':'טיפול פיזיותרפי','desc':'60 דקות, כולל עיסוי','price':'250'},
            {'name':'טיפול בכאב גב','desc':'טכניקות מתקדמות','price':'280'},
            {'name':'שיקום ספורטאים','desc':'חזרה מהירה לפעילות','price':'300'},
            {'name':'מניעת פציעות','desc':'ייעוץ ותרגילים','price':'200'},
        ]
    if _re_cat.search(r'כושר|gym|fitness', txt):
        return [
            {'name':'מנוי חודשי','desc':'גישה מלאה לציוד','price':'200'},
            {'name':'אימון אישי — מפגש','desc':'עם מאמן מוסמך','price':'250'},
            {'name':'חבילת 10 אימונים','desc':'חיסכון משמעותי','price':'2,000'},
            {'name':'יוגה / פילאטיס','desc':'כיתה שבועית','price':'80'},
            {'name':'תוכנית תזונה','desc':'מותאמת אישית','price':'400'},
        ]
    return [
        {'name':'ייעוץ ראשוני','desc':'בדיקה ואבחון','price':'200–300'},
        {'name':'טיפול פרטני','desc':'60 דקות','price':'250'},
        {'name':'חבילת טיפולים','desc':'5 מפגשים','price':'1,000'},
        {'name':'מעקב ובקרה','desc':'ביקור חוזר','price':'150'},
    ]

def _render_health(c: dict) -> str:
    from html import escape as _e
    import re as _r
    name_raw = _r.sub(r'\s*Draft Site$', '', c.get('site_title') or c.get('hero_title') or 'קליניקה')
    name  = _e(name_raw)
    phone = _e(c.get('phone') or '')
    phone_c = _r.sub(r'\D', '', phone)
    city  = _e(c.get('city') or '')
    tagline = _e(c.get('tagline') or 'בריאות ואיכות חיים — בידיים מקצועיות')
    about = _e(c.get('about_text') or 'מרפאה / קליניקה עם ניסיון של שנים. הגישה שלנו: מקצועית, אישית ויעילה.')
    rating = c.get('rating')
    reviews = c.get('reviews_count') or 0
    maps_url = _e(c.get('maps_url') or '')
    is_demo = c.get('is_demo', True)
    cat = c.get('category') or ''
    types = c.get('business_types') or ''
    svcs = _health_services(cat, types)
    wa_phone = phone_c or '972546363350'
    wa_url = f"https://wa.me/{wa_phone}?text={'קביעת%20תור%20ב'+name_raw.replace(' ','%20')}"
    demo_banner = _build_site_banner(is_demo, c.get('phase', 'beta'))
    stars_str = ('★'*int(rating)+'☆'*(5-int(rating))) if rating else ''
    svcs_html = ''.join(
        f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(16,185,129,0.15);border-radius:14px;padding:18px 22px;display:flex;justify-content:space-between;align-items:center">'
        f'<div><div style="font-weight:700;font-size:15px;color:white">{_e(s["name"])}</div>'
        f'<div style="color:rgba(255,255,255,0.45);font-size:13px;margin-top:3px">{_e(s["desc"])}</div></div>'
        f'<div style="font-size:17px;font-weight:800;color:#34d399;white-space:nowrap">&#x20aa;{_e(s["price"])}</div></div>'
        for s in svcs
    )
    return f"""<!doctype html><html lang="he" dir="rtl"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{name}</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;800;900&display=swap" rel="stylesheet">
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:Heebo,sans-serif;background:#030f0d;color:white;direction:rtl}}a{{text-decoration:none;color:inherit}}.appt-btn{{background:linear-gradient(135deg,#0f766e,#059669);border:none;border-radius:50px;padding:15px 34px;color:white;font-weight:800;font-size:15px;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:9px;box-shadow:0 8px 28px rgba(5,150,105,0.45)}}</style>
</head><body>
{demo_banner}
<section style="min-height:90vh;background:linear-gradient(135deg,#030f0d,#042f2e 50%,#064e3b 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:80px 24px;position:relative;overflow:hidden">
  <div style="position:absolute;top:-100px;right:-100px;width:400px;height:400px;background:radial-gradient(circle,rgba(5,150,105,0.15),transparent);border-radius:50%"></div>
  <div style="position:relative;max-width:680px">
    <div style="display:inline-block;background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.3);border-radius:50px;padding:6px 18px;font-size:12px;font-weight:700;color:#34d399;margin-bottom:20px;letter-spacing:1px">&#x1f3e5; שירות מקצועי ברמה הגבוהה ביותר</div>
    <h1 style="font-size:clamp(34px,6vw,62px);font-weight:900;line-height:1.1;margin-bottom:14px;background:linear-gradient(135deg,#fff,#6ee7b7);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{name}</h1>
    <p style="font-size:18px;color:rgba(255,255,255,0.55);margin-bottom:10px">{tagline}</p>
    {f'<p style="color:rgba(255,255,255,0.3);font-size:14px;margin-bottom:24px">&#128205; {city}</p>' if city else '<div style="margin-bottom:24px"></div>'}
    {f'<div style="color:#34d399;font-size:20px;letter-spacing:2px;margin-bottom:28px">{stars_str} <span style="color:rgba(255,255,255,0.5);font-size:13px">{rating} ({reviews} ביקורות)</span></div>' if rating else ''}
    <div style="display:flex;flex-wrap:wrap;gap:14px;justify-content:center">
      <a href="{wa_url}" target="_blank" class="appt-btn">&#x1f4ac; קביעת תור עכשיו</a>
      {f'<a href="tel:{phone_c}" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:50px;padding:15px 28px;color:white;font-weight:700;font-size:14px;display:inline-flex;align-items:center;gap:8px">&#128222; {phone}</a>' if phone else ''}
    </div>
  </div>
</section>
<section style="padding:72px 24px;max-width:700px;margin:0 auto">
  <h2 style="font-size:28px;font-weight:900;text-align:center;margin-bottom:10px">השירותים שלנו</h2>
  
  <div style="display:flex;flex-direction:column;gap:10px">{svcs_html}</div>
  <div style="text-align:center;margin-top:40px"><a href="{wa_url}" target="_blank" class="appt-btn">&#x1f4cb; קביעת תור</a></div>
</section>
<section style="padding:56px 24px;background:rgba(16,185,129,0.04);border-top:1px solid rgba(16,185,129,0.1)">
  <div style="max-width:660px;margin:0 auto;text-align:center">
    <h2 style="font-size:24px;font-weight:800;margin-bottom:16px">&#x2764; אודותינו</h2>
    <p style="color:rgba(255,255,255,0.55);font-size:15px;line-height:1.9">{about}</p>
  </div>
</section>
<section style="padding:64px 24px;text-align:center">
  <div style="max-width:520px;margin:0 auto">
    <h2 style="font-size:26px;font-weight:900;margin-bottom:10px">נשמח לעזור &#x1f91d;</h2>
    <p style="color:rgba(255,255,255,0.4);margin-bottom:26px;font-size:14px">שלחו הודעה ונחזור מיד</p>
    <a href="{wa_url}" target="_blank" class="appt-btn" style="font-size:16px;padding:17px 44px">&#x1f4ac; שלחו הודעה ב-WhatsApp</a>
    {f'<div style="margin-top:16px"><a href="{maps_url}" target="_blank" style="color:rgba(255,255,255,0.35);font-size:13px">&#128205; הצג במפות גוגל</a></div>' if maps_url else ''}
  </div>
</section>
<footer style="background:#020a08;color:rgba(255,255,255,0.25);text-align:center;padding:22px;font-size:12px;border-top:1px solid rgba(16,185,129,0.08)">
  <span style="color:rgba(255,255,255,0.45);font-weight:700">{name}</span>{'  |  '+city if city else ''}
  <div style="margin-top:8px">&#169; 2026 <a href="https://tazo-web.com" style="color:#059669;font-weight:700">TAZO</a> | כל הזכויות שמורות</div>
</footer>
</body></html>"""


# ── Vehicles / Garage / Mechanic ──────────────────────────────────────────────
def _vehicle_services(cat, types):
    txt = f"{cat} {types}".lower()
    if _re_cat.search(r'צמיג|tire|wheel', txt):
        return [
            {'name':'החלפת צמיגים','desc':'לכל סוגי הרכבים','price':'60/צמיג'},
            {'name':'מיזוג גלגלים','desc':'איזון מקצועי','price':'80'},
            {'name':'בדיקת לחץ + תיקון','desc':'שרות מהיר','price':'30–80'},
            {'name':'אחסון עונתי','desc':'חורף/קיץ','price':'200/עונה'},
            {'name':'ייעוץ רכישה','desc':'ידע מקצועי','price':'חינם'},
        ]
    if _re_cat.search(r'שטיפה|car wash', txt):
        return [
            {'name':'שטיפה חיצונית','desc':'מים בלחץ + ניקוי בסיסי','price':'30'},
            {'name':'שטיפה פנימית+חיצונית','desc':'ניקוי מלא','price':'60–80'},
            {'name':'פוליש + ציפוי','desc':'הגנה מפני קרינה','price':'150–250'},
            {'name':'ניקוי עמוק','desc':'שמפו שטיחים + ריפוד','price':'200'},
            {'name':'ציפוי ננו','desc':'הגנה ארוכת טווח','price':'400'},
        ]
    return [
        {'name':'בדיקת רכב שנתית','desc':'טסט + רשיון ישיר','price':'200'},
        {'name':'החלפת שמן','desc':'סינטטי/חצי סינטטי','price':'150–250'},
        {'name':'בלמים — בדיקה ותיקון','desc':'בטיחות מקסימלית','price':'200–500'},
        {'name':'מערכת קירור','desc':'תחזוקה ותיקון','price':'200–400'},
        {'name':'מיזוג אוויר ברכב','desc':'טעינת גז + תיקון','price':'150–350'},
        {'name':'חשמל ואלקטרוניקה','desc':'אבחון ממוחשב','price':'100+'},
    ]

def _render_vehicles(c: dict) -> str:
    from html import escape as _e
    import re as _r
    name_raw = _r.sub(r'\s*Draft Site$', '', c.get('site_title') or c.get('hero_title') or 'מוסך')
    name  = _e(name_raw)
    phone = _e(c.get('phone') or '')
    phone_c = _r.sub(r'\D', '', phone)
    city  = _e(c.get('city') or '')
    tagline = _e(c.get('tagline') or 'שירות מהיר. עבודה ישרה. מחיר הוגן.')
    about = _e(c.get('about_text') or 'מוסך מקצועי עם שנות ניסיון. כל הרכבים, כל התקלות. אנחנו לצדכם על הדרך.')
    rating = c.get('rating')
    reviews = c.get('reviews_count') or 0
    maps_url = _e(c.get('maps_url') or '')
    is_demo = c.get('is_demo', True)
    cat = c.get('category') or ''
    types = c.get('business_types') or ''
    svcs = _vehicle_services(cat, types)
    wa_phone = phone_c or '972546363350'
    wa_url = f"https://wa.me/{wa_phone}?text={'שלום%2C%20אשמח%20לקבל%20שירות%20ב'+name_raw.replace(' ','%20')}"
    demo_banner = _build_site_banner(is_demo, c.get('phase', 'beta'))
    stars_str = ('★'*int(rating)+'☆'*(5-int(rating))) if rating else ''
    svcs_html = ''.join(
        f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(217,119,6,0.2);border-radius:14px;padding:18px 22px;display:flex;justify-content:space-between;align-items:center">'
        f'<div><div style="font-weight:700;font-size:15px;color:white">{_e(s["name"])}</div>'
        f'<div style="color:rgba(255,255,255,0.4);font-size:13px;margin-top:3px">{_e(s["desc"])}</div></div>'
        f'<div style="font-size:16px;font-weight:800;color:#fbbf24;white-space:nowrap">&#x20aa;{_e(s["price"])}</div></div>'
        for s in svcs
    )
    return f"""<!doctype html><html lang="he" dir="rtl"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{name}</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;800;900&display=swap" rel="stylesheet">
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:Heebo,sans-serif;background:#0c0a00;color:white;direction:rtl}}a{{text-decoration:none;color:inherit}}.svc-btn{{background:linear-gradient(135deg,#b45309,#d97706);border:none;border-radius:50px;padding:15px 34px;color:white;font-weight:800;font-size:15px;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:9px;box-shadow:0 8px 28px rgba(180,83,9,0.5)}}</style>
</head><body>
{demo_banner}
<section style="background:linear-gradient(135deg,#0c0a00,#1c1200 40%,#292000 100%);padding:90px 24px 70px;text-align:center;position:relative;overflow:hidden">
  <div style="position:absolute;inset:0;background:url('data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2260%22 height=%2260%22><path d=%22M0 60L60 0%22 stroke=%22rgba(180,83,9,0.06)%22 stroke-width=%221%22/></svg>')"></div>
  <div style="position:relative;max-width:700px;margin:0 auto">
    <div style="display:inline-flex;align-items:center;gap:8px;background:rgba(217,119,6,0.12);border:1px solid rgba(217,119,6,0.25);border-radius:50px;padding:6px 16px;font-size:12px;font-weight:700;color:#fbbf24;margin-bottom:22px">&#x1f527; שירות מהיר ואמין</div>
    <h1 style="font-size:clamp(32px,6vw,60px);font-weight:900;line-height:1.1;margin-bottom:14px;background:linear-gradient(135deg,#fff,#fde68a);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{name}</h1>
    <p style="font-size:18px;color:rgba(255,255,255,0.5);margin-bottom:10px">{tagline}</p>
    {f'<p style="color:rgba(255,255,255,0.3);font-size:14px;margin-bottom:24px">&#128205; {city}</p>' if city else '<div style="margin-bottom:24px"></div>'}
    {f'<div style="color:#fbbf24;font-size:20px;margin-bottom:28px">{stars_str} <span style="color:rgba(255,255,255,0.45);font-size:13px">{rating} ({reviews} ביקורות)</span></div>' if rating else ''}
    <div style="display:flex;flex-wrap:wrap;gap:14px;justify-content:center">
      <a href="{wa_url}" target="_blank" class="svc-btn">&#x1f697; פנייה לשירות</a>
      {f'<a href="tel:{phone_c}" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:50px;padding:15px 28px;color:white;font-weight:700;font-size:14px;display:inline-flex;align-items:center;gap:8px">&#128222; {phone}</a>' if phone else ''}
    </div>
  </div>
</section>
<section style="padding:70px 24px;max-width:700px;margin:0 auto">
  <h2 style="font-size:28px;font-weight:900;text-align:center;margin-bottom:8px">השירותים שלנו</h2>
  
  <div style="display:flex;flex-direction:column;gap:10px">{svcs_html}</div>
  <div style="text-align:center;margin-top:38px"><a href="{wa_url}" target="_blank" class="svc-btn">&#x1f4ac; שלחו הודעה לקביעת תור</a></div>
</section>
<section style="padding:52px 24px;background:rgba(180,83,9,0.05);border-top:1px solid rgba(180,83,9,0.12);border-bottom:1px solid rgba(180,83,9,0.12)">
  <div style="max-width:660px;margin:0 auto;text-align:center">
    <h2 style="font-size:23px;font-weight:800;margin-bottom:16px">&#x1f6e0; אודות המוסך</h2>
    <p style="color:rgba(255,255,255,0.5);font-size:15px;line-height:1.9">{about}</p>
  </div>
</section>
<section style="padding:64px 24px;text-align:center">
  <h2 style="font-size:25px;font-weight:900;margin-bottom:10px">נשמח לטפל ברכבכם &#x1f91d;</h2>
  <p style="color:rgba(255,255,255,0.35);margin-bottom:26px;font-size:14px">שלחו הודעה ונחזור מיד</p>
  <a href="{wa_url}" target="_blank" class="svc-btn" style="font-size:16px;padding:17px 44px">&#x1f4ac; WhatsApp</a>
  {f'<div style="margin-top:14px"><a href="{maps_url}" target="_blank" style="color:rgba(255,255,255,0.3);font-size:13px">&#128205; הצג במפות גוגל</a></div>' if maps_url else ''}
</section>
<footer style="background:#080600;color:rgba(255,255,255,0.25);text-align:center;padding:22px;font-size:12px;border-top:1px solid rgba(180,83,9,0.1)">
  <span style="color:rgba(255,255,255,0.45);font-weight:700">{name}</span>{'  |  '+city if city else ''}
  <div style="margin-top:8px">&#169; 2026 <a href="https://tazo-web.com" style="color:#d97706;font-weight:700">TAZO</a> | כל הזכויות שמורות</div>
</footer>
</body></html>"""


# ── Repairs / Electrician / Plumber / Contractor ──────────────────────────────
def _repair_services(cat, types):
    txt = f"{cat} {types}".lower()
    if _re_cat.search(r'חשמלאי|electrician', txt):
        return [
            {'name':'תיקון תקלה חשמלית','desc':'אבחון + תיקון','price':'200–400'},
            {'name':'התקנת נקודות חשמל','desc':'לכל סוג חדר','price':'150/נקודה'},
            {'name':'התקנת גוף תאורה','desc':'LED, ספוטים, נברשות','price':'100–200'},
            {'name':'לוח חשמל — תיקון/שדרוג','desc':'על פי תקן','price':'500–1,500'},
            {'name':'הכנה לבדיקת חשמל','desc':'בדיקות בטיחות','price':'300'},
            {'name':'התקנת אינטרקום/קלוזד','desc':'גישה מאובטחת','price':'400+'},
        ]
    if _re_cat.search(r'שרברב|plumber|אינסטלצ', txt):
        return [
            {'name':'תיקון נזילה','desc':'איתור ותיקון מהיר','price':'200–400'},
            {'name':'פתיחת סתימה','desc':'כיור, אסלה, ביוב','price':'150–300'},
            {'name':'החלפת ברז/מקלחת','desc':'כולל חומרים','price':'200–400'},
            {'name':'התקנת מדחס/סוילר','desc':'חימום מים','price':'500–800'},
            {'name':'הכנה לשיפוץ','desc':'תשתיות חדשות','price':'לפי פרויקט'},
        ]
    if _re_cat.search(r'מזגן|hvac|air', txt):
        return [
            {'name':'התקנת מזגן','desc':'כולל חיבור + אטימה','price':'600–900'},
            {'name':'ניקוי + תחזוקה','desc':'עונתי, מומלץ שנתי','price':'150–250'},
            {'name':'תיקון מזגן','desc':'אבחון + חלקים','price':'200–500'},
            {'name':'טעינת גז','desc':'R410A / R32','price':'250–400'},
            {'name':'הסרת מזגן ישן','desc':'כולל פירוק','price':'200'},
        ]
    return [
        {'name':'שיפוץ חדר אמבטיה','desc':'מלא + חלקי','price':'לפי פרויקט'},
        {'name':'צביעה פנימית','desc':'סלון, חדרי שינה','price':'25/מ"ר'},
        {'name':'ריצוף + חיפוי','desc':'כל הסוגים','price':'50/מ"ר+'},
        {'name':'גבס ותקרות','desc':'גבסניות ותקרות מתוחות','price':'לפי פרויקט'},
        {'name':'נגרות ורהיטנות','desc':'ארונות מטבח + שירות','price':'לפי מידה'},
        {'name':'בדיקת נכס + הצעת מחיר','desc':'ייעוץ ראשוני','price':'חינם'},
    ]

def _render_repairs(c: dict) -> str:
    from html import escape as _e
    import re as _r
    name_raw = _r.sub(r'\s*Draft Site$', '', c.get('site_title') or c.get('hero_title') or 'שירות שיפוצים')
    name  = _e(name_raw)
    phone = _e(c.get('phone') or '')
    phone_c = _r.sub(r'\D', '', phone)
    city  = _e(c.get('city') or '')
    tagline = _e(c.get('tagline') or 'עבודה מקצועית. תוצאה מושלמת. מחיר הוגן.')
    about = _e(c.get('about_text') or 'בעל מקצוע מנוסה עם שנות ניסיון. אנחנו לוקחים אחריות מלאה על כל עבודה.')
    rating = c.get('rating')
    reviews = c.get('reviews_count') or 0
    maps_url = _e(c.get('maps_url') or '')
    is_demo = c.get('is_demo', True)
    cat = c.get('category') or ''
    types = c.get('business_types') or ''
    svcs = _repair_services(cat, types)
    wa_phone = phone_c or '972546363350'
    wa_url = f"https://wa.me/{wa_phone}?text={'שלום%2C%20אשמח%20לקבל%20הצעת%20מחיר%20מ'+name_raw.replace(' ','%20')}"
    demo_banner = _build_site_banner(is_demo, c.get('phase', 'beta'))
    stars_str = ('★'*int(rating)+'☆'*(5-int(rating))) if rating else ''
    svcs_html = ''.join(
        f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(30,64,175,0.25);border-radius:14px;padding:18px 22px;display:flex;justify-content:space-between;align-items:center">'
        f'<div><div style="font-weight:700;font-size:15px;color:white">{_e(s["name"])}</div>'
        f'<div style="color:rgba(255,255,255,0.4);font-size:13px;margin-top:3px">{_e(s["desc"])}</div></div>'
        f'<div style="font-size:16px;font-weight:800;color:#60a5fa;white-space:nowrap">&#x20aa;{_e(s["price"])}</div></div>'
        for s in svcs
    )
    return f"""<!doctype html><html lang="he" dir="rtl"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{name}</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;800;900&display=swap" rel="stylesheet">
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:Heebo,sans-serif;background:#020814;color:white;direction:rtl}}a{{text-decoration:none;color:inherit}}.rep-btn{{background:linear-gradient(135deg,#1d4ed8,#0ea5e9);border:none;border-radius:50px;padding:15px 34px;color:white;font-weight:800;font-size:15px;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:9px;box-shadow:0 8px 28px rgba(14,165,233,0.4)}}</style>
</head><body>
{demo_banner}
<section style="background:linear-gradient(135deg,#020814,#0c1445 50%,#1e3a8a 100%);padding:90px 24px 70px;text-align:center;position:relative;overflow:hidden">
  <div style="position:absolute;bottom:-60px;left:50%;transform:translateX(-50%);width:600px;height:300px;background:radial-gradient(ellipse,rgba(14,165,233,0.1),transparent);border-radius:50%"></div>
  <div style="position:relative;max-width:700px;margin:0 auto">
    <div style="display:inline-flex;align-items:center;gap:8px;background:rgba(14,165,233,0.1);border:1px solid rgba(14,165,233,0.25);border-radius:50px;padding:6px 16px;font-size:12px;font-weight:700;color:#38bdf8;margin-bottom:22px">&#x26a1; מקצועיות ומהירות בשירות אחד</div>
    <h1 style="font-size:clamp(32px,6vw,60px);font-weight:900;line-height:1.1;margin-bottom:14px;background:linear-gradient(135deg,#fff,#bae6fd);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{name}</h1>
    <p style="font-size:18px;color:rgba(255,255,255,0.5);margin-bottom:10px">{tagline}</p>
    {f'<p style="color:rgba(255,255,255,0.3);font-size:14px;margin-bottom:24px">&#128205; {city}</p>' if city else '<div style="margin-bottom:24px"></div>'}
    {f'<div style="color:#60a5fa;font-size:20px;margin-bottom:28px">{stars_str} <span style="color:rgba(255,255,255,0.45);font-size:13px">{rating} ({reviews} ביקורות)</span></div>' if rating else ''}
    <div style="display:flex;flex-wrap:wrap;gap:14px;justify-content:center">
      <a href="{wa_url}" target="_blank" class="rep-btn">&#x1f4ac; קבלת הצעת מחיר</a>
      {f'<a href="tel:{phone_c}" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:50px;padding:15px 28px;color:white;font-weight:700;font-size:14px;display:inline-flex;align-items:center;gap:8px">&#128222; {phone}</a>' if phone else ''}
    </div>
  </div>
</section>
<section style="padding:70px 24px;max-width:700px;margin:0 auto">
  <h2 style="font-size:28px;font-weight:900;text-align:center;margin-bottom:8px">השירותים שלנו</h2>
  
  <div style="display:flex;flex-direction:column;gap:10px">{svcs_html}</div>
  <div style="text-align:center;margin-top:38px"><a href="{wa_url}" target="_blank" class="rep-btn">&#x1f527; בקשת הצעת מחיר</a></div>
</section>
<section style="padding:52px 24px;background:rgba(30,58,138,0.08);border-top:1px solid rgba(30,58,138,0.2);border-bottom:1px solid rgba(30,58,138,0.2)">
  <div style="max-width:660px;margin:0 auto;text-align:center">
    <h2 style="font-size:23px;font-weight:800;margin-bottom:16px">&#x1f3e0; אודותינו</h2>
    <p style="color:rgba(255,255,255,0.5);font-size:15px;line-height:1.9">{about}</p>
  </div>
</section>
<section style="padding:64px 24px;text-align:center">
  <h2 style="font-size:25px;font-weight:900;margin-bottom:10px">מוכנים להתחיל? &#x1f91d;</h2>
  <p style="color:rgba(255,255,255,0.35);margin-bottom:26px;font-size:14px">שלחו הודעה ונחזור מיד לתיאום</p>
  <a href="{wa_url}" target="_blank" class="rep-btn" style="font-size:16px;padding:17px 44px">&#x1f4ac; WhatsApp</a>
  {f'<div style="margin-top:14px"><a href="{maps_url}" target="_blank" style="color:rgba(255,255,255,0.3);font-size:13px">&#128205; הצג במפות גוגל</a></div>' if maps_url else ''}
</section>
<footer style="background:#01050f;color:rgba(255,255,255,0.25);text-align:center;padding:22px;font-size:12px;border-top:1px solid rgba(30,58,138,0.15)">
  <span style="color:rgba(255,255,255,0.45);font-weight:700">{name}</span>{'  |  '+city if city else ''}
  <div style="margin-top:8px">&#169; 2026 <a href="https://tazo-web.com" style="color:#0ea5e9;font-weight:700">TAZO</a> | כל הזכויות שמורות</div>
</footer>
</body></html>"""


# ── Events / Catering / Photography ──────────────────────────────────────────
def _events_services(cat, types):
    txt = f"{cat} {types}".lower()
    if _re_cat.search(r'קייטרינג|catering', txt):
        return [
            {'name':'ארוחת עסקים','desc':'מגש אוכל לישיבות','price':'35/אורח'},
            {'name':'חתונה / בר מצווה','desc':'מנות מלאות + שרות','price':'לפי הצעה'},
            {'name':'מסיבות וימי הולדת','desc':'בופה + שרות','price':'לפי הצעה'},
            {'name':'מגשי פרי וחטיפים','desc':'מגוון גדול','price':'120+/מגש'},
            {'name':'כשרות מהדרין','desc':'עם תעודת כשרות','price':'לפי תפריט'},
        ]
    if _re_cat.search(r'צלם|photographer|photo', txt):
        return [
            {'name':'צילום חתונה','desc':'יום מלא + עריכה','price':'3,500–7,000'},
            {'name':'צילום בר/בת מצווה','desc':'אירוע מלא','price':'2,000–4,000'},
            {'name':'צילום תדמית','desc':'לעסקים ורשתות','price':'600–1,500'},
            {'name':'צילום רגעים (לידה, ...)','desc':'מיוחד ואינטימי','price':'1,200–2,500'},
            {'name':'עריכה בלבד','desc':'אולפן עריכה מקצועי','price':'100/שעה'},
        ]
    return [
        {'name':'שכירת אולם לאירוע','desc':'עד 200 אורחים','price':'לפי תאריך'},
        {'name':'חבילת חתונה מלאה','desc':'אוכל, שמע, תאורה','price':'לפי הצעה'},
        {'name':'אירוע חברה','desc':'ניהול אירוע מקצועי','price':'לפי הצעה'},
        {'name':'דיג\'יי + ציוד שמע','desc':'עד 500 אורחים','price':'2,000–4,000'},
        {'name':'עיצוב ופרחים','desc':'קישוט מקצועי','price':'לפי בקשה'},
    ]

def _render_events(c: dict) -> str:
    from html import escape as _e
    import re as _r
    name_raw = _r.sub(r'\s*Draft Site$', '', c.get('site_title') or c.get('hero_title') or 'שירותי אירועים')
    name  = _e(name_raw)
    phone = _e(c.get('phone') or '')
    phone_c = _r.sub(r'\D', '', phone)
    city  = _e(c.get('city') or '')
    tagline = _e(c.get('tagline') or 'כל אירוע — חוויה בלתי נשכחת')
    about = _e(c.get('about_text') or 'אנחנו מתמחים בהפקת אירועים ייחודיים עם תשומת לב לכל פרט. מרגש, מקצועי, בלתי נשכח.')
    rating = c.get('rating')
    reviews = c.get('reviews_count') or 0
    maps_url = _e(c.get('maps_url') or '')
    is_demo = c.get('is_demo', True)
    cat = c.get('category') or ''
    types = c.get('business_types') or ''
    svcs = _events_services(cat, types)
    wa_phone = phone_c or '972546363350'
    wa_url = f"https://wa.me/{wa_phone}?text={'שלום%2C%20אשמח%20לשמוע%20פרטים%20על%20'+name_raw.replace(' ','%20')}"
    demo_banner = _build_site_banner(is_demo, c.get('phase', 'beta'))
    stars_str = ('★'*int(rating)+'☆'*(5-int(rating))) if rating else ''
    svcs_html = ''.join(
        f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(167,139,250,0.2);border-radius:14px;padding:18px 22px;display:flex;justify-content:space-between;align-items:center">'
        f'<div><div style="font-weight:700;font-size:15px;color:white">{_e(s["name"])}</div>'
        f'<div style="color:rgba(255,255,255,0.4);font-size:13px;margin-top:3px">{_e(s["desc"])}</div></div>'
        f'<div style="font-size:16px;font-weight:800;color:#c4b5fd;white-space:nowrap">{_e(s["price"])}</div></div>'
        for s in svcs
    )
    return f"""<!doctype html><html lang="he" dir="rtl"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{name}</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;800;900&display=swap" rel="stylesheet">
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:Heebo,sans-serif;background:#07030f;color:white;direction:rtl}}a{{text-decoration:none;color:inherit}}.evt-btn{{background:linear-gradient(135deg,#7c3aed,#a855f7);border:none;border-radius:50px;padding:15px 34px;color:white;font-weight:800;font-size:15px;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:9px;box-shadow:0 8px 32px rgba(168,85,247,0.45)}}</style>
</head><body>
{demo_banner}
<section style="background:linear-gradient(135deg,#07030f,#1a0b2e 50%,#2d1254 100%);padding:100px 24px 80px;text-align:center;position:relative;overflow:hidden">
  <div style="position:absolute;top:-80px;right:-80px;width:500px;height:500px;background:radial-gradient(circle,rgba(168,85,247,0.12),transparent);border-radius:50%"></div>
  <div style="position:absolute;bottom:-80px;left:-60px;width:400px;height:400px;background:radial-gradient(circle,rgba(251,191,36,0.06),transparent);border-radius:50%"></div>
  <div style="position:relative;max-width:720px;margin:0 auto">
    <div style="font-size:64px;margin-bottom:18px">✨</div>
    <h1 style="font-size:clamp(34px,6vw,64px);font-weight:900;line-height:1.1;margin-bottom:14px;background:linear-gradient(135deg,#fff 30%,#c4b5fd 70%,#fbbf24);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{name}</h1>
    <p style="font-size:19px;color:rgba(255,255,255,0.5);margin-bottom:10px">{tagline}</p>
    {f'<p style="color:rgba(255,255,255,0.3);font-size:14px;margin-bottom:28px">&#128205; {city}</p>' if city else '<div style="margin-bottom:28px"></div>'}
    {f'<div style="color:#c4b5fd;font-size:20px;margin-bottom:32px">{stars_str} <span style="color:rgba(255,255,255,0.45);font-size:13px">{rating} ({reviews} ביקורות)</span></div>' if rating else ''}
    <div style="display:flex;flex-wrap:wrap;gap:14px;justify-content:center">
      <a href="{wa_url}" target="_blank" class="evt-btn">&#x1f4ac; יצירת קשר לתיאום</a>
      {f'<a href="tel:{phone_c}" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:50px;padding:15px 28px;color:white;font-weight:700;font-size:14px;display:inline-flex;align-items:center;gap:8px">&#128222; {phone}</a>' if phone else ''}
    </div>
  </div>
</section>
<section style="padding:70px 24px;max-width:700px;margin:0 auto">
  <h2 style="font-size:28px;font-weight:900;text-align:center;margin-bottom:8px">השירותים שלנו</h2>
  
  <div style="display:flex;flex-direction:column;gap:10px">{svcs_html}</div>
  <div style="text-align:center;margin-top:38px"><a href="{wa_url}" target="_blank" class="evt-btn">&#x1f4ac; שלחו פרטים לקבלת הצעה</a></div>
</section>
<section style="padding:52px 24px;background:rgba(124,58,237,0.05);border-top:1px solid rgba(124,58,237,0.15);border-bottom:1px solid rgba(124,58,237,0.15)">
  <div style="max-width:660px;margin:0 auto;text-align:center">
    <h2 style="font-size:23px;font-weight:800;margin-bottom:16px">&#x1f39e; אודותינו</h2>
    <p style="color:rgba(255,255,255,0.5);font-size:15px;line-height:1.9">{about}</p>
  </div>
</section>
<section style="padding:64px 24px;text-align:center;background:linear-gradient(135deg,#0f0520,#1a0b2e)">
  <h2 style="font-size:25px;font-weight:900;margin-bottom:10px">בואו נעשה את האירוע שלכם מושלם &#x1f48e;</h2>
  <p style="color:rgba(255,255,255,0.35);margin-bottom:26px;font-size:14px">שלחו הודעה ונחזור מיד</p>
  <a href="{wa_url}" target="_blank" class="evt-btn" style="font-size:16px;padding:17px 44px">&#x1f4ac; WhatsApp</a>
  {f'<div style="margin-top:14px"><a href="{maps_url}" target="_blank" style="color:rgba(255,255,255,0.3);font-size:13px">&#128205; הצג במפות גוגל</a></div>' if maps_url else ''}
</section>
<footer style="background:#050209;color:rgba(255,255,255,0.25);text-align:center;padding:22px;font-size:12px;border-top:1px solid rgba(124,58,237,0.12)">
  <span style="color:rgba(255,255,255,0.45);font-weight:700">{name}</span>{'  |  '+city if city else ''}
  <div style="margin-top:8px">&#169; 2026 <a href="https://tazo-web.com" style="color:#a855f7;font-weight:700">TAZO</a> | כל הזכויות שמורות</div>
</footer>
</body></html>"""


# ── Education / Childcare / Tutoring ─────────────────────────────────────────
def _education_services(cat, types):
    txt = f"{cat} {types}".lower()
    if _re_cat.search(r'גן ילד|kindergarten|daycare', txt):
        return [
            {'name':'גן יום מלא','desc':'7:00–16:00 כולל ארוחות','price':'לפי מקום'},
            {'name':'צהרון','desc':'עד 18:00, פעילויות','price':'לפי מקום'},
            {'name':'חוג בוקר','desc':'פעילות מועשרת','price':'250/חודש'},
            {'name':'קייטנת קיץ','desc':'יולי–אוגוסט','price':'לפי תוכנית'},
        ]
    if _re_cat.search(r'שיעור|tutor|teacher|מורה', txt):
        return [
            {'name':'שיעור פרטי — מתמטיקה','desc':'כל שכבות הגיל','price':'120–180/שעה'},
            {'name':'שיעור פרטי — אנגלית','desc':'יסודי עד בגרות','price':'120–160/שעה'},
            {'name':'שיעור פרטי — פיזיקה/כימיה','desc':'תיכון ובגרות','price':'140–200/שעה'},
            {'name':'חבילת 5 שיעורים','desc':'חיסכון 10%','price':'מ-550'},
            {'name':'שיעור קבוצתי','desc':'עד 4 תלמידים','price':'80/שעה/תלמיד'},
        ]
    return [
        {'name':'שיעורי הכנה לבגרות','desc':'כל המקצועות','price':'150/שעה'},
        {'name':'חוג מחשבים','desc':'קידוד ופיתוח','price':'200/חודש'},
        {'name':'לימוד שפות','desc':'אנגלית, ספרדית, ערבית','price':'120/שעה'},
        {'name':'שיעורי עברית','desc':'לעולים חדשים','price':'100/שעה'},
        {'name':'ייעוץ חינוכי','desc':'תכנון מסלול לימוד','price':'250/שעה'},
    ]

def _render_education(c: dict) -> str:
    from html import escape as _e
    import re as _r
    name_raw = _r.sub(r'\s*Draft Site$', '', c.get('site_title') or c.get('hero_title') or 'שירות חינוכי')
    name  = _e(name_raw)
    phone = _e(c.get('phone') or '')
    phone_c = _r.sub(r'\D', '', phone)
    city  = _e(c.get('city') or '')
    tagline = _e(c.get('tagline') or 'ידע הוא כוח — אנחנו כאן ללמד')
    about = _e(c.get('about_text') or 'מוסד חינוכי מוביל עם גישה חמה ומקצועית. כל ילד ותלמיד מקבל יחס אישי.')
    rating = c.get('rating')
    reviews = c.get('reviews_count') or 0
    maps_url = _e(c.get('maps_url') or '')
    is_demo = c.get('is_demo', True)
    cat = c.get('category') or ''
    types = c.get('business_types') or ''
    svcs = _education_services(cat, types)
    wa_phone = phone_c or '972546363350'
    wa_url = f"https://wa.me/{wa_phone}?text={'שלום%2C%20אשמח%20לשמוע%20פרטים%20על%20'+name_raw.replace(' ','%20')}"
    demo_banner = _build_site_banner(is_demo, c.get('phase', 'beta'))
    stars_str = ('★'*int(rating)+'☆'*(5-int(rating))) if rating else ''
    svcs_html = ''.join(
        f'<div style="background:linear-gradient(135deg,rgba(2,132,199,0.08),rgba(99,102,241,0.08));border:1px solid rgba(99,102,241,0.2);border-radius:16px;padding:18px 22px;display:flex;justify-content:space-between;align-items:center">'
        f'<div><div style="font-weight:700;font-size:15px;color:white">{_e(s["name"])}</div>'
        f'<div style="color:rgba(255,255,255,0.45);font-size:13px;margin-top:3px">{_e(s["desc"])}</div></div>'
        f'<div style="font-size:16px;font-weight:800;color:#a5b4fc;white-space:nowrap">&#x20aa;{_e(s["price"])}</div></div>'
        for s in svcs
    )
    return f"""<!doctype html><html lang="he" dir="rtl"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{name}</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;800;900&display=swap" rel="stylesheet">
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:Heebo,sans-serif;background:#020c18;color:white;direction:rtl}}a{{text-decoration:none;color:inherit}}.edu-btn{{background:linear-gradient(135deg,#0284c7,#6366f1);border:none;border-radius:50px;padding:15px 34px;color:white;font-weight:800;font-size:15px;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:9px;box-shadow:0 8px 28px rgba(99,102,241,0.45)}}</style>
</head><body>
{demo_banner}
<section style="background:linear-gradient(135deg,#020c18,#0a1f35 40%,#0e2d4e 100%);padding:90px 24px 70px;text-align:center;position:relative;overflow:hidden">
  <div style="position:absolute;top:-80px;left:50%;transform:translateX(-50%);width:600px;height:400px;background:radial-gradient(ellipse,rgba(99,102,241,0.1),transparent);border-radius:50%"></div>
  <div style="position:relative;max-width:700px;margin:0 auto">
    <div style="font-size:60px;margin-bottom:18px">&#x1f393;</div>
    <h1 style="font-size:clamp(32px,6vw,60px);font-weight:900;line-height:1.1;margin-bottom:14px;background:linear-gradient(135deg,#fff,#a5b4fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{name}</h1>
    <p style="font-size:18px;color:rgba(255,255,255,0.5);margin-bottom:10px">{tagline}</p>
    {f'<p style="color:rgba(255,255,255,0.3);font-size:14px;margin-bottom:24px">&#128205; {city}</p>' if city else '<div style="margin-bottom:24px"></div>'}
    {f'<div style="color:#a5b4fc;font-size:20px;margin-bottom:28px">{stars_str} <span style="color:rgba(255,255,255,0.45);font-size:13px">{rating} ({reviews} ביקורות)</span></div>' if rating else ''}
    <div style="display:flex;flex-wrap:wrap;gap:14px;justify-content:center">
      <a href="{wa_url}" target="_blank" class="edu-btn">&#x1f4ac; צרו קשר עכשיו</a>
      {f'<a href="tel:{phone_c}" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:50px;padding:15px 28px;color:white;font-weight:700;font-size:14px;display:inline-flex;align-items:center;gap:8px">&#128222; {phone}</a>' if phone else ''}
    </div>
  </div>
</section>
<section style="padding:70px 24px;max-width:700px;margin:0 auto">
  <h2 style="font-size:28px;font-weight:900;text-align:center;margin-bottom:8px">תוכניות ושירותים</h2>
  
  <div style="display:flex;flex-direction:column;gap:10px">{svcs_html}</div>
  <div style="text-align:center;margin-top:38px"><a href="{wa_url}" target="_blank" class="edu-btn">&#x1f4da; שלחו הודעה לפרטים</a></div>
</section>
<section style="padding:52px 24px;background:rgba(2,132,199,0.05);border-top:1px solid rgba(2,132,199,0.1);border-bottom:1px solid rgba(2,132,199,0.1)">
  <div style="max-width:660px;margin:0 auto;text-align:center">
    <h2 style="font-size:23px;font-weight:800;margin-bottom:16px">&#x1f31f; אודותינו</h2>
    <p style="color:rgba(255,255,255,0.5);font-size:15px;line-height:1.9">{about}</p>
  </div>
</section>
<section style="padding:64px 24px;text-align:center">
  <h2 style="font-size:25px;font-weight:900;margin-bottom:10px">נשמח לדבר &#x1f44b;</h2>
  <p style="color:rgba(255,255,255,0.35);margin-bottom:26px;font-size:14px">שלחו הודעה ונחזור מיד</p>
  <a href="{wa_url}" target="_blank" class="edu-btn" style="font-size:16px;padding:17px 44px">&#x1f4ac; WhatsApp</a>
  {f'<div style="margin-top:14px"><a href="{maps_url}" target="_blank" style="color:rgba(255,255,255,0.3);font-size:13px">&#128205; הצג במפות גוגל</a></div>' if maps_url else ''}
</section>
<footer style="background:#010c18;color:rgba(255,255,255,0.25);text-align:center;padding:22px;font-size:12px;border-top:1px solid rgba(2,132,199,0.1)">
  <span style="color:rgba(255,255,255,0.45);font-weight:700">{name}</span>{'  |  '+city if city else ''}
  <div style="margin-top:8px">&#169; 2026 <a href="https://tazo-web.com" style="color:#6366f1;font-weight:700">TAZO</a> | כל הזכויות שמורות</div>
</footer>
</body></html>"""


# ──────────────────────────────────────────────────────────────────────────────

class TemplateRenderService:
    def render(self, context: dict) -> str:
        c = context
        cat   = c.get('category') or ''
        types = c.get('business_types') or ''

        # Food/cafe template with full cart ordering
        if _is_food(cat, types):
            return _render_food(c)

        # Beauty / salon / nail / spa
        if _is_beauty(cat, types):
            return _premium_templates.render_beauty(c, _beauty_services(cat, types))

        # Health / fitness / clinic
        if _is_health(cat, types):
            return _premium_templates.render_health(c, _health_services(cat, types))

        # Vehicles / mechanic / tire / car wash
        if _is_vehicle(cat, types):
            return _premium_templates.render_vehicles(c, _vehicle_services(cat, types))

        # Repairs / electrician / plumber / contractor
        if _is_repair(cat, types):
            return _premium_templates.render_repairs(c, _repair_services(cat, types))

        # Events / catering / photography
        if _is_events(cat, types):
            return _premium_templates.render_events(c, _events_services(cat, types))

        # Education / childcare / tutoring
        if _is_education(cat, types):
            return _premium_templates.render_education(c, _education_services(cat, types))

        return _premium_templates.render_generic(c, c.get('services') or [])
