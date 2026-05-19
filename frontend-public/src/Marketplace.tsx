import { useState, useEffect, useCallback } from 'react';
import VersionBar from './VersionBar';

const API = import.meta.env.VITE_API_BASE_URL || 'https://tazo-web.com/api/v1';

type View = 'mall' | 'category' | 'building';

interface Category {
  id: string;
  name: string;
  emoji: string;
  gradient: string;
  description: string;
}

interface Business {
  id: number;
  name: string;
  city?: string;
  phone?: string;
  rating?: number;
  tagline?: string;
  status: 'active' | 'building' | 'pending';
  subdomain?: string;
  photo_url?: string;
}

const CATEGORIES: Category[] = [
  { id: 'food',      name: 'מסעדות ואוכל',    emoji: '🍕', gradient: 'linear-gradient(135deg,#7f1d1d,#dc2626,#f97316)', description: 'פיצה, גריל, שוורמה, פלאפל ועוד' },
  { id: 'cafe',      name: 'קפה ומאפיות',      emoji: '☕', gradient: 'linear-gradient(135deg,#451a03,#92400e,#d97706)', description: 'קפה, מאפים, קינוחים ועוד' },
  { id: 'beauty',    name: 'יופי ואסתטיקה',    emoji: '✂️', gradient: 'linear-gradient(135deg,#4a1d96,#7c3aed,#ec4899)', description: 'מספרות, ספא, ציפורניים ועוד' },
  { id: 'health',    name: 'בריאות וכושר',     emoji: '💪', gradient: 'linear-gradient(135deg,#042f2e,#0f766e,#34d399)', description: 'פיזיותרפיה, יוגה, פילאטיס ועוד' },
  { id: 'repairs',   name: 'שיפוצים ואחזקה',   emoji: '🔧', gradient: 'linear-gradient(135deg,#1c0a00,#92400e,#f59e0b)', description: 'צביעה, ריצוף, גבס ועוד' },
  { id: 'electric',  name: 'חשמל ואינסטלציה',  emoji: '⚡', gradient: 'linear-gradient(135deg,#1e3a5f,#1d4ed8,#38bdf8)', description: 'חשמלאי, שרברב, מזגנים ועוד' },
  { id: 'vehicles',  name: 'רכב ומוסכים',      emoji: '🚗', gradient: 'linear-gradient(135deg,#111827,#374151,#9ca3af)', description: 'תיקון רכב, צמיגים, מיזוג ועוד' },
  { id: 'garden',    name: 'גינון ונוף',        emoji: '🌿', gradient: 'linear-gradient(135deg,#052e16,#166534,#4ade80)', description: 'גינון, עיצוב גינה, נוף ועוד' },
  { id: 'cleaning',  name: 'ניקיון ובית',       emoji: '🏠', gradient: 'linear-gradient(135deg,#082f49,#0369a1,#38bdf8)', description: 'ניקיון, כביסה, שטיחים ועוד' },
  { id: 'pets',      name: 'בעלי חיים',         emoji: '🐾', gradient: 'linear-gradient(135deg,#431407,#c2410c,#fb923c)', description: 'וטרינר, אילוף, חיות מחמד ועוד' },
  { id: 'education', name: 'חינוך ולימוד',      emoji: '🎓', gradient: 'linear-gradient(135deg,#1e1b4b,#4338ca,#818cf8)', description: 'שיעורים פרטיים, קורסים, גן ילדים' },
  { id: 'events',    name: 'אירועים ובידור',    emoji: '🎉', gradient: 'linear-gradient(135deg,#4c0519,#be185d,#fb7185)', description: 'אולמות, צלמים, קייטרינג ועוד' },
];

const BUILD_STEPS = [
  { icon: '🔍', text: 'מחפשים מידע על העסק ברשת...' },
  { icon: '🤖', text: 'AI בונה את האתר בהתאמה אישית...' },
  { icon: '🎨', text: 'מעצב את הנראות ואת התוכן...' },
  { icon: '📱', text: 'שולח את הקישור לבעל העסק ב-WhatsApp...' },
  { icon: '✅', text: 'האתר יהיה מוכן תוך דקות!' },
];

// ── Star Rating ─────────────────────────────────────────────────────────────
function StarRating({ rating }: { rating: number }) {
  return (
    <span style={{ color: '#f59e0b', fontSize: 14 }}>
      {'★'.repeat(Math.floor(rating))}{'☆'.repeat(5 - Math.floor(rating))}
      <span style={{ color: '#9ca3af', marginRight: 4, fontSize: 12 }}>{rating.toFixed(1)}</span>
    </span>
  );
}

// ── Category Card ────────────────────────────────────────────────────────────
function CategoryCard({ cat, onClick }: { cat: Category; onClick: () => void }) {
  const [hov, setHov] = useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        background: hov ? cat.gradient : 'rgba(255,255,255,0.05)',
        border: `1px solid ${hov ? 'transparent' : 'rgba(255,255,255,0.08)'}`,
        borderRadius: 20,
        padding: 'clamp(16px,3vw,28px) clamp(14px,3vw,24px)',
        cursor: 'pointer',
        textAlign: 'right' as const,
        fontFamily: 'inherit',
        transition: 'all 0.25s ease',
        transform: hov ? 'translateY(-4px)' : 'none',
        boxShadow: hov ? '0 20px 40px rgba(0,0,0,0.4)' : 'none',
        color: 'white',
      }}
    >
      <div style={{ fontSize: 44, marginBottom: 12 }}>{cat.emoji}</div>
      <div style={{ fontWeight: 800, fontSize: 18, marginBottom: 6 }}>{cat.name}</div>
      <div style={{ fontSize: 13, color: hov ? 'rgba(255,255,255,0.75)' : 'rgba(255,255,255,0.4)', lineHeight: 1.5 }}>{cat.description}</div>
    </button>
  );
}

