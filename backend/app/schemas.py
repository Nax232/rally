"""Strict F9 inputs; quantities are decimal and timestamps carry offsets."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, SecretStr, model_validator

Text = Annotated[str, Field(min_length=1, max_length=500)]
Quantity = Annotated[Decimal, Field(ge=0, allow_inf_nan=False, max_digits=24, decimal_places=8)]
Positive = Annotated[Decimal, Field(gt=0, allow_inf_nan=False, max_digits=24, decimal_places=8)]
Role = Literal["ADMIN", "OPERATOR", "ANALYST", "DECISION_MAKER", "VIEWER"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="after")
    def dates_not_future(self):
        for name in ("start_at", "observed_at", "reported_at", "baseline_at", "cutoff_at"):
            value = getattr(self, name, None)
            if value and value > datetime.now(UTC):
                raise ValueError(f"{name} cannot be in the future")
        return self


class Login(Input):
    login: Annotated[str, Field(min_length=3, max_length=100)]
    password: SecretStr = Field(min_length=12, max_length=256)


class UserCreate(Login):
    roles: list[Role] = Field(min_length=1, max_length=5)


class UserUpdate(Input):
    active: bool
    roles: list[Role] = Field(min_length=1, max_length=5)


class Member(Input):
    user_id: UUID


class Emergency(Input):
    name: Text
    hazard_type: Text
    territory: Text
    description: Text
    start_at: AwareDatetime
    mode: Literal["SIMULATED"] = "SIMULATED"


class EmergencyUpdate(Input):
    expected_revision: int = Field(ge=1)
    state: Literal["DRAFT", "ACTIVE", "CLOSED", "CANCELLED"]
    name: Text
    description: Text
    reason: Text


class Source(Input):
    organization: Text
    kind: Text
    description: Text


class Zone(Input):
    external_id: Text
    name: Text
    geometry: dict
    baseline_population: int = Field(ge=0)
    source_id: UUID
    baseline_at: AwareDatetime
    quality: Text

    @model_validator(mode="after")
    def geojson(self):
        if self.geometry.get("type") != "MultiPolygon" or "crs" in self.geometry:
            raise ValueError("Use GeoJSON MultiPolygon in EPSG:4326 without crs override")
        return self


class Observation(Input):
    metric_code: Text
    value_numeric: Quantity | None
    unit: Text
    evidence_status: Literal["OBSERVED", "ESTIMATED_APPROVED", "UNKNOWN"]
    quality_flags: list[Text] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def unknown(self):
        if (self.evidence_status == "UNKNOWN") != (self.value_numeric is None):
            raise ValueError("UNKNOWN requires null; known evidence requires a value")
        return self


class Report(Input):
    zone_id: UUID
    source_id: UUID
    observed_at: AwareDatetime
    comments: Text
    supersedes_id: UUID | None = None
    observations: list[Observation] = Field(min_length=1, max_length=100)


class Need(Input):
    zone_id: UUID
    resource_type_id: UUID | None = None
    specialty_type_id: UUID | None = None
    quantity: Quantity | None
    unit: Text
    status: Literal["CONFIRMED", "ESTIMATED_APPROVED", "UNKNOWN"]
    urgency: Text
    source_id: UUID
    reported_at: AwareDatetime
    supersedes_id: UUID | None = None

    @model_validator(mode="after")
    def known_and_type(self):
        if (self.resource_type_id is None) == (self.specialty_type_id is None):
            raise ValueError("Exactly one resource or specialty type is required")
        if (self.status == "UNKNOWN") != (self.quantity is None):
            raise ValueError("UNKNOWN requires null; known demand requires quantity")
        return self


class Resource(Input):
    code: Text
    unit: Text
    discrete: bool
    kg_per_unit: Quantity
    m3_per_unit: Quantity


class Specialty(Input):
    code: Text


class Depot(Input):
    name: Text
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    source_id: UUID


class Stock(Input):
    depot_id: UUID
    resource_type_id: UUID
    change_quantity: Decimal = Field(allow_inf_nan=False, max_digits=24, decimal_places=8)
    reason: Text
    source_id: UUID


class Asset(Input):
    asset_tag: Text
    type: Text
    state: Literal["AVAILABLE", "UNAVAILABLE", "MAINTENANCE"]
    base_id: UUID
    source_id: UUID
    max_kg: Positive | None = None
    max_m3: Positive | None = None
    specialty_type_id: UUID | None = None
    qualification_status: Literal["QUALIFIED", "UNVERIFIED", "EXPIRED"] = "UNVERIFIED"

    @model_validator(mode="after")
    def physical(self):
        if (self.max_kg is None) != (self.max_m3 is None):
            raise ValueError("Vehicle requires both mass and volume capacity")
        if self.max_kg is None and self.specialty_type_id is None:
            raise ValueError("At least vehicle or specialized unit data is required")
        return self


class AssetUpdate(Input):
    expected_revision: int = Field(ge=1)
    state: Literal["AVAILABLE", "UNAVAILABLE", "MAINTENANCE"]
    reason: Text


class Snapshot(Input):
    cutoff_at: AwareDatetime


class Job(Input):
    snapshot_id: UUID
    kind: Literal["SNAPSHOT_VERIFY"] = "SNAPSHOT_VERIFY"


EdgeStatus = Literal["VERIFIED_OPEN", "VERIFIED_RESTRICTED", "BLOCKED", "UNKNOWN"]


class RoadNode(Input):
    external_id: Text
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)


class RoadEdge(Input):
    external_id: Text
    from_node: Text
    to_node: Text
    from_longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    from_latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    to_longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    to_latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    length_m: Positive
    travel_sec: Positive
    status: EdgeStatus
    allowed_vehicle_types: list[Text] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def status_types(self):
        blocked = self.status in ("BLOCKED", "UNKNOWN")
        open_unrestricted = self.status == "VERIFIED_OPEN"
        if blocked and self.allowed_vehicle_types:
            raise ValueError("BLOCKED or UNKNOWN edges cannot allow vehicle types")
        if open_unrestricted and self.allowed_vehicle_types:
            raise ValueError("VERIFIED_OPEN edges must not restrict vehicle types")
        if self.status == "VERIFIED_RESTRICTED" and not self.allowed_vehicle_types:
            raise ValueError("VERIFIED_RESTRICTED requires at least one vehicle type")
        if any(not t.strip() for t in self.allowed_vehicle_types):
            raise ValueError("Vehicle types must be non-empty")
        return self


class RoadEdgeUpdate(Input):
    expected_revision: int = Field(ge=0)
    status: EdgeStatus
    allowed_vehicle_types: list[Text] = Field(default_factory=list, max_length=50)
    reason: Text

    @model_validator(mode="after")
    def status_types(self):
        blocked = self.status in ("BLOCKED", "UNKNOWN")
        open_unrestricted = self.status == "VERIFIED_OPEN"
        if blocked and self.allowed_vehicle_types:
            raise ValueError("BLOCKED or UNKNOWN edges cannot allow vehicle types")
        if open_unrestricted and self.allowed_vehicle_types:
            raise ValueError("VERIFIED_OPEN edges must not restrict vehicle types")
        if self.status == "VERIFIED_RESTRICTED" and not self.allowed_vehicle_types:
            raise ValueError("VERIFIED_RESTRICTED requires at least one vehicle type")
        if any(not t.strip() for t in self.allowed_vehicle_types):
            raise ValueError("Vehicle types must be non-empty")
        return self


class RoutePlanRequest(Input):
    external_id: Text
    depot_id: UUID
    zone_id: UUID
    vehicle_type: Text
    unload_sec: Positive = Field(gt=0)
    require_return: bool = False
    horizon_hours: Positive = Field(gt=0, le=72)
    expires_in_hours: Positive = Field(gt=0, le=72)
