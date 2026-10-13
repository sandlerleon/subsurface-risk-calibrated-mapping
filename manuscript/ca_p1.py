# -*- coding: utf-8 -*-
"""Change-aware manuscript, part 1: title page, abstract, Introduction, Related work."""
P("**" + TITLE + "**", align="center", size=15, space_after=10)
P("Leon Sandler", align="center", size=12, space_after=0)
P("Independent Researcher, Northbrook, Illinois, USA", align="center", size=10.5, space_after=0)
P("ORCID: 0009-0007-4584-808X • Corresponding author: sandler.leon@gmail.com", align="center", size=10.5, space_after=12)
P("Software: %s (archived at https://doi.org/%s). Preprint: https://doi.org/%s." % (REPO, SW, PP), align="center", size=9.5, space_after=14)
HD("Abstract", 2)
P(ABSTRACT_TEXT, align="justify")
AB_WORDS = len(ABSTRACT_TEXT.split())
P("**Keywords:** reliability of monitoring systems; digital twin; model mismatch; change detection; work-permit reconciliation; sensor fusion; reliability-gated decisions; underground utilities; scaffolding", size=10.5)
doc.add_page_break()
BODY[0] = True

# =============================================================================================== 1 Introduction
HD("1. Introduction: reliability of decisions under changing infrastructure states")
P("Monitoring systems for infrastructure turn sensor evidence into decisions: release a stretch of ground for mechanical excavation, let people continue to use a scaffold, keep a pipeline in service. "
  "The evidence is rarely complete, and the thing being monitored does not stand still. A utility is relocated, repaired or newly installed between two surveys; a brace is removed from a scaffold in the course of authorized work, or without any authorization. "
  "The usual remedy is a digital twin or an as-built model that is kept up to date with sensors and work records " + C("tao19", "kritzinger18", "jones20") + ". "
  "A twin, however, is a model, and the decisions that rest on it are only as reliable as the model’s validity at the moment of the decision. It can be stale because the last observation is old, "
  "invalid because the change process differs from the one assumed, or misled by an instrument that has failed without announcing it, by a work record that is incomplete or wrong, or by a region that no sensor observes " + C("zio09", "zio18", "isermann05") + ".", align="justify")
P("The question that motivates this study is therefore a reliability question: **how can a monitoring system distinguish genuine safety-relevant changes from authorized modifications, sensor failures and incomplete observations without becoming overconfident?** "
  "Three requirements follow. The system has to know what it can observe and when it last observed it, and let the probability of an unobserved change grow in the way the process it monitors dictates, not by an arbitrary confidence-decay factor. "
  "It has to use work records as evidence about what is likely to have changed, without treating an authorized change as a safe one, since a permitted activity can still leave the structure hazardous and the record may be wrong. "
  "And it has to refuse to support a decision when its model alternatives, taken together, no longer meet the risk criterion, which is a property of the decision and not only of the estimate.", align="justify")
P("We study these requirements on two structurally different problems. In the first, a utility map and a periodic ground-penetrating radar (GPR) and electromagnetic (EM) survey support the decision whether a segment of corridor may be released for mechanical excavation; "
  "the hazard is a utility inside the excavation envelope, and the changes are installations, relocations and repairs. In the second, point sensors on the joints of an industrial scaffold, periodic three-dimensional vision sweeps and work permits support the decision whether the scaffold may continue to be used; "
  "the hazard is a missing or disconnected load-bearing member, and the changes are authorized and unauthorized removals. The two problems share a structure (elements with a hidden hazard state, observed asynchronously, with records of work) and differ in sensors, rates, observability and in how element hazards combine into a decision. "
  "That is the reason for studying them together: a reliability method that works for one sensor model and one infrastructure type tells little about the method.", align="justify")
