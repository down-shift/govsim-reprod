# GovSim preview audit

All inputs are constructed. Counts below describe exact roster enumeration.
Baseline means the ordinary preview for the original roster.
“Order effect” means the distribution over removed identities changes.

| Case | Baseline removal possible | Order effect at preview | Order effect at trigger | Trigger orders differing from original |
|---|---|---|---|---:|
| deferred_tenure_all_tied | no | no | yes | 96/120 |
| deferred_tenure_cutoff_pair | no | no | yes | 60/120 |
| deferred_tenure_unique_cutoff | no | no | no | 0/120 |
| named_tenure_all_tied | yes | yes | yes | 96/120 |
| named_tenure_cutoff_pair | yes | yes | yes | 60/120 |
| named_tenure_unique_cutoff | yes | no | no | 0/120 |
| explicit_index | yes | yes | yes | 108/120 |
| explicit_name | yes | no | no | 0/120 |
| uniform_remove_one | yes | no | no | 0/120 |
| uniform_remove_four | yes | no | no | 0/120 |

An order effect is expected when positional priority is declared.
The lottery rows compare exact distributions conditional on each roster.
See audit.json for inputs, per-permutation outputs, and identity witnesses.
