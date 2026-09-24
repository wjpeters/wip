import base64
from decimal import Decimal as D
import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError
from app import tax, planning, rules, lab, vault, estate

COMMON = {"resident_full_year": True, "inputs_complete": True}


def calc(calculator, **values):
    return tax.calculate(calculator, {**COMMON, **values}, concept=True)["result"]


def test_official_examples():
    assert rules.test_vectors()["passed"]


def test_rule_approval_is_bound_to_formula():
    with pytest.raises(ValueError, match="UNAPPROVED"):
        tax.calculate("box2", {**COMMON, "gross_income": "10000"})
    assert (
        tax.calculate(
            "box2", {**COMMON, "gross_income": "10000"}, approved_hash=tax.rule_hash()
        )["status"]
        == "REVIEWED_SCOPED_RESULT"
    )


def test_tax_scope_blocks_incomplete_foreign_and_special():
    for bad in [
        {"inputs_complete": False},
        {"resident_full_year": False},
        {"special_cases": ["EMIGRATION"]},
    ]:
        with pytest.raises(ValueError):
            calc("box2", gross_income="10000", **bad)
    with pytest.raises(ValidationError):
        calc("box2", gross_income="10000", year=2026)


def test_box1_brackets_and_aow_no_fabricated_net():
    first = calc("box1", taxable_income="38441", age_regime="UNDER_AOW_ALL_YEAR")
    assert D(first["gross_tax_before_credits"]) == D("13769.57")
    assert first["net_tax"] is None
    aow = calc("box1", taxable_income="38441", age_regime="AOW_ALL_YEAR_BORN_1946_PLUS")
    assert D(aow["gross_tax_before_credits"]) == D("6888.63")


def test_box2_withholding_not_tax_twice():
    result = calc("box2", gross_income="10000", dividend_tax_withheld="1500")
    assert result["received_cash"] == "8500.00" and result["remaining_tax"] == "950.00"
    assert result["after_box2_tax"] == "7550.00"
    with pytest.raises(ValueError):
        calc("box2", gross_income="-1")


def test_box3_actual_uses_capital_changes_not_only_cash_income():
    inputs = {
        "savings": "100000",
        "other_assets": "150000",
        "debts": "0",
        "fiscal_partner_all_year": False,
        "actual": {
            "complete": True,
            "bank_interest": "1200",
            "investment_income": "500",
            "investments_start": "150000",
            "investments_end": "160000",
            "purchases": "1200",
            "sales": "3000",
            "debt_interest": "0",
        },
    }
    r = calc("box3", **inputs)
    assert r["actual_income"] == "13500.00"
    assert D(r["tax"]) <= D(r["actual_tax"])
    inputs["actual"]["investments_end"] = "140000"
    r = calc("box3", **inputs)
    assert r["actual_tax"] == "0.00"
    inputs["actual"]["complete"] = False
    with pytest.raises(ValueError, match="INCOMPLETE_ACTUAL"):
        calc("box3", **inputs)


def test_box3_debt_threshold_exemption_and_partner_allocation():
    assert (
        calc(
            "box3",
            savings="57684",
            other_assets="0",
            debts="0",
            fiscal_partner_all_year=False,
        )["tax"]
        == "0.00"
    )
    with pytest.raises(ValueError):
        calc(
            "box3",
            savings="150000",
            other_assets="0",
            debts="0",
            fiscal_partner_all_year=False,
            allocation_percent="50",
        )
    assert (
        calc(
            "box3",
            savings="1",
            other_assets="0",
            debts="999999",
            fiscal_partner_all_year=False,
        )["tax"]
        == "0.00"
    )


def pension(**overrides):
    return calc(
        "pension",
        **{
            "eligible_age": True,
            "income_previous_year": "60000",
            "regime": "TRANSITION_FACTOR_A",
            "factor_a": "1000",
            "contribution_paid": "12000",
            "history_complete": False,
            **overrides,
        },
    )


def test_pension_regime_and_missing_history():
    r = pension()
    assert (
        r["annual_room"] == "6187.50"
        and r["reserve_room"] is None
        and r["deductible_paid"] is None
    )
    assert (
        pension(regime="NO_PENSION", factor_a="0", income_previous_year="200000")[
            "annual_room"
        ]
        == "35797.50"
    )
    with pytest.raises(ValueError):
        pension(regime="WTP_CONFIRMED_UPO")


def test_pension_oldest_first_reserve_limit_and_no_guessed_years():
    history = [
        {
            "year": year,
            "unused_room": "1000",
            "evidence": "Bevestigde officiële berekening",
        }
        for year in range(2015, 2025)
    ]
    r = pension(history=history, history_complete=True)
    assert (
        r["reserve_room"] == "10000.00"
        and r["annual_used"] == "2000.00"
        and r["deductible_paid"] == "12000.00"
    )
    assert r["history_usage"][0]["year"] == 2015
    assert pension(history=history[:-1], history_complete=True)["reserve_room"] is None
    with pytest.raises(ValueError):
        pension(history=[history[0], history[0]])


def test_gift_no_double_exemption_and_excluded_cases():
    r = calc(
        "gift",
        kind="GIFT",
        relation="CHILD",
        gross_acquisition="10000",
        earlier_same_year="6713",
    )
    assert r["tax"] == "1000.00"
    assert (
        calc("gift", kind="INHERITANCE", relation="CHILD", gross_acquisition="25490")[
            "tax"
        ]
        == "0.00"
    )
    with pytest.raises(ValueError):
        calc(
            "gift",
            kind="INHERITANCE",
            relation="CHILD",
            gross_acquisition="100000",
            earlier_same_year="1",
        )


