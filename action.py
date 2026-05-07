from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import pyautogui

import config
from input_driver import InputDriver


logger = logging.getLogger(__name__)


@dataclass
class ActionController:
    last_action_at: dict[str, float] = field(default_factory=dict)
    input_driver: InputDriver = field(default_factory=InputDriver)

    def __post_init__(self) -> None:
        pyautogui.PAUSE = 0.04
        pyautogui.FAILSAFE = True

    def select_town_center(self) -> bool:
        if not self._cooldown_ready("select_town_center", config.ACTION_COOLDOWN_SECONDS):
            return False
        self._press_hotkey("select_town_center")
        logger.info("action=select_town_center")
        return True

    def train_villager(self) -> bool:
        if not self._cooldown_ready("train_villager", config.VILLAGER_TRAIN_COOLDOWN_SECONDS):
            return False
        self._press_hotkey("select_town_center")
        logger.info("action=select_town_center source=train_villager")
        time.sleep(0.08)
        self._press_hotkey("train_villager")
        logger.info("action=train_villager")
        return True

    def select_villagers(self, all_idle: bool = False) -> bool:
        action = "select_all_idle_villagers" if all_idle else "select_idle_villager"
        if not self._cooldown_ready(action, config.ACTION_COOLDOWN_SECONDS):
            return False
        self._press_hotkey(action)
        logger.info("action=%s", action)
        return True

    def build_house(self, position: tuple[int, int] = config.DEFAULT_HOUSE_PLACEMENT) -> bool:
        if not self._cooldown_ready("build_house", config.HOUSE_BUILD_COOLDOWN_SECONDS):
            return False

        self.select_villagers(all_idle=False)
        time.sleep(0.1)
        self._press_hotkey("build_menu")
        time.sleep(0.08)
        self._press_hotkey("build_house")
        time.sleep(0.08)
        self.input_driver.click(*position)
        logger.info("action=build_house position=%s", position)
        return True

    def cancel_current_command(self) -> None:
        self._press_hotkey("cancel")
        logger.info("action=cancel_current_command")

    def _press_hotkey(self, action_name: str) -> None:
        keys = config.HOTKEYS[action_name]
        if len(keys) == 1:
            self.input_driver.press(keys[0])
        else:
            self.input_driver.hotkey(*keys)

    def _cooldown_ready(self, action_name: str, cooldown_seconds: float) -> bool:
        now = time.monotonic()
        last = self.last_action_at.get(action_name, 0.0)
        if now - last < cooldown_seconds:
            return False

        self.last_action_at[action_name] = now
        return True