// ── Business Card ────────────────────────────────────────────────────────────
function BusinessCard({ biz, onClick }: { biz: Business; onClick: () => void }) {
  const [hov, setHov] = useState(false);
  const badge = {
    active:   { text: '✅ פעיל',         bg: 'rgba(16,185,129,0.2)',  color: '#10b981', border: 'rgba(16,185,129,0.3)' },
    building: { text: '🔨 בבנייה',       bg: 'rgba(245,158,11,0.2)',  color: '#f59e0b', border: 'rgba(245,158,11,0.3)' },
    pending:  { text: '⏳ טרם הצטרף',    bg: 'rgba(156,163,175,0.15)', color: '#9ca3af', border: 'rgba(156,163,175,0.2)' },
  }[biz.status];

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        background: hov ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.04)',
        border: `1px solid ${hov ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.08)'}`,
        borderRadius: 18,
        padding: '24px',
        cursor: 'pointer',
        textAlign: 'right' as const,
        fontFamily: 'inherit',
        color: 'white',
        transition: 'all 0.2s ease',
        transform: hov ? 'translateY(-2px)' : 'none',
        width: '100%',
        overflow: 'hidden',
      }}
    >
      {biz.photo_url && (
        <img src={biz.photo_url} alt={biz.name}
          style={{ width: 'calc(100% + 48px)', height: 140, objectFit: 'cover', display: 'block', margin: '-24px -24px 16px', borderRadius: '18px 18px 0 0' }}
        />
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <span style={{ background: badge.bg, color: badge.color, border: `1px solid ${badge.border}`, borderRadius: 50, padding: '4px 12px', fontSize: 12, fontWeight: 600 }}>
          {badge.text}
        </span>
        {biz.city && <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>📍 {biz.city}</span>}
      </div>
      <div style={{ fontWeight: 800, fontSize: 18, marginBottom: 6 }}>{biz.name}</div>
      {biz.tagline && <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14, marginBottom: 10, lineHeight: 1.5 }}>{biz.tagline}</div>}
      {biz.rating != null && <div style={{ marginBottom: 8 }}><StarRating rating={biz.rating} /></div>}
      <div style={{
        marginTop: 16, padding: '10px 16px', borderRadius: 10,
        background: biz.status === 'active' ? 'linear-gradient(135deg,#f59e0b,#ef4444)' : 'rgba(255,255,255,0.08)',
        color: biz.status === 'active' ? 'white' : 'rgba(255,255,255,0.6)',
        fontWeight: 700, fontSize: 14, textAlign: 'center' as const,
      }}>
        {biz.status === 'active' ? '→ כנס לאתר' : biz.status === 'building' ? '🔨 האתר בבנייה' : '✨ בנה את האתר שלו'}
      </div>
    </button>
  );
}

// ── Mall View ────────────────────────────────────────────────────────────────

// ── Mall FAQ ──────────────────────────────────────────────────────────────────
const MALL_FAQ = [
  { cat: 'צרכן', q: 'מה זה TAZO Mall?', a: 'TAZO Mall הוא מרחב דיגיטלי של עסקים ישראלים — מסעדות, מספרות, שיפוצים ועוד. מחפשים עסק, מוצאים אתר, מזמינים ישירות.' },
  { cat: 'צרכן', q: 'איך מחפשים עסק?', a: 'בחרו קטגוריה (אוכל, יופי, חינוך...) או השתמשו בשורת החיפוש. המערכת מציגה עסקים אמיתיים שקיימים בסביבה שלכם.' },
  { cat: 'צרכן', q: 'האתר של העסק שבחרתי לא מוכן — מה קורה?', a: 'TAZO בונה אתר לעסק תוך דקות, ושולח לבעל העסק WhatsApp עם קישור לאישור. אפשר להשאיר טלפון ולקבל התראה כשהאתר עולה לאוויר.' },
  { cat: 'צרכן', q: 'האם ניתן להזמין ישירות מהאתר?', a: 'כן! עסקי מסעדות ואוכל מאפשרים הזמנה עם עגלה קניות ישירות. עסקי יופי וספא מאפשרים תיאום תור ב-WhatsApp.' },
  { cat: 'עסק', q: 'איך העסק שלי מופיע ב-TAZO Mall?', a: 'TAZO סורקת עסקים ממפות גוגל. אם העסק שלך רשום בגוגל מפות — הוא כבר שם. לקוח שמחפש אותך → TAZO בונה לך אתר ושולחת לך WhatsApp.' },
  { cat: 'עסק', q: 'קיבלתי WhatsApp מ-TAZO — מה עושים?', a: 'פשוט מאוד: ענו "אישור" — האתר שלכם יעלה לאוויר תוך דקות בכתובת שמית. אתר חינמי, ללא הגדרה, ללא תשלום.' },
  { cat: 'עסק', q: 'איך מקבלים בעלות על האתר ומנהלים אותו?', a: 'נרשמים ב-TAZO-SYNC (tazo-sync.com) → מאמתים את העסק (תעודה עסקית + טלפון) → מקבלים גישה לדשבורד. משם ניתן לערוך תפריט, שעות פעילות, ולראות הזמנות.' },
  { cat: 'עסק', q: 'האם האתר ממשיך להיות חינמי?', a: 'כן — האתר הבסיסי עם הזמנות ב-WhatsApp הוא חינמי לגמרי. תכונות מתקדמות (תשלום אונליין, ניהול מלאי, קופון) זמינות בחבילות בתשלום.' },
  { cat: 'עסק', q: 'איך הזמנות מגיעות אלי?', a: 'ישירות ל-WhatsApp שלכם! בנוסף, אם נרשמתם ב-TAZO-SYNC — ההזמנות מגיעות גם לדשבורד העסקי עם כל הפרטים.' },
  { cat: 'מערכת', q: 'איך TAZO בונה אתר לעסק תוך דקות?', a: 'שלב 1: שואבים מידע מגוגל מפות (שם, כתובת, טלפון, ביקורות). שלב 2: AI בוחר תבנית (מסעדה/מספרה/כללי). שלב 3: ממלאים תוכן אוטומטית. שלב 4: האתר עולה לכתובת ייחודית.' },
  { cat: 'מערכת', q: 'מה הקשר בין tazo-web.com ל-tazo-sync.com?', a: 'tazo-web.com הוא הפנים הציבורי — הלקוח רואה את האתר ומזמין. tazo-sync.com הוא הצד של בעל העסק — מקבל הזמנות, מאמת עסק, מנהל קטלוג.' },
  { cat: 'מערכת', q: 'מה הקשר ל-tazo-go.com?', a: 'tazo-go.com הוא מערכת ההסעות — נוסעים, נהגי מונית, ושליחים. עסקים שצריכים שליח לאחר קבלת הזמנה יכולים לתאם שליח דרך TAZO-GO ישירות מה-SYNC.' },
];

