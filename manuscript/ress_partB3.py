# -*- coding: utf-8 -*-
"""RESS manuscript, part B3: Discussion, Conclusions, declarations, appendices, references."""
# =============================================================================================== 7 Discussion
HD("7. Discussion")
HD("7.1 Reliability limits of probabilistic decision support", 2)
P("**What the simulation demonstrates, within the model.** (i) The conditional risk of released segments is a steep function of the released coverage, and the policies differ less at equal coverage than at their own operating points: much of what separates them is where on the curve they stop (Sections 6.1 and 6.2). "
  "(ii) A policy built on a nominal model is overconfident where the model is wrong; its predicted risk among released segments can be two orders of magnitude below the observed risk (Section 6.2). "
  "(iii) A lateral-tracking model that is the most reliable in the matched case is the least reliable under a parallel utility, so that complexity cannot be taken as a proxy for reliability (Section 6.4). "
  "(iv) A bound over an explicit set of parameters and structures removes most of that failure at a stated cost in released coverage, but only for what the set contains; an unflagged sensor failure lies outside it and defeats every policy (Section 6.3). "
  "(v) Parameter uncertainty accounts for most of the variance of the unsafe-release probability of every policy in the matched geometry, and the dominant failure driver depends on the policy: the geometry for the quality-adjusted policy, undetected sensor failure for the robust one (Sections 6.5 and 6.7). "
  "(vi) The benefit of the framework in conditions of sensor and soil mismatch comes from the health information and the reference check, not from the abstention or the robust bound alone (Sections 6.2 and 6.6).", align="justify")
P("**What it suggests, conditionally on the model resembling reality.** A decision layer should publish, with its recommendation, an estimate of its risk among released segments under a stated set of alternatives and not only the posterior probability; the gap between the two is the measure of its overconfidence. "
  "The health diagnostic and the reference check are the critical components, and their sensitivity should be measured before the rest is trusted. Verification should be directed at the segments in the marginal zone and in conditions flagged as unfamiliar, ranked by probability. "
  "Where the geometry cannot be assumed, parallel passes and a swath-wide assessment are needed, and the policy should be run alongside a simpler one whose disagreement is itself a warning.", align="justify")
P("**What it does not establish.** Whether the sensor model reproduces real GPR and EM behaviour in any soil; whether any measured detection-versus-depth dataset agrees with the assumed curves (none was reproduced); the real frequency of parallel utilities, branches and unflagged faults; the sensitivity and false-flag rate of real diagnostics; "
  "the real cost and consequences of strikes, holds and pits; whether crews would use a three-state output as intended; and any result in a specific country, soil or network. The numerical values of the risks are properties of the simulator. The qualitative findings, that the nominal model is overconfident under mismatch, that a bound costs coverage, that undetected faults dominate, and that no policy dominates at equal coverage, are what the simulation is designed to expose, and they would have to be tested with data.", align="justify")
HD("7.2 Safety implications and operator decision support", 2)
P("A recommendation to release a segment is read by an operator, and misplaced trust is a known failure of automation " + C("parasuraman97", "lee04") + ". The three-state output addresses it in part: a segment is not released unless it is in a zone where the sensors could have seen a utility and the checks passed, and the unverified share is reported. "
  "The results show where that is not enough. With an unflagged sensor failure the output looks the same as with healthy sensors and is wrong for two thirds of the released segments; with a parallel utility the lateral tracker releases the footprint with an apparent confidence that its own probability does not justify. "
  "A safety case for such a layer would have to state the conditions under which each branch of the failure tree has been tested, the diagnostic coverage that is assumed, and the independent verification that is required where the structural assumptions cannot be checked. "
  "The robust policy is one way to turn the second into a rule; the cost is a lower coverage (Section 6.2), which an operator pays in verification effort, and the explicit trade-off between the two is the decision that the reliability–coverage curve supports. "
  "The bound is conservative by construction, and the use of conservatism in risk assessment has its own cautions " + C("aven16") + ": a bound that is too wide makes the policy unusable (P7), and one that is too narrow gives false assurance.", align="justify")
HD("7.3 Transferability", 2)
P("The case is subsurface utility mapping, but the analysis is not specific to it. Any system that releases an action on sensor evidence, whether an automated vehicle, a process shutdown or an inspection gate, has a failure event of the kind F = {released, hazard present}, a coverage, a set of faults that the diagnostic may or may not see, and a model whose structure may be wrong. "
  "What transfers is the method: define the failure event and the metrics with explicit denominators; compare policies on reliability–coverage curves and not at single operating points; decompose the variance of the failure probability into aleatory and epistemic parts without weighting structural alternatives; "
  "simulate fault combinations jointly and check dependence; and rank the drivers of failure by global sensitivity analysis for each policy separately. What does not transfer is any number.", align="justify")
