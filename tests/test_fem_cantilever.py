from helpers import task_grade, ref, starter
T = "fem_cantilever"


def test_reference_passes(): assert task_grade(T, ref(T))["passed"]
def test_starter_fails(): assert not task_grade(T, starter(T))["passed"]


def test_formula_cheat_fails(tmp_path):
    f = tmp_path / "s.py"
    f.write_text("def solve_cantilever(p,nx,ny):\n"
                 "    I=p['b']*p['h']**3/12\n    return p['P']*p['L']**3/(3*p['E']*I)\n")
    assert not task_grade(T, str(f))["passed"]


def test_hardcoded_fails(tmp_path):
    f = tmp_path / "s.py"
    f.write_text("def solve_cantilever(p,nx,ny):\n    return 0.0123\n")
    assert not task_grade(T, str(f))["passed"]
