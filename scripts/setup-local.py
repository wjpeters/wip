from pathlib import Path
import secrets
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
