# GENERATED. Runtime authority remains the canonical Pydantic request model.
from __future__ import annotations
from typing import Any,Literal
from pydantic import BaseModel,ConfigDict
class WireModel(BaseModel):
    model_config=ConfigDict(extra="forbid")
class AccountInput(WireModel):
    name: str
    entity: str
    currency: Literal['EUR', 'USD', 'GBP'] = 'EUR'
    opening: str = '0'

class ActualReturn(WireModel):
    complete: bool
    bank_interest: str
    investment_income: str
    investments_start: str
    investments_end: str
    purchases: str
    sales: str
    debt_interest: str

class AnalysisConfirm(WireModel):
    preview_id: str
    public_confirmed: bool

class AnalysisPreview(WireModel):
    provider: Literal['CODEX', 'JEV']
    prompt: str
    source_ids: list[str]
    task: Literal['news_kind', 'source_support', 'relevance'] = 'news_kind'
    conversation_id: str

class AssetInput(WireModel):
    asset_id: str | None = None
    name: str
    entity: str
    kind: Literal['PROPERTY', 'LIABILITY', 'RECEIVABLE', 'EQUITY_INTEREST', 'PENSION_RIGHT', 'CASH_EQUIVALENT']
    value_eur: str
    as_of: str
    linked_entity: str | None = None

class BacktestInput(WireModel):
    instrument_id: Literal['sim:BTC-EUR', 'sim:ETH-EUR', 'sim:SOL-EUR']
    interval: Literal['15m', '1u', '4u', '1d'] = '1u'
    initial_cash: str = '10000'
    fee_bps: str = '16'
    slippage_bps: str = '10'
    short_window: int
    long_window: int
    allocation_percent: str = '25'
    start: int
    end: int

class Beneficiary(WireModel):
    id: str
    name: str
    relation: Literal['CHILD', 'GRANDCHILD', 'OTHER']
    percentage: str

class Box1Input(WireModel):
    year: Literal[2025] = 2025
    resident_full_year: bool
    inputs_complete: bool
    special_cases: list[str] = None
    taxable_income: str
    age_regime: Literal['UNDER_AOW_ALL_YEAR', 'AOW_ALL_YEAR_BORN_1946_PLUS', 'AOW_ALL_YEAR_BORN_BEFORE_1946']

class Box2Input(WireModel):
    year: Literal[2025] = 2025
    resident_full_year: bool
    inputs_complete: bool
    special_cases: list[str] = None
    gross_income: str
    dividend_tax_withheld: str = '0'

class Box3Input(WireModel):
    year: Literal[2025] = 2025
    resident_full_year: bool
    inputs_complete: bool
    special_cases: list[str] = None
    savings: str
    other_assets: str
    debts: str
    fiscal_partner_all_year: bool
    allocation_percent: str = '100'
    actual: ActualReturn | None = None

class ComparisonInput(WireModel):
    left: str
    right: str

class ConfirmImport(WireModel):
    preview_id: str

class Confirmation(WireModel):
    preview_id: str

class EntityImpactInput(WireModel):
    scope: Literal['DEMO', 'PERSONAL']
    account_id: str
    scenario_id: str
    trade_amount: str
    fee: str
    long_term_reserve: str
    trading_pot: str

class EntityInput(WireModel):
    name: str
    kind: Literal['PERSON', 'HOUSEHOLD', 'HOLDING', 'OPERATING_COMPANY']

class EstateInput(WireModel):
    plan: EstatePlan

class EstatePlan(WireModel):
    name: str
    gross_assets: str
    debts: str
    funeral_costs: str
    beneficiaries: list[Beneficiary]
    complex_cases: list[str] = None
    document_ids: list[str] = None
    notes: str

class FXMarkInput(WireModel):
    account_id: str
    rate_to_eur: str
    as_of: str
    source: str

class FXRequest(WireModel):
    amount: str
    base: str
    quote: str
    purpose: str = 'VALUATION'

class FeedImport(WireModel):
    format: str = 'RSS_ATOM'
    content: str
    publisher: str
    source_family: str
    region: str
    display_rights_confirmed: bool = False

class GiftInput(WireModel):
    year: Literal[2025] = 2025
    resident_full_year: bool
    inputs_complete: bool
    special_cases: list[str] = None
    kind: Literal['GIFT', 'INHERITANCE']
    relation: Literal['CHILD', 'GRANDCHILD', 'OTHER']
    gross_acquisition: str
    earlier_same_year: str = '0'
    earlier_tax: str = '0'
    payer: Literal['RECIPIENT'] = 'RECIPIENT'

class Goal(WireModel):
    id: str
    name: str
    month: int
    amount: str
    priority: Literal['ESSENTIAL', 'OPTIONAL'] = 'ESSENTIAL'

class HTTPValidationError(WireModel):
    detail: list[ValidationError] = None

class ImpactInput(WireModel):
    cash: str
    trade_amount: str
    fee: str
    tax_reserve: str
    long_term_reserve: str
    trading_pot: str

class ImportInput(WireModel):
    content: str
    format: Literal['CSV', 'CAMT053'] = 'CSV'
    account: str = ''
    delimiter: Literal[',', ';', '\t'] = ','
    decimal_separator: Literal['.', ','] = '.'
    date_format: Literal['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'] = '%Y-%m-%d'
    mapping: dict[str,str] | None = None

