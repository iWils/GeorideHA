"""Siren of GeoRide 3 trackers."""

from __future__ import annotations

from typing import Any

from homeassistant.components.siren import SirenEntity, SirenEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GeoRideConfigEntry
from .api import GeoRideError
from .entity import GeoRideTrackerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GeoRideConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        GeoRideSiren(coordinator, tracker_id)
        for tracker_id, tracker in coordinator.trackers.items()
        if tracker.version > 2
    )


class GeoRideSiren(GeoRideTrackerEntity, SirenEntity):
    """The tracker siren stops by itself after ~30 s."""

    _unique_prefix = "siren"
    _name_suffix = "siren"
    _attr_supported_features = SirenEntityFeature.TURN_ON | SirenEntityFeature.TURN_OFF

    @property
    def is_on(self) -> bool:
        return self.tracker.siren_on

    async def _set(self, state: bool) -> None:
        try:
            await self.coordinator.api.async_set_siren(self._tracker_id, state)
        except GeoRideError as err:
            raise HomeAssistantError(f"GeoRide: {err}") from err
        self.tracker.set_siren(state)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
