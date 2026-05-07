from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from dataclasses import dataclass

import pyautogui

import config


INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002

VK_CODES = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
    "esc": 0x1B,
    "space": 0x20,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "period": 0xBE,
    "comma": 0xBC,
}

for index, letter in enumerate("abcdefghijklmnopqrstuvwxyz", start=0x41):
    VK_CODES[letter] = index

for number in range(10):
    VK_CODES[str(number)] = 0x30 + number


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


@dataclass
class InputDriver:
    use_send_input: bool = True

    def press(self, key: str) -> None:
        if self.use_send_input:
            try:
                self.key_down(key)
                time.sleep(config.KEY_HOLD_SECONDS)
                self.key_up(key)
                return
            except Exception:
                pass

        pyautogui.press(_pyautogui_key(key))

    def hotkey(self, *keys: str) -> None:
        if not keys:
            return

        if self.use_send_input:
            try:
                for key in keys:
                    self.key_down(key)
                    time.sleep(0.01)
                time.sleep(config.KEY_HOLD_SECONDS)
                for key in reversed(keys):
                    self.key_up(key)
                    time.sleep(0.01)
                return
            except Exception:
                pass

        pyautogui.hotkey(*[_pyautogui_key(key) for key in keys])

    def click(self, x: int, y: int) -> None:
        pyautogui.moveTo(x, y, duration=config.MOUSE_MOVE_SECONDS)
        pyautogui.click()

    def key_down(self, key: str) -> None:
        self._send_key(key, 0)

    def key_up(self, key: str) -> None:
        self._send_key(key, KEYEVENTF_KEYUP)

    def _send_key(self, key: str, flags: int) -> None:
        vk = VK_CODES[key.lower()]
        event = INPUT(
            type=INPUT_KEYBOARD,
            union=INPUT_UNION(ki=KEYBDINPUT(vk, 0, flags, 0, None)),
        )
        sent = ctypes.windll.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event))
        if sent != 1:
            raise OSError("SendInput failed")


def _pyautogui_key(key: str) -> str:
    if key == "period":
        return "."
    if key == "esc":
        return "escape"
    return key
