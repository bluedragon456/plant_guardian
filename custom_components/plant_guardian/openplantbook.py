from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_OPENPLANTBOOK_ENABLED, CONF_OPENPLANTBOOK_PID

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class OpenPlantbookPlantDetails:
    pid: str
    image_url: str | None = None
    moisture_min: float | None = None
    light_min: float | None = None
    temp_min: float | None = None
    temp_max: float | None = None
    watering_interval_days: int | None = None
    fertilizing_interval_days: int | None = None


class OpenPlantbookClient:
    """Small integration point for future OpenPlantbook API support."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

    async def async_fetch_plant_details(self) -> OpenPlantbookPlantDetails | None:
        enabled = bool(
            self.entry.options.get(
                CONF_OPENPLANTBOOK_ENABLED,
                self.entry.data.get(CONF_OPENPLANTBOOK_ENABLED, False),
            )
        )
        pid = self.entry.options.get(
            CONF_OPENPLANTBOOK_PID,
            self.entry.data.get(CONF_OPENPLANTBOOK_PID),
        )

        if not enabled or not pid:
            return None

        _LOGGER.debug(
            "OpenPlantbook is enabled for %s (pid=%s), but API fetching is not wired yet.",
            self.entry.title,
            pid,
        )
        return OpenPlantbookPlantDetails(pid=pid)
