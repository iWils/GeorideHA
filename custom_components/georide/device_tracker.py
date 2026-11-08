"""Position of GeoRide trackers."""

from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GeoRideConfigEntry
from .entity import GeoRideTrackerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GeoRideConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities(GeoRidePosition(coordinator, tracker_id) for tracker_id in coordinator.trackers)


class GeoRidePosition(GeoRideTrackerEntity, TrackerEntity):
    _unique_prefix = "georide_tracker"
    _name_suffix = "position"
    _attr_icon = "mdi:map-marker"
    _attr_source_type = SourceType.GPS
    _attr_location_accuracy = 20

    @property
    def latitude(self) -> float | None:
        return self.tracker.latitude

    @property
    def longitude(self) -> float | None:
        return self.tracker.longitude
