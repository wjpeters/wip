"""Reproducible cashflow and goal scenarios, isolated from order execution."""

from __future__ import annotations
from decimal import Decimal as D
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .contracts import DecimalString
from .accounting import amount, money
import hashlib
import json
import random
import math


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Goal(Strict):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=100)
    month: int = Field(ge=1, le=600)
    amount: DecimalString
    priority: Literal["ESSENTIAL", "OPTIONAL"] = "ESSENTIAL"


class Scenario(Strict):
    name: str = Field(min_length=1, max_length=100)
    scope: Literal["DEMO", "PERSONAL"]
    entity_id: str = Field(min_length=1, max_length=80)
    months: int = Field(ge=1, le=600)
    cash: DecimalString
    investments: DecimalString
    pension_capital: DecimalString
    monthly_income: DecimalString
    monthly_expenses: DecimalString
    monthly_investment: DecimalString
    monthly_pension: DecimalString
    monthly_tax_reserve: DecimalString
    emergency_reserve: DecimalString
    initial_tax_reserve: DecimalString
    annual_return_percent: DecimalString
    annual_pension_return_percent: DecimalString
    annual_inflation_percent: DecimalString
    annual_fee_percent: DecimalString
    stress_drop_percent: DecimalString
    stress_income_loss_months: int = Field(ge=0, le=60)
    goals: list[Goal] = Field(default_factory=list, max_length=40)
    source_revision: int = Field(ge=0)
    assumptions_note: str = Field(min_length=8, max_length=2000)


def validate(s):
    nonnegative = [
        "cash",
        "investments",
        "pension_capital",
        "monthly_income",
        "monthly_expenses",
        "monthly_investment",
        "monthly_pension",
        "monthly_tax_reserve",
        "emergency_reserve",
        "initial_tax_reserve",
    ]
    if any(amount(getattr(s, k)) < 0 for k in nonnegative):
        raise ValueError("NEGATIVE_PLAN_INPUT")
    if amount(s.initial_tax_reserve) > amount(s.cash):
        raise ValueError("TAX_RESERVE_EXCEEDS_CASH")
    for key in [
        "annual_return_percent",
        "annual_pension_return_percent",
        "annual_inflation_percent",
    ]:
        if not D("-50") <= amount(getattr(s, key)) <= D("50"):
            raise ValueError("RATE_OUT_OF_RANGE")
    if not D("0") <= amount(s.annual_fee_percent) <= D("10") or not D("0") <= amount(
        s.stress_drop_percent
    ) <= D("100"):
        raise ValueError("RATE_OUT_OF_RANGE")
    if len({g.id for g in s.goals}) != len(s.goals):
        raise ValueError("DUPLICATE_GOAL")
    if any(amount(g.amount) < 0 or g.month > s.months for g in s.goals):
        raise ValueError("GOAL_OUTSIDE_SCENARIO")


def path(s: Scenario, stress=False, monthly_returns=None):
    validate(s)
    cash = amount(s.cash)
    invest = amount(s.investments)
    pension = amount(s.pension_capital)
    tax = amount(s.initial_tax_reserve)
    reserve = amount(s.emergency_reserve)
    inflation = D(1)
    rows = []
    goals = []
    warnings = []
    net_flow = D(0)
    fee = amount(s.annual_fee_percent) / 1200
    rate = amount(s.annual_return_percent) / 1200
    prate = amount(s.annual_pension_return_percent) / 1200
    if stress:
        invest *= 1 - amount(s.stress_drop_percent) / 100
        pension *= 1 - amount(s.stress_drop_percent) / 100
    for month in range(s.months + 1):
        if month:
            inflation *= 1 + amount(s.annual_inflation_percent) / 1200
            income = (
                D(0)
                if stress and month <= s.stress_income_loss_months
                else amount(s.monthly_income)
            )
            expenses = amount(s.monthly_expenses) * inflation
            cash += income - expenses
            net_flow += income - expenses
            tax += amount(s.monthly_tax_reserve)
            free = max(D(0), cash - tax - reserve)
            pension_pay = min(free, amount(s.monthly_pension))
            cash -= pension_pay
            pension += pension_pay
            free -= pension_pay
            investment_pay = min(free, amount(s.monthly_investment))
            cash -= investment_pay
            invest += investment_pay
            if investment_pay < amount(s.monthly_investment) or pension_pay < amount(
                s.monthly_pension
            ):
                warnings.append(
                    {"month": month, "code": "CONTRIBUTION_LIMITED_BY_RESERVES"}
                )
            r = monthly_returns[month - 1] if monthly_returns is not None else rate
            invest *= max(D(0), 1 + r - fee)
            pension *= max(D(0), 1 + prate - fee)
            for g in [g for g in s.goals if g.month == month]:
                target = amount(g.amount) * inflation
                available = max(D(0), cash - tax - reserve)
                funded = available >= target
                if funded:
                    cash -= target
                    net_flow -= target
                goals.append(
                    {
                        "id": g.id,
                        "name": g.name,
                        "month": month,
                        "priority": g.priority,
                        "inflation_adjusted_target": money(target),
                        "available_cash": money(available),
                        "funded": funded,
                        "shortfall": money(max(D(0), target - available)),
                    }
                )
        total = cash + invest
        rows.append(
            {
                "month": month,
                "cash": money(cash),
                "investments": money(invest),
                "pension_locked": money(pension),
                "tax_reserve": money(tax),
                "available_above_reserves": money(cash - tax - reserve),
                "liquid_wealth": money(total),
                "real_liquid_wealth": money(total / inflation),
                "total_including_locked": money(total + pension),
            }
        )
    return {
        "rows": rows,
        "goals": goals,
        "warnings": warnings,
        "cash_shortfall_month": next(
            (r["month"] for r in rows if amount(r["available_above_reserves"]) < 0),
            None,
        ),
        "net_external_flow": money(net_flow),
        "unfunded_goals": sum(not g["funded"] for g in goals),
    }


