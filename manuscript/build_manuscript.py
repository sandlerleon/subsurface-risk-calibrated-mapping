# -*- coding: utf-8 -*-
"""Build the TUST manuscript (docx) from results/results.json.   python build_manuscript.py -> out/Manuscript_TUST.docx"""
import os
import re
import sys

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import docx_helpers as H  # noqa: E402
from common import *  # noqa: E402,F401,F403
import common as K  # noqa: E402

H.AUTO_MATH = False          # variables are italicised explicitly with *x*
doc = H.new_document(size=11, line=1.5)
H.page_numbers_and_line_numbers(doc, line_numbers=True)
WORDS = {"body": 0}
BODY = [False]



SUPP = []
SUPPFILES = ("fig03_", "fig05_", "fig07_", "fig09_", "fig10_", "fig11_", "fig12_", "fig15_", "fig18_", "fig21_")


def FIGX(doc_, path, w, cap=None, alt=None):
    """main-text figure, or (for the supplementary set) collected for Supplementary_Material"""
    if os.path.basename(path).startswith(SUPPFILES):
        SUPP.append(dict(path=path, width=w, caption=cap))
    else:
        H.figure(doc_, path, w, cap, alt)


def P(text, **kw):
    if BODY[0]:
        WORDS["body"] += len(re.sub(r"[*_^{}]", "", text).split())
    return H.para(doc, text, **kw)


def HD(text, lvl=1):
    return H.heading(doc, text, lvl)


def pct(x, d=1):
    return pc(x, d)


m = R["main"]
cal = m["calibration"]
S = R["stress"]
DEC = R["decision"]
POL = DEC["policies"]
POS = R["positioning"]
SEC = R["sections"]
SENS = R["sensitivity"]
CB = R["class_balance"]
META = R["meta"]
CFG = R["config"]
nst = sum(1 for t in R["selftests"] if t["passed"])
ntot = len(R["selftests"])
unv = m["sensor_blind_share"]
TS = {k: v[0] for k, v in m["three_state"].items()}
decided = 1 - unv
anch = "anch_full"
G = R["grid"]
RD = R["reliable_depth_m"]
N_CORR = META["corridors_per_block"]


def thr(key):
    return ("anchored three-state, clear if p<%.2f" % key)


def pol_name(t):
    return "anchored fusion, three-state, clear if p<%.2f" % t


pb = R["main"]["probability_bands"]


# =============================================================================================== v1.1 numbers (SubSurface_v4.py)
SC = R4["scenarios"]
EC, EH = R4["equal_coverage"], R4["equal_coverage_half_shifts"]
SWP, ZT, DR, VO = R4["shift_sweep"], R4["zones"], R4["depth_resolved"], R4["voi"]
A4 = R4["assumptions_v4"]


def sm(sc, m, k, d=1):
    return pc(SC[sc]["models"][m]["metrics"][k][0], d)


def sci(sc, m, k, d=1):
    v = SC[sc]["models"][m]["metrics"][k]
    return "%s (%s to %s)" % (pc(v[0], d), pc(v[1], d), pc(v[2], d))


def secs(sc, m):
    return "%.3f" % SC[sc]["models"][m]["ece"][0]


def cvr(E, p, c, d=1):
    for q in E["policies"][p]["by_coverage"]:
        if abs(q["coverage"] - c) < 1e-9:
            return "n/a" if q["strikes_per_km"] is None else ("%." + str(d) + "f") % q["strikes_per_km"][0]


def eqr(E, p, r):
    return pc(E["policies"][p]["equal_risk_coverage"][r][0], 1)


def mincost(E, p):
    v = E["policies"][p]["cost_per_km"]["strike_cost_x1"]
    return v["min_cost_usd_per_km_excl_survey"], v["coverage_at_min"]


def sw(rate, m, k):
    return pc(SWP["rate_per_100m"][rate][m]["metrics"][k][0], 1)


def swe(rate, m):
    return "%.3f" % SWP["rate_per_100m"][rate][m]["ece"][0]


def swl(rate, m):
    return pc(SWP["rate_per_100m"][rate][m]["lateral_error_m"]["share_within_0p5m"], 0)


def voi(h, strat, bf, key="change_vs_no_pits_usd_per_km"):
    for q in VO[h]["strategies"][strat]:
        if abs(q["budget"] - bf) < 1e-9:
            return q[key]


# =============================================================================================== title page
P("**" + TITLE + "**", align="center", size=15, space_after=10)
P("Leon Sandler", align="center", size=12, space_after=0)
P("Independent Researcher, Northbrook, Illinois, USA", align="center", size=10.5, space_after=0)
P("ORCID: 0009-0007-4584-808X • Corresponding author: sandler.leon@gmail.com", align="center", size=10.5, space_after=12)
P("Manuscript prepared for submission to *Tunnelling and Underground Space Technology* (original research article). Software: %s (archived at https://doi.org/%s). Preprint: https://doi.org/%s." % (REPO, SW, PP), align="center", size=9.5, space_after=14)

HD("Abstract", 2)
ABSTRACT = (
    "Excavation near buried utilities relies on maps whose reliability is rarely stated. This paper specifies and tests, in simulation only, a decision policy above ground-penetrating radar (GPR), an electromagnetic (EM) locator and a known anchor: "
    "a Bayesian filter follows a utility along a corridor and across a lateral grid, treats a sensor flagged as failed as uninformative, and reports each segment as present, absent or unverified, the last where capability at the estimated depth is below 0.3 or an on-site reference check fails. "
    "It is a methodological demonstration: sensor behaviour is assumed and no published detection-versus-depth dataset was reproduced. "
    "Seeded Monte Carlo experiments with cluster-bootstrap intervals compare six models in sixteen scenarios, a structural-mismatch series and a parameter envelope, keeping detection, calibration, localisation and unverified coverage apart. "
    "In sensor-visible cells the anchored filter reaches %s%% accuracy against %s%% for an EM-only proxy, and with three parallel passes false alarms stay near %s%% under frequent lateral shifts where one-pass filters reach %s%%; "
    "sensor-health awareness cuts false clearance from %s%% to %s%% under mixed sensor health with an imperfect diagnostic, but an unflagged GPR failure defeats every model (%s%%). At equal released coverage the gain over per-segment fusion is small. "
    "Structural mismatch hurts: with a parallel utility the lateral tracker trades false alarms for false clearance (%s%% against %s%% for a one-pass filter), and wide parameter uncertainty and unseen soils (%s%% false clearance with a reference check) degrade all models. Modelled intersections are risk proxies, not strikes."
) % (mm(anch, "visible", "acc"), mm("em_only", "visible", "acc"), sw("2.0", "proposed_3pass", "false_alarm"), sw("2.0", "continuity_1d", "false_alarm"),
     sm("mixed_health_realistic_diagnostic", "continuity_1d", "false_clearance"), sm("mixed_health_realistic_diagnostic", "proposed_3pass", "false_clearance"), sm("C_gpr_failed_unflagged", "proposed_3pass", "false_clearance", 0), pc(R4["geometry_mismatch"]["levels"][3]["models"]["proposed_3pass"]["metrics"]["false_clearance"][0], 0), pc(R4["geometry_mismatch"]["levels"][3]["models"]["continuity_1d"]["metrics"]["false_clearance"][0], 0), sm("ood_soils", "proposed_3pass", "false_clearance"))
P(ABSTRACT, align="justify")
AB_WORDS = len(ABSTRACT.split())
P("**Keywords:** utility mapping; ground-penetrating radar; electromagnetic locator; sensor fusion; probability calibration; excavation safety", size=10.5)
doc.add_page_break()
BODY[0] = True

# =============================================================================================== 1 Introduction
HD("1. Introduction")
P("Strikes on buried utilities are a recurrent cause of injury, service interruption and cost " + C("metje15", "makana20") + ", and the records on which excavation planning starts are often incomplete or positionally uncertain "
  + C("adebiyi25") + ". Subsurface utility engineering practice grades the quality of utility information from record review to exposure of the utility itself " + C("asce02") + ". Between those extremes, "
  "non-intrusive geophysical surveys with ground-penetrating radar (GPR) and electromagnetic (EM) locators are the usual way to turn records into positions. Their capabilities and limits have been reviewed in this journal "
  + C("metje07", "costello07", "hao12") + " and elsewhere " + C("lai18") + ".", align="justify")
P("The limits are well known. GPR penetration falls with soil conductivity and moisture " + C("doolittle95", "annan09") + "; EM locators need a conductive path or an injected signal and are largely blind to dielectric pipes and fibres; "
  "and positions derived from either instrument depend on survey set-up " + C("jaw13") + " and on velocity and depth-picking uncertainty " + C("xie22") + ". A great deal of recent work improves detection with one sensor, for example by automatic hyperbola "
  "recognition " + C("dou17") + ", or combines sensors into a three-dimensional picture " + C("dou16") + ". Stakeholder studies of utility location have examined what users need from such outputs " + C("thomas09", "royal10") + ".", align="justify")
P("A question that receives less attention is what the map should say where the sensors carry little information. A conventional deliverable marks what was detected, and the absence of a mark is read as the absence of a utility. "
  "That reading is safe only where the sensors could have detected the utility had it been there. Where they could not, for example a plastic sewer at several metres in moist clay, the absence of a mark is the sensors' silence, not evidence. "
  "Whether the output distinguishes the two cases is a design choice with direct consequences for excavation.", align="justify")
P("This paper takes that design choice as its subject. It specifies a decision layer that sits above GPR, EM and positioning hardware and evaluates it in seeded Monte Carlo simulation. The layer has these parts: "
  "(i) utility-specific anchors, such as a manhole of known network identity, that start a belief; (ii) likelihoods that depend on soil, material and depth; (iii) a Bayesian filter that carries the belief along the corridor and across a lateral grid, so that a utility that has moved sideways can be followed; "
  "(iv) sensor-health awareness, so that a sensor flagged as failed stops counting as evidence of absence; and (v) a three-state output (present, absent, unverified) set by depth-resolved capability zones, with a verification ranking for trial pits. The contributions are:", align="justify")
for t in (
    "a formulation in which the unverified state is derived from the expected detectability of each soil, utility and depth combination and from the health of the instruments, so that it can be reported, counted and audited;",
    "an evaluation protocol that keeps four outcomes apart (detection and classification, probability calibration, location and depth accuracy, and the share of the network left unverified), with explicit denominators and cluster-bootstrap intervals;",
    "baselines, ablations and stress tests, including an equal-effort baseline, a scenario matrix of sixteen conditions and soils not used to set the model, that show where the layer helps and where it does not; and",
    "an excavation-clearance comparison at equal released coverage, equal risk and equal cost, and a value-of-information allocation of trial pits.",
):
    H.bullet(doc, t)
P("**Scope.** Everything reported here is a simulation under stated assumptions. The sensor model is a thresholded signal-to-noise model with parameters chosen to give a plausible range of detectability, not fitted to field data. "
  "The simulation tests the logic of the decision layer and its sensitivity to its own assumptions. It cannot show how the layer would perform on real corridors, and the Discussion says what would be needed to find out. "
  "This version corrects an operating-point confound in the clearance comparison of version 1 (Section 5.6).", align="justify")

# =============================================================================================== 2 Background
HD("2. Background and related work")
HD("2.1 Sensors and their limits", 2)
P("GPR responds to contrasts in dielectric permittivity and can detect metallic and non-metallic utilities, but its range is set by attenuation in the ground, which depends strongly on soil type and moisture " + C("doolittle95", "annan09")
  + ". Higher frequencies give finer resolution and stronger attenuation. EM locators detect the field around a conductor, either passive (power or radio signals already present) or active (a transmitter couples a signal into the line), and therefore depend on a conductive path that may not exist for plastic pipes and dielectric fibre. "
  "The two sensors are complementary in the materials they see and in how they fail, which is the usual argument for combining them " + C("metje07", "costello07") + ".", align="justify")
HD("2.2 Fusion of GPR and EM data", 2)
P("Fusion of GPR with induction-based sensing has been studied most extensively for buried-object detection, at feature and decision levels " + C("stanley02") + " and with evidence-theoretic combination of radar data " + C("milis03")
  + ". Work on the combination of correlated decisions " + C("tesf12") + " is relevant here because the two GPR bands and, in poor soils, GPR and EM can fail together. For utilities, multi-sensor data have been combined into three-dimensional location estimates " + C("dou16") + " and utilities mapped from partial observations " + C("dou20")
  + ". The present paper does not propose a new detector or a new fusion operator. It takes detections as given and asks how they should be turned into a probabilistic, auditable statement about each segment.", align="justify")
HD("2.3 Probabilistic mapping, reject options and calibration", 2)
P("Maintaining a probability of occupancy per cell and updating it with each observation is established in robot mapping " + C("elfes89") + ". The corridor filter used here is a one-dimensional relative of that idea with a persistence prior along the alignment. "
  "Classifiers with a reject option, which decline to decide when the evidence is weak, trade error against coverage " + C("chow70") + "; the unverified state plays that role, with the difference that it is set by expected detectability rather than by the posterior alone. "
  "Probabilities are useful for decisions only if they are calibrated. Calibration and sharpness are distinct properties of probabilistic forecasts " + C("gneiting07b") + ", scored by proper scoring rules such as the Brier score " + C("brier50", "gneiting07a")
  + ", which decomposes into reliability, resolution and uncertainty " + C("murphy73") + ". Methods exist to recalibrate scores " + C("zadrozny02", "niculescu05", "naeini15") + ", and the independence assumption of naive combination of evidence can give good decisions while giving poor probabilities "
  + C("domingos97", "hand01") + ", which is the situation examined in Sections 5.4 and 5.9. Accuracy depends on how many segments are truly occupied, which changes with the corridor and with the loss hazard, and precision-recall or balanced measures are more informative when classes are imbalanced "
  + C("fawcett06", "saito15") + ". The results therefore report balanced accuracy and class prevalence alongside accuracy.", align="justify")


HD("2.4 Positioning against the closest existing approaches", 2)
P("Spatial tracking of utilities across scan lines with multi-sensor fusion exists: " + CN("dou16") + " march utility tracks from one scan cross-section to the next with an extended Kalman filter and associate hypothesised detections from five sensor types, and " + CN("dou20") + " map utilities from partial observations. "
  "Occupancy mapping " + C("elfes89") + ", reject-option decisions " + C("chow70") + " and GPR-EM fusion " + C("stanley02", "tesf12", "milis03") + " supply the other ingredients. Table 1 states, as far as the titles and abstracts say, which of the properties of the present layer each addresses; it is a reading of the cited work, not an audit of it.", align="justify")
