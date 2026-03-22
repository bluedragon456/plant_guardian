from __future__ import annotations

from datetime import datetime

from homeassistant.components.image import ImageEntity
from homeassistant.core import callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .__init__ import PlantGuardianConfigEntry
from .entity import PlantGuardianEntity


async def async_setup_entry(
    hass,
    entry: PlantGuardianConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([PlantGuardianImage(entry)])


class PlantGuardianImage(PlantGuardianEntity, ImageEntity):
    def __init__(self, entry: PlantGuardianConfigEntry) -> None:
        super().__init__(entry)
        self._attr_name = "Image"
        self._attr_unique_id = f"{entry.entry_id}_image"
        self._last_image_url: str | None = self.coordinator.data.image
        self._image_last_updated: datetime | None = (
            dt_util.utcnow() if self._last_image_url else None
        )

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data.image)

    @property
    def image_url(self) -> str | None:
        return self.coordinator.data.image

    @property
    def image_last_updated(self) -> datetime | None:
        return self._image_last_updated

    @callback
    def _handle_coordinator_update(self) -> None:
        image_url = self.coordinator.data.image
        if image_url != self._last_image_url:
            self._last_image_url = image_url
            self._image_last_updated = dt_util.utcnow() if image_url else None
        elif image_url and self._image_last_updated is None:
            self._image_last_updated = dt_util.utcnow()

        super()._handle_coordinator_update()
