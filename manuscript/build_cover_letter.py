# -*- coding: utf-8 -*-
"""Cover letter and highlights for Tunnelling and Underground Space Technology.   python build_cover_letter.py -> out/Cover_Letter_TUST.docx, out/Highlights_TUST.docx"""
import os
import sys

from docx.shared import Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import docx_helpers as H  # noqa: E402
from common import R, SW, PP, REPO, RELEASE, TITLE, mm, pc  # noqa: E402

H.AUTO_MATH = False
M = R["main"]
POL = R["decision"]["policies"]
bn = POL["anchored fusion, binary map (absent = clear)"]
p10 = POL["anchored fusion, three-state, clear if p<0.10"]
unv = M["sensor_blind_share"]

# ------------------------------------------------------------------------------------------------ highlights
HL = [
    "A decision layer fuses GPR, EM locator and a known anchor along a utility corridor.",
    "Each 5 m segment is present, absent or unverified; silence is never called clear.",
    "Detection, calibration, location error and unverified share are reported apart.",
    "Seeded simulation tests baselines, ablations, stress cases and an excavation trial.",
    "Lateral shifts, uncertain depth and GPR failure are the main failure modes.",
]
for t in HL:
    assert len(t) <= 85, (len(t), t)
d = H.new_document(size=11, line=1.15)
H.para(d, "**Highlights** – " + TITLE, space_after=8)
for t in HL:
    H.bullet(d, t)
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
d.save(os.path.join(HERE, "out", "Highlights_TUST.docx"))

# ------------------------------------------------------------------------------------------------ cover letter
doc = H.new_document(size=11, line=1.15)


def para(text, bold=False, after=6):
    p = doc.add_paragraph()
    if bold:
        p.add_run(text).bold = True
    else:
        H.add_rich(p, text)
    p.paragraph_format.space_after = Pt(after)
    return p


def bullet(text):
    p = doc.add_paragraph(style="List Bullet")
    H.add_rich(p, text)
    p.paragraph_format.space_after = Pt(3)


for line in ("Leon Sandler", "Independent researcher, Northbrook, Illinois, USA", "sandler.leon@gmail.com", "ORCID: https://orcid.org/0009-0007-4584-808X"):
    para(line, after=0)
para("")
para("11 October 2026")
para("The Editors\nTunnelling and Underground Space Technology", after=10)
para("Submission of an original research article: “%s”" % TITLE, bold=True, after=10)
para("Dear Editors,")
para("I submit the enclosed article for consideration in Tunnelling and Underground Space Technology. It concerns the mapping of buried utilities before excavation in the urban underground, "
     "a subject the journal has addressed in its reviews of utility mapping and location accuracy (Metje et al., 2007; Costello et al., 2007; Hao et al., 2012; Jaw and Hashim, 2013; Xie et al., 2022). The paper is a simulation study. It uses no field data and says so throughout.")
para("What the paper does", bold=True, after=3)
para("Ground-penetrating radar (GPR) and electromagnetic locators report detections, but a missing detection is weak evidence where soil attenuates the signal, and a map that marks only what was detected invites the reader to treat silence as clearance. "
     "The paper specifies a decision layer above the sensors: an anchored Bayesian filter along the corridor, likelihoods that depend on soil, material and depth, and a three-state output (present, absent, unverified) with a verification-priority ranking for trial pits. "
     "It then tests the layer in a seeded Monte Carlo study, with the following design choices that I believe respond to what a reader of this journal would ask:", after=3)
bullet("Detection and classification, probability calibration, location and depth accuracy, and the share of the network left unverified are reported separately, each with explicit denominators (sensor-visible cells, all cells, sensor-blind cells).")
bullet("Fifteen baselines and ablations are compared on identical simulated data, including an EM-only proxy for current practice, rule-based and per-segment fusion, propagation without an anchor, generic soil likelihoods and three diagnostic variants.")
bullet("Stress tests cover lateral displacement of utilities, an anchor that is certain but wrong, a dead sensor, dropped observations, a mis-specified hazard, correlated evidence and ten one-at-a-time parameter changes.")
bullet("A decision-consequence experiment compares excavation-clearance policies by strikes per kilometre and corridor released, and trial-pit allocation rules.")
para("Principal results (all within the model)", bold=True, after=3)
para("In sensor-visible cells the framework reaches %s%% accuracy (miss rate %s%%, false-alarm rate %s%%), a modest improvement over calibrated per-segment fusion (%s%%) and far above the EM-only proxy (%s%%). "
     "%s%% of the assumed network is sensor-blind and is reported as unverified. In a simulated clearance trial the three-state rule gives about %.1f times fewer strikes per kilometre than a binary map, for %.0f percentage points less corridor released. "
     "The paper also reports where the framework fails: lateral shifts, an incorrectly certain anchor, GPR failure and uncertain depth. Several results are unflattering to the proposal, for example that the anchor adds little in sensor-visible cells and that EM adds little in aggregate, and they are reported as found." % (
         mm("anch_full", "visible", "acc"), mm("anch_full", "visible", "miss"), mm("anch_full", "visible", "fa"), mm("seg_flat", "visible", "acc"), mm("em_only", "visible", "acc"), pc(unv, 0),
         bn["strikes_per_km"][0] / p10["strikes_per_km"][0], 100 * (bn["cleared"][0] - p10["cleared"][0])))
para("Scope and limits", bold=True, after=3)
para("The simulation tests the logic of the decision layer and its sensitivity to its own assumptions. Its parameters are assumptions, not measurements, and the manuscript has a section that separates what is demonstrated within the model, what is suggested conditionally on the model resembling reality, and what is not established. "
     "I do not claim field performance. I would welcome the Editors’ and reviewers’ views on whether a simulation-based article of this kind, which fixes definitions and a protocol for a field trial, is appropriate for the journal.")
para("Prior dissemination and disclosures", bold=True, after=3)
para("An earlier, non-peer-reviewed white paper describing the concept was prepared in response to an open innovation challenge on detecting underground utilities issued through the Wazoku (InnoCentive) platform. It is not a publication. "
     "The numerical results of that white paper came from an earlier version of the simulation whose code was not available when this manuscript was prepared; the simulation was reimplemented from the method description, all numbers in the manuscript come from the released code, and they differ from those of the white paper. "
     "The manuscript is not under consideration elsewhere. I am the sole author, have no competing interests and received no funding.")
para("Data, code and AI use", bold=True, after=3)
para("All code, tests, the configuration, results.json and figure scripts are public at %s (release %s) and archived at https://doi.org/%s; a preprint of the manuscript is available at https://doi.org/%s. Every table and figure is regenerated by the commands in Appendix B of the manuscript. "
     "The manuscript declares, in line with the publisher’s policy, that Claude (Anthropic; Claude Sonnet 5.5, through Claude Code) was used to help write and run the code, generate figures and draft and edit the text, that the simulation outputs were produced by running the released code with a fixed seed, and that I take full responsibility for the content." % (REPO, RELEASE, SW, PP))
para("Thank you for considering the paper.")
para("Yours sincerely,", after=18)
para("Leon Sandler")
doc.save(os.path.join(HERE, "out", "Cover_Letter_TUST.docx"))
print("saved cover letter and highlights")
