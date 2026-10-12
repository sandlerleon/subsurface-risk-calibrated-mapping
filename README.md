# Risk-calibrated sensor fusion for underground utility mapping: a simulation study

**Author:** Leon Sandler, Independent Researcher (ORCID [0009-0007-4584-808X](https://orcid.org/0009-0007-4584-808X))
**Manuscript:** *Risk-Calibrated Sensor Fusion for Underground Utility Mapping: A Simulation-Based Decision-Support Framework for Excavation Safety* (submitted to *Tunnelling and Underground Space Technology*)

**Everything here is a simulation under stated assumptions. No field data are used and no result is a measurement.** The parameters in `CFG` (also written to `results/config.json`) are an assumptions register to be calibrated against ground truth.

A decision layer sits above ground-penetrating radar (GPR, 250 and 600 MHz), an electromagnetic (EM) locator and a known anchor (manhole, chamber). A Bayesian filter carries the probability that a utility lies on the tracked alignment along a corridor of 5 m segments, and each segment is reported as **present**, **absent** or **unverified**; unverified marks soil–utility–depth combinations whose expected detection probability is below 0.3, so that sensor silence is never reported as clearance. A seeded Monte Carlo study compares baselines and ablations, stress cases, probability calibration and an excavation-clearance trial, and keeps four outcomes apart: detection, calibration, location/depth accuracy and the share left unverified.

## Headline results (mean over 10 blocks of 17,500 corridors; 100 segments each)

| View (denominator) | Method | Accuracy | Miss | False alarm |
|---|---|---|---|---|
| Sensor-visible cells (84% of the weighted network) | EM locator only (proxy) | 53.5 | 70.2 | 1.0 |
| | GPR + EM, per segment | 97.8 | 3.0 | 0.7 |
| | **Framework (anchored filter)** | **98.3** | **2.4** | **0.3** |
| All cells, blind forced to binary | Framework | 93.4 | 6.7 | 6.3 |

16% of the assumed network is sensor-blind (plastic and concrete sewers in loam, clay and fill) and is reported as unverified. Expected calibration error 0.030. In the clearance trial the three-state rule gives about 4.5 times fewer strikes per kilometre than a binary map for 7 percentage points less corridor released. Failure modes: lateral shifts of utilities, an anchor that is certain but wrong, GPR failure, uncertain depth. See the manuscript for all tables, intervals, definitions and limitations; `results/results.json` holds every number.

## Layout

```
SubSurface_MC.py          the whole simulation (one file: model, filter, metrics, experiments, self-tests)
figure_generation.py      regenerates the 12 figures from results/results.json
tests/test_subsurface.py  runs the self-tests and a few invariants
results/                  config.json, results.json, manifest.json (SHA-256), figures/
refs/                     reference harvest from Crossref (every cited DOI was checked)
manuscript/              builders (read results.json) and the manuscript, cover letter and highlights (docx only)
tools/                    manifest and Zenodo scripts (the token is read from ZENODO_TOKEN and never stored)
```

## Reproducing

```bash
pip install -r requirements.txt
python SubSurface_MC.py --demo                 # 27 closed-form-versus-Monte-Carlo self-tests
python SubSurface_MC.py --grid-size            # 1,470-configuration closed-form reference grid
python SubSurface_MC.py --reproduce --out results --n 500 --blocks 10 --seed 42     # about 2 minutes
python figure_generation.py --results results/results.json --out results/figures
python tests/test_subsurface.py
```

`--quick` runs a small version for a smoke test. Results are deterministic for a given seed, Python and library versions (results.json was produced with Python 3.11.9, NumPy 2.4.6, SciPy 1.17.1, Matplotlib 3.11.1).

## What the self-tests check

Closed-form detection probabilities (single band, correlated dual band, EM with coupling) against Monte Carlo; the engine against the closed form; the Markov truth process (mean presence and persistence) against analytic values; the filter against a cumulative likelihood ratio when hazard and re-birth are zero; the position-error formulae against sampling; confusion-fraction and weight bookkeeping; determinism under a fixed seed; the grid size. They check the code against its own mathematics. They are not validation against reality.

## Metric definitions

Per corridor, 100 segments, each truly on the tracked alignment or not. Accuracy = correct calls / segments considered; miss rate = missed / truly present; false-alarm rate = false calls / truly empty; balanced accuracy = mean of (1 − miss) and (1 − false alarm). Metrics are formed from cell-level fractions weighted by assumed network share. *Sensor-visible* cells: fused detection probability at class mid-depth ≥ 0.3 (the segments on which the framework issues a call). *All cells*: sensor-blind cells forced to a binary call. *Sensor-blind* cells are labelled unverified by the framework and receive no call.

## Use of generative AI

The code, figures and text were drafted with Claude (Anthropic; Claude Sonnet 5.5, through Claude Code) working with the author; the outputs were produced by running the code with a fixed seed. See the manuscript's declaration.

## Licence

MIT (code) — see `LICENSE`. The manuscript preprint on Zenodo is CC BY 4.0.
