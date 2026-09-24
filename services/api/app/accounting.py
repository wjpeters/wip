"""Deterministic double-entry finance book, independent of the paper account."""

from __future__ import annotations
import copy
import csv
import io
import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal as D, ROUND_HALF_UP
from xml.etree import ElementTree as ET

CENT = D(".01")
KINDS = {
    "INCOME",
    "EXPENSE",
    "TRANSFER",
    "INTERCOMPANY",
    "BUY",
    "SELL",
    "DIVIDEND",
    "INTEREST",
    "FEE",
    "REVIEW",
}


def amount(value):
    if not isinstance(value, str) or len(value) > 32:
        raise ValueError("AMOUNT_MUST_BE_DECIMAL_STRING")
    x = D(value)
    if not x.is_finite() or abs(x) > D("1000000000000") or x.as_tuple().exponent < -8:
        raise ValueError("INVALID_AMOUNT")
    return x


def money(value):
    return str(D(value).quantize(CENT, rounding=ROUND_HALF_UP))


def new_book(scope):
    return {
        "schema_version": "1",
        "scope": scope,
        "revision": 0,
        "entities": {},
        "ownership": [],
        "accounts": {},
        "journal": [],
        "positions": {},
        "imports": {},
        "previews": {},
        "reviews": [],
        "valuations": [],
        "goals": [],
        "assets": {},
        "reversals": [],
    }


def add_entity(book, entity_id, name, kind):
    if entity_id in book["entities"]:
        raise ValueError("ENTITY_EXISTS")
    if kind not in {"PERSON", "HOUSEHOLD", "HOLDING", "OPERATING_COMPANY"}:
        raise ValueError("INVALID_ENTITY_TYPE")
    book["entities"][entity_id] = {"id": entity_id, "name": name, "kind": kind}


def add_account(book, account_id, name, entity, currency, opening="0"):
    if entity not in book["entities"] or account_id in book["accounts"]:
        raise ValueError("INVALID_ACCOUNT_OWNER")
    if currency not in {"EUR", "USD", "GBP"}:
        raise ValueError("UNSUPPORTED_CURRENCY")
    value = amount(opening)
    if value < 0:
        raise ValueError("NEGATIVE_OPENING_CASH")
    if currency != "EUR" and value != 0:
        raise ValueError("OPENING_FX_REQUIRED: import opening valuation separately")
    book["accounts"][account_id] = {
        "id": account_id,
        "name": name,
        "entity": entity,
        "currency": currency,
    }
    if value:
        post(
            book,
            "opening:" + account_id,
            [("cash:" + account_id, value, entity), ("opening_equity", -value, entity)],
            {
                "kind": "OPENING",
                "date": date.today().isoformat(),
                "currency": currency,
                "amount": opening,
                "fx_rate": "1",
                "quality": book["scope"],
            },
        )


def set_ownership(book, parent, child, percentage):
    pct = amount(percentage)
    if (
        parent not in book["entities"]
        or child not in book["entities"]
        or parent == child
        or not D(0) < pct <= D(100)
    ):
        raise ValueError("INVALID_OWNERSHIP")
    links = [
        posting
        for posting in book["ownership"]
        if not (posting["parent"] == parent and posting["child"] == child)
    ] + [{"parent": parent, "child": child, "percentage": str(pct)}]
    if (
        sum(
            (
                D(posting["percentage"])
                for posting in links
                if posting["child"] == child
            ),
            D(0),
        )
        > 100
    ):
        raise ValueError("OWNERSHIP_ABOVE_100")

    def visit(node, path):
        if node in path:
            raise ValueError("OWNERSHIP_CYCLE")
        for posting in links:
            if posting["parent"] == node:
                visit(posting["child"], path | {node})

    for entity in book["entities"]:
        visit(entity, set())
    book["ownership"] = links


