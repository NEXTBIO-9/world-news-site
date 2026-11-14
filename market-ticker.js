/* NEXT BIO real market quotes widget — data/market.json, 5s rotation */
(() => {
  'use strict';
  if (window.__nextbioMarketLive) return;
  window.__nextbioMarketLive = true;
  document.getElementById('nb-market-strip')?.remove();
  document.getElementById('nb-market-restore')?.remove();
  document.getElementById('nb-market-strip-style')?.remove();

  const markets = [
    {id:'kospi',name:'코스피',url:'https://www.tradingview.com/symbols/KRX-KOSPI/',decimals:2},
    {id:'nasdaq',name:'나스닥',url:'https://www.tradingview.com/symbols/NASDAQ-IXIC/',decimals:2},
    {id:'usdkrw',name:'달러/원',url:'https://www.tradingview.com/symbols/USDKRW/',decimals:2}
  ];
  const css = document.createElement('style');
  css.id = 'nb-market-strip-style';
  css.textContent = `
    #nb-market-strip{position:fixed;top:8px;right:12px;z-index:9000;width:min(405px,calc(100vw - 24px));min-height:54px;display:flex;align-items:center;gap:10px;padding:8px 10px;background:#101b2b;border:1px solid #34455c;border-radius:10px;box-shadow:0 8px 22px #0005;color:#e2e8f0;font:12px system-ui,sans-serif;box-sizing:border-box}
    #nb-market-strip *{box-sizing:border-box}
    #nb-market-strip .nbm-brand{color:#60a5fa;font-weight:800;font-size:10px;letter-spacing:.08em;flex:none}
    #nb-market-strip .nbm-main{display:flex;align-items:center;gap:8px;flex:1;min-width:0;text-decoration:none;color:inherit}
    #nb-market-strip .nbm-info{display:flex;flex-direction:column;gap:2px;min-width:0;flex:1}
    #nb-market-strip .nbm-name{font-weight:750;white-space:nowrap;font-size:12px}
    #nb-market-strip .nbm-value{display:flex;align-items:baseline;gap:6px;white-space:nowrap;font-variant-numeric:tabular-nums}
    #nb-market-strip .nbm-price{font-size:14px;font-weight:750}
    #nb-market-strip .nbm-change{font-size:11px;font-weight:650}
    #nb-market-strip .nbm-change.up{color:#fb7185}
    #nb-market-strip .nbm-change.down{color:#60a5fa}
    #nb-market-strip .nbm-change.flat{color:#94a3b8}
    #nb-market-strip .nbm-graph{width:68px;height:28px;flex:none;overflow:visible}
    #nb-market-strip .nbm-side{display:flex;flex-direction:column;align-items:flex-end;gap:3px;flex:none;border-left:1px solid #34455c;padding-left:8px}
    #nb-market-strip .nbm-clock{font-size:10px;color:#cbd5e1;white-space:nowrap;font-variant-numeric:tabular-nums}
    #nb-market-strip .nbm-age{font-size:9px;color:#94a3b8;white-space:nowrap}
    #nb-market-strip .nbm-close{border:0;background:none;color:#94a3b8;cursor:pointer;font-size:17px;line-height:1;padding:0 1px;align-self:flex-start}
    #nb-market-strip .nbm-close:hover{color:white}
    #nb-market-strip[hidden],#nb-market-restore[hidden]{display:none!important}
    #nb-market-restore{position:fixed;top:8px;right:12px;z-index:9000;border:1px solid #34455c;border-radius:8px;background:#101b2b;color:#93c5fd;padding:9px 12px;cursor:pointer;font:12px system-ui,sans-serif}
    @media(max-width:620px){#nb-market-strip{top:auto;bottom:8px;right:8px;width:min(405px,calc(100vw - 16px))}#nb-market-restore{top:auto;bottom:8px;right:8px}#nb-market-strip .nbm-brand{display:none}}
    @media(max-width:360px){#nb-market-strip .nbm-graph{width:45px}#nb-market-strip .nbm-price{font-size:12px}}
  `;
  document.head.appendChild(css);
  const bar = document.createElement('aside');
  bar.id = 'nb-market-strip';
  bar.setAttribute('aria-label','주요 금융시장 실제 시세 (지연 가능)');
  bar.innerHTML = `<span class="nbm-brand">MARKET</span><a class="nbm-main" target="_blank" rel="noopener noreferrer"><span class="nbm-info"><span class="nbm-name">코스피</span><span class="nbm-value"><span class="nbm-price">불러오는 중</span><span class="nbm-change"></span></span></span><svg class="nbm-graph" viewBox="0 0 68 28" aria-hidden="true"><polyline fill="none" stroke="#94a3b8" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round" points=""/></svg></a><div class="nbm-side"><time class="nbm-clock">--:--</time><span class="nbm-age">시세 확인 중</span></div><button class="nbm-close" type="button" aria-label="시세 위젯 닫기">×</button>`;
  document.body.appendChild(bar);
  const restore = document.createElement('button');
  restore.id = 'nb-market-restore';
  restore.type = 'button';
  restore.textContent = 'MARKET ↗';
  restore.hidden = true;
  document.body.appendChild(restore);
  bar.querySelector('.nbm-close').addEventListener('click',()=>{bar.hidden=true;restore.hidden=false;});
  restore.addEventListener('click',()=>{bar.hidden=false;restore.hidden=true;});

  const link=bar.querySelector('.nbm-main'), name=bar.querySelector('.nbm-name');
  const price=bar.querySelector('.nbm-price'), change=bar.querySelector('.nbm-change');
  const graph=bar.querySelector('polyline'), age=bar.querySelector('.nbm-age');
  const clock=bar.querySelector('.nbm-clock');
  const formatter=new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
  let quotes={}, index=0, fetching=false, fetchFailed=false, lastChecked=0;
  const REFRESH_MS=60000;
  const number = (n,decimals) => Number(n).toLocaleString('ko-KR',{minimumFractionDigits:decimals,maximumFractionDigits:decimals});
  function drawSparkline(values, direction){
    const data=Array.isArray(values)?values.map(Number).filter(Number.isFinite):[];
    if(data.length<2){graph.setAttribute('points','');return;}
    const min=Math.min(...data),max=Math.max(...data),spread=max-min||1;
    graph.setAttribute('points',data.map((v,i)=>`${(i*67/(data.length-1)).toFixed(1)},${(25-(v-min)/spread*22).toFixed(1)}`).join(' '));
    graph.setAttribute('stroke',direction>0?'#fb7185':direction<0?'#60a5fa':'#94a3b8');
  }
  function render(){
    const m=markets[index%markets.length],q=quotes[m.id];
    name.textContent=m.name;
    link.href=m.url;
    if(!q||!Number.isFinite(Number(q.price))){
      price.textContent='시세 대기';change.textContent='';change.className='nbm-change';
      graph.setAttribute('points','');age.textContent=fetchFailed?'데이터 연결 실패':'데이터 준비 중';return;
    }
    price.textContent=number(q.price,m.decimals);
    const pct=Number(q.change_percent);
    change.textContent=Number.isFinite(pct)?`${pct>0?'+':''}${pct.toFixed(2)}%`:'';
    change.className=`nbm-change ${pct>0?'up':pct<0?'down':'flat'}`;
    drawSparkline(q.sparkline || q.history,pct);
    const time=Date.parse(q.as_of || quotes.__updated_at || '');
    const mins=Number.isFinite(time)?Math.max(0,Math.floor((Date.now()-time)/60000)):null;
    // The JSON timestamp is the file collection time, not the exchange trade time.
    const kstDay=new Intl.DateTimeFormat('en-US',{timeZone:'Asia/Seoul',weekday:'short'}).format(new Date());
    const usDay=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',weekday:'short'}).format(new Date());
    const isWeekend=m.id==='kospi'?['Sat','Sun'].includes(kstDay):m.id==='nasdaq'?['Sat','Sun'].includes(usDay):false;
    const updatedLabel=mins===null?'갱신 시각 미상':mins<60?`데이터 갱신 ${mins}분 전`:`데이터 갱신 ${Math.floor(mins/60)}시간 전`;
    age.textContent=fetchFailed?'연결 실패 · 이전 시세':q.stale?'이전 시세':isWeekend?`${m.name} 휴장 · 최근 종가`:updatedLabel;
    age.title=`${updatedLabel} (거래 체결 시각 아님)`+(lastChecked?` · 파일 확인: ${formatter.format(new Date(lastChecked))} KST`:'');
    link.title=`${m.name} 시세 보기 (지연 가능)`;
  }
  async function fetchQuotes(){
    if(fetching) return;
    fetching=true;
    const controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort(),12000);
    try{
      const res=await fetch(`./data/market.json?t=${Date.now()}`,{cache:'no-store',signal:controller.signal});
      if(!res.ok) throw new Error(`HTTP ${res.status}`);
      const data=await res.json();
      if(!data) throw new Error('empty market data');
      if(Array.isArray(data.markets)) {
        quotes = Object.fromEntries(data.markets.filter(q => q && q.id).map(q => [q.id, q]));
        quotes.__updated_at = data.updated_at;
      } else if(data.quotes && typeof data.quotes === 'object') {
        quotes = data.quotes;
        quotes.__updated_at = data.updated_at;
      } else {
        throw new Error('invalid market data format');
      }
      fetchFailed=false;
      lastChecked=Date.now();
      render();
    }catch(err){
      fetchFailed=true;
      render();
      console.warn('[NEXT BIO market]',err);
    }finally{
      clearTimeout(timeout);
      fetching=false;
    }
  }
  clock.textContent=formatter.format(new Date())+' KST';
  const clockTimer=setInterval(()=>{clock.textContent=formatter.format(new Date())+' KST';},1000);
  const rotationTimer=setInterval(()=>{index++;render();},5000);
  setInterval(fetchQuotes,REFRESH_MS);
  // Background tabs can throttle timers; refresh immediately when the page is revisited.
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)fetchQuotes();});
  window.addEventListener('focus',()=>{if(Date.now()-lastChecked>15000)fetchQuotes();});
  window.addEventListener('pageshow',event=>{if(event.persisted)fetchQuotes();});
  render();fetchQuotes();
})();
