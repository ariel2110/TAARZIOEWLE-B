import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getPublicDemo, trackDemoView, PublicDemoData } from '../services/queries';

// ── Color themes by category ──────────────────────────────────────────────
function getTheme(category?: string | null, types?: string | null) {
    const text = `${category || ''} ${types || ''}`.toLowerCase();
    if (/גריל|פיצ|קפה|מאפ|אוכל|מסעד/.test(text))
        return { primary: '#dc2626', secondary: '#f97316', gradient: 'linear-gradient(135deg,#7f1d1d,#dc2626,#f97316)', emoji: '🍽️' };
    if (/ספר|יופי|ציפור|עיצוב שיער/.test(text))
        return { primary: '#9333ea', secondary: '#ec4899', gradient: 'linear-gradient(135deg,#4a1d96,#9333ea,#ec4899)', emoji: '✂️' };
    if (/מוסך|מכונא|שרברב|חשמל|מזגן|שיפוץ|ניקיון/.test(text))
        return { primary: '#1d4ed8', secondary: '#0ea5e9', gradient: 'linear-gradient(135deg,#1e3a5f,#1d4ed8,#0ea5e9)', emoji: '🔧' };
    if (/גנן|גינ/.test(text))
        return { primary: '#15803d', secondary: '#16a34a', gradient: 'linear-gradient(135deg,#14532d,#15803d,#4ade80)', emoji: '🌿' };
    if (/פיזיוטרפ|יוגה|פילאטיס|וטרינר|בריא/.test(text))
        return { primary: '#0f766e', secondary: '#059669', gradient: 'linear-gradient(135deg,#042f2e,#0f766e,#34d399)', emoji: '🌿' };
    if (/גן ילד|ילד/.test(text))
        return { primary: '#0284c7', secondary: '#a21caf', gradient: 'linear-gradient(135deg,#0c4a6e,#0284c7,#a21caf)', emoji: '🌈' };
    return { primary: '#7c3aed', secondary: '#6366f1', gradient: 'linear-gradient(135deg,#1e1b4b,#7c3aed,#6366f1)', emoji: '⭐' };
}

function Stars({ rating }: { rating?: number | null }) {
    if (!rating) return null;
    const full = Math.floor(rating);
    const half = rating - full >= 0.5;
    return (
        <span style={{ fontSize: 22, letterSpacing: 2 }}>
            {'★'.repeat(full)}
            {half ? '½' : ''}
            {'☆'.repeat(Math.max(0, 5 - full - (half ? 1 : 0)))}
        </span>
    );
}

function PhoneBtn({ phone, primary }: { phone: string; primary: string }) {
    const clean = phone.replace(/\D/g, '');
    return (
        <a href={`tel:${clean}`}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 10, background: '#16a34a', color: 'white', textDecoration: 'none', borderRadius: 50, padding: '14px 32px', fontSize: 18, fontWeight: 700, boxShadow: '0 8px 24px rgba(22,163,74,0.4)', letterSpacing: 0.5 }}>
            📞 {phone}
        </a>
    );
}

function WaBtnAdmin({ bizName }: { bizName: string }) {
    const phone = (import.meta.env.VITE_TAZO_WEB_WA_PHONE || '972523456789') as string;
    const msg = encodeURIComponent(
        `שלום! ראיתי את האתר הדמו שבניתם עבור "${bizName}" 🌐\n\nהאתר נראה מדהים וייצוגי!\nאשמח לשמוע פרטים על תהליך בניית האתר האמיתי ⭐`
    );
    return (
        <a href={`https://wa.me/${phone}?text=${msg}`} target="_blank" rel="noopener noreferrer"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 10, background: '#25d366', color: 'white', textDecoration: 'none', borderRadius: 50, padding: '14px 32px', fontSize: 17, fontWeight: 700, boxShadow: '0 8px 24px rgba(37,211,102,0.4)' }}>
            💬 אני מעוניין — שלחו לי פרטים
        </a>
    );
}

