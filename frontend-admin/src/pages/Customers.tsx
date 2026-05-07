import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle, Input } from '../components/ui';
import { Customer, getCustomers, syncCustomersFromDemos } from '../services/queries';

const STATUS_STYLE: Record<string, { bg: string; color: string }> = {
  'לקוח במנוי':    { bg: '#dbeafe', color: '#1d4ed8' },
  'שילם — אתר פעיל': { bg: '#dcfce7', color: '#065f46' },
  'אתר פעיל':     { bg: '#d1fae5', color: '#065f46' },
  'אישר דמו':     { bg: '#ede9fe', color: '#5b21b6' },
  'דמו נשלח':     { bg: '#fef9c3', color: '#713f12' },
  'חשבון נוצר':   { bg: '#f3f4f6', color: '#374151' },
};

export default function CustomersPage() {
  const [items, setItems] = useState<Customer[]>([]);
  const [search, setSearch] = useState('');
  const [showActive, setShowActive] = useState<boolean | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState('');

  const load = () => getCustomers(0, 500).then(setItems).catch(console.error);
  useEffect(() => { load(); }, []);

  const handleSync = async () => {
    setSyncing(true);
    setSyncMsg('');
    try {
      const result = await syncCustomersFromDemos();
      setSyncMsg(`✅ נוצרו ${result.created} חשבונות לקוח חדשים. (${result.skipped} כבר קיימים)`);
      load();
    } catch (e) {
      setSyncMsg(`❌ שגיאה בסנכרון: ${e instanceof Error ? e.message : 'unknown'}`);
    } finally {
      setSyncing(false);
    }
  };

  const filtered = items.filter(c => {
    const q = search.toLowerCase();
    const matchSearch = !q
      || (c.contact_name || '').toLowerCase().includes(q)
      || (c.business_name || '').toLowerCase().includes(q)
      || (c.phone || '').includes(q)
      || (c.email || '').toLowerCase().includes(q)
      || (c.package_name || '').toLowerCase().includes(q);
    const matchActive = showActive === null || c.is_active === showActive;
    return matchSearch && matchActive;
  });

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <SectionTitle>לקוחות ({filtered.length})</SectionTitle>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button onClick={load}>🔄 רענן</Button>
          <Button
            onClick={handleSync}
            disabled={syncing}
            style={{ background: '#166534', color: '#fff', fontWeight: 700 }}
          >
            {syncing ? '⏳ מסנכרן…' : '⚡ סנכרן לקוחות מדמו'}
          </Button>
        </div>
      </div>

      {syncMsg && (
        <div style={{
          padding: '10px 14px', borderRadius: 8, marginBottom: 12, fontSize: 13,
          background: syncMsg.startsWith('✅') ? '#dcfce7' : '#fee2e2',
          color: syncMsg.startsWith('✅') ? '#166534' : '#991b1b',
        }}>
          {syncMsg}
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        <Input placeholder="חיפוש לפי שם / עסק / טלפון / מייל..." value={search} onChange={e => setSearch(e.target.value)} style={{ flex: 1, minWidth: 200 }} />
        <div style={{ display: 'flex', gap: 4 }}>
          <Button onClick={() => setShowActive(null)} style={showActive === null ? { background: '#111827', color: '#fff' } : {}}>הכל</Button>
          <Button onClick={() => setShowActive(true)} style={showActive === true ? { background: '#059669', color: '#fff' } : {}}>פעילים</Button>
          <Button onClick={() => setShowActive(false)} style={showActive === false ? { background: '#dc2626', color: '#fff' } : {}}>לא פעילים</Button>
        </div>
      </div>

      <div className="table-list">
        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <p className="muted">לא נמצאו לקוחות.</p>
            <p style={{ fontSize: 13, marginTop: 6 }}>לחץ <strong>⚡ סנכרן לקוחות מדמו</strong> כדי לרשום אוטומטית עסקים עם אתרי דמו.</p>
          </div>
        )}
        {filtered.map(c => {
          const statusStyle = STATUS_STYLE[c.customer_status || ''] || STATUS_STYLE['חשבון נוצר'];
          return (
            <div key={c.id} style={{ padding: '12px 0', borderBottom: '1px solid #f1f5f9' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 4 }}>
                <div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                    <strong style={{ fontSize: 15 }}>{c.contact_name || c.business_name || `לקוח #${c.id}`}</strong>
                    {c.customer_status && (
                      <span style={{ background: statusStyle.bg, color: statusStyle.color, borderRadius: 20, padding: '2px 10px', fontSize: 12, fontWeight: 700 }}>
                        {c.customer_status}
                      </span>
                    )}
                    <span style={{ background: c.is_active ? '#d1fae5' : '#fee2e2', color: c.is_active ? '#065f46' : '#991b1b', borderRadius: 6, padding: '2px 8px', fontSize: 11 }}>
                      {c.is_active ? 'פעיל' : 'לא פעיל'}
                    </span>
                    {c.must_change_password && (
                      <span style={{ background: '#fef3c7', color: '#92400e', borderRadius: 6, padding: '2px 6px', fontSize: 11 }}>חייב שינוי סיסמה</span>
                    )}
                  </div>

                  {c.business_name && (
                    <div style={{ fontSize: 13, fontWeight: 600, marginTop: 3, color: '#374151' }}>
                      🏢 {c.business_name}{c.business_city ? ` · ${c.business_city}` : ''}{c.business_category ? ` · ${c.business_category}` : ''}
                    </div>
                  )}

                  <div className="muted" style={{ marginTop: 3, fontSize: 13 }}>
                    {c.phone && <span>📞 {c.phone} · </span>}
                    {c.email && <span>✉️ {c.email} · </span>}
                    {c.package_name && <span>📦 {c.package_name}</span>}
                  </div>

                  <div className="muted" style={{ fontSize: 12, marginTop: 3 }}>
                    {c.business_id && <span>עסק #{c.business_id} · </span>}
                    {c.draft_site_id && (
                      <>
                        <span>דמו #{c.draft_site_id}</span>
                        {c.draft_status && <span style={{ marginRight: 4, background: '#f1f5f9', padding: '1px 6px', borderRadius: 4 }}>{c.draft_status}</span>}
                        {c.draft_preview_url && (
                          <a href={`https://api.tazo-web.com${c.draft_preview_url}`} target="_blank" rel="noopener noreferrer" style={{ marginRight: 6, color: '#6366f1', fontSize: 11 }}>
                            👁️ צפה בדמו
                          </a>
                        )}
                      </>
                    )}
                    {c.active_site_id && <span> · אתר פעיל #{c.active_site_id}</span>}
                  </div>
                </div>

                <div style={{ textAlign: 'left', fontSize: 12, color: '#9ca3af' }}>
                  <div>#{c.id}</div>
                  {c.created_at && <div style={{ marginTop: 2 }}>{new Date(c.created_at).toLocaleDateString('he-IL')}</div>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
