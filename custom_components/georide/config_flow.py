"""Config flow for GeoRide."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GeoRideApiClient, GeoRideAuthError, GeoRideError
from .const import CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): vol.All(str, vol.Length(min=3)),
        vol.Required(CONF_PASSWORD): str,
    }
)


class GeoRideConfigFlow(ConfigFlow, domain=DOMAIN):
    """GeoRide config flow."""

    VERSION = 1

    async def _async_login(self, email: str, password: str) -> tuple[str | None, dict[str, str]]:
        api = GeoRideApiClient(async_get_clientsession(self.hass), email, password)
        try:
            return await api.async_login(), {}
        except GeoRideAuthError:
            return None, {"base": "faulty_credentials"}
        except GeoRideError:
            return None, {"base": "cannot_connect"}
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error during GeoRide login")
            return None, {"base": "unknown"}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()
            token, errors = await self._async_login(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
            if token:
                return self.async_create_entry(
                    title=user_input[CONF_EMAIL], data={**user_input, CONF_TOKEN: token}
                )
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            token, errors = await self._async_login(entry.data[CONF_EMAIL], user_input[CONF_PASSWORD])
            if token:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD], CONF_TOKEN: token},
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={"email": entry.data[CONF_EMAIL]},
            errors=errors,
        )
