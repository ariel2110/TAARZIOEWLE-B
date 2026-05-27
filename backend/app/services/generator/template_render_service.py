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
                {"name": "מנה ראשונה", "desc": "מנה מיוחדת של השף", "price": 45},
                {"name": "מנה עיקרית", "desc": "עם תוספות ביתיות", "price": 68},
                {"name": "מנה ילדים", "desc": "מנה קטנה ומיוחדת", "price": 35},
            ]},
            {"cat": "🥤 שתיות", "items": [
                {"name": "שתייה קרה", "desc": "330 מ'ל", "price": 10},
                {"name": "מים", "desc": "500 מ'ל", "price": 6},
            ]},
        ]

def _render_food(c: dict) -> str:
    from html import escape as _e
    import re as _re

    name = _e(_re.sub(r"\s*Draft Site$", "", c.get("site_title") or c.get("hero_title") or "העסק"))
    phone = _re.sub(r"\D", "", c.get("phone") or "")
    wa_phone = c.get("wa_admin_phone") or "972546363350"
    category = c.get("category") or ""
    types = c.get("business_types") or ""
    city = _e(c.get("city") or "")
    about = _e(c.get("about_text") or "")
    tagline = _e(c.get("tagline") or "")
    is_demo = c.get("is_demo", True)

    menu = c.get("menu_items") or _food_menu(category, types)
    menu_json = __import__("json").dumps(menu, ensure_ascii=False)

    biz_phone_attr = f'data-biz-phone="{phone}"' if phone else ""
    demo_banner = (
        f'<div id="demo-banner" style="background:#f59e0b;color:#111;padding:10px 20px;text-align:center;font-size:13px;font-weight:700;direction:rtl">'
        f'⚠️ זהו אתר הדגמה בלבד | '
        f'<a href="https://wa.me/{wa_phone}?text=שלום%20אשמח%20לשמוע%20פרטים" target="_blank" style="color:#111;text-decoration:underline">לאתר האמיתי לחץ כאן</a>'
        f'</div>'
    ) if is_demo else ""

    return f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="robots" content="noindex,nofollow"/>
