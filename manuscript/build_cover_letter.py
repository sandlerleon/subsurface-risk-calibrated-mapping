# -*- coding: utf-8 -*-
"""Cover letter and highlights for Tunnelling and Underground Space Technology (version 1.2).   python build_cover_letter.py -> out/Cover_Letter_TUST.docx, out/Highlights_TUST.docx"""
import os
import sys

from docx.shared import Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import docx_helpers as H  # noqa: E402
from common import R, R4, SW, PP, PP_V1, REPO, RELEASE, TITLE, mm, pc  # noqa: E402

H.AUTO_MATH = False
M = R["main"]
SC = R4["scenarios"]
GM = R4["geometry_mismatch"]["levels"]
unv = M["sensor_blind_share"]


def sm(sc, m, k, d=1):
    return pc(SC[sc]["models"][m]["metrics"][k][0], d)


# ------------------------------------------------------------------------------------------------ highlights
HL = [
    "A filter tracks utilities along and across a corridor: present, absent or unverified.",
    "A sensor flagged as failed no longer counts as evidence of absence.",
    "Detection, calibration, lateral error and unverified share are reported separately.",
    "Parallel surveys improve lateral tracking under simulated utility shifts.",
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


for line in ("Leon Sandler", "Independent researcher, Northbrook, Illinois, USA", "sandler.leon@gmail.com", "ORCID: https://orcid.org/0009-0007-4584-808X"):
    para(line, after=0)
para("")
para("11 October 2026")
para("The Editors\nTunnelling and Underground Space Technology", after=10)
para("Submission of an original research article: “%s”" % TITLE, bold=True, after=10)
para("Dear Editors,")
para("**Relevance to underground engineering.** Excavation in the urban underground starts from utility maps whose reliability is rarely stated, and a map that marks only what was detected invites the reader to treat silence as clearance, "
     "where the ground, the depth or a failed instrument may have made detection impossible. The journal has addressed utility mapping and location accuracy in its reviews (Metje et al., 2007; Costello et al., 2007; Hao et al., 2012; Jaw and Hashim, 2013; Xie et al., 2022). "
     "The enclosed paper concerns how a survey should represent the limits of its own evidence.")
para("**Methodological contribution.** The paper specifies and evaluates a risk-calibrated decision policy for subsurface utility surveys, built from known ingredients (spatial tracking, sensor fusion, reject-option decisions, calibration): "
     "a filter that follows a utility along and across a corridor, treats a sensor flagged as failed as uninformative, derives an explicit “unverified” state from the capability of the instruments at the estimated depth, and ranks verification by value of information. "
     "The contribution claimed is the integration and the evaluation, not a new filtering algorithm; the manuscript compares the policy with the closest existing approaches (Table 1), keeps detection, calibration, lateral localisation and unverified coverage apart, and compares policies at equal survey effort and equal released coverage.")
para("**Why the findings merit review although the study is a simulation.** The paper is a methodological demonstration and says so: sensor behaviour is assumed, and no published detection-versus-depth dataset was reproduced (Section 4.10). "
     "Its value is that it shows where the policy helps and where it does not, with intervals and stress tests that include a structurally different truth. With three parallel passes, lateral tracking holds false alarms near %s%% under frequent lateral shifts where one-pass filters reach %s%%, and sensor-health awareness cuts false clearance from %s%% to %s%% under mixed sensor health; "
     "but an unflagged sensor failure defeats every model, a parallel utility turns the lateral tracker’s advantage into a disadvantage (false clearance %s%% against %s%%), unseen soils leave %s%% false clearance with an on-site check, and at equal released coverage the gain over per-segment fusion is small. "
     "These unflattering results are reported as found. Simulated utility intersections are used as a risk proxy, not as evidence of real strike rates. I would welcome the Editors’ view on whether a simulation-based article of this kind, which fixes definitions and a protocol for a field trial, is appropriate for the journal." % (
         pc(R4["shift_sweep"]["rate_per_100m"]["2.0"]["proposed_3pass"]["metrics"]["false_alarm"][0]), pc(R4["shift_sweep"]["rate_per_100m"]["2.0"]["continuity_1d"]["metrics"]["false_alarm"][0]),
         sm("mixed_health_realistic_diagnostic", "continuity_1d", "false_clearance", 0), sm("mixed_health_realistic_diagnostic", "proposed_3pass", "false_clearance", 0),
         pc(GM[3]["models"]["proposed_3pass"]["metrics"]["false_clearance"][0], 0), pc(GM[3]["models"]["continuity_1d"]["metrics"]["false_clearance"][0], 0), sm("ood_soils", "proposed_3pass", "false_clearance", 0)))
para("**Prior dissemination and corrections.** Version 1 of the preprint (https://doi.org/%s) reported a four-fold advantage of a three-state rule that came from comparing different released coverages; it is withdrawn and the manuscript compares policies at equal coverage. "
     "An earlier non-peer-reviewed white paper for an open innovation challenge (Wazoku/InnoCentive) described the concept; it is not a publication, and its numbers came from simulation code that was not available when this manuscript was prepared, so the simulation was reimplemented. "
     "The manuscript is not under consideration elsewhere. I am the sole author, have no competing interests and received no funding." % PP_V1)
para("**Data, code and AI use.** Code, tests, configurations, results and figure scripts are public at %s (release %s) and archived at https://doi.org/%s; the preprint is at https://doi.org/%s. A fresh clone of the release reproduces the results files (Appendix B). "
     "The manuscript declares, in line with the publisher’s policy, that Claude (Anthropic; Claude Sonnet 5.5, through Claude Code) was used to help write and run the code, generate figures and draft and edit the text, that the simulation outputs were produced by running the released code with a fixed seed, and that I take full responsibility for the content." % (REPO, RELEASE, SW, PP))
para("Thank you for considering the paper.")
para("Yours sincerely,", after=18)
para("Leon Sandler")
doc.save(os.path.join(HERE, "out", "Cover_Letter_TUST.docx"))
print("saved cover letter and highlights")
