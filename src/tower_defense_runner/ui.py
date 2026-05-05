"""Heads-up display rendering."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from tower_defense_runner import settings


@dataclass(frozen=True)
class HudData:
    base_hp: int
    max_base_hp: int
    wave: int
    score: int
    soldier_count: int
    weapon_level: int
    paused: bool
    game_over: bool
    message: str


class GameUI:
    def __init__(self) -> None:
        self.font_large = pygame.font.SysFont("arial", 46, bold=True)
        self.font_title = pygame.font.SysFont("arial", 30, bold=True)
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18)

    def draw_hud(self, screen: pygame.Surface, data: HudData) -> None:
        pygame.draw.rect(screen, settings.PANEL_COLOR, pygame.Rect(0, 0, settings.SCREEN_WIDTH, 76))

        hp_text = f"Base HP: {data.base_hp}/{data.max_base_hp}"
        items = (
            hp_text,
            f"Wave: {data.wave}",
            f"Score: {data.score}",
            f"Soldiers: {data.soldier_count}",
            f"Weapon Lv: {data.weapon_level}",
        )

        x = 22
        for item in items:
            surface = self.font.render(item, True, settings.TEXT_COLOR)
            screen.blit(surface, (x, 14))
            x += surface.get_width() + 34

        instructions = "SPACE Pause/Resume   R Restart after Game Over   ESC Quit"
        hint = self.font_small.render(instructions, True, settings.MUTED_TEXT_COLOR)
        screen.blit(hint, (22, 49))

        if data.message:
            message_surface = self.font.render(data.message, True, (255, 235, 142))
            screen.blit(
                message_surface,
                message_surface.get_rect(midtop=(settings.SCREEN_WIDTH // 2, 48)),
            )

    def draw_pause(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface(settings.SCREEN_SIZE, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        screen.blit(overlay, (0, 0))
        title = self.font_large.render("PAUSED", True, settings.TEXT_COLOR)
        hint = self.font.render("Press SPACE to resume", True, settings.MUTED_TEXT_COLOR)
        screen.blit(title, title.get_rect(center=(settings.SCREEN_WIDTH // 2, 320)))
        screen.blit(hint, hint.get_rect(center=(settings.SCREEN_WIDTH // 2, 370)))

    def draw_game_over(self, screen: pygame.Surface, score: int, wave: int) -> None:
        overlay = pygame.Surface(settings.SCREEN_SIZE, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        title = self.font_large.render("GAME OVER", True, (255, 116, 102))
        detail = self.font_title.render(f"Score {score}  |  Wave {wave}", True, settings.TEXT_COLOR)
        hint = self.font.render("Press R to restart or ESC to quit", True, settings.MUTED_TEXT_COLOR)

        screen.blit(title, title.get_rect(center=(settings.SCREEN_WIDTH // 2, 292)))
        screen.blit(detail, detail.get_rect(center=(settings.SCREEN_WIDTH // 2, 350)))
        screen.blit(hint, hint.get_rect(center=(settings.SCREEN_WIDTH // 2, 404)))
