import React, { useCallback, useEffect, useRef, useState } from 'react';
import './styles.css';

const API = import.meta.env.VITE_API_BASE_URL || 'https://api.tazo-web.com/api/v1';

// ── Types ──────────────────────────────────────────────────────────
interface Me {
  customer_account_id: number;
  business_id: number;
  active_site_id: number | null;
  draft_site_id: number | null;
  phone: string;
  email: string | null;
  contact_name: string | null;
  must_change_password: boolean;
  package_name: string | null;
}
interface Overview { business: Record<string, unknown>; recent_payments: unknown[] }
interface TimelineItem { event_type: string; description: string; created_at: string }
interface EditItem { id: number; field_key: string; new_value: string; status: string; created_at: string }
interface ChangeReqItem { id: number; title: string; status: string; request_type: string; created_at: string }
interface SupportItem { id: number; subject: string; status: string; created_at: string }

// ── API helper ─────────────────────────────────────────────────────
async function apiCall(path: string, token: string, init: RequestInit = {}) {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...((init.headers as Record<string, string>) || {}),
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'שגיאה בשרת');
  return data;
}

function statusBadge(s: string) {
  const cls: Record<string, string> = { pending: 'badge-yellow', approved: 'badge-green', rejected: 'badge-red', open: 'badge-blue', resolved: 'badge-green', active: 'badge-green', draft: 'badge-yellow', confirmed: 'badge-green' };
  const lbl: Record<string, string> = { pending: 'ממתין', approved: 'אושר', rejected: 'נדחה', open: 'פתוח', resolved: 'נסגר', active: 'פעיל', draft: 'טיוטה', confirmed: 'אושר' };
  return <span className={`badge ${cls[s] || 'badge-gray'}`}>{lbl[s] || s}</span>;
}
function fmtDate(iso: string) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('he-IL', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
function fieldLbl(k: string) {
  const m: Record<string, string> = { contact_name: 'שם איש קשר', phone: 'טלפון', email: 'אימייל', address: 'כתובת', website: 'אתר', facebook_url: 'פייסבוק', instagram_url: 'אינסטגרם', description: 'תיאור', name: 'שם', category: 'קטגוריה', city: 'עיר' };
  return m[k] || k;
}

// ── Login ──────────────────────────────────────────────────────────
function LoginPage({ onLogin }: { onLogin: (token: string, me: Me) => void }) {
  const [phone, setPhone] = useState('');
  const [pass, setPass] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(''); setLoading(true);
    try {
      const data = await fetch(`${API}/customer/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone, password: pass }) }).then(r => r.json());
      if (!data.access_token) { setErr(data.detail || 'כניסה נכשלה'); return; }
      localStorage.setItem('customer_token', data.access_token);
      const me: Me = await apiCall('/customer/me', data.access_token);
      onLogin(data.access_token, me);
    } catch (e: unknown) { setErr(e instanceof Error ? e.message : 'שגיאה'); }
    finally { setLoading(false); }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="login-logo">🏪</div>
        <div className="login-title">פורטל לקוחות</div>
        <div className="login-subtitle">tazo-web — כניסה לניהול האתר שלך</div>
        {err && <div className="alert alert-error" style={{ marginBottom: 16 }}>{err}</div>}
        <form onSubmit={submit}>
          <label>מספר טלפון</label>
          <input type="tel" value={phone} onChange={e => setPhone(e.target.value)} placeholder="05XXXXXXXX" required autoFocus />
          <label>סיסמה</label>
          <input type="password" value={pass} onChange={e => setPass(e.target.value)} placeholder="הסיסמה שלך" required />
          <button className="btn-primary" type="submit" disabled={loading}>{loading ? '⏳ מתחבר...' : '🔐 כניסה'}</button>
        </form>
        <p className="muted" style={{ textAlign: 'center', marginTop: 16, fontSize: 12 }}>קיבלת סיסמה זמנית? הכנס אותה כאן ותתבקש להחליף אחרי הכניסה.</p>
      </div>
    </div>
  );
}

// ── Change Password Banner ─────────────────────────────────────────
function ChangePasswordBanner({ token, onDone }: { token: string; onDone: () => void }) {
  const [cur, setCur] = useState(''); const [nw, setNw] = useState(''); const [nw2, setNw2] = useState(''); const [msg, setMsg] = useState(''); const [loading, setLoading] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (nw !== nw2) { setMsg('הסיסמאות אינן תואמות'); return; }
    if (nw.length < 6) { setMsg('מינימום 6 תווים'); return; }
    setLoading(true);
    try {
      await apiCall('/customer/change-password', token, { method: 'POST', body: JSON.stringify({ current_password: cur, new_password: nw }) });
      setMsg('✅ הסיסמה שונתה!'); setTimeout(onDone, 1200);
    } catch (e: unknown) { setMsg(e instanceof Error ? e.message : 'שגיאה'); }
    finally { setLoading(false); }
  }
  return (
    <div className="pw-banner">
      <div className="pw-banner-title">🔑 נדרש לשנות סיסמה בכניסה ראשונה</div>
      <p className="muted" style={{ marginBottom: 16 }}>הוזנת עם סיסמה זמנית. אנא צור סיסמה אישית חדשה.</p>
      {msg && <div className={`alert ${msg.startsWith('✅') ? 'alert-success' : 'alert-error'}`} style={{ marginBottom: 10 }}>{msg}</div>}
      <form onSubmit={submit} style={{ display: 'grid', gap: 10, maxWidth: 360 }}>
        <input className="form-input" type="password" value={cur} onChange={e => setCur(e.target.value)} placeholder="סיסמה זמנית נוכחית" required />
        <input className="form-input" type="password" value={nw} onChange={e => setNw(e.target.value)} placeholder="סיסמה חדשה (מינ' 6 תווים)" required />
        <input className="form-input" type="password" value={nw2} onChange={e => setNw2(e.target.value)} placeholder="אישור סיסמה חדשה" required />
        <button className="btn-submit" type="submit" disabled={loading}>{loading ? '⏳' : '💾 שמור סיסמה חדשה'}</button>
      </form>
    </div>
  );
}

// ── Overview Tab ───────────────────────────────────────────────────
function OverviewTab({ token, me }: { token: string; me: Me }) {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  useEffect(() => {
    Promise.all([apiCall('/customer/overview', token), apiCall('/customer/timeline', token)])
      .then(([o, t]) => { setOverview(o); setTimeline((t as TimelineItem[]).slice(0, 8)); }).catch(() => { });
  }, [token]);
  const biz = overview?.business as Record<string, string | number> | undefined;
  return (
    <>
      <div className="stats-row">
        <div className="stat-box"><div className="stat-icon">🏪</div><div className="stat-value" style={{ fontSize: 16, wordBreak: 'break-word' }}>{biz?.name || '—'}</div><div className="stat-label">שם העסק</div></div>
        <div className="stat-box"><div className="stat-icon">📦</div><div className="stat-value" style={{ fontSize: 18 }}>{me.package_name || 'Demo'}</div><div className="stat-label">חבילה</div></div>
        <div className="stat-box"><div className="stat-icon">{me.active_site_id ? '🌐' : '📝'}</div><div className="stat-value" style={{ fontSize: 16 }}>{me.active_site_id ? 'פעיל' : me.draft_site_id ? 'טיוטה' : 'ממתין'}</div><div className="stat-label">סטטוס אתר</div></div>
        <div className="stat-box"><div className="stat-icon">💳</div><div className="stat-value">{(overview?.recent_payments as unknown[])?.length || 0}</div><div className="stat-label">תשלומים</div></div>
      </div>
      <div className="grid-2">
        <div className="card">
          <div className="card-title">🏪 פרטי העסק</div>
          {biz ? ['name', 'category', 'city', 'address', 'phone', 'website'].filter(k => biz[k]).map(k => (
            <div className="info-row" key={k}><span className="info-label">{fieldLbl(k)}</span><span className="info-value">{String(biz[k])}</span></div>
          )) : <p className="muted">⏳ טוען...</p>}
        </div>
        <div className="card">
          <div className="card-title">📋 החשבון שלי</div>
          {[['טלפון', me.phone], ['אימייל', me.email || '—'], ['שם', me.contact_name || '—'], ['אתר פעיל', me.active_site_id ? `#${me.active_site_id}` : '—'], ['טיוטה', me.draft_site_id ? `#${me.draft_site_id}` : '—']].map(([l, v]) => (
            <div className="info-row" key={l as string}><span className="info-label">{l as string}</span><span className="info-value">{v as string}</span></div>
          ))}
          <div className="info-row"><span className="info-label">חבילה</span><span className="info-value"><span className="pkg-badge">{me.package_name || 'Demo'}</span></span></div>
        </div>
      </div>
      {timeline.length > 0 && (
        <div className="card">
          <div className="card-title">⏱️ היסטוריית פעילות</div>
          <div className="timeline">
            {timeline.map((t, i) => (
              <div className="timeline-item" key={i}><div className="timeline-dot" /><div className="timeline-content"><div className="timeline-label">{t.description || t.event_type}</div><div className="timeline-time">{fmtDate(t.created_at)}</div></div></div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

// ── Edit Info Tab ──────────────────────────────────────────────────
function EditInfoTab({ token }: { token: string }) {
  const [items, setItems] = useState<EditItem[]>([]); const [fieldKey, setFieldKey] = useState('contact_name'); const [fieldValue, setFieldValue] = useState(''); const [msg, setMsg] = useState(''); const [loading, setLoading] = useState(false);
  const load = useCallback(() => apiCall('/customer/edit-submissions', token).then(setItems).catch(() => { }), [token]);
  useEffect(() => { load(); }, [load]);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setLoading(true);
    try { await apiCall('/customer/edit-submissions', token, { method: 'POST', body: JSON.stringify({ field_key: fieldKey, new_value: fieldValue }) }); setMsg('✅ בקשת עריכה נשלחה לאישור'); setFieldValue(''); load(); }
    catch (e: unknown) { setMsg(e instanceof Error ? e.message : 'שגיאה'); }
    finally { setLoading(false); }
  }
  return (
    <>
      <div className="card">
        <div className="card-title">✏️ בקשת שינוי פרטים</div>
        <p className="muted" style={{ marginBottom: 16 }}>כל שינוי עובר לאישור הצוות טרם עדכונו באתר.</p>
        {msg && <div className={`alert ${msg.startsWith('✅') ? 'alert-success' : 'alert-error'}`} style={{ marginBottom: 12 }}>{msg}</div>}
        <form onSubmit={submit} style={{ display: 'grid', gap: 12, maxWidth: 440 }}>
          <div className="form-group"><label>שדה לשינוי</label>
            <select className="form-select" value={fieldKey} onChange={e => setFieldKey(e.target.value)}>
              {[['contact_name', 'שם איש קשר'], ['phone', 'טלפון עסק'], ['email', 'אימייל'], ['address', 'כתובת'], ['facebook_url', 'פייסבוק'], ['instagram_url', 'אינסטגרם'], ['description', 'תיאור העסק']].map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
          <div className="form-group"><label>ערך חדש</label><input className="form-input" value={fieldValue} onChange={e => setFieldValue(e.target.value)} placeholder="הכנס ערך חדש" required /></div>
          <button className="btn-submit" type="submit" disabled={loading || !fieldValue.trim()}>{loading ? '⏳' : '📤 שלח לאישור'}</button>
        </form>
      </div>
      <div className="card">
        <div className="card-title">📋 בקשות עריכה קודמות ({items.length})</div>
        {items.length === 0 ? <div className="empty-note">אין בקשות עריכה עדיין</div> : (
          <div className="item-list">{items.map(item => (
            <div className="item-card" key={item.id}>
              <div className="item-card-top"><div><div className="item-card-title">{fieldLbl(item.field_key)}: <span style={{ fontWeight: 400 }}>{item.new_value}</span></div></div>{statusBadge(item.status)}</div>
              <div className="item-card-sub">{fmtDate(item.created_at)}</div>
            </div>
          ))}</div>
        )}
      </div>
    </>
  );
}

// ── Change Requests Tab ────────────────────────────────────────────
function ChangeRequestsTab({ token }: { token: string }) {
  const [items, setItems] = useState<ChangeReqItem[]>([]); const [title, setTitle] = useState(''); const [desc, setDesc] = useState(''); const [reqType, setReqType] = useState('general'); const [msg, setMsg] = useState(''); const [loading, setLoading] = useState(false);
  const load = useCallback(() => apiCall('/customer/change-requests', token).then(setItems).catch(() => { }), [token]);
  useEffect(() => { load(); }, [load]);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setLoading(true);
    try { await apiCall('/customer/change-requests', token, { method: 'POST', body: JSON.stringify({ request_type: reqType, title, description: desc }) }); setMsg('✅ הבקשה נשלחה'); setTitle(''); setDesc(''); load(); }
    catch (e: unknown) { setMsg(e instanceof Error ? e.message : 'שגיאה'); }
    finally { setLoading(false); }
  }
  return (
    <>
      <div className="card">
        <div className="card-title">📬 בקשת שינוי כללית</div>
        <p className="muted" style={{ marginBottom: 16 }}>צריך שינוי גדול? תאר אותו כאן ונטפל.</p>
        {msg && <div className={`alert ${msg.startsWith('✅') ? 'alert-success' : 'alert-error'}`} style={{ marginBottom: 12 }}>{msg}</div>}
        <form onSubmit={submit} style={{ display: 'grid', gap: 12, maxWidth: 480 }}>
          <div className="form-group"><label>סוג בקשה</label>
            <select className="form-select" value={reqType} onChange={e => setReqType(e.target.value)}>
              {[['general', 'כללי'], ['design', 'עיצוב'], ['content', 'תוכן'], ['technical', 'טכני'], ['billing', 'חיוב']].map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
          <div className="form-group"><label>כותרת</label><input className="form-input" value={title} onChange={e => setTitle(e.target.value)} placeholder="תיאור קצר" required /></div>
          <div className="form-group"><label>פירוט</label><textarea className="form-textarea" value={desc} onChange={e => setDesc(e.target.value)} placeholder="פרט את הבקשה..." required /></div>
          <button className="btn-submit" type="submit" disabled={loading || !title.trim()}>{loading ? '⏳' : '📤 שלח בקשה'}</button>
        </form>
      </div>
      <div className="card">
        <div className="card-title">📋 בקשות קודמות ({items.length})</div>
        {items.length === 0 ? <div className="empty-note">אין בקשות שינוי עדיין</div> : (
          <div className="item-list">{items.map(item => (
            <div className="item-card" key={item.id}>
              <div className="item-card-top"><div className="item-card-title">{item.title}</div>{statusBadge(item.status)}</div>
              <div className="item-card-sub">{item.request_type} · {fmtDate(item.created_at)}</div>
            </div>
          ))}</div>
        )}
      </div>
    </>
  );
}

// ── Support Tab ────────────────────────────────────────────────────
function SupportTab({ token }: { token: string }) {
  const [items, setItems] = useState<SupportItem[]>([]); const [subject, setSubject] = useState(''); const [body, setBody] = useState(''); const [msg, setMsg] = useState(''); const [loading, setLoading] = useState(false);
  const load = useCallback(() => apiCall('/customer/support', token).then(setItems).catch(() => { }), [token]);
  useEffect(() => { load(); }, [load]);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setLoading(true);
    try { await apiCall('/customer/support', token, { method: 'POST', body: JSON.stringify({ subject, message: body }) }); setMsg('✅ הודעה נשלחה!'); setSubject(''); setBody(''); load(); }
    catch (e: unknown) { setMsg(e instanceof Error ? e.message : 'שגיאה'); }
    finally { setLoading(false); }
  }
  return (
    <>
      <div className="card">
        <div className="card-title">💬 פנייה לתמיכה</div>
        <p className="muted" style={{ marginBottom: 16 }}>שאלות, בעיות טכניות — אנחנו כאן.</p>
        {msg && <div className={`alert ${msg.startsWith('✅') ? 'alert-success' : 'alert-error'}`} style={{ marginBottom: 12 }}>{msg}</div>}
        <form onSubmit={submit} style={{ display: 'grid', gap: 12, maxWidth: 480 }}>
          <div className="form-group"><label>נושא</label><input className="form-input" value={subject} onChange={e => setSubject(e.target.value)} placeholder="כותרת פנייה" required /></div>
          <div className="form-group"><label>הודעה</label><textarea className="form-textarea" rows={4} value={body} onChange={e => setBody(e.target.value)} placeholder="תאר את השאלה..." required /></div>
          <button className="btn-submit" type="submit" disabled={loading || !subject.trim()}>{loading ? '⏳' : '📨 שלח הודעה'}</button>
        </form>
      </div>
      <div className="card">
        <div className="card-title">📋 פניות קודמות ({items.length})</div>
        {items.length === 0 ? <div className="empty-note">אין פניות תמיכה עדיין</div> : (
          <div className="item-list">{items.map(item => (
            <div className="item-card" key={item.id}>
              <div className="item-card-top"><div className="item-card-title">{item.subject}</div>{statusBadge(item.status)}</div>
              <div className="item-card-sub">{fmtDate(item.created_at)}</div>
            </div>
          ))}</div>
        )}
      </div>
    </>
  );
}

// ── Settings Tab ───────────────────────────────────────────────────
function SettingsTab({ token, onPasswordChanged }: { token: string; onPasswordChanged: () => void }) {
  const [cur, setCur] = useState(''); const [nw, setNw] = useState(''); const [nw2, setNw2] = useState(''); const [msg, setMsg] = useState(''); const [loading, setLoading] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (nw !== nw2) { setMsg('הסיסמאות אינן תואמות'); return; }
    if (nw.length < 6) { setMsg('מינימום 6 תווים'); return; }
    setLoading(true);
    try { await apiCall('/customer/change-password', token, { method: 'POST', body: JSON.stringify({ current_password: cur, new_password: nw }) }); setMsg('✅ הסיסמה שונתה!'); setCur(''); setNw(''); setNw2(''); onPasswordChanged(); }
    catch (e: unknown) { setMsg(e instanceof Error ? e.message : 'שגיאה'); }
    finally { setLoading(false); }
  }
  return (
    <div className="card">
      <div className="card-title">🔑 שינוי סיסמה</div>
      {msg && <div className={`alert ${msg.startsWith('✅') ? 'alert-success' : 'alert-error'}`} style={{ marginBottom: 12 }}>{msg}</div>}
      <form onSubmit={submit} style={{ display: 'grid', gap: 12, maxWidth: 380 }}>
        <div className="form-group"><label>סיסמה נוכחית</label><input className="form-input" type="password" value={cur} onChange={e => setCur(e.target.value)} placeholder="הכנס סיסמה נוכחית" required /></div>
        <div className="form-group"><label>סיסמה חדשה</label><input className="form-input" type="password" value={nw} onChange={e => setNw(e.target.value)} placeholder="לפחות 6 תווים" required /></div>
        <div className="form-group"><label>אישור סיסמה חדשה</label><input className="form-input" type="password" value={nw2} onChange={e => setNw2(e.target.value)} placeholder="הכנס שוב" required /></div>
        <button className="btn-submit" type="submit" disabled={loading}>{loading ? '⏳' : '💾 שמור סיסמה'}</button>
      </form>
    </div>
  );
}

// ── AI Site Editor Tab ─────────────────────────────────────────────
const SECTIONS: { key: string; label: string; icon: string; hint: string }[] = [
  { key: 'hero_title', label: 'כותרת ראשית', icon: '🏷️', hint: 'המשפט הראשי שרואים בעמוד הבית' },
  { key: 'about_text', label: 'טקסט "אודות"', icon: '📝', hint: 'תיאור העסק — מי אתה, מה אתה עושה' },
  { key: 'site_title', label: 'שם האתר', icon: '🌐', hint: 'שם שמופיע בלשונית הדפדפן' },
  { key: 'contact_phone', label: 'טלפון ליצירת קשר', icon: '📞', hint: 'מספר הטלפון המוצג בדף' },
  { key: 'address', label: 'כתובת', icon: '📍', hint: 'כתובת העסק המוצגת באתר' },
  { key: 'facebook_url', label: 'קישור פייסבוק', icon: '📘', hint: 'כתובת עמוד הפייסבוק שלך' },
  { key: 'instagram_url', label: 'קישור אינסטגרם', icon: '📸', hint: 'כתובת פרופיל האינסטגרם' },
  { key: 'tiktok_url', label: 'קישור טיקטוק', icon: '🎵', hint: 'כתובת פרופיל הטיקטוק' },
];

interface SiteContent {
  current_values: Record<string, string | null>;
  site_preview_url: string | null;
  site_status: string | null;
}

interface ChatMessage {
  role: 'user' | 'ai' | 'system';
  text: string;
  suggestion?: string;
  section?: string;
  applied?: boolean;
}

function AIEditorTab({ token }: { token: string }) {
  const [siteContent, setSiteContent] = useState<SiteContent | null>(null);
  const [selectedSection, setSelectedSection] = useState<string>('hero_title');
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'system', text: '✨ שלום! אני ה-AI שיעזור לך לערוך את האתר שלך. בחר איזה חלק אתה רוצה לשנות ואמור לי מה לכתוב.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [applyingIdx, setApplyingIdx] = useState<number | null>(null);
  const [appliedCount, setAppliedCount] = useState(0);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiCall('/customer/site-content', token).then(setSiteContent).catch(() => { });
  }, [token]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const currentSection = SECTIONS.find(s => s.key === selectedSection)!;
  const currentValue = siteContent?.current_values?.[selectedSection];

  async function sendMessage() {
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: trimmed }]);
    setLoading(true);
    try {
      const res = await apiCall('/customer/ai-edit', token, {
        method: 'POST',
        body: JSON.stringify({
          message: trimmed,
          section: selectedSection,
          current_value: currentValue || null,
        }),
      });
      setMessages(prev => [
        ...prev,
        {
          role: 'ai',
          text: res.explanation || 'הנה ההצעה שלי:',
          suggestion: res.suggestion,
          section: res.section,
          applied: false,
        },
      ]);
    } catch (e: unknown) {
      setMessages(prev => [
        ...prev,
        { role: 'system', text: `❌ ${e instanceof Error ? e.message : 'שגיאה. נסה שוב.'}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function applyEdit(msgIdx: number, suggestion: string, section: string) {
    setApplyingIdx(msgIdx);
    try {
      await apiCall('/customer/apply-ai-edit', token, {
        method: 'POST',
        body: JSON.stringify({ section, new_value: suggestion, ai_suggestion: suggestion }),
      });
      setMessages(prev => prev.map((m, i) => i === msgIdx ? { ...m, applied: true } : m));
      setAppliedCount(c => c + 1);
      setMessages(prev => [
        ...prev,
        { role: 'system', text: `✅ השינוי ב"${SECTIONS.find(s => s.key === section)?.label}" נשלח לאישור הצוות ויופעל בקרוב.` },
      ]);
    } catch (e: unknown) {
      setMessages(prev => [
        ...prev,
        { role: 'system', text: `❌ ${e instanceof Error ? e.message : 'שגיאה בשמירה'}` },
      ]);
    } finally {
      setApplyingIdx(null);
    }
  }

  function rejectEdit(msgIdx: number) {
    setMessages(prev => prev.map((m, i) => i === msgIdx ? { ...m, applied: false, suggestion: undefined } : m));
    setMessages(prev => [...prev, { role: 'system', text: '↩️ הצעה בוטלה. ספר לי מה לשנות אחרת.' }]);
  }

  return (
    <div className="ai-editor-root">
      {/* ── Section selector panel ── */}
      <div className="ai-sections-panel">
        <div className="ai-sections-title">✏️ בחר חלק לעריכה</div>
        {SECTIONS.map(s => {
          const val = siteContent?.current_values?.[s.key];
          return (
            <button
              key={s.key}
              className={`ai-section-item ${selectedSection === s.key ? 'active' : ''}`}
              onClick={() => {
                setSelectedSection(s.key);
                setMessages([{ role: 'system', text: `✨ עורכים: ${s.label}. ${s.hint}. מה לשנות?` }]);
                setInput('');
              }}
            >
              <span className="ai-section-icon">{s.icon}</span>
              <span className="ai-section-info">
                <span className="ai-section-label">{s.label}</span>
                {val && <span className="ai-section-current">{val.length > 40 ? val.slice(0, 37) + '...' : val}</span>}
              </span>
            </button>
          );
        })}

        {appliedCount > 0 && (
          <div className="ai-applied-note">
            ✅ {appliedCount} שינוי{appliedCount !== 1 ? 'ים' : ''} ממתין{appliedCount !== 1 ? 'ים' : ''} לאישור
          </div>
        )}

        {siteContent?.site_preview_url && (
          <a
            className="ai-preview-link"
            href={`https://api.tazo-web.com${siteContent.site_preview_url}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            👀 צפה באתר הנוכחי
          </a>
        )}
      </div>

      {/* ── Chat panel ── */}
      <div className="ai-chat-panel">
        {/* Header */}
        <div className="ai-chat-header">
          <div className="ai-chat-header-icon">{currentSection.icon}</div>
          <div>
            <div className="ai-chat-header-title">עורך {currentSection.label}</div>
            <div className="ai-chat-header-sub">{currentSection.hint}</div>
          </div>
        </div>

        {/* Current value */}
        {currentValue && (
          <div className="ai-current-value">
            <span className="ai-current-label">ערך נוכחי:</span>
            <span className="ai-current-text">{currentValue}</span>
          </div>
        )}

        {/* Messages */}
        <div className="ai-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`ai-msg ai-msg-${msg.role}`}>
              {msg.role === 'ai' && (
                <div className="ai-msg-avatar">🤖</div>
              )}
              {msg.role === 'user' && (
                <div className="ai-msg-avatar ai-msg-avatar-user">👤</div>
              )}
              <div className="ai-msg-content">
                <div className="ai-msg-text">{msg.text}</div>
                {msg.suggestion && !msg.applied && (
                  <div className="ai-suggestion-card">
                    <div className="ai-suggestion-label">הצעת AI:</div>
                    <div className="ai-suggestion-text">{msg.suggestion}</div>
                    <div className="ai-suggestion-actions">
                      <button
                        className="ai-btn-apply"
                        onClick={() => applyEdit(i, msg.suggestion!, msg.section!)}
                        disabled={applyingIdx === i}
                      >
                        {applyingIdx === i ? '⏳ שומר...' : '✅ אשר ושמור'}
                      </button>
                      <button
                        className="ai-btn-reject"
                        onClick={() => rejectEdit(i)}
                        disabled={applyingIdx === i}
                      >
                        ✕ נסה שוב
                      </button>
                    </div>
                  </div>
                )}
                {msg.suggestion && msg.applied && (
                  <div className="ai-suggestion-applied">✅ שינוי נשלח לאישור</div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="ai-msg ai-msg-ai">
              <div className="ai-msg-avatar">🤖</div>
              <div className="ai-msg-content">
                <div className="ai-typing">
                  <span /><span /><span />
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="ai-input-row">
          <textarea
            className="ai-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
            placeholder={`ספר ל-AI מה לשנות ב${currentSection.label}... (Enter לשליחה)`}
            rows={2}
            disabled={loading}
          />
          <button
            className="ai-send-btn"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
          >
            {loading ? '⏳' : '➤'}
          </button>
        </div>
        <p className="ai-input-note">
          💡 דוגמאות: "כתוב קצת יותר מוזמן" · "הוסף שעות פתיחה" · "שנה לכיוון מקצועי יותר"
        </p>
      </div>
    </div>
  );
}

// ── App ────────────────────────────────────────────────────────────
const TABS = [
  { key: 'overview', label: '🏠 סקירה כללית' },
  { key: 'ai_editor', label: '✨ עריכה עם AI' },
  { key: 'edit', label: '✏️ עדכון פרטים' },
  { key: 'requests', label: '📬 בקשות שינוי' },
  { key: 'support', label: '💬 תמיכה' },
  { key: 'settings', label: '⚙️ הגדרות' },
];

export default function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem('customer_token') || '');
  const [me, setMe] = useState<Me | null>(null);
  const [tab, setTab] = useState('overview');
  const [loadingMe, setLoadingMe] = useState(false);

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
  }, [tab]);

  useEffect(() => {
    if (!token) return;
    setLoadingMe(true);
    apiCall('/customer/me', token).then(setMe).catch(() => { localStorage.removeItem('customer_token'); setToken(''); }).finally(() => setLoadingMe(false));
  }, [token]);

  function handleLogin(t: string, m: Me) { setToken(t); setMe(m); }
  function logout() { localStorage.removeItem('customer_token'); setToken(''); setMe(null); }
  function refreshMe() { if (!token) return; apiCall('/customer/me', token).then(setMe).catch(() => { }); }

  if (loadingMe) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontSize: 32 }}>⏳</div>;
  if (!token || !me) return <LoginPage onLogin={handleLogin} />;

  return (
    <div className="app-layout">
      <header className="topbar">
        <div className="topbar-brand">� tazo-web</div>
        <div className="topbar-right">
          <span className="user-pill">{me.contact_name || me.phone}</span>
          {me.package_name && <span className="pkg-badge">{me.package_name}</span>}
          <button className="btn-logout" onClick={logout}>יציאה</button>
        </div>
      </header>
      <nav className="nav-tabs">
        {TABS.map(t => (
          <button key={t.key} className={`tab-btn${tab === t.key ? ' active' : ''}`} onClick={() => setTab(t.key)}>{t.label}</button>
        ))}
      </nav>
      <main className="content">
        {me.must_change_password && tab !== 'settings' && <ChangePasswordBanner token={token} onDone={refreshMe} />}
        {tab === 'overview' && <OverviewTab token={token} me={me} />}
        {tab === 'ai_editor' && <AIEditorTab token={token} />}
        {tab === 'edit' && <EditInfoTab token={token} />}
        {tab === 'requests' && <ChangeRequestsTab token={token} />}
        {tab === 'support' && <SupportTab token={token} />}
        {tab === 'settings' && <SettingsTab token={token} onPasswordChanged={refreshMe} />}
      </main>
    </div>
  );
}
