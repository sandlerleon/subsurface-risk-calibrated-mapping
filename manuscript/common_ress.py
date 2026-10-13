# -*- coding: utf-8 -*-
"""Shared pieces for the RESS manuscript, supplement, highlights and cover letter (version 1.3): results of SubSurface_v5.py, DOIs, citation helpers."""
import json
import os

from common import *  # noqa: F401,F403
import common as K

R5_PATH = os.path.join(K.ROOT, "results_v5", "results_v5.json")
R5 = json.load(open(R5_PATH, encoding="utf-8")) if os.path.exists(R5_PATH) else None
SW = (K.ZEN.get("software_1.3.1") or K.ZEN.get("software_1.3.0") or K.ZEN["software_1.2.0"])["doi"]
PP = (K.ZEN.get("publication_v5") or K.ZEN.get("publication_v4") or K.ZEN["publication_v3"])["doi"]
SW_V12, PP_V3 = K.ZEN["software_1.2.0"]["doi"], K.ZEN["publication_v3"]["doi"]
SW_V13, PP_V4 = K.ZEN["software_1.3.0"]["doi"], K.ZEN["publication_v4"]["doi"]
RELEASE = "v1.3.1"
TITLE = "Risk-Calibrated Sensor Fusion Under Model Uncertainty: A Simulation-Based Reliability Framework for Underground Utility Mapping"
FIG5 = os.path.join(K.ROOT, "results_v5", "figures")
JOURNAL = "Reliability Engineering & System Safety"
from common import _note, _short  # noqa: E402,F401
