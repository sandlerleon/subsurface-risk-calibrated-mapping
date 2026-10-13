# -*- coding: utf-8 -*-
"""RESS manuscript, part A: title page, Introduction, Related work, Reliability problem formulation, Methods, Experimental design.
Exec'd by build_manuscript_ress.py (shares its namespace: H, doc, P, HD, FIGX, C, CN, K, R, R4, R5 ...)."""

# =============================================================================================== title page
P("**" + TITLE + "**", align="center", size=15, space_after=10)
P("Leon Sandler", align="center", size=12, space_after=0)
P("Independent Researcher, Northbrook, Illinois, USA", align="center", size=10.5, space_after=0)
P("ORCID: 0009-0007-4584-808X • Corresponding author: sandler.leon@gmail.com", align="center", size=10.5, space_after=12)
P("Software: %s (archived at https://doi.org/%s). Preprint: https://doi.org/%s." % (REPO, SW, PP), align="center", size=9.5, space_after=14)
HD("Abstract", 2)
P(ABSTRACT_TEXT, align="justify")
AB_WORDS = len(ABSTRACT_TEXT.split())
P("**Keywords:** reliability of decision support; model uncertainty; aleatory and epistemic uncertainty; sensor fusion; fault detection; selective decision-making; underground utility mapping", size=10.5)
doc.add_page_break()
BODY[0] = True

# =============================================================================================== 1 Introduction
HD("1. Introduction")
P("Many safety-critical decisions are taken on incomplete, heterogeneous and sometimes faulty sensor evidence. A decision-support system that turns such evidence into a recommendation is itself a system whose reliability must be assessed: "
  "it can fail because the evidence is weak, because an instrument has failed without announcing it, because its internal model of the world is wrong, or because its decision threshold was set on conditions that no longer hold "
  + C("zio09", "zio18") + ". The probabilistic safety assessment literature has long insisted that the uncertainty behind such failures be separated into the part that is random within a model and the part that is ignorance about the model "
  + C("apostolakis90", "helton96", "derkiureghian09", "aven11") + ", and the fault-diagnosis literature has treated the detection of faulty sensors as a precondition of trustworthy inference " + C("isermann05", "venkat03") + ".", align="justify")
P("Excavation near buried utilities is a concrete and consequential instance. Before a mechanical excavator is released onto a stretch of ground, someone must decide whether a buried utility could lie within its reach. "
  "The evidence comes from ground-penetrating radar (GPR), an electromagnetic (EM) locator, records and an anchor such as a manhole, and its quality depends on soil, depth, utility material and the health of the instruments "
  + C("metje07", "costello07", "doolittle95", "annan09") + ". Strikes on buried utilities cause injury, service loss and cost " + C("metje15", "makana20") + ". "
  "A utility map that marks only what was detected invites the reader to treat silence as clearance; whether the map can say that it does not know is a reliability property of the decision-support system, not only an accuracy property of the sensors.", align="justify")
P("Two features make this setting a useful test of reliability methodology. First, the safety failure event is well defined: a segment is released for mechanical excavation although a utility lies within its excavation envelope. "
  "Second, a decision layer can fail in ways that a classification score does not show. It can be accurate on average and still release segments it should not; it can refuse to decide so often that it is useless; "
  "and a more elaborate spatial model, which improves accuracy under the conditions it was designed for, can make its output more confidently wrong when its structural assumptions are violated.", align="justify")
P("This study investigates the reliability of probabilistic sensor-fusion decisions for underground utility mapping under incomplete observations, sensor degradation, and structural model mismatch. "
  "Rather than treating classification accuracy as the primary measure of system performance, we examine the probability of unsafe clearance, the relationship between residual risk and operational coverage, and the ability of an abstention policy to prevent unsupported absence decisions. "
  "Using a simulation-based case study involving ground-penetrating radar and electromagnetic observations, we compare alternative fusion and decision policies under matched survey conditions. "
  "Particular attention is given to the distinction between stochastic variability and uncertainty arising from incorrect model assumptions. "
  "The objective is to identify conditions under which increased model complexity improves decision reliability and conditions under which it creates false confidence.", align="justify")
P("The contributions are: (i) a formal safety failure event and three reliability metrics, with their denominators and their relation to the engineering outcomes of earlier versions of this work (Section 3.1); "
  "(ii) a decomposition of unsafe-release risk into aleatory variability and epistemic uncertainty over an explicit set of sensor parameters and five structural models of the geometry, without assigning probabilities to the structural models (Sections 3.3, 5.2 and 6.5); "
  "(iii) a conceptual failure decomposition, evaluated by fault scenarios that combine sensor-health states, model mismatch and a common-cause case, with an attribution of simulated unsafe releases to its branches (Sections 3.4 and 6.3); "
  "(iv) seven release policies, including an expected-loss policy and robust policies that release only if an upper bound over an uncertainty set is acceptable, compared with calibrated-abstention and oracle baselines on reliability–coverage curves with intervals over independent simulated networks (Sections 3.2, 5.3, 6.1 and 6.2); "
  "(v) a component ablation at equal released coverage and a global sensitivity analysis that ranks the drivers of unsafe release (Sections 6.6 and 6.7); and (vi) negative results reported in the main text: a model with lateral tracking that is more reliable in the matched case is much less reliable when a parallel utility is present, and no policy dominates in all conditions (Section 6.4).", align="justify")
