import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle, Select } from '../components/ui';
import { Payment, getPayments, confirmPayment, movePaymentToActivation } from '../services/queries';

const STATUSES = ['pending', 'confirmed', 'activation_ready', 'active', 'refunded', 'failed'];

export default function PaymentsPage() {
  const [items, setItems] = useState<Payment[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [msg, setMsg] = useState('');

  const load = () => getPayments(0, 500).then(setItems).catch(console.error);
  useEffect(() => { load(); }, []);

  const filtered = !statusFilter ? items : items.filter(p => p.internal_status === statusFilter);

  const action = async (fn: () => Promise<unknown>, successMsg: string) => {
    try { await fn(); setMsg(successMsg); load(); }
    catch (e: any) { setMsg('פעולה נכשלה: ' + (e?.message || '')); }
  };

  const total = items.reduce((s, p) => s + p.amount, 0);

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <SectionTitle>תשלומים ({filtered.length})</SectionTitle>
        <div style={{ fontSize: 14, color: '#6b7280' }}>סה"כ: ₪{total.toLocaleString()}</div>
      </div>

      {msg && <div style={{ background: '#fef9c3', border: '1px solid #fbbf24', borderRadius: 8, padding: '8px 12px', marginBottom: 12, fontSize: 14 }}>{msg}</div>}

      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ minWidth: 160 }}>
          <option value="">כל הסטטוסים</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </Select>
        <Button onClick={load}>רענן</Button>
      </div>

      <div className="table-list">
        {filtered.length === 0 && <p className="muted">לא נמצאו תשלומים.</p>}
        {filtered.map(p => (
          <div key={p.id} style={{ padding: '10px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 4 }}>
              <div>
                <strong>תשלום #{p.id}</strong>
                {p.business_id && <span className="muted" style={{ marginLeft: 8 }}>עסק #{p.business_id}</span>}
                <div style={{ marginTop: 2 }}>
                  <span style={{ fontSize: 20, fontWeight: 700, color: '#111827' }}>₪{p.amount.toLocaleString()}</span>
                  <span style={{ background: paymentColor(p.internal_status), color: '#fff', borderRadius: 6, padding: '2px 8px', fontSize: 12, marginLeft: 8 }}>{p.internal_status}</span>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
              {p.internal_status === 'pending' && (
                <Button onClick={() => action(() => confirmPayment(p.id), `תשלום #${p.id} אושר ✓`)} style={{ background: '#059669', color: '#fff' }}>
                  ✅ אשר תשלום
                </Button>
              )}
              {(p.internal_status === 'confirmed' || p.internal_status === 'pending') && (
                <Button onClick={() => action(() => movePaymentToActivation(p.id), `תשלום #${p.id} הועבר להפעלה`)} style={{ background: '#7c3aed', color: '#fff' }}>
                  🚀 העבר להפעלה
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function paymentColor(s: string) {
  const m: Record<string, string> = { pending: '#d97706', confirmed: '#2563eb', activation_ready: '#7c3aed', active: '#059669', refunded: '#6b7280', failed: '#dc2626' };
  return m[s] || '#6b7280';
}
