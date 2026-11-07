/* NEXT BIO: original classical-style synthesizer BGM and first-visit intro. */
(() => {
  'use strict';
  if (window.__nextbioAtmosphere) return;
  window.__nextbioAtmosphere = true;
  const $ = id => document.getElementById(id);
  const storage = {
    get(k) { try { return localStorage.getItem(k); } catch (_) { return null; } },
    set(k,v) { try { localStorage.setItem(k,v); } catch (_) {} }
  };
  // Show the intro once per browser tab session, not on every refresh.
  let showIntro = true;
  try { showIntro = sessionStorage.getItem('nextbio-intro-seen') !== '1'; sessionStorage.setItem('nextbio-intro-seen','1'); } catch (_) {}
  if (showIntro) {
    const overlay = document.createElement('div');
    overlay.id = 'nb-opening';
    overlay.setAttribute('role','dialog');
    overlay.setAttribute('aria-label','NEXT BIO 시작 화면');
    overlay.innerHTML = '<div class="nb-opening-inner"><div class="nb-opening-logo">NEXT<span>BIO</span></div><div class="nb-opening-sub">GLOBAL BIO &amp; NEWS NETWORK</div><div class="nb-opening-line"></div><button id="nb-opening-skip" type="button">바로 시작</button></div>';
    document.body.appendChild(overlay);
    let closed = false;
    const dismiss = () => { if (closed) return; closed = true; overlay.classList.add('nb-hide'); window.setTimeout(() => overlay.remove(), 650); };
    $('nb-opening-skip').addEventListener('click',dismiss);
    overlay.addEventListener('keydown',e=>{if(e.key==='Escape')dismiss();});
    window.setTimeout(dismiss, window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 300 : 1900);
  }
  const tour = $('nb-tour-toggle');
  const anchor = $('nb-tour-status');
  if (!tour || !anchor) return;
  const panel = document.createElement('div');
  panel.className = 'nb-bgm-panel';
  panel.innerHTML = '<button type="button" id="nb-bgm-toggle" aria-pressed="false">♫ BGM 켜기</button><label for="nb-bgm-volume">음량</label><input id="nb-bgm-volume" type="range" min="0" max="100" step="1" value="35" aria-label="배경음악 음량"><span id="nb-bgm-value">35%</span><span class="nb-bgm-status" id="nb-bgm-status" role="status">우아한 현악 앙상블</span>';
  const parent = anchor.closest('.nb-tour-controls') || anchor.parentElement;
  parent.insertAdjacentElement('afterend',panel);
  const button=$('nb-bgm-toggle'), slider=$('nb-bgm-volume'), value=$('nb-bgm-value'), status=$('nb-bgm-status');
  const savedVol=Number(storage.get('nextbio-bgm-volume'));
  slider.value=String(Math.max(0,Math.min(100,storage.get('nextbio-bgm-volume')===null?35:(Number.isFinite(savedVol)?savedVol:35))));
  value.textContent=slider.value+'%';
  const AC=window.AudioContext||window.webkitAudioContext;
  let context=null, output=null, running=false, timer=null, voices=new Set(), nextBar=0;
  const hz=m=>440*Math.pow(2,(m-69)/12);
  function playNote(midi,start,duration,level,kind='string') {
    if(!context||!output)return;
    const osc=context.createOscillator(),filter=context.createBiquadFilter(),env=context.createGain();
    osc.type=kind==='piano'?'triangle':'sawtooth';osc.frequency.setValueAtTime(hz(midi),start);
    filter.type='lowpass';filter.frequency.value=kind==='piano'?1750:700;
    env.gain.setValueAtTime(.0001,start);
    env.gain.linearRampToValueAtTime(level,start+(kind==='piano'?.018:.23));
    env.gain.exponentialRampToValueAtTime(.0001,start+duration);
    osc.connect(filter).connect(env).connect(output);
    osc.start(start);osc.stop(start+duration+.04);
    voices.add(osc);osc.onended=()=>{voices.delete(osc);osc.disconnect();filter.disconnect();env.disconnect();};
  }
  // Original 16-note classical-style phrase, four soft chord changes.
  const melody=[67,69,72,74,76,74,72,69,67,65,69,72,74,72,69,67];
  const chords=[[48,55,60],[45,52,57],[53,60,65],[48,55,60]];
  const beat=.82, phrase=melody.length*beat;
  function schedulePhrase(start){
    melody.forEach((n,i)=>playNote(n,start+i*beat,beat*1.55,.11,'string'));
    chords.forEach((ch,i)=>ch.forEach(n=>playNote(n,start+i*beat*4,beat*3.8,.042,'string')));
    melody.forEach((n,i)=>{if(i%2===0)playNote(n-12,start+i*beat,beat*.85,.035,'piano');});
  }
  function tick(){
    if(!running||!context)return;
    while(nextBar<context.currentTime+1.5){schedulePhrase(nextBar);nextBar+=phrase;}
  }
  function updateGain(){if(output&&context)output.gain.setTargetAtTime(Number(slider.value)/100*.22,context.currentTime,.04);}
  async function start(){
    if(!AC){status.textContent='오디오 미지원 브라우저';return;}
    try{
      if(!context)context=new AC();
      await context.resume();
      if(!output){output=context.createGain();output.connect(context.destination);}
      updateGain();running=true;nextBar=context.currentTime+.07;tick();timer=window.setInterval(tick,350);
      button.textContent='♫ BGM 끄기';button.setAttribute('aria-pressed','true');status.textContent='현악 앙상블 재생 중';
      storage.set('nextbio-bgm-enabled','on');
    }catch(e){status.textContent='재생 불가 · 브라우저 소리 설정 확인';}
  }
  function stop(){
    running=false;if(timer!==null){clearInterval(timer);timer=null;}
    for(const osc of voices){try{osc.stop()}catch(_){}}voices.clear();
    if(output){output.disconnect();output=null;}
    button.textContent='♫ BGM 켜기';button.setAttribute('aria-pressed','false');status.textContent='BGM 꺼짐';
    storage.set('nextbio-bgm-enabled','off');
  }
  button.addEventListener('click',()=>{if(running)stop();else start();});
  slider.addEventListener('input',()=>{value.textContent=slider.value+'%';storage.set('nextbio-bgm-volume',slider.value);updateGain();});
  // Browsers require a gesture to start audio. Resume saved preference when user starts the tour.
  tour.addEventListener('change',()=>{
    if(tour.checked&&storage.get('nextbio-bgm-enabled')==='on'&&!running)start();
    if(!tour.checked&&running)stop();
  });
  document.addEventListener('visibilitychange',()=>{
    if(document.hidden&&running&&context)context.suspend().catch(()=>{});
    else if(!document.hidden&&running&&context)context.resume().catch(()=>{});
  });
  window.addEventListener('pagehide',()=>{stop();if(context)context.close().catch(()=>{});},{once:true});
})();
