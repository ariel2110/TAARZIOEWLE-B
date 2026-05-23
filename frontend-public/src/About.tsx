import { useEffect, useRef, useState } from 'react'

/* ─────────────────────────────────────────────────────────────────
   TAZO About Page — "מהשטח אל העולם"
   Full-page, RTL, dark-navy theme, zero external deps
───────────────────────────────────────────────────────────────── */

const C = {
  navy:    '#0A0F1A',
  navy2:   '#0D1526',
  card:    '#111827',
  border:  '#1E2D45',
  orange:  '#FF6B2B',
  orange2: '#FF4500',
  gold:    '#F59E0B',
  green:   '#10B981',
  blue:    '#3B82F6',
  purple:  '#8B5CF6',
  text:    '#F1F5F9',
  muted:   '#94A3B8',
  dim:     '#4B5563',
}

const PLATFORMS = [
  {
    icon: '🤖',
    color: C.blue,
    name: 'TAZO Web',
    domain: 'tazo-web.com',
    tagline: 'הלב הציבורי של האקוסיסטם',
    desc: 'TAZO Mall — קניון דיגיטלי מבוסס מיקום ורדיוס דינמי (5–50 ק"מ). שואב נתונים מ-Google Places ומקים נוכחות דיגיטלית לעסקים תוך דקות. כולל מנגנון Shadow Stores לתביעת בעלות מיידית.',
    url: 'https://tazo-web.com',
  },
  {
    icon: '🔗',
    color: C.green,
    name: 'TAZO Sync',
    domain: 'tazo-sync.com',
    tagline: 'רשת אספקה חכמה B2B | B2C',
    desc: 'דשבורד ניהול לעסקים + רשת אספקה מיידית. פותרת מצבי חירום של חוסר במלאי באמצע משמרת בלילה. מרכז ניהול להזמנות ומשלוחים מ-TAZO Web.',
    url: 'https://tazo-sync.com',
  },
  {
    icon: '🚕',
    color: C.orange,
    name: 'TAZO Go',
    domain: 'tazo-go.com',
    tagline: 'תחבורה והסעות הוגנות',
    desc: 'עמלה של 12% בלבד לנהגים מורשים. מודל חבר-מביא-חבר (150 ₪ בונוס). ארכיטקטורת Uber-Pilot להפעלה מיידית בכל נקודה בעולם.',
    url: 'https://tazo-go.com',
  },
  {
    icon: '🔐',
    color: C.purple,
    name: 'TAZO Portal',
    domain: 'tazo-app.com',
    tagline: 'שער כניסה מרכזי',
    desc: 'פורטל מעבר ונקודת ציר המקשרת ומנווטת בין חלקי האקוסיסטם. מנהל אימות זהות, ארנק דיגיטלי גלובלי (TAZO Vault) ומערכת Escrow.',
    url: 'https://tazo-app.com',
  },
]

const TIMELINE = [
  {
    num: '01',
    icon: '📱',
    color: C.blue,
    title: 'הניצוץ — רעיון מטיקטוק',
    text: 'נחשפתי לקונספט מעניין: לאתר עסקים מקומיים ולבנות להם אתר אינטרנט. הרעיון הדליק אותי, אבל השיטה הקיימת הייתה מסורבלת — בנייה חצי-ידנית, תוצאות לא מקצועיות, דפיקה על דלתות. בניתי מנוע אוטומטי לחלוטין: שואב מידע מ-Google ובונה אתר מקצועי תוך דקות.',
  },
  {
    num: '02',
    icon: '🚕',
    color: C.orange,
    title: 'נהג המונית שפתח את העיניים',
    text: 'שיחה כנה עם נהג מונית שסיפר על העמלות החונקות בשוק. באותו רגע קבעתי: 12% בלבד לנהגים מורשים. ובניתי תשתית Uber-Pilot ערוכה ליום שבו יכנס לתוקף החוק לתחבורה שיתופית עצמאית בישראל.',
  },
  {
    num: '03',
    icon: '📦',
    color: C.green,
    title: 'TazoSync — רשת האספקה',
    text: 'מתוך שיחות עם סוחרים: מה קורה לעסק שנתקע בלי סחורה בלילה? עם שרתים שהקמתי בעצמי ותשוקה, פיתחתי TazoSync — רשת שמאפשרת לעסקים סמוכים לאתר סחורה חסרה ולשלוח בקשת סיוע תוך דקות.',
  },
  {
    num: '04',
    icon: '🌍',
    color: C.purple,
    title: 'PWA — מהפכת "מעכשיו לעכשיו"',
    text: 'TAZO בנויה כ-PWA (Progressive Web App) — פלטפורמת-על רזה ומהירה שרצה ישירות מהדפדפן. אין התקנה, אין App Store, אין המתנה. כל מקום שיש בו קליטה סלולרית הופך מיידית לאזור פעיל של TAZO.',
  },
]

