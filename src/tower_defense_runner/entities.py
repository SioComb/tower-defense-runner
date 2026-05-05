"""Drawable and updateable game entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import pygame

from tower_defense_runner import settings


Route = Sequence[tuple[float, float]]


@dataclass
class Enemy:
    route: Route
    max_hp: float
    hp: float
    speed: float
    reward: int
    radius: int
    damage_to_base: int
    is_boss: bool = False
    position: pygame.Vector2 = field(init=False)
    waypoint_index: int = field(default=1, init=False)
    alive: bool = True
    reached_base: bool = False

    def __post_init__(self) -> None:
        self.position = pygame.Vector2(self.route[0])

    def update(self, dt: float) -> bool:
        if not self.alive:
            return False

        remaining = self.speed * dt
        while remaining > 0.0 and self.waypoint_index < len(self.route):
            target = pygame.Vector2(self.route[self.waypoint_index])
            offset = target - self.position
            distance = offset.length()
            if distance <= 0.001:
                self.waypoint_index += 1
                continue

            if distance <= remaining:
                self.position = target
                remaining -= distance
                self.waypoint_index += 1
            else:
                self.position += offset.normalize() * remaining
                remaining = 0.0

        if self.waypoint_index >= len(self.route):
            self.reached_base = True
            self.alive = False
            return True
        return False

    def take_damage(self, amount: float) -> bool:
        if not self.alive:
            return False
        self.hp = max(0.0, self.hp - amount)
        if self.hp <= 0.0:
            self.alive = False
            return True
        return False

    def draw(self, screen: pygame.Surface) -> None:
        color = settings.BOSS_COLOR if self.is_boss else settings.ENEMY_COLOR
        center = (round(self.position.x), round(self.position.y))
        pygame.draw.circle(screen, color, center, self.radius)
        pygame.draw.circle(screen, (45, 24, 32), center, self.radius, 2)

        if self.is_boss:
            self._draw_health_bar(screen, width=72, y_offset=self.radius + 15)

    def _draw_health_bar(self, screen: pygame.Surface, width: int, y_offset: int) -> None:
        ratio = 0.0 if self.max_hp <= 0.0 else self.hp / self.max_hp
        bar_rect = pygame.Rect(0, 0, width, 8)
        bar_rect.center = (round(self.position.x), round(self.position.y - y_offset))
        fill_rect = bar_rect.copy()
        fill_rect.width = round(bar_rect.width * ratio)
        pygame.draw.rect(screen, settings.HEALTH_BACK_COLOR, bar_rect, border_radius=3)
        pygame.draw.rect(screen, settings.HEALTH_FRONT_COLOR, fill_rect, border_radius=3)
        pygame.draw.rect(screen, (20, 20, 20), bar_rect, 1, border_radius=3)


@dataclass
class Gate:
    center: pygame.Vector2
    label: str
    effect: str
    value: int
    max_hp: float
    hp: float
    alive: bool = True

    @property
    def rect(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, *settings.GATE_SIZE)
        rect.center = (round(self.center.x), round(self.center.y))
        return rect

    def take_damage(self, amount: float) -> bool:
        if not self.alive:
            return False
        self.hp = max(0.0, self.hp - amount)
        if self.hp <= 0.0:
            self.alive = False
            return True
        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        rect = self.rect
        ratio = 0.0 if self.max_hp <= 0.0 else self.hp / self.max_hp
        color = settings.GATE_COLOR if ratio > 0.35 else settings.GATE_DAMAGED_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=7)
        pygame.draw.rect(screen, (18, 78, 65), rect, 3, border_radius=7)
        label = font.render(self.label, True, settings.TEXT_COLOR)
        screen.blit(label, label.get_rect(center=rect.center))
        draw_rect_health_bar(screen, rect, ratio)


@dataclass
class WeaponCrate:
    center: pygame.Vector2
    max_hp: float
    hp: float
    alive: bool = True

    @property
    def rect(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, *settings.CRATE_SIZE)
        rect.center = (round(self.center.x), round(self.center.y))
        return rect

    def take_damage(self, amount: float) -> bool:
        if not self.alive:
            return False
        self.hp = max(0.0, self.hp - amount)
        if self.hp <= 0.0:
            self.alive = False
            return True
        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        rect = self.rect
        ratio = 0.0 if self.max_hp <= 0.0 else self.hp / self.max_hp
        color = settings.CRATE_COLOR if ratio > 0.35 else settings.CRATE_DAMAGED_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, (82, 51, 25), rect, 3, border_radius=6)
        pygame.draw.line(screen, (120, 74, 35), rect.midleft, rect.midright, 3)
        label = font.render("LV+", True, settings.TEXT_COLOR)
        screen.blit(label, label.get_rect(center=rect.center))
        draw_rect_health_bar(screen, rect, ratio)


@dataclass
class Bullet:
    position: pygame.Vector2
    velocity: pygame.Vector2
    damage: float
    radius: int = settings.BULLET_RADIUS
    lifetime: float = settings.BULLET_LIFETIME
    alive: bool = True

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        self.position += self.velocity * dt
        self.lifetime -= dt
        if (
            self.lifetime <= 0.0
            or self.position.x < -30
            or self.position.x > settings.SCREEN_WIDTH + 30
            or self.position.y < -30
            or self.position.y > settings.SCREEN_HEIGHT + 30
        ):
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(
            screen,
            settings.BULLET_COLOR,
            (round(self.position.x), round(self.position.y)),
            self.radius,
        )


def draw_rect_health_bar(screen: pygame.Surface, owner_rect: pygame.Rect, ratio: float) -> None:
    bar_rect = pygame.Rect(owner_rect.left, owner_rect.top - 10, owner_rect.width, 6)
    fill_rect = bar_rect.copy()
    fill_rect.width = round(bar_rect.width * max(0.0, min(1.0, ratio)))
    pygame.draw.rect(screen, settings.HEALTH_BACK_COLOR, bar_rect, border_radius=3)
    pygame.draw.rect(screen, settings.HEALTH_FRONT_COLOR, fill_rect, border_radius=3)
