import { useEffect, useState } from 'react';
import { Card, SectionTitle } from '../components/ui';
import { Digest, Health, Snapshot, Business, Approval, getSnapshot, getDigest, getHealth, getBusinesses, getApprovals } from '../services/queries';

export default function OverviewPage() {
  const [snapshot, setSnapshot] = useState<Snapshot>({});
  const [digest, setDigest] = useState<Digest | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);

  useEffect(() => {
    Promise.all([getSnapshot(), getDigest(), getHealth(), getBusinesses(), getApprovals()]).then(([s, d, h, b, a]) => {
      setSnapshot(s); setDigest(d); setHealth(h); setBusinesses(b); setApprovals(a);
    }).catch(console.error);
  }, []);

  return (
    <div className="grid">
      <div>
        <SectionTitle>Overview</SectionTitle>
        <div className="cards">
          {Object.entries(snapshot).map(([k, v]) => (
            <Card key={k}><div className="muted" style={{ textTransform:'uppercase' }}>{k}</div><div style={{ fontSize: 24, fontWeight: 700 }}>{v}</div></Card>
          ))}
        </div>
      </div>
      <div className="two-col">
        <Card dark>
          <SectionTitle>CEO Daily Digest</SectionTitle>
          <p>{digest?.executive_summary}</p>
          <ul>{digest?.recommended_actions?.map(x => <li key={x}>{x}</li>)}</ul>
        </Card>
        <Card>
          <SectionTitle>System Health</SectionTitle>
          <p><strong>Status:</strong> {health?.overall_status || health?.status}</p>
          <p><strong>Database:</strong> {health?.database_ok ? 'connected' : 'unknown/degraded'}</p>
          <ul>{health?.drivers?.map(x => <li key={x}>{x}</li>)}</ul>
        </Card>
      </div>
      <div className="two-col">
        <Card>
          <SectionTitle>Businesses</SectionTitle>
          <div className="table-list">
            {businesses.slice(0, 6).map(b => (
              <div key={b.id}><strong>{b.name}</strong><div className="muted">{b.city || '—'} · {b.category || '—'} · {b.status}</div></div>
            ))}
          </div>
        </Card>
        <Card>
          <SectionTitle>Pending Approvals</SectionTitle>
          <div className="table-list">
            {approvals.filter(a => ['proposed','under_review'].includes(a.status)).slice(0, 6).map(a => (
              <div key={a.id}><strong>{a.title}</strong><div className="muted">{a.approval_type} · {a.status}</div></div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
