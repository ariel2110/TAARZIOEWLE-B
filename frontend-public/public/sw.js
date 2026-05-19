// TAZO-WEB — Service Worker v1
const CACHE_NAME   = 'tazo-web-v1'
const STATIC_CACHE = 'tazo-web-static-v1'
const API_CACHE    = 'tazo-web-api-v1'

const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/favicon.svg',
  '/site.webmanifest',
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then(names => Promise.all(
        names
          .filter(n => n !== STATIC_CACHE && n !== API_CACHE)
          .map(n => caches.delete(n))
      ))
      .then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  if (request.method !== 'GET') return
  if (url.origin !== self.location.origin && !url.hostname.includes('fonts.g')) return

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then(res => {
          if (res.ok) {
            const clone = res.clone()
            caches.open(API_CACHE).then(c => c.put(request, clone))
          }
          return res
        })
        .catch(() => caches.match(request))
    )
    return
  }

  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/index.html')))
    return
  }

  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached
      return fetch(request).then(res => {
        if (res.ok && res.type !== 'opaque') {
          const clone = res.clone()
          caches.open(STATIC_CACHE).then(c => c.put(request, clone))
        }
        return res
      })
    })
  )
})
