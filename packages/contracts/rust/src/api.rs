// GENERATED API types. Validate incoming JSON against openapi.json before use.
use serde::{Serialize,Deserialize};
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AccountInput {
    pub name: String,
    pub entity: String,
    pub currency: Option<String>,
    pub opening: Option<String>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ActualReturn {
    pub complete: bool,
    pub bank_interest: String,
    pub investment_income: String,
    pub investments_start: String,
    pub investments_end: String,
    pub purchases: String,
    pub sales: String,
    pub debt_interest: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AnalysisConfirm {
    pub preview_id: String,
    pub public_confirmed: bool,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AnalysisPreview {
    pub provider: String,
    pub prompt: String,
    pub source_ids: Vec<String>,
    pub task: Option<String>,
    pub conversation_id: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AssetInput {
    pub asset_id: Option<String>,
    pub name: String,
    pub entity: String,
    pub kind: String,
    pub value_eur: String,
    pub as_of: String,
    pub linked_entity: Option<String>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BacktestInput {
    pub instrument_id: String,
    pub interval: Option<String>,
    pub initial_cash: Option<String>,
    pub fee_bps: Option<String>,
    pub slippage_bps: Option<String>,
    pub short_window: i64,
    pub long_window: i64,
    pub allocation_percent: Option<String>,
    pub start: i64,
    pub end: i64,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Beneficiary {
    pub id: String,
    pub name: String,
    pub relation: String,
    pub percentage: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Box1Input {
    pub year: Option<i64>,
    pub resident_full_year: bool,
    pub inputs_complete: bool,
    pub special_cases: Option<Vec<String>>,
    pub taxable_income: String,
    pub age_regime: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Box2Input {
    pub year: Option<i64>,
    pub resident_full_year: bool,
    pub inputs_complete: bool,
    pub special_cases: Option<Vec<String>>,
    pub gross_income: String,
    pub dividend_tax_withheld: Option<String>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Box3Input {
    pub year: Option<i64>,
    pub resident_full_year: bool,
    pub inputs_complete: bool,
    pub special_cases: Option<Vec<String>>,
    pub savings: String,
    pub other_assets: String,
    pub debts: String,
    pub fiscal_partner_all_year: bool,
    pub allocation_percent: Option<String>,
    pub actual: Option<ActualReturn>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ComparisonInput {
    pub left: String,
    pub right: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ConfirmImport {
    pub preview_id: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Confirmation {
    pub preview_id: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EntityImpactInput {
    pub scope: String,
    pub account_id: String,
    pub scenario_id: String,
    pub trade_amount: String,
    pub fee: String,
    pub long_term_reserve: String,
    pub trading_pot: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EntityInput {
    pub name: String,
    pub kind: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EstateInput {
    pub plan: EstatePlan,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EstatePlan {
    pub name: String,
    pub gross_assets: String,
    pub debts: String,
    pub funeral_costs: String,
    pub beneficiaries: Vec<Beneficiary>,
    pub complex_cases: Option<Vec<String>>,
    pub document_ids: Option<Vec<String>>,
    pub notes: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FXMarkInput {
    pub account_id: String,
    pub rate_to_eur: String,
    pub as_of: String,
    pub source: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FXRequest {
    pub amount: String,
    pub base: String,
    pub quote: String,
    pub purpose: Option<String>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FeedImport {
    pub format: Option<String>,
    pub content: String,
    pub publisher: String,
    pub source_family: String,
    pub region: String,
    pub display_rights_confirmed: Option<bool>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GiftInput {
    pub year: Option<i64>,
    pub resident_full_year: bool,
    pub inputs_complete: bool,
    pub special_cases: Option<Vec<String>>,
    pub kind: String,
    pub relation: String,
    pub gross_acquisition: String,
    pub earlier_same_year: Option<String>,
    pub earlier_tax: Option<String>,
    pub payer: Option<String>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Goal {
    pub id: String,
    pub name: String,
    pub month: i64,
    pub amount: String,
    pub priority: Option<String>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HTTPValidationError {
    pub detail: Option<Vec<ValidationError>>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ImpactInput {
    pub cash: String,
    pub trade_amount: String,
    pub fee: String,
    pub tax_reserve: String,
    pub long_term_reserve: String,
    pub trading_pot: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ImportInput {
    pub content: String,
    pub format: Option<String>,
    pub account: Option<String>,
    pub delimiter: Option<String>,
    pub decimal_separator: Option<String>,
    pub date_format: Option<String>,
    pub mapping: Option<std::collections::BTreeMap<String,String>>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ImportRow {
    pub date: String,
    pub kind: String,
    pub amount: String,
    pub currency: String,
    pub account: String,
    pub reference: String,
    pub counteraccount: Option<String>,
    pub asset: Option<String>,
    pub quantity: Option<String>,
    pub fee: Option<String>,
    pub fx_rate: Option<String>,
    pub line: Option<i64>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LocalExplanation {
    pub topic: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MarkInput {
    pub position_id: String,
    pub price_eur: String,
    pub as_of: String,
    pub source: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OrderIntent {
    pub schema_version: Option<String>,
    pub instrument_id: String,
    pub account_id: Option<String>,
    pub mode: Option<String>,
    pub side: String,
    pub order_type: Option<String>,
    pub time_in_force: Option<String>,
    pub quantity: String,
    pub limit_price: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OwnershipInput {
    pub parent: String,
    pub child: String,
    pub percentage: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Password {
    pub password: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Pause {
    pub paused: bool,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PensionHistory {
    pub year: i64,
    pub unused_room: String,
    pub evidence: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PensionInput {
    pub year: Option<i64>,
    pub resident_full_year: bool,
    pub inputs_complete: bool,
    pub special_cases: Option<Vec<String>>,
    pub eligible_age: bool,
    pub income_previous_year: String,
    pub income_year: Option<i64>,
    pub regime: String,
    pub factor_a: Option<String>,
    pub upo_deduction: Option<String>,
    pub net_pension_premium: Option<String>,
    pub contribution_paid: String,
    pub history_complete: bool,
    pub history: Option<Vec<PensionHistory>>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PerformanceFlow {
    pub date: String,
    pub amount: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PerformanceInput {
    pub periods: Vec<PerformancePeriod>,
    pub flows: Vec<PerformanceFlow>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PerformancePeriod {
    pub start: String,
    pub end: String,
    pub external_flow: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Plan {
    pub reserve: String,
    pub monthly_in: String,
    pub monthly_out: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Preferences {
    pub priorities: Vec<String>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Reminder {
    pub title: String,
    pub scheduled_at: String,
    pub timezone: String,
    pub scope: String,
    pub kind: Option<String>,
    pub instrument_id: Option<String>,
    pub source: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReplayInput {
    pub instrument_id: String,
    pub interval: Option<String>,
    pub cursor: i64,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReverseInput {
    pub event_id: String,
    pub reason: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReviewedImport {
    pub rows: Vec<ImportRow>,
    pub original_preview_id: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RuleReview {
    pub rule_hash: String,
    pub binding: String,
    pub decision: String,
    pub reviewer: String,
    pub note: String,
    pub scope_understood: bool,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Scenario {
    pub name: String,
    pub scope: String,
    pub entity_id: String,
    pub months: i64,
    pub cash: String,
    pub investments: String,
    pub pension_capital: String,
    pub monthly_income: String,
    pub monthly_expenses: String,
    pub monthly_investment: String,
    pub monthly_pension: String,
    pub monthly_tax_reserve: String,
    pub emergency_reserve: String,
    pub initial_tax_reserve: String,
    pub annual_return_percent: String,
    pub annual_pension_return_percent: String,
    pub annual_inflation_percent: String,
    pub annual_fee_percent: String,
    pub stress_drop_percent: String,
    pub stress_income_loss_months: i64,
    pub goals: Option<Vec<Goal>>,
    pub source_revision: i64,
    pub assumptions_note: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ScenarioJob {
    pub scenario: Scenario,
    pub mode: Option<String>,
    pub seed: Option<i64>,
    pub paths: Option<i64>,
    pub volatility: Option<String>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SplitInput {
    pub position_id: String,
    pub action_id: String,
    pub numerator: String,
    pub denominator: String,
    pub effective_date: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TaxRequest {
    pub calculator: String,
    pub inputs: serde_json::Value,
    pub concept: Option<bool>,
    pub scope: String,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ValidationError {
    pub loc: Vec<serde_json::Value>,
    pub msg: String,
    pub r#type: String,
    pub input: Option<serde_json::Value>,
    pub ctx: Option<std::collections::BTreeMap<String,serde_json::Value>>,
}
#[derive(Debug,Clone,Serialize,Deserialize)]
#[serde(deny_unknown_fields)]
pub struct VaultInput {
    pub name: String,
    pub mime: String,
    pub content_b64: String,
    pub category: String,
    pub entity_id: String,
    pub note: Option<String>,
    pub supersedes: Option<String>,
}
