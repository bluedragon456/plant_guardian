from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    CONF_OPENPLANTBOOK_ENABLED,
    CONF_OPENPLANTBOOK_PID,
    CONF_PLANT_NAME,
    CONF_SPECIES,
)

_LOGGER = logging.getLogger(__name__)

OPENPLANTBOOK_DOMAIN = "openplantbook"
SERVICE_GET = "get"
SERVICE_SEARCH = "search"
SEARCH_RESULT_ENTITY_ID = "openplantbook.search_result"
CACHE_TTL = timedelta(hours=24)


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
    """Resolve plant details through Home Assistant's OpenPlantbook services."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._cache_key: tuple[bool, str | None, str | None, str | None] | None = None
        self._cache_expires_at = None
        self._cached_details: OpenPlantbookPlantDetails | None = None

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
        species = self.entry.options.get(
            CONF_SPECIES,
            self.entry.data.get(CONF_SPECIES),
        )
        plant_name = self.entry.title or self.entry.data.get(CONF_PLANT_NAME)

        if not enabled:
            return None

        cache_key = (
            enabled,
            _clean_text(pid),
            _clean_text(species),
            _clean_text(plant_name),
        )
        if (
            self._cache_key == cache_key
            and self._cache_expires_at is not None
            and dt_util.utcnow() < self._cache_expires_at
        ):
            return self._cached_details

        details = await self._async_fetch_uncached(
            pid=pid,
            species=species,
            plant_name=plant_name,
        )
        self._cache_key = cache_key
        self._cache_expires_at = dt_util.utcnow() + CACHE_TTL
        self._cached_details = details
        return details

    async def _async_fetch_uncached(
        self,
        *,
        pid: str | None,
        species: str | None,
        plant_name: str | None,
    ) -> OpenPlantbookPlantDetails | None:
        query = _clean_text(pid) or _clean_text(species) or _clean_text(plant_name)
        if not query:
            return None

        if not self.hass.services.has_service(OPENPLANTBOOK_DOMAIN, SERVICE_GET):
            _LOGGER.debug(
                "OpenPlantbook sync is enabled for %s, but the OpenPlantbook integration is not available.",
                self.entry.title,
            )
            return OpenPlantbookPlantDetails(pid=query) if pid else None

        resolved_pid = _clean_text(pid)
        if not resolved_pid:
            resolved_pid = await self._async_resolve_pid(query)
            if not resolved_pid:
                _LOGGER.debug("No OpenPlantbook match found for %s", query)
                return None

        state = await self._async_get_species_state(resolved_pid)
        if state is None:
            return OpenPlantbookPlantDetails(pid=resolved_pid)

        attrs = state.attributes
        return OpenPlantbookPlantDetails(
            pid=resolved_pid,
            image_url=_clean_text(attrs.get("image_url")),
            moisture_min=_coerce_float(
                attrs.get("min_soil_moist"),
                attrs.get("moisture_min"),
            ),
            light_min=_coerce_float(
                attrs.get("min_light_lux"),
                attrs.get("min_light"),
                attrs.get("light_min"),
            ),
            temp_min=_coerce_float(attrs.get("min_temp"), attrs.get("temp_min")),
            temp_max=_coerce_float(attrs.get("max_temp"), attrs.get("temp_max")),
            watering_interval_days=_coerce_int(
                attrs.get("watering_interval_days"),
                attrs.get("watering_days"),
            ),
            fertilizing_interval_days=_coerce_int(
                attrs.get("fertilizing_interval_days"),
                attrs.get("fertilizing_days"),
            ),
        )

    async def _async_resolve_pid(self, query: str) -> str | None:
        if not self.hass.services.has_service(OPENPLANTBOOK_DOMAIN, SERVICE_SEARCH):
            return None

        await self.hass.services.async_call(
            OPENPLANTBOOK_DOMAIN,
            SERVICE_SEARCH,
            {"alias": query},
            blocking=True,
        )

        search_result = self.hass.states.get(SEARCH_RESULT_ENTITY_ID)
        if search_result is None:
            return None

        attrs = dict(search_result.attributes)
        if not attrs:
            return None

        normalized_query = query.casefold()

        for candidate_pid, candidate_name in attrs.items():
            if str(candidate_pid).casefold() == normalized_query:
                return str(candidate_pid)
            if str(candidate_name).casefold() == normalized_query:
                return str(candidate_pid)

        for candidate_pid, candidate_name in attrs.items():
            if normalized_query in str(candidate_pid).casefold():
                return str(candidate_pid)
            if normalized_query in str(candidate_name).casefold():
                return str(candidate_pid)

        return next(iter(attrs), None)

    async def _async_get_species_state(self, pid: str):
        entity_id = f"{OPENPLANTBOOK_DOMAIN}.{slugify(pid)}"
        existing_state = self.hass.states.get(entity_id)
        if existing_state is not None:
            return existing_state

        await self.hass.services.async_call(
            OPENPLANTBOOK_DOMAIN,
            SERVICE_GET,
            {"species": pid},
            blocking=True,
        )
        return self.hass.states.get(entity_id)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_float(*values: Any) -> float | None:
    for value in values:
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _coerce_int(*values: Any) -> int | None:
    for value in values:
        if value in (None, ""):
            continue
        try:
            return int(float(value))
        except (TypeError, ValueError):
            continue
    return None
