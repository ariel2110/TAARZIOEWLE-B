import { useCallback, useEffect, useRef, useState } from 'react';

const API = import.meta.env.VITE_API_BASE || 'https://api.sitenest.site/api/v1';
const WHATSAPP_NUMBER = import.meta.env.VITE_WA_NUMBER || '972546363350';
const SCARCITY_MINUTES = 15;

// ── Types ─────────────────────────────────────────────────────────────────────
interface Prediction {
    place_id: string;
    description: string;
    structured_formatting: { main_text: string; secondary_text: string };
}

interface TaskStatus {
    task_id: string;
    state: string;
    step: string | null;
    label: string | null;
    percent: number | null;
    preview_url: string | null;
    public_url: string | null;
    error: string | null;
}

// ── Progress labels (shown in sequence while task runs) ───────────────────────
const PROGRESS_STEPS = [
    { percent: 8, label: 'שואב דירוגים וביקורות מגוגל מפות...' },
    { percent: 22, label: 'מאתר חשבון אינסטגרם וטיקטוק שלך...' },
    { percent: 38, label: 'מנתח שירותים מובילים מתוך איזי...' },
    { percent: 52, label: 'ה-AI מנתח ומבין את העסק שלך...' },
    { percent: 66, label: 'מעצב לפי צבעי המותג שלך...' },
    { percent: 80, label: 'קלוד בונה את האתר שלך...' },
    { percent: 94, label: 'מגמר פרטים אחרונים...' },
];

// ── Countdown hook ────────────────────────────────────────────────────────────
function useCountdown(minutes: number) {
    const [secs, setSecs] = useState(minutes * 60);
    useEffect(() => {
        if (secs <= 0) return;
        const t = setTimeout(() => setSecs(s => s - 1), 1000);
        return () => clearTimeout(t);
    }, [secs]);
    const mm = String(Math.floor(secs / 60)).padStart(2, '0');
    const ss = String(secs % 60).padStart(2, '0');
    return { display: `${mm}:${ss}`, expired: secs <= 0 };
}

