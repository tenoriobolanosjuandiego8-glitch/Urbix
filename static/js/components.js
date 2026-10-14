/* ============================================================
   URBIX — components.js
   Genera Sidebar / Topbar / Footer / Notificaciones reutilizables
   e inyecta en cada página vía Components.init({...})
   ============================================================ */

const URBIX_MENUS = {
  usuario: [
    { icon:'bi-house-door', label:'Inicio', href:'principal.html', key:'inicio' },
    { icon:'bi-map', label:'Mapa', href:'mapa.html', key:'mapa' },
    { icon:'bi-signpost-split', label:'Rutas', href:'rutas.html', key:'rutas' },
    { icon:'bi-clock-history', label:'Horarios', href:'horarios.html', key:'horarios' },
    { icon:'bi-cup-hot', label:'Restaurantes', href:'restaurantes.html', key:'restaurantes' },
    { icon:'bi-building', label:'Hoteles', href:'hoteles.html', key:'hoteles' },
    { icon:'bi-camera', label:'Turismo', href:'turismo.html', key:'turismo' },
    { icon:'bi-calendar-event', label:'Eventos', href:'eventos.html', key:'eventos' },
    { icon:'bi-heart', label:'Favoritos', href:'favoritos.html', key:'favoritos' },
    { icon:'bi-person', label:'Perfil', href:'perfil.html', key:'perfil' },
    { icon:'bi-gear', label:'Configuración', href:'configuracion.html', key:'configuracion' },
  ],
  conductor: [
    { icon:'bi-map', label:'Mapa', href:'mapa.html', key:'mapa' },
    { icon:'bi-signpost-split', label:'Ruta asignada', href:'dashboard-conductor.html', key:'ruta-asignada' },
    { icon:'bi-bus-front', label:'Mi bus', href:'dashboard-conductor.html', key:'bus' },
    { icon:'bi-arrow-repeat', label:'Vueltas', href:'dashboard-conductor.html', key:'vueltas' },
    { icon:'bi-flag', label:'Estado del servicio', href:'dashboard-conductor.html', key:'estado' },
    { icon:'bi-file-earmark-text', label:'Reportes', href:'dashboard-conductor.html', key:'reportes' },
    { icon:'bi-person', label:'Perfil', href:'perfil.html', key:'perfil' },
  ],
  admin: [
    { icon:'bi-grid-1x2', label:'Dashboard', href:'dashboard-admin.html', key:'dashboard' },
    { icon:'bi-people', label:'Usuarios', href:'dashboard-admin.html', key:'usuarios' },
    { icon:'bi-person-badge', label:'Conductores', href:'dashboard-admin.html', key:'conductores' },
    { icon:'bi-bus-front', label:'Buses', href:'dashboard-admin.html', key:'buses' },
    { icon:'bi-signpost-split', label:'Rutas', href:'rutas.html', key:'rutas' },
    { icon:'bi-geo-alt', label:'Paraderos', href:'dashboard-admin.html', key:'paraderos' },
    { icon:'bi-file-earmark-bar-graph', label:'Reportes', href:'dashboard-admin.html', key:'reportes' },
    { icon:'bi-bar-chart', label:'Estadísticas', href:'dashboard-admin.html', key:'estadisticas' },
    { icon:'bi-gear', label:'Configuración', href:'configuracion.html', key:'configuracion' },
  ]
};

