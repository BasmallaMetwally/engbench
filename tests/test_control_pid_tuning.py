from helpers import task_grade, ref, starter
T = "control_pid_tuning"


def _write(tmp_path, body):
    f = tmp_path / "s.py"; f.write_text(body); return str(f)


def test_reference_passes(): assert task_grade(T, ref(T))["passed"]
def test_starter_fails(): assert not task_grade(T, starter(T))["passed"]


def test_p_only_fails(tmp_path):      # no integral action -> steady-state error
    r = task_grade(T, _write(tmp_path, "def design_pid(p):\n    return dict(Kp=1.0/p['K'], Ki=0.0, Kd=0.0)\n"))
    assert not r["checks"]["steady_state_error"]


def test_unstable_high_gain_fails(tmp_path):
    r = task_grade(T, _write(tmp_path, "def design_pid(p):\n    return dict(Kp=50.0, Ki=50.0, Kd=0.0)\n"))
    assert not r["passed"] and not r["checks"]["nominal_stable"]


def test_aggressive_textbook_rule_fails(tmp_path):   # SIMC tau_c=theta: overshoot ~20% > spec
    body = ("def design_pid(p):\n    Kp=p['tau1']/(p['K']*2*p['theta']); Ti=min(p['tau1'],8*p['theta'])\n"
            "    return dict(Kp=Kp, Ki=Kp/Ti, Kd=Kp*p['tau2'])\n")
    r = task_grade(T, _write(tmp_path, body))
    assert not r["checks"]["overshoot"]
