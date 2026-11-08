"""Sensors for GeoRide trackers and beacons."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfSpeed,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GeoRideConfigEntry
from .entity import GeoRideBeaconEntity, GeoRideTrackerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GeoRideConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = []
    for tracker_id, tracker in coordinator.trackers.items():
        entities += [
            GeoRideOdometerSensor(coordinator, tracker_id),
            GeoRideOdometerKmSensor(coordinator, tracker_id),
            GeoRideSpeedSensor(coordinator, tracker_id),
            GeoRideFixtimeSensor(coordinator, tracker_id),
        ]
        if tracker.version > 2:
            entities += [
                GeoRideInternalBatterySensor(coordinator, tracker_id),
                GeoRideExternalBatterySensor(coordinator, tracker_id),
            ]
    entities += [GeoRideBeaconBatterySensor(coordinator, beacon_id) for beacon_id in coordinator.beacons]
    async_add_entities(entities)


class GeoRideOdometerSensor(GeoRideTrackerEntity, SensorEntity):
    _unique_prefix = "odometer"
    _name_suffix = "odometer"
    _attr_icon = "mdi:counter"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfLength.METERS

    @property
    def native_value(self) -> int | None:
        return self.tracker.odometer


class GeoRideOdometerKmSensor(GeoRideTrackerEntity, SensorEntity):
    _unique_prefix = "odometer_km"
    _name_suffix = "odometer km"
    _attr_icon = "mdi:counter"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS

    @property
    def native_value(self) -> int | None:
        odometer = self.tracker.odometer
        return None if odometer is None else odometer // 1000


class GeoRideSpeedSensor(GeoRideTrackerEntity, SensorEntity):
    """Speed: the API returns knots, converted here to km/h."""

    _unique_prefix = "speed"
    _name_suffix = "speed"
    _attr_icon = "mdi:speedometer"
    _attr_device_class = SensorDeviceClass.SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR

    @property
    def native_value(self) -> float | None:
        return self.tracker.speed_kmh


class GeoRideFixtimeSensor(GeoRideTrackerEntity, SensorEntity):
    _unique_prefix = "fixtime"
    _name_suffix = "last fixed position"
    _attr_icon = "mdi:map-clock"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> datetime | None:
        return self.tracker.fixtime


class GeoRideInternalBatterySensor(GeoRideTrackerEntity, SensorEntity):
    _unique_prefix = "internal_battery_voltage"
    _name_suffix = "internal_battery_voltage"
    _attr_icon = "mdi:battery"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float | None:
        return self.tracker.internal_battery_voltage


class GeoRideExternalBatterySensor(GeoRideTrackerEntity, SensorEntity):
    _unique_prefix = "external_battery_voltage"
    _name_suffix = "external_battery_voltage"
    _attr_icon = "mdi:car-battery"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float | None:
        return self.tracker.external_battery_voltage


class GeoRideBeaconBatterySensor(GeoRideBeaconEntity, SensorEntity):
    """Beacon battery: 255 means 'unknown' and is reported as such."""

    _unique_prefix = "battery_percent"
    _name_suffix = "battery percent"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> int | None:
        return self.beacon.battery_level
