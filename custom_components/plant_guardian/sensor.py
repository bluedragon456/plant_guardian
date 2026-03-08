from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
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
    CONF_PLANT_NAME,
)
from .entity import PlantGuardianEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    plant_entry = entry
    async_add_entities(
        [
            PlantGuardianStatusSensor(plant_entry),
            PlantGuardianDaysSinceWateredSensor(plant_entry),
            PlantGuardianDaysSinceFertilizedSensor(plant_entry),
        ]
    )


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