def scenario(**kw):
    data = {
        "name": "Fixture scenario",
        "scope": "DEMO",
        "entity_id": "private",
        "months": 24,
        "cash": "10000",
        "investments": "0",
        "pension_capital": "0",
        "monthly_income": "2000",
        "monthly_expenses": "1000",
        "monthly_investment": "100",
        "monthly_pension": "100",
        "monthly_tax_reserve": "100",
        "emergency_reserve": "2000",
        "initial_tax_reserve": "1000",
        "annual_return_percent": "0",
        "annual_pension_return_percent": "0",
        "annual_inflation_percent": "0",
        "annual_fee_percent": "0",
        "stress_drop_percent": "30",
        "stress_income_loss_months": 3,
        "goals": [],
        "source_revision": 0,
        "assumptions_note": "Synthetische demonstratie, geen gebruikersfeiten.",
    }
    return planning.Scenario.model_validate({**data, **kw})


def test_scenario_reserve_is_not_double_counted_and_pension_is_locked():
    r = planning.calculate(scenario())
    last = r["base"]["rows"][-1]
    assert (
        last["cash"] == "29200.00"
        and last["investments"] == "2400.00"
        and last["pension_locked"] == "2400.00"
    )
    assert (
        last["liquid_wealth"] == "31600.00"
        and last["total_including_locked"] == "34000.00"
    )
    assert last["tax_reserve"] == "3400.00"
    assert r == planning.calculate(scenario())


def test_scenario_no_implicit_loan_or_sale_for_goals():
    r = planning.calculate(
        scenario(
            cash="1000",
            initial_tax_reserve="0",
            monthly_income="0",
            investments="100000",
            goals=[{"id": "house", "name": "Woning", "month": 1, "amount": "50000"}],
        )
    )
    assert not r["base"]["goals"][0]["funded"]
    assert r["base"]["rows"][1]["investments"] == "100000.00"
    assert r["base"]["cash_shortfall_month"] == 0


def test_seeded_simulation_and_trade_buffer_gate():
    a = planning.monte_carlo(scenario(months=12), 7, 20, "15")
    assert a == planning.monte_carlo(scenario(months=12), 7, 20, "15")
    r = planning.trade_impact("1000", "500", "10", "200", "400", "800")
    assert not r["within_plan"] and not r["execution_authorized"]


def test_replay_and_backtest_no_lookahead():
    r = lab.replay(lab.ReplayInput(instrument_id="sim:BTC-EUR", cursor=10))
    assert len(r["rows"]) == 11
    p = lab.BacktestInput(
        instrument_id="sim:BTC-EUR", short_window=5, long_window=20, start=0, end=119
    )
    result = lab.backtest(p)
    assert all(f["fill_bar"] == f["signal_bar"] + 1 for f in result["fills"])
    assert result == lab.backtest(p)
    original = {
        "id": "macro",
        "revision": 1,
        "first_available_at": "2025-01-01T12:00:00Z",
        "value": "1",
    }
    revision = {
        **original,
        "revision": 2,
        "first_available_at": "2025-02-01T12:00:00Z",
        "value": "2",
    }
    assert lab.as_of([revision, original], "2025-01-15T12:00:00Z")[0]["value"] == "1"


def test_vault_authenticated_roundtrip_and_tamper(tmp_path, monkeypatch):
    key = tmp_path / "key"
    key.write_bytes(Fernet.generate_key())
    monkeypatch.setenv("VAULT_KEY_FILE", str(key))
    raw = b"local private evidence"
    r = vault.encrypt(
        "../../note.txt",
        "text/plain",
        base64.b64encode(raw).decode(),
        {"category": "TAX"},
    )
    assert raw not in r["ciphertext"]
    assert vault.decrypt(r["ciphertext"], r["content_hash"]) == raw
    assert "/" not in vault.metadata(r["name"])["name"]
    with pytest.raises(ValueError):
        vault.decrypt(r["ciphertext"][:-3] + b"xxx", r["content_hash"])
    with pytest.raises(ValueError):
        vault.encrypt("bad.pdf", "application/pdf", base64.b64encode(raw).decode(), {})


def test_estate_share_validation_and_legal_review():
    data = {
        "name": "Voorbeeld",
        "gross_assets": "100000",
        "debts": "0",
        "funeral_costs": "5000",
        "beneficiaries": [
            {
                "id": "1",
                "name": "Voorbeeldkind",
                "relation": "CHILD",
                "percentage": "100",
            }
        ],
        "notes": "",
    }
    r = estate.assess(estate.EstatePlan(**data))
    assert r["review_required"] and not r["legal_document"]
    r = estate.assess(estate.EstatePlan(**{**data, "complex_cases": ["Vruchtgebruik"]}))
    assert r["beneficiaries"][0]["tax_concept"] is None
    data["beneficiaries"][0]["percentage"] = "50"
    with pytest.raises(ValueError):
        estate.assess(estate.EstatePlan(**data))


def test_crawl_failure_is_not_unchanged():
    class Client:
        def stream(self, *a, **kw):
            raise TimeoutError()

    result = rules.fetch_source(tax.SOURCES[0], {"latest_hash": "old"}, Client())
    assert result["status"] == "FETCH_FAILED" and result["latest_hash"] == "old"
    assert rules.status(rules.empty())["review_status"] == "NEEDS_HUMAN_REVIEW"
