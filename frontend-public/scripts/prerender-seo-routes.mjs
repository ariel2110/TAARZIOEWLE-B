import fs from 'node:fs'
import path from 'node:path'

const distDir = path.resolve('dist')
const indexPath = path.join(distDir, 'index.html')

if (!fs.existsSync(indexPath)) {
  throw new Error('dist/index.html not found. Run vite build first.')
}

const baseHtml = fs.readFileSync(indexPath, 'utf8')

const ROUTES = [
  {
    route: '/',
    title: 'TAZO Web - בניית אתר AI לעסק מקומי תוך דקות ובקלות',
    description: 'TAZO Web מאפשרת לעסקים מקומיים לבנות אתר מקצועי עם AI תוך דקות, לפרסם שירותים ומוצרים, ולמשוך לקוחות חדשים דרך חוויית דיגיטל מהירה ופשוטה.',
    h1: 'TAZO Web - בניית אתר AI לעסק מקומי תוך דקות ובקלות',
    p: 'פלטפורמה חכמה לעסקים מקומיים לבניית אתר מקצועי, ניהול נוכחות דיגיטלית והגדלת חשיפה אונליין.',
  },
  {
    route: '/business',
    title: 'TAZO Web לעסקים - הגדלת חשיפה דיגיטלית עם אתר חכם ומהיר',
    description: 'הפתרון של TAZO Web לעסקים מקומיים: אתר חכם, תשתית שיווק דיגיטלית ותהליך הצטרפות מהיר שמייצר נוכחות ברשת ומניע צמיחה עסקית.',
    h1: 'TAZO Web לעסקים - הגדלת חשיפה דיגיטלית עם אתר חכם ומהיר',
    p: 'פתרון דיגיטלי לעסקים מקומיים עם הצטרפות מהירה ותשתית שיווקית לצמיחה.',
  },
  {
    route: '/about',
    title: 'אודות TAZO Web - פלטפורמת AI לבניית אתרים לעסקים בישראל',
    description: 'למד על TAZO Web, החזון, הטכנולוגיה והשירותים שמסייעים לעסקים בישראל להשיג נוכחות דיגיטלית איכותית עם בניית אתר חכמה ומהירה.',
    h1: 'אודות TAZO Web - פלטפורמת AI לבניית אתרים לעסקים בישראל',
    p: 'החזון והטכנולוגיה שמאפשרים לעסקים בישראל לבנות אתר במהירות ובאיכות גבוהה.',
  },
  {
    route: '/start',
    title: 'פתיחת אתר ב-TAZO Web - טופס הצטרפות מהיר לעסקים מקומיים',
    description: 'התחל את תהליך ההצטרפות ל-TAZO Web עם טופס קצר ופשוט, וקבל אתר עסקי מקצועי המבוסס AI שמוכן לפרסום ולהבאת לקוחות חדשים.',
    h1: 'פתיחת אתר ב-TAZO Web - טופס הצטרפות מהיר לעסקים מקומיים',
    p: 'מלא פרטים בטופס קצר והתחל תהליך מהיר לבניית אתר עסקי חכם.',
  },
]

function escapeAttr(value) {
  return value.replaceAll('&', '&amp;').replaceAll('"', '&quot;')
}

function escapeHtml(value) {
  return value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
}

function applySeo(html, config) {
  const canonical = `https://tazo-web.com${config.route}`
  let out = html

  out = out.replace(/<title>[\s\S]*?<\/title>/i, `<title>${escapeHtml(config.title)}</title>`)
  out = out.replace(
    /<meta\s+name="description"\s+content="[^"]*"\s*\/?>(?:\s*)/i,
    `<meta name="description" content="${escapeAttr(config.description)}" />\n`,
  )
  out = out.replace(
    /<link\s+rel="canonical"\s+href="[^"]*"\s*\/?>(?:\s*)/i,
    `<link rel="canonical" href="${canonical}" />\n`,
  )
  out = out.replace(/<main>[\s\S]*?<\/main>/i, `<main>\n      <h1>${escapeHtml(config.h1)}</h1>\n      <p>${escapeHtml(config.p)}</p>\n    </main>`)
  return out
}

for (const route of ROUTES) {
  const html = applySeo(baseHtml, route)
  if (route.route === '/') {
    fs.writeFileSync(indexPath, html, 'utf8')
    continue
  }

  const outputDir = path.join(distDir, route.route.replace(/^\//, ''))
  fs.mkdirSync(outputDir, { recursive: true })
  fs.writeFileSync(path.join(outputDir, 'index.html'), html, 'utf8')
}

console.log(`prerendered ${ROUTES.length} routes for frontend-public`)
