"""Async client for the GeoRide REST API (https://api.georide.com/index)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import json as json_lib
import logging
import time
from typing import Any

import aiohttp
import jwt

from .const import API_HOST, TOKEN_SAFE_DAY
from .models import GeoRideBeacon, GeoRideTracker

_LOGGER = logging.getLogger(__name__)

TIMEOUT = aiohttp.ClientTimeout(total=20)


class GeoRideError(Exception):
    """Generic GeoRide API error."""


class GeoRideAuthError(GeoRideError):
    """Credentials or token refused."""


class GeoRideApiClient:
    """Small async wrapper around the GeoRide REST API, with token management."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
        token: str | None = None,
        on_token_update: Callable[[str], Awaitable[None] | None] | None = None,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._token = token
        self._on_token_update = on_token_update

    @property
    def token(self) -> str | None:
        """Current token (used by the socket at (re)connection)."""
        return self._token

    # --- low level ---------------------------------------------------------------
    async def _request(
        self, method: str, endpoint: str, *, auth: bool = True, json: Any = None
    ) -> Any:
        try:
            return await self._raw_request(method, endpoint, auth=auth, json=json)
        except GeoRideAuthError:
            if not auth:
                raise
            # Token revoked or expired: log in again once and retry
            _LOGGER.info("GeoRide token refused, logging in again")
            await self.async_login()
            return await self._raw_request(method, endpoint, auth=auth, json=json)

    async def _raw_request(
        self, method: str, endpoint: str, *, auth: bool = True, json: Any = None
    ) -> Any:
        headers = {"Content-Type": "application/json"}
        if auth:
            headers["Authorization"] = f"Bearer {await self.async_get_token()}"
        try:
            async with self._session.request(
                method, f"{API_HOST}{endpoint}", headers=headers, json=json, timeout=TIMEOUT
            ) as resp:
                if resp.status in (401, 403):
                    raise GeoRideAuthError(f"{method} {endpoint}: HTTP {resp.status}")
                if resp.status >= 400:
                    raise GeoRideError(f"{method} {endpoint}: HTTP {resp.status}")
                if resp.status == 204:
                    return None
                body = await resp.text()
                return json_lib.loads(body) if body.strip() else None
        except (aiohttp.ClientError, TimeoutError) as err:
            raise GeoRideError(f"{method} {endpoint}: {err}") from err

    # --- authentication ----------------------------------------------------------
    async def async_login(self) -> str:
        """POST /user/login: returns a token valid 30 days."""
        data = await self._request(
            "POST", "/user/login", auth=False,
            json={"email": self._email, "password": self._password},
        )
        await self._set_token(data["authToken"])
        return self._token

    async def _set_token(self, token: str) -> None:
        self._token = token
        if self._on_token_update is not None:
            result = self._on_token_update(token)
            if result is not None:
                await result

    @staticmethod
    def _token_expiration(token: str) -> int:
        try:
            return int(jwt.decode(token, options={"verify_signature": False})["exp"])
        except (jwt.PyJWTError, KeyError, ValueError):
            return 0

    async def async_get_token(self) -> str:
        """Return a valid token, renewing it via /user/new-token when close to expiry."""
        if not self._token:
            return await self.async_login()
        if self._token_expiration(self._token) - TOKEN_SAFE_DAY < time.time():
            _LOGGER.info("GeoRide token close to expiry, renewing it")
            try:
                async with self._session.get(
                    f"{API_HOST}/user/new-token",
                    headers={"Authorization": f"Bearer {self._token}"},
                    timeout=TIMEOUT,
                ) as resp:
                    if resp.status == 200:
                        await self._set_token((await resp.json(content_type=None))["authToken"])
                        return self._token
                    _LOGGER.warning("Token renewal refused (HTTP %s), logging in again", resp.status)
            except (aiohttp.ClientError, TimeoutError) as err:
                _LOGGER.warning("Token renewal failed (%s), logging in again", err)
            return await self.async_login()
        return self._token

    # --- trackers ----------------------------------------------------------------
    async def async_get_trackers(self) -> list[GeoRideTracker]:
        data = await self._request("GET", "/user/trackers")
        return [GeoRideTracker.from_json(item) for item in data or []]

    async def async_get_beacons(self, tracker_id: int) -> list[GeoRideBeacon]:
        try:
            data = await self._request("GET", f"/tracker/{tracker_id}/beacon")
        except GeoRideAuthError:
            raise
        except GeoRideError as err:
            _LOGGER.debug("No beacon for tracker %s: %s", tracker_id, err)
            return []
        if isinstance(data, dict):
            data = [data]
        return [GeoRideBeacon.from_json(item, tracker_id) for item in data or []]

    async def async_lock(self, tracker_id: int) -> None:
        await self._request("POST", f"/tracker/{tracker_id}/lock")

    async def async_unlock(self, tracker_id: int) -> None:
        await self._request("POST", f"/tracker/{tracker_id}/unlock")

    async def async_toggle_lock(self, tracker_id: int) -> bool:
        data = await self._request("POST", f"/tracker/{tracker_id}/toggleLock")
        return bool((data or {}).get("locked"))

    async def async_set_siren(self, tracker_id: int, state: bool) -> None:
        await self._request("POST", f"/tracker/{tracker_id}/sonor-alarm/{'on' if state else 'off'}")

    async def async_set_eco_mode(self, tracker_id: int, state: bool) -> None:
        await self._request("POST", f"/tracker/{tracker_id}/eco-mode/{'on' if state else 'off'}")
