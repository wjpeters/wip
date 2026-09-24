from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
subprocess.run(["rtk", "proxy", "npm", "run", "e2e"], cwd=root / "apps/web", check=True)
