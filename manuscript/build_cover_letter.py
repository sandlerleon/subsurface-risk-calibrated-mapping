# -*- coding: utf-8 -*-
"""Cover letter and highlights for Tunnelling and Underground Space Technology (version 1.1).   python build_cover_letter.py -> out/Cover_Letter_TUST.docx, out/Highlights_TUST.docx"""
import os
import sys

from docx.shared import Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import docx_helpers as H  # noqa: E402
from common import R, R4, SW, PP, SW_V1, PP_V1, REPO, RELEASE, TITLE, mm, pc  # noqa: E402

H.AUTO_MATH = False
M = R["main"]
SC = R4["scenarios"]
unv = M["sensor_blind_share"]


def sm(sc, m, k, d=1):
    return pc(SC[sc]["models"][m]["metrics"][k][0], d)


# ------------------------------------------------------------------------------------------------ highlights
HL = [
    "A filter tracks utilities along and across a corridor: present, absent or unverified.",
    "A sensor flagged as failed no longer counts as evidence of absence.",
    "Detection, calibration, lateral error and unverified share are reported separately.",
    "Six models, sixteen scenarios and unseen soils are compared with bootstrap intervals.",
    "At equal released coverage the gain is small; failures and unseen soils remain risks.",
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
para("Ground-penetrating radar (GPR) and electromagnetic locators report detections, but a missing detection is weak evidence where soil attenuates the signal or an instrument has failed, and a map that marks only what was detected invites the reader to treat silence as clearance. "
     "The paper specifies a decision layer above the sensors: a Bayesian filter that follows a utility along a corridor and across a lateral grid, likelihoods that depend on soil, material and depth, sensor-health awareness, depth-resolved capability zones, and a three-state output (present, absent, unverified) with a value-of-information ranking for trial pits. "
     "It tests the layer in seeded Monte Carlo experiments designed so that a reader can see where it helps and where it does not:", after=3)
bullet("Detection and classification, probability calibration, lateral and depth accuracy, and the share of the network left unverified are reported separately, with explicit denominators and cluster-bootstrap 95% intervals.")
bullet("Six models are compared on identical simulated data in sixteen scenarios, including an equal-effort baseline (three repeat passes on the centre line), lateral displacement of utilities, sensor failure with an imperfect diagnostic, a wrong or missing anchor, an offset map, sparse coverage, and two soils not used to set the model.")
bullet("The excavation-clearance comparison is made at equal released coverage, equal risk and equal cost, and trial-pit allocation by value of information is compared with random and probability-first allocation.")
para("Principal results (all within the model)", bold=True, after=3)
para("In sensor-visible cells the anchored filter reaches %s%% accuracy (miss rate %s%%, false-alarm rate %s%%), a modest improvement over calibrated per-segment fusion (%s%%) and far above an EM-only proxy (%s%%); %s%% of the assumed network is sensor-blind and is reported as unverified. "
     "With three parallel passes, lateral tracking keeps false alarms near %s%% when lateral shifts are frequent, where one-pass filters reach %s%%. Sensor-health awareness reduces false clearance from %s%% to %s%% under mixed sensor health, but an unflagged GPR failure defeats every model tested, and in soils not used to set the model false clearance is still %s%% with an on-site reference check. "
     "Several results are unflattering to the proposal and are reported as found: the anchor adds little in sensor-visible cells, EM adds little in aggregate, and at equal released coverage the layer is only slightly safer than per-segment fusion." % (
         mm("anch_full", "visible", "acc"), mm("anch_full", "visible", "miss"), mm("anch_full", "visible", "fa"), mm("seg_flat", "visible", "acc"), mm("em_only", "visible", "acc"), pc(unv, 0),
         pc(R4["shift_sweep"]["rate_per_100m"]["2.0"]["proposed_3pass"]["metrics"]["false_alarm"][0]), pc(R4["shift_sweep"]["rate_per_100m"]["2.0"]["continuity_1d"]["metrics"]["false_alarm"][0]),
         sm("mixed_health_realistic_diagnostic", "continuity_1d", "false_clearance", 0), sm("mixed_health_realistic_diagnostic", "proposed_3pass", "false_clearance", 0), sm("ood_soils", "proposed_3pass", "false_clearance", 0)))
para("Scope and limits", bold=True, after=3)
para("The simulation tests the logic of the decision layer and its sensitivity to its own assumptions. Its parameters are assumptions, not measurements, and the manuscript separates what is demonstrated within the model, what is suggested conditionally on the model resembling reality, and what is not established. "
     "I do not claim field performance. I would welcome the Editors’ and reviewers’ views on whether a simulation-based article of this kind, which fixes definitions and a protocol for a field trial, is appropriate for the journal.")
para("Correction to an earlier preprint and prior dissemination", bold=True, after=3)
para("Version 1 of the preprint (https://doi.org/%s) reported that a three-state rule gave about four times fewer simulated strikes than a binary map. That comparison confounded the rule with the operating point (the two policies released different shares of the corridor). "
     "The enclosed manuscript, which is version 2 of the preprint, compares policies at equal coverage and withdraws the claim. "
     "An earlier, non-peer-reviewed white paper describing the concept was prepared in response to an open innovation challenge on detecting underground utilities issued through the Wazoku (InnoCentive) platform; it is not a publication, and its numerical results came from an earlier version of the simulation whose code was not available when this manuscript was prepared, so the simulation was reimplemented from the method description. "
     "The manuscript is not under consideration elsewhere. I am the sole author, have no competing interests and received no funding." % PP_V1)
para("Data, code and AI use", bold=True, after=3)
para("All code, tests, configurations, results files and figure scripts are public at %s (release %s) and archived at https://doi.org/%s; a preprint is available at https://doi.org/%s. Every table and figure is regenerated by the commands in Appendix B of the manuscript, and a Supplementary Material file gives the full scenario tables. "
     "The manuscript declares, in line with the publisher’s policy, that Claude (Anthropic; Claude Sonnet 5.5, through Claude Code) was used to help write and run the code, generate figures and draft and edit the text, that the simulation outputs were produced by running the released code with a fixed seed, and that I take full responsibility for the content." % (REPO, RELEASE, SW, PP))
para("Thank you for considering the paper.")
para("Yours sincerely,", after=18)
para("Leon Sandler")
doc.save(os.path.join(HERE, "out", "Cover_Letter_TUST.docx"))
print("saved cover letter and highlights")
