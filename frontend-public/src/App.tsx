import { lazy, Suspense, useEffect, useState } from 'react';
import Sidebar from './Sidebar'
import TazoWebInstallBanner from './TazoWebInstallBanner';
import './styles.css';

const Marketplace = lazy(() => import('./Marketplace'))
const MagicPortal = lazy(() => import('./MagicPortal'))
const LandingExtra = lazy(() => import('./LandingExtra'))
const IntakeForm = lazy(() => import('./IntakeForm'))
const SubmissionStatus = lazy(() => import('./SubmissionStatus'))
const About = lazy(() => import('./About'))
const Privacy = lazy(() => import('./Privacy'))
const Terms = lazy(() => import('./Terms'))

const PageFallback = () => (
  <div style={{ minHeight: '40vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94A3B8' }}>
    טוען...
  </div>
)

const SEO_BY_PAGE: Record<AppPage, { title: string; description: string }> = {
  marketplace: {
    title: 'TAZO Web - בניית אתר AI לעסק מקומי תוך דקות ובקלות',
    description: 'TAZO Web מאפשרת לעסקים מקומיים לבנות אתר מקצועי עם AI תוך דקות, לפרסם שירותים ומוצרים, ולמשוך לקוחות חדשים דרך חוויית דיגיטל מהירה ופשוטה.',
  },
  home: {
    title: 'TAZO Web לעסקים - הגדלת חשיפה דיגיטלית עם אתר חכם ומהיר',
    description: 'הפתרון של TAZO Web לעסקים מקומיים: אתר חכם, תשתית שיווק דיגיטלית ותהליך הצטרפות מהיר שמייצר נוכחות ברשת ומניע צמיחה עסקית.',
  },
  intake: {
    title: 'פתיחת אתר ב-TAZO Web - טופס הצטרפות מהיר לעסקים מקומיים',
    description: 'התחל את תהליך ההצטרפות ל-TAZO Web עם טופס קצר ופשוט, וקבל אתר עסקי מקצועי המבוסס AI שמוכן לפרסום ולהבאת לקוחות חדשים.',
  },
  status: {
    title: 'סטטוס יצירת אתר ב-TAZO Web - מעקב התקדמות בזמן אמת לעסק',
    description: 'עקוב אחר התקדמות הקמת האתר שלך ב-TAZO Web בזמן אמת, וקבל שקיפות מלאה על מצב הבקשה, שלבי העיבוד והעלייה לאוויר של האתר העסקי.',
  },
  about: {
    title: 'אודות TAZO Web - פלטפורמת AI לבניית אתרים לעסקים בישראל',
    description: 'למד על TAZO Web, החזון, הטכנולוגיה והשירותים שמסייעים לעסקים בישראל להשיג נוכחות דיגיטלית איכותית עם בניית אתר חכמה ומהירה.',
  },
};

function upsertCanonical() {
  let canonical = document.querySelector('link[rel="canonical"]') as HTMLLinkElement | null
  if (!canonical) {
    canonical = document.createElement('link')
    canonical.rel = 'canonical'
    document.head.appendChild(canonical)
  }
  canonical.href = `${window.location.origin}${window.location.pathname}`
}

function upsertJsonLd(id: string, payload: unknown) {
  let script = document.getElementById(id) as HTMLScriptElement | null
  if (!script) {
    script = document.createElement('script')
    script.type = 'application/ld+json'
    script.id = id
    document.head.appendChild(script)
  }
  script.text = JSON.stringify(payload)
}

export type AppPage = 'marketplace' | 'home' | 'intake' | 'status' | 'about' | 'privacy' | 'terms';

function normalizePath(pathname: string): string {
  const stripped = pathname.replace(/\/+$/, '')
  return stripped || '/'
}

