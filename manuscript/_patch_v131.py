# -*- coding: utf-8 -*-
"""One-off edits for release v1.3.1 / preprint v5 (copy-editing review and submission-readiness feedback)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))


def edit(fn, pairs):
    p = os.path.join(HERE, fn)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert old in s, (fn, old[:80])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8").write(s)


# ---- common_ress: v1.3.1 / preprint v5
edit("common_ress.py", [
    ('SW = (K.ZEN.get("software_1.3.0") or K.ZEN["software_1.2.0"])["doi"]', 'SW = (K.ZEN.get("software_1.3.1") or K.ZEN.get("software_1.3.0") or K.ZEN["software_1.2.0"])["doi"]'),
    ('PP = (K.ZEN.get("publication_v4") or K.ZEN["publication_v3"])["doi"]', 'PP = (K.ZEN.get("publication_v5") or K.ZEN.get("publication_v4") or K.ZEN["publication_v3"])["doi"]'),
    ('SW_V12, PP_V3 = K.ZEN["software_1.2.0"]["doi"], K.ZEN["publication_v3"]["doi"]', 'SW_V12, PP_V3 = K.ZEN["software_1.2.0"]["doi"], K.ZEN["publication_v3"]["doi"]\nSW_V13, PP_V4 = K.ZEN["software_1.3.0"]["doi"], K.ZEN["publication_v4"]["doi"]'),
    ('RELEASE = "v1.3.0"', 'RELEASE = "v1.3.1"'),
])

# ---- abstract: state the coverage at which the comparison is made, and that the gain is a more conservative release decision
edit("ress_numbers.py", [
    ('"Underground utility mapping is a representative case: releasing a segment for mechanical excavation while a utility lies within its envelope is a well-defined safety failure. "',
     '"In underground utility mapping, releasing a segment for excavation while a utility lies within its envelope is a well-defined safety failure. "'),
    ('"In the matched model the sensor-quality-adjusted policy releases %s%% of the corridor at %s%% conditional risk. With a parallel utility and a branch the same policy reaches %s%% risk at %s%% coverage, while a robust policy that releases only if an upper bound over a stated uncertainty set is acceptable holds %s%% at %s%% coverage. "',
     '"In the matched model the sensor-quality-adjusted policy releases %s%% of the corridor at %s%% conditional risk. With a parallel utility and a branch it reaches %s%% risk at %s%% coverage, whereas a robust policy that releases only if an upper bound over a stated uncertainty set is acceptable holds %s%% at %s%% coverage: the gain comes from a more conservative release decision, not from a better probability model. "'),
    ('"Safety-critical decisions often rest on incomplete, heterogeneous and possibly faulty sensor evidence, so a decision-support system must itself be assessed as a system that can fail. "',
     '"Safety-critical decisions often rest on incomplete, heterogeneous and possibly faulty sensor evidence, so decision support must itself be assessed as a system that can fail. "'),
    ('"Added spatial-model complexity improves reliability in the matched model and reduces it under structural mismatch, which motivates conservative abstention and independent verification. "',
     '"Added spatial-model complexity improves reliability in the matched model but reduces it under structural mismatch, which motivates conservative abstention and independent verification. "'),
    ('"Robust abstention cut false clearance from %s%% to %s%% under parallel utilities." % (_c("G4_parallel_branch", "P2_quality", d=0), _c("G4_parallel_branch", "P5_robust_theta_struct")),',
     '"Robust abstention lowers simulated risk at the cost of released coverage.",'),
])

# ---- title page: remove the submission sentence
edit("ress_partA.py", [
    ('P("Manuscript prepared for submission to *Reliability Engineering & System Safety* (research article). Software: %s (archived at https://doi.org/%s). Preprint: https://doi.org/%s." % (REPO, SW, PP), align="center", size=9.5, space_after=14)',
     'P("Software: %s (archived at https://doi.org/%s). Preprint: https://doi.org/%s." % (REPO, SW, PP), align="center", size=9.5, space_after=14)'),
    # 95%% in a plain (non-formatted) string
    ('intervals are 95%% percentile intervals of 300 cluster-bootstrap resamples', 'intervals are 95% percentile intervals of 300 cluster-bootstrap resamples'),
    ('and curves are averaged over networks with 95%% t-intervals over the 10 independent networks', 'and curves are averaged over networks with 95% t-intervals over the 10 independent networks'),
    # Sobol methodology
    ('A gradient-boosting surrogate is fitted to the unsafe-release probability and the conditional risk of each policy; first-order and total-order Sobol indices are estimated on the surrogate (Saltelli et al., 2010; Jansen, 1999; Sobol, 2001) and their stability is checked by refitting on 60 bootstrap resamples of the design points. ',
     'A gradient-boosting surrogate (300 trees of depth 3, fitted to the 320 design points; hold-out R\\u00b2 on a random 20% of the points) is fitted to the unsafe-release probability and the conditional risk of each policy. The Sobol indices are not computed from the Latin hypercube points themselves: they are estimated by Monte Carlo on the fitted surrogate, using an independent random design in the unit hypercube of the (transformed) parameters, with two independent matrices A and B of 4,096 samples each and, for each parameter, a matrix AB that takes that parameter from B and the others from A; the first-order index uses the estimator of Saltelli et al. (2010) and the total-order index that of Jansen (1999) (see also Sobol, 2001). '
     'Their stability is checked by refitting the surrogate on 60 bootstrap resamples of the design points and re-estimating the indices, which also gives the intervals and the share of refits in which each parameter is ranked first. '),
])
edit("ress_partB3.py", [
    ('"A fresh clone of the release was run and its results files compared with the archived ones (see the repository README). results_v5.json records',
     '"A fresh clone of the archived code (release v1.3.0, whose code is unchanged in v1.3.1) was run, reproducing results_v5.json exactly with six worker processes against the eight used for the archived results, and its self-tests and tests passed. results_v5.json records'),
    ('Version 4 (this version) reframes the study as a reliability analysis:', 'Version 4 (https://doi.org/" + PP_V4 + ") reframes the study as a reliability analysis:'),
    ('Numbers of earlier versions that are quoted here are unchanged.", align="justify")\nP("**Data and code availability.**',
     'Version 5 (this version) revises the wording after a copy-editing review, states the released coverage at which policies are compared in the abstract and highlights, and documents how the sensitivity indices were estimated; no result has changed. Numbers of earlier versions that are quoted here are unchanged.", align="justify")\nP("**Data and code availability.**'),
])
print("patched")
