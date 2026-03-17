#%%
import asyncio
import pygame
import random
import math

pygame.init()
pygame.mixer.init()

# --- ボタン用クラス ---
class Button:
    def __init__(self, x, y, w, h, text, font, color, text_color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = color
        self.text_color = text_color
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.rendered_text.get_rect(center=self.rect.center)
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        surface.blit(self.rendered_text, self.text_rect)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
    
    def update_text(self, new_text):
        self.text = new_text
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.rendered_text.get_rect(center=self.rect.center)

# --- 音楽・効果音の設定 ---
current_music = "Future_2"  # 初期は Future_2.mp3
pygame.mixer.music.load("assets/Future_2.mp3")
pygame.mixer.music.play(-1)
missile_sound = pygame.mixer.Sound("assets/ミサイル.mp3")

# --- 画面設定 ---
WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("シューティングゲーム with BOSS, アイテム3 & アイテム4")

# --- 色の定義 ---
WHITE    = (255, 255, 255)
BLACK    = (0, 0, 0)
RED      = (255, 0, 0)
GREEN    = (0, 255, 0)
MAGENTA  = (255, 0, 255)  # アイテム3などに使用

# --- 画像の読み込み (assets フォルダ内) ---
player_img   = pygame.image.load("assets/player_1.png").convert_alpha()
enemy1_img   = pygame.image.load("assets/enemy_1.png").convert_alpha()
enemy2_img   = pygame.image.load("assets/enemy_2.png").convert_alpha()
enemy3_img   = pygame.image.load("assets/enemy_3_1.png").convert_alpha()
boss_img     = pygame.image.load("assets/boss_2.png").convert_alpha()
item1_img    = pygame.image.load("assets/item_1.png").convert_alpha()    # 回復アイテム
item2_img    = pygame.image.load("assets/item_2.png").convert_alpha()    # 弾強化アイテム
item3_img    = pygame.image.load("assets/item_3.png").convert_alpha()    # レーザー
item4_img    = pygame.image.load("assets/item_4.png").convert_alpha()    # ミサイル補給

# --- ゲーム状態管理 ---
# game_state: "start", "playing", "paused", "game_over", "game_clear"
game_state = "start"

# プレイヤーの設定
player_width = 50
player_height = 50
player_x = WIDTH // 2 - player_width // 2
player_y = HEIGHT - player_height - 10
player_speed = 3
lives = 30
score = 0

# プレイヤー弾の設定（矩形描画）
bullet_width = 3
bullet_height = 5
bullet_speed = 12
normal_damage = 1
initial_lives = 30

# Item2効果：6秒間、2発ずつ発射
power_damage = normal_damage
player_bullets = []
normal_shoot_delay = 100  # ms
power_shoot_delay = 100
last_shot_time = 0

# ロケットの設定（アイテム4取得時）
rocket_ammo = 0
rocket_bullets = []
rocket_shoot_delay = 300  # ms
last_rocket_shot_time = 0
rocket_width = bullet_width * 5    # 通常弾の5倍
rocket_height = bullet_height * 5
rocket_damage = normal_damage * 5

# パワーアップ効果の管理（Item2）
powerup_active = False
powerup_duration = 6000  # 6秒間
powerup_end_time = 0

# 敵の設定
num_enemies = 10
enemies = []
enemy_types = ["enemy1", "enemy2", "enemy3"]
enemy_weights = [4, 4, 4]
for i in range(num_enemies):
    enemy_type = random.choices(enemy_types, weights=enemy_weights)[0]
    if enemy_type == "enemy1":
        speed = 1
        width, height_enemy = 50, 50
        health = 1
    elif enemy_type == "enemy2":
        speed = 2
        width, height_enemy = 60, 60
        health = 1
    elif enemy_type == "enemy3":
        speed = 1
        width, height_enemy = 80, 80
        health = 5
    enemy_x = random.randint(0, WIDTH - width)
    enemy_y = random.randint(-150, -50)
    enemy = {"type": enemy_type, "x": enemy_x, "y": enemy_y,
             "speed": speed, "width": width, "height": height_enemy,
             "health": health}
    enemies.append(enemy)

# 敵弾の設定
enemy_bullet_width = 3
enemy_bullet_height = 5
enemy_bullet_speed = 3
enemy_bullets = []
enemy_fire_prob = 0.01

# アイテムの設定（種類："life", "power", "item3", "item4"）
items = []
item_speed = 1   # アイテムの流れる速度を遅くする
item_size = 30
last_life_item_spawn_time = 0
last_power_item_spawn_time = 0
last_item4_spawn_time = 0
item_spawn_interval = 5000  # テスト用（本来は10000msに設定）

# ボス出現後は item3 もスポーン
last_item3_spawn_time = 0

# ボス関連の設定
# 出現設定時間 T（ms）→ 30000ms（テスト用、通常は60000ms＝1分）
T = 30000
boss_spawned = False
boss_defeated = False
boss = None
boss_bullets = []
boss_shoot_delay = 1000  # ms
last_boss_shot_time = 0
boss_laser_interval = 10000  # 10秒ごと
last_laser_time = 0
laser_active = False
laser_end_time = 0
laser_beam_direction = (0, 0)
laser_beam_width = 10
last_laser_damage_time = 0
laser_damage_interval = 500  # ms
BOSS_MAX_LIFE = 600

# アイテム3（レーザー）の管理（プレイヤー上端から出る）
item3_laser_active = False
item3_laser_end_time = 0
last_item3_laser_damage_time = 0
item3_laser_beam_width = 3

# グローバル変数：レーザービームの先端位置
laser_beam_end = (0, 0)

# --- グローバルゲーム用変数 ---
# 変数は reset_game() で初期化します
def reset_game():
    global player_x, player_y, lives, score
    global player_bullets, last_shot_time
    global rocket_ammo, rocket_bullets, last_rocket_shot_time
    global powerup_active, powerup_end_time
    global enemies, enemy_bullets, items
    global last_life_item_spawn_time, last_power_item_spawn_time, last_item4_spawn_time, last_item3_spawn_time
    global boss_spawned, boss_defeated, boss, boss_bullets, last_boss_shot_time, last_laser_time, laser_active
    global game_state, current_music, game_over_sound_played, game_clear_sound_played
    
    player_x = WIDTH // 2 - player_width // 2
    player_y = HEIGHT - player_height - 10
    lives = initial_lives
    score = 0
    player_bullets = []
    last_shot_time = 0

    rocket_ammo = 0
    rocket_bullets = []
    last_rocket_shot_time = 0

    powerup_active = False
    powerup_end_time = 0

    enemies.clear()
    enemy_types = ["enemy1", "enemy2", "enemy3"]
    enemy_weights = [4, 4, 4]
    for i in range(num_enemies):
        enemy_type = random.choices(enemy_types, weights=enemy_weights)[0]
        if enemy_type == "enemy1":
            speed = 1
            width, height_enemy = 50, 50
            health = 1
        elif enemy_type == "enemy2":
            speed = 2
            width, height_enemy = 60, 60
            health = 1
        elif enemy_type == "enemy3":
            speed = 1
            width, height_enemy = 80, 80
            health = 5
        enemy_x = random.randint(0, WIDTH - width)
        enemy_y = random.randint(-150, -50)
        enemies.append({"type": enemy_type, "x": enemy_x, "y": enemy_y,
                        "speed": speed, "width": width, "height": height_enemy,
                        "health": health})
    enemy_bullets.clear()

    items.clear()
    last_life_item_spawn_time = 0
    last_power_item_spawn_time = 0
    last_item4_spawn_time = 0
    last_item3_spawn_time = 0

    boss_spawned = False
    boss_defeated = False
    boss = None
    boss_bullets.clear()
    last_boss_shot_time = 0
    last_laser_time = 0
    laser_active = False

    # 背景音楽を Future_2.mp3 に戻す
    if current_music != "Future_2":
        pygame.mixer.music.load("assets/Future_2.mp3")
        pygame.mixer.music.play(-1)
        current_music = "Future_2"
    
    game_state = "playing"
    # 再生済みサウンドフラグもリセット
    game_over_sound_played = False
    game_clear_sound_played = False

# サウンド再生用フラグ
game_over_sound_played = False
game_clear_sound_played = False

# --- ボタン生成 ---
font30 = pygame.font.SysFont("Arial", 10)
font24 = pygame.font.SysFont("Arial", 14)
start_button = Button(WIDTH//2 - 75, HEIGHT//2 - 25, 75, 50, "GAME START", font30, RED, WHITE)
pause_button = Button(10, HEIGHT - 60, 75, 25, "PAUSE", font24, RED, WHITE)
startover_button = Button(10, HEIGHT - 30, 75, 25, "START OVER", font24, RED, WHITE)

# 初期状態はスタート画面
game_state = "start"
reset_game()  # ゲーム変数初期化

# --- 補助関数 ---
def ray_intersect_aabb(ray_origin, ray_direction, rect):
    tmin = -float('inf')
    tmax = float('inf')
    ox, oy = ray_origin
    if ray_direction[0] != 0:
        tx1 = (rect.left - ox) / ray_direction[0]
        tx2 = (rect.right - ox) / ray_direction[0]
        tmin = max(tmin, min(tx1, tx2))
        tmax = min(tmax, max(tx1, tx2))
    else:
        if not (rect.left <= ox <= rect.right):
            return None
    if ray_direction[1] != 0:
        ty1 = (rect.top - oy) / ray_direction[1]
        ty2 = (rect.bottom - oy) / ray_direction[1]
        tmin = max(tmin, min(ty1, ty2))
        tmax = min(tmax, max(ty1, ty2))
    else:
        if not (rect.top <= oy <= rect.bottom):
            return None
    if tmax < 0 or tmin > tmax:
        return None
    return tmin if tmin >= 0 else tmax

def point_line_distance(px, py, x1, y1, x2, y2):
    A = (x1, y1)
    B = (x2, y2)
    P = (px, py)
    AB2 = (B[0]-A[0])**2 + (B[1]-A[1])**2
    if AB2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((P[0]-A[0])*(B[0]-A[0]) + (P[1]-A[1])*(B[1]-A[1])) / AB2))
    closest_x = A[0] + t * (B[0]-A[0])
    closest_y = A[1] + t * (B[1]-A[1])
    return math.hypot(px - closest_x, py - closest_y)

