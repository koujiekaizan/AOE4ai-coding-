from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    width: int
    height: int

    @property
    def pyautogui_region(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    @property
    def win32_bbox(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


@dataclass(frozen=True)
class ResourceBarRegions:
    food: Region
    wood: Region
    gold: Region
    stone: Region
    population: Region


SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
GAME_WINDOW_TITLE = "Age of Empires IV"
REQUIRE_FOREGROUND_WINDOW = True

# Adjust these regions after taking one screenshot in your own AoE4 UI scale.
# Format is x, y, width, height. These are fixed screen ROIs, not derived from
# town center position.
RESOURCE_REGIONS = ResourceBarRegions(
    food=Region(80, 18, 88, 28),
    wood=Region(188, 18, 88, 28),
    gold=Region(296, 18, 88, 28),
    stone=Region(404, 18, 88, 28),
    population=Region(520, 18, 105, 28),
)

TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_CONFIG = "--psm 7 -c tessedit_char_whitelist=0123456789/"

LOOP_INTERVAL_SECONDS = 0.35
ACTION_COOLDOWN_SECONDS = 1.25
VILLAGER_TRAIN_COOLDOWN_SECONDS = 2.5
HOUSE_BUILD_COOLDOWN_SECONDS = 8.0
KEY_HOLD_SECONDS = 0.035
MOUSE_MOVE_SECONDS = 0.02

OCR_HISTORY_SIZE = 5
OCR_MAX_JUMP_RATIO = 0.45
OCR_MIN_CONFIDENCE = 35

RESOURCE_SANITY_LIMITS = {
    "food": (0, 50000),
    "wood": (0, 50000),
    "gold": (0, 50000),
    "stone": (0, 50000),
    "population_current": (0, 300),
    "population_cap": (0, 300),
}

PAUSE_KEY = "t"
EXIT_KEY = "esc"

# AoE4 hotkeys vary by user profile. Keep them centralized here.
HOTKEYS = {
    "select_town_center": ["h"],
    "train_villager": ["q"],
    "select_idle_villager": ["period"],
    "select_all_idle_villagers": ["ctrl", "period"],
    "build_menu": ["q"],
    "build_house": ["q"],
    "cancel": ["esc"],
}

DEFAULT_HOUSE_PLACEMENT = (960, 620)

HOUSE_POP_BUFFER = 3
HOUSE_WOOD_COST = 50
VILLAGER_FOOD_COST = 50

LOG_FILE = BASE_DIR / "aoe4_bot.log"