P("**Scope.** Everything reported here is a simulation under stated assumptions. The sensor model is a thresholded signal-to-noise model whose parameters were chosen to give a plausible range of detectability and were not fitted to field data, and no published detection-versus-depth dataset was reproduced (Section 5.6). "
  "The reliability figures are therefore conditional on the simulated environment and are used to compare policies and to expose failure mechanisms; they are not estimates of the safety of any real excavation.", align="justify")

# =============================================================================================== 2 Related work
HD("2. Related work")
HD("2.1 Probabilistic safety assessment and model uncertainty", 2)
P("Safety is quantified in probabilistic risk assessment as the likelihood and consequence of failure events " + C("kaplan81") + ". Aleatory uncertainty is the variability of a random process inside a model; epistemic uncertainty is lack of knowledge about the model or its parameters "
  + C("apostolakis90", "derkiureghian09", "helton96") + ". Treating the two with a single probability can hide the second, and methods that propagate ignorance and variability differently have been argued for " + C("ferson96", "oberkampf04", "pate96")
  + ". Model uncertainty, the possibility that the structural form of the model is wrong, is harder still, because probabilities for structural alternatives are rarely defensible " + C("droguett08", "flage14") + ". "
  "When they are not, a scenario or envelope treatment states results for each alternative and for the worst credible case, and conservative decisions must be justified against an explicit criterion " + C("aven16") + ". The present study follows this line: parameters are drawn from stated ranges, structural alternatives are scenarios, and no averaged risk across them is reported.", align="justify")
HD("2.2 Fault detection, sensor health and dependent failures", 2)
P("Fault detection and diagnosis treats an instrument that has failed or degraded as a hypothesis to be tested against the evidence, with model-based, process-history and qualitative approaches " + C("isermann05", "venkat03") + ". "
  "Bayesian networks and fault trees are standard ways to connect component failures to system failure " + C("bobbio01", "langseth07", "weber12") + ", and the fault tree itself has an extensive literature of modelling and analysis methods " + C("ruijters15") + ". "
  "A recurrent difficulty is dependence: failures that share a cause, such as a soil that degrades two sensors at once, invalidate the multiplication of component probabilities " + C("mosleh91") + ". "
  "The study therefore evaluates failure combinations, including a common-cause case, by simulation instead of composing independent probabilities (Section 6.3).", align="justify")
HD("2.3 Selective decisions, abstention and calibrated risk control", 2)
P("A classifier with a reject option declines to decide when the evidence is weak, trading error against coverage " + C("chow70", "hendrickx24") + "; the three-state output of the present layer (present, absent, unverified) is of this kind. "
  "The trade-off is characterised by a risk–coverage curve, and a threshold can be chosen on calibration data so that a risk target is met " + C("bates21") + ". Calibration methods map scores to probabilities " + C("zadrozny02", "niculescu05", "naeini15") + " "
  "and probabilistic forecasts are scored by proper scoring rules " + C("gneiting07a", "gneiting07b", "brier50") + ". Because a monotone calibration does not change a ranking, an abstention rule can look better than a competitor merely because it abstains more; "
  "the study therefore compares policies at equal released coverage on reliability–coverage curves and, separately, at a calibrated risk target. Distinguishing aleatoric from epistemic uncertainty is also central to modern machine learning " + C("hullermeier21") + ", which is the same distinction in another vocabulary.", align="justify")
HD("2.4 Underground utility mapping and operator decision support", 2)
P("The capabilities and limits of GPR and EM locators for utility mapping have been reviewed " + C("metje07", "costello07", "hao12", "lai18") + ". Positional accuracy depends on survey set-up " + C("jaw13") + " and on velocity and depth picking " + C("xie22") + "; detection and tracking can use automatic hyperbola recognition " + C("dou17")
  + ", multi-sensor tracking with an extended Kalman filter " + C("dou16") + ", or mapping from partial observations " + C("dou20") + "; and the quality of utility information is graded from records to exposure " + C("asce02") + ". "
  "These works improve detection or location. They do not address when the output should say that it does not know, nor how the decision layer fails when its own model is wrong. "
  "Automation that is trusted beyond its reliability is a known source of misuse " + C("parasuraman97", "lee04") + ", which is why a decision-support output should convey the limits of its evidence. Table 1 positions the present work against the closest existing approaches.", align="justify")
