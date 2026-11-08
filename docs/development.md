# Development notes

## Architecture

```
custom_components/georide/
├── __init__.py        setup / unload of the config entry, runtime_data, socket lifecycle
├── api.py             async REST client (aiohttp) + token management
├── realtime.py        Socket.IO client (socketio.AsyncClient) for real-time events
├── coordinator.py     DataUpdateCoordinator: REST polling + merge of socket events
├── models.py          GeoRideTracker / GeoRideBeacon (thin wrappers around the API JSON)
├── entity.py          base entities, device info (tracker and beacon devices)
├── config_flow.py     user + re-authentication flows
├── device_tracker.py  binary_sensor.py  sensor.py  switch.py  siren.py
└── const.py
```

### Data flow
1. `async_setup_entry` creates the `GeoRideApiClient`, makes sure the token is valid, runs the first
   coordinator refresh, forwards the platforms and starts the socket as a config-entry background task.
2. Every 10 minutes the coordinator calls `GET /user/trackers` and `GET /tracker/:id/beacon`.
3. Between two polls, socket events (`position`, `lockedPosition`, `device`, `alarm`,
   `refreshTrackersInstruction`) update the models in place, fire the `georide_*_event` events and call
   `async_update_listeners()` so that entities are refreshed immediately.
4. The socket is stopped on unload and on `homeassistant_stop`.

### GeoRide API used
Reference: <https://api.georide.com/index>

| Call | Usage |
|---|---|
| `POST /user/login` | Login (token valid 30 days) |
| `GET /user/new-token` | Token renewal, 5 days before expiry |
| `GET /user/trackers` | Trackers and their state |
| `GET /tracker/:id/beacon` | Beacons of a tracker |
| `POST /tracker/:id/lock`, `/unlock`, `/toggleLock` | Lock |
| `POST /tracker/:id/sonor-alarm/on` / `off` | Siren |
| `POST /tracker/:id/eco-mode/on` / `off` | Eco mode |
| Socket.IO `wss://socket.georide.com` | Real-time events — websocket transport, `auth: {token}` |

Notes:
- Speeds are returned in **knots**; `models.GeoRideTracker.speed_kmh` converts them.
- Beacons report `batteryLevel = 255` when the level is unknown.
- On HTTP 401/403 the client logs in again once; if it is refused, the coordinator raises
  `ConfigEntryAuthFailed`, which starts the re-authentication flow.

### Compatibility rules
- **Never change a `unique_id`**: entity IDs of existing installations depend on them
  (`<prefix>_<tracker_id>`, see `_unique_prefix` in each entity class).
- Entity IDs must not be forced (`self.entity_id = ...`).
- Device identifiers are `(DOMAIN, tracker_id)` / `(DOMAIN, beacon_id)` with the raw integer ids, as created
  by 1.x.
- Beacon devices are linked with `via_device_id` (HA ≥ 2026.8), with a fallback to `via_device` detected at
  import time.

## Tests

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
pytest
```

The tests mock the REST API with `aioclient_mock` and disable the socket. They check that historical entity
IDs are kept, unit conversions, socket event handling, token renewal and the config flow.

## Release
1. Update `version` in `custom_components/georide/manifest.json` and `CHANGELOG.md`.
2. Merge into `master`, then create a GitHub release `vX.Y.Z`: HACS proposes the update to users.
