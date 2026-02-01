import arcade
import math
import random

# --------------------
# НАСТРОЙКИ
# --------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Platformer Shooter"

PLAYER_SPEED = 5
JUMP_SPEED = 14
GRAVITY = 0.45

LEVEL_WIDTH = 5200  # увеличили карту для босса

PLAYER_MAX_HP = 20
ENEMY_HP = 10
ENEMY_DAMAGE = 5
BULLET_DAMAGE = 5

ENEMY_SPEED = 0.5
BULLET_SPEED = 10
SHOOT_COOLDOWN = 0.4
SHOOT_ANIM_TIME = 0.15
INVINCIBLE_TIME = 1.0

GUN_OFFSET_X = 45
GUN_HEIGHT_OFFSET = 18


# --------------------
# УТИЛИТА
# --------------------
def make_sprite(width, height, color):
    texture = arcade.make_soft_square_texture(max(width, height), color, 255, 255)
    sprite = arcade.Sprite(texture)
    sprite.width = width
    sprite.height = height
    return sprite


# --------------------
# ИГРОК
# --------------------
class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()

        # Текстуры
        self.texture_right = arcade.load_texture("data/doomguy-Photoroom.png")
        self.texture_left = arcade.load_texture("data/doomguy_left-Photoroom.png")
        self.texture_shoot_right = arcade.load_texture("data/doomguy_shooting-Photoroom.png")
        self.texture_shoot_left = arcade.load_texture("data/doonguy_shooting_left-Photoroom.png")
        self.texture_jump_right = arcade.load_texture("data/doomguy_jump-Photoroom.png")
        self.texture_jump_left = arcade.load_texture("data/doomguy_jump_left-Photoroom.png")

        self.run_textures_right = [
            arcade.load_texture(f"data/file_run animations/run-animation{i}-Photoroom.png") for i in range(1, 11)
        ]
        self.run_textures_left = [
            arcade.load_texture(f"data/file_run_left_animations/run-animation{i}_left-Photoroom.png") for i in
            range(1, 11)
        ]

        self.texture = self.texture_right
        self.scale = 0.8

        self.facing = 1
        self.hp = PLAYER_MAX_HP
        self.invincible_timer = 0

        self.walk_frame = 0
        self.walk_timer = 0
        self.walk_speed = 0.1

        self.is_on_ground = False
        self.is_shooting = False
        self.shoot_anim_timer = 0

        self.bullet_type = "normal"
        self.bullet_count = 0

    def update_texture(self, delta_time):
        if not self.is_on_ground:
            self.texture = self.texture_jump_right if self.facing == 1 else self.texture_jump_left
            return

        if self.is_shooting:
            self.shoot_anim_timer -= delta_time
            if self.shoot_anim_timer <= 0:
                self.is_shooting = False
            self.texture = self.texture_shoot_right if self.facing == 1 else self.texture_shoot_left
            return

        if abs(self.change_x) > 0.1:
            self.walk_timer += delta_time
            if self.walk_timer >= self.walk_speed:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % len(self.run_textures_right)
            self.texture = (
                self.run_textures_right[self.walk_frame] if self.facing == 1 else self.run_textures_left[
                    self.walk_frame]
            )
        else:
            self.walk_frame = 0
            self.texture = self.texture_right if self.facing == 1 else self.texture_left


