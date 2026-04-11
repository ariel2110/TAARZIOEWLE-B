
import { useEffect, useState, useCallback } from 'react';
import { SectionTitle } from '../components/ui';
import {
  Digest, Health, QueueSummary, QueueItem, Approval,
  GrokCEOResponse, GrokExecutionPayload,
  getDigest, getHealth, getQueueSummary, getQueueItems,
  getApprovals, approve, reject,
  addCeoDecisionNote, runQueueAction,
  buildBusinessWhatsApp,
  askGrok, executeGrokAction,
} from '../services/queries';

const WA_PHONE = (import.meta.env.VITE_SITENEST_WA_PHONE || '972546363350') as string;

// ────────────────────────────────────────────────────────────────────
// Translation helpers
// ────────────────────────────────────────────────────────────────────
function translateAction(action: string): string {
  const map: Record<string, string> = {
    build_whatsapp_message: '📱 שלח WhatsApp',
    mark_outreach_sent: '✅ סמן כנשלח',
    assign_campaign: '📡 שייך לקמפיין',
    qualify: '⭐ אשר כליד',
    convert: '🔄 המר לעסק',
    approve: '✅ אשר',
    reject: '❌ דחה',
    apply: '⚡ בצע',
  };
  return map[action] || action;
}

function translateQueueType(qt: string): string {
  const map: Record<string, string> = {
    outreach_ready: '📤 עסקים מוכנים לפנייה',
    lead_review: '🎯 לידים לסקירה',
    approvals: '✅ ממתין לאישור',
    payments: '💳 תשלומים ממתינים',
    expiring_drafts: '⏳ דראפטים פגי תוקף',
    feedback_review: '💬 פידבק לטיפול',
  };
  return map[qt] || qt;
}

function translatePriority(p: string): { label: string; color: string } {
  if (p === 'high') return { label: 'דחוף', color: '#dc2626' };
  if (p === 'medium') return { label: 'בינוני', color: '#f97316' };
  return { label: 'רגיל', color: '#6b7280' };
}

function translateApprovalType(t: string): string {
  const map: Record<string, string> = {
    template_update: 'עדכון תבנית',
    campaign_launch: 'השקת קמפיין',
    site_activation: 'הפעלת אתר',
    pricing_change: 'שינוי מחיר',
    outreach_batch: 'אצווה שליחה',
    lead_import: 'ייבוא לידים',
    business_qualification: 'כשירות עסק',
  };
  return map[t] || t;
}

