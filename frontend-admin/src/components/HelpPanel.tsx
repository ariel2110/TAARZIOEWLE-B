import React, { useState } from 'react';

/* ─── Types ─────────────────────────────────────────────────── */
type Tab = 'workflow' | 'pricing' | 'faq';

/* ─── Content ────────────────────────────────────────────────── */

const WORKFLOW_STEPS = [
  {
    phase: 'שלב 1 — איסוף לידים',
    icon: '🔍',
    color: '#3b82f6',
    steps: [
      { who: 'מנהל', action: 'כנס ל"איסוף נתונים" → הכנס עיר + קטגוריה עסקית (למשל: "תל אביב, ספרות")' },
      { who: 'מערכת', action: 'Google Places API מחפש עסקים ומחזיר רשימה עם פרטים, ביקורות ומיקום' },
      { who: 'מנהל', action: 'בחר עסקים רלוונטיים → לחץ "ייבא לרשימת לידים"' },
    ],
  },
  {
    phase: 'שלב 2 — ניהול לידים',
    icon: '🎯',
    color: '#8b5cf6',
    steps: [
      { who: 'מנהל', action: 'כנס ל"לידים" → ראה את כל העסקים שייובאו' },
      { who: 'מנהל', action: 'סנן לפי עיר / קטגוריה / סטטוס → לחץ "כשר ליד" כדי להעביר לעסקים' },
      { who: 'מערכת', action: 'הליד הופך לעסק פעיל בעמוד "עסקים"' },
    ],
  },
  {
    phase: 'שלב 3 — בניית אתר דמו',
    icon: '🤖',
    color: '#10b981',
    steps: [
      { who: 'מנהל', action: 'כנס ל"אתרי דמו" → לחץ "צור דמו" → בחר עסק מהרשימה' },
      { who: 'AI Pipeline', action: 'GPT-4o כותב תוכן שיווקי עשיר + Gemini קובע עיצוב + Claude בונה HTML מלא' },
      { who: 'מערכת', action: 'האתר עולה בפחות מ-3 דקות בכתובת https://[שם-עסק].sitenest.site' },
      { who: 'מנהל', action: 'שלח לעסק קישור + הודעת WhatsApp אוטומטית שנוצרת ע"י AI' },
    ],
  },
  {
    phase: 'שלב 4 — Magic Portal (לקוחות מזדמנים)',
    icon: '✨',
    color: '#f59e0b',
    steps: [
      { who: 'לקוח', action: 'נכנס ל-sitenest.site → מזין שם עסק + עיר' },
      { who: 'מערכת', action: 'מריץ את צינור ה-AI המלא אוטומטית ובונה אתר ייחודי' },
      { who: 'לקוח', action: 'מקבל קישור מיידי לאתרו — https://[שם-עסק].sitenest.site' },
      { who: 'מנהל', action: 'האתר מופיע אוטומטית ב"אתרי דמו" ב-Admin Panel' },
    ],
  },
  {
    phase: 'שלב 5 — אישור ותשלום',
    icon: '💳',
    color: '#ef4444',
    steps: [
      { who: 'מנהל', action: 'לקוח רוצה להמשיך? כנס ל"תשלומים" → שלח קישור תשלום' },
      { who: 'לקוח', action: 'משלם → האתר עובר ממצב דמו לאתר פעיל' },
      { who: 'מנהל', action: 'אשר הפעלה ב"אישורים" → הלקוח מקבל גישה לפורטל לקוח' },
    ],
  },
];

