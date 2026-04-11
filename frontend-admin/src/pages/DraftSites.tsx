import { useEffect, useState, useCallback, useRef } from 'react';
import { Button, Card, SectionTitle, Tooltip } from '../components/ui';
import {
    DraftSite,
    getDraftSites,
    generateDraftPreview,
    createAndPreview,
    Business,
    getBusinesses,
    triggerGenerateSite,
    getTaskStatus,
    TaskStatus,
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
    // task_id per business while an async Celery task is running
    const [taskIds, setTaskIds] = useState<Record<number, string>>({});
    const [taskStatuses, setTaskStatuses] = useState<Record<number, TaskStatus>>({});
    const pollIntervals = useRef<Record<number, ReturnType<typeof setInterval>>>({});

    const load = useCallback(() => {
        Promise.all([getBusinesses(), getDraftSites(0, 500)]).then(([biz, dr]) => {
            setBusinesses(biz);
            setDrafts(dr);
        }).catch(console.error);
    }, []);

    useEffect(() => { load(); }, [load]);

    // Clean up intervals on unmount
    useEffect(() => {
        const intervals = pollIntervals.current;
        return () => { Object.values(intervals).forEach(clearInterval); };
    }, []);

    const draftByBiz = (bizId: number) => drafts.find(d => d.business_id === bizId);

    const setLoaderFor = (bizId: number, val: boolean) =>
        setLoading(prev => ({ ...prev, [bizId]: val }));

    const stopPolling = (bizId: number) => {
        if (pollIntervals.current[bizId]) {
            clearInterval(pollIntervals.current[bizId]);
            delete pollIntervals.current[bizId];
        }
    };

    const startPolling = (bizId: number, taskId: string) => {
        stopPolling(bizId);
        setTaskIds(prev => ({ ...prev, [bizId]: taskId }));
        pollIntervals.current[bizId] = setInterval(async () => {
            try {
                const status = await getTaskStatus(taskId);
                setTaskStatuses(prev => ({ ...prev, [bizId]: status }));
                if (status.state === 'SUCCESS') {
                    stopPolling(bizId);
                    setLoaderFor(bizId, false);
                    setTaskIds(prev => { const n = { ...prev }; delete n[bizId]; return n; });
                    setMsg(`✅ האתר נוצר בהצלחה! (עסק #${bizId})`);
                    load();
                } else if (status.state === 'FAILURE') {
                    stopPolling(bizId);
                    setLoaderFor(bizId, false);
                    setTaskIds(prev => { const n = { ...prev }; delete n[bizId]; return n; });
                    setMsg(`❌ שגיאה ביצירה: ${status.error || 'שגיאה לא ידועה'}`);
                }
            } catch {
                // ignore transient poll errors
            }
        }, 5000);
    };

    const handleAsyncGenerate = async (bizId: number) => {
        setLoaderFor(bizId, true);
        setMsg('');
        try {
            const { task_id } = await triggerGenerateSite(bizId);
            startPolling(bizId, task_id);
        } catch (e: unknown) {
            setLoaderFor(bizId, false);
            setMsg(`❌ שגיאה: ${e instanceof Error ? e.message : 'unknown'}`);
        }
    };

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

    function stepLabel(step?: string | null): string {
        const map: Record<string, string> = {
            running_ai_pipeline: '🤖 מריץ AI…',
            saving_draft: '💾 שומר טיוטה…',
        };
        return step ? (map[step] || step) : '⏳ בתור…';
    }

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
                    const taskId = taskIds[biz.id];
                    const taskStatus = taskStatuses[biz.id];
                    const st = statusLabel(draft?.status || '');
                    return (
                        <div key={biz.id} style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', padding: '12px 0', borderBottom: '1px solid #f1f5f9' }}>
                            {/* Business info */}
                            <div style={{ flex: 1, minWidth: 200 }}>
                                <div style={{ fontWeight: 700, fontSize: 15, color: '#111827' }}>{biz.name}</div>
                                <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
                                    {biz.city || '—'} · {biz.category || '—'} · {biz.phone || '—'}
                                </div>
                                {/* Polling progress indicator */}
                                {taskId && (
                                    <div style={{ fontSize: 12, color: '#6366f1', marginTop: 4 }}>
                                        {taskStatus ? stepLabel(taskStatus.step) : '⏳ ממתין לסטטוס…'}
                                    </div>
                                )}
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
                                    <>
                                        <Tooltip text="צור אתר AI ב-background — עדכון אוטומטי עם סיום">
                                            <Button onClick={() => handleAsyncGenerate(biz.id)} disabled={busy}>
                                                {taskId ? stepLabel(taskStatus?.step) : '⚡ AI אסינכרוני'}
                                            </Button>
                                        </Tooltip>
                                        <Tooltip text="בנה אתר טיוטה בעזרת AI לעסק זה (סינכרוני)">
                                            <Button onClick={() => handleCreate(biz.id)} disabled={busy} style={{ background: '#e0e7ff', color: '#3730a3' }}>
                                                {busy && !taskId ? '⏳ יוצר…' : '✨ צור אתר'}
                                            </Button>
                                        </Tooltip>
                                    </>
                                ) : (
                                    <>
                                        {previewUrl(draft) && (
                                            <Tooltip text="פתח תצוגה מקדימה של האתר">
                                                <a href={previewUrl(draft)} target="_blank" rel="noopener noreferrer">
                                                    <Button>👁️ צפה באתר</Button>
                                                </a>
                                            </Tooltip>
                                        )}
                                        <Tooltip text="בנה מחדש ב-background — ה-AI יחדש את התוכן">
                                            <Button onClick={() => handleAsyncGenerate(biz.id)} disabled={busy}>
                                                {taskId ? stepLabel(taskStatus?.step) : '⚡ AI מחדש'}
                                            </Button>
                                        </Tooltip>
                                        <Tooltip text="בנה מחדש את האתר — שלב AI נוסף יחדש את התוכן (סינכרוני)">
                                            <Button onClick={() => handleRegenerate(draft)} disabled={busy} style={{ background: '#e0e7ff', color: '#3730a3' }}>
                                                {busy && !taskId ? '⏳ מחדש…' : '🔄 צור מחדש'}
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
