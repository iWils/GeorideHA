"""Integration tests: entity ids preserved, conversions, socket events, token renewal."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.georide.const import DOMAIN

from .conftest import BEACON_ID, TRACKER_ID, make_token

# Entity ids created by the old (1.1.1) integration
OLD_IDS = {
    ("switch", f"lock_{TRACKER_ID}"): f"switch.lock_{TRACKER_ID}",
    ("sensor", f"speed_{TRACKER_ID}"): f"sensor.speed_{TRACKER_ID}",
    ("sensor", f"battery_percent_{BEACON_ID}"): f"sensor.battery_percent_{BEACON_ID}",
    ("siren", f"siren_{TRACKER_ID}"): f"siren.eco_mode_{TRACKER_ID}",
    ("binary_sensor", f"update_{TRACKER_ID}"): f"binary_sensor.update_{TRACKER_ID}",
    ("device_tracker", f"georide_tracker_{TRACKER_ID}"): f"device_tracker.{TRACKER_ID}",
}


async def test_setup_keeps_ids_and_values(hass: HomeAssistant, entry, mock_api, no_socket):
    ent_reg = er.async_get(hass)
    for (platform, unique_id), entity_id in OLD_IDS.items():
        ent_reg.async_get_or_create(
            platform, DOMAIN, unique_id, config_entry=entry,
            suggested_object_id=entity_id.split(".", 1)[1],
        )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Existing entity ids are kept (no forced, invalid entity_id any more)
    for (platform, unique_id), entity_id in OLD_IDS.items():
        assert ent_reg.async_get_entity_id(platform, DOMAIN, unique_id) == entity_id
        assert hass.states.get(entity_id) is not None, entity_id

    # Knots -> km/h
    assert hass.states.get(f"sensor.speed_{TRACKER_ID}").state == "18.5"
    assert hass.states.get(f"sensor.speed_{TRACKER_ID}").attributes["unit_of_measurement"] == "km/h"
    # 255 % -> unknown
    assert hass.states.get(f"sensor.battery_percent_{BEACON_ID}").state == "unknown"
    assert hass.states.get(f"switch.lock_{TRACKER_ID}").state == "on"
    assert hass.states.get(f"device_tracker.{TRACKER_ID}").attributes["latitude"] == 48.95

    # Beacon device linked to the tracker device through via_device_id
    dev_reg = dr.async_get(hass)
    tracker_dev = dev_reg.async_get_device(identifiers={(DOMAIN, TRACKER_ID)})
    beacon_dev = dev_reg.async_get_device(identifiers={(DOMAIN, BEACON_ID)})
    assert tracker_dev and beacon_dev
    assert beacon_dev.via_device_id == tracker_dev.id
    assert tracker_dev.model == "GeoRide 3"

    # Real-time position event (as received from the socket)
    coordinator = entry.runtime_data.coordinator
    events = []
    hass.bus.async_listen(f"{DOMAIN}_position_event", lambda e: events.append(e))
    coordinator.handle_socket_event(
        "position",
        {"trackerId": TRACKER_ID, "latitude": 49.0, "longitude": 2.0, "moving": True,
         "speed": 20, "fixtime": "2026-11-08T18:00:00.000Z"},
    )
    await hass.async_block_till_done()
    assert hass.states.get(f"device_tracker.{TRACKER_ID}").attributes["latitude"] == 49.0
    assert hass.states.get(f"sensor.speed_{TRACKER_ID}").state == "37.0"
    assert events and events[0].data == {"device_id": TRACKER_ID, "device_name": "CB-650-R"}

    # Lock event + switch action
    coordinator.handle_socket_event("lockedPosition", {"trackerId": TRACKER_ID, "isLocked": False})
    await hass.async_block_till_done()
    assert hass.states.get(f"switch.lock_{TRACKER_ID}").state == "off"
    await hass.services.async_call("switch", "turn_on", {"entity_id": f"switch.lock_{TRACKER_ID}"}, blocking=True)
    assert hass.states.get(f"switch.lock_{TRACKER_ID}").state == "on"

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_token_renewed_before_expiry(hass: HomeAssistant, mock_api, no_socket):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    old = make_token(2)  # expires in 2 days < 5 days safety margin
    e = MockConfigEntry(domain=DOMAIN, data={"email": "a@b.c", "password": "p", "token": old})
    e.add_to_hass(hass)
    assert await hass.config_entries.async_setup(e.entry_id)
    await hass.async_block_till_done()
    assert e.data["token"] != old
    assert any(str(call[1]).endswith("/user/new-token") for call in mock_api.mock_calls)
