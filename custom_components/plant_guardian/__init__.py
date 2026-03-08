from __future__ import annotations

from typing import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_PLANT_NAME, DOMAIN, PLATFORMS
from .coordinator import PlantGuardianCoordinator, PlantGuardianRuntimeData


PlantGuardianConfigEntry: TypeAlias = ConfigEntry[PlantGuardianRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: PlantGuardianConfigEntry) -> bool:
    """Set up Plant Guardian from a config entry."""
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