<title>{name}</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Heebo","Segoe UI",Arial,sans-serif;background:#111;color:#f5f5f5;direction:rtl;min-height:100vh}}
a{{text-decoration:none;color:inherit}}
button{{font-family:inherit;cursor:pointer;border:none}}
input,textarea{{font-family:inherit}}
/* HEADER */
.hdr{{position:sticky;top:0;z-index:200;background:rgba(17,17,17,.95);backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,.08);padding:12px 20px;display:flex;align-items:center;justify-content:space-between;gap:12px}}
.hdr-title{{font-size:18px;font-weight:800}}
.hdr-sub{{font-size:12px;color:rgba(255,255,255,.5)}}
.cart-btn{{background:linear-gradient(135deg,#dc2626,#f97316);border-radius:50px;padding:10px 18px;color:white;font-weight:700;font-size:14px;display:flex;align-items:center;gap:8px;position:relative}}
.cart-badge{{background:white;color:#dc2626;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:900;min-width:20px}}
/* HERO */
.hero{{background:linear-gradient(135deg,#7f1d1d,#dc2626,#f97316);padding:36px 20px;text-align:center}}
.hero h1{{font-size:clamp(26px,5vw,42px);font-weight:900;margin-bottom:8px}}
.hero p{{color:rgba(255,255,255,.8);font-size:15px;margin-bottom:20px}}
.order-type{{display:flex;gap:0;border-radius:10px;overflow:hidden;border:2px solid rgba(255,255,255,.3);display:inline-flex}}
.order-type-btn{{padding:10px 24px;font-size:14px;font-weight:700;cursor:pointer;transition:all .2s;font-family:inherit;color:white;background:transparent}}
.order-type-btn.active{{background:white;color:#dc2626}}
/* MENU */
.menu-wrap{{max-width:900px;margin:0 auto;padding:20px}}
.cat-tabs{{display:flex;gap:8px;overflow-x:auto;padding-bottom:12px;margin-bottom:20px;scrollbar-width:none}}
.cat-tabs::-webkit-scrollbar{{display:none}}
.cat-tab{{white-space:nowrap;padding:8px 18px;border-radius:50px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);color:rgba(255,255,255,.6);font-size:14px;font-weight:600;cursor:pointer;transition:all .2s;font-family:inherit}}
.cat-tab.active{{background:linear-gradient(135deg,#dc2626,#f97316);color:white;border-color:transparent}}
.menu-section{{margin-bottom:32px}}
.menu-section-title{{font-size:17px;font-weight:800;margin-bottom:14px;color:rgba(255,255,255,.8);padding:0 4px}}
.item-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}}
.item-card{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:16px;display:flex;flex-direction:column;gap:8px;transition:all .2s}}
.item-card:hover{{background:rgba(255,255,255,.09);border-color:rgba(255,255,255,.16)}}
.item-name{{font-size:15px;font-weight:700}}
.item-desc{{font-size:13px;color:rgba(255,255,255,.5);line-height:1.5}}
.item-footer{{display:flex;align-items:center;justify-content:space-between;margin-top:4px}}
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
{demo_banner}

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
  <h1>{name}</h1>
  {f'<p>{tagline}</p>' if tagline else ('<p>הזמנה מהירה לדלת שלך 🚀</p>' if not tagline else '')}
  <div class="order-type">
    <button class="order-type-btn active" onclick="setOrderType(this,'delivery')">🛵 משלוח</button>
    <button class="order-type-btn" onclick="setOrderType(this,'pickup')">🏃 איסוף עצמי</button>
  </div>
</section>

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
    <button class="wa-order-btn" onclick="sendOrder()">
      💬 שלח הזמנה ב-WhatsApp
    </button>
    <button onclick="document.getElementById('checkout-overlay').classList.remove('open')" style="width:100%;padding:12px;border-radius:12px;background:rgba(255,255,255,.06);color:white;font-size:14px;margin-top:10px;cursor:pointer;font-family:inherit">
      ← חזרה לתפריט
    </button>
  </div>
</div>

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
      card.innerHTML = `
        <div class="item-name">${{item.name}}</div>
        <div class="item-desc">${{item.desc || ""}}</div>
        <div class="item-footer">
          <div class="item-price">₪${{item.price}}</div>
          <div class="qty-ctrl">
            <button class="qty-btn" onclick="changeQty('${{id}}',${{si}},${{ii}},-1)">−</button>
            <span class="qty-num" id="qty-${{id}}">0</span>
            <button class="qty-btn" onclick="changeQty('${{id}}',${{si}},${{ii}},1)">+</button>
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

function sendOrder() {{
  const name = document.getElementById("c-name").value.trim();
  const phone = document.getElementById("c-phone").value.trim();
  const address = document.getElementById("c-address")?.value.trim() || "";
  const notes = document.getElementById("c-notes").value.trim();
  if (!name || !phone) {{ alert("נא למלא שם וטלפון"); return; }}
  const items = Object.values(cart);
  if (!items.length) {{ alert("הסל ריק"); return; }}
  const total = items.reduce((s,i) => s + i.price*i.qty, 0);
  let msg = `הזמנה חדשה מ-${{BIZ_NAME}}!\n\n`;
  msg += `לקוח: ${{name}}\nטלפון: ${{phone}}\n`;
  if (orderType === "delivery" && address) msg += `כתובת: ${{address}}\n`;
  else msg += `סוג: איסוף עצמי\n`;
  msg += `\nפרטי ההזמנה:\n`;
  items.forEach(i => {{ msg += `• ${{i.name}} x${{i.qty}} = ₪${{i.price*i.qty}}\n`; }});
  msg += `\nסה"כ: ₪${{total}}`;
  if (notes) msg += `\n\nהערות: ${{notes}}`;
  const target = BIZ_PHONE || "972546363350";
  const encoded = encodeURIComponent(msg);
  window.open(`https://wa.me/${{target}}?text=${{encoded}}`, "_blank");
  // Async tracking — best-effort
  try {{
    fetch(TAZO_API + "/public/site-order", {{
      method: "POST",
      headers: {{"Content-Type":"application/json"}},
      body: JSON.stringify({{
        business_name: BIZ_NAME, customer_name: name, customer_phone: phone,
        items: items, total: total, order_type: orderType,
        notes: notes, business_phone: BIZ_PHONE
      }})
    }}).catch(() => {{}});
  }} catch(e) {{}}
  document.getElementById("checkout-overlay").classList.remove("open");
  cart = {{}};
  updateCartBadge();
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
    demo_banner = (
        f'<div style="background:linear-gradient(90deg,#9333ea,#ec4899);color:white;padding:10px 20px;'
        f'text-align:center;font-size:13px;font-weight:700">'
        f'<a href="https://tazo-web.com" style="color:white">TAZO</a> '
        f'— אתר הדגמה | '
        f'<a href="{wa_url}" target="_blank" style="color:white;text-decoration:underline">לאישור ועריכה — לחץ כאן</a>'
        f'</div>'
    ) if is_demo else ''
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
  <p style="text-align:center;color:rgba(255,255,255,0.4);margin-bottom:44px;font-size:14px">מחירים לדוגמה — בואו להתאמה אישית</p>
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
  {'<div style="margin-top:4px;font-size:10px;color:rgba(255,255,255,0.2)">אתר הדגמה בלבד</div>' if is_demo else ''}
</footer>
</body></html>"""

class TemplateRenderService:
    def render(self, context: dict) -> str:
        c = context
        # Food/cafe template with cart ordering
        if _is_food(c.get('category', ''), c.get('business_types', '')):
            return _render_food(c)

        if _is_beauty(c.get('category') or '', c.get('business_types') or ''):
            return _render_beauty(c)

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
        wa_msg_encoded = wa_msg.replace(' ', '%20').replace('\n', '%0A')
        wa_url = f"https://wa.me/{wa_phone}?text={wa_msg_encoded}"

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
  {'<div style="margin-top:12px;font-size:11px;color:rgba(255,255,255,0.3)">אתר הדגמה — <a href="https://tazo-web.com" style="color:rgba(255,255,255,0.4)">TAZO</a> | &copy; 2026 אריאל אביב עוסק מורשה</div>' if is_demo else ''}
</footer>

  <!-- FAQ Section -->
  <section style="background:#0f0f0f;padding:52px 20px 64px">
  <div style="max-width:680px;margin:0 auto">
    <div style="text-align:center;margin-bottom:32px">
      <div style="display:inline-block;background:rgba(147,51,234,0.12);border:1px solid rgba(147,51,234,0.3);border-radius:50px;padding:4px 14px;font-size:12px;color:#a855f7;margin-bottom:12px;font-weight:700">&#10067; &#1513;&#1488;&#1500;&#1493;&#1514; &#1504;&#1508;&#1493;&#1510;&#1493;&#1514;</div>
      <h2 style="font-size:clamp(20px,4vw,30px);font-weight:900;margin:0;color:white">&#1499;&#1500; &#1502;&#1492; &#1513;&#1512;&#1510;&#1497;&#1514; &#1500;&#1491;&#1506;&#1514;</h2>
    </div>
    <div id="beauty-faq"></div>
    <script>
    (function(){{
      var items=[
        ["איך קובעים תור?","לחצו על כפתור קביעת תור → נפתח WhatsApp עם הודעה מוכנת → שלחו → נחזור לאישור תוך כמה דקות."],
        ["מה שעות הפעילות?","ימים א-ה: 09:00-20:00 | שישי: 08:00-15:00 | שבת: סגור. לשעות עדכניות — שלחו WhatsApp."],
        ["האם צריך לשלם מראש?","לא. אין תשלום מקדמה לרוב השירותים."],
        ["איך מבטלים או משנים תור?","שלחו WhatsApp לפחות 24 שעות לפני התור."],
        ["אפשר לבוא ללא תיאום?","מומלץ לשאול קודם ב-WhatsApp."],
        ["אפשר לבקש סטייליסט ספציפי?","בהחלט! בקביעת תור ציינו שם מועדף."],
        ["אני בעל העסק — איך מנהל?","היכנסו ל-tazo-sync.com &#x2192; הירשמו עם מספר הטלפון של העסק &#x2192; ערכו שירותים, מחירים ושעות פעילות."],
      ];
      var el=document.getElementById('beauty-faq');
      items.forEach(function(it,i){{
        var d=document.createElement('div');
        d.style.cssText='border:1px solid rgba(255,255,255,0.08);border-radius:13px;margin-bottom:9px;overflow:hidden;';
        var id='bqa'+i;
        var btn=document.createElement('button');
        btn.style.cssText='width:100%;text-align:right;padding:16px 18px;display:flex;justify-content:space-between;align-items:center;gap:10px;background:none;border:none;color:white;font-weight:700;font-size:14px;cursor:pointer;font-family:inherit';
        btn.innerHTML='<span>'+it[0]+'</span><span style="flex-shrink:0;width:20px;height:20px;border-radius:50%;background:rgba(255,255,255,0.07);display:flex;align-items:center;justify-content:center;font-size:10px;transition:transform .3s">&#9660;</span>';
        var ans=document.createElement('div');
        ans.id=id; ans.style.cssText='display:none;padding:0 18px 16px;color:rgba(255,255,255,0.6);font-size:13px;line-height:1.8';
        ans.innerHTML=it[1];
        btn.onclick=(function(d2,id2){{ return function(){{
          var a=document.getElementById(id2);
          var op=a.style.display!=='none';
          a.style.display=op?'none':'block';
          d2.style.borderColor=op?'rgba(255,255,255,0.08)':'rgba(147,51,234,0.4)';
        }}; }})(d,id);
        d.appendChild(btn); d.appendChild(ans);
        el.appendChild(d);
      }});
    }})();
    </script>
  </div>
  </section>
</body>
</html>'''
