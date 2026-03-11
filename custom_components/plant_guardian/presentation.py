from __future__ import annotations

from .const import (
    STATE_COLD,
    STATE_DRY,
    STATE_HEALTHY,
    STATE_HOT,
    STATE_LOW_LIGHT,
    STATE_NEEDS_CARE,
    STATE_NEEDS_FERTILIZER,
    STATE_NEEDS_WATERING,
    STATE_UNKNOWN,
)

CARE_STATES = {
    STATE_DRY,
    STATE_LOW_LIGHT,
    STATE_COLD,
    STATE_HOT,
    STATE_NEEDS_WATERING,
    STATE_NEEDS_FERTILIZER,
    STATE_NEEDS_CARE,
}

_STATUS_ICON_MAP = {
    STATE_HEALTHY: "mdi:sprout",
    STATE_DRY: "mdi:water-alert",
    STATE_LOW_LIGHT: "mdi:weather-sunny-alert",
    STATE_COLD: "mdi:snowflake",
    STATE_HOT: "mdi:thermometer-high",
    STATE_NEEDS_WATERING: "mdi:watering-can-outline",
    STATE_NEEDS_FERTILIZER: "mdi:leaf",
    STATE_NEEDS_CARE: "mdi:alert-circle-outline",
    STATE_UNKNOWN: "mdi:help-circle-outline",
}

_STATUS_LABEL_MAP = {
    STATE_HEALTHY: "healthy",
    STATE_DRY: "dry",
    STATE_LOW_LIGHT: "low light",
    STATE_COLD: "cold",
    STATE_HOT: "hot",
    STATE_NEEDS_WATERING: "needs watering",
    STATE_NEEDS_FERTILIZER: "needs fertilizer",
    STATE_NEEDS_CARE: "needs care",
    STATE_UNKNOWN: "unknown",
}


def status_icon(status: str) -> str:
    return _STATUS_ICON_MAP.get(status, "mdi:flower-outline")


def status_tags(status: str) -> list[str]:
    tags: list[str] = []

    if status in CARE_STATES:
        tags.append("needs care")

    label = _STATUS_LABEL_MAP.get(status)
    if label and label not in {"healthy", "unknown", "needs care"}:
        tags.append(label)

    return tags


def status_needs_care(status: str) -> bool:
    return status in CARE_STATES
