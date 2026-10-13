# -*- coding: utf-8 -*-
"""Change-aware manuscript, part 5: Discussion, Conclusions, declarations, appendices, references."""
HD("9. Discussion: model validity, failure modes and transferability")
HD("9.1 What the simulations show", 2)
P("**Demonstrated within the models.** (i) A map that is not updated for what can have changed since it was made becomes unreliable at a rate that the change process determines, and a decision layer that tracks the hazard state recursively can predict that rate for its own decisions (Sections 6.2 and 7.2). "
  "(ii) Work records are valuable as context and dangerous as explanation: using them to modulate the probability of change and the share of authorized events reduced the undetected hazardous states, and suppressing matched changes multiplied them (Sections 6.3 and 7.3). "
  "(iii) Continuous point sensors on a small share of the elements added little to periodic surveys, and where they were placed mattered more than whether the placement was optimized (Sections 6.4, 6.5 and 7.4). "
  "(iv) A gate over the model alternatives that the surveys have not rejected lowered risk under departures from the assumed change process and survey, but mainly by releasing fewer decisions; at the gate’s coverage the ungated estimator was close to it where the departure was a faster change process (Section 8.2). "
  "(v) In the survey evidence layer, a more elaborate spatial model was less reliable than a simpler one when its geometry assumption failed, the probabilities it attached to released segments could understate the observed risk by two orders of magnitude, and an unflagged sensor failure defeated every policy (Section 6.1).", align="justify")
P("**Suggested, conditionally on the models resembling reality.** A monitoring system that supports safety decisions should publish with each decision the age and coverage of the evidence behind it, treat work records as probabilistic context and report the hazard probability and the authorization probability separately, "
  "and be run beside a model whose disagreement with it is a warning. The architecture should not be judged by the accuracy of its estimate but by the risk of the decisions it supports at the coverage at which they are taken.", align="justify")
P("**Not established.** Whether any of the sensor models, change processes or reporting probabilities resembles a real utility corridor or scaffold; whether a real work-permit system has the record, delay and misattribution characteristics assumed; whether the hazard of the synthetic scaffold criterion corresponds to the structural hazard of a real scaffold; "
  "whether the change processes of real infrastructure are independent across elements (the bursts of Section 8.2 are one departure, not a model of reality); and any result in a specific plant, country or network. The numbers are properties of the simulators.", align="justify")
HD("9.2 Model validity and the role of abstention", 2)
P("The gate is one answer to the question of when a model has become invalid. Its likelihood-based rejection makes an alternative that the surveys contradict stop constraining the decision, and keeps the others in force. Two features of the results qualify it. "
  "First, it can only reject what the surveys reveal: silent failures of sensors that the surveys do not cover, or misattributed work records, leave the surveyed predictive likelihood unchanged. Second, its benefit is bought in abstention, which has a cost that this study does not value: a scaffold that is not released for use, "
  "or a segment that must be verified by a trial pit. A policy has to be judged on the risk–coverage curve and on the cost of the decisions it declines to take, and the cost model of the survey evidence layer (a miss, a hold and a pit) is one way to do that.", align="justify")
P("The result that a more complex spatial model can be less reliable than a simpler one when its assumptions are wrong, and the result that a change-aware estimator is more reliable than a static one when the change process is as assumed, are not in conflict. "
  "They are two instances of the same principle: the reliability of a decision is conditional on the validity of the model that supports it, and a method should be evaluated both where its assumptions hold and where they do not.", align="justify")
HD("9.3 Transferability", 2)
P("The framework is stated for elements with a hidden hazard state, observed asynchronously, with records of work. It transfers to other infrastructure whose state changes between observations: a pipeline whose wall thickness is surveyed periodically and monitored at a few points, a temporary works structure, a rail track. "
  "What transfers is the method: the decision, not the estimate, as the object of analysis; the observation age and coverage as explicit variables; the work record as context; and the evaluation at matched coverage against static and domain-specific baselines under single and combined failures. What does not transfer is any number.", align="justify")
