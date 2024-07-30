import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.webhook import async_generate_id
from homeassistant.helpers.network import get_url
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

import logging
_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN, WEBHOOK_ENDPOINT, CONF_DEVICE_NAME

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.device_name = None

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.device_name = user_input[CONF_DEVICE_NAME]
            self.webhook_id = async_generate_id()
            self.webhook_url = await self._get_webhook_url(self.webhook_id)
            return await self.async_step_webhook_info()
            
            return self.async_show_form(
                step_id="webhook_info",
                description_placeholders={
                    "webhook_url": webhook_url,
                    "device_name": self.device_name
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_NAME): str,
            }),
            errors=errors,
        )

    async def async_step_webhook_info(self, user_input=None):
        _LOGGER.debug("Entering async_step_webhook_info")
        _LOGGER.debug("Device name: %s", self.device_name)
        _LOGGER.debug("Webhook URL: %s", self.webhook_url)

        if user_input is not None:
            _LOGGER.debug("User input is not None, creating entry")
            return self.async_create_entry(
                title=self.device_name,
                data={
                    CONF_DEVICE_NAME: self.device_name,
                    WEBHOOK_ENDPOINT: self.webhook_id,
                    "webhook_url": self.webhook_url,
                },
            )

        _LOGGER.debug("Showing webhook info form")

        description = f"Your webhook URL for device '{self.device_name}' is:\n\n{self.webhook_url}\n\nPlease save this URL as you will need it to configure your tracking device. Click Submit to finish the setup."

        _LOGGER.debug(description)

        return self.async_show_form(
            step_id="webhook_info",
            description_placeholders={
                "webhook_url": self.webhook_url,
                "device_name": self.device_name,
                "description": description,
            },
            data_schema=vol.Schema({}),
        )

    async def _get_webhook_url(self, webhook_id):
        """Get the webhook URL."""
        return f"{get_url(self.hass, prefer_external=True, allow_cloud=True)}/api/webhook/{webhook_id}"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.attributes_to_delete = []

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            if "delete_attributes" in user_input:
                self.attributes_to_delete = user_input["delete_attributes"]
                return await self.async_step_delete_confirm()
            return self.async_create_entry(title="", data=user_input)

        webhook_url = f"{get_url(self.hass, prefer_external=True, allow_cloud=True)}/api/webhook/{self.config_entry.data[WEBHOOK_ENDPOINT]}"
        device_name = self.config_entry.data[CONF_DEVICE_NAME]

        description = f"Webhook URL for {device_name}:\n\n{webhook_url}\n\nYou can use this URL to update the device's location."

        # Get current attributes
        entity_registry = er.async_get(self.hass)
        entity_entries = er.async_entries_for_config_entry(entity_registry, self.config_entry.entry_id)
        
        options = {}
        for entity_entry in entity_entries:
            if entity_entry.domain == "device_tracker":
                state = self.hass.states.get(entity_entry.entity_id)
                if state:
                    attributes = state.attributes
                    options = {k: k for k in attributes.keys() if k not in [
                        "friendly_name", "icon", "latitude", "longitude",
                        "distance_from_home_meters", "distance_from_home_miles",
                        "direction_relative_to_home", "last_updated",
                        "time_since_last_significant_change", "cardinal_direction_from_home"
                    ]}
                _LOGGER.debug(f"Entity ID: {entity_entry.entity_id}, Attributes: {attributes}")
                break

        _LOGGER.debug(f"Options for deletion: {options}")

        return self.async_show_form(
            step_id="init",
            description_placeholders={"description": description},
            data_schema=vol.Schema({
                vol.Optional("delete_attributes"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=list(options.values()),
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN
                    )
                )
            }) if options else None
        )

    async def async_step_delete_confirm(self, user_input=None):
        if user_input is not None:
            # Perform the actual deletion of attributes
            entity_registry = er.async_get(self.hass)
            entity_entries = er.async_entries_for_config_entry(
                entity_registry, self.config_entry.entry_id
            )
            for entity_entry in entity_entries:
                if entity_entry.domain == "device_tracker":
                    state = self.hass.states.get(entity_entry.entity_id)
                    if state:
                        new_attributes = {k: v for k, v in state.attributes.items() if k not in self.attributes_to_delete}
                        self.hass.states.async_set(entity_entry.entity_id, state.state, new_attributes)
                    break
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="delete_confirm",
            description_placeholders={"attributes": ", ".join(self.attributes_to_delete)},
            data_schema=vol.Schema({}),
        )