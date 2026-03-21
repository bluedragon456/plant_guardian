from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .__init__ import PlantGuardianConfigEntry
from .entity import PlantGuardianEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(
        [
            PlantGuardianWateringLogDaysAgoNumber(entry),
            PlantGuardianFertilizingLogDaysAgoNumber(entry),
        ]
    )


class _PlantGuardianLogDaysAgoNumber(PlantGuardianEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 365
    _attr_native_step = 1
    _attr_mode = "box"
    _attr_icon = "mdi:calendar-edit"

    @property
    def native_value(self) -> int:
        raise NotImplementedError


class PlantGuardianWateringLogDaysAgoNumber(_PlantGuardianLogDaysAgoNumber):
    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Watering Log Days Ago"
        self._attr_unique_id = f"{entry.entry_id}_watering_log_days_ago"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.watering_log_days_ago

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_watering_log_days_ago(value)


class PlantGuardianFertilizingLogDaysAgoNumber(_PlantGuardianLogDaysAgoNumber):
    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Fertilizing Log Days Ago"
        self._attr_unique_id = f"{entry.entry_id}_fertilizing_log_days_ago"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.fertilizing_log_days_ago

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_fertilizing_log_days_ago(value)
