# -*- coding: utf-8 -*-
import os
HERE = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(HERE, "build_supplement_ress.py"), encoding="utf-8").read()
blk = open(os.path.join(HERE, "_new_supp_block.txt"), encoding="utf-8").read()
marker = "# ------------------------------------------------------------------------------------------------ S7.. version 1.1/1.2 material"
assert marker in s
s = s.replace(marker, blk + "# ------------------------------------------------------------------------------------------------ S12.. lateral-tracking and cost experiments")
rep = [('"S7. Version 1.1 scenario tables (six models in sixteen scenarios)"', '"S12. Lateral-tracking experiments: scenario tables (six models in sixteen scenarios)"'),
       ('"S8. Equal-coverage clearance (version 1.1, both worlds)"', '"S13. Equal-coverage clearance (lateral-tracking experiments, both worlds)"'),
       ('"S9. Capability zones and attenuation consistency"', '"S14. Capability zones and attenuation consistency"'),
       ('"S10. Value of information (version 1.1): change in total cost against no pits (US$ thousand per km)"', '"S15. Value of information: change in total cost against no pits (US$ thousand per km)"'),
       ('"S11. Pilot sample sizes (exact binomial, two-sided 95% interval)"', '"S16. Pilot sample sizes (exact binomial, two-sided 95% interval)"'),
       ('"S12. Supplementary figures"', '"S17. Supplementary figures"'),
       ("supp_figs_ress.json", "supp_figs_ca.json"),
       ("Supplementary_Material_RESS.docx", "Supplementary_Material_CA.docx"),
       ("from common_ress import R, R4, R5, TITLE, SW, PP", "from common_ress import R, R4, R5, SW, PP"),
       ('H.para(doc, "**Supplementary Material**", size=14, space_after=2)\nH.para(doc, TITLE, size=10.5, space_after=2)',
        'TITLE = "Change-Aware Reliability-Gated Sensor Fusion: Risk-Bounded Decisions Under Infrastructure Modifications and Model Uncertainty"\nH.para(doc, "**Supplementary Material**", size=14, space_after=2)\nH.para(doc, TITLE, size=10.5, space_after=2)'),
       ('"S1. Policies and baselines in every scenario"', '"S1. Survey evidence layer: policies and baselines in every scenario"'),
       ("strikes per km are released occupied segments per km of corridor (modelled intersections)", "intersections per km are released occupied segments per km of corridor (modeled intersections)"),
       ("Strikes/km", "Intersections/km")]
for a, b in rep:
    if a in s:
        s = s.replace(a, b)
    else:
        print("MISSING", a[:60])
open(os.path.join(HERE, "build_supplement_ca.py"), "w", encoding="utf-8").write(s)
print("ok")
