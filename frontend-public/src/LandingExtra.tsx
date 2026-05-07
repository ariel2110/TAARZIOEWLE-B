import { useState } from 'react';

interface Props {
    onStartIntake: (planName?: string) => void;
}

const FEATURES = [
    { icon: '🌐', title: 'אתר מקצועי מלא', desc: 'עמוד ראשי, שירותים, גלריה, ביקורות, צור קשר — הכל מוכן לפרסום' },
    { icon: '📱', title: 'מותאם למובייל 100%', desc: 'האתר נראה מושלם בטלפון, טאבלט ומחשב — ללא עלות נוספת' },
    { icon: '🤖', title: 'בנוי על ידי AI', desc: 'Claude AI מנתח את העסק שלך ומייצר תוכן ממוקד ומשכנע' },
    { icon: '⭐', title: 'ביקורות גוגל מוטמעות', desc: 'הביקורות האמיתיות שלך מגוגל מוצגות ישירות באתר' },
    { icon: '📸', title: 'תכנים מהרשתות החברתיות', desc: 'AI מאתר ומשלב את הפוסטים, הסרטונים והתמונות מהאינסטגרם והטיקטוק שלך' },
    { icon: '🔒', title: 'תעודת SSL ואבטחה מלאה', desc: 'HTTPS מוגן, פרטיות הגולשים מובטחת, ציון SEO מלא' },
    { icon: '✏️', title: 'עד 3 תיקונים חינם', desc: 'לא מרוצה ממשהו? מותר לבקש שינויים — עד 3 פעמים ללא עלות' },
    { icon: '📞', title: 'תמיכה אישית בוואטסאפ', desc: 'יש שאלה? אנחנו זמינים. שלח הודעה ונחזור אליך תוך שעה' },
];

const PLANS = [
    {
        name: 'Starter',
        nameHe: 'מתחיל',
        price: '₪299',
        period: '/חודש',
        annual: 'או ₪249/חודש בתשלום שנתי',
        color: '#6366f1',
        recommended: false,
        features: [
            'אתר אחד מקצועי',
            'דומיין בחירתך (xxx.tazo-web.com)',
            'SSL + אחסון מנוהל',
            '2 תיקונים לחודש',
            'תמיכה בוואטסאפ',
            'עדכון תכנים פעם בחודש',
        ],
        cta: 'בחר תוכנית →',
        ctaAction: 'intake' as const,
    },
    {
        name: 'Growth',
        nameHe: 'צמיחה',
        price: '₪699',
        period: '/חודש',
        annual: 'או ₪559/חודש בתשלום שנתי',
        color: '#f59e0b',
        recommended: true,
        features: [
            'הכל ב-Starter +',
            'דומיין עצמאי שלך',
            'עדכון תכנים שבועי',
            'דוח ביצועים חודשי',
            'AI צ\'אט-בוט לקוחות',
            'קישורי מדיה חברתית',
            'עדיפות בתמיכה',
        ],
        cta: 'הכי פופולרי ✦',
        ctaAction: 'intake' as const,
    },
    {
        name: 'Pro',
        nameHe: 'מקצועי',
        price: '₪1,299',
        period: '/חודש',
        annual: 'או ₪999/חודש בתשלום שנתי',
        color: '#10b981',
        recommended: false,
        features: [
            'הכל ב-Growth +',
            'עמודי נחיתה ממוקדים',
            'קמפיין גוגל/פייסבוק ראשוני',
            'ניהול חשבון מדיה חברתית',
            'SEO מורחב + בלוג',
            'CRM בסיסי + כפתור הזמנה',
            'מנהל חשבון אישי',
        ],
        cta: 'צור קשר לפרטים →',
        ctaAction: 'whatsapp' as const,
    },
];