const Components = {

  init({ role = 'usuario', active = '', title = 'Panel' } = {}){
    this.injectSidebar(role, active);
    this.injectTopbar(title);
    this.injectFooter();
    this.wireGlobalEvents();
    this.revealOnScroll();
    this.applySavedTheme();
    this.applyAccessibilityPrefs();
  },

  injectSidebar(role, active){
    const root = document.getElementById('sidebar-root');
    if(!root) return;
    const menu = URBIX_MENUS[role] || URBIX_MENUS.usuario;
    const roleLabel = { usuario:'Cuenta usuario', conductor:'Panel conductor', admin:'Panel administrador' }[role];

    root.innerHTML = `
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-toggle" id="sidebarToggle"><i class="bi bi-chevron-left"></i></div>
      <div class="sidebar-head">
        <img src="assets/logo/urbix-logo.jpg" alt="Logo URBIX">
        <div class="brand">UR<span>BIX</span></div>
      </div>
      <div class="role-tag">${roleLabel}</div>
      <nav class="sidebar-nav">
        ${menu.map(item => `
          <a href="${item.href}" class="${item.key===active?'active':''}">
            <i class="bi ${item.icon}"></i><span>${item.label}</span>
          </a>`).join('')}
      </nav>
      <div class="sidebar-foot">
        <a href="index.html" id="logoutBtn"><i class="bi bi-box-arrow-right"></i><span>Cerrar sesión</span></a>
      </div>
    </aside>
    <div class="sidebar-overlay" id="sidebarOverlay"></div>`;
  },

  injectTopbar(title){
    const root = document.getElementById('topbar-root');
    if(!root) return;
    root.innerHTML = `
    <header class="topbar">
      <div class="topbar-left">
        <button class="icon-btn" id="mobileMenuBtn" aria-label="Abrir menú"><i class="bi bi-list"></i></button>
        <div>
          <span class="eyebrow">URBIX</span>
          <h2 style="margin:0;font-size:1.05rem;">${title}</h2>
        </div>
      </div>
      <div class="search-bar">
        <i class="bi bi-search"></i>
        <input type="search" placeholder="Buscar rutas, lugares, eventos…">
      </div>
      <div class="topbar-left" style="position:relative;">
        <button class="icon-btn" id="themeToggle" aria-label="Cambiar tema"><i class="bi bi-moon-stars"></i></button>
        <button class="icon-btn" id="notifBtn" aria-label="Notificaciones"><i class="bi bi-bell"></i><span class="dot"></span></button>
        <div class="notif-panel glass" id="notifPanel"></div>
        <div class="user-chip" onclick="location.href='perfil.html'">
          <img class="avatar" src="https://i.pravatar.cc/80?img=12" alt="Usuario">
        </div>
      </div>
    </header>`;
    this.renderNotifications();
  },

  renderNotifications(){
    const panel = document.getElementById('notifPanel');
    if(!panel || typeof URBIX_DATA === 'undefined') return;
    panel.innerHTML = `<div style="padding:14px 12px 8px;font-family:var(--font-display);color:var(--text-hi);">Notificaciones</div>` +
      URBIX_DATA.notifications.map(n => `
        <div class="notif-item">
          <div class="ic"><i class="bi ${n.icon}"></i></div>
          <div>
            <div class="t">${n.title}</div>
            <div class="s">${n.sub} · ${n.time}</div>
          </div>
        </div>`).join('') +
      `<div style="padding:10px;"><a href="notificaciones.html" class="btn btn-ghost btn-block btn-sm">Ver todas</a></div>`;
  },

  injectFooter(){
    const root = document.getElementById('footer-root');
    if(!root) return;
    root.innerHTML = `
    <footer class="site-footer">
      <span>© 2026 URBIX · Movilidad Inteligente en Popayán</span>
      <div class="footer-links">
        <a href="ayuda.html">Ayuda</a>
        <a href="contacto.html">Contacto</a>
        <a href="configuracion.html">Configuración</a>
      </div>
    </footer>`;
  },

  wireGlobalEvents(){
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    if(toggle){
      toggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        const icon = toggle.querySelector('i');
        icon.className = sidebar.classList.contains('collapsed') ? 'bi bi-chevron-right' : 'bi bi-chevron-left';
      });
    }
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const overlay = document.getElementById('sidebarOverlay');
    if(mobileBtn){
      mobileBtn.addEventListener('click', () => {
        sidebar.classList.add('mobile-open');
        overlay?.classList.add('open');
      });
    }
    if(overlay){
      overlay.addEventListener('click', () => {
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('open');
      });
    }
    const notifBtn = document.getElementById('notifBtn');
    const notifPanel = document.getElementById('notifPanel');
    if(notifBtn){
      notifBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        notifPanel.classList.toggle('open');
      });
      document.addEventListener('click', (e) => {
        if(notifPanel && !notifPanel.contains(e.target) && e.target !== notifBtn){
          notifPanel.classList.remove('open');
        }
      });
    }
    const themeToggle = document.getElementById('themeToggle');
    if(themeToggle){
      const THEME_ORDER = ['dark', 'light', 'amoled'];
      const THEME_ICONS = { dark:'bi-moon-stars', light:'bi-sun', amoled:'bi-circle-half' };
      themeToggle.addEventListener('click', () => {
        const html = document.documentElement;
        const current = html.getAttribute('data-theme') || 'dark';
        const next = THEME_ORDER[(THEME_ORDER.indexOf(current) + 1) % THEME_ORDER.length];
        html.setAttribute('data-theme', next);
        localStorage.setItem('urbix-theme', next);
        themeToggle.querySelector('i').className = 'bi ' + THEME_ICONS[next];
      });
    }
  },

  applySavedTheme(){
    const saved = localStorage.getItem('urbix-theme');
    const ICONS = { dark:'bi-moon-stars', light:'bi-sun', amoled:'bi-circle-half' };
    if(saved && saved !== 'dark'){
      document.documentElement.setAttribute('data-theme', saved);
      const icon = document.querySelector('#themeToggle i');
      if(icon) icon.className = 'bi ' + (ICONS[saved] || 'bi-moon-stars');
    }
  },

  applyAccessibilityPrefs(){
    const fontScale = parseFloat(localStorage.getItem('urbix-font-scale') || '1');
    document.documentElement.style.fontSize = (fontScale * 100) + '%';
    if(localStorage.getItem('urbix-high-contrast') === '1') document.body.classList.add('high-contrast');
    if(localStorage.getItem('urbix-reduce-motion') === '1') document.body.classList.add('reduce-motion');
  },

  revealOnScroll(){
    if(typeof AOS !== 'undefined'){
      AOS.init({ duration:600, once:true, offset:60 });
      return;
    }
    const items = document.querySelectorAll('[data-aos]');
    if(!items.length) return;
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => { if(e.isIntersecting) e.target.classList.add('aos-in'); });
    }, { threshold:.15 });
    items.forEach(i => obs.observe(i));
  },

  refreshReveal(){
    if(typeof AOS !== 'undefined'){ AOS.refreshHard(); }
  },

  toast(message, type = 'success'){
    let stack = document.querySelector('.toast-stack');
    if(!stack){
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      document.body.appendChild(stack);
    }
    const el = document.createElement('div');
    el.className = `toast glass ${type}`;
    el.innerHTML = `<i class="bi ${type==='success' ? 'bi-check-circle-fill' : 'bi-x-circle-fill'}" style="color:${type==='success' ? 'var(--neon)' : 'var(--danger)'}"></i><span>${message}</span>`;
    stack.appendChild(el);
    setTimeout(() => { el.style.opacity='0'; el.style.transform='translateX(30px)'; setTimeout(()=>el.remove(), 250); }, 3200);
  },
};
