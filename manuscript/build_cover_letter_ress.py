# -*- coding: utf-8 -*-
"""Cover letter and highlights for Reliability Engineering & System Safety (version 1.3).   python build_cover_letter_ress.py -> out/Cover_Letter_RESS.docx, out/Highlights_RESS.docx"""
import os
import sys

from docx.shared import Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
import docx_helpers as H  # noqa: E402
from common_ress import *  # noqa: E402,F401,F403
import SubSurface_v5 as W5  # noqa: E402

H.AUTO_MATH = False
exec(open(os.path.join(HERE, "ress_numbers.py"), encoding="utf-8").read())

os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
d = H.new_document(size=11, line=1.15)
H.para(d, "**Highlights** – " + TITLE, space_after=8)
for t in HL:
    H.bullet(d, t)
d.save(os.path.join(HERE, "out", "Highlights_RESS.docx"))

doc = H.new_document(size=11, line=1.15)


def para(text, bold=False, after=6):
    p = doc.add_paragraph()
    if bold:
        p.add_run(text).bold = True
    else:
        H.add_rich(p, text)
    p.paragraph_format.space_after = Pt(after)
    return p


for line in ("Leon Sandler", "The Conscious Machine – Independent Research, Northbrook, Illinois, USA", "sandler.leon@gmail.com", "ORCID: https://orcid.org/0009-0007-4584-808X"):
    para(line, after=0)
para("")
para("12 October 2026")
para("The Editors\nReliability Engineering & System Safety", after=10)
para("Dear Editor,")
para("Please consider our manuscript, **“%s,”** for publication as an Original Research Article in *Reliability Engineering & System Safety*." % TITLE)
para("The manuscript investigates the reliability of safety-critical decisions derived from incomplete and potentially unreliable sensor evidence. Using underground utility mapping as an engineering case study, it defines a safety failure event (a segment released for excavation although a utility lies within its envelope) "
     "and evaluates probabilistic sensor fusion, uncertainty-aware classification, sensor-health monitoring and the consequences of structural model mismatch with reliability metrics: the unsafe-release probability, the conditional false-clearance risk and the release coverage.")
para("The principal contribution is an analysis of the conditions under which probabilistic decision systems provide reliable clearance recommendations and the conditions under which their assumptions produce unsafe confidence. In particular, the simulations reveal that increased spatial-model complexity can worsen false-clearance outcomes "
     "when the assumed utility geometry is incorrect: with a parallel utility and a branch, a sensor-quality-adjusted policy releases %s%% of the corridor at %s%% conditional risk while its own probabilities predict %s%%, and a simpler one-dimensional model has %s%%. "
     "A policy that releases only if an upper bound over an explicit set of parameters and structures is acceptable holds %s%% at %s%% coverage, at the price of released coverage, and an unflagged sensor failure defeats every policy (%s%%). "
     "The study separates aleatory variability from epistemic uncertainty (epistemic parameter uncertainty accounts for %s to %s%% of the variance of the unsafe-release probability of the quality-adjusted policy), evaluates sensor-fault and common-cause combinations jointly, "
     "compares policies at equal released coverage on reliability–coverage curves against calibrated-abstention and oracle baselines, and ranks failure drivers by global sensitivity analysis." % (
         _c("G4_parallel_branch", "P2_quality", "coverage", 0), _c("G4_parallel_branch", "P2_quality"), "%.1f" % (100 * _S["G4_parallel_branch"]["decision_gap"]["P2_quality"]["predicted"]), _c("G4_parallel_branch", "B2_1d_framework"),
         _c("G4_parallel_branch", "P5_robust_theta_struct"), _c("G4_parallel_branch", "P5_robust_theta_struct", "coverage", 0), _c("B_gpr_failed_unflagged", "P2_quality", d=0),
         "%.0f" % (100 * min(ES["P2_quality"])), "%.0f" % (100 * max(ES["P2_quality"]))))
para("We believe the work aligns with the journal’s interests in probabilistic safety assessment, model uncertainty, automatic fault detection and operator decision-support systems. "
     "The manuscript explicitly distinguishes simulation-based findings from field-validated performance: the sensor model is assumed, no published detection-versus-depth dataset was reproduced, and the reliability figures are conditional on the simulated environment. "
     "Its code, configurations, results and supplementary materials are public and are intended to support independent reproducibility (https://doi.org/%s; release %s at %s)." % (SW, RELEASE, REPO))
para("The manuscript is not under consideration elsewhere. An earlier, non-peer-reviewed white paper for an open innovation challenge described the concept and is not a publication; earlier versions of the preprint (https://doi.org/%s, https://doi.org/%s, https://doi.org/%s) were prepared for a different journal and were not submitted to it. "
     "I am the sole author, have no competing interests and received no funding. As required, the manuscript declares the use of generative AI (Claude, Anthropic; Claude Sonnet 5.5, through Claude Code) to help write and run the code, generate figures and draft and edit the text, and I take full responsibility for the content." % (PP_V1, PP_V2, PP_V3))
para("Thank you for considering this manuscript.")
para("Sincerely,", after=18)
para("Leon Sandler")
para("The Conscious Machine – Independent Research", after=0)
para("Northbrook, Illinois, USA")
doc.save(os.path.join(HERE, "out", "Cover_Letter_RESS.docx"))
print("saved cover letter and highlights; highlight lengths", [len(t) for t in HL])
