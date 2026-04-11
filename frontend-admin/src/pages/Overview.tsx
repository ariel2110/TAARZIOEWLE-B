import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip as ReTooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card, SectionTitle, InfoTip } from '../components/ui';
import { useLang } from '../i18n';
import { Digest, Health, Snapshot, Business, Approval, getSnapshot, getDigest, getHealth, getBusinesses, getApprovals, Notification, getNotifications } from '../services/queries';

const CHART_COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#3b82f6', '#ef4444', '#8b5cf6'];

const SNAPSHOT_LABELS: Record<string, string> = {
  leads: 'לידים',
  qualified_leads: 'לידים מוסמכים',
  businesses: 'עסקים',
  draft_sites: 'אתרי טיוטה',
  payments_confirmed: 'תשלומים אושרו',
  approvals_pending: 'אישורים ממתינים',
};

export default function OverviewPage() {
  const [snapshot, setSnapshot] = useState<Snapshot>({});
  const [digest, setDigest] = useState<Digest | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const { t } = useLang();

  useEffect(() => {
    setLoading(true);
    Promise.all([getSnapshot(), getDigest(), getHealth(), getBusinesses(), getApprovals(), getNotifications(10)]).then(([s, d, h, b, a, n]) => {
      setSnapshot(s); setDigest(d); setHealth(h); setBusinesses(b); setApprovals(a); setNotifications(n);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const chartData = Object.entries(snapshot).map(([k, v]) => ({ name: SNAPSHOT_LABELS[k] || k.replace(/_/g, ' '), value: v }));

  return (
    <div className="grid">
      {/* ── KPI Cards ─────────────────────────────── */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <SectionTitle>{t('overview')}</SectionTitle>
          {loading && <span style={{ fontSize: 12, color: '#9ca3af' }}>⏳ טוען נתונים…</span>}
        </div>
        <div className="cards">
          {Object.entries(snapshot).length === 0 && !loading && (
            <p className="muted" style={{ gridColumn: '1/-1' }}>אין נתוני מערכת — ייתכן בעיית חיבור לשרת.</p>
          )}
          {Object.entries(snapshot).map(([k, v]) => (
            <Card key={k}>
              <div className="muted" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                {SNAPSHOT_LABELS[k] || k.replace(/_/g, ' ')}
              </div>
              <div style={{ fontSize: 28, fontWeight: 700, marginTop: 4 }}>{v}</div>
            </Card>
          ))}
        </div>
      </div>

      {/* ── What's Needed / Action Alerts ─────────── */}
      {digest?.what_needed && digest.what_needed.length > 0 && (
        <div style={{ borderLeft: '4px solid #f59e0b', background: '#fffbeb', borderRadius: 12, padding: '16px 20px', marginBottom: 8 }}>
          <SectionTitle>⚠️ נדרשת פעולה עכשיו</SectionTitle>
          <div style={{ display: 'grid', gap: 8 }}>
            {digest.what_needed.map((item, i) => (
              <div key={i} style={{ fontSize: 14, fontWeight: 600, color: '#92400e', padding: '6px 10px', background: '#fef3c7', borderRadius: 8 }}>
                {item}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── KPI Chart ─────────────────────────────── */}
      {chartData.length > 0 && (
        <Card>
          <SectionTitle>📊 תרשים KPI <InfoTip text="תצוגה גרפית של מדדי המערכת — לידים, עסקים, אישורים ותשלומים" /></SectionTitle>
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
        {/* ── CEO Digest ────────────────────────────── */}
        <Card dark>
          <SectionTitle>
            🧠 {t('ceo_digest')}
            <InfoTip text="תקציר יומי אוטומטי — מנהל AI מסכם את מצב המערכת ומציע פעולות עדיפות" />
            {digest?.generated_at && (
              <span style={{ fontSize: 11, fontWeight: 400, marginRight: 10, color: '#9ca3af' }}>עודכן: {digest.generated_at}</span>
            )}
          </SectionTitle>

          {/* System counters inline */}
          {digest && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 14 }}>
              {[
                { label: 'עסקים', val: digest.total_businesses },
                { label: 'לידים', val: digest.total_leads },
                { label: 'לקוחות', val: digest.total_customers },
                { label: 'דמו פעיל', val: digest.expiring_drafts },
                { label: 'תשלומים אושרו', val: digest.payments_confirmed },
              ].filter(x => x.val !== undefined).map(({ label, val }) => (
                <span key={label} style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 20, padding: '3px 10px', fontSize: 12 }}>
                  <strong>{val}</strong> {label}
                </span>
              ))}
            </div>
          )}

          {/* Executive summary */}
          {digest?.executive_summary ? (
            <p style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 14, whiteSpace: 'pre-line' }}>{digest.executive_summary}</p>
          ) : !loading && (
            <p className="muted" style={{ marginBottom: 14 }}>לא ניתן לטעון סיכום — בדוק חיבור לשרת.</p>
          )}

          {/* 🔴 מה לתקן עכשיו */}
          {digest?.pressure_notes && digest.pressure_notes.some(n => !n.startsWith('0 ')) && (
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#ef4444', marginBottom: 6, letterSpacing: 0.3 }}>🔴 לתיקון עכשיו</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {digest.pressure_notes.filter(n => !n.startsWith('0 ')).map(n => (
                  <span key={n} style={{ background: '#fee2e2', color: '#991b1b', borderRadius: 20, padding: '3px 10px', fontSize: 12, fontWeight: 600 }}>{n}</span>
                ))}
              </div>
            </div>
          )}

          {/* ✅ לוג פעולות אחרון */}
          {digest?.recent_fixes && digest.recent_fixes.length > 0 && (
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#16a34a', marginBottom: 6, letterSpacing: 0.3 }}>✅ פעולות אחרונות</div>
              <div style={{ display: 'grid', gap: 4 }}>
                {digest.recent_fixes.map((f, i) => (
                  <div key={i} style={{ display: 'flex', gap: 6, alignItems: 'baseline', fontSize: 13 }}>
                    <span style={{ background: '#dcfce7', color: '#166534', borderRadius: 4, padding: '1px 6px', fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap' }}>{f.label}</span>
                    {f.timestamp && <span style={{ fontSize: 11, color: '#9ca3af', whiteSpace: 'nowrap' }}>{f.timestamp}</span>}
                    <span className="muted" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '100%' }}>{f.summary}</span>
                  </div>
                ))}
                {digest.recent_fixes.length === 0 && <span className="muted" style={{ fontSize: 13 }}>אין פעולות אחרונות עדיין.</span>}
              </div>
            </div>
          )}

          {/* 📋 פעולות מומלצות */}
          {digest?.recommended_actions && digest.recommended_actions.length > 0 && (
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#6366f1', marginBottom: 6, letterSpacing: 0.3 }}>📋 פעולות מומלצות</div>
              <ul style={{ margin: 0, paddingRight: 18, display: 'grid', gap: 4 }}>
                {digest.recommended_actions.map(x => <li key={x} style={{ fontSize: 13, lineHeight: 1.5 }}>{x}</li>)}
              </ul>
            </div>
          )}
        </Card>

        {/* ── System Health ─────────────────────────── */}
        <Card>
          <SectionTitle>{t('system_health')} <InfoTip text="בדיקת תקינות — חיבור לבסיס נתונים, מצב שירותים פנימיים" /></SectionTitle>
          {!health && !loading && (
            <p className="muted">לא ניתן לטעון בריאות מערכת.</p>
          )}
          {health && (
            <>
              <div style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: (health.overall_status === 'פעיל' || health.status === 'ok') ? '#16a34a' : '#dc2626' }}>
                  {(health.overall_status === 'פעיל' || health.status === 'ok') ? '🟢' : '🔴'}
                </span>
                <strong>{t('status')}:</strong>
                <span style={{ color: (health.overall_status === 'פעיל' || health.status === 'ok') ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
                  {health.overall_status || health.status || 'לא ידוע'}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                <strong>{t('database')}:</strong>
                <span style={{ color: health.database_ok ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
                  {health.database_ok ? '✅ ' + t('db_connected') : '❌ ' + t('db_unknown')}
                </span>
              </div>
              {health.drivers && health.drivers.length > 0 && (
                <ul style={{ margin: 0, paddingRight: 18 }}>
                  {health.drivers.map(x => <li key={x} style={{ fontSize: 13, color: '#16a34a', marginBottom: 2 }}>✓ {x}</li>)}
                </ul>
              )}
            </>
          )}
        </Card>
      </div>

      <div className="two-col">
        {/* ── Businesses ───────────────────────────── */}
        <Card>
          <SectionTitle>{t('businesses')}</SectionTitle>
          <div className="table-list">
            {businesses.length === 0 && <p className="muted">אין עסקים.</p>}
            {businesses.slice(0, 8).map(b => (
              <div key={b.id}><strong>{b.name}</strong><div className="muted">{b.city || '—'} · {b.category || '—'} · {b.status}</div></div>
            ))}
          </div>
        </Card>

        {/* ── Approvals / Notifications ─────────────── */}
        <Card>
          <SectionTitle>{t('pending_approvals')}</SectionTitle>
          <div className="table-list">
            {approvals.filter(a => ['proposed', 'under_review'].includes(a.status)).length === 0 && (
              <p className="muted">אין אישורים ממתינים.</p>
            )}
            {approvals.filter(a => ['proposed', 'under_review'].includes(a.status)).slice(0, 6).map(a => (
              <div key={a.id}><strong>{a.title}</strong><div className="muted">{a.approval_type} · {a.status}</div></div>
            ))}
          </div>
        </Card>
      </div>

      {/* ── Recent Notifications ──────────────────── */}
      {notifications.length > 0 && (
        <Card>
          <SectionTitle>🔔 התראות אחרונות <InfoTip text="אירועים חשובים — דמו נצפה, תשלום אושר, תגובת WhatsApp" /></SectionTitle>
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
