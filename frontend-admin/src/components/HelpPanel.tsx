import React, { useState } from 'react';

/* ─── Types ─────────────────────────────────────────────────── */
type Tab = 'workflow' | 'pricing' | 'faq';

/* ─── Content ────────────────────────────────────────────────── */

const WORKFLOW_STEPS_OUTBOUND = [
    {
        phase: 'שלב 1 — איסוף לידים',
        icon: '🔍',
        color: '#3b82f6',
        steps: [
            { who: 'מנהל', action: 'כנס ל"איסוף נתונים" → הכנס עיר + קטגוריה (למשל: "תל אביב, ספרות")' },
            { who: 'מערכת', action: 'Google Places API + Serper מחפשים עסקים ומחזירים רשימה עם ביקורות, טלפון ומיקום' },
            { who: 'מנהל', action: 'בחר עסקים רלוונטיים → לחץ "ייבא לרשימת לידים"' },
        ],
    },
    {
        phase: 'שלב 2 — כישור ובניית דמו',
        icon: '🤖',
        color: '#8b5cf6',
        steps: [
            { who: 'מנהל', action: 'כנס ל"לידים" → לחץ "כשר" → העסק עובר לעמוד "עסקים"' },
            { who: 'מנהל', action: 'בעמוד "עסקים" לחץ "בנה אתר" → הצינור מופעל' },
            { who: 'AI Pipeline', action: 'Grok כותב תוכן שיווקי → Claude בונה HTML → אתר עולה ב-tazo-web.com' },
            { who: 'מנהל', action: 'כנס ל"אתרי דמו" → אשר ושלח קישור ל-WhatsApp של הלקוח' },
        ],
    },
    {
        phase: 'שלב 3 — תשלום (לידים יוצאים)',
        icon: '💳',
        color: '#ef4444',
        steps: [
            { who: 'מנהל', action: 'לקוח מעוניין? כנס ל"תשלומים" → שלח קישור Morning המתאים לתוכנית' },
            { who: 'לקוח', action: 'משלם ב-Morning → מערכת מקבלת Webhook ומשדרגת סטטוס' },
            { who: 'מערכת', action: 'Starter/Growth/Pro → ♻ הודעת WhatsApp נשלחת לך אוטומטית עם משימות לטיפול' },
        ],
    },
];

const WORKFLOW_STEPS_INBOUND = [
    {
        phase: 'שלב 1 — הגשת טופס (tazo-web.com)',
        icon: '📋',
        color: '#10b981',
        steps: [
            { who: 'לקוח', action: 'נכנס ל-tazo-web.com → מזין שם עסק, טלפון, תיאור, קישורי סושיאל' },
            { who: 'מערכת', action: 'שומרת בקשה + מריצה את צינור ה-AI בברקע (עד 3 דקות)' },
            { who: 'לקוח', action: 'מקבל token — יכול לעקוב אחרי הסטטוס בזמן אמת' },
        ],
    },
    {
        phase: 'שלב 2 — AI בונה + מנהל מאשר',
        icon: '🤖',
        color: '#8b5cf6',
        steps: [
            { who: 'AI Pipeline', action: 'Grok + Claude + Gemini בונים HTML מלא + הודעת שיווק ב-WhatsApp' },
            { who: 'מנהל', action: 'מקבל WhatsApp עם הודעה מוצעת + קישור לאישור/עריכה/דחייה' },
            { who: 'מנהל', action: 'אחרי אישור — ההודעה נשלחת לעסק עם קישור לתצוגה מקדימה' },
        ],
    },
    {
        phase: 'שלב 3 — בחירת דומיין',
        icon: '🌐',
        color: '#f59e0b',
        steps: [
            { who: 'לקוח', action: 'רואה דמו ומחליט לקנות → בוחר שם לדומיין (xxx.tazo-web.com)' },
            { who: 'מערכת', action: 'מאמתת שהדומיין חוקי ולא בשימוש (Hostinger API)' },
        ],
    },
    {
        phase: '💳 שלב 4 — תשלום (כאן הלקוח משלם!)',
        icon: '💳',
        color: '#ef4444',
        steps: [
            { who: 'לקוח', action: 'לוחץ "לתשלום" → מועבר לדף Morning עם 39 ₪/חודש' },
            { who: 'לקוח', action: '✅ משלם בכרטיס אשראי — Morning שולח Webhook בזמן אמת' },
            { who: 'מערכת', action: 'מזהה תשלום → מפעילה את finalize_deployment_task בסלרי' },
        ],
    },
    {
        phase: 'שלב 5 — הפעלה אוטומטית מלאה',
        icon: '🚀',
        color: '#06b6d4',
        steps: [
            { who: 'מערכת', action: 'רוכשת דומיין דרך Hostinger API + מגדירה DNS + מפרסת HTML' },
            { who: 'מערכת', action: 'יוצרת nginx vhost + מנפיקה SSL דרך Certbot — אתר פעיל' },
            { who: 'לקוח', action: 'מקבל WhatsApp: "🎉 האתר שלך כבר באוויר! https://[דומיין].tazo-web.com"' },
        ],
    },
];

