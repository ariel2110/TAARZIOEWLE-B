
import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle } from '../components/ui';
import { Lead, getLeads, qualifyLead, convertLeadToBusiness } from '../services/queries';

export default function LeadsPage() {
  const [items, setItems] = useState<Lead[]>([]);
  const load = () => getLeads().then(setItems).catch(console.error);
  useEffect(() => { load(); }, []);
  return (
    <Card>
      <SectionTitle>Leads</SectionTitle>
      <div className="table-list">
        {items.map(l => (
          <div key={l.id}>
            <strong>{l.imported_name}</strong>
            <div className="muted">{l.city || '—'} · {l.category || '—'} · score {l.score} · {l.status} · campaign {l.campaign_id || '—'}</div>
            <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
              <Button onClick={() => qualifyLead(l.id).then(load)}>Qualify</Button>
              <Button onClick={() => convertLeadToBusiness(l.id).then(load)}>Convert to business</Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