def post(book, event_id, lines, source):
    if any(posting["event_id"] == event_id for posting in book["journal"]):
        return False
    values = [
        (account, D(value).quantize(CENT, rounding=ROUND_HALF_UP), entity)
        for account, value, entity in lines
    ]
    if sum((v for _, v, _ in values), D(0)) != 0:
        raise ValueError("UNBALANCED_JOURNAL")
    for i, (account, value, entity) in enumerate(values):
        book["journal"].append(
            {
                "event_id": event_id,
                "line": i,
                "account": account,
                "entity": entity,
                "amount_eur": money(value),
                "source": source,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    return True


def native_cash(book, account):
    # Native amount is retained on the source row. EUR ledger never substitutes today's FX.
    return sum(
        (
            D(posting["source"].get("native_cash", posting["source"]["amount"]))
            for posting in book["journal"]
            if posting["account"] == "cash:" + account
        ),
        D(0),
    )


def normalize_decimal(value, separator):
    value = value.strip().replace(" ", "")
    if separator == ",":
        value = value.replace(".", "").replace(",", ".")
    elif separator != ".":
        raise ValueError("INVALID_DECIMAL_SEPARATOR")
    return str(amount(value))


def parse_csv(
    content, mapping=None, delimiter=",", decimal_separator=".", date_format="%Y-%m-%d"
):
    if len(content.encode()) > 2_000_000:
        raise ValueError("FILE_TOO_LARGE")
    if delimiter not in {",", ";", "\t"}:
        raise ValueError("INVALID_DELIMITER")
    mapping = mapping or {
        k: k
        for k in [
            "date",
            "type",
            "amount",
            "currency",
            "account",
            "reference",
            "counteraccount",
            "asset",
            "quantity",
            "fee",
            "fx_rate",
        ]
    }
    reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError("EMPTY_FILE")
    result = []
    for n, row in enumerate(reader, 2):
        if len(result) >= 2000:
            raise ValueError("ROW_LIMIT")

        def cell(k, default=""):
            return (row.get(mapping.get(k, k)) or default).strip()

        try:
            kind = cell("type", "REVIEW").upper()
            if kind not in KINDS:
                kind = "REVIEW"
            result.append(
                {
                    "date": datetime.strptime(cell("date"), date_format)
                    .date()
                    .isoformat(),
                    "kind": kind,
                    "amount": normalize_decimal(cell("amount"), decimal_separator),
                    "currency": cell("currency", "EUR").upper(),
                    "account": cell("account"),
                    "reference": cell("reference") or f"row-{n}",
                    "counteraccount": cell("counteraccount"),
                    "asset": cell("asset"),
                    "quantity": normalize_decimal(
                        cell("quantity", "0"), decimal_separator
                    ),
                    "fee": normalize_decimal(cell("fee", "0"), decimal_separator),
                    "fx_rate": normalize_decimal(
                        cell(
                            "fx_rate", "1" if cell("currency", "EUR") == "EUR" else "0"
                        ),
                        decimal_separator,
                    ),
                    "line": n,
                }
            )
        except (ValueError, ArithmeticError) as e:
            raise ValueError(f"INVALID_ROW_{n}: {e}")
    return result


def parse_camt(content, account):
    if (
        len(content.encode()) > 2_000_000
        or "<!DOCTYPE" in content.upper()
        or "<!ENTITY" in content.upper()
    ):
        raise ValueError("UNSAFE_XML")
    root = ET.fromstring(content)
    rows = []

    def find(node, name):
        return next((x for x in node.iter() if x.tag.split("}")[-1] == name), None)

    for i, entry in enumerate(x for x in root.iter() if x.tag.split("}")[-1] == "Ntry"):
        if i >= 2000:
            raise ValueError("ROW_LIMIT")
        status = find(entry, "Sts")
        if status is not None and "".join(status.itertext()).strip() not in {
            "BOOK",
            "BOOKED",
        }:
            continue
        a = find(entry, "Amt")
        direction = find(entry, "CdtDbtInd")
        booking = find(entry, "BookgDt")
        if a is None or direction is None or booking is None:
            raise ValueError("INCOMPLETE_CAMT_ENTRY")
        dt = find(booking, "Dt")
        dt = dt if dt is not None else find(booking, "DtTm")
        ref = find(entry, "AcctSvcrRef")
        ref = ref if ref is not None else find(entry, "NtryRef")
        if dt is None or ref is None or not ref.text:
            raise ValueError("CAMT_REFERENCE_REQUIRED")
        currency = a.get("Ccy")
        value = amount(a.text or "0")
        if direction.text == "DBIT":
            value = -value
        elif direction.text != "CRDT":
            raise ValueError("INVALID_CAMT_DIRECTION")
        # CdtDbtInd already describes this entry's cash direction, including reversals.
        rows.append(
            {
                "date": date.fromisoformat(dt.text[:10]).isoformat(),
                "kind": "REVIEW",
                "amount": str(value),
                "currency": currency,
                "account": account,
                "reference": ref.text,
                "counteraccount": "",
                "asset": "",
                "quantity": "0",
                "fee": "0",
                "fx_rate": "1" if currency == "EUR" else "0",
                "line": i + 1,
            }
        )
    return rows


def row_key(row):
    # Stable bank/broker transaction identity, independent of filename or import order.
    return hashlib.sha256(
        (row["account"] + "|" + row["reference"]).encode()
    ).hexdigest()


def apply_row(book, row):
    key = row_key(row)
    if any(posting["event_id"] == key for posting in book["journal"]):
        return "DUPLICATE"
    account = book["accounts"].get(row["account"])
    if not account:
        raise ValueError("UNKNOWN_ACCOUNT")
    if account["currency"] != row["currency"]:
        raise ValueError("ACCOUNT_CURRENCY_MISMATCH")
    date.fromisoformat(row["date"])
    if not row["reference"].strip():
        raise ValueError("REFERENCE_REQUIRED")
    kind = row["kind"]
    v = amount(row["amount"])
    rate = amount(row["fx_rate"])
    fee = amount(row.get("fee", "0"))
    if kind == "REVIEW":
        raise ValueError("CLASSIFICATION_REQUIRED")
    if rate <= 0:
        raise ValueError("MISSING_HISTORICAL_FX")
    if row["currency"] == "EUR" and rate != 1:
        raise ValueError("EUR_FX_MUST_BE_ONE")
    if fee < 0:
        raise ValueError("NEGATIVE_FEE")
    if fee and kind not in {"BUY", "SELL"}:
        raise ValueError("FEES_REQUIRE_SEPARATE_LINE")
    value = D(money(v * rate))
    entity = account["entity"]
    cash = "cash:" + account["id"]
    source = {
        **row,
        "native_cash": str(v),
        "fx_source": "USER_CONFIRMED_HISTORICAL",
        "quality": book["scope"],
    }
    lines = [(cash, value, entity)]
    if kind in {"INCOME", "DIVIDEND", "INTEREST"}:
        if v <= 0:
            raise ValueError("POSITIVE_INCOME_REQUIRED")
        lines.append(("income:" + kind.lower(), -value, entity))
    elif kind in {"EXPENSE", "FEE"}:
        if v >= 0:
            raise ValueError("NEGATIVE_EXPENSE_REQUIRED")
        lines.append(("expense:" + kind.lower(), -value, entity))
    elif kind in {"TRANSFER", "INTERCOMPANY"}:
        other = book["accounts"].get(row["counteraccount"])
        if not other or other["id"] == account["id"]:
            raise ValueError("COUNTERACCOUNT_REQUIRED")
        if other["currency"] != account["currency"]:
            raise ValueError("CROSS_CURRENCY_TRANSFER_REQUIRES_TWO_REVIEWED_LEGS")
        if kind == "TRANSFER" and other["entity"] != entity:
            raise ValueError("INTERCOMPANY_CLASSIFICATION_REQUIRED")
        # Both imported bank legs post to a common clearing key. A single leg stays unreconciled.
        group = "|".join(sorted([account["id"], other["id"]]))
        if kind == "INTERCOMPANY" and other["entity"] == entity:
            raise ValueError("INTERCOMPANY_REQUIRES_DISTINCT_ENTITIES")
        lines.append(
            (
                (
                    "intercompany_loan:"
                    if kind == "INTERCOMPANY"
                    else "transfer_clearing:"
                )
                + group,
                -value,
                entity,
            )
        )
    elif kind in {"BUY", "SELL"}:
        asset = row["asset"]
        quantity = amount(row["quantity"])
        if not asset or quantity <= 0:
            raise ValueError("ASSET_AND_POSITIVE_QUANTITY_REQUIRED")
        position_key = account["id"] + "|" + asset
        prior = [
            posting
            for posting in book["journal"]
            if posting["source"].get("kind") in {"BUY", "SELL"}
            and posting["source"].get("account") == row["account"]
            and posting["source"].get("asset") == asset
            and posting["event_id"] not in book.get("reversals", [])
        ]
        if prior and row["date"] < max(posting["source"]["date"] for posting in prior):
            raise ValueError("HISTORICAL_TRADE_ORDER_REQUIRES_REVIEW")
        pos = book["positions"].setdefault(
            position_key,
            {
                "account": account["id"],
                "entity": entity,
                "asset": asset,
                "quantity": "0",
                "cost_eur": "0",
                "cost_native": "0",
                "mark_eur": None,
                "mark_at": None,
            },
        )
        oldq, oldcost = D(pos["quantity"]), D(pos["cost_eur"])
        native_basis = pos.get(
            "cost_native", pos["cost_eur"] if row["currency"] == "EUR" else None
        )
        if native_basis is None:
            raise ValueError("NATIVE_COST_BASIS_REQUIRES_REVIEW")
        old_native = D(native_basis)
        fee_eur = D(money(fee * rate))
        if kind == "BUY":
            if v >= 0 or abs(value) <= fee_eur:
                raise ValueError("BUY_REQUIRES_NEGATIVE_NET_CASH")
            cost = abs(value) - fee_eur
            pos["quantity"] = str(oldq + quantity)
            pos["cost_eur"] = money(oldcost + cost)
            native_delta = abs(v) - fee
            pos["cost_native"] = money(old_native + native_delta)
            source["cost_delta_native"] = money(native_delta)
            lines.extend(
                [
                    ("inventory:" + position_key, cost, entity),
                    ("expense:fees", fee_eur, entity),
                ]
            )
        else:
            if v <= 0 or quantity > oldq:
                raise ValueError("SELL_EXCEEDS_POSITION")
            cost = oldcost if quantity == oldq else D(money(oldcost * quantity / oldq))
            pnl = value + fee_eur - cost
            native_cost = (
                old_native
                if quantity == oldq
                else D(money(old_native * quantity / oldq))
            )
            pos["cost_native"] = money(old_native - native_cost)
            source["cost_delta_native"] = money(-native_cost)
            market_pnl = D(money((v + fee - native_cost) * rate))
            source["market_pnl_eur"] = money(market_pnl)
            source["fx_pnl_eur"] = money(pnl - market_pnl)
            pos["quantity"] = str(oldq - quantity)
            pos["cost_eur"] = money(oldcost - cost)
            lines.extend(
                [
                    ("inventory:" + position_key, -cost, entity),
                    ("expense:fees", fee_eur, entity),
                    ("realized_pnl", -pnl, entity),
                ]
            )
    else:
        raise ValueError("UNKNOWN_TRANSACTION_KIND")
    post(book, key, lines, source)
    return "IMPORTED"


def preview_import(book, rows):
    working = copy.deepcopy(book)
    results = []
    for row in rows:
        row = copy.deepcopy(row)
        key = row_key(row)
        existing = next(
            (posting for posting in working["journal"] if posting["event_id"] == key),
            None,
        )
        if existing and any(
            str(existing["source"].get(k, "")) != str(row.get(k, ""))
            for k in [
                "date",
                "amount",
                "currency",
                "kind",
                "quantity",
                "asset",
                "fee",
                "fx_rate",
                "counteraccount",
            ]
        ):
            results.append(
                {
                    "row": row,
                    "status": "CONFLICT",
                    "reason": "REFERENCE_CONTENT_CHANGED",
                }
            )
            continue
        candidate = copy.deepcopy(working)
        try:
            status = apply_row(candidate, row)
            working = candidate
            reason = None
        except (ValueError, ArithmeticError) as e:
            status = "REVIEW"
            reason = str(e)
        results.append({"row": row, "status": status, "reason": reason})
    return {
        "rows": results,
        "importable": sum(x["status"] == "IMPORTED" for x in results),
        "duplicates": sum(x["status"] == "DUPLICATE" for x in results),
        "review_count": sum(x["status"] in {"CONFLICT", "REVIEW"} for x in results),
        "book_after": working,
    }


def reconcile(book):
    total = sum((D(posting["amount_eur"]) for posting in book["journal"]), D(0))
    clearing = {}
    for line in book["journal"]:
        if line["account"].startswith(("transfer_clearing:", "intercompany_loan:")):
            clearing[line["account"]] = clearing.get(line["account"], D(0)) + D(
                line["amount_eur"]
            )
    issues = [
        {"type": "UNMATCHED_TRANSFER", "account": k, "difference_eur": money(v)}
        for k, v in clearing.items()
        if v
    ]
    if total:
        issues.append({"type": "UNBALANCED_LEDGER", "difference_eur": money(total)})
    # Holdings and inventory cost are reconciled, not just overall journal balance.
    for key, pos in book["positions"].items():
        cost = sum(
            (
                D(posting["amount_eur"])
                for posting in book["journal"]
                if posting["account"] == "inventory:" + key
            ),
            D(0),
        )
        if cost != D(pos["cost_eur"]):
            issues.append({"type": "POSITION_COST_MISMATCH", "position": key})
    return {
        "balanced": total == 0,
        "issues": issues,
        "status": "RECONCILED" if not issues else "REQUIRES_REVIEW",
    }


def snapshot(book, root=None):
    weights = {e: D(1) for e in book["entities"]} if root is None else {}
    if root is not None:
        if root not in book["entities"]:
            raise ValueError("UNKNOWN_ENTITY")

        def walk(e, w):
            weights[e] = weights.get(e, D(0)) + w
            for link in book["ownership"]:
                if link["parent"] == e:
                    walk(link["child"], w * D(link["percentage"]) / 100)

        walk(root, D(1))
        if any(w > 1 for w in weights.values()):
            raise ValueError("OWNERSHIP_PATH_DOUBLE_COUNT")
    accounts = []
    cash_total = D(0)
    income = expense = realized = realized_market = realized_fx = D(0)
    for a in book["accounts"].values():
        value = sum(
            (
                D(posting["amount_eur"])
                for posting in book["journal"]
                if posting["account"] == "cash:" + a["id"]
            ),
            D(0),
        )
        weight = weights.get(a["entity"], D(0))
        accounts.append(
            {
                **a,
                "balance_eur": money(value),
                "native_balance": str(native_cash(book, a["id"])),
                "ownership_weight": str(weight),
                "included_eur": money(value * weight),
            }
        )
        cash_total += value * weight
    position_values = []
    position_total = D(0)
    missing = []
    for key, pos in book["positions"].items():
        weight = weights.get(pos["entity"], D(0))
        qty = D(pos["quantity"])
        value = (
            D(pos["mark_eur"]) * qty
            if pos["mark_eur"] is not None
            else D(pos["cost_eur"])
        )
        position_values.append(
            {
                **pos,
                "id": key,
                "value_eur": money(value),
                "unrealized_eur": money(value - D(pos["cost_eur"])),
                "valuation_method": "CONFIRMED_MARK"
                if pos["mark_eur"]
                else "COST_FALLBACK",
                "ownership_weight": str(weight),
            }
        )
        position_total += value * weight
        if pos["mark_eur"] is None and qty and weight:
            missing.append(key)
    for line in book["journal"]:
        value = D(line["amount_eur"]) * weights.get(line["entity"], D(0))
        if line["account"].startswith("income:"):
            income -= value
        if line["account"].startswith("expense:"):
            expense += value
        if line["account"] == "realized_pnl":
            realized -= value
            realized_fx += D(line["source"].get("fx_pnl_eur", "0")) * weights.get(
                line["entity"], D(0)
            )
            realized_market += D(
                line["source"].get("market_pnl_eur", str(-D(line["amount_eur"])))
            ) * weights.get(line["entity"], D(0))
    intercompany = sum(
        (
            D(posting["amount_eur"]) * weights.get(posting["entity"], D(0))
            for posting in book["journal"]
            if posting["account"].startswith("intercompany_loan:")
        ),
        D(0),
    )
    other_total = intercompany
    asset_rows = []
    for asset in book.get("assets", {}).values():
        w = weights.get(asset["entity"], D(0))
        value = D(asset["value_eur"])
        duplicate = (
            asset["kind"] == "EQUITY_INTEREST"
            and weights.get(asset.get("linked_entity"), D(0)) > 0
        )
        included = D(0) if duplicate or asset["kind"] == "PENSION_RIGHT" else value * w
        other_total += included
        asset_rows.append(
            {
                **asset,
                "included_eur": money(included),
                "eliminated": duplicate,
                "liquid": asset["kind"] == "CASH_EQUIVALENT",
            }
        )
    return {
        "intercompany_loan_net_eur": money(intercompany),
        "assets": asset_rows,
        "other_net_assets_eur": money(other_total),
        "positions_and_other_eur": money(position_total + other_total),
        "scope": book["scope"],
        "revision": book["revision"],
        "entities": list(book["entities"].values()),
        "ownership": book["ownership"],
        "accounts": accounts,
        "positions": position_values,
        "cash_eur": money(cash_total),
        "positions_eur": money(position_total),
        "economic_wealth_eur": money(cash_total + position_total + other_total),
        "income_eur": money(income),
        "expenses_eur": money(expense),
        "realized_eur": money(realized),
        "realized_market_eur": money(realized_market),
        "realized_fx_eur": money(realized_fx),
        "missing_marks": missing,
        "reconciliation": reconcile(book),
        "consolidation": "Underlying assets weighted through ownership; no duplicate holding share value",
        "private_spendable_after_tax": None,
        "journal": book["journal"][-200:],
        "journal_count": len(book["journal"]),
        "goals": book["goals"],
        "reviews": book["reviews"],
    }


def demo_book():
    b = new_book("DEMO")
    for i, n, k in [
        ("private", "Voorbeeld privé", "PERSON"),
        ("holding", "Voorbeeld holding", "HOLDING"),
        ("operating", "Voorbeeld werk-BV", "OPERATING_COMPANY"),
    ]:
        add_entity(b, i, n, k)
    set_ownership(b, "private", "holding", "100")
    set_ownership(b, "holding", "operating", "100")
    for a, n, e, v in [
        ("demo-bank", "Oefenbank privé", "private", "25000"),
        ("demo-broker", "Oefenbroker", "private", "50000"),
        ("demo-holding", "Oefenrekening holding", "holding", "40000"),
        ("demo-operating", "Oefenrekening werk-BV", "operating", "15000"),
    ]:
        add_account(b, a, n, e, "EUR", v)
    b["revision"] = 1
    return b


def csv_export(book):
    def safe(value):
        text = str(value)
        return "'" + text if text[:1] in {"=", "+", "-", "@", "\t", "\r"} else text

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        ["event_id", "account", "entity", "amount_eur", "date", "reference"]
    )
    for posting in book["journal"]:
        writer.writerow(
            [safe(posting[k]) for k in ["event_id", "account", "entity", "amount_eur"]]
            + [
                safe(posting["source"]["date"]),
                safe(posting["source"].get("reference", "")),
            ]
        )
    return out.getvalue()


def reverse_event(book, event_id, reason):
    if event_id in book.get("reversals", []):
        raise ValueError("ALREADY_REVERSED")
    lines = [posting for posting in book["journal"] if posting["event_id"] == event_id]
    if not lines or event_id.startswith("opening:"):
        raise ValueError("REVERSAL_NOT_SUPPORTED")
    source = lines[0]["source"]
    kind = source["kind"]
    if kind == "REVERSAL":
        raise ValueError("REVERSAL_OF_REVERSAL_NOT_SUPPORTED")
    if kind in {"BUY", "SELL"}:
        key = source["account"] + "|" + source["asset"]
        pos = book["positions"][key]
        qty = D(source["quantity"])
        subsequent = [
            posting
            for posting in book["journal"]
            if posting["source"].get("kind") in {"BUY", "SELL"}
            and posting["source"].get("account") == source["account"]
            and posting["source"].get("asset") == source["asset"]
            and posting["event_id"] not in book.get("reversals", [])
        ]
        if subsequent[-1]["event_id"] != event_id:
            raise ValueError("REVERSE_DEPENDENT_TRANSACTIONS_FIRST")
        if any(
            v.get("kind") == "SPLIT"
            and v.get("position_id") == key
            and v.get("created_at", "9999") > lines[0]["created_at"]
            for v in book["valuations"]
        ):
            raise ValueError("CORPORATE_ACTION_REQUIRES_REVIEW")
        newq = D(pos["quantity"]) + (-qty if kind == "BUY" else qty)
        cost = sum(
            (
                D(posting["amount_eur"])
                for posting in lines
                if posting["account"] == "inventory:" + key
            ),
            D(0),
        )
        newcost = D(pos["cost_eur"]) - cost
        if newq < 0 or newcost < 0:
            raise ValueError("REVERSE_DEPENDENT_TRANSACTIONS_FIRST")
        pos["quantity"] = str(newq)
        pos["cost_eur"] = money(newcost)
        if "cost_native" in pos:
            pos["cost_native"] = money(
                D(pos["cost_native"]) - D(source.get("cost_delta_native", str(cost)))
            )
    src = {
        **source,
        "kind": "REVERSAL",
        "date": date.today().isoformat(),
        "native_cash": str(-D(source.get("native_cash", source["amount"]))),
        "reversal_of": event_id,
        "market_pnl_eur": money(
            -D(
                source.get(
                    "market_pnl_eur",
                    str(
                        -sum(
                            (
                                D(p["amount_eur"])
                                for p in lines
                                if p["account"] == "realized_pnl"
                            ),
                            D(0),
                        )
                    ),
                )
            )
        ),
        "fx_pnl_eur": money(-D(source.get("fx_pnl_eur", "0"))),
        "reason": reason,
    }
    post(
        book,
        "reversal:" + event_id,
        [
            (posting["account"], -D(posting["amount_eur"]), posting["entity"])
            for posting in lines
        ],
        src,
    )
    book.setdefault("reversals", []).append(event_id)


def corporate_action(
    book, position_id, action_id, numerator, denominator, effective_date
):
    if any(v.get("id") == action_id for v in book["valuations"]):
        return "DUPLICATE"
    n, d = amount(numerator), amount(denominator)
    if n <= 0 or d <= 0:
        raise ValueError("INVALID_SPLIT_RATIO")
    if date.fromisoformat(effective_date) > date.today():
        raise ValueError("FUTURE_ACTION_NOT_EFFECTIVE")
    pos = book["positions"].get(position_id)
    if not pos:
        raise ValueError("UNKNOWN_POSITION")
    position_events = [
        posting
        for posting in book["journal"]
        if posting["account"] == "inventory:" + position_id
    ]
    if position_events and effective_date < max(
        posting["source"]["date"] for posting in position_events
    ):
        raise ValueError("HISTORICAL_ACTION_REQUIRES_REVIEW")
    old = D(pos["quantity"])
    new = old * n / d
    if new.as_tuple().exponent < -8 and new != new.quantize(D(".00000001")):
        raise ValueError("FRACTIONAL_SETTLEMENT_REQUIRES_REVIEW")
    pos["quantity"] = str(new)
    if pos["mark_eur"] is not None:
        pos["mark_eur"] = str(D(pos["mark_eur"]) * d / n)
    book["valuations"].append(
        {
            "id": action_id,
            "kind": "SPLIT",
            "position_id": position_id,
            "before_quantity": str(old),
            "after_quantity": str(new),
            "effective_date": effective_date,
            "cost_unchanged": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return "APPLIED"


def performance(periods, flows):
    growth = D(1)
    for period in periods:
        start, end, external = map(
            D, [period["start"], period["end"], period["external_flow"]]
        )
        if start <= 0:
            return {"twr": None, "irr": None, "status": "INVALID_STARTING_VALUE"}
        growth *= (end - external) / start
    ordered = sorted(flows, key=lambda x: x["date"])
    signs = [1 if D(x["amount"]) > 0 else -1 for x in ordered if D(x["amount"]) != 0]
    if not signs or len(set(signs)) < 2:
        return {"twr": str(growth - 1), "irr": None, "status": "NO_IRR_SOLUTION"}
    if sum(a != b for a, b in zip(signs, signs[1:])) > 1:
        return {"twr": str(growth - 1), "irr": None, "status": "MULTIPLE_IRR_POSSIBLE"}
    start_date = date.fromisoformat(ordered[0]["date"])

    def npv(rate):
        return sum(
            (
                D(f["amount"])
                / (D(1) + rate)
                ** (D((date.fromisoformat(f["date"]) - start_date).days) / D("365.25"))
                for f in ordered
            ),
            D(0),
        )

    low, high = D("-.999"), D("10")
    if npv(low) * npv(high) > 0:
        return {
            "twr": str(growth - 1),
            "irr": None,
            "status": "IRR_OUTSIDE_SEARCH_RANGE",
        }
    for _ in range(120):
        mid = (low + high) / 2
        if npv(low) * npv(mid) <= 0:
            high = mid
        else:
            low = mid
    return {
        "twr": str((growth - 1).quantize(D(".000001"))),
        "irr": str(mid.quantize(D(".000001"))),
        "status": "CALCULATED",
        "method": "TWR using period-end external flows; dated IRR, bounded single-sign-change root",
    }


def revalue_cash(book, account_id, rate_to_eur, as_of, source):
    account = book["accounts"].get(account_id)
    if not account:
        raise ValueError("UNKNOWN_ACCOUNT")
    rate = amount(rate_to_eur)
    if rate <= 0 or account["currency"] == "EUR" and rate != 1:
        raise ValueError("INVALID_FX_RATE")
    if date.fromisoformat(as_of) > date.today():
        raise ValueError("FUTURE_VALUATION_NOT_CURRENT")
    prior_dates = [
        p["source"].get("date", "")
        for p in book["journal"]
        if p["account"] == "cash:" + account_id
    ]
    if prior_dates and as_of < max(prior_dates):
        raise ValueError("HISTORICAL_FX_VALUATION_REQUIRES_REVIEW")
    native = native_cash(book, account_id)
    previous = sum(
        (
            D(p["amount_eur"])
            for p in book["journal"]
            if p["account"] == "cash:" + account_id
        ),
        D(0),
    )
    value = D(money(native * rate))
    delta = value - previous
    key = hashlib.sha256(
        (
            "FX|" + account_id + "|" + as_of + "|" + rate_to_eur + "|" + str(previous)
        ).encode()
    ).hexdigest()
    if delta:
        post(
            book,
            key,
            [
                ("cash:" + account_id, delta, account["entity"]),
                ("valuation_fx", -delta, account["entity"]),
            ],
            {
                "kind": "FX_VALUATION",
                "account": account_id,
                "date": as_of,
                "amount": "0",
                "native_cash": "0",
                "currency": account["currency"],
                "fx_rate": rate_to_eur,
                "source": source,
                "previous_eur": money(previous),
                "quality": "USER_CONFIRMED_REFERENCE",
            },
        )
    return {
        "difference_eur": money(delta),
        "native_balance": str(native),
        "value_eur": money(value),
        "rate_to_eur": rate_to_eur,
    }
