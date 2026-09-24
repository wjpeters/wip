"""NL 2025 deterministic, bounded calculators. No model participates in money math.
Concept outputs remain concepts until this exact ruleset passes human review.
"""

from __future__ import annotations
from decimal import Decimal as D, ROUND_FLOOR, ROUND_HALF_UP
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .contracts import DecimalString
from .accounting import amount, money
import hashlib
import json


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaxContext(Strict):
    year: Literal[2025] = 2025
    resident_full_year: bool
    inputs_complete: bool
    special_cases: list[str] = Field(default_factory=list, max_length=20)


class Box1Input(TaxContext):
    taxable_income: DecimalString
    age_regime: Literal[
        "UNDER_AOW_ALL_YEAR",
        "AOW_ALL_YEAR_BORN_1946_PLUS",
        "AOW_ALL_YEAR_BORN_BEFORE_1946",
    ]


class Box2Input(TaxContext):
    gross_income: DecimalString
    dividend_tax_withheld: DecimalString = "0"


class ActualReturn(Strict):
    complete: bool
    bank_interest: DecimalString
    investment_income: DecimalString
    investments_start: DecimalString
    investments_end: DecimalString
    purchases: DecimalString
    sales: DecimalString
    debt_interest: DecimalString


class Box3Input(TaxContext):
    savings: DecimalString
    other_assets: DecimalString
    debts: DecimalString
    fiscal_partner_all_year: bool
    allocation_percent: DecimalString = "100"
    actual: ActualReturn | None = None


class PensionHistory(Strict):
    year: int = Field(ge=2015, le=2024)
    unused_room: DecimalString
    evidence: str = Field(min_length=1, max_length=200)


class PensionInput(TaxContext):
    eligible_age: bool
    income_previous_year: DecimalString
    income_year: Literal[2024] = 2024
    regime: Literal["NO_PENSION", "TRANSITION_FACTOR_A", "WTP_CONFIRMED_UPO"]
    factor_a: DecimalString = "0"
    upo_deduction: DecimalString = "0"
    net_pension_premium: DecimalString = "0"
    contribution_paid: DecimalString
    history_complete: bool
    history: list[PensionHistory] = Field(default_factory=list, max_length=10)


class GiftInput(TaxContext):
    kind: Literal["GIFT", "INHERITANCE"]
    relation: Literal["CHILD", "GRANDCHILD", "OTHER"]
    gross_acquisition: DecimalString
    earlier_same_year: DecimalString = "0"
    earlier_tax: DecimalString = "0"
    payer: Literal["RECIPIENT"] = "RECIPIENT"


BASE = "https://www.belastingdienst.nl/wps/wcm/connect/"
SOURCES = [
    {
        "id": "box1",
        "url": BASE
        + "bldcontentnl/belastingdienst/prive/inkomstenbelasting/heffingskortingen_boxen_tarieven/boxen_en_tarieven/box_1/",
        "topic": "Box 1 tarieven",
    },
    {
        "id": "box2",
        "url": BASE
        + "bldcontentnl/belastingdienst/prive/vermogen_en_aanmerkelijk_belang/aanmerkelijk_belang/inkomsten_uit_aanmerkelijk_belang/",
        "topic": "Box 2 bruto en voorheffing",
    },
    {
        "id": "box3",
        "url": BASE + "nl/box-3/content/berekening-box-3-inkomen-2025",
        "topic": "Box 3 forfait 2025",
    },
    {
        "id": "actual",
        "url": BASE
        + "nl/box-3/content/rekenvoorbeelden-berekening-werkelijk-rendement",
        "topic": "Werkelijk rendement",
    },
    {
        "id": "pension",
        "url": BASE + "fisin/fisin2025/uitgaven_voor_inkomensvoorzieningen",
        "topic": "Lijfrente en tienjaarsperiode",
    },
    {
        "id": "pension-regimes",
        "url": "https://kennisgroepen.belastingdienst.nl/publicaties/kg07020243-vragen-en-antwoorden-over-de-jaarruimteberekening-en-de-opbouw-van-pensioenaanspraken/",
        "topic": "Factor A en WTP",
    },
    {
        "id": "parameters-2025",
        "url": "https://open.overheid.nl/documenten/dcbb490f-d406-4842-ac33-b5c397e19df0/file",
        "topic": "Officiële fiscale parameters 2025",
    },
    {
        "id": "indexation",
        "url": "https://zoek.officielebekendmakingen.nl/stcrt-2025-40487.html",
        "topic": "Bestaande 2025 franchise/reserveringsgrens versus wijzigingen 2026",
    },
    {
        "id": "gift-rates",
        "url": BASE + "nl/schenken/content/tarieven-schenkbelasting-2025",
        "topic": "Tarieven schenkbelasting 2025",
    },
    {
        "id": "gift-exemptions",
        "url": BASE
        + "nl/schenken/content/tot-welk-bedrag-belastingvrij-schenken-in-2025",
        "topic": "Jaarlijkse schenkvrijstellingen",
    },
    {
        "id": "estate-exemptions",
        "url": BASE + "nl/erfbelasting/content/vrijstelling-erfbelasting-2025",
        "topic": "Erfvrijstellingen 2025",
    },
    {
        "id": "estate-rates",
        "url": "https://www.belastingdienst.nl/wps/wcm/connect/nl/erfbelasting/content/tarieven-erfbelasting-2025",
        "topic": "Tarieven erfbelasting 2025",
    },
]
PARAMETERS = {
    "box1": {
        "thresholds": ["38441", "76817"],
        "rates": ["0.3582", "0.3748", "0.4950"],
        "aow_first_rate": "0.1792",
        "older_first_threshold": "40502",
    },
    "box2": {"threshold": "67804", "rates": ["0.245", "0.31"]},
    "box3": {
        "savings": "0.0137",
        "other": "0.0588",
        "debt": "0.0270",
        "debt_threshold": "3800",
        "exemption": "57684",
        "rate": "0.36",
    },
    "pension": {
        "cap": "137800",
        "franchise": "18475",
        "percentage": "0.30",
        "factor_a": "6.27",
        "net_factor": "0.505",
        "reserve_cap": "42108",
    },
    "gift_estate": {
        "threshold": "154197",
        "child": ["0.10", "0.20"],
        "grandchild": ["0.18", "0.36"],
        "other": ["0.30", "0.40"],
        "gift_child": "6713",
        "gift_other": "2690",
        "estate_child": "25490",
        "estate_grandchild": "25490",
        "estate_other": "2690",
    },
}
VERSION = "nl-2025-scope-1.0.0"