# --------------------
# ВРАГ
# --------------------
class Enemy(arcade.Sprite):
    def __init__(self, x, y, platforms):
        super().__init__()
        # Основная текстура (стоит)
        self.texture_stand_right = arcade.load_texture("data/enemy_stay-Photoroom.png")
        self.texture_stand_left = arcade.load_texture("data/enemy_stay_left-Photoroom.png")

        # Анимация бега (список текстур)
        self.run_textures_right = [
            arcade.load_texture(f"data/enemy_run/run_anim{i}-Photoroom.png") for i in range(1, 9)
        ]
        self.run_textures_left = [
            arcade.load_texture(f"data/enemy_run_left/run_anim{i}_left-Photoroom.png") for i in range(1, 9)
        ]

        self.texture = self.texture_stand_right
        self.width = 40
        self.height = 80
        self.center_x = x
        self.center_y = y
        self.hp = ENEMY_HP
        self.physics = arcade.PhysicsEnginePlatformer(self, platforms, gravity_constant=GRAVITY)

        self.facing = 1
        self.walk_frame = 0
        self.walk_timer = 0
        self.walk_speed = 0.25  # скорость анимации

    def update_enemy(self, player, delta_time, all_enemies=None):
        self.physics.update()

        # Движение к игроку
        dx = player.center_x - self.center_x
        self.change_x = math.copysign(ENEMY_SPEED, dx) if abs(dx) > 20 else 0
        self.center_x += self.change_x

        # Раздвигаем врагов, чтобы они не слипались
        if all_enemies:
            for other in all_enemies:
                if other == self:
                    continue
                if arcade.check_for_collision(self, other):
                    # Если враги пересекаются, раздвигаем их в стороны
                    overlap = (self.width + other.width) / 2 - abs(self.center_x - other.center_x)
                    if self.center_x < other.center_x:
                        self.center_x -= overlap / 2
                        other.center_x += overlap / 2
                    else:
                        self.center_x += overlap / 2
                        other.center_x -= overlap / 2

        # Определяем направление
        if self.change_x > 0:
            self.facing = 1
        elif self.change_x < 0:
            self.facing = -1

        # Анимация
        if abs(self.change_x) > 0.1:
            self.walk_timer += delta_time
            if self.walk_timer >= self.walk_speed:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % len(self.run_textures_right)
            self.texture = (
                self.run_textures_right[self.walk_frame] if self.facing == 1 else self.run_textures_left[
                    self.walk_frame]
            )
        else:
            self.walk_frame = 0
            self.texture = self.texture_stand_right if self.facing == 1 else self.texture_stand_left


