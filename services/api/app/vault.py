"""Authenticated local document encryption. Downloads are attachments, never executable views."""

import base64
import hashlib
import json
import os
import re
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

MAX_BYTES = 5 * 1024 * 1024
MIMES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/plain",
    "text/csv",
    "application/json",
}


def cipher():
    return Fernet(
        Path(os.getenv("VAULT_KEY_FILE", "/run/secrets/vault_key")).read_bytes().strip()
    )


def encrypt(name, mime, content_b64, metadata):
    if mime not in MIMES:
        raise ValueError("DOCUMENT_TYPE_NOT_SUPPORTED")
    if len(content_b64) > MAX_BYTES * 4 // 3 + 8:
        raise ValueError("DOCUMENT_TOO_LARGE")
    try:
        raw = base64.b64decode(content_b64, validate=True)
    except ValueError:
        raise ValueError("INVALID_BASE64")
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("DOCUMENT_SIZE")
    if mime == "application/pdf" and not raw.startswith(b"%PDF-"):
        raise ValueError("PDF_SIGNATURE_MISMATCH")
    if mime == "image/png" and not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("PNG_SIGNATURE_MISMATCH")
    if mime == "image/jpeg" and not raw.startswith(b"\xff\xd8\xff"):
        raise ValueError("JPEG_SIGNATURE_MISMATCH")
    if mime.startswith("text/") or mime == "application/json":
        raw.decode("utf-8")
    clean = re.sub(r"[\x00-\x1f/\\]", "_", name).strip()[:180]
    if not clean:
        raise ValueError("DOCUMENT_NAME_REQUIRED")
    c = cipher()
    meta = {"name": clean, **metadata}
    return {
        "name": c.encrypt(json.dumps(meta).encode()).decode(),
        "mime": mime,
        "ciphertext": c.encrypt(raw),
        "content_hash": hashlib.sha256(raw).hexdigest(),
        "size": len(raw),
    }


def metadata(encrypted):
    try:
        return json.loads(cipher().decrypt(encrypted.encode()))
    except (InvalidToken, ValueError):
        raise ValueError("VAULT_AUTHENTICATION_FAILED")


def decrypt(ciphertext, expected_hash):
    try:
        raw = cipher().decrypt(bytes(ciphertext))
    except InvalidToken:
        raise ValueError("VAULT_AUTHENTICATION_FAILED")
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError("VAULT_HASH_MISMATCH")
    return raw
