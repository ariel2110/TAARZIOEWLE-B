
import React, { useEffect, useState } from 'react';
const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

type Tab = 'overview'|'leads'|'approvals'|'targeting'|'ceo'|'customers'|'security';

export default function App() {
  const [tab, setTab] = useState<Tab>('overview');
  const [data, setData] = useState<any>({});
  const adminToken = localStorage.getItem('admin_token') || 'dev-admin-token';
  const headers:any = { 'X-Admin-Token': adminToken, 'X-Admin-Email': 'ar.2110@gmail.com' };

  useEffect(() => {
    Promise.all([
      fetch(`${API}/admin/analytics/snapshot`, { headers }).then(r=>r.json()).catch(()=>({})),
      fetch(`${API}/admin/ceo/daily-digest`, { headers }).then(r=>r.json()).catch(()=>({})),
      fetch(`${API}/admin/leads`, { headers }).then(r=>r.json()).catch(()=>([])),
      fetch(`${API}/admin/approvals`, { headers }).then(r=>r.json()).catch(()=>([])),
      fetch(`${API}/admin/targeting/search`, { headers }).then(r=>r.json()).catch(()=>([])),
      fetch(`${API}/admin/customers`, { headers }).then(r=>r.json()).catch(()=>([])),
      fetch(`${API}/admin/security/summary`, { headers }).then(r=>r.json()).catch(()=>({})),
      fetch(`${API}/admin/security/alerts`, { headers }).then(r=>r.json()).catch(()=>([])),
    ]).then(([analytics, ceo, leads, approvals, targeting, customers, securitySummary, securityAlerts]) => setData({analytics, ceo, leads, approvals, targeting, customers, securitySummary, securityAlerts}));
  }, []);

  const NavBtn = ({id,label}:{id:Tab,label:string}) => <button onClick={()=>setTab(id)} style={{marginRight:8}}>{label}</button>;
  const customerPackages = (data.customers || []).reduce((acc:any, c:any) => { const k = c.package_name || '—'; acc[k] = (acc[k] || 0) + 1; return acc; }, {});

  return <div style={{fontFamily:'Arial', padding:20}}>
    <h1>LocalBiz Admin — Ariel</h1>
    <div style={{marginBottom:16}}>
      <NavBtn id='overview' label='Overview' />
      <NavBtn id='leads' label='Leads' />
      <NavBtn id='approvals' label='Approvals' />
      <NavBtn id='targeting' label='Targeting' />
      <NavBtn id='ceo' label='CEO Console' />
      <NavBtn id='customers' label='Customers' />
      <NavBtn id='security' label='Security' />
    </div>
    {tab==='overview' && <pre>{JSON.stringify({analytics:data.analytics, customer_packages:customerPackages, security:data.securitySummary}, null, 2)}</pre>}
    {tab==='leads' && <pre>{JSON.stringify(data.leads, null, 2)}</pre>}
    {tab==='approvals' && <pre>{JSON.stringify(data.approvals, null, 2)}</pre>}
    {tab==='targeting' && <pre>{JSON.stringify(data.targeting, null, 2)}</pre>}
    {tab==='ceo' && <pre>{JSON.stringify(data.ceo, null, 2)}</pre>}
    {tab==='customers' && <pre>{JSON.stringify(data.customers, null, 2)}</pre>}
    {tab==='security' && <pre>{JSON.stringify({summary:data.securitySummary, alerts:data.securityAlerts}, null, 2)}</pre>}
  </div>;
}
