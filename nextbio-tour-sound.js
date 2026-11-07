/* NEXT BIO tour sound: 22 Airport announcement chime. Standalone addon. */
(() => {
  'use strict';
  if (window.__nextbioTourSound) return;
  window.__nextbioTourSound = true;
  const toggle = document.getElementById('nb-tour-toggle');
  const status = document.getElementById('nb-tour-status');
  if (!toggle || !status) return;

  const label = document.createElement('label');
  label.className = 'nb-tour-sound-control';
  label.style.cssText = 'display:inline-flex;align-items:center;gap:5px;margin-left:10px;cursor:pointer;font-size:12px;white-space:nowrap;';
  const soundSwitch = document.createElement('input');
  soundSwitch.type = 'checkbox';
  soundSwitch.id = 'nb-tour-sound-toggle';
  soundSwitch.setAttribute('aria-label', '국가 자동 순회 효과음 켜기');
  try { soundSwitch.checked = localStorage.getItem('nextbio-tour-sound') !== 'off'; }
  catch (_) { soundSwitch.checked = true; }
  const text = document.createElement('span');
  function updateLabel() { text.textContent = soundSwitch.checked ? '🔊 순회 소리 켜짐' : '🔇 순회 소리 꺼짐'; }
  updateLabel();
  label.append(soundSwitch, text);
  status.insertAdjacentElement('afterend', label);

  let audio = null;
  let lastStatus = '';
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  function unlockAudio() {
    if (!soundSwitch.checked || !AudioContextClass) return;
    try {
      if (!audio) audio = new AudioContextClass();
      if (audio.state === 'suspended') audio.resume().catch(() => {});
    } catch (error) { console.warn('[NEXT BIO tour sound]', error); }
  }
  function chime() {
    if (!soundSwitch.checked || !toggle.checked || document.hidden || !audio || audio.state !== 'running') return;
    // Airport announcement chime #22: three soft, ascending sine tones.
    // UI volume is 100%; output is capped at a comfortable level to avoid clipping.
    const now = audio.currentTime + 0.012;
    const notes = [[659.25, 0, 0.70, 0.45], [987.77, 0.12, 0.75, 0.32], [1318.5, 0.20, 0.90, 0.14]];
    const master = audio.createGain();
    master.gain.value = 0.25;
    master.connect(audio.destination);
    notes.forEach(([frequency, offset, duration, level]) => {
      const osc = audio.createOscillator();
      const env = audio.createGain();
      const start = now + offset;
      osc.type = 'sine';
      osc.frequency.value = frequency;
      env.gain.setValueAtTime(0.0001, start);
      env.gain.exponentialRampToValueAtTime(level, start + 0.012);
      env.gain.exponentialRampToValueAtTime(0.0001, start + duration);
      osc.connect(env).connect(master);
      osc.start(start);
      osc.stop(start + duration + 0.025);
      osc.onended = () => { osc.disconnect(); env.disconnect(); };
    });
  }
  // Capture phase: unlock sound from the same user gesture that starts the tour.
  toggle.addEventListener('change', () => { if (toggle.checked) unlockAudio(); }, {capture:true});
  soundSwitch.addEventListener('change', () => {
    updateLabel();
    try { localStorage.setItem('nextbio-tour-sound', soundSwitch.checked ? 'on' : 'off'); } catch (_) {}
    if (soundSwitch.checked) unlockAudio();
  });
  // The existing app updates this status once per country. No changes to app.js needed.
  const observer = new MutationObserver(() => {
    const value = status.textContent.trim();
    if (value === lastStatus) return;
    lastStatus = value;
    if (toggle.checked && /·\s*\d+\s*\/\s*\d+/.test(value)) chime();
  });
  observer.observe(status, {childList:true, characterData:true, subtree:true});
  window.addEventListener('pagehide', () => { observer.disconnect(); if (audio) audio.close().catch(() => {}); }, {once:true});
})();
