"""DataUpdateCoordinator voor een enkele Marktplaats-zoekopdracht."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import homeassistant.components.notify as notify
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import api
from .const import (
    CONF_CONDITION,
    CONF_L1_CATEGORY_ID,
    CONF_L2_CATEGORY_ID,
    CONF_MAX_PRICE,
    CONF_MIN_PRICE,
    CONF_NOTIFY_SERVICE,
    CONF_POSTCODE,
    CONF_QUERY,
    CONF_RADIUS_KM,
    DOMAIN,
    EVENT_NEW_LISTING,
    SEARCH_RESULT_LIMIT,
)

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1

type MarktplaatsConfigEntry = ConfigEntry["MarktplaatsCoordinator"]


@dataclass
class MarktplaatsData:
    """Resultaat van een enkele pollronde."""

    # Marktplaats' eigen totalResultCount, NIET len(all_listings) - dat laatste
    # is altijd afgekapt op SEARCH_RESULT_LIMIT en zou het werkelijke aantal
    # bij een brede zoekterm ernstig te laag weergeven.
    total_count: int
    new_listings: list[dict[str, Any]] = field(default_factory=list)
    all_listings: list[dict[str, Any]] = field(default_factory=list)


def _first_image_url(item: dict[str, Any]) -> str | None:
    image_urls = item.get("imageUrls") or []
    if not image_urls:
        return None
    url = image_urls[0]
    return f"https:{url}" if url.startswith("//") else url


def _format_price(item: dict[str, Any]) -> str | None:
    # priceType (bv. "SEE_DESCRIPTION", "ON_REQUEST") is nooit empirisch
    # geverifieerd als vaste enum-lijst (zie const.py's CONDITIONS-commentaar
    # voor wat hier wel geverifieerd is), dus alleen de wel-geverifieerde
    # priceCents wordt getoond - liever geen prijs dan een geraden label.
    price_cents = item.get("priceInfo", {}).get("priceCents")
    if price_cents is None:
        return None
    return f"€ {price_cents / 100:.2f}".replace(".", ",")


def _build_notify_payload(item: dict[str, Any]) -> dict[str, Any]:
    """Bouwt de payload voor een klassieke notify-service uit een advertentie.

    Zet zowel "url" (de sleutel die de iOS Companion App leest) als
    "clickAction" (het Android-equivalent - los, niet-uitwisselbaar veld,
    empirisch geverifieerd via companion.home-assistant.io/docs/notifications/
    notifications-basic) op dezelfde advertentielink, zodat tikken op de
    melding de advertentie opent ongeacht op welk platform de geconfigureerde
    notify-service daadwerkelijk uitkomt (de integratie weet dat zelf niet -
    de gebruiker vult alleen een servicenaam in).
    """
    price = _format_price(item)
    location = item.get("location", {}).get("cityName")
    subtitle = " · ".join(part for part in (price, location) if part)
    url = f"https://link.marktplaats.nl/{item.get('itemId')}"

    payload: dict[str, Any] = {
        notify.ATTR_TITLE: item.get("title"),
        notify.ATTR_MESSAGE: "\n".join(line for line in (subtitle, url) if line),
    }
    data: dict[str, Any] = {"url": url, "clickAction": url}
    image_url = _first_image_url(item)
    if image_url:
        data["image"] = image_url
    payload[notify.ATTR_DATA] = data
    return payload


class MarktplaatsCoordinator(DataUpdateCoordinator[MarktplaatsData]):
    """Poll een enkele opgeslagen zoekopdracht en meld nieuwe advertenties."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: MarktplaatsConfigEntry,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=update_interval,
        )
        self.entry = entry
        self._session = async_get_clientsession(hass)
        self._store: Store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{entry.entry_id}_seen")
        self._seen_ids: set[str] | None = None
        # Blijft None totdat de opslag voor het eerst gelezen is; onderscheidt
        # "nooit eerder gepolld" (geen storage-bestand) van "wel eerder
        # gepolld, toen waren er gewoon 0 advertenties" (leeg bestand). Zonder
        # dit onderscheid zou de allereerste poll van een nieuwe zoekopdracht
        # in een keer tot wel 30 "nieuwe advertentie"-meldingen leiden voor
        # advertenties die er allang stonden.
        self._is_new_search: bool | None = None

    async def _async_load_seen_ids(self) -> set[str]:
        if self._seen_ids is None:
            stored = await self._store.async_load()
            self._is_new_search = stored is None
            self._seen_ids = set(stored) if stored else set()
        return self._seen_ids

    async def _async_update_data(self) -> MarktplaatsData:
        seen_ids = await self._async_load_seen_ids()

        entry_data = self.entry.data
        try:
            listings, total_result_count = await api.fetch_listings(
                self._session,
                entry_data[CONF_QUERY],
                entry_data[CONF_POSTCODE],
                entry_data[CONF_RADIUS_KM],
                limit=SEARCH_RESULT_LIMIT,
                min_price=entry_data.get(CONF_MIN_PRICE),
                max_price=entry_data.get(CONF_MAX_PRICE),
                condition=entry_data.get(CONF_CONDITION),
                l1_category_id=entry_data.get(CONF_L1_CATEGORY_ID),
                l2_category_id=entry_data.get(CONF_L2_CATEGORY_ID),
            )
        except api.MarktplaatsApiError as err:
            raise UpdateFailed(str(err)) from err

        if self._is_new_search:
            # Eerste poll ooit voor deze zoekopdracht: dit is de baseline,
            # geen van deze bestaande advertenties is "nieuw".
            new_listings: list[dict[str, Any]] = []
            self._is_new_search = False
        else:
            new_listings = [item for item in listings if item.get("itemId") not in seen_ids]

        notify_service = entry_data.get(CONF_NOTIFY_SERVICE)
        for item in new_listings:
            price_info = item.get("priceInfo", {})
            self.hass.bus.async_fire(
                EVENT_NEW_LISTING,
                {
                    "entry_id": self.entry.entry_id,
                    "query": entry_data[CONF_QUERY],
                    "item_id": item.get("itemId"),
                    "title": item.get("title"),
                    "price_cents": price_info.get("priceCents"),
                    "price_type": price_info.get("priceType"),
                    "url": f"https://link.marktplaats.nl/{item.get('itemId')}",
                    "location": item.get("location", {}).get("cityName"),
                    "image_url": _first_image_url(item),
                },
            )
            if notify_service:
                await self._async_notify(notify_service, item)

        seen_ids.update(item["itemId"] for item in listings if item.get("itemId") is not None)
        await self._store.async_save(sorted(seen_ids))

        return MarktplaatsData(
            total_count=total_result_count,
            new_listings=new_listings,
            all_listings=listings,
        )

    async def _async_notify(self, service_name: str, item: dict[str, Any]) -> None:
        """Stuurt een pushmelding voor één nieuwe advertentie.

        Roept bewust de klassieke, per-doel notify-service aan (bv.
        "mobile_app_telefoon") in plaats van de moderne entity-gebaseerde
        notify.send_message - alleen die klassieke variant accepteert nog een
        "data"-veld, nodig om de foto als bijlage mee te sturen (zie
        CONF_NOTIFY_SERVICE in const.py). Fouten (bv. een niet-bestaande of
        inmiddels verwijderde service) worden alleen gelogd, niet
        doorgegeven - een mislukte melding mag de poll zelf niet laten
        mislukken (de sensor/het event zijn dan nog steeds bijgewerkt).
        """
        try:
            await self.hass.services.async_call(
                notify.DOMAIN,
                service_name,
                _build_notify_payload(item),
                blocking=True,
            )
        except HomeAssistantError as err:
            _LOGGER.warning(
                "Kon geen melding sturen via notify.%s voor advertentie %s: %s",
                service_name,
                item.get("itemId"),
                err,
            )
