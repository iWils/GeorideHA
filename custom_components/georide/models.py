"""Data models for the GeoRide API (https://api.georide.com/index)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import time
from typing import Any

from homeassistant.util import dt as dt_util

from .const import BEACON_BATTERY_UNKNOWN, KNOTS_TO_KMH, SIREN_ACTIVATION_DELAY


@dataclass
class GeoRideTracker:
    """A GeoRide tracker, as returned by GET /user/trackers."""

    tracker_id: int
    tracker_name: str
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    is_siren_on: bool = False
    siren_last_on_date: float = 0.0

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> GeoRideTracker:
        """Build a tracker from its JSON representation."""
        return cls(tracker_id=data["trackerId"], tracker_name=data["trackerName"], raw=dict(data))

    def update_from(self, other: GeoRideTracker) -> None:
        """Refresh the REST fields, keeping the local siren state."""
        self.tracker_name = other.tracker_name
        self.raw = other.raw

    def get(self, key: str, default: Any = None) -> Any:
        """Return a raw API field."""
        value = self.raw.get(key, default)
        return default if value is None else value

    # --- identity / device ---------------------------------------------------
    @property
    def version(self) -> int:
        return int(self.get("version", 1))

    @property
    def model(self) -> str | None:
        return self.get("model")

    @property
    def software_version(self) -> str:
        return str(self.get("softwareVersion", ""))

    @property
    def has_beacon(self) -> bool:
        return bool(self.get("hasBeacon", False))

    @property
    def role(self) -> str:
        return self.get("role", "owner")

    # --- status ---------------------------------------------------------------
    @property
    def status(self) -> str:
        return self.get("status", "unknown")

    @property
    def is_locked(self) -> bool:
        return bool(self.get("isLocked", False))

    @property
    def is_stolen(self) -> bool:
        return bool(self.get("isStolen", False))

    @property
    def is_crashed(self) -> bool:
        return bool(self.get("isCrashed", False))

    @property
    def is_in_eco(self) -> bool:
        return bool(self.get("isInEco", False))

    @property
    def is_up_to_date(self) -> bool:
        return bool(self.get("isUpToDate", True))

    @property
    def moving(self) -> bool:
        return bool(self.get("moving", False))

    @property
    def has_active_subscription(self) -> bool:
        if self.get("isOldSubscription", True):
            return self.raw.get("subscriptionId") is not None
        subscription = self.raw.get("subscription") or {}
        return subscription.get("id") is not None

    @property
    def siren_on(self) -> bool:
        """Siren state, automatically reset after the activation delay."""
        if self.is_siren_on and time.time() - SIREN_ACTIVATION_DELAY > self.siren_last_on_date:
            self.is_siren_on = False
        return self.is_siren_on

    def set_siren(self, state: bool) -> None:
        self.is_siren_on = state
        if state:
            self.siren_last_on_date = time.time()

    # --- measures ---------------------------------------------------------------
    @property
    def latitude(self) -> float | None:
        return self.raw.get("latitude")

    @property
    def longitude(self) -> float | None:
        return self.raw.get("longitude")

    @property
    def speed_kmh(self) -> float | None:
        """Speed converted from knots (API unit) to km/h."""
        speed = self.raw.get("speed")
        if speed is None:
            return None
        return round(float(speed) * KNOTS_TO_KMH, 1)

    @property
    def odometer(self) -> int | None:
        value = self.raw.get("odometer")
        return int(value) if isinstance(value, (int, float)) else None

    @property
    def fixtime(self) -> datetime | None:
        value = self.raw.get("fixtime")
        return dt_util.parse_datetime(value) if isinstance(value, str) else None

    @property
    def internal_battery_voltage(self) -> float | None:
        value = self.raw.get("internalBatteryVoltage")
        return value if isinstance(value, (int, float)) and value >= 0 else None

    @property
    def external_battery_voltage(self) -> float | None:
        value = self.raw.get("externalBatteryVoltage")
        return value if isinstance(value, (int, float)) and value >= 0 else None


@dataclass
class GeoRideBeacon:
    """A GeoRide beacon (badge), as returned by GET /tracker/:id/beacon."""

    beacon_id: int
    linked_tracker_id: int
    name: str
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_json(cls, data: dict[str, Any], tracker_id: int) -> GeoRideBeacon:
        return cls(
            beacon_id=data["id"],
            linked_tracker_id=tracker_id,
            name=data.get("name") or f"Beacon {data['id']}",
            raw=dict(data),
        )

    def update_from(self, other: GeoRideBeacon) -> None:
        self.name = other.name
        self.raw = other.raw

    @property
    def battery_level(self) -> int | None:
        value = self.raw.get("batteryLevel")
        if not isinstance(value, (int, float)) or value == BEACON_BATTERY_UNKNOWN or value > 100:
            return None
        return int(value)

    @property
    def is_updated(self) -> bool:
        return bool(self.raw.get("isUpdated", True))
