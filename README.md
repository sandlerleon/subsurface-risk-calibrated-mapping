# Risk-calibrated sensor fusion for underground utility mapping: a simulation study

**Author:** Leon Sandler, Independent Researcher (ORCID [0009-0007-4584-808X](https://orcid.org/0009-0007-4584-808X))
**Manuscript:** *Risk-Calibrated Sensor Fusion for Underground Utility Mapping: A Simulation-Based Decision-Support Framework for Excavation Safety* (prepared for submission to *Tunnelling and Underground Space Technology*)

**Everything here is a simulation under stated assumptions. No field data are used and no result is a measurement.** The parameters in `CFG` and `A4` (also written to the results files) are an assumptions register to be calibrated against ground truth.

A decision layer sits above ground-penetrating radar (GPR, 250 and 600 MHz), an electromagnetic (EM) locator and a known anchor (manhole, chamber). A Bayesian filter carries the probability that a utility lies on the tracked alignment along a corridor of 5 m segments (and, in version 1.1, across a lateral grid), and each segment is reported as **present**, **absent** or **unverified**; unverified marks soil–utility–depth combinations whose expected detection probability is below 0.3, segments whose needed sensor has failed, and corridors where an on-site reference check fails, so that sensor silence is never reported as clearance.

## Version history

* **v1.0.0** — `SubSurface_MC.py`: baselines, ablations, stress tests, calibration, a clearance trial, 27 self-tests.
* **v1.1.0** — `SubSurface_v4.py` (v1.0 results unchanged): lateral tracking, sensor-health-aware fusion, depth-resolved capability zones, unseen soils with an on-site reference check, cluster-bootstrap intervals, six models in sixteen scenarios, clearance at **equal** released coverage / risk / cost, value-of-information pit allocation, five-year cost of ownership, exact pilot sample sizes; 13 further self-tests.
* **v1.2.0** — reviewer revision: structural-mismatch experiment (truth geometry from piecewise-linear paths with abrupt bends, a parallel utility and a branch; `geometry_mismatch`), a parameter-uncertainty envelope (`parameter_envelope`), an external plausibility check of the attenuation values (`external_plausibility`), "modelled intersections" instead of "strikes", main-text figures reduced to ten (the rest in the supplement), a comparison table with the closest existing approaches; 14 self-tests in `SubSurface_v4.py`.
  **Findings that cut against the framework:** with a parallel utility the lateral tracker trades false alarms for false clearance (14.8 % vs 1.8 % for a one-pass filter); over the parameter envelope the median false clearance is 11.4 % (5th–95th percentile 1.5–31.0 %). No published detection-versus-depth dataset was reproduced; the model is a methodological demonstration.
  **Correction (v1.1):** version 1.0.0 (and the first Zenodo preprint) compared a binary map with a three-state rule at *different* released coverages and reported about four times fewer strikes; that was an operating-point confound and is withdrawn. At equal coverage the gain over per-segment fusion is modest (see `results_v4/results_v4.json`, `equal_coverage`).

## Headline results (see the manuscript and results files for definitions, intervals and limitations)

| Result | Value |
|---|---|
| Sensor-visible cells (84% of the weighted network): accuracy / miss / false alarm, anchored filter | 98.3 / 2.4 / 0.3 % (EM-only proxy: 53.5 % accuracy) |
| Share of the assumed network that is sensor-blind (reported unverified) | 16 % |
| Lateral shifts, false-alarm rate at 2 shifts per 100 m | 2.3 % with three parallel passes; 6.7 % for one pass (v1.0 filter) |
| Mixed sensor health, imperfect diagnostic: false clearance | 18.9 % (v1.0 filter) → 3.5 % |
| GPR failed and **not** flagged: false clearance | about 65 % for every model |
| Unseen soils, with the reference check: false clearance | 8.7 % (31.9 % without the check) |
| Equal risk (at most 1 % of released segments occupied): releasable corridor | 27.1 % (anchored filter) vs 24.7 % (per-segment fusion) |

## Layout

```
SubSurface_MC.py          v1.0 simulation (model, filter, metrics, experiments, 27 self-tests)
SubSurface_v4.py          v1.1 extensions (lateral world, health, zones, scenario matrix, clearance, VOI, TCO; 13 self-tests)
figure_generation.py      figures 1-12 from results/results.json
figure_generation_v4.py   figures 8 (equal coverage), 13-21 from results_v4/results_v4.json
tests/test_subsurface.py  runs the self-tests and a few invariants
results/, results_v4/     config, results JSON, manifest.json (SHA-256), figures/
refs/                     reference harvest from Crossref (every cited DOI was checked)
manuscript/               builders (read the results files); the manuscript, supplement, cover letter and highlights (docx only)
tools/                    manifest and Zenodo scripts (the token is read from ZENODO_TOKEN and never stored)
```

## Reproducing

```bash
pip install -r requirements.txt
python SubSurface_MC.py --demo                 # 27 self-tests
python SubSurface_MC.py --reproduce --out results --n 500 --blocks 10 --seed 42     # about 2 minutes
python figure_generation.py --results results/results.json --out results/figures
python SubSurface_v4.py --demo                 # 14 self-tests of the v1.1/v1.2 code
python SubSurface_v4.py --reproduce --out results_v4 --seed 42                     # about 12 minutes
python figure_generation_v4.py --results results_v4/results_v4.json --out results_v4/figures
python tests/test_subsurface.py
```

`--quick` runs small versions for a smoke test. Results are deterministic for a given seed, Python and library versions (Python 3.11.9, NumPy 2.4.6, SciPy 1.17.1, Matplotlib 3.11.1).

## What the self-tests check

v1.0: closed-form detection probabilities (single band, correlated dual band, EM with coupling) against Monte Carlo; the Markov truth process against analytic values; the filter against a cumulative likelihood ratio; the position-error formulae against sampling; bookkeeping; determinism; the grid size.
v1.1: the lateral transition matrix; bounds of the lateral filter; exact neutrality of a sensor flagged as failed; the posterior under a persistent detection; zone thresholds; monotone capability in depth; the bootstrap; equal-coverage ranking; the sign of the value of information; exact binomial sample sizes; the reference check's false-flag rate; determinism.
They check the code against its own mathematics. They are not validation against reality.

## Metric definitions

Per corridor, 100 segments, each truly on the tracked alignment (within 1 m of it) or not. *Sensitivity* = present calls among truly present decided segments; *false clearance* = truly present among released (called absent) segments; *false-alarm rate* = present calls among truly empty segments; *unverified share* = segments with no call. In the v1.0 tables: accuracy, miss rate and false-alarm rate in three views (sensor-visible cells, all cells with blind cells forced to a call, sensor-blind cells). Intervals in v1.1 are 95 % percentile intervals of a cluster bootstrap over corridors, stratified by soil-by-utility cell.

## Use of generative AI

The code, figures and text were drafted with Claude (Anthropic; Claude Sonnet 5.5, through Claude Code) working with the author; the outputs were produced by running the code with a fixed seed. See the manuscript's declaration.

## Licence

MIT (code) — see `LICENSE`. The manuscript preprint on Zenodo is CC BY 4.0.