class ImportRow(WireModel):
    date: str
    kind: Literal['INCOME', 'EXPENSE', 'TRANSFER', 'INTERCOMPANY', 'BUY', 'SELL', 'DIVIDEND', 'INTEREST', 'FEE', 'REVIEW']
    amount: str
    currency: str
    account: str
    reference: str
    counteraccount: str = ''
    asset: str = ''
    quantity: str = '0'
    fee: str = '0'
    fx_rate: str = '1'
    line: int = 0

class LocalExplanation(WireModel):
    topic: Literal['fees', 'ownership', 'tax', 'pension', 'source_quality']

class MarkInput(WireModel):
    position_id: str
    price_eur: str
    as_of: str
    source: str

class OrderIntent(WireModel):
    schema_version: Literal['1'] = '1'
    instrument_id: str
    account_id: Literal['demo-paper'] = 'demo-paper'
    mode: Literal['PAPER'] = 'PAPER'
    side: Literal['BUY', 'SELL']
    order_type: Literal['LIMIT'] = 'LIMIT'
    time_in_force: Literal['IOC'] = 'IOC'
    quantity: str
    limit_price: str

class OwnershipInput(WireModel):
    parent: str
    child: str
    percentage: str

class Password(WireModel):
    password: str

class Pause(WireModel):
    paused: bool

class PensionHistory(WireModel):
    year: int
    unused_room: str
    evidence: str

class PensionInput(WireModel):
    year: Literal[2025] = 2025
    resident_full_year: bool
    inputs_complete: bool
    special_cases: list[str] = None
    eligible_age: bool
    income_previous_year: str
    income_year: Literal[2024] = 2024
    regime: Literal['NO_PENSION', 'TRANSITION_FACTOR_A', 'WTP_CONFIRMED_UPO']
    factor_a: str = '0'
    upo_deduction: str = '0'
    net_pension_premium: str = '0'
    contribution_paid: str
    history_complete: bool
    history: list[PensionHistory] = None

class PerformanceFlow(WireModel):
    date: str
    amount: str

class PerformanceInput(WireModel):
    periods: list[PerformancePeriod]
    flows: list[PerformanceFlow]

class PerformancePeriod(WireModel):
    start: str
    end: str
    external_flow: str

class Plan(WireModel):
    reserve: str
    monthly_in: str
    monthly_out: str

class Preferences(WireModel):
    priorities: list[str]

class Reminder(WireModel):
    title: str
    scheduled_at: str
    timezone: str
    scope: Literal['DEMO', 'PERSONAL']
    kind: Literal['PERSONAL_DEADLINE', 'EARNINGS', 'DIVIDEND', 'SPLIT', 'MACRO', 'EXPIRY', 'SESSION', 'HALT'] = 'PERSONAL_DEADLINE'
    instrument_id: str = ''
    source: str

class ReplayInput(WireModel):
    instrument_id: Literal['sim:BTC-EUR', 'sim:ETH-EUR', 'sim:SOL-EUR']
    interval: Literal['15m', '1u', '4u', '1d'] = '1u'
    cursor: int

class ReverseInput(WireModel):
    event_id: str
    reason: str

class ReviewedImport(WireModel):
    rows: list[ImportRow]
    original_preview_id: str

class RuleReview(WireModel):
    rule_hash: str
    binding: str
    decision: Literal['APPROVE', 'REJECT']
    reviewer: str
    note: str
    scope_understood: bool

class Scenario(WireModel):
    name: str
    scope: Literal['DEMO', 'PERSONAL']
    entity_id: str
    months: int
    cash: str
    investments: str
    pension_capital: str
    monthly_income: str
    monthly_expenses: str
    monthly_investment: str
    monthly_pension: str
    monthly_tax_reserve: str
    emergency_reserve: str
    initial_tax_reserve: str
    annual_return_percent: str
    annual_pension_return_percent: str
    annual_inflation_percent: str
    annual_fee_percent: str
    stress_drop_percent: str
    stress_income_loss_months: int
    goals: list[Goal] = None
    source_revision: int
    assumptions_note: str

class ScenarioJob(WireModel):
    scenario: Scenario
    mode: Literal['SCENARIO', 'MONTE_CARLO'] = 'SCENARIO'
    seed: int = 2025
    paths: int = 100
    volatility: str = '15'

class SplitInput(WireModel):
    position_id: str
    action_id: str
    numerator: str
    denominator: str
    effective_date: str

class TaxRequest(WireModel):
    calculator: Literal['box1', 'box2', 'box3', 'pension', 'gift']
    inputs: Box1Input | Box2Input | Box3Input | PensionInput | GiftInput
    concept: bool = True
    scope: Literal['DEMO', 'PERSONAL']

class ValidationError(WireModel):
    loc: list[str | int]
    msg: str
    type: str
    input: Any = None
    ctx: dict[str,Any] = None

class VaultInput(WireModel):
    name: str
    mime: str
    content_b64: str
    category: Literal['TAX', 'PENSION', 'ESTATE', 'ACCOUNT', 'OTHER']
    entity_id: str
    note: str = ''
    supersedes: str | None = None

for _model in list(globals().values()):
    if isinstance(_model,type) and issubclass(_model,WireModel):_model.model_rebuild()
