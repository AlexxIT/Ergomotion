from homeassistant.components.cover import CoverEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import DOMAIN
from .core.entity import XEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]

    add_entities([XCover(device, "head_position"), XCover(device, "foot_position")])


class XCover(XEntity, CoverEntity):
    _attr_is_closed = None

    def internal_update(self):
        attribute = self.device.attribute(self.attr)

        if attribute.get("move") and self._attr_current_cover_position is not None:
            if attribute["position"] > self._attr_current_cover_position:
                self._attr_is_opening = True
                self._attr_is_closing = False
            elif attribute["position"] < self._attr_current_cover_position:
                self._attr_is_opening = False
                self._attr_is_closing = True
        else:
            self._attr_is_opening = self._attr_is_closing = False

        self._attr_current_cover_position = attribute.get("position")

        if self._attr_current_cover_position is not None:
            self._attr_is_closed = self._attr_current_cover_position == 0

        if self.hass:
            self._async_write_ha_state()

    async def async_open_cover(self) -> None:
        await self.async_set_cover_position(100)

    async def async_close_cover(self) -> None:
        await self.async_set_cover_position(0)

    async def async_set_cover_position(self, position: int) -> None:
        self.device.set_attribute(self.attr, position)

    async def async_stop_cover(self) -> None:
        self.device.set_attribute("stop", None)
