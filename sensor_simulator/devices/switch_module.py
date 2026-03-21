import random
import time
from typing import Any, Dict

from devices.device_base import ZigbeeDevice


class ZigbeeSwitchModule(ZigbeeDevice):
    """
    Симулятор модуля выключателя (ZG-301Z).
    Поддерживает:
    - state (ON/OFF)
    - countdown (обратный отсчёт до выключения)
    - power_on_behavior (off, previous, on)
    - switch_type (toggle, state, momentary)
    """

    def __init__(self, ieee_address: str, friendly_name: str, location: str):
        super().__init__(ieee_address, friendly_name, location)
        self.state = random.choice(["ON", "OFF"])
        self.countdown = 0  # секунд до автоматического выключения
        self.power_on_behavior = random.choice(["off", "previous", "on"])
        self.switch_type = random.choice(["toggle", "state", "momentary"])
        self.last_command_time = 0

    def generate_data(self) -> Dict[str, Any]:
        current_time = time.time()

        # Обработка обратного отсчёта
        if self.countdown > 0:
            elapsed = current_time - self.last_command_time
            if elapsed >= self.countdown:
                self.state = "OFF"
                self.countdown = 0
            # для имитации мы не обновляем countdown в payload, он остаётся прежним
            # можно уменьшать его, но проще оставить как есть
            # однако чтобы не показывать устаревшие значения, можно обновлять:
            remaining = max(0, self.countdown - elapsed)
            self.countdown = int(remaining) if remaining > 0 else 0
        else:
            # Если таймер не активен, устройство может случайно менять состояние (редко)
            if random.random() < 0.005:  # 0.5% вероятность за цикл
                self.state = "ON" if self.state == "OFF" else "OFF"

        data = {
            "state": self.state,
            "countdown": self.countdown,
            "power_on_behavior": self.power_on_behavior,
            "switch_type": self.switch_type,
        }

        self.simulate_battery_drain(0.0002)
        return data

    def handle_command(self, command_payload: Dict[str, Any]) -> bool:
        """
        Обработка команд из топика /set.
        Возвращает True, если состояние устройства изменилось.
        """
        changed = False
        now = time.time()

        if "state" in command_payload:
            cmd_state = command_payload["state"].upper()
            if cmd_state in ["ON", "OFF", "TOGGLE"]:
                if cmd_state == "TOGGLE":
                    self.state = "OFF" if self.state == "ON" else "ON"
                else:
                    self.state = cmd_state
                changed = True
                self.last_command_time = now

        if "countdown" in command_payload:
            try:
                new_countdown = int(command_payload["countdown"])
                if 0 <= new_countdown <= 43200:  # согласно документации
                    self.countdown = new_countdown
                    changed = True
                    self.last_command_time = now
            except ValueError:
                pass

        if "power_on_behavior" in command_payload:
            behavior = command_payload["power_on_behavior"]
            if behavior in ["off", "previous", "on"]:
                self.power_on_behavior = behavior
                changed = True

        if "switch_type" in command_payload:
            stype = command_payload["switch_type"]
            if stype in ["toggle", "state", "momentary"]:
                self.switch_type = stype
                changed = True

        return changed
