// GENERATED. Decimal strings are never converted to floats.
use serde::{Serialize, Deserialize};
pub mod api;
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum IdentitySchemaVersion {
    #[serde(rename = "1")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum IdentityCurrency {
    #[serde(rename = "EUR")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Identity {
    pub schema_version: Option<IdentitySchemaVersion>,
    pub instrument_id: String,
    pub symbol: String,
    pub base: String,
    pub currency: Option<IdentityCurrency>,
    pub venue_id: String,
    pub tick_size: String,
    pub lot_size: String,
    pub min_notional: String,
    pub paper_supported: bool,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum QuoteSchemaVersion {
    #[serde(rename = "1")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum QuoteQuality {
    #[serde(rename = "SIMULATED")] V0,
    #[serde(rename = "STALE")] V1,
    #[serde(rename = "READ_ONLY_PUBLIC")] V2,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Quote {
    pub schema_version: Option<QuoteSchemaVersion>,
    pub instrument_id: String,
    pub bid: String,
    pub ask: String,
    pub last: String,
    pub available_quantity: String,
    pub provider_id: String,
    pub venue_id: String,
    pub origin_feed_id: String,
    pub source_event_id: String,
    pub adapter_version: String,
    pub source_time: String,
    pub received_at: String,
    pub license_status: String,
    pub quality: QuoteQuality,
    pub revision: i64,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TradeSchemaVersion {
    #[serde(rename = "1")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TradeTakerSide {
    #[serde(rename = "BUY")] V0,
    #[serde(rename = "SELL")] V1,
    #[serde(rename = "UNKNOWN")] V2,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TradeQuality {
    #[serde(rename = "SIMULATED")] V0,
    #[serde(rename = "READ_ONLY_PUBLIC")] V1,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Trade {
    pub schema_version: Option<TradeSchemaVersion>,
    pub event_id: String,
    pub instrument_id: String,
    pub price: String,
    pub quantity: String,
    pub taker_side: TradeTakerSide,
    pub provider_id: String,
    pub origin_feed_id: String,
    pub source_time: String,
    pub quality: TradeQuality,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderIntentSchemaVersion {
    #[serde(rename = "1")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderIntentAccountId {
    #[serde(rename = "demo-paper")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderIntentMode {
    #[serde(rename = "PAPER")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderIntentSide {
    #[serde(rename = "BUY")] V0,
    #[serde(rename = "SELL")] V1,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderIntentOrderType {
    #[serde(rename = "LIMIT")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderIntentTimeInForce {
    #[serde(rename = "IOC")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OrderIntent {
    pub schema_version: Option<OrderIntentSchemaVersion>,
    pub instrument_id: String,
    pub account_id: Option<OrderIntentAccountId>,
    pub mode: Option<OrderIntentMode>,
    pub side: OrderIntentSide,
    pub order_type: Option<OrderIntentOrderType>,
    pub time_in_force: Option<OrderIntentTimeInForce>,
    pub quantity: String,
    pub limit_price: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum JournalLineSchemaVersion {
    #[serde(rename = "1")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum JournalLineAccountId {
    #[serde(rename = "demo-paper")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum JournalLineCurrency {
    #[serde(rename = "EUR")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum JournalLineMode {
    #[serde(rename = "PAPER")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct JournalLine {
    pub schema_version: Option<JournalLineSchemaVersion>,
    pub event_id: String,
    pub account_id: Option<JournalLineAccountId>,
    pub account: String,
    pub amount: String,
    pub currency: Option<JournalLineCurrency>,
    pub mode: Option<JournalLineMode>,
    pub created_at: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaxRuleSchemaVersion {
    #[serde(rename = "1")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaxRuleJurisdiction {
    #[serde(rename = "NL")] V0,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaxRuleLegislativeStatus {
    #[serde(rename = "PROPOSED")] V0,
    #[serde(rename = "ADOPTED")] V1,
    #[serde(rename = "PROMULGATED")] V2,
    #[serde(rename = "REPEALED")] V3,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaxRuleImplementationStatus {
    #[serde(rename = "DRAFT")] V0,
    #[serde(rename = "TESTED")] V1,
    #[serde(rename = "APPROVED")] V2,
    #[serde(rename = "RETIRED")] V3,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TaxRule {
    pub schema_version: Option<TaxRuleSchemaVersion>,
    pub rule_id: String,
    pub rule_version: String,
    pub tax_year: i64,
    pub jurisdiction: Option<TaxRuleJurisdiction>,
    pub legislative_status: TaxRuleLegislativeStatus,
    pub implementation_status: TaxRuleImplementationStatus,
    pub valid_from: String,
    pub known_from: String,
    pub official_url: String,
    pub content_hash: String,
    pub reviewed_by: String,
}
