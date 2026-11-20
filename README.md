# GovSim rule preview audit

This repository contains the manuscript, standalone Python audit, and exact run outputs. The supplementary archive contains the audit code and results. The manuscript discloses the use of ChatGPT.

## Reproduce the experiments

Run from this directory with uv and Python 3.12 available:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked python -m govsim_audit run --out reproduced
uv run --locked python -m govsim_audit.reachability reproduced/reachability.json
```

There are no third-party dependencies or model calls. Use a fresh output directory. With versions available locally, add `--offline` after `uv sync` and `uv run`. `results/audit.json` contains the original preview, the preview-state roster sweep, the trigger-state sweep, and exact lottery controls for all ten fixtures. `results/reachability.json` contains the equal-harvest witness and every result from the 32-profile final-harvest sweep. `results/environment.json` records the verification environment.

The pinned source is Rehm, arXiv:2609.22600v2, 7 October 2026. The two enacted rule listings are from Appendices D.5 and I.1. The order and name controls are printed in Appendix I. The stock recurrence and capacity bounds are in Equation (1) and Appendix A.1. The capacity path is a constructed schedule consistent with those bounds. All five agents meet subsistence throughout the constructed prefix. The replay stops before harvest at the activating state. Historical rosters, vote conditions, protocol-specific interactions, and downstream survival remain unverified.

For a historical snapshot, adapt `examples/deferred_tie.json` and use `uv run --locked python -m govsim_audit replay SNAPSHOT.json`. The example itself is constructed.

Build the manuscript with `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` on a complete TeX Live installation with the AAAI-27 kit dependencies. The supplementary archive does not include the manuscript source or template.
