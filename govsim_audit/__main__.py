"""Command-line entry point for the GovSim roster audit."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

from .core import Agent, IMPLEMENTATIONS, Snapshot, reorder
from .experiment import SOURCE, builtin_cases, compare, lottery_comparisons, report


def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def hashes():
    root = Path(__file__).parent
    return {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(root.glob("*.py"))}


def run(output: Path):
    output.mkdir(parents=True, exist_ok=False)
    results = [compare(case) for case in builtin_cases()]
    write_json(output / "audit.json", {
        "schema_version": 1, "publication": SOURCE, "source_sha256": hashes(),
        "cases": results, "lottery_comparisons": lottery_comparisons(results),
    })
    write_json(output / "environment.json", {
        "python": platform.python_version(), "implementation": platform.python_implementation(),
        "platform": sys.platform, "architecture": platform.machine(),
    })
    (output / "summary.md").write_text(report(results), encoding="utf-8")
    print(report(results), end="")
    print(f"Outputs: {output.resolve()}")


def replay(path: Path) -> int:
    raw = path.read_bytes()
    data = json.loads(raw)
    kind = data["kind"]
    if kind not in ("constructed", "historical"):
        raise ValueError("kind must be constructed or historical")
    if not isinstance(data["source"], str) or not data["source"].strip():
        raise ValueError("provide snapshot provenance in source")
    policy = data["policy"]
    if policy not in IMPLEMENTATIONS:
        raise ValueError(f"unknown published policy: {policy!r}")
    world = dict(data["snapshot"])
    agents = world["agents"]
    if not isinstance(agents, list) or any(not isinstance(agent, dict) for agent in agents):
        raise ValueError("snapshot.agents must be an ordered list of agent records")
    if kind == "historical" and any("active" not in agent for agent in agents):
        raise ValueError("historical snapshots require an explicit active flag for every agent")
    world["agents"] = tuple(Agent(**agent) for agent in agents)
    snapshot = Snapshot(**world)
    observed = data["observed_removed"]
    active_names = {a.name for a in snapshot.agents if a.active}
    if (not isinstance(observed, list) or not all(isinstance(a, str) for a in observed)
            or len(observed) != len(set(observed)) or not set(observed) <= active_names):
        raise ValueError("observed_removed must list distinct, initially active identities")
    result = reorder(policy, snapshot)
    matches = result["baseline"]["outcomes"][0]["removed"] == sorted(observed)
    print(json.dumps({
        "kind": kind, "source": data["source"], "policy": policy,
        "source_sha256": hashes(),
        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "observed_removed": sorted(observed), "baseline_matches": matches,
        "interpretation": ("baseline reproduced; inspect order sensitivity"
                           if matches else "baseline mismatch; do not infer a historical effect"),
        "result": result,
    }, indent=2))
    return 0 if matches else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("run", help="run all three checks on the built-in cases")
    audit.add_argument("--out", type=Path, default=Path("runs/govsim"))
    recorded = commands.add_parser("replay", help="check a supplied ordered snapshot")
    recorded.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "run":
            run(args.out)
            return 0
        return replay(args.snapshot)
    except FileExistsError:
        parser.error(f"{args.out} already exists; choose a new --out directory")
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    sys.exit(main())
