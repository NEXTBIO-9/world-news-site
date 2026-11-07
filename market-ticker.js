/* NEXT BIO compact market ticker. Independent of app.js and news loading. */
(() => {
  'use strict';
  if (document.getElementById('nb-market-strip')) return;
  const style = document.createElement('style');
  style.textContent = `
    #nb-market-strip{position:fixed;top:8px;right:12px;z-index:9000;width:min(610px,calc(100vw - 24px));height:45px;display:flex;align-items:center;gap:8px;padding:3px 8px 3px 4px;background:#080c13;border:1px solid #263344;border-radius:8px;box-shadow:0 5px 20px #0006;color:#d8e3f1;font:12px system-ui,sans-serif;box-sizing:border-box}
    #nb-market-strip .nb-market-data{min-width:0;flex:1;height:36px;overflow:hidden}
    #nb-market-strip .tradingview-widget-container{height:36px!important;overflow:hidden}
    #nb-market-strip .tradingview-widget-container__widget{height:36px!important}
    #nb-market-strip .nb-market-clock{white-space:nowrap;border-left:1px solid #293747;padding-left:9px;font-variant-numeric:tabular-nums;font-weight:600;color:#b9c9dd}
    #nb-market-strip .nb-market-close{background:none;border:0;color:#8395a9;font-size:17px;line-height:1;cursor:pointer;padding:1px 2px}
    #nb-market-restore{position:fixed;top:8px;right:12px;z-index:9000;background:#0e1725;color:#dbeafe;border:1px solid #334155;border-radius:6px;padding:7px 10px;cursor:pointer;font:12px system-ui,sans-serif}
    @media(max-width:720px){#nb-market-strip{top:auto;bottom:8px;right:8px;width:calc(100vw - 16px)}#nb-market-restore{top:auto;bottom:8px;right:8px}#nb-market-strip .nb-market-clock{font-size:11px}}
  `;
  document.head.appendChild(style);
  const bar=document.createElement('div');
  bar.id='nb-market-strip';
  bar.setAttribute('aria-label','주요 금융시장 시세 및 서울 현재 시각');
  bar.innerHTML='<div class="nb-market-data"><div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div></div></div><time class="nb-market-clock" title="서울 현재 시각">--:--:--</time><button class="nb-market-close" type="button" title="시세 숨기기" aria-label="시세 숨기기">×</button>';
  document.body.appendChild(bar);
  const clock=bar.querySelector('.nb-market-clock');
  const formatter=new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
  function updateClock(){clock.textContent=formatter.format(new Date())+' KST';}
  updateClock();
  const timer=setInterval(updateClock,1000);
  const restore=document.createElement('button');
  restore.id='nb-market-restore';restore.type='button';restore.textContent='📈 시세 보기';restore.hidden=true;
  document.body.appendChild(restore);
  bar.querySelector('.nb-market-close').addEventListener('click',()=>{bar.hidden=true;bar.style.display='none';restore.hidden=false;});
  restore.addEventListener('click',()=>{bar.hidden=false;bar.style.display='flex';restore.hidden=true;});
  const script=document.createElement('script');
  script.src='https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js';
  script.async=true;
  script.textContent=JSON.stringify({
    symbols:[
      {proName:'KRX:KOSPI',title:'코스피'},
      {proName:'FOREXCOM:SPXUSD',title:'S&P 500'},
      {proName:'NASDAQ:IXIC',title:'나스닥'},
      {proName:'FX_IDC:USDKRW',title:'달러/원'},
      {proName:'TVC:GOLD',title:'금'},
      {proName:'TVC:USOIL',title:'WTI 유가'}
    ],showSymbolLogo:false,isTransparent:true,displayMode:'adaptive',colorTheme:'dark',locale:'kr'
  });
  bar.querySelector('.tradingview-widget-container').appendChild(script);
  window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});
})();
