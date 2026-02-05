from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import DOMAIN, NAME
from .device import Device


class XEntity(Entity):
    _attr_should_poll = False

    def __init__(self, device: Device, attr: str):
        self.device = device
        self.attr = attr

        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, device.mac)},
            identifiers={(DOMAIN, device.mac)},
            manufacturer=NAME,
            name=device.name or NAME,
        )
        self._attr_name = f"{device.name} {attr.replace('_', ' ').title()}"
        self._attr_unique_id = device.mac.replace(":", "").lower() + "_" + attr

        self.internal_update()
        device.register_update(attr, self.internal_update)

    def internal_update(self):
        pass

    async def async_update(self):
        self.device.client.ping()
