# -*- coding: utf-8 -*-
"""Change-aware manuscript, part 2: Sections 3 (formulation), 4 (method), 5 (experimental design)."""
DU, DS = W6.DOMAINS["utility"], W6.DOMAINS["scaffold"]

# =============================================================================================== 3 Formulation
HD("3. Dynamic reliability problem formulation")
HD("3.1 Decision, safety failure event and reliability metrics", 2)
P("A decision unit is the object on which a release decision is taken: a 5 m corridor segment in the utility problem, a whole scaffold in the scaffold problem. At epoch *t* let *A*_{t} = 1 if the decision unit is released (a segment is released for mechanical excavation; a scaffold may continue in use), "
  "and *Q*_{t} = 1 if the unit is in a hazardous state (a utility lies inside the excavation envelope; a critical member is missing or disconnected). The safety failure event is", align="justify")
H.equation(doc, H.SUB(H.V("F"), H.V("t")) + H.T(" = {") + H.SUB(H.V("A"), H.V("t")) + H.T(" = 1, ") + H.SUB(H.V("Q"), H.V("t")) + H.T(" = 1}"), 1)
P("Three metrics are reported with explicit denominators: the unsafe-decision probability *P*(*F*) = *P*(*A* = 1, *Q* = 1), the conditional risk among released decisions *P*(*Q* = 1 | *A* = 1), and the decision coverage *P*(*A* = 1), related by", align="justify")
H.equation(doc, H.V("P") + H.T("(") + H.V("F") + H.T(") = ") + H.V("P") + H.T("(") + H.V("Q") + H.T(" = 1 | ") + H.V("A") + H.T(" = 1) ") + H.V("P") + H.T("(") + H.V("A") + H.T(" = 1)"), 2)
P("The conditional decision reliability in the simulated environment is *R*_{decision} = 1 − *P*(*Q* = 1 | *A* = 1). It is not the probability that an actual excavation or an actual period of scaffold use is accident-free, which depends on practice, supervision and behaviour that are not modelled. "
  "Because a method that releases less is safer by construction, every comparison of risk is made at matched coverage on a risk–coverage curve, or the coverage is reported next to the risk.", align="justify")
HD("3.2 Dynamic infrastructure state and observation freshness", 2)
P("The monitored object changes between observations. Let its latent state be", align="justify")
H.equation(doc, H.SUB(H.V("X"), H.V("t")) + H.T(" = (") + H.SUB(H.V("G"), H.V("t")) + H.T(", ") + H.SUB(H.V("Q"), H.V("t")) + H.T(", ") + H.SUB(H.V("H"), H.V("t")) + H.T(")"), 3)
P("with *G*_{t} the physical geometry or configuration, *Q*_{t} the safety-relevant condition and *H*_{t} the health of the sensors, and let it evolve as *P*(*X*_{t} | *X*_{t−1}, *W*_{t}, *M*), where *W*_{t} are recorded work and environmental events and *M* is the assumed transition model. "
  "For underground utilities the transitions are relocation, repair, excavation disturbance and new installation; for scaffolds they are missing braces, altered connections and displacement. "
  "In the simulations *G* enters through modification events only, *Q* is a binary hazard indicator per element and *H* the health state of each point sensor (Section 4). "
  "The probability that a previously reliable map has become unreliable grows with the time since the last observation of the element at a rate that the transition model, not a universal decay factor, determines. The study asks how fast (Section 6.2).", align="justify")
HD("3.3 Modification, authorization and work records", 2)
P("Let *C*_{t} = 1 if a physical modification occurred at epoch *t*, *A*^{auth}_{t} = 1 if it was authorized, *D*_{t} the sensor evidence and *W*_{t} the work-record evidence. The quantity of interest is the joint posterior", align="justify")
H.equation(doc, H.V("P") + H.T("(") + H.SUB(H.V("C"), H.V("t")) + H.T(", ") + H.SUB(H.V("A"), H.T("auth,") + H.V("t")) + H.T(" | ") + H.SUB(H.V("D"), H.V("t")) + H.T(", ") + H.SUB(H.V("W"), H.V("t")) + H.T(")"), 4)
P("which is kept separate from the probability of a hazardous state, *P*(*Q*_{t} = 1 | *C*_{t}, *A*^{auth}_{t}, …). An authorized modification may or may not leave a hazard (with probability θ_{A} it does), an unauthorized one usually does (θ_{U} > θ_{A}), "
  "and the work records may be missing, delayed, attached to the wrong element or spurious. Table 2 lists the four cases that distinguish a method that uses the records as context from one that does not, and the response that a reliable method should give.", align="justify")
