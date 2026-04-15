import { useEffect, useRef, useState } from 'react';
import { Button, Card, SectionTitle, Input, Select, Tooltip } from '../components/ui';
import { Lead, IntegrityStats, getLeads, createLead, qualifyLead, convertLeadToBusiness, importLeadsCSV, autoQualifyLeads, triggerCrossValidate, getIntegrityStats, bulkCrossValidate } from '../services/queries';

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
  const [crossValidating, setCrossValidating] = useState<number | null>(null);
  const [bulkValidating, setBulkValidating] = useState(false);
  const [integrityStats, setIntegrityStats] = useState<IntegrityStats | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => getLeads(0, 500).then(setItems).catch(console.error);
  const loadStats = () => getIntegrityStats().then(setIntegrityStats).catch(() => {});
  useEffect(() => { load(); loadStats(); }, []);

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

  const handleCrossValidate = async (leadId: number) => {
    setCrossValidating(leadId);
    try {
      const result = await triggerCrossValidate(leadId);
      const statusLabel: Record<string, string> = { verified: '✅ מאומת', manual_review: '⚠️ לבדיקה', mismatch: '❌ אי-התאמה', pending: '⏳ ממתין' };
      setMsg(`כיול הושלם — ${statusLabel[result.cross_ref_status] ?? result.cross_ref_status} (${result.cross_ref_score}/100)`);
      load(); loadStats();
    } catch (e: any) { setMsg('כיול נכשל: ' + (e?.message || '')); }
    finally { setCrossValidating(null); }
  };

  const handleBulkValidate = async () => {
    setBulkValidating(true);
    try {
      const r = await bulkCrossValidate({ limit: 50, skip_already_validated: true });
      setMsg(`Bulk כיול: ${r.validated} לידים | ✅ ${r.summary.verified ?? 0} מאומת | ⚠️ ${r.summary.manual_review ?? 0} לבדיקה | ❌ ${r.summary.mismatch ?? 0} אי-התאמה`);
      load(); loadStats();
    } catch (e: any) { setMsg('Bulk כיול נכשל: ' + (e?.message || '')); }
    finally { setBulkValidating(false); }
  };

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <SectionTitle>לידים ({filtered.length})</SectionTitle>
        <div style={{ display: 'flex', gap: 8 }}>
          <input ref={fileRef} type="file" accept=".csv" style={{ display: 'none' }} onChange={handleCSV} />
          <Tooltip text="אמת נתוני אמינות חוצה-סוכנים לכלל הלידים שטרם אומתו (עד 50)">
            <Button onClick={handleBulkValidate} disabled={bulkValidating} style={{ background: '#0e7490', color: '#fff' }}>
              {bulkValidating ? '⏳ מכייל...' : '🔍 Bulk כיול'}
            </Button>
          </Tooltip>
          <Tooltip text="כשר אוטומטית לידים עם ציון ≥70 ללא אתר קיים">
            <Button onClick={() => action(() => autoQualifyLeads().then(r => { setMsg(`כושרו אוטומטית ${r.qualified} לידים`); return r; }), '')} style={{ background: '#7c3aed', color: '#fff' }}>⚡ כישור אוטומטי</Button>
          </Tooltip>
          <Button onClick={() => fileRef.current?.click()} style={{ background: '#2563eb', color: '#fff' }}>📤 ייבוא CSV</Button>
          <Button onClick={() => setShowAdd(v => !v)} style={{ background: '#111827', color: '#fff' }}>
            {showAdd ? 'סגור' : '+ הוסף ליד'}
          </Button>
        </div>
      </div>

      {msg && <div style={{ background: '#fef9c3', border: '1px solid #fbbf24', borderRadius: 8, padding: '8px 12px', marginBottom: 12, fontSize: 14 }}>{msg}</div>}

      {integrityStats && <IntegrityStatsPanel stats={integrityStats} />}

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
                  <DataIntegrityBadge score={l.cross_ref_score} status={l.cross_ref_status} agents={l.cross_ref_agents} />
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
              <Tooltip text="בדוק אמינות נתונים חוצה-סוכנים (Google / Facebook / Instagram)">
                <Button
                  onClick={() => handleCrossValidate(l.id)}
                  disabled={crossValidating === l.id}
                  style={{ background: '#0891b2', color: '#fff' }}
                >
                  {crossValidating === l.id ? '⏳...' : '🔍 כייל'}
                </Button>
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