def calculate(s: Scenario):
    validate(s)
    base = path(s)
    stress = path(s, True)
    serialized = s.model_dump()
    key = hashlib.sha256(json.dumps(serialized, sort_keys=True).encode()).hexdigest()
    return {
        "schema_version": 1,
        "model_version": "monthly-nominal-1.0",
        "input_hash": key,
        "inputs": serialized,
        "base": base,
        "stress": stress,
        "delta_end_liquid": money(
            amount(stress["rows"][-1]["liquid_wealth"])
            - amount(base["rows"][-1]["liquid_wealth"])
        ),
        "assumptions": [
            "Nominale jaarpercentages gedeeld door 12; geen beloofd rendement.",
            "Kosten maandelijks op belegd vermogen; inflatie op uitgaven en doelen.",
            "Pensioen is geblokkeerd vermogen; uitkeringsbelasting is niet automatisch berekend.",
            "Belastingreserve is een deel van cash, geen extra bezit. Maandreserve is een eigen aanname, geen aanslag.",
            "Stortingen alleen uit cash boven beide reserves; geen automatische verkoop of lening.",
            "Stress: één koersschok bij aanvang en tijdelijk nul inkomen.",
        ],
        "is_prediction": False,
    }


def monte_carlo(s: Scenario, seed: int, paths: int, volatility: str):
    if paths < 20 or paths > 500:
        raise ValueError("PATH_LIMIT")
    vol = amount(volatility)
    if vol < 0 or vol > 100:
        raise ValueError("VOLATILITY_RANGE")
    validate(s)
    rng = random.Random(seed)
    ends = []
    success = 0
    for _ in range(paths):
        # Approximate statistics only. Decimal conversion precedes all financial arithmetic.
        returns = [
            D(
                str(
                    max(
                        -1.0,
                        rng.gauss(
                            float(amount(s.annual_return_percent) / 1200),
                            float(vol) / 100 / math.sqrt(12),
                        ),
                    )
                )
            )
            for _ in range(s.months)
        ]
        result = path(s, monthly_returns=returns)
        ends.append(amount(result["rows"][-1]["liquid_wealth"]))
        success += (
            result["unfunded_goals"] == 0 and result["cash_shortfall_month"] is None
        )
    ends.sort()
    return {
        "model_version": "iid-normal-monthly-1.0",
        "seed": seed,
        "paths": paths,
        "p10": money(ends[int((paths - 1) * 0.1)]),
        "p50": money(ends[int((paths - 1) * 0.5)]),
        "p90": money(ends[int((paths - 1) * 0.9)]),
        "sample_goal_success_fraction": str(D(success) / paths),
        "limitations": [
            "Benaderende simulatiestatistiek. Onafhankelijke normaal verdeelde maandrendementen; geen staart-, correlatie- of regimegarantie.",
            "Doelfractie is alleen de frequentie binnen dit gekozen model, geen persoonlijke kans op succes.",
        ],
    }


def trade_impact(cash, trade_amount, fee, tax_reserve, long_term_reserve, trading_pot):
    values = [
        amount(v)
        for v in [cash, trade_amount, fee, tax_reserve, long_term_reserve, trading_pot]
    ]
    if any(v < 0 for v in values):
        raise ValueError("NEGATIVE_IMPACT_INPUT")
    cash, trade, fee, tax, long, pot = values
    after = cash - trade - fee
    return {
        "cash_before": money(cash),
        "cash_after": money(after),
        "tax_reserve": money(tax),
        "long_term_reserve": money(long),
        "trading_pot_before": money(pot),
        "trading_pot_after": money(pot - trade - fee),
        "available_before": money(cash - tax - long),
        "available_after": money(after - tax - long),
        "within_plan": after >= tax + long and trade + fee <= pot,
        "execution_authorized": False,
        "tax_effect": None,
        "quality": "WHAT_IF_NOT_EXECUTION_PREVIEW",
    }
