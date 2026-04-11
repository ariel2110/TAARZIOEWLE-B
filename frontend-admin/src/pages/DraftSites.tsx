import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle } from '../components/ui';
import { DraftSite, getDraftSites, generateDraftPreview } from '../services/queries';

export default function DraftSitesPage() {
    const [items, setItems] = useState<DraftSite[]>([]);
    const load = () => getDraftSites().then(setItems).catch(console.error);
    useEffect(() => { load(); }, []);

    const handleGeneratePreview = (id: number) => {
        generateDraftPreview(id).then(load).catch(console.error);
    };

    return (
        <Card>
            <SectionTitle>Draft Sites</SectionTitle>
            <div className="table-list">
                {items.map(d => (
                    <div key={d.id}>
                        <strong>{d.site_title}</strong>
                        <div className="muted">
                            id {d.id} · business_id {d.business_id} · status {d.status}
                            {d.is_demo && ' · demo'} {d.noindex && ' · noindex'}
                        </div>
                        {d.hero_title && <div className="muted" style={{ fontSize: 12 }}>hero: {d.hero_title}</div>}
                        {d.primary_color && <div className="muted" style={{ fontSize: 12 }}>color: {d.primary_color}</div>}
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                            <Button onClick={() => handleGeneratePreview(d.id)}>Generate preview</Button>
                            {d.preview_url && (
                                <a href={d.preview_url} target="_blank" rel="noopener noreferrer">
                                    <Button>View preview</Button>
                                </a>
                            )}
                        </div>
                    </div>
                ))}
                {items.length === 0 && <p className="muted">No draft sites found.</p>}
            </div>
        </Card>
    );
}