H.caption(doc, "**Table 1.** Closest existing approaches and the present layer. Yes = addressed; — = not described in the abstract or title read; n/e = not examined in detail. A reading of the cited work, not an audit of it.", keep_next=True)
H.table(doc, [["Approach", "Spatial tracking", "Sensor-health modelling", "Detection-limit awareness", "Calibrated abstention", "Robustness to model mismatch"],
              ["Occupancy grids (Elfes, 1989)", "Yes (grid cells)", "—", "through sensor models", "—", "—"],
              ["Reject-option decisions (Chow, 1970)", "—", "—", "—", "Yes (posterior threshold)", "—"],
              ["GPR-EMI fusion, landmines (Stanley et al., 2002)", "—", "n/e", "n/e", "n/e", "n/e"],
              ["Fusion of correlated decisions, GPR (Tesfamariam et al., 2012)", "—", "—", "n/e", "n/e", "n/e"],
              ["Multi-sensor utility location, extended Kalman filter (Dou et al., 2016)", "Yes (tracks across scan lines)", "—", "—", "—", "—"],
              ["Utility mapping from partial observations (Dou et al., 2020)", "Yes (3D mapping)", "n/e", "n/e", "n/e", "n/e"],
              ["**This work (simulation)**", "Yes (along and across, grid filter)", "Yes (assumed diagnostic)", "Yes (capability zones)", "Yes (three states; risk-controlled baselines)", "Evaluated (parameter sets, structural alternatives, supremum rule)"]],
        widths=[2.0, 0.95, 0.9, 0.9, 0.95, 1.0], size=7)
P("The novelty claimed is the reliability analysis of a decision policy for subsurface utility surveys, not a new filtering algorithm: the lateral filter is a standard grid filter whose tracking function overlaps with that of " + CN("dou16") + ". "
  "What is new is the treatment of the policy as a system with a defined failure event, the separation of aleatory and epistemic contributions to that failure, the evaluation of failure combinations and of structural mismatch, and the comparison of abstention policies at equal coverage.", align="justify")

# =============================================================================================== 3 Formulation
HD("3. Reliability problem formulation")
HD("3.1 Safety failure event and reliability metrics", 2)
P("A corridor is divided into segments of 5 m along a tracked alignment. For segment *i* let *A*_{i} = 1 if the segment is released for mechanical excavation under the decision policy, and *U*_{i} = 1 if an actual utility intersects the modelled excavation envelope (a footprint of ±1 m around the reference alignment). The safety failure event is", align="justify")
H.equation(doc, H.SUB(H.V("F"), H.V("i")) + H.T(" = {") + H.SUB(H.V("A"), H.V("i")) + H.T(" = 1, ") + H.SUB(H.V("U"), H.V("i")) + H.T(" = 1}"), 1)
P("The unsafe-release probability is the joint probability that a segment is released and occupied; it is the product of the conditional false-clearance risk and the release coverage:", align="justify")
H.equation(doc, H.V("P") + H.T("(") + H.V("F") + H.T(") = ") + H.V("P") + H.T("(") + H.V("A") + H.T(" = 1, ") + H.V("U") + H.T(" = 1) = ") + H.V("P") + H.T("(") + H.V("U") + H.T(" = 1 | ") + H.V("A") + H.T(" = 1) ") + H.V("P") + H.T("(") + H.V("A") + H.T(" = 1)"), 2)
P("The conditional decision reliability in the simulated environment is", align="justify")
H.equation(doc, H.SUB(H.V("R"), H.T("decision")) + H.T(" = 1 − ") + H.V("P") + H.T("(") + H.V("U") + H.T(" = 1 | ") + H.V("A") + H.T(" = 1)"), 3)
P("This is the share of released segments that are clear in the simulation. It is not the probability that an actual excavation will be accident-free, which depends on excavation practice, locating before digging and operator behaviour, none of which is modelled. "
  "Table 2 gives the three metrics, their denominators and their correspondence with the quantities reported in earlier versions of this work; the correspondence is exact because the denominators and event definitions match, and no other earlier quantity is relabelled.", align="justify")
H.caption(doc, "**Table 2.** Reliability metrics. All are cell-weighted over soil-by-utility cells (the weights are assumptions, Section 5.1) and computed from per-corridor counts, with cluster-bootstrap intervals over corridors.", keep_next=True)
H.table(doc, [["Metric", "Definition", "Denominator", "Interpretation", "Earlier name"],
              ["Unsafe-release probability", "P(A = 1, U = 1)", "all segments", "joint frequency of unsafe release", "modelled intersections per km / 200"],
              ["Conditional false-clearance risk", "P(U = 1 | A = 1)", "released segments", "risk among released segments", "false clearance"],
              ["Release coverage", "P(A = 1)", "all segments", "fraction released for excavation review", "released share"],
              ["Unverified share", "P(call = unverified)", "all segments", "verification burden", "unverified share"]],
        widths=[1.5, 1.2, 1.0, 1.7, 1.4], size=8)
