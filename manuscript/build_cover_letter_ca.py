# -*- coding: utf-8 -*-
"""Cover letter and highlights for Reliability Engineering & System Safety (change-aware manuscript).   python build_cover_letter_ca.py -> out/Cover_Letter_CA.docx, out/Highlights_CA.docx"""
import os
import sys

import numpy as np
from docx.shared import Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
import docx_helpers as H  # noqa: E402
from common_ress import *  # noqa: E402,F401,F403
import SubSurface_v6 as W6  # noqa: E402

H.AUTO_MATH = False
TITLE = "Change-Aware Reliability-Gated Sensor Fusion: Risk-Bounded Decisions Under Infrastructure Modifications and Model Uncertainty"
exec(open(os.path.join(HERE, "ca_numbers.py"), encoding="utf-8").read())
import usspell  # noqa: E402

os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
d = H.new_document(size=11, line=1.15)
H.para(d, "**Highlights** – " + TITLE, space_after=8)
for t in HL:
    H.bullet(d, t)
usspell.apply(d, stop_at=None)
d.save(os.path.join(HERE, "out", "Highlights_CA.docx"))

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
para("13 October 2026")
para("The Editors\nReliability Engineering & System Safety", after=10)
para("Dear Editor,")
para("Please consider our manuscript, **“%s,”** for publication as an Original Research Article in *Reliability Engineering & System Safety*." % TITLE)
para("The manuscript addresses a reliability question that arises whenever a monitoring system or a digital twin supports a safety decision while the monitored infrastructure changes between observations: how can the system distinguish genuine safety-relevant changes from authorized modifications, "
     "sensor failures and incomplete observations without becoming overconfident? It formulates the reliability of the decision, not of the estimate, as the object of analysis, and proposes change-aware reliability-gated sensor fusion: a dynamic hazard estimator fed by asynchronous point sensors, periodic surveys and work records; "
     "work-permit reconciliation that keeps authorization separate from hazard; and a gate that releases a decision only if the supremum over the model alternatives not rejected by the data meets a risk criterion. "
     "The manuscript states what the gate does not do: it bounds a modeled hazard probability over a finite, assumed set of alternatives and is not a guarantee about the failure probability of a real structure.")
para("The method is evaluated by simulation on two structurally different problems, excavation clearance above buried utilities and continued use of an industrial scaffold, against static, dynamic and domain-specific baselines at matched decision coverage and under single and combined failures. "
     "Three pre-stated hypotheses are tested, and the manuscript reports the negative results with the same weight as the positive ones: continuous point sensors added little to periodic surveys, risk-optimized sensor placement was not consistently better than simple rules, "
     "the reliability gate lowered risk mainly by abstaining, and no method was reliable against every failure mode. "
     "Because the scaffold hazard criterion is synthetic, the scaffold conclusions were also tested under sixteen alternative definitions of an unsafe structure, and the advantage of dynamic estimation held under all of them.")
para("We believe the work aligns with the journal’s interests in probabilistic safety assessment, model uncertainty, fault detection and operator decision support. "
     "The manuscript states plainly that the findings are simulation-based: the sensor models and change processes are assumed, the scaffold hazard criterion is synthetic, and no field validation is reported. "
     "Code, configurations, results and supplementary materials are public to support reproducibility (https://doi.org/%s; release %s at %s)." % (SW, RELEASE, REPO))
para("The manuscript is not under consideration elsewhere. Two non-peer-reviewed white papers describing applications of the concept were prepared for open innovation challenges and are not publications, and a preprint of the manuscript is available on Zenodo (https://doi.org/%s). "
     "I am the sole author, have no competing interests and received no funding. As required, the manuscript declares the use of generative AI (Claude, Anthropic; Claude Sonnet 5.5, through Claude Code) to help write and run the code, generate figures and draft and edit the text, and I take full responsibility for the content." % PP)
para("Thank you for considering this manuscript.")
para("Sincerely,", after=18)
para("Leon Sandler")
para("The Conscious Machine – Independent Research", after=0)
para("Northbrook, Illinois, USA")
usspell.apply(doc, stop_at=None)
doc.save(os.path.join(HERE, "out", "Cover_Letter_CA.docx"))
print("saved cover letter and highlights; highlight lengths", [len(t) for t in HL])
