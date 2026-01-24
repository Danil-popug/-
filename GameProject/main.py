import arcade
import math

# --------------------
# НАСТРОЙКИ
# --------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Platformer Shooter"

PLAYER_SPEED = 5
JUMP_SPEED = 14
GRAVITY = 0.45

LEVEL_WIDTH = 2600

ENEMY_SPEED = 0.8
BULLET_SPEED = 10
SHOOT_COOLDOWN = 0.4
SHOOT_ANIM_TIME = 0.15

PLAYER_MAX_HP = 10
ENEMY_HP = 5
ENEMY_DAMAGE = 1
INVINCIBLE_TIME = 1.0

GUN_OFFSET_X = 45
GUN_OFFSET_Y = 10
GUN_HEIGHT_OFFSET = 18

# --------------------
# УТИЛИТА
# --------------------
def make_sprite(width, height, color):
    texture = arcade.make_soft_square_texture(
        max(width, height), color, 255, 255
    )
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

        # Основные текстуры
        self.texture_right = arcade.load_texture("data/doomguy-Photoroom.png")
        self.texture_left = arcade.load_texture("data/doomguy_left-Photoroom.png")

        # Текстуры выстрела
        self.texture_shoot_right = arcade.load_texture("data/doomguy_shooting-Photoroom.png")
        self.texture_shoot_left = arcade.load_texture("data/doonguy_shooting_left-Photoroom.png")

        # Прыжковые текстуры
        self.texture_jump_right = arcade.load_texture("data/doomguy_jump-Photoroom.png")
        self.texture_jump_left = arcade.load_texture("data/doomguy_jump_left-Photoroom.png")

        # Анимация бега
        self.run_textures_right = [
            arcade.load_texture(f"data/file_run animations/run-animation{i}-Photoroom.png")
            for i in range(1, 11)
        ]
        self.run_textures_left = [
            arcade.load_texture(f"data/file_run_left_animations/run-animation{i}_left-Photoroom.png")
            for i in range(1, 11)
        ]

        self.texture = self.texture_right
        self.scale = 0.9

        self.facing = 1
        self.hp = PLAYER_MAX_HP
        self.invincible_timer = 0

        self.walk_frame = 0
        self.walk_timer = 0
        self.walk_speed = 0.1

        self.is_on_ground = False
        self.is_shooting = False
        self.shoot_anim_timer = 0

    def update_texture(self, delta_time):
        # --------------------
        # Прыжок
        if not self.is_on_ground:
            self.texture = (
                self.texture_jump_right if self.facing == 1 else self.texture_jump_left
            )
            self.scale = 0.9
            return

        # --------------------
        # Стрельба
        if self.is_shooting:
            self.shoot_anim_timer -= delta_time
            if self.shoot_anim_timer <= 0:
                self.is_shooting = False

            self.texture = (
                self.texture_shoot_right if self.facing == 1 else self.texture_shoot_left
            )
            self.scale = 0.9
            return

        # --------------------
        # Ходьба
        if abs(self.change_x) > 0.1:
            self.walk_timer += delta_time
            if self.walk_timer >= self.walk_speed:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % len(self.run_textures_right)

            self.texture = (
                self.run_textures_right[self.walk_frame]
                if self.facing == 1 else self.run_textures_left[self.walk_frame]
            )
            self.scale = 0.9
        else:
            self.walk_frame = 0
            self.texture = self.texture_right if self.facing == 1 else self.texture_left
            self.scale = 0.9

# --------------------
# ВРАГ
# --------------------
class Enemy(arcade.Sprite):
    def __init__(self, x, y, platforms):
        super().__init__()

        self.texture = arcade.make_soft_square_texture(48, arcade.color.RED, 255, 255)
        self.width = 40
        self.height = 80
        self.center_x = x
        self.center_y = y

        self.hp = ENEMY_HP

        self.physics = arcade.PhysicsEnginePlatformer(
            self, platforms, gravity_constant=GRAVITY
        )

    def update_enemy(self, player):
        self.physics.update()
        dx = player.center_x - self.center_x
        self.change_x = math.copysign(ENEMY_SPEED, dx) if abs(dx) > 10 else 0
        self.center_x += self.change_x