// ── Main component ────────────────────────────────────────────────────────────
export default function MagicPortal() {
    // Search
    const [query, setQuery] = useState('');
    const [predictions, setPredictions] = useState<Prediction[]>([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [sessionToken] = useState(() => crypto.randomUUID());
    const acTimer = useRef<ReturnType<typeof setTimeout>>();

    // Build state
    const [phase, setPhase] = useState<'search' | 'building' | 'phone_wall' | 'done' | 'error'>('search');
    const [taskId, setTaskId] = useState<string>('');
    const [businessId, setBusinessId] = useState<number>(0);
    const [businessName, setBusinessName] = useState<string>('');
    const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
    const [displayStep, setDisplayStep] = useState(0); // index into PROGRESS_STEPS
    const pollRef = useRef<ReturnType<typeof setInterval>>();
    const stepAdvTimer = useRef<ReturnType<typeof setInterval>>();

    // Phone wall
    const [phone, setPhone] = useState('');
    const [phoneSaved, setPhoneSaved] = useState(false);
    const [showWall, setShowWall] = useState(false);

    // Demo
    const [previewUrl, setPreviewUrl] = useState<string>('');
    const [publicUrl, setPublicUrl] = useState<string>('');

    const { display: countdown, expired: countdownExpired } = useCountdown(SCARCITY_MINUTES);

    // ── Autocomplete ────────────────────────────────────────────────────────────
    const fetchPredictions = useCallback(async (text: string) => {
        if (text.length < 2) { setPredictions([]); return; }
        try {
            const r = await fetch(`${API}/public/places-autocomplete?input=${encodeURIComponent(text)}&session_token=${sessionToken}`);
            const data = await r.json();
            setPredictions(data.predictions || []);
            setShowDropdown(true);
        } catch { setPredictions([]); }
    }, [sessionToken]);

    function handleQueryChange(e: React.ChangeEvent<HTMLInputElement>) {
        const v = e.target.value;
        setQuery(v);
        clearTimeout(acTimer.current);
        acTimer.current = setTimeout(() => fetchPredictions(v), 320);
    }

    // ── Select prediction ────────────────────────────────────────────────────────
    async function handleSelect(p: Prediction) {
        setShowDropdown(false);
        setQuery(p.structured_formatting?.main_text || p.description);
        setBusinessName(p.structured_formatting?.main_text || p.description);
        setPhase('building');
        setDisplayStep(0);
        startStepAdvancer();

        // Show phone wall automatically after 40 seconds
        setTimeout(() => setShowWall(true), 40_000);

        try {
            const r = await fetch(`${API}/public/build-instant`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ place_id: p.place_id, business_name: p.description }),
            });
            const data = await r.json();
            if (data.task_id) {
                setTaskId(data.task_id);
                setBusinessId(data.business_id);
                startPolling(data.task_id);
            } else {
                setPhase('error');
            }
        } catch {
            setPhase('error');
        }
    }

    // ── Step advancer (frontend animation) ──────────────────────────────────────
    function startStepAdvancer() {
        clearInterval(stepAdvTimer.current);
        setDisplayStep(0);
        let idx = 0;
        stepAdvTimer.current = setInterval(() => {
            idx = Math.min(idx + 1, PROGRESS_STEPS.length - 1);
            setDisplayStep(idx);
        }, 28_000);
    }

    // ── Polling ──────────────────────────────────────────────────────────────────
    function startPolling(tid: string) {
        clearInterval(pollRef.current);
        pollRef.current = setInterval(async () => {
            try {
                const r = await fetch(`${API}/public/task-status/${tid}`);
                const status: TaskStatus = await r.json();
                setTaskStatus(status);

                if (status.step === 'scouted') setShowWall(true);

                if (status.state === 'SUCCESS' && status.preview_url) {
                    clearInterval(pollRef.current);
                    clearInterval(stepAdvTimer.current);
                    setPreviewUrl(status.preview_url);
                    setPublicUrl(status.public_url || '');
                    setDisplayStep(PROGRESS_STEPS.length - 1);
                    setTimeout(() => setPhase('done'), 1200);
                } else if (status.state === 'FAILURE') {
                    clearInterval(pollRef.current);
                    setPhase('error');
                }
            } catch { /* network blip — keep polling */ }
        }, 3_000);
    }

    useEffect(() => () => {
        clearInterval(pollRef.current);
        clearInterval(stepAdvTimer.current);
    }, []);

    // ── Save phone ───────────────────────────────────────────────────────────────
    async function handlePhoneSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!phone.match(/^0\d{9}$|^972\d{9}$/)) return;
        try {
            await fetch(`${API}/public/capture-phone`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ business_id: businessId, phone }),
            });
            setPhoneSaved(true);
            setShowWall(false);
        } catch { setPhoneSaved(true); setShowWall(false); }
    }

    // ── WA upgrade link ──────────────────────────────────────────────────────────
    const waMessage = encodeURIComponent(`היי! ראיתי את הדמו של ${businessName} ואני רוצה להעביר את האתר לדומיין שלי 🚀`);
    const waLink = `https://wa.me/${WHATSAPP_NUMBER}?text=${waMessage}`;

    const currentStep = PROGRESS_STEPS[displayStep];
    const displayPercent = taskStatus?.percent ?? currentStep.percent;
    const displayLabel = taskStatus?.label ?? currentStep.label;

    // ── Estimated time remaining ─────────────────────────────────────────────────
    function estimatedTimeLabel() {
        const pct = displayPercent || 0;
        if (pct < 20) return '~4 דקות';
        if (pct < 50) return '~2.5 דקות';
        if (pct < 70) return '~1.5 דקות';
        if (pct < 90) return '~30 שניות';
        return 'כמה שניות...';
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Render
    // ═══════════════════════════════════════════════════════════════════════════
    return (
        <div className="mp-root">
            {/* ── Scarcity bar (always visible once building starts) ── */}
            {phase !== 'search' && (
                <div className={`mp-scarcity-bar ${countdownExpired ? 'expired' : ''}`}>
                    🔥&nbsp;
                    {countdownExpired
                        ? 'ההצעה פגה! בנה עכשיו ותקבל אחוזים מהירות'
                        : `ההצעה לבניית האתר בחינם פגה בעוד ${countdown} דקות`}
                </div>
            )}

            {/* ══════════════════════════════════════════════════════ SEARCH ══ */}
            {phase === 'search' && (
                <div className="mp-search-page">
                    {/* Top nav */}
                    <nav className="mp-topnav">
                        <span className="mp-topnav-logo">SiteNest ✦</span>
                        <a href="https://admin.sitenest.site" className="mp-topnav-login">
                            <span className="mp-topnav-login-icon">👤</span>
                            כניסה לניהול
                        </a>
                    </nav>
                    <div className="mp-hero">
                        <h1 className="mp-headline">
                            תוך 3 דקות<br />
                            <span className="mp-accent">הפכנו את הידע שלך לאתר מקצועי</span>
                        </h1>
                        <p className="mp-subheadline">
                            הקלד את שם העסק שלך — ה-AI יבנה לך אתר חינם, מבוסס על הביקורות, הרשתות החברתיות והזהות שלך
                        </p>
                        <div className="mp-search-wrap" style={{ position: 'relative' }}>
                            <div className="mp-search-box">
                                <span className="mp-search-icon">🔍</span>
                                <input
                                    className="mp-search-input"
                                    type="text"
                                    placeholder="שם העסק שלך, למשל: מספרת שיק תל אביב"
                                    value={query}
                                    onChange={handleQueryChange}
                                    onFocus={() => predictions.length > 0 && setShowDropdown(true)}
                                    autoComplete="off"
                                />
                            </div>
                            {showDropdown && predictions.length > 0 && (
                                <ul className="mp-dropdown">
                                    {predictions.map(p => (
                                        <li key={p.place_id} className="mp-dropdown-item" onClick={() => handleSelect(p)}>
                                            <span className="mp-di-main">{p.structured_formatting?.main_text || p.description}</span>
                                            <span className="mp-di-sub">{p.structured_formatting?.secondary_text || ''}</span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                        <div className="mp-pills">
                            <span className="mp-pill">📍 Google מפות</span>
                            <span className="mp-pill">📸 אינסטגרם</span>
                            <span className="mp-pill">🎵 טיקטוק</span>
                            <span className="mp-pill">⭐ ביקורות אמיתיות</span>
                            <span className="mp-pill">⚡ Claude AI</span>
                        </div>
                        <div className="mp-how">
                            <div className="mp-how-step"><span className="mp-how-num">1</span><span>בחר עסק</span></div>
                            <div className="mp-how-arrow">→</div>
                            <div className="mp-how-step"><span className="mp-how-num">2</span><span>ה-AI עובד</span></div>
                            <div className="mp-how-arrow">→</div>
                            <div className="mp-how-step"><span className="mp-how-num">3</span><span>ראה את האתר</span></div>
                            <div className="mp-how-arrow">→</div>
                            <div className="mp-how-step"><span className="mp-how-num">4</span><span>קנה דומיין</span></div>
                        </div>
                    </div>
                </div>
            )}

            {/* ══════════════════════════════════════════════════════ BUILDING ══ */}
            {phase === 'building' && (
                <div className="mp-building-page">
                    {/* Exit button */}
                    <button
                        className="mp-exit-btn"
                        onClick={() => { setPhase('search'); setQuery(''); clearInterval(pollRef.current); clearInterval(stepAdvTimer.current); }}
                        title="חזור לחיפוש"
                    >
                        ✕ חזור
                    </button>
                    <div className="mp-factory">
                        <div className="mp-factory-header">
                            <div className="mp-spinner" />
                            <div>
                                <div className="mp-factory-title">בונה את האתר של</div>
                                <div className="mp-factory-biz">{businessName}</div>
                            </div>
                        </div>

                        <div className="mp-progress-track">
                            <div className="mp-progress-bar" style={{ width: `${displayPercent}%` }} />
                        </div>
                        <div className="mp-progress-pct">{displayPercent}%&nbsp;&nbsp;·&nbsp;&nbsp;נותר: {estimatedTimeLabel()}</div>
                        <div className="mp-progress-label">✦ {displayLabel}</div>

                        <div className="mp-steps-list">
                            {PROGRESS_STEPS.map((s, i) => (
                                <div key={i} className={`mp-step-row ${i <= displayStep ? 'done' : ''} ${i === displayStep ? 'active' : ''}`}>
                                    <span className="mp-step-dot">{i < displayStep ? '✓' : i === displayStep ? '◉' : '○'}</span>
                                    <span>{s.label}</span>
                                </div>
                            ))}
                        </div>

                        <div className="mp-factory-note">
                            ⏱ תהליך זה לוקח בדרך כלל 3–5 דקות. לא נורא — זה שווה את זה.
                        </div>
                    </div>

                    {/* Phone wall overlay */}
                    {showWall && !phoneSaved && (
                        <div className="mp-wall-overlay">
                            <div className="mp-wall-card">
                                <div className="mp-wall-icon">📲</div>
                                <h2 className="mp-wall-title">מצאנו את כל החומרים!</h2>
                                <p className="mp-wall-sub">
                                    לאן לשלוח לך את הלינק לאתר כשהוא יהיה מוכן?<br />
                                    <strong>נשאר {countdown} לפני שהמבצע נסגר</strong>
                                </p>
                                <form className="mp-wall-form" onSubmit={handlePhoneSubmit}>
                                    <input
                                        className="mp-wall-input"
                                        type="tel"
                                        placeholder="מספר וואטסאפ (05X-XXXXXXX)"
                                        value={phone}
                                        onChange={e => setPhone(e.target.value)}
                                        required
                                        pattern="^0\d{9}$|^972\d{9}$"
                                    />
                                    <button className="mp-wall-btn" type="submit">
                                        שלח לי את האתר ✦
                                    </button>
                                </form>
                                <p className="mp-wall-privacy">🔒 לא נשתמש במספר שלך לשום דבר אחר</p>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ══════════════════════════════════════════════════════ DONE ══ */}
            {phase === 'done' && (
                <div className="mp-done-page">
                    {/* Sticky gold bar */}
                    <div className="mp-sticky-bar">
                        <div className="mp-sticky-left">
                            🌟&nbsp;<strong>זה האתר שלך — {businessName}</strong>
                            &nbsp;·&nbsp; מוכן לעלות לאוויר!
                        </div>
                        <div className="mp-sticky-actions">
                            <a href={waLink} target="_blank" rel="noopener noreferrer" className="mp-btn-gold">
                                ✦ אני רוצה את האתר הזה!
                            </a>
                            <a
                                href={`https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent('היי, ראיתי את האתר שנבנה לעסק שלי ואשמח לדבר!')}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="mp-btn-outline"
                                style={{ display: 'inline-block', textDecoration: 'none', textAlign: 'center' }}
                            >
                                💬 דברו איתנו בוואטסאפ
                            </a>
                            <button
                                className="mp-btn-restart"
                                onClick={() => { setPhase('search'); setQuery(''); setPreviewUrl(''); setPublicUrl(''); setPhoneSaved(false); }}
                                title="בנה אתר לעסק אחר"
                            >
                                🔄 עסק אחר
                            </button>
                        </div>
                    </div>

                    {/* Demo iframe (gated if no phone) */}
                    {phoneSaved || true /* show demo regardless */ ? (
                        <iframe
                            className="mp-iframe"
                            src={publicUrl || `https://api.sitenest.site${previewUrl}`}
                            title={`אתר הדמו — ${businessName}`}
                            sandbox="allow-same-origin allow-scripts"
                        />
                    ) : (
                        <div className="mp-gate">
                            <div className="mp-wall-card">
                                <div className="mp-wall-icon">🎉</div>
                                <h2 className="mp-wall-title">האתר מוכן!</h2>
                                <p className="mp-wall-sub">השאר טלפון כדי לראות את האתר</p>
                                <form className="mp-wall-form" onSubmit={handlePhoneSubmit}>
                                    <input
                                        className="mp-wall-input"
                                        type="tel"
                                        placeholder="מספר וואטסאפ"
                                        value={phone}
                                        onChange={e => setPhone(e.target.value)}
                                        required
                                    />
                                    <button className="mp-wall-btn" type="submit">הצג לי את האתר ✦</button>
                                </form>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ══════════════════════════════════════════════════════ ERROR ══ */}
            {phase === 'error' && (
                <div className="mp-search-page">
                    <div className="mp-hero">
                        <div className="mp-logo">SiteNest ✦</div>
                        <div className="mp-error-card">
                            <div style={{ fontSize: 48 }}>😕</div>
                            <h2>משהו השתבש</h2>
                            <p>לא הצלחנו לבנות את האתר הפעם. נסה שוב עם עסק אחר.</p>
                            <button className="mp-wall-btn" onClick={() => { setPhase('search'); setQuery(''); }}>
                                נסה שוב
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