def rule_hash():
    # Bind approvals to both formulas and parameters; a deploy cannot inherit approval.
    from pathlib import Path

    return hashlib.sha256(
        Path(__file__).read_bytes() + json.dumps(PARAMETERS, sort_keys=True).encode()
    ).hexdigest()


def registry():
    return {
        "version": VERSION,
        "hash": rule_hash(),
        "year": 2025,
        "jurisdiction": "NL",
        "currency": "EUR",
        "legal_status": "ENACTED_2025_SCOPED",
        "effective_from": "2025-01-01",
        "effective_to": "2025-12-31",
        "review_status": "NEEDS_HUMAN_REVIEW",
        "parameters": PARAMETERS,
        "sources": SOURCES,
        "scope": [
            "Box 1 schijventarief vóór heffingskortingen en voorheffingen",
            "Box 2 positief regulier inkomen, opgegeven dividendvoorheffing",
            "Box 3 volledig jaar: gewone banktegoeden, beleggingen en aftrekbare schulden; partnerverdeling expliciet",
            "Lijfrente 2025 met bevestigd pensioenregime; historische ruimte uit bewijsstukken",
            "Gewone geldschenking/nalatenschap aan kind, kleinkind of overige verkrijger",
        ],
        "exclusions": [
            "Geen volledige IB-aangifte of berekening van heffingskortingen",
            "Geen emigratie, overlijden in belastingjaar, buitenlandse vrijstelling, groene vrijstellingen, verliesverrekening of overgangsrecht",
            "Geen Box 3 vastgoed/crypto-werkelijk-rendement zonder vooraf afzonderlijk berekende volledige input",
            "Geen partner-erfvrijstelling/pensioenimputatie, vruchtgebruik, BOR, éénmalige schenkvrijstelling of vrij-van-rechtberekening",
        ],
    }


def positive(value):
    x = amount(value)
    if x < 0:
        raise ValueError("NEGATIVE_TAX_INPUT")
    return x


def whole(x):
    return x.quantize(D("1"), rounding=ROUND_FLOOR)


def context(data):
    issues = []
    if not data.resident_full_year:
        issues.append("RESIDENCY_OUTSIDE_SCOPE")
    if not data.inputs_complete:
        issues.append("INCOMPLETE_INPUT")
    issues.extend("REVIEW:" + s for s in data.special_cases)
    if issues:
        raise ValueError("; ".join(issues))


def progressive(value, thresholds, rates):
    total = D(0)
    lower = D(0)
    steps = []
    for upper, rate in zip([*thresholds, None], rates):
        taxable = max(
            D(0), min(value, upper) - lower if upper is not None else value - lower
        )
        tax = taxable * rate
        total += tax
        steps.append(
            {"base": money(taxable), "rate": str(rate), "tax_unrounded": str(tax)}
        )
        if upper is not None:
            lower = upper
    return total, steps


