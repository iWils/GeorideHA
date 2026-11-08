"""Fixtures for GeoRide tests."""
import time
from unittest.mock import patch

import jwt
import pytest

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.georide.const import DOMAIN

TRACKER_ID = 2123980
BEACON_ID = 93563


def make_token(days: float) -> str:
    return jwt.encode({"exp": int(time.time() + days * 86400)}, "secret", algorithm="HS256")


TRACKERS = [
    {
        "trackerId": TRACKER_ID,
        "trackerName": "CB-650-R",
        "latitude": 48.95,
        "longitude": 1.98,
        "fixtime": "2026-07-19T18:52:26.883Z",
        "speed": 10,  # knots
        "moving": False,
        "odometer": 7302325,
        "isLocked": True,
        "isStolen": False,
        "isCrashed": False,
        "isInEco": False,
        "status": "online",
        "role": "owner",
        "version": 3,
        "model": "georide-3",
        "softwareVersion": 42,
        "hasBeacon": True,
        "isUpToDate": True,
        "isOldSubscription": False,
        "subscription": {"id": 12, "type": "premium"},
        "externalBatteryVoltage": 13.4,
        "internalBatteryVoltage": 4.1,
    }
]
BEACONS = [{"id": BEACON_ID, "name": "Badge de Wilson", "batteryLevel": 255, "isUpdated": True}]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_api(aioclient_mock):
    aioclient_mock.get("https://api.georide.com/user/trackers", json=TRACKERS)
    aioclient_mock.get(f"https://api.georide.com/tracker/{TRACKER_ID}/beacon", json=BEACONS)
    aioclient_mock.post(f"https://api.georide.com/tracker/{TRACKER_ID}/unlock", status=204)
    aioclient_mock.post(f"https://api.georide.com/tracker/{TRACKER_ID}/lock", status=204)
    aioclient_mock.get("https://api.georide.com/user/new-token", json={"authToken": make_token(30)})
    aioclient_mock.post("https://api.georide.com/user/login", json={"authToken": make_token(30)})
    return aioclient_mock


@pytest.fixture
def no_socket():
    async def _noop(self):
        return None

    with patch("custom_components.georide.realtime.GeoRideSocket.async_run", _noop):
        yield


@pytest.fixture
def entry(hass):
    e = MockConfigEntry(
        domain=DOMAIN,
        title="moi@example.com",
        data={"email": "moi@example.com", "password": "pwd", "token": make_token(20)},
    )
    e.add_to_hass(hass)
    return e
