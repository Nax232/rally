"""H7 route provider: loads the scenario graph, plans candidates and persists them.

Road edges and route candidates live in PostGIS; NetworkX/Dijkstra computes the
path and the sequence of arcs is stored so a route can be re-validated or
invalidated when an edge is blocked. Distances use geography/metric length,
never degrees-as-metres.
"""

from sqlalchemy import text

from app.gis.graph import Edge, ScenarioGraph
from app.gis.routes import (
    RouteCandidate,
    RouteError,
    plan_route,
)


def load_graph(db, emergency_id):
    """Read nodes/edges for an emergency into a ScenarioGraph."""
    rows = db.execute(
        text(
            """SELECT node_id,ST_X(geom),ST_Y(geom) FROM geo.road_nodes
            WHERE emergency_id=:e ORDER BY node_id"""
        ),
        {"e": str(emergency_id)},
    ).all()
    nodes = {str(node_id): (float(lon), float(lat)) for node_id, lon, lat in rows}
    edge_rows = db.execute(
        text(
            """SELECT edge_id,from_node,to_node,length_m,travel_sec,status,
            coalesce(allowed_vehicle_types,'{}'),network_revision
            FROM geo.road_edges WHERE emergency_id=:e ORDER BY edge_id"""
        ),
        {"e": str(emergency_id)},
    ).all()
    edges = [
        Edge(
            edge_id=str(row[0]),
            from_node=str(row[1]),
            to_node=str(row[2]),
            length_m=float(row[3]),
            travel_sec=float(row[4]),
            status=row[5],
            allowed_vehicle_types=frozenset(row[6] or ()),
            network_revision=int(row[7]),
        )
        for row in edge_rows
    ]
    return ScenarioGraph(edges, nodes=nodes)


def path_geojson(db, emergency_id, plan: RouteCandidate) -> str:
    """Assemble the ordered edge geometries into one LineString GeoJSON document."""
    edge_ids = [edge_id for edge_id, _seq, _direction in plan.edge_sequence]
    if not edge_ids:
        raise RouteError("ROUTE_NOT_FOUND")
    placeholders = ",".join(f":e{i}" for i in range(len(edge_ids)))
    params = {"e": str(emergency_id), **{f"e{i}": edge_id for i, edge_id in enumerate(edge_ids)}}
    rows = db.execute(
        text(
            f"""SELECT edge_id,ST_AsGeoJSON(geom) FROM geo.road_edges
            WHERE emergency_id=:e AND edge_id IN ({placeholders})"""
        ),
        params,
    ).all()
    lookup = {str(row[0]): row[1] for row in rows}
    coordinates = []
    for edge_id, _seq, direction in plan.edge_sequence:
        document = lookup.get(edge_id)
        if not document:
            raise RouteError("ROUTE_NOT_FOUND")
        import json

        points = json.loads(document)["coordinates"]
        if direction == "backward":
            points = list(reversed(points))
        if coordinates:
            points = points[1:]
        coordinates.extend(points)
    if len(coordinates) < 2:
        raise RouteError("ROUTE_NOT_FOUND")
    import json

    return json.dumps({"type": "LineString", "coordinates": coordinates})


def direction_is_backward(plan: RouteCandidate, edge_id: str) -> bool:
    for candidate_edge, _seq, direction in plan.edge_sequence:
        if candidate_edge == edge_id and direction == "backward":
            return True
    return False


