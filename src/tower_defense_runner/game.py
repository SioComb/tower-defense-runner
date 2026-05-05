"""Main game orchestration."""

from __future__ import annotations

import math
import os
import random
from typing import TypeAlias

import pygame

from tower_defense_runner import settings
from tower_defense_runner.entities import Bullet, Enemy, Gate, WeaponCrate
from tower_defense_runner.ui import GameUI, HudData
from tower_defense_runner.weapons import WeaponSystem
from tower_defense_runner.waves import WaveManager


LaneObject: TypeAlias = Enemy | Gate | WeaponCrate


class Game:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode(settings.SCREEN_SIZE)
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.ui = GameUI()
        self.rng = random.Random()
        self.running = True
        self.reset()

    def reset(self) -> None:
        self.base_hp = settings.BASE_MAX_HP
        self.score = 0
        self.soldier_count = settings.INITIAL_SOLDIER_COUNT
        self.squad_x = float(settings.PLAYER_START_X)
        self.weapon = WeaponSystem()
        self.wave_manager = WaveManager()
        self.enemies: list[Enemy] = []
        self.bullets: list[Bullet] = []
        self.gates: list[Gate] = []
        self.crates: list[WeaponCrate] = []
        self.paused = False
        self.game_over = False
        self.fire_timer = 0.0
        self.message = "Move left/right to line up shots"
        self.message_timer = settings.MESSAGE_DURATION

    def run(self) -> None:
        max_frames = int(os.environ.get("TOWER_DEFENSE_RUNNER_MAX_FRAMES", "0"))
        frame_count = 0
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
            frame_count += 1
            if max_frames > 0 and frame_count >= max_frames:
                self.running = False

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE and not self.game_over:
                    self.paused = not self.paused
                elif event.key == pygame.K_r and self.game_over:
                    self.reset()

    def _update(self, dt: float) -> None:
        self._update_message(dt)
        if self.paused or self.game_over:
            return

        self._update_player(dt)

        for event_name in self.wave_manager.update(dt):
            self._spawn_from_event(event_name)

        self._update_weapon(dt)
        self._update_bullets(dt)
        self._update_lane_objects(dt)
        self._cleanup_entities()

        if self.base_hp <= 0:
            self.base_hp = 0
            self.game_over = True
            self.paused = False
            return

        if self.wave_manager.should_advance():
            self.wave_manager.advance_wave()
            self._show_message(f"Wave {self.wave_manager.current_wave} started")

    def _update_message(self, dt: float) -> None:
        if self.message_timer <= 0.0:
            self.message = ""
            return
        self.message_timer -= dt
        if self.message_timer <= 0.0:
            self.message = ""

    def _update_player(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        direction = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction += 1

        self.squad_x += direction * settings.PLAYER_MOVE_SPEED * dt
        self._clamp_squad_to_lane()

    def _clamp_squad_to_lane(self) -> None:
        half_width = self._squad_half_width()
        min_x = settings.LANE_LEFT + half_width
        max_x = settings.LANE_RIGHT - half_width
        self.squad_x = max(min_x, min(max_x, self.squad_x))

    def _spawn_from_event(self, event_name: str) -> None:
        if event_name == "enemy":
            self._spawn_enemy()
        elif event_name == "boss":
            self._spawn_boss()
        elif event_name == "utility":
            if self.rng.random() < 0.58:
                self._spawn_gate()
            else:
                self._spawn_crate()

    def _spawn_enemy(self) -> None:
        config = self.wave_manager.config
        x = self._random_lane_x(settings.ENEMY_RADIUS)
        self.enemies.append(
            Enemy(
                position=pygame.Vector2(x, settings.SPAWN_Y),
                max_hp=config.enemy_hp,
                hp=config.enemy_hp,
                speed=config.enemy_speed,
                reward=config.enemy_reward,
                radius=settings.ENEMY_RADIUS,
                damage_to_base=settings.ENEMY_BASE_DAMAGE,
            )
        )

    def _spawn_boss(self) -> None:
        config = self.wave_manager.config
        x = self._random_lane_x(settings.BOSS_RADIUS)
        self.enemies.append(
            Enemy(
                position=pygame.Vector2(x, settings.SPAWN_Y - settings.BOSS_RADIUS),
                max_hp=config.boss_hp,
                hp=config.boss_hp,
                speed=config.boss_speed,
                reward=config.boss_reward,
                radius=settings.BOSS_RADIUS,
                damage_to_base=settings.BOSS_BASE_DAMAGE,
                is_boss=True,
            )
        )
        self._show_message("Boss incoming")

    def _spawn_gate(self) -> None:
        label, effect, value = self.rng.choice(settings.GATE_EFFECTS)
        width, height = settings.GATE_SIZE
        charge_required = (
            settings.GATE_CHARGE_REQUIRED_BASE
            + (self.wave_manager.current_wave - 1) * settings.GATE_CHARGE_REQUIRED_GROWTH
        )
        if effect == "multiply":
            charge_required += 5

        self.gates.append(
            Gate(
                center=pygame.Vector2(self._random_lane_x(width / 2), settings.SPAWN_Y - height),
                label=label,
                effect=effect,
                value=value,
                charge_required=charge_required,
                speed=settings.GATE_SPEED,
            )
        )

    def _spawn_crate(self) -> None:
        wave = self.wave_manager.current_wave
        width, height = settings.CRATE_SIZE
        hp = settings.CRATE_BASE_HP + (wave - 1) * settings.CRATE_HP_GROWTH
        self.crates.append(
            WeaponCrate(
                center=pygame.Vector2(self._random_lane_x(width / 2), settings.SPAWN_Y - height),
                max_hp=hp,
                hp=hp,
                speed=settings.CRATE_SPEED,
            )
        )

    def _random_lane_x(self, half_width: float) -> float:
        return self.rng.uniform(settings.LANE_LEFT + half_width, settings.LANE_RIGHT - half_width)

    def _update_weapon(self, dt: float) -> None:
        self.fire_timer -= dt
        if self.fire_timer > 0.0:
            return

        stats = self.weapon.stats()
        self._fire_straight_volley(stats.damage, stats.bullet_speed)
        self.fire_timer = stats.fire_interval

    def _fire_straight_volley(self, damage: float, bullet_speed: float) -> None:
        if len(self.bullets) >= settings.MAX_ACTIVE_BULLETS:
            return

        open_slots = settings.MAX_ACTIVE_BULLETS - len(self.bullets)
        for soldier_pos in self._soldier_positions()[:open_slots]:
            bullet_pos = pygame.Vector2(soldier_pos.x, soldier_pos.y - settings.SOLDIER_RADIUS - 4)
            self.bullets.append(Bullet(position=bullet_pos, speed=bullet_speed, damage=damage))

    def _update_bullets(self, dt: float) -> None:
        for bullet in self.bullets:
            bullet.update(dt)
            if not bullet.alive:
                continue
            hit_object = self._bullet_hit_object(bullet)
            if hit_object is None:
                continue
            bullet.alive = False
            self._apply_bullet_hit(hit_object, bullet.damage)

    def _bullet_hit_object(self, bullet: Bullet) -> LaneObject | None:
        for enemy in self.enemies:
            if enemy.alive and bullet.position.distance_to(enemy.position) <= bullet.radius + enemy.radius:
                return enemy

        for gate in self.gates:
            if gate.alive and gate.rect.inflate(bullet.radius * 2, bullet.radius * 2).collidepoint(
                bullet.position.x,
                bullet.position.y,
            ):
                return gate

        for crate in self.crates:
            if crate.alive and crate.rect.inflate(bullet.radius * 2, bullet.radius * 2).collidepoint(
                bullet.position.x,
                bullet.position.y,
            ):
                return crate

        return None

    def _apply_bullet_hit(self, hit_object: LaneObject, damage: float) -> None:
        if isinstance(hit_object, Enemy):
            destroyed = hit_object.take_damage(damage)
            if destroyed:
                self.score += hit_object.reward
                if hit_object.is_boss:
                    self._show_message(f"Boss defeated +{hit_object.reward}")
            return

        if isinstance(hit_object, Gate):
            activated = hit_object.add_charge(settings.GATE_CHARGE_PER_HIT)
            if activated:
                self._activate_gate(hit_object)
            return

        destroyed = hit_object.take_damage(damage)
        if destroyed:
            upgrade_name = self.weapon.upgrade()
            self.score += settings.CRATE_SCORE_REWARD
            self._show_message(f"Weapon Lv {self.weapon.level}: {upgrade_name}")

    def _activate_gate(self, gate: Gate) -> None:
        old_count = self.soldier_count
        if gate.effect == "add":
            self.soldier_count += gate.value
        elif gate.effect == "multiply":
            self.soldier_count *= gate.value
        self.soldier_count = min(settings.MAX_SOLDIERS, self.soldier_count)
        self._clamp_squad_to_lane()

        gained = self.soldier_count - old_count
        self.score += max(0, gained) * 2
        self._show_message(f"Gate {gate.label}: soldiers +{max(0, gained)}")

    def _update_lane_objects(self, dt: float) -> None:
        for enemy in self.enemies:
            if enemy.update(dt):
                self.base_hp -= enemy.damage_to_base
                label = "Boss" if enemy.is_boss else "Enemy"
                self._show_message(f"{label} hit the base")

        for gate in self.gates:
            gate.update(dt)

        for crate in self.crates:
            crate.update(dt)

    def _cleanup_entities(self) -> None:
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        self.gates = [gate for gate in self.gates if gate.alive]
        self.crates = [crate for crate in self.crates if crate.alive]
        self.bullets = [bullet for bullet in self.bullets if bullet.alive]

    def _soldier_positions(self) -> list[pygame.Vector2]:
        visible_count = min(self.soldier_count, settings.MAX_SOLDIERS)
        columns = min(visible_count, settings.SOLDIER_MAX_COLUMNS)
        if columns <= 0:
            return []

        positions: list[pygame.Vector2] = []
        for index in range(visible_count):
            row = index // columns
            col = index % columns
            remaining = visible_count - row * columns
            row_count = min(columns, remaining)
            row_start_x = self.squad_x - (row_count - 1) * settings.SOLDIER_SPACING_X / 2
            x = row_start_x + col * settings.SOLDIER_SPACING_X
            y = settings.SOLDIER_BOTTOM_Y - row * settings.SOLDIER_SPACING_Y
            positions.append(pygame.Vector2(x, y))
        return positions

    def _squad_half_width(self) -> float:
        visible_count = min(self.soldier_count, settings.MAX_SOLDIERS)
        columns = max(1, min(visible_count, settings.SOLDIER_MAX_COLUMNS))
        return (columns - 1) * settings.SOLDIER_SPACING_X / 2 + settings.SOLDIER_RADIUS + 4

    def _show_message(self, message: str) -> None:
        self.message = message
        self.message_timer = settings.MESSAGE_DURATION

    def _draw(self) -> None:
        self.screen.fill(settings.BACKGROUND_COLOR)
        self._draw_lane()
        self._draw_base_area()

        for gate in self.gates:
            gate.draw(self.screen, self.ui.font_title, self.ui.font_small)
        for crate in self.crates:
            crate.draw(self.screen, self.ui.font)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)
        self._draw_soldiers()

        self.ui.draw_hud(
            self.screen,
            HudData(
                base_hp=self.base_hp,
                max_base_hp=settings.BASE_MAX_HP,
                wave=self.wave_manager.current_wave,
                score=self.score,
                soldier_count=self.soldier_count,
                weapon_level=self.weapon.level,
                paused=self.paused,
                game_over=self.game_over,
                message=self.message,
            ),
        )

        if self.paused:
            self.ui.draw_pause(self.screen)
        if self.game_over:
            self.ui.draw_game_over(self.screen, self.score, self.wave_manager.current_wave)

    def _draw_lane(self) -> None:
        lane_rect = pygame.Rect(settings.LANE_LEFT, settings.LANE_TOP, settings.LANE_WIDTH, settings.SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, settings.LANE_COLOR, lane_rect)
        pygame.draw.line(
            self.screen,
            settings.LANE_EDGE_COLOR,
            (settings.LANE_LEFT, settings.LANE_TOP),
            (settings.LANE_LEFT, settings.SCREEN_HEIGHT),
            4,
        )
        pygame.draw.line(
            self.screen,
            settings.LANE_EDGE_COLOR,
            (settings.LANE_RIGHT, settings.LANE_TOP),
            (settings.LANE_RIGHT, settings.SCREEN_HEIGHT),
            4,
        )

        lane_column_count = 5
        for index in range(1, lane_column_count):
            x = settings.LANE_LEFT + settings.LANE_WIDTH * index / lane_column_count
            pygame.draw.line(
                self.screen,
                settings.LANE_MARK_COLOR,
                (round(x), settings.LANE_TOP),
                (round(x), settings.BASE_LINE_Y),
                1,
            )

        for y in range(settings.LANE_TOP + 46, settings.BASE_LINE_Y, 72):
            pygame.draw.line(
                self.screen,
                settings.LANE_MARK_COLOR,
                (settings.LANE_LEFT + 20, y),
                (settings.LANE_RIGHT - 20, y),
                1,
            )

    def _draw_base_area(self) -> None:
        base_rect = pygame.Rect(settings.BASE_AREA_RECT)
        pygame.draw.rect(self.screen, settings.BASE_AREA_COLOR, base_rect)
        pygame.draw.rect(self.screen, settings.BASE_AREA_EDGE_COLOR, base_rect, 3)
        pygame.draw.line(
            self.screen,
            settings.BASE_DANGER_COLOR if self.base_hp <= 30 else settings.BASE_COLOR,
            (settings.LANE_LEFT, settings.BASE_LINE_Y),
            (settings.LANE_RIGHT, settings.BASE_LINE_Y),
            4,
        )

        base_label = self.ui.font_small.render("BASE", True, settings.TEXT_COLOR)
        self.screen.blit(base_label, (settings.LANE_RIGHT - 62, settings.BASE_AREA_TOP + 10))

    def _draw_soldiers(self) -> None:
        for pos in self._soldier_positions():
            center = (round(pos.x), round(pos.y))
            pygame.draw.circle(self.screen, settings.SOLDIER_COLOR, center, settings.SOLDIER_RADIUS)
            pygame.draw.circle(self.screen, settings.SOLDIER_OUTLINE_COLOR, center, settings.SOLDIER_RADIUS, 1)

        if self.soldier_count >= settings.MAX_SOLDIERS:
            cap_text = self.ui.font_small.render("MAX", True, (255, 235, 142))
            self.screen.blit(cap_text, (settings.LANE_LEFT + 14, settings.BASE_AREA_TOP + 10))

        squad_width = math.ceil(self._squad_half_width() * 2)
        guide_rect = pygame.Rect(0, 0, squad_width, 12)
        guide_rect.center = (round(self.squad_x), settings.BASE_LINE_Y + 17)
        pygame.draw.rect(self.screen, (63, 132, 156), guide_rect, border_radius=4)