function parseRouteFromLocation() {
  const hash = window.location.hash
  const path = normalizePath(window.location.pathname)

  if (hash.startsWith('#/status/')) {
    return { page: 'status' as AppPage, token: hash.replace('#/status/', ''), category: undefined as string | undefined }
  }
  if (path.startsWith('/status/')) {
    return { page: 'status' as AppPage, token: path.replace('/status/', ''), category: undefined as string | undefined }
  }
  if (hash === '#/start' || path === '/start') {
    return { page: 'intake' as AppPage, token: '', category: undefined as string | undefined }
  }
  if (hash === '#/business' || path === '/business') {
    return { page: 'home' as AppPage, token: '', category: undefined as string | undefined }
  }
  if (hash === '#/about' || path === '/about') {
    return { page: 'about' as AppPage, token: '', category: undefined as string | undefined }
  }
  if (path === '/privacy' || path === '/privacy/') {
    return { page: 'privacy' as AppPage, token: '', category: undefined as string | undefined }
  }
  if (path === '/terms' || path === '/terms/') {
    return { page: 'terms' as AppPage, token: '', category: undefined as string | undefined }
  }

  const hashCategory = hash.match(/^#\/category\/([^/]+)/)
  if (hashCategory) {
    return { page: 'marketplace' as AppPage, token: '', category: hashCategory[1] }
  }
  const pathCategory = path.match(/^\/category\/([^/]+)/)
  if (pathCategory) {
    return { page: 'marketplace' as AppPage, token: '', category: pathCategory[1] }
  }

  return { page: 'marketplace' as AppPage, token: '', category: undefined as string | undefined }
}

export default function App() {
  const [page, setPage] = useState<AppPage>(() => parseRouteFromLocation().page);
  const [statusToken, setStatusToken] = useState<string>(() => parseRouteFromLocation().token);
  const [selectedPlan, setSelectedPlan] = useState<string | undefined>(undefined);
  const [jumpCategory, setJumpCategory] = useState<string | undefined>(() => parseRouteFromLocation().category);

  useEffect(() => {
    const syncFromLocation = () => {
      const parsed = parseRouteFromLocation()
      setPage(parsed.page)
      setStatusToken(parsed.token)
      setJumpCategory(parsed.category)
    }

    window.addEventListener('popstate', syncFromLocation)
    window.addEventListener('hashchange', syncFromLocation)
    return () => {
      window.removeEventListener('popstate', syncFromLocation)
      window.removeEventListener('hashchange', syncFromLocation)
    }
  }, [])

  function navigatePath(path: string) {
    if (normalizePath(window.location.pathname) !== path) {
      window.history.pushState(null, '', path)
    }
  }

  useEffect(() => {
    const seo = SEO_BY_PAGE[page]
    document.title = seo.title
    let desc = document.querySelector('meta[name="description"]') as HTMLMetaElement | null
    if (!desc) {
      desc = document.createElement('meta')
      desc.name = 'description'
      document.head.appendChild(desc)
    }
    desc.content = seo.description

    upsertCanonical()

    upsertJsonLd('tazo-web-org-jsonld', {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: 'TAZO Web',
      url: 'https://tazo-web.com',
      logo: 'https://tazo-web.com/android-chrome-192x192.png',
      sameAs: ['https://tazo-web.com'],
    })

    upsertJsonLd('tazo-web-website-jsonld', {
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      name: 'TAZO Web',
      url: 'https://tazo-web.com',
      inLanguage: 'he-IL',
    })
  }, [page]);

  function goToIntake(planName?: string) {
    navigatePath('/start')
    setSelectedPlan(planName);
    setPage('intake');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goToStatus(token: string) {
    navigatePath(`/status/${token}`)
    setStatusToken(token);
    setPage('status');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goHome() {
    navigatePath('/')
    setPage('marketplace');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goToBusinessLanding() {
    navigatePath('/business')
    setPage('home');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function handleGoTo(target: AppPage, categoryId?: string) {
    if (target === 'marketplace') {
      if (categoryId) {
        navigatePath(`/category/${categoryId}`)
        setJumpCategory(categoryId);
      } else {
        navigatePath('/')
        setJumpCategory(undefined);
      }
      setPage('marketplace');
    } else if (target === 'home') goToBusinessLanding();
    else if (target === 'intake') goToIntake(categoryId);
    else if (target === 'about') { navigatePath('/about'); setPage('about'); }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  if (page === 'about') {
    return (
      <>
        <Sidebar currentPage={page} onGoTo={handleGoTo} />
        <Suspense fallback={<PageFallback />}>
          <About />
        </Suspense>
      </>
    );
  }

  if (page === 'privacy') {
    return (
      <Suspense fallback={<PageFallback />}>
        <Privacy />
      </Suspense>
    );
  }

  if (page === 'terms') {
    return (
      <Suspense fallback={<PageFallback />}>
        <Terms />
      </Suspense>
    );
  }

  if (page === 'status') {
    return (
      <>
        <Sidebar currentPage={page} onGoTo={handleGoTo} />
        <Suspense fallback={<PageFallback />}>
          <SubmissionStatus token={statusToken} onBack={goHome} selectedPlan={selectedPlan} />
        </Suspense>
      </>
    );
  }

  if (page === 'intake') {
    return (
      <>
        <Sidebar currentPage={page} onGoTo={handleGoTo} />
        <Suspense fallback={<PageFallback />}>
          <IntakeForm onSubmitted={goToStatus} onBack={goHome} selectedPlan={selectedPlan} />
        </Suspense>
      </>
    );
  }

  if (page === 'home') {
    return (
      <>
        <Sidebar currentPage={page} onGoTo={handleGoTo} />
        <Suspense fallback={<PageFallback />}>
          <MagicPortal />
          <LandingExtra onStartIntake={goToIntake} />
        </Suspense>
      </>
    );
  }

  // Default: Marketplace
  return (
    <>
      <TazoWebInstallBanner />
      <Sidebar currentPage={page} onGoTo={handleGoTo} />
      <Suspense fallback={<PageFallback />}>
        <Marketplace onJoin={goToBusinessLanding} jumpCategory={jumpCategory} onClearJumpCategory={() => setJumpCategory(undefined)} />
      </Suspense>
    </>
  );
}
