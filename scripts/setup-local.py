from base64 import urlsafe_b64encode
from pathlib import Path
import secrets
import os
import sys

root = Path(__file__).resolve().parents[1]
folder = root / ".secrets"
folder.mkdir(exist_ok=True, mode=0o700)
folder.chmod(0o700)
p = folder / "db_password"
if not p.exists():
    p.write_text(secrets.token_urlsafe(48))
    p.chmod(0o600)
print("Lokale database-toegang ingericht. Kies bij openen zelf je appwachtwoord.")

if "--qa" in sys.argv:
    qa = folder / "e2e_password"
    if not qa.exists():
        qa.write_text(secrets.token_urlsafe(32))
    qa.chmod(0o600)
    print(
        "Afzonderlijke QA-toegang ingericht; geen wijziging aan het gebruikersaccount."
    )

# One independent local encryption key, never copied into the synchronized WPOS tree.

vault_key = folder / "vault_key"
if not vault_key.exists():
    fd = os.open(vault_key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as out:
        out.write(urlsafe_b64encode(os.urandom(32)))
vault_key.chmod(0o600)

bridge_token = folder / "assistant_token"
if not bridge_token.exists():
    fd = os.open(bridge_token, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as out:
        out.write(secrets.token_urlsafe(48))
bridge_token.chmod(0o600)
ai_config = folder / "ai_config.json"
if not ai_config.exists():
    fd = os.open(ai_config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as out:
        out.write((root / "services/assistant/config.example.json").read_text())
ai_config.chmod(0o600)

market_token = folder / "market_token"
if not market_token.exists():
    fd = os.open(market_token, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as out:
        out.write(secrets.token_urlsafe(48))
market_token.chmod(0o600)
providers = folder / "providers.json"
if not providers.exists():
    fd = os.open(providers, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as out:
        out.write((root / "services/api/providers.example.json").read_text())
providers.chmod(0o600)
