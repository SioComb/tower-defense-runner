from __future__ import annotations

from tower_defense_runner import settings
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
    manager.normal_spawned = manager.config.normal_enemy_count
    manager.advance_wave()

    assert manager.current_wave == 2
    assert manager.normal_spawned == 0
    assert not manager.boss_spawned


def test_required_window_size() -> None:
    assert settings.SCREEN_SIZE == (1280, 720)
