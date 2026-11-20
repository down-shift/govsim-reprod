"""Exact distributions over removed identities for fixed snapshots."""
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, permutations
from math import isfinite
from types import SimpleNamespace

from . import rules

IMPLEMENTATIONS = {
    "deferred_tenure": rules.survival_population_limit,
    "named_tenure": rules.emergency_population_cap,
    "explicit_index": rules.emergency_cull_rule,
    "explicit_name": rules.right_size_fleet,
}
LOTTERIES = {"uniform_remove_one": 1, "uniform_remove_four": 4}
Outcome = tuple[str, ...]
Distribution = dict[Outcome, Fraction]


@dataclass(frozen=True)
class Agent:
    name: str
    tenure: int
    active: bool = True
    catch_cap: float = 7.0


@dataclass(frozen=True)
class Snapshot:
    stock: float
    capacity: float
    poverty_line: float
    treasury: float
    agents: tuple[Agent, ...]

    def __post_init__(self):
        for value in (self.stock, self.capacity, self.poverty_line, self.treasury):
            if type(value) not in (float, int) or not isfinite(value):
                raise ValueError("world inputs must be finite numbers")
        if not 0 <= self.stock <= self.capacity or self.capacity <= 0:
            raise ValueError("expected 0 <= stock <= positive capacity")
        if self.poverty_line <= 0 or self.treasury < 0:
            raise ValueError("expected positive poverty line and nonnegative treasury")
        if not 1 <= len(self.agents) <= 7:
            raise ValueError("audit supports rosters of one to seven agents")
        names = [a.name for a in self.agents]
        if any(not isinstance(name, str) or not name.strip() for name in names):
            raise ValueError("agent names must be nonempty strings")
        if len(set(names)) != len(names):
            raise ValueError("agent names must be unique")
        for agent in self.agents:
            if type(agent.active) is not bool or type(agent.tenure) is not int or agent.tenure < 0:
                raise ValueError("expected a Boolean active flag and a nonnegative integer tenure")
            if type(agent.catch_cap) not in (int, float) or not isfinite(agent.catch_cap):
                raise ValueError("agent catch caps must be finite numbers")
        if not any(a.active for a in self.agents):
            raise ValueError("at least one agent must be active")


def evaluate(policy: str, snapshot: Snapshot, roster: tuple[Agent, ...]) -> Distribution:
    """Compute the exact outcome law conditional on this roster."""
    if policy in LOTTERIES:
        eligible = sorted(a.name for a in roster if a.active)
        count = LOTTERIES[policy]
        if count >= len(eligible):
            raise ValueError("lottery control must leave at least one eligible agent")
        outcomes = list(combinations(eligible, count))
        return {outcome: Fraction(1, len(outcomes)) for outcome in outcomes}

    world = SimpleNamespace(
        stock=snapshot.stock,
        capacity=snapshot.capacity,
        poverty_line=snapshot.poverty_line,
        treasury=snapshot.treasury,
        agents=[SimpleNamespace(name=a.name, rounds_active=a.tenure, active=a.active,
                                catch_cap=a.catch_cap) for a in roster],
    )
    result = IMPLEMENTATIONS[policy](world)
    removed = tuple(sorted(a.name for before, a in zip(roster, result.agents, strict=True)
                           if before.active and not a.active))
    return {removed: Fraction(1)}


def encode(distribution: Distribution) -> list[dict]:
    return [{"removed": list(outcome), "probability": str(probability)}
            for outcome, probability in sorted(distribution.items())]


def describe(distribution: Distribution) -> dict:
    return {
        "outcomes": encode(distribution),
        "removal_possible": any(distribution),
        "removal_counts": sorted({len(outcome) for outcome in distribution}),
    }


def reorder(policy: str, snapshot: Snapshot) -> dict:
    """Compare conditional distributions, preserving every field per agent."""
    roster = snapshot.agents
    baseline = evaluate(policy, snapshot, roster)
    affected_sets = set()
    seen_distributions = set()
    changed = 0
    witness = None
    rows = []
    for order in permutations(roster):
        distribution = evaluate(policy, snapshot, order)
        names = [a.name for a in order]
        rows.append({"roster": names, "outcomes": encode(distribution)})
        affected_sets.update(distribution)
        seen_distributions.add(tuple(sorted(distribution.items())))
        if distribution != baseline:
            changed += 1
            swaps = sum(x != y for x, y in zip(roster, order, strict=True))
            if witness is None or swaps < witness["changed_positions"]:
                witness = {"roster": names, "changed_positions": swaps,
                           "outcomes": encode(distribution)}
    possible = set().union(*affected_sets)
    always = set.intersection(*(set(outcome) for outcome in affected_sets))
    return {
        "order_sensitive": changed > 0,
        "orders_tested": len(rows),
        "orders_differing_from_baseline": changed,
        "distinct_conditional_distributions": len(seen_distributions),
        "removal_counts": sorted({len(outcome) for outcome in affected_sets}),
        "always_removed": sorted(always),
        "possibly_removed": sorted(possible),
        "baseline_roster": [a.name for a in roster],
        "baseline": describe(baseline),
        "witness": witness,
        "orders": rows,
    }
