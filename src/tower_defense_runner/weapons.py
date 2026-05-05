"""Weapon progression and derived combat stats."""

from __future__ import annotations

from dataclasses import dataclass

from tower_defense_runner import settings


@dataclass(frozen=True)
class WeaponStats:
    level: int
    damage: float
    fire_interval: float
    bullet_speed: float


@dataclass
class WeaponSystem:
    level: int = 1

    def stats(self) -> WeaponStats:
        upgrades = self.level - 1
        return WeaponStats(
            level=self.level,
            damage=settings.BASE_WEAPON_DAMAGE + upgrades * 2.4,
            fire_interval=max(
                settings.MIN_FIRE_INTERVAL,
                settings.BASE_FIRE_INTERVAL - upgrades * 0.028,
            ),
            bullet_speed=settings.BASE_BULLET_SPEED + upgrades * 26.0,
        )

    def upgrade(self) -> str:
        self.level += 1
        upgrade_kind = (self.level - 2) % 3
        if upgrade_kind == 0:
            return "Damage Up"
        if upgrade_kind == 1:
            return "Fire Rate Up"
        return "Bullet Speed Up"
