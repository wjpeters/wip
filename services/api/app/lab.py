"""Causal fixture replay/backtest. Read-only experiments cannot call the order gateway."""

from decimal import Decimal as D
from pydantic import Field
from typing import Literal
from .planning import Strict
from .contracts import DecimalString
from .accounting import amount, money
from .market import history
import hashlib
import json


class ReplayInput(Strict):
    instrument_id: Literal["sim:BTC-EUR", "sim:ETH-EUR", "sim:SOL-EUR"]
    interval: Literal["15m", "1u", "4u", "1d"] = "1u"
    cursor: int = Field(ge=0, le=119)


class BacktestInput(Strict):
    instrument_id: Literal["sim:BTC-EUR", "sim:ETH-EUR", "sim:SOL-EUR"]
    interval: Literal["15m", "1u", "4u", "1d"] = "1u"
    initial_cash: DecimalString = "10000"
    fee_bps: DecimalString = "16"
    slippage_bps: DecimalString = "10"
    short_window: int = Field(ge=2, le=30)
    long_window: int = Field(ge=5, le=60)
    allocation_percent: DecimalString = "25"
    start: int = Field(ge=0, le=100)
    end: int = Field(ge=10, le=119)


def as_of(events, timestamp):
    # Publication time is not knowledge time. Revisions only replace data after availability.
    result = {}
    for e in events:
        if e["first_available_at"] <= timestamp:
            previous = result.get(e["id"])
            if previous is None or (e["first_available_at"], e["revision"]) > (
                previous["first_available_at"],
                previous["revision"],
            ):
                result[e["id"]] = e
    return list(result.values())


def replay(p: ReplayInput):
    h = history(p.instrument_id, p.interval)
    rows = h["rows"][: p.cursor + 1]
    return {
        "rows": rows,
        "cursor": p.cursor,
        "remaining": len(h["rows"]) - len(rows),
        "quality": "SIMULATED",
        "knowledge_cutoff": rows[-1]["time"],
        "revision_policy": "Only events available by this replay cursor; no future bars returned.",
        "dataset_hash": hashlib.sha256(
            json.dumps(h, sort_keys=True).encode()
        ).hexdigest(),
    }


def backtest(p: BacktestInput):
    if p.short_window >= p.long_window or p.end <= p.start:
        raise ValueError("INVALID_BACKTEST_WINDOW")
    initial = amount(p.initial_cash)
    fee = amount(p.fee_bps) / 10000
    slip = amount(p.slippage_bps) / 10000
    allocation = amount(p.allocation_percent) / 100
    if (
        initial <= 0
        or not 0 <= fee <= D(".05")
        or not 0 <= slip <= D(".05")
        or not 0 < allocation <= 1
    ):
        raise ValueError("BACKTEST_LIMIT")
    data = history(p.instrument_id, p.interval)
    bars = data["rows"]
    cash = initial
    quantity = D(0)
    pending = None
    fills = []
    equity = []
    peak = initial
    drawdown = D(0)
    fees = D(0)
    turnover = D(0)
    for i in range(p.start, p.end + 1):
        row = bars[i]
        if pending:
            side, signal_i = pending
            price = amount(row["open"]) * (1 + slip if side == "BUY" else 1 - slip)
            if side == "BUY" and not quantity:
                budget = cash * allocation
                notional = budget / (1 + fee)
                q = notional / price
                cost = notional * fee
                cash -= notional + cost
                quantity = q
            elif side == "SELL" and quantity:
                q = quantity
                notional = q * price
                cost = notional * fee
                cash += notional - cost
                quantity = D(0)
            else:
                q = D(0)
                notional = D(0)
                cost = D(0)
            if q:
                fees += cost
                turnover += notional
                fills.append(
                    {
                        "side": side,
                        "signal_bar": signal_i,
                        "fill_bar": i,
                        "time": row["time"],
                        "price": money(price),
                        "quantity": str(q),
                        "fee": money(cost),
                    }
                )
            pending = None
        close = amount(row["close"])
        value = cash + quantity * close
        peak = max(peak, value)
        drawdown = max(drawdown, (peak - value) / peak)
        equity.append(
            {
                "bar": i,
                "time": row["time"],
                "value": money(value),
                "cash": money(cash),
                "position": str(quantity),
            }
        )
        # At close i, only bars <= i are eligible. Any signal fills at i+1 open.
        if i + 1 >= p.long_window:
            short = (
                sum(
                    (amount(b["close"]) for b in bars[i + 1 - p.short_window : i + 1]),
                    D(0),
                )
                / p.short_window
            )
            long = (
                sum(
                    (amount(b["close"]) for b in bars[i + 1 - p.long_window : i + 1]),
                    D(0),
                )
                / p.long_window
            )
            if short > long and not quantity:
                pending = ("BUY", i)
            elif short < long and quantity:
                pending = ("SELL", i)
    final = amount(equity[-1]["value"])
    benchmark = initial * amount(bars[p.end]["close"]) / amount(bars[p.start]["open"])
    return {
        "model_version": "sma-next-open-1.0",
        "quality": "SIMULATED",
        "inputs": p.model_dump(),
        "dataset_hash": hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest(),
        "equity": equity,
        "fills": fills,
        "ending_value": money(final),
        "return_percent": str((final / initial - 1) * 100),
        "max_drawdown_percent": str(drawdown * 100),
        "fees": money(fees),
        "turnover": money(turnover),
        "benchmark_before_costs": money(benchmark),
        "unexecuted_last_signal": pending is not None,
        "limitations": [
            "Synthetische bars, geen historisch providerbewijs.",
            "SMA-signaal bij slot, uitvoering pas op volgende open met opgegeven spread/slippage en kosten.",
            "Fractionele spotposities, geen orderboekcapaciteit of belasting. Eindpositie gewaardeerd, niet automatisch geliquideerd.",
            "Geen optimalisatie op uitkomst; kies aparte tijdvakken voor ontwikkeling en validatie.",
        ],
        "live_execution": False,
    }
