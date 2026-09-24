"""Separate versioned domain documents; mutations use one PostgreSQL row lock."""

from psycopg.types.json import Jsonb


def migrate_extended(c):
    c.execute(
        "CREATE TABLE IF NOT EXISTS domain_state (key TEXT PRIMARY KEY, document JSONB NOT NULL)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS vault (id TEXT PRIMARY KEY, scope TEXT NOT NULL, name TEXT NOT NULL, mime TEXT NOT NULL, ciphertext BYTEA NOT NULL, content_hash TEXT NOT NULL, size INT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS analysis_jobs (id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT NOT NULL, request JSONB NOT NULL, result JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )


def document(c, key, factory, lock=False):
    c.execute(
        "INSERT INTO domain_state VALUES(%s,%s) ON CONFLICT DO NOTHING",
        (key, Jsonb(factory())),
    )
    return c.execute(
        "SELECT document FROM domain_state WHERE key=%s"
        + (" FOR UPDATE" if lock else " FOR SHARE"),
        (key,),
    ).fetchone()[0]


def save(c, key, value):
    c.execute("UPDATE domain_state SET document=%s WHERE key=%s", (Jsonb(value), key))
