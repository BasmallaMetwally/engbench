# Task: PID tuning for a delayed second-order plant

Implement `design_pid(plant)` in `/workspace/solution.py`.

Plant:  `G(s) = K e^{-theta s} / ((tau1 s + 1)(tau2 s + 1))`, unit step reference, input saturation `|u| <= umax`.
`sim.py` is the exact simulator (controller structure, anti-windup, derivative filter) used for grading.
`plant` contains `K, tau1, tau2, theta, umax, os_max, ts_max`. See `example_plant.json`.

## Requirements (checked on hidden plants)
1. Closed loop is stable.
2. Overshoot <= `os_max` (%).
3. 2% settling time <= `ts_max` (s).
4. Steady-state error <= 1%.
5. Robust: with gain x1.2 and delay x1.2, and with gain x0.8, the loop stays stable
   with overshoot <= 20% and steady-state error <= 1%.
6. A 0.2 input step disturbance at mid-simulation is rejected (error <= 1% at the end).

You may tune analytically or by optimising against `sim.py`. `design_pid` should not take more than a few minutes.
Don't modify `sim.py` (grading uses its own copy). Return non-negative finite gains.
