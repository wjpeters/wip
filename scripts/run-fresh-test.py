from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
subprocess.run(
    ["rtk", "proxy", "node", "e2e/fresh-install.mjs"], cwd=root / "apps/web", check=True
)
