"""Optional bounded workaround for exhausted Docker default address pools. No network removal."""

import argparse
import ipaddress
import json
import subprocess

p = argparse.ArgumentParser()
p.add_argument(
    "--project", choices=["wpos-mtt", "wpos-mtt-qa", "wpos-mtt-fresh05"], required=True
)
p.add_argument(
    "--prefix", required=True, help="Unused private /24 prefix, for example 10.254.186"
)
a = p.parse_args()
base = ipaddress.ip_network(a.prefix + ".0/24")
if not base.is_private:
    raise SystemExit("Private IPv4 prefix required")
ids = subprocess.check_output(["docker", "network", "ls", "-q"], text=True).split()
networks = json.loads(
    subprocess.check_output(["docker", "network", "inspect", *ids], text=True)
)
existing = {n["Name"]: n for n in networks}
occupied = [
    ipaddress.ip_network(c["Subnet"])
    for n in networks
    for c in (n["IPAM"]["Config"] or [])
    if c.get("Subnet")
]
for i, name in enumerate(
    [
        "edge",
        "frontend",
        "database",
        "source-fetch",
        "market-internal",
        "market-egress",
        "assistant-internal",
        "ai-egress",
    ]
):
    full = a.project + "_" + name
    if full in existing:
        continue
    subnet = ipaddress.ip_network(f"{a.prefix}.{i * 16}/28")
    if any(subnet.version == old.version and subnet.overlaps(old) for old in occupied):
        raise SystemExit("Subnet conflict: " + str(subnet))
    command = [
        "docker",
        "network",
        "create",
        "--subnet",
        str(subnet),
        "--label",
        "com.docker.compose.project=" + a.project,
        "--label",
        "com.docker.compose.network=" + name,
    ]
    if name in ["frontend", "database", "market-internal", "assistant-internal"]:
        command += ["--internal"]
    subprocess.run([*command, full], check=True, capture_output=True)
    occupied.append(subnet)
    print("Created", full, str(subnet))