const PLANS = [
  {
    name: 'Starter',
    icon: '🌱',
    price: '₪299',
    period: '/חודש',
    annual: '₪249/חודש בתשלום שנתי',
    color: '#3b82f6',
    features: [
      '5 אתרי לקוחות פעילים',
      '20 דמו חודשיים',
      'SSL + subdomain ייחודי',
      'AI בנייה אוטומטית',
      'ניהול דרך WhatsApp',
      'תמיכה במייל',
    ],
    notIncluded: ['CEO Agent', 'API Access', 'White-label'],
    cta: 'התחל ב-Starter',
    recommended: false,
  },
  {
    name: 'Growth',
    icon: '🚀',
    price: '₪699',
    period: '/חודש',
    annual: '₪579/חודש בתשלום שנתי',
    color: '#8b5cf6',
    features: [
      '25 אתרי לקוחות פעילים',
      'דמו ללא הגבלה',
      'SSL + subdomain ייחודי',
      'AI בנייה אוטומטית',
      'CEO Agent (Grok AI)',
      'ניתוח לידים מתקדם',
      'Targeting & Campaigns',
      'תמיכה מועדפת',
    ],
    notIncluded: ['API Access', 'White-label'],
    cta: 'שדרג ל-Growth',
    recommended: true,
  },
  {
    name: 'Agency',
    icon: '🏢',
    price: '₪1,799',
    period: '/חודש',
    annual: '₪1,499/חודש בתשלום שנתי',
    color: '#f59e0b',
    features: [
      'לקוחות ללא הגבלה',
      'דמו ללא הגבלה',
      'SSL + subdomain ייחודי',
      'AI בנייה אוטומטית',
      'CEO Agent (Grok AI)',
      'API Access מלא',
      'White-label (לוגו שלך)',
      'מנהל חשבון ייעודי',
      'SLA 99.9%',
    ],
    notIncluded: [],
    cta: 'צור קשר ל-Agency',
    recommended: false,
  },
];

