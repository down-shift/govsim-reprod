"""Construct and check a G3-compatible stock trace under Rehm v2, Eq. (1)."""
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
import sys

from .core import Agent, Snapshot, evaluate, reorder

CAPACITY = (100, 85, 70, 56, 56, 56)
POVERTY = 7
NAMES = "ABCDE"
POLICIES = ("deferred_tenure", "named_tenure")


def next_stock(stock, catches, capacity):
    """Restrict to feasible, unsubsidized catches in this constructed trace."""
    total = sum(catches)
    if len(catches) != len(NAMES) or min(catches) < POVERTY or total > stock:
        raise ValueError("the constructed profile must meet subsistence without overharvest")
    return min(capacity, 2 * (stock - total))


def snapshot(stock, capacity, elapsed, catch_cap):
    return Snapshot(stock, capacity, POVERTY, 0,
                    tuple(Agent(name, elapsed, catch_cap=catch_cap) for name in NAMES))


def evaluate_trace(catches):
    stock = CAPACITY[0]
    result = []
    for elapsed, capacity in enumerate(CAPACITY):
        state = snapshot(stock, capacity, elapsed, 8)
        harvest = catches[elapsed] if elapsed < len(catches) else None
        outcomes = {policy: [list(x) for x in evaluate(policy, state, state.agents)]
                    for policy in POLICIES}
        result.append({"elapsed": elapsed, "stock": stock, "capacity": capacity,
                       "harvest": harvest, "removed_in_isolated_preview": outcomes})
        if harvest is not None:
            stock = next_stock(stock, harvest, CAPACITY[elapsed + 1])
    return result


def main(output):
    common = [(7,) * len(NAMES)] * (len(CAPACITY) - 2)
    witness = evaluate_trace(common + [(7,) * len(NAMES)])
    assert [step["stock"] for step in witness] == [100, 85, 70, 56, 42, 14]
    assert all(step["removed_in_isolated_preview"] == {p: [[]] for p in POLICIES}
               for step in witness[:-1])
    episodes = []
    for final_catches in product((7, 8), repeat=len(NAMES)):
        trace = evaluate_trace(common + [final_catches])
        trigger = snapshot(trace[-1]["stock"], CAPACITY[-1], len(common) + 1, 8)
        checks = {policy: reorder(policy, trigger) for policy in POLICIES}
        for policy, target_count in zip(POLICIES, (1, 4), strict=True):
            assert checks[policy]["removal_counts"] == [target_count]
            assert checks[policy]["orders_differing_from_baseline"] == 96
            assert checks[policy]["distinct_conditional_distributions"] == 5
        episodes.append({"final_harvest_by_identity": dict(zip(NAMES, final_catches, strict=True)),
                         "trigger": asdict(trigger), "checks": checks})
    stocks = sorted({episode["trigger"]["stock"] for episode in episodes})
    assert len(episodes) == 32 and stocks == [4, 6, 8, 10, 12, 14]
    summary = {
        "harvest_profiles": len(episodes),
        "distinct_trigger_stocks": stocks,
        "sensitive_profiles_by_rule": {policy: len(episodes) for policy in POLICIES},
        "orders_per_trigger": 120,
        "orders_changing_identity_set_per_profile_per_rule": 96,
    }
    output.write_text(json.dumps({
        "source": "arXiv:2609.22600v2, Eq. (1), Appendices A.1 and B",
        "scope": "Constructed stock-model witness; no full-simulator or historical replay.",
        "assumptions": {
            "capacity_path": CAPACITY,
            "prior_harvest_per_member": 7,
            "assumed_per_member_catch_cap": 8,
            "last_round_harvest_per_member": [7, 8],
            "balances_and_taxes": 0,
            "lookahead": "One transition from stock 42; finish before harvesting at the trigger.",
        },
        "summary": summary, "equal_harvest_witness": witness, "profiles": episodes,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m govsim_audit.reachability OUTPUT.json")
    main(Path(sys.argv[1]))