const CUSTOMER_PLANS = [
    {
        name: 'Auto',
        icon: '⚡',
        price: '₪39',
        period: '/חודש',
        color: '#10b981',
        tag: 'הכי מהיר',
        features: [
            'אתר אחד — מופעל אוטומטית',
            'דומיין xxx.tazo-web.com',
            'SSL + אחסון מנוהל',
            'AI בנייה מלאה (ללא מגע ידיים)',
            'הפעלה תוך ~5 דקות מהתשלום',
        ],
        paid_flow: 'אוטומטי לחלוטין — Webhook מפעיל Celery task, Hostinger קונה דומיין, nginx עולה, לקוח מקבל WhatsApp.',
        admin_actions: [],
        recommended: false,
    },
    {
        name: 'Starter',
        icon: '🌱',
        price: '₪299',
        period: '/חודש',
        color: '#3b82f6',
        tag: 'הכי פופולרי',
        features: [
            'אתר אחד מקצועי',
            'דומיין בחירתך (xxx.tazo-web.com)',
            'SSL + אחסון מנוהל',
            '2 תיקונים לחודש',
            'תמיכה בוואטסאפ',
            'עדכון תכנים פעם בחודש',
        ],
        paid_flow: 'Morning שולח Webhook → נוצר רשומת pro_lead → מגיעה אליך הודעת WhatsApp עם פרטי הלקוח.',
        admin_actions: [
            '📞 צור קשר עם הלקוח תוך שעה',
            '🌐 הגדר לו תת-דומיין ב-tazo-web.com',
            '🤖 הפעל את צינור ה-AI ב"עסקים" → "בנה אתר"',
            '✅ אשר את האתר ושלח קישור פעיל',
            '📅 תזמן 2 תיקונים לחודש בלוח השנה',
        ],
        recommended: true,
    },
    {
        name: 'Growth',
        icon: '🚀',
        price: '₪699',
        period: '/חודש',
        color: '#8b5cf6',
        tag: 'מאיצים',
        features: [
            'כל מה שב-Starter',
            'דומיין עצמאי (xxx.co.il / .com)',
            'רכישת דומיין + DNS מלא',
            '5 תיקונים לחודש',
            'דוח ביצועים חודשי',
            'AI Chat-Bot בסיסי לאתר',
        ],
        paid_flow: 'Morning שולח Webhook → נוצר pro_lead → הודעת WhatsApp עם צ\'ק-ליסט Growth.',
        admin_actions: [
            '📞 צור קשר תוך 2 שעות — לקוח Premium',
            '🌐 עזור ללקוח לבחור דומיין עצמאי (.co.il / .com)',
            '🔧 רכוש דומיין ב-Hostinger + הגדר DNS A record',
            '🤖 הפעל צינור AI + deploy לנתיב ייחודי',
            '🔐 הנפק SSL עם Certbot --nginx',
            '📊 הכן דוח ביצועים ראשוני לאחר שבוע',
        ],
        recommended: false,
    },
    {
        name: 'Pro',
        icon: '🏆',
        price: '₪1,299',
        period: '/חודש',
        color: '#f59e0b',
        tag: 'VIP',
        features: [
            'כל מה שב-Growth',
            'מנהל חשבון אישי',
            'קמפיין Google/Facebook ראשוני',
            'SEO מורחב',
            'CRM + ניתוח לידים',
            'SLA תגובה תוך שעה',
        ],
        paid_flow: 'Morning שולח Webhook → נוצר pro_lead → הודעת WhatsApp VIP ← ⚡ גם הלקוח מקבל ברכה אישית ממך אוטומטית.',
        admin_actions: [
            '⚠️ עדיפות עליונה — טפל תוך 30 דקות',
            '📞 לקוח קיבל ברכה אישית ממך (אוטומטית) — צלצל אליו',
            '📋 בנה אסטרטגיה דיגיטלית תוך 24 שעות',
            '🌐 הגדר דומיין + DNS + SSL + deploy',
            '📣 תכנן קמפיין Google/Facebook ראשוני',
            '🤝 תאם שיחת Kickoff — הצג תוכנית פעולה מלאה',
        ],
        recommended: false,
    },
];

