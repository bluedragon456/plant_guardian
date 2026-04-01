from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CACHE_IMAGES_LOCALLY,
    CONF_FERTILIZING_INTERVAL_DAYS,
    CONF_IMAGE_URL,
    CONF_LIGHT_ENTITY,
    CONF_LIGHT_MIN,
    CONF_MOISTURE_ENTITY,
    CONF_MOISTURE_MIN,
    CONF_OPENPLANTBOOK_ENABLED,
    CONF_OPENPLANTBOOK_PID,
    CONF_OPENPLANTBOOK_SYNC_CARE,
    CONF_OPENPLANTBOOK_SYNC_IMAGE,
    CONF_PLANT_NAME,
    CONF_SPECIES,
    CONF_TEMP_ENTITY,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_WATERING_INTERVAL_DAYS,
    DEFAULT_FERTILIZING_INTERVAL_DAYS,
    DEFAULT_LIGHT_MIN,
    DEFAULT_MOISTURE_MIN,
    DEFAULT_TEMP_MAX,
    DEFAULT_TEMP_MIN,
    DEFAULT_WATERING_INTERVAL_DAYS,
    DOMAIN,
)
from .openplantbook import OpenPlantbookSearchMatch, async_search_species

CONF_USE_OPENPLANTBOOK_LOOKUP = "use_openplantbook_lookup"
CONF_OPENPLANTBOOK_QUERY = "openplantbook_query"
CONF_OPENPLANTBOOK_MATCH = "openplantbook_match"


def _cleanup_optional_fields(user_input: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(user_input)

    for key in (
        CONF_MOISTURE_ENTITY,
        CONF_LIGHT_ENTITY,
        CONF_TEMP_ENTITY,
        CONF_SPECIES,
        CONF_IMAGE_URL,
        CONF_OPENPLANTBOOK_PID,
    ):
        if not cleaned.get(key):
            cleaned.pop(key, None)

    if not cleaned.get(CONF_OPENPLANTBOOK_ENABLED):
        cleaned.pop(CONF_OPENPLANTBOOK_ENABLED, None)
        cleaned.pop(CONF_OPENPLANTBOOK_PID, None)
        cleaned.pop(CONF_OPENPLANTBOOK_SYNC_IMAGE, None)
        cleaned.pop(CONF_OPENPLANTBOOK_SYNC_CARE, None)

    return cleaned


def _normalize_defaults(defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(defaults or {})
    return {
        CONF_PLANT_NAME: str(data.get(CONF_PLANT_NAME) or ""),
        CONF_SPECIES: str(data.get(CONF_SPECIES) or ""),
        CONF_IMAGE_URL: str(data.get(CONF_IMAGE_URL) or ""),
        CONF_CACHE_IMAGES_LOCALLY: bool(data.get(CONF_CACHE_IMAGES_LOCALLY, True)),
        CONF_OPENPLANTBOOK_ENABLED: bool(data.get(CONF_OPENPLANTBOOK_ENABLED, False)),
        CONF_OPENPLANTBOOK_PID: str(data.get(CONF_OPENPLANTBOOK_PID) or ""),
        CONF_OPENPLANTBOOK_SYNC_IMAGE: bool(data.get(CONF_OPENPLANTBOOK_SYNC_IMAGE, True)),
        CONF_OPENPLANTBOOK_SYNC_CARE: bool(data.get(CONF_OPENPLANTBOOK_SYNC_CARE, False)),
        CONF_MOISTURE_ENTITY: data.get(CONF_MOISTURE_ENTITY),
        CONF_LIGHT_ENTITY: data.get(CONF_LIGHT_ENTITY),
        CONF_TEMP_ENTITY: data.get(CONF_TEMP_ENTITY),
        CONF_MOISTURE_MIN: float(data.get(CONF_MOISTURE_MIN, DEFAULT_MOISTURE_MIN)),
        CONF_LIGHT_MIN: float(data.get(CONF_LIGHT_MIN, DEFAULT_LIGHT_MIN)),
        CONF_TEMP_MIN: float(data.get(CONF_TEMP_MIN, DEFAULT_TEMP_MIN)),
        CONF_TEMP_MAX: float(data.get(CONF_TEMP_MAX, DEFAULT_TEMP_MAX)),
        CONF_WATERING_INTERVAL_DAYS: int(
            data.get(CONF_WATERING_INTERVAL_DAYS, DEFAULT_WATERING_INTERVAL_DAYS)
        ),
        CONF_FERTILIZING_INTERVAL_DAYS: int(
            data.get(CONF_FERTILIZING_INTERVAL_DAYS, DEFAULT_FERTILIZING_INTERVAL_DAYS)
        ),
    }


def _add_optional_entity_selector(schema: dict, key: str, defaults: dict[str, Any]) -> None:
    default_value = defaults.get(key)
    if default_value:
        schema[vol.Optional(key, default=default_value)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        )
    else:
        schema[vol.Optional(key)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        )


def _build_user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = dict(defaults or {})
    return vol.Schema(
        {
            vol.Required(CONF_PLANT_NAME, default=str(defaults.get(CONF_PLANT_NAME) or "")): selector.TextSelector(),
            vol.Required(
                CONF_USE_OPENPLANTBOOK_LOOKUP,
                default=bool(defaults.get(CONF_USE_OPENPLANTBOOK_LOOKUP, True)),
            ): selector.BooleanSelector(),
        }
    )


def _build_lookup_schema(default_query: str) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_OPENPLANTBOOK_QUERY, default=default_query): selector.TextSelector(),
        }
    )


