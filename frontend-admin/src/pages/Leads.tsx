import { useEffect, useRef, useState } from 'react';
import { Button, Card, SectionTitle, Input, Select, Tooltip } from '../components/ui';
import { Lead, getLeads, createLead, qualifyLead, convertLeadToBusiness, importLeadsCSV, autoQualifyLeads } from '../services/queries';

const STATUSES = ['imported', 'qualified', 'converted', 'rejected'];
const emptyForm = { imported_name: '', city: '', category: '', phone: '', website_url: '', score: '0', status: 'imported' };

export default function LeadsPage() {
  const [items, setItems] = useState<Lead[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [msg, setMsg] = useState('');
  const [saving, setSaving] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => getLeads(0, 500).then(setItems).catch(console.error);
  useEffect(() => { load(); }, []);

  const filtered = items.filter(l => {
    const q = search.toLowerCase();
    const matchSearch = !q || l.imported_name.toLowerCase().includes(q) || (l.city || '').toLowerCase().includes(q) || (l.category || '').toLowerCase().includes(q) || (l.phone || '').includes(q);
    const matchStatus = !statusFilter || l.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const handleAdd = async () => {
    if (!form.imported_name.trim()) { setMsg('שם ליד הוא שדה חובה'); return; }
    setSaving(true); setMsg('');
    try {
      await createLead({ ...form, score: Number(form.score) });
      setForm(emptyForm); setShowAdd(false); load();
    } catch { setMsg('שמירה נכשלה'); }
    finally { setSaving(false); }
  };

  const handleCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setMsg('מייבא...');
    try {
      const text = await file.text();
      const result = await importLeadsCSV(text);
      setMsg(`יובאו ${result.imported} לידים${result.errors?.length ? ' (' + result.errors.length + ' שגיאות)' : ''}`);
      load();
    } catch { setMsg('ייבוא נכשל'); }
    if (fileRef.current) fileRef.current.value = '';
  };

  const action = async (fn: () => Promise<unknown>, successMsg: string) => {
    try { await fn(); setMsg(successMsg); load(); }
    catch (e: any) { setMsg('פעולה נכשלה: ' + (e?.message || '')); }
  };

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <SectionTitle>לידים ({filtered.length})</SectionTitle>
        <div style={{ display: 'flex', gap: 8 }}>
          <input ref={fileRef} type="file" accept=".csv" style={{ display: 'none' }} onChange={handleCSV} />
          <Button onClick={() => fileRef.current?.click()} style={{ background: '#2563eb', color: '#fff' }}>📤 ייבוא CSV</Button>
          <Button onClick={() => setShowAdd(v => !v)} style={{ background: '#111827', color: '#fff' }}>
            {showAdd ? 'סגור' : '+ הוסף ליד'}
          </Button>
        </div>
      </div>

      {msg && <div style={{ background: '#fef9c3', border: '1px solid #fbbf24', borderRadius: 8, padding: '8px 12px', marginBottom: 12, fontSize: 14 }}>{msg}</div>}

      {showAdd && (
        <div style={{ background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, marginBottom: 16 }}>
          <strong style={{ display: 'block', marginBottom: 10 }}>ליד חדש</strong>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 8 }}>
            <Input placeholder="שם *" value={form.imported_name} onChange={e => setForm(f => ({ ...f, imported_name: e.target.value }))} />
            <Input placeholder="עיר" value={form.city} onChange={e => setForm(f => ({ ...f, city: e.target.value }))} />
            <Input placeholder="קטגוריה" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} />
            <Input placeholder="טלפון" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
            <Input placeholder="אתר (URL)" value={form.website_url} onChange={e => setForm(f => ({ ...f, website_url: e.target.value }))} />
            <Input placeholder="ציון (0-100)" type="number" min="0" max="100" value={form.score} onChange={e => setForm(f => ({ ...f, score: e.target.value }))} />
            <Select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
              {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
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
        <Input placeholder="חיפוש לפי שם / עיר / טלפון..." value={search} onChange={e => setSearch(e.target.value)} style={{ flex: 1, minWidth: 200 }} />
        <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ minWidth: 140 }}>
          <option value="">כל הסטטוסים</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </Select>
        <Button onClick={load}>רענן</Button>
      </div>

      <div className="table-list">
        {filtered.length === 0 && <p className="muted">לא נמצאו לידים.</p>}
        {filtered.map(l => (
          <div key={l.id} style={{ padding: '10px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 4 }}>
              <div>
                <strong>{l.imported_name}</strong>
                {l.phone && <span className="muted" style={{ marginLeft: 8 }}>📞 {l.phone}</span>}
                <div className="muted">{l.city || '—'} · {l.category || '—'}{l.website_url ? ` · ${l.website_url}` : ''}</div>
                <div style={{ marginTop: 2 }}>
                  <span style={{ background: scoreColor(l.score), color: '#fff', borderRadius: 6, padding: '2px 8px', fontSize: 12 }}>ציון: {l.score}</span>
                  <span style={{ background: '#e5e7eb', borderRadius: 6, padding: '2px 8px', fontSize: 12, marginLeft: 6 }}>{l.status}</span>
                </div>
              </div>
              <div style={{ fontSize: 12, color: '#9ca3af' }}>#{l.id}</div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
              <Tooltip text="סמן ליד כשיר — מעביר אותו לשלב הבא בצינור">
                <Button onClick={() => action(() => qualifyLead(l.id), 'ליד עבר כשירות ✓')}>✅ כשר</Button>
              </Tooltip>
              <Tooltip text="המר ליד לעסק פעיל במערכת">
                <Button onClick={() => action(() => convertLeadToBusiness(l.id), 'הומר לעסק!')} style={{ background: '#111827', color: '#fff' }}>🏢 המר לעסק</Button>
              </Tooltip>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function scoreColor(s: number) {
  if (s >= 70) return '#059669';
  if (s >= 40) return '#d97706';
  return '#9ca3af';
}
