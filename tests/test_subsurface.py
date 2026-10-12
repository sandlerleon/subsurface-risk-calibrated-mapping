# -*- coding: utf-8 -*-
"""pytest-free test runner: python tests/test_subsurface.py  (exit code 0 when all checks pass)"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
import SubSurface_MC as S


def test_selftests():
    res = S.selftests(S.CFG, 42, verbose=False)
    bad = [r for r in res if not r["passed"]]
    assert not bad, bad


def test_reproducible_quick_experiment():
    import copy
    cfg = copy.deepcopy(S.CFG)
    a = S.main_metrics_only(cfg, 7, 2, 30, "t", ("anch_full",))["anch_full"]["all"]["acc"][0]
    b = S.main_metrics_only(cfg, 7, 2, 30, "t", ("anch_full",))["anch_full"]["all"]["acc"][0]
    assert a == b


def test_unverified_is_never_clear():
    """sensor-blind cells are exactly those whose fused Pd at class mid-depth is below the threshold"""
    blind, pd = S.blind_table(S.CFG)
    assert (blind == (pd < S.CFG["filter"]["unverified_pd_threshold"])).all()
    assert blind[S.SOILS.index("clay"), S.UTILS.index("concrete_sewer")]
    assert not blind[S.SOILS.index("dry_sand"), S.UTILS.index("power")]


def test_metric_denominators():
    F = np.array([[0.5, 0.1, 0.05, 0.35]])
    m = S.mix(F, [1.0])
    assert abs(m["miss"] - 0.1 / 0.6) < 1e-12 and abs(m["fa"] - 0.05 / 0.40) < 1e-12 and abs(m["acc"] - 0.85) < 1e-12


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print("PASS", name)
            except Exception as e:  # noqa
                fails += 1; print("FAIL", name, repr(e))
    sys.exit(1 if fails else 0)
