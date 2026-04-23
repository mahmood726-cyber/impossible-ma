import numpy as np
import pytest

from impossible_ma._pool import dl_tau2, fe_pool, reml_pool


def test_fe_pool_identical_studies_equals_mean():
    effects = np.array([0.2, 0.2, 0.2])
    variances = np.array([0.04, 0.04, 0.04])
    mu, se = fe_pool(effects, variances)
    assert mu == pytest.approx(0.2, abs=1e-10)
    assert se == pytest.approx(np.sqrt(0.04 / 3), rel=1e-10)


def test_reml_tau2_zero_when_no_heterogeneity():
    effects = np.array([0.3, 0.3, 0.3, 0.3, 0.3])
    variances = np.array([0.01, 0.01, 0.01, 0.01, 0.01])
    mu, se, tau2 = reml_pool(effects, variances)
    assert tau2 == pytest.approx(0.0, abs=1e-4)
    assert mu == pytest.approx(0.3, abs=1e-6)


def test_dl_tau2_positive_under_heterogeneity():
    effects = np.array([0.1, 0.5, -0.2, 0.8, -0.4])
    variances = np.array([0.01, 0.01, 0.01, 0.01, 0.01])
    tau2 = dl_tau2(effects, variances)
    assert tau2 > 0.0
