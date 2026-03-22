from homeassistant.const import Platform

DOMAIN = "plant_guardian"
SERVICE_MARK_WATERED = "mark_watered"
SERVICE_MARK_FERTILIZED = "mark_fertilized"
SERVICE_ATTR_OCCURRED_ON = "occurred_on"
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.IMAGE,
]

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}_state"

CONF_PLANT_NAME = "plant_name"
CONF_SPECIES = "species"
CONF_IMAGE_URL = "image_url"
CONF_MOISTURE_ENTITY = "moisture_entity"
CONF_LIGHT_ENTITY = "light_entity"
CONF_TEMP_ENTITY = "temp_entity"
CONF_MOISTURE_MIN = "moisture_min"
CONF_LIGHT_MIN = "light_min"
CONF_TEMP_MIN = "temp_min"
CONF_TEMP_MAX = "temp_max"
CONF_WATERING_INTERVAL_DAYS = "watering_interval_days"
CONF_FERTILIZING_INTERVAL_DAYS = "fertilizing_interval_days"
CONF_OPENPLANTBOOK_ENABLED = "openplantbook_enabled"
CONF_OPENPLANTBOOK_PID = "openplantbook_pid"
CONF_OPENPLANTBOOK_SYNC_IMAGE = "openplantbook_sync_image"
CONF_OPENPLANTBOOK_SYNC_CARE = "openplantbook_sync_care"

DEFAULT_MOISTURE_MIN = 25.0
DEFAULT_LIGHT_MIN = 300.0
DEFAULT_TEMP_MIN = 60.0
DEFAULT_TEMP_MAX = 85.0
DEFAULT_WATERING_INTERVAL_DAYS = 7
DEFAULT_FERTILIZING_INTERVAL_DAYS = 30

ATTR_LAST_WATERED = "last_watered"
ATTR_LAST_FERTILIZED = "last_fertilized"
ATTR_DAYS_SINCE_WATERED = "days_since_watered"
ATTR_DAYS_SINCE_FERTILIZED = "days_since_fertilized"
ATTR_CARE_SUMMARY = "care_summary"
ATTR_PROBLEM = "problem"
ATTR_IMAGE = "image"
ATTR_SPECIES = "species"
ATTR_TAGS = "tags"
ATTR_NEEDS_CARE = "needs_care"
ATTR_IMAGE_SOURCE = "image_source"
ATTR_CARE_SOURCE = "care_source"
ATTR_MOISTURE_MIN = "moisture_min"
ATTR_LIGHT_MIN = "light_min"
ATTR_TEMP_MIN = "temp_min"
ATTR_TEMP_MAX = "temp_max"
ATTR_WATERING_INTERVAL_DAYS = "watering_interval_days"
ATTR_FERTILIZING_INTERVAL_DAYS = "fertilizing_interval_days"
ATTR_WATERING_LOG_DAYS_AGO = "watering_log_days_ago"
ATTR_FERTILIZING_LOG_DAYS_AGO = "fertilizing_log_days_ago"

STATE_HEALTHY = "healthy"
STATE_DRY = "dry"
STATE_LOW_LIGHT = "low_light"
STATE_COLD = "cold"
STATE_HOT = "hot"
STATE_NEEDS_WATERING = "needs_watering"
STATE_NEEDS_FERTILIZER = "needs_fertilizer"
STATE_NEEDS_CARE = "needs_care"
STATE_UNKNOWN = "unknown"
