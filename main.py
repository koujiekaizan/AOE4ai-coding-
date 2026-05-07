from __future__ import annotations

import logging

import config
from aoe4_env import Aoe4Env


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
        ],
    )


def main() -> None:
    setup_logging()
    Aoe4Env().run()


if __name__ == "__main__":
    main()
