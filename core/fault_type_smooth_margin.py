"""Train-only diagonal margin solver diagnostics, never production selection.

LMNN-inspired objective: Weinberger & Saul (JMLR,2009), locally mean-scaled
diagonal metric/ridge. Scalar SGL adaptation: Rennie & Srebro (ICML,2005),
section3.3 equation9, not their matrix factorization or smooth-hinge model.
"""
import time
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from core.fault_type_continuous import margin_problem, margin_loss_grad
from core.fault_type_literature import finite
from core.fault_type_final_guard import digest


def smooth_loss_grad(w, problem, tau=.1, ridge=.01):
    if not np.isfinite(tau) or tau <= 0:
        raise ValueError("positive finite tau required")
    delta, pull, negative = problem
    pd, nd = pull @ w, delta @ w
    u = 1 + pd[:, :, None] - nd[:, None, :]
    mask = np.broadcast_to(negative[:, None, :], u.shape)
    denom = int(negative.sum()) * pull.shape[1]
    if denom == 0:
        raise ValueError("negative class pairs required")
    value = (.5 * pd.mean() + .5 * (tau * np.logaddexp(0, u / tau))[mask].sum() / denom
             + ridge * np.mean((w - 1) ** 2))
    active = expit(u / tau) * mask
    grad = (.5 * pull.mean((0, 1))
            + .5 * (np.einsum("ik,ikd->d", active.sum(2), pull)
                     - np.einsum("il,ild->d", active.sum(1), delta)) / denom
            + 2 * ridge * (w - 1) / len(w))
    return float(value), grad


def projected_gradient(w, g):
    return np.where((w <= 0) & (g > 0), 0., g)


def solve(X, y, *, smooth=False, maxiter=150, maxfun=500, seconds=120):
    X = finite(X)
    if len(X) > 360 or maxiter < 1 or maxfun < 1 or seconds <= 0:
        raise ValueError("invalid bounded solver budget")
    problem = margin_problem(X, y, k=3)
    objective = smooth_loss_grad if smooth else margin_loss_grad
    start = time.perf_counter()
    initial = np.ones(X.shape[1])
    last = {"x": initial.copy(), "value": objective(initial, problem)[0], "calls": 0}

    def fun(w):
        if time.perf_counter() - start > seconds:
            raise TimeoutError("train solver wall budget exhausted")
        value, grad = objective(w, problem)
        if not np.isfinite(value) or not np.isfinite(grad).all():
            raise ValueError("nonfinite loss/gradient")
        last.update(x=w.copy(), value=value, calls=last["calls"] + 1)
        return value, grad

    initial_loss = last["value"]
    try:
        result = minimize(fun, initial, jac=True, method="L-BFGS-B",
                          bounds=[(0, None)] * X.shape[1],
                          options={"maxiter":maxiter, "maxfun":maxfun, "maxls":50,
                                   "ftol":1e-9, "gtol":1e-6})
        w = np.asarray(result.x)
        status = {"success":bool(result.success), "status":int(result.status),
                  "message":str(result.message), "iterations":int(result.nit),
                  "evaluations":int(result.nfev)}
    except TimeoutError as error:
        w = last["x"]
        status = {"success":False, "status":"WALL_BUDGET", "message":str(error),
                  "iterations":None, "evaluations":last["calls"]}
    value, grad = objective(w, problem)
    hard = margin_loss_grad(w, problem)[0]
    if not np.isfinite(w).all() or (w < 0).any():
        raise ValueError("invalid diagnostic weights")
    return dict(status, weights=w.tolist(), weights_checksum=digest(w.tolist()),
                initial_loss=initial_loss, final_loss=value, same_hard_loss=hard,
                initial_hard_loss=margin_loss_grad(initial, problem)[0],
                projected_gradient_inf=float(np.abs(projected_gradient(w, grad)).max()),
                maxiter=maxiter, maxfun=maxfun, maxls=50, ftol=1e-9, gtol=1e-6,
                tau=.1 if smooth else None, ridge=.01,
                seconds=time.perf_counter()-start, budget_seconds=seconds,
                state_is_last_evaluation_not_converged_iterate=status["status"]=="WALL_BUDGET")
