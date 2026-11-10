
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
            # Use recent intraday 5-minute bars instead of daily closes.
            # The latest available bar can lag the live exchange price.
            history = ticker.history(
                period="5d",
                interval="5m"
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
    # Keep previously known quotes when a provider temporarily omits a symbol.
    previous_data = {}
    if output.exists():
        try:
            previous_data = json.loads(output.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            previous_data = {}
    old_markets = {item.get("id"): item for item in previous_data.get("markets", []) if isinstance(item, dict)}
    fresh_markets = {item["id"]: item for item in result["markets"]}
    result["markets"] = [fresh_markets.get(key, old_markets.get(key)) for key in SYMBOLS]
    result["markets"] = [item for item in result["markets"] if item is not None]
    # An unchanged quote is not a new market update; avoid a commit and Pages rebuild.
    if result["markets"] == previous_data.get("markets"):
        print("시세 변동 없음: 기존 market.json 유지")
        return


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