H.caption(doc, "**Table 2.** Cases of physical change and work-record status, and the expected response.", keep_next=True)
H.table(doc, [["Physical change", "Work-record status", "Expected response"],
              ["No change", "No record", "Continue monitoring"],
              ["Change", "Valid record", "Reassess the physical hazard and update the state; authorization does not suppress the hazard"],
              ["Change", "No valid record", "Investigate and escalate"],
              ["Change", "Record missing or incorrect", "Mark authorization uncertain and verify"]], widths=[1.4, 1.8, 3.4], size=8)
HD("3.4 Asynchronous evidence and coverage", 2)
P("Observations arrive at different frequencies and cover different elements. Write them as", align="justify")
H.equation(doc, H.SUB(H.V("D"), H.V("t")) + H.T(" = {(") + H.SUB(H.V("y"), H.V("k")) + H.T(", ") + H.SUB(H.V("t"), H.V("k")) + H.T(", ") + H.SUB(H.V("s"), H.V("k")) + H.T(", ") + H.SUB(H.V("Ω"), H.V("k")) + H.T("): ") + H.SUB(H.V("t"), H.V("k")) + H.T(" ≤ ") + H.V("t") + H.T("}"), 5)
P("with *y*_{k} the measurement, *t*_{k} its time, *s*_{k} the sensor type and Ω_{k} the set of elements it covers. A measurement updates only the elements in Ω_{k}; an element covered by no sensor, or by a sensor flagged as failed, or hidden from a survey by occlusion or by the physics (a utility beyond the reach of the radar), "
  "keeps evolving according to the transition model and is reported as unverified when its probability does not meet the risk criterion.", align="justify")
HD("3.5 Model uncertainty, aleatory variability and the reliability gate", 2)
P("Aleatory variability is the random variation within a specified model (sensor noise, the timing of events); epistemic uncertainty is lack of knowledge about the model or its parameters (the rate of modification, the reliability of the records, the detection probability of a survey). "
  "No defensible probabilities are available for the model alternatives, so the study does not average over them. The reliability gate releases a decision only if the highest hazard probability over the alternatives that have not been rejected by the data meets a risk criterion:", align="justify")
H.equation(doc, H.T("release only if ") + H.SUB(H.T("sup"), H.V("m") + H.T(" ∈ ") + H.SUB(H.V("ℳ"), H.V("t"))) + H.T(" ") + H.V("P") + H.T("(") + H.SUB(H.V("Q"), H.V("t")) + H.T(" = 1 | ") + H.SUB(H.V("D"), H.V("t")) + H.T(", ") + H.SUB(H.V("W"), H.V("t")) + H.T(", ") + H.V("m") + H.T(") ≤ ") + H.SUB(H.V("τ"), H.T("safety")), 6)
P("where ℳ_{t} is the retained set of alternatives *m* (Section 4.4). The threshold τ_{safety} is a design criterion and not a safety standard: it is the highest hazard probability the policy tolerates before it asks for verification, and any other value moves the method along its risk–coverage curve.", align="justify")
HD("3.6 Failure mechanisms", 2)
P("The top event is an unsafe decision. Four conceptual branches lead to it: *detection failure* (the element could not be observed, or an observation missed), *model failure* (the change process, the geometry or the sensor parameters differ from those assumed), *decision failure* (a threshold too permissive for the conditions, visible as a predicted risk below the observed risk among released decisions) "
  "and *verification failure* (a sensor fault or a wrong or missing work record that no diagnostic caught). The decomposition is conceptual and not a Boolean fault tree: the branches are dependent, and the study evaluates failure combinations jointly (Section 8.2) instead of multiplying component probabilities.", align="justify")

# =============================================================================================== 4 Method
HD("4. Change-aware reliability-gated sensor fusion")
FIGX(doc, os.path.join(FIG6, "fig31_framework.png"), 6.4, "**Fig. 1.** Architecture of change-aware reliability-gated sensor fusion (CARGSF). Continuous, periodic and work-record evidence feed a dynamic state estimator; reconciliation keeps authorization separate from hazard; the gate releases a decision only if the supremum over the retained model alternatives meets the risk criterion. The architecture is a proposal evaluated in simulation, not a system demonstrated in the field.", alt="Architecture")
HD("4.1 Evidence layers", 2)
P("**Point sensors.** A point sensor covers one element and reports a modification event with probability *d*_{e} when one occurs and a false event with probability *f*_{e} per epoch (%s and %s for the utility monitors, %s and %s for the scaffold tilt and proximity sensors; assumptions). "
  "A sensor fails with a per-epoch probability (%s and %s) and a failure is flagged by a diagnostic with probability %s; an unflagged failed sensor is silent, and the estimator, believing it healthy, reads its silence as the absence of an event." % (
      DU["d_e"], DU["f_e"], DS["d_e"], DS["f_e"], DU["fail"], DS["fail"], DU["diag"]), align="justify")