const FAQ_ITEMS = [
    {
        q: 'כמה זמן לוקח לבנות אתר?',
        a: 'בין 1–3 דקות. צינור ה-AI (Grok → Claude → Gemini) פועל במקביל ומחזיר אתר HTML מלא.',
    },
    {
        q: 'מתי הלקוח משלם בתהליך ה-Auto (39 ₪)?',
        a: 'שלב 4 מתוך 5: אחרי שבחר דומיין וצפה בדמו. הוא מועבר לדף Morning ומשלם שם. מיד אחרי אישור התשלום מופעל Celery task שרוכש דומיין, מגדיר DNS, מפרסם nginx+SSL ושולח לו WhatsApp עם הקישור.',
    },
    {
        q: 'מה קורה כשמישהו לוחץ "בחר תוכנית Starter" (299 ₪)?',
        a: 'הוא מועבר לדף תשלום קבוע של Morning. אחרי תשלום, Webhook מגיע למערכת → נוצר רשומת pro_lead → אתה מקבל WhatsApp עם רשימת משימות: צור קשר, הגדר subdomain, הפעל צינור AI ידנית. אין הפעלה אוטומטית — הכל ידני.',
    },
    {
        q: 'מה ההבדל בין Auto (39 ₪) ל-Starter (299 ₪)?',
        a: 'Auto = הכל אוטומטי, דומיין xxx.tazo-web.com, ללא תמיכה אישית. Starter = אתה מלווה את הלקוח ידנית, הוא מקבל 2 תיקונים לחודש + תמיכה ב-WhatsApp + עדכון תכנים חודשי.',
    },
    {
        q: 'האם הלקוח מקבל כתובת מותאמת אישית?',
        a: 'Auto ו-Starter: xxx.tazo-web.com (subdomain חינמי). Growth ו-Pro: דומיין עצמאי (.co.il / .com) שנרכש דרך Hostinger API.',
    },
    {
        q: 'מה זה CEO Agent?',
        a: 'מנוע Grok AI (xAI) שמנתח את המערכת כל יום, מזהה לידים בעדיפות גבוהה ומציע מהלכים אסטרטגיים. נגיש דרך "מרכז מנכ"ל" בתפריט.',
    },
    {
        q: 'איך מקבלים לידים חדשים?',
        a: 'דרך "איסוף נתונים": הכנס עיר + קטגוריה → Google Places + Serper מחפשים ומחזירים עסקים עם ביקורות, טלפונים ופרטי קשר. Apify מוסיף נתוני אינסטגרם ו-TikTok.',
    },
    {
        q: 'האם ניתן לערוך את האתר אחרי הבנייה?',
        a: 'כן. דרך "דראפטים" ניתן לשלוח בקשת שינוי. ה-AI מציע עריכה ומנהל מאשר. בפלאן Agency יש עריכה ישירה.',
    },
    {
        q: 'מה קורה אם הלקוח לא מגיב לדמו?',
        a: 'דרך "לידים" ניתן לסמן מעקב ולשלוח תזכורת אוטומטית. ה-CEO Agent גם מציין לידים שלא קיבלו מענה מעל X ימים.',
    },
    {
        q: 'האם יש תמיכה ב-SSL בכל הכתובות?',
        a: 'כן. כל *.tazo-web.com מכוסה ב-Wildcard SSL עם חידוש אוטומטי (Let\'s Encrypt + Hostinger API).',
    },
];