HD("3.2 Loss model and release policies", 2)
P("Three actions are available for a segment: release for mechanical excavation, verify (a trial pit or an equivalent independent check) or restrict (hold or reroute). With *p*_{i} = *P*(*U*_{i} = 1 | *D*_{i}) the posterior probability that a utility lies in the envelope given evidence *D*_{i}, a simplified loss model is", align="justify")
H.equation(doc, H.V("L") + H.T("(release) = ") + H.SUB(H.V("p"), H.V("i")) + H.SUB(H.V("C"), H.T("miss")) + H.T(",   ") + H.V("L") + H.T("(verify) = ") + H.SUB(H.V("C"), H.T("verify")) + H.T(" + ") + H.SUB(H.V("p"), H.V("i")) + H.SUB(H.V("C"), H.T("hold")) + H.T(",   ") + H.V("L") + H.T("(restrict) = ") + H.SUB(H.V("C"), H.T("hold")), 4)
P("where a pit that finds the utility leads to a hold, so that verification costs the pit plus the hold with probability *p*_{i}. The cost values are scenario assumptions (a miss costs US$5,000 per consequence unit of the utility class, a hold US$1,000 per segment and a pit US$400 plus US$200 per metre of class mid-depth), and the expected-loss policy picks the action of least expected loss. "
  "The costs set the break-even probabilities (for a power duct, release is preferred below 0.013), and every cost is an assumption; they are used only to define a decision-theoretic policy and to compare policies, not to claim a real cost.", align="justify")
P("Seven release policies and four baselines are compared (Table 3). P1 releases when the posterior is at most 0.10. P2 adjusts the threshold to sensor quality: it requires 0.10 in zone A (fused detection capability at least 0.9), 0.02 in zone B (0.3 to 0.9) and never releases in zone C (below 0.3) or when an on-site reference check fails. "
  "P3 minimises expected loss. The robust policies release only if an upper bound over an uncertainty set is acceptable:", align="justify")
H.equation(doc, H.T("release only if ") + H.SUB(H.T("sup"), H.T("(") + H.V("θ") + H.T(", ") + H.V("M") + H.T(") ∈ ") + H.V("Ω")) + H.T(" ") + H.V("P") + H.T("(") + H.SUB(H.V("U"), H.V("i")) + H.T(" = 1 | ") + H.SUB(H.V("D"), H.V("i")) + H.T(", ") + H.V("θ") + H.T(", ") + H.V("M") + H.T(") ≤ ") + H.SUB(H.V("τ"), H.T("safety")), 5)
P("where Ω is an explicit set of parameter variants θ and structural alternatives *M* of the filter (Section 5.2) and τ_{safety} equals the zone-specific threshold of P2. "
  "The threshold is a design criterion, not an excavation safety standard: 0.10 is the highest probability of an occupied envelope that the policy tolerates before it asks for verification, chosen so that, in the matched model, the conditional risk of the released set is of the order of one percent; any other value moves the policy along its reliability–coverage curve (Section 6.1). "
  "P4 takes the supremum over parameter variants, P5 over parameter variants and structural alternatives, P6 applies the expected-loss rule to the P5 bound, and P7 adds the most conservative structural alternative, the probability that a utility lies anywhere in the ±5 m swath.", align="justify")
rows = [["Label", "Policy or baseline", "Role"],
        ["B1", "Standard Bayesian fusion, per segment, fixed 0.5 threshold, no abstention", "ordinary probability fusion"],
        ["B2", "Continuity-aware 1D filter with the blind-cell rule (version 1.0 framework)", "simpler continuity model with abstention"],
        ["RC", "Calibrated abstention: score isotonic-calibrated on separate networks; release if calibrated probability ≤ 2% (fusion, 1D, health-aware, quality-adjusted and robust scores)", "isolates the benefit of abstention itself"],
        ["P1", "Health-aware lateral filter, fixed threshold 0.10", "sensor-health-aware fusion"],
        ["P2", "P1 with capability-zone thresholds and reference check", "sensor-quality-adjusted policy"],
        ["P3", "Expected-loss policy on the P1 probability", "decision-theoretic policy"],
        ["P4", "Robust over parameter variants (zone thresholds)", "parameter uncertainty only"],
        ["P5", "Robust over parameter variants and structural alternatives (zone thresholds)", "proposed reliability policy"],
        ["P6", "Expected-loss rule on the P5 bound", "robust decision-theoretic policy"],
        ["P7", "P5 plus the full-swath alternative", "most conservative envelope"],
        ["B5", "Oracle: true sensor parameters, true soil, true health states, fixed threshold", "unattainable upper reference"]]
