from homeassistant.components.light import LightEntity, LightEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import DOMAIN
from .core.entity import XEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]

    add_entities([XScene(device, "scene")])


class XScene(XEntity, LightEntity):
    _attr_icon = "mdi:bed"
    _attr_supported_features = LightEntityFeature.EFFECT

    def internal_update(self):
        attribute = self.device.attribute(self.attr)

        self._attr_is_on = attribute.get("is_on")
        self._attr_effect_list = attribute.get("options")
        self._attr_extra_state_attributes = attribute.get("extra")

        if self.hass:
            self._async_write_ha_state()

    async def async_turn_on(self, effect: str = None, **kwargs) -> None:
        self.device.set_attribute(self.attr, effect or "zerog")

    async def async_turn_off(self, **kwargs) -> None:
        self.device.set_attribute(self.attr, "flat")
