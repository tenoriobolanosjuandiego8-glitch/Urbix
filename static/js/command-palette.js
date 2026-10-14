/* ============================================================
   URBIX — command-palette.js
   Paleta de comandos estilo VS Code (Ctrl+K / Cmd+K).
   Navegación rápida por toda la app sin usar el mouse.
   ============================================================ */

(function(){
  const COMMANDS = [
    { label: 'Inicio', icon: 'bi-house-door', url: '/dashboard/inicio/' },
    { label: 'Mapa', icon: 'bi-map', url: '/mapa/' },
    { label: 'Rutas', icon: 'bi-signpost-split', url: '/rutas/' },
    { label: 'Horarios', icon: 'bi-clock-history', url: '/rutas/horarios/' },
    { label: 'Paraderos', icon: 'bi-geo-alt', url: '/rutas/paraderos/' },
    { label: 'Empresas', icon: 'bi-bus-front', url: '/rutas/empresas/' },
    { label: 'Comparar rutas', icon: 'bi-bar-chart-steps', url: '/rutas/comparar/' },
    { label: 'Planificar viaje', icon: 'bi-signpost-2', url: '/rutas/planificador/' },
    { label: 'Restaurantes', icon: 'bi-cup-hot', url: '/restaurantes/' },
    { label: 'Hoteles', icon: 'bi-building', url: '/hoteles/' },
    { label: 'Turismo', icon: 'bi-camera', url: '/turismo/' },
    { label: 'Eventos', icon: 'bi-calendar-event', url: '/eventos/' },
    { label: 'Centro Empresarial', icon: 'bi-shop', url: '/empresas-urbix/' },
    { label: 'Favoritos', icon: 'bi-heart', url: '/interacciones/favoritos/' },
    { label: 'Historial', icon: 'bi-clock-history', url: '/interacciones/historial/' },
    { label: 'Buscador con IA', icon: 'bi-stars', url: '/asistente/buscar/' },
    { label: 'Notificaciones', icon: 'bi-bell', url: '/notificaciones/' },
    { label: 'Perfil', icon: 'bi-person', url: '/cuenta/perfil/' },
    { label: 'Configuración', icon: 'bi-gear', url: '/dashboard/configuracion/' },
    { label: 'Contactos de emergencia', icon: 'bi-shield-exclamation', url: '/cuenta/contactos-emergencia/' },
    { label: 'Botón SOS', icon: 'bi-exclamation-triangle-fill', url: '/cuenta/sos/' },
    { label: 'Centro de ayuda', icon: 'bi-question-circle', url: '/dashboard/ayuda/' },
    { label: 'Novedades', icon: 'bi-megaphone', url: '/dashboard/novedades/' },
    { label: 'Estadísticas (admin)', icon: 'bi-bar-chart', url: '/dashboard/administrador/estadisticas/' },
    { label: 'Auditoría (admin)', icon: 'bi-journal-check', url: '/dashboard/administrador/auditoria/' },
    { label: 'Panel de negocio', icon: 'bi-speedometer2', url: '/empresas-urbix/panel/' },
    { label: 'Cerrar sesión', icon: 'bi-box-arrow-right', url: '/cuenta/logout/' },
  ];

  function buildPalette(){
    const overlay = document.createElement('div');
    overlay.id = 'cmdPaletteOverlay';
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal-box glass" style="max-width:520px;padding:0;">
        <div style="display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid var(--border);">
          <i class="bi bi-search text-dim"></i>
          <input type="text" id="cmdPaletteInput" placeholder="Ir a..." autocomplete="off"
                 style="border:none;background:transparent;flex:1;font-size:.95rem;padding:6px 0;">
          <span class="badge" style="font-size:.68rem;">Esc</span>
        </div>
        <div id="cmdPaletteList" style="max-height:340px;overflow-y:auto;padding:8px;"></div>
      </div>`;
    document.body.appendChild(overlay);
    return overlay;
  }

  function renderList(listEl, query){
    const q = query.trim().toLowerCase();
    const matches = COMMANDS.filter(c => c.label.toLowerCase().includes(q));
    listEl.innerHTML = matches.map((c, i) => `
      <a href="${c.url}" class="cmd-item ${i===0?'active':''}" style="display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:10px;color:var(--text-hi);text-decoration:none;">
        <i class="bi ${c.icon}" style="color:var(--neon);width:20px;"></i>${c.label}
      </a>`).join('') || `<div class="empty-state" style="padding:24px;"><i class="bi bi-emoji-frown"></i>Sin resultados</div>`;
  }

  let overlay = null;
  function openPalette(){
    if(!overlay) overlay = buildPalette();
    overlay.classList.add('open');
    const input = document.getElementById('cmdPaletteInput');
    const list = document.getElementById('cmdPaletteList');
    renderList(list, '');
    input.value = '';
    setTimeout(() => input.focus(), 50);

    input.oninput = () => renderList(list, input.value);
    input.onkeydown = (e) => {
      const items = [...list.querySelectorAll('.cmd-item')];
      const activeIdx = items.findIndex(i => i.classList.contains('active'));
      if(e.key === 'ArrowDown'){ e.preventDefault(); setActive(items, Math.min(activeIdx+1, items.length-1)); }
      if(e.key === 'ArrowUp'){ e.preventDefault(); setActive(items, Math.max(activeIdx-1, 0)); }
      if(e.key === 'Enter'){ const active = items[activeIdx] || items[0]; if(active) window.location.href = active.getAttribute('href'); }
    };
    overlay.onclick = (e) => { if(e.target === overlay) closePalette(); };
  }
  function setActive(items, idx){
    items.forEach(i => i.classList.remove('active'));
    if(items[idx]){ items[idx].classList.add('active'); items[idx].style.background='var(--surface-strong)'; items[idx].scrollIntoView({block:'nearest'}); }
  }
  function closePalette(){ if(overlay) overlay.classList.remove('open'); }

  document.addEventListener('keydown', (e) => {
    if((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k'){
      e.preventDefault();
      openPalette();
    }
    if(e.key === 'Escape') closePalette();
  });

  // Estilo del item activo vía CSS inline dinámico (evita depender de :hover del mouse)
  const style = document.createElement('style');
  style.textContent = `.cmd-item:hover, .cmd-item.active{ background:var(--surface-strong); }`;
  document.head.appendChild(style);
})();