H.caption(doc, "**Table 1.** Closest existing approaches and the present layer. Yes = addressed; \u2014 = not described in the abstract or title read; n/e = not examined in detail.", keep_next=True)
H.table(doc, [["Approach", "Spatial tracking", "Sensor-health modelling", "Detection-limit awareness", "Calibrated abstention", "Risk-based verification"],
              ["Occupancy grids (Elfes, 1989)", "Yes (grid cells)", "\u2014", "through sensor models", "\u2014", "\u2014"],
              ["Reject-option decisions (Chow, 1970)", "\u2014", "\u2014", "\u2014", "Yes (posterior threshold)", "\u2014"],
              ["GPR-EMI fusion, landmines (Stanley et al., 2002)", "\u2014", "n/e", "n/e", "n/e", "n/e"],
              ["Fusion of correlated decisions, GPR (Tesfamariam et al., 2012)", "\u2014", "\u2014", "n/e", "n/e", "n/e"],
              ["Dempster-Shafer fusion of GPR data (Milisavljevi\u0107 et al., 2003)", "\u2014", "n/e", "n/e", "n/e", "n/e"],
              ["Multi-sensor utility location, extended Kalman filter (Dou et al., 2016)", "Yes (tracks across scan lines)", "\u2014", "\u2014", "\u2014", "\u2014"],
              ["Utility mapping from partial observations (Dou et al., 2020)", "Yes (3D mapping)", "n/e", "n/e", "n/e", "n/e"],
              ["**This work (simulation)**", "Yes (along and across, grid filter)", "Yes (assumed diagnostic)", "Yes (capability zones)", "Yes (three states, calibration scored)", "Yes (value of information, assumed costs)"]],
        widths=[2.0, 0.95, 0.9, 0.9, 0.95, 0.9], size=7)
P("The novelty claimed is therefore the integration and evaluation of a risk-calibrated decision policy for subsurface utility surveys, in which the unverified state is derived from the capability of the instruments and their health, and in which the policy is compared with simpler ones at equal effort and equal coverage. "
  "It is not a new filtering algorithm: the lateral filter is a grid filter of a standard kind, and its tracking function overlaps with that of " + CN("dou16") + ".", align="justify")

# =============================================================================================== 3 Framework
HD("3. The decision layer")
P("A corridor is divided into segments of 5 m along a tracked alignment, typically the line of a known utility between two access points. For one utility, *b*_{k} is the probability that the utility lies on the tracked alignment in segment *k*. "
  "Figure 1 shows the information flow.", align="justify")
FIGX(doc, os.path.join(FIG, "fig01_framework.png"), 6.4, "**Fig. 1.** The decision layer. Anchors, GPR and the EM locator feed soil- and depth-aware likelihoods; a filter carries the belief along the corridor; each segment is reported as present, absent or unverified, and the residual probabilities rank where trial pits are worth their cost.",
         alt="Flow diagram of the decision layer")
HD("3.1 Anchors", 2)
P("A manhole, valve chamber or cabinet establishes the existence of the utility only for the network to which it belongs. An anchor therefore carries a network identity and a reliability. The belief is started from the anchor only for utilities whose connection to that anchor is established, "
  "with *b*_{0} equal to the anchor reliability (1 when the identity is certain). Section 5.5 examines the consequences of an anchor that is less reliable than assumed.", align="justify")
HD("3.2 Evidence and likelihoods", 2)
P("Each sensor reports detect or no-detect for a segment. A detection has probability *P*_{d} when the utility is on the alignment and *P*_{fa} when it is not, where *P*_{d} depends on soil, utility material and depth (Section 4.2) and *P*_{fa} is a clutter rate that depends on soil. "
  "The filter holds these likelihoods in tables indexed by soil and utility. Depth is not known exactly in practice, so by default the tables use the mid-depth of the depth class of the utility; two variants use the true depth and a likelihood averaged over the class range (Section 5.2).", align="justify")
HD("3.3 Propagation and update", 2)
P("Between segments the belief is predicted with a survival probability and a small re-birth term, where *h* is the probability per segment that the utility leaves the alignment (ends, turns or is displaced) and *r* the probability that it returns:", align="justify")
H.equation(doc, H.SUB(H.V("b"), H.V("k|k−1")) + H.T(" = (1 − ") + H.V("h") + H.T(") ") + H.SUB(H.V("b"), H.V("k−1")) + H.T(" + ") + H.V("r") + H.T(" (1 − ") + H.SUB(H.V("b"), H.V("k−1")) + H.T(")"), 1)
P("Each sensor *s* then updates the odds of presence by a likelihood ratio, with *y*_{s,k} = 1 for a detection:", align="justify")
H.equation(doc, H.FRAC(H.SUB(H.V("b"), H.V("k")), H.T("1 − ") + H.SUB(H.V("b"), H.V("k"))) + H.T(" = ") + H.FRAC(H.SUB(H.V("b"), H.V("k|k−1")), H.T("1 − ") + H.SUB(H.V("b"), H.V("k|k−1"))) + H.T(" ")
           + H.NARY("∏", H.V("s"), H.SUP(H.DELIM(H.FRAC(H.SUB(H.V("P"), H.T("d,") + H.V("s")), H.SUB(H.V("P"), H.T("fa,") + H.V("s")))), H.SUB(H.V("y"), H.V("s,k")))
                    + H.SUP(H.DELIM(H.FRAC(H.T("1 − ") + H.SUB(H.V("P"), H.T("d,") + H.V("s")), H.T("1 − ") + H.SUB(H.V("P"), H.T("fa,") + H.V("s")))), H.T("1 − ") + H.SUB(H.V("y"), H.V("s,k")))), 2)
P("The filter treats sensors and segments as conditionally independent given the state. That assumption is false in the simulation by construction, because noise is shared between the two GPR bands and along a run, and the effect is examined directly (Section 5.9). "
  "Likelihood floors keep any single observation from driving the belief to certainty (Appendix A).", align="justify")
HD("3.4 Three-state output and verification priority", 2)
P("A segment is reported as present when *b*_{k} > 0.5 and absent otherwise, except in sensor-blind cells. A cell, defined by soil, utility and depth class, is sensor-blind when the closed-form probability that at least one sensor produces a true signal detection at the class mid-depth is below 0.3:", align="justify")
H.equation(doc, H.SUP(H.V("P"), H.T("fused")) + H.T(" = 1 − (1 − ") + H.SUP(H.V("P"), H.T("GPR")) + H.T(")(1 − ") + H.SUB(H.V("c"), H.V("u")) + H.SUP(H.V("P"), H.T("EM")) + H.T(") < 0.3"), 3)
P("where *P*^{GPR} is the probability that either GPR band detects, *c*_{u} the probability that utility *u* couples to the EM locator, and *P*^{EM} the detection probability of a coupled line. In a blind cell the output is unverified whatever the filter says, because the filter's belief there rests on the continuity prior and not on sensor evidence. "
  "A low probability is never presented as clearance. The threshold of 0.3 is a design choice and Section 5.9 reports how the share of the network it flags changes with the sensor parameters.", align="justify")
P("Segments that are not called present are ranked for verification by their residual probability *b*_{k}, optionally weighted by the consequence of a strike and divided by the cost of a pit (Section 5.6). The unverified segments are candidates for the same ranking, with the continuity prior as their probability.", align="justify")


HD("3.5 Lateral tracking", 2)
P("To follow a utility that moves sideways, the state of a segment is extended from presence to a lateral position: the utility is either absent or at one of %d offsets between \u22125 m and +5 m in 0.5 m steps (the offsets are modelling choices, not survey specifications). "
  "Between segments it may stay, drift by one step, shift by 1 to 4 m, end, or return from absence; the filter assumes small fixed rates for these events and does not know which geometry a corridor has. "
  "A pass at lateral position *y*_{p} observes the utility with a signal reduced by a lateral penalty that depends on the offset \u0394 = |*y* \u2212 *y*_{p}| and the depth *d*:" % 21, align="justify")
H.equation(doc, H.SUB(H.V("L"), H.T("lat")) + H.T("(") + H.V("\u0394") + H.T(", ") + H.V("d") + H.T(") = min(10 (") + H.V("\u0394") + H.T(" / ") + H.V("w") + H.T("(") + H.V("d") + H.T("))") + H.SUP(H.T(""), H.T("2")) + H.T(", 60) dB"), 5)
P("with half-widths *w*(*d*) of 0.6 + 0.35 *d* m for the GPR and 1.0 + 0.5 *d* m for the EM locator (assumptions). Detection probabilities for every offset and pass then follow from the same signal-to-noise model as in Section 4.2. "
  "The probability that the utility lies on the excavation footprint (offset within 1 m) is the sum of the belief over those offsets. The state does not include depth or utility class: depth enters through the class mid-depth or an estimated depth with 10% velocity uncertainty, and the class is the network of the anchor. "
  "The EM coupling of a utility is a property of the corridor, so the filter carries a persistent coupling state; repeated EM non-detections then lower the belief only slowly, which matters when the GPR is unavailable.", align="justify")
HD("3.6 Sensor health", 2)
P("Each instrument is healthy, degraded (a loss of 6 dB) or failed (it returns only clutter). A health diagnostic, such as a self-test or a pass over a reference target, reports healthy, degraded or failed with imperfect accuracy; the assumed rates are in Table 8. "
  "A sensor flagged as failed contributes a likelihood of one, that is, no evidence in either direction; a sensor flagged as degraded uses the degraded likelihood; a failure that is not flagged is treated as healthy. A fixed observation model would instead read the silence of a dead GPR as evidence of absence.", align="justify")
HD("3.7 Capability zones and the fail-safe rule", 2)
P("The capability of a segment is the closed-form probability that at least one available sensor produces a true signal detection at the estimated depth (Eq. 3 with the estimated depth, the sensors not flagged as failed, and the filter\u2019s soil parameters). "
  "Zone A (capability at least 0.9) is detectable under the model, zone B (0.3 to 0.9) is marginal, and zone C (below 0.3) is a zone in which detection capability is not established. The decision rule is: present if *p* \u2265 \u03c4_{P}; absent only in zone A with *p* \u2264 \u03c4_{A}, or in zone B with *p* \u2264 0.02; otherwise unverified; "
  "and always unverified in zone C or when the on-site reference check fails. The thresholds \u03c4_{P} = 0.5 and \u03c4_{A} = 0.1 are design choices. "
  "The reference check passes a reference target of the segment\u2019s class %d times and compares the detection rate with the rate predicted by the filter\u2019s soil table by an exact binomial test (\u03b1 = 0.01); a failed check marks the corridor as zone C until the site is recalibrated. "
  "For zone C, the escalation is to other sources of information: network records, manhole and chamber inspection, accessible inspection points, and qualified verification or trial pits." % A4["reference_check"]["n_passes"], align="justify")
HD("3.8 Value of information for trial pits", 2)
P("Let *d* be the decision to release a segment for mechanical excavation or to hold it, *U* the true state, *D* the evidence, and *Y*_{a} the outcome of a verification action *a*. The value of information of *a* is", align="justify")
H.equation(doc, H.V("VOI") + H.T("(") + H.V("a") + H.T(") = ") + H.SUB(H.T("min"), H.V("d")) + H.V("E") + H.T("[") + H.V("L") + H.T("(") + H.V("d") + H.T(", ") + H.V("U") + H.T(") | ") + H.V("D") + H.T("] \u2212 ") + H.SUB(H.V("E"), H.SUB(H.V("Y"), H.V("a")))
           + H.T("[") + H.SUB(H.T("min"), H.V("d")) + H.V("E") + H.T("[") + H.V("L") + H.T("(") + H.V("d") + H.T(", ") + H.V("U") + H.T(") | ") + H.V("D") + H.T(", ") + H.SUB(H.V("Y"), H.V("a")) + H.T("]] \u2212 ") + H.V("C") + H.T("(") + H.V("a") + H.T(")"), 6)
P("where *L* is the loss (the consequence of a strike if a present utility is released, a holding cost if the segment is held) and *C*(*a*) the cost of the action. For a trial pit that reveals the state of one segment with probability *p* of presence, "
  "VOI = min(*p* *C*_{s}, *C*_{h}) \u2212 *p* *C*_{h} \u2212 *C*_{p}, with strike cost *C*_{s}, holding cost *C*_{h} and pit cost *C*_{p}. Pits are chosen in decreasing order of VOI while it is positive " + C("howard66") + ".", align="justify")
# =============================================================================================== 4 Methods
HD("4. Simulation methodology")
P("All results come from one Python file, SubSurface_MC.py (NumPy, SciPy, Matplotlib; %s), run with a fixed seed (%d). The command, versions and every parameter are written to results.json. %d of %d built-in self-tests pass; they check the code against its own mathematics (Section 4.8)." % (
    "%s on Python %s" % (META["numpy"], META["python"]), META["seed"], nst, ntot), align="justify")
HD("4.1 Synthetic corridors", 2)
P("A corridor holds one utility of one type, buried at one depth in one soil, tracked over %d segments of %d m. Five soils (dry sand, dry loam, moist loam, clay, rubble fill) and seven utility types (PE/PVC water, cast-iron water, plastic sewer, concrete sewer, power duct, telephone duct, dielectric fibre) define 35 cells. "
  "Depth is drawn uniformly from a range per utility (sewers 3 to 7 m, water and fibre 1 to 2 m, telephone 0.6 to 1.0 m, power 0.5 to 2 m) and is constant along a corridor. Cells are weighted by an assumed network share (Table 2) with the five soils equally weighted, "
  "which defines the \"mixed network\". The ranges and shares are assumptions, informed by the depths and utility types of the rehabilitation setting that motivated the study, not data." % (META["segments_per_corridor"], int(CFG["truth"]["segment_m"])), align="justify")
HD("4.2 Sensor model", 2)
P("For band *b* (250 or 600 MHz) the signal-to-noise ratio in segment *k* is", align="justify")
H.equation(doc, H.SUB(H.V("S"), H.V("b,k")) + H.T(" = ") + H.SUB(H.V("B"), H.V("b")) + H.T(" + ") + H.SUB(H.V("ρ"), H.V("u")) + H.T(" − ") + H.SUB(H.V("a"), H.V("b")) + H.T("(") + H.V("s") + H.T(") ") + H.V("d") + H.T(" − 40 log") + H.SUB(H.T(""), H.T("10")) + H.T("(max(2") + H.V("d") + H.T(", 1)) − ")
           + H.SUB(H.V("L"), H.V("k")) + H.T(" + ") + H.SUB(H.V("z"), H.T("run,") + H.V("b")) + H.T(" + ") + H.SUB(H.V("z"), H.T("seg,") + H.V("b,k")), 4)
P("where *B*_{b} is the system budget (70 dB at 250 MHz, 74 dB at 600 MHz), *ρ*_{u} the reflectivity of the utility (0 dB cast iron to −14 dB fibre), *a*_{b}(*s*) the two-way attenuation per metre of soil *s*, scaled with frequency as (*f*/250 MHz)^{0.5}, *d* the depth, "
  "*L*_{k} a loss that is 6 dB when the utility has shifted sideways and, in Section 5.8, a shadowing term for an overlying line, and *z* Gaussian noise. The run-level term *z*_{run} (standard deviation 3 dB) is constant along a corridor and the segment-level term *z*_{seg} (4.0 to 7.0 dB by soil) varies from segment to segment; "
  "for both, the two bands are correlated with coefficient 0.7. A signal detection occurs when *S* exceeds 8 dB and the utility is on or near the alignment; in addition, clutter produces a detection with a soil-dependent probability (1% in dry sand to 6% in rubble fill), so a detection can be a false alarm whether or not a utility is present. "
  "The closed-form signal detection probability of a band is Φ((E[*S*] − 8)/σ_{tot}), with σ_{tot}² = σ_{run}² + σ_{seg}², and that of the two bands jointly follows from the bivariate normal distribution.", align="justify")
