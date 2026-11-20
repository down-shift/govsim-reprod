"""Compare a single preview with two exhaustive roster checks."""
from dataclasses import asdict, dataclass, replace
from fractions import Fraction

from .core import Agent, Snapshot, describe, evaluate, reorder

SOURCE = "https://arxiv.org/pdf/2609.22600v2"


@dataclass(frozen=True)
class Case:
    name: str
    policy: str
    source: str
    order_policy: str
    preview: Snapshot
    trigger: Snapshot


def builtin_cases() -> tuple[Case, ...]:
    tied = tuple(Agent(name, 4) for name in "ABCDE")
    pair = tuple(Agent(name, tenure) for name, tenure in zip("ABCDE", (4, 4, 5, 6, 7), strict=True))
    unique = tuple(Agent(name, tenure) for name, tenure in zip("ABCDE", (3, 4, 4, 4, 4), strict=True))
    cases = []
    for policy, appendix, default_stock, crisis in (
        ("deferred_tenure", "I.1", 40, 28),
        ("named_tenure", "D.5", 21, 21),
    ):
        for profile, roster in (("all_tied", tied), ("cutoff_pair", pair), ("unique_cutoff", unique)):
            preview = Snapshot(default_stock, 56, 7, 0, roster)
            cases.append(Case(f"{policy}_{profile}", policy, f"Rehm v2 Appendix {appendix}",
                              "not_declared", preview, replace(preview, stock=crisis)))

    for policy, stock, order_policy, source in (
        ("explicit_index", 21, "declared_for_control", "Rehm v2 Appendix I positional example"),
        ("explicit_name", 28, "not_declared", "Rehm v2 Appendix I name-sorted example"),
        ("uniform_remove_one", 28, "not_declared", "Artificial uniform lottery over all active members"),
        ("uniform_remove_four", 21, "not_declared", "Artificial uniform lottery over all active members"),
    ):
        snapshot = Snapshot(stock, 56, 7, 0, tied)
        cases.append(Case(policy, policy, source, order_policy, snapshot, snapshot))
    return tuple(cases)


def compare(case: Case) -> dict:
    first = describe(evaluate(case.policy, case.preview, case.preview.agents))
    preview = reorder(case.policy, case.preview)
    trigger = preview if case.preview == case.trigger else reorder(case.policy, case.trigger)
    return {
        "case": case.name,
        "policy": case.policy,
        "rule_source": case.source,
        "snapshot_kind": "constructed",
        "roster_order_as_policy_input": case.order_policy,
        "preview_input": asdict(case.preview),
        "trigger_input": asdict(case.trigger),
        "single_preview": first,
        "reorder_at_preview": preview,
        "reorder_at_trigger": trigger,
        "order_sensitivity_hidden_at_preview": not preview["order_sensitive"] and trigger["order_sensitive"],
        "order_dependence_for_review": (
            trigger["order_sensitive"] and case.order_policy == "not_declared"
        ),
    }


def lottery_comparisons(results: list[dict]) -> dict:
    """Distinguish averaging over rosters from evaluating a fixed roster."""
    by_name = {result["case"]: result for result in results}
    checks = {}
    for policy, lottery in (
        ("deferred_tenure", "uniform_remove_one"), ("named_tenure", "uniform_remove_four")
    ):
        trigger = by_name[f"{policy}_all_tied"]["reorder_at_trigger"]
        reference = by_name[lottery]["single_preview"]["outcomes"]
        marginal = {}
        for order in trigger["orders"]:
            for result in order["outcomes"]:
                key = tuple(result["removed"])
                marginal[key] = marginal.get(key, Fraction(0)) + (
                    Fraction(result["probability"]) / trigger["orders_tested"]
                )
        expected = {tuple(row["removed"]): Fraction(row["probability"]) for row in reference}
        checks[policy] = {
            "lottery_control": lottery,
            "uniform_roster_average_matches": marginal == expected,
            "fixed_roster_matches": trigger["baseline"]["outcomes"] == reference,
        }
    return checks


def report(results: list[dict]) -> str:
    rows = [
        "# GovSim preview audit", "",
        "All inputs are constructed. Counts below describe exact roster enumeration.",
        "Baseline means the ordinary preview for the original roster.",
        "“Order effect” means the distribution over removed identities changes.", "",
        "| Case | Baseline removal possible | Order effect at preview | Order effect at trigger | Trigger orders differing from original |",
        "|---|---|---|---|---:|",
    ]
    for result in results:
        preview = result["reorder_at_preview"]
        trigger = result["reorder_at_trigger"]
        yes_no = ["yes" if x else "no" for x in (
            result["single_preview"]["removal_possible"],
            preview["order_sensitive"], trigger["order_sensitive"],
        )]
        count = f"{trigger['orders_differing_from_baseline']}/{trigger['orders_tested']}"
        rows.append(f"| {result['case']} | {' | '.join(yes_no)} | {count} |")
    rows += [
        "", "An order effect is expected when positional priority is declared.",
        "The lottery rows compare exact distributions conditional on each roster.",
        "See audit.json for inputs, per-permutation outputs, and identity witnesses.",
        "",
    ]
    return "\n".join(rows)
