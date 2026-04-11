
import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle } from '../components/ui';
import { Business, getBusinesses, moveBusinessToDraft, markBusinessOutreachReady, buildBusinessWhatsApp } from '../services/queries';

export default function BusinessesPage() {
  const [items, setItems] = useState<Business[]>([]);
  const [launchInfo, setLaunchInfo] = useState('');
  const load = () => getBusinesses().then(setItems).catch(console.error);
  useEffect(() => { load(); }, []);
  return (
    <Card>
      <SectionTitle>Businesses</SectionTitle>
      {launchInfo ? <div className="card subtle"><strong>WhatsApp launcher:</strong><p>{launchInfo}</p></div> : null}
      <div className="table-list">
        {items.map((b) => (
          <div key={b.id}>
            <strong>{b.name}</strong>
            <div className="muted">{b.city || '—'} · {b.category || '—'} · {b.status} · campaign {b.campaign_id || '—'}</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <Button onClick={() => moveBusinessToDraft(b.id).then(load)}>Move to draft</Button>
              <Button onClick={() => markBusinessOutreachReady(b.id).then(load)}>Mark outreach ready</Button>
              <Button onClick={() => buildBusinessWhatsApp(b.id).then((x: any) => setLaunchInfo(`Outreach #${x.outreach_id} ready → ${x.whatsapp_url}`))}>Build WhatsApp message</Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
