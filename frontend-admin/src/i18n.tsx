import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Lang = 'he' | 'en';

const T = {
    // ── Overview ──────────────────────────────────────────────────────
    overview: { he: 'סקירה כללית', en: 'Overview' },
    ceo_digest: { he: 'סיכום יומי מנכ"ל', en: 'CEO Daily Digest' },
    system_health: { he: 'בריאות המערכת', en: 'System Health' },
    status: { he: 'סטטוס', en: 'Status' },
    database: { he: 'בסיס נתונים', en: 'Database' },
    db_connected: { he: 'מחובר', en: 'connected' },
    db_unknown: { he: 'לא ידוע', en: 'unknown/degraded' },
    businesses: { he: 'עסקים', en: 'Businesses' },
    pending_approvals: { he: 'אישורים ממתינים', en: 'Pending Approvals' },
    // ── Approvals ─────────────────────────────────────────────────────
    approval_queue: { he: 'תור אישורים', en: 'Approval Queue' },
    approval_detail: { he: 'פרטי אישור', en: 'Approval Detail' },
    open_detail: { he: 'פתח פרטים', en: 'Open detail' },
    approve: { he: 'אשר', en: 'Approve' },
    execute: { he: '▶ בצע', en: '▶ Execute' },
    reject: { he: 'דחה', en: 'Reject' },
    why: { he: 'למה', en: 'Why' },
    evidence: { he: 'עדות', en: 'Evidence' },
    before: { he: 'לפני', en: 'Before' },
    after: { he: 'אחרי', en: 'After' },
    create_ceo_task: { he: 'צור משימת מנכ"ל', en: 'Create CEO task' },
    confidence: { he: 'ביטחון', en: 'confidence' },
    select_approval: { he: 'בחר פריט אישור לבדיקה לפני/אחרי, נימוק, עדות וביטחון.', en: 'Select an approval item to inspect before/after, rationale, evidence, and confidence.' },
    // ── Security ──────────────────────────────────────────────────────
    security_monitoring: { he: 'ניטור אבטחה', en: 'Security Monitoring' },
    overall: { he: 'כללי', en: 'Overall' },
    login_failures: { he: 'כשלי כניסה', en: 'Login Failures' },
    blocked_logins: { he: 'כניסות חסומות', en: 'Blocked Logins' },
    rate_limited: { he: 'הגבלת קצב', en: 'Rate Limited' },
    suspicion_watchlist: { he: 'רשימת חשדות', en: 'Suspicion Watchlist' },
    security_timeline: { he: 'ציר זמן אבטחה', en: 'Security Timeline' },
    score_label: { he: 'ציון', en: 'score' },
    failures_label: { he: 'כשלים', en: 'failures' },
    blocked_label: { he: 'חסומים', en: 'blocked' },
    unknown_status: { he: 'לא ידוע', en: 'unknown' },
    // ── Queues ────────────────────────────────────────────────────────
    queue_summary: { he: 'סיכום תורים', en: 'Queue Summary' },
    queue_items: { he: 'פריטי תור', en: 'Queue Items' },
    open: { he: 'פתח', en: 'Open' },
    priority_label: { he: 'עדיפות', en: 'priority' },
    // ── Targeting ─────────────────────────────────────────────────────
    targeting_console: { he: 'קונסולת טירגוט', en: 'Targeting Console' },
    city: { he: 'עיר', en: 'City' },
    category: { he: 'קטגוריה', en: 'Category' },
    run_search: { he: 'חפש', en: 'Run search' },
    profiles_label: { he: 'פרופילים', en: 'Profiles' },
    campaigns_label: { he: 'קמפיינים', en: 'Campaigns' },
    campaign_results: { he: 'תוצאות קמפיין', en: 'Campaign results' },
    leads_label: { he: 'לידים', en: 'Leads' },
    has_website: { he: 'יש אתר', en: 'has website' },
    no_website: { he: 'אין אתר', en: 'no website' },
    campaign_label: { he: 'קמפיין', en: 'campaign' },
    assign_campaign: { he: 'שייך לקמפיין הנבחר', en: 'Assign to selected campaign' },
    segment_preview: { he: 'תצוגת תוצאות סגמנט', en: 'Segment Result Preview' },
    use_campaign: { he: 'בחר קמפיין', en: 'Use campaign' },
    beauty_rg: { he: 'יופי · רמת גן', en: 'Beauty · Ramat Gan' },
    garages_pt: { he: 'מוסכים · פתח תקווה', en: 'Garages · Petah Tikva' },
    city_placeholder: { he: 'לדוגמה: רמת גן', en: 'e.g. Ramat Gan' },
    category_placeholder: { he: 'לדוגמה: יופי', en: 'e.g. beauty' },
    km_label: { he: 'ק"מ', en: 'km' },
    // ── Feedback ──────────────────────────────────────────────────────
    feedback_intelligence: { he: 'מודיעין פידבק', en: 'Feedback Intelligence' },
    feedback_subtitle: { he: 'פידבק מהיר + פידבק פתוח + פרשנות מנכ"ל', en: 'Quick feedback + open feedback + CEO interpretation.' },
    target_type: { he: 'סוג יעד', en: 'Target type' },
    draft_site: { he: 'אתר טיוטה', en: 'Draft site' },
    outreach_message: { he: 'הודעת פנייה', en: 'Outreach message' },
    ceo_report: { he: 'דוח מנכ"ל', en: 'CEO report' },
    recommendation: { he: 'המלצה', en: 'Recommendation' },
    system_general: { he: 'כללי מערכת', en: 'System general' },
    quick_feedback: { he: 'פידבק מהיר', en: 'Quick feedback' },
    good_as_is: { he: 'טוב כמו שהוא', en: 'Good as-is' },
    needs_improvement: { he: 'דרוש שיפור', en: 'Needs improvement' },
    not_a_fit: { he: 'לא מתאים', en: 'Not a fit' },
    open_feedback: { he: 'פידבק פתוח', en: 'Open feedback' },
    open_feedback_ph: { he: 'כתוב חופשי: מה צריך להשתפר, להשתנות, או להיזכר בפעם הבאה?', en: 'Write freely: what should improve, change, or be remembered next time?' },
    submit_feedback: { he: 'שלח פידבק', en: 'Submit feedback' },
    status_label: { he: 'סטטוס', en: 'Status' },
    scope_label: { he: 'תחום', en: 'Scope' },
    ceo_response: { he: 'תגובת מנכ"ל', en: 'CEO response' },
    analyze: { he: 'נתח', en: 'Analyze' },
    preference_candidate: { he: 'מועמד להעדפה', en: 'Preference candidate' },
    // ── Login ─────────────────────────────────────────────────────────
    admin_title: { he: 'tazo-web Admin', en: 'tazo-web Admin' },
    // ── Lang toggle ───────────────────────────────────────────────────
    switch_lang: { he: 'English', en: 'עברית' },
} as const;