H.caption(doc, "**Table 3.** Policies and baselines. P1 is the sensor-health-aware baseline; B5 is not attainable because it knows the true parameters and health states.", keep_next=True)
H.table(doc, rows, widths=[0.5, 4.2, 1.8], size=7.8)
HD("3.3 Uncertainty decomposition", 2)
P("Aleatory uncertainty is random variability within a specified model: measurement noise, depth variability, stochastic degradation and random alignment deviations. Epistemic uncertainty concerns the model itself: soil attenuation, the continuity assumption, unmodelled branching, the likelihoods of sensor health and the transfer of calibration to unfamiliar sites. "
  "Let θ denote uncertain parameters and *M* a structural model. When defensible probabilities for (θ, *M*) exist, the failure probability given the evidence *D* is", align="justify")
H.equation(doc, H.V("P") + H.T("(") + H.V("F") + H.T(" | ") + H.V("D") + H.T(") = ") + H.NARY("∑", H.V("M"), H.T("") ) + H.NARY("∫", H.T(""), H.V("P") + H.T("(") + H.V("F") + H.T(" | ") + H.V("D") + H.T(", ") + H.V("θ") + H.T(", ") + H.V("M") + H.T(") ") + H.V("p") + H.T("(") + H.V("θ") + H.T(", ") + H.V("M") + H.T(" | ") + H.V("D") + H.T(") d") + H.V("θ")), 6)
P("We do not have such probabilities for the structural models, and assigning arbitrary weights merely to obtain a single averaged risk would conceal the result that matters, which is how large the risk is under each structure. "
  "The study therefore uses the parameter envelope as a distribution (stated ranges, independent log-uniform or uniform draws) within each structural model, and reports the structural models as scenarios with an explicit worst case,", align="justify")
H.equation(doc, H.SUB(H.V("P"), H.T("F")) + H.SUP(H.T(""), H.T("worst")) + H.T(" = ") + H.SUB(H.T("sup"), H.T("(") + H.V("θ") + H.T(", ") + H.V("M") + H.T(") ∈ ") + H.V("Ω")) + H.T(" ") + H.V("P") + H.T("(") + H.V("F") + H.T(" | ") + H.V("θ") + H.T(", ") + H.V("M") + H.T(")"), 7)
P("estimated as a high quantile and the maximum over the sampled parameter draws for each structural model. Within a structural model the variance of the unsafe-release probability of a simulated network is decomposed by the law of total variance into the aleatory part (variation between independent networks of the same parameter draw) and the epistemic part (variation of the expected value across parameter draws):", align="justify")
H.equation(doc, H.V("Var") + H.T("(") + H.V("Y") + H.T(") = ") + H.V("E") + H.SUB(H.T(""), H.V("θ")) + H.T("[") + H.V("Var") + H.T("(") + H.V("Y") + H.T(" | ") + H.V("θ") + H.T(")] + ") + H.V("Var") + H.SUB(H.T(""), H.V("θ")) + H.T("(") + H.V("E") + H.T("[") + H.V("Y") + H.T(" | ") + H.V("θ") + H.T("])"), 8)
P("with *Y* the unsafe-release probability of one simulated network. The epistemic term is corrected for the sampling variance of its estimate. The aleatory share depends on the size of the simulated network and is reported for the network size used (Section 5.2).", align="justify")
HD("3.4 Failure mechanisms and system-level reliability", 2)
P("The top event is unsafe utility clearance. Figure 1a decomposes it conceptually into four branches. *Detection failure*: weak signal at depth (the segment lies in capability zone B) or a miss inside the capable zone. "
  "*Model failure*: an unmodelled branch or parallel utility, sensor parameters that differ from those assumed, or an unseen soil. *Decision failure*: a threshold that is too permissive for the actual conditions, visible as a predicted risk that is below the observed risk among released segments. "
  "*Verification failure*: a sensor fault that the diagnostic does not flag, or an unseen soil that the reference check does not detect. The decomposition is conceptual and not a complete Boolean fault tree: the branches are not independent and share causes such as soil, sensor condition and geometry. "
  "The logical conditions are defined operationally for the simulation: a segment is attributed to *verification failure* if its corridor has a failed or degraded sensor whose state the diagnostic did not report, or lies in an unseen soil that the reference check did not flag; otherwise to *model failure* if it is intersected by an unmodelled branch; "
  "otherwise to *detection failure* in the marginal capability range or inside the capable zone. The order is a convention and the categories are exclusive by construction (Section 6.3). Decision failure is measured by the calibration gap among released segments. "
  "To avoid multiplying component probabilities whose independence is not established, failure combinations are simulated jointly and the conditional risk is evaluated for each combination of sensor-health states and geometry model, *P*(*F* | *H*_{G}, *H*_{E}, *M*), where *H*_{G} and *H*_{E} are the GPR and EM health states and *M* the geometry model:", align="justify")
