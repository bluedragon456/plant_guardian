from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_CARE_SUMMARY,
    ATTR_DAYS_SINCE_FERTILIZED,
    ATTR_DAYS_SINCE_WATERED,
    ATTR_IMAGE,
    ATTR_LAST_FERTILIZED,
    ATTR_LAST_WATERED,
    ATTR_PROBLEM,
    ATTR_SPECIES,
    CONF_FERTILIZING_INTERVAL_DAYS,
    CONF_IMAGE_URL,
    CONF_LIGHT_ENTITY,
    CONF_LIGHT_MIN,
    CONF_MOISTURE_ENTITY,
    CONF_MOISTURE_MIN,
    CONF_PLANT_NAME,
    CONF_SPECIES,
    CONF_TEMP_ENTITY,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_WATERING_INTERVAL_DAYS,
    DOMAIN,
    STATE_COLD,
    STATE_DRY,
    STATE_HEALTHY,
    STATE_HOT,
    STATE_LOW_LIGHT,
    STATE_NEEDS_FERTILIZER,
    STATE_NEEDS_WATERING,
    STATE_UNKNOWN as PLANT_STATE_UNKNOWN,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class PlantData:
    status: str
    problem: str
    moisture: float | None
    light: float | None
    temperature: float | None
    last_watered: str | None
    last_fertilized: str | None
    days_since_watered: int | None
    days_since_fertilized: int | None
    image: str | None
    species: str | None
    care_summary: str


class PlantGuardianCoordinator(DataUpdateCoordinator[PlantData]):
    """Coordinator for a single plant config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=None,
        )
        self.entry = entry
        self._store = Store[dict[str, Any]](
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}_{entry.entry_id}",
        )
        self._unsub: CALLBACK_TYPE | None = None
        self._last_watered: datetime | None = None
        self._last_fertilized: datetime | None = None

    async def async_setup(self) -> None:
        stored = await self._store.async_load() or {}
        self._last_watered = _parse_datetime(stored.get("last_watered"))
        self._last_fertilized = _parse_datetime(stored.get("last_fertilized"))

        watch_entities = [
            self.entry.options.get(CONF_MOISTURE_ENTITY, self.entry.data.get(CONF_MOISTURE_ENTITY)),
            self.entry.options.get(CONF_LIGHT_ENTITY, self.entry.data.get(CONF_LIGHT_ENTITY)),
            self.entry.options.get(CONF_TEMP_ENTITY, self.entry.data.get(CONF_TEMP_ENTITY)),
        ]
        watch_entities = [entity_id for entity_id in watch_entities if entity_id]

        if watch_entities:
            self._unsub = async_track_state_change_event(
                self.hass,
                watch_entities,
                self._handle_source_change,
            )

        await self.async_refresh()

    async def async_shutdown(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    async def _async_update_data(self) -> PlantData:
        return self._build_data()

    @callback
    def _handle_source_change(self, event) -> None:
        self.async_set_updated_data(self._build_data())

    async def async_mark_watered_now(self) -> None:
        self._last_watered = dt_util.now()
        await self._async_save_state()
        self.async_set_updated_data(self._build_data())

    async def async_mark_fertilized_now(self) -> None:
        self._last_fertilized = dt_util.now()
        await self._async_save_state()
        self.async_set_updated_data(self._build_data())

    async def _async_save_state(self) -> None:
        await self._store.async_save(
            {
                "last_watered": self._last_watered.isoformat() if self._last_watered else None,
                "last_fertilized": self._last_fertilized.isoformat() if self._last_fertilized else None,
            }
        )

    def _build_data(self) -> PlantData:
        moisture = self._safe_float(self._conf(CONF_MOISTURE_ENTITY))
        light = self._safe_float(self._conf(CONF_LIGHT_ENTITY))
        temp = self._safe_float(self._conf(CONF_TEMP_ENTITY))

        moisture_min = float(self._conf(CONF_MOISTURE_MIN))
        light_min = float(self._conf(CONF_LIGHT_MIN))
        temp_min = float(self._conf(CONF_TEMP_MIN))
        temp_max = float(self._conf(CONF_TEMP_MAX))
        watering_interval_days = int(self._conf(CONF_WATERING_INTERVAL_DAYS))
        fertilizing_interval_days = int(self._conf(CONF_FERTILIZING_INTERVAL_DAYS))

        days_since_watered = _days_since(self._last_watered)
        days_since_fertilized = _days_since(self._last_fertilized)

        status = PLANT_STATE_UNKNOWN
        problem = "moisture_unavailable"

        if moisture is not None:
            status = STATE_HEALTHY
            problem = "none"

            if moisture < moisture_min:
                status = STATE_DRY
                problem = STATE_DRY
            elif light is not None and light < light_min:
                status = STATE_LOW_LIGHT
                problem = STATE_LOW_LIGHT
            elif temp is not None and temp < temp_min:
                status = STATE_COLD
                problem = STATE_COLD
            elif temp is not None and temp > temp_max:
                status = STATE_HOT
                problem = STATE_HOT
            elif days_since_watered is not None and days_since_watered >= watering_interval_days:
                status = STATE_NEEDS_WATERING
                problem = STATE_NEEDS_WATERING
            elif (
                days_since_fertilized is not None
                and days_since_fertilized >= fertilizing_interval_days
            ):
                status = STATE_NEEDS_FERTILIZER
                problem = STATE_NEEDS_FERTILIZER

        care_summary = _build_care_summary(
            plant_name=self._conf(CONF_PLANT_NAME),
            status=status,
            days_since_watered=days_since_watered,
            watering_interval_days=watering_interval_days,
            days_since_fertilized=days_since_fertilized,
            fertilizing_interval_days=fertilizing_interval_days,
        )

        return PlantData(
            status=status,
            problem=problem,
            moisture=moisture,
            light=light,
            temperature=temp,
            last_watered=self._last_watered.isoformat() if self._last_watered else None,
            last_fertilized=self._last_fertilized.isoformat() if self._last_fertilized else None,
            days_since_watered=days_since_watered,
            days_since_fertilized=days_since_fertilized,
            image=self._conf(CONF_IMAGE_URL),
            species=self._conf(CONF_SPECIES),
            care_summary=care_summary,
        )

    def _safe_float(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None

        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None

    def _conf(self, key: str) -> Any:
        return self.entry.options.get(key, self.entry.data.get(key))


class PlantGuardianRuntimeData:
    """Runtime data for a config entry."""

    def __init__(self, coordinator: PlantGuardianCoordinator) -> None:
        self.coordinator = coordinator


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return dt_util.parse_datetime(value)
    except (TypeError, ValueError):
        return None


def _days_since(value: datetime | None) -> int | None:
    if value is None:
        return None
    now = dt_util.now()
    delta: timedelta = now - value
    return max(delta.days, 0)


def _build_care_summary(
    *,
    plant_name: str,
    status: str,
    days_since_watered: int | None,
    watering_interval_days: int,
    days_since_fertilized: int | None,
    fertilizing_interval_days: int,
) -> str:
    watered_text = (
        f"watered {days_since_watered} day(s) ago"
        if days_since_watered is not None
        else "watering not logged yet"
    )
    fertilized_text = (
        f"fertilized {days_since_fertilized} day(s) ago"
        if days_since_fertilized is not None
        else "fertilizer not logged yet"
    )
    return (
        f"{plant_name} is {status}. {watered_text} "
        f"(target every {watering_interval_days} day(s)); {fertilized_text} "
        f"(target every {fertilizing_interval_days} day(s))."
    )