HD("7.4 Limitations and what a field test would need", 2)
for t in (
    "**No external validation.** The sensor model is assumed. The first step is external: compare the assumed detection curves with at least one published or newly measured dataset that reports GPR and EM detection across known utility depths and soils, and report the mismatch. This is the most important missing step, and additional synthetic experiments cannot replace it.",
    "**The uncertainty set is the designer’s.** The robust policies are robust to what Ω contains. The test envelope overlaps it and goes beyond it in places, and the policy is not robust to an unflagged failure. A different set gives a different cost in coverage; the sets were not optimised.",
    "**Structure and parameters are sampled from stated ranges.** The ranges (attenuation from a quarter to four times the assumed value, ±3 dB, geometry from five structures) are assumptions, the five structures are not exhaustive (no crossings, depth changes or buried obstacles), and the independence assumed in the sensitivity analysis is not realistic.",
    "**Network size.** The aleatory share depends on the network size, and 490 corridors of 500 m is one choice. The variance decomposition assumes that the parameter draws are independent of the network.",
    "**Costs and diagnostics are assumed.** The loss model, the diagnostic rates and the reference check are assumptions; the expected-loss policy is only as good as its costs.",
    "**The ablation shows reversals that are unexplained** (Section 6.6), and the attribution to the failure tree uses a fixed priority order; it is a diagnostic, not a probability decomposition.",
    "**Reliability is conditional.** All reliability figures are conditional decision reliability in the simulated environment (Section 3.1). They do not include excavation practice, locating before digging or operator behaviour, and modelled intersections are not strikes.",
):
    H.bullet(doc, t)
P("The minimum field test is a controlled corridor with known pipe positions, depths and materials in at least two soils, surveyed with a centre pass and parallel passes; GPR and EM data recorded with surveyed positions; a deliberate sensor fault and a reference-target check; the software run offline; "
  "and the conditional risk, coverage, calibration and unverified share reported with the definitions of Section 3.1. A false clearance of at most 1%% shown with a 95%% upper bound needs about %d released segments with no failure, or about %d with one failure (exact binomial intervals; %s). "
  "A parallel utility, a branch and a deliberately unflagged fault should be included, because these are where the simulation says the risk is." % (
      [r for r in R4["pilot_sample_sizes"]["false_clearance_or_event_rate"] if r["target_upper_bound"] == 0.01 and r["observed_events"] == 0][0]["n_required"],
      [r for r in R4["pilot_sample_sizes"]["false_clearance_or_event_rate"] if r["target_upper_bound"] == 0.01 and r["observed_events"] == 1][0]["n_required"], C("clopper34", "brown01")), align="justify")

# =============================================================================================== 8 Conclusions
HD("8. Conclusions")
P("The reliability of a probabilistic decision layer for excavation clearance was analysed in simulation. The conclusions apply to the model and not to the field.", align="justify")
for t in (
    "The unsafe-release probability, the conditional false-clearance risk and the release coverage are linked by P(F) = P(U | A) P(A) and have to be reported together; in the matched model the sensor-quality-adjusted policy releases %s%% of the corridor at %s%% conditional risk, and the policies differ less at equal coverage than at their own operating points." % (q("baseline", "P2", "coverage", 0), q("baseline", "P2")),
    "A nominal model is overconfident where it is wrong: with a parallel utility and a branch the quality-adjusted policy releases %s%% of the corridor at %s%% conditional risk while its probabilities predict %s%%, and a more complex spatial model is less reliable than a simpler one there (%s%% against %s%% for the one-dimensional framework)." % (
        q("G4_parallel_branch", "P2", "coverage", 0), q("G4_parallel_branch", "P2"), "%.1f" % (100 * SCN["G4_parallel_branch"]["decision_gap"]["P2_quality"]["predicted"]), q("G4_parallel_branch", "P2", d=0), q("G4_parallel_branch", "B2", d=0)),
    "A policy that releases only if an upper bound over an explicit set of parameters and structures is acceptable reduces that risk to %s%% at %s%% coverage, at the price of %s percentage points of released coverage; it does not protect against what the set does not contain, and an unflagged sensor failure leaves every policy at %s%% conditional risk." % (
        q("G4_parallel_branch", "P5"), q("G4_parallel_branch", "P5", "coverage", 0), "%.0f" % (100 * (qv("G4_parallel_branch", "P2", "coverage") - qv("G4_parallel_branch", "P5", "coverage"))), q("B_gpr_failed_unflagged", "P2", d=0)),
    "Epistemic parameter uncertainty accounts for %s to %s%% of the variance of the unsafe-release probability of the quality-adjusted policy, and the dominant failure driver depends on the policy: the share of parallel utilities and branches for the quality-adjusted policy, and undetected sensor failure for the robust one." % ("%.0f" % (100 * min(ES["P2_quality"])), "%.0f" % (100 * max(ES["P2_quality"]))),
    "Sensor-health information and a reference check, not abstention alone, are what separate the framework from calibrated-abstention baselines when sensors or soils depart from the assumed ones; no policy dominates at equal released coverage.",
    "The simulated performance has not been validated against field measurements. Physical validation against measured detection data, with parallel utilities, branches and deliberately unflagged faults, is the necessary next step.",
):
    H.bullet(doc, t)
