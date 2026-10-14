/* ============================================================
   URBIX — push-notifications.js
   Activa las notificaciones push reales del navegador (Web Push API).
   Si el proyecto no tiene VAPID_PUBLIC_KEY configurada, el botón
   simplemente explica que falta activarlo — no rompe nada.
   ============================================================ */

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
}

function getCookie(name){
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return match ? match.pop() : '';
}

async function enablePushNotifications(vapidPublicKey){
  if(!('serviceWorker' in navigator) || !('PushManager' in window)){
    Components.toast('Tu navegador no soporta notificaciones push.', 'error');
    return;
  }
  if(!vapidPublicKey){
    Components.toast('Las notificaciones push aún no están activadas por el administrador.', 'error');
    return;
  }
  try {
    const registration = await navigator.serviceWorker.register('/sw.js');
    const permission = await Notification.requestPermission();
    if(permission !== 'granted'){
      Components.toast('No diste permiso de notificaciones.', 'error');
      return;
    }
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
    });
    await fetch('/notificaciones/push/suscribir/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify(subscription),
    });
    Components.toast('¡Notificaciones activadas!');
    localStorage.setItem('urbix-push-enabled', '1');
  } catch(err){
    Components.toast('No se pudo activar: ' + err.message, 'error');
  }
}
