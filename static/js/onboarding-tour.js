/* ============================================================
   URBIX — onboarding-tour.js
   Tour de bienvenida para usuarios nuevos. Se muestra una sola vez
   (se guarda en localStorage) la primera vez que entran a "Inicio".
   ============================================================ */

(function(){
  const STEPS = [
    { icon: 'bi-house-door', title: '¡Bienvenido a URBIX!', text: 'Te ayudamos a moverte por Popayán en bus, encontrar lugares y planificar tu viaje. Este tour dura 30 segundos.' },
    { icon: 'bi-map', title: 'Mapa en tiempo real', text: 'En "Mapa" ves los buses moviéndose en vivo, coloreados por empresa (Transpubenza, Translibertad, Sotracauca, Transtambo).' },
    { icon: 'bi-signpost-2', title: 'Planifica tu viaje', text: 'Elige tu origen y destino en "Planificar viaje" y te mostramos la mejor ruta, directa o con transbordo.' },
    { icon: 'bi-stars', title: 'Buscador con IA', text: 'Escribe lo que buscas en lenguaje natural, como "algo económico para comer cerca del centro".' },
    { icon: 'bi-command', title: 'Atajo rápido', text: 'Presiona Ctrl + K en cualquier momento para saltar a cualquier parte de la app sin usar el mouse.' },
  ];

  function shouldShowTour(){
    return localStorage.getItem('urbix-tour-done') !== '1';
  }

  function markDone(){
    localStorage.setItem('urbix-tour-done', '1');
  }

  function buildOverlay(){
    let step = 0;
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay open';
    overlay.id = 'onboardingOverlay';

    function render(){
      const s = STEPS[step];
      overlay.innerHTML = `
        <div class="modal-box glass" style="max-width:420px;text-align:center;">
          <i class="bi ${s.icon}" style="font-size:2.2rem;color:var(--neon);"></i>
          <h3 style="margin:14px 0 8px;">${s.title}</h3>
          <p class="text-dim" style="font-size:.9rem;">${s.text}</p>
          <div class="progress-dots" style="justify-content:center;margin:18px 0;">
            ${STEPS.map((_, i) => `<span class="${i===step?'active':''}"></span>`).join('')}
          </div>
          <div style="display:flex;gap:10px;">
            <button class="btn btn-ghost btn-block" id="tourSkip">Saltar</button>
            <button class="btn btn-primary btn-block" id="tourNext">${step === STEPS.length-1 ? 'Empezar' : 'Siguiente'}</button>
          </div>
        </div>`;
      document.getElementById('tourSkip').onclick = closeTour;
      document.getElementById('tourNext').onclick = () => {
        if(step < STEPS.length - 1){ step++; render(); }
        else closeTour();
      };
    }

    function closeTour(){
      markDone();
      overlay.remove();
    }

    render();
    document.body.appendChild(overlay);
  }

  document.addEventListener('DOMContentLoaded', () => {
    if(document.body.dataset.tourEligible === '1' && shouldShowTour()){
      setTimeout(buildOverlay, 600);
    }
  });

  // Permite relanzar el tour manualmente desde Configuración
  window.urbixRestartTour = function(){
    localStorage.removeItem('urbix-tour-done');
    buildOverlay();
  };
})();
