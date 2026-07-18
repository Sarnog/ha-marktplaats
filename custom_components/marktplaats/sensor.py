"""Sensor-platform voor de Marktplaats-integratie."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MarktplaatsConfigEntry, MarktplaatsCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MarktplaatsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([MarktplaatsListingsSensor(coordinator, entry)])


class MarktplaatsListingsSensor(CoordinatorEntity[MarktplaatsCoordinator], SensorEntity):
    """Aantal advertenties dat momenteel aan de zoekopdracht voldoet.

    Nieuwe advertenties worden gemeld via het `marktplaats_new_listing` event
    op de HA event bus (zie coordinator.py) - dat event bevat de volledige
    advertentiegegevens en is bedoeld om automations op te bouwen. Deze
    sensor is vooral bedoeld voor dashboards/overzicht.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "matching_listings"
    _attr_icon = "mdi:home-search"

    def __init__(self, coordinator: MarktplaatsCoordinator, entry: MarktplaatsConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_matching_listings"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Marktplaats.nl (onofficiële integratie)",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> int:
        return self.coordinator.data.total_count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        return {
            "new_listings_last_poll": len(data.new_listings),
            "latest_new_listings": [
                {
                    "title": item.get("title"),
                    "price_cents": item.get("priceInfo", {}).get("priceCents"),
                    "url": f"https://link.marktplaats.nl/{item.get('itemId')}",
                }
                for item in data.new_listings[:5]
            ],
        }
