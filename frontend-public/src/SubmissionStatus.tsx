import { useEffect, useState } from 'react';

const API = import.meta.env.VITE_API_BASE || 'https://api.sitenest.site/api/v1';
const WA = '972546363350';
const MAX_CORRECTIONS = 3;

interface IntakeStatus {
    token: string;
    business_name: string;
    phone: string;
    facebook_url: string | null;
    tiktok_url: string | null;
    instagram_url: string | null;
    website_url: string | null;
    description: string | null;
    image_urls: string[];
    status: string;
    correction_count: number;
    corrections_remaining: number;
    admin_note: string | null;
    created_at: string | null;
}

interface Props {
    token: string;
    onBack: () => void;
}

const STATUS_LABELS: Record<string, { label: string; color: string; icon: string }> = {
    submitted: { label: 'התקבל — בבדיקה', color: '#6366f1', icon: '📥' },
    in_review: { label: 'בבדיקה', color: '#f59e0b', icon: '🔍' },
    revision_requested: { label: 'שינוי התבקש', color: '#3b82f6', icon: '✏️' },
    done: { label: 'מוכן! 🎉', color: '#10b981', icon: '✅' },
    cancelled: { label: 'בוטל', color: '#ef4444', icon: '❌' },
};

export default function SubmissionStatus({ token, onBack }: Props) {
    const [data, setData] = useState<IntakeStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState('');
    const [correctionNote, setCorrectionNote] = useState('');
    const [showCorrectionForm, setShowCorrectionForm] = useState(false);
    const [correctionSubmitting, setCorrectionSubmitting] = useState(false);
    const [correctionError, setCorrectionError] = useState('');
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [deleteSubmitting, setDeleteSubmitting] = useState(false);
    const [actionSuccess, setActionSuccess] = useState('');

    useEffect(() => {
        if (!token) {
            setLoadError('קישור לא תקין');
            setLoading(false);
            return;
        }
        fetchStatus();
    }, [token]);

    async function fetchStatus() {
        setLoading(true);
        setLoadError('');
        try {
            const res = await fetch(`${API}/public/intake/${token}`);
            if (!res.ok) throw new Error('לא נמצא');
            const d: IntakeStatus = await res.json();
            setData(d);
        } catch {
            setLoadError('לא ניתן לטעון את פרטי הבקשה. בדוק את הקישור.');
        } finally {
            setLoading(false);
        }
    }

    async function submitCorrection() {
        if (!correctionNote.trim()) {
            setCorrectionError('נא לפרט מה לשנות');
            return;
        }
        setCorrectionSubmitting(true);
        setCorrectionError('');
        try {
            const res = await fetch(`${API}/public/intake/${token}/correction`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `note=${encodeURIComponent(correctionNote.trim())}`,
            });
            if (!res.ok) {
                const d = await res.json().catch(() => ({}));
                throw new Error(d.detail || 'שגיאה');
            }
            const updated: IntakeStatus = await res.json();
            setData(updated);
            setShowCorrectionForm(false);
            setCorrectionNote('');
            setActionSuccess('✅ בקשת התיקון התקבלה! ניצור קשר בקרוב.');
        } catch (err: unknown) {
            setCorrectionError(err instanceof Error ? err.message : 'שגיאה');
        } finally {
            setCorrectionSubmitting(false);
        }
    }

    async function confirmDelete() {
        setDeleteSubmitting(true);
        try {
            await fetch(`${API}/public/intake/${token}`, { method: 'DELETE' });
            setData(prev => prev ? { ...prev, status: 'cancelled' } : prev);
            setShowDeleteConfirm(false);
            setActionSuccess('הבקשה בוטלה. נשמח לשמוע מך שוב בעתיד!');
        } catch {
            setShowDeleteConfirm(false);
        } finally {
            setDeleteSubmitting(false);
        }
    }

    const waMessage = data
        ? encodeURIComponent(`היי! שלחתי בקשה לאתר עבור "${data.business_name}" ואני צריך עזרה`)
        : encodeURIComponent('היי! יש לי שאלה על הבקשה שלי ב-SiteNest');

    // ── Loading ──
    if (loading) {
        return (
            <div className="ss-root ss-loading">
                <div className="ss-spinner-large" />
                <p>טוען את פרטי הבקשה...</p>
            </div>
        );
    }

    // ── Error ──
    if (loadError || !data) {
        return (
            <div className="ss-root ss-error-page">
                <div className="ss-back-row">
                    <button className="if-back-btn" onClick={onBack}>← חזור לדף הבית</button>
                </div>
                <div className="ss-error-card">
                    <div className="ss-error-icon">😕</div>
                    <h2>לא נמצאה בקשה</h2>
                    <p>{loadError || 'הקישור אינו תקין או שפג תוקפו'}</p>
                    <button className="le-cta-btn-primary" onClick={onBack}>חזור לדף הבית</button>
                </div>
            </div>
        );
    }

    const statusInfo = STATUS_LABELS[data.status] || { label: data.status, color: '#6b7280', icon: '❓' };
    const isCancelled = data.status === 'cancelled';
    const canCorrect = !isCancelled && data.corrections_remaining > 0;

    return (
        <div className="ss-root">
            {/* Header */}
            <div className="if-header">
                <button className="if-back-btn" onClick={onBack}>
                    ← דף הבית
                </button>
                <div className="if-header-logo">SiteNest ✦</div>
            </div>

            <div className="ss-wrap">
                {/* Status hero */}
                <div className="ss-status-hero" style={{ '--status-color': statusInfo.color } as React.CSSProperties}>
                    <div className="ss-status-icon-big">{statusInfo.icon}</div>
                    <h1 className="ss-title">הבקשה שלך — {data.business_name}</h1>
                    <div className="ss-status-badge" style={{ background: statusInfo.color }}>
                        {statusInfo.label}
                    </div>
                    <p className="ss-status-sub">
                        {data.status === 'submitted' && 'קיבלנו את הבקשה! ה-AI מתחיל לבנות את האתר שלך. נעדכן אותך בוואטסאפ.'}
                        {data.status === 'in_review' && 'הצוות שלנו בונה ובודק את האתר. נשלח לך לינק בקרוב.'}
                        {data.status === 'revision_requested' && 'ביקשת שינויים — הצוות מטפל. נדאג לעדכנך.'}
                        {data.status === 'done' && '🎉 האתר שלך מוכן! בדוק אותו בלינק שנשלח לוואטסאפ שלך.'}
                        {data.status === 'cancelled' && 'הבקשה בוטלה. נשמח לעזור שוב בכל עת.'}
                    </p>
                </div>

                {/* Success message */}
                {actionSuccess && (
                    <div className="ss-action-success">
                        {actionSuccess}
                    </div>
                )}

                <div className="ss-grid">
                    {/* ── Details card ── */}
                    <div className="ss-card">
                        <h2 className="ss-card-title">📋 פרטי הבקשה</h2>
                        <div className="ss-detail-list">
                            <div className="ss-detail-row">
                                <span className="ss-detail-label">שם עסק</span>
                                <span className="ss-detail-value">{data.business_name}</span>
                            </div>
                            <div className="ss-detail-row">
                                <span className="ss-detail-label">טלפון</span>
                                <span className="ss-detail-value" dir="ltr">{data.phone}</span>
                            </div>
                            {data.facebook_url && (
                                <div className="ss-detail-row">
                                    <span className="ss-detail-label">📘 פייסבוק</span>
                                    <a className="ss-detail-link" href={data.facebook_url} target="_blank" rel="noopener noreferrer">
                                        צפה בעמוד ↗
                                    </a>
                                </div>
                            )}
                            {data.tiktok_url && (
                                <div className="ss-detail-row">
                                    <span className="ss-detail-label">🎵 טיקטוק</span>
                                    <a className="ss-detail-link" href={data.tiktok_url} target="_blank" rel="noopener noreferrer">
                                        צפה בפרופיל ↗
                                    </a>
                                </div>
                            )}
                            {data.instagram_url && (
                                <div className="ss-detail-row">
                                    <span className="ss-detail-label">📸 אינסטגרם</span>
                                    <a className="ss-detail-link" href={data.instagram_url} target="_blank" rel="noopener noreferrer">
                                        צפה בפרופיל ↗
                                    </a>
                                </div>
                            )}
                            {data.description && (
                                <div className="ss-detail-row ss-detail-full">
                                    <span className="ss-detail-label">תיאור העסק</span>
                                    <p className="ss-detail-desc">{data.description}</p>
                                </div>
                            )}
                            {data.created_at && (
                                <div className="ss-detail-row">
                                    <span className="ss-detail-label">נשלח ב</span>
                                    <span className="ss-detail-value">
                                        {new Date(data.created_at).toLocaleDateString('he-IL', {
                                            day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
                                        })}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* ── Corrections + actions card ── */}
                    <div className="ss-card">
                        <h2 className="ss-card-title">⚙️ פעולות</h2>

                        {/* Correction counter */}
                        <div className="ss-corrections-bar">
                            <span>בקשות תיקון</span>
                            <div className="ss-correction-dots">
                                {[0, 1, 2].map(i => (
                                    <span
                                        key={i}
                                        className={`ss-correction-dot ${i < data.correction_count ? 'used' : ''}`}
                                    />
                                ))}
                            </div>
                            <span className="ss-corrections-remaining">
                                {data.corrections_remaining} נותרו מתוך {MAX_CORRECTIONS}
                            </span>
                        </div>

                        {/* Correction form */}
                        {canCorrect && !showCorrectionForm && !isCancelled && (
                            <button
                                className="ss-action-btn ss-btn-correction"
                                onClick={() => setShowCorrectionForm(true)}
                            >
                                ✏️ בקש תיקון / שינוי
                            </button>
                        )}

                        {showCorrectionForm && (
                            <div className="ss-correction-form">
                                <label className="if-label">מה לשנות?</label>
                                <textarea
                                    className="if-textarea"
                                    placeholder="תאר בפירוט מה תרצה שנשנה: צבע, טקסט, תמונה, סדר, וכו'"
                                    value={correctionNote}
                                    onChange={e => setCorrectionNote(e.target.value)}
                                    rows={4}
                                    maxLength={500}
                                />
                                {correctionError && <p className="if-error-msg">{correctionError}</p>}
                                <div className="ss-correction-actions">
                                    <button
                                        className="ss-action-btn ss-btn-correction"
                                        onClick={submitCorrection}
                                        disabled={correctionSubmitting}
                                    >
                                        {correctionSubmitting ? '⏳ שולח...' : '✓ שלח בקשת תיקון'}
                                    </button>
                                    <button
                                        className="ss-action-btn ss-btn-secondary"
                                        onClick={() => { setShowCorrectionForm(false); setCorrectionNote(''); }}
                                    >
                                        ביטול
                                    </button>
                                </div>
                            </div>
                        )}

                        {!canCorrect && !isCancelled && (
                            <div className="ss-corrections-exhausted">
                                ℹ️ ניצלת את כל בקשות התיקון החינמיות.
                                לתיקונים נוספים, צור קשר בוואטסאפ.
                            </div>
                        )}

                        {/* Help button */}
                        <a
                            href={`https://wa.me/${WA}?text=${waMessage}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="ss-action-btn ss-btn-help"
                        >
                            💬 בקש עזרה בוואטסאפ
                        </a>

                        {/* Refresh */}
                        <button className="ss-action-btn ss-btn-secondary" onClick={fetchStatus}>
                            🔄 רענן סטטוס
                        </button>

                        {/* Delete */}
                        {!isCancelled && (
                            <button
                                className="ss-action-btn ss-btn-delete"
                                onClick={() => setShowDeleteConfirm(true)}
                            >
                                🗑 מחק את הבקשה
                            </button>
                        )}
                    </div>
                </div>

                {/* Uploaded images */}
                {data.image_urls.length > 0 && (
                    <div className="ss-card ss-images-card">
                        <h2 className="ss-card-title">🖼 תמונות שהעלית</h2>
                        <div className="if-image-grid">
                            {data.image_urls.map((url, i) => (
                                <div key={i} className="if-image-thumb">
                                    <img
                                        src={`https://api.sitenest.site${url}`}
                                        alt={`תמונה ${i + 1}`}
                                        loading="lazy"
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Timeline */}
                <div className="ss-card">
                    <h2 className="ss-card-title">🗺 מה הלאה?</h2>
                    <div className="ss-timeline">
                        {[
                            { done: true, label: 'הבקשה התקבלה' },
                            { done: ['in_review', 'revision_requested', 'done'].includes(data.status), label: 'ה-AI בונה את האתר' },
                            { done: ['done'].includes(data.status), label: 'אישור סופי ופרסום' },
                        ].map((item, i) => (
                            <div key={i} className={`ss-timeline-item ${item.done ? 'done' : ''}`}>
                                <span className="ss-timeline-dot">{item.done ? '✓' : '○'}</span>
                                <span>{item.label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── Delete confirmation modal ── */}
            {showDeleteConfirm && (
                <div className="ss-modal-overlay">
                    <div className="ss-modal">
                        <div className="ss-modal-icon">⚠️</div>
                        <h2 className="ss-modal-title">האם למחוק את הבקשה?</h2>
                        <p className="ss-modal-body">
                            פעולה זו לא ניתנת לביטול. כל הפרטים והתמונות שהעלית יימחקו.
                        </p>
                        <div className="ss-modal-actions">
                            <button
                                className="ss-action-btn ss-btn-delete"
                                onClick={confirmDelete}
                                disabled={deleteSubmitting}
                            >
                                {deleteSubmitting ? '⏳ מוחק...' : '✓ כן, מחק הכל'}
                            </button>
                            <button
                                className="ss-action-btn ss-btn-secondary"
                                onClick={() => setShowDeleteConfirm(false)}
                            >
                                ביטול — השאר את הבקשה
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
