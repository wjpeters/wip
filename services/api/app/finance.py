"""Authoritative Decimal-only paper engine. No networking, AI or fiscal inference."""

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from .contracts import OrderIntent, Quote

D = Decimal
CENT = D("0.01")
FEE_RATE = D("0.0016")
MAX_ORDER = D("25000")
MAX_EXPOSURE = D("0.50")


class PolicyError(ValueError):
    pass


def money(value):
    return D(value).quantize(CENT, rounding=ROUND_HALF_UP)


def initial_state():
    return {
        "cash": "100000.00",
        "reserve": "20000.00",
        "monthly_in": "500.00",
        "monthly_out": "0.00",
        "revision": 0,
        "positions": {},
        "fees": "0.00",
        "realized": "0.00",
    }


def calculate(intent: OrderIntent, quote: Quote, state: dict, instrument: dict):
    qty, limit = D(intent.quantity), D(intent.limit_price)
    cash, reserve = D(state["cash"]), D(state["reserve"])
    bid, ask = D(quote.bid), D(quote.ask)
    if quote.quality != "SIMULATED":
        raise PolicyError(
            "STALE_DATA: alleen actieve lokale fixtures zijn in deze release uitvoerbaar."
        )
    if (
        quote.instrument_id != intent.instrument_id
        or quote.venue_id != instrument["venue_id"]
    ):
        raise PolicyError("QUOTE_MISMATCH: instrument of handelsplaats wijkt af.")
    if qty <= 0 or limit <= 0 or bid <= 0 or ask < bid:
        raise PolicyError(
            "INVALID_AMOUNT: bedragen en aantal moeten positief zijn; ask moet minstens bid zijn."
        )
    if qty % D(instrument["lot_size"]) or limit % D(instrument["tick_size"]):
        raise PolicyError(
            "PRECISION: aantal of prijs past niet bij lot- of tickgrootte."
        )
    if qty * limit < D(instrument["min_notional"]) or qty * limit > MAX_ORDER:
        raise PolicyError(
            "ORDER_LIMIT: orderwaarde moet tussen minimum en EUR 25.000 liggen."
        )
    if (ask - bid) / bid > D("0.02"):
        raise PolicyError("SPREAD_TOO_WIDE: spread is groter dan 2%.")
    old = state["positions"].get(
        intent.instrument_id, {"quantity": "0", "cost": "0.00"}
    )
    held, cost = D(old["quantity"]), D(old["cost"])
    if intent.side == "SELL" and qty > held:
        raise PolicyError("NO_SHORT: onvoldoende vrije paperpositie.")
    if (
        intent.side == "BUY"
        and money(qty * limit) + money(qty * limit * FEE_RATE) > cash - reserve
    ):
        raise PolicyError(
            "BUFFER_LIMIT: volledige order overschrijdt cash boven de doelreserve."
        )
    crosses = ask <= limit if intent.side == "BUY" else bid >= limit
    fill = min(qty, D(quote.available_quantity)) if crosses else D("0")
    px = ask if intent.side == "BUY" else bid
    amount, fee = money(fill * px), money(fill * px * FEE_RATE)
    after = deepcopy(state)
    lines = []
    realized = D("0")
    if fill:
        if intent.side == "BUY":
            after["cash"] = str(cash - amount - fee)
            after["positions"][intent.instrument_id] = {
                "quantity": str(held + fill),
                "cost": str(cost + amount),
            }
            lines = [
                ("inventory:" + intent.instrument_id, amount),
                ("fees", fee),
                ("cash", -amount - fee),
            ]
        else:
            released = cost if fill == held else money(cost * fill / held)
            realized = amount - released
            after["cash"] = str(cash + amount - fee)
            after["positions"][intent.instrument_id] = {
                "quantity": str(held - fill),
                "cost": str(cost - released),
            }
            lines = [
                ("cash", amount - fee),
                ("inventory:" + intent.instrument_id, -released),
                ("fees", fee),
                ("realized_pnl", -realized),
            ]
        after["fees"] = str(D(state["fees"]) + fee)
        after["realized"] = str(D(state["realized"]) + realized)
    # Conservative cost exposure, including full requested order, across all instruments.
    exposure = sum((D(p["cost"]) for p in state["positions"].values()), D("0"))
    equity_at_cost = cash + exposure
    if (
        intent.side == "BUY"
        and exposure + money(qty * limit) > equity_at_cost * MAX_EXPOSURE
    ):
        raise PolicyError(
            "EXPOSURE_LIMIT: maximaal 50% van oefenvermogen tegen kostprijs."
        )
    if sum((v for _, v in lines), D("0")) != 0:
        raise AssertionError("Unbalanced journal")
    status = "CANCELED" if not fill else "FILLED" if fill == qty else "PARTIALLY_FILLED"
    return {
        "status": status,
        "fill_quantity": str(fill),
        "fill_price": str(px) if fill else None,
        "notional": str(amount),
        "fee": str(fee),
        "remaining_quantity": str(qty - fill),
        "remaining_status": "CANCELED" if fill < qty else "NONE",
        "cash_before": str(cash),
        "cash_after": after["cash"],
        "position_before": str(held),
        "position_after": after["positions"].get(intent.instrument_id, old)["quantity"],
        "buffer_before": str(cash - reserve),
        "buffer_after": str(D(after["cash"]) - reserve),
        "reserve": str(reserve),
        "realized": str(realized),
        "currency": "EUR",
        "mode": "PAPER",
        "reason": "IOC: niet direct uitvoerbaar restant vervalt. Liquiditeit en kosten zijn gesimuleerd.",
        "state_after": after,
        "postings": [(a, str(v)) for a, v in lines],
    }


def portfolio(state, quotes):
    positions = []
    for instrument_id, p in state["positions"].items():
        q = quotes[instrument_id]
        value = money(D(p["quantity"]) * D(q.last))
        positions.append(
            {
                "instrument_id": instrument_id,
                **p,
                "mark": q.last,
                "value": str(value),
                "unrealized": str(value - D(p["cost"])),
                "quality": q.quality,
            }
        )
    total = money(D(state["cash"]) + sum((D(p["value"]) for p in positions), D("0")))
    return {
        "scope": "PAPER_SCENARIO",
        "excluded_from_real_wealth": True,
        "cash": state["cash"],
        "reserve": state["reserve"],
        "buffer": str(D(state["cash"]) - D(state["reserve"])),
        "total": str(total),
        "positions": positions,
        "fees": state["fees"],
        "realized": state["realized"],
        "tax_status": "NOT_CALCULATED",
        "revision": state["revision"],
    }


def cash_path(state, months=24):
    cash = D(state["cash"])
    rows = []
    for month in range(months + 1):
        rows.append(
            {
                "month": month,
                "cash": str(cash),
                "reserve": state["reserve"],
                "buffer": str(cash - D(state["reserve"])),
            }
        )
        cash += D(state["monthly_in"]) - D(state["monthly_out"])
    return rows