def _build_match_schema(
    matches: list[OpenPlantbookSearchMatch],
    selected_pid: str | None = None,
) -> vol.Schema:
    options = [
        {
            "value": match.pid,
            "label": f"{match.display_name} ({match.pid})",
        }
        for match in matches
    ]

    return vol.Schema(
        {
            vol.Required(
                CONF_OPENPLANTBOOK_MATCH,
                default=selected_pid or matches[0].pid,
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


def _build_details_schema(defaults: dict[str, Any] | None = None, *, include_name: bool = True) -> vol.Schema:
    defaults = _normalize_defaults(defaults)
    schema: dict = {}

    if include_name:
        schema[vol.Required(CONF_PLANT_NAME, default=defaults[CONF_PLANT_NAME])] = selector.TextSelector()

    schema[vol.Optional(CONF_SPECIES, default=defaults[CONF_SPECIES])] = selector.TextSelector()
    schema[vol.Optional(CONF_IMAGE_URL, default=defaults[CONF_IMAGE_URL])] = selector.TextSelector()
    schema[vol.Optional(CONF_CACHE_IMAGES_LOCALLY, default=defaults[CONF_CACHE_IMAGES_LOCALLY])] = selector.BooleanSelector()
    schema[vol.Optional(CONF_OPENPLANTBOOK_ENABLED, default=defaults[CONF_OPENPLANTBOOK_ENABLED])] = selector.BooleanSelector()
    schema[vol.Optional(CONF_OPENPLANTBOOK_PID, default=defaults[CONF_OPENPLANTBOOK_PID])] = selector.TextSelector()
    schema[vol.Optional(CONF_OPENPLANTBOOK_SYNC_IMAGE, default=defaults[CONF_OPENPLANTBOOK_SYNC_IMAGE])] = selector.BooleanSelector()
    schema[vol.Optional(CONF_OPENPLANTBOOK_SYNC_CARE, default=defaults[CONF_OPENPLANTBOOK_SYNC_CARE])] = selector.BooleanSelector()

    _add_optional_entity_selector(schema, CONF_MOISTURE_ENTITY, defaults)
    _add_optional_entity_selector(schema, CONF_LIGHT_ENTITY, defaults)
    _add_optional_entity_selector(schema, CONF_TEMP_ENTITY, defaults)

    schema[vol.Required(CONF_MOISTURE_MIN, default=defaults[CONF_MOISTURE_MIN])] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
    )
    schema[vol.Required(CONF_LIGHT_MIN, default=defaults[CONF_LIGHT_MIN])] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=0, max=200000, step=10, mode=selector.NumberSelectorMode.BOX)
    )
    schema[vol.Required(CONF_TEMP_MIN, default=defaults[CONF_TEMP_MIN])] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=-50, max=150, step=1, mode=selector.NumberSelectorMode.BOX)
    )
    schema[vol.Required(CONF_TEMP_MAX, default=defaults[CONF_TEMP_MAX])] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=-50, max=150, step=1, mode=selector.NumberSelectorMode.BOX)
    )
    schema[
        vol.Required(
            CONF_WATERING_INTERVAL_DAYS,
            default=defaults[CONF_WATERING_INTERVAL_DAYS],
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=1, max=365, step=1, mode=selector.NumberSelectorMode.BOX)
    )
    schema[
        vol.Required(
            CONF_FERTILIZING_INTERVAL_DAYS,
            default=defaults[CONF_FERTILIZING_INTERVAL_DAYS],
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(min=1, max=365, step=1, mode=selector.NumberSelectorMode.BOX)
    )

    return vol.Schema(schema)


class PlantGuardianConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._config_data: dict[str, Any] = {}
        self._openplantbook_matches: list[OpenPlantbookSearchMatch] = []
        self._openplantbook_query = ""

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return PlantGuardianOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            plant_name = str(user_input[CONF_PLANT_NAME]).strip()
            use_openplantbook_lookup = bool(user_input[CONF_USE_OPENPLANTBOOK_LOOKUP])

            if not plant_name:
                errors[CONF_PLANT_NAME] = "required"
            elif use_openplantbook_lookup and not self.hass.services.has_service("openplantbook", "search"):
                errors["base"] = "openplantbook_unavailable"
            else:
                await self.async_set_unique_id(plant_name.lower())
                self._abort_if_unique_id_configured()
                self._config_data = _normalize_defaults({CONF_PLANT_NAME: plant_name})

                if use_openplantbook_lookup:
                    self._config_data.update(
                        {
                            CONF_OPENPLANTBOOK_ENABLED: True,
                            CONF_OPENPLANTBOOK_SYNC_IMAGE: True,
                            CONF_OPENPLANTBOOK_SYNC_CARE: True,
                        }
                    )
                    return await self.async_step_openplantbook_lookup()

                return await self.async_step_details()

        return self.async_show_form(
            step_id="user",
            data_schema=_build_user_schema(user_input),
            errors=errors,
        )

    async def async_step_openplantbook_lookup(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        default_query = self._openplantbook_query or self._config_data.get(CONF_PLANT_NAME, "")

        if user_input is not None:
            query = str(user_input[CONF_OPENPLANTBOOK_QUERY]).strip()
            if not query:
                errors[CONF_OPENPLANTBOOK_QUERY] = "required"
            else:
                self._openplantbook_query = query
                self._openplantbook_matches = await async_search_species(self.hass, query)
                if self._openplantbook_matches:
                    return await self.async_step_openplantbook_match()
                errors["base"] = "openplantbook_no_matches"

        return self.async_show_form(
            step_id="openplantbook_lookup",
            data_schema=_build_lookup_schema(default_query),
            errors=errors,
        )

    async def async_step_openplantbook_match(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if not self._openplantbook_matches:
            return await self.async_step_openplantbook_lookup()

        if user_input is not None:
            selected_pid = str(user_input[CONF_OPENPLANTBOOK_MATCH])
            match = next(
                (candidate for candidate in self._openplantbook_matches if candidate.pid == selected_pid),
                None,
            )
            if match is None:
                errors["base"] = "openplantbook_match_invalid"
            else:
                self._config_data.update(
                    {
                        CONF_SPECIES: match.display_name,
                        CONF_OPENPLANTBOOK_PID: match.pid,
                        CONF_OPENPLANTBOOK_ENABLED: True,
                        CONF_OPENPLANTBOOK_SYNC_IMAGE: True,
                        CONF_OPENPLANTBOOK_SYNC_CARE: True,
                    }
                )
                return await self.async_step_details()

        return self.async_show_form(
            step_id="openplantbook_match",
            data_schema=_build_match_schema(
                self._openplantbook_matches,
                user_input.get(CONF_OPENPLANTBOOK_MATCH) if user_input else None,
            ),
            errors=errors,
        )

    async def async_step_details(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = dict(user_input)
            if user_input[CONF_TEMP_MIN] > user_input[CONF_TEMP_MAX]:
                errors["base"] = "temp_range_invalid"
            else:
                data = _cleanup_optional_fields({**self._config_data, **user_input})
                plant_name = str(self._config_data[CONF_PLANT_NAME]).strip()
                data[CONF_PLANT_NAME] = plant_name
                return self.async_create_entry(title=plant_name, data=data)

        defaults = _normalize_defaults(self._config_data | (user_input or {}))
        return self.async_show_form(
            step_id="details",
            data_schema=_build_details_schema(defaults, include_name=False),
            errors=errors,
        )


class PlantGuardianOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = dict(user_input)

            if user_input[CONF_TEMP_MIN] > user_input[CONF_TEMP_MAX]:
                errors["base"] = "temp_range_invalid"
            else:
                user_input = _cleanup_optional_fields(user_input)
                return self.async_create_entry(title="", data=user_input)

        defaults = _normalize_defaults({**self._config_entry.data, **self._config_entry.options})
        return self.async_show_form(
            step_id="init",
            data_schema=_build_details_schema(defaults, include_name=False),
            errors=errors,
        )
