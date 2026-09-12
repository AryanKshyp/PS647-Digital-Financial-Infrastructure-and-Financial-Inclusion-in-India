#!/usr/bin/env python3
"""
Shared estimation helpers for the H5 track.

Everything here is a thin wrapper over the SAME estimator the H1 track used
(linearmodels.PanelOLS, two-way fixed effects, SEs clustered by state), plus the
wild cluster bootstrap that H5 needs and H1 did not: H1's regressors varied within state,
so 33 clusters were adequate; H5's key coefficients are identified off ONE time-invariant
number per state, which is exactly the case where the cluster-robust t-distribution
approximation is worst.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

CONTROLS = ["branches_per_lakh_adults", "atms_per_lakh_adults", "ln_nsdp_pc"]
ENTITY, TIME = "state_key", "fy_end"


def fit(d: pd.DataFrame, y: str, X: list[str]):
    """Two-way FE, SEs clustered by entity. Identical call to scripts/estimate_digital.py."""
    dd = d.set_index([ENTITY, TIME])
    m = PanelOLS(dd[y], dd[X], entity_effects=True, time_effects=True, drop_absorbed=True)
    return m.fit(cov_type="clustered", cluster_entity=True)


def stars(p: float) -> str:
    return "***" if p < .01 else "**" if p < .05 else "*" if p < .10 else ""


# --------------------------------------------------------------------------- LSDV machinery
def _design(d: pd.DataFrame, y: str, X: list[str]):
    """Least-squares-dummy-variable form of the same two-way FE model.

    Algebraically identical to PanelOLS with entity_effects + time_effects (verified in
    estimate_h5.py against the PanelOLS fit). Used for the bootstrap because it gives direct
    access to residuals and a refit that costs one lstsq call.
    """
    sub = d[[y, ENTITY, TIME] + X].dropna()
    D = pd.get_dummies(sub[ENTITY], prefix="s", drop_first=True, dtype=float)
    T = pd.get_dummies(sub[TIME], prefix="t", drop_first=True, dtype=float)
    Z = np.column_stack([np.ones(len(sub)), sub[X].to_numpy(float), D.to_numpy(), T.to_numpy()])
    return sub[y].to_numpy(float), Z, sub[ENTITY].to_numpy(), len(X)


def _ols(yv, Z):
    beta, *_ = np.linalg.lstsq(Z, yv, rcond=None)
    return beta, yv - Z @ beta


def _cluster_se(Z, resid, clusters):
    """CR1 cluster-robust covariance.

    k is the full column count of the LSDV design (regressors + intercept + both sets of fixed
    effect dummies). linearmodels counts the absorbed effects differently, so its SEs are a
    constant factor smaller; estimate_h5.py verifies that factor is the same for every regressor,
    and it cancels in the bootstrap t-ratio.
    """
    n, k = Z.shape
    XtX_inv = np.linalg.pinv(Z.T @ Z)
    meat = np.zeros((k, k))
    uniq = np.unique(clusters)
    for g in uniq:
        m = clusters == g
        Zg, ug = Z[m], resid[m]
        s = Zg.T @ ug
        meat += np.outer(s, s)
    G = len(uniq)
    scale = (G / (G - 1)) * ((n - 1) / (n - k))
    V = XtX_inv @ meat @ XtX_inv * scale
    return np.sqrt(np.diag(V))


def wild_cluster_bootstrap(d: pd.DataFrame, y: str, X: list[str], target: str,
                           B: int = 9999, seed: int = 647) -> dict:
    """Wild cluster bootstrap-t, Rademacher weights, null imposed (WCR).

    Cameron, Gelbach & Miller (2008). The null-imposed variant is the one that performs well
    with few clusters. Procedure:
      1. fit the RESTRICTED model with the target regressor excluded -> fitted values, residuals
      2. for each replication, flip the sign of every residual in a cluster with prob 1/2,
         rebuild y* = y_restricted_fit + w_g * u_g, refit the UNRESTRICTED model, record t*
      3. p = share of |t*| >= |t_observed|
    The bootstrap distribution is generated under the null, so it is a valid test even when the
    cluster-robust t-statistic is badly sized.

    Vectorised. The design matrix Z is identical in every replication, so the OLS projector and
    residual-maker are formed once and all B replications run as a handful of matrix products
    rather than B separate refits. Two identities make the cluster SE cheap:

        beta* = P y*          with P = pinv(Z)          (k x n, fixed)
        u*    = M y*          with M = I - Z P          (n x n, fixed)

    and, for the single coefficient j being tested, writing a_j for column j of (Z'Z)^-1 and
    h = Z a_j, the CR1 variance of beta_j reduces to a grouped sum:

        V_jj = scale * sum_g ( sum_{i in g} h_i u_i )^2

    so only a group-sum of h*u is needed, never the full k x k meat matrix.
    """
    yv, Z, cl, _ = _design(d, y, X)
    j = X.index(target) + 1  # +1 for the intercept column

    beta, resid = _ols(yv, Z)
    se_full = _cluster_se(Z, resid, cl)
    t_obs = beta[j] / se_full[j]

    n, kz = Z.shape
    uniq, cl_idx = np.unique(cl, return_inverse=True)
    G = len(uniq)
    # kz, not len(X): _cluster_se scales on the FULL LSDV column count. Must match exactly.
    scale = (G / (G - 1)) * ((n - 1) / (n - kz))

    P = np.linalg.pinv(Z)                 # k x n
    M = np.eye(n) - Z @ P                 # n x n, residual maker
    A = np.linalg.pinv(Z.T @ Z)
    h = Z @ A[:, j]                       # n, turns V_jj into a grouped sum

    def t_from(Y):
        """Y: n x B matrix of outcome draws -> length-B vector of t statistics for coefficient j."""
        Bt = P @ Y                        # k x B
        U = M @ Y                         # n x B
        S = np.zeros((G, Y.shape[1]))
        np.add.at(S, cl_idx, h[:, None] * U)
        Vjj = scale * (S ** 2).sum(axis=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(Vjj > 0, Bt[j] / np.sqrt(Vjj), np.nan)

    # restricted fit: impose beta_target = 0 by dropping the target column
    Zr = np.delete(Z, j, axis=1)
    beta_r, resid_r = _ols(yv, Zr)
    fit_r = Zr @ beta_r

    rng = np.random.default_rng(seed)
    W = rng.choice([-1.0, 1.0], size=(G, B))          # one Rademacher draw per cluster per rep
    Y = fit_r[:, None] + resid_r[:, None] * W[cl_idx, :]
    t_star = t_from(Y)

    ok = np.isfinite(t_star)
    p = float((np.abs(t_star[ok]) >= abs(t_obs)).sum() + 1) / (ok.sum() + 1)
    lo, hi = np.percentile(t_star[ok], [2.5, 97.5])
    return {"coef": beta[j], "se_cluster": se_full[j], "t": t_obs, "p_wcb": p,
            "B": int(ok.sum()), "crit_lo": lo, "crit_hi": hi,
            "ci_lo": beta[j] - hi * se_full[j], "ci_hi": beta[j] - lo * se_full[j]}