rows = [["Scenario", "GPR", "EM", "Geometry", "Other"],
        ["Baseline", "healthy", "healthy", "as assumed", "—"],
        ["Failure A", "failed, flagged", "healthy", "as assumed", "—"],
        ["Failure B", "failed, not flagged", "healthy", "as assumed", "—"],
        ["Failure C", "healthy", "degraded (6 dB)", "incorrect (bends, parallel utility)", "—"],
        ["Common cause D", "degraded", "degraded", "incorrect (bends, parallel utility, branch)", "soil twice as lossy as assumed"],
        ["B with mismatch", "failed, not flagged", "healthy", "incorrect (bends, parallel utility, branch)", "—"]]
FIGX(doc, os.path.join(FIG5, "fig22_failure_tree.png"), 6.6, "**Fig. 1.** (a) Conceptual decomposition of the top event, unsafe clearance, into detection, model, decision and verification failure. (b) Attribution of the simulated unsafe releases of the sensor-quality-adjusted policy P2 to mechanisms (exclusive categories assigned by the priority order of Section 3.4); the figure at the end of each bar is the unsafe-release probability P(F) of the scenario.",
     alt="Failure tree and attribution of unsafe releases")
H.caption(doc, "**Table 4.** Failure combinations simulated jointly (the other scenarios are listed in Section 5.1).", keep_next=True)
H.table(doc, rows, widths=[1.2, 1.2, 1.1, 2.2, 1.6], size=8)

# =============================================================================================== 4 Methods
HD("4. Methods")
P("All results come from three Python files (NumPy, SciPy, scikit-learn, Matplotlib): SubSurface_MC.py (version 1.0 simulation), SubSurface_v4.py (lateral tracking, sensor health, zones, mismatch and envelope experiments) and SubSurface_v5.py (the reliability analyses of this paper), "
  "run with a fixed seed (%d). Every random stream is derived from the seed, a scenario tag and a block index, so that results do not depend on the number of processes. The built-in self-tests pass (%d + %d + %d tests); they check code against its own mathematics, not against reality." % (
      R4["meta"]["seed"], len(R["selftests"]), len(R4["selftests"]), len(R5["selftests"])), align="justify")
HD("4.1 Simulated corridors, sensors and truth", 2)
P("A corridor holds one utility of one type buried at one depth in one soil, tracked over 100 segments of 5 m. Five seen soils (dry sand, dry loam, moist loam, clay, rubble fill) and seven utility types (PE/PVC water, cast-iron water, plastic sewer, concrete sewer, power duct, telephone duct, dielectric fibre) define 35 cells, weighted by an assumed network share with the soils equally weighted; "
  "two unseen soils (wet clay and saline fill) are used only as test conditions. For band *b* (250 or 600 MHz) the signal-to-noise ratio in segment *k* is", align="justify")
H.equation(doc, H.SUB(H.V("S"), H.V("b,k")) + H.T(" = ") + H.SUB(H.V("B"), H.V("b")) + H.T(" + ") + H.SUB(H.V("ρ"), H.V("u")) + H.T(" − ") + H.SUB(H.V("a"), H.V("b")) + H.T("(") + H.V("s") + H.T(") ") + H.V("d") + H.T(" − 40 log") + H.SUB(H.T(""), H.T("10")) + H.T("(max(2") + H.V("d") + H.T(", 1)) − ")
           + H.SUB(H.V("L"), H.T("lat")) + H.T(" + ") + H.SUB(H.V("z"), H.T("run,") + H.V("b")) + H.T(" + ") + H.SUB(H.V("z"), H.T("seg,") + H.V("b,k")), 9)
P("with system budget *B*_{b} (70 and 74 dB), utility reflectivity *ρ*_{u}, two-way soil attenuation *a*_{b}(*s*), depth *d*, a lateral penalty *L*_{lat} that depends on the offset between the utility and the survey pass, run-level noise *z*_{run} (3 dB, shared along a corridor) and segment-level noise *z*_{seg} (4 to 7 dB by soil); the bands are correlated (0.7). "
  "A detection occurs when *S* exceeds 8 dB; clutter adds a soil-dependent false-detection probability. The EM locator couples to a utility with a class-specific probability drawn once per corridor. Every value is an assumption, listed in the assumptions register of the repository and in the Supplementary Material.", align="justify")
P("The truth process puts the utility on the alignment at the anchor and lets it leave, return, shift sideways or drift. Five structural models of the geometry are used as scenarios: L0, straight (the filter’s assumption); L1, curved with a lateral drift; "
  "L2, a piecewise-linear path with abrupt bends (legs of 8 to 25 segments, slopes up to 0.25 m per segment) that is not a Markov chain on the filter’s grid; L3, bends plus a second utility 2 to 5 m away that also returns signals; and L4, bends, a parallel utility and a branch that leaves at a random position and adds to the truth where it lies on the excavation footprint. "
  "The filter never knows which geometry a corridor has. The truth label is that a modelled utility lies within 1 m of the reference alignment.", align="justify")