P("**Periodic survey.** A survey every %d epochs (and a baseline survey at the start) reads the hazard state of each element it covers, with detection probability *d*_{v,i} and false-alarm probability *f*_{v}. "
  "For underground utilities *d*_{v,i} is the closed-form fused GPR and EM detection probability for the soil, utility class and depth of the segment (the sensor model of the evidence layer analysed in Section 6.1); %s%% of the assumed network lies in cells where it is below 0.3. "
  "For the scaffold, vision detects a missing member with probability 0.85 where the structure is visible, and the %d%% of members hidden by tarps or netting are not observed and are known to be unobserved." % (
      W6.DELTA, pc(R["main"]["sensor_blind_share"], 0), int(100 * DS["occl"])), align="justify")
P("**Work records.** An authorized modification is recorded with probability %s (utilities) or %s (scaffold); a record is active from one epoch before to one epoch after the modification, is attached to a wrong element with probability %s or %s, and spurious records are generated at a rate of %s or %s per element and epoch. "
  "Unauthorized modifications leave no record." % (DU["rho_rec"], DS["rho_rec"], DU["eta"], DS["eta"], DU["sigma"], DS["sigma"]), align="justify")
HD("4.2 Dynamic hazard estimator", 2)
P("Each element has a binary hazard state *Q*. In each epoch a modification event occurs with a probability that depends on whether a work record is active, and is authorized or unauthorized; an event creates a hazard with probability θ_{A} (authorized) or θ_{U} (unauthorized) if the element was safe, and removes it with probability ρ (repair) if it was hazardous. "
  "Given the posterior *p*_{t−1} = *P*(*Q*_{t−1} = 1), the joint probability of the new state and the event type follows from these rules, and the point-sensor report *y*_{e} enters through its likelihood under an event (*d*_{e} for a report) and under no event (*f*_{e}):", align="justify")
H.equation(doc, H.SUB(H.V("p"), H.V("t")) + H.T(" = ") + H.FRAC(H.NARY("∑", H.V("ε"), H.SUB(H.V("L"), H.V("ε")) + H.T("(") + H.SUB(H.V("y"), H.V("e")) + H.T(") ") + H.V("P") + H.T("(") + H.V("ε") + H.T(") ") + H.V("P") + H.T("(") + H.SUB(H.V("Q"), H.V("t")) + H.T(" = 1 | ") + H.SUB(H.V("p"), H.T("t−1")) + H.T(", ") + H.V("ε") + H.T(")")),
                                                  H.NARY("∑", H.V("ε"), H.SUB(H.V("L"), H.V("ε")) + H.T("(") + H.SUB(H.V("y"), H.V("e")) + H.T(") ") + H.V("P") + H.T("(") + H.V("ε") + H.T(")"))), 7)
P("where ε ∈ {none, authorized, unauthorized}. At a survey epoch the posterior is then updated by Bayes’ rule with the survey likelihood of the elements covered, *L*(*y*_{v} | *Q*) = *d*_{v,i} or 1 − *d*_{v,i} if *Q* = 1 and *f*_{v} or 1 − *f*_{v} if *Q* = 0. "
  "A sensor flagged as failed contributes a likelihood of one. The event rates, the authorized share and the event probability when a record is active are estimated from separate calibration sites of the nominal world (Section 5.2); θ_{A}, θ_{U} and ρ are taken as known. "
  "The estimator treats elements as independent and assumes the calibrated rates, which is wrong in the mismatch scenarios by design.", align="justify")
HD("4.3 Work-event reconciliation and change attribution", 2)
P("Three treatments of the work records are compared on the same dynamic estimator. **D0** ignores the records: events occur at the pooled rate. **D1** follows a rule found in operational displays: a change that matches an active record is logged and does not raise the hazard probability (permit suppression). "
  "**D2** uses the record as contextual evidence: the event probability and the authorized share given an active record differ from those without one, and the hazard that an authorized change leaves is estimated, not assumed away. "
  "D2 also yields the posterior probability that a reported event was authorized, which classifies it as authorized (above 0.8), unauthorized (below 0.2) or uncertain.", align="justify")
