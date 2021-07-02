"""Config flow for Rinnai integration."""
from rinnaicontrolr import async_get_api
from rinnaicontrolr.errors import RequestError
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, LOGGER

DATA_SCHEMA = vol.Schema({vol.Required("email"): str, vol.Required("password"): str})

async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.
    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    session = async_get_clientsession(hass)
    try:
        api = await async_get_api(
            data[CONF_EMAIL], data[CONF_PASSWORD], session=session
        )
    except RequestError as request_error:
        LOGGER.error("Error connecting to the Rinnai API: %s", request_error)
        raise CannotConnect from request_error

    user_info = await api.user.get_info()
    first_device_name = user_info["devices"]["items"][0]["id"]
    device_info = await api.device.get_info(first_device_name)
    return {"title": device_info["data"]["getDevice"]["device_name"]}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rinnai."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL])
            self._abort_if_unique_id_configured()
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""