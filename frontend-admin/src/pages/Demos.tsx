import { useEffect, useState } from 'react';
import { Card, SectionTitle } from '../components/ui';
import { DemoRecord, getDemos, markDemoSent, markDemoConverted, deleteDemo } from '../services/queries';

const DEMO_BASE = 'https://admin.sitenest.site';

const STATUS_LABELS: Record<string, { label: string; bg: string; color: string }> = {
    draft: { label: '📝 טיוטה', bg: '#f3f4f6', color: '#374151' },
    sent: { label: '📤 נשלח', bg: '#dbeafe', color: '#1e40af' },
    viewed: { label: '👁️ נצפה', bg: '#fef3c7', color: '#92400e' },
    converted: { label: '✅ הומר', bg: '#d1fae5', color: '#065f46' },
};

function cleanPhone(phone: string): string {
    const digits = phone.replace(/\D/g, '');
    if (digits.startsWith('0')) return '972' + digits.slice(1);
    if (digits.startsWith('+')) return digits.slice(1);
    return digits;
}

function buildWhatsApp(demo: DemoRecord): string {
    if (!demo.phone) return '';
    const demoUrl = `${DEMO_BASE}/demo/${demo.slug}`;
    const msg = encodeURIComponent(
        `שלום ${demo.business_name} 👋\n\n` +
        `ראינו שאין לכם אתר אינטרנט, אז הכנו לכם אחד *במתנה* — ` +
        `תוך 5 דקות! 🎉\n\n` +
        `👉 *לצפייה בדמו שלכם:*\n${demoUrl}\n\n` +
        `האתר כולל:\n` +
        `✅ עמוד עסק מקצועי\n` +
        `✅ הביקורות שלכם מגוגל\n` +
        `✅ כפתור חיוג ישיר\n` +
        `✅ מיקום בגוגל מפות\n\n` +
        `אם תרצו להמשיך לאתר אמיתי — נשמח לדבר 😊\n` +
        `— צוות *SiteNest*`
    );
    return `https://wa.me/${cleanPhone(demo.phone)}?text=${msg}`;
}

