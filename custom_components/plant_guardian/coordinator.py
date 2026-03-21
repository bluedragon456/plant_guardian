from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
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
    CONF_FERTILIZING_INTERVAL_DAYS,
    CONF_IMAGE_URL,
    CONF_LIGHT_ENTITY,
    CONF_LIGHT_MIN,
    CONF_MOISTURE_ENTITY,
    CONF_MOISTURE_MIN,
    CONF_OPENPLANTBOOK_SYNC_CARE,
    CONF_OPENPLANTBOOK_SYNC_IMAGE,
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
    STATE_NEEDS_CARE,
    STATE_NEEDS_FERTILIZER,
    STATE_NEEDS_WATERING,
    STATE_UNKNOWN as PLANT_STATE_UNKNOWN,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)
from .openplantbook import OpenPlantbookClient
from .presentation import status_needs_care, status_tags

_LOGGER = logging.getLogger(__name__)


@dataclass
class PlantData:
    status: str
    problem: str
    needs_care: bool
    tags: list[str]
    moisture: float | None
    light: float | None
    temperature: float | None
    moisture_min: float
    light_min: float
    temp_min: float
    temp_max: float
    watering_interval_days: int
    fertilizing_interval_days: int
    watering_log_days_ago: int
    fertilizing_log_days_ago: int
    last_watered: str | None
    last_fertilized: str | None
    days_since_watered: int
    days_since_fertilized: int
    image: str | None
    image_source: str | None
    species: str | None
    care_summary: str
    care_source: str | None


