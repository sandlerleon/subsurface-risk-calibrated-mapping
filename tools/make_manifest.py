# -*- coding: utf-8 -*-
"""Write results/manifest.json: SHA-256 and size of every file that the paper's numbers and figures depend on.   python tools/make_manifest.py"""
import hashlib
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FILES = ["SubSurface_MC.py", "figure_generation.py", "requirements.txt", "tests/test_subsurface.py", "results/config.json", "results/results.json"]
FILES += sorted("results/figures/" + f for f in os.listdir(os.path.join(ROOT, "results", "figures")) if f.endswith(".png"))
out = {}
for f in FILES:
    p = os.path.join(ROOT, f)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    out[f] = {"sha256": h, "bytes": os.path.getsize(p)}
json.dump(out, open(os.path.join(ROOT, "results", "manifest.json"), "w"), indent=1)
print("manifest for %d files" % len(out))