/* ─── Component ──────────────────────────────────────────────── */
export function HelpPanel() {
    const [open, setOpen] = useState(false);
    const [tab, setTab] = useState<Tab>('workflow');
    const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

    return (
        <>
            {/* Floating help button */}
            <button
                onClick={() => setOpen(true)}
                title="הוראות הפעלה ומדריך מערכת"
                style={{
                    position: 'fixed',
                    bottom: 28,
                    left: 28,
                    zIndex: 9990,
                    width: 54,
                    height: 54,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                    color: '#fff',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: 24,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 20px rgba(99,102,241,0.5)',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                }}
                onMouseEnter={e => {
                    (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1.1)';
                    (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 6px 28px rgba(99,102,241,0.7)';
                }}
                onMouseLeave={e => {
                    (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)';
                    (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 4px 20px rgba(99,102,241,0.5)';
                }}
            >
                ❓
            </button>

            {/* Backdrop */}
            {open && (
                <div
                    onClick={() => setOpen(false)}
                    style={{
                        position: 'fixed', inset: 0, zIndex: 9991,
                        background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(3px)',
                    }}
                />
            )}

            {/* Panel */}
            {open && (
                <div
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        bottom: 0,
                        width: 'min(640px, 100vw)',
                        zIndex: 9992,
                        background: 'var(--bg, #fff)',
                        boxShadow: '4px 0 40px rgba(0,0,0,0.25)',
                        display: 'flex',
                        flexDirection: 'column',
                        overflow: 'hidden',
                    }}
                    dir="rtl"
                >
                    {/* Header */}
                    <div style={{
                        padding: '20px 24px 16px',
                        borderBottom: '1px solid var(--border, #e5e7eb)',
                        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                        color: '#fff',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <div>
                                <div style={{ fontSize: 22, fontWeight: 700 }}>📖 מרכז הידע</div>
                                <div style={{ fontSize: 13, opacity: 0.85, marginTop: 2 }}>מדריך מערכת · מחירים · שאלות נפוצות</div>
                            </div>
                            <button
                                onClick={() => setOpen(false)}
                                style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: '#fff', borderRadius: 8, width: 34, height: 34, cursor: 'pointer', fontSize: 18, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                            >✕</button>
                        </div>

                        {/* Tabs */}
                        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                            {([
                                { id: 'workflow', label: '🗺️ תהליך עבודה' },
                                { id: 'pricing', label: '💎 מסלולים' },
                                { id: 'faq', label: '❓ שאלות ותשובות' },
                            ] as { id: Tab; label: string }[]).map(t => (
                                <button
                                    key={t.id}
                                    onClick={() => setTab(t.id)}
                                    style={{
                                        padding: '7px 14px',
                                        borderRadius: 8,
                                        border: 'none',
                                        cursor: 'pointer',
                                        fontSize: 13,
                                        fontWeight: 600,
                                        background: tab === t.id ? '#fff' : 'rgba(255,255,255,0.15)',
                                        color: tab === t.id ? '#6366f1' : '#fff',
                                        transition: 'all 0.15s',
                                    }}
                                >
                                    {t.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Body */}
                    <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>

                        {/* ── WORKFLOW TAB ── */}
                        {tab === 'workflow' && (
                            <div>
                                {/* Track A: Outbound */}
                                <div style={{
                                    background: '#eff6ff', borderRadius: 12, padding: '12px 16px', marginBottom: 20,
                                    borderRight: '4px solid #3b82f6',
                                }}>
                                    <div style={{ fontWeight: 700, fontSize: 14, color: '#1d4ed8', marginBottom: 4 }}>📤 מסלול A — יוצא (ממוכן חיצוני)</div>
                                    <div style={{ fontSize: 13, color: '#1e40af' }}>אתה מוצא לידים → בונה דמו → שולח WhatsApp → לקוח משלם</div>
                                </div>
                                {WORKFLOW_STEPS_OUTBOUND.map((phase, pi) => (
                                    <div key={pi} style={{ marginBottom: 20 }}>
                                        <div style={{
                                            display: 'flex', alignItems: 'center', gap: 10,
                                            padding: '10px 14px',
                                            background: phase.color + '18',
                                            borderRight: `4px solid ${phase.color}`,
                                            borderRadius: '0 10px 10px 0',
                                            marginBottom: 10,
                                        }}>
                                            <span style={{ fontSize: 20 }}>{phase.icon}</span>
                                            <span style={{ fontWeight: 700, fontSize: 15, color: phase.color }}>{phase.phase}</span>
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, paddingRight: 8 }}>
                                            {phase.steps.map((step, si) => (
                                                <div key={si} style={{
                                                    display: 'flex', gap: 12, alignItems: 'flex-start',
                                                    padding: '10px 14px',
                                                    background: 'var(--surface, #f9fafb)',
                                                    borderRadius: 10,
                                                    border: '1px solid var(--border, #e5e7eb)',
                                                }}>
                                                    <div style={{
                                                        minWidth: 70, padding: '2px 8px', borderRadius: 20,
                                                        fontSize: 11, fontWeight: 700, textAlign: 'center',
                                                        background: step.who === 'מנהל' ? '#dbeafe' : step.who === 'מערכת' ? '#dcfce7' : step.who === 'AI Pipeline' ? '#ede9fe' : step.who === 'לקוח' ? '#fef3c7' : '#f3f4f6',
                                                        color: step.who === 'מנהל' ? '#1d4ed8' : step.who === 'מערכת' ? '#15803d' : step.who === 'AI Pipeline' ? '#7c3aed' : step.who === 'לקוח' ? '#92400e' : '#374151',
                                                    }}>{step.who}</div>
                                                    <div style={{ fontSize: 13.5, lineHeight: 1.6, color: 'var(--text, #111)' }}>{step.action}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}

                                {/* Track B: Inbound */}
                                <div style={{
                                    background: '#f0fdf4', borderRadius: 12, padding: '12px 16px', marginBottom: 20, marginTop: 8,
                                    borderRight: '4px solid #10b981',
                                }}>
                                    <div style={{ fontWeight: 700, fontSize: 14, color: '#065f46', marginBottom: 4 }}>📥 מסלול B — נכנס (לקוח מזדמן · Auto 39 ₪)</div>
                                    <div style={{ fontSize: 13, color: '#047857' }}>לקוח נכנס ל-tazo-web.com → ממלא טופס → משלם ← הכל אוטומטי</div>
                                </div>
                                {WORKFLOW_STEPS_INBOUND.map((phase, pi) => (
                                    <div key={pi} style={{ marginBottom: 20 }}>
                                        <div style={{
                                            display: 'flex', alignItems: 'center', gap: 10,
                                            padding: '10px 14px',
                                            background: phase.color + '18',
                                            borderRight: `4px solid ${phase.color}`,
                                            borderRadius: '0 10px 10px 0',
                                            marginBottom: 10,
                                        }}>
                                            <span style={{ fontSize: 20 }}>{phase.icon}</span>
                                            <span style={{ fontWeight: 700, fontSize: 15, color: phase.color }}>{phase.phase}</span>
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, paddingRight: 8 }}>
                                            {phase.steps.map((step, si) => (
                                                <div key={si} style={{
                                                    display: 'flex', gap: 12, alignItems: 'flex-start',
                                                    padding: '10px 14px',
                                                    background: 'var(--surface, #f9fafb)',
                                                    borderRadius: 10,
                                                    border: '1px solid var(--border, #e5e7eb)',
                                                }}>
                                                    <div style={{
                                                        minWidth: 70, padding: '2px 8px', borderRadius: 20,
                                                        fontSize: 11, fontWeight: 700, textAlign: 'center',
                                                        background: step.who === 'מנהל' ? '#dbeafe' : step.who === 'מערכת' ? '#dcfce7' : step.who === 'AI Pipeline' ? '#ede9fe' : step.who === 'לקוח' ? '#fef3c7' : '#f3f4f6',
                                                        color: step.who === 'מנהל' ? '#1d4ed8' : step.who === 'מערכת' ? '#15803d' : step.who === 'AI Pipeline' ? '#7c3aed' : step.who === 'לקוח' ? '#92400e' : '#374151',
                                                    }}>{step.who}</div>
                                                    <div style={{ fontSize: 13.5, lineHeight: 1.6, color: 'var(--text, #111)' }}>{step.action}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}

                                {/* Legend */}
                                <div style={{ marginTop: 16, padding: 14, background: 'var(--surface, #f9fafb)', borderRadius: 10, border: '1px solid var(--border, #e5e7eb)' }}>
                                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted, #6b7280)', marginBottom: 8 }}>מקרא תפקידים</div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                        {[{ who: 'מנהל', color: '#dbeafe', text: '#1d4ed8' }, { who: 'מערכת', color: '#dcfce7', text: '#15803d' }, { who: 'AI Pipeline', color: '#ede9fe', text: '#7c3aed' }, { who: 'לקוח', color: '#fef3c7', text: '#92400e' }].map(b => (
                                            <span key={b.who} style={{ padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 700, background: b.color, color: b.text }}>{b.who}</span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ── PRICING TAB ── */}
                        {tab === 'pricing' && (
                            <div>
                                <p style={{ fontSize: 14, color: 'var(--text-muted, #6b7280)', marginBottom: 8, lineHeight: 1.7 }}>
                                    תוכניות ללקוחות עסקיים — מה הלקוח מקבל ומה אתה צריך לעשות:
                                </p>

                                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                    {CUSTOMER_PLANS.map((plan, pi) => (
                                        <div key={pi} style={{
                                            border: plan.recommended ? `2px solid ${plan.color}` : '1px solid var(--border, #e5e7eb)',
                                            borderRadius: 14,
                                            overflow: 'hidden',
                                            boxShadow: plan.recommended ? `0 4px 20px ${plan.color}30` : 'none',
                                        }}>
                                            {plan.recommended && (
                                                <div style={{ background: plan.color, color: '#fff', textAlign: 'center', padding: '5px 0', fontSize: 12, fontWeight: 700 }}>
                                                    ⭐ הנמכר ביותר
                                                </div>
                                            )}
                                            <div style={{ padding: '16px 20px' }}>
                                                {/* Header */}
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                                                    <div>
                                                        <div style={{ fontSize: 17, fontWeight: 700 }}>{plan.icon} {plan.name}</div>
                                                        <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 20, background: plan.color + '20', color: plan.color, fontWeight: 600 }}>{plan.tag}</span>
                                                    </div>
                                                    <div style={{ textAlign: 'left' }}>
                                                        <span style={{ fontSize: 24, fontWeight: 800, color: plan.color }}>{plan.price}</span>
                                                        <span style={{ fontSize: 13, color: 'var(--text-muted, #6b7280)' }}>{plan.period}</span>
                                                    </div>
                                                </div>

                                                {/* Features */}
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }}>
                                                    {plan.features.map((f, fi) => (
                                                        <div key={fi} style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
                                                            <span style={{ color: plan.color, fontWeight: 700 }}>✓</span> {f}
                                                        </div>
                                                    ))}
                                                </div>

                                                {/* Payment flow */}
                                                <div style={{ background: '#f0f9ff', borderRadius: 8, padding: '8px 12px', marginBottom: 10, fontSize: 12, color: '#0369a1', borderRight: `3px solid ${plan.color}` }}>
                                                    <span style={{ fontWeight: 700 }}>⚡ מה קורה אחרי תשלום: </span>{plan.paid_flow}
                                                </div>

                                                {/* Admin checklist */}
                                                {plan.admin_actions.length > 0 && (
                                                    <div style={{ background: '#fefce8', borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
                                                        <div style={{ fontWeight: 700, color: '#92400e', marginBottom: 6 }}>📋 משימות לך (מנהל):</div>
                                                        {plan.admin_actions.map((a, ai) => (
                                                            <div key={ai} style={{ color: '#78350f', marginBottom: 3 }}>{a}</div>
                                                        ))}
                                                    </div>
                                                )}
                                                {plan.admin_actions.length === 0 && (
                                                    <div style={{ background: '#f0fdf4', borderRadius: 8, padding: '8px 12px', fontSize: 12, color: '#166534' }}>
                                                        ✅ <strong>אין פעולה ידנית נדרשת</strong> — הכל מופעל אוטומטית
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div style={{ marginTop: 16, padding: 12, background: '#ede9fe', borderRadius: 10, fontSize: 12, color: '#4c1d95' }}>
                                    <strong>💳 קישורי Morning לכל תוכנית:</strong><br />
                                    Auto 39₪: mrng.to/Afe6Dg21q0 · Starter 299₪: mrng.to/sHDNNsGZwX<br />
                                    Growth 699₪: mrng.to/nTNb7uWesR · Pro 1299₪: mrng.to/SDxruL9Hg0
                                </div>
                            </div>
                        )}

                        {/* ── FAQ TAB ── */}
                        {tab === 'faq' && (
                            <div>
                                <p style={{ fontSize: 14, color: 'var(--text-muted, #6b7280)', marginBottom: 20 }}>
                                    תשובות לשאלות הנפוצות ביותר על המערכת:
                                </p>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                    {FAQ_ITEMS.map((item, i) => (
                                        <div key={i} style={{
                                            border: '1px solid var(--border, #e5e7eb)',
                                            borderRadius: 12,
                                            overflow: 'hidden',
                                        }}>
                                            <button
                                                onClick={() => setExpandedFaq(expandedFaq === i ? null : i)}
                                                style={{
                                                    width: '100%',
                                                    padding: '13px 16px',
                                                    background: 'var(--surface, #f9fafb)',
                                                    border: 'none',
                                                    cursor: 'pointer',
                                                    display: 'flex',
                                                    justifyContent: 'space-between',
                                                    alignItems: 'center',
                                                    gap: 10,
                                                    textAlign: 'right',
                                                }}
                                            >
                                                <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text, #111)', flex: 1 }}>{item.q}</span>
                                                <span style={{
                                                    fontSize: 14,
                                                    color: '#6366f1',
                                                    transition: 'transform 0.2s',
                                                    transform: expandedFaq === i ? 'rotate(180deg)' : 'rotate(0deg)',
                                                    display: 'inline-block',
                                                    minWidth: 16,
                                                }}>▾</span>
                                            </button>
                                            {expandedFaq === i && (
                                                <div style={{
                                                    padding: '12px 16px 14px',
                                                    fontSize: 13.5,
                                                    lineHeight: 1.8,
                                                    color: 'var(--text-muted, #374151)',
                                                    borderTop: '1px solid var(--border, #e5e7eb)',
                                                    background: 'var(--bg, #fff)',
                                                }}>
                                                    {item.a}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>

                                {/* Contact */}
                                <div style={{ marginTop: 20, padding: 16, background: '#f0fdf4', borderRadius: 12, border: '1px solid #bbf7d0' }}>
                                    <div style={{ fontSize: 14, fontWeight: 700, color: '#15803d', marginBottom: 4 }}>💬 לא מצאת תשובה?</div>
                                    <div style={{ fontSize: 13, color: '#166534' }}>
                                        פנה למנכ"ל AI דרך <strong>מרכז מנכ"ל</strong> בתפריט הצדדי, או שלח מייל ל-admin@tazo-web.com
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div style={{
                        padding: '12px 24px',
                        borderTop: '1px solid var(--border, #e5e7eb)',
                        fontSize: 12,
                        color: 'var(--text-muted, #9ca3af)',
                        textAlign: 'center',
                    }}>
                        tazo-web Admin Panel · v27 · כל הזכויות שמורות
                    </div>
                </div>
            )}
        </>
    );
}
