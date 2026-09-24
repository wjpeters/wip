"""Encrypted local backups; restore verification never overwrites an existing database."""

import base64
import argparse
import hashlib
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("action", choices=["create", "verify", "recover"])
parser.add_argument(
    "--project", choices=["wpos-mtt", "wpos-mtt-qa"], default="wpos-mtt"
)
parser.add_argument("--file", type=Path)
args = parser.parse_args()
compose = [
    "docker",
    "compose",
    "-p",
    args.project,
    "-f",
    str(ROOT / "infra/compose/compose.yaml"),
    "exec",
    "-T",
    "postgres",
]
env = {**os.environ, "WEB_PORT": "4187" if args.project.endswith("-qa") else "4186"}


def command(*parts, data=None):
    result = subprocess.run(
        [*compose, *parts], input=data, capture_output=True, env=env
    )
    if result.returncode:
        raise RuntimeError(
            "Database command failed; no secret-bearing output is printed."
        )
    return result.stdout


def sql(database, statement):
    return command(
        "psql",
        "-U",
        "mtt",
        "-d",
        database,
        "-X",
        "-At",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        statement,
    )


def fingerprint(database):
    hashes = {}
    tables = (
        sql(
            database,
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename",
        )
        .decode()
        .splitlines()
    )
    for table in tables:
        if not table.replace("_", "").isalnum():
            raise RuntimeError("UNEXPECTED_TABLE_NAME")
        payload = sql(
            database,
            f'SELECT value FROM (SELECT row_to_json(t)::text AS value FROM "{table}" t) q ORDER BY value',
        )
        hashes[table] = hashlib.sha256(payload).hexdigest()
    return hashes


keyfile = ROOT / ".secrets/backup_key"
if not keyfile.exists():
    if args.action != "create":
        raise SystemExit("Missing original backup key. No data changed.")
    fd = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as out:
        out.write(Fernet.generate_key())
cipher = Fernet(keyfile.read_bytes())
if args.action == "create":
    # pg_dump gives a transactionally consistent snapshot. Plaintext stays in memory.
    dump = command(
        "pg_dump", "-U", "mtt", "-d", "mtt", "-Fc", "--no-owner", "--no-privileges"
    )
    folder = ROOT / "backups"
    folder.mkdir(exist_ok=True, mode=0o700)
    target = folder / (
        args.project
        + "-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        + ".fernet"
    )
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as out:
        bundle = {
            "format": "MTT_BACKUP_2",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database": base64.b64encode(dump).decode(),
            "vault_key": (ROOT / ".secrets/vault_key").read_text()
            if (ROOT / ".secrets/vault_key").exists()
            else None,
        }
        out.write(cipher.encrypt(json.dumps(bundle).encode()))
    print(json.dumps({"backup": str(target), "encrypted_bytes": target.stat().st_size}))
else:
    if not args.file:
        raise SystemExit("--file is required")
    encrypted = args.file.read_bytes()
    try:
        dump = cipher.decrypt(encrypted)
    except InvalidToken:
        raise SystemExit("Authentication failed. No database created or changed.")
    vault_cipher = None
    if dump.startswith(b"{"):
        bundle = json.loads(dump)
        if bundle.get("format") != "MTT_BACKUP_2":
            raise SystemExit("Unsupported authenticated backup format")
        dump = base64.b64decode(bundle["database"], validate=True)
        if bundle.get("vault_key"):
            vault_cipher = Fernet(bundle["vault_key"].encode())
    database = (
        "recovered_mtt_" if args.action == "recover" else "restore_test_mtt_"
    ) + uuid.uuid4().hex[:12]
    sql("postgres", "CREATE DATABASE " + database)
    completed = False
    try:
        command(
            "pg_restore",
            "-U",
            "mtt",
            "-d",
            database,
            "--no-owner",
            "--exit-on-error",
            data=dump,
        )
        balance = sql(database, "SELECT COALESCE(SUM(amount),0)=0 FROM ledger").strip()
        cash = sql(
            database,
            "SELECT (SELECT SUM(amount) FROM ledger WHERE account='cash') = (SELECT (state->>'cash')::numeric FROM account WHERE id='demo-paper')",
        ).strip()
        assert balance == b"t" and cash == b"t", "Restored ledger does not reconcile"
        vault_count = 0
        if (
            sql(database, "SELECT to_regclass('public.vault') IS NOT NULL").strip()
            == b"t"
        ):
            records = (
                sql(
                    database,
                    "SELECT json_build_object('name',name,'data',encode(ciphertext,'base64'),'hash',content_hash)::text FROM vault",
                )
                .decode()
                .splitlines()
            )
            for line in records:
                record = json.loads(line)
                if vault_cipher is None:
                    raise RuntimeError(
                        "Backup has documents but no encrypted recovery key"
                    )
                raw = vault_cipher.decrypt(base64.b64decode(record["data"]))
                assert hashlib.sha256(raw).hexdigest() == record["hash"], (
                    "Restored document hash mismatch"
                )
                json.loads(vault_cipher.decrypt(record["name"].encode()))
                vault_count += 1
        report = {
            "status": "PASS",
            "project": args.project,
            "encrypted_sha256": hashlib.sha256(encrypted).hexdigest(),
            "ledger_balanced": True,
            "vault_documents_decrypted_and_verified": vault_count,
            "vault_key_in_encrypted_bundle": vault_cipher is not None,
            "cash_reconciled": True,
            "restored_hashes": fingerprint(database),
        }
        if args.action == "verify":
            report["matches_current_source"] = report["restored_hashes"] == fingerprint(
                "mtt"
            )
            # Old backups legitimately differ from a database that changed afterwards.
            report["temporary_database_removed"] = True
        else:
            sql(database, "DELETE FROM sessions")
            if vault_cipher is not None:
                recovered_key = ROOT / ".secrets" / ("recovered_vault_key_" + database)
                fd = os.open(recovered_key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w") as output:
                    output.write(bundle["vault_key"])
                report["recovered_vault_key_file"] = str(recovered_key)
            report["recovered_database"] = database
            report["active_database_unchanged"] = True
        print(json.dumps(report, indent=2))
        completed = True
    finally:
        if args.action == "verify" or not completed:
            sql("postgres", "DROP DATABASE " + database + " WITH (FORCE)")
