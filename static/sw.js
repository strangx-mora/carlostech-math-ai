const CACHE_NAME = 'carlostech-v1';
const CACHE_STATIC = 'carlostech-static-v1';

// Assets que se cachean al instalar
const PRECACHE = [
  '/',
  '/app',
  '/login',
  '/static/style.css',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/mathquill@0.10.1/build/mathquill.css',
  'https://cdn.jsdelivr.net/npm/mathquill@0.10.1/build/mathquill.js',
  'https://ajax.googleapis.com/ajax/libs/jquery/1.11.0/jquery.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
];

// Instalar: pre-cachear assets críticos
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_STATIC)
      .then(cache => cache.addAll(PRECACHE).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

// Activar: limpiar caches viejos
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

// Fetch: estrategia según tipo de request
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // API calls → network-first, sin caché (siempre frescos)
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

  // Plotly y MathJax son muy grandes → network-first con fallback a caché
  if (url.hostname.includes('cdn.plot.ly') || url.hostname.includes('cdn.jsdelivr.net/npm/mathjax')) {
    e.respondWith(
      fetch(e.request)
        .then(res => {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // Todo lo demás → cache-first
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(res => {
        if (!res || res.status !== 200 || res.type === 'opaque') return res;
        const clone = res.clone();
        caches.open(CACHE_STATIC).then(c => c.put(e.request, clone));
        return res;
      }).catch(() => {
        // Fallback offline para páginas HTML
        if (e.request.destination === 'document') {
          return caches.match('/app') || caches.match('/');
        }
      });
    })
  );
});
