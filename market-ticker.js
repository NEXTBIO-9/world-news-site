/* NEXT BIO market strip v2 — dark, responsive, unclipped. */
(() => {
  'use strict';
  document.getElementById('nb-market-strip')?.remove();
  document.getElementById('nb-market-restore')?.remove();
  document.getElementById('nb-market-strip-style')?.remove();

  const style=document.createElement('style');
  style.id='nb-market-strip-style';
  style.textContent=`
    #nb-market-strip{position:fixed;top:8px;right:12px;z-index:9000;width:min(540px,calc(100vw - 24px));height:48px;display:flex;align-items:center;gap:8px;padding:0 10px;background:#0e192a;border:1px solid #33445d;border-radius:9px;box-shadow:0 6px 20px #0007;color:#e2e8f0;font:12px system-ui,sans-serif;box-sizing:border-box;overflow:hidden}
    #nb-market-strip *{box-sizing:border-box}
    #nb-market-strip .nb-market-label{font-size:10px;letter-spacing:.09em;color:#60a5fa;font-weight:700;white-space:nowrap}
    #nb-market-strip .nb-market-symbol{display:flex;align-items:center;gap:9px;min-width:0;flex:1;color:inherit;text-decoration:none;overflow:hidden}
    #nb-market-strip .nb-market-symbol-name{white-space:nowrap;font-weight:650;color:#f1f5f9}
    #nb-market-strip .nb-market-spark{width:72px;height:22px;flex:none;opacity:.8}
    #nb-market-strip .nb-market-quote{color:#93a4bb;white-space:nowrap;font-size:11px}
    #nb-market-strip .nb-market-clock{white-space:nowrap;border-left:1px solid #34465e;padding-left:10px;font-variant-numeric:tabular-nums;color:#cbd5e1;font-size:11px}
    #nb-market-strip .nb-market-close{flex:none;background:none;border:0;color:#94a3b8;font-size:18px;line-height:1;cursor:pointer;padding:2px}
    #nb-market-strip .nb-market-close:hover{color:white}
    #nb-market-restore{position:fixed;top:8px;right:12px;z-index:9000;background:#0e192a;color:#dbeafe;border:1px solid #33445d;border-radius:8px;padding:9px 12px;cursor:pointer;font:12px system-ui,sans-serif}
    #nb-market-strip[hidden],#nb-market-restore[hidden]{display:none!important}
    @media(max-width:650px){#nb-market-strip{top:auto;bottom:10px;right:8px;width:calc(100vw - 16px)}#nb-market-restore{top:auto;bottom:10px;right:8px}#nb-market-strip .nb-market-label{display:none}#nb-market-strip .nb-market-spark{width:48px}#nb-market-strip .nb-market-clock{font-size:10px}}
  `;
  document.head.appendChild(style);
  const symbols=[
    ['코스피','KRX-KOSPI','https://www.tradingview.com/symbols/KRX-KOSPI/'],
    ['S&P 500','SPX','https://www.tradingview.com/symbols/SPX/'],
    ['나스닥','NASDAQ-IXIC','https://www.tradingview.com/symbols/NASDAQ-IXIC/'],
    ['달러/원','FX_IDC-USDKRW','https://www.tradingview.com/symbols/USDKRW/'],
    ['금','TVC-GOLD','https://www.tradingview.com/symbols/GOLD/'],
    ['WTI 유가','TVC-USOIL','https://www.tradingview.com/symbols/USOIL/']
  ];
  const bar=document.createElement('aside');
  bar.id='nb-market-strip';
  bar.setAttribute('aria-label','세계 주요 금융 지수와 서울 현재 시각');
  bar.innerHTML=`<span class="nb-market-label">MARKET</span><a class="nb-market-symbol" target="_blank" rel="noopener noreferrer"><span class="nb-market-symbol-name"></span><svg class="nb-market-spark" viewBox="0 0 72 22" aria-hidden="true"><path d="M1 15 L10 14 L17 17 L24 10 L31 12 L38 5 L44 9 L52 4 L59 11 L66 8 L71 7" fill="none" stroke="#22c55e" stroke-width="1.6" stroke-linejoin="round"/></svg><span class="nb-market-quote">시세 보기 ↗</span></a><time class="nb-market-clock">--:--:--</time><button class="nb-market-close" type="button" aria-label="시세 숨기기" title="시세 숨기기">×</button>`;
  // Sparkline is decorative only: no fabricated price movements or numerical quotes.
  bar.querySelector('.nb-market-spark').style.display='none';
  document.body.appendChild(bar);
  const link=bar.querySelector('.nb-market-symbol');
  const name=bar.querySelector('.nb-market-symbol-name');
  let i=0;
  function rotate(){const s=symbols[i++%symbols.length];name.textContent=s[0];link.href=s[2];link.title=`${s[0]} 실제 시세 확인 (새 창)`;}
  rotate();
  const rotator=setInterval(rotate,5000);
  const clock=bar.querySelector('.nb-market-clock');
  const formatter=new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
  function updateClock(){clock.textContent=formatter.format(new Date())+' KST';}
  updateClock();
  const timer=setInterval(updateClock,1000);
  const restore=document.createElement('button');
  restore.id='nb-market-restore';restore.type='button';restore.textContent='↗ MARKET';restore.hidden=true;
  document.body.appendChild(restore);
  bar.querySelector('.nb-market-close').addEventListener('click',()=>{bar.hidden=true;restore.hidden=false;});
  restore.addEventListener('click',()=>{bar.hidden=false;restore.hidden=true;});
  window.addEventListener('pagehide',()=>{clearInterval(timer);clearInterval(rotator);},{once:true});
})();
