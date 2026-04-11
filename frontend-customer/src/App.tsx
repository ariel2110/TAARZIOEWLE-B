import React, { useEffect, useState } from 'react';

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

export default function App() {
  const [token, setToken] = useState<string>('');
  const [phone, setPhone] = useState('0500000000');
  const [password, setPassword] = useState('');
  const [me, setMe] = useState<any>(null);
  const [overview, setOverview] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [editSubmissions, setEditSubmissions] = useState<any[]>([]);
  const [changeRequests, setChangeRequests] = useState<any[]>([]);
  const [supportMessages, setSupportMessages] = useState<any[]>([]);
  const [fieldKey, setFieldKey] = useState('contact_name');
  const [fieldValue, setFieldValue] = useState('');
  const [crTitle, setCrTitle] = useState('');
  const [crDescription, setCrDescription] = useState('');
  const [supportSubject, setSupportSubject] = useState('General help');
  const [supportBody, setSupportBody] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => { const saved = localStorage.getItem('customer_token'); if (saved) setToken(saved); }, []);
  async function authed(path: string, init: RequestInit = {}) {
    const res = await fetch(`${API}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...(init.headers||{}), Authorization: `Bearer ${token}` } });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
  }
  async function load() {
    if (!token) return;
    try {
      const [m, o, tl, es, cr, sm] = await Promise.all([
        authed('/customer/me'), authed('/customer/overview'), authed('/customer/timeline'), authed('/customer/edit-submissions'), authed('/customer/change-requests'), authed('/customer/support')
      ]);
      setMe(m); setOverview(o); setTimeline(tl); setEditSubmissions(es); setChangeRequests(cr); setSupportMessages(sm);
    } catch (e:any) { setMessage(e.message); }
  }
  useEffect(() => { load(); }, [token]);
  async function login(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch(`${API}/customer/login`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ phone, password }) });
    const data = await res.json();
    if (!res.ok) { setMessage(data.detail || 'Login failed'); return; }
    localStorage.setItem('customer_token', data.access_token); setToken(data.access_token); setMessage(data.must_change_password ? 'Please change your temporary password.' : 'Login successful');
  }
  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    try { await authed('/customer/change-password', { method:'POST', body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }) }); setMessage('Password changed successfully'); setCurrentPassword(''); setNewPassword(''); load(); } catch (e:any) { setMessage(e.message); }
  }
  async function submitEdit(e: React.FormEvent) {
    e.preventDefault();
    try { await authed('/customer/edit-submissions', { method:'POST', body: JSON.stringify({ field_key: fieldKey, new_value: fieldValue }) }); setMessage('Edit submitted for review'); setFieldValue(''); load(); } catch (e:any) { setMessage(e.message); }
  }
  async function submitChangeRequest(e: React.FormEvent) {
    e.preventDefault();
    try { await authed('/customer/change-requests', { method:'POST', body: JSON.stringify({ request_type:'general', title: crTitle, description: crDescription }) }); setMessage('Change request sent'); setCrTitle(''); setCrDescription(''); load(); } catch (e:any) { setMessage(e.message); }
  }
  async function submitSupport(e: React.FormEvent) {
    e.preventDefault();
    try { await authed('/customer/support', { method:'POST', body: JSON.stringify({ subject: supportSubject, message: supportBody }) }); setMessage('Support message sent'); setSupportBody(''); load(); } catch (e:any) { setMessage(e.message); }
  }
  function logout() { localStorage.removeItem('customer_token'); setToken(''); setMe(null); setOverview(null); }
  if (!token || !me) return <div style={{fontFamily:'Arial',padding:24,maxWidth:560,margin:'0 auto'}}><h1>Customer Portal</h1><p>Login with your phone number and temporary password.</p><form onSubmit={login} style={{display:'grid',gap:12}}><input value={phone} onChange={e=>setPhone(e.target.value)} placeholder="Phone" /><input value={password} onChange={e=>setPassword(e.target.value)} placeholder="Temporary password" type="password" /><button type="submit">Login</button></form>{message && <p>{message}</p>}</div>;
  return <div style={{fontFamily:'Arial',padding:24,maxWidth:980,margin:'0 auto',display:'grid',gap:20}}>
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}><h1>Welcome {me.contact_name || 'Customer'}</h1><button onClick={logout}>Logout</button></div>
    {message && <p>{message}</p>}
    <div style={{display:'grid',gridTemplateColumns:'repeat(2, minmax(0,1fr))',gap:16}}>
      <div style={{border:'1px solid #ddd',padding:16,borderRadius:8}}><h3>Account</h3><p><strong>Business ID:</strong> {me.business_id}</p><p><strong>Phone:</strong> {me.phone}</p><p><strong>Email:</strong> {me.email || '—'}</p><p><strong>Package:</strong> {me.package_name || 'Not set'}</p><p><strong>Linked site:</strong> active={String(me.active_site_id)} draft={String(me.draft_site_id)}</p></div>
      <div style={{border:'1px solid #ddd',padding:16,borderRadius:8}}><h3>Business Overview</h3><pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(overview?.business || {}, null, 2)}</pre></div>
    </div>
    <div style={{border:'1px solid #ddd',padding:16,borderRadius:8}}><h3>Change password</h3><form onSubmit={changePassword} style={{display:'grid',gap:12,maxWidth:420}}><input value={currentPassword} onChange={e=>setCurrentPassword(e.target.value)} placeholder="Current password" type="password" /><input value={newPassword} onChange={e=>setNewPassword(e.target.value)} placeholder="New password" type="password" /><button type="submit">Change password</button></form></div>
    <div style={{display:'grid',gridTemplateColumns:'repeat(3, minmax(0,1fr))',gap:16}}>
      <div style={{border:'1px solid #ddd',padding:16,borderRadius:8}}><h3>Submit basic edit</h3><form onSubmit={submitEdit} style={{display:'grid',gap:12}}><select value={fieldKey} onChange={e=>setFieldKey(e.target.value)}><option value="contact_name">Contact name</option><option value="phone">Phone</option><option value="email">Email</option></select><input value={fieldValue} onChange={e=>setFieldValue(e.target.value)} placeholder="New value" /><button type="submit">Submit edit</button></form></div>
      <div style={{border:'1px solid #ddd',padding:16,borderRadius:8}}><h3>Change request</h3><form onSubmit={submitChangeRequest} style={{display:'grid',gap:12}}><input value={crTitle} onChange={e=>setCrTitle(e.target.value)} placeholder="Title" /><textarea value={crDescription} onChange={e=>setCrDescription(e.target.value)} placeholder="Describe the change you want" /><button type="submit">Send request</button></form></div>
      <div style={{border:'1px solid #ddd',padding:16,borderRadius:8}}><h3>Support</h3><form onSubmit={submitSupport} style={{display:'grid',gap:12}}><input value={supportSubject} onChange={e=>setSupportSubject(e.target.value)} placeholder="Subject" /><textarea value={supportBody} onChange={e=>setSupportBody(e.target.value)} placeholder="Write your support message" /><button type="submit">Send support message</button></form></div>
    </div>
    <div style={{display:'grid',gridTemplateColumns:'repeat(3, minmax(0,1fr))',gap:16}}><div style={{border:'1px solid #ddd',padding:16,borderRadius:8}}><h3>Recent payments</h3><pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(overview?.recent_payments || [], null, 2)}</pre></div><div style={{border:'1px solid #ddd',padding:16,borderRadius:8}}><h3>Edit submissions</h3><pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(editSubmissions, null, 2)}</pre></div><div style={{border:'1px solid #ddd',padding:16,borderRadius:8}}><h3>Change requests</h3><pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(changeRequests, null, 2)}</pre></div></div>
    <div style={{display:'grid',gridTemplateColumns:'repeat(2, minmax(0,1fr))',gap:16}}><div style={{border:'1px solid #ddd',padding:16,borderRadius:8}}><h3>Support messages</h3><pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(supportMessages, null, 2)}</pre></div><div style={{border:'1px solid #ddd',padding:16,borderRadius:8}}><h3>Timeline</h3><pre style={{whiteSpace:'pre-wrap',maxHeight:300,overflow:'auto'}}>{JSON.stringify(timeline, null, 2)}</pre></div></div>
  </div>;
}
