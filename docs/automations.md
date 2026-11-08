# Automation examples

Replace `cb_650_r` / `<id>` with your own entity IDs (Settings → Entities, filter on *georide*).
All examples use the current Home Assistant syntax (`triggers` / `actions`).

## Alarm notifications

Every GeoRide alarm is fired as `georide_alarm_event`, with `data.type` = `alarm_<name>`.

```yaml
alias: GeoRide – alarms
triggers:
  - trigger: event
    event_type: georide_alarm_event
variables:
  labels:
    alarm_vibration: "Vibration detected"
    alarm_exitZone: "Left the geofence"
    alarm_crash: "CRASH detected"
    alarm_crashParking: "Knocked over while parked"
    alarm_powerCut: "Motorbike battery disconnected"
    alarm_batteryWarning: "Tracker battery low"
    alarm_deviceOffline: "Tracker offline"
actions:
  - condition: template
    value_template: "{{ trigger.event.data.type in labels }}"
  - action: notify.mobile_app_my_phone
    data:
      title: "GeoRide – {{ trigger.event.data.device_name }}"
      message: "{{ labels[trigger.event.data.type] }}"
      data:
        push:
          interruption-level: "{{ 'critical' if trigger.event.data.type in ['alarm_crash', 'alarm_powerCut'] else 'time-sensitive' }}"
mode: queued
```

## Lock the motorbike when you get home

```yaml
alias: GeoRide – lock when parked at home
triggers:
  - trigger: state
    entity_id: device_tracker.cb_650_r_position
    to: home
    for: "00:05:00"
conditions:
  - condition: state
    entity_id: binary_sensor.cb_650_r_is_moving
    state: "off"
  - condition: state
    entity_id: switch.cb_650_r_lock
    state: "off"
actions:
  - action: switch.turn_on
    target:
      entity_id: switch.cb_650_r_lock
mode: single
```

## Motorbike battery low (GeoRide 3)

```yaml
alias: GeoRide – motorbike battery low
triggers:
  - trigger: numeric_state
    entity_id: sensor.cb_650_r_external_battery_voltage
    below: 12.2
    for: "01:00:00"
actions:
  - action: notify.mobile_app_my_phone
    data:
      message: >-
        Motorbike battery at {{ states('sensor.cb_650_r_external_battery_voltage') }} V:
        consider a battery charger.
mode: single
```

## Stolen or crashed

`is not stolen` / `is not crashed` binary sensors use the *problem* device class: **on = stolen / crashed**.

```yaml
alias: GeoRide – stolen or crashed
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.cb_650_r_is_not_stolen
      - binary_sensor.cb_650_r_is_not_crashed
    to: "on"
actions:
  - action: notify.mobile_app_my_phone
    data:
      title: GeoRide
      message: "{{ trigger.to_state.name }}: check your motorbike!"
      data:
        push:
          interruption-level: critical
mode: single
```

## Mileage-based maintenance reminder

```yaml
alias: GeoRide – oil change every 6,000 km
triggers:
  - trigger: template
    value_template: >-
      {{ states('sensor.cb_650_r_odometer_km') | int(0) // 6000 >
         states('input_number.moto_last_oil_change_km') | int(0) // 6000 }}
actions:
  - action: persistent_notification.create
    data:
      title: Motorbike maintenance
      message: "Oil change due ({{ states('sensor.cb_650_r_odometer_km') }} km)."
mode: single
```
