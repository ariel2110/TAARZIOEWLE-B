import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip as ReTooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card, SectionTitle, InfoTip } from '../components/ui';
import { useLang } from '../i18n';
import { Digest, Health, Snapshot, Business, Approval, getSnapshot, getDigest, getHealth, getBusinesses, getApprovals, Notification, getNotifications } from '../services/queries';

const CHART_COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#3b82f6', '#ef4444', '#8b5cf6'];

export default function OverviewPage() {
  const [snapshot, setSnapshot] = useState<Snapshot>({});
  const [digest, setDigest] = useState<Digest | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const { t } = useLang();

  useEffect(() => {
    Promise.all([getSnapshot(), getDigest(), getHealth(), getBusinesses(), getApprovals(), getNotifications(10)]).then(([s, d, h, b, a, n]) => {
      setSnapshot(s); setDigest(d); setHealth(h); setBusinesses(b); setApprovals(a); setNotifications(n);
    }).catch(console.error);
  }, []);

  const chartData = Object.entries(snapshot).map(([k, v]) => ({ name: k.replace(/_/g, ' '), value: v }));

  return (
    <div className="grid">
      <div>
        <SectionTitle>{t('overview')}</SectionTitle>
        <div className="cards">
          {Object.entries(snapshot).map(([k, v]) => (
            <Card key={k}><div className="muted" style={{ textTransform: 'uppercase' }}>{k}</div><div style={{ fontSize: 24, fontWeight: 700 }}>{v}</div></Card>
          ))}
        </div>
      </div>

      {/* KPI Chart */}
      {chartData.length > 0 && (
        <Card>
          <SectionTitle>📊 {t('kpi_chart') || 'תרשים KPI'} <InfoTip text="תצוגה גרפית של מדדי המערכת — לידים, עסקים, אישורים ותשלומים" /></SectionTitle>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 4 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <ReTooltip />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {chartData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      <div className="two-col">
        <Card dark>
          <SectionTitle>{t('ceo_digest')} <InfoTip text="תקציר יומי אוטומטי — מנהל AI מסכם את מצב המערכת ומציע פעולות עדיפות" /></SectionTitle>
          <p>{digest?.executive_summary}</p>
          <ul>{digest?.recommended_actions?.map(x => <li key={x}>{x}</li>)}</ul>
        </Card>
        <Card>
          <SectionTitle>{t('system_health')} <InfoTip text="בדיקת תקינות — חיבור לבסיס נתונים, מצב שירותים פנימיים" /></SectionTitle>
          <p><strong>{t('status')}:</strong> {health?.overall_status || health?.status}</p>
          <p><strong>{t('database')}:</strong> {health?.database_ok ? t('db_connected') : t('db_unknown')}</p>
          <ul>{health?.drivers?.map(x => <li key={x}>{x}</li>)}</ul>
        </Card>
      </div>
      <div className="two-col">
        <Card>
          <SectionTitle>{t('businesses')}</SectionTitle>
          <div className="table-list">
            {businesses.slice(0, 6).map(b => (
              <div key={b.id}><strong>{b.name}</strong><div className="muted">{b.city || '—'} · {b.category || '—'} · {b.status}</div></div>
            ))}
          </div>
        </Card>
        <Card>
          <SectionTitle>{t('pending_approvals')}</SectionTitle>
          <div className="table-list">
            {approvals.filter(a => ['proposed', 'under_review'].includes(a.status)).slice(0, 6).map(a => (
              <div key={a.id}><strong>{a.title}</strong><div className="muted">{a.approval_type} · {a.status}</div></div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent Notifications */}
      {notifications.length > 0 && (
        <Card>
          <SectionTitle>🔔 {t('notifications') || 'התראות אחרונות'} <InfoTip text="אירועים חשובים — דמו נצפה, תשלום אושר, תגובת WhatsApp" /></SectionTitle>
          <div className="table-list">
            {notifications.map(n => (
              <div key={n.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <span style={{ marginLeft: 6 }}>{n.event === 'demo_viewed' ? '👁️' : n.event === 'payment_confirmed' ? '💳' : '📣'}</span>
                  <span>{n.summary}</span>
                </div>
                <span className="muted" style={{ fontSize: 11, whiteSpace: 'nowrap' }}>{n.created_at ? new Date(n.created_at).toLocaleString('he-IL') : ''}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