HD("4.2 Fusion filter, sensor health and capability zones", 2)
P("The belief that the utility is absent or at one of 21 lateral offsets (−5 m to +5 m in 0.5 m steps) is propagated along the corridor with small fixed rates for ending, return, shifting and drifting, and updated by each sensor and pass through likelihoods that depend on soil, utility class and offset; the probability that the utility lies on the excavation footprint is the sum of the belief within 1 m. "
  "Survey is one centre pass or three parallel passes (−3, 0, +3 m). The EM coupling is a persistent per-corridor state, so that repeated EM non-detections are not counted as independent evidence of absence. "
  "Each instrument is healthy, degraded (6 dB loss) or failed (clutter only); an imperfect diagnostic reports the state, and a sensor flagged as failed contributes no evidence, a sensor flagged as degraded uses the degraded likelihood and an unflagged failure is treated as healthy (the assumed diagnostic rates are given in the Supplementary Material). "
  "The capability of a segment is the closed-form probability that at least one available sensor produces a true signal detection at the estimated depth (10% velocity error), and defines zones A (at least 0.9), B (0.3 to 0.9) and C (below 0.3). "
  "An on-site reference check passes a reference target of the segment’s class 20 times and compares the detection rate with the rate the filter predicts, by an exact binomial test (α = 0.01); in this study it is evaluated against the true sensor parameters of the world, so that it can detect a mismatch of the parameters as well as an unseen soil.", align="justify")
HD("4.3 Uncertainty sets of the robust policies and the oracle", 2)
P("The filter-side set Ω used by P4 to P7 is explicit and is an assumption of the designer. Its parameter variants are the nominal sensor model; soil attenuation doubled; sensor budgets reduced by 3 dB; EM coupling halved; and attenuation doubled together with the 3 dB reduction. "
  "Its structural alternatives are a filter with a much less stable geometry model (loss 0.05, shift 0.03 and drift 0.10 per segment); a filter without the anchor; and the one-dimensional on-alignment model of version 1.0. P7 adds the probability that a utility lies anywhere in the ±5 m swath. "
  "All members are run on the same observations and the policy uses the pointwise supremum of their probabilities. The set does not contain every condition of the test worlds: the test envelope (Section 5.2) allows attenuation to be a quarter of the assumed value and as much as four times it, thresholds and budgets to vary by ±3 dB, and the geometry to be one of five structures, and the set cannot represent an unflagged sensor failure. "
  "The oracle B5 runs the filter with the true parameters, the true soil and the true health states as flags.", align="justify")

# =============================================================================================== 5 Experimental design
HD("5. Experimental design")
HD("5.1 Scenarios, replicates and denominators", 2)
P("Twelve scenarios combine sensor health, geometry and parameter mismatch (Table 4 and Table 5). Each is simulated as 10 independent networks (blocks) of 40 corridors per soil-by-utility cell (1,400 corridors, 140,000 segments, 700 km of corridor per network for the seen soils); "
  "the conditional risks and coverages are cell-weighted means over the networks, intervals are 95% percentile intervals of 300 cluster-bootstrap resamples of whole corridors within each cell (Efron, 1979; Field and Welsh, 2007), "
  "and curves are averaged over networks with 95% t-intervals over the 10 independent networks, never over adjacent segments. All policies see the same simulated detections in a scenario (paired comparison).", align="justify")
rows = [["Scenario", "Description"]] + [[n.replace("_", " "), SC5[n]["label"]] for n in SC5_ORDER]
H.caption(doc, "**Table 5.** The twelve scenarios.", keep_next=True)
H.table(doc, rows, widths=[1.9, 4.6], size=8)
HD("5.2 Uncertainty experiment", 2)
P("The epistemic envelope draws the true sensor parameters from the ranges of version 1.1 (40 draws): attenuation of each seen soil multiplied by a log-uniform factor between 0.25 and 4, detection threshold and system budget each varied by ±3 dB, spreading coefficient 30 to 50, EM coupling multiplied by 0.5 to 1.5; the filters keep the nominal parameters, and the reference check sees the true parameters. "
  "Each draw is crossed with the five structural models and simulated as 3 independent networks of 14 corridors per cell (490 corridors per network), giving 600 networks. The structural models are scenarios and are never averaged. "
  "The envelope is a stated assumption about how far the true parameters might be from the assumed ones, and is wider than the one-at-a-time sensitivity analysis of earlier versions.", align="justify")
HD("5.3 Reliability–coverage curves, dominance and calibrated abstention", 2)
P("For each score the segments are ordered from lowest to highest score and released from the bottom; the conditional risk is evaluated at every released coverage from 1% to 90%. Each curve is computed per independent network and averaged. "
  "Two curves are compared at each coverage by the paired difference over networks; A is said to be better where the 95% t-interval of the difference lies below zero, worse where it lies above, and indistinguishable otherwise, and the share of the common coverage range in each state is reported, together with whether A is nowhere worse. "
  "The calibrated-abstention baselines are fitted on 8 separate calibration networks of the baseline scenario: the score is isotonic-calibrated against the outcome and a segment is released if its calibrated probability of a utility is at most 2%.", align="justify")
