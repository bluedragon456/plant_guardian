from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .__init__ import PlantGuardianConfigEntry
from .const import (
    ATTR_CARE_SUMMARY,
    ATTR_DAYS_SINCE_FERTILIZED,
    ATTR_DAYS_SINCE_WATERED,
    ATTR_IMAGE,
    ATTR_LAST_FERTILIZED,
    ATTR_LAST_WATERED,
    ATTR_PROBLEM,
    ATTR_SPECIES,
)
from .entity import PlantGuardianEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    plant_entry = entry

    entities: list[SensorEntity] = [
        PlantGuardianStatusSensor(plant_entry),
        PlantGuardianDaysSinceWateredSensor(plant_entry),
        PlantGuardianDaysSinceFertilizedSensor(plant_entry),
    ]

    # Add mirrored plant sensors only if the linked source sensors exist
    if getattr(plant_entry.options, "get", None):
        moisture_entity = plant_entry.options.get("moisture_entity", plant_entry.data.get("moisture_entity"))
        light_entity = plant_entry.options.get("light_entity", plant_entry.data.get("light_entity"))
        temp_entity = plant_entry.options.get("temp_entity", plant_entry.data.get("temp_entity"))
    else:
        moisture_entity = plant_entry.data.get("moisture_entity")
        light_entity = plant_entry.data.get("light_entity")
        temp_entity = plant_entry.data.get("temp_entity")

    if moisture_entity:
        entities.append(PlantGuardianMoistureSensor(plant_entry))

    if light_entity:
        entities.append(PlantGuardianLightSensor(plant_entry))

    if temp_entity:
        entities.append(PlantGuardianTemperatureSensor(plant_entry))

    async_add_entities(entities)


class PlantGuardianStatusSensor(PlantGuardianEntity, SensorEntity):
    _attr_icon = "mdi:sprout"

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Status"
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.status

    @property
    def extra_state_attributes(self) -> dict:
        return {
            ATTR_PROBLEM: self.coordinator.data.problem,
            ATTR_LAST_WATERED: self.coordinator.data.last_watered,
            ATTR_LAST_FERTILIZED: self.coordinator.data.last_fertilized,
            ATTR_DAYS_SINCE_WATERED: self.coordinator.data.days_since_watered,
            ATTR_DAYS_SINCE_FERTILIZED: self.coordinator.data.days_since_fertilized,
            ATTR_IMAGE: self.coordinator.data.image,
            ATTR_SPECIES: self.coordinator.data.species,
            ATTR_CARE_SUMMARY: self.coordinator.data.care_summary,
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
    def native_value(self) -> int | None:
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
    def native_value(self) -> int | None:
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
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Temperature"
        self._attr_unique_id = f"{entry.entry_id}_temperature"

    @property
    def native_value(self) -> float | int | None:
        return self.coordinator.data.temperature
