from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np
import pyautogui
import win32con
import win32gui
import win32ui

import config
from config import Region


logger = logging.getLogger(__name__)


def capture_screen(region: Optional[Region] = None) -> np.ndarray:
    """Return a BGR OpenCV image of the whole screen or a fixed region."""
    try:
        return _capture_screen_win32(region)
    except Exception as exc:
        logger.debug("win32_capture_failed reason=%s; falling back to pyautogui", exc)
        return _capture_screen_pyautogui(region)


def _capture_screen_pyautogui(region: Optional[Region] = None) -> np.ndarray:
    screenshot = pyautogui.screenshot(region=region.pyautogui_region if region else None)
    rgb = np.array(screenshot)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _capture_screen_win32(region: Optional[Region] = None) -> np.ndarray:
    left, top, right, bottom = region.win32_bbox if region else (0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    width = right - left
    height = bottom - top

    hwnd = win32gui.GetDesktopWindow()
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    src_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    mem_dc = src_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(src_dc, width, height)
    mem_dc.SelectObject(bitmap)

    try:
        mem_dc.BitBlt((0, 0), (width, height), src_dc, (left, top), win32con.SRCCOPY)
        raw = bitmap.GetBitmapBits(True)
        image = np.frombuffer(raw, dtype=np.uint8)
        image.shape = (height, width, 4)
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    finally:
        win32gui.DeleteObject(bitmap.GetHandle())
        mem_dc.DeleteDC()
        src_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)


def is_game_foreground() -> bool:
    if not config.REQUIRE_FOREGROUND_WINDOW:
        return True

    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    return config.GAME_WINDOW_TITLE.lower() in title.lower()


def save_debug_capture(path: str, region: Optional[Region] = None) -> None:
    image = capture_screen(region)
    cv2.imwrite(path, image)