export type TranslationKey = keyof typeof T;

const LangContext = createContext<{ lang: Lang; toggle: () => void }>({
    lang: 'he',
    toggle: () => { },
});

export function LangProvider({ children }: { children: ReactNode }) {
    const stored = (localStorage.getItem('sn_lang') ?? 'he') as Lang;
    const [lang, setLang] = useState<Lang>(stored);
    const toggle = () => {
        const next: Lang = lang === 'he' ? 'en' : 'he';
        localStorage.setItem('sn_lang', next);
        setLang(next);
    };
    return <LangContext.Provider value={{ lang, toggle }}>{children}</LangContext.Provider>;
}

export function useLang() {
    const { lang, toggle } = useContext(LangContext);
    const t = (key: TranslationKey): string => T[key][lang];
    return { lang, toggle, t };
}

// ── Dark Mode ────────────────────────────────────────────────────────
type Theme = 'light' | 'dark';
const ThemeContext = createContext<{ theme: Theme; toggleTheme: () => void }>({ theme: 'light', toggleTheme: () => { } });

export function ThemeProvider({ children }: { children: ReactNode }) {
    const stored = (localStorage.getItem('sn_theme') ?? 'light') as Theme;
    const [theme, setTheme] = useState<Theme>(stored);
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);
    const toggleTheme = () => {
        const next: Theme = theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('sn_theme', next);
        setTheme(next);
    };
    return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
    return useContext(ThemeContext);
}
