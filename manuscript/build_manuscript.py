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

# =============================================================================================== title page
P("**" + TITLE + "**", align="center", size=15, space_after=10)
P("Leon Sandler", align="center", size=12, space_after=0)
P("Independent Researcher, Northbrook, Illinois, USA", align="center", size=10.5, space_after=0)
P("ORCID: 0009-0007-4584-808X • Corresponding author: sandler.leon@gmail.com", align="center", size=10.5, space_after=12)
P("Manuscript submitted to *Tunnelling and Underground Space Technology* (original research article). Software: %s (archived at https://doi.org/%s). Preprint: https://doi.org/%s." % (REPO, SW, PP), align="center", size=9.5, space_after=14)

HD("Abstract", 2)
ABSTRACT = (
    "Excavation near buried utilities relies on maps whose reliability is rarely stated. Ground-penetrating radar (GPR) and electromagnetic (EM) locators report detections, "
    "but a missing detection is weak evidence where soil attenuates the signal, and utility records are themselves uncertain. This paper proposes and evaluates, in simulation only, "
    "a decision layer that combines dual-band GPR, an EM locator and an anchor (a manhole or chamber of known network identity) along a corridor of 5 m segments with a Bayesian filter. "
    "Each segment is reported as present, absent or unverified; unverified marks soil, utility and depth combinations whose expected detection probability is below 0.3. "
    "A seeded Monte Carlo study (%d blocks of %s corridors of %d segments) compares fifteen baselines and ablations and reports detection, probability calibration, location and depth error and unverified coverage separately. "
    "In sensor-visible cells the framework reaches %s%% accuracy (miss rate %s%%, false-alarm rate %s%%), against %s%% for calibrated per-segment fusion and %s%% for an EM-only proxy; "
    "%s%% of the assumed network is unverified. Reported probabilities have an expected calibration error of %s. In a simulated clearance trial the three-state rule lowers strikes per kilometre by a factor of about %.1f relative to a binary map, "
    "while releasing %s percentage points less of the corridor. Lateral shifts of utilities, uncertain depth, GPR failure and an incorrectly certain anchor degrade performance substantially. "
    "All parameters are assumptions and no field data are used: the results indicate where field trials are needed, not how the method performs in the field."
) % (META["blocks"], "{:,}".format(N_CORR), META["segments_per_corridor"], mm(anch, "visible", "acc"), mm(anch, "visible", "miss"), mm(anch, "visible", "fa"), mm("seg_flat", "visible", "acc"), mm("em_only", "visible", "acc"),
     pct(unv, 0), "%.3f" % cal[anch]["ece"][0], POL["anchored fusion, binary map (absent = clear)"]["strikes_per_km"][0] / POL[pol_name(0.1)]["strikes_per_km"][0],
     "%.0f" % (100 * (POL["anchored fusion, binary map (absent = clear)"]["cleared"][0] - POL[pol_name(0.1)]["cleared"][0])))
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
P("This paper takes that design choice as its subject. It specifies a decision layer that sits above GPR, EM and positioning hardware and evaluates it in a seeded Monte Carlo simulation. The layer has four parts: "
  "(i) utility-specific anchors, such as a manhole of known network identity, that start a belief; (ii) likelihoods that depend on soil, material and depth; (iii) a Bayesian filter that carries the belief along the corridor; and (iv) a three-state output (present, absent, unverified) "
  "together with a verification-priority ranking for trial pits. The contributions are:", align="justify")
for t in (
    "a formulation in which the unverified state is derived from the expected detectability of each soil, utility and depth combination, so that it can be reported, counted and audited;",
    "an evaluation protocol that keeps four outcomes apart (detection and classification, probability calibration, location and depth accuracy, and the share of the network left unverified), with explicit denominators;",
    "baselines, ablations and stress tests that show which components carry the performance and where it fails, including lateral shifts, depth mis-specification, sensor failure, an uncertain anchor and correlated evidence; and",
    "a decision-consequence experiment that compares excavation-clearance policies by strikes per kilometre and corridor released, and compares trial-pit allocation rules.",
):
    H.bullet(doc, t)
P("**Scope.** Everything reported here is a simulation under stated assumptions. The sensor model is a thresholded signal-to-noise model with parameters chosen to give a plausible range of detectability, not fitted to field data, and the EM locator is represented only to the extent that "
  "its coupling to the utility is probabilistic. The simulation tests the logic of the decision layer and its sensitivity to its own assumptions. It cannot show how the layer would perform on real corridors, and the Discussion says what would be needed to find out.", align="justify")

# =============================================================================================== 2 Background
HD("2. Background and related work")
HD("2.1 Sensors and their limits", 2)
P("GPR responds to contrasts in dielectric permittivity and can detect metallic and non-metallic utilities, but its range is set by attenuation in the ground, which depends strongly on soil type and moisture " + C("doolittle95", "annan09")
  + ". Higher frequencies give finer resolution and stronger attenuation. EM locators detect the field around a conductor, either passive (power or radio signals already present) or active (a transmitter couples a signal into the line), and therefore depend on a conductive path that may not exist for plastic pipes and dielectric fibre. "
  "The two sensors are complementary in the materials they see and in how they fail, which is the usual argument for combining them " + C("metje07", "costello07") + ".", align="justify")
HD("2.2 Fusion of GPR and EM data", 2)
P("Fusion of GPR with induction-based sensing has been studied most extensively for buried-object detection, at feature and decision levels " + C("stanley02") + " and with evidence-theoretic combination of radar data " + C("milis03")
  + ". Work on the combination of correlated decisions " + C("tesf12") + " is relevant here because the two GPR bands and, in poor soils, GPR and EM can fail together. For utilities, multi-sensor data have been combined into three-dimensional location estimates " + C("dou16")
  + ". The present paper does not propose a new detector or a new fusion operator. It takes detections as given and asks how they should be turned into a probabilistic, auditable statement about each segment.", align="justify")
