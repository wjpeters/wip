# GENERATED from canonical JSON Schema. Do not edit.
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field
DecimalString = Annotated[str, Field(pattern=r"^-?(?:0|[1-9]\d{0,15})(?:\.\d{1,8})?$")]
class Identity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal['1'] = '1'
    instrument_id: str
    symbol: str
    base: str
    currency: Literal['EUR'] = 'EUR'
    venue_id: str
    tick_size: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]
    lot_size: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]
    min_notional: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]
    paper_supported: bool

class Quote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal['1'] = '1'
    instrument_id: str
    bid: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]
    ask: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]
    last: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]
    available_quantity: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]
    provider_id: str
    venue_id: str
    origin_feed_id: str
    source_event_id: str
    adapter_version: str
    source_time: str
    received_at: str
    license_status: str
    quality: Literal['SIMULATED', 'STALE', 'READ_ONLY_PUBLIC']
    revision: int

class Trade(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal['1'] = '1'
    event_id: str
    instrument_id: str
    price: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]
    quantity: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]
    taker_side: Literal['BUY', 'SELL', 'UNKNOWN']
    provider_id: str
    origin_feed_id: str
    source_time: str
    quality: Literal['SIMULATED', 'READ_ONLY_PUBLIC']

class OrderIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal['1'] = '1'
    instrument_id: str
    account_id: Literal['demo-paper'] = 'demo-paper'
    mode: Literal['PAPER'] = 'PAPER'
    side: Literal['BUY', 'SELL']
    order_type: Literal['LIMIT'] = 'LIMIT'
    time_in_force: Literal['IOC'] = 'IOC'
    quantity: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]
    limit_price: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]

class JournalLine(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal['1'] = '1'
    event_id: str
    account_id: Literal['demo-paper'] = 'demo-paper'
    account: str
    amount: Annotated[str, Field(pattern='^-?(?:0|[1-9]\\d{0,15})(?:\\.\\d{1,8})?$')]
    currency: Literal['EUR'] = 'EUR'
    mode: Literal['PAPER'] = 'PAPER'
    created_at: str

class TaxRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal['1'] = '1'
    rule_id: str
    rule_version: str
    tax_year: int
    jurisdiction: Literal['NL'] = 'NL'
    legislative_status: Literal['PROPOSED', 'ADOPTED', 'PROMULGATED', 'REPEALED']
    implementation_status: Literal['DRAFT', 'TESTED', 'APPROVED', 'RETIRED']
    valid_from: str
    known_from: str
    official_url: str
    content_hash: str
    reviewed_by: str

