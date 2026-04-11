import { NavLink, useNavigate } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/', end: true, icon: '📊', label: 'סקירה כללית' },
  { to: '/leads', icon: '🎯', label: 'לידים' },
  { to: '/businesses', icon: '🏢', label: 'עסקים' },
  { to: '/enrich', icon: '🔍', label: 'איסוף נתונים' },
  { to: '/demos', icon: '📱', label: 'אתרי דמו' },
  { to: '/draft-sites', icon: '📝', label: 'דראפטים' },
  { to: '/payments', icon: '💳', label: 'תשלומים' },
  { to: '/customers', icon: '👥', label: 'לקוחות' },
  { to: '/targeting', icon: '📡', label: 'טירגוט' },
  { to: '/queues', icon: '⏳', label: 'תורים' },
  { to: '/approvals', icon: '✅', label: 'אישורים' },
  { to: '/ceo', icon: '🧠', label: 'מרכז מנכ"ל' },
  { to: '/feedback', icon: '💬', label: 'פידבק' },
  { to: '/security', icon: '🛡️', label: 'אבטחה' },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('admin_access_token');
    navigate('/login', { replace: true });
  };

  return (
    <div className="app-shell" dir="rtl">
      <aside className="sidebar" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '100vh' }}>
        <div>
          <div style={{ padding: '4px 0 16px', borderBottom: '1px solid #f0f0f0', marginBottom: 12 }}>
            <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: -0.5 }}>🏙️ SiteNest</div>
            <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>לוח בקרה · v27</div>
          </div>
          <nav className="nav">
            {NAV_ITEMS.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => isActive ? 'active' : ''}
                style={{ display: 'flex', alignItems: 'center', gap: 10 }}
              >
                <span style={{ fontSize: 16, width: 22, textAlign: 'center' }}>{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
        <button
          onClick={handleLogout}
          style={{ margin: '16px 0', padding: '10px 12px', background: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: 10, cursor: 'pointer', fontWeight: 500, fontSize: 14, display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}
        >
          <span>🚪</span> יציאה
        </button>
      </aside>
      <main className="main" dir="rtl">{children}</main>
    </div>
  );
}
