import { useState, useEffect, useRef } from "react"
import type { AppPage } from "./App"

const AUTH_BADGE: Record<string, { label: string; color: string; bg: string }> = {
  approved:            { label: 'Sumsub מאומת ✓', color: '#22c55e', bg: 'rgba(34,197,94,0.12)'  },
  persona_completed:   { label: 'בבדיקה...', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  docs_collecting:     { label: 'בבדיקה...', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  persona_in_progress: { label: 'KYC בתהליך', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  blocked:             { label: 'חשבון חסום', color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
}
const DEFAULT_BADGE = { label: 'כניסה / הרשמה', color: '#FF6B2B', bg: 'rgba(255,107,43,0.1)' }

const LANGS = [{ code: 'he', label: 'עב' }, { code: 'en', label: 'EN' }, { code: 'es', label: 'ES' }]

interface SidebarProps {
  currentPage: AppPage
  onGoTo: (page: AppPage, plan?: string) => void
}

export default function Sidebar({ currentPage, onGoTo }: SidebarProps) {
  const [open, setOpen]               = useState(false)
  const [servicesOpen, setServicesOpen] = useState(false)
  const [lang, setLang]               = useState(() => localStorage.getItem('tazo-lang') || 'he')
  const touchStartX                   = useRef(0)

  // Body scroll lock
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  // ESC
  useEffect(() => {
    const fn = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', fn)
    return () => window.removeEventListener('keydown', fn)
  }, [])

  const onTouchStart = (e: React.TouchEvent) => { touchStartX.current = e.touches[0].clientX }
  const onTouchEnd   = (e: React.TouchEvent) => {
    if (touchStartX.current - e.changedTouches[0].clientX > 60) setOpen(false)
  }

  const setLangAndSave = (code: string) => {
    localStorage.setItem('tazo-lang', code)
    setLang(code)
    window.location.reload()
  }

  const lines: [boolean][] = [[false], [true], [false]]

  return (
    <>
      {/* ── Hamburger ── */}
      <button
        onClick={() => setOpen(v => !v)}
        aria-label={open ? 'סגור תפריט' : 'פתח תפריט'}
        style={{
          position: 'fixed', top: 12, right: 12,
          width: 44, height: 44, borderRadius: 10,
          background: open ? 'rgba(255,107,43,0.15)' : 'rgba(26,26,26,0.92)',
          border: open ? '1px solid rgba(255,107,43,0.35)' : '1px solid rgba(255,255,255,0.1)',
          backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)',
          cursor: 'pointer', zIndex: 10012,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'all 220ms ease',
        }}
      >
        <span style={{ display: 'block', position: 'relative', width: 18, height: 14 }}>
          {[0, 1, 2].map(i => (
            <span key={i} style={{
              position: 'absolute', left: 0, top: open ? 6 : [0, 6, 12][i],
              width: 18, height: 2, borderRadius: 2, background: '#e6edf3',
              transformOrigin: 'center',
              transition: 'transform 220ms ease, opacity 180ms ease, top 220ms ease',
              transform: open ? (i === 0 ? 'rotate(45deg)' : i === 2 ? 'rotate(-45deg)' : 'none') : 'none',
              opacity: open && i === 1 ? 0 : 1,
            }} />
          ))}
        </span>
      </button>

      {/* Backdrop */}
      <div
        onClick={() => setOpen(false)}
        style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(3px)', WebkitBackdropFilter: 'blur(3px)',
          zIndex: 10010, opacity: open ? 1 : 0, pointerEvents: open ? 'all' : 'none',
          transition: 'opacity 280ms ease',
        }}
      />

      {/* Panel */}
      <div
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
        style={{
          position: 'fixed', top: 0, right: 0, bottom: 0,
          width: 'min(320px, 90vw)',
          background: 'linear-gradient(180deg,#1e1e1e 0%,#1a1a1a 100%)',
          borderLeft: '1px solid #2d2d2d',
          zIndex: 10011,
          transform: open ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 300ms cubic-bezier(0.22,1,0.36,1)',
          boxShadow: open ? '-24px 0 60px rgba(0,0,0,.7)' : 'none',
          display: 'flex', flexDirection: 'column', overflowY: 'auto',
          fontFamily: "'Heebo','Segoe UI',system-ui,sans-serif", direction: 'rtl',
        }}
      >
        {/* Close btn */}
        <button
          onClick={() => setOpen(false)}
          aria-label="סגור"
          style={{
            position: 'absolute', top: 14, left: 14,
            width: 32, height: 32, borderRadius: 8,
            background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
            color: '#9ca3af', cursor: 'pointer', fontSize: 16,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >✕</button>

        {/* ── HEADER ── */}
        <div style={{ padding: '24px 20px 18px', background: 'rgba(255,69,0,0.03)', borderBottom: '1px solid #252525' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <div style={{
              width: 48, height: 48, borderRadius: '50%',
              background: 'linear-gradient(135deg,#FF4500,#FF6B2B)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 22, fontWeight: 900, color: '#fff', flexShrink: 0,
              boxShadow: '0 4px 12px rgba(255,69,0,0.3)',
            }}>T</div>
            <div>
              <div style={{ fontSize: 17, fontWeight: 800, color: '#f5f5f5', letterSpacing: '.02em' }}>
                TAZO<span style={{ color: '#FF6B2B' }}>.</span>web
              </div>
              <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>בניית נוכחות דיגיטלית</div>
            </div>
          </div>

          {/* CTA to join */}
          <button
            onClick={() => { onGoTo('intake'); setOpen(false) }}
            style={{
              width: '100%', padding: '10px 16px',
              background: 'linear-gradient(135deg,#FF4500,#FF6B2B)', border: 'none',
              color: '#fff', borderRadius: 8, cursor: 'pointer',
              fontSize: 13, fontWeight: 700, fontFamily: 'inherit',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              boxShadow: '0 4px 12px rgba(255,69,0,0.25)',
            }}
          >🚀 בנה אתר עכשיו →</button>
        </div>

        {/* ── SECTION 1: Navigation ── */}
        <SectionBlock label="🧭 ניווט ראשי">
          <NavItem icon="🏠" label="קניון TAZO" sublabel="כל המוצרים והשירותים" active={currentPage === 'marketplace'} onClick={() => { onGoTo('marketplace'); setOpen(false) }} />
          <NavItem icon="🏢" label="פתיחת עסק דיגיטלי" sublabel="בניית עמוד עסק מקצועי" active={currentPage === 'home'} onClick={() => { onGoTo('home'); setOpen(false) }} />
          <NavItem icon="📝" label="טופס רישום" sublabel="התחל את התהליך" active={currentPage === 'intake'} onClick={() => { onGoTo('intake'); setOpen(false) }} />
          <NavItem icon="📊" label="סטטוס הגשה" sublabel="מעקב אחר הבקשה שלך" active={currentPage === 'status'} onClick={() => { onGoTo('status'); setOpen(false) }} />
        </SectionBlock>

        <Divider />

        {/* ── SECTION 2: TAZO Consumer ── */}
        <SectionBlock label="🛍️ TAZO App — לקוחות">
          <NavItem icon="🚕" label="הזמן מונית / שליח" onClick={() => window.open('https://tazo-go.com','_blank')} cta />
          <NavItem
            icon="🛠️" label="שירותים מיוחדים" sublabel="Auto · Events · Health"
            expandable expanded={servicesOpen} onToggle={() => setServicesOpen(v => !v)}
          />
          {servicesOpen && (
            <div style={{ paddingRight: 30, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <SubItem icon="🔧" label="Tazo Auto — מוסכים" onClick={() => window.open('https://tazo-go.com/services','_blank')} />
              <SubItem icon="🎟️" label="Tazo Events — כרטיסים" onClick={() => window.open('https://tazo-go.com/events','_blank')} />
              <SubItem icon="🏥" label="Tazo Health" onClick={() => window.open('https://tazo-go.com/health','_blank')} />
            </div>
          )}
        </SectionBlock>

        <Divider />

        {/* ── SECTION 3: Business ── */}
        <SectionBlock label="🏢 TAZO Sync — עסקים">
          <NavItem icon="🏪" label="ניהול עסק דיגיטלי" sublabel="לוח בקרה · מוצרים · הזמנות" onClick={() => window.open('https://tazo-sync.com','_blank')} cta />
          <NavItem icon="📦" label="Shadow Stores — תבע חנות" sublabel="כבר קיים ב-Google?" onClick={() => window.open('https://tazo-sync.com/claim','_blank')} />
        </SectionBlock>

        <Divider />

        {/* ── SECTION 4: Driver ── */}
        <SectionBlock label="🚗 TAZO Go — נהגים">
          <NavItem icon="🛵" label="הצטרף כנהג / שליח" sublabel="תהליך Uber-Pilot" onClick={() => window.open('https://tazo-go.com/driver/join','_blank')} cta />
        </SectionBlock>

        <Divider />

        {/* ── SECTION 5: TAZO Family ── */}
        <SectionBlock label="🌐 TAZO Family">
          <NavItem icon="🌐" label="TAZO Portal" sublabel="tazo-app.com" onClick={() => window.open('https://tazo-app.com','_blank')} />
          <NavItem icon="🚗" label="TAZO Go — נסיעות" sublabel="tazo-go.com" onClick={() => window.open('https://tazo-go.com','_blank')} />
          <NavItem icon="🔄" label="TAZO Sync — עסקים" sublabel="tazo-sync.com" onClick={() => window.open('https://tazo-sync.com','_blank')} />
        </SectionBlock>

        <Divider />

        {/* ── FOOTER ── */}
        <SectionBlock label="⚙️ הגדרות ותמיכה" extraStyle={{ marginTop: 'auto' }}>
          <div style={{ padding: '4px 10px 8px' }}>
            <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 6 }}>🌐 שפה ואזור</div>
            <div style={{ display: 'flex', gap: 6 }}>
              {LANGS.map(l => (
                <button key={l.code} onClick={() => setLangAndSave(l.code)} style={{
                  padding: '5px 14px', borderRadius: 6, cursor: 'pointer',
                  fontSize: 12, fontWeight: 700, fontFamily: 'inherit',
                  background: lang === l.code ? 'linear-gradient(135deg,#FF4500,#FF6B2B)' : '#242424',
                  color: lang === l.code ? '#fff' : '#9ca3af',
                  border: lang === l.code ? 'none' : '1px solid #2e2e2e',
                  transition: 'all 180ms ease',
                }}>{l.label}</button>
              ))}
            </div>
          </div>
          <NavItem icon="❓" label="מרכז תמיכה ו-FAQ" sublabel="30 תרחישים" onClick={() => window.open('https://tazo-web.com/faq','_blank')} />
          <NavItem icon="💬" label="צור קשר ב-WhatsApp" onClick={() => window.open('https://wa.me/972501234567','_blank')} />
          <NavItem icon="🔒" label="מדיניות פרטיות" onClick={() => window.open('https://tazo-web.com/privacy','_blank')} />
        </SectionBlock>
      </div>
    </>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SectionBlock({ label, children, extraStyle }: { label: string; children: React.ReactNode; extraStyle?: React.CSSProperties }) {
  return (
    <div style={{ padding: '12px 12px 8px', ...extraStyle }}>
      <div style={{ fontSize: 10, fontWeight: 800, color: '#6b7280', letterSpacing: '.08em', textTransform: 'uppercase', paddingRight: 4, marginBottom: 6 }}>{label}</div>
      {children}
    </div>
  )
}

const navBase: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 10, padding: '9px 10px',
  borderRadius: 8, cursor: 'pointer', width: '100%',
  border: 'none', background: 'transparent', fontFamily: 'inherit', textAlign: 'right',
  transition: 'background 150ms ease',
}

function NavItem({ icon, label, sublabel, cta, active, expandable, expanded, onToggle, onClick }: {
  icon: string; label: string; sublabel?: string; cta?: boolean; active?: boolean
  expandable?: boolean; expanded?: boolean; onToggle?: () => void; onClick?: () => void
}) {
  const [hov, setHov] = useState(false)
  const handleClick = expandable ? onToggle : onClick
  const isActive = active && !expandable
  return (
    <button
      onClick={handleClick}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        ...navBase,
        background: isActive ? 'rgba(255,107,43,0.12)' : hov ? (cta ? 'rgba(255,107,43,0.08)' : 'rgba(255,255,255,0.04)') : 'transparent',
        borderRight: isActive ? '3px solid #FF6B2B' : '3px solid transparent',
        justifyContent: expandable ? 'space-between' : 'flex-start',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1 }}>
        <span style={{ fontSize: 17, flexShrink: 0 }}>{icon}</span>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: isActive ? '#FF6B2B' : (cta ? '#FF6B2B' : '#e6edf3') }}>{label}</div>
          {sublabel && <div style={{ fontSize: 10, color: '#6b7280', marginTop: 1 }}>{sublabel}</div>}
        </div>
      </div>
      {cta && <span style={{ color: '#FF6B2B', fontSize: 12 }}>→</span>}
      {expandable && <span style={{ color: '#6b7280', fontSize: 10, transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 200ms' }}>▼</span>}
    </button>
  )
}

function SubItem({ icon, label, onClick }: { icon: string; label: string; onClick: () => void }) {
  const [hov, setHov] = useState(false)
  return (
    <button onClick={onClick} onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{ ...navBase, padding: '6px 8px', background: hov ? 'rgba(255,255,255,0.04)' : 'transparent' }}
    >
      <span style={{ fontSize: 14 }}>{icon}</span>
      <span style={{ fontSize: 12, color: '#9ca3af' }}>{label}</span>
    </button>
  )
}

function Divider() {
  return <div style={{ height: 1, background: '#252525', margin: '4px 12px' }} />
}