const FAQS = [
    {
        q: 'כמה זמן לוקח לבנות את האתר שלי?',
        a: 'תמלא טופס קצר → ה-AI בונה את האתר תוך 3–5 דקות → תראה דמו ותאשר → תקבל קישור תשלום והאתר עולה לאוויר. האתר הסופי מוכן תוך 24–48 שעות לאחר האישור.',
    },
    {
        q: 'מה קורה אחרי שאני רואה ומאשר את הדמו?',
        a: 'לאחר שתאשר את הדמו תקבל קישור תשלום — תבחר דומיין, תשלם, והאתר עולה לאוויר. אפשר לבקש עד 3 תיקונים חינם לפני התשלום.',
    },
    {
        q: 'מה ההבדל בין AI בלבד (39 ₪) לתוכניות עם ליווי?',
        a: 'תוכנית ה-AI בלבד (39 ₪/חודש) בונה לך אתר אוטומטית — ללא ליווי אנושי. התוכניות הכוללות ליווי (מתחיל 299₪, צמיחה 699₪) כוללות תמיכה צמודה של צוות אנושי לאורך כל הדרך: מהבנייה, דרך השינויים, ועד שהאתר עולה לאוויר בזמן הקצוב.',
    },
    {
        q: 'מה אני מקבל בתוכנית ה-Starter?',
        a: 'אתר מקצועי מלא הכולל: עמוד ראשי, שירותים, גלריה, ביקורות גוגל, צור קשר, כפתורי וואטסאפ ואינסטגרם. אחסון ו-SSL ללא הגבלה. 2 תיקונים חינם לחודש. בניגוד ל-AI בלבד — כוללת ליווי אנושי צמוד לכל אורך הדרך.',
    },
    {
        q: 'האם אני צריך ידע טכני?',
        a: 'אפס! תמלא טופס עם שם העסק, מספר טלפון וקישורי הרשתות החברתיות שלך — ה-AI עושה הכל. אין ניסיון נדרש.',
    },
    {
        q: 'האם יש חוזה מינימום?',
        a: 'לא! אפשר לבטל בכל עת. אם אתה משלם מראש שנתית אתה חוסך 20% ומקבל שניים חודשים חינם.',
    },
    {
        q: 'מה זה "עד 3 תיקונים"?',
        a: 'לאחר שה-AI יבנה את האתר, תוכל לבקש עד 3 שינויים חינם (צבעים, טקסטים, תמונות, סדר עמודים). תיקונים נוספים מחושבים לפי שעה.',
    },
    {
        q: 'האם ניתן לקבל דומיין עצמאי כמו www.haircutbymiri.co.il?',
        a: 'כן! בתוכנית Growth ומעלה אנחנו מחברים את הדומיין שלך (או רוכשים עבורך) ומגדירים הכל אוטומטית.',
    },
    {
        q: 'מה קורה לאתר שלי אם אני מבטל?',
        a: 'האתר ייפסל ב-14 ימים לאחר סיום המנוי. נשלח לך תמיד הודעה מראש. ניתן לייצא את תכני האתר לפני הסגירה.',
    },
    {
        q: 'האם ניתן לעדכן את האתר לבד?',
        a: 'בתוכנית Growth ומעלה תקבל לוח ניהול פשוט לעדכון טקסטים ותמונות. מבצעים ועדכונים עונתיים — אנחנו מטפלים.',
    },
    {
        q: 'אני עסק קטן מאוד, זה מתאים לי?',
        a: 'בדיוק לזה בנינו את tazo-web. אנחנו עובדים עם מספרות, מסעדות, מאפיות, קלינאים, מורים פרטיים ועוד — כולם עסקים קטנים שמקבלים אתר מקצועי שנראה כמו של חברה גדולה.',
    },
    {
        q: 'מה אם אני לא מרוצה מהתוצאה?',
        a: 'אנחנו מציעים החזר כספי מלא תוך 7 ימים ראשונים, ללא שאלות. בנוסף לכך — 3 תיקונים חינם מובטחים עד שתהיה מרוצה.',
    },
];

