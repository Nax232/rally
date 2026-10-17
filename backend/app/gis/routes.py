"""Verified routes for one destination per vehicle (H7, D18).

Selection policy: the first leg is the *fastest* path in travel time that also
fits the horizon (including unload and optional return). Dijkstra by time
avoids picking a short but slow road that exceeds H when a valid longer
alternative exists. Costs are metric (metres/seconds); degrees are never
treated as metres.
"""

import uuid
from dataclasses import dataclass

from app.gis.graph import Edge, ScenarioGraph


class RouteError(ValueError):
    """A stable machine-readable reason why no verified route exists."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class RouteCandidate:
    """One destination per vehicle; not a CVRP tour."""

    route_id: str
    vehicle_type: str
    edge_sequence: list[tuple[str, int, str]]
    length_m: float
    travel_sec: float
    return_length_m: float
    return_travel_sec: float
    unload_sec: float
    route_status: str
    network_revision: int

    @property
    def total_time_hr(self) -> float:
        return (self.travel_sec + self.return_travel_sec + self.unload_sec) / 3600.0

    @property
    def total_length_km(self) -> float:
        return (self.length_m + self.return_length_m) / 1000.0


def reverse_path(graph: ScenarioGraph, edges: list[Edge], vehicle_type: str):
    """Return-path edges from the destination back to the depot, or None."""
    if not edges:
        return []
    origin = str(edges[0].from_node)
    destination = str(edges[-1].to_node)
    if destination == origin:
        return []
    found = graph.shortest(destination, origin, vehicle_type, "travel_sec")
    return None if found is None else found[0]


def plan_route(
    graph: ScenarioGraph,
    vehicle_type: str,
    origin,
    destination,
    unload_sec: float,
    horizon_hr: float,
    require_return: bool = True,
    route_id: str | None = None,
    network_revision: int | None = None,
):
    """Build a verified candidate or raise RouteError with a stable code."""
    unload_sec = float(unload_sec)
    horizon_hr = float(horizon_hr)
    if unload_sec <= 0 or horizon_hr <= 0:
        raise RouteError("INVALID_ROUTE_PARAMETERS")
    found = graph.shortest(str(origin), str(destination), vehicle_type, "travel_sec")
    if found is None:
        raise RouteError("ROUTE_NOT_FOUND")
    outbound, travel_sec = found
    if not outbound:
        raise RouteError("ROUTE_NOT_FOUND")
    return_edges = reverse_path(graph, outbound, vehicle_type) if require_return else []
    if require_return and return_edges is None:
        raise RouteError("RETURN_PATH_MISSING")
    length_m = float(sum(edge.length_m for edge in outbound))
    return_length_m = float(sum(edge.length_m for edge in return_edges))
    return_travel_sec = float(sum(edge.travel_sec for edge in return_edges))
    total_hr = (travel_sec + return_travel_sec + unload_sec) / 3600.0
    if total_hr > horizon_hr:
        raise RouteError(
            "HORIZON_EXCEEDED",
            detail=f"fastest round trip {total_hr:.6f}h exceeds horizon {horizon_hr:.6f}h",
        )
    restricted = any(
        edge.status == "VERIFIED_RESTRICTED" or bool(edge.allowed_vehicle_types)
        for edge in list(outbound) + list(return_edges)
    )
    sequence = [(edge.edge_id, index, "forward") for index, edge in enumerate(outbound)]
    offset = len(sequence)
    sequence.extend(
        (edge.edge_id, offset + index, "backward") for index, edge in enumerate(return_edges)
    )
    revision = graph.network_revision if network_revision is None else network_revision
    return RouteCandidate(
        route_id=route_id or str(uuid.uuid4()),
        vehicle_type=vehicle_type,
        edge_sequence=sequence,
        length_m=length_m,
        travel_sec=travel_sec,
        return_length_m=return_length_m,
        return_travel_sec=return_travel_sec,
        unload_sec=unload_sec,
        route_status="VERIFIED_RESTRICTED" if restricted else "VERIFIED_OPEN",
        network_revision=revision,
    )


def eligibility(plan: RouteCandidate | None, horizon_hr: float) -> bool:
    """Eligible for planning only when verified and within the horizon."""
    return (
        plan is not None
        and plan.route_status in ("VERIFIED_OPEN", "VERIFIED_RESTRICTED")
        and plan.total_time_hr <= horizon_hr
        and bool(plan.edge_sequence)
    )


def accessibility_c5(plan: RouteCandidate | None, base_time_hr: float, ratio_max: float):
    """C5 accessibility (F4): confirmed absence of route -> 1; known route -> clip delay.

    An unknown or unverified route is never assumed open and never silently
    mapped to zero or one; callers must treat the criterion as unavailable
    instead of inventing a travel time.
    """
    if base_time_hr <= 0 or ratio_max <= 0:
        raise RouteError("INVALID_C5_PARAMETERS")
    if plan is None or not eligibility(plan, horizon_hr=float("inf")):
        return 1.0
    return max(0.0, min((plan.total_time_hr / base_time_hr - 1.0) / ratio_max, 1.0))
