# -*- coding: utf-8 -*-
"""Numbers, abstract and highlights shared by the RESS builders (exec'd inside build_manuscript_ress.py and build_cover_letter_ress.py namespaces)."""
import numpy as np

_S = R5["scenario_study"]["scenarios"]
_D = R5["decomposition"]["by_policy"]
_G = R5["gsa"]["sobol"]
_GM = R4["geometry_mismatch"]["levels"]


def _c(sc, p, k="cond_risk", d=1, scale=100.0):
    v = _S[sc]["policies"][p][k][0]
    return ("%." + str(d) + "f") % (scale * v)


def _curve(sc, score, c):
    j = int(np.argmin(np.abs(W5.CGRID - c)))
    v = _S[sc]["curves"][score][0][j]
    return None if v is None else v


ES = {p: [(_D[p][m]["epistemic_share"]) for m in R5["decomposition"]["structural_models"]] for p in _D}

ABSTRACT_TEXT = (
    "Safety-critical decisions often rest on incomplete, heterogeneous and possibly faulty sensor evidence, so a decision-support system must itself be assessed as a system that can fail. "
    "Underground utility mapping is a representative case: releasing a segment for mechanical excavation while a utility lies within its envelope is a well-defined safety failure. "
    "This simulation study, which uses no field data, defines the unsafe-release probability, the conditional false-clearance risk and the release coverage, and compares fixed, sensor-quality-adjusted, expected-loss and robust release policies for ground-penetrating radar and electromagnetic evidence "
    "with calibrated-abstention, health-aware and oracle baselines. It separates aleatory variability from epistemic uncertainty over a parameter envelope and five structural models, simulates sensor-fault and common-cause combinations, and ranks failure drivers by global sensitivity analysis. "
    "In the matched model the sensor-quality-adjusted policy releases %s%% of the corridor at %s%% conditional risk. With a parallel utility and a branch the same policy reaches %s%% risk at %s%% coverage, while a robust policy that releases only if an upper bound over a stated uncertainty set is acceptable holds %s%% at %s%% coverage. "
    "An unflagged sensor failure defeats every policy (%s%%), epistemic parameter uncertainty accounts for %s to %s%% of the variance of the unsafe-release probability of the quality-adjusted policy, and at equal coverage no policy dominates. "
    "Added spatial-model complexity improves reliability in the matched model and reduces it under structural mismatch, which motivates conservative abstention and independent verification. "
    "The results are conditional on the simulated environment and have not been validated against field measurements."
) % (_c("baseline", "P2_quality", "coverage", 0), _c("baseline", "P2_quality"), _c("G4_parallel_branch", "P2_quality", d=0), _c("G4_parallel_branch", "P2_quality", "coverage", 0),
     _c("G4_parallel_branch", "P5_robust_theta_struct"), _c("G4_parallel_branch", "P5_robust_theta_struct", "coverage", 0), _c("B_gpr_failed_unflagged", "P2_quality", d=0),
     "%.0f" % (100 * min(ES["P2_quality"])), "%.0f" % (100 * max(ES["P2_quality"])))

HL = [
    "Probabilistic sensor fusion is evaluated for safety-critical utility mapping.",
    "Unsafe-clearance risk is examined under sensor and model failures.",
    "Structural mismatch can make complex spatial models less reliable.",
    "Robust abstention cut false clearance from %s%% to %s%% under parallel utilities." % (_c("G4_parallel_branch", "P2_quality", d=0), _c("G4_parallel_branch", "P5_robust_theta_struct")),
    "Abstention identifies locations requiring independent verification.",
]
for _t in HL:
    assert len(_t) <= 85, (len(_t), _t)
