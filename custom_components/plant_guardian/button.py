from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
            PlantGuardianWateredNowButton(entry),
            PlantGuardianFertilizedNowButton(entry),
        ]
    )


class PlantGuardianWateredNowButton(PlantGuardianEntity, ButtonEntity):
    _attr_icon = "mdi:watering-can"

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Watered Now"
        self._attr_unique_id = f"{entry.entry_id}_watered_now"

    async def async_press(self) -> None:
        await self.coordinator.async_mark_watered_now()


class PlantGuardianFertilizedNowButton(PlantGuardianEntity, ButtonEntity):
    _attr_icon = "mdi:sprout-outline"

    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Fertilized Now"
        self._attr_unique_id = f"{entry.entry_id}_fertilized_now"

    async def async_press(self) -> None:
        await self.coordinator.async_mark_fertilized_now()
