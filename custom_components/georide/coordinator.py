"""Coordinator holding the GeoRide account state (REST polling + real-time socket)."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GeoRideApiClient, GeoRideAuthError, GeoRideError
from .const import (
    DOMAIN,
    EVENT_ALARM,
    EVENT_DEVICE,
    EVENT_LOCK,
    EVENT_POSITION,
    EVENT_REFRESH,
    KNOWN_ALARMS,
    MIN_UNTIL_REFRESH,
)
from .models import GeoRideBeacon, GeoRideTracker

_LOGGER = logging.getLogger(__name__)


class GeoRideCoordinator(DataUpdateCoordinator[None]):
    """Polls GET /user/trackers and merges real-time socket events."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: GeoRideApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=MIN_UNTIL_REFRESH),
        )
        self.api = api
        self.trackers: dict[int, GeoRideTracker] = {}
        self.beacons: dict[int, GeoRideBeacon] = {}

    async def _async_update_data(self) -> None:
        try:
            fresh = await self.api.async_get_trackers()
            for tracker in fresh:
                if tracker.tracker_id in self.trackers:
                    self.trackers[tracker.tracker_id].update_from(tracker)
                else:
                    self.trackers[tracker.tracker_id] = tracker
                if tracker.version > 2 or tracker.has_beacon:
                    for beacon in await self.api.async_get_beacons(tracker.tracker_id):
                        if beacon.beacon_id in self.beacons:
                            self.beacons[beacon.beacon_id].update_from(beacon)
                        else:
                            self.beacons[beacon.beacon_id] = beacon
        except GeoRideAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except GeoRideError as err:
            raise UpdateFailed(str(err)) from err

    # --- real-time events (called from the HA event loop) --------------------------
    @callback
    def handle_socket_event(self, event: str, data: Any) -> None:
        if event == "refreshTrackersInstruction":
            self.hass.bus.async_fire(EVENT_REFRESH, {})
            self.hass.async_create_task(self.async_request_refresh())
            return

        if not isinstance(data, dict) or "trackerId" not in data:
            return
        tracker = self.trackers.get(data["trackerId"])
        if tracker is None:
            return
        event_data = {"device_id": tracker.tracker_id, "device_name": tracker.tracker_name}

        if event == "position":
            for key in ("latitude", "longitude", "moving", "speed", "fixtime"):
                if key in data:
                    tracker.raw[key] = data[key]
            self.hass.bus.async_fire(EVENT_POSITION, event_data)
        elif event == "lockedPosition":
            for key in ("lockedLatitude", "lockedLongitude", "isLocked"):
                if key in data:
                    tracker.raw[key] = data[key]
            self.hass.bus.async_fire(EVENT_LOCK, event_data)
        elif event == "device":
            if "status" in data:
                tracker.raw["status"] = data["status"]
            self.hass.bus.async_fire(EVENT_DEVICE, event_data)
        elif event == "alarm":
            name = data.get("name", "unknown")
            if name not in KNOWN_ALARMS:
                _LOGGER.warning("Unmanaged GeoRide alarm: %s", name)
            if name == "sonorAlarmOn":
                tracker.set_siren(True)
            elif name in ("deviceOffline", "deviceOnline"):
                tracker.raw["status"] = "offline" if name == "deviceOffline" else "online"
            elif name == "crash":
                tracker.raw["isCrashed"] = True
            self.hass.bus.async_fire(EVENT_ALARM, {**event_data, "type": f"alarm_{name}"})
        else:
            return

        # Push the change to the entities immediately
        self.async_update_listeners()
