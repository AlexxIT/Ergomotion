import time
from typing import TypedDict, Callable

from bleak import BLEDevice, BleakGATTCharacteristic

from .client import Client

MIN_STEP = 100
SCENE_OPTIONS = ["flat", "lounge", "tv", "zerog"]
TIMER_OPTIONS = ["10", "20", "30"]


class Attribute(TypedDict, total=False):
    is_on: bool  # binary_sensor

    position: int  # cover
    move: bool  # cover

    percentage: int

    current: str  # select
    options: list[str]  # select

    extra: dict  # entity


class Device:
    def __init__(self, name: str, device: BLEDevice | None):
        self.name = name

        self.client = Client(device, self.on_data) if device else None

        self.connected = False

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

    def on_data(self, char: BleakGATTCharacteristic | None, data: bytes | bool):
        if isinstance(data, bool):
            # connected true/false update
            self.connected = data

            for handler in self.updates_connect:
                handler()
            return

        if self.current_data != data:
            if data[0] == 0xED and len(data) == 16:
                data1 = data[3:]
                data2 = data[9:]
            elif data[0] == 0xF0 and len(data) == 19:
                data1 = data[3:]
                data2 = data[10:]
            elif data[0] == 0xF1 and len(data) == 20:
                data1 = data[3:]
                data2 = data[9:]
            else:
                return

            head_position = int.from_bytes(data1[0:2], "little")
            foot_position = int.from_bytes(data1[2:4], "little")
            remain = int.from_bytes(data2[0:3], "little")
            move = data2[4] & 0xF if data[0] != 0xF1 else 0xF
            timer = data2[5]

            self.current_data = data
            self.current_state = {
                "head_position": head_position if head_position != 0xFFFF else 0,
                "foot_position": foot_position if foot_position != 0xFFFF else 0,
                "head_move": move != 0xF and move & 1 > 0,
                "foot_move": move != 0xF and move & 2 > 0,
                # Hass uses int, not round
                "head_massage": int(data1[4] / 6 * 100),
                "foot_massage": int(data1[5] / 6 * 100),
                "timer_target": TIMER_OPTIONS[timer - 1] if timer != 0xFF else None,
                "timer_remain": round(remain / 100),
                "led": data2[4] & 0x40 > 0,
            }

            self.current_state["scene"] = (
                self.current_state["head_position"] > MIN_STEP
                or self.current_state["foot_position"] > MIN_STEP
                or self.current_state["head_massage"] > 0
                or self.current_state["foot_massage"] > 0
            )

            for handler in self.updates_state:
                handler()

        if self.target_state:
            self.send_command()

    def attribute(self, attr: str) -> Attribute:
        if attr == "connection":
            return Attribute(
                is_on=self.connected, extra={"mac": self.client.device.address}
            )

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

        if attr == "led":
            return Attribute(is_on=self.current_state.get(attr))

    def set_attribute(self, name: str, value: int | str | None):
        self.target_state[name] = value
        self.client.ping()

    def send_command(self):
        command = 0

        for attr, target in list(self.target_state.items()):
            if attr == "stop":
                self.target_state.clear()
                command = 0
                break

            current = self.current_state.get(attr)
            if (
                abs(current - target) < MIN_STEP  # not best idea
                if attr.endswith("position")
                else current == target
            ):
                self.target_state.pop(attr)
                continue

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

            elif attr == "foot_massage":
                if current < target:
                    command |= 0x00000400
                elif current > target:
                    command |= 0x01000000
            elif attr == "head_massage":
                if current < target:
                    command |= 0x00000800
                elif current > target:
                    command |= 0x00800000

            # multiple push buttons
            elif attr == "timer_target":
                command |= 0x00000200
            elif attr == "led":
                command |= 0x00020000

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
