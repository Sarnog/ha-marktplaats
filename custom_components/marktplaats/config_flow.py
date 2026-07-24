"""Config flow voor de Marktplaats-integratie."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from . import api
from .const import (
    CONDITIONS,
    CONF_CONDITION,
    CONF_L1_CATEGORY_ID,
    CONF_L2_CATEGORY_ID,
    CONF_MAX_PRICE,
    CONF_MIN_PRICE,
    CONF_NOTIFY_SERVICE,
    CONF_POSTCODE,
    CONF_QUERY,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_TITLE_ONLY,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MIN_SCAN_INTERVAL_MINUTES,
)
from .coordinator import STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)

CONF_NAME = "name"

CONDITION_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=list(CONDITIONS),
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key="condition",
    )
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_QUERY): str,
        vol.Optional(CONF_TITLE_ONLY, default=False): bool,
        vol.Optional(CONF_NAME): str,
        vol.Optional(CONF_POSTCODE, default=""): str,
        vol.Optional(CONF_RADIUS_KM, default=DEFAULT_RADIUS_KM): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=200)
        ),
        vol.Optional(CONF_MIN_PRICE): vol.Coerce(float),
        vol.Optional(CONF_MAX_PRICE): vol.Coerce(float),
        vol.Optional(CONF_CONDITION): CONDITION_SELECTOR,
        vol.Optional(CONF_L1_CATEGORY_ID): vol.Coerce(int),
        vol.Optional(CONF_L2_CATEGORY_ID): vol.Coerce(int),
        vol.Optional(CONF_SCAN_INTERVAL_MINUTES, default=DEFAULT_SCAN_INTERVAL_MINUTES): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL_MINUTES)
        ),
        vol.Optional(CONF_NOTIFY_SERVICE): str,
    }
)


def _build_unique_id(data: dict[str, Any]) -> str:
    """Stabiele identifier voor een zoekopdracht, zodat identieke zoekopdrachten
    niet twee keer toegevoegd kunnen worden maar variaties op dezelfde
    zoekterm (andere filters) wel apart mogen bestaan."""
    parts = [
        data[CONF_QUERY].strip().lower(),
        str(data.get(CONF_TITLE_ONLY, False)),
        data[CONF_POSTCODE],
        str(data[CONF_RADIUS_KM]),
        str(data.get(CONF_MIN_PRICE)),
        str(data.get(CONF_MAX_PRICE)),
        str(data.get(CONF_CONDITION)),
        str(data.get(CONF_L1_CATEGORY_ID)),
        str(data.get(CONF_L2_CATEGORY_ID)),
    ]
    return "|".join(parts)


def _normalize_notify_service(value: str) -> str:
    """Verdraagt de veelgemaakte fout om de volledige "notify.xxx" in te
    vullen i.p.v. alleen de servicenaam die hass.services.async_call
    verwacht."""
    return value.strip().removeprefix("notify.")


async def _async_reset_seen_listings(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wist de opgeslagen 'geziene advertenties' voor een config entry.

    Gebruikt dezelfde opslagsleutel als MarktplaatsCoordinator (zie
    coordinator.py), zodat de eerstvolgende poll na een reconfigure met
    gewijzigde zoekcriteria een schone baseline krijgt in plaats van alle
    huidige treffers als "nieuw" te melden.
    """
    store: Store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{entry.entry_id}_seen")
    await store.async_remove()


class MarktplaatsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow: een enkele Marktplaats-zoekopdracht per config entry."""

    VERSION = 1

    async def _async_validate_and_resolve(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Vult data aan (postcode-resolutie) en test de zoekopdracht live."""
        data = {k: v for k, v in user_input.items() if k != CONF_NAME}
        session = async_get_clientsession(self.hass)

        if notify_service := data.get(CONF_NOTIFY_SERVICE):
            data[CONF_NOTIFY_SERVICE] = _normalize_notify_service(notify_service)

        postcode = data.get(CONF_POSTCODE) or ""
        if not postcode:
            postcode = await api.resolve_postcode_from_latlon(
                session, self.hass.config.latitude, self.hass.config.longitude
            )
        data[CONF_POSTCODE] = postcode

        # Test-call: bevestigt dat de combinatie van zoekterm/postcode/filters
        # daadwerkelijk werkt voordat de config entry aangemaakt wordt.
        await api.fetch_listings(
            session,
            data[CONF_QUERY],
            postcode,
            data[CONF_RADIUS_KM],
            limit=1,
            title_only=data.get(CONF_TITLE_ONLY, False),
            min_price=data.get(CONF_MIN_PRICE),
            max_price=data.get(CONF_MAX_PRICE),
            condition=data.get(CONF_CONDITION),
            l1_category_id=data.get(CONF_L1_CATEGORY_ID),
            l2_category_id=data.get(CONF_L2_CATEGORY_ID),
        )
        return data

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                resolved = await self._async_validate_and_resolve(user_input)
            except api.PostcodeResolutionError:
                errors["base"] = "postcode_resolution_failed"
            except api.MarktplaatsApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(_build_unique_id(resolved))
                self._abort_if_unique_id_configured()
                title = user_input.get(CONF_NAME) or resolved[CONF_QUERY]
                return self.async_create_entry(title=title, data=resolved)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            try:
                resolved = await self._async_validate_and_resolve(user_input)
            except api.PostcodeResolutionError:
                errors["base"] = "postcode_resolution_failed"
            except api.MarktplaatsApiError:
                errors["base"] = "cannot_connect"
            else:
                unique_id = _build_unique_id(resolved)
                # Let op: geen self._abort_if_unique_id_mismatch() hier. Die
                # methode is bedoeld voor reauth/reconfigure-flows waar de
                # unique_id een vaste identiteit is (bv. een serienummer) en
                # zou hier elke wijziging van zoekterm/filters blokkeren -
                # precies de velden die je via reconfigure wilt kunnen
                # aanpassen. async_set_unique_id() geeft zelf de eventueel
                # bestaande entry met deze unique_id terug; alleen als dat
                # een ANDERE entry is dan degene die we aan het bewerken zijn
                # is er echt een conflict (een identieke zoekopdracht bestaat
                # al elders).
                existing_entry = await self.async_set_unique_id(unique_id)
                if (
                    existing_entry is not None
                    and existing_entry.entry_id != reconfigure_entry.entry_id
                ):
                    errors["base"] = "already_configured"
                else:
                    if unique_id != reconfigure_entry.unique_id:
                        # De zoekcriteria zijn echt gewijzigd: de oude
                        # "geziene advertenties"-opslag hoort niet meer bij
                        # deze zoekopdracht. Zonder reset zou de coordinator
                        # denken dat dit geen nieuwe zoekopdracht is (de
                        # opslag bestaat al) en bij de eerstvolgende poll alle
                        # huidige treffers als "nieuw" melden.
                        await _async_reset_seen_listings(self.hass, reconfigure_entry)
                    title = user_input.get(CONF_NAME) or resolved[CONF_QUERY]
                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        title=title,
                        data=resolved,
                        unique_id=unique_id,
                    )

        suggested = {**reconfigure_entry.data, CONF_NAME: reconfigure_entry.title}
        schema = self.add_suggested_values_to_schema(DATA_SCHEMA, suggested)
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)
