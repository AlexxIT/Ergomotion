import time
from datetime import datetime, timezone
from typing import TypedDict, Callable

from bleak import BLEDevice, AdvertisementData, BleakGATTCharacteristic

from .client import Client

HEAD_MAX = 22500
FOOT_MAX = 11500
TIMER_OPTIONS = ["10", "20", "30"]
SCENE_OPTIONS = ["flat", "lounge", "tv", "zerog"]


class Attribute(TypedDict, total=False):
    is_on: bool  # binary_sensor

    position: int  # cover
    move: bool  # cover

    percentage: int

    current: str  # select
    options: list[str]  # select

    extra: dict  # entity


class Device:
    def __init__(self, name: str, device: BLEDevice):
        self.name = name

        self.client = Client(device, self.on_data)

        self.connected = False
        self.conn_info = {"mac": device.address}

        self.current_data = None
        self.current_state = {}

        self.target_delay = 0
        self.target_state = {}

        self.updates_connect: list = []
        self.updates_state: list = []

    @property
    def mac(self) -> str:
        return self.client.device.address

    def register_update(self, attr: str, handler: Callable):
        if attr == "connection":
            self.updates_connect.append(handler)
        else:
            self.updates_state.append(handler)

    def update_ble(self, adv: AdvertisementData):
        self.conn_info["last_seen"] = (datetime.now(timezone.utc),)
        if adv:
            self.conn_info["rssi"] = adv.rssi

        for handler in self.updates_connect:
            handler()

    def on_data(self, char: BleakGATTCharacteristic | None, data: bytes | bool):
        if char is None:
            # connected true/false update
            self.connected = data

            for handler in self.updates_connect:
                handler()
            return

        if not data.startswith(b"\xed\xfe\x16") or len(data) < 16:
            return

        if self.current_data != data:
            self.current_data = data
            self.current_state = {
                "head_position": min(
                    round(int.from_bytes(data[3:5], "little") / HEAD_MAX * 100), 100
                ),
                "foot_position": min(
                    round(int.from_bytes(data[5:7], "little") / HEAD_MAX * 100), 100
                ),
                "head_move": (data[13] & 1) > 0,
                "foot_move": (data[13] & 2) > 0,
                # Hass uses int, not round
                "head_massage": int(data[7] / 6 * 100),
                "foot_massage": int(data[8] / 6 * 100),
                "timer_target": TIMER_OPTIONS[data[14] - 1]
                if data[14] != 0xFF
                else None,
                "timer_remain": round(int.from_bytes(data[9:12], "little") / 100),
            }

            self.current_state["scene"] = (
                self.current_state["head_position"]
                or self.current_state["foot_position"]
                or self.current_state["head_massage"]
                or self.current_state["foot_massage"]
            ) != 0

            for handler in self.updates_state:
                handler()

        if self.target_state:
            self.send_command()

    def attribute(self, attr: str) -> Attribute:
        if attr == "connection":
            return Attribute(is_on=self.connected, extra=self.conn_info)

        if attr == "head_position":
            return Attribute(
                position=self.current_state.get(attr),
                move=self.current_state.get("head_move"),
            )

        if attr == "foot_position":
            return Attribute(
                position=self.current_state.get(attr),
                move=self.current_state.get("head_move"),
            )

        if attr in ("head_massage", "foot_massage"):
            if percent := self.current_state.get(attr):
                return Attribute(
                    percentage=percent,
                    current=self.current_state.get("timer_target"),
                    options=TIMER_OPTIONS,
                )
            else:
                return Attribute(percentage=percent, options=TIMER_OPTIONS)

        if attr == "scene":
            remain = self.current_state.get("timer_remain")
            return Attribute(
                is_on=self.current_state.get(attr),
                options=SCENE_OPTIONS,
                extra={"timer_remain": remain} if remain else None,
            )

    def set_attribute(self, name: str, value: int | str):
        self.target_state[name] = value
        self.client.ping()

    def send_command(self):
        command = 0

        for attr, target in list(self.target_state.items()):
            current = self.current_state.get(attr)
            if current == target:
                self.target_state.pop(attr)

            if attr == "stop":
                self.target_state.clear()
                command = 0
                break

            # hold buttons
            elif attr == "head_position":
                if current < target:
                    command |= 0x00000001
                elif current > target:
                    command |= 0x00000002
            elif attr == "foot_position":
                if current < target:
                    command |= 0x00000004
                elif current > target:
                    command |= 0x00000008

            # multiple push buttons
            elif attr == "timer_target":
                command |= 0x00000200
            elif attr == "foot_massage":
                command |= 0x00000400
            elif attr == "head_massage":
                command |= 0x00000800

            # single push buttons
            elif attr == "scene":
                if target == "flat":
                    command |= 0x08000000
                elif target == "zerog":
                    command |= 0x00001000
                elif target == "lounge":
                    command |= 0x00002000
                elif target == "tv":
                    command |= 0x00004000

                self.target_state.pop(attr)

        # send push buttons with 0.5 sec delay
        if time.time() > self.target_delay:
            self.target_delay = time.time() + 0.5
        else:
            command &= 0xFF

        data = b"\xe5\xfe\x16" + command.to_bytes(4, "little")
        data += bytes([crc(data)])

        self.client.send(data)


def crc(data: bytes) -> int:
    return (~sum(i for i in data)) & 0xFF
