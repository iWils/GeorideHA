"""Binary sensors for GeoRide trackers and beacons."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
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
    entities: list[BinarySensorEntity] = []
    for tracker_id in coordinator.trackers:
        entities += [
            cls(coordinator, tracker_id)
            for cls in (
                GeoRideStolenBinarySensor,
                GeoRideCrashedBinarySensor,
                GeoRideOwnerBinarySensor,
                GeoRideActiveSubscriptionBinarySensor,
                GeoRideNetworkBinarySensor,
                GeoRideMovingBinarySensor,
                GeoRideUpdateBinarySensor,
            )
        ]
    entities += [GeoRideBeaconUpdateBinarySensor(coordinator, beacon_id) for beacon_id in coordinator.beacons]
    async_add_entities(entities)


class GeoRideStolenBinarySensor(GeoRideTrackerEntity, BinarySensorEntity):
    """On = the motorbike is declared stolen."""

    _unique_prefix = "is_stolen"
    _name_suffix = "is not stolen"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool:
        return self.tracker.is_stolen


class GeoRideCrashedBinarySensor(GeoRideTrackerEntity, BinarySensorEntity):
    """On = a crash has been detected."""

    _unique_prefix = "is_crashed"
    _name_suffix = "is not crashed"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool:
        return self.tracker.is_crashed


class GeoRideOwnerBinarySensor(GeoRideTrackerEntity, BinarySensorEntity):
    _unique_prefix = "is_owner"
    _name_suffix = "is own tracker"

    @property
    def is_on(self) -> bool:
        return self.tracker.role == "owner"


class GeoRideActiveSubscriptionBinarySensor(GeoRideTrackerEntity, BinarySensorEntity):
    _unique_prefix = "is_active_subscription"
    _name_suffix = "has an active subscription"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        return self.tracker.has_active_subscription


class GeoRideNetworkBinarySensor(GeoRideTrackerEntity, BinarySensorEntity):
    _unique_prefix = "have_network"
    _name_suffix = "have network"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        return self.tracker.status == "online"


class GeoRideMovingBinarySensor(GeoRideTrackerEntity, BinarySensorEntity):
    _unique_prefix = "moving"
    _name_suffix = "is moving"
    _attr_device_class = BinarySensorDeviceClass.MOVING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        return self.tracker.moving


class GeoRideUpdateBinarySensor(GeoRideTrackerEntity, BinarySensorEntity):
    _unique_prefix = "update"
    _name_suffix = "have an update"
    _attr_device_class = BinarySensorDeviceClass.UPDATE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        return not self.tracker.is_up_to_date


class GeoRideBeaconUpdateBinarySensor(GeoRideBeaconEntity, BinarySensorEntity):
    _unique_prefix = "update"
    _name_suffix = "have an update"
    _attr_device_class = BinarySensorDeviceClass.UPDATE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        return not self.beacon.is_updated