HD("2.3 Probabilistic mapping, reject options and calibration", 2)
P("Maintaining a probability of occupancy per cell and updating it with each observation is established in robot mapping " + C("elfes89") + ". The corridor filter used here is a one-dimensional relative of that idea with a persistence prior along the alignment. "
  "Classifiers with a reject option, which decline to decide when the evidence is weak, trade error against coverage " + C("chow70") + "; the unverified state plays that role, with the difference that it is set by expected detectability rather than by the posterior alone. "
  "Probabilities are useful for decisions only if they are calibrated. Calibration and sharpness are distinct properties of probabilistic forecasts " + C("gneiting07b") + ", scored by proper scoring rules such as the Brier score " + C("brier50", "gneiting07a")
  + ", which decomposes into reliability, resolution and uncertainty " + C("murphy73") + ". Methods exist to recalibrate scores " + C("zadrozny02", "niculescu05", "naeini15") + ", and the independence assumption of naive combination of evidence can give good decisions while giving poor probabilities "
  + C("domingos97", "hand01") + ", which is the situation examined in Sections 5.4 and 5.9. Accuracy depends on how many segments are truly occupied, which changes with the corridor and with the loss hazard, and precision-recall or balanced measures are more informative when classes are imbalanced "
  + C("fawcett06", "saito15") + ". The results therefore report balanced accuracy and class prevalence alongside accuracy.", align="justify")

# =============================================================================================== 3 Framework
HD("3. The decision layer")
P("A corridor is divided into segments of 5 m along a tracked alignment, typically the line of a known utility between two access points. For one utility, *b*_{k} is the probability that the utility lies on the tracked alignment in segment *k*. "
  "Figure 1 shows the information flow.", align="justify")