P("The EM locator is modelled by coupling, a property of the utility and the survey: each utility couples to the locator with probability *c*_{u} (cast iron 0.60, telephone 0.35, fibre 0.12, PE/PVC 0.08, plastic sewer 0.05, concrete sewer 0.02; power 0.85 when energised and 0.25 when not, 50% energised). "
  "A coupled utility is detected when its signal-to-noise ratio, which falls with depth and soil conductivity, exceeds a threshold; an uncoupled one is detected only by clutter (1%). Coupling is drawn once per corridor, so an EM miss on one segment is informative about the next, which the filter ignores.", align="justify")
HD("4.3 Truth process", 2)
P("The truth along a corridor is a Markov chain over three states: on the tracked alignment, gone (ended or turned away) and laterally shifted (still near the alignment, with a 6 dB weaker signal). "
  "Starting on the alignment at the anchor, the utility leaves with probability *h* per segment, corresponding to a hazard of 0.2 per 100 m, and returns with probability *r* corresponding to 0.05 per 100 m. "
  "In the baseline all losses are \"gone\"; lateral shifts are introduced as a stress (Section 5.5). The label that is scored is \"the utility is on the tracked alignment\". With these values the utility is on the alignment in %s%% of segments, so about a third of all segments are truly empty." % pct(M[anch]["all"]["prev"][0], 0), align="justify")
HD("4.4 Methods compared", 2)
P("All methods see the same simulated detections (paired comparison). The sensor-only baselines are the EM locator alone, which stands in for current practice and is not an evaluation of any real instrument, GPR at 250 MHz, at 600 MHz and dual-band. Rule-based fusion uses OR (any sensor detects) and AND (GPR and EM detect). "
  "Per-segment Bayesian fusion combines the three sensors with a flat prior or with the base-rate prior of the truth process, with no propagation. Propagation without an anchor starts the filter at *b*_{0} = 0.5. The framework is the anchored filter with GPR and EM and soil-specific likelihoods at the class mid-depth. "
  "Ablations remove or alter one element: GPR only, generic (soil-averaged) likelihoods, evidence tempered by a factor of 0.5, an exact joint likelihood for the two GPR bands, a likelihood averaged over the class depth range, and a variant that knows the true depth. "
  "The last three are diagnostics of the assumptions of the framework and are labelled as such.", align="justify")
HD("4.5 Metrics and denominators", 2)
P("Each corridor contributes 100 segments, each either truly on the alignment or not. For a method that makes a binary call per segment, accuracy is the share of correct calls among all segments considered, the miss rate is missed segments divided by truly present segments, and the false-alarm rate is false calls divided by truly empty segments. "
  "Balanced accuracy is the mean of 1 − miss and 1 − false-alarm. Metrics are formed from cell-level fractions and weighted by the network share of each cell. Three views are reported, and the denominator of every table is stated by its view:", align="justify")
for t in (
    "*Sensor-visible cells* (%s%% of the weighted network, %d of 35 cells): cells where the fused detection probability at mid-depth is at least 0.3. These are the segments on which the framework issues a present or absent call." % (pct(1 - unv, 0), 35 - len(m["sensor_blind_cells"])),
    "*All cells, blind forced to binary*: all 35 cells, including sensor-blind cells where the binary call rests on the continuity prior. This is the view in which a method without an unverified state would be scored.",
    "*Sensor-blind cells* (%s%%): reported only for diagnosis. Under the framework these segments are labelled unverified and no present or absent call is issued." % pct(unv, 0),
):
    H.bullet(doc, t)
P("Detection and classification performance is therefore always reported with its view. Probability calibration is scored with the Brier score and the expected calibration error (ECE) in ten equal-width bins, "
  "ECE = Σ_{j} *w*_{j} |*p̄*_{j} − *ȳ*_{j}|, where *w*_{j} is the share of segments in bin *j*, *p̄*_{j} the mean reported probability and *ȳ*_{j} the observed frequency of presence; the Brier score is the mean squared difference between probability and outcome. "
  "Location and depth accuracy come from a separate closed-form error model (Section 5.7), and the share of the network left unverified is reported as such. These four outcomes are not combined into a single score.", align="justify")
