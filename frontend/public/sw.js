const CACHE_NAME = 'metos-v1';
const OFFLINE_URLS = ['/', '/manifest.json'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_URLS)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request).then((cached) => cached || caches.match('/')))
  );
});

self.addEventListener('push', (event) => {
  let data = { title: 'Metabolic OS', body: 'Discipline Active.', payload: {} };
  try {
    data = { ...data, ...(event.data?.json() || {}) };
  } catch {}

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icons/icon-192.svg',
      badge: '/icons/icon-192.svg',
      data: data.payload || {},
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow('/'));
});

self.addEventListener('sync', (event) => {
  if (event.tag !== 'hydration-sync') return;
  event.waitUntil(
    clients.matchAll({ includeUncontrolled: true, type: 'window' }).then((clientList) => {
      for (const client of clientList) {
        client.postMessage({ type: 'HYDRATION_SYNC_REQUEST' });
      }
    })
  );
});