// ── Data Integrity Badge ──────────────────────────────────────────────────────
const AGENT_LABELS: Record<string, string> = { google_places: 'G', facebook: 'FB', instagram: 'IG', serper: 'Srp', tiktok: 'TT' };

function DataIntegrityBadge({ score, status, agents }: { score?: number; status?: string; agents?: string | null }) {
  if (!status || status === 'pending') {
    return <span style={{ fontSize: 11, color: '#9ca3af', marginLeft: 6 }}>⏳ טרם אומת</span>;
  }

  const color = status === 'verified' ? '#059669' : status === 'manual_review' ? '#d97706' : '#dc2626';
  const icon = status === 'verified' ? '✅' : status === 'manual_review' ? '⚠️' : '❌';
  const label = status === 'verified' ? 'VERIFIED' : status === 'manual_review' ? 'REVIEW' : 'MISMATCH';

  let chips: React.ReactNode = null;
  if (agents) {
    try {
      const parsed: Record<string, boolean> = JSON.parse(agents);
      chips = (
        <span style={{ display: 'flex', gap: 3, marginTop: 2, flexWrap: 'wrap' }}>
          {Object.entries(parsed).map(([k, ok]) => (
            <span key={k} title={k} style={{
              fontSize: 10, padding: '1px 5px', borderRadius: 4,
              background: ok ? '#dcfce7' : '#fee2e2',
              color: ok ? '#166534' : '#991b1b',
            }}>
              {AGENT_LABELS[k] ?? k}:{ok ? '✅' : '❌'}
            </span>
          ))}
        </span>
      );
    } catch { /* ignore malformed JSON */ }
  }

  return (
    <span style={{ display: 'inline-flex', flexDirection: 'column', marginLeft: 6, verticalAlign: 'middle' }}>
      <span style={{ background: color, color: '#fff', borderRadius: 6, padding: '2px 8px', fontSize: 12, fontWeight: 700 }}>
        {icon} {score}/100 {label}
      </span>
      {chips}
    </span>
  );
}

// ── Integrity Stats Panel ─────────────────────────────────────────────────────
function IntegrityStatsPanel({ stats }: { stats: IntegrityStats }) {
  const { total_leads, status_counts, average_score, agent_pass_rates, validation_coverage } = stats;
  return (
    <div style={{
      display: 'flex', gap: 12, flexWrap: 'wrap', padding: '10px 14px',
      background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 10, marginBottom: 14, fontSize: 13,
    }}>
      <StatChip label="סה״כ לידים" value={String(total_leads)} color="#0369a1" />
      <StatChip label="כיסוי אימות" value={`${validation_coverage}%`} color="#0891b2" />
      <StatChip label="ניקוד ממוצע" value={`${average_score}/100`} color="#0284c7" />
      <StatChip label="✅ מאומת" value={String(status_counts.verified)} color="#059669" />
      <StatChip label="⚠️ לבדיקה" value={String(status_counts.manual_review)} color="#d97706" />
      <StatChip label="❌ אי-התאמה" value={String(status_counts.mismatch)} color="#dc2626" />
      {Object.entries(agent_pass_rates).map(([agent, rate]) => (
        <StatChip key={agent} label={`${AGENT_LABELS[agent] ?? agent} pass`} value={`${rate}%`} color="#6366f1" />
      ))}
    </div>
  );
}

function StatChip({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontWeight: 700, fontSize: 16, color }}>{value}</div>
      <div style={{ fontSize: 11, color: '#6b7280' }}>{label}</div>
    </div>
  );
}