HD("4.6 Experiments", 2)
P("The main experiment simulates %d blocks, each with %s corridors (500 per cell) of %d segments. Stress tests re-simulate with changed truth or sensor conditions on %d blocks of 250 corridors per cell: loss hazard 0.05 to 1.0 per 100 m; "
  "the share of losses that are lateral shifts (0 to 100%%); an anchor that is on the alignment with probability 0.9, 0.7 or 0.5, scored both for a filter that assumes certainty and for one that knows the reliability; a dead GPR or EM in a share of runs; "
  "correlation between GPR and EM noise (0 to 0.9); dropped observations; and a filter that assumes the wrong hazard. A clearance trial compares policies by modelled intersections and corridor released, and a trial-pit experiment compares allocation rules. "
  "A repeat pass on uncertain segments (Section 5.9) examines the value of a re-scan. One-at-a-time sensitivity to ten parameters uses common random numbers (3 blocks of 166 corridors per cell). The intervals are 95%% t-intervals over blocks (half-width in brackets); they describe simulation noise, not uncertainty about the real world." % (
      META["blocks"], "{:,}".format(N_CORR), META["segments_per_corridor"], max(3, META["blocks"] // 2)), align="justify")
HD("4.7 Assumptions register", 2)
P("Table 2 lists the assumptions. They were chosen to give a plausible spread of detectability and to reproduce the qualitative depth envelope of the setting that motivated the study (about 5 m or more in dry sand, 3 to 4 m in dry loam, about 2 m in moist loam and 1 to 2 m in clay); they are not fitted to measurements.", align="justify")
rows = [["Quantity", "Value used", "Role"],
        ["Soils (cells)", "dry sand, dry loam, moist loam, clay, rubble fill", "5 soils, equal weight"],
        ["Two-way attenuation at 250 MHz (dB/m)", ", ".join("%.1f" % x for x in CFG["soil"]["atten_250_db_per_m"]), "per soil, scaled as (f/250)^0.5"],
        ["Segment noise σ_seg (dB)", ", ".join("%.1f" % x for x in CFG["soil"]["sigma_seg_db"]), "per soil"],
        ["Clutter false-alarm probability", ", ".join("%.3f" % x for x in CFG["soil"]["clutter_pfa"]), "per soil, per segment"],
        ["EM attenuation (dB/m)", ", ".join("%.1f" % x for x in CFG["soil"]["em_atten_db_per_m"]), "per soil"],
        ["GPR budget 250 / 600 MHz; threshold", "%.0f / %.0f dB; %.0f dB" % (CFG["gpr"]["budget_db"]["250"], CFG["gpr"]["budget_db"]["600"], CFG["gpr"]["threshold_db"]), "detection"],
        ["Run-level noise; band correlation", "%.0f dB; %.1f" % (CFG["gpr"]["sigma_run_db"], CFG["gpr"]["band_correlation"]), "shared along a corridor"],
        ["Spreading loss", "%.0f log10(max(2d, 1)) dB" % CFG["gpr"]["spreading_coef"], "depth d in m"],
        ["Reflectivity (dB): PE/PVC, cast iron, plastic sewer, concrete sewer, power, telephone, fibre", ", ".join("%.0f" % x for x in CFG["util"]["reflectivity_db"]), "GPR"],
        ["EM coupling: PE/PVC, cast iron, plastic sewer, concrete sewer, power, telephone, fibre", "0.08, 0.60, 0.05, 0.02, 0.55 (mean), 0.35, 0.12", "probability, per corridor"],
        ["EM budget; threshold; segment noise; clutter", "%.0f dB; %.0f dB; %.0f dB; %.2f" % (CFG["em"]["budget_db"], CFG["em"]["threshold_db"], CFG["em"]["sigma_seg_db"], CFG["em"]["pfa"]), "EM"],
        ["Network share (same order as reflectivity)", ", ".join("%.2f" % x for x in CFG["util"]["share"]), "weights utilities within a soil"],
        ["Loss hazard; re-birth", "%.2f; %.2f per 100 m" % (CFG["truth"]["hazard_per_100m"], CFG["truth"]["rebirth_per_100m"]), "truth process (filter matched)"],
        ["Off-alignment penalty; shadowing", "6 dB; 3 dB (PE/PVC above), 10 dB (cast iron above)", "shifts; cross-sections"],
        ["Unverified threshold", "fused signal detection probability < 0.3 at mid-depth", "design choice"],
        ["Consequence of a strike (relative)", "PE/PVC 4, cast iron 6, plastic sewer 3, concrete sewer 3, power 10, telephone 2, fibre 2", "clearance trial, pit ranking"],
        ["Pit cost (relative)", "1 + 0.5 × depth (m)", "pit ranking"],
        ["Horizontal and depth error", "GNSS 0.05 m (RTK-class) or 3 m; picking 0.10 + 0.05 d m; velocity 10%; depth picking 0.05 m", "closed form"]]
H.caption(doc, "**Table 2.** Assumptions register. Every value is an assumption; none is a measurement.", keep_next=True)
H.table(doc, rows, widths=[2.7, 2.6, 1.2], size=8)
HD("4.8 Verification of the code and reproducibility", 2)
P("The %d self-tests compare closed-form detection probabilities with Monte Carlo estimates for five cells (single band, dual band with correlation, EM with coupling), the simulation engine with the closed form, the mean presence and persistence of the Markov chain with analytic values, the filter with a cumulative likelihood ratio when *h* = *r* = 0, "
  "the position-error formulae with sampling, the bookkeeping of confusion fractions and weights, determinism under a fixed seed and the number of configurations in the closed-form reference grid. For example, the fused dual-band probability for a concrete sewer at 3.5 m in moist loam is 0.1598 in closed form and 0.1591 by simulation (standard error 0.0006). "
  "These tests check the code against its own mathematics. They are not validation against reality. The repository contains a pinned requirements file, the configuration, results.json, the figure script and a manifest with file hashes; the command to regenerate everything is given in Appendix B." % ntot, align="justify")


HD("4.9 Extended world, models and statistics (version 1.1)", 2)
P("The extended experiments use a second generator (SubSurface_v4.py) that leaves the version 1.0 results unchanged. A corridor has a lateral position that follows the Markov process of Section 3.5 in the truth world: geometry **straight** (no shifts), **curved** (a lateral drift of one step with probability 0.1 per segment), "
  "**shifted** (0.5 shifts per 100 m of 1 to 4 m) or **shifted frequent** (1.5 per 100 m), or **interrupted** (frequent loss and return). Seven survey passes are simulated at lateral positions \u22124, \u22123, \u22122, 0, 2, 3 and 4 m, plus two repeat passes on the centre line that serve as an equal-effort baseline; "
  "every pass has independent noise and the EM coupling of a utility is common to all passes. A map-quality factor sets the starting position and the anchor: **accurate**; **offset** (the reference alignment is 1.5 to 3 m from the utility); **incomplete** (no anchor, so the filter starts from a broad prior); "
  "**misleading** (the anchor belongs to another network half of the time but the filter assumes certainty). A sparse-coverage factor drops half of the observations. Sensor health is drawn per corridor (Table 8). "
  "Two **unseen soils**, wet clay and saline fill (two-way attenuation 30 and 12 dB/m at 250 MHz, segment noise 7 and 8 dB, clutter 0.05 and 0.08), are used only as test soils; the filter treats them as the nearest seen soil (clay and rubble fill). "
  "For orientation, the low-loss relation between conductivity and attenuation (Annan, 2009) gives implied conductivities of %s mS/m (dry sand) to %s mS/m (wet clay) for the assumed attenuations and relative permittivities; these should be compared with site measurements and are not claimed to represent any specific soil." % (
      "%.1f" % R4["attenuation_consistency"]["dry_sand"]["implied_conductivity_mS_per_m"], "%.0f" % R4["attenuation_consistency"]["wet_clay"]["implied_conductivity_mS_per_m"]), align="justify")
P("Six models are run on the same simulated detections: EM only; GPR only (dual band); per-segment GPR + EM fusion; the version 1.0 continuity-aware filter on the centre pass; the same filter with three repeat passes on the centre line (equal survey effort); "
  "and the proposed layer (lateral tracking, latent EM coupling, sensor health, capability zones, reference check where stated) with one centre pass or three parallel passes (\u22123, 0, +3 m). "
  "The truth label is that the utility lies within 1 m of the reference alignment (the excavation footprint); in scenarios with an offset map it is that the utility is present anywhere in the \u00b15 m swath, because otherwise no segment is positive. "
  "Metrics are computed from the per-segment calls (present, absent, unverified): sensitivity among decided segments, false clearance (the share of released, that is called-absent, segments that are truly occupied), false-alarm rate, unverified share, released share and modelled intersections per km (released occupied segments per km of corridor). "
  "Each scenario has 5 blocks of 100 corridors per soil-by-utility cell (17,500 corridors for the seen soils); intervals are 95%% percentile intervals of %d cluster-bootstrap resamples that resample whole corridors within each cell (Efron, 1979; Field and Welsh, 2007), so neighbouring segments are never treated as independent. "
  "Calibration error is averaged over blocks. The same seeds are used for all models within a scenario." % R4["meta"]["bootstrap_draws"], align="justify")
H.caption(doc, "**Table 8.** Added assumptions of version 1.1 (all are assumptions). Diagnostic rates are probabilities that the health diagnostic reports the stated state.", keep_next=True)
dg = A4["health"]["diag"]
H.table(doc, [["Quantity", "Value used"],
              ["Lateral grid", "21 offsets, \u22125 m to +5 m, 0.5 m; footprint \u00b11 m"],
              ["Lateral penalty", "10 dB at one half-width, quadratic, capped at 60 dB; half-widths 0.6 + 0.35 d (GPR), 1.0 + 0.5 d (EM) m"],
              ["Filter rates (per segment)", "loss %.4f, return %.4f, shift %.3f, drift %.2f" % (A4["filter_2d"]["loss_per_seg"], A4["filter_2d"]["rebirth_per_seg"], A4["filter_2d"]["shift_per_seg"], A4["filter_2d"]["drift_per_seg"])],
              ["Health states", "healthy; degraded (6 dB loss); failed (clutter only); mixed: 70%, 20%, 10%"],
              ["Diagnostic", "failed flagged failed %.2f; degraded flagged degraded %.2f (failed %.2f); healthy flagged failed %.2f (degraded %.2f)" % (dg["failed_flagged_failed"], dg["degraded_flagged_degraded"], dg["degraded_flagged_failed"], dg["healthy_flagged_failed"], dg["healthy_flagged_degraded"])],
              ["Capability zones", "A \u2265 0.9; B 0.3 to 0.9; C < 0.3; depth estimate with 10% error"],
              ["Decision thresholds", "\u03c4_P = 0.5; \u03c4_A = 0.1 (0.02 in zone B)"],
              ["Reference check", "%d passes, exact binomial test, \u03b1 = %.2f" % (A4["reference_check"]["n_passes"], A4["reference_check"]["alpha"])],
              ["Costs (US$, scenario assumptions)", "strike %s per consequence unit; holding %s per segment; pit %s + %s per m of depth" % ("{:,.0f}".format(A4["costs_usd"]["strike_per_consequence_unit"]), "{:,.0f}".format(A4["costs_usd"]["hold_per_segment"]), "{:,.0f}".format(A4["costs_usd"]["pit_base"]), "{:,.0f}".format(A4["costs_usd"]["pit_per_m"]))],
              ], widths=[2.0, 4.5], size=8)

HD("4.10 Physical plausibility and external sensor validation", 2)
EP = R4["external_plausibility"]
P("**No published measurement of GPR or EM detection probability against known utility depth and soil was reproduced in this study.** The detection curves of Section 5.1 are therefore outputs of an assumed model, and the paper is a methodological demonstration of a decision policy, not a predictive utility-detection model. "
  "Two independent plausibility checks are reported, neither of which is a validation. First, the low-loss relation between conductivity and attenuation used in Section 4.9 reproduces a worked example given by the US Environmental Protection Agency (US EPA, n.d.): for 100 mS/m and a relative permittivity of 20 it gives %.1f dB/m against the %.0f dB/m published (a difference of %.0f%%). "
  "Second, the one-way attenuations implied by the assumed values at 250 MHz (%.2f dB/m for dry sand, %.1f dB/m for clay, %.1f dB/m for wet clay) lie within the range tabulated on the same page for clays (1 to 300 dB/m) but well above the value tabulated for dry sand (0.01 dB/m); the table states no frequency and no primary source, and the assumed attenuation lumps absorption, scattering and clutter loss, so this is a plausibility check on orders of magnitude, not on detection. "
  "Because the true parameters may differ from the assumed ones by more than the one-at-a-time sensitivity analysis varies them, Section 5.15 repeats the baseline experiment over a parameter-uncertainty envelope in which each seen soil\u2019s attenuation is scaled by a factor between 0.25 and 4, the threshold, budget and spreading loss are varied, and the filter keeps the nominal parameters. "
  "A comparison with a measured detection-versus-depth dataset is the most important missing step and is listed in Section 6.4." % (
      EP["worked_example"]["low_loss_formula_db_per_m"], EP["worked_example"]["published_attenuation_db_per_m"], 100 * abs(EP["worked_example"]["low_loss_formula_db_per_m"] / EP["worked_example"]["published_attenuation_db_per_m"] - 1),
      EP["assumed_one_way_db_per_m_at_250MHz"]["dry_sand"], EP["assumed_one_way_db_per_m_at_250MHz"]["clay"], EP["assumed_one_way_db_per_m_at_250MHz"]["wet_clay"]), align="justify")
P("**Modelled intersections are not strikes.** A segment released for mechanical excavation that is truly occupied is called a modelled utility intersection in this paper. Whether an intersection becomes a strike depends on excavation practice, hand-digging and vacuum-excavation procedures, locating before digging and operator behaviour, none of which is modelled. "
  "If a fraction *a* of intersections were avoided by such procedures, the expected number of strikes would be (1 \u2212 *a*) times the intersections; no value of *a* is claimed, and the intersection rate is a risk proxy for comparing policies, not a measure of real-world safety performance. False clearance is likewise the share of released segments that are occupied, not the probability of damage.", align="justify")

# =============================================================================================== 5 Results
HD("5. Results")
HD("5.1 Detectability envelope", 2)
P("Figure 2 shows the fused closed-form signal detection probability against depth. It is near 1 at shallow depth in every soil and falls steeply, the more so the higher the attenuation and the weaker the reflector. "
  "Cast-iron water mains and power ducts remain detectable deepest, because of their strong reflectivity and, for EM, their coupling; dielectric fibre and PE/PVC water are the first to fade. Table 3 lists the deepest depth at which the fused probability is at least 0.9.", align="justify")
FIGX(doc, os.path.join(FIG, "fig02_detectability_depth.png"), 6.5, "**Fig. 2.** Fused signal detection probability (dual-band GPR and EM) against depth for each soil and utility type (closed form). Dotted lines mark 0.3 (below which a cell is sensor-blind at mid-depth) and 0.9.", alt="Detection probability against depth")
rows = [["Soil", "PE/PVC water", "Cast-iron water", "Plastic sewer", "Concrete sewer", "Power duct", "Telephone duct", "Dielectric fibre"]]
SOILN = {"dry_sand": "Dry sand", "dry_loam": "Dry loam", "moist_loam": "Moist loam", "clay": "Clay", "rubble_fill": "Rubble fill"}
UT = ["pe_water", "ci_water", "plastic_sewer", "concrete_sewer", "power", "telephone", "fibre"]
for s in SOILN:
    rows.append([SOILN[s]] + ["%.1f" % RD[s][u] for u in UT])
H.caption(doc, "**Table 3.** Deepest depth (m) at which the fused closed-form signal detection probability (dual-band GPR and EM) is at least 0.9.", keep_next=True)
H.table(doc, rows, widths=[1.0] + [0.78] * 7, size=8)
nb = len(m["sensor_blind_cells"])
P("At the mid-depth of each class, %d of 35 cells fall below 0.3 (Fig. S1): plastic and concrete sewers in dry loam, moist loam, clay and rubble fill, which together carry %s%% of the assumed network. In dry sand and for all shallow utilities in every soil the fused probability at mid-depth is 0.90 or higher. "
  "On the closed-form reference grid of %s configurations (5 soils, 7 utilities, 7 depths from 1 to 7 m, 3 GPR configurations, EM on or off) the probability is at least 0.9 for %s%% of configurations and at most 0.5 for %s%%; a method that maps to 7 m is therefore, in this model, making a claim for which most configurations provide little signal." % (
      nb, pct(unv, 0), "{:,}".format(G["n"]), pct(G["share_ge_0p9"], 1), pct(G["share_le_0p5"], 1)), align="justify")
FIGX(doc, os.path.join(FIG, "fig03_detectability_maps.png"), 6.5, "**Fig. S1.** (a) Fused detection probability at the mid-depth of each utility class; outlined cells (below 0.3) are sensor-blind and are reported as unverified. (b) Deepest depth with probability of at least 0.9.", alt="Heat maps of detectability")

HD("5.2 Baselines and ablations", 2)
P("Table 4 and Fig. 3 compare the methods in the two views. On sensor-visible cells every GPR-based method is accurate (%s%% to %s%%). The EM-only proxy reaches %s%% accuracy with a miss rate of %s%% because most utilities in the assumed network do not couple to the locator. "
  "GPR at 250 MHz alone reaches %s%%; the 600 MHz band alone is worse (%s%%) because attenuation is higher, and adding it to the 250 MHz band lowers the false-alarm rate from %s%% to %s%% and raises the miss rate from %s%% to %s%%, a small net change that is consistent with the high correlation between the bands." % (
      mm("gpr600", "visible", "acc"), mm("anch_depthmarg", "visible", "acc"), mm("em_only", "visible", "acc"), mm("em_only", "visible", "miss"), mm("gpr250", "visible", "acc"), mm("gpr600", "visible", "acc"),
      mm("gpr250", "visible", "fa"), mm("gpr_dual", "visible", "fa"), mm("gpr250", "visible", "miss"), mm("gpr_dual", "visible", "miss")), align="justify")
order = ["em_only", "gpr250", "gpr600", "gpr_dual", "rule_or", "rule_and", "seg_flat", "seg_prior", "prop_no_anchor", "anch_gpr", "anch_generic", "anch_tempered", "anch_joint", "anch_depthmarg", "anch_oracle_depth", "anch_full"]
lab = {"em_only": "EM locator only (proxy for current practice)", "gpr250": "GPR 250 MHz", "gpr600": "GPR 600 MHz", "gpr_dual": "GPR dual-band, per segment", "rule_or": "OR rule (any sensor)", "rule_and": "AND rule (GPR and EM)",
       "seg_flat": "GPR + EM, per segment, flat prior", "seg_prior": "GPR + EM, per segment, base-rate prior", "prop_no_anchor": "Propagation, no anchor", "anch_gpr": "Anchored, GPR only", "anch_generic": "Anchored, generic soil likelihoods",
       "anch_tempered": "Anchored, evidence tempered (0.5)", "anch_joint": "Anchored, exact joint GPR bands (diagnostic)", "anch_depthmarg": "Anchored, depth-averaged likelihood (diagnostic)", "anch_oracle_depth": "Anchored, true depth known (diagnostic)",
       "anch_full": "**Framework: anchored, GPR + EM, soil-specific**"}
rows = [["Method", "Vis. acc.", "Vis. miss", "Vis. FA", "All acc.", "All miss", "All FA", "All bal. acc."]]
for k in order:
    b = "**" if k == "anch_full" else ""
    rows.append([lab[k]] + [b + mci(k, "visible", "acc") + b, b + mci(k, "visible", "miss") + b, b + mci(k, "visible", "fa") + b, b + mci(k, "all", "acc") + b, b + mci(k, "all", "miss") + b, b + mci(k, "all", "fa") + b, b + mci(k, "all", "bacc") + b])
H.caption(doc, "**Table 4.** Detection and classification performance (%%; mean over %d blocks, 95%% interval half-width in brackets). Vis. = sensor-visible cells (84%% of the weighted network); All = all 35 cells with sensor-blind cells forced to a binary call. "
          "Miss = missed / truly present segments; FA = false calls / truly empty segments; bal. acc. = mean of 1 − miss and 1 − FA. In the All view %s%% of segments are truly on the alignment." % (META["blocks"], pct(M[anch]["all"]["prev"][0], 0)), keep_next=True)
H.table(doc, rows, widths=[2.35, 0.62, 0.62, 0.62, 0.62, 0.62, 0.62, 0.65], size=7.5)
FIGX(doc, os.path.join(FIG, "fig04_ablation.png"), 6.5, "**Fig. 3.** Accuracy, miss rate and false-alarm rate of the compared methods in sensor-visible cells and in all cells (error bars are 95% intervals over blocks and are mostly smaller than the markers).", alt="Ablation chart")
P("Three findings follow. First, on sensor-visible cells the benefit of the framework over a calibrated per-segment fusion is modest: accuracy rises from %s%% to %s%%, the miss rate falls from %s%% to %s%% and the false-alarm rate from %s%% to %s%%. "
  "Propagation without an anchor gives the same visible-cell results (%s%% accuracy), so in sensor-visible cells it is the continuity prior, not the anchor, that helps. The anchor matters where the sensors are blind: in the all-cell view propagation without an anchor reaches %s%% accuracy and a miss rate of %s%%, against %s%% and %s%% with the anchor, "
  "because the anchored belief starts at 1 and persists through blind stretches while the unanchored one starts at 0.5. That persistence is a prior, and the corresponding false-alarm rate (%s%% against %s%%) is the price of it. Second, soil calibration matters: with generic likelihoods the all-cell accuracy falls from %s%% to %s%% and the miss rate rises from %s%% to %s%%. "
  "Third, a per-segment fusion with a base-rate prior (all-cell miss %s%%, false-alarm %s%%) shows how strongly the all-cell numbers depend on what is assumed about the blind cells, which is why Table 4 does not rank methods on the all-cell view alone." % (
      mm("seg_flat", "visible", "acc"), mm(anch, "visible", "acc"), mm("seg_flat", "visible", "miss"), mm(anch, "visible", "miss"), mm("seg_flat", "visible", "fa"), mm(anch, "visible", "fa"), mm("prop_no_anchor", "visible", "acc"),
      mm("prop_no_anchor", "all", "acc"), mm("prop_no_anchor", "all", "miss"), mm(anch, "all", "acc"), mm(anch, "all", "miss"), mm(anch, "all", "fa"), mm("prop_no_anchor", "all", "fa"),
      mm("anch_generic", "all", "acc") if False else mm(anch, "all", "acc"), mm("anch_generic", "all", "acc"), mm(anch, "all", "miss"), mm("anch_generic", "all", "miss"), mm("seg_prior", "all", "miss"), mm("seg_prior", "all", "fa")), align="justify")
P("The diagnostics bound what better modelling could add. Averaging the likelihood over the depth range of the class rather than using the mid-depth lowers the visible-cell miss rate from %s%% to %s%%, and knowing the true depth lowers it to %s%%; an exact joint likelihood for the two GPR bands lowers it to %s%%. "
  "Depth knowledge, for example from velocity calibration, is therefore worth more in this model than modelling the correlation between bands. The EM locator contributes little in aggregate: the anchored GPR-only variant has a visible-cell miss rate of %s%% against %s%% with EM, because GPR already covers most of the assumed network. "
  "EM contributes where it provides a second route to detection, notably cast iron and power (miss rates of %s%% and %s%% in Table 6, against %s%% and %s%% for EM alone)." % (
      mm(anch, "visible", "miss"), mm("anch_depthmarg", "visible", "miss"), mm("anch_oracle_depth", "visible", "miss"), mm("anch_joint", "visible", "miss"), mm("anch_gpr", "visible", "miss"), mm(anch, "visible", "miss"),
      pc(m["cells"]["anch_full_by_utility"]["ci_water"]["miss"]), pc(m["cells"]["anch_full_by_utility"]["power"]["miss"]), pc(m["cells"]["em_only_by_utility"]["ci_water"]["miss"]), pc(m["cells"]["em_only_by_utility"]["power"]["miss"])), align="justify")

HD("5.3 Three-state output and unverified coverage", 2)
tp, fn, fp, tn = TS["truth_present_called_present"], TS["truth_present_called_absent"], TS["truth_absent_called_present"], TS["truth_absent_called_absent"]
tu, au_ = TS["truth_present_unverified"], TS["truth_absent_unverified"]
rows = [["Share of all segments (%)", "Called present", "Called absent", "Unverified", "Total"],
        ["Truly on the alignment", pct(tp, 2), pct(fn, 2), pct(tu, 2), pct(tp + fn + tu, 2)],
        ["Truly not on the alignment", pct(fp, 2), pct(tn, 2), pct(au_, 2), pct(fp + tn + au_, 2)],
        ["Total", pct(tp + fp, 2), pct(fn + tn, 2), pct(tu + au_, 2), "100"]]
H.caption(doc, "**Table 5.** Three-state output of the framework, mixed network (mean over blocks; fractions of all segments). The unverified column is the %s%% of the network in sensor-blind cells; no present or absent call is issued there." % pct(unv, 0), keep_next=True)
H.table(doc, rows, widths=[2.3, 1.0, 1.0, 1.0, 0.8], size=8.5)
P("The segments in blind cells are not mostly empty: %s%% of the network is truly on the alignment there and %s%% is not, so unverified is not a statement that the utility is probably absent. Among the %s%% of segments on which a call is issued, a present call is wrong in %s%% of cases and an absent call is wrong in %s%% of cases; "
  "the missed segments (%s%% of all segments) are the principal residual risk of the framework in visible cells, and the probability attached to them is what the verification ranking uses. Table 6 breaks the results down by utility. "
  "The sewers are visible only in dry sand, and there the mid-depth rule is coarse: a sewer at the deep end of its 3 to 7 m range is poorly detectable although the cell is labelled visible, which is why their visible-cell miss rates (%s%% and %s%%) are high. "
  "A depth-resolved unverified rule would label those segments unverified; this is a limitation of the cell-level rule used here. The all-cell false-alarm rates of the sewers (%s%% and %s%%) are the continuity prior speaking in the blind cells." % (
      pct(tu, 1), pct(au_, 1), pct(decided, 0), pct(fp / (tp + fp), 1), pct(fn / (fn + tn), 1), pct(fn, 1),
      pc(m["cells"]["anch_full_by_utility"]["plastic_sewer"]["miss_visible"]), pc(m["cells"]["anch_full_by_utility"]["concrete_sewer"]["miss_visible"]),
      pc(m["cells"]["anch_full_by_utility"]["plastic_sewer"]["fa"]), pc(m["cells"]["anch_full_by_utility"]["concrete_sewer"]["fa"])), align="justify")
UN = {"pe_water": "PE/PVC water", "ci_water": "Cast-iron water", "plastic_sewer": "Plastic sewer", "concrete_sewer": "Concrete sewer", "power": "Power duct", "telephone": "Telephone duct", "fibre": "Dielectric fibre"}
rows = [["Utility", "Framework miss, visible cells", "Framework miss, all cells", "Framework FA, all cells", "EM-only miss, all cells"]]
for u in UT:
    a = m["cells"]["anch_full_by_utility"][u]
    e = m["cells"]["em_only_by_utility"][u]
    rows.append([UN[u], pc(a["miss_visible"]) if a["miss_visible"] is not None else "n/a", pc(a["miss"]), pc(a["fa"]), pc(e["miss"])])
H.caption(doc, "**Table 6.** Results by utility (%, mean over blocks and equal-weighted soils). The sewer rows include sensor-blind soils in the all-cell columns and should not be read as detection performance.", keep_next=True)
H.table(doc, rows, widths=[1.6, 1.3, 1.2, 1.2, 1.2], size=8.5)
FIGX(doc, os.path.join(FIG, "fig05_belief_trace.png"), 6.4, "**Fig. S2.** One simulated corridor in clay (dielectric fibre at 1.8 m; fused detection probability 0.59, whereas the filter assumes the mid-depth value 0.90). The anchored belief decays within a few segments of the anchor although the utility is present, an illustration of how a depth greater than the filter assumes makes non-detections look more informative than they are.", alt="Belief trace along a corridor")

HD("5.4 Probability calibration", 2)
P("Calibration is a property separate from the miss and false-alarm rates in Table 4. Fig. 4a shows that the framework's reported probabilities have an ECE of %s (Brier score %s). Probabilities near 0 and 1 are reliable: %s%% of segments are reported above 0.9 and %s%% of those are on the alignment, while the %s%% reported below 0.1 are in fact on the alignment %s%% of the time. "
  "The middle of the range is under-confident: segments reported between 0.1 and 0.4 are on the alignment %s%% to %s%% of the time. A low probability is therefore a reason to prioritise verification, not a clearance. "
  "Calibration with generic soil likelihoods is worse (ECE %s) and the per-segment fusion is less calibrated than the filter (ECE %s). The correction of an isotonic map fitted on two blocks and tested on the other three reduces the ECE from %s to %s and the Brier score from %s to %s, which shows that the miscalibration is systematic and correctable in simulation; "
  "whether it is correctable in the field depends on having ground-truth data for fitting, and the held-out blocks here share the simulator's assumptions with the fitting blocks." % (
      "%.3f" % cal[anch]["ece"][0], "%.3f" % cal[anch]["brier"][0], pct(pb["high_share"][0], 0), pct(pb["high_correct"][0], 1), pct(pb["share"][0], 0), pct(pb["occupied"][0], 1),
      pct(min(cal[anch]["bins"]["mean_y"][1:4]), 0), pct(max(cal[anch]["bins"]["mean_y"][1:4]), 0), "%.3f" % cal["anch_generic"]["ece"][0], "%.3f" % cal["seg_flat"]["ece"][0],
      "%.3f" % m["recalibration"]["before"]["ece"][0], "%.3f" % m["recalibration"]["after"]["ece"][0], "%.3f" % m["recalibration"]["before"]["brier"][0], "%.3f" % m["recalibration"]["after"]["brier"][0]), align="justify")
FIGX(doc, os.path.join(FIG, "fig06_calibration.png"), 6.5, "**Fig. 4.** Calibration. (a) Reliability curves; (b) distribution of reported probabilities for the framework; (c) the framework before and after an isotonic recalibration fitted on separate blocks.", alt="Reliability diagrams")

HD("5.5 Stress tests", 2)
hz = S["hazard"]
sh = S["shift"]
an = S["anchor"]
fl = S["sensor_failure"]
hm = S["hazard_misspecified"]
P("**Loss hazard and class balance.** Accuracy of the framework rises from %s%% to %s%% as the loss hazard rises from 0.05 to 1.0 per 100 m (Fig. S3a, b) but this is mostly a change of class balance: the share of segments truly on the alignment falls from %s%% to %s%% and the accuracy of the trivial rule \"always absent\" rises from %s%% to %s%%. "
  "Balanced accuracy changes by only %.1f points (%s%% to %s%%). Behind it the error profile changes: with more frequent losses the filter lags more (miss rate %s%% to %s%%) and false alarms fall (%s%% to %s%%). Accuracy should not be compared across scenarios with different prevalence without the balanced measure." % (
      pc(hz["0.05"]["anch_full"]["all"]["acc"][0]), pc(hz["1.0"]["anch_full"]["all"]["acc"][0]), pc(CB["0.05"]["prev"][0]), pc(CB["1.0"]["prev"][0]), pc(CB["0.05"]["always_absent_acc"][0]), pc(CB["1.0"]["always_absent_acc"][0]),
      100 * (CB["1.0"]["bacc"][0] - CB["0.05"]["bacc"][0]), pc(CB["0.05"]["bacc"][0]), pc(CB["1.0"]["bacc"][0]), pc(CB["0.05"]["miss"][0]), pc(CB["1.0"]["miss"][0]), pc(CB["0.05"]["fa"][0]), pc(CB["1.0"]["fa"][0])), align="justify")
P("**Hazard assumed by the filter.** If the filter assumes a hazard between 0.05 and 2.0 per 100 m while the truth is 0.2, all-cell accuracy changes from %s%% to %s%% and visible-cell accuracy from %s%% to %s%% (Fig. S3f): the framework is not sensitive to this assumption in visible cells." % (
    pc(hm["0.05"]["anch_full"]["all"]["acc"][0]), pc(hm["2.0"]["anch_full"]["all"]["acc"][0]), pc(hm["0.05"]["anch_full"]["visible"]["acc"][0]), pc(hm["2.0"]["anch_full"]["visible"]["acc"][0])), align="justify")
P("**Lateral shifts.** The most damaging stress is a utility that moves sideways but is still partly seen. When 25%%, 50%% and 100%% of losses are lateral shifts, accuracy falls to %s%%, %s%% and %s%%, and the all-cell false-alarm rate rises from %s%% to %s%%, %s%% and %s%%, because the displaced utility still returns a weaker signal and the filter keeps calling it present. "
  "Per-segment fusion falls almost as far (%s%%, %s%%, %s%%), so this is a weakness of the sensing and of the one-dimensional model, not of the propagation. A shift-aware filter and parallel survey passes across the carriageway are natural remedies, and neither is tested here." % (
      pc(sh["0.25"]["anch_full"]["all"]["acc"][0]), pc(sh["0.5"]["anch_full"]["all"]["acc"][0]), pc(sh["1.0"]["anch_full"]["all"]["acc"][0]), pc(sh["0.0"]["anch_full"]["all"]["fa"][0]), pc(sh["0.25"]["anch_full"]["all"]["fa"][0]), pc(sh["0.5"]["anch_full"]["all"]["fa"][0]), pc(sh["1.0"]["anch_full"]["all"]["fa"][0]),
      pc(sh["0.25"]["seg_flat"]["all"]["acc"][0]), pc(sh["0.5"]["seg_flat"]["all"]["acc"][0]), pc(sh["1.0"]["seg_flat"]["all"]["acc"][0])), align="justify")
P("**Uncertain anchor.** If the anchor is on the alignment with probability 0.9, 0.7 and 0.5 but the filter assumes certainty, all-cell accuracy falls from %s%% to %s%%, %s%% and %s%%, below that of per-segment fusion at 0.5 (%s%%). A filter that knows the anchor reliability recovers (%s%%, %s%%, %s%%) by trading false alarms (%s%% at reliability 0.5) for misses (%s%%, against %s%% with a certain anchor). "
  "Accuracy rises when the anchor is less reliable partly because more segments are then truly empty. The framework therefore needs the reliability of each anchor as an input, and an overconfident anchor is worse than none." % (
      pc(an["1.0"]["overconfident"]["all"]["acc"][0]), pc(an["0.9"]["overconfident"]["all"]["acc"][0]), pc(an["0.7"]["overconfident"]["all"]["acc"][0]), pc(an["0.5"]["overconfident"]["all"]["acc"][0]), pc(an["0.5"]["per_segment"]["all"]["acc"][0]),
      pc(an["0.9"]["calibrated"]["all"]["acc"][0]), pc(an["0.7"]["calibrated"]["all"]["acc"][0]), pc(an["0.5"]["calibrated"]["all"]["acc"][0]), pc(an["0.5"]["calibrated"]["all"]["fa"][0]), pc(an["0.5"]["calibrated"]["all"]["miss"][0]), pc(an["1.0"]["calibrated"]["all"]["miss"][0])), align="justify")
P("**Sensor failure and dropped observations.** A GPR that is dead in 10%%, 25%% and 50%% of runs, with the filter unaware, lowers accuracy to %s%%, %s%% and %s%%; a dead EM locator changes it by less than 0.2 percentage points, which restates the small aggregate contribution of EM in this model and not that EM is unimportant for the utilities it detects. "
  "Dropping up to half of the observations leaves visible-cell accuracy near %s%%, because the continuity prior bridges gaps. Detection of a failed sensor is the missing piece, and the framework as specified does not include it." % (
      pc(fl["0.1"]["gpr"]["all"]["acc"][0]), pc(fl["0.25"]["gpr"]["all"]["acc"][0]), pc(fl["0.5"]["gpr"]["all"]["acc"][0]), pc(S["dropout"]["0.5"]["visible"]["acc"][0])), align="justify")
FIGX(doc, os.path.join(FIG, "fig07_stress_tests.png"), 6.5, "**Fig. S3.** Stress tests (accuracy in all cells unless stated). (a) Loss hazard; (b) class balance: accuracy, balanced accuracy, the trivial \"always absent\" rule and the share of segments truly present; (c) share of losses that are lateral shifts; "
         "(d) probability that the anchor is on the alignment; (e) dead sensor; (f) hazard assumed by the filter.", alt="Stress test panels")

HD("5.6 Excavation clearance at equal coverage, equal risk and equal cost", 2)
P("**A correction.** Version 1 of this manuscript compared a binary map that releases segments with *p* \u2264 0.5 with a three-state rule that releases segments with *p* < 0.1, and reported about four times fewer modelled intersections for the second. That comparison confounded the rule with the operating point: the binary map released %s%% of the corridor and the three-state rule %s%%. "
  "Here every policy releases the same share of the corridor, by ranking segments from lowest to highest probability (the three-state rule never releases an unverified segment, and the EM and GPR baselines rank by detection) and counting released segments that are truly occupied." % (pc(R["decision"]["policies"]["anchored fusion, binary map (absent = clear)"]["cleared"][0], 0), pc(R["decision"]["policies"]["anchored fusion, three-state, clear if p<0.10"]["cleared"][0], 0)), align="justify")
rows = [["Policy", "20%", "30%", "40%", "50%", "Coverage at \u2264 1% intersection rate", "at \u2264 5%"]]
for p_ in ("em_only", "gpr_dual", "seg_flat", "anch_binary", "anch_three_state", "random"):
    rows.append([EC["policies"][p_]["label"]] + [cvr(EC, p_, c) for c in (0.2, 0.3, 0.4, 0.5)] + [eqr(EC, p_, "0.01") + "%", eqr(EC, p_, "0.05") + "%"])
H.caption(doc, "**Table 7.** Utility modelled intersections per km of corridor when a given share of the corridor is released for mechanical excavation (matched model; mean over %d blocks), and the share that can be released at a maximum intersection rate among released segments." % META["blocks"], keep_next=True)
H.table(doc, rows, widths=[2.6, 0.55, 0.55, 0.55, 0.55, 1.0, 0.65], size=8)
FIGX(doc, os.path.join(FIG4, "fig08_equal_coverage.png"), 6.5, "**Fig. 5.** Clearance at equal coverage. (a) Modelled intersections per km against released coverage in the matched model; (b) the same when half of utility losses are lateral shifts; (c) share of the corridor that can be released at equal maximum intersection rate; (d) strike plus holding cost against released coverage (scenario assumptions, survey cost excluded).", alt="Equal-coverage clearance comparison")
P("At equal coverage the differences are small. At 30%% of the corridor released the anchored filter has %s modelled intersections per km, per-segment fusion %s, GPR alone %s and the EM locator %s; at equal risk (intersection rate among released segments of at most 1%%) the anchored filter can release %s%% of the corridor against %s%% for per-segment fusion, "
  "a gain of about %.1f percentage points. The three-state rule is not safer than the binary ranking at equal coverage: at 30%% it has %s modelled intersections per km (binary: %s) and at 40%% it has %s (binary %s), because it holds back blind segments that are, in this model, mostly empty. "
  "When half of utility losses are lateral shifts, intersections at 30%% rise to %s (binary) and %s (three-state), and the coverage at a intersection rate of at most 1%% falls to %s%% and %s%%. "
  "With the assumed costs, the minimum of strike plus holding cost is US$%s per km at %s%% coverage for the anchored filter and US$%s per km at %s%% for GPR alone, a difference of %.1f%%." % (
      cvr(EC, "anch_binary", 0.3), cvr(EC, "seg_flat", 0.3), cvr(EC, "gpr_dual", 0.3), cvr(EC, "em_only", 0.3), eqr(EC, "anch_binary", "0.01"), eqr(EC, "seg_flat", "0.01"), float(eqr(EC, "anch_binary", "0.01")) - float(eqr(EC, "seg_flat", "0.01")),
      cvr(EC, "anch_three_state", 0.3), cvr(EC, "anch_binary", 0.3), cvr(EC, "anch_three_state", 0.4), cvr(EC, "anch_binary", 0.4), cvr(EH, "anch_binary", 0.3), cvr(EH, "anch_three_state", 0.3), eqr(EH, "anch_binary", "0.01"), eqr(EH, "anch_three_state", "0.01"),
      "{:,.0f}".format(mincost(EC, "anch_binary")[0]), pc(mincost(EC, "anch_binary")[1], 0), "{:,.0f}".format(mincost(EC, "gpr_dual")[0]), pc(mincost(EC, "gpr_dual")[1], 0), 100 * (1 - mincost(EC, "anch_binary")[0] / mincost(EC, "gpr_dual")[0])), align="justify")
P("The value of the layer in this comparison is therefore modest in the matched model: calibrated probabilities allow a few points more corridor to be released at the same risk, and the operating point becomes explicit. "
  "What the unverified state adds is not fewer modelled intersections at equal coverage but a refusal to release where capability is not established, whose benefit depends on conditions the matched model does not contain (Sections 5.10 to 5.13).", align="justify")

HD("5.7 Location and depth accuracy", 2)
P("Location and depth errors are treated separately from detection, by a closed-form error model rather than by simulation of radargrams. The horizontal error combines positioning error with a picking error that grows with depth (0.10 + 0.05 m per metre of depth), and the depth error combines a 10%% velocity uncertainty with 0.05 m of picking. "
  "With RTK-class positioning (0.05 m) the probability that the horizontal error is within 1 m is %s at 1 m depth, %s at 5 m and %s at 7 m; depth within 0.5 m is %s at 1 m, %s at 2 m, %s at 3.5 m, %s at 5 m and %s at 7 m. With stand-alone GNSS (3 m) the probability of meeting a 1 m horizontal requirement is about %s whatever the depth. "
  "Survey-grade positioning or local control is therefore a precondition of metre-level horizontal accuracy in this model, and depth accuracy degrades with depth because velocity uncertainty is proportional to it. These numbers follow from the assumed error model; they are not measurements. Fig. S4 shows the curves." % (
      "%.3f" % POS["rtk"]["horizontal_within_1m"][0], "%.2f" % POS["rtk"]["horizontal_within_1m"][3], "%.2f" % POS["rtk"]["horizontal_within_1m"][4], "%.2f" % POS["rtk"]["depth_within_0p5m"][0], "%.2f" % POS["rtk"]["depth_within_0p5m"][1],
      "%.2f" % POS["rtk"]["depth_within_0p5m"][2], "%.2f" % POS["rtk"]["depth_within_0p5m"][3], "%.2f" % POS["rtk"]["depth_within_0p5m"][4], "%.2f" % POS["standalone"]["horizontal_within_1m"][2]), align="justify")
FIGX(doc, os.path.join(FIG, "fig09_position_depth.png"), 5.8, "**Fig. S4.** Closed-form location and depth error model. (a) Probability that the horizontal error is within 1 m. (b) Probability that the depth error is within 0.5 m (RTK-class positioning).", alt="Position and depth error curves")

HD("5.8 Cross-sections and shadowing by overlying lines", 2)
T = SEC["table"]
P("Three representative arrangements of utilities in a road section are often of interest: parallel utilities at different depths (A), a water line stacked directly above a sewer in a shared trench (B) and a sewer and fibre beneath a transverse water line (C). Using depths of 3.5 m for sewers, 1.8 m for water and fibre and 0.8 m for ducts, "
  "an overlying line shadows the lower utility by 3 dB (PE/PVC) or 10 dB (cast iron) in the model. Fig. S5 shows the resulting fused detection probability. A concrete sewer at 3.5 m is detected in dry sand (%s) but in dry loam falls from %s without shadowing to %s beneath PE/PVC and %s beneath cast iron; "
  "in moist loam it is %s, %s and %s, and in clay at most %s. Fibre in clay falls from %s to %s beneath an overlying PE/PVC line, while shallow ducts stay at 1.00 in every soil. Closed-form values agree with direct simulation within 0.003 for three checked cells." % (
      "%.2f" % T["dry_sand"]["Concrete sewer, A"], "%.2f" % T["dry_loam"]["Concrete sewer, A"], "%.2f" % T["dry_loam"]["Sewer, B (PE/PVC above)"], "%.2f" % T["dry_loam"]["Sewer, B (cast iron above)"],
      "%.2f" % T["moist_loam"]["Concrete sewer, A"], "%.2f" % T["moist_loam"]["Sewer, B (PE/PVC above)"], "%.2f" % T["moist_loam"]["Sewer, B (cast iron above)"], "%.2f" % max(T["clay"]["Concrete sewer, A"], T["clay"]["Sewer, B (PE/PVC above)"]), "%.2f" % T["clay"]["Fibre, A"], "%.2f" % T["clay"]["Fibre, C (PE/PVC above)"]), align="justify")
FIGX(doc, os.path.join(FIG, "fig10_cross_sections.png"), 5.6, "**Fig. S5.** Fused detection probability for utilities in the three cross-section arrangements, with shadowing by an overlying water line (closed form).", alt="Cross-section detection probabilities")

HD("5.9 Sensitivity, re-scanning and correlated evidence", 2)
items = SENS["items"]
base = SENS["base"]
rng_acc = sorted(items, key=lambda it: -abs(it["high"]["acc"] - it["low"]["acc"]))
P("**Parameter sensitivity.** Fig. S6 shows the change in all-cell accuracy and visible-cell miss rate when one parameter is changed at a time, with common random numbers. The results are most sensitive to the soil attenuation, the spreading loss, the system budget and the detection threshold, which move the detectability envelope: "
  "for example attenuation scaled by 0.75 and 1.25 gives all-cell accuracy of %s%% and %s%% (base %s%%), with an unverified share of %s%% and %s%% (base %s%%). Changes in the noise terms, the EM coupling and the band correlation have small effects. "
  "The conclusions about the structure of the framework therefore hold across these ranges, but the numerical values, including the share of the network that is unverified, are properties of the assumed detectability envelope." % (
      pc([i for i in items if i["name"].startswith("soil attenuation")][0]["low"]["acc"]), pc([i for i in items if i["name"].startswith("soil attenuation")][0]["high"]["acc"]), pc(base["acc"]),
      pc([i for i in items if i["name"].startswith("soil attenuation")][0]["low"]["unverified_share"], 0), pc([i for i in items if i["name"].startswith("soil attenuation")][0]["high"]["unverified_share"], 0), pc(base["unverified_share"], 0)), align="justify")
rs = R["rescan"]
ks = list(rs.keys())
P("**Repeat passes.** Segments whose belief lies between 0.15 and 0.85 were re-scanned immediately (95%% availability) or later (25%% chance, offline), in the four harder soils. The visible-cell miss rate is %s%% without a re-scan, %s%% offline and %s%% on the spot, with the repeat pass decorrelated from the first (%s%%); false alarms fall from %s%% to %s%%. "
  "Re-scans covered %s%% of segments offline and %s%% on the spot. A repeat pass does not reduce the miss rate even when its noise is independent, because the remaining misses are caused by weak signal and not by noise. In this model, connectivity that enables immediate re-scanning is not needed for detection." % (
      pc(rs[ks[0]]["visible"]["miss"][0]), pc(rs[ks[1]]["visible"]["miss"][0]), pc(rs[ks[2]]["visible"]["miss"][0]), pc(rs[ks[4]]["visible"]["miss"][0]), pc(rs[ks[0]]["visible"]["fa"][0], 2), pc(rs[ks[2]]["visible"]["fa"][0], 2), pc(rs[ks[1]]["rescan_fraction"][0]), pc(rs[ks[2]]["rescan_fraction"][0])), align="justify")
cr = S["correlation"]
P("**Correlated evidence.** The filter assumes independence, while in the simulation the two GPR bands are correlated (0.7) and a GPR-EM correlation of up to 0.9 is added. The correlation between GPR and EM noise changes visible-cell accuracy by less than 0.2 percentage points, because EM contributes little in aggregate. "
  "The ECE of the framework is %s at zero correlation and %s at 0.9; tempering the evidence by a factor of 0.5 gives %s and %s, and an exact joint likelihood for the two bands %s and %s (Fig. S7b). Miscalibration from the independence assumption is therefore present but small compared with the miscalibration that comes from the depth and the continuity prior." % (
      "%.3f" % cr["0.0"]["independent"]["calibration"]["ece"][0], "%.3f" % cr["0.9"]["independent"]["calibration"]["ece"][0], "%.3f" % cr["0.0"]["tempered"]["calibration"]["ece"][0], "%.3f" % cr["0.9"]["tempered"]["calibration"]["ece"][0], "%.3f" % cr["0.0"]["joint_gpr"]["calibration"]["ece"][0], "%.3f" % cr["0.9"]["joint_gpr"]["calibration"]["ece"][0]), align="justify")
FIGX(doc, os.path.join(FIG, "fig11_sensitivity.png"), 6.5, "**Fig. S6.** One-at-a-time sensitivity of (a) all-cell accuracy and (b) visible-cell miss rate of the framework. Circles and squares are the first and second value named on the axis; the dotted line is the base case.", alt="Sensitivity")
FIGX(doc, os.path.join(FIG, "fig12_rescan_correlation.png"), 6.5, "**Fig. S7.** (a) Effect of a repeat pass on uncertain segments (visible cells in the four harder soils); ρ is the correlation of the run-level noise of the repeat pass with the first. (b) Calibration error under correlated GPR and EM noise for three evidence rules.", alt="Re-scan and correlated evidence")

HD("5.10 Lateral tracking", 2)
P("Fig. 6 sweeps the frequency of lateral shifts (0 to 4 per 100 m) with shifts of 1 to 4 m. The version 1.0 filter on one centre pass has a false-alarm rate that rises from %s%% without shifts to %s%% at 0.25 shifts per 100 m and stays near %s%%; three repeat passes on the centre line change little (%s%%). "
  "The proposed layer with one centre pass behaves like the version 1.0 filter (%s%% at 2 shifts per 100 m), because one pass cannot tell a displaced utility from an absent one. With three parallel passes the false-alarm rate stays at %s%% to %s%% over the whole range, and the share of segments whose lateral error is at most 0.5 m falls from %s%% to %s%% as shifts become frequent. "
  "False clearance falls with more frequent shifts for all models because fewer segments are on the footprint (%s%% for the version 1.0 filter and %s%% for the proposed three-pass layer at 2 per 100 m). "
  "Calibration error grows with shift frequency for every model (version 1.0: %s to %s; proposed three-pass: %s to %s). Small shifts (1 to 2 m) are harder than large ones: false alarms are %s%% for the version 1.0 filter and %s%% for the proposed three-pass layer with small shifts, against %s%% and %s%% with shifts of 3 to 4 m, "
  "because a large shift moves the utility out of the footprint and out of range of the centre pass, so the version 1.0 filter loses the signal. The comparison is at three times the survey effort for the parallel passes; the equal-effort baseline of three repeat passes on the centre line does not reproduce the effect." % (
      sw("0.0", "continuity_1d", "false_alarm"), sw("0.25", "continuity_1d", "false_alarm"), sw("2.0", "continuity_1d", "false_alarm"), sw("2.0", "continuity_1d_3rep", "false_alarm"), sw("2.0", "proposed_1pass", "false_alarm"),
      sw("0.25", "proposed_3pass", "false_alarm"), sw("4.0", "proposed_3pass", "false_alarm"), swl("0.0", "proposed_3pass"), swl("4.0", "proposed_3pass"), sw("2.0", "continuity_1d", "false_clearance"), sw("2.0", "proposed_3pass", "false_clearance"),
      swe("0.0", "continuity_1d"), swe("4.0", "continuity_1d"), swe("0.0", "proposed_3pass"), swe("4.0", "proposed_3pass"),
      pc(SWP["magnitude"]["small_1_to_2_m"]["continuity_1d"]["metrics"]["false_alarm"][0]), pc(SWP["magnitude"]["small_1_to_2_m"]["proposed_3pass"]["metrics"]["false_alarm"][0]),
      pc(SWP["magnitude"]["large_3_to_4_m"]["continuity_1d"]["metrics"]["false_alarm"][0]), pc(SWP["magnitude"]["large_3_to_4_m"]["proposed_3pass"]["metrics"]["false_alarm"][0])), align="justify")
FIGX(doc, os.path.join(FIG4, "fig13_lateral_robustness.png"), 6.5, "**Fig. 6.** Robustness to lateral displacement of the utility: (a) false-alarm rate, (b) false clearance among released segments, (c) expected calibration error, (d) share of segments with lateral error of at most 0.5 m, against the number of lateral shifts per 100 m (95% cluster-bootstrap intervals where shown).", alt="Lateral robustness")
HD("5.11 Sensor health", 2)
rows = [["Scenario", "Per-segment fusion", "Version 1.0 filter", "Proposed, three passes", "Proposed: unverified"]]
for key, lab_ in (("baseline", "A: both healthy"), ("B_gpr_failed_flagged", "B: GPR failed, flagged"), ("C_gpr_failed_unflagged", "C: GPR failed, not flagged"), ("D_both_degraded", "D: both degraded"), ("mixed_health_realistic_diagnostic", "Mixed health, imperfect diagnostic")):
    rows.append([lab_, sci(key, "fusion", "false_clearance"), sci(key, "continuity_1d", "false_clearance"), sci(key, "proposed_3pass", "false_clearance"), sci(key, "proposed_3pass", "unverified")])
H.caption(doc, "**Table 9.** False clearance among released segments (%) and unverified share (%) under sensor failure and degradation (mean and 95% cluster-bootstrap interval).", keep_next=True)
H.table(doc, rows, widths=[2.0, 1.1, 1.1, 1.2, 1.2], size=8)
FIGX(doc, os.path.join(FIG4, "fig14_sensor_health.png"), 6.5, "**Fig. 7.** Classification under sensor degradation and failure: (a) false clearance among released segments, (b) unverified share, (c) sensitivity among decided segments.", alt="Sensor health scenarios")
P("When the GPR has failed and the failure is flagged (B), the per-segment methods and the version 1.0 filter read its silence as absence and clear %s%% to %s%% of the released segments wrongly; the proposed layer treats the GPR as uninformative, marks %s%% of the corridor unverified and has a false clearance of %s%% among the %s%% it still releases. "
  "When the failure is not flagged (C) every method fails alike (%s%% for the proposed layer): the protection is only as good as the diagnostic, and the assumed sensitivity of 0.90 and false-flag rate of 0.02 are assumptions. "
  "With both sensors degraded (D) the proposed layer reduces false clearance from %s%% to %s%%, and with mixed health and an imperfect diagnostic from %s%% to %s%% at the cost of %s%% unverified against %s%%. "
  "A good result here is not higher accuracy: it is that unreliable evidence moves segments to unverified instead of clearing them." % (
      sm("B_gpr_failed_flagged", "continuity_1d", "false_clearance", 0), sm("B_gpr_failed_flagged", "fusion", "false_clearance", 0), sm("B_gpr_failed_flagged", "proposed_3pass", "unverified", 0), sm("B_gpr_failed_flagged", "proposed_3pass", "false_clearance"),
      sm("B_gpr_failed_flagged", "proposed_3pass", "released", 0), sm("C_gpr_failed_unflagged", "proposed_3pass", "false_clearance", 0),
      sm("D_both_degraded", "continuity_1d", "false_clearance"), sm("D_both_degraded", "proposed_3pass", "false_clearance"), sm("mixed_health_realistic_diagnostic", "continuity_1d", "false_clearance"), sm("mixed_health_realistic_diagnostic", "proposed_3pass", "false_clearance"),
      sm("mixed_health_realistic_diagnostic", "proposed_3pass", "unverified"), sm("mixed_health_realistic_diagnostic", "continuity_1d", "unverified")), align="justify")
HD("5.12 Capability zones and the depth-resolved rule", 2)
P("Fig. S8 shows the zones for the seven soils as functions of depth. Over the grid of depths from 0.5 to 7 m in the five seen soils, %s%% of the combinations are zone A, %s%% zone B and %s%% zone C. "
  "Applying the zones at the estimated depth instead of the class mid-depth changes which segments are unverified: the unverified share falls from %s%% (cell-level rule) to %s%%, because shallow parts of the sewer classes become decidable, and the false clearance of the sewers is high either way (plastic sewer %s%%, concrete sewer %s%% with the cell-level rule). "
  "Requiring a much lower probability for an absent call in zone B, and an unverified band between the two thresholds, lowers the sewers\u2019 false clearance to %s%% and %s%% and the overall false clearance from %s%% to %s%%, at an unverified share of %s%%. "
  "Zone B is therefore treated as marginal evidence, not as clearance capability. For zone C the escalation of Section 3.7 applies." % (
      pc(ZT["share_in_distribution_grid"]["A"], 0), pc(ZT["share_in_distribution_grid"]["B"], 0), pc(ZT["share_in_distribution_grid"]["C"], 0), pc(DR["rules"]["cell_level"]["unverified"][0], 0), pc(DR["rules"]["depth_resolved"]["unverified"][0], 0),
      pc(DR["false_clearance_by_utility"]["cell_level"]["plastic_sewer"][0], 0), pc(DR["false_clearance_by_utility"]["cell_level"]["concrete_sewer"][0], 0),
      pc(DR["false_clearance_by_utility"]["depth_resolved_tau"]["plastic_sewer"][0], 0), pc(DR["false_clearance_by_utility"]["depth_resolved_tau"]["concrete_sewer"][0], 0), pc(DR["rules"]["cell_level"]["false_clearance"][0]), pc(DR["rules"]["depth_resolved_tau"]["false_clearance"][0]), pc(DR["rules"]["depth_resolved_tau"]["unverified"][0], 0)), align="justify")
FIGX(doc, os.path.join(FIG4, "fig15_capability_zones.png"), 6.5, "**Fig. S8.** Capability zones by soil, utility and depth (closed form): zone A detectable (fused probability at least 0.9), zone B marginal, zone C capability not established (below 0.3). The two lower rows are the unseen soils.", alt="Capability zones")
HD("5.13 Model comparison across scenarios and unseen soils", 2)
names = [("baseline", "baseline"), ("curved", "curved"), ("shifted", "shifted"), ("shifted_frequent", "shifted, frequent"), ("interrupted", "interrupted"), ("map_offset", "map offset (swath label)"), ("map_incomplete", "no anchor"), ("map_misleading", "misleading anchor"),
         ("sparse_coverage", "sparse coverage"), ("mixed_health_realistic_diagnostic", "mixed sensor health"), ("ood_soils", "unseen soils, reference check"), ("ood_soils_no_guard", "unseen soils, no check"), ("combined_stress", "combined stress")]
rows = [["Scenario", "Fusion", "v1.0 filter", "v1.0, 3 repeats", "Proposed, 1 pass", "Proposed, 3 passes", "Unverified (proposed, 3)"]]
for key, lab_ in names:
    rows.append([lab_] + [sci(key, m_, "false_clearance") for m_ in ("fusion", "continuity_1d", "continuity_1d_3rep", "proposed_1pass", "proposed_3pass")] + [sm(key, "proposed_3pass", "unverified", 0)])
H.caption(doc, "**Table 10.** False clearance among released segments (%, mean and 95% cluster-bootstrap interval) for the six-model comparison; last column unverified share (%). Full tables are in the Supplementary Material.", keep_next=True)
H.table(doc, rows, widths=[1.5, 0.85, 0.85, 0.85, 0.9, 0.95, 0.7], size=7)
FIGX(doc, os.path.join(FIG4, "fig16_model_comparison.png"), 6.4, "**Fig. 8.** False clearance and unverified share for five models in twelve scenarios (95% cluster-bootstrap intervals; logarithmic axis in (a)).", alt="Model comparison")
P("In the baseline the proposed layer with three passes has a false clearance of %s%% against %s%% for the version 1.0 filter, %s%% for the filter with three repeat passes and %s%% for per-segment fusion; with one pass it has %s%%, close to the version 1.0 filter, and a worse calibration error (%s against %s). "
  "Across the scenarios the layer helps most when its extra machinery is exercised: shifted or curved geometry, sparse coverage, a map offset by 1.5 to 3 m (where the centre-line models find %s%% of present segments and the three-pass layer %s%%), and mixed sensor health. It does not help when the sensors are blind in the same way (unflagged GPR failure) or when the soil is unseen. "
  "The additional compute is small in absolute terms: %.2f s per block of 3,500 corridors for the three-pass layer against %.2f s for the version 1.0 filter." % (
      sm("baseline", "proposed_3pass", "false_clearance"), sm("baseline", "continuity_1d", "false_clearance"), sm("baseline", "continuity_1d_3rep", "false_clearance"), sm("baseline", "fusion", "false_clearance"), sm("baseline", "proposed_1pass", "false_clearance"),
      secs("baseline", "proposed_1pass"), secs("baseline", "continuity_1d"), sm("map_offset", "continuity_1d", "sensitivity", 0), sm("map_offset", "proposed_3pass", "sensitivity", 0),
      SC["baseline"]["models"]["proposed_3pass"]["compute_seconds_per_block"], SC["baseline"]["models"]["continuity_1d"]["compute_seconds_per_block"]), align="justify")
P("**Unseen soils.** In wet clay and saline fill, with the filter using the nearest seen soil, the proposed layer without a check has a false clearance of %s%% and the version 1.0 filter %s%%. The reference check flags %s%% of the corridors in the unseen soils and %s%% in the seen soils; with the check, the proposed layer\u2019s false clearance falls to %s%% and its unverified share rises to %s%%. "
  "Calibration error stays poor in the unseen soils (%s with the check): the check removes the corridors that are furthest from the model, not the miscalibration of the rest. The remedy for unseen conditions is site-specific calibration and a larger unverified share, not a better filter. "
  "In all comparisons the models share the same detections, and all intervals are cluster-bootstrap intervals; they describe simulation noise, not the uncertainty of the assumptions." % (
      sm("ood_soils_no_guard", "proposed_3pass", "false_clearance"), sm("ood_soils_no_guard", "continuity_1d", "false_clearance"), pc(SC["ood_soils"]["reference_check_flag_share"], 0), pc(SC["baseline_with_reference_check"]["reference_check_flag_share"], 1),
      sm("ood_soils", "proposed_3pass", "false_clearance"), sm("ood_soils", "proposed_3pass", "unverified", 0), secs("ood_soils", "proposed_3pass")), align="justify")
FIGX(doc, os.path.join(FIG4, "fig17_out_of_distribution.png"), 6.4, "**Fig. 9.** Seen and unseen soils with and without the on-site reference check: (a) false clearance, (b) unverified share, (c) calibration error.", alt="Unseen soils")
HD("5.14 Value of information and trial-pit allocation", 2)
P("With a holding cost of US$1,000 per segment, pits cost more than the holding they avoid for almost every segment, and ranking pits by value of information selects almost none (change in total cost against no pits: %.1f thousand US$ per km at a pit budget of 5%% of the cost of pitting every candidate); ranking by probability alone adds %.1f thousand and random placement %.1f thousand. "
  "With a holding cost of US$10,000 per segment, value-of-information ranking lowers the total cost by %.1f thousand US$ per km at 5%% and %.1f thousand at 40%%, a saving of about %s%% of the total, with an interval that includes zero at the larger budgets, whereas probability-first and random pits add cost. "
  "Pits are valuable in this model only where the cost of holding a segment is high relative to the cost of a pit, and the benefit is small (under 2%% of total cost) because a pit resolves one segment only; neighbouring segments are not updated by it, which understates its value. The comparison depends entirely on the assumed costs." % (
      voi("1000.0", "value_of_information", 0.05)[0] / 1000, voi("1000.0", "probability", 0.05)[0] / 1000, voi("1000.0", "random", 0.05)[0] / 1000,
      -voi("10000.0", "value_of_information", 0.05)[0] / 1000, -voi("10000.0", "value_of_information", 0.4)[0] / 1000, pc(-voi("10000.0", "value_of_information", 0.4)[0] / voi("10000.0", "value_of_information", 0.4, "total_cost_usd_per_km")[0], 1)), align="justify")
FIGX(doc, os.path.join(FIG4, "fig18_value_of_information.png"), 6.4, "**Fig. S9.** Change in total cost (pits, holding and modelled strike costs) against the pit budget for three allocation rules and three holding costs (paired differences against no pits; 95% intervals over blocks).", alt="Value of information")


HD("5.15 Structural mismatch and parameter uncertainty", 2)
GM = R4["geometry_mismatch"]["levels"]
PE = R4["parameter_envelope"]
P("In every scenario so far the truth process is close to the process the filter assumes. To test whether the conclusions survive a structurally different truth, utility geometry was generated as a piecewise-linear path with abrupt bends (leg lengths of 8 to 25 segments, slopes up to 0.25 m per segment, unrelated to the filter\u2019s transition model), "
  "then with a second, parallel utility 2 to 5 m away that also returns signals, and then with a branch that leaves the utility at a random position and adds to the truth where it lies on the excavation footprint. The filters are unchanged. Fig. 10 and Table 11 show how false clearance, false alarms and calibration change as the assumed geometry becomes increasingly wrong.", align="justify")
rows = [["Geometry", "Fusion", "v1.0 filter", "v1.0, 3 repeats", "Proposed, 1 pass", "Proposed, 3 passes", "ECE (v1.0 / proposed 3)"]]
for lv in GM:
    rows.append([lv["name"]] + [("%s [%s, %s]" % tuple(pc(x) for x in lv["models"][m]["metrics"]["false_clearance"])) for m in ("fusion", "continuity_1d", "continuity_1d_3rep", "proposed_1pass", "proposed_3pass")]
                + ["%.3f / %.3f" % (lv["models"]["continuity_1d"]["ece"][0], lv["models"]["proposed_3pass"]["ece"][0])])
H.caption(doc, "**Table 11.** False clearance among released segments (%, mean and 95% cluster-bootstrap interval) as the truth geometry departs from the filter\u2019s model; last column calibration error.", keep_next=True)
H.table(doc, rows, widths=[1.6, 0.9, 0.9, 0.9, 0.9, 0.95, 0.8], size=7)
FIGX(doc, os.path.join(FIG4, "fig20_geometry_mismatch.png"), 6.5, "**Fig. 10.** Deterioration as the truth geometry departs from the filter\u2019s model (L0 matched to L4 bends with a parallel utility and a branch): (a) false clearance among released segments, (b) false-alarm rate, (c) calibration error.", alt="Structural mismatch")
l0, l2, l4 = GM[0]["models"], GM[2]["models"], GM[4]["models"]
P("With abrupt bends (L2) the false clearance of the proposed three-pass layer is %s%% (L0: %s%%) and that of the version 1.0 filter %s%% (L0: %s%%). The result changes sign when a second utility runs nearby: with a parallel utility (L3) and with a parallel utility and a branch (L4) the false clearance of the three-pass layer rises to %s%% and %s%%, "
  "against %s%% and %s%% for the one-pass version 1.0 filter, while its false-alarm rate falls to %s%% and %s%% (version 1.0: %s%% and %s%%). The lateral tracker attributes the returns to the best-fitting offset, takes the parallel line for the target, and clears the excavation footprint; the one-pass filters keep calling present and are safe in this respect only because they cannot tell the lines apart. "
  "Calibration error grows from %.3f to %.3f for the three-pass layer and from %.3f to %.3f for the version 1.0 filter. Lateral tracking is therefore not uniformly beneficial: it reduces false alarms under lateral shifts, but with parallel utilities it trades false alarms for false clearance, which is the wrong direction for safety, and the matched-model advantage should not be read as general." % (
      pc(l2["proposed_3pass"]["metrics"]["false_clearance"][0]), pc(l0["proposed_3pass"]["metrics"]["false_clearance"][0]), pc(l2["continuity_1d"]["metrics"]["false_clearance"][0]), pc(l0["continuity_1d"]["metrics"]["false_clearance"][0]),
      pc(GM[3]["models"]["proposed_3pass"]["metrics"]["false_clearance"][0]), pc(l4["proposed_3pass"]["metrics"]["false_clearance"][0]), pc(GM[3]["models"]["continuity_1d"]["metrics"]["false_clearance"][0]), pc(l4["continuity_1d"]["metrics"]["false_clearance"][0]),
      pc(GM[3]["models"]["proposed_3pass"]["metrics"]["false_alarm"][0]), pc(l4["proposed_3pass"]["metrics"]["false_alarm"][0]), pc(GM[3]["models"]["continuity_1d"]["metrics"]["false_alarm"][0]), pc(l4["continuity_1d"]["metrics"]["false_alarm"][0]),
      l0["proposed_3pass"]["ece"][0], l4["proposed_3pass"]["ece"][0], l0["continuity_1d"]["ece"][0], l4["continuity_1d"]["ece"][0]), align="justify")
sp = PE["summary"]
P("**Parameter envelope.** Over %d draws of the true sensor parameters (Section 4.10), the share of the assumed network that is truly sensor-blind ranges from %s%% to %s%% (5th to 95th percentile; median %s%%), against the 16%% of the nominal model, and the median false clearance is %s%% for per-segment fusion, %s%% for the version 1.0 filter and %s%% for the proposed three-pass layer (5th to 95th percentile: %s to %s, %s to %s and %s to %s %%). "
  "The proposed layer has a lower false clearance than the version 1.0 filter in %s%% of the draws and than per-segment fusion in %s%%. The ranking of the methods is thus fairly robust to the parameters, whereas the absolute level of false clearance, and the share of the network that is unverifiable, are not: they are properties of the assumed sensor model (Fig. S10)." % (
      PE["n_draws"], pc(PE["true_blind_share"][0], 0), pc(PE["true_blind_share"][2], 0), pc(PE["true_blind_share"][1], 0), pc(sp["fusion"]["false_clearance"][1]), pc(sp["continuity_1d"]["false_clearance"][1]), pc(sp["proposed_3pass"]["false_clearance"][1]),
      pc(sp["fusion"]["false_clearance"][0], 0), pc(sp["fusion"]["false_clearance"][2], 0), pc(sp["continuity_1d"]["false_clearance"][0], 0), pc(sp["continuity_1d"]["false_clearance"][2], 0), pc(sp["proposed_3pass"]["false_clearance"][0], 0), pc(sp["proposed_3pass"]["false_clearance"][2], 0),
      pc(PE["share_proposed_better_than_continuity"], 0), pc(PE["share_proposed_better_than_fusion"], 0)), align="justify")
FIGX(doc, os.path.join(FIG4, "fig21_parameter_envelope.png"), 6.4, "**Fig. S10.** Parameter-uncertainty envelope: (a) false clearance of three methods over parameter draws, (b) true sensor-blind share, (c) per-draw false clearance of the proposed layer against the version 1.0 filter.", alt="Parameter envelope")

# =============================================================================================== 6 Discussion
HD("6. Discussion")
HD("6.1 What the simulation demonstrates, suggests and does not establish", 2)
P("**Demonstrated within the model.** (i) A large share of a plausible utility network is invisible to GPR and EM at the depths where it lies, and a map that marks only detections cannot say so. (ii) A filter with lateral tracking and three parallel passes keeps false alarms low when utilities shift sideways, where one-pass filters and repeat passes on the centre line do not. "
  "(iii) A health-aware filter that treats a flagged failed sensor as uninformative removes most of the false clearance that sensor failure causes, provided the failure is flagged. (iv) At equal released coverage the layer is only slightly safer than per-segment fusion in the matched model, and the three-state rule is not safer than a binary ranking there; "
  "an earlier apparent advantage came from comparing different operating points. (v) Soil-specific likelihoods matter; the anchor matters mainly where the sensors are blind; probabilities are well ordered but not calibrated in the mid-range. (vi) In soils unlike those used to set the model, false clearance stays high even with a reference check. (vii) A structurally different geometry degrades the models, and a parallel utility turns the advantage of the lateral tracker into a disadvantage in false clearance; wide parameter uncertainty widens the false clearance of every model.", align="justify")
P("**Suggested, conditionally on the model resembling reality.** Depth knowledge and a depth-resolved capability rule are the cheapest improvements; the health diagnostic is the critical component of sensor-health awareness, and its sensitivity should be measured before the rest is trusted; "
  "parallel passes across the carriageway are needed to follow shifted utilities, at about three times the survey effort; a reference-target check on site is worth running; and a published unverified fraction by soil and depth band would give a client a number with which to compare surveys. "
  "Re-scanning and the connectivity that would allow it add nothing to detection in the model.", align="justify")
P("**Not established.** Whether the sensor model reproduces real GPR and EM behaviour in any soil; the agreement of the detection curves with any measured detection-versus-depth data (none was reproduced); the lateral response of real antennas; the detection probabilities and their dependence on antenna, geometry and operator; the frequency and form of utility displacement; the reliability of anchors and records; the sensitivity and false-flag rate of real health diagnostics; "
  "the real cost and consequences of strikes and the cost of holding a segment; whether crews would use a three-state map as intended; and any result in a specific country, soil or network. The EM-only proxy is a model of an instrument that couples only to some utilities, not a measurement of any product.", align="justify")
HD("6.2 Relation to practice", 2)
P("The framework is designed to complement, not replace, established practice. Quality levels of subsurface utility data " + C("asce02") + " already distinguish records, geophysical detection and exposure; the unverified state states, per segment, that geophysical detection could not have established presence or absence, "
  "and so that the segment sits at the quality of the records until a pit is dug. A probabilistic classification is an input to engineering review, not an authorisation to excavate. The clearance comparison shows that the benefit of such a layer cannot be read from one operating point: at equal coverage the gain over per-segment fusion is a few points of releasable corridor in the matched model, "
  "and larger only in the stressed scenarios in which the extra components are exercised. The consequence weights, the holding cost and the pit cost are the parts of the framework most dependent on local judgement.", align="justify")
HD("6.3 Limitations", 2)
for t in (
    "The lateral model has one utility per corridor with no crossings, branches or parallel lines, a fixed 0.5 m grid and a fixed lateral response; a real survey covers a swath and must decide which response belongs to which utility, and the framework starts after that decision. Depth and class are not tracked in the filter state.",
    "The sensor model is a thresholded signal-to-noise model with Gaussian noise and an assumed spreading loss; it has no radargram, no clutter structure, no antenna pattern and no operator. The attenuation values and the 8 dB threshold determine the detectability envelope, and the sensitivity analysis shows that results are most sensitive to them. No published detection-versus-depth dataset was reproduced, so the model is a methodological demonstration, not a predictive detection model.",
    "The truth process is Markov and matched to the filter in the baseline; the stress scenarios mismatch it only in the directions listed. The unseen soils are two cases, not a distribution of soils.",
    "The health diagnostic, the reference check and the costs are assumed. An unflagged sensor failure defeats every model, and the reference check removes corridors but does not repair calibration.",
    "The unverified rule is evaluated at an estimated depth with an assumed 10% error; depth is fixed within a corridor.",
    "A pit resolves one segment only in the value-of-information analysis. The filter assumes conditional independence, which the simulation violates; the effect is small in the sensitivity analysis.",
    "All uncertainty intervals describe simulation noise; no interval expresses uncertainty about the assumptions, which is the dominant uncertainty.",
):
    H.bullet(doc, t)
HD("6.4 What a field test would need", 2)
P("The first step is external: compare the assumed detection curves with at least one published or newly measured dataset that reports GPR and EM detection across known utility depths and soils, and report the mismatch. The minimum field test then consists of a controlled corridor with known pipe positions, depths and materials in at least two soils, surveyed with a centre pass and parallel passes; GPR and EM data recorded with surveyed positions; a deliberate sensor fault and a reference-target check; the software run offline; and detection, location and depth errors, calibration and unverified coverage reported with the definitions of Section 4.5. "
  "A false clearance of at most 1%% shown with a 95%% upper bound needs about %d released segments with no failure, or about %d with one failure (exact binomial intervals; %s). "
  "The attenuation, threshold, coupling and persistence parameters would be fitted per soil, and the three-state rule validated by trial pits placed by verification priority. Until then the numbers in this paper are properties of the simulator." % (
      [r for r in R4["pilot_sample_sizes"]["false_clearance_or_event_rate"] if r["target_upper_bound"] == 0.01 and r["observed_events"] == 0][0]["n_required"],
      [r for r in R4["pilot_sample_sizes"]["false_clearance_or_event_rate"] if r["target_upper_bound"] == 0.01 and r["observed_events"] == 1][0]["n_required"], C("clopper34", "brown01")), align="justify")

# =============================================================================================== 7 Conclusions
HD("7. Conclusions")
P("A decision layer that turns GPR and EM detections into present, absent and unverified states, with lateral tracking, sensor-health awareness, depth-resolved capability zones and a verification ranking, was specified and evaluated in simulation. The following conclusions apply to the model and not to the field.", align="justify")
for t in (
    "%s%% of the assumed network (plastic and concrete sewers at the depths where they lie, in loam, clay and fill) is sensor-blind at the class mid-depth, and a map that does not say so would convert silence into clearance." % pct(unv, 0),
    "In sensor-visible cells the anchored filter reaches %s%% accuracy (miss %s%%, false alarm %s%%), a modest improvement over calibrated per-segment fusion (%s%%, %s%%, %s%%) and far above the EM-only proxy (%s%% accuracy)." % (
        mm(anch, "visible", "acc"), mm(anch, "visible", "miss"), mm(anch, "visible", "fa"), mm("seg_flat", "visible", "acc"), mm("seg_flat", "visible", "miss"), mm("seg_flat", "visible", "fa"), mm("em_only", "visible", "acc")),
    "At equal released coverage the layer is only slightly safer than per-segment fusion, and the three-state rule is not safer than a binary ranking in the matched model; the apparent fourfold advantage reported in version 1 came from comparing different operating points.",
    "Three parallel passes with lateral tracking hold false alarms near %s%% under frequent lateral shifts where one-pass filters reach %s%%; a flagged sensor failure is handled by treating the sensor as uninformative, but an unflagged failure and unseen soils defeat every model tested (false clearance %s%% and %s%%).",
    "The simulation has not been validated against measured sensor data, and the structural-mismatch and parameter-envelope experiments show that the margins between methods are fragile outside the matched model.",
    "The most useful next step is a field test with ground truth that measures the health diagnostic, the lateral response and the soil attenuation, because these assumptions decide the results.",
):
    H.bullet(doc, t if "%s%% and %s%%)" not in t else t % (sw("2.0", "proposed_3pass", "false_alarm"), sw("2.0", "continuity_1d", "false_alarm"), sm("C_gpr_failed_unflagged", "proposed_3pass", "false_clearance", 0), sm("ood_soils", "proposed_3pass", "false_clearance", 0)))
P("The study fixes definitions and a protocol, and shows which assumptions the conclusions rest on. It cannot show field performance, which requires data with known ground truth.", align="justify")

# =============================================================================================== declarations
HD("Declarations", 1)
P("**CRediT authorship contribution statement.** Leon Sandler: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Visualization, Writing – original draft, Writing – review and editing.", align="justify")
P("**Funding.** This research received no specific grant from any funding agency in the public, commercial or not-for-profit sectors.", align="justify")
P("**Declaration of competing interests.** The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.", align="justify")
P("**Prior dissemination.** An earlier, non-peer-reviewed white paper describing the concept was prepared in response to an open innovation challenge on detecting underground utilities issued through the Wazoku (InnoCentive) platform. "
  "Its numerical results came from an earlier version of the simulation whose code was not available when this manuscript was prepared; the simulation was reimplemented from the method description and all numbers in this paper come from the released code. The challenge submission is not a publication and the present manuscript is not under consideration elsewhere.", align="justify")
P("**Version history.** Version 1 of this preprint (https://doi.org/" + PP_V1 + ") compared a binary map and a three-state rule at different released coverages and reported about four times fewer strikes for the three-state rule; that comparison is withdrawn. "
  "Version 2 (https://doi.org/" + PP_V2 + ") compared policies at equal coverage, equal risk and equal cost and added lateral tracking, sensor-health awareness, capability zones, unseen soils, cluster-bootstrap intervals and a value-of-information analysis. "
  "Version 3 (this version) adds a comparison with the closest existing approaches, a physical-plausibility section, a structural-mismatch experiment, a parameter-uncertainty envelope, the wording “modelled intersections” for what earlier versions called strikes, and a reduced set of main-text figures. Numbers of earlier versions that are quoted here are unchanged.", align="justify")
P("**Data and code availability.** All code, the configurations, results.json and results_v4.json, the figure scripts, tests and the manuscript builders are available at %s (release %s) and are archived on Zenodo (software: https://doi.org/%s, all versions https://doi.org/%s; manuscript preprint: https://doi.org/%s, all versions https://doi.org/%s). "
  "Every table and figure is regenerated by the commands in Appendix B. No field data were used." % (REPO, RELEASE, SW, SW_CONCEPT, PP, PP_CONCEPT), align="justify")
P("**Declaration of generative AI and AI-assisted technologies in the writing process.** During the preparation of this work the author used Claude (Anthropic; Claude Sonnet 5.5, accessed through Claude Code) to help write and run the simulation code, generate figures and draft and edit the text. "
  "The simulation outputs were produced by running the released code with a fixed seed and were not written by the model. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the publication.", align="justify")
P("**Acknowledgements.** None.", align="justify")

# =============================================================================================== appendices
HD("Appendix A. Filter details", 1)
P("Likelihoods in the filter are floored so that no single observation yields a probability of exactly 0 or 1: the total detection probability of each sensor (signal or clutter) is capped at %s and the belief is clipped to [10^{−9}, 1 − 10^{−9}] in log-odds arithmetic. "
  "The total detection probability of a sensor when the utility is present is *P*_{d} + (1 − *P*_{d})*P*_{fa}, since clutter can produce a detection whether or not the signal does; for the EM locator *P*_{d} includes the coupling probability. "
  "For the exact joint variant the four outcomes of the two GPR bands are weighted by the bivariate normal probabilities of the two signal detections. Unverified status is evaluated once per cell from the closed-form fused probability at the class mid-depth and does not depend on the data of a corridor." % "0.999", align="justify")
HD("Appendix B. Reproducing the results", 1)
for line in ("pip install -r requirements.txt", "python SubSurface_MC.py --demo                 # %d self-tests" % ntot, "python SubSurface_MC.py --grid-size             # 1,470 closed-form configurations",
             "python SubSurface_MC.py --reproduce --out results --n 500 --blocks 10 --seed 42", "python figure_generation.py --results results/results.json --out results/figures", "python SubSurface_v4.py --demo                 # 13 self-tests of the version 1.1 code", "python SubSurface_v4.py --reproduce --out results_v4 --seed 42", "python figure_generation_v4.py --results results_v4/results_v4.json --out results_v4/figures", "python tests/test_subsurface.py"):
    p = doc.add_paragraph()
    r = p.add_run(line)
    r.font.name = "Courier New"
    r.font.size = Pt(9.5)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
P("")
P("The reproduce commands take a few minutes (SubSurface_MC.py about %d s). A fresh clone of the release was run and its results files compared with the archived ones (see the repository README). results.json records the command, the seed, the library versions (Python %s, NumPy %s, SciPy %s), the configuration and every table quoted in this paper." % (round(META["runtime_s"]), META["python"], META["numpy"], META["scipy"]), align="justify")

# =============================================================================================== references
HD("References", 1)
for key in ("numpy20", "scipy20", "mpl07"):
    K._note(key)
P("The simulation uses NumPy " + C("numpy20") + ", SciPy " + C("scipy20") + " and Matplotlib " + C("mpl07") + ".", align="justify")
BODY[0] = False
REFLINES = K.reference_list()
EPA = "US EPA (n.d.). Environmental Geophysics: Ground Penetrating Radar (Table 1, electromagnetic properties of earth materials). U.S. Environmental Protection Agency. https://archive.epa.gov/esd/archive-geophysics/web/html/ground-penetrating_radar.html (accessed 11 October 2026)."
pos = [i for i, l in enumerate(REFLINES) if l.startswith("Virtanen")]
REFLINES.insert(pos[0] if pos else len(REFLINES), EPA)
for line in REFLINES:
    p = H.para(doc, line, size=9.5, space_after=3)
    p.paragraph_format.left_indent = Pt(18)
    p.paragraph_format.first_line_indent = Pt(-18)
    p.paragraph_format.line_spacing = 1.1

os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
import json as _json
_json.dump(SUPP, open(os.path.join(HERE, "out", "supp_figs.json"), "w"), indent=1)
out = os.path.join(HERE, "out", "Manuscript_TUST.docx")
doc.save(out)
print("saved", out)
print("abstract words:", AB_WORDS, "body words (approx, excl. refs/tables):", WORDS["body"], "references:", len(K.USED))
