import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/tazo-tokens.css';
import './styles.css';

// ── PWA Update Toast ────────────────────────────────────────────────
function showUpdateToast() {
  const existing = document.getElementById('tazo-web-update-toast')
  if (existing) return
  const toast = document.createElement('div')
  toast.id = 'tazo-web-update-toast'
  Object.assign(toast.style, {
    position:'fixed', bottom:'24px', right:'12px', left:'12px',
    maxWidth:'420px', margin:'0 auto',
    background:'linear-gradient(135deg,#1a0a00,#0d0d0d)',
    border:'1px solid rgba(255,107,0,0.4)', borderRadius:'16px',
    padding:'14px 18px', display:'flex', alignItems:'center', gap:'12px',
    boxShadow:'0 8px 32px rgba(255,107,0,0.25)',
    zIndex:'99999', direction:'rtl',
    fontFamily:"'Rubik','Heebo',sans-serif",
    animation:'tzSlideUp 0.35s cubic-bezier(0.34,1.56,0.64,1)',
  })
  toast.innerHTML = `
    <style>@keyframes tzSlideUp{from{transform:translateY(80px);opacity:0}to{transform:translateY(0);opacity:1}}</style>
    <span style="font-size:22px;flex-shrink:0">🔄</span>
    <div style="flex:1">
      <div style="color:#fff;font-weight:700;font-size:14px">גרסה חדשה זמינה!</div>
      <div style="color:rgba(255,255,255,0.55);font-size:12px">TAZO-WEB עודכן</div>
    </div>
    <button id="tazo-web-update-btn" style="background:#FF6B00;color:#fff;border:none;border-radius:20px;padding:8px 18px;font-weight:800;font-size:13px;cursor:pointer;flex-shrink:0;font-family:inherit">עדכן</button>
    <button id="tazo-web-update-close" style="background:none;border:none;color:rgba(255,255,255,0.4);font-size:20px;cursor:pointer;flex-shrink:0">×</button>
  `
  document.body.appendChild(toast)
  document.getElementById('tazo-web-update-btn')?.addEventListener('click', () => window.location.reload())
  document.getElementById('tazo-web-update-close')?.addEventListener('click', () => toast.remove())
  setTimeout(() => toast.remove(), 30000)
}

// ── Service Worker Registration ─────────────────────────────────────
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then(reg => {
      if (reg.waiting) showUpdateToast()
      reg.addEventListener('updatefound', () => {
        const nw = reg.installing
        if (!nw) return
        nw.addEventListener('statechange', () => {
          if (nw.state === 'installed' && navigator.serviceWorker.controller) showUpdateToast()
        })
      })
      let refreshing = false
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) { refreshing = true; window.location.reload() }
      })
    }).catch(() => {})
  })
}

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
