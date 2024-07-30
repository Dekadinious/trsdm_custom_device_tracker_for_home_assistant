import logging
from homeassistant.const import CONF_PLATFORM
from homeassistant.helpers import config_validation as cv
from homeassistant.core import HomeAssistant
from homeassistant.components import webhook
from homeassistant.helpers.dispatcher import async_dispatcher_send
from aiohttp import web

from .const import DOMAIN, WEBHOOK_ENDPOINT, CONF_DEVICE_NAME

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the TRSDM Dynamic Device Tracker component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[DOMAIN][entry.entry_id] = {}
    
    webhook_id = entry.data[WEBHOOK_ENDPOINT]
    
    webhook.async_register(
        hass,
        DOMAIN,
        f"TRSDM Tracker {entry.data[CONF_DEVICE_NAME]}",
        webhook_id,
        handle_webhook,
    )
    
    await hass.config_entries.async_forward_entry_setups(entry, ["device_tracker"])
    
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["device_tracker"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    webhook.async_unregister(hass, entry.data[WEBHOOK_ENDPOINT])
    return unload_ok

async def handle_webhook(hass: HomeAssistant, webhook_id: str, request) -> web.Response:
    try:
        payload = await request.json()
    except ValueError:
        _LOGGER.error(f"Received invalid JSON for webhook {webhook_id}")
        return web.json_response(
            {"success": False, "message": "Invalid JSON"}, 
            status=400
        )

    if 'latitude' not in payload or 'longitude' not in payload:
        _LOGGER.error(f"Received payload without latitude or longitude for webhook {webhook_id}")
        return web.json_response(
            {"success": False, "message": "Latitude and longitude are required"}, 
            status=400
        )

    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data[WEBHOOK_ENDPOINT] == webhook_id:
            device_name = entry.data[CONF_DEVICE_NAME]
            async_dispatcher_send(hass, f"{DOMAIN}_{device_name}_update", payload)
            return web.json_response(
                {"success": True},
                status=200
            )

    _LOGGER.error(f"Received data for unknown webhook: {webhook_id}")
    return web.json_response(
        {"success": False, "message": "Unknown webhook ID"},
        status=400
    )