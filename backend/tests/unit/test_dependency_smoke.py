import numpy as np
import pytest
from ortools.linear_solver import pywraplp


def test_scip_binary_and_continuous_variables_are_available():
    """Dependency smoke only. This does not implement or validate SIPRE F5."""
    solver = pywraplp.Solver.CreateSolver("SCIP")
    assert solver is not None, "SCIP backend is required; no silent substitution"
    discrete = solver.IntVar(0, 1, "discrete")
    continuous = solver.NumVar(0, 0.5, "continuous")
    solver.Maximize(2 * discrete + continuous)
    assert solver.Solve() == pywraplp.Solver.OPTIMAL
    assert continuous.solution_value() == pytest.approx(0.5)
    assert solver.Objective().Value() == pytest.approx(2.5)
    assert np.isfinite(solver.Objective().Value())
