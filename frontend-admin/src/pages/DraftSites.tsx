import { useEffect, useState, useCallback } from 'react';
import { Button, Card, SectionTitle, Tooltip } from '../components/ui';
import {
    DraftSite,
    getDraftSites,
    generateDraftPreview,
    createAndPreview,
    Business,
    getBusinesses,
} from '../services/queries';

const API_BASE = import.meta.env.VITE_API_URL || 'https://api.sitenest.site';

function previewUrl(draft: DraftSite): string {
    if (!draft.preview_url) return '';
    // turn /static/... into absolute URL
    return draft.preview_url.startsWith('http') ? draft.preview_url : `${API_BASE}${draft.preview_url}`;
}

function statusLabel(status: string) {
    const map: Record<string, { label: string; color: string }> = {
        draft: { label: 'טיוטה', color: '#6b7280' },
        published_preview: { label: '✅ פורסם', color: '#15803d' },
        approved: { label: '🌟 מאושר', color: '#0ea5e9' },
    };
    return map[status] || { label: status, color: '#374151' };
}

export default function DraftSitesPage() {
    const [businesses, setBusinesses] = useState<Business[]>([]);
    const [drafts, setDrafts] = useState<DraftSite[]>([]);
    const [loading, setLoading] = useState<Record<number, boolean>>({});
    const [msg, setMsg] = useState('');

    const load = useCallback(() => {
        Promise.all([getBusinesses(), getDraftSites(0, 500)]).then(([biz, dr]) => {
            setBusinesses(biz);
            setDrafts(dr);
        }).catch(console.error);
    }, []);

    useEffect(() => { load(); }, [load]);

    const draftByBiz = (bizId: number) => drafts.find(d => d.business_id === bizId);

    const setLoaderFor = (bizId: number, val: boolean) =>
        setLoading(prev => ({ ...prev, [bizId]: val }));

    const handleCreate = async (bizId: number) => {
        setLoaderFor(bizId, true);
        setMsg('');
        try {
            const result = await createAndPreview(bizId);
            setMsg(`✅ אתר נוצר! (draft #${result.id})`);
            load();
        } catch (e: unknown) {
            setMsg(`❌ שגיאה: ${e instanceof Error ? e.message : 'unknown'}`);
        } finally {
            setLoaderFor(bizId, false);
        }
    };

    const handleRegenerate = async (draft: DraftSite) => {
        setLoaderFor(draft.business_id, true);
        setMsg('');
        try {
            await generateDraftPreview(draft.id);
            setMsg(`✅ האתר עודכן (#${draft.id})`);
            load();
        } catch (e: unknown) {
            setMsg(`❌ שגיאה: ${e instanceof Error ? e.message : 'unknown'}`);
        } finally {
            setLoaderFor(draft.business_id, false);
        }
    };

    return (
        <Card>
            <SectionTitle>✨ ניהול אתרי טיוטה</SectionTitle>
            {msg && (
                <div style={{
                    padding: '10px 16px', borderRadius: 10, marginBottom: 16,
                    background: msg.startsWith('✅') ? '#dcfce7' : '#fee2e2',
                    color: msg.startsWith('✅') ? '#166534' : '#991b1b', fontSize: 14,
                }}>
                    {msg}
                </div>
            )}
            <div className="table-list">
                {businesses.length === 0 && <p className="muted">טוען עסקים…</p>}
                {businesses.map(biz => {
                    const draft = draftByBiz(biz.id);
                    const busy = !!loading[biz.id];
                    const st = statusLabel(draft?.status || '');
                    return (
                        <div key={biz.id} style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', padding: '12px 0', borderBottom: '1px solid #f1f5f9' }}>
                            {/* Business info */}
                            <div style={{ flex: 1, minWidth: 200 }}>
                                <div style={{ fontWeight: 700, fontSize: 15, color: '#111827' }}>{biz.name}</div>
                                <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
                                    {biz.city || '—'} · {biz.category || '—'} · {biz.phone || '—'}
                                </div>
                            </div>

                            {/* Status badge */}
                            {draft && (
                                <span style={{ fontSize: 12, fontWeight: 700, color: st.color, background: '#f8fafc', borderRadius: 20, padding: '4px 12px', border: `1px solid ${st.color}` }}>
                                    {st.label}
                                </span>
                            )}

                            {/* Actions */}
                            <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                                {!draft ? (
                                    <Tooltip text="בנה אתר טיוטה בעזרת AI לעסק זה">
                                      <Button onClick={() => handleCreate(biz.id)} disabled={busy}>
                                          {busy ? '⏳ יוצר…' : '✨ צור אתר'}
                                      </Button>
                                    </Tooltip>
                                ) : (
                                    <>
                                        {previewUrl(draft) && (
                                            <Tooltip text="פתח תצוגה מקדימה של האתר">
                                              <a href={previewUrl(draft)} target="_blank" rel="noopener noreferrer">
                                                  <Button>👁️ צפה באתר</Button>
                                              </a>
                                            </Tooltip>
                                        )}
                                        <Tooltip text="בנה מחדש את האתר — שלב AI נוסף יחדש את התוכן">
                                          <Button onClick={() => handleRegenerate(draft)} disabled={busy}>
                                              {busy ? '⏳ מחדש…' : '🔄 צור מחדש'}
                                          </Button>
                                        </Tooltip>
                                    </>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </Card>
    );
}
