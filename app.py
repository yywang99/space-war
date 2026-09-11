import pygame
import random
import os

# --- 常數設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 顏色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 180, 0)
LIGHT_GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# --- 遊戲效果常數 ---
GAME_HIT_PAUSE_DURATION = 500  # 遊戲邏輯暫停的毫秒數
PLAYER_INVULNERABILITY_DURATION = 3000 # 玩家無敵的毫秒數
PLAYER_BLINK_INTERVAL = 100    # 玩家閃爍的毫秒間隔
POWERUP_TIME = 5000 # 強化道具持續時間 (毫秒)
POWERUP_SPAWN_CHANCE = 0.1 # 強化道具掉落機率 (10%)

# --- 資源路徑 ---
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')

# --- 遊戲設定 ---
SCORE_FILE = "scores.txt"
MAX_SCORES = 5 # 只顯示前 5 名
MAX_NAME_LENGTH = 8 # 玩家姓名最大長度

LIVES_ICON_SPACING = 30 # 生命值圖示間距
# 遊戲狀態
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_PAUSED = 3
STATE_LEADERBOARD = 4
STATE_ENTER_NAME = 5

def draw_text(surf, text, font, x, y, color=WHITE):
    """在畫面上繪製文字"""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    surf.blit(text_surface, text_rect)

def load_scores():
    """從檔案載入排行榜分數，格式為 '姓名,分數'"""
    if not os.path.exists(SCORE_FILE):
        return []
    scores = []
    try:
        with open(SCORE_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    name = parts[0]
                    score = int(parts[1])
                    scores.append((name, score))
    except (ValueError, IOError, IndexError) as e:
        print(f"讀取分數時發生錯誤: {e}")
        return []
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:MAX_SCORES]

def draw_lives(surf, x, y, lives, img):
    """在畫面上繪製生命值"""
    for i in range(lives):
        img_rect = img.get_rect()
        img_rect.x = x + LIVES_ICON_SPACING * i
        img_rect.y = y
        surf.blit(img, img_rect)

def save_score(name, new_score):
    """儲存新分數到排行榜"""
    if new_score <= 0: return # 不儲存 0 分或負分
    if not name: name = "AAA" # 如果沒輸入名字，給予預設值

    scores = load_scores()
    scores.append((name, new_score))
    scores.sort(key=lambda x: x[1], reverse=True)
    # 只保留前 MAX_SCORES 名
    scores = scores[:MAX_SCORES]
    try:
        with open(SCORE_FILE, 'w', encoding='utf-8') as f:
            for s in scores:
                f.write(f"{s[0]},{s[1]}\n")
    except IOError as e:
        print(f"儲存分數時發生錯誤: {e}")

def is_high_score(score):
    """檢查分數是否能進入排行榜"""
    if score <= 0:
        return False
    high_scores = load_scores()
    if len(high_scores) < MAX_SCORES:
        return True
    return score > high_scores[-1][1]
# --- 類別定義 ---

