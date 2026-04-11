import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useLang } from '../i18n';
import { Tooltip } from './ui';

const NAV_ITEMS = [
  { to: '/', end: true, icon: '📊', label: 'סקירה כללית',  tip: 'מצב כללי של המערכת — מדדים, תקציר מנכ"ל ובריאות שירות' },
  { to: '/leads', icon: '🎯', label: 'לידים',              tip: 'עסקים פוטנציאלים שנאספו — סנן, כשר והמר לעסק' },
  { to: '/businesses', icon: '🏢', label: 'עסקים',         tip: 'עסקים פעילים במערכת — נהל סטטוס, שלח פנייה, צור דראפט' },
  { to: '/enrich', icon: '🔍', label: 'איסוף נתונים',      tip: 'חפש עסקים דרך Google Places וייבא לרשימת הלידים' },
  { to: '/demos', icon: '📱', label: 'אתרי דמו',           tip: 'שלח אתר דמו ייחודי לעסק דרך WhatsApp וצפה בסטטוס' },
  { to: '/draft-sites', icon: '📝', label: 'דראפטים',      tip: 'אתרים שנוצרו ומחכים לתשלום — תצוגה מקדימה ועדכון' },
  { to: '/payments', icon: '💳', label: 'תשלומים',         tip: 'עקוב אחר תשלומים ממתינים ואשר הפעלה של אתרים' },
  { to: '/customers', icon: '👥', label: 'לקוחות',         tip: 'לקוחות פעילים עם גישה לפורטל לקוח' },
  { to: '/targeting', icon: '📡', label: 'טירגוט',         tip: 'פרופילי חיפוש וקמפיינים — שייך לידים ועסקים לקמפיין' },
  { to: '/queues', icon: '⏳', label: 'תורים',              tip: 'תצוגת עדיפויות — כל מה שממתין לפעולה מסודר בתורים' },
  { to: '/approvals', icon: '✅', label: 'אישורים',         tip: 'הצעות שינוי שדורשות אישור ידני לפני ביצוע' },
  { to: '/ceo', icon: '🧠', label: 'מרכז מנכ"ל',           tip: 'תכנון אסטרטגי יומי + Grok AI מנכ"ל מציע מהלכים' },
  { to: '/feedback', icon: '💬', label: 'פידבק',           tip: 'רישום פידבק פנימי — שיפורים, תובנות וניתוח AI' },
  { to: '/security', icon: '🛡️', label: 'אבטחה',          tip: 'ניטור כניסות חשודות, חסימות ורשימת חשד' },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const { lang, toggle, t } = useLang();

  const handleLogout = () => {
    localStorage.removeItem('admin_access_token');
    navigate('/login', { replace: true });
  };

  return (
    <div className="app-shell" dir={lang === 'he' ? 'rtl' : 'ltr'}>
      <aside className="sidebar" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '100vh' }}>
        <div>
          <div style={{ padding: '4px 0 16px', borderBottom: '1px solid #f0f0f0', marginBottom: 12 }}>
            <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: -0.5 }}>🏙️ SiteNest</div>
            <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>לוח בקרה · v27</div>
          </div>
          <nav className="nav">
            {NAV_ITEMS.map(item => (
              <Tooltip key={item.to} text={item.tip} position="right">
                <NavLink
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => isActive ? 'active' : ''}
                  style={{ display: 'flex', alignItems: 'center', gap: 10 }}
                >
                  <span style={{ fontSize: 16, width: 22, textAlign: 'center' }}>{item.icon}</span>
                  <span>{item.label}</span>
                </NavLink>
              </Tooltip>
            ))}
          </nav>
        </div>
        <div>
          <button
            onClick={toggle}
            style={{ margin: '8px 0 4px', padding: '8px 12px', background: '#f3f4f6', color: '#374151', border: '1px solid #e5e7eb', borderRadius: 10, cursor: 'pointer', fontWeight: 600, fontSize: 13, display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}
            title="עבור בין ממשק עברי לאנגלי"
          >
            <span>🌐</span> {t('switch_lang')}
          </button>
          <button
            onClick={handleLogout}
            style={{ margin: '4px 0 16px', padding: '10px 12px', background: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: 10, cursor: 'pointer', fontWeight: 500, fontSize: 14, display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}
            title="התנתק מהממשק"
          >
            <span>🚪</span> {lang === 'he' ? 'יציאה' : 'Logout'}
          </button>
        </div>
      </aside>
      <main className="main" dir={lang === 'he' ? 'rtl' : 'ltr'}>{children}</main>
    </div>
  );
}
