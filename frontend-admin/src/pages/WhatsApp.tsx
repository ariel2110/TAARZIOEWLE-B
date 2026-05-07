import { useEffect, useState, useRef, useCallback } from 'react';
import { Card, SectionTitle, Button } from '../components/ui';
import { apiGet, apiPost } from '../services/api';

// ── Types ─────────────────────────────────────────────────────────────────────
type WaStatus = {
  status: 'open' | 'connecting' | 'close' | 'error' | 'unknown';
  owner?: string;
  profile_name?: string;
  profile_picture?: string;
};

type WaQR = { connected: true } | { connected: false; base64: string; code: string; count: number };

type PendingMsg = {
  token: string;
  business_name: string;
  phone: string;
  message: string;
  preview_url?: string;
  created_at?: string;
};

// ── Status badge ──────────────────────────────────────────────────────────────
const STATUS_COLORS: Record<string, string> = {
  open: '#22c55e',
  connecting: '#f59e0b',
  close: '#ef4444',
  error: '#ef4444',
  unknown: '#9ca3af',
};

function StatusDot({ status }: { status: string }) {
  return (
    <span style={{
      display: 'inline-block',
      width: 10,
      height: 10,
      borderRadius: '50%',
      background: STATUS_COLORS[status] ?? '#9ca3af',
      marginLeft: 6,
      boxShadow: status === 'open' ? `0 0 0 3px ${STATUS_COLORS.open}33` : 'none',
    }} />
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function WhatsAppPage() {
  const [waStatus, setWaStatus] = useState<WaStatus | null>(null);
  const [qr, setQr] = useState<WaQR | null>(null);
  const [pending, setPending] = useState<PendingMsg[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [editedMsgs, setEditedMsgs] = useState<Record<string, string>>({});
  const [toast, setToast] = useState<{ text: string; ok: boolean } | null>(null);
  const qrInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  const showToast = (text: string, ok = true) => {
    setToast({ text, ok });
    setTimeout(() => setToast(null), 4000);
  };

  const fetchStatus = useCallback(async () => {
    try {
      const s = await apiGet<WaStatus>('/admin/whatsapp/status');
      setWaStatus(s);
      return s;
    } catch {
      setWaStatus({ status: 'error' });
      return null;
    }
  }, []);

  const fetchPending = useCallback(async () => {
    try {
      const msgs = await apiGet<PendingMsg[]>('/admin/whatsapp/pending-messages');
      setPending(msgs);
    } catch { /* silent */ }
  }, []);

  const startQrPolling = useCallback(() => {
    if (qrInterval.current) clearInterval(qrInterval.current);
    qrInterval.current = setInterval(async () => {
      try {
        const data = await apiGet<WaQR>('/admin/whatsapp/qr');
        setQr(data);
        if (data.connected) {
          clearInterval(qrInterval.current!);
          qrInterval.current = null;
          fetchStatus();
          showToast('✅ WhatsApp מחובר!');
        }
      } catch { /* silent */ }
    }, 20000);
  }, [fetchStatus]);

  useEffect(() => {
    Promise.all([fetchStatus(), fetchPending()]).finally(() => setLoading(false));
    return () => { if (qrInterval.current) clearInterval(qrInterval.current); };
  }, [fetchStatus, fetchPending]);

  const handleDisconnect = async () => {
    if (!confirm('לנתק את WhatsApp? תצטרך לסרוק QR מחדש.')) return;
    setActionLoading(true);
    try {
      await apiPost('/admin/whatsapp/disconnect', {});
      showToast('הניתוק בוצע', true);
      setQr(null);
      await fetchStatus();
    } catch (e: any) {
      showToast(`שגיאה: ${e.message}`, false);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReconnect = async () => {
    setActionLoading(true);
    try {
      const data = await apiPost<WaQR>('/admin/whatsapp/reconnect', {});
      setQr(data);
      if (!data.connected) {
        showToast('QR חדש מוכן — סרוק עם הטלפון', true);
        startQrPolling();
      } else {
        showToast('WhatsApp כבר מחובר ✅', true);
        fetchStatus();
      }
    } catch (e: any) {
      showToast(`שגיאה: ${e.message}`, false);
    } finally {
      setActionLoading(false);
    }
  };

  const handleApprove = async (token: string) => {
    const msg = editedMsgs[token] ?? pending.find(p => p.token === token)?.message ?? '';
    setActionLoading(true);
    try {
      const res = await apiPost<{ ok: boolean; sent_to: string }>(
        `/admin/whatsapp/approve-message/${token}`,
        { message: msg },
      );
      showToast(`✅ נשלח ל-${res.sent_to}`);
      setPending(prev => prev.filter(p => p.token !== token));
    } catch (e: any) {
      showToast(`שגיאה: ${e.message}`, false);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (token: string) => {
    if (!confirm('לדחות הודעה זו?')) return;
    setActionLoading(true);
    try {
      await apiPost(`/admin/whatsapp/reject-message/${token}`, {});
      showToast('🗑️ ההודעה נדחתה');
      setPending(prev => prev.filter(p => p.token !== token));
    } catch (e: any) {
      showToast(`שגיאה: ${e.message}`, false);
    } finally {
      setActionLoading(false);
    }
  };

  const statusLabel: Record<string, string> = {
    open: 'מחובר',
    connecting: 'מתחבר...',
    close: 'מנותק',
    error: 'שגיאה',
    unknown: 'לא ידוע',
  };

  return (
    <div className="grid" dir="rtl">
      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)',
          background: toast.ok ? '#14532d' : '#7f1d1d',
          color: '#fff', padding: '10px 24px', borderRadius: 10,
          zIndex: 9999, fontWeight: 600, fontSize: 14, boxShadow: '0 4px 20px #0006',
        }}>
          {toast.text}
        </div>
      )}

      {/* Header */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <SectionTitle>📱 WhatsApp ניהול חיבור</SectionTitle>
          {loading && <span style={{ fontSize: 12, color: '#9ca3af' }}>⏳ טוען…</span>}
        </div>

        {/* Status card */}
        <div className="cards">
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              {waStatus?.profile_picture && (
                <img src={waStatus.profile_picture} alt="avatar"
                  style={{ width: 52, height: 52, borderRadius: '50%', objectFit: 'cover' }} />
              )}
              <div>
                <div style={{ fontWeight: 700, fontSize: 17 }}>
                  {waStatus?.profile_name || 'tazo-web WhatsApp'}
                  <StatusDot status={waStatus?.status ?? 'unknown'} />
                </div>
                <div style={{ color: '#9ca3af', fontSize: 13, marginTop: 2 }}>
                  {statusLabel[waStatus?.status ?? 'unknown'] ?? waStatus?.status}
                  {waStatus?.owner && ` · ${waStatus.owner.replace('@s.whatsapp.net', '')}`}
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {waStatus?.status === 'open' ? (
                <button
                  onClick={handleDisconnect}
                  disabled={actionLoading}
                  style={{
                    padding: '9px 22px', borderRadius: 8, border: 'none',
                    background: '#ef4444', color: '#fff', fontWeight: 600,
                    fontSize: 14, cursor: 'pointer', opacity: actionLoading ? 0.6 : 1,
                  }}
                >
                  🔌 נתק WhatsApp
                </button>
              ) : (
                <button
                  onClick={handleReconnect}
                  disabled={actionLoading}
                  style={{
                    padding: '9px 22px', borderRadius: 8, border: 'none',
                    background: '#25d366', color: '#fff', fontWeight: 600,
                    fontSize: 14, cursor: 'pointer', opacity: actionLoading ? 0.6 : 1,
                  }}
                >
                  🔄 חבר מחדש / הצג QR
                </button>
              )}
              <button
                onClick={async () => { setLoading(true); await Promise.all([fetchStatus(), fetchPending()]); setLoading(false); }}
                disabled={loading}
                style={{
                  padding: '9px 18px', borderRadius: 8, border: '1px solid #374151',
                  background: 'transparent', color: '#9ca3af', fontSize: 13,
                  cursor: 'pointer', opacity: loading ? 0.6 : 1,
                }}
              >
                🔄 רענן
              </button>
            </div>
          </Card>
        </div>
      </div>

      {/* QR code section */}
      {qr && !qr.connected && (
        <div>
          <SectionTitle>📷 סרוק QR לחיבור</SectionTitle>
          <div className="cards">
            <Card>
              <p style={{ color: '#9ca3af', fontSize: 13, marginBottom: 12 }}>
                פתח WhatsApp בטלפון → הגדרות → מכשירים מקושרים → קישור מכשיר → סרוק
              </p>
              <img
                src={qr.base64}
                alt="WhatsApp QR"
                style={{ maxWidth: 260, borderRadius: 12, display: 'block', margin: '0 auto' }}
              />
              {qr.code && (
                <div style={{
                  marginTop: 14, textAlign: 'center',
                  fontFamily: 'monospace', fontSize: 18, fontWeight: 700, letterSpacing: 3,
                  color: '#f1f5f9',
                }}>
                  {qr.code.replace(/(.{4})(?=.)/g, '$1-')}
                </div>
              )}
              <p style={{ textAlign: 'center', color: '#64748b', fontSize: 12, marginTop: 8 }}>
                QR מתרענן אוטומטית כל 20 שניות
              </p>
            </Card>
          </div>
        </div>
      )}

      {/* Pending messages */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <SectionTitle>
            📋 הודעות ממתינות לאישור
            {pending.length > 0 && (
              <span style={{
                marginRight: 8, background: '#f59e0b', color: '#fff',
                borderRadius: 999, padding: '2px 9px', fontSize: 12, fontWeight: 700,
              }}>
                {pending.length}
              </span>
            )}
          </SectionTitle>
        </div>

        {pending.length === 0 && !loading && (
          <p style={{ color: '#64748b', fontSize: 14 }}>אין הודעות ממתינות לאישור</p>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {pending.map(msg => (
            <Card key={msg.token}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15 }}>{msg.business_name}</div>
                  <div style={{ color: '#9ca3af', fontSize: 12, marginTop: 2 }}>
                    📞 {msg.phone}
                    {msg.created_at && ` · ${new Date(msg.created_at).toLocaleString('he-IL')}`}
                  </div>
                </div>
                {msg.preview_url && (
                  <a
                    href={msg.preview_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: '#60a5fa', fontSize: 12, textDecoration: 'none' }}
                  >
                    👁️ תצוגה מקדימה
                  </a>
                )}
              </div>

              <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 6 }}>
                ✏️ ערוך לפני שליחה:
              </label>
              <textarea
                value={editedMsgs[msg.token] ?? msg.message ?? ''}
                onChange={e => setEditedMsgs(prev => ({ ...prev, [msg.token]: e.target.value }))}
                rows={5}
                style={{
                  width: '100%', background: '#111827', border: '1px solid #374151',
                  borderRadius: 8, color: '#e2e8f0', padding: 10, fontSize: 13,
                  fontFamily: 'inherit', lineHeight: 1.6, resize: 'vertical',
                  direction: 'rtl',
                }}
              />

              <div style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap' }}>
                <button
                  onClick={() => handleApprove(msg.token)}
                  disabled={actionLoading}
                  style={{
                    padding: '9px 22px', borderRadius: 8, border: 'none',
                    background: '#25d366', color: '#fff', fontWeight: 600,
                    fontSize: 13, cursor: 'pointer', opacity: actionLoading ? 0.6 : 1,
                  }}
                >
                  ✅ שלח ללקוח
                </button>
                <button
                  onClick={() => handleReject(msg.token)}
                  disabled={actionLoading}
                  style={{
                    padding: '9px 18px', borderRadius: 8, border: '1px solid #374151',
                    background: 'transparent', color: '#9ca3af', fontSize: 13,
                    cursor: 'pointer', opacity: actionLoading ? 0.6 : 1,
                  }}
                >
                  🗑️ דחה
                </button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