P("The study fixes definitions and a protocol for assessing the reliability of a decision-support layer, and shows which assumptions its conclusions rest on. It cannot show field performance.", align="justify")

# =============================================================================================== declarations
HD("Declarations", 1)
P("**CRediT authorship contribution statement.** Leon Sandler: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Visualization, Writing – original draft, Writing – review and editing.", align="justify")
P("**Funding.** This research received no specific grant from any funding agency in the public, commercial or not-for-profit sectors.", align="justify")
P("**Declaration of competing interests.** The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.", align="justify")
P("**Prior dissemination.** An earlier, non-peer-reviewed white paper describing the concept was prepared in response to an open innovation challenge on detecting underground utilities issued through the Wazoku (InnoCentive) platform. "
  "Its numerical results came from an earlier version of the simulation whose code was not available when this manuscript was prepared; the simulation was reimplemented from the method description and all numbers in this paper come from the released code. "
  "The challenge submission is not a publication and the present manuscript is not under consideration elsewhere. Earlier versions of the preprint were prepared for a different journal and have not been submitted to it.", align="justify")
P("**Version history of the preprint.** Version 1 (https://doi.org/" + PP_V1 + ") compared a binary map and a three-state rule at different released coverages and reported about four times fewer strikes for the three-state rule; that comparison is withdrawn. "
  "Version 2 (https://doi.org/" + PP_V2 + ") compared policies at equal coverage and added lateral tracking, sensor-health awareness, capability zones, unseen soils and a value-of-information analysis. Version 3 (https://doi.org/" + PP_V3 + ") added a structural-mismatch experiment and a parameter envelope. "
  "Version 4 (this version) reframes the study as a reliability analysis: it defines the safety failure event and the reliability metrics, adds the aleatory–epistemic decomposition, the fault and common-cause scenarios, the release policies and calibrated-abstention baselines, the reliability–coverage curves, the ablation and the global sensitivity analysis. Numbers of earlier versions that are quoted here are unchanged.", align="justify")
P("**Data and code availability.** All code, configurations, results (results.json, results_v4.json, results_v5.json), figure scripts, tests and manuscript builders are available at %s (release %s) and archived on Zenodo (software: https://doi.org/%s, all versions https://doi.org/%s; manuscript preprint: https://doi.org/%s, all versions https://doi.org/%s). "
  "Every table and figure is regenerated by the commands in Appendix A. No field data were used." % (REPO, RELEASE, SW, SW_CONCEPT, PP, PP_CONCEPT), align="justify")
P("**Declaration of generative AI and AI-assisted technologies in the writing process.** During the preparation of this work the author used Claude (Anthropic; Claude Sonnet 5.5, accessed through Claude Code) to help write and run the simulation code, generate figures and draft and edit the text. "
  "The simulation outputs were produced by running the released code with a fixed seed and were not written by the model. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the publication.", align="justify")
P("**Acknowledgements.** None.", align="justify")

# =============================================================================================== appendices
HD("Appendix A. Reproducing the results", 1)
for line in ("pip install -r requirements.txt", "python SubSurface_MC.py --demo                 # %d self-tests of the version 1.0 code" % len(R["selftests"]), "python SubSurface_MC.py --reproduce --out results --n 500 --blocks 10 --seed 42",
             "python figure_generation.py --results results/results.json --out results/figures", "python SubSurface_v4.py --demo                 # %d self-tests of the version 1.1 code" % len(R4["selftests"]),
             "python SubSurface_v4.py --reproduce --out results_v4 --seed 42", "python figure_generation_v4.py --results results_v4/results_v4.json --out results_v4/figures",
             "python SubSurface_v5.py --demo                 # %d self-tests of the reliability analyses" % len(R5["selftests"]), "python SubSurface_v5.py --reproduce --out results_v5 --seed 42 --workers 8",
             "python figure_generation_v5.py --results results_v5/results_v5.json --out results_v5/figures", "python tests/test_subsurface.py"):
    p = doc.add_paragraph()
    r = p.add_run(line)
    r.font.name = "Courier New"
    r.font.size = Pt(9.5)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