class Player(pygame.sprite.Sprite):
    """玩家的太空船"""
    def __init__(self):
        super().__init__()
        self.invulnerable = False
        self.invulnerable_start_time = 0
        self.last_blink_time = 0
        self.visible = True # 用於控制閃爍時的顯示/隱藏
        self.power_level = 1
        self.powerup_timer = 0
        try:
            self.lives = 3 # 增加生命值屬性
            # 載入玩家圖片，並進行優化
            player_img_path = os.path.join(ASSETS_DIR, 'player.png')
            original_image = pygame.image.load(player_img_path).convert_alpha()
            # 調整圖片大小
            self.image = pygame.transform.scale(original_image, (50, 45))
            # 建立一個較小的圖片用於顯示生命值
            self.lives_image = pygame.transform.scale(self.image, (25, 23))
        except pygame.error as e:
            print(f"警告: 玩家圖片 'player.png' 載入失敗: {e}")
            print("將使用預設的三角形圖形。")
            # 若圖片載入失敗，則退回繪製三角形
            self.image = pygame.Surface((50, 40), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, WHITE, [(25, 0), (0, 40), (50, 40)])
            # 建立一個較小的三角形用於顯示生命值
            self.lives_image = pygame.transform.scale(self.image, (25, 20))

        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10

    def update(self):
        """根據滑鼠位置更新太空船位置"""
        pos = pygame.mouse.get_pos()
        self.rect.centerx = pos[0]
        # 限制太空船在螢幕範圍內
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        # 處理無敵狀態和閃爍
        if self.invulnerable:
            now = pygame.time.get_ticks()
            if now - self.invulnerable_start_time > PLAYER_INVULNERABILITY_DURATION:
                self.invulnerable = False
                self.visible = True
                self.image.set_alpha(255) # 確保無敵結束時完全可見
            elif now - self.last_blink_time > PLAYER_BLINK_INTERVAL:
                self.visible = not self.visible
                self.image.set_alpha(255 if self.visible else 100) # 閃爍時半透明
                self.last_blink_time = now
        else:
            # 確保非無敵時完全可見
            self.image.set_alpha(255)

        # 檢查強化道具是否過期
        if self.power_level > 1 and pygame.time.get_ticks() - self.powerup_timer > POWERUP_TIME:
            self.power_level = 1

    def powerup(self):
        """提升武器等級"""
        self.power_level += 1
        if self.power_level > 3: # 最高等級為 3
            self.power_level = 3
        self.powerup_timer = pygame.time.get_ticks()

    def shoot(self):
        """發射雷射，根據強化等級決定模式"""
        if self.power_level == 1:
            # 等級 1: 單發雷射
            laser = Laser(self.rect.centerx, self.rect.top)
            all_sprites.add(laser)
            lasers.add(laser)
        elif self.power_level == 2:
            # 等級 2: 雙發雷射
            laser1 = Laser(self.rect.left + 10, self.rect.centery)
            laser2 = Laser(self.rect.right - 10, self.rect.centery)
            all_sprites.add(laser1, laser2)
            lasers.add(laser1, laser2)
        elif self.power_level >= 3:
            # 等級 3: 三發雷射
            laser1 = Laser(self.rect.centerx, self.rect.top)
            laser2 = Laser(self.rect.left + 10, self.rect.centery)
            laser3 = Laser(self.rect.right - 10, self.rect.centery)
            all_sprites.add(laser1, laser2, laser3)
            lasers.add(laser1, laser2, laser3)

        laser_sound.play()

