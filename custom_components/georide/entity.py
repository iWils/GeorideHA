"""Base entities for GeoRide."""

from __future__ import annotations

import inspect

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GeoRideCoordinator
from .models import GeoRideBeacon, GeoRideTracker


# HA >= 2026.8 links child devices with via_device_id (via_device is deprecated,
# removed in 2027.8). Older versions only know via_device.
_HAS_VIA_DEVICE_ID = "via_device_id" in inspect.signature(dr.DeviceRegistry.async_get_or_create).parameters


def tracker_model_name(tracker: GeoRideTracker) -> str:
    if tracker.version == 1:
        return "GeoRide 1"
    if tracker.version == 2:
        return "GeoRide 2"
    if tracker.version == 3:
        return "GeoRide 3" if tracker.model == "georide-3" else "GeoRide Mini"
    return "Prototype / Unknown"


class GeoRideTrackerEntity(CoordinatorEntity[GeoRideCoordinator]):
    """Entity attached to a GeoRide tracker (the motorbike).

    Entity IDs are NOT forced: Home Assistant keeps the ones already registered
    (e.g. switch.lock_2123980) thanks to the unchanged unique IDs.
    """

    _unique_prefix: str = ""
    _name_suffix: str = ""

    def __init__(self, coordinator: GeoRideCoordinator, tracker_id: int) -> None:
        super().__init__(coordinator)
        self._tracker_id = tracker_id
        tracker = self.tracker
        self._attr_unique_id = f"{self._unique_prefix}_{tracker_id}"
        self._attr_name = f"{tracker.tracker_name} {self._name_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, tracker_id)},
            name=tracker.tracker_name,
            manufacturer="GeoRide",
            model=tracker_model_name(tracker),
            sw_version=tracker.software_version,
            hw_version=str(tracker.version),
            suggested_area="Garage",
        )

    @property
    def tracker(self) -> GeoRideTracker:
        return self.coordinator.trackers[self._tracker_id]

    @property
    def available(self) -> bool:
        return super().available and self._tracker_id in self.coordinator.trackers


class GeoRideBeaconEntity(CoordinatorEntity[GeoRideCoordinator]):
    """Entity attached to a GeoRide beacon (badge), linked to its tracker."""

    _unique_prefix: str = ""
    _name_suffix: str = ""

    def __init__(self, coordinator: GeoRideCoordinator, beacon_id: int) -> None:
        super().__init__(coordinator)
        self._beacon_id = beacon_id
        self._attr_unique_id = f"{self._unique_prefix}_{beacon_id}"
        self._attr_name = f"{self.beacon.name} {self._name_suffix}"

    @property
    def beacon(self) -> GeoRideBeacon:
        return self.coordinator.beacons[self._beacon_id]

    @property
    def available(self) -> bool:
        return super().available and self._beacon_id in self.coordinator.beacons

    @property
    def device_info(self) -> DeviceInfo:
        beacon = self.beacon
        info = DeviceInfo(
            identifiers={(DOMAIN, beacon.beacon_id)},
            name=beacon.name,
            manufacturer="GeoRide",
            model="GeoRide Beacon",
            suggested_area="Garage",
        )
        if not _HAS_VIA_DEVICE_ID:
            info["via_device"] = (DOMAIN, beacon.linked_tracker_id)
            return info
        # HA 2026.8+: link to the parent device by its registry id
        parent = dr.async_get(self.hass).async_get_device(
            identifiers={(DOMAIN, beacon.linked_tracker_id)}
        )
        if parent is not None:
            info["via_device_id"] = parent.id
        return info
