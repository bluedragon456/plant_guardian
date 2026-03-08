from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .__init__ import PlantGuardianConfigEntry
from .const import CONF_PLANT_NAME, DOMAIN
from .coordinator import PlantGuardianCoordinator


class PlantGuardianEntity(CoordinatorEntity[PlantGuardianCoordinator]):
    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry.runtime_data.coordinator)
        self.entry = entry
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.entry.title or self.entry.data.get(CONF_PLANT_NAME, "Plant"),
            manufacturer="Custom",
            model="Plant Guardian",
        )