H.figure(doc, os.path.join(FIG, "fig01_framework.png"), 6.4, "**Fig. 1.** The decision layer. Anchors, GPR and the EM locator feed soil- and depth-aware likelihoods; a filter carries the belief along the corridor; each segment is reported as present, absent or unverified, and the residual probabilities rank where trial pits are worth their cost.",
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

# =============================================================================================== 4 Methods
HD("4. Simulation methodology")
P("All results come from one Python file, SubSurface_MC.py (NumPy, SciPy, Matplotlib; %s), run with a fixed seed (%d). The command, versions and every parameter are written to results.json. %d of %d built-in self-tests pass; they check the code against its own mathematics (Section 4.8)." % (
    "%s on Python %s" % (META["numpy"], META["python"]), META["seed"], nst, ntot), align="justify")
HD("4.1 Synthetic corridors", 2)
P("A corridor holds one utility of one type, buried at one depth in one soil, tracked over %d segments of %d m. Five soils (dry sand, dry loam, moist loam, clay, rubble fill) and seven utility types (PE/PVC water, cast-iron water, plastic sewer, concrete sewer, power duct, telephone duct, dielectric fibre) define 35 cells. "
  "Depth is drawn uniformly from a range per utility (sewers 3 to 7 m, water and fibre 1 to 2 m, telephone 0.6 to 1.0 m, power 0.5 to 2 m) and is constant along a corridor. Cells are weighted by an assumed network share (Table 1) with the five soils equally weighted, "
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
  "correlation between GPR and EM noise (0 to 0.9); dropped observations; and a filter that assumes the wrong hazard. A clearance trial compares policies by strikes and corridor released, and a trial-pit experiment compares allocation rules. "
  "A repeat pass on uncertain segments (Section 5.9) examines the value of a re-scan. One-at-a-time sensitivity to ten parameters uses common random numbers (3 blocks of 166 corridors per cell). The intervals are 95%% t-intervals over blocks (half-width in brackets); they describe simulation noise, not uncertainty about the real world." % (
      META["blocks"], "{:,}".format(N_CORR), META["segments_per_corridor"], max(3, META["blocks"] // 2)), align="justify")
HD("4.7 Assumptions register", 2)
P("Table 1 lists the assumptions. They were chosen to give a plausible spread of detectability and to reproduce the qualitative depth envelope of the setting that motivated the study (about 5 m or more in dry sand, 3 to 4 m in dry loam, about 2 m in moist loam and 1 to 2 m in clay); they are not fitted to measurements.", align="justify")
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
H.caption(doc, "**Table 1.** Assumptions register. Every value is an assumption; none is a measurement.", keep_next=True)
H.table(doc, rows, widths=[2.7, 2.6, 1.2], size=8)
HD("4.8 Verification of the code and reproducibility", 2)
P("The %d self-tests compare closed-form detection probabilities with Monte Carlo estimates for five cells (single band, dual band with correlation, EM with coupling), the simulation engine with the closed form, the mean presence and persistence of the Markov chain with analytic values, the filter with a cumulative likelihood ratio when *h* = *r* = 0, "
  "the position-error formulae with sampling, the bookkeeping of confusion fractions and weights, determinism under a fixed seed and the number of configurations in the closed-form reference grid. For example, the fused dual-band probability for a concrete sewer at 3.5 m in moist loam is 0.1598 in closed form and 0.1591 by simulation (standard error 0.0006). "
  "These tests check the code against its own mathematics. They are not validation against reality. The repository contains a pinned requirements file, the configuration, results.json, the figure script and a manifest with file hashes; the command to regenerate everything is given in Appendix B." % ntot, align="justify")

# =============================================================================================== 5 Results
HD("5. Results")
HD("5.1 Detectability envelope", 2)
P("Figure 2 shows the fused closed-form signal detection probability against depth. It is near 1 at shallow depth in every soil and falls steeply, the more so the higher the attenuation and the weaker the reflector. "
  "Cast-iron water mains and power ducts remain detectable deepest, because of their strong reflectivity and, for EM, their coupling; dielectric fibre and PE/PVC water are the first to fade. Table 2 lists the deepest depth at which the fused probability is at least 0.9.", align="justify")
H.figure(doc, os.path.join(FIG, "fig02_detectability_depth.png"), 6.5, "**Fig. 2.** Fused signal detection probability (dual-band GPR and EM) against depth for each soil and utility type (closed form). Dotted lines mark 0.3 (below which a cell is sensor-blind at mid-depth) and 0.9.", alt="Detection probability against depth")
rows = [["Soil", "PE/PVC water", "Cast-iron water", "Plastic sewer", "Concrete sewer", "Power duct", "Telephone duct", "Dielectric fibre"]]
SOILN = {"dry_sand": "Dry sand", "dry_loam": "Dry loam", "moist_loam": "Moist loam", "clay": "Clay", "rubble_fill": "Rubble fill"}
UT = ["pe_water", "ci_water", "plastic_sewer", "concrete_sewer", "power", "telephone", "fibre"]
for s in SOILN:
    rows.append([SOILN[s]] + ["%.1f" % RD[s][u] for u in UT])
H.caption(doc, "**Table 2.** Deepest depth (m) at which the fused closed-form signal detection probability (dual-band GPR and EM) is at least 0.9.", keep_next=True)
H.table(doc, rows, widths=[1.0] + [0.78] * 7, size=8)
nb = len(m["sensor_blind_cells"])
P("At the mid-depth of each class, %d of 35 cells fall below 0.3 (Fig. 3): plastic and concrete sewers in dry loam, moist loam, clay and rubble fill, which together carry %s%% of the assumed network. In dry sand and for all shallow utilities in every soil the fused probability at mid-depth is 0.90 or higher. "
  "On the closed-form reference grid of %s configurations (5 soils, 7 utilities, 7 depths from 1 to 7 m, 3 GPR configurations, EM on or off) the probability is at least 0.9 for %s%% of configurations and at most 0.5 for %s%%; a method that maps to 7 m is therefore, in this model, making a claim for which most configurations provide little signal." % (
      nb, pct(unv, 0), "{:,}".format(G["n"]), pct(G["share_ge_0p9"], 1), pct(G["share_le_0p5"], 1)), align="justify")
H.figure(doc, os.path.join(FIG, "fig03_detectability_maps.png"), 6.5, "**Fig. 3.** (a) Fused detection probability at the mid-depth of each utility class; outlined cells (below 0.3) are sensor-blind and are reported as unverified. (b) Deepest depth with probability of at least 0.9.", alt="Heat maps of detectability")

HD("5.2 Baselines and ablations", 2)
P("Table 3 and Fig. 4 compare the methods in the two views. On sensor-visible cells every GPR-based method is accurate (%s%% to %s%%). The EM-only proxy reaches %s%% accuracy with a miss rate of %s%% because most utilities in the assumed network do not couple to the locator. "
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
H.caption(doc, "**Table 3.** Detection and classification performance (%%; mean over %d blocks, 95%% interval half-width in brackets). Vis. = sensor-visible cells (84%% of the weighted network); All = all 35 cells with sensor-blind cells forced to a binary call. "
          "Miss = missed / truly present segments; FA = false calls / truly empty segments; bal. acc. = mean of 1 − miss and 1 − FA. In the All view %s%% of segments are truly on the alignment." % (META["blocks"], pct(M[anch]["all"]["prev"][0], 0)), keep_next=True)
H.table(doc, rows, widths=[2.35, 0.62, 0.62, 0.62, 0.62, 0.62, 0.62, 0.65], size=7.5)
H.figure(doc, os.path.join(FIG, "fig04_ablation.png"), 6.5, "**Fig. 4.** Accuracy, miss rate and false-alarm rate of the compared methods in sensor-visible cells and in all cells (error bars are 95% intervals over blocks and are mostly smaller than the markers).", alt="Ablation chart")
P("Three findings follow. First, on sensor-visible cells the benefit of the framework over a calibrated per-segment fusion is modest: accuracy rises from %s%% to %s%%, the miss rate falls from %s%% to %s%% and the false-alarm rate from %s%% to %s%%. "
  "Propagation without an anchor gives the same visible-cell results (%s%% accuracy), so in sensor-visible cells it is the continuity prior, not the anchor, that helps. The anchor matters where the sensors are blind: in the all-cell view propagation without an anchor reaches %s%% accuracy and a miss rate of %s%%, against %s%% and %s%% with the anchor, "
  "because the anchored belief starts at 1 and persists through blind stretches while the unanchored one starts at 0.5. That persistence is a prior, and the corresponding false-alarm rate (%s%% against %s%%) is the price of it. Second, soil calibration matters: with generic likelihoods the all-cell accuracy falls from %s%% to %s%% and the miss rate rises from %s%% to %s%%. "
  "Third, a per-segment fusion with a base-rate prior (all-cell miss %s%%, false-alarm %s%%) shows how strongly the all-cell numbers depend on what is assumed about the blind cells, which is why Table 3 does not rank methods on the all-cell view alone." % (
      mm("seg_flat", "visible", "acc"), mm(anch, "visible", "acc"), mm("seg_flat", "visible", "miss"), mm(anch, "visible", "miss"), mm("seg_flat", "visible", "fa"), mm(anch, "visible", "fa"), mm("prop_no_anchor", "visible", "acc"),
      mm("prop_no_anchor", "all", "acc"), mm("prop_no_anchor", "all", "miss"), mm(anch, "all", "acc"), mm(anch, "all", "miss"), mm(anch, "all", "fa"), mm("prop_no_anchor", "all", "fa"),
      mm("anch_generic", "all", "acc") if False else mm(anch, "all", "acc"), mm("anch_generic", "all", "acc"), mm(anch, "all", "miss"), mm("anch_generic", "all", "miss"), mm("seg_prior", "all", "miss"), mm("seg_prior", "all", "fa")), align="justify")
P("The diagnostics bound what better modelling could add. Averaging the likelihood over the depth range of the class rather than using the mid-depth lowers the visible-cell miss rate from %s%% to %s%%, and knowing the true depth lowers it to %s%%; an exact joint likelihood for the two GPR bands lowers it to %s%%. "
  "Depth knowledge, for example from velocity calibration, is therefore worth more in this model than modelling the correlation between bands. The EM locator contributes little in aggregate: the anchored GPR-only variant has a visible-cell miss rate of %s%% against %s%% with EM, because GPR already covers most of the assumed network. "
  "EM contributes where it provides a second route to detection, notably cast iron and power (miss rates of %s%% and %s%% in Table 5, against %s%% and %s%% for EM alone)." % (
      mm(anch, "visible", "miss"), mm("anch_depthmarg", "visible", "miss"), mm("anch_oracle_depth", "visible", "miss"), mm("anch_joint", "visible", "miss"), mm("anch_gpr", "visible", "miss"), mm(anch, "visible", "miss"),
      pc(m["cells"]["anch_full_by_utility"]["ci_water"]["miss"]), pc(m["cells"]["anch_full_by_utility"]["power"]["miss"]), pc(m["cells"]["em_only_by_utility"]["ci_water"]["miss"]), pc(m["cells"]["em_only_by_utility"]["power"]["miss"])), align="justify")

HD("5.3 Three-state output and unverified coverage", 2)
tp, fn, fp, tn = TS["truth_present_called_present"], TS["truth_present_called_absent"], TS["truth_absent_called_present"], TS["truth_absent_called_absent"]
tu, au_ = TS["truth_present_unverified"], TS["truth_absent_unverified"]
rows = [["Share of all segments (%)", "Called present", "Called absent", "Unverified", "Total"],
        ["Truly on the alignment", pct(tp, 2), pct(fn, 2), pct(tu, 2), pct(tp + fn + tu, 2)],
        ["Truly not on the alignment", pct(fp, 2), pct(tn, 2), pct(au_, 2), pct(fp + tn + au_, 2)],
        ["Total", pct(tp + fp, 2), pct(fn + tn, 2), pct(tu + au_, 2), "100"]]
H.caption(doc, "**Table 4.** Three-state output of the framework, mixed network (mean over blocks; fractions of all segments). The unverified column is the %s%% of the network in sensor-blind cells; no present or absent call is issued there." % pct(unv, 0), keep_next=True)
H.table(doc, rows, widths=[2.3, 1.0, 1.0, 1.0, 0.8], size=8.5)
P("The segments in blind cells are not mostly empty: %s%% of the network is truly on the alignment there and %s%% is not, so unverified is not a statement that the utility is probably absent. Among the %s%% of segments on which a call is issued, a present call is wrong in %s%% of cases and an absent call is wrong in %s%% of cases; "
  "the missed segments (%s%% of all segments) are the principal residual risk of the framework in visible cells, and the probability attached to them is what the verification ranking uses. Table 5 breaks the results down by utility. "
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
H.caption(doc, "**Table 5.** Results by utility (%, mean over blocks and equal-weighted soils). The sewer rows include sensor-blind soils in the all-cell columns and should not be read as detection performance.", keep_next=True)
H.table(doc, rows, widths=[1.6, 1.3, 1.2, 1.2, 1.2], size=8.5)
H.figure(doc, os.path.join(FIG, "fig05_belief_trace.png"), 6.4, "**Fig. 5.** One simulated corridor in clay (dielectric fibre at 1.8 m; fused detection probability 0.59, whereas the filter assumes the mid-depth value 0.90). The anchored belief decays within a few segments of the anchor although the utility is present, an illustration of how a depth greater than the filter assumes makes non-detections look more informative than they are.", alt="Belief trace along a corridor")

HD("5.4 Probability calibration", 2)
P("Calibration is a property separate from the miss and false-alarm rates in Table 3. Fig. 6a shows that the framework's reported probabilities have an ECE of %s (Brier score %s). Probabilities near 0 and 1 are reliable: %s%% of segments are reported above 0.9 and %s%% of those are on the alignment, while the %s%% reported below 0.1 are in fact on the alignment %s%% of the time. "
  "The middle of the range is under-confident: segments reported between 0.1 and 0.4 are on the alignment %s%% to %s%% of the time. A low probability is therefore a reason to prioritise verification, not a clearance. "
  "Calibration with generic soil likelihoods is worse (ECE %s) and the per-segment fusion is less calibrated than the filter (ECE %s). The correction of an isotonic map fitted on two blocks and tested on the other three reduces the ECE from %s to %s and the Brier score from %s to %s, which shows that the miscalibration is systematic and correctable in simulation; "
  "whether it is correctable in the field depends on having ground-truth data for fitting, and the held-out blocks here share the simulator's assumptions with the fitting blocks." % (
      "%.3f" % cal[anch]["ece"][0], "%.3f" % cal[anch]["brier"][0], pct(pb["high_share"][0], 0), pct(pb["high_correct"][0], 1), pct(pb["share"][0], 0), pct(pb["occupied"][0], 1),
      pct(min(cal[anch]["bins"]["mean_y"][1:4]), 0), pct(max(cal[anch]["bins"]["mean_y"][1:4]), 0), "%.3f" % cal["anch_generic"]["ece"][0], "%.3f" % cal["seg_flat"]["ece"][0],
      "%.3f" % m["recalibration"]["before"]["ece"][0], "%.3f" % m["recalibration"]["after"]["ece"][0], "%.3f" % m["recalibration"]["before"]["brier"][0], "%.3f" % m["recalibration"]["after"]["brier"][0]), align="justify")
H.figure(doc, os.path.join(FIG, "fig06_calibration.png"), 6.5, "**Fig. 6.** Calibration. (a) Reliability curves; (b) distribution of reported probabilities for the framework; (c) the framework before and after an isotonic recalibration fitted on separate blocks.", alt="Reliability diagrams")

HD("5.5 Stress tests", 2)
hz = S["hazard"]
sh = S["shift"]
an = S["anchor"]
fl = S["sensor_failure"]
hm = S["hazard_misspecified"]
P("**Loss hazard and class balance.** Accuracy of the framework rises from %s%% to %s%% as the loss hazard rises from 0.05 to 1.0 per 100 m (Fig. 7a, b) but this is mostly a change of class balance: the share of segments truly on the alignment falls from %s%% to %s%% and the accuracy of the trivial rule \"always absent\" rises from %s%% to %s%%. "
  "Balanced accuracy changes by only %.1f points (%s%% to %s%%). Behind it the error profile changes: with more frequent losses the filter lags more (miss rate %s%% to %s%%) and false alarms fall (%s%% to %s%%). Accuracy should not be compared across scenarios with different prevalence without the balanced measure." % (
      pc(hz["0.05"]["anch_full"]["all"]["acc"][0]), pc(hz["1.0"]["anch_full"]["all"]["acc"][0]), pc(CB["0.05"]["prev"][0]), pc(CB["1.0"]["prev"][0]), pc(CB["0.05"]["always_absent_acc"][0]), pc(CB["1.0"]["always_absent_acc"][0]),
      100 * (CB["1.0"]["bacc"][0] - CB["0.05"]["bacc"][0]), pc(CB["0.05"]["bacc"][0]), pc(CB["1.0"]["bacc"][0]), pc(CB["0.05"]["miss"][0]), pc(CB["1.0"]["miss"][0]), pc(CB["0.05"]["fa"][0]), pc(CB["1.0"]["fa"][0])), align="justify")
P("**Hazard assumed by the filter.** If the filter assumes a hazard between 0.05 and 2.0 per 100 m while the truth is 0.2, all-cell accuracy changes from %s%% to %s%% and visible-cell accuracy from %s%% to %s%% (Fig. 7f): the framework is not sensitive to this assumption in visible cells." % (
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
H.figure(doc, os.path.join(FIG, "fig07_stress_tests.png"), 6.5, "**Fig. 7.** Stress tests (accuracy in all cells unless stated). (a) Loss hazard; (b) class balance: accuracy, balanced accuracy, the trivial \"always absent\" rule and the share of segments truly present; (c) share of losses that are lateral shifts; "
         "(d) probability that the anchor is on the alignment; (e) dead sensor; (f) hazard assumed by the filter.", alt="Stress test panels")

HD("5.6 Excavation-clearance trial and trial-pit allocation", 2)
bn = POL["anchored fusion, binary map (absent = clear)"]
p10 = POL[pol_name(0.1)]
p02 = POL[pol_name(0.02)]
P("A decision-consequence trial asks what a crew would strike if it released for mechanical excavation the segments that a policy clears. Table 6 and Fig. 8a report the share of the corridor released and the strikes per kilometre (a strike is a released segment that is truly on the alignment). "
  "Digging everywhere strikes %s per km; releasing the segments the EM locator does not flag strikes %s per km while releasing %s%%; per-segment GPR and EM fusion strikes %s per km at %s%% released; and the anchored binary map strikes %s per km at %s%% released. "
  "The three-state rule, which releases only segments that lie in verified cells, are called absent and have a probability below a threshold τ, strikes %s per km at τ = 0.1 and %s per km at τ = 0.02 while releasing %s%% and %s%% of the corridor. Relative to the binary map this is a factor of %.1f (τ = 0.1) to %.1f (τ = 0.02) fewer strikes for %.1f to %.1f percentage points less corridor released. "
  "The consequence-weighted strike measure, with the assumed weights of Table 1, falls by a similar factor." % (
      "%.0f" % POL["no map: dig everywhere"]["strikes_per_km"][0], "%.0f" % POL["EM locator only"]["strikes_per_km"][0], pc(POL["EM locator only"]["cleared"][0], 0), "%.1f" % POL["fusion, per segment"]["strikes_per_km"][0], pc(POL["fusion, per segment"]["cleared"][0], 0),
      "%.1f" % bn["strikes_per_km"][0], pc(bn["cleared"][0], 0), "%.1f" % p10["strikes_per_km"][0], "%.1f" % p02["strikes_per_km"][0], pc(p10["cleared"][0], 0), pc(p02["cleared"][0], 0),
      bn["strikes_per_km"][0] / p10["strikes_per_km"][0], bn["strikes_per_km"][0] / p02["strikes_per_km"][0], 100 * (bn["cleared"][0] - p10["cleared"][0]), 100 * (bn["cleared"][0] - p02["cleared"][0])), align="justify")
rows = [["Policy: segments released for mechanical excavation", "Released (%)", "Strike rate among released (%)", "Strikes per km", "Consequence-weighted strikes per km"]]
for name, show in (("no map: dig everywhere", "No map: dig everywhere"), ("EM locator only", "EM locator: no detection"), ("GPR dual-band, per segment", "GPR dual-band, per segment"), ("fusion, per segment", "GPR + EM fusion, per segment"),
                   ("anchored fusion, binary map (absent = clear)", "Anchored fusion, binary: p ≤ 0.5"), (pol_name(0.2), "Three-state: verified, p < 0.20"), (pol_name(0.1), "Three-state: verified, p < 0.10"), (pol_name(0.05), "Three-state: verified, p < 0.05"), (pol_name(0.02), "Three-state: verified, p < 0.02")):
    p = POL[name]
    rows.append([show, pc(p["cleared"][0], 1), pc(p["strike_rate"][0], 1), "%.1f" % p["strikes_per_km"][0], "%.1f" % p["consequence_per_km"][0]])
H.caption(doc, "**Table 6.** Clearance policies (mean over %d blocks; strike = released segment truly on the alignment; 200 segments per kilometre; consequence weights from Table 1)." % META["blocks"], keep_next=True)
H.table(doc, rows, widths=[2.5, 0.8, 1.1, 0.8, 1.3], size=8)
pits = DEC["pits"]


def pit_at(name, frac, key="residual_missed"):
    for q in pits[name]:
        if abs(q["budget_fraction"] - frac) < 1e-9:
            return q[key][0]


P("For trial-pit allocation, candidates are all segments that are not called present, including unverified ones, ranked by the residual probability, by that probability times the consequence divided by pit cost, or at random. With a budget of 5%% of the cost of pitting every candidate, ranking by probability removes %s%% of the missed utilities and random placement %s%%; "
  "at 10%% the figures are %s%% and %s%%. Ranking by consequence and cost gives nearly the same residual as ranking by probability alone (consequence-weighted residual %s%% against %s%% at 5%%). Each simulated corridor holds one utility, so consequence is constant within a corridor and the weighting only reorders corridors of different utilities and depths; it is expected to matter more where consequences differ within a corridor." % (
      "%.0f" % (100 - 100 * pit_at("probability", 0.05)), "%.0f" % (100 - 100 * pit_at("random", 0.05)), "%.0f" % (100 - 100 * pit_at("probability", 0.1)), "%.0f" % (100 - 100 * pit_at("random", 0.1)),
      "%.1f" % (100 * pit_at("consequence/cost", 0.05, "residual_consequence")), "%.1f" % (100 * pit_at("probability", 0.05, "residual_consequence"))), align="justify")
H.figure(doc, os.path.join(FIG, "fig08_decision.png"), 6.5, "**Fig. 8.** (a) Strikes per kilometre against the share of the corridor released for mechanical excavation for each clearance policy (logarithmic axis; error bars are 95% intervals). (b) Consequence-weighted missed utility remaining as trial pits are added in different orders.", alt="Clearance policies and pit allocation")

HD("5.7 Location and depth accuracy", 2)
P("Location and depth errors are treated separately from detection, by a closed-form error model rather than by simulation of radargrams. The horizontal error combines positioning error with a picking error that grows with depth (0.10 + 0.05 m per metre of depth), and the depth error combines a 10%% velocity uncertainty with 0.05 m of picking. "
  "With RTK-class positioning (0.05 m) the probability that the horizontal error is within 1 m is %s at 1 m depth, %s at 5 m and %s at 7 m; depth within 0.5 m is %s at 1 m, %s at 2 m, %s at 3.5 m, %s at 5 m and %s at 7 m. With stand-alone GNSS (3 m) the probability of meeting a 1 m horizontal requirement is about %s whatever the depth. "
  "Survey-grade positioning or local control is therefore a precondition of metre-level horizontal accuracy in this model, and depth accuracy degrades with depth because velocity uncertainty is proportional to it. These numbers follow from the assumed error model; they are not measurements. Fig. 9 shows the curves." % (
      "%.3f" % POS["rtk"]["horizontal_within_1m"][0], "%.2f" % POS["rtk"]["horizontal_within_1m"][3], "%.2f" % POS["rtk"]["horizontal_within_1m"][4], "%.2f" % POS["rtk"]["depth_within_0p5m"][0], "%.2f" % POS["rtk"]["depth_within_0p5m"][1],
      "%.2f" % POS["rtk"]["depth_within_0p5m"][2], "%.2f" % POS["rtk"]["depth_within_0p5m"][3], "%.2f" % POS["rtk"]["depth_within_0p5m"][4], "%.2f" % POS["standalone"]["horizontal_within_1m"][2]), align="justify")
H.figure(doc, os.path.join(FIG, "fig09_position_depth.png"), 5.8, "**Fig. 9.** Closed-form location and depth error model. (a) Probability that the horizontal error is within 1 m. (b) Probability that the depth error is within 0.5 m (RTK-class positioning).", alt="Position and depth error curves")

HD("5.8 Official cross-sections and shadowing by overlying lines", 2)
T = SEC["table"]
P("Three representative arrangements of utilities in a road section are often of interest: parallel utilities at different depths (A), a water line stacked directly above a sewer in a shared trench (B) and a sewer and fibre beneath a transverse water line (C). Using depths of 3.5 m for sewers, 1.8 m for water and fibre and 0.8 m for ducts, "
  "an overlying line shadows the lower utility by 3 dB (PE/PVC) or 10 dB (cast iron) in the model. Fig. 10 shows the resulting fused detection probability. A concrete sewer at 3.5 m is detected in dry sand (%s) but in dry loam falls from %s without shadowing to %s beneath PE/PVC and %s beneath cast iron; "
  "in moist loam it is %s, %s and %s, and in clay at most %s. Fibre in clay falls from %s to %s beneath an overlying PE/PVC line, while shallow ducts stay at 1.00 in every soil. Closed-form values agree with direct simulation within 0.003 for three checked cells." % (
      "%.2f" % T["dry_sand"]["Concrete sewer, A"], "%.2f" % T["dry_loam"]["Concrete sewer, A"], "%.2f" % T["dry_loam"]["Sewer, B (PE/PVC above)"], "%.2f" % T["dry_loam"]["Sewer, B (cast iron above)"],
      "%.2f" % T["moist_loam"]["Concrete sewer, A"], "%.2f" % T["moist_loam"]["Sewer, B (PE/PVC above)"], "%.2f" % T["moist_loam"]["Sewer, B (cast iron above)"], "%.2f" % max(T["clay"]["Concrete sewer, A"], T["clay"]["Sewer, B (PE/PVC above)"]), "%.2f" % T["clay"]["Fibre, A"], "%.2f" % T["clay"]["Fibre, C (PE/PVC above)"]), align="justify")
H.figure(doc, os.path.join(FIG, "fig10_cross_sections.png"), 5.6, "**Fig. 10.** Fused detection probability for utilities in the three cross-section arrangements, with shadowing by an overlying water line (closed form).", alt="Cross-section detection probabilities")

HD("5.9 Sensitivity, re-scanning and correlated evidence", 2)
items = SENS["items"]
base = SENS["base"]
rng_acc = sorted(items, key=lambda it: -abs(it["high"]["acc"] - it["low"]["acc"]))
P("**Parameter sensitivity.** Fig. 11 shows the change in all-cell accuracy and visible-cell miss rate when one parameter is changed at a time, with common random numbers. The results are most sensitive to the soil attenuation, the spreading loss, the system budget and the detection threshold, which move the detectability envelope: "
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
  "The ECE of the framework is %s at zero correlation and %s at 0.9; tempering the evidence by a factor of 0.5 gives %s and %s, and an exact joint likelihood for the two bands %s and %s (Fig. 12b). Miscalibration from the independence assumption is therefore present but small compared with the miscalibration that comes from the depth and the continuity prior." % (
      "%.3f" % cr["0.0"]["independent"]["calibration"]["ece"][0], "%.3f" % cr["0.9"]["independent"]["calibration"]["ece"][0], "%.3f" % cr["0.0"]["tempered"]["calibration"]["ece"][0], "%.3f" % cr["0.9"]["tempered"]["calibration"]["ece"][0], "%.3f" % cr["0.0"]["joint_gpr"]["calibration"]["ece"][0], "%.3f" % cr["0.9"]["joint_gpr"]["calibration"]["ece"][0]), align="justify")
H.figure(doc, os.path.join(FIG, "fig11_sensitivity.png"), 6.5, "**Fig. 11.** One-at-a-time sensitivity of (a) all-cell accuracy and (b) visible-cell miss rate of the framework. Circles and squares are the first and second value named on the axis; the dotted line is the base case.", alt="Sensitivity")
H.figure(doc, os.path.join(FIG, "fig12_rescan_correlation.png"), 6.5, "**Fig. 12.** (a) Effect of a repeat pass on uncertain segments (visible cells in the four harder soils); ρ is the correlation of the run-level noise of the repeat pass with the first. (b) Calibration error under correlated GPR and EM noise for three evidence rules.", alt="Re-scan and correlated evidence")

# =============================================================================================== 6 Discussion
HD("6. Discussion")
HD("6.1 What the simulation demonstrates, suggests and does not establish", 2)
P("**Demonstrated within the model.** Given the assumed sensor behaviour, (i) a large share of a plausible utility network is invisible to GPR and EM at the depths where it lies, and a map that marks only detections cannot say so; (ii) a rule that withholds a present or absent call in those cells costs coverage but "
  "removes most of the strikes that a binary map would produce in the clearance trial; (iii) soil-specific likelihoods matter, whereas the anchor matters mainly where the sensors are blind; (iv) the filter's probabilities are well ordered but not calibrated in the mid-range; and (v) the framework degrades markedly with lateral shifts, a certain-but-wrong anchor and GPR failure, and loses accuracy when depth is uncertain.", align="justify")
P("**Suggested, conditionally on the model resembling reality.** Depth knowledge, for example from velocity calibration at each site, is the cheapest improvement in the model, since averaging over the depth range or knowing the true depth lowers the visible-cell miss rate substantially. Recording the reliability of each anchor, and not only its network identity, "
  "is cheap and, if the model is right, matters. A dual-band GPR adds little over a single band in the assumed soils, and the case for the second band rests on resolution, which the model does not represent. Re-scanning, and the connectivity that would allow remote re-scanning decisions, adds nothing to detection in the model. "
  "A published unverified fraction, by soil and depth band, would give a client a number with which to compare surveys.", align="justify")
P("**Not established.** Whether the sensor model reproduces real GPR and EM behaviour in any soil; the actual detection probabilities and their dependence on antenna, survey geometry and operator; the frequency and form of utility displacement; the real reliability of anchors and records; the real cost and consequences of strikes; "
  "whether crews would use a three-state map as intended; and any result in a specific country, soil or network. The EM-only proxy is a model of an instrument that couples only to some utilities, not a measurement of any product, and the gain over it should not be quoted as a field improvement.", align="justify")
HD("6.2 Relation to practice", 2)
P("The framework is designed to complement, not replace, established practice. Quality levels of subsurface utility data " + C("asce02") + " already distinguish records, geophysical detection and exposure; the unverified state is a way of stating, per segment, that geophysical detection could not have established presence or absence, "
  "and so that the segment sits at the quality of the records until a pit is dug. The clearance trial suggests that the cost of such honesty is a smaller released share of the corridor and that it can be repaid in fewer strikes, but it also shows the converse: a binary map with high accuracy still releases segments at a strike rate of %s%% that the three-state rule lowers to %s%%." % (pc(bn["strike_rate"][0], 0), pc(p10["strike_rate"][0], 0)) + " "
  " Consequences differ between utilities, and the consequence-weighted ranking is the part of the framework most dependent on local judgement.", align="justify")
HD("6.3 Limitations", 2)
for t in (
    "The corridor is one-dimensional. A real survey covers a swath and must decide which hyperbolic response belongs to which utility; the framework starts after that decision.",
    "The sensor model is a thresholded signal-to-noise model with Gaussian noise and an assumed spreading loss; it has no radargram, no clutter structure, no antenna pattern and no operator. The attenuation values and the 8 dB threshold determine the detectability envelope, and Section 5.9 shows that results are most sensitive to them.",
    "The truth process is a first-order Markov chain with a single utility per corridor and no crossings; real corridors have crossing and parallel utilities, branches and unrecorded lines.",
    "The unverified rule is evaluated at the class mid-depth and is therefore coarse: a sewer at the deep end of its range can be poorly detectable in a cell labelled visible (Section 5.3).",
    "Depth is fixed within a corridor, and the filter uses a class mid-depth. In practice depth varies and can be estimated from the data; the diagnostics show this is the largest single source of avoidable error in the model.",
    "The filter assumes conditional independence, which the simulation violates; Section 5.9 shows the effect is small here but the sign and size of the effect in the field are unknown.",
    "Consequence weights and pit costs are assumed relative values and affect only Section 5.6.",
    "All uncertainty intervals are simulation noise; no interval expresses uncertainty about the assumptions, which is the dominant uncertainty.",
):
    H.bullet(doc, t)
HD("6.4 What a field test would need", 2)
P("The minimum test consists of a controlled corridor with known pipe positions, depths and materials in at least two soils; GPR and EM data recorded with surveyed positions; the software run offline; and detection, location and depth errors, calibration and unverified coverage reported with the definitions of Section 4.5. "
  "The attenuation, threshold, coupling and persistence parameters would be fitted per soil, and the three-state rule validated by trial pits placed by verification priority. Until then the numbers in this paper are properties of the simulator.", align="justify")

# =============================================================================================== 7 Conclusions
HD("7. Conclusions")
P("A decision layer that turns GPR and EM detections into present, absent and unverified states, with probabilities and a verification ranking, was specified and evaluated in simulation. The following conclusions apply to the model and not to the field.", align="justify")
for t in (
    "%s%% of the assumed network (plastic and concrete sewers at the depths where they lie, in loam, clay and fill) is sensor-blind, and a map that does not say so would convert silence into clearance." % pct(unv, 0),
    "In sensor-visible cells the framework reaches %s%% accuracy (miss %s%%, false alarm %s%%), a modest improvement over calibrated per-segment fusion (%s%%, %s%%, %s%%), and far above the EM-only proxy (%s%% accuracy, miss %s%%)." % (
        mm(anch, "visible", "acc"), mm(anch, "visible", "miss"), mm(anch, "visible", "fa"), mm("seg_flat", "visible", "acc"), mm("seg_flat", "visible", "miss"), mm("seg_flat", "visible", "fa"), mm("em_only", "visible", "acc"), mm("em_only", "visible", "miss")),
    "Its probabilities are well ordered, with an ECE of %s, but are under-confident in the mid-range; an isotonic map fitted on separate runs corrects this in simulation." % ("%.3f" % cal[anch]["ece"][0]),
    "In the clearance trial the three-state rule gives about %.1f times fewer strikes per kilometre than the binary map for %.0f percentage points less corridor released." % (bn["strikes_per_km"][0] / p10["strikes_per_km"][0], 100 * (bn["cleared"][0] - p10["cleared"][0])),
    "Lateral shifts of utilities, an anchor that is certain but wrong, GPR failure and uncertain depth are the main failure modes; depth knowledge is the cheapest improvement; re-scanning and EM add little to detection in this model.",
):
    H.bullet(doc, t)
P("The study fixes definitions and a protocol, and shows which assumptions the conclusions rest on. It cannot show field performance, which requires data with known ground truth.", align="justify")

# =============================================================================================== declarations
HD("Declarations", 1)
P("**CRediT authorship contribution statement.** Leon Sandler: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Visualization, Writing – original draft, Writing – review and editing.", align="justify")
P("**Funding.** This research received no specific grant from any funding agency in the public, commercial or not-for-profit sectors.", align="justify")
P("**Declaration of competing interests.** The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.", align="justify")
P("**Prior dissemination.** An earlier, non-peer-reviewed white paper describing the concept was prepared in response to an open innovation challenge on detecting underground utilities issued through the Wazoku (InnoCentive) platform. "
  "Its numerical results came from an earlier version of the simulation whose code was not available when this manuscript was prepared; the simulation was reimplemented from the method description and all numbers in this paper come from the released code. The challenge submission is not a publication and the present manuscript is not under consideration elsewhere.", align="justify")
P("**Data and code availability.** All code, the configuration, results.json, the figure script, tests and the manuscript builders are available at %s (release %s) and are archived on Zenodo (software: https://doi.org/%s; manuscript preprint: https://doi.org/%s). "
  "Every table and figure is regenerated by the commands in Appendix B. No field data were used." % (REPO, RELEASE, SW, PP), align="justify")
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
             "python SubSurface_MC.py --reproduce --out results --n 500 --blocks 10 --seed 42", "python figure_generation.py --results results/results.json --out results/figures", "python tests/test_subsurface.py"):
    p = doc.add_paragraph()
    r = p.add_run(line)
    r.font.name = "Courier New"
    r.font.size = Pt(9.5)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
P("")
P("The reproduce command takes about %d s on a consumer laptop. results.json records the command, the seed, the library versions (Python %s, NumPy %s, SciPy %s), the configuration and every table quoted in this paper." % (round(META["runtime_s"]), META["python"], META["numpy"], META["scipy"]), align="justify")

# =============================================================================================== references
HD("References", 1)
for key in ("numpy20", "scipy20", "mpl07"):
    K._note(key)
P("The simulation uses NumPy " + C("numpy20") + ", SciPy " + C("scipy20") + " and Matplotlib " + C("mpl07") + ".", align="justify")
BODY[0] = False
for line in K.reference_list():
    p = H.para(doc, line, size=9.5, space_after=3)
    p.paragraph_format.left_indent = Pt(18)
    p.paragraph_format.first_line_indent = Pt(-18)
    p.paragraph_format.line_spacing = 1.1

os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
out = os.path.join(HERE, "out", "Manuscript_TUST.docx")
doc.save(out)
print("saved", out)
print("abstract words:", AB_WORDS, "body words (approx, excl. refs/tables):", WORDS["body"], "references:", len(K.USED))
