const CACHE_NAME = 'carlostech-v3';
const CACHE_STATIC = 'carlostech-static-v3';

const PRECACHE = [
  '/static/style.css',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/mathquill@0.10.1/build/mathquill.css',
  'https://cdn.jsdelivr.net/npm/mathquill@0.10.1/build/mathquill.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_STATIC)
      .then(cache => cache.addAll(PRECACHE).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys
        .filter(k => k !== CACHE_NAME && k !== CACHE_STATIC)
        .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // API calls → network-first, sin caché
  if (url.pathname.startsWith('/api/')) {
    e.respondWith(
      fetch(e.request).catch(() =>
        new Response(JSON.stringify({
          success: false,
          error: 'Sin conexión. Conéctate a internet para resolver expresiones.',
          offline: true,
          steps: []
        }), { headers: { 'Content-Type': 'application/json' } })
      )
    );
    return;
  }

  // Páginas HTML → siempre network-first, nunca cachear redirecciones
  if (e.request.destination === 'document' || e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request));
    return;
  }

  // CDNs grandes → network-first con fallback a caché
  if (url.hostname.includes('cdn.plot.ly') || url.hostname.includes('mathjax')) {
    e.respondWith(
      fetch(e.request)
        .then(res => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
          }
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // Estáticos → cache-first, solo cachear respuestas 200
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(res => {
        if (res && res.status === 200 && res.type !== 'opaque') {
          const clone = res.clone();
          caches.open(CACHE_STATIC).then(c => c.put(e.request, clone));
        }
        return res;
      });
    })
  );
});
