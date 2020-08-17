import enum
from typing import Any, Dict

import click
from miio.click_common import format_output, command
from miio.fan import OperationMode, FanException
from miio.miot_device import MiotDevice

_MAPPING = {
    "power": {"siid": 2, "piid": 1},
    "fan_level": {"siid": 2, "piid": 2},
    "child_lock": {"siid": 3, "piid": 1},
    "swing_mode": {"siid": 2, "piid": 3},
    "power_off_time": {"siid": 2, "piid": 10},
    "buzzer": {"siid": 2, "piid": 11},
    "light": {"siid": 2, "piid": 12},
    "mode": {"siid": 2, "piid": 7},
}


# class OperationMode(enum.Enum):
#     Normal = "0"
#     Nature = "1"


class FanStatus1C:
    """Container for status reports from the Xiaomi Mi Smart Pedestal Fan DMaker 1C."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data

    @property
    def power(self) -> str:
        """Power state."""
        return "on" if self.data["power"] else "off"

    @property
    def is_on(self) -> bool:
        """True if device is currently on."""
        return self.data["power"]

    @property
    def mode(self) -> OperationMode:
        """Operation mode."""
        return OperationMode.Nature if self.data["mode"] == 1 else OperationMode.Normal

    @property
    def speed(self) -> int:
        """Speed of the motor."""
        return self.data["fan_level"]

    @property
    def oscillate(self) -> bool:
        """True if oscillation is enabled."""
        return self.data["swing_mode"]

    @property
    def delay_off_countdown(self) -> int:
        """Countdown until turning off in seconds."""
        return self.data["power_off_time"]

    @property
    def led(self) -> bool:
        """True if LED is turned on, if available."""
        return self.data["light"]

    @property
    def buzzer(self) -> bool:
        """True if buzzer is turned on."""
        return self.data["buzzer"]

    @property
    def child_lock(self) -> bool:
        """True if child lock is on."""
        return self.data["child_lock"]

    def __repr__(self) -> str:
        s = (
            "<FanStatus power=%s, "
            "mode=%s, "
            "speed=%s, "
            "oscillate=%s, "
            "led=%s, "
            "buzzer=%s, "
            "child_lock=%s, "
            "delay_off_countdown=%s>"
            % (
                self.power,
                self.mode,
                self.speed,
                self.oscillate,
                self.led,
                self.buzzer,
                self.child_lock,
                self.delay_off_countdown,
            )
        )
        return s

    def __json__(self):
        return self.data


class Fan1C(MiotDevice):
    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = 0,
        debug: int = 0,
        lazy_discover: bool = True,
    ) -> None:
        super().__init__(_MAPPING, ip, token, start_id, debug, lazy_discover)

    @command(
        default_output=format_output(
            "",
            "Power: {result.power}\n"
            "Operation mode: {result.mode}\n"
            "Speed: {result.speed}\n"
            "Oscillate: {result.oscillate}\n"
            "Angle: {result.angle}\n"
            "LED: {result.led}\n"
            "Buzzer: {result.buzzer}\n"
            "Child lock: {result.child_lock}\n"
        )
    )
    def status(self):
        """Retrieve properties."""
        data = {}
        for prop in self.get_properties_for_mapping():
            data[prop["did"]] = prop["value"] if prop["code"] == 0 else None

        return FanStatus1C(data)

    @command(default_output=format_output("Powering on"))
    def on(self):
        """Power on."""
        return self.set_property("power", True)

    @command(default_output=format_output("Powering off"))
    def off(self):
        """Power off."""
        return self.set_property("power", False)

    @command(
        click.argument("speed", type=int),
        default_output=format_output("Setting speed of the direct mode to {speed}"),
    )
    def set_direct_speed(self, speed: int):
        """Set speed of the direct mode."""
        if speed not in (1, 2, 3):
            raise FanException("Invalid speed: %s" % speed)

        return self.set_property("fan_level", speed)

    def set_oscillate(self, oscillate: bool):
        """Set oscillate on/off."""
        return self.set_property("swing_mode", oscillate)

    @command(
        click.argument("buzzer", type=bool),
        default_output=format_output(
            lambda buzzer: "Turning on buzzer" if buzzer else "Turning off buzzer"
        ),
    )
    def set_buzzer(self, buzzer: bool):
        """Set buzzer on/off."""
        return self.set_property("buzzer", buzzer)

    @command(
        click.argument("lock", type=bool),
        default_output=format_output(
            lambda lock: "Turning on child lock" if lock else "Turning off child lock"
        ),
    )
    def set_child_lock(self, lock: bool):
        """Set child lock on/off."""
        return self.set_property("child_lock", lock)

    @command(
        click.argument("natural", type=bool),
        default_output=format_output(
            lambda natural: "Turning on natural mode" if natural else "Turning off natural mode"
        ),
    )
    def set_natural_mode(self, natural: bool):
        """Set natural mode on/off."""
        return self.set_property("mode", 1 if natural else 0)

    @command(
        click.argument("seconds", type=int),
        default_output=format_output("Setting delayed turn off to {seconds} seconds"),
    )
    def delay_off(self, seconds: int):
        """Set delay off seconds."""

        if seconds < 0:
            raise FanException("Invalid value for a delayed turn off: %s" % seconds)

        return self.set_property("power_off_time", seconds)
