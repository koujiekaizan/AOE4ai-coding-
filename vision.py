from __future__ import annotations

import logging
import re
from collections import deque
from dataclasses import dataclass, field
from statistics import median
from typing import Deque, Optional

import cv2
import numpy as np
import pytesseract

import config
from screen_capture import capture_screen


logger = logging.getLogger(__name__)


@dataclass
class ResourceSnapshot:
    food: Optional[int] = None
    wood: Optional[int] = None
    gold: Optional[int] = None
    stone: Optional[int] = None
    population_current: Optional[int] = None
    population_cap: Optional[int] = None
    failures: dict[str, str] = field(default_factory=dict)

    @property
    def is_population_capped_soon(self) -> bool:
        if self.population_current is None or self.population_cap is None:
            return False
        return self.population_cap - self.population_current <= config.HOUSE_POP_BUFFER


class SmoothedValue:
    def __init__(self, history_size: int) -> None:
        self.values: Deque[int] = deque(maxlen=history_size)

    def update(self, value: int) -> int:
        if self.values:
            last = self.values[-1]
            jump_limit = max(25, int(max(last, 1) * config.OCR_MAX_JUMP_RATIO))
            if abs(value - last) > jump_limit:
                logger.debug("OCR jump rejected: last=%s new=%s limit=%s", last, value, jump_limit)
                return int(median(self.values))

        self.values.append(value)
        return int(median(self.values))


class ResourceReader:
    def __init__(self) -> None:
        pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
        self.smoothers = {
            "food": SmoothedValue(config.OCR_HISTORY_SIZE),
            "wood": SmoothedValue(config.OCR_HISTORY_SIZE),
            "gold": SmoothedValue(config.OCR_HISTORY_SIZE),
            "stone": SmoothedValue(config.OCR_HISTORY_SIZE),
            "population_current": SmoothedValue(config.OCR_HISTORY_SIZE),
            "population_cap": SmoothedValue(config.OCR_HISTORY_SIZE),
        }

    def read_resources(self) -> ResourceSnapshot:
        snapshot = ResourceSnapshot()

        for name in ("food", "wood", "gold", "stone"):
            value, reason = self._read_single_number(name)
            if value is None:
                snapshot.failures[name] = reason or "unknown OCR failure"
            else:
                setattr(snapshot, name, value)

        current, cap, reason = self._read_population()
        if current is None or cap is None:
            snapshot.failures["population"] = reason or "population OCR failure"
        else:
            snapshot.population_current = current
            snapshot.population_cap = cap

        return snapshot

    def _read_single_number(self, name: str) -> tuple[Optional[int], Optional[str]]:
        region = getattr(config.RESOURCE_REGIONS, name)
        image = capture_screen(region)
        text, confidence = self._ocr_text(image)
        digits = re.sub(r"\D", "", text)

        if confidence < config.OCR_MIN_CONFIDENCE:
            return None, f"low OCR confidence: text={text!r}, confidence={confidence:.1f}"
        if not digits:
            return None, f"no digits found in OCR text={text!r}, confidence={confidence:.1f}"

        value = int(digits)
        if not self._in_sanity_range(name, value):
            return None, f"value out of sanity range: {value}"

        return self.smoothers[name].update(value), None

    def _read_population(self) -> tuple[Optional[int], Optional[int], Optional[str]]:
        image = capture_screen(config.RESOURCE_REGIONS.population)
        text, confidence = self._ocr_text(image)

        if confidence < config.OCR_MIN_CONFIDENCE:
            return None, None, f"low OCR confidence: text={text!r}, confidence={confidence:.1f}"

        match = re.search(r"(\d+)\s*/\s*(\d+)", text)

        if not match:
            numbers = re.findall(r"\d+", text)
            if len(numbers) >= 2:
                current, cap = int(numbers[0]), int(numbers[1])
            else:
                return None, None, f"cannot parse population from text={text!r}, confidence={confidence:.1f}"
        else:
            current, cap = int(match.group(1)), int(match.group(2))

        if not self._in_sanity_range("population_current", current):
            return None, None, f"population current out of range: {current}"
        if not self._in_sanity_range("population_cap", cap):
            return None, None, f"population cap out of range: {cap}"
        if current > cap:
            return None, None, f"population current exceeds cap: {current}/{cap}"

        current = self.smoothers["population_current"].update(current)
        cap = self.smoothers["population_cap"].update(cap)
        return current, cap, None

    def _ocr_text(self, image: np.ndarray) -> tuple[str, float]:
        processed = preprocess_for_ocr(image)
        data = pytesseract.image_to_data(
            processed,
            config=config.TESSERACT_CONFIG,
            output_type=pytesseract.Output.DICT,
        )
        words: list[str] = []
        confidences: list[float] = []

        for text, conf in zip(data.get("text", []), data.get("conf", [])):
            text = text.strip()
            try:
                confidence = float(conf)
            except ValueError:
                confidence = -1

            if text:
                words.append(text)
            if confidence >= 0:
                confidences.append(confidence)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return "".join(words), avg_confidence

    def _in_sanity_range(self, key: str, value: int) -> bool:
        low, high = config.RESOURCE_SANITY_LIMITS[key]
        return low <= value <= high


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    denoised = cv2.GaussianBlur(scaled, (3, 3), 0)
    _, threshold = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return threshold
