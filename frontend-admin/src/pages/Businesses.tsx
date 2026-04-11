import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle, Input, Select, Tooltip } from '../components/ui';
import {
  Business, getBusinesses, createBusiness,
  moveBusinessToDraft, markBusinessOutreachReady, buildBusinessWhatsApp,
  getCampaigns, Campaign,
} from '../services/queries';

const STATUSES = ['new', 'outreach_ready', 'draft_pending', 'draft_ready', 'active', 'inactive'];

const emptyForm = { name: '', city: '', category: '', phone: '', address: '', status: 'new', campaign_id: '' };

export default function BusinessesPage() {
  const [items, setItems] = useState<Business[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [msg, setMsg] = useState('');
  const [saving, setSaving] = useState(false);

  const load = () => {
    getBusinesses(0, 500).then(setItems).catch(console.error);
    getCampaigns().then(setCampaigns).catch(console.error);
  };
  useEffect(() => { load(); }, []);

  const filtered = items.filter(b => {
    const q = search.toLowerCase();
    const matchSearch = !q || b.name.toLowerCase().includes(q) || (b.city || '').toLowerCase().includes(q) || (b.category || '').toLowerCase().includes(q);
    const matchStatus = !statusFilter || b.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const handleAdd = async () => {
    if (!form.name.trim()) { setMsg('שם עסק הוא שדה חובה'); return; }
    setSaving(true); setMsg('');
    try {
      await createBusiness({ ...form, campaign_id: form.campaign_id ? Number(form.campaign_id) : null });
      setForm(emptyForm); setShowAdd(false); load();
    } catch { setMsg('שמירה נכשלה'); }
    finally { setSaving(false); }
  };

  const action = async (fn: () => Promise<unknown>, successMsg?: string) => {
    try { await fn(); load(); if (successMsg) setMsg(successMsg); }
    catch (e: any) { setMsg('פעולה נכשלה: ' + (e?.message || '')); }
  };

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <SectionTitle>עסקים ({filtered.length})</SectionTitle>
        <Button onClick={() => setShowAdd(v => !v)} style={{ background: '#111827', color: '#fff' }}>
          {showAdd ? 'סגור' : '+ הוסף עסק'}
        </Button>
      </div>

      {msg && <div style={{ background: '#fef9c3', border: '1px solid #fbbf24', borderRadius: 8, padding: '8px 12px', marginBottom: 12, fontSize: 14 }}>{msg}</div>}

      {showAdd && (
        <div style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, marginBottom: 16 }}>
          <strong style={{ display: 'block', marginBottom: 10 }}>עסק חדש</strong>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 8 }}>
            <Input placeholder="שם עסק *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
            <Input placeholder="עיר" value={form.city} onChange={e => setForm(f => ({ ...f, city: e.target.value }))} />
            <Input placeholder="קטגוריה" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} />
            <Input placeholder="טלפון" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
            <Input placeholder="כתובת" value={form.address} onChange={e => setForm(f => ({ ...f, address: e.target.value }))} />
            <Select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
              {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
            <Select value={form.campaign_id} onChange={e => setForm(f => ({ ...f, campaign_id: e.target.value }))}>
              <option value="">ללא קמפיין</option>
              {campaigns.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </Select>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            <Button onClick={handleAdd} disabled={saving} style={{ background: '#111827', color: '#fff' }}>
              {saving ? 'שומר...' : 'שמור'}
            </Button>
            <Button onClick={() => { setShowAdd(false); setForm(emptyForm); }}>ביטול</Button>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        <Input placeholder="חיפוש לפי שם / עיר / קטגוריה..." value={search} onChange={e => setSearch(e.target.value)} style={{ flex: 1, minWidth: 200 }} />
        <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ minWidth: 140 }}>
          <option value="">כל הסטטוסים</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </Select>
        <Button onClick={load}>רענן</Button>
      </div>

      <div className="table-list">
        {filtered.length === 0 && <p className="muted">לא נמצאו עסקים.</p>}
        {filtered.map(b => (
          <div key={b.id} style={{ padding: '12px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 4 }}>
              <div>
                <strong>{b.name}</strong>
                {b.phone && <span className="muted" style={{ marginLeft: 8 }}>📞 {b.phone}</span>}
                <div className="muted">{b.city || '—'} · {b.category || '—'} · {b.address || ''}</div>
                <div style={{ marginTop: 2 }}>
                  <span style={{ background: statusColor(b.status), color: '#fff', borderRadius: 6, padding: '2px 8px', fontSize: 12 }}>{b.status}</span>
                  {b.campaign_id && <span className="muted" style={{ marginLeft: 8, fontSize: 12 }}>קמפיין #{b.campaign_id}</span>}
                </div>
              </div>
              <div style={{ fontSize: 12, color: '#9ca3af' }}>#{b.id}</div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
              <Tooltip text="צור אתר טיוטה לעסק זה — מוכן לתצוגה מקדימה">
                <Button onClick={() => action(() => moveBusinessToDraft(b.id), 'דראפט נוצר!')}>
                  📝 צור דראפט
                </Button>
              </Tooltip>
              <Tooltip text="סמן עסק זה כמוכן לפנייה — יעבור לתור הפנייה">
                <Button onClick={() => action(() => markBusinessOutreachReady(b.id), 'סומן כמוכן לפנייה')}>
                  ✅ מוכן לפנייה
                </Button>
              </Tooltip>
              <Tooltip text="בנה הודעת WhatsApp מותאמת אישית לעסק זה">
                <Button onClick={() => action(() => buildBusinessWhatsApp(b.id).then((x: any) => {
                  setMsg(`WhatsApp מוכן: ${x.whatsapp_url || 'outreach #' + x.outreach_id}`);
                }))}>
                  💬 בנה WhatsApp
                </Button>
              </Tooltip>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function statusColor(s: string) {
  const m: Record<string, string> = { new: '#6b7280', outreach_ready: '#2563eb', draft_pending: '#d97706', draft_ready: '#7c3aed', active: '#059669', inactive: '#dc2626' };
  return m[s] || '#6b7280';
}