# --------------------
# БОСС
# --------------------
# --------------------
# БОСС
# --------------------
class Boss(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()

        # Текстуры
        self.texture_stand = arcade.load_texture("data/boss-Photoroom.png")  # статичная текстура босса
        self.texture = self.texture_stand  # по умолчанию стоим

        self.width = 100
        self.height = 150

        self.center_x = x
        self.center_y = y
        self.hp = 100
        self.shoot_timer = 0

    def update_boss(self, player, bullets_list):
        distance = abs(player.center_x - self.center_x)
        if distance <= 1300:
            self.shoot_timer -= 1 / 60
            if self.shoot_timer <= 0:
                direction = 1 if player.center_x > self.center_x else -1
                bullet = Bullet(
                    self.center_x + direction * 60,
                    self.center_y + 20,
                    direction,
                    bullet_type="boss"
                )
                bullets_list.append(bullet)
                self.shoot_timer = 1.5  # 1.5 секунды между выстрелами


# --------------------
# ПУЛЯ
# --------------------
class Bullet(arcade.Sprite):
    def __init__(self, x, y, direction, bullet_type="normal"):
        self.is_boss_bullet = False  # 👈 ДОБАВЛЕНО

        if bullet_type == "fast":
            color = arcade.color.BLUE
            speed = BULLET_SPEED * 1.5
            damage = BULLET_DAMAGE

        elif bullet_type == "strong":
            color = arcade.color.YELLOW
            speed = BULLET_SPEED
            damage = BULLET_DAMAGE * 2

        elif bullet_type == "boss":  # 👈 ДОБАВЛЕНО
            color = arcade.color.PURPLE
            speed = BULLET_SPEED
            damage = 10
            self.is_boss_bullet = True

        else:
            color = arcade.color.BLACK
            speed = BULLET_SPEED
            damage = BULLET_DAMAGE

        super().__init__(arcade.make_circle_texture(8, color))
        self.center_x = x
        self.center_y = y
        self.change_x = speed * direction
        self.damage = damage
        self.bullet_type = bullet_type


# --------------------
# ПРЕДМЕТЫ
# --------------------
class Item(arcade.Sprite):
    def __init__(self, x, y, item_type):
        self.item_type = item_type
        color = arcade.color.GREEN if item_type == "hp" else (
            arcade.color.BLUE if item_type == "fast" else arcade.color.YELLOW)
        super().__init__(arcade.make_soft_square_texture(20, color, 255, 255))
        self.center_x = x
        self.center_y = y


# --------------------
# ОКНО ИГРЫ
# --------------------
class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        self.camera = arcade.Camera2D()

        self.player_list = arcade.SpriteList()
        self.platforms = arcade.SpriteList(use_spatial_hash=True)
        self.enemies = arcade.SpriteList()
        self.bullets = arcade.SpriteList()
        self.items = arcade.SpriteList()
        self.boss_list = arcade.SpriteList()

        self.player = None
        self.physics_engine = None
        self.shooting = False
        self.game_over = False
        self.shoot_timer = 0
        self.boss = None
        self.boss_defeated = False
        self.victory = False  # флаг для победы

    def setup(self):
        self.game_over = False
        self.player_list.clear()
        self.platforms.clear()
        self.enemies.clear()
        self.bullets.clear()
        self.items.clear()
        self.boss_list.clear()
        self.boss = None
        self.boss_defeated = False
        self.victory = False

        # Игрок
        self.player = Player()
        self.player.center_x = 200
        self.player.center_y = 120
        self.player_list.append(self.player)

        # Основная земля
        ground = make_sprite(LEVEL_WIDTH, 40, arcade.color.GRAY)
        ground.center_x = LEVEL_WIDTH // 2
        ground.center_y = 20
        self.platforms.append(ground)

        # Малые платформы
        start_x = 500
        for group in range(7):
            for step in range(3):
                p = make_sprite(180, 20, arcade.color.GRAY)
                p.center_x = start_x + group * 550 + step * 260
                p.center_y = 150 + step * 80
                self.platforms.append(p)

        # Враги
        for i in range(20):
            self.enemies.append(Enemy(700 + i * 200, 300, self.platforms))

        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player, self.platforms, GRAVITY)

    def on_draw(self):
        self.clear()

        # ===== МИР =====
        self.camera.use()
        self.platforms.draw()
        self.enemies.draw()
        self.bullets.draw()
        self.items.draw()
        self.player_list.draw()
        self.boss_list.draw()

        # ===== HUD (БЕЗ КАМЕРЫ) =====
        arcade.Camera2D().use()

        arcade.draw_text(
            f"HP: {self.player.hp}",
            10,
            SCREEN_HEIGHT - 30,
            arcade.color.WHITE,
            16
        )

        # Отображение HP босса
        if self.boss:
            arcade.draw_text(
                f"BOSS HP: {self.boss.hp}",
                SCREEN_WIDTH - 150,
                SCREEN_HEIGHT - 30,
                arcade.color.PURPLE,
                16
            )

        if self.game_over:
            arcade.draw_text(
                "GAME OVER",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 + 30,
                arcade.color.RED,
                48,
                anchor_x="center"
            )
            arcade.draw_text(
                "Press R to restart",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 - 30,
                arcade.color.WHITE,
                18,
                anchor_x="center"
            )

        if self.victory:
            arcade.draw_text(
                "YOU WIN!",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 + 30,
                arcade.color.GOLD,
                48,
                anchor_x="center"
            )
            arcade.draw_text(
                "Thanks for playing",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 - 30,
                arcade.color.WHITE,
                18,
                anchor_x="center"
            )

    def on_update(self, delta_time):
        if self.game_over:
            return

        if self.game_over or self.victory:
            return

        self.physics_engine.update()
        self.player.is_on_ground = self.physics_engine.can_jump()
        self.player.update_texture(delta_time)

        self.player.invincible_timer -= delta_time
        self.shoot_timer -= delta_time

        if self.shooting and self.shoot_timer <= 0:
            self.spawn_bullet()
            self.shoot_timer = SHOOT_COOLDOWN

        for enemy in self.enemies:
            enemy.update_enemy(self.player, delta_time)

        # Обновление врагов с анимацией и проверкой столкновений
        for enemy in self.enemies:
            enemy.update_enemy(self.player, delta_time, self.enemies)

        # Спавн босса после убийства всех врагов
        if len(self.enemies) == 0 and self.boss is None and not self.boss_defeated:
            self.boss = Boss(LEVEL_WIDTH - 150, 100)
            self.boss_list.append(self.boss)

        # Босс стреляет
        if self.boss:
            self.boss.update_boss(self.player, self.bullets)

        self.bullets.update()
        self.items.update()

        # Урон врагам
        for bullet in self.bullets:
            hits = arcade.check_for_collision_with_list(bullet, self.enemies)
            for enemy in hits:
                enemy.hp -= bullet.damage
                bullet.remove_from_sprite_lists()
                if enemy.hp <= 0:
                    if random.random() < 0.3:
                        item_type = random.choice(["hp", "fast", "strong"])
                        self.items.append(Item(enemy.center_x, enemy.center_y, item_type))
                    enemy.remove_from_sprite_lists()

            # Урон боссу от пуль игрока (кроме пуль самого босса)
            if self.boss and not bullet.is_boss_bullet and arcade.check_for_collision(bullet, self.boss):
                self.boss.hp -= bullet.damage
                bullet.remove_from_sprite_lists()
                if self.boss.hp <= 0:
                    self.boss.remove_from_sprite_lists()
                    self.boss = None
                    self.boss_defeated = True
                    self.victory = True  # 👈 победа
                    print("BOSS DEFEATED!")

            # Урон игроку от пуль босса
            if bullet.is_boss_bullet and self.player.invincible_timer <= 0:
                if arcade.check_for_collision(bullet, self.player):
                    self.player.hp -= bullet.damage
                    self.player.invincible_timer = INVINCIBLE_TIME
                    bullet.remove_from_sprite_lists()
                    if self.player.hp <= 0:
                        self.game_over = True

        # Урон игроку от столкновения с врагами и боссом
        if self.player.invincible_timer <= 0:
            hits = arcade.check_for_collision_with_list(self.player, self.enemies)
            if self.boss and arcade.check_for_collision(self.player, self.boss):
                self.player.hp -= ENEMY_DAMAGE * 2  # Босс наносит двойной урон
                self.player.invincible_timer = INVINCIBLE_TIME
                if self.player.hp <= 0:
                    self.game_over = True
            elif hits:
                self.player.hp -= ENEMY_DAMAGE
                self.player.invincible_timer = INVINCIBLE_TIME
                if self.player.hp <= 0:
                    self.game_over = True

        # Подбор предметов
        hits = arcade.check_for_collision_with_list(self.player, self.items)
        for item in hits:
            if item.item_type == "hp":
                self.player.hp = min(self.player.hp + 5, PLAYER_MAX_HP)
            else:
                self.player.bullet_type = item.item_type
                self.player.bullet_count = 15
            item.remove_from_sprite_lists()

        for enemy in self.enemies:
            enemy.update_enemy(self.player, delta_time)

        # Камера
        screen_center_x = self.player.center_x - SCREEN_WIDTH / 60
        screen_center_y = self.player.center_y - SCREEN_HEIGHT / 60
        self.camera.position = (screen_center_x, screen_center_y)

    def spawn_bullet(self):
        x = self.player.center_x + GUN_OFFSET_X * self.player.facing
        y = self.player.center_y + GUN_HEIGHT_OFFSET
        self.bullets.append(Bullet(x, y, self.player.facing, self.player.bullet_type))
        self.player.is_shooting = True
        self.player.shoot_anim_timer = SHOOT_ANIM_TIME

        if self.player.bullet_type != "normal":
            self.player.bullet_count -= 1
            if self.player.bullet_count <= 0:
                self.player.bullet_type = "normal"
                self.player.bullet_count = 0

    def on_key_press(self, key, modifiers):
        if self.game_over and key == arcade.key.R:
            self.setup()
            return
        if key == arcade.key.A:
            self.player.change_x = -PLAYER_SPEED
            self.player.facing = -1
        elif key == arcade.key.D:
            self.player.change_x = PLAYER_SPEED
            self.player.facing = 1
        elif key == arcade.key.W:
            if self.physics_engine.can_jump():
                self.player.change_y = JUMP_SPEED
        elif key == arcade.key.SPACE:
            self.shooting = True

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.A, arcade.key.D):
            self.player.change_x = 0
        elif key == arcade.key.SPACE:
            self.shooting = False


# --------------------
# ЗАПУСК
# --------------------
def main():
    window = GameWindow()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()