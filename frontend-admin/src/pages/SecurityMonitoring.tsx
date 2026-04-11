import { useEffect, useState } from 'react';
import { Card, SectionTitle } from '../components/ui';
import { getSecuritySummary, getSecurityTimeline, getSuspicion, SecuritySummary, SecurityTimelineItem, SuspicionItem } from '../services/queries';

export default function SecurityMonitoring(){
  const [summary, setSummary] = useState<SecuritySummary | null>(null);
  const [timeline, setTimeline] = useState<SecurityTimelineItem[]>([]);
  const [suspicion, setSuspicion] = useState<SuspicionItem[]>([]);
  useEffect(() => {
    Promise.all([getSecuritySummary(), getSecurityTimeline(), getSuspicion()]).then(([s,t,sp]) => {
      setSummary(s); setTimeline(t.items || []); setSuspicion(sp.items || []);
    }).catch(console.error);
  }, []);
  return <div className="grid">
    <SectionTitle>Security Monitoring</SectionTitle>
    <div className="cards">
      <Card><div className="muted">Overall</div><div style={{fontSize:24,fontWeight:700}}>{summary?.overall_status || 'unknown'}</div></Card>
      <Card><div className="muted">Login Failures</div><div style={{fontSize:24,fontWeight:700}}>{summary?.login_failures || 0}</div></Card>
      <Card><div className="muted">Blocked Logins</div><div style={{fontSize:24,fontWeight:700}}>{summary?.blocked_logins || 0}</div></Card>
      <Card><div className="muted">Rate Limited</div><div style={{fontSize:24,fontWeight:700}}>{summary?.rate_limited_events || 0}</div></Card>
    </div>
    <div className="two-col">
      <Card>
        <SectionTitle>Suspicion Watchlist</SectionTitle>
        <div className="table-list">
          {suspicion.slice(0,10).map(item => <div key={item.customer_phone}><strong>{item.customer_phone}</strong><div className="muted">score {item.suspicion_score} · {item.suspicion_tier} · failures {item.login_failures} · blocked {item.blocked_logins}</div></div>)}
        </div>
      </Card>
      <Card>
        <SectionTitle>Security Timeline</SectionTitle>
        <div className="table-list">
          {timeline.slice(0,12).map((item, idx) => <div key={idx}><strong>{item.label}</strong><div className="muted">{item.type} · {item.phone || '—'} · {item.detail || '—'}</div></div>)}
        </div>
      </Card>
    </div>
  </div>
}
