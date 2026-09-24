"""Canonical indicators on original bars; Decimal throughout, no forward data."""

from decimal import Decimal as D
from datetime import datetime, timezone


def ema(values, period):
    result = [None] * len(values)
    if len(values) < period:
        return result
    current = sum(values[:period], D(0)) / period
    result[period - 1] = current
    alpha = D(2) / (period + 1)
    for i in range(period, len(values)):
        current = values[i] * alpha + current * (1 - alpha)
        result[i] = current
    return result


def enrich(history):
    rows = history["rows"]
    close = [D(r["close"]) for r in rows]
    fast = ema(close, 12)
    slow = ema(close, 26)
    e20 = ema(close, 20)
    macd = [None if a is None or b is None else a - b for a, b in zip(fast, slow)]
    sig = ema([v for v in macd if v is not None], 9)
    signal = [None] * (len(macd) - len(sig)) + sig
    gains = losses = atr = None
    vsum = psum = D(0)
    day = None
    result = []

    def serial(v):
        return None if v is None else str(v.quantize(D(".00000001")))

    for i, row in enumerate(rows):
        high, low, c, volume = map(
            D, [row["high"], row["low"], row["close"], row["volume"]]
        )
        if high < low or not low <= c <= high or volume < 0:
            raise ValueError("INVALID_INDICATOR_BAR")
        if i and row["time"] <= rows[i - 1]["time"]:
            raise ValueError("BARS_MUST_BE_ORDERED")
        tr = (
            max(high - low, abs(high - close[i - 1]), abs(low - close[i - 1]))
            if i
            else high - low
        )
        if i == 13:
            atr = (
                sum(
                    (
                        max(
                            D(r["high"]) - D(r["low"]),
                            abs(D(r["high"]) - close[j - 1]),
                            abs(D(r["low"]) - close[j - 1]),
                        )
                        if j
                        else D(r["high"]) - D(r["low"])
                        for j, r in enumerate(rows[:14])
                    ),
                    D(0),
                )
                / 14
            )
        elif i > 13:
            atr = (atr * 13 + tr) / 14
        rsi = None
        if i == 14:
            diffs = [close[j] - close[j - 1] for j in range(1, 15)]
            gains = sum((max(d, D(0)) for d in diffs), D(0)) / 14
            losses = sum((max(-d, D(0)) for d in diffs), D(0)) / 14
        elif i > 14:
            delta = c - close[i - 1]
            gains = (gains * 13 + max(delta, D(0))) / 14
            losses = (losses * 13 + max(-delta, D(0))) / 14
        if i >= 14:
            rsi = (
                D(50)
                if gains == losses == 0
                else D(100)
                if losses == 0
                else D(100) - D(100) / (1 + gains / losses)
            )
        current_day = datetime.fromtimestamp(row["time"], timezone.utc).date()
        if current_day != day:
            day = current_day
            vsum = psum = D(0)
        vsum += volume
        psum += (high + low + c) / 3 * volume
        result.append(
            {
                **row,
                "ema20": serial(e20[i]),
                "rsi14": serial(rsi),
                "atr14": serial(atr),
                "macd": serial(macd[i]),
                "macd_signal": serial(signal[i]),
                "vwap": serial(psum / vsum) if vsum else None,
            }
        )
    return {
        **history,
        "rows": result,
        "adjustment": "RAW",
        "indicator_version": "decimal-wilder-1",
        "vwap_anchor": "UTC calendar day; typical price (H+L+C)/3, actual supplied base volume",
        "warmup": "Null until sufficient original bars; no look-ahead",
    }


def adjust_split(rows, effective_time, numerator, denominator):
    n, d = D(numerator), D(denominator)
    if n <= 0 or d <= 0:
        raise ValueError("INVALID_SPLIT")
    return [
        {
            **r,
            **(
                {k: str(D(r[k]) * d / n) for k in ["open", "high", "low", "close"]}
                | {"volume": str(D(r["volume"]) * n / d)}
                if r["time"] < effective_time
                else {}
            ),
        }
        for r in rows
    ]
