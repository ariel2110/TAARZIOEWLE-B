import React from 'react'

const S = {
  wrap: { maxWidth: 780, margin: '0 auto', padding: '60px 24px 80px', fontFamily: 'Heebo, Segoe UI, sans-serif', direction: 'rtl' as const, color: '#e2e8f0' },
  h1:   { fontSize: 'clamp(22px,4vw,34px)', fontWeight: 900, marginBottom: 8, background: 'linear-gradient(135deg,#f59e0b,#ef4444)', WebkitBackgroundClip: 'text' as const, WebkitTextFillColor: 'transparent' as const },
  h2:   { fontSize: 18, fontWeight: 800, marginTop: 32, marginBottom: 10, color: '#f59e0b' },
  p:    { fontSize: 14, lineHeight: 1.8, marginBottom: 12, color: '#94a3b8' },
  ul:   { paddingRight: 20, marginBottom: 12 },
  li:   { fontSize: 14, lineHeight: 1.8, color: '#94a3b8', marginBottom: 4 },
  sep:  { border: 'none', borderTop: '1px solid rgba(255,255,255,0.07)', margin: '32px 0' },
}

export default function Terms() {
  return (
    <main style={{ background: '#0d1117', minHeight: '100vh' }}>
      <div style={S.wrap}>
        <h1 style={S.h1}>תנאי שימוש — TAZO Web</h1>
        <p style={{ ...S.p, fontSize: 12, color: '#475569' }}>עדכון אחרון: יוני 2026 | tazo-web.com</p>
        <hr style={S.sep} />

        <h2 style={S.h2}>הסכם שימוש</h2>
        <p style={S.p}>
          שימוש בפלטפורמת TAZO Web מהווה הסכמה לתנאים אלה. אם אינך מסכים — אנא הפסק להשתמש בשירות.
        </p>

        <h2 style={S.h2}>השירות</h2>
        <p style={S.p}>
          TAZO Web מספקת כלים לבניית אתרי עסקים, ניהול הזמנות, וחיבור לקוחות לעסקים מקומיים.
          השירות ניתן "כמות שהוא" (as-is) ו-TAZO אינה מתחייבת לזמינות מלאה.
        </p>

        <h2 style={S.h2}>חשבון ואימות</h2>
        <ul style={S.ul}>
          <li style={S.li}>נדרש מספר טלפון ישראלי תקין לאימות</li>
          <li style={S.li}>אינך רשאי ליצור חשבון עבור עסק שאינך מייצג</li>
          <li style={S.li}>TAZO שומרת לעצמה את הזכות להשהות חשבונות</li>
        </ul>

        <h2 style={S.h2}>תוכן ועסקים</h2>
        <ul style={S.ul}>
          <li style={S.li}>המשתמש אחראי לנכונות פרטי העסק</li>
          <li style={S.li}>TAZO רשאית להסיר תוכן שאינו עומד בקווים המנחים</li>
          <li style={S.li}>אין להשתמש בפלטפורמה לפעילות בלתי חוקית</li>
        </ul>

        <h2 style={S.h2}>תשלומים</h2>
        <p style={S.p}>
          עסקאות המבוצעות דרך TAZO כפופות לתנאי ספקי התשלום (Morning / Vault). עמלות הפלטפורמה
          מוצגות לפני אישור כל עסקה.
        </p>

        <h2 style={S.h2}>הגבלת אחריות</h2>
        <p style={S.p}>
          TAZO אינה אחראית לנזק עקיף, אובדן רווח, או הפרעות בשירות. האחריות המקסימלית של TAZO
          מוגבלת לסכום ששולם ב-12 החודשים האחרונים.
        </p>

        <h2 style={S.h2}>קניין רוחני</h2>
        <p style={S.p}>
          הלוגו, העיצוב, והקוד של TAZO הם קניינו של אריאל אביב. אין לשכפל או להשתמש ללא אישור.
        </p>

        <h2 style={S.h2}>שינויים בתנאים</h2>
        <p style={S.p}>
          TAZO רשאית לעדכן תנאים אלה. המשך שימוש לאחר עדכון מהווה הסכמה לתנאים החדשים.
        </p>

        <h2 style={S.h2}>דין וסמכות</h2>
        <p style={S.p}>
          הדין הישראלי חל על תנאים אלה. סמכות השיפוט — בתי המשפט בתל אביב.
        </p>

        <h2 style={S.h2}>יצירת קשר</h2>
        <p style={S.p}>
          <a href="mailto:ar.2110@gmail.com" style={{ color: '#f59e0b' }}>ar.2110@gmail.com</a>{' '}
          | <a href="tel:+972546363350" style={{ color: '#f59e0b' }}>+972-54-6363350</a>
        </p>

        <hr style={S.sep} />
        <p style={{ ...S.p, fontSize: 11, color: '#334155' }}>
          © 2026 TAZO | אריאל אביב, עוסק פטור 040978207 |{' '}
          <a href="/privacy" style={{ color: '#475569' }}>מדיניות פרטיות</a>
        </p>
      </div>
    </main>
  )
}
