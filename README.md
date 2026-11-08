# GeoRide for Home Assistant

![Logo GeoRide](https://brands.home-assistant.io/georide/logo.png)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz/docs/faq/custom_repositories/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/gpl-3.0)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.8%2B-41BDF5.svg?style=for-the-badge)

> ⚠️ Unofficial integration, not affiliated with GeoRide. Official website: https://georide.fr/
>
> This repository is a maintained fork of [ptimatth/GeorideHA](https://github.com/ptimatth/GeorideHA)
> (last upstream release 1.1.1, November 2024).

Track your motorbike and control your **GeoRide** tracker (GeoRide 1, 2, 3, Mini) and **GeoRide beacons**
(badges) from Home Assistant, using the [official GeoRide API](https://api.georide.com/index):

| Channel | Endpoint | Usage |
|---|---|---|
| REST API | `https://api.georide.com` | Login, trackers, beacons, lock / unlock, siren, eco mode — polled every 10 min |
| Socket.IO | `wss://socket.georide.com` | Real-time positions, lock changes, alarms, device status |

The real-time connection follows the official documentation: websocket transport only, token sent in the
`auth` object, infinite automatic reconnection with an up-to-date token.

## Requirements

- Home Assistant **2026.8** or newer
- A GeoRide account (same credentials as the GeoRide mobile app) with an active subscription

## Installation

### HACS (recommended)
1. HACS → ⋮ → **Custom repositories** → add `https://github.com/iWils/GeorideHA`, type **Integration**.
2. Search for **GeoRide**, install it, then restart Home Assistant.
3. **Settings → Devices & services → Add integration → GeoRide**, then enter your GeoRide email and password.

### Manual
1. Copy `custom_components/georide` into `/config/custom_components/`.
2. Restart Home Assistant and add the integration as above.

> YAML configuration (`georide:` in `configuration.yaml`) is no longer supported since 2.0.0:
> use the UI.

## Entities

One device is created per tracker (suggested area: *Garage*) and per beacon, the beacon being linked to
its tracker. Entity names are `<tracker or beacon name> <suffix>`.

| Platform | Name suffix | Description | Trackers |
|---|---|---|---|
| Device tracker | `position` | GPS position | all |
| Switch | `lock` | Lock status, lock / unlock | all |
| Switch | `eco mode` | Eco mode | GeoRide 3 / Mini |
| Siren | `siren` | Tracker siren (stops by itself after ~30 s) | GeoRide 3 / Mini |
| Sensor | `odometer` | Odometer (m) | all |
| Sensor | `odometer km` | Odometer (km) | all |
| Sensor | `speed` | Speed in km/h (the API returns knots, converted by the integration) | all |
| Sensor | `last fixed position` | Date of the last GPS position | all |
| Sensor | `internal_battery_voltage` | Tracker internal battery (V) | GeoRide 3 / Mini |
| Sensor | `external_battery_voltage` | Motorbike battery (V) | GeoRide 3 / Mini |
| Sensor | `battery percent` | Beacon battery (%) — *unknown* when the beacon reports 255 | beacons |
| Binary sensor | `is not stolen` | On = declared stolen | all |
| Binary sensor | `is not crashed` | On = crash detected | all |
| Binary sensor | `is own tracker` | On = you own the tracker (not shared with you) | all |
| Binary sensor | `has an active subscription` | Subscription active | all |
| Binary sensor | `have network` | Tracker online | all |
| Binary sensor | `is moving` | Motorbike moving | all |
| Binary sensor | `have an update` | Firmware update available | all / beacons |

Entity IDs:
- **new installations**: generated from the name, e.g. `switch.cb_650_r_lock`;
- **installations upgraded from 1.x** keep their historical IDs, e.g. `switch.lock_<id>`, `sensor.speed_<id>`,
  `device_tracker.<id>`, `siren.eco_mode_<id>` (the siren historically used this ID).

> The *is not stolen* / *is not crashed* names are historical: these binary sensors use the *problem*
> device class, so **on means stolen / crashed**. Rename them in the UI if you prefer.

## Events

The integration fires events on the Home Assistant bus. `data.device_id` is the tracker id (integer) and
`data.device_name` the tracker name.

| Event | When |
|---|---|
| `georide_position_event` | The tracker sent a position |
| `georide_lock_event` | The tracker was locked or unlocked |
| `georide_device_event` | The tracker status changed (online / offline) |
| `georide_alarm_event` | The tracker raised an alarm (`data.type`, see below) |
| `georide_refresh_tracker_event` | GeoRide asked to refresh the tracker list |

Alarm types (`data.type`): `alarm_vibration`, `alarm_exitZone`, `alarm_crash`, `alarm_crashParking`,
`alarm_deviceOffline`, `alarm_deviceOnline`, `alarm_powerCut`, `alarm_powerUncut`, `alarm_batteryWarning`,
`alarm_temperatureWarning`, `alarm_magnetOn`, `alarm_magnetOff`, `alarm_sonorAlarmOn`.

Example — notify on vibration while the motorbike is locked:

```yaml
alias: GeoRide – vibration alert
triggers:
  - trigger: event
    event_type: georide_alarm_event
    event_data:
      type: alarm_vibration
actions:
  - action: notify.mobile_app_my_phone
    data:
      title: GeoRide
      message: "Vibration detected on {{ trigger.event.data.device_name }}"
mode: single
```

More examples in [docs/automations.md](docs/automations.md).

## Upgrading from 1.x

- Unique IDs are unchanged: **existing entity IDs, history, dashboards and automations are kept**.
- Units: speed is now really in km/h (1.x displayed knots labelled km/h); odometers now have the *distance*
  device class.
- `data.device_id` in events is now the tracker id (integer), as documented.
- The token is renewed through `GET /user/new-token` before it expires (30 days). If your GeoRide password
  changes, Home Assistant shows a re-authentication request.
- The `georideapilib` library is no longer used; `python-socketio` ≥ 5.11 is installed instead.

See the [CHANGELOG](CHANGELOG.md) for details.

## Troubleshooting

Enable debug logs:

```yaml
logger:
  logs:
    custom_components.georide: debug
```

| Symptom | Check |
|---|---|
| Position or lock never updates in real time | The log must show `GeoRide socket connected`. Disconnections are logged as warnings and reconnected automatically. |
| *Re-authentication required* notification | Your GeoRide password changed: enter it again from the notification. |
| Beacon battery *unknown* | The beacon did not report its level (255) — normal right after a battery change. |

Architecture and development notes: [docs/development.md](docs/development.md).

## License

GPL-3.0 — see [LICENSE](LICENSE).
