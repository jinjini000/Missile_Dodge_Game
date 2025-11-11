import pygame
import math
import random
pygame.init()

class Colors():
    def __init__(self):
        self.black = (0, 0, 0)
        self.white = (255, 255, 255) 
        self.red = (255, 0, 0)     
        self.yellow = (255, 255, 0) 
        self.flare_core_color = (255, 220, 100) 
        self.flare_outer_color = (255, 120, 0)

class Fonts():
    def __init__(self):
        self.font_larege = pygame.font.SysFont('Arial', 80)
        self.font_score = pygame.font.SysFont('Arial', 30) 
        self.font_flare_count = pygame.font.SysFont('Arial', 24, bold=True)

class Consts():
    def __init__(self):
        self.screen_width = 1200
        self.screen_height = 720
        self.game_state_countdown = 0
        self.game_state_playing = 1
        self.game_state_gameover = 2

        self.countdown_time = 5.0
        self.player_accel_rate = 0.5
        self.player_max_speed = 7.0
        self.player_drag = 0.97

        # 미사일 상수
        self.missile_acceleration = 0.6
        self.missile_max_speed = 17.0
        self.missile_drag = 0.999 # 2 -> 0.999로 현실적인 관성값으로 수정 (2는 미사일 속도를 비정상적으로 높임)

        # 회피 관련 상수
        self.evasion_distance = 700
        self.proximity_time_threshold = 120
        self.repel_strength = 0.5
        self.evasion_duration = 90

        # 점수 및 경고 시스템 상수
        self.score_spawn_interval = 1000
        self.warning_time_ms = 1500
        self.first_missile_delay_ms = 3000

        # --- 플레어 상수 (수정) ---
        self.flare_duration_ms = 1500
        self.flare_max_size = 25
        self.flare_initial_size = 5
        self.max_flares = 3

        # 3. 플레이어 객체 설정 
        self.player_size = 64 
        self.player_x_start = float(self.screen_width // 2 - self.player_size // 2)
        self.player_y_start = float(self.screen_height // 2 - self.player_size // 2)

class Screen():
    def __init__(self):
        self.consts = Consts()
        self.screen = pygame.display.set_mode((self.consts.screen_width, self.consts.screen_height))
        pygame.display.set_caption("미사일 회피 게임")

class ImgLoad():
    def __init__(self):
        self.consts = Consts()
        try:
            original_player_image = pygame.image.load('player_plane.png').convert_alpha()
            self.player_image = pygame.transform.scale(original_player_image, (self.consts.player_size, self.consts.player_size))
            original_missile_image = pygame.image.load('missile.png').convert_alpha()
            self.missile_image = pygame.transform.scale(original_missile_image, (32, 64)) 
        except pygame.error as e:
            print(f"Error loading image: {e}")
            print("Ensure 'player_plane.png' and 'missile.png' files are present.")
            pygame.quit()
            exit()

class Flare:
    def __init__(self, center_x, center_y, spawn_time):
        self.consts = Consts()
        self.colors = Colors()
        self.x = center_x
        self.y = center_y
        self.spawn_time = spawn_time
        self.rect = pygame.Rect(self.x - self.consts.flare_initial_size, self.y - self.consts.flare_initial_size, self.consts.flare_initial_size * 2, self.consts.flare_initial_size * 2)

    def is_expired(self, current_time):
        return (current_time - self.spawn_time) >= self.consts.flare_duration_ms

    def get_current_size(self, elapsed_time):
        progress = elapsed_time / self.consts.flare_duration_ms
        
        if progress < 0.5:
            current_size = self.consts.flare_initial_size + (self.consts.flare_max_size - self.consts.flare_initial_size) * (progress * 2)
        else:
            current_size = self.consts.flare_max_size - (self.consts.flare_max_size - self.consts.flare_initial_size) * ((progress - 0.5) * 2)
        
        return max(1, current_size)

    def get_current_alpha(self, elapsed_time):
        fade_start_time = self.consts.flare_duration_ms * 0.8
        if elapsed_time > fade_start_time:
            fade_progress = (elapsed_time - fade_start_time) / (self.consts.flare_duration_ms - fade_start_time)
            alpha = 255 - int(255 * fade_progress)
            return max(0, alpha)
        return 255 

    def get_current_color(self, elapsed_time):
        progress = elapsed_time / self.consts.flare_duration_ms
        
        r = int(self.colors.flare_core_color[0] + (self.colors.flare_outer_color[0] - self.colors.flare_core_color[0]) * progress)
        g = int(self.colors.flare_core_color[1] + (self.colors.flare_outer_color[1] - self.colors.flare_core_color[1]) * progress)
        b = int(self.colors.flare_core_color[2] + (self.colors.flare_outer_color[2] - self.colors.flare_core_color[2]) * progress)
        
        return (r, g, b)

    def draw(self, screen, current_time):
        elapsed_time = current_time - self.spawn_time
        current_size = self.get_current_size(elapsed_time)
        current_alpha = self.get_current_alpha(elapsed_time)
        current_color = self.get_current_color(elapsed_time)

        flare_surface = pygame.Surface((current_size * 4, current_size * 4), pygame.SRCALPHA)
        flare_surface.fill((0,0,0,0)) 

        # 가장 안쪽 (가장 밝고 작음)
        pygame.draw.circle(flare_surface, (255, 255, 255, int(current_alpha * 0.9)), 
                           (flare_surface.get_width() // 2, flare_surface.get_height() // 2), 
                           int(current_size * 0.4))
        
        # 중간 (메인 색상)
        pygame.draw.circle(flare_surface, (current_color[0], current_color[1], current_color[2], int(current_alpha * 0.7)), 
                           (flare_surface.get_width() // 2, flare_surface.get_height() // 2), 
                           int(current_size * 0.7))
        
        # 가장 바깥쪽 (확산 효과)
        pygame.draw.circle(flare_surface, (self.colors.flare_outer_color[0], self.colors.flare_outer_color[1], self.colors.flare_outer_color[2], int(current_alpha * 0.4)), 
                           (flare_surface.get_width() // 2, flare_surface.get_height() // 2), 
                           int(current_size * 1.0))

        screen.blit(flare_surface, (self.x - flare_surface.get_width() // 2, self.y - flare_surface.get_height() // 2))

class Missile:
    def __init__(self, start_x, start_y):
        self.img = ImgLoad()
        self.consts = Consts()
        self.x = float(start_x)
        self.y = float(start_y)
        self.vx = 0.0
        self.vy = 0.0
        self.size = 32
        self.image = self.img.missile_image 
        
        self.evading = False
        self.evasion_timer = 0
        self.close_proximity_timer = 0
        
    def is_outside_screen(self, width, height):
        return (self.x < -50 or self.x > width + 50 or 
                self.y < -50 or self.y > height + 50)
        
    def update(self, player_x, player_y, player_size, active_flares):
        
        target_x = player_x + player_size // 2
        target_y = player_y + player_size // 2
        
        # 1. 타겟 결정 (플레어 유인 로직)
        closest_flare = None
        min_flare_distance = float('inf')
        
        if active_flares:
            for flare in active_flares:
                dx_f = flare.x - self.x
                dy_f = flare.y - self.y
                dist_f = math.sqrt(dx_f**2 + dy_f**2)
                
                if dist_f < min_flare_distance:
                    min_flare_distance = dist_f
                    closest_flare = flare

        # 2. 미사일 행동 로직: 플레어 추적 vs 플레이어 추적
        if closest_flare:
            tx, ty = closest_flare.x, closest_flare.y
            self.evading = False 
        else:
            tx, ty = target_x, target_y
            
        dx = tx - self.x
        dy = ty - self.y
        distance = math.sqrt(dx**2 + dy**2) 
        
        # 3. 회피/추적 가속 적용
        if closest_flare is None:
            if not self.evading:
                if distance < self.consts.evasion_distance:
                    self.close_proximity_timer += 1
                else: 
                    self.close_proximity_timer = 0
                    
                if self.close_proximity_timer >= self.consts.proximity_time_threshold:
                    self.evading = True
                    self.evasion_timer = self.consts.evasion_duration
                    self.close_proximity_timer = 0

            if self.evading:
                self.evasion_timer -= 1
                if self.evasion_timer <= 0: 
                    self.evading = False
                    
                self.vx -= dx * self.consts.repel_strength / 100.0
                self.vy -= dy * self.consts.repel_strength / 100.0
            else:
                self.vx += dx * self.consts.missile_acceleration / 100.0
                self.vy += dy * self.consts.missile_acceleration / 100.0
        else:
            self.vx += dx * self.consts.missile_acceleration / 100.0
            self.vy += dy * self.consts.missile_acceleration / 100.0

        # 4. 관성 및 속도 제한
        self.vx *= self.consts.missile_drag
        self.vy *= self.consts.missile_drag
        
        current_missile_speed = math.sqrt(self.vx**2 + self.vy**2)
        if current_missile_speed > self.consts.missile_max_speed:
            ratio = self.consts.missile_max_speed / current_missile_speed
            self.vx *= ratio
            self.vy *= ratio

        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        angle = 0
        if self.vx != 0 or self.vy != 0: 
            angle = math.degrees(math.atan2(-self.vy, self.vx)) - 90
        
        rotated_image = pygame.transform.rotate(self.image, angle)
        rect = rotated_image.get_rect(center=(int(self.x + self.size // 2), int(self.y + self.size // 2)))
        screen.blit(rotated_image, rect)

# 전역함수들
