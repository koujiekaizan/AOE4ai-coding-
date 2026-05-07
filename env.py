from __future__ import annotations

import logging
import time

import keyboard

import config
from actions import ActionController
from screen_capture import is_game_foreground
from vision import ResourceReader, ResourceSnapshot


logger = logging.getLogger(__name__)


class Aoe4Env:
    def __init__(self) -> None:
        self.reader = ResourceReader()
        self.actions = ActionController()
        self.paused = False
        self.last_pause_toggle = 0.0

    def run(self) -> None:
        logger.info("AoE4 automation started. Press T to pause/resume, Esc to exit.")

        while True:
            if self._exit_requested():
                logger.info("Exit key pressed. Stopping bot.")
                return

            self._update_pause_state()
            if self.paused:
                time.sleep(config.LOOP_INTERVAL_SECONDS)
                continue

            if not is_game_foreground():
                logger.warning("game_not_foreground expected_title=%r", config.GAME_WINDOW_TITLE)
                time.sleep(config.LOOP_INTERVAL_SECONDS)
                continue

            self.step()
            time.sleep(config.LOOP_INTERVAL_SECONDS)

    def step(self) -> None:
        resources = self._read_resources()
        if resources is None:
            return

        self._log_resources(resources)

        if resources.failures:
            for field, reason in resources.failures.items():
                logger.warning("ocr_failure field=%s reason=%s", field, reason)

        if should_build_house(resources):
            self.actions.build_house()
        elif should_train_villager(resources):
            self.actions.train_villager()

    def _read_resources(self) -> ResourceSnapshot | None:
        try:
            return self.reader.read_resources()
        except Exception:
            logger.exception("resource_read_failed")
            return None

    def _update_pause_state(self) -> None:
        if not keyboard.is_pressed(config.PAUSE_KEY):
            return

        now = time.monotonic()
        if now - self.last_pause_toggle <= 0.5:
            return

        self.paused = not self.paused
        self.last_pause_toggle = now
        logger.info("paused=%s", self.paused)

    def _exit_requested(self) -> bool:
        return keyboard.is_pressed(config.EXIT_KEY)

    def _log_resources(self, resources: ResourceSnapshot) -> None:
        logger.info(
            "resources food=%s wood=%s gold=%s stone=%s pop=%s/%s failures=%s",
            resources.food,
            resources.wood,
            resources.gold,
            resources.stone,
            resources.population_current,
            resources.population_cap,
            resources.failures,
        )


def should_build_house(resources: ResourceSnapshot) -> bool:
    return (
        resources.wood is not None
        and resources.wood >= config.HOUSE_WOOD_COST
        and resources.is_population_capped_soon
    )


def should_train_villager(resources: ResourceSnapshot) -> bool:
    if resources.food is None:
        return False
    if resources.food < config.VILLAGER_FOOD_COST:
        return False
    if resources.population_current is None or resources.population_cap is None:
        return True
    return resources.population_current < resources.population_cap
