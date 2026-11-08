# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [2.0.0] - 2026-11-08

First release of the maintained fork. Requires **Home Assistant 2026.8+**.

### Changed
- The [official GeoRide API](https://api.georide.com/index) is now called directly with an asynchronous
  client (aiohttp). The `georideapilib` library is no longer used: it pins `python-socketio==4.6.1`, which
  is not compatible with the current GeoRide Socket.IO server.
- Real-time events use `socketio.AsyncClient` inside the Home Assistant event loop, with the websocket
  transport and the token in the `auth` object, as documented by GeoRide.
- A single `DataUpdateCoordinator` holds all trackers and beacons; data is stored in `entry.runtime_data`.
- Sensors use `native_value` and proper device classes (distance, speed, voltage, battery, timestamp).
- `data.device_id` in `georide_*_event` events is now the tracker id (integer), as the documentation always
  stated (it used to be an internal, non-serialisable set).
- `iot_class` is now `cloud_push`; manifest and HACS metadata point to this fork.

### Added
- Token renewal through `GET /user/new-token` five days before expiry, with fallback to a full login.
- Re-authentication flow when the GeoRide credentials are refused.
- Config entry unique ID (the GeoRide email) and a `cannot_connect` error in the config flow.
- `georide_refresh_tracker_event` documented.
- Test suite based on `pytest-homeassistant-custom-component`.
- GeoRide 3S model name (from upstream 1.1.2RC, thanks to djodjo02130).
- GitHub Actions: `Validate` (hassfest, HACS, pytest — on push, PR and weekly) and `Release` (builds
  `georide.zip` and attaches it to each release; HACS installs from it).

### Fixed
- Speed was displayed in **knots** with a km/h unit: it is now converted (× 1.852).
- Real-time updates stopped for good after 5 failed reconnections (delays of 1,000 to 5,000 s): the socket
  now reconnects forever (2 s to 2 min) and always sends the current token.
- Socket callbacks ran outside the Home Assistant event loop and blocked on it; the server-side refresh
  instruction was never executed (coroutine not awaited).
- The socket thread was not stopped when Home Assistant shut down (`Thread ... is still running at shutdown`).
- Beacon battery reported 255 %: it is now *unknown*.
- The siren reused the `eco_mode` entity ID of the switch in an invalid `georide.` domain.
- Entity IDs were forced with an invalid format (`switch.lock.<id>`), which stops working in Home Assistant
  2027.2. They are no longer forced; existing IDs are kept thanks to unchanged unique IDs.
- Deprecated `via_device` replaced by `via_device_id` (removed in Home Assistant 2027.8), with automatic
  fallback on older versions.
- `TrackerEntity` is imported from `homeassistant.components.device_tracker` (old alias removed in 2027.6).

### Removed
- YAML configuration (`georide:` in `configuration.yaml`) and its import flow: configure the integration from
  the UI.
- Travis CI configuration (Python 3.7).

## [1.1.1] - 2024-11-12

Last upstream release by [ptimatth](https://github.com/ptimatth/GeorideHA). See the upstream repository
for earlier history.

[2.0.0]: https://github.com/iWils/GeorideHA/compare/691b5c2...v2.0.0
[1.1.1]: https://github.com/ptimatth/GeorideHA/releases
