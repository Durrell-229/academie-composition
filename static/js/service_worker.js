const CACHE_NAME = 'academie-numerique-v1';
const STATIC_ASSETS = [
  '/accueil/',
  '/static/img/logo.png',
  '/static/img/logo_small.png',
];

// Installation : mise en cache des assets statiques
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activation : nettoyage des anciens caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch : stratégie Network-first avec fallback cache
self.addEventListener('fetch', event => {
  // Ne pas intercepter les requêtes non-GET ni les API
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/api/') || event.request.url.includes('/admin/')) return;

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Mettre en cache les réponses réussies
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => {
        // Réseau indisponible : servir depuis le cache
        return caches.match(event.request).then(cached => {
          if (cached) return cached;
          // Page hors-ligne de fallback
          if (event.request.destination === 'document') {
            return caches.match('/accueil/');
          }
        });
      })
  );
});
