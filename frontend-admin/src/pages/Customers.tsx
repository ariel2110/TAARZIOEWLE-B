import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle, Input } from '../components/ui';
import { Customer, getCustomers } from '../services/queries';

export default function CustomersPage() {
  const [items, setItems] = useState<Customer[]>([]);
  const [search, setSearch] = useState('');
  const [showActive, setShowActive] = useState<boolean | null>(null);

  const load = () => getCustomers(0, 500).then(setItems).catch(console.error);
  useEffect(() => { load(); }, []);

  const filtered = items.filter(c => {
    const q = search.toLowerCase();
    const matchSearch = !q
      || (c.contact_name || '').toLowerCase().includes(q)
      || (c.phone || '').includes(q)
      || (c.email || '').toLowerCase().includes(q)
      || (c.package_name || '').toLowerCase().includes(q);
    const matchActive = showActive === null || c.is_active === showActive;
    return matchSearch && matchActive;
  });

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <SectionTitle>לקוחות ({filtered.length})</SectionTitle>
        <Button onClick={load}>רענן</Button>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        <Input placeholder="חיפוש לפי שם / טלפון / מייל / חבילה..." value={search} onChange={e => setSearch(e.target.value)} style={{ flex: 1, minWidth: 200 }} />
        <div style={{ display: 'flex', gap: 4 }}>
          <Button onClick={() => setShowActive(null)} style={showActive === null ? { background: '#111827', color: '#fff' } : {}}>הכל</Button>
          <Button onClick={() => setShowActive(true)} style={showActive === true ? { background: '#059669', color: '#fff' } : {}}>פעילים</Button>
          <Button onClick={() => setShowActive(false)} style={showActive === false ? { background: '#dc2626', color: '#fff' } : {}}>לא פעילים</Button>
        </div>
      </div>

      <div className="table-list">
        {filtered.length === 0 && <p className="muted">לא נמצאו לקוחות.</p>}
        {filtered.map(c => (
          <div key={c.id} style={{ padding: '10px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 4 }}>
              <div>
                <strong>{c.contact_name || `לקוח #${c.id}`}</strong>
                <span style={{ marginLeft: 8, background: c.is_active ? '#d1fae5' : '#fee2e2', color: c.is_active ? '#065f46' : '#991b1b', borderRadius: 6, padding: '2px 8px', fontSize: 12 }}>
                  {c.is_active ? 'פעיל' : 'לא פעיל'}
                </span>
                {c.must_change_password && <span style={{ marginLeft: 6, background: '#fef3c7', color: '#92400e', borderRadius: 6, padding: '2px 6px', fontSize: 11 }}>חייב לשנות סיסמה</span>}
                <div className="muted" style={{ marginTop: 2 }}>
                  {c.phone && <span>📞 {c.phone} · </span>}
                  {c.email && <span>✉️ {c.email} · </span>}
                  {c.package_name && <span>📦 {c.package_name}</span>}
                </div>
                <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
                  {c.business_id && <span>עסק #{c.business_id} · </span>}
                  {c.draft_site_id && <span>דראפט #{c.draft_site_id} · </span>}
                  {c.active_site_id && <span>אתר פעיל #{c.active_site_id}</span>}
                </div>
              </div>
              <div style={{ fontSize: 12, color: '#9ca3af' }}>#{c.id}</div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
