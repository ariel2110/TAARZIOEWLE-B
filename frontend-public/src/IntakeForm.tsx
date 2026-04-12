import { useRef, useState } from 'react';

const API = import.meta.env.VITE_API_BASE || 'https://api.sitenest.site/api/v1';
const WA = '972546363350';

interface Props {
    onSubmitted: (token: string) => void;
    onBack: () => void;
}

const MAX_IMAGES = 5;
const ACCEPTED = 'image/jpeg,image/png,image/webp,image/gif';

// ── Validation helpers ──────────────────────────────────────────────────────
function isValidPhone(v: string) {
    return /^0\d{8,9}$|^972\d{9}$/.test(v.replace(/[-\s]/g, ''));
}

function isValidUrl(v: string) {
    if (!v) return true;
    try {
        const url = v.startsWith('http') ? v : `https://${v}`;
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

export default function IntakeForm({ onSubmitted, onBack }: Props) {
    const [businessName, setBusinessName] = useState('');
    const [phone, setPhone] = useState('');
    const [facebook, setFacebook] = useState('');
    const [tiktok, setTiktok] = useState('');
    const [instagram, setInstagram] = useState('');
    const [website, setWebsite] = useState('');
    const [description, setDescription] = useState('');
    const [images, setImages] = useState<File[]>([]);
    const [imagePreviews, setImagePreviews] = useState<string[]>([]);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [touched, setTouched] = useState<Record<string, boolean>>({});
    const fileInputRef = useRef<HTMLInputElement>(null);

    function touch(field: string) {
        setTouched(t => ({ ...t, [field]: true }));
    }

    function handleImageAdd(e: React.ChangeEvent<HTMLInputElement>) {
        const files = Array.from(e.target.files || []);
        const remaining = MAX_IMAGES - images.length;
        const toAdd = files.slice(0, remaining);
        setImages(prev => [...prev, ...toAdd]);
        toAdd.forEach(f => {
            const reader = new FileReader();
            reader.onload = ev => {
                setImagePreviews(prev => [...prev, ev.target?.result as string]);
            };
            reader.readAsDataURL(f);
        });
        if (fileInputRef.current) fileInputRef.current.value = '';
    }

    function removeImage(index: number) {
        setImages(prev => prev.filter((_, i) => i !== index));
        setImagePreviews(prev => prev.filter((_, i) => i !== index));
    }

    const errors = {
        businessName: !businessName.trim() ? 'שם העסק נדרש' : '',
        phone: !phone.trim() ? 'מספר טלפון נדרש' : !isValidPhone(phone) ? 'מספר לא תקין (05XXXXXXXX)' : '',
        facebook: facebook && !isValidUrl(facebook) ? 'כתובת URL לא תקינה' : '',
        tiktok: tiktok && !isValidUrl(tiktok) ? 'כתובת URL לא תקינה' : '',
        instagram: instagram && !isValidUrl(instagram) ? 'כתובת URL לא תקינה' : '',
        website: website && !isValidUrl(website) ? 'כתובת URL לא תקינה' : '',
    };

    const hasErrors = Object.values(errors).some(Boolean);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setTouched({ businessName: true, phone: true, facebook: true, tiktok: true, instagram: true, website: true });
        if (hasErrors) return;

        setSubmitting(true);
        setError('');

        try {
            const fd = new FormData();
            fd.append('business_name', businessName.trim());
            fd.append('phone', phone.trim());
            if (facebook) fd.append('facebook_url', facebook.trim());
            if (tiktok) fd.append('tiktok_url', tiktok.trim());
            if (instagram) fd.append('instagram_url', instagram.trim());
            if (website) fd.append('website_url', website.trim());
            if (description) fd.append('description', description.trim());
            images.forEach(img => fd.append('images', img));

            const res = await fetch(`${API}/public/intake`, {
                method: 'POST',
                body: fd,
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || 'שגיאה בשליחה');
            }

            const data = await res.json();
            onSubmitted(data.token);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'שגיאה לא צפויה. נסה שוב.');
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="if-root">
            {/* Header */}
            <div className="if-header">
                <button className="if-back-btn" onClick={onBack} aria-label="חזור">
                    ← חזור
                </button>
                <div className="if-header-logo">SiteNest ✦</div>
            </div>

            <div className="if-wrap">
                {/* Sidebar info */}
                <div className="if-sidebar">
                    <h2 className="if-sidebar-title">
                        ✦ בנה את האתר שלך
                    </h2>
                    <p className="if-sidebar-sub">
                        מלא את הטופס — ה-AI יבנה לך אתר מקצועי תוך שעות ספורות, מבוסס בדיוק על העסק שלך.
                    </p>
                    <div className="if-sidebar-benefits">
                        {[
                            '🤖 AI מנתח ובונה הכל אוטומטית',
                            '📱 האתר מותאם לכל מסך',
                            '✏️ עד 3 תיקונים חינם',
                            '⚡ מוכן ב-24–48 שעות',
                            '🔒 SSL + אחסון מנוהל',
                            '💬 תמיכה אישית בוואטסאפ',
                        ].map((b, i) => (
                            <div key={i} className="if-benefit">{b}</div>
                        ))}
                    </div>
                    <a
                        href={`https://wa.me/${WA}?text=${encodeURIComponent('היי! יש לי שאלה לפני שאני ממלא את הטופס')}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="if-sidebar-wa"
                    >
                        💬 שאלה לפני מילוי? כתוב לנו
                    </a>
                </div>

                {/* Form */}
                <form className="if-form" onSubmit={handleSubmit} noValidate>
                    <h1 className="if-form-title">פרטי העסק שלך</h1>
                    <p className="if-form-subtitle">
                        ככל שתתן יותר פרטים, כך האתר יהיה מדויק ומקצועי יותר
                    </p>

                    {/* ── Business name ── */}
                    <div className="if-field">
                        <label className="if-label" htmlFor="businessName">
                            שם העסק <span className="if-required">*</span>
                        </label>
                        <input
                            id="businessName"
                            className={`if-input ${touched.businessName && errors.businessName ? 'if-input-error' : ''}`}
                            type="text"
                            placeholder='למשל: "מספרת שיק תל אביב"'
                            value={businessName}
                            onChange={e => setBusinessName(e.target.value)}
                            onBlur={() => touch('businessName')}
                            maxLength={255}
                        />
                        {touched.businessName && errors.businessName && (
                            <span className="if-error-msg">{errors.businessName}</span>
                        )}
                    </div>

                    {/* ── Phone ── */}
                    <div className="if-field">
                        <label className="if-label" htmlFor="phone">
                            מספר טלפון (לוואטסאפ) <span className="if-required">*</span>
                        </label>
                        <input
                            id="phone"
                            className={`if-input ${touched.phone && errors.phone ? 'if-input-error' : ''}`}
                            type="tel"
                            placeholder="05X-XXXXXXX"
                            value={phone}
                            onChange={e => setPhone(e.target.value)}
                            onBlur={() => touch('phone')}
                            dir="ltr"
                        />
                        {touched.phone && errors.phone && (
                            <span className="if-error-msg">{errors.phone}</span>
                        )}
                        <span className="if-hint">🔒 מספרך נשמר בבטחה ולא ישותף</span>
                    </div>

                    {/* ── Social divider ── */}
                    <div className="if-divider">
                        <span>רשתות חברתיות (לא חובה)</span>
                    </div>
                    <p className="if-social-note">
                        AI שלנו ישתמש בפרופילים שלך כדי לשלב תכנים, תמונות ומידע אמיתי באתר
                    </p>

                    {/* ── Facebook ── */}
                    <div className="if-field">
                        <label className="if-label" htmlFor="facebook">
                            <span className="if-social-icon">📘</span> פייסבוק
                        </label>
                        <input
                            id="facebook"
                            className={`if-input ${touched.facebook && errors.facebook ? 'if-input-error' : ''}`}
                            type="url"
                            placeholder="https://facebook.com/העמוד-שלך"
                            value={facebook}
                            onChange={e => setFacebook(e.target.value)}
                            onBlur={() => touch('facebook')}
                            dir="ltr"
                        />
                        {touched.facebook && errors.facebook && (
                            <span className="if-error-msg">{errors.facebook}</span>
                        )}
                    </div>

                    {/* ── TikTok ── */}
                    <div className="if-field">
                        <label className="if-label" htmlFor="tiktok">
                            <span className="if-social-icon">🎵</span> טיקטוק
                        </label>
                        <input
                            id="tiktok"
                            className={`if-input ${touched.tiktok && errors.tiktok ? 'if-input-error' : ''}`}
                            type="url"
                            placeholder="https://tiktok.com/@הפרופיל-שלך"
                            value={tiktok}
                            onChange={e => setTiktok(e.target.value)}
                            onBlur={() => touch('tiktok')}
                            dir="ltr"
                        />
                        {touched.tiktok && errors.tiktok && (
                            <span className="if-error-msg">{errors.tiktok}</span>
                        )}
                    </div>

                    {/* ── Instagram ── */}
                    <div className="if-field">
                        <label className="if-label" htmlFor="instagram">
                            <span className="if-social-icon">📸</span> אינסטגרם
                        </label>
                        <input
                            id="instagram"
                            className={`if-input ${touched.instagram && errors.instagram ? 'if-input-error' : ''}`}
                            type="url"
                            placeholder="https://instagram.com/הפרופיל-שלך"
                            value={instagram}
                            onChange={e => setInstagram(e.target.value)}
                            onBlur={() => touch('instagram')}
                            dir="ltr"
                        />
                        {touched.instagram && errors.instagram && (
                            <span className="if-error-msg">{errors.instagram}</span>
                        )}
                    </div>

                    {/* ── Website ── */}
                    <div className="if-field">
                        <label className="if-label" htmlFor="website">
                            <span className="if-social-icon">🌐</span> אתר קיים (אם יש)
                        </label>
                        <input
                            id="website"
                            className={`if-input ${touched.website && errors.website ? 'if-input-error' : ''}`}
                            type="url"
                            placeholder="https://www.האתר-הישן-שלך.co.il"
                            value={website}
                            onChange={e => setWebsite(e.target.value)}
                            onBlur={() => touch('website')}
                            dir="ltr"
                        />
                        {touched.website && errors.website && (
                            <span className="if-error-msg">{errors.website}</span>
                        )}
                    </div>

                    {/* ── Description ── */}
                    <div className="if-field">
                        <label className="if-label" htmlFor="description">
                            ספר לנו על העסק שלך
                        </label>
                        <textarea
                            id="description"
                            className="if-textarea"
                            placeholder="מה אתה עושה? מה הייחוד שלך? מה חשוב שהגולשים ידעו? כמה שיותר פרטים = אתר טוב יותר"
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            rows={5}
                            maxLength={1000}
                        />
                        <span className="if-char-count">{description.length}/1000</span>
                    </div>

                    {/* ── Image upload ── */}
                    <div className="if-divider">
                        <span>תמונות לאתר (לא חובה)</span>
                    </div>

                    <div className="if-field">
                        <label className="if-label">
                            העלה תמונות לאתר שלך (עד {MAX_IMAGES})
                        </label>
                        <p className="if-hint">
                            לוגו, תמונות מהעסק, עבודות. JPG/PNG/WebP עד 5MB לתמונה
                        </p>

                        {/* Previews */}
                        {imagePreviews.length > 0 && (
                            <div className="if-image-grid">
                                {imagePreviews.map((src, i) => (
                                    <div key={i} className="if-image-thumb">
                                        <img src={src} alt={`תמונה ${i + 1}`} />
                                        <button
                                            type="button"
                                            className="if-image-remove"
                                            onClick={() => removeImage(i)}
                                            aria-label="הסר תמונה"
                                        >
                                            ✕
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}

                        {images.length < MAX_IMAGES && (
                            <label className="if-upload-zone">
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept={ACCEPTED}
                                    multiple
                                    onChange={handleImageAdd}
                                    className="if-upload-input"
                                />
                                <div className="if-upload-inner">
                                    <span className="if-upload-icon">📷</span>
                                    <span className="if-upload-text">לחץ להוספת תמונות</span>
                                    <span className="if-upload-sub">או גרור לכאן · {MAX_IMAGES - images.length} נותרו</span>
                                </div>
                            </label>
                        )}
                    </div>

                    {/* ── Error message ── */}
                    {error && (
                        <div className="if-submit-error">
                            ❌ {error}
                        </div>
                    )}

                    {/* ── Submit ── */}
                    <button
                        type="submit"
                        className="if-submit-btn"
                        disabled={submitting}
                    >
                        {submitting ? (
                            <span className="if-spinner" />
                        ) : (
                            '✦ שלח את הפרטים — ה-AI יתחיל לבנות'
                        )}
                    </button>

                    <p className="if-submit-note">
                        לאחר השליחה תקבל קישור לעקוב אחרי ההתקדמות ולבקש שינויים
                    </p>
                </form>
            </div>
        </div>
    );
}
