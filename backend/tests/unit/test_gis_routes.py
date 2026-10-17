"""H7 GIS: graph eligibility, metric geometry, horizon and C5."""

import pytest
from app.gis.graph import Edge, ScenarioGraph
from app.gis.routes import RouteError, accessibility_c5, eligibility, plan_route


def edge(
    edge_id, a, b, length_m=1000.0, travel_sec=120.0, status="VERIFIED_OPEN", allowed=(), rev=1
):
    return Edge(
        edge_id=edge_id,
        from_node=a,
        to_node=b,
        length_m=length_m,
        travel_sec=travel_sec,
        status=status,
        allowed_vehicle_types=frozenset(allowed),
        network_revision=rev,
    )


def test_graph_skips_blocked_unknown_and_restricted():
    edges = [
        edge("open", "A", "B"),
        edge("blocked", "B", "C", status="BLOCKED"),
        edge("unknown", "B", "D", status="UNKNOWN"),
        edge("restricted", "B", "E", status="VERIFIED_RESTRICTED", allowed=("TRUCK",)),
    ]
    graph = ScenarioGraph(edges, nodes={"A": (0, 0), "B": (0.001, 0), "C": (0.002, 0)})
    found = graph.shortest("A", "C", "TRUCK")
    assert found is None
    assert graph.shortest("A", "B", "TRUCK")[1] == pytest.approx(120.0)


def test_vehicle_restriction_and_open_equals_all():
    edges = [
        edge("e1", "A", "B", status="VERIFIED_RESTRICTED", allowed=("AMBULANCE",)),
        edge("e2", "B", "C"),
    ]
    graph = ScenarioGraph(edges)
    assert graph.shortest("A", "C", "AMBULANCE") is not None
    assert graph.shortest("A", "C", "TRUCK") is None


def test_shortest_prefers_time_not_distance_d18():
    # Short but slow alternative vs longer fast alternative.
    edges = [
        edge("slow_short", "A", "Z", length_m=5000, travel_sec=3600),
        edge("fast_long_1", "A", "M", length_m=20000, travel_sec=600),
        edge("fast_long_2", "M", "Z", length_m=20000, travel_sec=600),
    ]
    graph = ScenarioGraph(edges)
    path, total = graph.shortest("A", "Z", "TRUCK")
    assert [e.edge_id for e in path] == ["fast_long_1", "fast_long_2"]
    assert total == pytest.approx(1200.0)


def test_return_path_missing_one_way():
    edges = [edge("e1", "A", "B")]
    graph = ScenarioGraph(edges)
    with pytest.raises(RouteError) as error:
        plan_route(graph, "TRUCK", "A", "B", unload_sec=60, horizon_hr=6, require_return=True)
    assert error.value.code == "RETURN_PATH_MISSING"


def test_horizon_exceeded_reports_and_blocks_eligibility():
    edges = [edge("e1", "A", "B", travel_sec=7200), edge("e2", "B", "A", travel_sec=7200)]
    graph = ScenarioGraph(edges)
    with pytest.raises(RouteError) as error:
        plan_route(graph, "TRUCK", "A", "B", unload_sec=600, horizon_hr=2, require_return=True)
    assert error.value.code == "HORIZON_EXCEEDED"
    assert eligibility(None, 2) is False


def test_route_status_restricted_and_sequence_round_trip():
    edges = [
        edge("e1", "A", "B", status="VERIFIED_RESTRICTED", allowed=("TRUCK",)),
        edge("e2", "B", "A"),
    ]
    graph = ScenarioGraph(edges)
    plan = plan_route(graph, "TRUCK", "A", "B", unload_sec=60, horizon_hr=6, require_return=True)
    assert plan.route_status == "VERIFIED_RESTRICTED"
    assert plan.edge_sequence == [("e1", 0, "forward"), ("e2", 1, "backward")]
    assert eligibility(plan, 6) is True
    assert eligibility(plan, 0.05) is False


def test_c5_is_one_only_for_confirmed_absence_and_clips_delay():
    edges = [edge("e1", "A", "B", travel_sec=1000), edge("e2", "B", "A", travel_sec=1000)]
    graph = ScenarioGraph(edges)
    plan = plan_route(graph, "TRUCK", "A", "B", unload_sec=0.01, horizon_hr=6, require_return=True)
    base = plan.total_time_hr
    assert accessibility_c5(plan, base, 1.0) == pytest.approx(0.0)
    delayed = plan_route(
        graph, "TRUCK", "A", "B", unload_sec=3600, horizon_hr=6, require_return=True
    )
    assert delayed.total_time_hr == pytest.approx((1000 + 1000 + 3600) / 3600.0)
    assert accessibility_c5(delayed, base, 1.0) == pytest.approx(1.0)
    with pytest.raises(RouteError) as error:
        accessibility_c5(plan, 0, 1.0)
    assert error.value.code == "INVALID_C5_PARAMETERS"


def test_nearest_node_projects_metres_not_degrees():
    graph = ScenarioGraph([], nodes={"north": (0.0, 0.01), "east": (0.01, 0.0)})
    assert graph.nearest_node(0.0, 0.009) == "north"
    assert graph.nearest_node(0.009, 0.0) == "east"


def test_duplicate_and_self_loop_rejected():
    with pytest.raises(ValueError):
        ScenarioGraph([edge("e1", "A", "B"), edge("e1", "A", "B")])
    with pytest.raises(ValueError):
        ScenarioGraph([edge("e1", "A", "A")])
