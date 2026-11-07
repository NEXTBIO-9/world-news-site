#!/usr/bin/env python3
"""Fetch delayed public market quotes via yfinance (unofficial Yahoo endpoint)."""
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'market.json'
SYMBOLS = [('kospi', '^KS11'), ('nasdaq', '^IXIC'), ('usdkrw', 'KRW=X')]


def finite(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None


def get_quote(symbol):
    ticker = yf.Ticker(symbol)
    # Daily historical closes are more reliable for previous-close comparisons.
    daily = ticker.history(period='10d', interval='1d', auto_adjust=False)
    if daily.empty:
        raise ValueError('No daily history')
    closes = [finite(x) for x in daily['Close'].tolist()]
    closes = [x for x in closes if x is not None]
    if len(closes) < 2:
        raise ValueError('Not enough daily history')
    price, previous = closes[-1], closes[-2]
    # Intraday series used only for real sparkline points, not invented data.
    intraday = ticker.history(period='1d', interval='5m', auto_adjust=False)
    series = []
    if not intraday.empty:
        series = [finite(x) for x in intraday['Close'].tolist()]
        series = [round(x, 5) for x in series if x is not None]
    if not series:
        series = [round(x, 5) for x in closes[-10:]]
    change = (price / previous - 1) * 100 if previous else None
    return {
        'price': round(price, 4),
        'change_percent': round(change, 3) if change is not None else None,
        'sparkline': series[-72:],
        'source': 'Yahoo Finance (unofficial, via yfinance)',
        'as_of': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }


def main():
    existing = {}
    if OUT.exists():
        try:
            existing = json.loads(OUT.read_text(encoding='utf-8')).get('quotes', {})
        except (ValueError, OSError):
            pass
    quotes = {}
    successes = 0
    for key, symbol in SYMBOLS:
        try:
            quotes[key] = get_quote(symbol)
            successes += 1
            print(f'{key}: {quotes[key]["price"]}')
        except Exception as exc:
            print(f'WARNING {key}: {exc}')
            if key in existing:
                quotes[key] = existing[key]
                quotes[key]['stale'] = True
    if not successes and not quotes:
        raise RuntimeError('No quote data available')
    payload = {
        'updated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'note': 'Quotes may be delayed; market data is not guaranteed real-time.',
        'quotes': quotes,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Saved', OUT)


if __name__ == '__main__':
    main()
