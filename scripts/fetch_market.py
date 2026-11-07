
import json
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

SYMBOLS = {
    "kospi": ("^KS11", "코스피"),
    "nasdaq": ("^IXIC", "나스닥"),
    "usdkrw": ("KRW=X", "달러/원"),
}


def fetch_market():
    result = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "markets": []
    }

    for key, (symbol, name) in SYMBOLS.items():
        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(
                period="5d",
                interval="1d"
            )

            if history.empty:
                print(f"시세 없음: {symbol}")
                continue

            close = history["Close"].dropna()

            if close.empty:
                continue

            price = float(close.iloc[-1])

            previous = (
                float(close.iloc[-2])
                if len(close) > 1
                else price
            )

            change = price - previous

            change_percent = (
                change / previous * 100
                if previous
                else 0
            )

            result["markets"].append({
                "id": key,
                "symbol": symbol,
                "name": name,
                "price": round(price, 2),
                "change": round(change, 2),
                "change_percent": round(
                    change_percent, 2
                ),
                "history": [
                    round(float(value), 2)
                    for value in close.tail(5)
                ]
            })

            print(
                f"수집 성공: {name} {price}"
            )

        except Exception as error:
            print(
                f"수집 실패: {name}: {error}"
            )

    if not result["markets"]:
        raise RuntimeError(
            "모든 금융 시세 수집 실패"
        )

    output = Path("data/market.json")

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(f"저장 완료: {output}")


if __name__ == "__main__":
    fetch_market()
