# -*- coding: utf-8 -*-
"""American spelling for the body text of a python-docx document (the reference list is left exactly as cited)."""
import re

PAIRS = {
    "unmodelled": "unmodeled", "modelled": "modeled", "modelling": "modeling", "behaviour": "behavior", "behaviours": "behaviors", "centre": "center", "centres": "centers",
    "fibre": "fiber", "fibres": "fibers", "metre": "meter", "metres": "meters", "prioritisation": "prioritization", "prioritising": "prioritizing", "prioritised": "prioritized",
    "minimises": "minimizes", "minimise": "minimize", "maximise": "maximize", "maximises": "maximizes", "optimised": "optimized", "characterised": "characterized", "analysed": "analyzed",
    "towards": "toward", "acknowledgements": "acknowledgments", "relabelled": "relabeled", "labelled": "labeled", "favourable": "favorable", "colour": "color", "normalised": "normalized",
    "recognised": "recognized", "summarised": "summarized", "generalisation": "generalization", "licence": "license", "judgement": "judgment", "grey": "gray",
    "unfavourable": "unfavorable", "catalogue": "catalog", "programme": "program", "utilisation": "utilization", "parameterised": "parameterized", "randomised": "randomized",
}
_RX = re.compile(r"\b(" + "|".join(sorted(PAIRS, key=len, reverse=True)) + r")\b", re.I)


def _sub(m):
    w = m.group(0)
    new = PAIRS[w.lower()]
    if w.isupper():
        return new.upper()
    if w[0].isupper():
        return new[0].upper() + new[1:]
    return new


def fix_text(t):
    return _RX.sub(_sub, t)


def _paras(doc):
    for p in doc.paragraphs:
        yield p
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    yield p


def apply(doc, stop_at="References"):
    """replace British spellings in runs; stop at a paragraph whose text equals stop_at (body paragraphs before the reference list)"""
    seen_stop = False
    n = 0
    for p in doc.paragraphs:
        if stop_at and p.text.strip() == stop_at:
            seen_stop = True
        if seen_stop:
            continue
        for r in p.runs:
            t = fix_text(r.text)
            if t != r.text:
                r.text = t; n += 1
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    for r in p.runs:
                        x = fix_text(r.text)
                        if x != r.text:
                            r.text = x; n += 1
    return n
