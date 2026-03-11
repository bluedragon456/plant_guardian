from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .__init__ import PlantGuardianConfigEntry
from .const import STATE_HEALTHY, STATE_UNKNOWN
from .entity import PlantGuardianEntity
from .presentation import status_icon


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(
        [
            PlantGuardianProblemBinarySensor(entry),
            PlantGuardianNeedsCareBinarySensor(entry),
        ]
    )


class PlantGuardianProblemBinarySensor(PlantGuardianEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Problem"
        self._attr_unique_id = f"{entry.entry_id}_problem"

    @property
    def icon(self) -> str:
        return status_icon(self.coordinator.data.status)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.status not in (STATE_HEALTHY, STATE_UNKNOWN)


class PlantGuardianNeedsCareBinarySensor(PlantGuardianEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:tag-outline"

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Needs Care"
        self._attr_unique_id = f"{entry.entry_id}_needs_care"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.needs_care