def box1(data: Box1Input):
    context(data)
    p = PARAMETERS["box1"]
    income = positive(data.taxable_income)
    thresholds = list(map(D, p["thresholds"]))
    rates = list(map(D, p["rates"]))
    if data.age_regime != "UNDER_AOW_ALL_YEAR":
        rates[0] = D(p["aow_first_rate"])
    if data.age_regime == "AOW_ALL_YEAR_BORN_BEFORE_1946":
        thresholds[0] = D(p["older_first_threshold"])
    value, steps = progressive(income, thresholds, rates)
    return {
        "gross_tax_before_credits": money(value),
        "taxable_income": money(income),
        "steps": steps,
        "net_tax": None,
        "limitations": [
            "Heffingskortingen, tariefsaanpassing aftrekposten, Zvw en voorheffingen niet berekend. Invoer is reeds vastgesteld belastbaar inkomen."
        ],
    }


def box2(data: Box2Input):
    context(data)
    p = PARAMETERS["box2"]
    income = positive(data.gross_income)
    withheld = positive(data.dividend_tax_withheld)
    if withheld > income:
        raise ValueError("WITHHOLDING_EXCEEDS_GROSS")
    value, steps = progressive(income, [D(p["threshold"])], list(map(D, p["rates"])))
    return {
        "tax": money(value),
        "gross_income": money(income),
        "already_withheld": money(withheld),
        "received_cash": money(income - withheld),
        "remaining_tax": money(value - withheld),
        "after_box2_tax": money(income - value),
        "steps": steps,
        "limitations": [
            "Geen heffingskortingen of persoonlijke verliesverrekening; bronheffing wordt éénmaal verrekend."
        ],
    }


def box3(data: Box3Input):
    context(data)
    p = PARAMETERS["box3"]
    bank = positive(data.savings)
    assets = positive(data.other_assets)
    debts = positive(data.debts)
    people = 2 if data.fiscal_partner_all_year else 1
    share = positive(data.allocation_percent) / 100
    if share > 1 or (people == 1 and share != 1):
        raise ValueError("INVALID_PARTNER_ALLOCATION")
    eligible = max(D(0), debts - D(p["debt_threshold"]) * people)
    net = max(D(0), bank + assets - eligible)
    base = max(D(0), net - D(p["exemption"]) * people)
    # Published examples round intermediate euro yields down and percentage to 2 decimals.
    bank_y = whole(bank * D(p["savings"]))
    asset_y = whole(assets * D(p["other"]))
    debt_y = whole(eligible * D(p["debt"]))
    deemed = max(D(0), bank_y + asset_y - debt_y)
    proportion = (
        ((base * share / net) * 100).quantize(D(".01"), rounding=ROUND_HALF_UP) / 100
        if net
        else D(0)
    )
    income = whole(deemed * proportion)
    forfait = whole(income * D(p["rate"]))
    actual_income = None
    actual_tax = None
    if data.actual is not None:
        a = data.actual
        if not a.complete:
            raise ValueError("INCOMPLETE_ACTUAL_RETURN")
        actual_income = max(
            D(0),
            positive(a.bank_interest)
            + amount(a.investment_income)
            + positive(a.investments_end)
            - positive(a.investments_start)
            - positive(a.purchases)
            + positive(a.sales)
            - positive(a.debt_interest),
        )
        actual_income = whole(actual_income * share)
        actual_tax = whole(actual_income * D(p["rate"]))
    selected = min(forfait, actual_tax) if actual_tax is not None else forfait
    return {
        "tax": money(selected),
        "forfait_tax": money(forfait),
        "actual_tax": None if actual_tax is None else money(actual_tax),
        "actual_income": None if actual_income is None else money(actual_income),
        "taxable_income": money(income),
        "eligible_debt": money(eligible),
        "net_assets": money(net),
        "taxable_base": money(base * share),
        "allocation_percent": data.allocation_percent,
        "taxable_proportion_percent": str(proportion * 100),
        "forfait_return": money(deemed),
        "method": "ACTUAL"
        if actual_tax is not None and actual_tax < forfait
        else "FORFAIT",
        "limitations": [
            "Werkelijk rendement alleen vergeleken wanneer alle opbrengsten en waardemutaties compleet zijn verklaard. Geen kostenaftrek behalve schuld­rente. Geen heffingskortingen berekend."
        ],
    }


