from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .__init__ import PlantGuardianConfigEntry
from .const import STATE_HEALTHY, STATE_UNKNOWN
from .entity import PlantGuardianEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([PlantGuardianProblemBinarySensor(entry)])


class PlantGuardianProblemBinarySensor(PlantGuardianEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Problem"
        self._attr_unique_id = f"{entry.entry_id}_problem"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.status not in (STATE_HEALTHY, STATE_UNKNOWN)
