"""Estate inventory/checklist and ordinary gift scenario; never generates legal instruments."""

from decimal import Decimal as D
from pydantic import Field
from typing import Literal
from .planning import Strict
from .contracts import DecimalString
from .accounting import amount, money
from .tax import GiftInput, gift


class Beneficiary(Strict):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    relation: Literal["CHILD", "GRANDCHILD", "OTHER"]
    percentage: DecimalString


class EstatePlan(Strict):
    name: str = Field(min_length=1, max_length=120)
    gross_assets: DecimalString
    debts: DecimalString
    funeral_costs: DecimalString
    beneficiaries: list[Beneficiary] = Field(min_length=1, max_length=30)
    complex_cases: list[str] = Field(default_factory=list, max_length=30)
    document_ids: list[str] = Field(default_factory=list, max_length=30)
    notes: str = Field(max_length=2000)


def assess(plan: EstatePlan):
    assets, debts, costs = map(
        amount, [plan.gross_assets, plan.debts, plan.funeral_costs]
    )
    if min(assets, debts, costs) < 0:
        raise ValueError("NEGATIVE_ESTATE_INPUT")
    if len({b.id for b in plan.beneficiaries}) != len(plan.beneficiaries):
        raise ValueError("DUPLICATE_BENEFICIARY")
    if (
        any(amount(b.percentage) <= 0 for b in plan.beneficiaries)
        or sum((amount(b.percentage) for b in plan.beneficiaries), D(0)) != 100
    ):
        raise ValueError("SHARES_MUST_TOTAL_100")
    net = max(D(0), assets - debts - costs)
    outcomes = []
    for b in plan.beneficiaries:
        allocation = net * amount(b.percentage) / 100
        result = (
            None
            if plan.complex_cases
            else gift(
                GiftInput(
                    resident_full_year=True,
                    inputs_complete=True,
                    kind="INHERITANCE",
                    relation=b.relation,
                    gross_acquisition=money(allocation),
                )
            )
        )
        outcomes.append(
            {**b.model_dump(), "gross_share": money(allocation), "tax_concept": result}
        )
    return {
        "net_estate": money(net),
        "beneficiaries": outcomes,
        "review_required": True,
        "calculation_blocked": bool(plan.complex_cases),
        "review_reasons": plan.complex_cases,
        "checklist": [
            "Controleer testament, erfgenamen en partnerstatus met een notaris.",
            "Controleer juridische en economische eigendom en waarderingsdatum.",
            "Leg schulden, eerdere schenkingen en polissen vast.",
            "Controleer minderjarigen, ondernemingsvermogen en internationale aspecten.",
            "Bewaar originele bewijsstukken; dit scenario verandert geen testament of eigendom.",
        ],
        "legal_document": False,
    }
