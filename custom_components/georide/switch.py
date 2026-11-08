"""Switches for GeoRide trackers: lock and eco mode."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    entities: list[SwitchEntity] = []
    for tracker_id, tracker in coordinator.trackers.items():
        entities.append(GeoRideLockSwitch(coordinator, tracker_id))
        if tracker.version > 2:
            entities.append(GeoRideEcoModeSwitch(coordinator, tracker_id))
    async_add_entities(entities)


class GeoRideLockSwitch(GeoRideTrackerEntity, SwitchEntity):
    _unique_prefix = "lock"
    _name_suffix = "lock"

    @property
    def is_on(self) -> bool:
        return self.tracker.is_locked

    @property
    def icon(self) -> str:
        return "mdi:lock" if self.tracker.is_locked else "mdi:lock-open"

    async def _set(self, locked: bool) -> None:
        api = self.coordinator.api
        try:
            if locked:
                await api.async_lock(self._tracker_id)
            else:
                await api.async_unlock(self._tracker_id)
        except GeoRideError as err:
            raise HomeAssistantError(f"GeoRide: {err}") from err
        self.tracker.raw["isLocked"] = locked
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)

    async def async_toggle(self, **kwargs: Any) -> None:
        try:
            locked = await self.coordinator.api.async_toggle_lock(self._tracker_id)
        except GeoRideError as err:
            raise HomeAssistantError(f"GeoRide: {err}") from err
        self.tracker.raw["isLocked"] = locked
        self.async_write_ha_state()


class GeoRideEcoModeSwitch(GeoRideTrackerEntity, SwitchEntity):
    _unique_prefix = "eco_mode"
    _name_suffix = "eco mode"

    @property
    def is_on(self) -> bool:
        return self.tracker.is_in_eco

    @property
    def icon(self) -> str:
        return "mdi:battery-heart-variant" if self.tracker.is_in_eco else "mdi:battery"

    async def _set(self, state: bool) -> None:
        try:
            await self.coordinator.api.async_set_eco_mode(self._tracker_id, state)
        except GeoRideError as err:
            raise HomeAssistantError(f"GeoRide: {err}") from err
        self.tracker.raw["isInEco"] = state
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