def pension(data: PensionInput):
    context(data)
    if not data.eligible_age:
        raise ValueError("AGE_NOT_ELIGIBLE")
    p = PARAMETERS["pension"]
    income = positive(data.income_previous_year)
    factor = positive(data.factor_a)
    upo = positive(data.upo_deduction)
    net = positive(data.net_pension_premium)
    if data.regime == "NO_PENSION" and (factor or upo or net):
        raise ValueError("PENSION_REGIME_CONFLICT")
    if data.regime == "TRANSITION_FACTOR_A" and upo:
        raise ValueError("PENSION_REGIME_CONFLICT")
    if data.regime == "WTP_CONFIRMED_UPO" and (factor or net):
        raise ValueError("UPO_MUST_INCLUDE_ALL_CONFIRMED_DEDUCTIONS")
    deduction = (
        factor * D(p["factor_a"]) + net / D(p["net_factor"])
        if data.regime == "TRANSITION_FACTOR_A"
        else upo
    )
    base = max(D(0), min(income, D(p["cap"])) - D(p["franchise"]))
    annual = max(D(0), base * D(p["percentage"]) - deduction)
    years = {h.year for h in data.history}
    if len(years) != len(data.history):
        raise ValueError("DUPLICATE_PENSION_YEAR")
    complete = data.history_complete and years == set(range(2015, 2025))
    reserve = (
        min(
            D(p["reserve_cap"]),
            sum((positive(h.unused_room) for h in data.history), D(0)),
        )
        if complete
        else None
    )
    paid = positive(data.contribution_paid)
    used = []
    remaining = paid
    if complete:
        room = reserve
        for h in sorted(data.history, key=lambda h: h.year):
            take = min(remaining, room, positive(h.unused_room))
            used.append(
                {
                    "year": h.year,
                    "used": money(take),
                    "remaining": money(positive(h.unused_room) - take),
                    "expires_after": h.year + 10,
                }
            )
            remaining -= take
            room -= take
    annual_used = min(remaining, annual) if complete else None
    return {
        "income_year": 2024,
        "premium_base": money(base),
        "pension_deduction": money(deduction),
        "annual_room": money(annual),
        "reserve_room": None if reserve is None else money(reserve),
        "reserve_status": "COMPLETE" if complete else "MISSING_HISTORICAL_EVIDENCE",
        "missing_years": sorted(set(range(2015, 2025)) - years),
        "history_usage": used,
        "annual_used": None if annual_used is None else money(annual_used),
        "deductible_paid": money(paid - remaining + annual_used) if complete else None,
        "not_deductible": money(max(D(0), remaining - annual)) if complete else None,
        "limitations": [
            "Historische ruimte wordt niet geraden. UPO-aftrek voor WTP moet door de uitvoerder bevestigd zijn. Bedragen op centen zijn scenario-uitkomsten, geen afgeronde aangiftevelden."
        ],
    }


def gift(data: GiftInput):
    context(data)
    p = PARAMETERS["gift_estate"]
    gross = positive(data.gross_acquisition)
    earlier = positive(data.earlier_same_year)
    earlier_tax = positive(data.earlier_tax)
    if data.kind == "INHERITANCE" and (earlier or earlier_tax):
        raise ValueError("INHERITANCE_NOT_ANNUAL_GIFT")
    relation = data.relation.lower()
    exemption = (
        D(p["gift_child" if relation == "child" else "gift_other"])
        if data.kind == "GIFT"
        else D(p["estate_" + relation])
    )
    base = max(D(0), gross + earlier - exemption)
    total, steps = progressive(base, [D(p["threshold"])], list(map(D, p[relation])))
    if earlier_tax > total:
        raise ValueError("PREVIOUS_TAX_REQUIRES_REVIEW")
    return {
        "tax": money(total - earlier_tax),
        "total_tax": money(total),
        "exemption": money(exemption),
        "taxable_acquisition": money(base),
        "net_acquisition": money(gross - (total - earlier_tax)),
        "steps": steps,
        "limitations": [
            "Relatie en samengevoegde schenkingen van partners/ouders expliciet controleren. Ontvanger betaalt belasting; gewone geldverkrijging zonder bijzondere voorwaarden."
        ],
    }


CALCULATORS = {
    "box1": (Box1Input, box1),
    "box2": (Box2Input, box2),
    "box3": (Box3Input, box3),
    "pension": (PensionInput, pension),
    "gift": (GiftInput, gift),
}


def calculate(kind=None, inputs=None, approved_hash=None, concept=False):
    if not concept and approved_hash != rule_hash():
        raise ValueError("UNAPPROVED_RULESET")
    if kind not in CALCULATORS:
        raise ValueError("UNKNOWN_CALCULATOR")
    model, fn = CALCULATORS[kind]
    data = model.model_validate(inputs)
    output = fn(data)
    return {
        "schema_version": 1,
        "calculator": kind,
        "rule_version": VERSION,
        "rule_hash": rule_hash(),
        "status": "CONCEPT" if concept else "REVIEWED_SCOPED_RESULT",
        "currency": "EUR",
        "inputs": data.model_dump(),
        "result": output,
        "source_ids": [s["id"] for s in SOURCES],
        "is_tax_return": False,
    }
