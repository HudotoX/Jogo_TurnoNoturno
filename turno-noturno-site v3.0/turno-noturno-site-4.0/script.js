(() => {
  'use strict';
  const cameras = [
    { name: 'Ala de Descanso', description: 'É aqui que começa o acompanhamento de Daniel. Observe a estabilidade e escute o que ele tem a dizer.', alt: 'Interface do VIGIA com Daniel na Ala de Descanso, painel de atendimento e diário' },
    { name: 'Corredor Central', description: 'Os relatos mencionam batidas no corredor. Confira o sinal e procure os pacientes quando mudarem de sala.', alt: 'Câmera do Corredor Central no VIGIA, com portas ao longo do hospital' },
    { name: 'Sala de Observação', description: 'Elias começa o turno nesta sala. Os pedidos e o que ele conta fazem parte do seu acompanhamento.', alt: 'Elias na Sala de Observação, com os indicadores de estabilidade do VIGIA' },
    { name: 'Pátio Interno', description: 'Mais um espaço para conferir durante o plantão. Um paciente fora da última sala conhecida precisa ser localizado.', alt: 'Captura do Pátio Interno no sistema de monitoramento VIGIA' },
    { name: 'Ala Farmacêutica', description: 'Seis medicamentos fictícios, uma bandeja de três espaços. Confira o pedido, separe os itens e volte ao paciente.', alt: 'Farmácia do VIGIA com seis medicamentos, atalhos e painel de atendimento' }
  ];
  const tabs = [...document.querySelectorAll('[data-camera]')];
  const panel = document.getElementById('camera-panel');
  const image = document.getElementById('camera-image');
  const openCapture = document.getElementById('open-capture');
  const dialog = document.getElementById('capture-dialog');
  let currentCamera = 0;
  function selectCamera(index, moveFocus = false) {
    currentCamera = (index + cameras.length) % cameras.length;
    const camera = cameras[currentCamera];
    const number = String(currentCamera + 1).padStart(2, '0');
    const source = `assets/vigia/cam-${number}.png`;
    tabs.forEach((tab, i) => {
      tab.setAttribute('aria-selected', String(i === currentCamera));
      tab.tabIndex = i === currentCamera ? 0 : -1;
    });
    panel.setAttribute('aria-labelledby', tabs[currentCamera].id);
    image.src = source;
    image.alt = camera.alt;
    openCapture.setAttribute('aria-label', `Ampliar captura da ${camera.name}`);
    document.getElementById('camera-code').textContent = `CAM ${number}`;
    document.getElementById('camera-name').textContent = camera.name;
    document.getElementById('camera-description').textContent = camera.description;
    document.getElementById('camera-counter').textContent = `${number} / 05`;
    document.getElementById('dialog-image').src = source;
    document.getElementById('dialog-image').alt = camera.alt;
    document.getElementById('dialog-title').textContent = `CAM ${number} — ${camera.name}`;
    document.getElementById('dialog-counter').textContent = `${number} / 05`;
    if (moveFocus) tabs[currentCamera].focus();
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectCamera(index));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = currentCamera + 1;
      if (event.key === 'ArrowLeft') next = currentCamera - 1;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = cameras.length - 1;
      if (next !== undefined) { event.preventDefault(); selectCamera(next, true); }
    });
  });
  openCapture.addEventListener('click', () => {
    if (typeof dialog.showModal !== 'function') { window.open(image.src, '_blank', 'noopener'); return; }
    selectCamera(currentCamera);
    dialog.showModal();
    document.body.classList.add('modal-open');
  });
  document.getElementById('close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {
    document.body.classList.remove('modal-open');
    openCapture.focus({ preventScroll: true });
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
  dialog.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault(); selectCamera(currentCamera + (event.key === 'ArrowRight' ? 1 : -1));
    }
  });
  document.getElementById('previous-camera').addEventListener('click', () => selectCamera(currentCamera - 1));
  document.getElementById('next-camera').addEventListener('click', () => selectCamera(currentCamera + 1));

  const toggle = document.getElementById('effects-toggle');
  const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
  let effectsEnabled = !motionPreference.matches;
  let explicitPreference = false;
  try {
    const saved = localStorage.getItem('turno-noturno-effects');
    if (saved !== null) { effectsEnabled = saved === 'on'; explicitPreference = true; }
  } catch { /* Optional: local file access and private mode can block storage. */ }
  function updateEffects() {
    document.documentElement.classList.toggle('effects-off', !effectsEnabled);
    toggle.setAttribute('aria-pressed', String(effectsEnabled));
    toggle.textContent = `Efeitos visuais: ${effectsEnabled ? 'ligados' : 'desligados'}`;
  }
  toggle.addEventListener('click', () => {
    effectsEnabled = !effectsEnabled;
    explicitPreference = true;
    updateEffects();
    try { localStorage.setItem('turno-noturno-effects', effectsEnabled ? 'on' : 'off'); } catch { /* Optional preference. */ }
  });
  motionPreference.addEventListener('change', event => {
    if (!explicitPreference) { effectsEnabled = !event.matches; updateEffects(); }
  });
  updateEffects();

  // Invalid or absent links never become fake download buttons.
  const config = window.TURNO_CONFIG || {};
  function validUrl(value) {
    if (typeof value !== 'string' || !/^https?:\/\//i.test(value.trim())) return null;
    try {
      const url = new URL(value, document.baseURI);
      return /^https?:$/.test(url.protocol) ? url.href : null;
    } catch { return null; }
  }
  if (typeof config.version === 'string' && config.version.trim()) {
    document.querySelectorAll('[data-version]').forEach(element => { element.textContent = config.version; });
  }
  const downloadUrl = validUrl(config.downloadUrl);
  const repositoryUrl = validUrl(config.repositoryUrl);
  if (downloadUrl) {
    const link = document.getElementById('download-link');
    link.href = downloadUrl;
    link.hidden = false;
    document.getElementById('download-pending').hidden = true;
    document.getElementById('download-status').textContent = config.downloadDescription || 'O próximo plantão está esperando por você.';
  }
  if (repositoryUrl) {
    const link = document.getElementById('repo-link');
    link.href = repositoryUrl;
    link.hidden = false;
  }
})();