class PlantGuardianCoordinator(DataUpdateCoordinator[PlantData]):
    """Coordinator for a single plant config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(hours=1),
        )
        self.entry = entry
        self._store = Store[dict[str, Any]](
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}_{entry.entry_id}",
        )
        self._openplantbook = OpenPlantbookClient(hass, entry)
        self._unsub: CALLBACK_TYPE | None = None
        self._last_watered: datetime | None = None
        self._last_fertilized: datetime | None = None
        self._watering_log_days_ago = 0
        self._fertilizing_log_days_ago = 0

    async def async_setup(self) -> None:
        stored = await self._store.async_load() or {}
        self._last_watered = _parse_datetime(stored.get("last_watered"))
        self._last_fertilized = _parse_datetime(stored.get("last_fertilized"))
        self._watering_log_days_ago = _clamp_days_ago(stored.get("watering_log_days_ago"))
        self._fertilizing_log_days_ago = _clamp_days_ago(stored.get("fertilizing_log_days_ago"))

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
        return await self._async_build_data()

    @callback
    def _handle_source_change(self, event) -> None:
        self.hass.async_create_task(self.async_refresh())

    async def async_mark_watered_now(self) -> None:
        await self.async_mark_watered()

    async def async_mark_fertilized_now(self) -> None:
        await self.async_mark_fertilized()

    async def async_mark_watered(self, occurred_on: date | None = None) -> None:
        self._last_watered = self._resolve_logged_at(occurred_on)
        await self._async_save_state()
        await self.async_refresh()

    async def async_mark_fertilized(self, occurred_on: date | None = None) -> None:
        self._last_fertilized = self._resolve_logged_at(occurred_on)
        await self._async_save_state()
        await self.async_refresh()

    async def async_mark_watered_selected_day(self) -> None:
        await self.async_mark_watered(dt_util.now().date() - timedelta(days=self._watering_log_days_ago))

    async def async_mark_fertilized_selected_day(self) -> None:
        await self.async_mark_fertilized(dt_util.now().date() - timedelta(days=self._fertilizing_log_days_ago))

    async def async_set_watering_log_days_ago(self, days_ago: float) -> None:
        self._watering_log_days_ago = _clamp_days_ago(days_ago)
        await self._async_save_state()
        await self.async_refresh()

    async def async_set_fertilizing_log_days_ago(self, days_ago: float) -> None:
        self._fertilizing_log_days_ago = _clamp_days_ago(days_ago)
        await self._async_save_state()
        await self.async_refresh()

    async def _async_save_state(self) -> None:
        await self._store.async_save(
            {
                "last_watered": self._last_watered.isoformat() if self._last_watered else None,
                "last_fertilized": self._last_fertilized.isoformat() if self._last_fertilized else None,
                "watering_log_days_ago": self._watering_log_days_ago,
                "fertilizing_log_days_ago": self._fertilizing_log_days_ago,
            }
        )

    async def _async_build_data(self) -> PlantData:
        openplantbook = await self._openplantbook.async_fetch_plant_details()

        moisture_entity = self._conf(CONF_MOISTURE_ENTITY)
        light_entity = self._conf(CONF_LIGHT_ENTITY)
        temp_entity = self._conf(CONF_TEMP_ENTITY)

        moisture = self._safe_float(moisture_entity)
        light = self._safe_float(light_entity)
        temp = self._safe_float(temp_entity)

        moisture_min, light_min, temp_min, temp_max, watering_interval_days, fertilizing_interval_days, care_source = (
            self._resolve_care_config(openplantbook)
        )

        days_since_watered = _days_since(self._last_watered)
        days_since_fertilized = _days_since(self._last_fertilized)

        configured_entities = [entity_id for entity_id in (moisture_entity, light_entity, temp_entity) if entity_id]

        status = STATE_HEALTHY
        problem = "none"

        if configured_entities and moisture is None and light is None and temp is None:
            status = PLANT_STATE_UNKNOWN
            problem = "sensors_unavailable"
        elif moisture is not None and moisture < moisture_min:
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
        else:
            needs_watering = days_since_watered >= watering_interval_days
            needs_fertilizer = days_since_fertilized >= fertilizing_interval_days

            if needs_watering and needs_fertilizer:
                status = STATE_NEEDS_CARE
                problem = STATE_NEEDS_CARE
            elif needs_watering:
                status = STATE_NEEDS_WATERING
                problem = STATE_NEEDS_WATERING
            elif needs_fertilizer:
                status = STATE_NEEDS_FERTILIZER
                problem = STATE_NEEDS_FERTILIZER

        image, image_source = self._resolve_image(openplantbook)
        tags = status_tags(status)
        needs_care = status_needs_care(status)
        species = self._conf(CONF_SPECIES) or (openplantbook.pid if openplantbook else None)

        care_summary = _build_care_summary(
            plant_name=self.entry.title or self._conf(CONF_PLANT_NAME),
            status=status,
            days_since_watered=days_since_watered,
            watering_interval_days=watering_interval_days,
            days_since_fertilized=days_since_fertilized,
            fertilizing_interval_days=fertilizing_interval_days,
        )

        return PlantData(
            status=status,
            problem=problem,
            needs_care=needs_care,
            tags=tags,
            moisture=moisture,
            light=light,
            temperature=temp,
            moisture_min=moisture_min,
            light_min=light_min,
            temp_min=temp_min,
            temp_max=temp_max,
            watering_interval_days=watering_interval_days,
            fertilizing_interval_days=fertilizing_interval_days,
            watering_log_days_ago=self._watering_log_days_ago,
            fertilizing_log_days_ago=self._fertilizing_log_days_ago,
            last_watered=self._last_watered.isoformat() if self._last_watered else None,
            last_fertilized=self._last_fertilized.isoformat() if self._last_fertilized else None,
            days_since_watered=days_since_watered,
            days_since_fertilized=days_since_fertilized,
            image=image,
            image_source=image_source,
            species=species,
            care_summary=care_summary,
            care_source=care_source,
        )

    def _resolve_image(self, openplantbook) -> tuple[str | None, str | None]:
        image_url = self._conf(CONF_IMAGE_URL)
        sync_image = bool(self._conf(CONF_OPENPLANTBOOK_SYNC_IMAGE))

        if image_url:
            return image_url, "user"

        if sync_image and openplantbook and openplantbook.image_url:
            return openplantbook.image_url, "openplantbook"

        return None, None

    def _resolve_care_config(self, openplantbook) -> tuple[float, float, float, float, int, int, str]:
        sync_care = bool(self._conf(CONF_OPENPLANTBOOK_SYNC_CARE))

        moisture_min = float(self._conf(CONF_MOISTURE_MIN))
        light_min = float(self._conf(CONF_LIGHT_MIN))
        temp_min = float(self._conf(CONF_TEMP_MIN))
        temp_max = float(self._conf(CONF_TEMP_MAX))
        watering_interval_days = int(self._conf(CONF_WATERING_INTERVAL_DAYS))
        fertilizing_interval_days = int(self._conf(CONF_FERTILIZING_INTERVAL_DAYS))

        has_openplantbook_care = openplantbook and any(
            value is not None
            for value in (
                openplantbook.moisture_min,
                openplantbook.light_min,
                openplantbook.temp_min,
                openplantbook.temp_max,
                openplantbook.watering_interval_days,
                openplantbook.fertilizing_interval_days,
            )
        )

        if sync_care and has_openplantbook_care:
            moisture_min = float(openplantbook.moisture_min or moisture_min)
            light_min = float(openplantbook.light_min or light_min)
            temp_min = float(openplantbook.temp_min or temp_min)
            temp_max = float(openplantbook.temp_max or temp_max)
            watering_interval_days = int(openplantbook.watering_interval_days or watering_interval_days)
            fertilizing_interval_days = int(
                openplantbook.fertilizing_interval_days or fertilizing_interval_days
            )
            return (
                moisture_min,
                light_min,
                temp_min,
                temp_max,
                watering_interval_days,
                fertilizing_interval_days,
                "openplantbook",
            )

        return (
            moisture_min,
            light_min,
            temp_min,
            temp_max,
            watering_interval_days,
            fertilizing_interval_days,
            "manual",
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

    def _resolve_logged_at(self, occurred_on: date | None) -> datetime:
        now = dt_util.now()
        if occurred_on is None:
            return now

        logged_at = datetime.combine(occurred_on, now.timetz())
        if logged_at.tzinfo is None:
            logged_at = logged_at.replace(tzinfo=now.tzinfo)

        if logged_at > now:
            raise ValueError("Logged care date cannot be in the future")

        return logged_at


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


def _days_since(value: datetime | None) -> int:
    if value is None:
        return 0
    now = dt_util.now()
    delta: timedelta = now - value
    return max(delta.days, 0)


def _build_care_summary(
    *,
    plant_name: str,
    status: str,
    days_since_watered: int,
    watering_interval_days: int,
    days_since_fertilized: int,
    fertilizing_interval_days: int,
) -> str:
    watered_text = f"watered {days_since_watered} day(s) ago"
    fertilized_text = f"fertilized {days_since_fertilized} day(s) ago"
    return (
        f"{plant_name} is {status}. {watered_text} "
        f"(target every {watering_interval_days} day(s)); {fertilized_text} "
        f"(target every {fertilizing_interval_days} day(s))."
    )


def _clamp_days_ago(value: Any) -> int:
    try:
        return max(0, min(int(float(value)), 365))
    except (TypeError, ValueError):
        return 0
