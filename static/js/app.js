/* ============================================================
   URBIX — app.js
   Utilidades globales: pantalla de carga, favoritos (localStorage
   como simulación temporal de base de datos), helpers UI.
   ============================================================ */

(function(){
  // Pantalla de carga breve al entrar a cada página
  window.addEventListener('load', () => {
    const loader = document.getElementById('pageLoader');
    if(loader){
      setTimeout(() => {
        loader.style.opacity = '0';
        setTimeout(() => loader.remove(), 300);
      }, 450);
    }
  });
})();

const Favorites = {
  KEY: 'urbix-favorites',
  get(){ return JSON.parse(localStorage.getItem(this.KEY) || '[]'); },
  isFav(type, id){ return this.get().some(f => f.type===type && f.id===id); },
  toggle(type, id, meta={}){
    let list = this.get();
    const exists = list.find(f => f.type===type && f.id===id);
    if(exists){
      list = list.filter(f => !(f.type===type && f.id===id));
    } else {
      list.push({ type, id, ...meta, savedAt: Date.now() });
    }
    localStorage.setItem(this.KEY, JSON.stringify(list));
    return !exists;
  }
};

function favBtnState(btn, isFav){
  btn.classList.toggle('is-fav', isFav);
  const icon = btn.querySelector('i');
  if(icon) icon.className = isFav ? 'bi bi-heart-fill' : 'bi bi-heart';
  if(isFav) btn.style.color = 'var(--neon)';
  else btn.style.color = '';
}

function initFavButtons(scope = document){
  scope.querySelectorAll('[data-fav-type]').forEach(btn => {
    const type = btn.dataset.favType, id = Number(btn.dataset.favId);
    favBtnState(btn, Favorites.isFav(type, id));
    btn.addEventListener('click', (e) => {
      e.preventDefault(); e.stopPropagation();
      const nowFav = Favorites.toggle(type, id, {
        name: btn.dataset.favName || '',
        img: btn.dataset.favImg || ''
      });
      favBtnState(btn, nowFav);
      Components.toast(nowFav ? 'Agregado a favoritos' : 'Eliminado de favoritos', 'success');
    });
  });
}

function starRow(rating){
  const full = Math.floor(rating);
  let html = '';
  for(let i=0;i<5;i++) html += `<i class="bi ${i<full ? 'bi-star-fill':'bi-star'}"></i>`;
  return html;
}

/* ---------------- Ripple effect ---------------- */
document.addEventListener('click', (e) => {
  const el = e.target.closest('.btn, .icon-btn, .tab');
  if(!el) return;
  const rect = el.getBoundingClientRect();
  const ripple = document.createElement('span');
  const size = Math.max(rect.width, rect.height);
  ripple.className = 'ripple';
  ripple.style.width = ripple.style.height = size + 'px';
  ripple.style.left = (e.clientX - rect.left - size/2) + 'px';
  ripple.style.top = (e.clientY - rect.top - size/2) + 'px';
  el.appendChild(ripple);
  setTimeout(() => ripple.remove(), 650);
});

/* ---------------- Interactive star rating (hover preview before submit) ---------------- */
function initStarRating(scope = document){
  scope.querySelectorAll('.star-rate').forEach(row => {
    const buttons = [...row.querySelectorAll('button')];
    buttons.forEach((btn, idx) => {
      btn.addEventListener('mouseenter', () => {
        buttons.forEach((b, i) => {
          b.querySelector('i').className = i <= idx ? 'bi bi-star-fill' : 'bi bi-star';
        });
      });
    });
    row.addEventListener('mouseleave', () => {
      buttons.forEach(b => { b.querySelector('i').className = 'bi bi-star'; });
    });
  });
}
document.addEventListener('DOMContentLoaded', () => initStarRating());

/* ---------------- Animated number counters (dashboard stats) ---------------- */
function animateCounters(scope = document){
  scope.querySelectorAll('.stat-card .value').forEach(el => {
    const text = el.textContent.trim();
    const match = text.match(/^-?\d+/);
    if(!match) return;
    const target = parseInt(match[0], 10);
    const suffix = text.slice(match[0].length);
    if(isNaN(target) || el.dataset.counted) return;
    el.dataset.counted = '1';
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 30));
    const timer = setInterval(() => {
      current += step;
      if(current >= target){ current = target; clearInterval(timer); }
      el.textContent = current + suffix;
    }, 25);
  });
}
document.addEventListener('DOMContentLoaded', () => animateCounters());
