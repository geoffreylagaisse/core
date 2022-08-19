"""The qbittorrent component."""
import asyncio
import logging

from qbittorrent.client import LoginRequired
from requests.exceptions import RequestException

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_per_platform
from homeassistant.helpers.typing import ConfigType

from .client import create_client
from .const import DATA_KEY_CLIENT, DATA_KEY_NAME, DOMAIN

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Qbittorrent component."""
    hass.data.setdefault(DOMAIN, {})

    # Import configuration from sensor platform
    config_platform = config_per_platform(config, "sensor")
    for p_type, p_config in config_platform:
        if p_type != DOMAIN:
            continue

        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=p_config,
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Qbittorrent from a config entry."""
    name = "Qbittorrent"
    try:
        client = await hass.async_add_executor_job(
            create_client,
            entry.data[CONF_URL],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
    except LoginRequired:
        _LOGGER.error("Invalid authentication")
        return False

    except RequestException as err:
        raise ConfigEntryNotReady("Connection failed") from err

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_KEY_CLIENT: client,
        DATA_KEY_NAME: name,
    }
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload Qbittorrent Entry from config_entry."""

    unload_ok = all(
        await asyncio.gather(
            *(
                hass.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            )
        )
    )

    return unload_ok
