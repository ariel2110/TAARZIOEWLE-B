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
    triggerRegenerateWithNote,
    getTaskStatus,
    TaskStatus,
} from '../services/queries';

// Static files (e.g. /static/drafts/...) are served at the API root, not under /api/v1.
// Strip the /api/vN suffix so previewUrl() resolves correctly.
const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1')
    .replace(/\/api\/v\d+\/?$/, '');

function previewUrl(draft: DraftSite): string {
    if (draft.preview_url) {
        // turn /static/... into absolute URL using the main domain (has /static/ proxy)
        return draft.preview_url.startsWith('http') ? draft.preview_url : `${API_BASE}${draft.preview_url}`;
    }
    // Fallback: subdomain URL works via nginx wildcard + backend middleware
    if (draft.status === 'published_preview' || draft.status === 'preview_ready') {
        return `https://draft-${draft.id}.tazo-web.com`;
    }
    return '';
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
    // Per-business regeneration note (shown inline when expanding)
    const [noteOpen, setNoteOpen] = useState<Record<number, boolean>>({});
    const [notes, setNotes] = useState<Record<number, string>>({});;
    // Per-business inline preview toggle
    const [previewOpen, setPreviewOpen] = useState<Record<number, boolean>>({});

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

    // Prefer the draft that has already been generated (has preview_url or status != 'draft'),
    // so a newer empty draft doesn't hide the published one.
    const draftByBiz = (bizId: number) => {
        const all = drafts.filter(d => d.business_id === bizId);
        return all.find(d => d.preview_url) || all.find(d => d.status !== 'draft') || all[0];
    };

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

    const handleRegenerateWithNote = async (bizId: number) => {
        const note = (notes[bizId] || '').trim();
        if (!note) { setMsg('❌ יש להזין הערה לפני ביצוע'); return; }
        setLoaderFor(bizId, true);
        setMsg('');
        try {
            const { task_id } = await triggerRegenerateWithNote(bizId, note);
            startPolling(bizId, task_id);
            // clear the note panel after launch
            setNoteOpen(prev => ({ ...prev, [bizId]: false }));
            setNotes(prev => ({ ...prev, [bizId]: '' }));
        } catch (e: unknown) {
            setLoaderFor(bizId, false);
            setMsg(`❌ שגיאה: ${e instanceof Error ? e.message : 'unknown'}`);
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
                                            <>
                                                <Tooltip text="פתח את האתר המלא בטאב חדש">
                                                    <a href={previewUrl(draft)} target="_blank" rel="noopener noreferrer">
                                                        <Button style={{ background: '#0f172a', color: '#fff' }}>🔗 פתח בטאב חדש</Button>
                                                    </a>
                                                </Tooltip>
                                                <Tooltip text="הצג / הסתר תצוגה מקדימה מוטבעת">
                                                    <Button
                                                        onClick={() => setPreviewOpen(prev => ({ ...prev, [biz.id]: !prev[biz.id] }))}
                                                        style={{ background: previewOpen[biz.id] ? '#dbeafe' : '#f0f9ff', color: '#1d4ed8', border: '1px solid #3b82f6' }}
                                                    >
                                                        {previewOpen[biz.id] ? '🙈 הסתר תצוגה' : '👁️ צפה באתר'}
                                                    </Button>
                                                </Tooltip>
                                            </>
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
                                        <Tooltip text="ציין מה לשנות — ה-AI יבצע בדיוק את הבקשה ויבנה מחדש">
                                            <Button
                                                onClick={() => setNoteOpen(prev => ({ ...prev, [biz.id]: !prev[biz.id] }))}
                                                disabled={busy}
                                                style={{ background: noteOpen[biz.id] ? '#fef3c7' : '#f0fdf4', color: noteOpen[biz.id] ? '#92400e' : '#166534', border: `1px solid ${noteOpen[biz.id] ? '#f59e0b' : '#16a34a'}` }}
                                            >
                                                ✏️ שינויים
                                            </Button>
                                        </Tooltip>
                                    </>
                                )}
                            </div>

                            {/* ── Note expansion panel ─────────────────────── */}
                            {draft && noteOpen[biz.id] && (
                                <div style={{ width: '100%', marginTop: 10, padding: '14px 16px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 10 }}>
                                    <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 4, color: '#92400e' }}>
                                        ✏️ מה לשנות ב-<strong>{biz.name}</strong>?
                                    </div>
                                    <div style={{ fontSize: 12, color: '#a16207', marginBottom: 8, lineHeight: 1.5 }}>
                                        פרט כל שינוי — ה-AI ישמור את כל מה שלא ציינת ויעדכן רק מה שביקשת.
                                    </div>
                                    <textarea
                                        dir="rtl"
                                        rows={4}
                                        maxLength={2000}
                                        disabled={busy}
                                        value={notes[biz.id] || ''}
                                        onChange={e => setNotes(prev => ({ ...prev, [biz.id]: e.target.value }))}
                                        placeholder={`לדוגמה:\n• שנה את הכותרת הראשית ל"${biz.name} — המומחים שלך"\n• הוסף שירות חדש: ייעוץ ראשוני חינם\n• שנה טון לידידותי יותר`}
                                        style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid #fcd34d', fontSize: 13, fontFamily: 'inherit', resize: 'vertical', background: '#fff', outline: 'none', boxSizing: 'border-box' }}
                                    />
                                    <div style={{ display: 'flex', gap: 8, marginTop: 8, alignItems: 'center' }}>
                                        <Button
                                            onClick={() => handleRegenerateWithNote(biz.id)}
                                            disabled={busy || !(notes[biz.id] || '').trim()}
                                            style={{ background: '#16a34a', color: '#fff', fontWeight: 700 }}
                                        >
                                            {taskId ? stepLabel(taskStatus?.step) : '🔄 בצע שינויים עם AI'}
                                        </Button>
                                        <span style={{ fontSize: 11, color: '#a16207' }}>{(notes[biz.id] || '').length}/2000</span>
                                        <button
                                            onClick={() => setNoteOpen(prev => ({ ...prev, [biz.id]: false }))}
                                            disabled={busy}
                                            style={{ marginRight: 'auto', background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer', fontSize: 13, padding: '4px 8px' }}
                                        >
                                            ✕ ביטול
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* ── Inline iframe preview panel ───────────────── */}
                            {draft && previewOpen[biz.id] && previewUrl(draft) && (
                                <div style={{ width: '100%', marginTop: 10, borderRadius: 12, overflow: 'hidden', border: '2px solid #3b82f6', boxShadow: '0 8px 32px rgba(59,130,246,0.15)' }}>
                                    {/* Header bar */}
                                    <div style={{ background: '#0f172a', padding: '8px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                                        <span style={{ fontSize: 12, color: '#94a3b8', fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                                            🌐 {previewUrl(draft)}
                                        </span>
                                        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                                            <a
                                                href={previewUrl(draft)}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                style={{ background: '#1e40af', color: '#fff', textDecoration: 'none', borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 600 }}
                                            >
                                                ↗ פתח בטאב
                                            </a>
                                            <button
                                                onClick={() => setPreviewOpen(prev => ({ ...prev, [biz.id]: false }))}
                                                style={{ background: '#374151', border: 'none', color: '#9ca3af', cursor: 'pointer', borderRadius: 6, padding: '3px 8px', fontSize: 11 }}
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    </div>
                                    {/* iframe */}
                                    <iframe
                                        src={previewUrl(draft)}
                                        style={{ width: '100%', height: 700, border: 'none', display: 'block', background: '#fff' }}
                                        title={`תצוגה מקדימה: ${biz.name}`}
                                        sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
                                    />
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </Card>
    );
}