HD("9.4 Limitations and what field validation would need", 2)
for t in (
    "**No external validation.** The sensor models, the change processes and the work-record model are assumed. For the utility domain no published detection dataset was reproduced; for the scaffold there is no external check. A comparison with measured data in both domains is the necessary next step, and further synthetic experiments cannot replace it.",
    "**Synthetic scaffold criterion.** Hazard labels for the scaffold come from a simple, monotone criterion and not from a structural model or an independent assessment. The benchmark tests the reliability of the decision layer given a criterion, not the criterion.",
    "**Independence and simple change processes.** The estimators treat elements as independent and the events as a memoryless process; real removals are clustered and correlated with schedules. The burst scenario is a departure, not a model.",
    "**Calibration data.** The estimators are calibrated on simulated nominal worlds with known event labels; in practice the labels are unknown, and the event rates and record characteristics would have to be learned from the data and from audits.",
    "**Placement and gate parameters.** The risk-optimized placement uses 40 training worlds per site and the gate uses six alternatives and a rejection threshold of 5 in log-likelihood; none was tuned, and different choices would give different results.",
    "**Coverage and cost.** The risks are reported with the coverage, but the cost of abstaining is not valued for the change-aware experiments; the costs of nodes and surveys are assumptions in node equivalents.",
    "**Reliability is conditional.** All figures are conditional decision reliability in the simulated environments; they do not include human factors, procedures or the consequences of a decision. No claim is made about hardware, certification for hazardous areas or deployment.",
):
    H.bullet(doc, t)
P("A field test would need, for the utility domain, a controlled corridor with known and changing utilities in at least two soils, surveyed repeatedly with GPR and EM and recorded with work orders, with trial pits as ground truth; for the scaffold, instrumented scaffolds with recorded and deliberately unrecorded modifications and an independent structural assessment of the resulting states. "
  "In both, the estimator would be calibrated on part of the data and its predicted risk compared with the observed risk on the rest, with a deliberately unflagged sensor fault and a deliberately wrong work record.", align="justify")

HD("10. Conclusions")
P("The reliability of decisions supported by a monitoring system under changing infrastructure states was analysed in simulation on two structurally different problems. The conclusions apply to the models and not to the field.", align="justify")
for t in (
    f"Accounting for modifications and observation age lowered the conditional unsafe-decision risk by a factor of {H1_UT[0]:.1f} (utilities) and {H1_SF[0]:.1f} (scaffold) relative to static-state fusion at matched decision coverage, and the dynamic estimator’s predicted risk followed the observed risk as the time since the last survey grew.",
    f"Work records are context and not explanation: suppressing permit-matched changes left a hazardous, unflagged state after {m6(SUPP_MISS[UT],0)}% and {m6(SUPP_MISS[SF],0)}% of the changes made under a valid record, against {m6(CTX_MISS[UT],0)}% and {m6(CTX_MISS[SF],0)}% when the records were used as evidence.",
    "Continuous point sensors on a small share of the elements added little to periodic surveys, and risk-optimized placement was not consistently better than simple rules; the cadence of the survey and the placement relative to what the survey cannot see mattered more.",
    "A reliability gate over the model alternatives that the surveys have not rejected lowered the risk under mismatch, mainly by releasing fewer decisions, and no method was reliable against every failure mode; an unflagged failure that no survey reveals defeats all of them.",
    "In the survey evidence layer, a more elaborate spatial model was less reliable than a simpler one when its geometry assumption failed, and the probabilities attached to released decisions understated the observed risk by up to two orders of magnitude; the epistemic part of the variance of unsafe release was 58 to 98% across policies and structures.",
    "The simulated performance has not been validated against field data and the scaffold hazard criterion is synthetic. Validation against measured data, including deliberately wrong work records and unflagged sensor faults, is the necessary next step.",
):
    H.bullet(doc, t)
P("The study fixes definitions and a protocol for assessing the reliability of change-aware monitoring and shows which assumptions its conclusions rest on. It cannot show field performance.", align="justify")

# =============================================================================================== declarations
HD("Declarations", 1)
P("**CRediT authorship contribution statement.** Leon Sandler: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Visualization, Writing – original draft, Writing – review and editing.", align="justify")
P("**Funding.** This research received no specific grant from any funding agency in the public, commercial or not-for-profit sectors.", align="justify")
P("**Declaration of competing interests.** The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.", align="justify")
P("**Prior dissemination.** Two non-peer-reviewed white papers describing applications of the concept, one for underground utility detection and one for scaffold monitoring, were prepared in response to open innovation challenges on the Wazoku (InnoCentive) platform; neither is a publication. "
  "The numerical results of the first came from simulation code that was not available when this manuscript was prepared, and the simulation was reimplemented. A preprint of this work is available on Zenodo (https://doi.org/" + PP + "). The manuscript is not under consideration elsewhere.", align="justify")