P("The contributions are: (i) a dynamic formulation of the reliability of monitoring decisions, with a safety failure event, three reliability metrics and an explicit treatment of observation age, authorization and sensor coverage (Section 3); "
  "(ii) change-aware reliability-gated sensor fusion (CARGSF), which combines a hidden-Markov state estimator with permit reconciliation that keeps authorization separate from hazard, and a gate that releases a decision only if the supremum of the hazard probabilities over the model alternatives that the surveys have not rejected meets a risk criterion (Section 4); "
  "(iii) seven experiments that compare it with static, dynamic and domain-specific baselines at matched decision coverage, under single and combined failures, and that vary the monitoring architecture and the allocation of sensors (Sections 5 to 8); "
  "(iv) a reliability analysis of the survey evidence layer that feeds the utility case, including sensor-fault and common-cause scenarios, the aleatory and epistemic parts of the unsafe-release risk and a global sensitivity analysis (Section 6.1); and "
  "(v) negative results reported alongside the positive ones: continuous point sensors added little to periodic surveys, risk-optimized placement was not consistently better than simple rules, the reliability gate lowered risk mainly by abstaining, and a more elaborate spatial model was less reliable than a simpler one when its geometry assumption failed.", align="justify")
P("**Hypotheses.** The experiments were designed to test three hypotheses, stated before they were run.", align="justify")
for t in (
    "**H1 (dynamic model validity).** Accounting for infrastructure modifications and observation age reduces the conditional unsafe-decision risk relative to static-state probabilistic fusion at matched decision coverage.",
    "**H2 (context-aware change attribution).** Incorporating work-event information improves the identification of expected and unexpected changes without increasing the rate of undetected hazardous states.",
    "**H3 (cross-domain reliability).** A common reliability-gated architecture gives measurable benefits in two structurally different monitoring problems when compared with calibrated, domain-specific baselines.",
):
    H.bullet(doc, t)
P("**Scope.** Everything reported here is a simulation under stated assumptions. The sensor models are thresholded signal models whose parameters are assumptions and were not fitted to field data; no published detection dataset was reproduced. "
  "The scaffold benchmark uses a synthetic structural criterion (a critical member, or two non-critical members of a bay, hazardous), which is not an engineering model and has not been assessed by a structural engineer. "
  "Reliability figures are conditional on the simulated environments and are used to compare methods and to expose failure mechanisms, not to estimate the safety of any real excavation or structure. "
  "No claim is made about hardware, hazardous-area certification or deployment.", align="justify")

# =============================================================================================== 2 Related work
HD("2. Related work: state estimation, digital twins, change detection, mismatch and risk control")
HD("2.1 State estimation and digital twins", 2)
P("Recursive Bayesian estimation of a hidden state from noisy observations is classical, from the linear filter " + C("kalman60") + " to hidden Markov models " + C("rabiner89") + ", and underlies occupancy mapping " + C("elfes89") + ". "
  "Digital twins couple such a model to a physical asset and are reviewed for industry " + C("tao19") + ", manufacturing " + C("kritzinger18") + " and by systematic literature review " + C("jones20") + ". "
  "The twin literature is largely concerned with how the twin is built and kept synchronized. The question taken up here is different: when may a decision rest on the twin, given that its synchronization is never perfect.", align="justify")
HD("2.2 Change detection, concept drift and contextual anomalies", 2)
P("Sequential detection of changes in a process is an old problem " + C("page54", "basseville88") + ", and adaptation to a process whose statistics drift is surveyed as concept drift " + C("gama14") + ". "
  "Anomaly detection distinguishes point, collective and contextual anomalies and notes that context decides whether a deviation is an anomaly " + C("chandola09") + ". A work permit is context in this sense. "
  "The risk in using it is that context can be mistaken for explanation: a change that matches a permit is not thereby safe. The study evaluates this explicitly.", align="justify")
HD("2.3 Probabilistic safety assessment, model uncertainty and fault diagnosis", 2)
P("Safety is quantified as the likelihood and consequence of failure events " + C("kaplan81") + ". Aleatory variability and epistemic uncertainty have to be kept apart " + C("apostolakis90", "helton96", "derkiureghian09", "aven11", "hullermeier21")
  + ", and model uncertainty, where the structural form of the model may be wrong, is best treated by scenarios or envelopes when probabilities for the alternatives are not defensible " + C("droguett08", "flage14", "ferson96", "oberkampf04", "pate96", "aven16") + ". "
  "Fault detection treats a failed or degraded instrument as a hypothesis to be tested against the evidence " + C("isermann05", "venkat03") + ", fault trees and Bayesian networks connect component failures to system failure " + C("bobbio01", "langseth07", "weber12", "ruijters15", "straub10")
  + ", and dependent failures invalidate the multiplication of component probabilities " + C("mosleh91") + ". Life-cycle reliability treats deterioration of structures over time " + C("frangopol03") + "; the present study is concerned with the decision, not with the deterioration model.", align="justify")
