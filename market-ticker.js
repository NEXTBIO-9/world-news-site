
/* NEXT BIO Market Ticker V3 */
(() => {
  "use strict";

  if (window.NEXTBIO_MARKET_V3) return;
  window.NEXTBIO_MARKET_V3 = true;

  document.getElementById("nb-market-strip")?.remove();
  document.getElementById("nb-market-restore")?.remove();
  document.getElementById("nb-market-strip-style")?.remove();

  const markets = [
    ["코스피", "https://www.tradingview.com/symbols/KRX-KOSPI/"],
    ["S&P 500", "https://www.tradingview.com/symbols/SPX/"],
    ["나스닥", "https://www.tradingview.com/symbols/NASDAQ-IXIC/"],
    ["달러/원", "https://www.tradingview.com/symbols/USDKRW/"],
    ["금", "https://www.tradingview.com/symbols/GOLD/"],
    ["WTI", "https://www.tradingview.com/symbols/USOIL/"]
  ];

  const css = document.createElement("style");
  css.id = "nb-market-strip-style";
  css.textContent = `
    #nb-market-strip {
      position: fixed;
      top: 8px;
      right: 12px;
      z-index: 9000;
      width: min(650px, calc(100vw - 24px));
      height: 48px;
      padding: 0 12px;
      display: flex;
      align-items: center;
      gap: 12px;
      box-sizing: border-box;
      border: 1px solid #33445d;
      border-radius: 9px;
      background: #0e192a;
      color: #e2e8f0;
      box-shadow: 0 6px 20px #0005;
      font: 12px system-ui, sans-serif;
    }

    #nb-market-strip * {
      box-sizing: border-box;
    }

    #nb-market-strip .nb-label {
      flex: none;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1px;
      color: #60a5fa;
    }

    #nb-market-strip .nb-items {
      display: flex;
      flex: 1;
      align-items: center;
      gap: 18px;
      min-width: 0;
      overflow-x: auto;
      scrollbar-width: none;
    }

    #nb-market-strip .nb-items::-webkit-scrollbar {
      display: none;
    }

    #nb-market-strip .nb-item {
      flex: none;
      color: #e2e8f0;
      text-decoration: none;
      white-space: nowrap;
      font-weight: 600;
    }

    #nb-market-strip .nb-item:hover {
      color: #60a5fa;
    }

    #nb-market-strip .nb-clock {
      flex: none;
      border-left: 1px solid #33445d;
      padding-left: 10px;
      font-size: 11px;
      color: #94a3b8;
      white-space: nowrap;
    }

    #nb-market-strip .nb-close {
      flex: none;
      border: 0;
      background: transparent;
      color: #94a3b8;
      font-size: 18px;
      cursor: pointer;
    }

    #nb-market-restore {
      position: fixed;
      top: 8px;
      right: 12px;
      z-index: 9000;
      padding: 10px;
      background: #0e192a;
      color: #60a5fa;
      border: 1px solid #33445d;
      border-radius: 8px;
      cursor: pointer;
    }

    #nb-market-strip[hidden],
    #nb-market-restore[hidden] {
      display: none !important;
    }

    @media (max-width: 650px) {
      #nb-market-strip {
        top: auto;
        bottom: 10px;
        right: 8px;
        width: calc(100vw - 16px);
      }

      #nb-market-strip .nb-label {
        display: none;
      }

      #nb-market-strip .nb-clock {
        font-size: 10px;
      }

      #nb-market-restore {
        top: auto;
        bottom: 10px;
      }
    }
  `;
  document.head.appendChild(css);

  const bar = document.createElement("aside");
  bar.id = "nb-market-strip";
  bar.setAttribute("aria-label", "주요 금융시장 바로가기");

  const items = markets.map(([name, url]) =>
    `<a class="nb-item" href="${url}" target="_blank"
        rel="noopener noreferrer">${name} ↗</a>`
  ).join("");

  bar.innerHTML = `
    <span class="nb-label">MARKET</span>
    <div class="nb-items">${items}</div>
    <time class="nb-clock"></time>
    <button class="nb-close" type="button"
      aria-label="티커 닫기">×</button>
  `;

  document.body.appendChild(bar);

  const clock = bar.querySelector(".nb-clock");
  const formatter = new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  });

  function updateClock() {
    clock.textContent = formatter.format(new Date()) + " KST";
  }

  updateClock();
  const clockTimer = setInterval(updateClock, 1000);

  const restore = document.createElement("button");
  restore.id = "nb-market-restore";
  restore.type = "button";
  restore.textContent = "MARKET ↗";
  restore.hidden = true;
  document.body.appendChild(restore);

  bar.querySelector(".nb-close").addEventListener("click", () => {
    bar.hidden = true;
    restore.hidden = false;
  });

  restore.addEventListener("click", () => {
    bar.hidden = false;
    restore.hidden = true;
  });

  window.addEventListener("pagehide", () => {
    clearInterval(clockTimer);
  }, { once: true });
})();