HD("4.4 The reliability gate and model-validity selection", 2)
P("The gate runs D2 under six model alternatives on the same evidence: the nominal model; modification events three times as frequent; work records treated as uninformative; point sensors treated as uninformative (as if every one had failed silently); a survey with 60%% of the assumed detection probability; and all four departures combined. "
  "For each alternative the survey predictive log-likelihood, accumulated over all surveyed elements of the structure or corridor, measures how well it has explained the surveys so far. An alternative whose log-likelihood falls more than %.0f behind the best is rejected; the retained set ℳ_{t} defines the gate of Eq. 6, and the gated hazard probability is the supremum over it. "
  "The selection implements model-validity tracking: an alternative that the data contradict stops constraining the decision, and one that they cannot yet distinguish from the nominal model keeps doing so. "
  "For the scaffold the hazard probabilities of the members are combined into the probability that the structure is unsafe, *P*(unsafe) = 1 − ∏_{critical}(1 − *p*_{i}) ∏_{bays}[*P*(fewer than two non-critical members of the bay hazardous)], under independence; the structure may continue if *P*(unsafe) ≤ %.2f." % (W6.GATE_DELTA, W6.TAU_S), align="justify")
P(f"**What the gate bounds and what it does not.** The gate is a robust decision rule and not a safety guarantee. The six alternatives are a finite set assumed by the analyst; the rejection threshold of {W6.GATE_DELTA:.0f} in log-likelihood is a design choice; "
  "and the true process may be absent from the retained set, in which case the supremum can understate the hazard (the survey cannot reject an alternative whose consequences it does not reveal). "
  "The quantity that the gate holds below the criterion is therefore a *modeled* hazard probability, conditional on the alternatives, on the evidence and on the independence assumption of Section 4.2; it is not control of the failure probability of a real corridor or structure, "
  f"and “risk-bounded” in the title is meant in that sense only. The experiments test the property rather than assume it: the observed conditional risk among released decisions is reported next to the criterion and exceeds it where the departure is not visible to the surveys "
  f"(for example {CB(UT,'combined','G','cond_risk',1)}% in the combined utility scenario against a criterion of {100*W6.TAU_A:.0f}%, Section 8.2).", align="justify")
P("Release thresholds are fixed: an element is released if its hazard probability is at most %.2f, escalated if it is at least %.2f, and sent for verification otherwise." % (W6.TAU_A, W6.TAU_P), align="justify")
HD("4.5 Baselines", 2)
P("The static twin **S0** holds the Bayesian posterior of the surveys (state assumed constant between and across them); **S0d** relaxes it toward the prior with an ad hoc decay (κ = %.2f per epoch); **S1** is static-state probabilistic fusion: point-sensor reports are treated as hazard indicators with the sensor’s operating characteristics and silence as no evidence, and surveys update the same constant state. "
  "In the scaffold domain two domain-specific baselines are added: a **point-sensor alarm** (the structure is escalated once any healthy sensor has reported a change) and a **weighted index** between 0 and 100 of importance-weighted event reports and survey detections, with and without suppression of permit-matched changes; "
  "its ranking is evaluated as a risk–coverage curve, so that the choice of its thresholds does not decide the comparison. An **oracle** that knows the true event statistics and the true sensor health is an unattainable reference." % W6.KAPPA, align="justify")
HD("4.6 Risk-constrained sensor allocation", 2)
P("A set *S* of elements receives point sensors within a budget *B*. The aim is", align="justify")
H.equation(doc, H.SUP(H.V("S"), H.T("*")) + H.T(" = ") + H.SUB(H.T("arg min"), H.V("S") + H.T(": ") + H.V("C") + H.T("(") + H.V("S") + H.T(") ≤ ") + H.V("B")) + H.T(" ") + H.SUB(H.V("R"), H.T("unsafe")) + H.T("(") + H.V("S") + H.T(")"), 8)
P("where *R*_{unsafe}(*S*) is the unsafe-decision risk after the full monitoring and decision policy. Four strategies are compared: random, uniform spacing, uncertainty-based (the elements least observable by the survey, weighted by their modification rate) "
  "and risk-optimized (the elements with the largest importance-weighted unsafe-decision mass in independent training worlds of the same site, which a greedy selection under a uniform cost maximizes; the greedy rule is the standard approach for monotone submodular objectives " + C("nemhauser78") + ", and the objective here is only approximately of that kind).", align="justify")