function MallFAQ() {
  const [open, setOpen] = useState<number | null>(null);
  const [filter, setFilter] = useState<string>('הכל');
  const cats = ['הכל', 'צרכן', 'עסק', 'מערכת'];
  const shown = filter === 'הכל' ? MALL_FAQ : MALL_FAQ.filter(x => x.cat === filter);
  return (
    <section style={{ padding: '64px 24px 80px', maxWidth: 780, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <div style={{ display: 'inline-block', background: 'rgba(245,158,11,0.12)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 50, padding: '5px 16px', fontSize: 12, color: '#f59e0b', marginBottom: 16, fontWeight: 700 }}>❓ שאלות נפוצות</div>
        <h2 style={{ fontSize: 'clamp(24px,4vw,36px)', fontWeight: 900, margin: 0 }}>כל מה שרצית לדעת<br /><span style={{ background: 'linear-gradient(135deg,#f59e0b,#ef4444)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>על TAZO Mall</span></h2>
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 36, flexWrap: 'wrap' as const }}>
        {cats.map(c => (
          <button key={c} onClick={() => { setFilter(c); setOpen(null); }}
            style={{ padding: '8px 18px', borderRadius: 50, border: `1.5px solid ${filter === c ? '#f59e0b' : 'rgba(255,255,255,0.12)'}`, background: filter === c ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.04)', color: filter === c ? '#f59e0b' : 'rgba(255,255,255,0.55)', fontWeight: 700, fontSize: 13, cursor: 'pointer', fontFamily: 'inherit', transition: 'all .2s' }}>
            {c}
          </button>
        ))}
      </div>
      <div>
        {shown.map((item, i) => (
          <div key={i} style={{ border: `1px solid ${open === i ? 'rgba(245,158,11,0.35)' : 'rgba(255,255,255,0.07)'}`, borderRadius: 14, marginBottom: 10, background: open === i ? 'rgba(245,158,11,0.04)' : 'rgba(255,255,255,0.03)', overflow: 'hidden', transition: 'border-color .2s' }}>
            <button onClick={() => setOpen(open === i ? null : i)}
              style={{ width: '100%', textAlign: 'right' as const, padding: '18px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, background: 'none', border: 'none', color: 'white', fontWeight: 700, fontSize: 15, cursor: 'pointer', fontFamily: 'inherit', lineHeight: 1.45 }}>
              <span>{item.q}</span>
              <span style={{ flexShrink: 0, width: 22, height: 22, borderRadius: '50%', background: 'rgba(255,255,255,0.07)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, transition: 'transform .3s', transform: open === i ? 'rotate(180deg)' : 'none', color: open === i ? '#f59e0b' : 'rgba(255,255,255,0.4)' }}>&#9660;</span>
            </button>
            {open === i && (
              <div style={{ padding: '0 20px 18px', color: 'rgba(255,255,255,0.6)', fontSize: 14, lineHeight: 1.8 }}>{item.a}</div>
            )}
          </div>
        ))}
      </div>
      <div style={{ textAlign: 'center', marginTop: 40, padding: '28px 24px', background: 'rgba(37,211,102,0.06)', border: '1px solid rgba(37,211,102,0.15)', borderRadius: 16 }}>
        <div style={{ fontSize: 24, marginBottom: 10 }}>&#128172;</div>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>לא מצאת תשובה?</div>
        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13, marginBottom: 16 }}>פנה אלינו ישירות — נענה תוך דקות</div>
        <a href="https://wa.me/972546363350" target="_blank" rel="noopener noreferrer"
          style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '12px 24px', borderRadius: 50, background: 'linear-gradient(135deg,#25D366,#1ebe5d)', color: 'white', fontWeight: 700, fontSize: 14, textDecoration: 'none', fontFamily: 'inherit' }}>
          &#128172; WhatsApp תמיכה
        </a>
      </div>
    </section>
  );
}

interface NearbyBusiness {
  place_id: string;
  name: string;
  address: string;
  rating?: number;
  reviews_count?: number;
  distance_km: number;
  in_tazo: boolean;
  subdomain?: string;
  url?: string;
  status: 'active' | 'available';
  photo_url?: string;
  open_now?: boolean;
  category?: string;
}

// ── Nearby Card ──────────────────────────────────────────────────────────────
function NearbyCard({ biz, onBuild }: { biz: NearbyBusiness; onBuild: (b: NearbyBusiness) => void }) {
  const [building, setBuilding] = useState(false);
  const [built, setBuilt] = useState(false);
  const distLabel = biz.distance_km < 1
    ? `${Math.round(biz.distance_km * 1000)} מ'`
    : `${biz.distance_km.toFixed(1)} ק"מ`;
  const handleBuild = async () => {
    setBuilding(true);
    await onBuild(biz);
    setBuilt(true);
    setBuilding(false);
  };
  return (
    <div style={{ minWidth: 240, maxWidth: 260, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.09)', borderRadius: 16, overflow: 'hidden', flexShrink: 0 }}>
      {biz.photo_url ? (
        <img src={biz.photo_url} alt={biz.name} style={{ width: '100%', height: 140, objectFit: 'cover', display: 'block' }} />
      ) : (
        <div style={{ width: '100%', height: 140, background: 'rgba(255,255,255,0.04)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 40 }}>
          🏢
        </div>
      )}
      <div style={{ padding: '14px 14px 16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
          <span style={{ fontSize: 11, background: biz.in_tazo ? 'rgba(34,197,94,0.15)' : 'rgba(245,158,11,0.12)', color: biz.in_tazo ? '#4ade80' : '#f59e0b', borderRadius: 20, padding: '2px 10px', fontWeight: 700 }}>
            {biz.in_tazo ? '✅ ב-TAZO' : '🔨 זמין לבנייה'}
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 3 }}>
            <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>📍 {distLabel}</span>
            {biz.open_now !== undefined && (
              <span style={{ fontSize: 10, fontWeight: 700, color: biz.open_now ? '#4ade80' : '#f87171' }}>
                {biz.open_now ? '🟢 פתוח עכשיו' : '🔴 סגור'}
              </span>
            )}
          </div>
        </div>
        <div style={{ fontWeight: 800, fontSize: 15, marginBottom: 4, lineHeight: 1.3 }}>{biz.name}</div>
        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginBottom: 10 }}>{biz.address}</div>
        {biz.rating && (
          <div style={{ fontSize: 13, color: '#f59e0b', marginBottom: 12 }}>
            {'★'.repeat(Math.round(biz.rating))} {biz.rating.toFixed(1)} ({biz.reviews_count?.toLocaleString()})
          </div>
        )}
        {biz.in_tazo && biz.url ? (
          <a href={biz.url} target="_blank" rel="noopener noreferrer"
            style={{ display: 'block', textAlign: 'center', padding: '10px', background: 'linear-gradient(135deg,#4ade80,#22c55e)', borderRadius: 10, color: 'white', fontWeight: 700, fontSize: 13, textDecoration: 'none' }}>
            כנס לאתר →
          </a>
        ) : built ? (
          <div style={{ textAlign: 'center', padding: '10px', background: 'rgba(34,197,94,0.15)', borderRadius: 10, color: '#4ade80', fontWeight: 700, fontSize: 13 }}>
            ✅ נשלח לבעל העסק!
          </div>
        ) : (
          <button onClick={handleBuild} disabled={building}
            style={{ width: '100%', padding: '10px', background: building ? 'rgba(255,255,255,0.08)' : 'linear-gradient(135deg,#f59e0b,#ef4444)', border: 'none', borderRadius: 10, color: 'white', fontWeight: 700, fontSize: 13, cursor: building ? 'default' : 'pointer', fontFamily: 'inherit' }}>
            {building ? '🔨 בונה אתר...' : '🚀 בנה אתר עכשיו'}
          </button>
        )}
      </div>
    </div>
  );
}

// ── Nearby Section ───────────────────────────────────────────────────────────
const RADIUS_OPTIONS = [
  { km: 5,  label: '5 ק"מ'  },
  { km: 10, label: '10 ק"מ' },
  { km: 15, label: '15 ק"מ' },
  { km: 50, label: '50 ק"מ' },
] as const;

// Expand a short Hebrew query to a richer search term
function expandQuery(raw: string): string {
  const map: Record<string, string> = {
    'פיצה': 'פיצריה', 'פיצריה': 'פיצריה', 'פיצות': 'פיצריה',
    'המבורגר': 'המבורגר', 'המבורגרים': 'המבורגר',
    'שוורמה': 'שוורמה', 'שאורמה': 'שוורמה',
    'סושי': 'מסעדת סושי', 'יפנית': 'מסעדת סושי',
    'פלאפל': 'פלאפל', 'חומוס': 'מסעדת חומוס',
    'גריל': 'מסעדת גריל', 'בשר': 'מסעדת בשר',
    'מסעדה': 'מסעדה', 'אוכל': 'מסעדה',
    'קפה': 'בית קפה', 'קפיטריה': 'בית קפה', 'קפה בוקר': 'בית קפה',
    'עוגות': 'מאפייה', 'מאפה': 'מאפייה', 'לחם': 'מאפייה',
    'מספרה': 'מספרה', 'תספורת': 'מספרה', 'ספרות': 'מספרה',
    'ציפורניים': 'מניקור פדיקור', 'מניקור': 'מניקור פדיקור',
    'ספא': 'ספא עיסוי', 'עיסוי': 'ספא עיסוי',
    'כושר': 'חדר כושר', 'ספורט': 'חדר כושר', 'חדר כושר': 'חדר כושר',
    'יוגה': 'יוגה פילאטיס', 'פילאטיס': 'יוגה פילאטיס',
    'רכב': 'מוסך', 'מכונאות': 'מוסך', 'צמיגים': 'מוסך צמיגים',
    'חשמלאי': 'חשמלאי', 'שרברב': 'שרברב', 'אינסטלציה': 'שרברב',
    'שיפוץ': 'שיפוצניק', 'שיפוצים': 'שיפוצניק',
    'גן ילדים': 'גן ילדים', 'גן': 'גן ילדים',
    'פיזיותרפיה': 'פיזיותרפיה', 'פיזיו': 'פיזיותרפיה',
    'וטרינר': 'וטרינר', 'כלב': 'ספר כלבים', 'חתול': 'וטרינר',
    'גינון': 'גנן', 'גן': 'גנן',
    'ניקיון': 'ניקיון בית', 'שטיחים': 'ניקיון שטיחים',
  };
  const low = raw.trim().toLowerCase();
  return map[low] || raw.trim();
}

function NearbySection({ query, autoStart = false }: { query: string; autoStart?: boolean }) {
  const [loc, setLoc] = useState<{ lat: number; lng: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<NearbyBusiness[]>([]);
  const [error, setError] = useState('');
  const [askedLoc, setAskedLoc] = useState(false);
  const [radiusKm, setRadiusKm] = useState<5 | 10 | 15 | 50>(10);
  const [searchQ, setSearchQ] = useState(query || '');
  const [activeQ, setActiveQ] = useState(query || '');

  // Keep searchQ in sync when parent passes a new query
  useEffect(() => { if (query) { setSearchQ(query); } }, [query]);

  const fetchNearby = useCallback(async (lat: number, lng: number, q: string, km: number) => {
    const expanded = expandQuery(q || 'עסק');
    setLoading(true);
    setError('');
    try {
      const r = await fetch(
        `${API}/public/mall/nearby?lat=${lat}&lng=${lng}&q=${encodeURIComponent(expanded)}&radius=${km * 1000}&limit=20`
      );
      const d = await r.json();
      setResults(d.businesses || []);
      if ((d.businesses || []).length === 0) setError('');
    } catch {
      setError('לא הצלחנו לאחזר תוצאות. בדוק חיבור לאינטרנט.');
    }
    setLoading(false);
  }, []);

  const requestLocation = useCallback((q: string, km: number) => {
    setAskedLoc(true);
    if (!navigator.geolocation) { setError('הדפדפן לא תומך ב-GPS'); return; }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      pos => {
        const newLoc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setLoc(newLoc);
        fetchNearby(newLoc.lat, newLoc.lng, q, km);
      },
      () => { setError('לא אושר גישה למיקום. אפשר זאת בהגדרות הדפדפן.'); setLoading(false); },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, [fetchNearby]);

  const handleSearch = () => {
    const q = searchQ.trim() || 'עסק';
    setActiveQ(q);
    if (loc) fetchNearby(loc.lat, loc.lng, q, radiusKm);
    else requestLocation(q, radiusKm);
  };

  const handleRadiusChange = (km: 5 | 10 | 15 | 50) => {
    setRadiusKm(km);
    if (loc && activeQ) fetchNearby(loc.lat, loc.lng, activeQ, km);
  };

  const handleBuild = async (biz: NearbyBusiness) => {
    try {
      await fetch(`${API}/public/mall/build-from-place`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          place_id: biz.place_id,
          name: biz.name,
          address: biz.address,
          rating: biz.rating,
          reviews_count: biz.reviews_count,
          lat: (biz as NearbyBusiness & { lat?: number }).lat ?? loc?.lat,
          lng: (biz as NearbyBusiness & { lng?: number }).lng ?? loc?.lng,
        }),
      });
    } catch { /* handled by card */ }
  };

  useEffect(() => {
    if (autoStart && query) requestLocation(query, radiusKm);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Not yet asked for location → show the search widget ──────────────────
  if (!askedLoc) {
    return (
      <div style={{ maxWidth: 640, margin: '0 auto 40px', padding: '0 24px' }}>
        {/* Search row */}
        <div style={{
          display: 'flex', gap: 10, alignItems: 'stretch',
          background: 'rgba(255,255,255,0.05)', borderRadius: 18,
          border: '1px solid rgba(255,255,255,0.1)', padding: '10px 12px',
          boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
        }}>
          <span style={{ fontSize: 22, flexShrink: 0, alignSelf: 'center', paddingRight: 4 }}>📍</span>
          <input
            value={searchQ}
            onChange={e => setSearchQ(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="מה אתה מחפש? (פיצה, מספרה, כושר...)"
            style={{
              flex: 1, background: 'none', border: 'none', outline: 'none',
              color: 'white', fontSize: 15, fontFamily: 'inherit', direction: 'rtl', minWidth: 0,
            }}
          />
          <button
            onClick={handleSearch}
            style={{
              flexShrink: 0, padding: '10px 22px', borderRadius: 12,
              background: 'linear-gradient(135deg,#FF6B00,#ef4444)',
              border: 'none', color: 'white', fontWeight: 800, fontSize: 14,
              cursor: 'pointer', fontFamily: 'inherit', whiteSpace: 'nowrap',
            }}>
            חפש בסביבתי
          </button>
        </div>
        {/* Radius chips */}
        <div style={{ display: 'flex', gap: 8, marginTop: 12, justifyContent: 'center' }}>
          {RADIUS_OPTIONS.map(opt => (
            <button
              key={opt.km}
              onClick={() => setRadiusKm(opt.km as 5 | 10 | 15 | 50)}
              style={{
                padding: '6px 16px', borderRadius: 50, cursor: 'pointer', fontFamily: 'inherit', fontSize: 13,
                fontWeight: radiusKm === opt.km ? 800 : 500,
                background: radiusKm === opt.km ? 'rgba(255,107,0,0.2)' : 'rgba(255,255,255,0.04)',
                border: `1.5px solid ${radiusKm === opt.km ? '#FF6B00' : 'rgba(255,255,255,0.1)'}`,
                color: radiusKm === opt.km ? '#FF6B00' : 'rgba(255,255,255,0.5)',
                transition: 'all .15s',
              }}>
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    );
  }

  // ── After location requested → full results panel ────────────────────────
  return (
    <div style={{ margin: '0 auto 52px', maxWidth: 1100, padding: '0 24px' }}>

      {/* Control bar */}
      <div style={{
        display: 'flex', flexWrap: 'wrap' as const, gap: 10, alignItems: 'center',
        marginBottom: 20, background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.09)', borderRadius: 16, padding: '12px 16px',
      }}>
        {/* Search input */}
        <div style={{ flex: '1 1 200px', display: 'flex', gap: 8, minWidth: 0 }}>
          <input
            value={searchQ}
            onChange={e => setSearchQ(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="שנה חיפוש (פיצה, המבורגר...)"
            style={{
              flex: 1, padding: '9px 14px', borderRadius: 10, minWidth: 0,
              border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.06)',
              color: 'white', fontSize: 14, fontFamily: 'inherit', direction: 'rtl', outline: 'none',
            }}
          />
          <button onClick={handleSearch}
            style={{ padding: '9px 16px', borderRadius: 10, background: 'linear-gradient(135deg,#FF6B00,#ef4444)', border: 'none', color: 'white', fontWeight: 800, fontSize: 14, cursor: 'pointer', fontFamily: 'inherit', flexShrink: 0 }}>
            🔍
          </button>
        </div>

        {/* Radius selector */}
        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
          {RADIUS_OPTIONS.map(opt => (
            <button
              key={opt.km}
              onClick={() => handleRadiusChange(opt.km as 5 | 10 | 15 | 50)}
              style={{
                padding: '7px 14px', borderRadius: 50, cursor: 'pointer', fontFamily: 'inherit', fontSize: 12, fontWeight: radiusKm === opt.km ? 800 : 500,
                background: radiusKm === opt.km ? 'rgba(255,107,0,0.2)' : 'rgba(255,255,255,0.04)',
                border: `1.5px solid ${radiusKm === opt.km ? '#FF6B00' : 'rgba(255,255,255,0.1)'}`,
                color: radiusKm === opt.km ? '#FF6B00' : 'rgba(255,255,255,0.5)',
                transition: 'all .15s',
              }}>
              {opt.label}
            </button>
          ))}
        </div>

        {/* Refresh */}
        {loc && (
          <button onClick={() => fetchNearby(loc.lat, loc.lng, activeQ, radiusKm)}
            style={{ padding: '7px 14px', borderRadius: 10, background: 'none', border: '1px solid rgba(255,255,255,0.12)', color: 'rgba(255,255,255,0.5)', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', flexShrink: 0 }}>
            🔄
          </button>
        )}
      </div>

      {/* Title */}
      <h2 style={{ fontSize: 19, fontWeight: 800, margin: '0 0 16px', color: 'rgba(255,255,255,0.85)' }}>
        📍 {activeQ ? `"${activeQ}"` : 'עסקים'} בטווח של {radiusKm} ק"מ
      </h2>

      {/* Error */}
      {error && (
        <div style={{ padding: '12px 18px', borderRadius: 12, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)', color: '#fca5a5', fontSize: 14, marginBottom: 16 }}>
          ⚠️ {error}
        </div>
      )}

      {/* Skeletons */}
      {loading && (
        <div style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 8 }}>
          {[1,2,3,4,5].map(i => (
            <div key={i} style={{ minWidth: 220, height: 240, background: 'rgba(255,255,255,0.04)', borderRadius: 16, flexShrink: 0, animation: 'pulse 1.5s ease-in-out infinite' }} />
          ))}
        </div>
      )}

      {/* Results */}
      {!loading && results.length > 0 && (
        <>
          <div style={{ color: 'rgba(255,255,255,0.35)', fontSize: 13, marginBottom: 12 }}>
            נמצאו {results.length} עסקים
          </div>
          <div style={{ display: 'flex', gap: 14, overflowX: 'auto', paddingBottom: 12, scrollbarWidth: 'thin' as const }}>
            {results.map(biz => (
              <NearbyCard key={biz.place_id} biz={biz} onBuild={handleBuild} />
            ))}
          </div>
        </>
      )}

      {/* Empty state */}
      {!loading && results.length === 0 && loc && !error && (
        <div style={{ textAlign: 'center', padding: '40px 24px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 20 }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🔍</div>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>לא נמצאו עסקים</div>
          <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: 14, marginBottom: 16 }}>
            נסה לשנות את החיפוש או הגדל את הטווח
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' as const }}>
            {RADIUS_OPTIONS.filter(o => o.km > radiusKm).slice(0, 2).map(opt => (
              <button key={opt.km} onClick={() => handleRadiusChange(opt.km as 5 | 10 | 15 | 50)}
                style={{ padding: '8px 18px', borderRadius: 50, background: 'rgba(255,107,0,0.15)', border: '1px solid rgba(255,107,0,0.4)', color: '#FF6B00', fontWeight: 700, fontSize: 13, cursor: 'pointer', fontFamily: 'inherit' }}>
                הגדל ל-{opt.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


function MallView({ onCategory, onSearch, onJoin, onBusinessClick }: {
  onCategory: (c: Category) => void;
  onSearch: (q: string) => void;
  onJoin: () => void;
  onBusinessClick: (b: Business) => void;
}) {
  const [q, setQ] = useState('');
  const [featured, setFeatured] = useState<Business[]>([]);

  useEffect(() => {
    fetch(`${API}/public/mall/featured`)
      .then(r => r.ok ? r.json() : null)
      .then(d => d?.businesses && setFeatured(d.businesses))
      .catch(() => {});
  }, []);

  return (
    <div style={{ minHeight: '100vh', background: '#0f0f0f', color: 'white', fontFamily: '"Heebo", sans-serif', direction: 'rtl' }}>

      {/* NAV */}
      <nav style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.08)', position: 'sticky', top: 0, background: 'rgba(15,15,15,0.95)', backdropFilter: 'blur(12px)', zIndex: 100 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 28, fontWeight: 900, background: 'linear-gradient(135deg,#f59e0b,#ef4444)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>TAZO</span>
          <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', borderRight: '1px solid rgba(255,255,255,0.15)', paddingRight: 10 }}>Mall</span>
        </div>
        <button onClick={onJoin} style={{ background: 'linear-gradient(135deg,#f59e0b,#ef4444)', border: 'none', borderRadius: 50, padding: '10px 22px', color: 'white', fontWeight: 700, fontSize: 14, cursor: 'pointer', fontFamily: 'inherit' }}>
          הצטרף כעסק ✨
        </button>
      </nav>

      {/* HERO */}
      <section style={{ textAlign: 'center', padding: '64px 24px 48px' }}>
        <div style={{ display: 'inline-block', background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 50, padding: '6px 18px', fontSize: 13, color: '#f59e0b', marginBottom: 24 }}>
          🌐 המרחב הדיגיטלי של הרחוב שלך
        </div>
        <h1 style={{ fontSize: 'clamp(36px,6vw,72px)', fontWeight: 900, lineHeight: 1.1, marginBottom: 16, letterSpacing: '-1px' }}>
          מצא כל עסק.<br />
          <span style={{ background: 'linear-gradient(135deg,#f59e0b,#ef4444,#ec4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            הזמן, קבל, תהנה.
          </span>
        </h1>
        <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 18, marginBottom: 40, maxWidth: 520, margin: '0 auto 40px' }}>
          מסעדות, שירותים, יופי, חינוך — כולם כאן.<br />
          חפש עסק ו-TAZO יבנה לו אתר תוך דקות.
        </p>

        {/* Search Bar */}
        <div style={{ display: 'flex', gap: 12, maxWidth: 580, margin: '0 auto', direction: 'rtl' }}>
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && q.trim() && onSearch(q)}
            placeholder="חפש עסק, מוצר, שירות..."
            style={{ flex: 1, padding: '16px 22px', borderRadius: 14, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.07)', color: 'white', fontSize: 16, fontFamily: 'inherit', outline: 'none', direction: 'rtl' }}
          />
          <button
            onClick={() => q.trim() && onSearch(q)}
            style={{ padding: '16px 28px', borderRadius: 14, background: 'linear-gradient(135deg,#f59e0b,#ef4444)', border: 'none', color: 'white', fontWeight: 700, fontSize: 16, cursor: 'pointer', fontFamily: 'inherit', whiteSpace: 'nowrap' }}
          >
            🔍 חפש
          </button>
        </div>
      </section>


        {/* NEARBY SEARCH */}
        <NearbySection query={q} />
      {/* CATEGORIES */}
      <section style={{ padding: '0 24px 80px', maxWidth: 1100, margin: '0 auto' }}>
        <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 28, color: 'rgba(255,255,255,0.85)' }}>קטגוריות</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(150px,1fr))', gap: 12 }}>
          {CATEGORIES.map(cat => (
            <CategoryCard key={cat.id} cat={cat} onClick={() => onCategory(cat)} />
          ))}
        </div>
      </section>

      {/* FEATURED */}
      {featured.length > 0 && (
        <section style={{ padding: '0 24px 80px', maxWidth: 1100, margin: '0 auto' }}>
          <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 28 }}>עסקים מומלצים ⭐</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(280px,1fr))', gap: 16 }}>
            {featured.map(biz => (
              <BusinessCard key={biz.id} biz={biz} onClick={() => onBusinessClick(biz)} />
            ))}
          </div>
        </section>
      )}

      {/* HOW IT WORKS */}
      <section style={{ background: 'rgba(255,255,255,0.03)', padding: '64px 24px', textAlign: 'center' }}>
        <h2 style={{ fontSize: 28, fontWeight: 800, marginBottom: 48 }}>איך TAZO Mall עובד?</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 32, maxWidth: 900, margin: '0 auto' }}>
          {[
            { icon: '🔍', title: 'חפש עסק', desc: 'חפש עסק לפי קטגוריה או שם' },
            { icon: '🌐', title: 'אתר מוכן', desc: 'לחץ לכניסה לאתר האישי של העסק' },
            { icon: '🔨', title: 'טרם הצטרף?', desc: 'TAZO בונה לו אתר עכשיו ושולח קישור' },
            { icon: '🛒', title: 'הזמן ישירות', desc: 'הזמן, צור קשר, קנה — הכל מהאתר' },
          ].map(s => (
            <div key={s.title} style={{ padding: 24, borderRadius: 20, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>{s.icon}</div>
              <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 8 }}>{s.title}</div>
              <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14, lineHeight: 1.6 }}>{s.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <MallFAQ />

      {/* FOOTER */}
      <footer style={{ padding: '40px 24px 32px', textAlign: 'center', borderTop: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.3)', fontSize: 13 }}>
        <div style={{ fontWeight: 900, color: 'white', marginBottom: 6, fontSize: 22, background: 'linear-gradient(135deg,#f59e0b,#ef4444)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', display: 'inline-block' }}>TAZO Mall</div>
        <div style={{ color: 'rgba(255,255,255,0.4)', marginBottom: 20 }}>המרחב הדיגיטלי של הרחוב הישראלי</div>
        <div style={{ marginBottom: 24 }}>
          <button onClick={onJoin} style={{ background: 'none', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 50, padding: '8px 22px', color: 'rgba(255,255,255,0.5)', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit' }}>
            הצטרף כעסק →
          </button>
        </div>
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 18, fontSize: 12, color: 'rgba(255,255,255,0.25)', lineHeight: 2 }}>
          © 2026 TAZO | כל הזכויות שמורות<br />
          אריאל אביב עוסק מורשה<br />
          <a href="mailto:info@tazo-web.com" style={{ color: 'rgba(255,255,255,0.3)', textDecoration: 'none' }}>info@tazo-web.com</a>
        </div>
      </footer>
      <VersionBar />
    </div>
  );
}

// ── Category View ────────────────────────────────────────────────────────────
function CategoryView({ category, businesses, loading, onSearch, onBusinessClick, onBack }: {
  category: Category | null;
  businesses: Business[];
  loading: boolean;
  onSearch: (q: string) => void;
  onBusinessClick: (b: Business) => void;
  onBack: () => void;
}) {
  const [q, setQ] = useState('');
  const filtered = q ? businesses.filter(b => b.name.includes(q) || b.city?.includes(q)) : businesses;

  return (
    <div style={{ minHeight: '100vh', background: '#0f0f0f', color: 'white', fontFamily: '"Heebo", sans-serif', direction: 'rtl' }}>
      <nav style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', gap: 16, borderBottom: '1px solid rgba(255,255,255,0.08)', position: 'sticky', top: 0, background: 'rgba(15,15,15,0.95)', backdropFilter: 'blur(12px)', zIndex: 100 }}>
        <button onClick={onBack} style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10, padding: '10px 18px', color: 'white', cursor: 'pointer', fontFamily: 'inherit', fontSize: 14 }}>
          ← חזרה
        </button>
        {category && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 28 }}>{category.emoji}</span>
            <span style={{ fontWeight: 800, fontSize: 20 }}>{category.name}</span>
          </div>
        )}
      </nav>

      <div style={{ padding: '32px 24px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'flex', gap: 12, marginBottom: 32 }}>
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && onSearch(q)}
            placeholder="חפש בתוך הקטגוריה..."
            style={{ flex: 1, padding: '14px 20px', borderRadius: 12, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.06)', color: 'white', fontSize: 15, fontFamily: 'inherit', outline: 'none', direction: 'rtl' }}
          />
          <button onClick={() => onSearch(q)} style={{ padding: '14px 24px', borderRadius: 12, background: 'linear-gradient(135deg,#f59e0b,#ef4444)', border: 'none', color: 'white', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit' }}>
            🔍
          </button>
        </div>

        <NearbySection query={category?.name || ''} autoStart />

        {loading && (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'rgba(255,255,255,0.4)' }}>
            <div style={{ fontSize: 40, marginBottom: 16 }}>⚙️</div>טוען עסקים...
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <div style={{ fontSize: 60, marginBottom: 20 }}>🔍</div>
            <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 12 }}>לא נמצאו עסקים</div>
            <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: 15 }}>
              לא מצאנו עסקים בקטגוריה זו עדיין — אנחנו עובדים על הרחבת הרשת 🚀
            </div>
          </div>
        )}

        {!loading && filtered.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(280px,1fr))', gap: 16 }}>
            {filtered.map(biz => (
              <BusinessCard key={biz.id} biz={biz} onClick={() => onBusinessClick(biz)} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Building View ────────────────────────────────────────────────────────────
function BuildingView({ business, buildStep, notifyPhone, setNotifyPhone, notifySent, onNotifyMe, onBack }: {
  business: Business | null;
  buildStep: number;
  notifyPhone: string;
  setNotifyPhone: (v: string) => void;
  notifySent: boolean;
  onNotifyMe: () => void;
  onBack: () => void;
}) {
  const [pulse, setPulse] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setPulse(p => (p + 1) % 2), 500);
    return () => clearInterval(t);
  }, []);

  const done = buildStep >= BUILD_STEPS.length;

  return (
    <div style={{ minHeight: '100vh', background: '#0f0f0f', color: 'white', fontFamily: '"Heebo", sans-serif', direction: 'rtl', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <button onClick={onBack} style={{ position: 'fixed', top: 20, right: 24, background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10, padding: '10px 18px', color: 'white', cursor: 'pointer', fontFamily: 'inherit', fontSize: 14 }}>
        ← חזרה
      </button>

      <div style={{ maxWidth: 560, width: '100%', textAlign: 'center' }}>
        <div style={{ fontSize: 80, marginBottom: 24 }}>{done ? '🎉' : '🔨'}</div>

        <h1 style={{ fontSize: 'clamp(28px,5vw,42px)', fontWeight: 900, marginBottom: 12 }}>
          {done ? 'האתר יהיה מוכן בקרוב!' : 'בונים את האתר עכשיו...'}
        </h1>

        {business && (
          <div style={{ display: 'inline-block', background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 12, padding: '12px 24px', marginBottom: 32, fontSize: 18, fontWeight: 700, color: '#f59e0b' }}>
            {business.name}
          </div>
        )}

        {/* Steps */}
        <div style={{ textAlign: 'right', marginBottom: 40 }}>
          {BUILD_STEPS.map((step, i) => {
            const active = i === buildStep - 1;
            const completed = i < buildStep;
            return (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 16, padding: '14px 20px', marginBottom: 8,
                borderRadius: 14,
                background: completed ? 'rgba(16,185,129,0.1)' : active ? 'rgba(245,158,11,0.1)' : 'rgba(255,255,255,0.03)',
                border: `1px solid ${completed ? 'rgba(16,185,129,0.25)' : active ? 'rgba(245,158,11,0.25)' : 'rgba(255,255,255,0.06)'}`,
                opacity: i > buildStep ? 0.35 : 1,
                transition: 'all 0.4s ease',
              }}>
                <span style={{ fontSize: 22, minWidth: 28 }}>
                  {completed ? '✅' : active ? (pulse === 0 ? '⚡' : '✨') : step.icon}
                </span>
                <span style={{ fontSize: 15, fontWeight: completed || active ? 600 : 400, color: completed ? '#10b981' : active ? '#f59e0b' : 'rgba(255,255,255,0.4)' }}>
                  {step.text}
                </span>
              </div>
            );
          })}
        </div>

        {/* WA notice */}
        {buildStep >= 4 && (
          <div style={{ background: 'rgba(37,211,102,0.1)', border: '1px solid rgba(37,211,102,0.25)', borderRadius: 16, padding: 24, marginBottom: 32, textAlign: 'right' }}>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8, color: '#25d366' }}>💬 WhatsApp נשלח לבעל העסק!</div>
            <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: 14, lineHeight: 1.7 }}>
              שלחנו ל{business?.name || 'העסק'} קישור לאתר הדמו.<br />
              ברגע שיאשרו — האתר עולה לאוויר עם כל הפרטים האמיתיים.
            </div>
          </div>
        )}

        {/* Notify Me */}
        {buildStep >= 3 && !notifySent && (
          <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 16, padding: 24, textAlign: 'right' }}>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>📲 רוצה לדעת כשהאתר מוכן?</div>
            <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14, marginBottom: 16 }}>השאר מספר טלפון ונעדכן אותך ב-WhatsApp</div>
            <div style={{ display: 'flex', gap: 10 }}>
              <input
                type="tel"
                value={notifyPhone}
                onChange={e => setNotifyPhone(e.target.value)}
                placeholder="05X-XXXXXXX"
                style={{ flex: 1, padding: '12px 16px', borderRadius: 12, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: 'white', fontSize: 15, fontFamily: 'inherit', outline: 'none' }}
              />
              <button onClick={onNotifyMe} style={{ padding: '12px 20px', borderRadius: 12, background: 'linear-gradient(135deg,#25d366,#128c7e)', border: 'none', color: 'white', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit', whiteSpace: 'nowrap' }}>
                💬 עדכן אותי
              </button>
            </div>
          </div>
        )}

        {notifySent && (
          <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', borderRadius: 16, padding: 24, textAlign: 'center' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>🎉</div>
            <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 8, color: '#10b981' }}>נרשמת בהצלחה!</div>
            <div style={{ color: 'rgba(255,255,255,0.55)', fontSize: 15 }}>
              נשלח לך WhatsApp ברגע שהאתר של {business?.name} יהיה מוכן.<br />
              <strong style={{ color: 'white' }}>תודה שאתה חלק מהשינוי 💪</strong>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Root Export ──────────────────────────────────────────────────────────────
export default function Marketplace({ onJoin }: { onJoin: () => void }) {
  const [view, setView] = useState<View>('mall');
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(false);
  const [buildingBiz, setBuildingBiz] = useState<Business | null>(null);
  const [buildStep, setBuildStep] = useState(0);
  const [notifyPhone, setNotifyPhone] = useState('');
  const [notifySent, setNotifySent] = useState(false);

  const fetchBusinesses = useCallback(async (catId: string, q?: string) => {
    setLoading(true);
    try {
      const p = new URLSearchParams({ category: catId });
      if (q) p.append('q', q);
      const r = await fetch(`${API}/public/mall/businesses?${p}`);
      const d = r.ok ? await r.json() : {};
      setBusinesses(d.businesses || []);
    } catch { setBusinesses([]); }
    finally { setLoading(false); }
  }, []);

  const handleCategoryClick = (cat: Category) => {
    setSelectedCategory(cat);
    setView('category');
    fetchBusinesses(cat.id);
  };

  const handleSearch = async (q: string) => {
    setSelectedCategory(null);
    setView('category');
    setLoading(true);
    try {
      const r = await fetch(`${API}/public/mall/search?q=${encodeURIComponent(q)}`);
      const d = r.ok ? await r.json() : {};
      setBusinesses(d.businesses || []);
    } catch { setBusinesses([]); }
    finally { setLoading(false); }
  };

  const handleBusinessClick = async (biz: Business) => {
    if (biz.status === 'active' && biz.subdomain) {
      window.open(`https://${biz.subdomain}.tazo-web.com`, '_blank');
      return;
    }
    setBuildingBiz(biz);
    setBuildStep(0);
    setNotifyPhone('');
    setNotifySent(false);
    setView('building');
    [500, 1300, 2200, 3200, 4500].forEach((ms, i) =>
      setTimeout(() => setBuildStep(i + 1), ms)
    );
    try {
      await fetch(`${API}/public/mall/trigger-build`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_id: biz.id, business_name: biz.name }),
      });
    } catch {}
  };

  const handleNotifyMe = async () => {
    if (!notifyPhone.trim()) return;
    try {
      await fetch(`${API}/public/mall/notify-me`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: notifyPhone, business_id: buildingBiz?.id, business_name: buildingBiz?.name }),
      });
    } catch {}
    setNotifySent(true);
  };

  if (view === 'building') {
    return <BuildingView
      business={buildingBiz}
      buildStep={buildStep}
      notifyPhone={notifyPhone}
      setNotifyPhone={setNotifyPhone}
      notifySent={notifySent}
      onNotifyMe={handleNotifyMe}
      onBack={() => setView('category')}
    />;
  }
  if (view === 'category') {
    return <CategoryView
      category={selectedCategory}
      businesses={businesses}
      loading={loading}
      onSearch={q => { if (selectedCategory) fetchBusinesses(selectedCategory.id, q); }}
      onBusinessClick={handleBusinessClick}
      onBack={() => { setView('mall'); setBusinesses([]); }}
    />;
  }
  return <MallView onCategory={handleCategoryClick} onSearch={handleSearch} onJoin={onJoin} onBusinessClick={handleBusinessClick} />;
}