clock = pygame.time.Clock()
running = True
    
while running:
        clock.tick(60)
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if game_state == "start":
                    if start_button.is_clicked(pos):
                        reset_game()  # ボタン押下と同時にBGMも再生される
                elif game_state in ["playing", "paused"]:
                    if pause_button.is_clicked(pos):
                        if game_state == "playing":
                            game_state = "paused"
                            pause_button.update_text("RESUME")
                        else:
                            game_state = "playing"
                            pause_button.update_text("PAUSE")
                    if startover_button.is_clicked(pos):
                        reset_game()
                elif game_state in ["game_over", "game_clear"]:
                    if startover_button.is_clicked(pos):
                        reset_game()
        
        if game_state == "start":
            screen.fill(BLACK)
            start_button.draw(screen)
        elif game_state == "paused":
            # 画面更新は停止、オーバーレイ表示
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            pause_button.draw(screen)
            startover_button.draw(screen)
        elif game_state == "playing":
            # --- 更新処理 ---
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                player_x -= player_speed
            if keys[pygame.K_RIGHT]:
                player_x += player_speed
            if keys[pygame.K_UP]:
                player_y -= player_speed
            if keys[pygame.K_DOWN]:
                player_y += player_speed
            player_x = max(0, min(player_x, WIDTH - player_width))
            player_y = max(0, min(player_y, HEIGHT - player_height))
            
            current_delay = power_shoot_delay if powerup_active else normal_shoot_delay
            if keys[pygame.K_SPACE] and current_time - last_shot_time >= current_delay:
                bullet_x = player_x + player_width//2 - bullet_width//2
                bullet_y = player_y
                damage = power_damage if powerup_active else normal_damage
                if powerup_active:
                    offset = 5
                    player_bullets.append({"x": bullet_x - offset, "y": bullet_y, "damage": damage})
                    player_bullets.append({"x": bullet_x + offset, "y": bullet_y, "damage": damage})
                else:
                    player_bullets.append({"x": bullet_x, "y": bullet_y, "damage": damage})
                last_shot_time = current_time
            
            if keys[pygame.K_v] and current_time - last_rocket_shot_time >= rocket_shoot_delay and rocket_ammo > 0:
                rocket_x = player_x + player_width//2 - rocket_width//2
                rocket_y = player_y
                rocket_bullets.append({"x": rocket_x, "y": rocket_y, "damage": rocket_damage})
                last_rocket_shot_time = current_time
                rocket_ammo -= 1
                missile_sound.play()
            
            for bullet in player_bullets:
                bullet["y"] -= bullet_speed
            player_bullets[:] = [b for b in player_bullets if b["y"] > -bullet_height]
            
            for rocket in rocket_bullets:
                rocket["y"] -= bullet_speed
            rocket_bullets[:] = [r for r in rocket_bullets if r["y"] > -rocket_height]
            
            # ★ ミサイル（ロケット）と敵／ボスの衝突判定 ★
            for rocket in rocket_bullets[:]:
                rocket_rect = pygame.Rect(rocket["x"], rocket["y"], rocket_width, rocket_height)
                hit = False
                for enemy in enemies:
                    enemy_rect = pygame.Rect(enemy["x"], enemy["y"], enemy["width"], enemy["height"])
                    if rocket_rect.colliderect(enemy_rect):
                        enemy["health"] -= rocket["damage"]
                        if enemy["health"] <= 0:
                            if enemy["type"] == "enemy3":
                                score += 5
                            else:
                                score += 1
                            enemy["y"] = random.randint(-150, -50)
                            enemy["x"] = random.randint(0, WIDTH - enemy["width"])
                            enemy["health"] = 5 if enemy["type"]=="enemy3" else 1
                        hit = True
                        break
                if not hit and boss_spawned and not boss_defeated:
                    boss_rect = pygame.Rect(boss["x"], boss["y"], boss["width"], boss["height"])
                    if rocket_rect.colliderect(boss_rect):
                        boss["life"] -= rocket["damage"]
                        hit = True
                        if boss["life"] <= 0:
                            boss_defeated = True
                            score += 50
                if hit:
                    rocket_bullets.remove(rocket)
            
            for enemy in enemies:
                enemy["y"] += enemy["speed"]
                if enemy["y"] > HEIGHT:
                    enemy["y"] = random.randint(-150, -50)
                    enemy["x"] = random.randint(0, WIDTH - enemy["width"])
                    enemy["health"] = 5 if enemy["type"]=="enemy3" else 1
                if random.random() < enemy_fire_prob:
                    if enemy["type"] == "enemy3":
                        enemy_center_x = enemy["x"] + enemy["width"]/2
                        enemy_center_y = enemy["y"] + enemy["height"]/2
                        player_center_x = player_x + player_width/2
                        player_center_y = player_y + player_height/2
                        dx = player_center_x - enemy_center_x
                        dy = player_center_y - enemy_center_y
                        mag = math.hypot(dx, dy)
                        if mag == 0: mag = 1
                        dx = (dx/mag)*enemy_bullet_speed
                        dy = (dy/mag)*enemy_bullet_speed
                    else:
                        dx = 0
                        dy = enemy_bullet_speed
                    bullet_x = enemy["x"] + enemy["width"]//2 - enemy_bullet_width//2
                    bullet_y = enemy["y"] + enemy["height"]
                    enemy_bullets.append({"x": bullet_x, "y": bullet_y, "dx": dx, "dy": dy})
            new_enemy_bullets = []
            for bullet in enemy_bullets:
                bullet["x"] += bullet["dx"]
                bullet["y"] += bullet["dy"]
                if bullet["x"] < 0 or bullet["x"] > WIDTH or bullet["y"] < 0 or bullet["y"] > HEIGHT:
                    continue
                new_enemy_bullets.append(bullet)
            enemy_bullets[:] = new_enemy_bullets
            
            if current_time - last_life_item_spawn_time >= item_spawn_interval:
                item_x = random.randint(0, WIDTH - item_size)
                items.append({"type": "life", "x": item_x, "y": -item_size, "size": item_size})
                last_life_item_spawn_time = current_time
            if current_time - last_power_item_spawn_time >= item_spawn_interval:
                item_x = random.randint(0, WIDTH - item_size)
                items.append({"type": "power", "x": item_x, "y": -item_size, "size": item_size})
                last_power_item_spawn_time = current_time
            if current_time - last_item4_spawn_time >= item_spawn_interval:
                item_x = random.randint(0, WIDTH - item_size)
                items.append({"type": "item4", "x": item_x, "y": -item_size, "size": item_size})
                last_item4_spawn_time = current_time
            if boss_spawned and current_time - last_item3_spawn_time >= item_spawn_interval:
                item_x = random.randint(0, WIDTH - item_size)
                items.append({"type": "item3", "x": item_x, "y": -item_size, "size": item_size})
                last_item3_spawn_time = current_time
            for item in items:
                item["y"] += item_speed
            items[:] = [i for i in items if i["y"] < HEIGHT]
            
            player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
            for item in items[:]:
                item_rect = pygame.Rect(item["x"], item["y"], item["size"], item["size"])
                if player_rect.colliderect(item_rect):
                    if item["type"] == "life":
                        lives += 1
                    elif item["type"] == "power":
                        powerup_active = True
                        powerup_end_time = current_time + 6000
                    elif item["type"] == "item3":
                        item3_laser_active = True
                        item3_laser_end_time = current_time + 3000
                        last_item3_laser_damage_time = current_time
                    elif item["type"] == "item4":
                        rocket_ammo += 5
                    items.remove(item)
            
            if powerup_active and current_time >= powerup_end_time:
                powerup_active = False
            
            if item3_laser_active:
                if current_time >= item3_laser_end_time:
                    item3_laser_active = False
                if current_time - last_item3_laser_damage_time >= 50:
                    beam_x = player_x + player_width//2 - item3_laser_beam_width//2
                    beam_rect = pygame.Rect(beam_x, 0, item3_laser_beam_width, player_y)
                    for enemy in enemies:
                        enemy_rect = pygame.Rect(enemy["x"], enemy["y"], enemy["width"], enemy["height"])
                        if enemy_rect.colliderect(beam_rect):
                            enemy["health"] -= 1
                            if enemy["health"] <= 0:
                                if enemy["type"] == "enemy3":
                                    score += 5
                                else:
                                    score += 1
                                enemy["y"] = random.randint(-150, -50)
                                enemy["x"] = random.randint(0, WIDTH - enemy["width"])
                                enemy["health"] = 5 if enemy["type"]=="enemy3" else 1
                    last_item3_laser_damage_time = current_time
            
            for bullet in player_bullets[:]:
                bullet_rect = pygame.Rect(bullet["x"], bullet["y"], bullet_width, bullet_height)
                for enemy in enemies:
                    enemy_rect = pygame.Rect(enemy["x"], enemy["y"], enemy["width"], enemy["height"])
                    if bullet_rect.colliderect(enemy_rect):
                        enemy["health"] -= bullet["damage"]
                        if enemy["health"] <= 0:
                            if enemy["type"] == "enemy3":
                                score += 5
                            else:
                                score += 1
                            enemy["y"] = random.randint(-150, -50)
                            enemy["x"] = random.randint(0, WIDTH - enemy["width"])
                            enemy["health"] = 5 if enemy["type"]=="enemy3" else 1
                        if bullet in player_bullets:
                            player_bullets.remove(bullet)
                        break
            
            for bullet in enemy_bullets[:]:
                bullet_rect = pygame.Rect(bullet["x"], bullet["y"], enemy_bullet_width, enemy_bullet_height)
                if bullet_rect.colliderect(player_rect):
                    enemy_bullets.remove(bullet)
                    lives -= 1
                    if lives <= 0:
                        game_state = "game_over"
            
            for enemy in enemies:
                enemy_rect = pygame.Rect(enemy["x"], enemy["y"], enemy["width"], enemy["height"])
                if enemy_rect.colliderect(player_rect):
                    lives -= 1
                    enemy["y"] = random.randint(-150, -50)
                    enemy["x"] = random.randint(0, WIDTH - enemy["width"])
                    if lives <= 0:
                        game_state = "game_over"
            
            if current_time >= T and not boss_spawned:
                boss_spawned = True
                boss_scale = 11.84
                boss_width = int(player_width * boss_scale)
                boss_height = int(player_height * boss_scale)
                boss_x = (WIDTH - boss_width) // 2
                boss_y = - int(boss_height * 0.2)
                boss_speed = 0.5
                boss_direction = 1
                boss = {"x": boss_x, "y": boss_y, "width": boss_width, "height": boss_height,
                        "life": BOSS_MAX_LIFE, "speed": boss_speed, "direction": boss_direction}
                enemies[:] = enemies[:max(1, len(enemies)//3)]
                if current_music != "RPG_Battle_03":
                    pygame.mixer.music.load("assets/RPG_Battle_03.mp3")
                    pygame.mixer.music.play(-1)
                    current_music = "RPG_Battle_03"
            
            if boss_spawned and not boss_defeated:
                boss["x"] += boss["speed"] * boss["direction"]
                if boss["x"] <= 0 or boss["x"] + boss["width"] >= WIDTH:
                    boss["direction"] *= -1
                
                if current_time - last_boss_shot_time >= boss_shoot_delay:
                    left_shot = boss["x"] + boss["width"] * 0.2
                    center_shot = boss["x"] + boss["width"] * 0.5
                    right_shot = boss["x"] + boss["width"] * 0.8
                    shot_y = boss["y"] + boss["height"]
                    for shot_x in [left_shot, center_shot, right_shot]:
                        player_center_x = player_x + player_width/2
                        player_center_y = player_y + player_height/2
                        dx = player_center_x - shot_x
                        dy = player_center_y - shot_y
                        mag = math.hypot(dx, dy)
                        if mag == 0:
                            mag = 1
                        dx = (dx / mag) * enemy_bullet_speed
                        dy = (dy / mag) * enemy_bullet_speed
                        boss_bullets.append({"x": shot_x, "y": shot_y, "dx": dx, "dy": dy})
                    last_boss_shot_time = current_time
                
                if not laser_active and current_time - last_laser_time >= boss_laser_interval:
                    laser_active = True
                    laser_end_time = current_time + 3000
                    last_laser_time = current_time
                    boss_center = (boss["x"] + boss["width"]/2, boss["y"] + boss["height"]/2)
                    player_center = (player_x + player_width/2, player_y + player_height/2)
                    dx = player_center[0] - boss_center[0]
                    dy = player_center[1] - boss_center[1]
                    mag = math.hypot(dx, dy)
                    if mag == 0:
                        mag = 1
                    laser_beam_direction = (dx / mag, dy / mag)
                if laser_active and current_time >= laser_end_time:
                    laser_active = False
                
                new_boss_bullets = []
                for bullet in boss_bullets:
                    bullet["x"] += bullet["dx"]
                    bullet["y"] += bullet["dy"]
                    if bullet["x"] < 0 or bullet["x"] > WIDTH or bullet["y"] < 0 or bullet["y"] > HEIGHT:
                        continue
                    new_boss_bullets.append(bullet)
                boss_bullets[:] = new_boss_bullets
                
                for bullet in player_bullets[:]:
                    bullet_rect = pygame.Rect(bullet["x"], bullet["y"], bullet_width, bullet_height)
                    boss_rect = pygame.Rect(boss["x"], boss["y"], boss["width"], boss["height"])
                    if bullet_rect.colliderect(boss_rect):
                        boss["life"] -= bullet["damage"]
                        if bullet in player_bullets:
                            player_bullets.remove(bullet)
                        if boss["life"] <= 0:
                            boss_defeated = True  # GAME CLEAR
                            score += 50
                        break
                
                for bullet in boss_bullets[:]:
                    bullet_rect = pygame.Rect(bullet["x"], bullet["y"], enemy_bullet_width, enemy_bullet_height)
                    if bullet_rect.colliderect(player_rect):
                        boss_bullets.remove(bullet)
                        lives -= 1
                        if lives <= 0:
                            game_state = "game_over"
                
                if laser_active:
                    boss_center_x = boss["x"] + boss["width"] / 2
                    boss_center_y = boss["y"] + boss["height"] / 2
                    beam_length = 2000
                    for enemy in enemies:
                        enemy_rect = pygame.Rect(enemy["x"], enemy["y"], enemy["width"], enemy["height"])
                        t = ray_intersect_aabb((boss_center_x, boss_center_y), laser_beam_direction, enemy_rect)
                        if t is not None and t > 0:
                            beam_length = min(beam_length, t)
                    beam_end_x = boss_center_x + laser_beam_direction[0] * beam_length
                    beam_end_y = boss_center_y + laser_beam_direction[1] * beam_length
                    laser_beam_end = (beam_end_x, beam_end_y)
                    if point_line_distance(player_x + player_width/2, player_y + player_height/2,
                                           boss_center_x, boss_center_y, beam_end_x, beam_end_y) < laser_beam_width/2:
                        if current_time - last_laser_damage_time >= laser_damage_interval:
                            lives -= 1
                            last_laser_damage_time = current_time
                            if lives <= 0:
                                game_state = "game_over"
            
            # ゲーム終了判定
            if lives <= 0:
                game_state = "game_over"
            if boss_defeated:
                game_state = "game_clear"
        
        # --- 音楽の切り替え ---
        if game_state == "playing":
            if boss_spawned and current_music != "RPG_Battle_03":
                pygame.mixer.music.load("assets/RPG_Battle_03.mp3")
                pygame.mixer.music.play(-1)
                current_music = "RPG_Battle_03"
            elif not boss_spawned and current_music != "Future_2":
                pygame.mixer.music.load("assets/Future_2.mp3")
                pygame.mixer.music.play(-1)
                current_music = "Future_2"
        # ゲームオーバー時：BGMを止め、game_over.mp3を一回再生
        if game_state == "game_over" and not game_over_sound_played:
            pygame.mixer.music.stop()
            pygame.mixer.music.load("assets/game_over.mp3")
            pygame.mixer.music.play(0)
            game_over_sound_played = True
        # ゲームクリア時：BGMを止め、ゲームクリア(軽め①).mp3を一回再生
        if game_state == "game_clear" and not game_clear_sound_played:
            pygame.mixer.music.stop()
            pygame.mixer.music.load("assets/ゲームクリア(軽め①).mp3")
            pygame.mixer.music.play(0)
            game_clear_sound_played = True

        # --- 描画処理 ---
        if game_state == "start":
            screen.fill(BLACK)
            start_button.draw(screen)
        elif game_state in ["playing", "paused"]:
            screen.fill(BLACK)
            # プレイヤー描画
            scaled_player = pygame.transform.scale(player_img, (player_width, player_height))
            screen.blit(scaled_player, (player_x, player_y))
            # 通常弾
            for bullet in player_bullets:
                pygame.draw.rect(screen, WHITE, (bullet["x"], bullet["y"], bullet_width, bullet_height))
            # ロケット弾（item4.png 使用）
            for rocket in rocket_bullets:
                scaled_rocket = pygame.transform.scale(item4_img, (rocket_width, rocket_height))
                screen.blit(scaled_rocket, (rocket["x"], rocket["y"]))
            # 敵描画
            for enemy in enemies:
                if enemy["type"] == "enemy1":
                    img = enemy1_img
                elif enemy["type"] == "enemy2":
                    img = enemy2_img
                elif enemy["type"] == "enemy3":
                    img = enemy3_img
                scaled_enemy = pygame.transform.scale(img, (enemy["width"], enemy["height"]))
                screen.blit(scaled_enemy, (enemy["x"], enemy["y"]))
            # 敵弾描画
            for bullet in enemy_bullets:
                pygame.draw.rect(screen, GREEN, (bullet["x"], bullet["y"], enemy_bullet_width, enemy_bullet_height))
            # アイテム描画
            for item in items:
                if item["type"] == "life":
                    img = item1_img
                elif item["type"] == "power":
                    img = item2_img
                elif item["type"] == "item3":
                    img = item3_img
                elif item["type"] == "item4":
                    img = item4_img
                scaled_item = pygame.transform.scale(img, (item["size"], item["size"]))
                screen.blit(scaled_item, (item["x"], item["y"]))
            # ボス描画
            if boss_spawned and not boss_defeated:
                scaled_boss = pygame.transform.scale(boss_img, (boss["width"], boss["height"]))
                screen.blit(scaled_boss, (boss["x"], boss["y"]))
                for bullet in boss_bullets:
                    pygame.draw.rect(screen, RED, (bullet["x"], bullet["y"], enemy_bullet_width, enemy_bullet_height))
                if laser_active:
                    pygame.draw.line(screen, RED, (boss["x"]+boss["width"]/2, boss["y"]+boss["height"]/2),
                                     laser_beam_end, laser_beam_width)
                # ボスライフバー
                bar_width = 300
                bar_height = 20
                bar_x = WIDTH - bar_width - 10
                bar_y = 10
                life_ratio = boss["life"] / BOSS_MAX_LIFE
                current_bar_width = int(bar_width * life_ratio)
                bar_color = GREEN if boss["life"] > 200 else RED
                pygame.draw.rect(screen, (100,100,100), (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(screen, bar_color, (bar_x, bar_y, current_bar_width, bar_height))
                pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
            # アイテム3レーザー描画（プレイヤー上端から上方向へ）
            if item3_laser_active:
                beam_x = player_x + player_width//2 - item3_laser_beam_width//2
                pygame.draw.rect(screen, (0, 191, 255), (beam_x, 0, item3_laser_beam_width, player_y))
            # ロケット弾数表示
            rocket_text = pygame.font.SysFont("Arial", 24).render("Rockets: " + str(rocket_ammo), True, WHITE)
            screen.blit(rocket_text, (WIDTH - rocket_text.get_width() - 10, HEIGHT - rocket_text.get_height() - 10))
            # スコア・ライフ表示
            score_text = pygame.font.SysFont("Arial", 24).render("Score: " + str(score), True, WHITE)
            screen.blit(score_text, (10, 10))
            lives_text = pygame.font.SysFont("Arial", 24).render("Lives: " + str(lives), True, WHITE)
            screen.blit(lives_text, (10, 40))
            # ボタン描画
            pause_button.draw(screen)
            startover_button.draw(screen)
            if game_state == "paused":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
        elif game_state == "game_over":
            screen.fill(BLACK)
            over_text = pygame.font.SysFont("Arial", 64).render("GAME OVER", True, WHITE)
            text_rect = over_text.get_rect(center=(WIDTH/2, HEIGHT/2))
            screen.blit(over_text, text_rect)
            startover_button.draw(screen)
        elif game_state == "game_clear":
            screen.fill(BLACK)
            clear_text = pygame.font.SysFont("Arial", 64).render("GAME CLEAR", True, WHITE)
            text_rect = clear_text.get_rect(center=(WIDTH/2, HEIGHT/2))
            screen.blit(clear_text, text_rect)
            startover_button.draw(screen)
        
        pygame.display.flip()

pygame.quit()
#%%