"""Wave scaling and spawn scheduling."""

from __future__ import annotations

from dataclasses import dataclass

from tower_defense_runner import settings


@dataclass(frozen=True)
class WaveConfig:
    wave_number: int
    normal_enemy_count: int
    spawn_interval: float
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
    if is_boss_wave:
        normal_count = max(6, normal_count - 5)

    return WaveConfig(
        wave_number=wave_number,
        normal_enemy_count=normal_count,
        spawn_interval=max(
            settings.WAVE_MIN_SPAWN_INTERVAL,
            settings.WAVE_BASE_SPAWN_INTERVAL - wave_index * 0.025,
        ),
        enemy_hp=settings.ENEMY_BASE_HP + wave_index * 8.0,
        enemy_speed=settings.ENEMY_BASE_SPEED + wave_index * 2.5,
        enemy_reward=settings.ENEMY_BASE_REWARD + wave_index * 2,
        is_boss_wave=is_boss_wave,
        boss_hp=settings.BOSS_BASE_HP + wave_index * 85.0,
        boss_speed=max(28.0, settings.BOSS_BASE_SPEED + wave_index * 1.2),
        boss_reward=settings.BOSS_BASE_REWARD + wave_index * 45,
    )


@dataclass
class WaveManager:
    current_wave: int = 1

    def __post_init__(self) -> None:
        self.config = build_wave_config(self.current_wave)
        self.elapsed = 0.0
        self.spawn_timer = 0.4
        self.normal_spawned = 0
        self.boss_spawned = False

    def update(self, dt: float) -> list[str]:
        self.elapsed += dt
        self.spawn_timer -= dt

        spawn_kinds: list[str] = []
        while self.spawn_timer <= 0.0 and not self.all_spawns_done():
            spawn_kind = self._next_spawn_kind()
            if spawn_kind is None:
                break
            spawn_kinds.append(spawn_kind)
            self.spawn_timer += self.config.spawn_interval
        return spawn_kinds

    def should_advance(self, active_enemy_count: int) -> bool:
        cleared = self.all_spawns_done() and active_enemy_count == 0
        timed_out = self.elapsed >= settings.WAVE_TIME_LIMIT
        return cleared or timed_out

    def advance_wave(self) -> WaveConfig:
        self.current_wave += 1
        self.config = build_wave_config(self.current_wave)
        self.elapsed = 0.0
        self.spawn_timer = 0.5
        self.normal_spawned = 0
        self.boss_spawned = False
        return self.config

    def all_spawns_done(self) -> bool:
        return (
            self.normal_spawned >= self.config.normal_enemy_count
            and (not self.config.is_boss_wave or self.boss_spawned)
        )

    def _next_spawn_kind(self) -> str | None:
        if self.config.is_boss_wave:
            boss_trigger_count = max(1, self.config.normal_enemy_count // 2)
            if not self.boss_spawned and self.normal_spawned >= boss_trigger_count:
                self.boss_spawned = True
                return "boss"

        if self.normal_spawned < self.config.normal_enemy_count:
            self.normal_spawned += 1
            return "enemy"

        if self.config.is_boss_wave and not self.boss_spawned:
            self.boss_spawned = True
            return "boss"

        return None
