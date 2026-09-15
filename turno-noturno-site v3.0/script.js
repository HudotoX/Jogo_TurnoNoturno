// TURNO NOTURNO — troca de câmeras + timer de sessão

const tabs = document.querySelectorAll('.cam-tab');
const views = document.querySelectorAll('.cam-view');
const monitorLabel = document.getElementById('monitor-label');

const labels = {
  'cam-01': 'CAM 01 — Ala de Descanso',
  'cam-02': 'CAM 02 — Corredor Central',
  'cam-03': 'CAM 03 — Sala de Registros',
  'cam-04': 'CAM 04 — Pátio Interno',
};

function activate(targetId) {
  tabs.forEach(t => {
    const isMatch = t.dataset.target === targetId;
    t.classList.toggle('is-active', isMatch);
    t.setAttribute('aria-selected', isMatch ? 'true' : 'false');
  });
  views.forEach(v => v.classList.toggle('is-active', v.id === targetId));
  if (monitorLabel && labels[targetId]) monitorLabel.textContent = labels[targetId];
}

tabs.forEach(tab => {
  tab.addEventListener('click', () => activate(tab.dataset.target));
});

// botões internos com data-goto (ex: "Baixar o jogo" na seção 1)
document.querySelectorAll('[data-goto]').forEach(btn => {
  btn.addEventListener('click', () => activate(btn.dataset.goto));
});

// navegação por setas do teclado, igual ao jogo (← →)
const order = ['cam-01', 'cam-02', 'cam-03', 'cam-04'];
document.addEventListener('keydown', (e) => {
  const current = document.querySelector('.cam-view.is-active').id;
  const idx = order.indexOf(current);
  if (e.key === 'ArrowRight') activate(order[(idx + 1) % order.length]);
  if (e.key === 'ArrowLeft') activate(order[(idx - 1 + order.length) % order.length]);
});

// timer de sessão (só decoração, reinicia a cada visita)
const timerEl = document.getElementById('session-timer');
let seconds = 0;
setInterval(() => {
  seconds++;
  const m = String(Math.floor(seconds / 60)).padStart(2, '0');
  const s = String(seconds % 60).padStart(2, '0');
  if (timerEl) timerEl.textContent = `${m}:${s}`;
}, 1000);