HD("5.4 Ablation and verification prioritisation", 2)
P("Components of the full policy P5 are removed one at a time and the conditional risk is compared at equal released coverage, both on a common grid (10%, 20%, 30%, 40%) and at the released coverage of P5 itself in each scenario: sensor-health information (health-unaware filters and zones), spatial continuity (a near-memoryless filter with a hazard of 0.5 per segment), "
  "structural uncertainty (parameter variants only), parameter uncertainty (structural alternatives only), capability thresholds (ranking by the bound without zone-specific scaling or guard) and robustness altogether (the ranking of P2). "
  "Verification prioritisation is evaluated separately: segments left unverified by P5 are verified with a budget of pits (2% to 40% of all segments) in random order, lowest probability first, or highest value of information, and the share of the corridor cleared by pits is compared.", align="justify")
HD("5.5 Global sensitivity analysis", 2)
P("Eight parameters are sampled with a Latin hypercube design (McKay et al., 1979; 320 points) over stated ranges: soil attenuation multiplier (log-uniform, 0.25 to 4), sensor sensitivity offset (±4 dB), probability that a failed sensor is flagged (0 to 1), sensor failure prevalence (0 to 0.30; 20% of sensors are degraded), lateral displacements (0 to 3 per 100 m), "
  "share of corridors with a parallel utility and branch (0 to 1), share of corridors in unseen soils (0 to 0.5) and the hazard that the utility leaves the alignment (0.05 to 1.0 per 100 m, log-uniform). Each design point is simulated as four sub-worlds (straight or parallel-and-branch, seen or unseen soils) of two independent networks each, mixed by the design weights. "
  "A gradient-boosting surrogate (200 trees of depth 3, learning rate 0.07, subsample 0.8, fitted to the 320 design points; hold-out R\u00b2 on a random 20% of the points) is fitted to the unsafe-release probability and the conditional risk of each policy. The Sobol indices are not computed from the Latin hypercube points themselves: they are estimated by Monte Carlo on the fitted surrogate, using an independent random design in the unit hypercube of the (transformed) parameters, with two independent matrices A and B of 4,096 samples each and, for each parameter, a matrix AB that takes that parameter from B and the others from A; the first-order index uses the estimator of Saltelli et al. (2010) and the total-order index that of Jansen (1999) (see also Sobol, 2001). Their stability is checked by refitting the surrogate on 60 bootstrap resamples of the design points and re-estimating the indices, which also gives the intervals and the share of refits in which each parameter is ranked first. "
  "The indices are interpretable because the parameters are sampled independently by construction, which is an assumption: in reality soil conditions, sensor performance and model error may be correlated. The surrogate’s hold-out R² is reported, and indices are used only where the surrogate is adequate.", align="justify")
HD("5.6 Physical plausibility and the absence of external validation", 2)
EP = R4["external_plausibility"]
P("**No published measurement of GPR or EM detection probability against known utility depth and soil was reproduced in this study.** The detection curves are therefore outputs of an assumed model, and the paper is a methodological demonstration of the reliability analysis of a decision policy, not a predictive utility-detection model. "
  "Two independent plausibility checks are reported, neither of which is a validation. First, the low-loss relation between conductivity and attenuation reproduces a worked example given by the US Environmental Protection Agency (US EPA, n.d.): for 100 mS/m and a relative permittivity of 20 it gives %.1f dB/m against the %.0f dB/m published. "
  "Second, the one-way attenuations implied by the assumed values at 250 MHz (%.2f dB/m for dry sand, %.1f dB/m for clay, %.1f dB/m for wet clay) lie within the tabulated range for clays but well above the tabulated value for dry sand; the table states no frequency and no primary source, and the assumed attenuation lumps absorption, scattering and clutter, so this is a check on orders of magnitude only. "
  "Because the true parameters may differ from the assumed ones, the parameter envelope and the global sensitivity analysis vary them over wide ranges, and the study asks which conclusions survive, not which numbers are right. The most important missing step is a comparison with a measured detection-versus-depth dataset (Section 7.4). "
  "Modelled utility intersections are not strikes: whether an intersection becomes a strike depends on hand-digging and vacuum-excavation procedures, locating before digging and operator behaviour, none of which is modelled." % (
      EP["worked_example"]["low_loss_formula_db_per_m"], EP["worked_example"]["published_attenuation_db_per_m"], EP["assumed_one_way_db_per_m_at_250MHz"]["dry_sand"], EP["assumed_one_way_db_per_m_at_250MHz"]["clay"], EP["assumed_one_way_db_per_m_at_250MHz"]["wet_clay"]), align="justify")
