"""GeoRide integration for Home Assistant (https://api.georide.com/index)."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GeoRideApiClient, GeoRideAuthError, GeoRideError
from .const import CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN, DOMAIN, PLATFORMS
from .coordinator import GeoRideCoordinator
from .realtime import GeoRideSocket

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@dataclass
class GeoRideRuntimeData:
    """Objects shared by the platforms of a config entry."""

    api: GeoRideApiClient
    coordinator: GeoRideCoordinator
    socket: GeoRideSocket


type GeoRideConfigEntry = ConfigEntry[GeoRideRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: GeoRideConfigEntry) -> bool:
    """Set up GeoRide from a config entry."""

    async def _store_token(token: str) -> None:
        if entry.data.get(CONF_TOKEN) != token:
            hass.config_entries.async_update_entry(entry, data={**entry.data, CONF_TOKEN: token})

    api = GeoRideApiClient(
        async_get_clientsession(hass),
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_TOKEN),
        on_token_update=_store_token,
    )
    try:
        await api.async_get_token()
    except GeoRideAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except GeoRideError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = GeoRideCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    socket = GeoRideSocket(lambda: api.token, coordinator.handle_socket_event)
    entry.runtime_data = GeoRideRuntimeData(api=api, coordinator=coordinator, socket=socket)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Real-time events: background task, stopped with the entry or with HA
    entry.async_create_background_task(hass, socket.async_run(), f"{DOMAIN}_socket")
    entry.async_on_unload(socket.async_stop)

    async def _on_stop(_event: Event) -> None:
        await socket.async_stop()

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _on_stop))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GeoRideConfigEntry) -> bool:
    """Unload a GeoRide config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_config_entry_device(hass, config_entry, device_entry) -> bool:
    """Allow removing a GeoRide device from the UI."""
    return True
