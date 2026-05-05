"""Application entry point."""

from __future__ import annotations

import pygame

from tower_defense_runner.game import Game


def main() -> None:
    pygame.init()
    try:
        Game().run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
