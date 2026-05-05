"""Drawable and updateable game entities."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from tower_defense_runner import settings


@dataclass
class Enemy:
    position: pygame.Vector2
    max_hp: float
    hp: float
    speed: float
    reward: int
    radius: int
    damage_to_base: int
    is_boss: bool = False
    alive: bool = True

    def update(self, dt: float) -> bool:
        if not self.alive:
            return False

        self.position.y += self.speed * dt
        if self.position.y + self.radius >= settings.BASE_LINE_Y:
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
            self._draw_health_bar(screen, width=86, y_offset=self.radius + 15)

    def _draw_health_bar(self, screen: pygame.Surface, width: int, y_offset: int) -> None:
        ratio = 0.0 if self.max_hp <= 0.0 else self.hp / self.max_hp
        bar_rect = pygame.Rect(0, 0, width, 8)
        bar_rect.center = (round(self.position.x), round(self.position.y - y_offset))
        draw_bar(screen, bar_rect, ratio, settings.HEALTH_BACK_COLOR, settings.HEALTH_FRONT_COLOR)


@dataclass
class Gate:
    center: pygame.Vector2
    label: str
    effect: str
    value: int
    charge_required: int
    speed: float
    charge: int = 0
    alive: bool = True

    @property
    def rect(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, *settings.GATE_SIZE)
        rect.center = (round(self.center.x), round(self.center.y))
        return rect

    def update(self, dt: float) -> bool:
        if not self.alive:
            return False
        self.center.y += self.speed * dt
        if self.rect.bottom >= settings.BASE_LINE_Y:
            self.alive = False
            return True
        return False

    def add_charge(self, amount: int) -> bool:
        if not self.alive:
            return False
        self.charge = min(self.charge_required, self.charge + amount)
        if self.charge >= self.charge_required:
            self.alive = False
            return True
        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        rect = self.rect
        ratio = 0.0 if self.charge_required <= 0 else self.charge / self.charge_required
        color = settings.GATE_ACTIVE_COLOR if ratio >= 0.7 else settings.GATE_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=7)
        pygame.draw.rect(screen, (18, 78, 65), rect, 3, border_radius=7)

        label = font.render(self.label, True, settings.TEXT_COLOR)
        charge = small_font.render(f"Charge: {self.charge} / {self.charge_required}", True, settings.TEXT_COLOR)
        screen.blit(label, label.get_rect(center=(rect.centerx, rect.centery - 10)))
        screen.blit(charge, charge.get_rect(center=(rect.centerx, rect.centery + 17)))

        bar_rect = pygame.Rect(rect.left + 8, rect.bottom + 5, rect.width - 16, 6)
        draw_bar(screen, bar_rect, ratio, settings.CHARGE_BACK_COLOR, settings.CHARGE_FRONT_COLOR)


@dataclass
class WeaponCrate:
    center: pygame.Vector2
    max_hp: float
    hp: float
    speed: float
    alive: bool = True

    @property
    def rect(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, *settings.CRATE_SIZE)
        rect.center = (round(self.center.x), round(self.center.y))
        return rect

    def update(self, dt: float) -> bool:
        if not self.alive:
            return False
        self.center.y += self.speed * dt
        if self.rect.bottom >= settings.BASE_LINE_Y:
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

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        rect = self.rect
        ratio = 0.0 if self.max_hp <= 0.0 else self.hp / self.max_hp
        color = settings.CRATE_COLOR if ratio > 0.35 else settings.CRATE_DAMAGED_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, (82, 51, 25), rect, 3, border_radius=6)
        pygame.draw.line(screen, (120, 74, 35), rect.midleft, rect.midright, 3)

        label = font.render("LV+", True, settings.TEXT_COLOR)
        screen.blit(label, label.get_rect(center=rect.center))

        bar_rect = pygame.Rect(rect.left, rect.top - 10, rect.width, 6)
        draw_bar(screen, bar_rect, ratio, settings.HEALTH_BACK_COLOR, settings.HEALTH_FRONT_COLOR)


@dataclass
class Bullet:
    position: pygame.Vector2
    speed: float
    damage: float
    radius: int = settings.BULLET_RADIUS
    alive: bool = True

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        self.position.y -= self.speed * dt
        if self.position.y + self.radius < 0:
            self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(
            screen,
            settings.BULLET_COLOR,
            (round(self.position.x), round(self.position.y)),
            self.radius,
        )


def draw_bar(
    screen: pygame.Surface,
    bar_rect: pygame.Rect,
    ratio: float,
    back_color: tuple[int, int, int],
    front_color: tuple[int, int, int],
) -> None:
    ratio = max(0.0, min(1.0, ratio))
    fill_rect = bar_rect.copy()
    fill_rect.width = round(bar_rect.width * ratio)
    pygame.draw.rect(screen, back_color, bar_rect, border_radius=3)
    pygame.draw.rect(screen, front_color, fill_rect, border_radius=3)
    pygame.draw.rect(screen, (20, 20, 20), bar_rect, 1, border_radius=3)
