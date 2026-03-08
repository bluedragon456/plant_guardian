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


def _build_schema(defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_PLANT_NAME,
                default=defaults.get(CONF_PLANT_NAME, ""),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_SPECIES,
                default=defaults.get(CONF_SPECIES, ""),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_IMAGE_URL,
                default=defaults.get(CONF_IMAGE_URL, ""),
            ): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
            ),
            vol.Required(
                CONF_MOISTURE_ENTITY,
                default=defaults.get(CONF_MOISTURE_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(
                CONF_LIGHT_ENTITY,
                default=defaults.get(CONF_LIGHT_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(
                CONF_TEMP_ENTITY,
                default=defaults.get(CONF_TEMP_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(
                CONF_MOISTURE_MIN,
                default=defaults.get(CONF_MOISTURE_MIN, DEFAULT_MOISTURE_MIN),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_LIGHT_MIN,
                default=defaults.get(CONF_LIGHT_MIN, DEFAULT_LIGHT_MIN),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=200000, step=10, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_TEMP_MIN,
                default=defaults.get(CONF_TEMP_MIN, DEFAULT_TEMP_MIN),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-50, max=150, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_TEMP_MAX,
                default=defaults.get(CONF_TEMP_MAX, DEFAULT_TEMP_MAX),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-50, max=150, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_WATERING_INTERVAL_DAYS,
                default=defaults.get(
                    CONF_WATERING_INTERVAL_DAYS,
                    DEFAULT_WATERING_INTERVAL_DAYS,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=365, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_FERTILIZING_INTERVAL_DAYS,
                default=defaults.get(
                    CONF_FERTILIZING_INTERVAL_DAYS,
                    DEFAULT_FERTILIZING_INTERVAL_DAYS,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=365, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
        }
    )


class PlantGuardianConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            plant_name = user_input[CONF_PLANT_NAME].strip()
            if not plant_name:
                errors[CONF_PLANT_NAME] = "required"
            elif user_input[CONF_TEMP_MIN] > user_input[CONF_TEMP_MAX]:
                errors["base"] = "temp_range_invalid"
            else:
                await self.async_set_unique_id(plant_name.lower())
                self._abort_if_unique_id_configured()
                user_input[CONF_PLANT_NAME] = plant_name
                return self.async_create_entry(title=plant_name, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input),
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
            if user_input[CONF_TEMP_MIN] > user_input[CONF_TEMP_MAX]:
                errors["base"] = "temp_range_invalid"
            else:
                return self.async_create_entry(title="", data=user_input)

        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(defaults),
            errors=errors,
        )
