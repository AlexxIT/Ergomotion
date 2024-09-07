import asyncio
import logging
import time
from typing import Callable

from bleak import BleakClient, BLEDevice, BleakError
from bleak_retry_connector import establish_connection

_LOGGER = logging.getLogger(__name__)

ACTIVE_TIME = 120  # seconds


class Client:
    def __init__(self, device: BLEDevice, callback: Callable):
        self.device = device
        self.callback = callback

        self.client: BleakClient | None = None

        self.ping_task: asyncio.Task | None = None
        self.ping_time = 0

        self.send_task: asyncio.Task | None = None
        self.send_data: bytes | None = None

        self.ping()

    def ping(self):
        self.ping_time = time.time() + ACTIVE_TIME

        if not self.ping_task:
            self.ping_task = asyncio.create_task(self._ping_loop())

    async def _ping_loop(self):
        while self.ping_time > time.time():
            try:
                _LOGGER.debug("connecting...")

                self.client = await establish_connection(
                    BleakClient, self.device, self.device.address
                )

                self.callback(char=None, data=True)

                await self.client.start_notify(
                    "0000ffe4-0000-1000-8000-00805f9b34fb", self.callback
                )

                _LOGGER.debug("connected")

                while (delay := self.ping_time - time.time()) > 0:
                    await asyncio.sleep(delay)

                _LOGGER.debug("disconnecting...")

                await self.client.disconnect()
            except TimeoutError:
                pass
            except BleakError as e:
                _LOGGER.debug("ping error", exc_info=e)
            except Exception as e:
                _LOGGER.warning("ping error", exc_info=e)
            finally:
                self.client = None
                self.callback(None, False)
                await asyncio.sleep(1)

        self.ping_task = None

    def send(self, data: bytes):
        self.send_data = data

        if self.client and self.client.is_connected and not self.send_task:
            self.send_task = asyncio.create_task(self._send_coro())

    async def _send_coro(self):
        try:
            _LOGGER.debug(f"send command: {self.send_data.hex()}")
            await self.client.write_gatt_char(
                "0000ffe9-0000-1000-8000-00805f9b34fb", self.send_data, True
            )
        except Exception as e:
            _LOGGER.warning("send error", exc_info=e)

        self.send_task = None
