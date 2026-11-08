"""Real-time GeoRide events through Socket.IO (wss://socket.georide.com/).

Follows the official documentation (https://api.georide.com/index):
token passed in the ``auth`` object and websocket transport only.
Runs inside the Home Assistant event loop (socketio.AsyncClient).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
from typing import Any

import socketio

from .const import SOCKET_HOST

_LOGGER = logging.getLogger(__name__)

EVENTS = ("position", "alarm", "lockedPosition", "device", "refreshTrackersInstruction")


class GeoRideSocket:
    """Socket.IO client that stays connected as long as the integration is loaded."""

    def __init__(
        self,
        token_getter: Callable[[], str | None],
        handler: Callable[[str, Any], None],
    ) -> None:
        self._token_getter = token_getter
        self._handler = handler
        self._stopping = False
        self._sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=0,  # infinite
            reconnection_delay=2,
            reconnection_delay_max=120,
            logger=False,
            engineio_logger=False,
        )
        self._sio.on("connect", self._on_connect)
        self._sio.on("disconnect", self._on_disconnect)
        self._sio.on("message", self._on_message)
        for event in EVENTS:
            self._sio.on(event, self._make_handler(event))

    def _make_handler(self, event: str):
        async def _handler(data: Any = None) -> None:
            _LOGGER.debug("GeoRide socket event %s: %s", event, data)
            try:
                self._handler(event, data)
            except Exception:  # noqa: BLE001 - never kill the socket loop
                _LOGGER.exception("Error while handling GeoRide event %s", event)

        return _handler

    async def _on_connect(self) -> None:
        _LOGGER.info("GeoRide socket connected")

    async def _on_disconnect(self, *args: Any) -> None:
        if not self._stopping:
            _LOGGER.warning("GeoRide socket disconnected, reconnecting automatically")

    async def _on_message(self, data: Any = None) -> None:
        _LOGGER.debug("GeoRide socket message: %s", data)

    def _auth(self) -> dict[str, str]:
        # Called at each (re)connection: always sends the current token
        return {"token": self._token_getter() or ""}

    @property
    def connected(self) -> bool:
        return self._sio.connected

    async def async_run(self) -> None:
        """Connect, retrying with backoff until the first connection succeeds.

        Once connected, python-socketio handles reconnections by itself.
        """
        delay = 5
        while not self._stopping:
            try:
                await self._sio.connect(
                    SOCKET_HOST, transports=["websocket"], auth=self._auth, wait_timeout=20
                )
                await self._sio.wait()
                return
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("GeoRide socket connection failed (%s), retry in %s s", err, delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 300)

    async def async_stop(self) -> None:
        self._stopping = True
        if self._sio.connected:
            await self._sio.disconnect()
