import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle } from '../components/ui';
import {
  DomainApprovalItem,
  getDomainApprovals,
  approveDomain,
  rejectDomain,
} from '../services/queries';

const STATUS_COLORS: Record<string, string> = {
  pending_admin: '#ef4444',
  approved: '#059669',
  rejected: '#6b7280',
};

export default function DomainApprovalsPage() {
  const [items, setItems] = useState<DomainApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');
  const [noteMap, setNoteMap] = useState<Record<number, string>>({});

  const load = () => {
    setLoading(true);
    getDomainApprovals()
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const pending = items.filter(i => i.approval_status === 'pending_admin');

  const act = async (fn: () => Promise<unknown>, successMsg: string) => {
    try {
      await fn();
      setMsg(successMsg);
      load();
    } catch (e: any) {
      setMsg('פעולה נכשלה: ' + (e?.message || ''));
    }
  };

  return (
    <div className="grid">
      {/* ── Red Alert Banner (pending only) ─────────────────────────────── */}
      {pending.length > 0 && (
        <div style={{
          background: '#fee2e2',
          border: '2px solid #ef4444',
          borderRadius: 12,
          padding: '16px 20px',
          marginBottom: 8,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <span style={{ fontSize: 22 }}>🚨</span>
            <strong style={{ fontSize: 16, color: '#991b1b' }}>
              {pending.length} בקשת רכישת דומיין ממתינה לאישורך
            </strong>
          </div>
          <p style={{ fontSize: 13, color: '#b91c1c', margin: 0 }}>
            ⛔ המערכת מנועה לרכוש דומיינים מעל $3 בלי אישור ידני. בדוק את הפרטים למטה ואשר או דחה כל בקשה.
          </p>
        </div>
      )}

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <SectionTitle>אישורי רכישת דומיין ({items.length})</SectionTitle>
          <Button onClick={load}>רענן</Button>
        </div>

        {msg && (
          <div style={{ background: '#fef9c3', border: '1px solid #fbbf24', borderRadius: 8, padding: '8px 12px', marginBottom: 12, fontSize: 14 }}>
            {msg}
          </div>
        )}

        {loading && <p className="muted">טוען…</p>}
        {!loading && items.length === 0 && (
          <p className="muted">אין בקשות רכישת דומיין ממתינות. ✅</p>
        )}

        <div className="table-list">
          {items.map(item => (
            <div key={item.intake_id} style={{
              padding: '14px 0',
              borderBottom: '1px solid #f3f4f6',
            }}>
              {/* Status badge + domain */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                <div>
                  <strong style={{ fontSize: 15 }}>{item.domain}</strong>
                  <span style={{
                    marginRight: 10,
                    background: STATUS_COLORS[item.approval_status || ''] || '#d1d5db',
                    color: '#fff',
                    borderRadius: 6,
                    padding: '2px 8px',
                    fontSize: 12,
                  }}>
                    {item.approval_status === 'pending_admin' ? '⏳ ממתין לאישור' :
                     item.approval_status === 'approved' ? '✅ אושר' :
                     item.approval_status === 'rejected' ? '❌ נדחה' : item.approval_status}
                  </span>
                </div>
                {item.price_usd !== null && (
                  <span style={{
                    fontSize: 16,
                    fontWeight: 700,
                    color: (item.price_usd || 0) > 3 ? '#ef4444' : '#059669',
                  }}>
                    ${item.price_usd?.toFixed(2)}/שנה
                    {(item.price_usd || 0) > 3 && ' ⚠️'}
                  </span>
                )}
              </div>

              {/* Client info */}
              <div style={{ marginTop: 4, fontSize: 13, color: '#6b7280' }}>
                {item.business_name} | {item.phone} | תשלום: {item.payment_status} | token: {item.token_prefix}…
              </div>

              {/* Action buttons (only for pending) */}
              {item.approval_status === 'pending_admin' && (
                <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                  <input
                    type="text"
                    placeholder="הערה (אופציונלי)"
                    value={noteMap[item.intake_id] || ''}
                    onChange={e => setNoteMap(m => ({ ...m, [item.intake_id]: e.target.value }))}
                    style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13, minWidth: 180 }}
                  />
                  <Button
                    onClick={() => act(
                      () => approveDomain(item.intake_id, noteMap[item.intake_id]),
                      `✅ דומיין ${item.domain} אושר — המשימה הועמדה בתור`
                    )}
                    style={{ background: '#059669', color: '#fff', fontWeight: 700 }}
                  >
                    ✅ אשר רכישה
                  </Button>
                  <Button
                    onClick={() => act(
                      () => rejectDomain(item.intake_id, noteMap[item.intake_id]),
                      `❌ דומיין ${item.domain} נדחה — הלקוח יקבל הודעה`
                    )}
                    style={{ background: '#ef4444', color: '#fff' }}
                  >
                    ❌ דחה
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
