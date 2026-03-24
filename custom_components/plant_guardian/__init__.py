from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

import voluptuous as vol

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, device_registry as dr, entity_registry as er
from homeassistant.util import slugify

from .const import (
    CONF_PLANT_NAME,
    DOMAIN,
    PLATFORMS,
    SERVICE_ATTR_OCCURRED_ON,
    SERVICE_MARK_FERTILIZED,
    SERVICE_MARK_WATERED,
)
from .coordinator import PlantGuardianCoordinator, PlantGuardianRuntimeData


PlantGuardianConfigEntry: TypeAlias = ConfigEntry[PlantGuardianRuntimeData]

_FRONTEND_PATH = Path(__file__).parent / "frontend"
_STRATEGY_URL = f"/api/{DOMAIN}/frontend"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(_STRATEGY_URL, str(_FRONTEND_PATH), cache_headers=False)]
    )
    _async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: PlantGuardianConfigEntry) -> bool:
    """Set up Plant Guardian from a config entry."""
    _async_cleanup_stale_image_entities(hass, entry, remove_missing_states=False)

    coordinator = PlantGuardianCoordinator(hass, entry)
    await coordinator.async_setup()
    entry.runtime_data = PlantGuardianRuntimeData(coordinator)

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Custom",
        model="Plant Guardian",
        name=entry.title or entry.data.get(CONF_PLANT_NAME, "Plant"),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_cleanup_stale_image_entities(hass, entry, remove_missing_states=True)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PlantGuardianConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.coordinator.async_shutdown()
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: PlantGuardianConfigEntry) -> None:
    """Reload when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


def _async_cleanup_stale_image_entities(
    hass: HomeAssistant,
    entry: PlantGuardianConfigEntry,
    *,
    remove_missing_states: bool,
) -> None:
    entity_registry = er.async_get(hass)
    expected_unique_id = f"{entry.entry_id}_image"
    expected_slug = slugify(entry.title or entry.data.get(CONF_PLANT_NAME, "plant"))
    expected_prefix = f"image.{expected_slug}_image"

    for entity_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity_entry.domain != "image":
            continue

        is_expected = entity_entry.unique_id == expected_unique_id
        has_expected_entity_id = entity_entry.entity_id.startswith(expected_prefix)
        is_provided = hass.states.get(entity_entry.entity_id) is not None

        if not is_expected or not has_expected_entity_id or (remove_missing_states and not is_provided):
            entity_registry.async_remove(entity_entry.entity_id)


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_MARK_WATERED):
        return

    service_schema = vol.Schema(
        {
            vol.Optional("entity_id"): cv.entity_ids,
            vol.Optional("device_id"): vol.Any(cv.string, [cv.string]),
            vol.Optional(SERVICE_ATTR_OCCURRED_ON): cv.date,
        }
    )

    async def async_handle_mark_watered(call: ServiceCall) -> None:
        entries = _resolve_target_entries(hass, call)
        if not entries:
            raise HomeAssistantError("Select at least one Plant Guardian device or entity")
        for entry in entries:
            try:
                await entry.runtime_data.coordinator.async_mark_watered(
                    call.data.get(SERVICE_ATTR_OCCURRED_ON)
                )
            except ValueError as err:
                raise HomeAssistantError(str(err)) from err

    async def async_handle_mark_fertilized(call: ServiceCall) -> None:
        entries = _resolve_target_entries(hass, call)
        if not entries:
            raise HomeAssistantError("Select at least one Plant Guardian device or entity")
        for entry in entries:
            try:
                await entry.runtime_data.coordinator.async_mark_fertilized(
                    call.data.get(SERVICE_ATTR_OCCURRED_ON)
                )
            except ValueError as err:
                raise HomeAssistantError(str(err)) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_MARK_WATERED,
        async_handle_mark_watered,
        schema=service_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_MARK_FERTILIZED,
        async_handle_mark_fertilized,
        schema=service_schema,
    )


def _resolve_target_entries(
    hass: HomeAssistant,
    call: ServiceCall,
) -> list[PlantGuardianConfigEntry]:
    entry_ids: set[str] = set()
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    entity_ids = call.data.get("entity_id", [])
    if isinstance(entity_ids, str):
        entity_ids = [entity_ids]

    for entity_id in entity_ids:
        entity_entry = entity_registry.async_get(entity_id)
        if entity_entry and entity_entry.config_entry_id:
            entry_ids.add(entity_entry.config_entry_id)

    device_ids = call.data.get("device_id", [])
    if isinstance(device_ids, str):
        device_ids = [device_ids]

    for device_id in device_ids:
        device_entry = device_registry.async_get(device_id)
        if not device_entry:
            continue
        for identifier_domain, identifier_value in device_entry.identifiers:
            if identifier_domain == DOMAIN:
                entry_ids.add(identifier_value)

    return [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.entry_id in entry_ids and entry.runtime_data is not None
    ]