// ────────────────────────────────────────────────────────────────────
// Stat box
// ────────────────────────────────────────────────────────────────────
function StatBox({ icon, value, label, urgent }: { icon: string; value: number | string; label: string; urgent?: boolean }) {
  return (
    <div style={{
      background: urgent && Number(value) > 0 ? '#fef2f2' : 'white',
      border: `2px solid ${urgent && Number(value) > 0 ? '#fca5a5' : '#e5e7eb'}`,
      borderRadius: 14, padding: '18px 20px', textAlign: 'center',
      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
    }}>
      <div style={{ fontSize: 28, marginBottom: 4 }}>{icon}</div>
      <div style={{ fontSize: 28, fontWeight: 800, color: urgent && Number(value) > 0 ? '#dc2626' : '#1f2937' }}>{value}</div>
      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{label}</div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// Queue section
// ────────────────────────────────────────────────────────────────────
function QueueSection({ queueType, onDone }: { queueType: string; onDone: () => void }) {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [busy, setBusy] = useState<Record<number, string>>({});
  const [msgs, setMsgs] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    getQueueItems(queueType)
      .then(setItems)
      .catch(() => { })
      .finally(() => setLoading(false));
  }, [queueType]);

  useEffect(() => { load(); }, [load]);

  const handleAction = async (item: QueueItem, action: string) => {
    setBusy(prev => ({ ...prev, [item.id]: action }));
    try {
      if (action === 'build_whatsapp_message') {
        // Build WA message first, then open WA
        const res: any = await buildBusinessWhatsApp(item.linked_entity_id);
        const waText = encodeURIComponent(res?.message || `שלום! יש לנו הצעה מיוחדת לעסק שלכם 😊`);
        const phone = res?.phone ? res.phone.replace(/\D/g, '').replace(/^0/, '972') : WA_PHONE;
        window.open(`https://wa.me/${phone}?text=${waText}`, '_blank');
        setMsgs(prev => ({ ...prev, [item.id]: '✅ הודעה נפתחה ב-WhatsApp' }));
      } else {
        await runQueueAction(queueType, item.id, action);
        setMsgs(prev => ({ ...prev, [item.id]: `✅ בוצע: ${translateAction(action)}` }));
        setTimeout(() => { load(); onDone(); }, 800);
      }
    } catch {
      setMsgs(prev => ({ ...prev, [item.id]: '❌ שגיאה בביצוע הפעולה' }));
    } finally {
      setBusy(prev => { const n = { ...prev }; delete n[item.id]; return n; });
    }
  };

  if (loading) return <div style={{ color: '#9ca3af', fontSize: 13, padding: '8px 0' }}>⏳ טוען...</div>;
  if (!items.length) return <div style={{ color: '#9ca3af', fontSize: 13, padding: '8px 0' }}>✅ אין פריטים לטיפול</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
      {items.map(item => {
        const prio = translatePriority(item.priority);
        return (
          <div key={item.id} style={{
            background: '#fafafa', borderRadius: 12, padding: '12px 16px',
            border: `1.5px solid ${item.priority === 'high' ? '#fca5a5' : '#e5e7eb'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, marginBottom: 8 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, color: '#1f2937' }}>{item.title}</div>
                {item.subtitle && <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{item.subtitle}</div>}
              </div>
              <span style={{ background: prio.color, color: 'white', borderRadius: 20, padding: '2px 10px', fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap', flexShrink: 0 }}>
                {prio.label}
              </span>
            </div>

            {msgs[item.id] && (
              <div style={{ fontSize: 12, color: msgs[item.id].startsWith('✅') ? '#065f46' : '#991b1b', marginBottom: 8, fontWeight: 600 }}>
                {msgs[item.id]}
              </div>
            )}

            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {item.available_actions?.map(action => (
                <button key={action} disabled={!!busy[item.id]}
                  onClick={() => handleAction(item, action)}
                  style={{
                    background: action === 'build_whatsapp_message' ? '#dcfce7' :
                      action === 'mark_outreach_sent' ? '#dbeafe' :
                        action === 'qualify' ? '#ede9fe' : '#f3f4f6',
                    color: action === 'build_whatsapp_message' ? '#15803d' :
                      action === 'mark_outreach_sent' ? '#1e40af' :
                        action === 'qualify' ? '#6d28d9' : '#374151',
                    border: 'none', borderRadius: 8, padding: '7px 14px',
                    fontSize: 13, fontWeight: 600, cursor: 'pointer',
                    opacity: busy[item.id] ? 0.6 : 1,
                  }}>
                  {busy[item.id] === action ? '⏳' : translateAction(action)}
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// Approvals section
// ────────────────────────────────────────────────────────────────────
function ApprovalsSection({ onDone }: { onDone: () => void }) {
  const [items, setItems] = useState<Approval[]>([]);
  const [busy, setBusy] = useState<Record<number, string>>({});
  const [msgs, setMsgs] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    getApprovals()
      .then(all => setItems(all.filter(a => a.status === 'pending')))
      .catch(() => { })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleApprove = async (item: Approval) => {
    setBusy(prev => ({ ...prev, [item.id]: 'approve' }));
    try {
      await approve(item.id);
      setMsgs(prev => ({ ...prev, [item.id]: '✅ אושר!' }));
      setTimeout(() => { load(); onDone(); }, 600);
    } catch { setMsgs(prev => ({ ...prev, [item.id]: '❌ שגיאה' })); }
    finally { setBusy(prev => { const n = { ...prev }; delete n[item.id]; return n; }); }
  };

  const handleReject = async (item: Approval) => {
    setBusy(prev => ({ ...prev, [item.id]: 'reject' }));
    try {
      await reject(item.id);
      setMsgs(prev => ({ ...prev, [item.id]: '🚫 נדחה' }));
      setTimeout(() => { load(); onDone(); }, 600);
    } catch { setMsgs(prev => ({ ...prev, [item.id]: '❌ שגיאה' })); }
    finally { setBusy(prev => { const n = { ...prev }; delete n[item.id]; return n; }); }
  };

  if (loading) return <div style={{ color: '#9ca3af', fontSize: 13 }}>⏳ טוען...</div>;
  if (!items.length) return <div style={{ color: '#9ca3af', fontSize: 13 }}>✅ אין פריטים ממתינים לאישור</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
      {items.map(item => (
        <div key={item.id} style={{ background: '#fffbeb', border: '1.5px solid #fcd34d', borderRadius: 12, padding: '14px 16px' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 4 }}>{item.title}</div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>
            סוג: {translateApprovalType(item.approval_type)}
          </div>
          {item.summary && <div style={{ fontSize: 12, color: '#374151', background: 'white', borderRadius: 8, padding: '6px 10px', marginBottom: 10 }}>{item.summary}</div>}

          {msgs[item.id] && (
            <div style={{ fontSize: 12, fontWeight: 600, color: msgs[item.id].startsWith('✅') ? '#065f46' : '#991b1b', marginBottom: 8 }}>
              {msgs[item.id]}
            </div>
          )}

          <div style={{ display: 'flex', gap: 8 }}>
            <button disabled={!!busy[item.id]} onClick={() => handleApprove(item)}
              style={{ background: '#d1fae5', color: '#065f46', border: 'none', borderRadius: 8, padding: '8px 20px', fontSize: 14, fontWeight: 700, cursor: 'pointer', opacity: busy[item.id] ? 0.6 : 1 }}>
              {busy[item.id] === 'approve' ? '⏳' : '✅ אשר ובצע'}
            </button>
            <button disabled={!!busy[item.id]} onClick={() => handleReject(item)}
              style={{ background: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: 8, padding: '8px 20px', fontSize: 14, fontWeight: 700, cursor: 'pointer', opacity: busy[item.id] ? 0.6 : 1 }}>
              {busy[item.id] === 'reject' ? '⏳' : '❌ דחה'}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// Grok CEO Panel
// ────────────────────────────────────────────────────────────────────
function GrokCEOPanel() {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<GrokCEOResponse | null>(null);
  const [execStatus, setExecStatus] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);

  const handleAsk = async () => {
    setLoading(true);
    setResponse(null);
    setExecStatus(null);
    try {
      const res = await askGrok(message.trim() || undefined);
      setResponse(res);
    } catch {
      setExecStatus('❌ שגיאה בחיבור לגרוק');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!response) return;
    setExecuting(true);
    try {
      const result = await executeGrokAction(response.system_execution_payload as GrokExecutionPayload);
      setExecStatus(result.message);
      setResponse(null);
    } catch {
      setExecStatus('❌ שגיאה בביצוע הפעולה');
    } finally {
      setExecuting(false);
    }
  };

  const handleCancel = () => {
    setResponse(null);
    setExecStatus(null);
  };

  const hasAction = response?.system_execution_payload?.action_type &&
    response.system_execution_payload.action_type !== 'NONE';

  return (
    <div style={{
      background: 'linear-gradient(135deg, #0f0f1a, #1a1a2e)',
      border: '2px solid #7c3aed',
      borderRadius: 16,
      padding: '20px 22px',
      marginBottom: 24,
      color: 'white',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
        <div style={{ fontSize: 32 }}>🤖</div>
        <div>
          <div style={{ fontWeight: 800, fontSize: 18, color: '#a78bfa' }}>גרוק — מנכ"ל AI</div>
          <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>מנתח את המערכת ומציע מהלכים אסטרטגיים בעברית</div>
        </div>
      </div>

      {/* Input area */}
      {!response && (
        <div style={{ marginBottom: 14 }}>
          <textarea
            value={message}
            onChange={e => setMessage(e.target.value)}
            placeholder="כתוב הנחיה לגרוק... או השאר ריק לניתוח אוטומטי של המצב הנוכחי"
            rows={3}
            style={{
              width: '100%',
              background: '#1e1b4b',
              border: '1.5px solid #4c1d95',
              borderRadius: 10,
              padding: '10px 14px',
              fontSize: 14,
              color: 'white',
              resize: 'vertical',
              fontFamily: 'inherit',
              direction: 'rtl',
              boxSizing: 'border-box',
            }}
          />
          <button
            onClick={handleAsk}
            disabled={loading}
            style={{
              marginTop: 10,
              background: loading ? '#4c1d95' : '#7c3aed',
              color: 'white',
              border: 'none',
              borderRadius: 10,
              padding: '10px 28px',
              fontSize: 15,
              fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            {loading ? (
              <><span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⏳</span> גרוק חושב...</>
            ) : '💬 שאל את גרוק'}
          </button>
        </div>
      )}

      {/* Response */}
      {response && (
        <div style={{ direction: 'rtl' }}>
          {/* Understanding */}
          <div style={{ background: '#1e1b4b', borderRadius: 10, padding: '12px 16px', marginBottom: 12 }}>
            <div style={{ fontWeight: 700, fontSize: 12, color: '#818cf8', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>🎯 מה גרוק הבין</div>
            <div style={{ fontSize: 14, lineHeight: 1.7, color: '#e0e7ff' }}>{response.understanding_and_analysis}</div>
          </div>

          {/* Strategic insight */}
          <div style={{ background: '#14301a', border: '1px solid #166534', borderRadius: 10, padding: '12px 16px', marginBottom: 12 }}>
            <div style={{ fontWeight: 700, fontSize: 12, color: '#4ade80', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>💡 תובנה אסטרטגית</div>
            <div style={{ fontSize: 14, lineHeight: 1.7, color: '#d1fae5' }}>{response.strategic_insight}</div>
          </div>

          {/* Action plan */}
          <div style={{ background: '#172554', border: '1px solid #1e40af', borderRadius: 10, padding: '12px 16px', marginBottom: 12 }}>
            <div style={{ fontWeight: 700, fontSize: 12, color: '#60a5fa', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>📋 תוכנית פעולה</div>
            <div style={{ fontSize: 14, lineHeight: 1.7, color: '#dbeafe' }}>{response.proposed_action_plan}</div>
          </div>

          {/* Message to Ariel */}
          <div style={{ background: '#1c1917', border: '1.5px solid #d97706', borderRadius: 10, padding: '14px 16px', marginBottom: 16 }}>
            <div style={{ fontWeight: 700, fontSize: 12, color: '#fbbf24', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>📩 הודעה לאריאל</div>
            <div style={{ fontSize: 15, lineHeight: 1.7, color: '#fef3c7', fontWeight: 500 }}>{response.message_to_ariel}</div>
          </div>

          {/* Payload preview */}
          {hasAction && (
            <div style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 10, padding: '10px 14px', marginBottom: 14 }}>
              <div style={{ fontWeight: 700, fontSize: 11, color: '#64748b', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>⚙️ פעולה מוצעת</div>
              <div style={{ fontSize: 12, color: '#94a3b8', fontFamily: 'monospace' }}>
                <span style={{ color: '#38bdf8' }}>{response.system_execution_payload.action_type}</span>
                {response.system_execution_payload.target_component && (
                  <> → <span style={{ color: '#a78bfa' }}>{response.system_execution_payload.target_component}</span></>
                )}
              </div>
              {response.system_execution_payload.new_value && (
                <div style={{ marginTop: 6, fontSize: 11, color: '#64748b', maxHeight: 80, overflow: 'hidden', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                  {response.system_execution_payload.new_value.substring(0, 300)}{response.system_execution_payload.new_value.length > 300 ? '...' : ''}
                </div>
              )}
            </div>
          )}

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {hasAction && (
              <button
                onClick={handleApprove}
                disabled={executing}
                style={{
                  background: executing ? '#065f46' : '#10b981',
                  color: 'white', border: 'none', borderRadius: 10,
                  padding: '10px 26px', fontSize: 15, fontWeight: 700,
                  cursor: executing ? 'not-allowed' : 'pointer',
                  opacity: executing ? 0.7 : 1,
                }}
              >
                {executing ? '⏳ מבצע...' : '✅ אשר ובצע'}
              </button>
            )}
            <button
              onClick={() => { setMessage(''); handleCancel(); }}
              disabled={executing}
              style={{
                background: '#fee2e2', color: '#991b1b', border: 'none',
                borderRadius: 10, padding: '10px 26px', fontSize: 15,
                fontWeight: 700, cursor: executing ? 'not-allowed' : 'pointer',
              }}
            >
              {hasAction ? '❌ בטל' : '🔄 שאל שוב'}
            </button>
          </div>
        </div>
      )}

      {/* Execution result */}
      {execStatus && (
        <div style={{
          marginTop: 14,
          background: execStatus.startsWith('✅') ? '#064e3b' : execStatus.startsWith('⏳') ? '#1e1b4b' : '#450a0a',
          border: `1px solid ${execStatus.startsWith('✅') ? '#10b981' : execStatus.startsWith('⏳') ? '#818cf8' : '#ef4444'}`,
          borderRadius: 10, padding: '10px 16px',
          fontSize: 14, color: 'white', fontWeight: 600, direction: 'rtl',
        }}>
          {execStatus}
          {execStatus && (
            <button
              onClick={() => { setExecStatus(null); setMessage(''); }}
              style={{ marginRight: 10, background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: 12 }}
            >
              ✕ סגור
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// MAIN PAGE
// ────────────────────────────────────────────────────────────────────
export default function CEOConsolePage() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [queues, setQueues] = useState<QueueSummary[]>([]);
  const [note, setNote] = useState('');
  const [noteMsg, setNoteMsg] = useState('');
  const [openQueue, setOpenQueue] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const reload = useCallback(() => {
    Promise.all([getDigest(), getHealth(), getQueueSummary()])
      .then(([d, h, q]) => { setDigest(d); setHealth(h); setQueues(q); })
      .catch(() => { });
  }, []);

  useEffect(() => { reload(); }, [reload, tick]);

  const handleNote = async () => {
    if (!note.trim()) return;
    await addCeoDecisionNote(note).catch(() => { });
    setNoteMsg('✅ הנחיה נשמרה');
    setNote('');
    setTimeout(() => setNoteMsg(''), 3000);
  };

  const totalUrgent = queues.filter(q => q.count > 0).length;
  const healthColor = health?.overall_status === 'healthy' ? '#065f46' :
    health?.overall_status === 'warning' ? '#92400e' : '#991b1b';
  const healthBg = health?.overall_status === 'healthy' ? '#d1fae5' :
    health?.overall_status === 'warning' ? '#fef3c7' : '#fee2e2';

  return (
    <div dir="rtl" style={{ maxWidth: 900, margin: '0 auto' }}>
      <SectionTitle>🧠 מרכז מנכ"ל</SectionTitle>

      {/* Health banner */}
      {health && (
        <div style={{
          background: healthBg, border: `1.5px solid ${healthColor}`,
          borderRadius: 12, padding: '12px 18px', marginBottom: 18,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
        }}>
          <span style={{ fontWeight: 700, fontSize: 14, color: healthColor }}>
            {health.overall_status === 'healthy' ? '✅ המערכת תקינה' :
              health.overall_status === 'warning' ? '⚠️ יש התראות' : '🚨 בעיה דורשת טיפול'}
          </span>
          {totalUrgent > 0 && (
            <span style={{ background: '#f97316', color: 'white', borderRadius: 20, padding: '3px 14px', fontSize: 12, fontWeight: 700 }}>
              {totalUrgent} תורים פעילים
            </span>
          )}
          <button onClick={reload} style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: 20, padding: '4px 14px', fontSize: 12, cursor: 'pointer', color: '#374151' }}>
            🔄 רענן
          </button>
        </div>
      )}

      {/* Stats grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 12, marginBottom: 20 }}>
        <StatBox icon="📤" value={digest?.outreach_ready_count ?? 0} label="מוכנים לפנייה" urgent />
        <StatBox icon="✅" value={digest?.approval_queue_count ?? 0} label="ממתינים לאישור" urgent />
        <StatBox icon="💳" value={digest?.payments_pending ?? 0} label="תשלומים ממתינים" urgent />
        <StatBox icon="⏳" value={digest?.expiring_drafts ?? 0} label="דראפטים פגי תוקף" />
        <StatBox icon="🎯" value={digest?.qualified_leads ?? 0} label="לידים מוכשרים" />
      </div>

      {/* Executive summary */}
      {digest?.executive_summary && (
        <div style={{ background: 'linear-gradient(135deg,#ede9fe,#dbeafe)', border: '1.5px solid #a5b4fc', borderRadius: 14, padding: '16px 18px', marginBottom: 20 }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#3730a3', marginBottom: 8 }}>📋 סיכום מנהלים</div>
          <p style={{ fontSize: 14, color: '#1e1b4b', margin: 0, lineHeight: 1.6 }}>
            {digest.executive_summary}
          </p>
        </div>
      )}

      {/* Approvals */}
      <div style={{ background: 'white', borderRadius: 14, padding: '16px 20px', marginBottom: 16, boxShadow: '0 2px 8px rgba(0,0,0,0.05)', border: '1.5px solid #fcd34d' }}>
        <div style={{ fontWeight: 700, fontSize: 15, color: '#92400e', marginBottom: 4 }}>
          ✅ אישורים ממתינים לטיפול שלך
        </div>
        <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 8 }}>כל פריט כאן ממתין לאישור שלך לפני ביצוע</div>
        <ApprovalsSection onDone={() => setTick(t => t + 1)} />
      </div>

      {/* Queue sections */}
      {queues.filter(q => q.count > 0).map(q => (
        <div key={q.queue_type} style={{
          background: 'white', borderRadius: 14, padding: '16px 20px', marginBottom: 14,
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          border: `1.5px solid ${q.count > 0 ? '#e5e7eb' : '#f3f4f6'}`,
        }}>
          <button
            onClick={() => setOpenQueue(openQueue === q.queue_type ? null : q.queue_type)}
            style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'none', border: 'none', cursor: 'pointer', padding: 0, textAlign: 'right' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontWeight: 700, fontSize: 15, color: '#1f2937' }}>{translateQueueType(q.queue_type)}</span>
              <span style={{ background: q.count > 0 ? '#f97316' : '#e5e7eb', color: q.count > 0 ? 'white' : '#6b7280', borderRadius: 20, padding: '2px 10px', fontSize: 12, fontWeight: 700 }}>
                {q.count}
              </span>
            </div>
            <span style={{ fontSize: 18, color: '#9ca3af' }}>{openQueue === q.queue_type ? '▲' : '▼'}</span>
          </button>

          {openQueue === q.queue_type && (
            <QueueSection queueType={q.queue_type} onDone={() => setTick(t => t + 1)} />
          )}
        </div>
      ))}

      {/* Empty queues shown collapsed */}
      {queues.filter(q => q.count === 0).length > 0 && (
        <div style={{ background: '#f9fafb', borderRadius: 14, padding: '12px 20px', marginBottom: 16, border: '1px solid #f3f4f6' }}>
          <div style={{ fontSize: 13, color: '#9ca3af', fontWeight: 500 }}>
            📭 תורים ללא פריטים:{' '}
            {queues.filter(q => q.count === 0).map(q => translateQueueType(q.queue_type).replace(/^[^\s]+\s/, '')).join(' · ')}
          </div>
        </div>
      )}

      {/* Pressure notes */}
      {digest?.pressure_notes && digest.pressure_notes.length > 0 && (
        <div style={{ background: 'white', borderRadius: 14, padding: '16px 20px', marginBottom: 16, boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#374151', marginBottom: 10 }}>📊 לחץ תפעולי</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {digest.pressure_notes.map((n, i) => (
              <span key={i} style={{ background: '#f3f4f6', color: '#374151', borderRadius: 20, padding: '4px 14px', fontSize: 12 }}>
                {n}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Health drivers */}
      {health?.drivers && health.drivers.length > 0 && (
        <div style={{ background: 'white', borderRadius: 14, padding: '16px 20px', marginBottom: 16, boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#374151', marginBottom: 10 }}>🔍 גורמי מצב</div>
          {health.drivers.map((d, i) => (
            <div key={i} style={{ fontSize: 13, color: '#4b5563', padding: '4px 0', borderBottom: i < (health.drivers?.length ?? 0) - 1 ? '1px solid #f3f4f6' : 'none' }}>
              · {d}
            </div>
          ))}
        </div>
      )}

      {/* Grok CEO Panel */}
      <GrokCEOPanel />

      {/* Decision note */}
      <div style={{ background: 'white', borderRadius: 14, padding: '16px 20px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)', border: '1.5px solid #e5e7eb' }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: '#374151', marginBottom: 10 }}>📝 הנחיה / החלטה חדשה</div>
        <textarea
          value={note}
          onChange={e => setNote(e.target.value)}
          placeholder="כתוב כאן הנחיה, החלטה, או הערה לצוות..."
          rows={3}
          style={{ width: '100%', border: '1.5px solid #e5e7eb', borderRadius: 10, padding: '10px 12px', fontSize: 14, resize: 'vertical', fontFamily: 'inherit', direction: 'rtl', boxSizing: 'border-box' }}
        />
        <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={handleNote} disabled={!note.trim()}
            style={{ background: '#7c3aed', color: 'white', border: 'none', borderRadius: 10, padding: '9px 24px', fontSize: 14, fontWeight: 700, cursor: 'pointer', opacity: !note.trim() ? 0.5 : 1 }}>
            💾 שמור הנחיה
          </button>
          {noteMsg && <span style={{ fontSize: 13, color: '#065f46', fontWeight: 600 }}>{noteMsg}</span>}
        </div>
      </div>
    </div>
  );
}

