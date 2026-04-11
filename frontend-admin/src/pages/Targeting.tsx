
import { useEffect, useState } from 'react';
import { Button, Card, Input, SectionTitle } from '../components/ui';
import { Profile, Campaign, Lead, CampaignResults, getProfiles, getCampaigns, searchLeads, assignLeadToCampaign, getCampaignResults } from '../services/queries';

export default function TargetingPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [results, setResults] = useState<Lead[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<number | null>(null);
  const [campaignResults, setCampaignResults] = useState<CampaignResults | null>(null);
  const [city, setCity] = useState('');
  const [category, setCategory] = useState('');
  useEffect(() => {
    Promise.all([getProfiles(), getCampaigns(), searchLeads()]).then(([p, c, r]) => { setProfiles(p); setCampaigns(c); setResults(r); if (c[0]) { setSelectedCampaign(c[0].id); getCampaignResults(c[0].id).then(setCampaignResults); } }).catch(console.error);
  }, []);
  async function runSearch() { setResults(await searchLeads(city || undefined, category || undefined)); }
  async function assign(leadId: number) {
    if (!selectedCampaign) return;
    await assignLeadToCampaign(selectedCampaign, leadId);
    setResults(await searchLeads(city || undefined, category || undefined));
    setCampaignResults(await getCampaignResults(selectedCampaign));
  }
  return (
    <div className="two-col">
      <Card>
        <SectionTitle>Targeting Console</SectionTitle>
        <div className="grid-two">
          <div><label>City</label><Input value={city} onChange={(e) => setCity(e.target.value)} placeholder="e.g. Ramat Gan" /></div>
          <div><label>Category</label><Input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. beauty" /></div>
        </div>
        <div style={{ display:'flex', gap:8, marginTop:12 }}>
          <Button onClick={runSearch}>Run search</Button>
          <Button onClick={() => { setCity('Ramat Gan'); setCategory('beauty'); }}>Beauty · Ramat Gan</Button>
          <Button onClick={() => { setCity('Petah Tikva'); setCategory('garages'); }}>Garages · Petah Tikva</Button>
        </div>
        <p><strong>Profiles:</strong> {profiles.length}</p>
        <ul>{profiles.map(p => <li key={p.id}>{p.name} · {p.city} · {p.radius_km}km</li>)}</ul>
        <p><strong>Campaigns:</strong> {campaigns.length}</p>
        <div className="table-list">
          {campaigns.map(c => (
            <div key={c.id}>
              <strong>{c.name}</strong>
              <div className="muted">{c.status}</div>
              <Button onClick={() => { setSelectedCampaign(c.id); getCampaignResults(c.id).then(setCampaignResults); }}>Use campaign</Button>
            </div>
          ))}
        </div>
        {campaignResults ? <div className="card subtle"><strong>Campaign results:</strong><p>Leads: {campaignResults.lead_count} · Businesses: {campaignResults.business_count}</p></div> : null}
      </Card>
      <Card>
        <SectionTitle>Segment Result Preview</SectionTitle>
        <div className="table-list">
          {results.map(l => <div key={l.id}><strong>{l.imported_name}</strong><div className="muted">{l.city || '—'} · {l.category || '—'} · score {l.score} · {l.website_url ? 'has website' : 'no website'} · campaign {l.campaign_id || '—'}</div><Button onClick={() => assign(l.id)}>Assign to selected campaign</Button></div>)}
        </div>
      </Card>
    </div>
  );
}
