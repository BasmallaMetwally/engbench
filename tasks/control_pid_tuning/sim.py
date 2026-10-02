"""Closed-loop simulator + metrics + instance generator. Visible to the agent (and used by the grader).

Plant:   G(s) = K * exp(-theta*s) / ((tau1*s + 1)(tau2*s + 1)),  input disturbance d added to u.
Control: u = clip(Kp*e + I + D, -umax, umax),  e = 1 - y
         I += Ki*e*dt   (conditional integration anti-windup)
         D = -Kd * d/dt( lowpass(y, TF) )        (derivative on measurement, TF = 0.05 s)
"""
from collections import deque
import numpy as np

DT = 1e-3
TF = 0.05


def make_plant(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    tau1 = float(rng.uniform(0.8, 2.0))
    p = dict(K=float(rng.uniform(0.8, 3.0)), tau1=tau1,
             tau2=float(tau1 * rng.uniform(0.2, 0.5)),
             theta=float(rng.uniform(0.1, 0.3)), umax=10.0)
    p.update(os_max=10.0, ts_max=float(7.0 * (p["tau1"] + p["theta"])))   # % and seconds
    return p


def simulate(plant: dict, gains: dict, T: float, dist: float = 0.0, t_dist: float = None,
             gain_scale: float = 1.0, delay_scale: float = 1.0):
    K = plant["K"] * gain_scale
    t1, t2 = plant["tau1"], plant["tau2"]
    nd = int(round(plant["theta"] * delay_scale / DT))
    buf = deque([0.0] * nd, maxlen=nd) if nd > 0 else None
    a1, a2 = np.exp(-DT / t1), np.exp(-DT / t2)
    af = np.exp(-DT / TF)
    Kp, Ki, Kd = gains["Kp"], gains["Ki"], gains["Kd"]
    umax = plant["umax"]
    n = int(T / DT)
    t = np.arange(n) * DT
    y_log, u_log = np.zeros(n), np.zeros(n)
    x1 = x2 = yf = yf_prev = I = 0.0
    for k in range(n):
        y = x2
        yf = af * yf + (1 - af) * y
        e = 1.0 - y
        D = -Kd * (yf - yf_prev) / DT
        yf_prev = yf
        u_raw = Kp * e + I + D
        u = min(max(u_raw, -umax), umax)
        if u == u_raw or (u_raw > umax and e < 0) or (u_raw < -umax and e > 0):
            I += Ki * e * DT
        ud = u + (dist if (t_dist is not None and t[k] >= t_dist) else 0.0)
        if buf is not None:
            buf.append(ud); ud_del = buf[0]
        else:
            ud_del = ud
        x1 = a1 * x1 + (1 - a1) * K * ud_del
        x2 = a2 * x2 + (1 - a2) * x1
        y_log[k], u_log[k] = y, u
        if not np.isfinite(x2) or abs(x2) > 1e3:
            y_log[k:], u_log[k:] = np.nan, np.nan
            break
    return t, y_log, u_log


def metrics(t, y, band=0.02):
    if not np.all(np.isfinite(y)) or np.max(np.abs(y)) > 5:
        return dict(stable=False, overshoot=np.inf, settling=np.inf, sse=np.inf)
    out = np.where(np.abs(y - 1.0) > band)[0]
    ts = 0.0 if len(out) == 0 else float(t[min(out[-1] + 1, len(t) - 1)])
    tail = y[-max(1, len(y) // 20):]
    if np.ptp(tail) > 0.02:      # sustained oscillation / limit cycle (e.g. saturated) is not stable
        return dict(stable=False, overshoot=np.inf, settling=np.inf, sse=np.inf)
    return dict(stable=True, overshoot=float(max(0.0, (y.max() - 1.0) * 100)),
                settling=ts, sse=float(abs(1.0 - tail.mean())))
