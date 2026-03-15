from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .__init__ import PlantGuardianConfigEntry
from .const import (
    ATTR_CARE_SOURCE,
    ATTR_CARE_SUMMARY,
    ATTR_DAYS_SINCE_FERTILIZED,
    ATTR_DAYS_SINCE_WATERED,
    ATTR_FERTILIZING_INTERVAL_DAYS,
    ATTR_IMAGE,
    ATTR_IMAGE_SOURCE,
    ATTR_LAST_FERTILIZED,
    ATTR_LAST_WATERED,
    ATTR_LIGHT_MIN,
    ATTR_MOISTURE_MIN,
    ATTR_NEEDS_CARE,
    ATTR_PROBLEM,
    ATTR_SPECIES,
    ATTR_TAGS,
    ATTR_TEMP_MAX,
    ATTR_TEMP_MIN,
    ATTR_WATERING_INTERVAL_DAYS,
    CONF_LIGHT_ENTITY,
    CONF_MOISTURE_ENTITY,
    CONF_TEMP_ENTITY,
)
from .entity import PlantGuardianEntity
from .presentation import status_icon


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PlantGuardianConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities: list[SensorEntity] = [
        PlantGuardianStatusSensor(entry),
        PlantGuardianDaysSinceWateredSensor(entry),
        PlantGuardianDaysSinceFertilizedSensor(entry),
    ]

    moisture_entity = entry.options.get(CONF_MOISTURE_ENTITY, entry.data.get(CONF_MOISTURE_ENTITY))
    light_entity = entry.options.get(CONF_LIGHT_ENTITY, entry.data.get(CONF_LIGHT_ENTITY))
    temp_entity = entry.options.get(CONF_TEMP_ENTITY, entry.data.get(CONF_TEMP_ENTITY))

    if moisture_entity:
        entities.append(PlantGuardianMoistureSensor(entry))

    if light_entity:
        entities.append(PlantGuardianLightSensor(entry))

    if temp_entity:
        entities.append(PlantGuardianTemperatureSensor(entry))

    async_add_entities(entities)


class PlantGuardianStatusSensor(PlantGuardianEntity, SensorEntity):
    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Status"
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def icon(self) -> str:
        return status_icon(self.coordinator.data.status)

    @property
    def entity_picture(self) -> str | None:
        return self.coordinator.data.image

    @property
    def native_value(self) -> str:
        return self.coordinator.data.status

    @property
    def extra_state_attributes(self) -> dict:
        return {
            ATTR_PROBLEM: self.coordinator.data.problem,
            ATTR_NEEDS_CARE: self.coordinator.data.needs_care,
            ATTR_TAGS: self.coordinator.data.tags,
            ATTR_LAST_WATERED: self.coordinator.data.last_watered,
            ATTR_LAST_FERTILIZED: self.coordinator.data.last_fertilized,
            ATTR_DAYS_SINCE_WATERED: self.coordinator.data.days_since_watered,
            ATTR_DAYS_SINCE_FERTILIZED: self.coordinator.data.days_since_fertilized,
            ATTR_IMAGE: self.coordinator.data.image,
            ATTR_IMAGE_SOURCE: self.coordinator.data.image_source,
            ATTR_SPECIES: self.coordinator.data.species,
            ATTR_CARE_SUMMARY: self.coordinator.data.care_summary,
            ATTR_CARE_SOURCE: self.coordinator.data.care_source,
            ATTR_MOISTURE_MIN: self.coordinator.data.moisture_min,
            ATTR_LIGHT_MIN: self.coordinator.data.light_min,
            ATTR_TEMP_MIN: self.coordinator.data.temp_min,
            ATTR_TEMP_MAX: self.coordinator.data.temp_max,
            ATTR_WATERING_INTERVAL_DAYS: self.coordinator.data.watering_interval_days,
            ATTR_FERTILIZING_INTERVAL_DAYS: self.coordinator.data.fertilizing_interval_days,
            "moisture": self.coordinator.data.moisture,
            "light": self.coordinator.data.light,
            "temperature": self.coordinator.data.temperature,
        }


class PlantGuardianDaysSinceWateredSensor(PlantGuardianEntity, SensorEntity):
    _attr_icon = "mdi:watering-can-outline"
    _attr_native_unit_of_measurement = "d"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Days Since Watered"
        self._attr_unique_id = f"{entry.entry_id}_days_since_watered"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.days_since_watered


class PlantGuardianDaysSinceFertilizedSensor(PlantGuardianEntity, SensorEntity):
    _attr_icon = "mdi:leaf"
    _attr_native_unit_of_measurement = "d"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Days Since Fertilized"
        self._attr_unique_id = f"{entry.entry_id}_days_since_fertilized"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.days_since_fertilized


class PlantGuardianMoistureSensor(PlantGuardianEntity, SensorEntity):
    _attr_icon = "mdi:water-percent"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Moisture"
        self._attr_unique_id = f"{entry.entry_id}_moisture"

    @property
    def native_value(self) -> float | int | None:
        return self.coordinator.data.moisture


class PlantGuardianLightSensor(PlantGuardianEntity, SensorEntity):
    _attr_icon = "mdi:white-balance-sunny"
    _attr_native_unit_of_measurement = "lx"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Light"
        self._attr_unique_id = f"{entry.entry_id}_light"

    @property
    def native_value(self) -> float | int | None:
        return self.coordinator.data.light


class PlantGuardianTemperatureSensor(PlantGuardianEntity, SensorEntity):
    _attr_icon = "mdi:thermometer"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Temperature"
        self._attr_unique_id = f"{entry.entry_id}_temperature"

    @property
    def native_unit_of_measurement(self) -> str | None:
        if self.hass:
            return self.hass.config.units.temperature_unit
        return UnitOfTemperature.FAHRENHEIT

    @property
    def native_value(self) -> float | int | None:
        return self.coordinator.data.temperature