P("**Data and code availability.** All code, configurations, results (results.json, results_v4.json, results_v5.json, results_v6.json), figure scripts, tests and manuscript builders are available at %s (release %s) and are archived on Zenodo (software: https://doi.org/%s; manuscript preprint: https://doi.org/%s). "
  "Every table and figure is regenerated by the commands in Appendix A. No field data were used." % (REPO, RELEASE, SW, PP), align="justify")
P("**Declaration of generative AI and AI-assisted technologies in the writing process.** During the preparation of this work the author used Claude (Anthropic; Claude Sonnet 5.5, accessed through Claude Code) to help write and run the simulation code, generate figures and draft and edit the text. "
  "The simulation outputs were produced by running the released code with fixed seeds and were not written by the model. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the publication.", align="justify")
P("**Acknowledgments.** None.", align="justify")

# =============================================================================================== appendices
HD("Appendix A. Reproducing the results", 1)
for line in ("pip install -r requirements.txt", "python SubSurface_MC.py --demo                 # %d self-tests" % len(R["selftests"]), "python SubSurface_MC.py --reproduce --out results --n 500 --blocks 10 --seed 42",
             "python SubSurface_v4.py --demo                 # %d self-tests" % len(R4["selftests"]), "python SubSurface_v4.py --reproduce --out results_v4 --seed 42",
             "python SubSurface_v5.py --demo                 # %d self-tests (survey evidence layer)" % len(R5["selftests"]), "python SubSurface_v5.py --reproduce --out results_v5 --seed 42 --workers 8",
             "python SubSurface_v6.py --demo                 # %d self-tests (change-aware layer)" % len(R6["selftests"]), "python SubSurface_v6.py --reproduce --out results_v6 --seed 42",
             "python figure_generation.py --results results/results.json --out results/figures", "python figure_generation_v4.py --results results_v4/results_v4.json --out results_v4/figures",
             "python figure_generation_v5.py --results results_v5/results_v5.json --out results_v5/figures", "python figure_generation_v6.py --results results_v6/results_v6.json --out results_v6/figures", "python tests/test_subsurface.py"):
    p = doc.add_paragraph()
    r = p.add_run(line)
    r.font.name = "Courier New"
    r.font.size = Pt(9.5)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
P("")
P("SubSurface_v6.py (the change-aware experiments) took %d minutes on one process (Python %s, NumPy %s); SubSurface_v5.py (the survey evidence layer) took %d minutes with eight processes. Every random stream is derived from the seed, an experiment tag and a site or block index, so that results do not depend on the number of processes. "
  "A fresh clone of the archived code reproduced results_v5.json and results_v6.json exactly, and its self-tests and tests passed. Each results file records the command, the seed, the library versions, the definitions and every table quoted in this paper." % (
      round(R6["meta"]["runtime_s"] / 60), R6["meta"]["python"], R6["meta"]["numpy"], round(R5["meta"]["runtime_s"] / 60), ), align="justify")

# =============================================================================================== references
HD("References", 1)
for key in ("numpy20", "scipy20", "mpl07"):
    K._note(key)
P("The simulations use NumPy " + C("numpy20") + ", SciPy " + C("scipy20") + " and Matplotlib " + C("mpl07") + " and scikit-learn for the surrogate models of the sensitivity analysis.", align="justify")
for key in ("saltelli10", "sobol01", "mckay79", "jansen99", "borgonovo16", "iooss15", "efron79", "field07", "clopper34", "brown01", "howard66", "gneiting07a", "gneiting07b", "brier50", "oberkampf04"):
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

import usspell
print("US spelling edits:", usspell.apply(doc))
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
json.dump(SUPP, open(os.path.join(HERE, "out", "supp_figs_ca.json"), "w"), indent=1)
out = os.path.join(HERE, "out", "Manuscript_CA.docx")
doc.save(out)
print("saved", out)
print("abstract words:", AB_WORDS, "body words (approx, excl. refs/tables):", WORDS["body"], "references:", len(K.USED))