def persist_candidate(
    db,
    emergency_id,
    external_id,
    depot_id,
    zone_id,
    plan: RouteCandidate,
    expires_at,
    require_return=True,
):
    """Store a candidate and its arc sequence; returns the stored route_id."""
    db.execute(
        text(
            """INSERT INTO geo.route_candidates(
            route_id,emergency_id,external_id,depot_id,zone_id,vehicle_type,path_geom,length_m,
            travel_sec,unload_sec,return_length_m,return_travel_sec,require_return,route_status,
            network_revision,expires_at)
            VALUES(:route_id,:emergency_id,:external_id,:depot_id,:zone_id,:vehicle_type,
            ST_GeomFromGeoJSON(:path),:length_m,:travel_sec,:unload_sec,:return_length_m,
            :return_travel_sec,:require_return,:route_status,:network_revision,:expires_at)"""
        ),
        {
            "route_id": plan.route_id,
            "emergency_id": str(emergency_id),
            "external_id": external_id,
            "depot_id": str(depot_id),
            "zone_id": str(zone_id),
            "vehicle_type": plan.vehicle_type,
            "path": path_geojson(db, emergency_id, plan),
            "length_m": plan.length_m,
            "travel_sec": plan.travel_sec,
            "unload_sec": plan.unload_sec,
            "return_length_m": plan.return_length_m,
            "return_travel_sec": plan.return_travel_sec,
            "require_return": bool(require_return),
            "route_status": plan.route_status,
            "network_revision": plan.network_revision,
            "expires_at": expires_at,
        },
    )
    for edge_id, sequence_no, direction in plan.edge_sequence:
        db.execute(
            text(
                """INSERT INTO geo.route_candidate_edges(route_id,edge_id,sequence_no,direction)
                VALUES(:route_id,:edge_id,:sequence_no,:direction)"""
            ),
            {
                "route_id": plan.route_id,
                "edge_id": edge_id,
                "sequence_no": sequence_no,
                "direction": direction,
            },
        )
    return plan.route_id


def plan_and_persist(
    db,
    emergency_id,
    external_id,
    depot_id,
    zone_id,
    vehicle_type,
    unload_sec,
    horizon_hr,
    require_return=True,
    expires_at=None,
    route_id=None,
):
    """Plan one verified candidate for a depot/zone pair and persist it."""
    graph = load_graph(db, emergency_id)
    depot = db.execute(
        text("SELECT ST_X(geom),ST_Y(geom) FROM ops.depots WHERE depot_id=:d"),
        {"d": str(depot_id)},
    ).first()
    if depot is None:
        raise RouteError("DEPOT_NOT_FOUND")
    origin = graph.nearest_node(float(depot[0]), float(depot[1]))
    if origin is None:
        raise RouteError("ROUTE_NOT_FOUND")
    zone = db.execute(
        text(
            """SELECT ST_X(ST_PointOnSurface(z.geom)),ST_Y(ST_PointOnSurface(z.geom))
            FROM geo.zones z WHERE z.zone_id=:z AND z.emergency_id=:e"""
        ),
        {"z": str(zone_id), "e": str(emergency_id)},
    ).first()
    if zone is None:
        raise RouteError("ZONE_NOT_FOUND")
    destination = graph.nearest_node(float(zone[0]), float(zone[1]))
    if destination is None:
        raise RouteError("ROUTE_NOT_FOUND")
    plan = plan_route(
        graph,
        vehicle_type,
        origin,
        destination,
        unload_sec,
        horizon_hr,
        require_return=require_return,
        route_id=route_id,
        network_revision=graph.network_revision,
    )
    if expires_at is None:
        raise RouteError("EXPIRY_REQUIRED")
    persist_candidate(
        db, emergency_id, external_id, depot_id, zone_id, plan, expires_at, require_return
    )
    return plan


def eligibility_for_planning(db, emergency_id, route_id, horizon_hr=None):
    """True only for a stored candidate that is still verified and unexpired."""
    row = db.execute(
        text(
            """SELECT route_status,expires_at,network_revision,
            (travel_sec+return_travel_sec+unload_sec)/3600.0 AS total_hr
            FROM geo.route_candidates WHERE route_id=:r AND emergency_id=:e"""
        ),
        {"r": str(route_id), "e": str(emergency_id)},
    ).first()
    if row is None:
        return False
    if row[0] not in ("VERIFIED_OPEN", "VERIFIED_RESTRICTED"):
        return False
    import datetime

    now = datetime.datetime.now(datetime.UTC)
    if row[1] is not None and row[1] <= now:
        return False
    if horizon_hr is not None and float(row[3]) > float(horizon_hr):
        return False
    return True
