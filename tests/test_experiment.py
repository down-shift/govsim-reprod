"""Check conclusions against independently specified identity outcomes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from govsim_audit.experiment import builtin_cases, compare, lottery_comparisons

ROOT = Path(__file__).resolve().parents[1]


class ExperimentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = [compare(case) for case in builtin_cases()]
        cls.cases = {result["case"]: result for result in cls.results}

    def test_deferred_rule_only_detected_at_trigger(self):
        case = self.cases["deferred_tenure_all_tied"]
        self.assertEqual(case["single_preview"]["outcomes"],
                         [{"removed": [], "probability": "1"}])
        self.assertFalse(case["reorder_at_preview"]["order_sensitive"])
        trigger = case["reorder_at_trigger"]
        self.assertEqual(trigger["orders_differing_from_baseline"], 96)
        self.assertEqual(trigger["always_removed"], [])
        self.assertEqual(trigger["possibly_removed"], list("ABCDE"))
        self.assertEqual(trigger["witness"]["changed_positions"], 2)

    def test_named_rule_partial_tie_has_three_unavoidable_removals(self):
        case = self.cases["named_tenure_cutoff_pair"]
        preview = case["reorder_at_preview"]
        self.assertEqual(preview["always_removed"], list("CDE"))
        self.assertEqual(preview["orders_differing_from_baseline"], 60)
        outcomes = {tuple(row["outcomes"][0]["removed"]) for row in preview["orders"]}
        self.assertEqual(outcomes, {tuple("BCDE"), tuple("ACDE")})
        for prefix in ("deferred", "named"):
            unique = self.cases[f"{prefix}_tenure_unique_cutoff"]["reorder_at_trigger"]
            self.assertFalse(unique["order_sensitive"])

    def test_declared_position_and_uniform_lottery_controls(self):
        case = self.cases["explicit_index"]
        self.assertTrue(case["reorder_at_trigger"]["order_sensitive"])
        self.assertFalse(case["order_dependence_for_review"])
        self.assertFalse(self.cases["explicit_name"]["reorder_at_trigger"]["order_sensitive"])
        for count in ("one", "four"):
            lottery = self.cases[f"uniform_remove_{count}"]["reorder_at_trigger"]
            self.assertEqual(lottery["distinct_conditional_distributions"], 1)
            self.assertEqual(len(lottery["baseline"]["outcomes"]), 5)
        for result in lottery_comparisons(self.results).values():
            self.assertTrue(result["uniform_roster_average_matches"])
            self.assertFalse(result["fixed_roster_matches"])

    def test_recorded_replay_rejects_baseline_mismatch(self):
        data = json.loads((ROOT / "examples/deferred_tie.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            snapshot = Path(temp) / "snapshot.json"
            for observed, expected_exit in ((["A"], 0), (["B"], 1)):
                data["observed_removed"] = observed
                snapshot.write_text(json.dumps(data))
                result = subprocess.run(
                    [sys.executable, "-m", "govsim_audit", "replay", str(snapshot)],
                    cwd=ROOT, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, expected_exit, result.stderr)
                self.assertEqual(json.loads(result.stdout)["baseline_matches"], expected_exit == 0)
