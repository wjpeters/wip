from pathlib import Path
import subprocess
import sys
import webbrowser

root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "scripts/setup-local.py"], cwd=root, check=True)
subprocess.run(
    [
        "rtk",
        "proxy",
        "docker",
        "compose",
        "-f",
        "infra/compose/compose.yaml",
        "up",
        "--build",
        "-d",
        "--wait",
    ],
    cwd=root,
    check=True,
)
webbrowser.open("http://localhost:4186")