# =============================================================================================== 5 Experimental design
HD("5. Experimental design and baselines")
HD("5.1 The two domains", 2)
P("Both domains use %d epochs. A utility epoch is a month and a scaffold epoch a day; the epoch is a unit of simulation and the rates are assumptions. Table 3 lists the parameters. The utility sites are corridors of %d segments of 5 m whose soils, utility classes and depths are drawn from the assumed network of the evidence layer; "
  "the scaffold sites have %d members in %d bays, of which %d%% are critical (ties and primary diagonals; importance 1) and the others have importance 0.3. A scaffold is unsafe if a critical member, or two non-critical members of one bay, are hazardous. "
  "This criterion is a synthetic benchmark chosen to be simple and monotone; it was not derived from a structural analysis, and the importance values are assumptions." % (
      W6.T_EPOCHS, DU["N"], DS["N"], DS["N"] // DS["bay"], int(100 * DS["crit_share"])), align="justify")
rows = [["Quantity", "Utilities", "Scaffold"],
        ["Elements per site", str(DU["N"]), str(DS["N"])],
        ["Authorized / unauthorized events per element and epoch", "%s / %s" % (DU["lam_A"], DU["lam_U"]), "%s / %s" % (DS["lam_A"], DS["lam_U"])],
        ["Hazard created by an authorized / unauthorized event (θ_A / θ_U); repair probability ρ", "%s / %s; %s" % (DU["theta_A"], DU["theta_U"], DU["rho_fix"]), "%s / %s; %s" % (DS["theta_A"], DS["theta_U"], DS["rho_fix"])],
        ["Initial hazard probability", str(DU["pi0"]), str(DS["pi0"])],
        ["Survey interval; detection probability; false alarm", "%d epochs; 0 to 0.99 by capability; %s" % (W6.DELTA, DU["fv"]), "%d epochs; 0.85 (visible), 0 (occluded %d%%); %s" % (W6.DELTA, int(100 * DS["occl"]), DS["fv"])],
        ["Point sensor: event detection; false event per epoch; failure per epoch; failure flagged", "%s; %s; %s; %s" % (DU["d_e"], DU["f_e"], DU["fail"], DU["diag"]), "%s; %s; %s; %s" % (DS["d_e"], DS["f_e"], DS["fail"], DS["diag"])],
        ["Record rate; wrong element; spurious per element and epoch", "%s; %s; %s" % (DU["rho_rec"], DU["eta"], DU["sigma"]), "%s; %s; %s" % (DS["rho_rec"], DS["eta"], DS["sigma"])],
        ["Cost of a node; of a survey (node equivalents)", "%.0f; %.0f" % (DU["node_cost"], DU["survey_cost"]), "%.0f; %.0f" % (DS["node_cost"], DS["survey_cost"])]]
H.caption(doc, "**Table 3.** Parameters of the two simulated domains. Every value is an assumption; none is a measurement.", keep_next=True)
H.table(doc, rows, widths=[3.1, 1.8, 1.8], size=7.6)
HD("5.2 Calibration, training and test", 2)
P("The estimators are calibrated on separate calibration sites (%d sites of %d worlds) of the nominal world, from which the event probability with and without an active record and the authorized share are estimated; the risk-optimized placement uses training worlds (40 independent worlds per site) of the site it allocates; "
  "and all results are computed on test sites that share no random numbers with either (%d test sites per experiment, %d independent worlds each, drawn with seeds derived from the experiment tag and the site index). "
  "Intervals are 95%% t-intervals over the test sites. In the mismatch scenarios the true world departs from the calibrated assumptions, and the estimators are not recalibrated." % (
      R6["calibration"]["utility"]["n_sites"], R6["calibration"]["utility"]["R"], R6["meta"]["n_test_sites"], R6["meta"]["worlds_per_site"]), align="justify")
HD("5.3 Experiments", 2)
H.caption(doc, "**Table 4.** Experimental programme. E0 is the analysis of the survey evidence layer of the utility problem.", keep_next=True)
H.table(doc, [["Experiment", "Primary comparison", "Key outcome", "Hypothesis"],
              ["E0 Survey evidence layer", "Release policies, calibrated abstention, robust bounds (utilities)", "Unsafe release at matched coverage; epistemic share; drivers", "—"],
              ["E1 Dynamic changes", "Static twin and static fusion versus dynamic estimator", "Unsafe-decision risk at matched coverage", "H1"],
              ["E2 Observation staleness", "Risk against time since the last survey; event rate and survey interval", "Risk versus age; predicted versus observed risk", "H1"],
              ["E3 Permit reconciliation", "No records, permit suppression, permit as context", "Change attribution; hazardous changes not flagged", "H2"],
              ["E4 Hybrid sensing", "Point sensors only, surveys only, both", "Detection latency, missed changes, cost, risk", "H3"],
              ["E5 Sensor placement", "Random, uniform, uncertainty-based, risk-optimized", "Unsafe-decision risk at fixed budget", "H3"],
              ["E6 Transfer", "Proposed method versus domain-specific baselines in both domains", "Risk at matched coverage", "H3"],
              ["E7 Combined failures", "Silent sensor failures, erroneous records, mismatched change process, weak survey", "Conditional and worst-case risk with coverage", "H1–H3"],
              ["E8 Structural hazard definition", "Scaffold conclusions under 16 definitions of an unsafe structure (critical-member share × bay threshold)", "Risk ratios at matched coverage; gate coverage and risk", "H1, H3"]], widths=[1.4, 2.4, 2.0, 0.8], size=7.6)
P("Whether the proposed method outperforms simpler ones is not assumed. Its failures are reported with the same weight as its successes.", align="justify")
HD("5.4 Metrics, matched coverage and the survey evidence-layer study", 2)
P("All risks are conditional risks *P*(*Q* = 1 | *A* = 1) among released decisions, reported with the coverage *P*(*A* = 1); unsafe-decision probabilities are *P*(*F*). Detection delay is the number of epochs from the onset of a hazard (an element turning hazardous) until the decision is no longer a release; "
  "a hazard onset that is never flagged before the hazard ends or the horizon is reached counts as missed. The false-escalation rate is the share of non-hazardous element-epochs that are escalated. Risk–coverage curves release the decisions with the lowest hazard probability first and are evaluated at coverages of 2% to 98% in steps of 2%. "
  "At the decision level, the utility curves are at element level and the scaffold curves at structure level.", align="justify")
P("The utility evidence layer (E0) was analysed with release policies, scenarios and statistics that are described here briefly and in full in the Supplementary Material: twelve scenarios combining sensor health, geometry and parameter mismatch, each simulated as 10 independent networks of 700 km (1,400 corridors, 140,000 segments); "
  "seven release policies and four baselines; a parameter envelope of 40 draws crossed with five structural models of the geometry, 3 independent networks each; an ablation at equal released coverage; and a global sensitivity analysis with a Latin hypercube design of 320 points (McKay et al., 1979) and Sobol indices estimated by Monte Carlo on a gradient-boosting surrogate (Saltelli et al., 2010; Jansen, 1999; Sobol, 2001). "
  "Its definitions and results are in Section 6.1 and the Supplementary Material.", align="justify")
HD("5.5 Plausibility and the absence of external validation", 2)
EP = R4["external_plausibility"]
P("**No published measurement of GPR or EM detection probability against known utility depth and soil, and no measurement of scaffold-member removal detection, was reproduced in this study.** The detection curves and the change processes are outputs of assumed models, and the paper is a methodological demonstration of a reliability analysis, not a predictive model of either domain. "
  "For the radar, two plausibility checks are reported, neither of which is a validation: the low-loss relation between conductivity and attenuation reproduces a worked example of the US Environmental Protection Agency (US EPA, n.d.), which gives %.1f dB/m for 100 mS/m and a relative permittivity of 20 against the %.0f dB/m published, "
  "and the assumed one-way attenuations at 250 MHz (%.2f dB/m for dry sand, %.1f dB/m for clay) lie in the tabulated range for clays but above the tabulated value for dry sand, the table stating no frequency and no primary source. "
  "For the scaffold there is no external check at all. Because the true parameters may differ from the assumed ones, the mismatch scenarios, the parameter envelope and the sensitivity analysis vary them widely and ask which conclusions survive, not which numbers are right. "
  "The most important missing step is a comparison with measured data in both domains (Section 9.4)." % (
      EP["worked_example"]["low_loss_formula_db_per_m"], EP["worked_example"]["published_attenuation_db_per_m"], EP["assumed_one_way_db_per_m_at_250MHz"]["dry_sand"], EP["assumed_one_way_db_per_m_at_250MHz"]["clay"]), align="justify")
