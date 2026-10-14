// URBIX — Service Worker
// Recibe las notificaciones push del servidor y las muestra aunque
// la app no esté abierta en el navegador.

self.addEventListener('push', (event) => {
  let data = { title: 'URBIX', body: 'Tienes una notificación nueva.', url: '/notificaciones/' };
  try { data = event.data.json(); } catch (e) {}

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/static/images/urbix-logo.jpg',
      badge: '/static/images/urbix-logo.jpg',
      data: { url: data.url || '/notificaciones/' },
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data.url || '/notificaciones/'));
});
