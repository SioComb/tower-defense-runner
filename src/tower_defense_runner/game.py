"""Main game orchestration."""

from __future__ import annotations

import os
from typing import TypeAlias

import pygame

from tower_defense_runner import settings
from tower_defense_runner.entities import Bullet, Enemy, Gate, WeaponCrate
from tower_defense_runner.ui import GameUI, HudData
from tower_defense_runner.weapons import WeaponSystem
from tower_defense_runner.waves import WaveManager


Target: TypeAlias = Enemy | Gate | WeaponCrate


class Game:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode(settings.SCREEN_SIZE)
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.ui = GameUI()
        self.running = True
        self.reset()

    def reset(self) -> None:
        self.base_hp = settings.BASE_MAX_HP
        self.score = 0
        self.soldier_count = settings.INITIAL_SOLDIER_COUNT
        self.weapon = WeaponSystem()
        self.wave_manager = WaveManager()
        self.enemies: list[Enemy] = []
        self.bullets: list[Bullet] = []
        self.gates: list[Gate] = []
        self.crates: list[WeaponCrate] = []
        self.paused = False
        self.game_over = False
        self.fire_timer = 0.0
        self.message = "Destroy gates and crates to scale up"
        self.message_timer = settings.MESSAGE_DURATION
        self._setup_wave_objects()

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

        for spawn_kind in self.wave_manager.update(dt):
            self._spawn_enemy(spawn_kind)

        self._update_enemies(dt)
        self._update_weapons(dt)
        self._update_bullets(dt)
        self._cleanup_entities()

        if self.base_hp <= 0:
            self.base_hp = 0
            self.game_over = True
            self.paused = False
            return

        if self.wave_manager.should_advance(self._active_enemy_count()):
            self.wave_manager.advance_wave()
            self._setup_wave_objects()
            wave = self.wave_manager.current_wave
            self._show_message(f"Wave {wave} started")

    def _update_message(self, dt: float) -> None:
        if self.message_timer <= 0.0:
            self.message = ""
            return
        self.message_timer -= dt
        if self.message_timer <= 0.0:
            self.message = ""

    def _spawn_enemy(self, spawn_kind: str) -> None:
        config = self.wave_manager.config
        if spawn_kind == "boss":
            enemy = Enemy(
                route=settings.PATH_POINTS,
                max_hp=config.boss_hp,
                hp=config.boss_hp,
                speed=config.boss_speed,
                reward=config.boss_reward,
                radius=settings.BOSS_RADIUS,
                damage_to_base=settings.BOSS_BASE_DAMAGE,
                is_boss=True,
            )
            self._show_message("Boss incoming")
        else:
            enemy = Enemy(
                route=settings.PATH_POINTS,
                max_hp=config.enemy_hp,
                hp=config.enemy_hp,
                speed=config.enemy_speed,
                reward=config.enemy_reward,
                radius=settings.ENEMY_RADIUS,
                damage_to_base=settings.ENEMY_BASE_DAMAGE,
            )
        self.enemies.append(enemy)

    def _update_enemies(self, dt: float) -> None:
        for enemy in self.enemies:
            if enemy.update(dt):
                self.base_hp -= enemy.damage_to_base
                label = "Boss" if enemy.is_boss else "Enemy"
                self._show_message(f"{label} hit the base")

    def _update_weapons(self, dt: float) -> None:
        self.fire_timer -= dt
        stats = self.weapon.stats()
        if self.fire_timer > 0.0:
            return

        self._fire_volley(stats.damage, stats.bullet_speed)
        self.fire_timer = stats.fire_interval

    def _fire_volley(self, damage: float, bullet_speed: float) -> None:
        targets = self._targetable_objects()
        if not targets or len(self.bullets) >= settings.MAX_ACTIVE_BULLETS:
            return

        open_slots = settings.MAX_ACTIVE_BULLETS - len(self.bullets)
        for soldier_pos in self._soldier_positions()[:open_slots]:
            target = self._nearest_target(soldier_pos, targets)
            if target is None:
                continue
            aim_point = self._target_position(target)
            direction = aim_point - soldier_pos
            if direction.length_squared() < 1.0:
                continue
            velocity = direction.normalize() * bullet_speed
            self.bullets.append(Bullet(position=pygame.Vector2(soldier_pos), velocity=velocity, damage=damage))

    def _update_bullets(self, dt: float) -> None:
        for bullet in self.bullets:
            bullet.update(dt)
            if not bullet.alive:
                continue
            target = self._bullet_hit_target(bullet)
            if target is None:
                continue
            destroyed = target.take_damage(bullet.damage)
            bullet.alive = False
            if destroyed:
                self._handle_destroyed_target(target)

    def _handle_destroyed_target(self, target: Target) -> None:
        if isinstance(target, Enemy):
            self.score += target.reward
            if target.is_boss:
                self._show_message(f"Boss defeated +{target.reward}")
            return

        if isinstance(target, Gate):
            old_count = self.soldier_count
            if target.effect == "add":
                self.soldier_count += target.value
            elif target.effect == "multiply":
                self.soldier_count *= target.value
            self.soldier_count = min(settings.MAX_SOLDIERS, self.soldier_count)
            gained = self.soldier_count - old_count
            self.score += max(0, gained) * 2
            self._show_message(f"Gate {target.label}: soldiers +{max(0, gained)}")
            return

        if isinstance(target, WeaponCrate):
            upgrade_name = self.weapon.upgrade()
            self.score += settings.CRATE_SCORE_REWARD
            self._show_message(f"Weapon Lv {self.weapon.level}: {upgrade_name}")

    def _bullet_hit_target(self, bullet: Bullet) -> Target | None:
        hit_targets: list[tuple[float, Target]] = []
        for target in self._targetable_objects():
            if isinstance(target, Enemy):
                distance = bullet.position.distance_to(target.position)
                if distance <= bullet.radius + target.radius:
                    hit_targets.append((distance, target))
            else:
                hit_rect = target.rect.inflate(bullet.radius * 2, bullet.radius * 2)
                if hit_rect.collidepoint(bullet.position.x, bullet.position.y):
                    hit_targets.append((bullet.position.distance_to(self._target_position(target)), target))

        if not hit_targets:
            return None
        return min(hit_targets, key=lambda item: item[0])[1]

    def _cleanup_entities(self) -> None:
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        self.gates = [gate for gate in self.gates if gate.alive]
        self.crates = [crate for crate in self.crates if crate.alive]
        self.bullets = [bullet for bullet in self.bullets if bullet.alive]

    def _active_enemy_count(self) -> int:
        return sum(1 for enemy in self.enemies if enemy.alive)

    def _setup_wave_objects(self) -> None:
        self.gates.clear()
        self.crates.clear()
        wave = self.wave_manager.current_wave
        gate_hp = settings.GATE_BASE_HP + (wave - 1) * settings.GATE_HP_GROWTH
        effect_pair = settings.GATE_EFFECT_ROTATION[(wave - 1) % len(settings.GATE_EFFECT_ROTATION)]

        for route_position, (label, effect, value) in zip(settings.GATE_ROUTE_POSITIONS, effect_pair):
            self.gates.append(
                Gate(
                    center=self._point_on_route(route_position),
                    label=label,
                    effect=effect,
                    value=value,
                    max_hp=gate_hp,
                    hp=gate_hp,
                )
            )

        crate_hp = settings.CRATE_BASE_HP + (wave - 1) * settings.CRATE_HP_GROWTH
        self.crates.append(
            WeaponCrate(
                center=self._point_on_route(settings.CRATE_ROUTE_POSITION),
                max_hp=crate_hp,
                hp=crate_hp,
            )
        )

    def _point_on_route(self, route_fraction: float) -> pygame.Vector2:
        route_fraction = max(0.0, min(1.0, route_fraction))
        segments: list[tuple[pygame.Vector2, pygame.Vector2, float]] = []
        total_length = 0.0
        points = [pygame.Vector2(point) for point in settings.PATH_POINTS]
        for start, end in zip(points, points[1:]):
            length = start.distance_to(end)
            segments.append((start, end, length))
            total_length += length

        target_distance = total_length * route_fraction
        walked = 0.0
        for start, end, length in segments:
            if walked + length >= target_distance:
                local = 0.0 if length <= 0.0 else (target_distance - walked) / length
                return start.lerp(end, local)
            walked += length
        return points[-1]

    def _targetable_objects(self) -> list[Target]:
        targets: list[Target] = []
        targets.extend(enemy for enemy in self.enemies if enemy.alive)
        targets.extend(gate for gate in self.gates if gate.alive)
        targets.extend(crate for crate in self.crates if crate.alive)
        return targets

    def _nearest_target(self, origin: pygame.Vector2, targets: list[Target]) -> Target | None:
        if not targets:
            return None
        return min(targets, key=lambda target: origin.distance_squared_to(self._target_position(target)))

    def _target_position(self, target: Target) -> pygame.Vector2:
        if isinstance(target, Enemy):
            return pygame.Vector2(target.position)
        return pygame.Vector2(target.rect.center)

    def _soldier_positions(self) -> list[pygame.Vector2]:
        positions: list[pygame.Vector2] = []
        for index in range(self.soldier_count):
            col = index % settings.SOLDIER_COLUMNS
            row = index // settings.SOLDIER_COLUMNS
            x = settings.SOLDIER_START_X + col * settings.SOLDIER_SPACING_X
            y = settings.SOLDIER_START_Y + row * settings.SOLDIER_SPACING_Y
            if y > settings.SCREEN_HEIGHT - 18:
                break
            positions.append(pygame.Vector2(x, y))
        return positions

    def _show_message(self, message: str) -> None:
        self.message = message
        self.message_timer = settings.MESSAGE_DURATION

    def _draw(self) -> None:
        self.screen.fill(settings.BACKGROUND_COLOR)
        self._draw_route()
        self._draw_base_and_spawn()
        self._draw_soldiers()

        for gate in self.gates:
            gate.draw(self.screen, self.ui.font_title)
        for crate in self.crates:
            crate.draw(self.screen, self.ui.font)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)

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

    def _draw_route(self) -> None:
        points = [(round(x), round(y)) for x, y in settings.PATH_POINTS]
        pygame.draw.lines(self.screen, settings.ROUTE_EDGE_COLOR, False, points, settings.ROUTE_WIDTH + 8)
        pygame.draw.lines(self.screen, settings.ROUTE_COLOR, False, points, settings.ROUTE_WIDTH)
        for point in points:
            pygame.draw.circle(self.screen, settings.ROUTE_COLOR, point, settings.ROUTE_WIDTH // 2)
            pygame.draw.circle(self.screen, settings.ROUTE_EDGE_COLOR, point, settings.ROUTE_WIDTH // 2, 3)

    def _draw_base_and_spawn(self) -> None:
        start = pygame.Vector2(settings.PATH_POINTS[0])
        end = pygame.Vector2(settings.PATH_POINTS[-1])

        spawn_rect = pygame.Rect(0, 0, 58, 58)
        spawn_rect.center = (round(start.x), round(start.y))
        pygame.draw.rect(self.screen, settings.SPAWN_COLOR, spawn_rect, border_radius=8)
        pygame.draw.rect(self.screen, (89, 81, 39), spawn_rect, 3, border_radius=8)

        hp_ratio = self.base_hp / settings.BASE_MAX_HP
        base_color = settings.BASE_COLOR if hp_ratio > 0.3 else settings.BASE_DANGER_COLOR
        base_rect = pygame.Rect(0, 0, 74, 74)
        base_rect.center = (round(end.x + 28), round(end.y))
        pygame.draw.rect(self.screen, base_color, base_rect, border_radius=8)
        pygame.draw.rect(self.screen, (20, 50, 34), base_rect, 3, border_radius=8)

        font = self.ui.font_small
        spawn_text = font.render("SPAWN", True, (45, 38, 18))
        base_text = font.render("BASE", True, settings.TEXT_COLOR)
        self.screen.blit(spawn_text, spawn_text.get_rect(center=spawn_rect.center))
        self.screen.blit(base_text, base_text.get_rect(center=base_rect.center))

    def _draw_soldiers(self) -> None:
        barracks_rect = pygame.Rect(28, 594, 442, 106)
        pygame.draw.rect(self.screen, (22, 44, 59), barracks_rect, border_radius=8)
        pygame.draw.rect(self.screen, (49, 95, 119), barracks_rect, 2, border_radius=8)
        label = self.ui.font_small.render("SOLDIER SQUAD", True, settings.MUTED_TEXT_COLOR)
        self.screen.blit(label, (barracks_rect.left + 12, barracks_rect.top + 8))

        for pos in self._soldier_positions():
            center = (round(pos.x), round(pos.y))
            pygame.draw.circle(self.screen, settings.SOLDIER_COLOR, center, settings.SOLDIER_RADIUS)
            pygame.draw.circle(self.screen, settings.SOLDIER_OUTLINE_COLOR, center, settings.SOLDIER_RADIUS, 1)

        if self.soldier_count >= settings.MAX_SOLDIERS:
            cap_text = self.ui.font_small.render("MAX", True, (255, 235, 142))
            self.screen.blit(cap_text, (barracks_rect.right - 54, barracks_rect.top + 8))