P("")
P("The version 1.0 and 1.1 commands take a few minutes and about twelve minutes; SubSurface_v5.py took %d minutes with eight worker processes (Python %s, NumPy %s). Every random stream is derived from the seed, a scenario tag and a block index, so that the results do not depend on the number of processes. "
  "A fresh clone of the release was run and its results files compared with the archived ones (see the repository README). results_v5.json records the command, the seed, the library versions, the definitions, the uncertainty sets and every table quoted in this paper." % (round(R5["meta"]["runtime_s"] / 60), R5["meta"]["python"], R5["meta"]["numpy"]), align="justify")
HD("Appendix B. Assumptions of the reliability experiments", 1)
CT = R5["costs_usd"]
P("Costs (scenario assumptions): miss US$%s per consequence unit of the utility class (PE/PVC water 4, cast-iron water 6, plastic and concrete sewer 3, power 10, telephone and fibre 2), hold US$%s per segment, pit US$%s plus US$%s per metre of class mid-depth. "
  "Decision thresholds: present at 0.5; absent at 0.10 in zone A and 0.02 in zone B; calibrated-abstention target 2%%. Uncertainty set of the robust policies: attenuation doubled; sensors 3 dB weaker; EM coupling halved; both of the first two; a filter with loss 0.05, shift 0.03 and drift 0.10 per segment; no anchor; the one-dimensional on-alignment model; and, for P7, the probability that a utility lies anywhere in the ±5 m swath. "
  "All other assumptions are in the assumptions registers of the repository (Supplementary Material)." % ("{:,.0f}".format(CT["strike_per_consequence_unit"]), "{:,.0f}".format(CT["hold_per_segment"]), "{:,.0f}".format(CT["pit_base"]), "{:,.0f}".format(CT["pit_per_m"])), align="justify")

# =============================================================================================== references
HD("References", 1)
for key in ("numpy20", "scipy20", "mpl07"):
    K._note(key)
P("The simulation uses NumPy " + C("numpy20") + ", SciPy " + C("scipy20") + " and Matplotlib " + C("mpl07") + " and scikit-learn for the surrogate models.", align="justify")
for key in ("saltelli10", "sobol01", "mckay79", "borgonovo16", "iooss15", "jansen99", "ferson96", "oberkampf04", "pate96", "flage14", "droguett08", "helton96", "ruijters15", "isermann05", "langseth07", "weber12", "bobbio01", "mosleh91", "venkat03", "hendrickx24", "bates21", "hullermeier21", "kaplan81", "zio09", "zio18", "apostolakis90", "derkiureghian09", "aven11", "aven16", "parasuraman97", "lee04"):
    K._note(key)
BODY[0] = False
REFLINES = K.reference_list()
EPA = "US EPA (n.d.). Environmental Geophysics: Ground Penetrating Radar (Table 1, electromagnetic properties of earth materials). U.S. Environmental Protection Agency. https://archive.epa.gov/esd/archive-geophysics/web/html/ground-penetrating_radar.html (accessed 11 October 2026)."
SKL = "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: machine learning in Python. *Journal of Machine Learning Research* 12, 2825–2830."
import unicodedata


def _k(l):
    return unicodedata.normalize("NFKD", l).encode("ascii", "ignore").decode().lower()


for extra in (EPA, SKL):
    ix = next((i for i, l in enumerate(REFLINES) if _k(l) > _k(extra)), len(REFLINES))
    REFLINES.insert(ix, extra)
for line in REFLINES:
    p = H.para(doc, line, size=9.5, space_after=3)
    p.paragraph_format.left_indent = Pt(18)
    p.paragraph_format.first_line_indent = Pt(-18)
    p.paragraph_format.line_spacing = 1.1

os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
json.dump(SUPP, open(os.path.join(HERE, "out", "supp_figs_ress.json"), "w"), indent=1)
out = os.path.join(HERE, "out", "Manuscript_RESS.docx")
doc.save(out)
print("saved", out)
print("abstract words:", AB_WORDS, "body words (approx, excl. refs/tables):", WORDS["body"], "references:", len(K.USED))
