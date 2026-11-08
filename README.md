# GeoRide Home assistant
![Logo GeoRide](https://brands.home-assistant.io/georide/logo.png)

⚠️ This is not an official implementation
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/gpl-3.0)
[![install_badge](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.georide.total)](https://analytics.home-assistant.io/)

Official GeoRide website: https://georide.fr/

## Description
This component adds entities for GeoRide trackers and beacons, based on the
[official GeoRide API](https://api.georide.com/index):

- REST API `https://api.georide.com` (polled every 10 minutes)
- Real-time Socket.IO `wss://socket.georide.com` (positions, lock, alarms) — websocket transport,
  token sent in the `auth` object, infinite automatic reconnection

Requires **Home Assistant 2026.8 or newer**.

### Entities

    Position (device_tracker)
    Lock status / change lock status (switch)
    Eco mode (switch, GeoRide 3)
    Siren (siren, GeoRide 3)
    Stolen / crashed / owner / subscription / network / moving / update status (binary_sensor)
    Odometer in m and km
    Speed in km/h (the API returns knots, converted by the integration)
    Internal battery (GeoRide 3) and external battery (motorbike) voltage
    Fixtime (last registered position, timestamp)
    Beacon battery level (unknown when the beacon reports 255)

### Upgrade from 1.x
Unique IDs are unchanged: existing entity IDs, history and automations are kept.
The token is now renewed through `GET /user/new-token` before it expires (30 days);
if the password changes, Home Assistant asks for re-authentication.

## Question:

### How to have the odometer in Km ? (Deprecated, now you have an entity - thx @Inervo)

Simply add a sensor like this in configuration.yaml
(Replace XX by your tracker id)

```yaml
sensor:
  - platform: template # Conversion georide de m en km
    sensors:
      odometer_XX_km:
        friendly_name: "Odometter - Km"
        value_template: "{{ states.sensor.odometer_XX.state | multiply(0.001) | round(3, 'flour') }}"
        unit_of_measurement: 'Km'
```

### How to use the event:

Simply made a automation like this:

```yaml
alias: '[TEST] Send notification'
description: ''
trigger:
  - platform: event
    event_type: georide_lock_event
condition: []
action:
  - service: notify.mobile_app_oneplus_a3003
    data:
      message: 'The device {{ data.device_name }} have recieved a lock event'
mode: single

```


## Options

| Name | Type | Requirement | `default` Description
| ---- | ---- | ------- | -----------
| email | string | **Required** | GeoRide email
| password | string | **Required** | GeoRide password


## Installation
### Option 1
- Just follow the integration config steps.

### Option 2
- Add the following line in your configuration.yml
```yaml
    georide:
        email: <your-email>@exmple.com
        password: <your-password>
```

### Option 3 (manual)
- Download .zip git repo
- Go to /config (with File Editor or SSH)
- Unzip GeorideHA.zip
- Restart Home Assistant
- Go to "Integrations"
- If GeoRide not display, choose "add integration"
- Configure GeoRide add-on
