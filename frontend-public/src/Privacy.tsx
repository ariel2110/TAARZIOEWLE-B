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

export default function Privacy() {
  return (
    <main style={{ background: '#0d1117', minHeight: '100vh' }}>
      <div style={S.wrap}>
        <h1 style={S.h1}>מדיניות פרטיות — TAZO Web</h1>
        <p style={{ ...S.p, fontSize: 12, color: '#475569' }}>עדכון אחרון: יוני 2026 | tazo-web.com</p>
        <hr style={S.sep} />

        <h2 style={S.h2}>מי אנחנו</h2>
        <p style={S.p}>
          TAZO Web היא פלטפורמה לבניית אתרי עסקים ומסחר מקומי, המופעלת ובבעלות אריאל אביב,
          עוסק פטור מספר 040978207, תל אביב, ישראל.
        </p>

        <h2 style={S.h2}>מה אנחנו אוספים</h2>
        <ul style={S.ul}>
          <li style={S.li}>מספר טלפון — לצורך אימות דרך WhatsApp/OTP</li>
          <li style={S.li}>שם עסק וכתובת — לבניית הדף העסקי</li>
          <li style={S.li}>מיקום GPS — לזיהוי עסקים בקרבתך (בהסכמה בלבד)</li>
          <li style={S.li}>מידע מ-Google Maps — ציבורי, לבניית הדף</li>
          <li style={S.li}>לוגים טכניים — לצורכי אבחון ואבטחה</li>
        </ul>

        <h2 style={S.h2}>איך אנחנו משתמשים במידע</h2>
        <ul style={S.ul}>
          <li style={S.li}>בניית ועדכון דף עסקי אוטומטי</li>
          <li style={S.li}>שליחת הודעות WhatsApp לאישור ועדכונים</li>
          <li style={S.li}>שיפור השירות ואבטחת הפלטפורמה</li>
          <li style={S.li}>ציות לחוק ישראלי ו-GDPR</li>
        </ul>

        <h2 style={S.h2}>שיתוף מידע</h2>
        <p style={S.p}>
          אנו <strong style={{ color: '#e2e8f0' }}>לא מוכרים</strong> מידע אישי לצדדים שלישיים.
          מידע משותף רק עם ספקי שירות הכרחיים (Google, Twilio, Meta) לצורך פעילות הפלטפורמה.
        </p>

        <h2 style={S.h2}>אחסון ואבטחה</h2>
        <p style={S.p}>
          המידע מאוחסן בשרתים מאובטחים בישראל ובאירופה. אנחנו משתמשים בהצפנה SSL/TLS.
          אחסון מינימלי — רק מה שנחוץ לפעילות השירות.
        </p>

        <h2 style={S.h2}>זכויותיך</h2>
        <ul style={S.ul}>
          <li style={S.li}>גישה למידע שלך</li>
          <li style={S.li}>תיקון מידע לא מדויק</li>
          <li style={S.li}>מחיקת כל המידע שלך — <a href="https://tazo-app.com/data-deletion" style={{ color: '#f59e0b' }}>לחץ כאן</a></li>
          <li style={S.li}>התנגדות לעיבוד מסוים</li>
        </ul>

        <h2 style={S.h2}>צור קשר</h2>
        <p style={S.p}>
          Email: <a href="mailto:ar.2110@gmail.com" style={{ color: '#f59e0b' }}>ar.2110@gmail.com</a><br />
          WhatsApp / טלפון: <a href="tel:+972546363350" style={{ color: '#f59e0b' }}>+972-54-6363350</a>
        </p>

        <hr style={S.sep} />
        <p style={{ ...S.p, fontSize: 11, color: '#334155' }}>
          © 2026 TAZO | אריאל אביב, עוסק פטור 040978207 |{' '}
          <a href="/terms" style={{ color: '#475569' }}>תנאי שימוש</a>
        </p>
      </div>
    </main>
  )
}