export default function LandingExtra({ onStartIntake }: Props) {
    const [openFaq, setOpenFaq] = useState<number | null>(null);

    return (
        <div className="le-root">
            {/* ── Scroll anchor ── */}
            <div id="landing-extra" />

            {/* ══════════════════════════ WHAT YOU GET ══════════════════════════ */}
            <section className="le-section le-features-section">
                <div className="le-container">
                    <div className="le-section-badge">✦ מה כלול</div>
                    <h2 className="le-heading">אתר אחד שעושה הכל</h2>
                    <p className="le-subheading">
                        כל לקוח מקבל אתר מקצועי מלא — לא תבנית, לא דמו. אתר עובד, מוכן לגוגל, מוכן ללקוחות שלך.
                    </p>
                    <div className="le-features-grid">
                        {FEATURES.map((f, i) => (
                            <div key={i} className="le-feature-card">
                                <span className="le-feature-icon">{f.icon}</span>
                                <h3 className="le-feature-title">{f.title}</h3>
                                <p className="le-feature-desc">{f.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ══════════════════════════ PRICING ══════════════════════════════ */}
            <section className="le-section le-pricing-section">
                <div className="le-container">
                    <div className="le-section-badge">✦ מחירים</div>
                    <h2 className="le-heading">תוכניות שמתאימות לכל עסק</h2>
                    <p className="le-subheading">ללא חוזים. ללא הפתעות. ביטול בכל עת.</p>
                    <div className="le-plans-grid">
                        {PLANS.map((plan) => (
                            <div
                                key={plan.name}
                                className={`le-plan-card ${plan.recommended ? 'le-plan-recommended' : ''}`}
                                style={{ '--plan-color': plan.color } as React.CSSProperties}
                            >
                                {plan.recommended && (
                                    <div className="le-plan-badge">⭐ הכי פופולרי</div>
                                )}
                                <div className="le-plan-header">
                                    <div className="le-plan-name">{plan.nameHe}</div>
                                    <div className="le-plan-name-en">{plan.name}</div>
                                    <div className="le-plan-price">
                                        {plan.price}<span className="le-plan-period">{plan.period}</span>
                                    </div>
                                    <div className="le-plan-annual">{plan.annual}</div>
                                </div>
                                <ul className="le-plan-features">
                                    {plan.features.map((f, i) => (
                                        <li key={i}>
                                            <span className="le-plan-check">✓</span>
                                            {f}
                                        </li>
                                    ))}
                                </ul>
                                {plan.ctaAction === 'whatsapp' ? (
                                    <a
                                        className="le-plan-btn"
                                        href={`https://wa.me/972546363350?text=${encodeURIComponent('היי! אני מעוניין בתוכנית ה-Pro של tazo-web. אשמח לשמוע פרטים.')}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        {plan.cta}
                                    </a>
                                ) : (
                                    <button
                                        className="le-plan-btn"
                                        onClick={() => onStartIntake(plan.nameHe)}
                                    >
                                        {plan.cta}
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                    <p className="le-pricing-note">
                        💡 כל התוכניות כוללות ניסיון חינם של 7 ימים. לא צריך כרטיס אשראי להתחיל.
                    </p>
                </div>
            </section>

            {/* ══════════════════════════ HOW IT WORKS ═════════════════════════ */}
            <section className="le-section le-how-section">
                <div className="le-container">
                    <div className="le-section-badge">✦ איך זה עובד</div>
                    <h2 className="le-heading">מ-0 לאתר חי — ב-4 צעדים</h2>
                    <div className="le-steps">
                        {[
                            { n: '1', icon: '📝', title: 'מלא טופס קצר', desc: 'שם העסק, תחום, טלפון וקישורי הרשתות החברתיות שלך' },
                            { n: '2', icon: '🤖', title: 'ה-AI עובד', desc: 'Claude AI בונה אתר מותאם אישית בהתבסס על כל המידע שאסף על העסק שלך' },
                            { n: '3', icon: '👀', title: 'בדוק ואשר', desc: 'קבל לינק לדמו, בדוק, בקש שינויים (עד 3 חינם) ואשר' },
                            { n: '4', icon: '🚀', title: 'פרסם לאוויר', desc: 'האתר עולה עם הדומיין שלך, SSL, ומוכן לגוגל' },
                        ].map((s) => (
                            <div key={s.n} className="le-step">
                                <div className="le-step-num">{s.icon}</div>
                                <div className="le-step-title">{s.title}</div>
                                <div className="le-step-desc">{s.desc}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ══════════════════════════ FAQ ══════════════════════════════════ */}
            <section className="le-section le-faq-section">
                <div className="le-container le-container-narrow">
                    <div className="le-section-badge">✦ שאלות נפוצות</div>
                    <h2 className="le-heading">יש לך שאלה? יש לנו תשובה</h2>
                    <div className="le-faq-list">
                        {FAQS.map((faq, i) => (
                            <div
                                key={i}
                                className={`le-faq-item ${openFaq === i ? 'open' : ''}`}
                            >
                                <button
                                    className="le-faq-question"
                                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                                    aria-expanded={openFaq === i}
                                >
                                    <span>{faq.q}</span>
                                    <span className="le-faq-arrow">{openFaq === i ? '▲' : '▼'}</span>
                                </button>
                                {openFaq === i && (
                                    <div className="le-faq-answer">{faq.a}</div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ══════════════════════════ CTA BOTTOM ═══════════════════════════ */}
            <section className="le-section le-cta-section">
                <div className="le-container le-cta-content">
                    <h2 className="le-cta-heading">מוכן לקבל אתר מקצועי?</h2>
                    <p className="le-cta-sub">
                        מלא טופס קצר עם פרטי העסק שלך — ה-AI יבנה לך אתר תוך דקות.
                    </p>
                    <div className="le-cta-buttons">
                        <button className="le-cta-btn-primary" onClick={() => onStartIntake()}>
                            ✦ בנה את האתר שלי עכשיו
                        </button>
                        <a
                            href={`https://wa.me/972546363350?text=${encodeURIComponent('היי! אני רוצה לשמוע עוד על בניית אתר עם tazo-web')}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="le-cta-btn-wa"
                        >
                            💬 שאלות? כתוב לנו
                        </a>
                    </div>
                    <p className="le-cta-guarantee">
                        ✅ 7 ימי ניסיון חינם &nbsp;·&nbsp; ✅ ללא כרטיס אשראי &nbsp;·&nbsp; ✅ ביטול בכל עת
                    </p>
                </div>
            </section>

            {/* ══════════════════════════ FOOTER ═══════════════════════════════ */}
            <footer className="le-footer">
                <div className="le-container">
                    <div className="le-footer-logo">tazo-web ✦</div>
                    <p className="le-footer-tagline">בניית אתרים מבוססת AI לעסקים קטנים</p>
                    <div className="le-footer-links">
                        <a href="https://admin.tazo-web.com" target="_blank" rel="noopener noreferrer">כניסה למנהל</a>
                        <span>·</span>
                        <a href={`https://wa.me/972546363350`} target="_blank" rel="noopener noreferrer">וואטסאפ</a>
                        <span>·</span>
                        <a href="mailto:admin@tazo-web.com">מייל</a>
                    </div>
                    <p className="le-footer-copy">© 2026 tazo-web. כל הזכויות שמורות.</p>
                </div>
            </footer>
        </div>
    );
}
