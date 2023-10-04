from homeassistant.components.cover import CoverEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .core import DOMAIN
from .core.entity import XEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]

    add_entities([XCover(device, "head_position"), XCover(device, "foot_position")])


class XCover(XEntity, CoverEntity, RestoreEntity):
    _attr_is_closed = None

    async def async_added_to_hass(self) -> None:
        state = await self.async_get_last_state()
        max_position = state.attributes.get("max_position") if state else None
        self._attr_extra_state_attributes = {"max_position": max_position or 100}

    @property
    def max_position(self):
        return self._attr_extra_state_attributes["max_position"]

    def internal_update(self):
        attribute = self.device.attribute(self.attr)

        position = attribute["position"]
        if position is None:
            return

        if position > self.max_position:
            self._attr_extra_state_attributes["max_position"] = position
            position = 100
        else:
            position = round(position / self.max_position * 100.0)

        if attribute.get("move") and self._attr_current_cover_position is not None:
            if position > self._attr_current_cover_position:
                self._attr_is_opening = True
                self._attr_is_closing = False
            elif position < self._attr_current_cover_position:
                self._attr_is_opening = False
                self._attr_is_closing = True
        else:
            self._attr_is_opening = self._attr_is_closing = False

        self._attr_current_cover_position = position
        self._attr_is_closed = self._attr_current_cover_position == 0

        if self.hass:
            self._async_write_ha_state()

    async def async_open_cover(self) -> None:
        await self.async_set_cover_position(self.max_position)

    async def async_close_cover(self) -> None:
        await self.async_set_cover_position(0)

    async def async_set_cover_position(self, position: int) -> None:
        position = round(position / 100.0 * self.max_position)
        self.device.set_attribute(self.attr, position)

    async def async_stop_cover(self) -> None:
        self.device.set_attribute("stop", None)