function StatusBadge({ status }: { status: string }) {
    const s = STATUS_LABELS[status] || STATUS_LABELS.draft;
    return (
        <span style={{ background: s.bg, color: s.color, borderRadius: 20, padding: '2px 10px', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap' }}>
            {s.label}
        </span>
    );
}

export default function DemosPage() {
    const [demos, setDemos] = useState<DemoRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [msg, setMsg] = useState('');

    const load = () => {
        setLoading(true);
        getDemos()
            .then(setDemos)
            .catch(() => { })
            .finally(() => setLoading(false));
    };

    useEffect(() => { load(); }, []);

    const handleMarkSent = async (demo: DemoRecord) => {
        await markDemoSent(demo.id);
        setMsg(`✅ "${demo.business_name}" סומן כנשלח`);
        load();
    };

    const handleMarkConverted = async (demo: DemoRecord) => {
        await markDemoConverted(demo.id);
        setMsg(`🎉 "${demo.business_name}" הומר ללקוח!`);
        load();
    };

    const handleDelete = async (demo: DemoRecord) => {
        if (!confirm(`למחוק את הדמו של "${demo.business_name}"?`)) return;
        await deleteDemo(demo.id);
        setDemos(prev => prev.filter(d => d.id !== demo.id));
    };

    // Stats summary
    const totalViewed = demos.filter(d => d.view_count > 0).length;
    const totalConverted = demos.filter(d => d.status === 'converted').length;
    const totalSent = demos.filter(d => ['sent', 'viewed', 'converted'].includes(d.status)).length;

    return (
        <div dir="rtl" style={{ maxWidth: 1000, margin: '0 auto' }}>
            <SectionTitle>📱 אתרי דמו — שלח ולקוח</SectionTitle>

            {/* HOW IT WORKS */}
            <div style={{ background: 'linear-gradient(135deg,#ede9fe,#dbeafe)', border: '1.5px solid #a5b4fc', borderRadius: 14, padding: '16px 20px', marginBottom: 20 }}>
                <div style={{ fontWeight: 700, fontSize: 14, color: '#3730a3', marginBottom: 10 }}>🔄 איך זה עובד?</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                    {[
                        { n: '1', t: 'דף איסוף', d: 'בחר עסקים ולחץ "צור דמואים"' },
                        { n: '2', t: 'אתר דמו נוצר', d: 'קישור ייחודי מוכן לשליחה' },
                        { n: '3', t: 'שלח בוואטסאפ', d: 'כפתור מוכן עם הודעה מוכנה' },
                        { n: '4', t: 'לקוח צופה', d: 'אתה רואה כמה צפיות היו' },
                        { n: '5', t: 'לקוח נסגר', d: 'סמן "הומר" ועבור לשלב הבא' },
                    ].map(({ n, t, d }) => (
                        <div key={n} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, minWidth: 150 }}>
                            <span style={{ background: '#6366f1', color: 'white', borderRadius: '50%', width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, flexShrink: 0 }}>{n}</span>
                            <div>
                                <div style={{ fontSize: 12, fontWeight: 700, color: '#1e1b4b' }}>{t}</div>
                                <div style={{ fontSize: 11, color: '#6b7280' }}>{d}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Stats */}
            {demos.length > 0 && (
                <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
                    <span style={{ background: '#f3f4f6', borderRadius: 20, padding: '4px 14px', fontSize: 13 }}>📊 סה"כ: {demos.length}</span>
                    <span style={{ background: '#dbeafe', color: '#1e40af', borderRadius: 20, padding: '4px 14px', fontSize: 13, fontWeight: 600 }}>📤 נשלחו: {totalSent}</span>
                    <span style={{ background: '#fef3c7', color: '#92400e', borderRadius: 20, padding: '4px 14px', fontSize: 13, fontWeight: 600 }}>👁️ נצפו: {totalViewed}</span>
                    <span style={{ background: '#d1fae5', color: '#065f46', borderRadius: 20, padding: '4px 14px', fontSize: 13, fontWeight: 700 }}>✅ הומרו: {totalConverted}</span>
                </div>
            )}

            {msg && (
                <div style={{ background: '#d1fae5', color: '#065f46', borderRadius: 10, padding: '10px 16px', marginBottom: 14, fontWeight: 600, fontSize: 14 }}>
                    {msg}
                </div>
            )}

            {loading && <Card><p style={{ textAlign: 'center', color: '#9ca3af', padding: 24 }}>⏳ טוען...</p></Card>}

            {!loading && demos.length === 0 && (
                <Card>
                    <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                        <div style={{ fontSize: 48, marginBottom: 12 }}>🎬</div>
                        <h3 style={{ color: '#374151', marginBottom: 8 }}>אין עדיין דמואים</h3>
                        <p style={{ color: '#9ca3af', fontSize: 14 }}>
                            עבור ל<strong>איסוף נתונים</strong>, בחר עסקים ולחץ "🎬 צור אתרי דמו"
                        </p>
                    </div>
                </Card>
            )}

            {/* Demo cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {demos.map(demo => {
                    const demoUrl = `${DEMO_BASE}/demo/${demo.slug}`;
                    const waLink = buildWhatsApp(demo);

                    return (
                        <div key={demo.id} style={{
                            background: 'white', borderRadius: 14, padding: '16px 20px',
                            border: `2px solid ${demo.status === 'converted' ? '#6ee7b7' : demo.status === 'viewed' ? '#fcd34d' : '#e5e7eb'}`,
                            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 10, marginBottom: 10 }}>
                                {/* Left: name + info */}
                                <div>
                                    <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>{demo.business_name}</div>
                                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                                        <StatusBadge status={demo.status} />
                                        {demo.view_count > 0 && (
                                            <span style={{ background: '#fef3c7', color: '#92400e', borderRadius: 20, padding: '2px 10px', fontSize: 12, fontWeight: 600 }}>
                                                👁️ {demo.view_count} צפיות
                                            </span>
                                        )}
                                        {demo.city && <span style={{ fontSize: 12, color: '#6b7280' }}>📍 {demo.city}</span>}
                                        {demo.category && <span style={{ fontSize: 12, color: '#6b7280' }}>· {demo.category}</span>}
                                        {demo.phone && <span style={{ fontSize: 12, color: '#374151' }}>📞 {demo.phone}</span>}
                                    </div>
                                </div>

                                {/* Right: stats */}
                                <div style={{ textAlign: 'center', minWidth: 80 }}>
                                    {demo.rating && (
                                        <div style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>⭐ {demo.rating} ({demo.reviews_count?.toLocaleString()})</div>
                                    )}
                                    <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
                                        {demo.created_at ? new Date(demo.created_at).toLocaleDateString('he-IL') : ''}
                                    </div>
                                </div>
                            </div>

                            {/* Demo URL */}
                            <div style={{ background: '#f8fafc', borderRadius: 8, padding: '8px 12px', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                <span style={{ fontSize: 12, color: '#6b7280', flexShrink: 0 }}>🔗 קישור:</span>
                                <a href={demoUrl} target="_blank" rel="noopener noreferrer"
                                    style={{ fontSize: 12, color: '#6366f1', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                                    {demoUrl}
                                </a>
                            </div>

                            {/* Actions */}
                            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                {/* Preview */}
                                <a href={demoUrl} target="_blank" rel="noopener noreferrer"
                                    style={{ textDecoration: 'none', background: '#ede9fe', color: '#6d28d9', borderRadius: 8, padding: '7px 14px', fontSize: 13, fontWeight: 600 }}>
                                    👁️ תצוגה מקדימה
                                </a>

                                {/* WhatsApp */}
                                {waLink && demo.status !== 'converted' && (
                                    <a href={waLink} target="_blank" rel="noopener noreferrer" onClick={() => handleMarkSent(demo)}
                                        style={{ textDecoration: 'none', background: '#dcfce7', color: '#15803d', borderRadius: 8, padding: '7px 14px', fontSize: 13, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        📱 שלח ב-WhatsApp
                                    </a>
                                )}

                                {/* Copy link */}
                                <button onClick={() => { navigator.clipboard.writeText(demoUrl); setMsg('✅ קישור הועתק!'); }}
                                    style={{ background: '#f3f4f6', color: '#374151', border: 'none', borderRadius: 8, padding: '7px 14px', fontSize: 13, cursor: 'pointer' }}>
                                    📋 העתק קישור
                                </button>

                                {/* Mark converted */}
                                {demo.status !== 'converted' && demo.status !== 'draft' && (
                                    <button onClick={() => handleMarkConverted(demo)}
                                        style={{ background: '#d1fae5', color: '#065f46', border: 'none', borderRadius: 8, padding: '7px 14px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
                                        ✅ סמן כהומר
                                    </button>
                                )}

                                {/* Delete */}
                                <button onClick={() => handleDelete(demo)}
                                    style={{ background: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: 8, padding: '7px 14px', fontSize: 13, cursor: 'pointer', marginRight: 'auto' }}>
                                    🗑️
                                </button>
                            </div>

                            {/* Viewed / sent timestamps */}
                            {(demo.whatsapp_sent_at || demo.first_viewed_at) && (
                                <div style={{ marginTop: 10, fontSize: 11, color: '#9ca3af', display: 'flex', gap: 14, flexWrap: 'wrap' }}>
                                    {demo.whatsapp_sent_at && <span>📤 נשלח: {new Date(demo.whatsapp_sent_at).toLocaleString('he-IL')}</span>}
                                    {demo.first_viewed_at && <span>👁️ נצפה לראשונה: {new Date(demo.first_viewed_at).toLocaleString('he-IL')}</span>}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
