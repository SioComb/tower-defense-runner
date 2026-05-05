from __future__ import annotations

import pygame

from tower_defense_runner import settings
from tower_defense_runner.entities import Bullet, Enemy, Gate
from tower_defense_runner.weapons import WeaponSystem
from tower_defense_runner.waves import WaveManager, build_wave_config


def test_boss_wave_every_five_waves() -> None:
    assert not build_wave_config(4).is_boss_wave
    assert build_wave_config(5).is_boss_wave
    assert build_wave_config(10).is_boss_wave


def test_weapon_upgrade_improves_stats() -> None:
    weapon = WeaponSystem()
    level_one = weapon.stats()
    weapon.upgrade()
    level_two = weapon.stats()

    assert level_two.level == 2
    assert level_two.damage > level_one.damage
    assert level_two.fire_interval < level_one.fire_interval
    assert level_two.bullet_speed > level_one.bullet_speed


def test_wave_manager_advances_and_resets_spawn_state() -> None:
    manager = WaveManager()
    manager.elapsed = manager.config.duration
    assert manager.should_advance()

    manager.advance_wave()
    assert manager.current_wave == 2
    assert manager.normal_spawned == 0
    assert not manager.boss_spawned


def test_required_window_size() -> None:
    assert settings.SCREEN_SIZE == (1280, 720)


def test_enemy_moves_straight_down_only() -> None:
    enemy = Enemy(
        position=pygame.Vector2(320, 100),
        max_hp=10,
        hp=10,
        speed=50,
        reward=1,
        radius=10,
        damage_to_base=1,
    )

    enemy.update(0.5)
    assert enemy.position.x == 320
    assert enemy.position.y == 125


def test_bullet_moves_straight_up() -> None:
    bullet = Bullet(position=pygame.Vector2(400, 500), speed=200, damage=5)
    bullet.update(0.25)

    assert bullet.position.x == 400
    assert bullet.position.y == 450


def test_gate_uses_charge_instead_of_hp() -> None:
    gate = Gate(
        center=pygame.Vector2(500, 100),
        label="+5",
        effect="add",
        value=5,
        charge_required=3,
        speed=40,
    )

    assert not hasattr(gate, "hp")
    assert not gate.add_charge(1)
    assert not gate.add_charge(1)
    assert gate.add_charge(1)
    assert not gate.alive