HD("2.4 Selective decisions, abstention and risk control", 2)
P("A system that declines to decide when the evidence is weak trades error against coverage " + C("chow70", "hendrickx24") + ", and thresholds can be chosen on calibration data to meet a risk target " + C("bates21")
  + ". Scores are mapped to probabilities by calibration " + C("zadrozny02", "niculescu05", "naeini15") + ". Because a monotone calibration does not change a ranking, an abstention rule can look better than a competitor merely because it abstains more. "
  "The study therefore compares methods at matched decision coverage on risk–coverage curves and reports the coverage next to every risk.", align="justify")
HD("2.5 Sensor placement and structural health monitoring", 2)
P("Where to place sensors under a budget is a combinatorial problem, often attacked by greedy maximization of a monotone submodular objective " + C("nemhauser78", "guestrin05")
  + ", and it has a long history in structural identification " + C("papadimitriou04") + " and structural health monitoring " + C("farrar10") + ". "
  "These methods optimize information about a parameter or a mode shape. The objective here is the unsafe-decision risk of the full monitoring and decision policy.", align="justify")
HD("2.6 The two application domains", 2)
P("The capabilities and limits of GPR and EM locators for utility mapping have been reviewed " + C("metje07", "costello07", "hao12", "lai18") + ", positional accuracy depends on survey set-up " + C("jaw13") + " and depth picking " + C("xie22")
  + ", and detection and tracking can use hyperbola recognition " + C("dou17") + ", multi-sensor tracking " + C("dou16") + " or mapping from partial observations " + C("dou20") + ". The quality of utility information is graded from records to exposure " + C("asce02")
  + ". Scaffold accidents are a recurrent cause of construction injuries, and inspection practice and the condition of the structure at the time of use have been evaluated on construction sites " + C("halperin04") + ". "
  "Work records, permits to work and work orders are standard in both domains, and neither literature, as far as we are aware, treats them as probabilistic evidence about the hazard state while keeping authorization separate from safety.", align="justify")
H.caption(doc, "**Table 1.** Closest existing approaches and the present framework. Yes = addressed; — = not addressed in the abstract or title read; n/e = not examined in detail. A reading of the cited work, not an audit of it.", keep_next=True)
H.table(doc, [["Approach", "Dynamic state", "Work-record context", "Asynchronous coverage", "Sensor-health modelling", "Reliability gate over model alternatives", "Two-domain evaluation"],
              ["Digital twins (Tao et al., 2019; Jones et al., 2020)", "Yes (synchronization)", "n/e", "n/e", "n/e", "—", "—"],
              ["Kalman and hidden-Markov filtering (Kalman, 1960; Rabiner, 1989)", "Yes", "—", "Yes (by construction)", "—", "—", "—"],
              ["Change detection and concept drift (Page, 1954; Gama et al., 2014)", "Yes", "—", "—", "—", "—", "—"],
              ["Contextual anomaly detection (Chandola et al., 2009)", "n/e", "Yes (context)", "n/e", "—", "—", "—"],
              ["Selective prediction and risk control (Chow, 1970; Bates et al., 2021)", "—", "—", "—", "—", "Partly (calibrated threshold)", "—"],
              ["Sensor placement (Guestrin et al., 2005; Papadimitriou, 2004)", "—", "—", "—", "n/e", "—", "—"],
              ["Multi-sensor utility location (Dou et al., 2016)", "Partly (tracking)", "—", "—", "—", "—", "—"],
              ["**This work (simulation)**", "Yes", "Yes (kept separate from hazard)", "Yes", "Yes (assumed diagnostic)", "Yes (supremum, validity selection)", "Yes (synthetic scaffold)"]],
        widths=[1.7, 0.7, 0.8, 0.8, 0.8, 1.0, 0.8], size=6.6)
P("The novelty claimed is the combination and its reliability analysis, not a new filtering algorithm: the estimator is a standard hidden-Markov filter, and the gate is a supremum over a set of alternatives with a likelihood-based rejection rule. "
  "What is new is the treatment of the decision, not the estimate, as the object of reliability analysis under change, the explicit separation of authorization from hazard, and the comparison with static and domain-specific baselines at matched coverage in two domains.", align="justify")
