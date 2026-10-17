"""Scenario graph over VERIFIED_OPEN edges; costs are metres/seconds, never degrees."""

from dataclasses import dataclass
from heapq import heappop, heappush
from math import cos, radians


@dataclass(frozen=True)
class Edge:
    edge_id: str
    from_node: str
    to_node: str
    length_m: float
    travel_sec: float
    status: str
    allowed_vehicle_types: frozenset[str]
    network_revision: int

    def traversable(self, vehicle_type: str) -> bool:
        if self.status not in ("VERIFIED_OPEN", "VERIFIED_RESTRICTED"):
            return False
        restricted = self.status == "VERIFIED_RESTRICTED" or self.allowed_vehicle_types
        if restricted and vehicle_type not in self.allowed_vehicle_types:
            return False
        return True


class ScenarioGraph:
    """Directed multigraph. UNKNOWN/BLOCKED/RESTRICTED edges are never traversed."""

    def __init__(self, edges, nodes=None, network_revision=None):
        revisions = []
        seen = set()
        self._outgoing = {}
        self.nodes = {str(k): (float(v[0]), float(v[1])) for k, v in (nodes or {}).items()}
        for edge in edges:
            if edge.edge_id in seen:
                raise ValueError("duplicate edge_id")
            if edge.from_node == edge.to_node:
                raise ValueError("self-loop edges are not allowed")
            if not (edge.length_m > 0 and edge.travel_sec > 0):
                raise ValueError("edge costs must be positive")
            seen.add(edge.edge_id)
            self._outgoing.setdefault(str(edge.from_node), []).append(edge)
            self.nodes.setdefault(str(edge.from_node), None)
            self.nodes.setdefault(str(edge.to_node), None)
            revisions.append(edge.network_revision)
        self.network_revision = (
            max(revisions, default=0) if network_revision is None else network_revision
        )

    def shortest(self, origin, destination, vehicle_type, weight="travel_sec"):
        """Return (edges, total) by Dijkstra with a stable edge_id tie-break, or None."""
        origin, destination = str(origin), str(destination)
        if origin == destination:
            return [], 0.0
        field = {"travel_sec": "travel_sec", "length_m": "length_m"}.get(weight)
        if field is None:
            raise ValueError("weight must be travel_sec or length_m")
        queue = [(0.0, origin)]
        best = {origin: 0.0}
        previous = {}
        while queue:
            cost, node = heappop(queue)
            if cost > best.get(node, float("inf")):
                continue
            if node == destination:
                break
            for edge in sorted(self._outgoing.get(node, ()), key=lambda e: e.edge_id):
                if not edge.traversable(vehicle_type):
                    continue
                candidate = cost + getattr(edge, field)
                neighbour = str(edge.to_node)
                if candidate < best.get(neighbour, float("inf")):
                    best[neighbour] = candidate
                    previous[neighbour] = edge
                    heappush(queue, (candidate, neighbour))
        if destination not in best:
            return None
        path = []
        node = destination
        while node != origin:
            edge = previous[node]
            path.append(edge)
            node = str(edge.from_node)
        path.reverse()
        return path, best[destination]

    def nearest_node(self, lon, lat):
        """Closest node by projected metres at this latitude, not raw degrees."""
        candidates = [(node_id, point) for node_id, point in self.nodes.items() if point]
        if not candidates:
            return None
        best = None
        for node_id, (node_lon, node_lat) in candidates:
            north = (node_lat - lat) * 111_320.0
            east = (node_lon - lon) * 111_320.0 * max(cos(radians(lat)), 1e-6)
            span = north * north + east * east
            if best is None or span < best[0]:
                best = (span, node_id)
        return best[1]
