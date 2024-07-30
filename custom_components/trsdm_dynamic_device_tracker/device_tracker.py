from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from datetime import datetime

from .const import DOMAIN, CONF_DEVICE_NAME
from .util import calculate_distance, calculate_bearing, get_cardinal_direction

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([TRSDMDeviceTracker(hass, entry)])

class TRSDMDeviceTracker(TrackerEntity):
    def __init__(self, hass, entry):
        self._hass = hass
        self._entry = entry
        self._device_name = entry.data[CONF_DEVICE_NAME]
        self._attr = {}
        self._latitude = None
        self._longitude = None
        self._last_significant_change_time = None
        self._last_significant_distance = None
        self._cumulative_change = 0
        self._last_significant_change_time = None

    async def async_added_to_hass(self):
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self._hass,
                f"{DOMAIN}_{self._device_name}_update",
                self._handle_update
            )
        )

    async def async_remove_attributes(self, attributes_to_remove):
        """Remove specified attributes from the entity."""
        for attr in attributes_to_remove:
            self._attr.pop(attr, None)
        self.async_write_ha_state()

    @callback
    def _handle_update(self, payload):
        """Handle device updates."""

        current_time = datetime.now()

        if 'latitude' in payload and 'longitude' in payload:
            self._latitude = payload['latitude']
            self._longitude = payload['longitude']
            
            # Calculate distance from home
            home_lat = self._hass.config.latitude
            home_lon = self._hass.config.longitude
            current_distance = calculate_distance(home_lat, home_lon, self._latitude, self._longitude)
            
            self._attr['distance_from_home_meters'] = round(current_distance, 2)
            self._attr['distance_from_home_miles'] = round(current_distance / 1609.34, 2)

            # Direction calculation
            if self._last_significant_distance is None:
                self._last_significant_distance = current_distance
                self._attr['direction_relative_to_home'] = 'stationary'
            else:
                distance_change = current_distance - self._last_significant_distance
                self._cumulative_change += abs(distance_change)

                if self._cumulative_change >= 10:
                    self._last_significant_change_time = current_time

                    if current_distance > self._last_significant_distance:
                        self._attr['direction_relative_to_home'] = 'away_from'
                    elif current_distance < self._last_significant_distance:
                        self._attr['direction_relative_to_home'] = 'towards'
                    else:
                        self._attr['direction_relative_to_home'] = 'stationary'

                    self._last_significant_distance = current_distance
                    self._cumulative_change = 0

            self._attr['last_updated'] = datetime.now().isoformat()

            if self._last_significant_change_time:
                self._attr['time_since_last_significant_change'] = self._last_significant_change_time.isoformat()
            else:
                self._attr['time_since_last_significant_change'] = 'N/A'

            bearing = calculate_bearing(home_lat, home_lon, self._latitude, self._longitude)
            cardinal_direction = get_cardinal_direction(bearing)
            self._attr['cardinal_direction_from_home'] = cardinal_direction

        for key, value in payload.items():
            if key not in ['latitude', 'longitude']:
                self._attr[key] = value

        self.async_write_ha_state()

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self._entry.entry_id}"

    @property
    def name(self):
        return f"TRSDM Tracker {self._device_name}"

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    @property
    def state_attributes(self):
        """Return the device state attributes."""
        attrs = {}
        if self.latitude is not None and self.longitude is not None:
            attrs["latitude"] = self.latitude
            attrs["longitude"] = self.longitude
        attrs.update(self._attr)
        return attrs