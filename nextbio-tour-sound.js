/* NEXT BIO tour sound: selectable 22 Airport chime / 9 Radar ping. */
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
  // Select sound while preserving the existing on/off switch.
  const selector = document.createElement('select');
  selector.id = 'nb-tour-sound-select';
  selector.setAttribute('aria-label', '국가 자동 순회 효과음 선택');
  selector.style.cssText = 'margin-left:7px;padding:4px 6px;border-radius:6px;max-width:145px;font-size:12px;background:#182a41;color:#e5edf7;border:1px solid #526680;';
  selector.add(new Option('22번 공항 차임', '22'));
  selector.add(new Option('9번 레이더 핑', '9'));
  try { selector.value = localStorage.getItem('nextbio-tour-sound-type') === '9' ? '9' : '22'; }
  catch (_) { selector.value = '22'; }
  selector.addEventListener('change', () => {
    try { localStorage.setItem('nextbio-tour-sound-type', selector.value); } catch (_) {}
    unlockAudio();
  });
  label.appendChild(selector);
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
    // Both effects use the same safe output cap (100% UI volume setting).
    const now = audio.currentTime + 0.012;
    const radar = selector.value === '9';
    const notes = radar
      ? [[1150, 0, 0.16, 0.55], [1725, 0.035, 0.18, 0.15]]
      : [[659.25, 0, 0.70, 0.45], [987.77, 0.12, 0.75, 0.32], [1318.5, 0.20, 0.90, 0.14]];
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