export default function DemoSitePage() {
    const { slug } = useParams<{ slug: string }>();
    const [data, setData] = useState<PublicDemoData | null>(null);
    const [error, setError] = useState(false);

    useEffect(() => {
        if (!slug) return;
        getPublicDemo(slug)
            .then(d => { setData(d); trackDemoView(slug).catch(() => { }); })
            .catch(() => setError(true));
    }, [slug]);

    if (error) return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'system-ui', direction: 'rtl' }}>
            <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 48 }}>🔍</div>
                <h2 style={{ color: '#374151' }}>הדף לא נמצא</h2>
                <p style={{ color: '#9ca3af' }}>הקישור אינו תקין או שפג תוקפו.</p>
            </div>
        </div>
    );

    if (!data) return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'system-ui' }}>
            <div style={{ fontSize: 36, animation: 'spin 1s linear infinite' }}>⏳</div>
        </div>
    );

    const theme = getTheme(data.category, data.business_types);
    const reviewText = data.top_review?.slice(0, 280) || '';

    // About text — generated from types
    const aboutText = (() => {
        const t = `${data.category || ''} ${data.business_types || ''}`;
        if (/ספר|יופי/.test(t)) return `אנחנו מספרה/סלון מקצועי עם ניסיון של שנים. אנחנו מאמינים שכל לקוח ראוי לטיפול אישי ומקצועי. אצלנו תמצאו אווירה נעימה, ידיים מיומנות, ותוצאות שמדברות בעד עצמן.`;
        if (/מוסך|מכונא/.test(t)) return `אנחנו מוסך מורשה עם צוות מכונאים מנוסה. מתמחים בכל דגמי הרכב — מאבחון ועד תיקון. שקיפות מלאה, מחירים הוגנים, ועבודה שתעמוד בבדיקה.`;
        if (/גנן|גינ/.test(t)) return `גינן מקצועי עם עין לפרטים ואהבה לטבע. מטפלים בגינות פרטיות, מסחריות ובנייני מגורים. שתילה, עיצוב, גיזום וגינון שוטף — הכל אצלנו.`;
        if (/שרברב|אינסטלציה/.test(t)) return `שרברב מוסמך זמין לחירום ולתיקונים שוטפים. מים, ביוב, אינסטלציה — טיפול מהיר ומקצועי בלי הפתעות.`;
        if (/חשמל/.test(t)) return `חשמלאי מוסמך לכל עבודות החשמל בבית ובעסק. בטיחות היא ערך עליון אצלנו — עבודה לפי תקן, עם חומרים איכותיים בלבד.`;
        if (/גריל|פיצ|אוכל|מסעד/.test(t)) return `מקום אוכל אמיתי, עם אוכל טרי ואהבה לבישול. אנחנו מאמינים שארוחה טובה מתחילה מחומרי גלם איכותיים ומסתיימת בחיוך מרוצה.`;
        if (/קפה/.test(t)) return `בית קפה ביתי ונעים, שבו כל כוס מחולצת בקפידה. קפה טרי, עוגות אהבה, ואווירה שגורמת לך להישאר קצת יותר.`;
        if (/וטרינר/.test(t)) return `וטרינר עם לב גדול לחיות. מטפלים בחיות מחמד בגישה אוהבת ומקצועית, כי הם בני המשפחה שלכם.`;
        if (/פיזיוטרפ|יוגה|פילאטיס/.test(t)) return `אנחנו מאמינים שהגוף הוא מתנה. מטפלים בשיטות מתקדמות, מותאמות אישית לכל מטופל, עם דגש על תוצאות ולא רק על תסמינים.`;
        return `עסק מקצועי עם שנות ותק ולקוחות מרוצים. אנחנו גאים בשירות שלנו ומתחייבים לאיכות בכל עבודה. צרו קשר ונשמח לעזור!`;
    })();

    return (
        <div dir="rtl" style={{ fontFamily: '"Segoe UI", system-ui, -apple-system, Arial, sans-serif', minHeight: '100vh', background: '#f8fafc' }}>

            {/* ── Demo banner ── */}
            <div style={{ background: '#fef3c7', borderBottom: '2px solid #f59e0b', padding: '9px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, position: 'sticky', top: 0, zIndex: 100 }}>
                <span style={{ fontSize: 13, color: '#78350f', fontWeight: 600 }}>
                    🎬 זהו <strong>אתר דמו חינמי</strong> שנבנה עבור <strong>{data.business_name}</strong> ע"י tazo-web
                </span>
                <a href={`https://wa.me/${(import.meta.env.VITE_TAZO_WEB_WA_PHONE || '972523456789') as string}?text=${encodeURIComponent(`שלום! ראיתי את הדמו של "${data.business_name}" ואשמח לדבר על בניית האתר 😊`)}`}
                    target="_blank" rel="noopener noreferrer"
                    style={{ background: '#f59e0b', color: '#78350f', textDecoration: 'none', borderRadius: 20, padding: '5px 14px', fontSize: 12, fontWeight: 700, whiteSpace: 'nowrap' }}>
                    📱 רוצים אתר אמיתי? לחצו כאן!
                </a>
            </div>

            {/* ── Hero ── */}
            <div style={{ background: theme.gradient, color: 'white', padding: '60px 24px 70px', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
                {/* decorative circles */}
                <div style={{ position: 'absolute', top: -60, left: -60, width: 200, height: 200, borderRadius: '50%', background: 'rgba(255,255,255,0.07)', pointerEvents: 'none' }} />
                <div style={{ position: 'absolute', bottom: -40, right: -40, width: 160, height: 160, borderRadius: '50%', background: 'rgba(255,255,255,0.06)', pointerEvents: 'none' }} />

                <div style={{ fontSize: 52, marginBottom: 8 }}>{theme.emoji}</div>
                <h1 style={{ fontSize: 'clamp(28px,5vw,48px)', fontWeight: 800, margin: '0 0 10px', textShadow: '0 2px 8px rgba(0,0,0,0.3)', letterSpacing: -0.5 }}>
                    {data.business_name}
                </h1>
                {data.tagline && (
                    <p style={{ fontSize: 'clamp(15px,2.5vw,20px)', opacity: 0.9, margin: '0 0 24px', maxWidth: 600, marginLeft: 'auto', marginRight: 'auto' }}>
                        {data.tagline}
                    </p>
                )}

                {/* Stars + reviews */}
                {data.rating && (
                    <div style={{ marginBottom: 28, display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                        <div style={{ color: '#fbbf24' }}><Stars rating={data.rating} /></div>
                        <span style={{ fontSize: 15, opacity: 0.85 }}>
                            {data.rating} / 5 · {data.reviews_count?.toLocaleString()} ביקורות בגוגל
                        </span>
                    </div>
                )}

                {/* Phone CTA */}
                {data.phone && (
                    <div style={{ marginBottom: 16 }}>
                        <PhoneBtn phone={data.phone} primary={theme.primary} />
                    </div>
                )}
                {data.city && <p style={{ fontSize: 14, opacity: 0.7, margin: 0 }}>📍 {data.city}</p>}
            </div>

            {/* ── Wave divider ── */}
            <div style={{ marginTop: -2, lineHeight: 0 }}>
                <svg viewBox="0 0 1200 60" preserveAspectRatio="none" style={{ display: 'block', width: '100%', height: 50 }}>
                    <path d="M0,60 C300,0 900,60 1200,0 L1200,60 Z" fill="#f8fafc" />
                </svg>
            </div>

            {/* ── Content ── */}
            <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 20px 60px' }}>

                {/* About */}
                <section style={{ background: 'white', borderRadius: 16, padding: '28px 28px', marginBottom: 24, boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
                    <h2 style={{ fontSize: 20, fontWeight: 700, color: '#1f2937', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ background: theme.gradient, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>✦</span>
                        אודות {data.business_name}
                    </h2>
                    <p style={{ fontSize: 16, color: '#374151', lineHeight: 1.7, margin: 0 }}>{aboutText}</p>
                </section>

                {/* Review */}
                {reviewText && (
                    <section style={{ background: 'white', borderRadius: 16, padding: '28px 28px', marginBottom: 24, boxShadow: '0 2px 12px rgba(0,0,0,0.06)', borderRight: `4px solid ${theme.primary}` }}>
                        <h2 style={{ fontSize: 20, fontWeight: 700, color: '#1f2937', marginBottom: 16 }}>
                            💬 מה אומרים הלקוחות
                        </h2>
                        <blockquote style={{ fontSize: 16, color: '#4b5563', lineHeight: 1.7, fontStyle: 'italic', margin: '0 0 14px', borderRight: 'none' }}>
                            "{reviewText}{data.top_review && data.top_review.length > 280 ? '...' : ''}"
                        </blockquote>
                        {data.rating && (
                            <div style={{ color: '#fbbf24', fontSize: 18 }}>
                                {'★'.repeat(Math.round(data.rating))}
                                <span style={{ color: '#9ca3af', fontSize: 13, marginRight: 8 }}>לקוח מרוצה · גוגל</span>
                            </div>
                        )}
                    </section>
                )}

                {/* Stats row */}
                {(data.rating || data.reviews_count || data.phone) && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 14, marginBottom: 24 }}>
                        {data.rating && (
                            <div style={{ background: 'white', borderRadius: 14, padding: '20px 16px', textAlign: 'center', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
                                <div style={{ fontSize: 28, color: '#fbbf24', marginBottom: 4 }}>⭐</div>
                                <div style={{ fontSize: 22, fontWeight: 800, color: '#1f2937' }}>{data.rating}</div>
                                <div style={{ fontSize: 13, color: '#6b7280' }}>דירוג גוגל</div>
                            </div>
                        )}
                        {data.reviews_count && (
                            <div style={{ background: 'white', borderRadius: 14, padding: '20px 16px', textAlign: 'center', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
                                <div style={{ fontSize: 28, marginBottom: 4 }}>🗣️</div>
                                <div style={{ fontSize: 22, fontWeight: 800, color: '#1f2937' }}>{data.reviews_count.toLocaleString()}</div>
                                <div style={{ fontSize: 13, color: '#6b7280' }}>ביקורות</div>
                            </div>
                        )}
                        {data.phone && (
                            <div style={{ background: 'white', borderRadius: 14, padding: '20px 16px', textAlign: 'center', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
                                <div style={{ fontSize: 28, marginBottom: 4 }}>📞</div>
                                <div style={{ fontSize: 16, fontWeight: 700, color: '#1f2937' }}>{data.phone}</div>
                                <div style={{ fontSize: 13, color: '#6b7280' }}>טלפון</div>
                            </div>
                        )}
                    </div>
                )}

                {/* Location */}
                {data.address && (
                    <section style={{ background: 'white', borderRadius: 16, padding: '28px 28px', marginBottom: 24, boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
                        <h2 style={{ fontSize: 20, fontWeight: 700, color: '#1f2937', marginBottom: 12 }}>📍 מיקום ויצירת קשר</h2>
                        <p style={{ fontSize: 15, color: '#374151', margin: '0 0 14px' }}>{data.address}</p>
                        {data.google_maps_url && (
                            <a href={data.google_maps_url} target="_blank" rel="noopener noreferrer"
                                style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: theme.primary, fontWeight: 600, fontSize: 14, textDecoration: 'none', border: `1.5px solid ${theme.primary}`, borderRadius: 20, padding: '6px 16px' }}>
                                🗺️ פתח בגוגל מפות
                            </a>
                        )}
                    </section>
                )}

                {/* CTA conversion */}
                <section style={{ background: theme.gradient, borderRadius: 20, padding: '40px 28px', textAlign: 'center', color: 'white', boxShadow: `0 12px 40px rgba(0,0,0,0.2)` }}>
                    <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 10 }}>
                        🚀 רוצים אתר אמיתי לעסק שלכם?
                    </h2>
                    <p style={{ fontSize: 16, opacity: 0.9, marginBottom: 28, maxWidth: 500, margin: '0 auto 28px' }}>
                        tazo-web בונה אתרים מקצועיים לעסקים קטנים — תוך 48 שעות, בצורה פשוטה, ובמחיר שמתאים לכם.
                    </p>
                    <WaBtnAdmin bizName={data.business_name} />
                </section>
            </div>

            {/* ── Footer ── */}
            <div style={{ textAlign: 'center', padding: '20px', borderTop: '1px solid #e5e7eb', color: '#9ca3af', fontSize: 12 }}>
                האתר נבנה ע"י <strong>tazo-web</strong> · אתרים לעסקים קטנים ·
                <a href="https://admin.tazo-web.com" style={{ color: '#6b7280', marginRight: 4 }}>admin.tazo-web.com</a>
            </div>
        </div>
    );
}
