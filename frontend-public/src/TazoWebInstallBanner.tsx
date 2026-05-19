import { useState, useEffect } from 'react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const DISMISSED_KEY = 'tazo-web-pwa-dismissed'
const TTL = 30 * 24 * 60 * 60 * 1000

function isDismissed() {
  try {
    const v = localStorage.getItem(DISMISSED_KEY)
    if (!v) return false
    return Date.now() - JSON.parse(v).ts < TTL
  } catch { return false }
}

function isStandalone() {
  return window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as { standalone?: boolean }).standalone === true
}

function isIos() {
  return /iphone|ipad|ipod/i.test(navigator.userAgent)
}

export default function TazoWebInstallBanner() {
  const [prompt, setPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [showIos, setShowIos] = useState(false)
  const [gone, setGone] = useState(false)

  useEffect(() => {
    if (isStandalone() || isDismissed()) return

    const handler = (e: Event) => { e.preventDefault(); setPrompt(e as BeforeInstallPromptEvent) }
    window.addEventListener('beforeinstallprompt', handler)

    if (isIos()) {
      const t = setTimeout(() => setShowIos(true), 4000)
      return () => { window.removeEventListener('beforeinstallprompt', handler); clearTimeout(t) }
    }
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  const dismiss = () => {
    setGone(true)
    localStorage.setItem(DISMISSED_KEY, JSON.stringify({ ts: Date.now() }))
  }

  const install = async () => {
    if (!prompt) return
    await prompt.prompt()
    await prompt.userChoice
    dismiss()
  }

  if (gone || isStandalone()) return null

  if (prompt) return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 9999,
      background: 'linear-gradient(135deg,#1a0a00,#0d0d0d)',
      borderTop: '1px solid rgba(255,107,0,0.35)',
      padding: '14px 20px', display: 'flex', alignItems: 'center', gap: 14,
      boxShadow: '0 -4px 32px rgba(255,107,0,0.18)',
      backdropFilter: 'blur(12px)', direction: 'rtl',
      fontFamily: "'Rubik','Heebo',sans-serif",
    }}>
      <div style={{
        minWidth: 44, height: 44, borderRadius: 12, flexShrink: 0,
        background: '#FF6B00', display: 'flex', alignItems: 'center',
        justifyContent: 'center', fontWeight: 900, fontSize: 18, color: '#fff',
      }}>W</div>
      <div style={{ flex: 1 }}>
        <div style={{ color: '#fff', fontWeight: 700, fontSize: '0.9rem' }}>הוסף TAZO-WEB לדף הבית</div>
        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.76rem' }}>בנה אתרים ישירות מהאפליקציה</div>
      </div>
      <button onClick={install} style={{
        background: '#FF6B00', color: '#fff', border: 'none', borderRadius: 22,
        padding: '9px 22px', fontWeight: 800, fontSize: '0.85rem', cursor: 'pointer',
        flexShrink: 0, whiteSpace: 'nowrap', fontFamily: 'inherit',
        boxShadow: '0 4px 16px rgba(255,107,0,0.4)',
      }}>התקן</button>
      <button onClick={dismiss} aria-label="סגור" style={{
        background: 'none', border: 'none', color: 'rgba(255,255,255,0.4)',
        fontSize: '1.3rem', cursor: 'pointer', flexShrink: 0,
      }}>×</button>
    </div>
  )

  if (showIos) return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
    }} onClick={dismiss}>
      <div style={{
        background: 'linear-gradient(160deg,#1a0a00,#0d0d0d)',
        borderRadius: '24px 24px 0 0', border: '1px solid rgba(255,107,0,0.25)',
        padding: '28px 24px 44px', width: '100%', maxWidth: 480,
        fontFamily: "'Rubik','Heebo',sans-serif", direction: 'rtl',
      }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 }}>
          <div style={{
            width: 52, height: 52, borderRadius: 14, background: '#FF6B00',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 900, fontSize: 22, color: '#fff',
          }}>W</div>
          <div>
            <div style={{ color: '#fff', fontWeight: 800, fontSize: '1.05rem' }}>TAZO-WEB</div>
            <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.8rem' }}>הוסף לדף הבית</div>
          </div>
          <button onClick={dismiss} style={{
            marginRight: 'auto', background: 'rgba(255,255,255,0.08)', border: 'none',
            borderRadius: '50%', width: 30, height: 30, color: 'rgba(255,255,255,0.6)',
            fontSize: '1.1rem', cursor: 'pointer', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
          }}>×</button>
        </div>
        {[
          { n: '1', icon: '⬆️', t: 'לחץ על כפתור השיתוף', s: 'בתחתית Safari' },
          { n: '2', icon: '📌', t: 'בחר "הוסף למסך הבית"', s: 'גלול למטה ברשימה' },
          { n: '3', icon: '✅', t: 'אשר עם "הוסף"', s: 'בפינה הימנית עליונה' },
        ].map(step => (
          <div key={step.n} style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
            <div style={{
              width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
              background: 'rgba(255,107,0,0.2)', border: '1.5px solid rgba(255,107,0,0.6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#FF6B00', fontWeight: 700, fontSize: '0.95rem',
            }}>{step.n}</div>
            <div>
              <div style={{ color: '#fff', fontSize: '0.9rem', fontWeight: 600 }}>
                {step.icon} {step.t}
              </div>
              <div style={{ color: 'rgba(255,255,255,0.45)', fontSize: '0.76rem' }}>{step.s}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )

  return null
}