const TRUST_ITEMS = [
  {
    icon: '🛡️',
    color: C.blue,
    title: 'KYC דינמי ומאובטח',
    text: 'אימות קפדני לצרכנים, שליחים, נהגים ואנשי מקצוע — דרך WhatsApp ומול מאגרי מידע רשמיים (data.gov.il). נתוני הזיהוי הרגישים מנוהלים על ידי חברה חיצונית מתמחה בשרתים ייעודיים.',
  },
  {
    icon: '💎',
    color: C.gold,
    title: 'TAZO Vault — ארנק גלובלי',
    text: 'ניהול תשלומים, ארנק פנימי ומערכת Escrow המחזיקה כסף בבטחה עד לאישור קבלת השירות. 10% בונוס על טעינת הארנק.',
  },
  {
    icon: '🤖',
    color: C.green,
    title: 'AI Support 24/7',
    text: 'שירות לקוחות טלפוני AI ומענה WhatsApp בינה מלאכותית (053-388-9859). פותר בעיות, בירורים ואימותים תוך שניות — ללא זמני המתנה.',
  },
]

const NAME_STEPS = [
  { name: 'Easy Taxi Israel', color: C.dim, why: 'שם ראשון — אבל כבר קיים בברזיל (נקנה ע"י Cabify)' },
  { name: 'TaGo', color: C.muted, why: 'מוניות + דיגיטל. נשמע נורא ולא עובד במבטאים שונים 😬' },
  { name: 'TAZO ✨', color: C.orange, why: 'קליט, קצר, בינלאומי. מנצח!' },
]

// ── Reusable sub-components ───────────────────────────────────────