const FAQ_ITEMS = [
  {
    q: 'כמה זמן לוקח לבנות אתר?',
    a: 'בין 1–3 דקות. צינור ה-AI (GPT-4o → Gemini → Claude) פועל במקביל ומחזיר אתר HTML מלא.',
  },
  {
    q: 'האם הלקוח מקבל כתובת מותאמת אישית?',
    a: 'כן. כל אתר מקבל כתובת https://[שם-עסק].sitenest.site עם SSL מלא. בפלאן Agency ניתן להשתמש בדומיין מותאם אישית.',
  },
  {
    q: 'מה ההבדל בין דמו לאתר פעיל?',
    a: 'דמו הוא אתר הדגמה שנשלח ללקוח ב-WhatsApp בחינם. אחרי תשלום הלקוח, האתר הופך לפעיל עם גישה לפורטל לקוח ועריכה עצמאית.',
  },
  {
    q: 'מה זה CEO Agent?',
    a: 'מנוע Grok AI (xAI) שמנתח את המערכת כל יום, מזהה לידים בעדיפות גבוהה ומציע מהלכים אסטרטגיים. נגיש דרך "מרכז מנכ"ל" בתפריט.',
  },
  {
    q: 'איך מקבלים לידים חדשים?',
    a: 'דרך "איסוף נתונים": הכנס עיר + קטגוריה → המערכת מחפשת ב-Google Places ומחזירה עסקים עם ביקורות, טלפונים ופרטי קשר.',
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
    a: 'כן. כל *.sitenest.site מכוסה ב-Wildcard SSL עם חידוש אוטומטי (Let\'s Encrypt + Hostinger API).',
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
                <p style={{ fontSize: 14, color: 'var(--text-muted, #6b7280)', marginBottom: 20, lineHeight: 1.7 }}>
                  הצינור המלא מלסיוע ראשוני ועד אתר פעיל — 5 שלבים:
                </p>
                {WORKFLOW_STEPS.map((phase, pi) => (
                  <div key={pi} style={{ marginBottom: 20 }}>
                    {/* Phase header */}
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

                    {/* Steps */}
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
                            minWidth: 70,
                            padding: '2px 8px',
                            borderRadius: 20,
                            fontSize: 11,
                            fontWeight: 700,
                            textAlign: 'center',
                            background: step.who === 'מנהל' ? '#dbeafe' :
                                        step.who === 'מערכת' ? '#dcfce7' :
                                        step.who === 'AI Pipeline' ? '#ede9fe' :
                                        step.who === 'לקוח' ? '#fef3c7' : '#f3f4f6',
                            color: step.who === 'מנהל' ? '#1d4ed8' :
                                   step.who === 'מערכת' ? '#15803d' :
                                   step.who === 'AI Pipeline' ? '#7c3aed' :
                                   step.who === 'לקוח' ? '#92400e' : '#374151',
                          }}>
                            {step.who}
                          </div>
                          <div style={{ fontSize: 13.5, lineHeight: 1.6, color: 'var(--text, #111)' }}>
                            {step.action}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Who badge legend */}
                <div style={{ marginTop: 16, padding: 14, background: 'var(--surface, #f9fafb)', borderRadius: 10, border: '1px solid var(--border, #e5e7eb)' }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted, #6b7280)', marginBottom: 8 }}>מקרא תפקידים</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {[
                      { who: 'מנהל', color: '#dbeafe', text: '#1d4ed8' },
                      { who: 'מערכת', color: '#dcfce7', text: '#15803d' },
                      { who: 'AI Pipeline', color: '#ede9fe', text: '#7c3aed' },
                      { who: 'לקוח', color: '#fef3c7', text: '#92400e' },
                    ].map(b => (
                      <span key={b.who} style={{ padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 700, background: b.color, color: b.text }}>
                        {b.who}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ── PRICING TAB ── */}
            {tab === 'pricing' && (
              <div>
                <p style={{ fontSize: 14, color: 'var(--text-muted, #6b7280)', marginBottom: 20 }}>
                  בחר מסלול שמתאים לגודל הפעילות שלך:
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {PLANS.map((plan, pi) => (
                    <div key={pi} style={{
                      border: plan.recommended ? `2px solid ${plan.color}` : '1px solid var(--border, #e5e7eb)',
                      borderRadius: 14,
                      overflow: 'hidden',
                      boxShadow: plan.recommended ? `0 4px 20px ${plan.color}30` : 'none',
                    }}>
                      {plan.recommended && (
                        <div style={{ background: plan.color, color: '#fff', textAlign: 'center', padding: '5px 0', fontSize: 12, fontWeight: 700 }}>
                          ⭐ המומלץ ביותר
                        </div>
                      )}
                      <div style={{ padding: '16px 20px' }}>
                        {/* Plan name + price */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                          <div>
                            <div style={{ fontSize: 18, fontWeight: 700 }}>{plan.icon} {plan.name}</div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted, #6b7280)', marginTop: 3 }}>{plan.annual}</div>
                          </div>
                          <div style={{ textAlign: 'left' }}>
                            <span style={{ fontSize: 26, fontWeight: 800, color: plan.color }}>{plan.price}</span>
                            <span style={{ fontSize: 13, color: 'var(--text-muted, #6b7280)' }}>{plan.period}</span>
                          </div>
                        </div>

                        {/* Features */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 14 }}>
                          {plan.features.map((f, fi) => (
                            <div key={fi} style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
                              <span style={{ color: plan.color, fontWeight: 700 }}>✓</span>
                              {f}
                            </div>
                          ))}
                          {plan.notIncluded.map((f, fi) => (
                            <div key={fi} style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 8, opacity: 0.4 }}>
                              <span>✗</span> {f}
                            </div>
                          ))}
                        </div>

                        {/* CTA */}
                        <button style={{
                          width: '100%',
                          padding: '11px 0',
                          borderRadius: 10,
                          border: 'none',
                          cursor: 'pointer',
                          fontSize: 14,
                          fontWeight: 700,
                          background: plan.recommended ? plan.color : 'transparent',
                          color: plan.recommended ? '#fff' : plan.color,
                          border: plan.recommended ? 'none' : `2px solid ${plan.color}`,
                          transition: 'opacity 0.15s',
                        }}
                          onMouseEnter={e => (e.currentTarget.style.opacity = '0.85')}
                          onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
                        >
                          {plan.cta}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Upgrade benefits */}
                <div style={{ marginTop: 20, padding: 14, background: '#ede9fe', borderRadius: 12 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#7c3aed', marginBottom: 6 }}>💡 יתרונות תשלום שנתי</div>
                  <div style={{ fontSize: 13, color: '#4c1d95', lineHeight: 1.7 }}>
                    חסוך עד 17% בתשלום שנתי מראש. ביטול בכל עת. חידוש אוטומטי ב-30 יום לפני תאריך פקיעה.
                  </div>
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
                    פנה למנכ"ל AI דרך <strong>מרכז מנכ"ל</strong> בתפריט הצדדי, או שלח מייל ל-admin@sitenest.site
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
            SiteNest Admin Panel · v27 · כל הזכויות שמורות
          </div>
        </div>
      )}
    </>
  );
}
