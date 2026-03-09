from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
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
    DEFAULT_FERTILIZING_INTERVAL_DAYS,
    DEFAULT_LIGHT_MIN,
    DEFAULT_MOISTURE_MIN,
    DEFAULT_TEMP_MAX,
    DEFAULT_TEMP_MIN,
    DEFAULT_WATERING_INTERVAL_DAYS,
    DOMAIN,
)


def _cleanup_optional_fields(user_input: dict) -> dict:
    cleaned = dict(user_input)

    for key in (
        CONF_MOISTURE_ENTITY,
        CONF_LIGHT_ENTITY,
        CONF_TEMP_ENTITY,
        CONF_SPECIES,
        CONF_IMAGE_URL,
    ):
        if not cleaned.get(key):
            cleaned.pop(key, None)

    return cleaned


def _add_optional_entity_selector(schema: dict, key: str, defaults: dict) -> None:
    if defaults.get(key):
        schema[
            vol.Optional(
                key,
                default=defaults[key],
            )
        ] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        )
    else:
        schema[vol.Optional(key)] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        )


def _build_schema(defaults: dict | None = None, *, include_name: bool = True) -> vol.Schema:
    defaults = defaults or {}
    schema: dict = {}

    if include_name:
        schema[
            vol.Required(
                CONF_PLANT_NAME,
                default=defaults.get(CONF_PLANT_NAME, ""),
            )
        ] = selector.TextSelector()

    schema[
        vol.Optional(
            CONF_SPECIES,
            default=defaults.get(CONF_SPECIES, ""),
        )
    ] = selector.TextSelector()

    schema[
        vol.Optional(
            CONF_IMAGE_URL,
            default=defaults.get(CONF_IMAGE_URL, ""),
        )
    ] = selector.TextSelector(
        selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
    )

    _add_optional_entity_selector(schema, CONF_MOISTURE_ENTITY, defaults)
    _add_optional_entity_selector(schema, CONF_LIGHT_ENTITY, defaults)
    _add_optional_entity_selector(schema, CONF_TEMP_ENTITY, defaults)

    schema[
        vol.Required(
            CONF_MOISTURE_MIN,
            default=defaults.get(CONF_MOISTURE_MIN, DEFAULT_MOISTURE_MIN),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=100,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )

    schema[
        vol.Required(
            CONF_LIGHT_MIN,
            default=defaults.get(CONF_LIGHT_MIN, DEFAULT_LIGHT_MIN),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=200000,
            step=10,
            mode=selector.NumberSelectorMode.BOX,
        )
    )

    schema[
        vol.Required(
            CONF_TEMP_MIN,
            default=defaults.get(CONF_TEMP_MIN, DEFAULT_TEMP_MIN),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=-50,
            max=150,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )

    schema[
        vol.Required(
            CONF_TEMP_MAX,
            default=defaults.get(CONF_TEMP_MAX, DEFAULT_TEMP_MAX),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=-50,
            max=150,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )

    schema[
        vol.Required(
            CONF_WATERING_INTERVAL_DAYS,
            default=defaults.get(
                CONF_WATERING_INTERVAL_DAYS,
                DEFAULT_WATERING_INTERVAL_DAYS,
            ),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=365,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )

    schema[
        vol.Required(
            CONF_FERTILIZING_INTERVAL_DAYS,
            default=defaults.get(
                CONF_FERTILIZING_INTERVAL_DAYS,
                DEFAULT_FERTILIZING_INTERVAL_DAYS,
            ),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=365,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )

    return vol.Schema(schema)


class PlantGuardianConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = dict(user_input)
            plant_name = user_input[CONF_PLANT_NAME].strip()

            if not plant_name:
                errors[CONF_PLANT_NAME] = "required"
            elif user_input[CONF_TEMP_MIN] > user_input[CONF_TEMP_MAX]:
                errors["base"] = "temp_range_invalid"
            else:
                user_input = _cleanup_optional_fields(user_input)
                await self.async_set_unique_id(plant_name.lower())
                self._abort_if_unique_id_configured()
                user_input[CONF_PLANT_NAME] = plant_name
                return self.async_create_entry(title=plant_name, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input, include_name=True),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return PlantGuardianOptionsFlow(config_entry)


class PlantGuardianOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = dict(user_input)

            if user_input[CONF_TEMP_MIN] > user_input[CONF_TEMP_MAX]:
                errors["base"] = "temp_range_invalid"
            else:
                user_input = _cleanup_optional_fields(user_input)
                return self.async_create_entry(title="", data=user_input)

        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(defaults, include_name=False),
            errors=errors,
        )
