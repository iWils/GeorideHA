"""Constants for the GeoRide integration."""

from homeassistant.const import Platform

DOMAIN = "georide"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_TOKEN = "token"

API_HOST = "https://api.georide.com"
SOCKET_HOST = "https://socket.georide.com"

PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SIREN,
]

# Polling interval of the REST API (the socket brings real-time updates in between)
MIN_UNTIL_REFRESH = 10

# The siren stops by itself on the tracker after ~30 s
SIREN_ACTIVATION_DELAY = 30

# GeoRide tokens last 30 days: renew them when less than 5 days remain
TOKEN_SAFE_DAY = 432000

# GeoRide API speeds are expressed in knots
KNOTS_TO_KMH = 1.852

# Value returned by beacons when the battery level is unknown
BEACON_BATTERY_UNKNOWN = 255

# Events fired on the Home Assistant bus (kept for backward compatibility)
EVENT_LOCK = f"{DOMAIN}_lock_event"
EVENT_DEVICE = f"{DOMAIN}_device_event"
EVENT_POSITION = f"{DOMAIN}_position_event"
EVENT_ALARM = f"{DOMAIN}_alarm_event"
EVENT_REFRESH = f"{DOMAIN}_refresh_tracker_event"

KNOWN_ALARMS = {
    "vibration",
    "exitZone",
    "crash",
    "crashParking",
    "deviceOffline",
    "deviceOnline",
    "powerCut",
    "powerUncut",
    "batteryWarning",
    "temperatureWarning",
    "magnetOn",
    "magnetOff",
    "sonorAlarmOn",
}
