"""Wave scaling and spawn scheduling for the lane shooter."""

from __future__ import annotations

from dataclasses import dataclass

from tower_defense_runner import settings


@dataclass(frozen=True)
class WaveConfig:
    wave_number: int
    duration: float
    normal_enemy_count: int
    enemy_spawn_interval: float
    utility_spawn_interval: float
    enemy_hp: float
    enemy_speed: float
    enemy_reward: int
    is_boss_wave: bool
    boss_hp: float
    boss_speed: float
    boss_reward: int

    @property
    def total_spawn_count(self) -> int:
        return self.normal_enemy_count + (1 if self.is_boss_wave else 0)


def build_wave_config(wave_number: int) -> WaveConfig:
    wave_index = max(0, wave_number - 1)
    is_boss_wave = wave_number % settings.BOSS_WAVE_INTERVAL == 0
    normal_count = settings.WAVE_BASE_ENEMY_COUNT + wave_index * settings.WAVE_ENEMY_COUNT_GROWTH

    return WaveConfig(
        wave_number=wave_number,
        duration=settings.WAVE_DURATION,
        normal_enemy_count=normal_count,
        enemy_spawn_interval=max(
            settings.WAVE_MIN_SPAWN_INTERVAL,
            settings.WAVE_BASE_SPAWN_INTERVAL - wave_index * 0.025,
        ),
        utility_spawn_interval=max(
            settings.UTILITY_MIN_SPAWN_INTERVAL,
            settings.UTILITY_BASE_SPAWN_INTERVAL - wave_index * 0.12,
        ),
        enemy_hp=settings.ENEMY_BASE_HP + wave_index * 7.0,
        enemy_speed=settings.ENEMY_BASE_SPEED + wave_index * 3.0,
        enemy_reward=settings.ENEMY_BASE_REWARD + wave_index * 2,
        is_boss_wave=is_boss_wave,
        boss_hp=settings.BOSS_BASE_HP + wave_index * 95.0,
        boss_speed=max(30.0, settings.BOSS_BASE_SPEED + wave_index * 1.0),
        boss_reward=settings.BOSS_BASE_REWARD + wave_index * 50,
    )


@dataclass
class WaveManager:
    current_wave: int = 1

    def __post_init__(self) -> None:
        self.config = build_wave_config(self.current_wave)
        self.elapsed = 0.0
        self.enemy_timer = 0.45
        self.utility_timer = 2.0
        self.normal_spawned = 0
        self.boss_spawned = False

    def update(self, dt: float) -> list[str]:
        self.elapsed += dt
        events: list[str] = []

        self.enemy_timer -= dt
        while self.enemy_timer <= 0.0 and self.normal_spawned < self.config.normal_enemy_count:
            events.append("enemy")
            self.normal_spawned += 1
            self.enemy_timer += self.config.enemy_spawn_interval

        self.utility_timer -= dt
        while self.utility_timer <= 0.0 and self.elapsed < self.config.duration - 1.0:
            events.append("utility")
            self.utility_timer += self.config.utility_spawn_interval

        if (
            self.config.is_boss_wave
            and not self.boss_spawned
            and self.elapsed >= settings.BOSS_SPAWN_TIME
        ):
            events.append("boss")
            self.boss_spawned = True

        return events

    def should_advance(self) -> bool:
        return self.elapsed >= self.config.duration

    def advance_wave(self) -> WaveConfig:
        self.current_wave += 1
        self.config = build_wave_config(self.current_wave)
        self.elapsed = 0.0
        self.enemy_timer = 0.45
        self.utility_timer = 1.5
        self.normal_spawned = 0
        self.boss_spawned = False
        return self.config

    def all_spawns_done(self) -> bool:
        return (
            self.normal_spawned >= self.config.normal_enemy_count
            and (not self.config.is_boss_wave or self.boss_spawned)
        )
