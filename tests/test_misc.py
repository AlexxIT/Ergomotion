from custom_components.ergomotion.core.client import Client
from custom_components.ergomotion.core.device import Device

Client.ping = lambda *args: None


def test_450():
    device = Device("test", None)
    device.on_data(None, bytes.fromhex("edfe160000000000000000000000ffff"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 0,
        "head_massage": 0,
        "head_move": False,
        "head_position": 0,
        "scene": False,
        "timer_remain": 0,
        "timer_target": None,
        "led": False,
    }

    device.on_data(None, bytes.fromhex("edfe1600000000030307bf020000032d"))
    assert device.current_state == {
        "foot_massage": 50,
        "foot_move": False,
        "foot_position": 0,
        "head_massage": 50,
        "head_move": False,
        "head_position": 0,
        "scene": True,
        "timer_remain": 1800,
        "timer_target": "30",
        "led": False,
    }

    device.on_data(None, bytes.fromhex("edfe161e58c52c00000000000000ff98"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 11461,
        "head_massage": 0,
        "head_move": False,
        "head_position": 22558,
        "led": False,
        "scene": True,
        "timer_remain": 0,
        "timer_target": None,
    }


def test_630v1():
    device = Device("test", None)
    device.on_data(None, bytes.fromhex("EDFE16000000000000000000000FFFF0"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 0,
        "head_massage": 0,
        "head_move": False,
        "head_position": 0,
        "scene": False,
        "timer_remain": 0,
        "timer_target": None,
        "led": False,
    }

    # zero pos, led true
    device.on_data(None, bytes.fromhex("EDFE16000000000000000000004FFFB0"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 0,
        "head_massage": 0,
        "head_move": False,
        "head_position": 0,
        "scene": False,
        "timer_remain": 0,
        "timer_target": None,
        "led": True,
    }

    # max pos, led true
    device.on_data(None, bytes.fromhex("EDFE16AC443C2D0000000000004FFF57"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 11580,
        "head_massage": 0,
        "head_move": False,
        "head_position": 17580,
        "led": True,
        "scene": True,
        "timer_remain": 0,
        "timer_target": None,
    }

    # max pos, led false
    device.on_data(None, bytes.fromhex("EDFE16AC443C2D0000000000000FFF97"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 11580,
        "head_massage": 0,
        "head_move": False,
        "head_position": 17580,
        "led": False,
        "scene": True,
        "timer_remain": 0,
        "timer_target": None,
    }


def test_630v2():
    device = Device("test", None)

    # zero pos
    device.on_data(None, bytes.fromhex("F0FE16000000000000000000000000FF0100FB"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 0,
        "head_massage": 0,
        "head_move": False,
        "head_position": 0,
        "led": False,
        "scene": False,
        "timer_remain": 0,
        "timer_target": None,
    }

    # max pos
    device.on_data(None, bytes.fromhex("F0FE16FA79D4240000000000000000FF0100FF"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 9428,
        "head_massage": 0,
        "head_move": False,
        "head_position": 31226,
        "led": False,
        "scene": True,
        "timer_remain": 0,
        "timer_target": None,
    }

    # zero pos, led true
    device.on_data(None, bytes.fromhex("F0FE16000000000000000000000040FF0100BB"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 0,
        "head_massage": 0,
        "head_move": False,
        "head_position": 0,
        "led": True,
        "scene": False,
        "timer_remain": 0,
        "timer_target": None,
    }

    # head massage
    device.on_data(None, bytes.fromhex("F0FE1600000000060000B4D00000000101006F"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 0,
        "head_massage": 100,
        "head_move": False,
        "head_position": 0,
        "led": False,
        "scene": True,
        "timer_remain": 534,
        "timer_target": "10",
    }

    # foot massage
    device.on_data(None, bytes.fromhex("F0FE16000000000006002AD9000000010100F0"))
    assert device.current_state == {
        "foot_massage": 100,
        "foot_move": False,
        "foot_position": 0,
        "head_massage": 0,
        "head_move": False,
        "head_position": 0,
        "led": False,
        "scene": True,
        "timer_remain": 556,
        "timer_target": "10",
    }


def test_630v3():
    device = Device("test", None)

    device.on_data(None, bytes.fromhex("f1fe16 000000000000 0000000003ff00000C01EB"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 0,
        "head_massage": 0,
        "head_move": False,
        "head_position": 0,
        "led": False,
        "scene": False,
        "timer_remain": 0,
        "timer_target": None,
    }

    device.on_data(None, bytes.fromhex("f1fe16 6b514b230303 37EA0000020100000C0397"))
    assert device.current_state == {
        "foot_massage": 50,
        "foot_move": False,
        "foot_position": 9035,
        "head_massage": 50,
        "head_move": False,
        "head_position": 20843,
        "led": False,
        "scene": True,
        "timer_remain": 600,
        "timer_target": "10",
    }

    device.on_data(None, bytes.fromhex("f1fe166B514B2300000000000003ff00000C03BF"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 9035,
        "head_massage": 0,
        "head_move": False,
        "head_position": 20843,
        "led": False,
        "scene": True,
        "timer_remain": 0,
        "timer_target": None,
    }

    device.on_data(None, bytes.fromhex("f1fe16 6B514B230000 0000000043ff00000C037F"))
    assert device.current_state == {
        "foot_massage": 0,
        "foot_move": False,
        "foot_position": 9035,
        "head_massage": 0,
        "head_move": False,
        "head_position": 20843,
        "led": True,
        "scene": True,
        "timer_remain": 0,
        "timer_target": None,
    }