function FadeIn({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVisible(true); obs.disconnect() } }, { threshold: 0.1 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])
  return (
    <div ref={ref} style={{
      opacity: visible ? 1 : 0,
      transform: visible ? 'translateY(0)' : 'translateY(28px)',
      transition: `opacity 0.7s ease ${delay}ms, transform 0.7s ease ${delay}ms`,
    }}>
      {children}
    </div>
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
      <span style={{
        fontSize: 10, fontWeight: 800, letterSpacing: '.15em', textTransform: 'uppercase',
        color: C.orange, background: 'rgba(255,107,43,0.12)', padding: '3px 10px', borderRadius: 20,
        border: '1px solid rgba(255,107,43,0.25)',
      }}>{children}</span>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${C.border}, transparent)` }} />
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────

export default function AboutPage() {
  const [activeTab, setActiveTab] = useState<'story' | 'map' | 'trust'>('story')

  const css = `
    @keyframes glow-pulse {
      0%,100% { box-shadow: 0 0 20px rgba(255,107,43,0.3); }
      50%      { box-shadow: 0 0 50px rgba(255,107,43,0.6), 0 0 80px rgba(255,69,0,0.2); }
    }
    @keyframes float {
      0%,100% { transform: translateY(0px); }
      50%      { transform: translateY(-8px); }
    }
    @keyframes shimmer {
      0%   { background-position: -200% center; }
      100% { background-position: 200% center; }
    }
    @keyframes spin-slow {
      from { transform: rotate(0deg); }
      to   { transform: rotate(360deg); }
    }
    @keyframes rise {
      from { opacity:0; transform: translateY(40px) scale(0.96); }
      to   { opacity:1; transform: translateY(0) scale(1); }
    }
    .about-platform-card:hover {
      transform: translateY(-6px) scale(1.02) !important;
      border-color: var(--card-color) !important;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 30px color-mix(in srgb, var(--card-color) 25%, transparent) !important;
    }
    .about-platform-card { transition: transform 300ms ease, border-color 300ms ease, box-shadow 300ms ease !important; }
    .about-trust-card:hover { transform: translateY(-4px) !important; }
    .about-trust-card { transition: transform 250ms ease !important; }
    .tazo-tab-btn { transition: all 220ms ease !important; }
    .tazo-tab-btn:hover { background: rgba(255,107,43,0.12) !important; }
    @media (max-width: 640px) {
      .about-platform-grid { grid-template-columns: 1fr !important; }
      .about-trust-grid { grid-template-columns: 1fr !important; }
      .about-hero-title { font-size: clamp(2.4rem, 10vw, 4rem) !important; }
    }
  `

  return (
    <div dir="rtl" style={{
      minHeight: '100vh',
      background: `linear-gradient(180deg, ${C.navy} 0%, ${C.navy2} 100%)`,
      color: C.text,
      fontFamily: "'Heebo','Segoe UI',system-ui,sans-serif",
      overflowX: 'hidden',
    }}>
      <style>{css}</style>

      {/* ══════════════════════════════════════════════════════
          HERO
      ══════════════════════════════════════════════════════ */}
      <div style={{
        position: 'relative', minHeight: '100svh',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        padding: '80px 20px 60px', textAlign: 'center',
        background: `
          radial-gradient(ellipse 80% 60% at 50% 0%, rgba(255,107,43,0.12) 0%, transparent 70%),
          radial-gradient(ellipse 40% 40% at 80% 80%, rgba(59,130,246,0.06) 0%, transparent 60%),
          ${C.navy}
        `,
        overflow: 'hidden',
      }}>
        {/* Stars */}
        {Array.from({ length: 60 }).map((_, i) => (
          <div key={i} style={{
            position: 'absolute',
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            width: Math.random() * 2.5 + 0.5,
            height: Math.random() * 2.5 + 0.5,
            borderRadius: '50%',
            background: '#fff',
            opacity: Math.random() * 0.6 + 0.1,
            animation: `float ${3 + Math.random() * 5}s ease-in-out ${Math.random() * 3}s infinite`,
            pointerEvents: 'none',
          }} />
        ))}

        {/* Logo orb */}
        <div style={{
          width: 100, height: 100, borderRadius: '50%',
          background: 'linear-gradient(135deg, #FF4500 0%, #FF6B2B 50%, #FFD700 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 48, fontWeight: 900, color: '#fff',
          animation: 'glow-pulse 3s ease-in-out infinite, float 6s ease-in-out infinite',
          marginBottom: 28, zIndex: 1, flexShrink: 0,
          boxShadow: '0 0 40px rgba(255,107,43,0.5)',
          letterSpacing: '-2px',
        }}>ט</div>

        {/* Title */}
        <h1 className="about-hero-title" style={{
          fontSize: 'clamp(2.8rem, 8vw, 5.5rem)',
          fontWeight: 900, letterSpacing: '-2px', lineHeight: 1.05,
          margin: '0 0 16px',
          background: `linear-gradient(135deg, #FFFFFF 0%, ${C.orange} 40%, #FFD700 70%, #FFFFFF 100%)`,
          backgroundSize: '200% auto',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          animation: 'shimmer 4s linear infinite',
          zIndex: 1,
        }}>TAZO</h1>

        <div style={{
          fontSize: 'clamp(1rem, 3vw, 1.5rem)', fontWeight: 700,
          color: C.orange, marginBottom: 12, zIndex: 1, letterSpacing: '.02em',
        }}>Super-App  •  העולמי</div>

        <p style={{
          maxWidth: 580, fontSize: 'clamp(0.95rem, 2.2vw, 1.1rem)',
          color: C.muted, lineHeight: 1.7, margin: '0 auto 36px', zIndex: 1,
        }}>
          מהשטח אל העולם — הסיפור מאחורי הפלטפורמה שמחברת אנשים, עסקים וטכנולוגיה
          ללא מתווכים, <strong style={{ color: C.text }}>בכל נקודה על הגלובוס</strong>
        </p>

        {/* Stat pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, justifyContent: 'center', zIndex: 1 }}>
          {[
            { icon: '🌍', val: 'גלובלי', sub: 'בכל נקודה' },
            { icon: '⚡', val: 'PWA', sub: 'ללא התקנה' },
            { icon: '🚕', val: '12%', sub: 'עמלה לנהגים' },
            { icon: '🤖', val: 'AI 24/7', sub: 'תמיכה מלאה' },
          ].map(s => (
            <div key={s.val} style={{
              background: 'rgba(255,255,255,0.04)', border: `1px solid ${C.border}`,
              borderRadius: 12, padding: '10px 18px', textAlign: 'center',
              backdropFilter: 'blur(10px)',
            }}>
              <div style={{ fontSize: 18 }}>{s.icon}</div>
              <div style={{ fontSize: 15, fontWeight: 800, color: C.text }}>{s.val}</div>
              <div style={{ fontSize: 10, color: C.muted }}>{s.sub}</div>
            </div>
          ))}
        </div>

        {/* Scroll arrow */}
        <div style={{
          position: 'absolute', bottom: 28, left: '50%', transform: 'translateX(-50%)',
          animation: 'float 2s ease-in-out infinite', opacity: 0.5, zIndex: 1,
        }}>
          <div style={{ width: 20, height: 20, borderRight: `2px solid ${C.orange}`, borderBottom: `2px solid ${C.orange}`, transform: 'rotate(45deg)' }} />
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════
          TAB NAV
      ══════════════════════════════════════════════════════ */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: `${C.navy}ee`, backdropFilter: 'blur(16px)',
        borderBottom: `1px solid ${C.border}`,
        padding: '0 16px',
        display: 'flex', justifyContent: 'center',
      }}>
        <div style={{ display: 'flex', gap: 4, padding: '8px 0' }}>
          {([['story', '📖 הסיפור'], ['map', '🗺️ המפה הטכנולוגית'], ['trust', '🛡️ אמון ובטיחות']] as const).map(([tab, label]) => (
            <button key={tab} className="tazo-tab-btn" onClick={() => setActiveTab(tab)} style={{
              padding: '8px 16px', borderRadius: 10, border: 'none', cursor: 'pointer',
              fontFamily: 'inherit', fontSize: 13, fontWeight: 700,
              background: activeTab === tab ? 'linear-gradient(135deg,#FF4500,#FF6B2B)' : 'transparent',
              color: activeTab === tab ? '#fff' : C.muted,
            }}>{label}</button>
          ))}
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 20px 80px' }}>

        {/* ══════════════════════════════════════════════════════
            TAB 1: STORY TIMELINE
        ══════════════════════════════════════════════════════ */}
        {activeTab === 'story' && (
          <div>
            <FadeIn>
              <SectionLabel>הסיפור מאחורי TAZO</SectionLabel>
              <h2 style={{ fontSize: 'clamp(1.5rem,4vw,2.2rem)', fontWeight: 900, marginBottom: 8, color: C.text }}>
                יש סטארט-אפים שנולדים בחדרי ישיבות.
              </h2>
              <p style={{ color: C.muted, fontSize: '1.05rem', lineHeight: 1.8, maxWidth: 720, marginBottom: 48 }}>
                ויש כאלה שנולדים מהקשבה אמיתית לאנשים ברחוב, מזיהוי כאבים אמיתיים בשטח,
                ומחזון טכנולוגי חסר פשרות. הסיפור של TAZO שייך לסוג השני.
              </p>
            </FadeIn>

            {/* Timeline */}
            <div style={{ position: 'relative' }}>
              {/* Vertical line */}
              <div style={{
                position: 'absolute', right: 23, top: 0, bottom: 0, width: 2,
                background: `linear-gradient(180deg, ${C.orange}44, ${C.border}, transparent)`,
                pointerEvents: 'none',
              }} />

              {TIMELINE.map((item, i) => (
                <FadeIn key={i} delay={i * 120}>
                  <div style={{ display: 'flex', gap: 20, marginBottom: 40, alignItems: 'flex-start' }}>
                    {/* Node */}
                    <div style={{ flexShrink: 0, position: 'relative', zIndex: 1 }}>
                      <div style={{
                        width: 48, height: 48, borderRadius: '50%',
                        background: `linear-gradient(135deg, ${item.color}33, ${item.color}11)`,
                        border: `2px solid ${item.color}66`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 20,
                        boxShadow: `0 0 20px ${item.color}33`,
                      }}>{item.icon}</div>
                      <div style={{
                        position: 'absolute', top: -8, right: -8, width: 22, height: 22,
                        borderRadius: '50%', background: item.color,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 9, fontWeight: 900, color: '#fff',
                      }}>{item.num}</div>
                    </div>
                    {/* Card */}
                    <div style={{
                      flex: 1, background: C.card, borderRadius: 14,
                      border: `1px solid ${C.border}`, padding: '20px 24px',
                    }}>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: C.text, marginBottom: 8 }}>{item.title}</h3>
                      <p style={{ color: C.muted, lineHeight: 1.75, fontSize: '0.95rem', margin: 0 }}>{item.text}</p>
                    </div>
                  </div>
                </FadeIn>
              ))}
            </div>

            {/* Name origin */}
            <FadeIn delay={200}>
              <div style={{
                marginTop: 20,
                background: 'linear-gradient(135deg, rgba(245,158,11,0.06), rgba(255,107,43,0.04))',
                border: `1px solid ${C.gold}33`, borderRadius: 16, padding: '28px 28px 24px',
              }}>
                <div style={{ fontSize: 24, marginBottom: 10 }}>☕</div>
                <h3 style={{ fontWeight: 900, fontSize: '1.15rem', color: C.gold, marginBottom: 8 }}>
                  קוריוז: איך נולד השם TAZO?
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, margin: '18px 0' }}>
                  {NAME_STEPS.map((s, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{
                        background: C.card, border: `1px solid ${s.color}66`,
                        borderRadius: 10, padding: '8px 16px',
                      }}>
                        <div style={{ fontWeight: 800, color: s.color === C.dim ? C.muted : s.color, fontSize: 13, textDecoration: s.color === C.dim ? 'line-through' : 'none' }}>{s.name}</div>
                        <div style={{ fontSize: 10, color: C.dim, marginTop: 2, maxWidth: 180 }}>{s.why}</div>
                      </div>
                      {i < NAME_STEPS.length - 1 && <span style={{ color: C.dim, fontSize: 18 }}>→</span>}
                    </div>
                  ))}
                </div>
                <p style={{ color: C.muted, fontSize: '0.9rem', lineHeight: 1.7, margin: 0 }}>
                  <em>נ.ב. — כן, אנחנו מודעים שיש חברת תה אמריקאית מפורסמת בשם הזה...
                  אין לנו שום קשר אליהם ואנחנו לא מוכרים חליטות צמחים,
                  אבל אנחנו בהחלט <strong style={{ color: C.orange }}>מרתיחים את שוק ה-Super-Apps העולמי! </strong>🔥</em>
                </p>
              </div>
            </FadeIn>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════
            TAB 2: PLATFORM MAP
        ══════════════════════════════════════════════════════ */}
        {activeTab === 'map' && (
          <div>
            <FadeIn>
              <SectionLabel>המפה הטכנולוגית הגלובלית</SectionLabel>
              <h2 style={{ fontSize: 'clamp(1.5rem,4vw,2.2rem)', fontWeight: 900, marginBottom: 12, color: C.text }}>
                4 פלטפורמות. אקוסיסטם אחד.
              </h2>
              <p style={{ color: C.muted, fontSize: '1.05rem', lineHeight: 1.8, maxWidth: 680, marginBottom: 48 }}>
                כל חלק של TAZO תוכנן לפעול עצמאית — ויחד יוצרים פרוטוקול גלובלי מאובטח
                שמחבר בין אנשים, עסקים וטכנולוגיה בלי מתווכים.
              </p>
            </FadeIn>

            <div className="about-platform-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
              {PLATFORMS.map((p, i) => (
                <FadeIn key={i} delay={i * 100}>
                  <a href={p.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none' }}>
                    <div
                      className="about-platform-card"
                      style={{
                        // @ts-ignore
                        '--card-color': p.color,
                        background: C.card,
                        border: `1px solid ${C.border}`,
                        borderRadius: 16, padding: '24px 22px',
                        cursor: 'pointer', height: '100%',
                      } as React.CSSProperties}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
                        <div style={{
                          width: 48, height: 48, borderRadius: 12, fontSize: 22,
                          background: `${p.color}18`, border: `1px solid ${p.color}44`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          flexShrink: 0,
                        }}>{p.icon}</div>
                        <div>
                          <div style={{ fontWeight: 900, fontSize: 16, color: C.text }}>{p.name}</div>
                          <div style={{ fontSize: 11, color: p.color, fontWeight: 600 }}>{p.domain}</div>
                        </div>
                      </div>
                      <div style={{ fontWeight: 700, color: C.text, fontSize: 13, marginBottom: 8 }}>{p.tagline}</div>
                      <p style={{ color: C.muted, fontSize: 13, lineHeight: 1.7, margin: 0 }}>{p.desc}</p>
                      <div style={{ marginTop: 14, fontSize: 12, color: p.color, fontWeight: 700 }}>
                        גש לאתר ← <span style={{ color: C.dim }}>({p.domain})</span>
                      </div>
                    </div>
                  </a>
                </FadeIn>
              ))}
            </div>

            {/* Global vision */}
            <FadeIn delay={300}>
              <div style={{
                marginTop: 28,
                background: `linear-gradient(135deg, rgba(139,92,246,0.08), rgba(59,130,246,0.06))`,
                border: `1px solid rgba(139,92,246,0.25)`, borderRadius: 16, padding: '28px 28px',
              }}>
                <div style={{ fontSize: 26, marginBottom: 10 }}>🌐</div>
                <h3 style={{ fontWeight: 900, fontSize: '1.15rem', color: '#a78bfa', marginBottom: 14 }}>
                  החזון הגלובלי: רוגע נפשי בכל נקודה על הגלובוס
                </h3>
                <div style={{ display: 'grid', gap: 14 }}>
                  {[
                    { icon: '✈️', label: 'ברמה הגלובלית', text: 'תייר שנוחת בעיר זרה או באי מרוחק — סורק QR, מזמין מונית שעברה אימות, ונהנה מביטחון אישי מוחלט בלי להוריד דבר.' },
                    { icon: '🏘️', label: 'ברמה המקומית', text: 'פלטפורמה לפיצה שכונתית, מנעולן, טכנאי — בידיעה שהוא מאומת, בעל רישיון בתוקף ומפוקח.' },
                    { icon: '🏝️', label: 'ייחוד TAZO', text: 'כל מקום שיש בו קליטה סלולרית ומידע ב-Google Places הופך מיידית לאזור פעיל — מקומות שלענקיות כמו Wolt וGett אין אינטרס להגיע אליהם.' },
                  ].map((item, i) => (
                    <div key={i} style={{ display: 'flex', gap: 12 }}>
                      <span style={{ fontSize: 20, flexShrink: 0, marginTop: 2 }}>{item.icon}</span>
                      <div>
                        <strong style={{ color: C.text, fontSize: 14 }}>{item.label}: </strong>
                        <span style={{ color: C.muted, fontSize: 14, lineHeight: 1.7 }}>{item.text}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </FadeIn>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════
            TAB 3: TRUST & SAFETY
        ══════════════════════════════════════════════════════ */}
        {activeTab === 'trust' && (
          <div>
            <FadeIn>
              <SectionLabel>אמון, בטיחות ותמיכה</SectionLabel>
              <h2 style={{ fontSize: 'clamp(1.5rem,4vw,2.2rem)', fontWeight: 900, marginBottom: 12, color: C.text }}>
                רשת האמון הגלובלית של TAZO
              </h2>
              <p style={{ color: C.muted, fontSize: '1.05rem', lineHeight: 1.8, maxWidth: 680, marginBottom: 40 }}>
                אני לא רק בונה קוד ושרתים — אני בונה פרוטוקול גלובלי מאובטח שמחבר בין אנשים,
                עסקים וטכנולוגיה, ללא מתווכים ובכל נקודה בעולם.
              </p>
            </FadeIn>

            <div className="about-trust-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
              {TRUST_ITEMS.map((item, i) => (
                <FadeIn key={i} delay={i * 100}>
                  <div className="about-trust-card" style={{
                    background: C.card, border: `1px solid ${C.border}`,
                    borderTop: `3px solid ${item.color}`,
                    borderRadius: 16, padding: '24px 20px',
                  }}>
                    <div style={{
                      fontSize: 28, marginBottom: 14, width: 52, height: 52,
                      background: `${item.color}15`, border: `1px solid ${item.color}44`,
                      borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>{item.icon}</div>
                    <h3 style={{ fontWeight: 800, fontSize: '1rem', color: C.text, marginBottom: 10 }}>{item.title}</h3>
                    <p style={{ color: C.muted, fontSize: '0.9rem', lineHeight: 1.75, margin: 0 }}>{item.text}</p>
                  </div>
                </FadeIn>
              ))}
            </div>

            {/* Founder card */}
            <FadeIn delay={250}>
              <div style={{
                background: `linear-gradient(135deg, ${C.card}, rgba(255,107,43,0.04))`,
                border: `1px solid ${C.orange}33`,
                borderRadius: 20, padding: '32px 28px',
              }}>
                <SectionLabel>המייסד</SectionLabel>
                <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                  <div style={{
                    width: 72, height: 72, borderRadius: '50%',
                    background: 'linear-gradient(135deg,#FF4500,#FF6B2B)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 28, fontWeight: 900, color: '#fff', flexShrink: 0,
                    boxShadow: '0 0 30px rgba(255,107,43,0.4)',
                    animation: 'glow-pulse 4s ease-in-out infinite',
                  }}>א</div>
                  <div style={{ flex: 1, minWidth: 200 }}>
                    <div style={{ fontWeight: 900, fontSize: '1.3rem', color: C.text, marginBottom: 4 }}>אריאל אביב</div>
                    <div style={{ color: C.orange, fontSize: 14, fontWeight: 600, marginBottom: 14 }}>
                      מייסד ומפתח ראשי · עוסק מורשה ח.פ/ת.ז 040978207
                    </div>
                    <p style={{ color: C.muted, lineHeight: 1.7, fontSize: '0.95rem', marginBottom: 18 }}>
                      הקמתי את TAZO כדי להחזיר את הכוח והביטחון לרחוב — מעכשיו לעכשיו,
                      ישירות מהנייד, בכל מקום על הגלובוס. מהשטח אל העולם.
                    </p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                      <a
                        href="https://wa.me/972546363350"
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: 'flex', alignItems: 'center', gap: 8,
                          background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)',
                          color: '#10B981', borderRadius: 10, padding: '9px 16px',
                          textDecoration: 'none', fontWeight: 700, fontSize: 13,
                          fontFamily: 'inherit',
                        }}
                      >📱 WhatsApp ישיר</a>
                      <a
                        href="tel:+972546363350"
                        style={{
                          display: 'flex', alignItems: 'center', gap: 8,
                          background: `rgba(255,107,43,0.1)`, border: `1px solid rgba(255,107,43,0.3)`,
                          color: C.orange, borderRadius: 10, padding: '9px 16px',
                          textDecoration: 'none', fontWeight: 700, fontSize: 13,
                          fontFamily: 'inherit',
                        }}
                      >📞 054-636-3350</a>
                    </div>
                  </div>
                </div>
              </div>
            </FadeIn>

            {/* TAZO ecosystem links */}
            <FadeIn delay={350}>
              <div style={{ marginTop: 20, textAlign: 'center' }}>
                <div style={{ color: C.dim, fontSize: 12, marginBottom: 14, letterSpacing: '.06em', textTransform: 'uppercase', fontWeight: 700 }}>
                  האקוסיסטם המלא
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, justifyContent: 'center' }}>
                  {PLATFORMS.map(p => (
                    <a key={p.domain} href={p.url} target="_blank" rel="noopener noreferrer" style={{
                      background: C.card, border: `1px solid ${C.border}`,
                      borderRadius: 10, padding: '8px 16px',
                      color: p.color, textDecoration: 'none',
                      fontSize: 13, fontWeight: 700,
                      display: 'flex', alignItems: 'center', gap: 6,
                      transition: 'border-color 200ms',
                    }}>
                      {p.icon} {p.name}
                    </a>
                  ))}
                </div>
              </div>
            </FadeIn>
          </div>
        )}
      </div>

      {/* Footer bar */}
      <div style={{
        borderTop: `1px solid ${C.border}`,
        padding: '20px', textAlign: 'center',
        color: C.dim, fontSize: 12,
        background: C.navy,
      }}>
        TAZO Super-App © {new Date().getFullYear()} · עוסק מורשה 040978207 ·{' '}
        <a href="https://tazo-app.com/trust-center" target="_blank" rel="noopener noreferrer" style={{ color: C.orange, textDecoration: 'none' }}>Trust Center</a>
        {' · '}
        <a href="tel:053-388-9859" style={{ color: C.muted, textDecoration: 'none' }}>AI Support: 053-388-9859</a>
      </div>
    </div>
  )
}
