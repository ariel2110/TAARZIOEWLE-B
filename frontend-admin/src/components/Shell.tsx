import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useLang, useTheme } from '../i18n';
import { Tooltip } from './ui';
import { HelpPanel } from './HelpPanel';

type NavItem = { to: string; end?: boolean; icon: string; label: string; tip: string };
type NavGroup = { id: string; label: string; icon: string; items: NavItem[] };

const NAV_GROUPS: NavGroup[] = [
  {
    id: 'overview', label: 'סקירה', icon: '📊',
    items: [
      { to: '/', end: true, icon: '📊', label: 'סקירה כללית', tip: 'מצב כללי של המערכת — מדדים, תקציר מנכ"ל ובריאות שירות' },
    ],
  },
  {
    id: 'leads', label: 'לידים ועסקים', icon: '🎯',
    items: [
      { to: '/leads', icon: '🎯', label: 'לידים', tip: 'עסקים פוטנציאלים שנאספו — סנן, כשר והמר לעסק' },
      { to: '/businesses', icon: '🏢', label: 'עסקים', tip: 'עסקים פעילים במערכת — נהל סטטוס, שלח פנייה, צור דראפט' },
      { to: '/customers', icon: '👥', label: 'לקוחות', tip: 'לקוחות פעילים עם גישה לפורטל לקוח' },
    ],
  },
  {
    id: 'acquisition', label: 'גיוס ופנייה', icon: '🔍',
    items: [
      { to: '/enrich', icon: '🔍', label: 'איסוף נתונים', tip: 'חפש עסקים דרך Google Places וייבא לרשימת הלידים' },
      { to: '/demos', icon: '📱', label: 'אתרי דמו', tip: 'שלח אתר דמו ייחודי לעסק דרך WhatsApp וצפה בסטטוס' },
      { to: '/targeting', icon: '📡', label: 'טירגוט', tip: 'פרופילי חיפוש וקמפיינים — שייך לידים ועסקים לקמפיין' },
    ],
  },
  {
    id: 'build', label: 'בנייה ומכירה', icon: '🏗️',
    items: [
      { to: '/draft-sites', icon: '📝', label: 'דראפטים', tip: 'אתרים שנוצרו ומחכים לתשלום — תצוגה מקדימה ועדכון' },
      { to: '/payments', icon: '💳', label: 'תשלומים', tip: 'עקוב אחר תשלומים ממתינים ואשר הפעלה של אתרים' },
    ],
  },
  {
    id: 'management', label: 'ניהול ו-AI', icon: '⚙️',
    items: [
      { to: '/queues', icon: '⏳', label: 'תורים', tip: 'תצוגת עדיפויות — כל מה שממתין לפעולה מסודר בתורים' },
      { to: '/approvals', icon: '✅', label: 'אישורים', tip: 'הצעות שינוי שדורשות אישור ידני לפני ביצוע' },
      { to: '/ceo', icon: '🧠', label: 'מרכז מנכ"ל', tip: 'תכנון אסטרטגי יומי + Grok AI מנכ"ל מציע מהלכים' },
      { to: '/feedback', icon: '💬', label: 'פידבק', tip: 'רישום פידבק פנימי — שיפורים, תובנות וניתוח AI' },
      { to: '/security', icon: '🛡️', label: 'אבטחה', tip: 'ניטור כניסות חשודות, חסימות ורשימת חשד' },
      { to: '/whatsapp', icon: '📱', label: 'WhatsApp', tip: 'חיבור/ניתוק WhatsApp, QR, ואישור הודעות' },
      { to: '/agents', icon: '📡', label: 'סוכני AI', tip: 'מעקב עלויות API בזמן אמת — Claude, GPT, Gemini, Grok' },
    ],
  },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const { lang, toggle, t } = useLang();
  const { theme, toggleTheme } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  const handleLogout = () => {
    localStorage.removeItem('admin_access_token');
    navigate('/login', { replace: true });
  };

  const toggleGroup = (id: string) =>
    setCollapsed(prev => ({ ...prev, [id]: !prev[id] }));

  const closeOnMobile = () => setMobileOpen(false);

  const sidebarContent = (
    <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '100%' }}>
      <div>
        {/* Logo + close button (mobile) */}
        <div style={{ padding: '4px 0 16px', borderBottom: '1px solid var(--border)', marginBottom: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: -0.5 }}>🏙️ SiteNest</div>
            <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>לוח בקרה · v27</div>
          </div>
          <button
            className="sidebar-close-btn"
            onClick={closeOnMobile}
            aria-label="סגור תפריט"
            style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', color: 'var(--text-muted)', padding: 4 }}
          >✕</button>
        </div>

        {/* Grouped nav */}
        <nav>
          {NAV_GROUPS.map(group => {
            const isOpen = !collapsed[group.id];
            return (
              <div key={group.id} className="nav-group">
                {/* Skip the group header for "overview" (single item) */}
                {group.items.length > 1 ? (
                  <button
                    className="nav-group-header"
                    onClick={() => toggleGroup(group.id)}
                    aria-expanded={isOpen}
                  >
                    <span style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 13, fontWeight: 600 }}>
                      <span>{group.icon}</span>
                      <span>{group.label}</span>
                    </span>
                    <span style={{ fontSize: 11, transition: 'transform 0.2s', display: 'inline-block', transform: isOpen ? 'rotate(90deg)' : 'rotate(0deg)' }}>▶</span>
                  </button>
                ) : null}
                {(group.items.length === 1 || isOpen) && (
                  <div className={`nav-group-items${group.items.length > 1 ? ' indented' : ''}`}>
                    {group.items.map(item => (
                      <Tooltip key={item.to} text={item.tip} position="right">
                        <NavLink
                          to={item.to}
                          end={item.end}
                          className={({ isActive }) => isActive ? 'active' : ''}
                          style={{ display: 'flex', alignItems: 'center', gap: 10 }}
                          onClick={closeOnMobile}
                        >
                          <span style={{ fontSize: 15, width: 20, textAlign: 'center' }}>{item.icon}</span>
                          <span style={{ fontSize: 14 }}>{item.label}</span>
                        </NavLink>
                      </Tooltip>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </div>

      {/* Bottom controls */}
      <div>
        <button
          onClick={toggle}
          style={{ margin: '8px 0 4px', padding: '8px 12px', background: '#f3f4f6', color: '#374151', border: '1px solid #e5e7eb', borderRadius: 10, cursor: 'pointer', fontWeight: 600, fontSize: 13, display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}
        >
          <span>🌐</span> {t('switch_lang')}
        </button>
        <button
          onClick={toggleTheme}
          style={{ margin: '4px 0 4px', padding: '8px 12px', background: 'var(--bg)', color: 'var(--text)', border: '1px solid var(--border)', borderRadius: 10, cursor: 'pointer', fontWeight: 600, fontSize: 13, display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}
        >
          <span>{theme === 'dark' ? '☀️' : '🌙'}</span>
          {theme === 'dark' ? (lang === 'he' ? 'מצב בהיר' : 'Light mode') : (lang === 'he' ? 'מצב כהה' : 'Dark mode')}
        </button>
        <button
          onClick={handleLogout}
          style={{ margin: '4px 0 16px', padding: '10px 12px', background: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: 10, cursor: 'pointer', fontWeight: 500, fontSize: 14, display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}
        >
          <span>🚪</span> {lang === 'he' ? 'יציאה' : 'Logout'}
        </button>
      </div>
    </div>
  );

  return (
    <div className="app-shell" dir={lang === 'he' ? 'rtl' : 'ltr'}>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={closeOnMobile}
          aria-hidden="true"
        />
      )}

      {/* Sidebar — desktop: in-grid, mobile: fixed overlay */}
      <aside className={`sidebar${mobileOpen ? ' sidebar-open' : ''}`}>
        {sidebarContent}
      </aside>

      {/* Main content */}
      <main className="main" dir={lang === 'he' ? 'rtl' : 'ltr'}>
        {/* Mobile top bar */}
        <div className="mobile-topbar">
          <button
            className="hamburger"
            onClick={() => setMobileOpen(true)}
            aria-label="פתח תפריט"
          >
            <span /><span /><span />
          </button>
          <span style={{ fontWeight: 700, fontSize: 18 }}>🏙️ SiteNest</span>
          <span />
        </div>
        {children}
      </main>
      <HelpPanel />
    </div>
  );
}