class Asteroid(pygame.sprite.Sprite):
    """隕石"""
    def __init__(self):
        super().__init__()
        # 從預載入的圖片列表中隨機選擇一張原始圖片
        self.image_orig = random.choice(meteor_images)
        
        # 隨機設定隕石大小，並建立一個縮放後的版本以供旋轉，避免失真
        self.size = random.randint(20, 80)
        self.image_scaled = pygame.transform.scale(self.image_orig, (self.size, self.size))
        self.image = self.image_scaled.copy()

        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speed_y = random.randrange(1, 8)

        # 新增旋轉相關屬性
        self.rot = 0
        self.rot_speed = random.randrange(-5, 5)
        self.last_update = pygame.time.get_ticks()

    def rotate(self):
        """處理隕石旋轉，以縮放後的圖片為基礎，避免重複縮放導致失真"""
        now = pygame.time.get_ticks()
        if now - self.last_update > 50: # 每 50 毫秒更新一次旋轉角度
            self.last_update = now
            self.rot = (self.rot + self.rot_speed) % 360
            new_image = pygame.transform.rotate(self.image_scaled, self.rot)
            old_center = self.rect.center
            self.image = new_image
            self.rect = self.image.get_rect(center=old_center)
            self.mask = pygame.mask.from_surface(self.image)
            self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        """向下移動並旋轉隕石"""
        self.rotate()
        self.rect.y += self.speed_y
        # 如果隕石移出螢幕底部，就重新生成一個
        if self.rect.top > SCREEN_HEIGHT + 10:
            self.rect.x = random.randrange(SCREEN_WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speed_y = random.randrange(1, 8)

class Laser(pygame.sprite.Sprite):
    """雷射"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 20))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed_y = -10

    def update(self):
        """向上移動雷射"""
        self.rect.y += self.speed_y
        # 如果雷射移出螢幕頂部，就將其刪除
        if self.rect.bottom < 0:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    """爆炸效果"""
    def __init__(self, center, size):
        super().__init__()
        self.size = size
        self.image = explosion_anim[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50  # 每個畫格的毫秒數

    def update(self):
        """更新爆炸動畫"""
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(explosion_anim[self.size]):
                self.kill()
            else:
                # 保持中心點不變來更新圖片
                center = self.rect.center
                self.image = explosion_anim[self.size][self.frame]
                self.rect = self.image.get_rect(center=center)

class PowerUp(pygame.sprite.Sprite):
    """強化道具"""
    def __init__(self, center):
        super().__init__()
        self.type = 'gun' # 目前只有 'gun' 類型
        try:
            self.image = powerup_images[self.type]
        except (KeyError, NameError):
            # 若圖片載入失敗或字典不存在，則退回繪製圖形
            self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.rect(self.image, BLUE, (0, 0, 30, 30), border_radius=5)
            # 畫一個向上的箭頭
            pygame.draw.polygon(self.image, WHITE, [(15, 4), (24, 13), (18, 13), (18, 26), (12, 26), (12, 13), (6, 13)])

        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speed_y = 3

    def update(self):
        """向下移動道具"""
        self.rect.y += self.speed_y
        # 如果道具移出螢幕底部，就將其刪除
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

def reset_game():
    """重置遊戲並返回新的玩家和分數"""
    all_sprites.empty()
    asteroids.empty()
    lasers.empty()
    powerups.empty()
    
    player = Player()
    all_sprites.add(player)

    for _ in range(8): # 初始隕石數量
        a = Asteroid()
        all_sprites.add(a)
        asteroids.add(a)
    
    return player, 0

# --- 遊戲初始化 ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.mixer.init() # 初始化音效混合器
pygame.display.set_caption("太空戰爭 (Space War)")
clock = pygame.time.Clock()

# --- 字型設定 ---
# 為了顯示中文，我們需要指定一個支援中文的字型檔
# 請下載一個 .ttf/.otf 字型檔並放到專案目錄下，並在此處指定檔名
FONT_FILENAME = "font.ttf" 
try:
    font_lg = pygame.font.Font(FONT_FILENAME, 64)
    font_md = pygame.font.Font(FONT_FILENAME, 36)
    font_sm = pygame.font.Font(FONT_FILENAME, 24)
except pygame.error as e:
    print(f"警告: 字型檔案 '{FONT_FILENAME}' 載入失敗: {e}")
    print("將使用預設字型，中文可能無法正常顯示。")
    print(f"請確認已將支援中文的字型檔 '{FONT_FILENAME}' 放在專案目錄中。")
    # 若載入失敗，則退回使用預設字型
    font_lg = pygame.font.Font(None, 64)
    font_md = pygame.font.Font(None, 36)
    font_sm = pygame.font.Font(None, 24)

# --- 載入背景圖片 ---
try:
    background_img_path = os.path.join(ASSETS_DIR, 'background.png')
    # 使用 convert() 優化圖片，加快後續繪製速度
    background_img = pygame.image.load(background_img_path).convert()
    background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
except pygame.error as e:
    print(f"警告: 背景圖片 'background.png' 載入失敗: {e}")
    print("主選單將使用黑色背景。")
    background_img = None # 若載入失敗則設為 None

# --- 載入爆炸動畫 ---
# 由於沒有圖片，我們在這裡動態生成爆炸效果
explosion_anim = {}
explosion_anim['lg'] = []
explosion_anim['sm'] = []
for i in range(9):
    # 建立一個透明的 Surface
    img_lg = pygame.Surface((100, 100), pygame.SRCALPHA)
    img_sm = pygame.Surface((40, 40), pygame.SRCALPHA)
    # 繪製大小漸增、顏色漸淡的圓形
    radius_lg = 5 + i * 5
    radius_sm = 2 + i * 2
    color_val = 255 - i * 25
    pygame.draw.circle(img_lg, (255, color_val, 0), (50, 50), radius_lg)
    pygame.draw.circle(img_sm, (255, color_val, 0), (20, 20), radius_sm)
    explosion_anim['lg'].append(img_lg)
    explosion_anim['sm'].append(img_sm)

# --- 載入隕石圖片 ---
meteor_images = []
# 假設你的 assets 資料夾內有這些檔案，如果你的檔名不同，請修改這裡
meteor_list = ['meteor1.png', 'meteor2.png', 'meteor3.png', 'meteor4.png'] 
for img_name in meteor_list:
    try:
        img_path = os.path.join(ASSETS_DIR, img_name)
        meteor_images.append(pygame.image.load(img_path).convert_alpha())
    except pygame.error as e:
        print(f"警告: 隕石圖片 '{img_name}' 載入失敗: {e}")

# 如果沒有任何圖片成功載入，就退回使用預設的圓形圖形，避免遊戲崩潰
if not meteor_images:
    print("將使用預設的紅色圓形作為隕石。")
    fallback_img = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.circle(fallback_img, RED, (15, 15), 15)
    meteor_images.append(fallback_img)

# --- 載入強化道具圖片 ---
powerup_images = {}
try:
    powerup_img_path = os.path.join(ASSETS_DIR, 'powerup_gun.png')
    # 調整圖片大小並儲存
    original_powerup_img = pygame.image.load(powerup_img_path).convert_alpha()
    powerup_images['gun'] = pygame.transform.scale(original_powerup_img, (30, 30))
except pygame.error as e:
    print(f"警告: 強化道具圖片 'powerup_gun.png' 載入失敗: {e}")
    # 後續會在 PowerUp 類別中處理 fallback

# --- 載入音效 ---
try:
    pygame.mixer.music.load(os.path.join(ASSETS_DIR, 'background.mp3'))
    laser_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, 'laser.wav'))
    explosion_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, 'explosion.wav'))
    player_hit_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, 'player_hit.wav'))
    powerup_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, 'powerup.wav'))
    # 設定音量 (0.0 到 1.0)
    pygame.mixer.music.set_volume(0.4)
    laser_sound.set_volume(0.3)
    explosion_sound.set_volume(0.2)
    player_hit_sound.set_volume(0.5)
    powerup_sound.set_volume(0.4)
except pygame.error as e:
    print(f"警告: 音效檔案載入失敗: {e}")
    print("請確認 'assets' 資料夾內有 'background.mp3', 'laser.wav', 'explosion.wav', 'player_hit.wav', 'powerup.wav' 檔案。")
    # 建立一個無聲的 dummy sound，避免遊戲崩潰
    laser_sound = pygame.mixer.Sound(buffer=b'')
    explosion_sound = pygame.mixer.Sound(buffer=b'')
    player_hit_sound = pygame.mixer.Sound(buffer=b'')
    powerup_sound = pygame.mixer.Sound(buffer=b'')
# --- 遊戲物件與群組 ---
all_sprites = pygame.sprite.Group()
asteroids = pygame.sprite.Group()
lasers = pygame.sprite.Group()
powerups = pygame.sprite.Group()

# 遊戲變數
game_state = STATE_MENU
player = None
score = 0
player_name_input = ""
cursor_visible = True
last_cursor_toggle = 0

# 遊戲受擊停頓狀態
player_hit_pause_active = False
player_hit_pause_start_time = 0

# --- 遊戲主迴圈 ---
running = True
while running:
    # 控制遊戲更新頻率
    clock.tick(FPS)
    
    # 取得所有事件
    events = pygame.event.get()

    # 處理通用事件
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    # 根據遊戲狀態更新和繪製
    if game_state == STATE_MENU:
        if background_img:
            screen.blit(background_img, (0, 0))
        else:
            screen.fill(BLACK)

        draw_text(screen, "YY遊樂世界/太空戰爭", font_lg, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
        draw_text(screen, "滑鼠移動飛船, 左鍵發射", font_sm, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # 繪製開始按鈕
        start_button = pygame.Rect(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT * 0.6, 200, 50)
        if start_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, LIGHT_GREEN, start_button, border_radius=10)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    player, score = reset_game()
                    game_state = STATE_PLAYING
                    pygame.mixer.music.play(loops=-1) # 開始循環播放背景音樂
        else:
            pygame.draw.rect(screen, GREEN, start_button, border_radius=10)
        draw_text(screen, "開始遊戲", font_md, start_button.centerx, start_button.centery, BLACK)

        # 繪製排行榜按鈕
        leaderboard_button = pygame.Rect(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT * 0.75, 200, 50)
        if leaderboard_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, LIGHT_GREEN, leaderboard_button, border_radius=10)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    game_state = STATE_LEADERBOARD
        else:
            pygame.draw.rect(screen, GREEN, leaderboard_button, border_radius=10)
        draw_text(screen, "排行榜", font_md, leaderboard_button.centerx, leaderboard_button.centery, BLACK)

    elif game_state == STATE_PLAYING:
        # 處理遊戲中事件
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                player.shoot()
            if event.type == pygame.KEYDOWN:
                # 按下 ESC 或 P 鍵可暫停遊戲
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                    game_state = STATE_PAUSED
                    pygame.mixer.music.pause()

        # --- 遊戲邏輯更新 (包含受擊停頓) ---
        now = pygame.time.get_ticks()

        if player_hit_pause_active:
            # 在受擊停頓期間，只更新玩家（用於閃爍）和爆炸效果
            player.update()
            for sprite in all_sprites:
                if isinstance(sprite, Explosion):
                    sprite.update()
            
            # 檢查停頓時間是否結束
            if now - player_hit_pause_start_time > GAME_HIT_PAUSE_DURATION:
                player_hit_pause_active = False
        else:
            # 當不在受擊停頓狀態時，正常更新所有遊戲物件
            all_sprites.update()

            # --- 碰撞偵測 ---
            # 檢查雷射是否擊中隕石
            hits_lasers_asteroids = pygame.sprite.groupcollide(lasers, asteroids, True, True) 
            for asteroids_hit in hits_lasers_asteroids.values():
                for asteroid in asteroids_hit:
                    score += 1
                    explosion_sound.play()
                    expl_size = 'lg' if asteroid.size > 35 else 'sm'
                    expl = Explosion(asteroid.rect.center, expl_size)
                    all_sprites.add(expl)
                    new_asteroid = Asteroid()

                    # 機率性掉落強化道具
                    if random.random() < POWERUP_SPAWN_CHANCE:
                        pow = PowerUp(asteroid.rect.center)
                        all_sprites.add(pow)
                        powerups.add(pow)

                    all_sprites.add(new_asteroid)
                    asteroids.add(new_asteroid)

            # 檢查玩家是否被隕石擊中 (只有在非無敵狀態下才檢查)
            if not player.invulnerable:
                hits_player_asteroids = pygame.sprite.spritecollide(player, asteroids, True)
                if hits_player_asteroids:
                    player_hit_sound.play()
                    expl = Explosion(player.rect.center, 'lg')
                    all_sprites.add(expl)
                    player.lives -= 1
                    
                    # 啟動無敵和閃爍
                    player.invulnerable = True
                    player.invulnerable_start_time = pygame.time.get_ticks()
                    player.last_blink_time = pygame.time.get_ticks()

                    # 啟動遊戲停頓
                    player_hit_pause_active = True
                    player_hit_pause_start_time = pygame.time.get_ticks()

                    if player.lives <= 0:
                        pygame.mixer.music.stop()
                        if is_high_score(score):
                            game_state = STATE_ENTER_NAME
                            player_name_input = "" # 重置姓名輸入
                            last_cursor_toggle = pygame.time.get_ticks()
                        else:
                            game_state = STATE_GAME_OVER

                    
                    # 為被撞掉的隕石補上新的
                    for _ in hits_player_asteroids:
                        new_asteroid = Asteroid()
                        all_sprites.add(new_asteroid)
                        asteroids.add(new_asteroid)
            
            # 檢查玩家是否吃到強化道具
            hits_player_powerups = pygame.sprite.spritecollide(player, powerups, True)
            for hit in hits_player_powerups:
                if hit.type == 'gun':
                    player.powerup()
                    powerup_sound.play()

        # 畫面繪製
        screen.fill(BLACK)
        all_sprites.draw(screen)
        draw_text(screen, f"Score: {score}", font_md, SCREEN_WIDTH / 2, 20)
        draw_lives(screen, SCREEN_WIDTH - 100, 15, player.lives, player.lives_image)
        draw_text(screen, "按 ESC 或 P 暫停", font_sm, 90, SCREEN_HEIGHT - 20)

    elif game_state == STATE_PAUSED:
        # 遊戲暫停時，不更新遊戲邏輯，只繪製暫停畫面並監聽事件
        # 繪製半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # 黑色，180 alpha
        screen.blit(overlay, (0, 0))

        draw_text(screen, "遊戲暫停", font_lg, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)

        # 繪製繼續按鈕
        mouse_pos = pygame.mouse.get_pos()
        continue_button = pygame.Rect(SCREEN_WIDTH/2 - 75, SCREEN_HEIGHT * 3/4 - 25, 150, 50)

        button_color = LIGHT_GREEN if continue_button.collidepoint(mouse_pos) else GREEN
        pygame.draw.rect(screen, button_color, continue_button, border_radius=10)
        draw_text(screen, "繼續遊戲", font_md, continue_button.centerx, continue_button.centery, BLACK)

        # 處理取消暫停的事件 (點擊按鈕或按 ESC/P)
        for event in events:
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and continue_button.collidepoint(mouse_pos)) or \
               (event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_p)):
                game_state = STATE_PLAYING
                pygame.mixer.music.unpause()
                break

    elif game_state == STATE_GAME_OVER:
        if background_img:
            screen.blit(background_img, (0, 0))
        else:
            screen.fill(BLACK)

        draw_text(screen, "遊戲結束", font_lg, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
        draw_text(screen, f"最終得分: {score}", font_md, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

        mouse_pos = pygame.mouse.get_pos()
        button_y = SCREEN_HEIGHT * 3/4 - 25
        restart_button = pygame.Rect(SCREEN_WIDTH/2 - 200, button_y, 180, 50)
        leaderboard_button = pygame.Rect(SCREEN_WIDTH/2 + 20, button_y, 180, 50)

        # 重新開始按鈕
        if restart_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, LIGHT_GREEN, restart_button, border_radius=10)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    player, score = reset_game()
                    game_state = STATE_PLAYING
                    pygame.mixer.music.play(loops=-1)
        else:
            pygame.draw.rect(screen, GREEN, restart_button, border_radius=10)
        draw_text(screen, "重新開始", font_md, restart_button.centerx, restart_button.centery, BLACK)

        # 排行榜按鈕
        if leaderboard_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, LIGHT_GREEN, leaderboard_button, border_radius=10)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    game_state = STATE_LEADERBOARD
        else:
            pygame.draw.rect(screen, GREEN, leaderboard_button, border_radius=10)
        draw_text(screen, "排行榜", font_md, leaderboard_button.centerx, leaderboard_button.centery, BLACK)

    elif game_state == STATE_ENTER_NAME:
        if background_img:
            screen.blit(background_img, (0, 0))
        else:
            screen.fill(BLACK)

        draw_text(screen, "新高分!", font_lg, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
        draw_text(screen, f"你的分數: {score}", font_md, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50)
        draw_text(screen, "輸入你的名字:", font_sm, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 10)

        # 繪製輸入框
        input_rect = pygame.Rect(SCREEN_WIDTH/2 - 150, SCREEN_HEIGHT / 2 + 50, 300, 50)
        pygame.draw.rect(screen, WHITE, input_rect, 2, border_radius=5)

        # 繪製玩家輸入的文字 (靠左對齊)
        text_surface = font_md.render(player_name_input, True, WHITE)
        screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 5))

        # 繪製閃爍的游標
        now = pygame.time.get_ticks()
        if now - last_cursor_toggle > 500: # 每 500 毫秒閃爍一次
            cursor_visible = not cursor_visible
            last_cursor_toggle = now
        
        if cursor_visible:
            cursor_pos_x = input_rect.x + 10 + text_surface.get_width()
            if not player_name_input:
                cursor_pos_x += 5
            pygame.draw.line(screen, WHITE, (cursor_pos_x, input_rect.y + 10), (cursor_pos_x, input_rect.y + 40), 2)

        draw_text(screen, "輸入完畢後請按 Enter", font_sm, SCREEN_WIDTH / 2, input_rect.bottom + 40)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    save_score(player_name_input, score)
                    game_state = STATE_LEADERBOARD
                elif event.key == pygame.K_BACKSPACE:
                    player_name_input = player_name_input[:-1]
                elif len(player_name_input) < MAX_NAME_LENGTH:
                    player_name_input += event.unicode

    elif game_state == STATE_LEADERBOARD:
        if background_img:
            screen.blit(background_img, (0, 0))
        else:
            screen.fill(BLACK)

        draw_text(screen, "排行榜", font_lg, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 8)

        high_scores = load_scores()
        if not high_scores:
            draw_text(screen, "尚無紀錄", font_md, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        else:
            y_pos = SCREEN_HEIGHT / 4
            for i, (name, s) in enumerate(high_scores):
                # 分別繪製排名、姓名、分數，以利對齊
                rank_text = f"第 {i+1} 名:"
                score_text = f"{s}"
                
                draw_text(screen, rank_text, font_md, SCREEN_WIDTH * 0.25, y_pos + i * 50)
                draw_text(screen, name, font_md, SCREEN_WIDTH * 0.5, y_pos + i * 50)
                draw_text(screen, score_text, font_md, SCREEN_WIDTH * 0.75, y_pos + i * 50)

        # 返回主選單按鈕
        mouse_pos = pygame.mouse.get_pos()
        back_button = pygame.Rect(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT * 7/8 - 25, 200, 50)

        if back_button.collidepoint(mouse_pos):
            pygame.draw.rect(screen, LIGHT_GREEN, back_button, border_radius=10)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    game_state = STATE_MENU
        else:
            pygame.draw.rect(screen, GREEN, back_button, border_radius=10)
        
        draw_text(screen, "返回", font_md, back_button.centerx, back_button.centery, BLACK)

    # 更新螢幕
    pygame.display.flip()

pygame.quit()