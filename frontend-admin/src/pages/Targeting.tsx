
import { useEffect, useState } from 'react';
import { Button, Card, Input, SectionTitle, InfoTip } from '../components/ui';
import { useLang } from '../i18n';
import { Profile, Campaign, Lead, CampaignResults, getProfiles, getCampaigns, searchLeads, assignLeadToCampaign, getCampaignResults } from '../services/queries';

export default function TargetingPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [results, setResults] = useState<Lead[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<number | null>(null);
  const [campaignResults, setCampaignResults] = useState<CampaignResults | null>(null);
  const [city, setCity] = useState('');
  const [category, setCategory] = useState('');
  const { t } = useLang();
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
        <SectionTitle>{t('targeting_console')} <InfoTip text="חיפוש לידים לפי עיר/קטגוריה ושיוך לקמפיין פנייה" /></SectionTitle>
        <div className="grid-two">
          <div><label>{t('city')}</label><Input value={city} onChange={(e) => setCity(e.target.value)} placeholder={t('city_placeholder')} /></div>
          <div><label>{t('category')}</label><Input value={category} onChange={(e) => setCategory(e.target.value)} placeholder={t('category_placeholder')} /></div>
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <Button onClick={runSearch}>{t('run_search')}</Button>
          <Button onClick={() => { setCity('רמת גן'); setCategory('beauty'); }}>{t('beauty_rg')}</Button>
          <Button onClick={() => { setCity('פתח תקווה'); setCategory('garages'); }}>{t('garages_pt')}</Button>
        </div>
        <p><strong>{t('profiles_label')}:</strong> {profiles.length}</p>
        <ul>{profiles.map(p => <li key={p.id}>{p.name} · {p.city} · {p.radius_km}{t('km_label')}</li>)}</ul>
        <p><strong>{t('campaigns_label')}:</strong> {campaigns.length}</p>
        <div className="table-list">
          {campaigns.map(c => (
            <div key={c.id}>
              <strong>{c.name}</strong>
              <div className="muted">{c.status}</div>
              <Button onClick={() => { setSelectedCampaign(c.id); getCampaignResults(c.id).then(setCampaignResults); }}>{t('use_campaign')}</Button>
            </div>
          ))}
        </div>
        {campaignResults ? <div className="card subtle"><strong>{t('campaign_results')}:</strong><p>{t('leads_label')}: {campaignResults.lead_count} · {t('businesses')}: {campaignResults.business_count}</p></div> : null}
      </Card>
      <Card>
        <SectionTitle>{t('segment_preview')} <InfoTip text="לידים שמתאימים לסגמנט הנוכחי — שייך לקמפיין בלחיצה" /></SectionTitle>
        <div className="table-list">
          {results.map(l => <div key={l.id}><strong>{l.imported_name}</strong><div className="muted">{l.city || '—'} · {l.category || '—'} · {t('score_label')} {l.score} · {l.website_url ? t('has_website') : t('no_website')} · {t('campaign_label')} {l.campaign_id || '—'}</div><Button onClick={() => assign(l.id)}>{t('assign_campaign')}</Button></div>)}
        </div>
      </Card>
    </div>
  );
}
