# Risk-calibrated sensor fusion for underground utility mapping: a simulation study

**Author:** Leon Sandler, Independent Researcher (ORCID [0009-0007-4584-808X](https://orcid.org/0009-0007-4584-808X))
**Manuscript:** *Change-Aware Reliability-Gated Sensor Fusion: Risk-Bounded Decisions Under Infrastructure Modifications and Model Uncertainty* (release 2.1.0, prepared for submission to *Reliability Engineering & System Safety*). Earlier releases accompany earlier manuscripts: *Risk-Calibrated Sensor Fusion Under Model Uncertainty: A Simulation-Based Reliability Framework for Underground Utility Mapping* (version 1.3.0, prepared for submission to *Reliability Engineering & System Safety*; versions 1.0.0 to 1.2.0 were prepared for *Tunnelling and Underground Space Technology*). Title of versions 1.0.0 to 1.2.0: *Risk-Calibrated Sensor Fusion for Underground Utility Mapping: A Simulation-Based Decision-Support Framework for Excavation Safety*

**Everything here is a simulation under stated assumptions. No field data are used and no result is a measurement.** The parameters in `CFG` and `A4` (also written to the results files) are an assumptions register to be calibrated against ground truth.

A decision layer sits above ground-penetrating radar (GPR, 250 and 600 MHz), an electromagnetic (EM) locator and a known anchor (manhole, chamber). A Bayesian filter carries the probability that a utility lies on the tracked alignment along a corridor of 5 m segments (and, in version 1.1, across a lateral grid), and each segment is reported as **present**, **absent** or **unverified**; unverified marks soil–utility–depth combinations whose expected detection probability is below 0.3, segments whose needed sensor has failed, and corridors where an on-site reference check fails, so that sensor silence is never reported as clearance.

## Version history

* **v1.0.0** — `SubSurface_MC.py`: baselines, ablations, stress tests, calibration, a clearance trial, 27 self-tests.
* **v1.1.0** — `SubSurface_v4.py` (v1.0 results unchanged): lateral tracking, sensor-health-aware fusion, depth-resolved capability zones, unseen soils with an on-site reference check, cluster-bootstrap intervals, six models in sixteen scenarios, clearance at **equal** released coverage / risk / cost, value-of-information pit allocation, five-year cost of ownership, exact pilot sample sizes; 13 further self-tests.
* **v1.2.0** — reviewer revision: structural-mismatch experiment (truth geometry from piecewise-linear paths with abrupt bends, a parallel utility and a branch; `geometry_mismatch`), a parameter-uncertainty envelope (`parameter_envelope`), an external plausibility check of the attenuation values (`external_plausibility`), "modelled intersections" instead of "strikes", main-text figures reduced to ten (the rest in the supplement), a comparison table with the closest existing approaches; 14 self-tests in `SubSurface_v4.py`.
  **Findings that cut against the framework:** with a parallel utility the lateral tracker trades false alarms for false clearance (14.8 % vs 1.8 % for a one-pass filter); over the parameter envelope the median false clearance is 11.4 % (5th–95th percentile 1.5–31.0 %). No published detection-versus-depth dataset was reproduced; the model is a methodological demonstration.
  **Correction (v1.1):** version 1.0.0 (and the first Zenodo preprint) compared a binary map with a three-state rule at *different* released coverages and reported about four times fewer strikes; that was an operating-point confound and is withdrawn. At equal coverage the gain over per-segment fusion is modest (see `results_v4/results_v4.json`, `equal_coverage`).

* **v1.3.0** — reliability retarget (`SubSurface_v5.py`; v1.0 and v1.1/1.2 results unchanged; 17 self-tests; `results_v5/`): the safety failure event F = {released, utility in the excavation envelope} with P(F) = P(U|A) P(A); six release policies (fixed, sensor-quality-adjusted, expected-loss, robust over a parameter set, robust over parameters and structure, robust expected-loss) against calibrated-abstention, health-aware and oracle baselines; reliability-coverage curves with paired dominance analysis; fault scenarios and a common-cause case with attribution of unsafe releases to the branches of a failure tree; aleatory/epistemic variance decomposition over a parameter envelope and five structural models (not weighted); ablation at equal released coverage; value-of-information pit prioritisation; global sensitivity analysis (Latin hypercube, surrogate, Sobol indices, bootstrap rank stability).
  **Findings that cut against the framework:** the sensor-quality-adjusted policy with a parallel utility and a branch releases 65 % of the corridor at 18 % conditional risk while its own probabilities predict 0.3 %; a policy that is robust over an explicit uncertainty set holds 0.3 % at 36 % coverage but cannot protect against an unflagged sensor failure (about 65 % for every policy); at equal released coverage no policy dominates; some ablations lower the risk when a component is removed (reported, unexplained). The reliability figures are conditional on the simulated environment; no field validation exists.

* **v1.3.1** — manuscript revision only (no code or result change): copy-edit pass with American spelling, abstract and highlights state the released coverage at which policies are compared, the Sobol estimation from the surrogate is documented, title-page submission sentence removed. `manuscript/*_RESS.docx` are built by the `*_ress.py` builders (the builders produce the text before the copy-editing pass of the journal-preparation service; the committed documents are the submitted versions).

* **v2.0.0** — change-aware extension (`SubSurface_v6.py`, 12 self-tests, `results_v6/`; all earlier code and results unchanged): a dynamic hazard estimator (hidden Markov, per element) fed by asynchronous point sensors, periodic surveys and work records; work-permit reconciliation (no records, permit suppression, permit as context) with change attribution; a reliability gate over model alternatives with survey-likelihood validity selection; risk-constrained sensor placement; and two domains (underground utilities, whose survey capability comes from `SubSurface_MC.py`, and a synthetic industrial scaffold). Experiments E1-E7: static versus dynamic at matched coverage, observation staleness, permit reconciliation, hybrid sensing, placement, cross-domain transfer, combined failures, ablation.
* **v2.1.0** — corrections and one added experiment after a submission-readiness review (`SubSurface_v6.py`, 14 self-tests; every earlier number is unchanged): (i) E8, the sensitivity of the scaffold conclusions to the definition of an unsafe structure (critical-member share 5/10/20/35% x bay threshold 1-4, 16 definitions, nominal and combined failures; `results_v6/results_v6.json` key `structure_definitions`, figure 39, Supplementary Table S17); (ii) the number of released decisions behind every conditional risk (`release`, `unsafe`, `risk_defined`), so that a small coverage is not mistaken for none; (iii) manuscript: unresolved calculation placeholders in Section 8.1 replaced by numbers, coverage below 1% shown to one decimal, Section 4.4 states that the gate bounds a modeled, assumption-conditional hazard probability and not a real failure probability.
  **Findings that cut against the framework:** continuous point sensors on 5-20 % of the elements add little to periodic surveys; risk-optimised placement is not consistently better than simple rules (uncertainty-based placement is best in the scaffold domain); the reliability gate lowers risk under mismatch mainly by abstaining (at the gate's coverage the ungated estimator is about as safe in the event-rate scenarios); no method is reliable against every failure mode. The scaffold hazard criterion is synthetic and there is no field validation.

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
SubSurface_v4.py          v1.1 extensions (lateral world, health, zones, scenario matrix, clearance, VOI, TCO; 14 self-tests)
SubSurface_v5.py          v1.3 reliability analyses (policies, reliability-coverage curves, decomposition, fault scenarios, ablation, sensitivity; 17 self-tests)
SubSurface_v6.py          v2.1 change-aware monitoring (dynamic estimator, permits, gate, placement, two domains, structure-definition sensitivity; 14 self-tests)
figure_generation.py      figures 1-12 from results/results.json
figure_generation_v4.py   figures 8 (equal coverage), 13-21 from results_v4/results_v4.json
figure_generation_v5.py   figures 22-30 from results_v5/results_v5.json
figure_generation_v6.py   figures 31-38 from results_v6/results_v6.json
tests/test_subsurface.py  runs the self-tests and a few invariants
results/, results_v4/, results_v5/, results_v6/   config, results JSON, manifest.json (SHA-256), figures/
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
python SubSurface_v5.py --demo                 # 17 self-tests of the reliability analyses
python SubSurface_v5.py --reproduce --out results_v5 --seed 42 --workers 8          # about 40 minutes on 8 processes
python figure_generation_v5.py --results results_v5/results_v5.json --out results_v5/figures
python SubSurface_v6.py --demo                 # 14 self-tests of the change-aware layer
python SubSurface_v6.py --reproduce --out results_v6 --seed 42                     # about 14 minutes, one process
python figure_generation_v6.py --results results_v6/results_v6.json --out results_v6/figures
python tests/test_subsurface.py
```

`--quick` runs small versions for a smoke test. Results are deterministic for a given seed, Python and library versions (Python 3.11.9, NumPy 2.4.6, SciPy 1.17.1, Matplotlib 3.11.1, scikit-learn 1.9.1); the results of SubSurface_v5.py do not depend on the number of worker processes.

## What the self-tests check

v1.0: closed-form detection probabilities (single band, correlated dual band, EM with coupling) against Monte Carlo; the Markov truth process against analytic values; the filter against a cumulative likelihood ratio; the position-error formulae against sampling; bookkeeping; determinism; the grid size.
v1.3: metric identities against the v4 definitions, the quality-adjusted rule against the v4 rule, expected-loss thresholds, reliability-coverage curves, calibrated-abstention levels, the variance decomposition on a nested design with known components, Latin hypercube stratification, the Sobol estimator on the Ishigami function, reproducibility of a simulated network, the supremum over the uncertainty set, the reference check against the true world.
v1.1: the lateral transition matrix; bounds of the lateral filter; exact neutrality of a sensor flagged as failed; the posterior under a persistent detection; zone thresholds; monotone capability in depth; the bootstrap; equal-coverage ranking; the sign of the value of information; exact binomial sample sizes; the reference check's false-flag rate; determinism.
They check the code against its own mathematics. They are not validation against reality.

## Metric definitions

Per corridor, 100 segments, each truly on the tracked alignment (within 1 m of it) or not. *Sensitivity* = present calls among truly present decided segments; *false clearance* = truly present among released (called absent) segments; *false-alarm rate* = present calls among truly empty segments; *unverified share* = segments with no call. In the v1.0 tables: accuracy, miss rate and false-alarm rate in three views (sensor-visible cells, all cells with blind cells forced to a call, sensor-blind cells). Intervals in v1.1 are 95 % percentile intervals of a cluster bootstrap over corridors, stratified by soil-by-utility cell.

## Use of generative AI

The code, figures and text were drafted with Claude (Anthropic; Claude Sonnet 5.5, through Claude Code) working with the author; the outputs were produced by running the code with a fixed seed. See the manuscript's declaration.

## Licence

MIT (code) — see `LICENSE`. The manuscript preprint on Zenodo is CC BY 4.0.
