// GENERATED from canonical API/Pydantic definitions. Do not edit.
export type AccountInput = {
  "name": string;
  "entity": string;
  "currency"?: "EUR" | "USD" | "GBP";
  "opening"?: string;
};
export type ActualReturn = {
  "complete": boolean;
  "bank_interest": string;
  "investment_income": string;
  "investments_start": string;
  "investments_end": string;
  "purchases": string;
  "sales": string;
  "debt_interest": string;
};
export type AnalysisConfirm = {
  "preview_id": string;
  "public_confirmed": boolean;
};
export type AnalysisPreview = {
  "provider": "CODEX" | "JEV";
  "prompt": string;
  "source_ids": Array<string>;
  "task"?: "news_kind" | "source_support" | "relevance";
  "conversation_id": string;
};
export type AssetInput = {
  "asset_id"?: (string | null);
  "name": string;
  "entity": string;
  "kind": "PROPERTY" | "LIABILITY" | "RECEIVABLE" | "EQUITY_INTEREST" | "PENSION_RIGHT" | "CASH_EQUIVALENT";
  "value_eur": string;
  "as_of": string;
  "linked_entity"?: (string | null);
};
export type BacktestInput = {
  "instrument_id": "sim:BTC-EUR" | "sim:ETH-EUR" | "sim:SOL-EUR";
  "interval"?: "15m" | "1u" | "4u" | "1d";
  "initial_cash"?: string;
  "fee_bps"?: string;
  "slippage_bps"?: string;
  "short_window": number;
  "long_window": number;
  "allocation_percent"?: string;
  "start": number;
  "end": number;
};
export type Beneficiary = {
  "id": string;
  "name": string;
  "relation": "CHILD" | "GRANDCHILD" | "OTHER";
  "percentage": string;
};
export type Box1Input = {
  "year"?: 2025;
  "resident_full_year": boolean;
  "inputs_complete": boolean;
  "special_cases"?: Array<string>;
  "taxable_income": string;
  "age_regime": "UNDER_AOW_ALL_YEAR" | "AOW_ALL_YEAR_BORN_1946_PLUS" | "AOW_ALL_YEAR_BORN_BEFORE_1946";
};
export type Box2Input = {
  "year"?: 2025;
  "resident_full_year": boolean;
  "inputs_complete": boolean;
  "special_cases"?: Array<string>;
  "gross_income": string;
  "dividend_tax_withheld"?: string;
};
export type Box3Input = {
  "year"?: 2025;
  "resident_full_year": boolean;
  "inputs_complete": boolean;
  "special_cases"?: Array<string>;
  "savings": string;
  "other_assets": string;
  "debts": string;
  "fiscal_partner_all_year": boolean;
  "allocation_percent"?: string;
  "actual"?: (ActualReturn | null);
};
export type ComparisonInput = {
  "left": string;
  "right": string;
};
export type ConfirmImport = {
  "preview_id": string;
};
export type Confirmation = {
  "preview_id": string;
};
export type EntityImpactInput = {
  "scope": "DEMO" | "PERSONAL";
  "account_id": string;
  "scenario_id": string;
  "trade_amount": string;
  "fee": string;
  "long_term_reserve": string;
  "trading_pot": string;
};
export type EntityInput = {
  "name": string;
  "kind": "PERSON" | "HOUSEHOLD" | "HOLDING" | "OPERATING_COMPANY";
};
export type EstateInput = {
  "plan": EstatePlan;
};
export type EstatePlan = {
  "name": string;
  "gross_assets": string;
  "debts": string;
  "funeral_costs": string;
  "beneficiaries": Array<Beneficiary>;
  "complex_cases"?: Array<string>;
  "document_ids"?: Array<string>;
  "notes": string;
};
export type FXMarkInput = {
  "account_id": string;
  "rate_to_eur": string;
  "as_of": string;
  "source": string;
};
export type FXRequest = {
  "amount": string;
  "base": string;
  "quote": string;
  "purpose"?: string;
};
export type FeedImport = {
  "format"?: string;
  "content": string;
  "publisher": string;
  "source_family": string;
  "region": string;
  "display_rights_confirmed"?: boolean;
};
export type GiftInput = {
  "year"?: 2025;
  "resident_full_year": boolean;
  "inputs_complete": boolean;
  "special_cases"?: Array<string>;
  "kind": "GIFT" | "INHERITANCE";
  "relation": "CHILD" | "GRANDCHILD" | "OTHER";
  "gross_acquisition": string;
  "earlier_same_year"?: string;
  "earlier_tax"?: string;
  "payer"?: "RECIPIENT";
};
export type Goal = {
  "id": string;
  "name": string;
  "month": number;
  "amount": string;
  "priority"?: "ESSENTIAL" | "OPTIONAL";
};
export type HTTPValidationError = {
  "detail"?: Array<ValidationError>;
};
export type ImpactInput = {
  "cash": string;
  "trade_amount": string;
  "fee": string;
  "tax_reserve": string;
  "long_term_reserve": string;
  "trading_pot": string;
};
export type ImportInput = {
  "content": string;
  "format"?: "CSV" | "CAMT053";
  "account"?: string;
  "delimiter"?: "," | ";" | "\t";
  "decimal_separator"?: "." | ",";
  "date_format"?: "%Y-%m-%d" | "%d-%m-%Y" | "%d/%m/%Y";
  "mapping"?: (Record<string,string> | null);
};
export type ImportRow = {
  "date": string;
  "kind": "INCOME" | "EXPENSE" | "TRANSFER" | "INTERCOMPANY" | "BUY" | "SELL" | "DIVIDEND" | "INTEREST" | "FEE" | "REVIEW";
  "amount": string;
  "currency": string;
  "account": string;
  "reference": string;
  "counteraccount"?: string;
  "asset"?: string;
  "quantity"?: string;
  "fee"?: string;
  "fx_rate"?: string;
  "line"?: number;
};
export type LocalExplanation = {
  "topic": "fees" | "ownership" | "tax" | "pension" | "source_quality";
};
export type MarkInput = {
  "position_id": string;
  "price_eur": string;
  "as_of": string;
  "source": string;
};
export type OrderIntent = {
  "schema_version"?: "1";
  "instrument_id": string;
  "account_id"?: "demo-paper";
  "mode"?: "PAPER";
  "side": "BUY" | "SELL";
  "order_type"?: "LIMIT";
  "time_in_force"?: "IOC";
  "quantity": string;
  "limit_price": string;
};
export type OwnershipInput = {
  "parent": string;
  "child": string;
  "percentage": string;
};
export type Password = {
  "password": string;
};
export type Pause = {
  "paused": boolean;
};
export type PensionHistory = {
  "year": number;
  "unused_room": string;
  "evidence": string;
};
export type PensionInput = {
  "year"?: 2025;
  "resident_full_year": boolean;
  "inputs_complete": boolean;
  "special_cases"?: Array<string>;
  "eligible_age": boolean;
  "income_previous_year": string;
  "income_year"?: 2024;
  "regime": "NO_PENSION" | "TRANSITION_FACTOR_A" | "WTP_CONFIRMED_UPO";
  "factor_a"?: string;
  "upo_deduction"?: string;
  "net_pension_premium"?: string;
  "contribution_paid": string;
  "history_complete": boolean;
  "history"?: Array<PensionHistory>;
};
export type PerformanceFlow = {
  "date": string;
  "amount": string;
};
export type PerformanceInput = {
  "periods": Array<PerformancePeriod>;
  "flows": Array<PerformanceFlow>;
};
export type PerformancePeriod = {
  "start": string;
  "end": string;
  "external_flow": string;
};
export type Plan = {
  "reserve": string;
  "monthly_in": string;
  "monthly_out": string;
};
export type Preferences = {
  "priorities": Array<string>;
};
export type Reminder = {
  "title": string;
  "scheduled_at": string;
  "timezone": string;
  "scope": "DEMO" | "PERSONAL";
  "kind"?: "PERSONAL_DEADLINE" | "EARNINGS" | "DIVIDEND" | "SPLIT" | "MACRO" | "EXPIRY" | "SESSION" | "HALT";
  "instrument_id"?: string;
  "source": string;
};
export type ReplayInput = {
  "instrument_id": "sim:BTC-EUR" | "sim:ETH-EUR" | "sim:SOL-EUR";
  "interval"?: "15m" | "1u" | "4u" | "1d";
  "cursor": number;
};
export type ReverseInput = {
  "event_id": string;
  "reason": string;
};
export type ReviewedImport = {
  "rows": Array<ImportRow>;
  "original_preview_id": string;
};
export type RuleReview = {
  "rule_hash": string;
  "binding": string;
  "decision": "APPROVE" | "REJECT";
  "reviewer": string;
  "note": string;
  "scope_understood": boolean;
};
export type Scenario = {
  "name": string;
  "scope": "DEMO" | "PERSONAL";
  "entity_id": string;
  "months": number;
  "cash": string;
  "investments": string;
  "pension_capital": string;
  "monthly_income": string;
  "monthly_expenses": string;
  "monthly_investment": string;
  "monthly_pension": string;
  "monthly_tax_reserve": string;
  "emergency_reserve": string;
  "initial_tax_reserve": string;
  "annual_return_percent": string;
  "annual_pension_return_percent": string;
  "annual_inflation_percent": string;
  "annual_fee_percent": string;
  "stress_drop_percent": string;
  "stress_income_loss_months": number;
  "goals"?: Array<Goal>;
  "source_revision": number;
  "assumptions_note": string;
};
export type ScenarioJob = {
  "scenario": Scenario;
  "mode"?: "SCENARIO" | "MONTE_CARLO";
  "seed"?: number;
  "paths"?: number;
  "volatility"?: string;
};
export type SplitInput = {
  "position_id": string;
  "action_id": string;
  "numerator": string;
  "denominator": string;
  "effective_date": string;
};
export type TaxRequest = {
  "calculator": "box1" | "box2" | "box3" | "pension" | "gift";
  "inputs": (Box1Input | Box2Input | Box3Input | PensionInput | GiftInput);
  "concept"?: boolean;
  "scope": "DEMO" | "PERSONAL";
};
export type ValidationError = {
  "loc": Array<(string | number)>;
  "msg": string;
  "type": string;
  "input"?: unknown;
  "ctx"?: Record<string,unknown>;
};
export type VaultInput = {
  "name": string;
  "mime": string;
  "content_b64": string;
  "category": "TAX" | "PENSION" | "ESTATE" | "ACCOUNT" | "OTHER";
  "entity_id": string;
  "note"?: string;
  "supersedes"?: (string | null);
};