# --------------------
# ПУЛЯ
# --------------------
class Bullet(arcade.Sprite):
    def __init__(self, x, y, direction):
        super().__init__(arcade.make_circle_texture(5, arcade.color.BLACK))
        self.center_x = x
        self.center_y = y
        self.change_x = BULLET_SPEED * direction

    def update(self, delta_time=1/60):
        self.center_x += self.change_x
        if self.center_x < 0 or self.center_x > LEVEL_WIDTH:
            self.remove_from_sprite_lists()

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

        self.player = None
        self.physics_engine = None
        self.shooting = False
        self.game_over = False
        self.shoot_timer = 0

    def setup(self):
        self.game_over = False
        self.player_list.clear()
        self.platforms.clear()
        self.enemies.clear()
        self.bullets.clear()

        # Игрок
        self.player = Player()
        self.player.center_x = 200
        self.player.center_y = 120
        self.player_list.append(self.player)

        # Земля
        ground = make_sprite(LEVEL_WIDTH, 40, arcade.color.GRAY)
        ground.center_x = LEVEL_WIDTH // 2
        ground.center_y = 20
        self.platforms.append(ground)

        # Платформы лестничками (по 4, затем снова)
        start_x = 400
        ladder_count = 5
        platforms_per_ladder = 4
        step_x = 180  # расстояние по X
        step_y = 70   # расстояние по Y

        for ladder in range(ladder_count):
            base_x = start_x + ladder * 450
            base_y = 150
            for step in range(platforms_per_ladder):
                platform = make_sprite(180, 20, arcade.color.GRAY)
                platform.center_x = base_x + step * step_x
                platform.center_y = base_y + step * step_y
                self.platforms.append(platform)

        # Враги
        for i in range(6):
            self.enemies.append(Enemy(600 + i * 350, 300, self.platforms))

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player, self.platforms, GRAVITY
        )

    def on_draw(self):
        self.clear()
        self.camera.use()

        self.platforms.draw()
        self.enemies.draw()
        self.bullets.draw()
        self.player_list.draw()

        arcade.draw_text(
            f"HP: {self.player.hp}",
            self.camera.position[0] + 20,
            self.camera.position[1] + SCREEN_HEIGHT - 40,
            arcade.color.WHITE,
            20
        )

        if self.game_over:
            arcade.draw_text(
                "GAME OVER",
                self.camera.position[0] + SCREEN_WIDTH / 2,
                self.camera.position[1] + SCREEN_HEIGHT / 2 + 30,
                arcade.color.RED,
                48,
                anchor_x="center"
            )
            arcade.draw_text(
                "Press R to restart",
                self.camera.position[0] + SCREEN_WIDTH / 2,
                self.camera.position[1] + SCREEN_HEIGHT / 2 - 30,
                arcade.color.WHITE,
                18,
                anchor_x="center"
            )

    def on_update(self, delta_time):
        if self.game_over:
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
            enemy.update_enemy(self.player)

        self.bullets.update(delta_time)

        if self.player.invincible_timer <= 0:
            hits = arcade.check_for_collision_with_list(self.player, self.enemies)
            if hits:
                self.player.hp -= ENEMY_DAMAGE
                self.player.invincible_timer = INVINCIBLE_TIME
                if self.player.hp <= 0:
                    self.game_over = True

        self.camera.position = (
            self.player.center_x - SCREEN_WIDTH / 60,
            self.player.center_y - SCREEN_HEIGHT / 60
        )

    def spawn_bullet(self):
        x = self.player.center_x + GUN_OFFSET_X * self.player.facing
        y = self.player.center_y + GUN_HEIGHT_OFFSET
        self.bullets.append(Bullet(x, y, self.player.facing))

        # Запускаем анимацию выстрела
        self.player.is_shooting = True
        self.player.shoot_anim_timer = SHOOT_ANIM_TIME

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
