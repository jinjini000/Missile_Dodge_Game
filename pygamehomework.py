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
        self.font_large = pygame.font.SysFont('Arial', 80)
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

class MyDisplay():
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
class Func():
    def __init__(self):
        self.consts = Consts()
        self.colors = Colors()
        self.fonts = Fonts()

    # --- 헬퍼 함수 ---
    def get_random_spawn_point(self, width, height):
        side = random.randint(0, 3)
        if side == 0: 
            x = random.uniform(0, width)
            y = -50 
        elif side == 1: 
            x = random.uniform(0, width)
            y = height + 50
        elif side == 2: 
            x = -50
            y = random.uniform(0, height)
        else: 
            x = width + 50
            y = random.uniform(0, height)
        return (x, y)

    def draw_warning(self, screen, target_pos, screen_width, screen_height):
        center_x, center_y = screen_width // 2, screen_height // 2
        if 0 <= target_pos[0] <= screen_width and 0 <= target_pos[1] <= screen_height:
            return
        indicator_x = max(10, min(screen_width - 10, target_pos[0]))
        indicator_y = max(10, min(screen_height - 10, target_pos[1]))
        if target_pos[0] < 0: indicator_x = 10
        elif target_pos[0] > screen_width: indicator_x = screen_width - 10
        if target_pos[1] < 0: indicator_y = 10
        elif target_pos[1] > screen_height: indicator_y = screen_height - 10
        indicator_pos = pygame.Vector2(indicator_x, indicator_y)
        center_pos = pygame.Vector2(center_x, center_y)
        vec_to_center = center_pos - indicator_pos
        target_angle_deg = math.degrees(math.atan2(-vec_to_center.y, vec_to_center.x)) - 90
        arrow_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
        pts = [(15, 0), (30, 30), (0, 30)] 
        pygame.draw.polygon(arrow_surface, self.colors.yellow, pts)
        rotated_arrow = pygame.transform.rotate(arrow_surface, target_angle_deg)
        rotated_rect = rotated_arrow.get_rect(center=indicator_pos)
        screen.blit(rotated_arrow, rotated_rect)
        

    def draw_large_text(self, surface, text, color, y_offset=0):
        text_surface = self.fonts.font_large.render(text, True, color) 
        text_rect = text_surface.get_rect()           
        text_rect.center = (self.consts.screen_width // 2, self.consts.screen_height // 2 + y_offset)
        surface.blit(text_surface, text_rect)         

    def draw_score(self, surface, text, color, x, y):
        text_surface = self.fonts.font_score.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.topright = (x, y) 
        surface.blit(text_surface, text_rect)

    def draw_flare_count(self, surface, count, max_count):
        text = f"FLARES: {count}/{max_count}"
        color = self.colors.white
        if count == 0:
            color = self.colors.red
        elif count == 1:
            color = self.colors.yellow
            
        text_surface = self.fonts.font_flare_count.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.topleft = (10, 10) 
        surface.blit(text_surface, text_rect)



class EventService():
    def __init__(self):
        self.colors = Colors()
        self.fonts = Fonts()
        self.consts = Consts()
        self.func = Func()
        self.mydisplay = MyDisplay()

class Main():
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.colors = Colors()
        self.fonts = Fonts()
        self.consts = Consts()
        self.func = Func()
        self.mydisplay = MyDisplay()
        self.eventService = EventService()
        self.img = ImgLoad()
        self.running = True
    
        # 게임 변수 초기화 함수
    def reset_game(self):
            global game_state, countdown_start_time, score, game_start_time
            global player_x, player_y, player_vx, player_vy
            global missiles, next_missile_score
            global warning_active, warning_start_time, spawn_position
            global first_missile_spawned 
            global flares, flares_remaining 
            
            game_state = self.consts.game_state_countdown
            countdown_start_time = pygame.time.get_ticks() 
            score = 0
            game_start_time = 0
            
            player_x = self.consts.player_x_start
            player_y = self.consts.player_y_start
            player_vx = 0.0
            player_vy = 0.0
            
            missiles = [] 
            flares = [] 
            flares_remaining = self.consts.max_flares
            next_missile_score = self.consts.score_spawn_interval
            warning_active = False
            warning_start_time = 0
            first_missile_spawned = False
        
    
    def run(self):
        self.reset_game()
        global game_state, countdown_start_time, score, game_start_time
        global player_x, player_y, player_vx, player_vy
        global missiles, next_missile_score
        global warning_active, warning_start_time, spawn_position
        global first_missile_spawned 
        global flares, flares_remaining 
        
        self.running = True
        while self.running:
            current_time = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
                if game_state == self.consts.game_state_gameover and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                
                # --- 스페이스바 플레어 발사 로직 (횟수 제한 적용) ---
                if game_state == self.consts.game_state_playing and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if flares_remaining > 0: 
                            flare_x = player_x + self.consts.player_size // 2
                            flare_y = player_y + self.consts.player_size // 2
                            new_flare = Flare(flare_x, flare_y, current_time)
                            flares.append(new_flare)
                            flares_remaining -= 1
            keys = pygame.key.get_pressed()
            
            if game_state == self.consts.game_state_countdown:
                elapsed_time = (current_time - countdown_start_time) / 1000.0
                time_left = self.consts.countdown_time - elapsed_time
                
                if time_left <= 0:
                    game_state = self.consts.game_state_playing
                    game_start_time = current_time 
                    
                self.mydisplay.screen.fill(self.colors.black)
                if time_left > 0:
                    countdown_number = math.ceil(time_left)
                    self.func.draw_large_text(self.mydisplay.screen, str(countdown_number), self.colors.white)
                else:
                    self.func.draw_large_text(self.mydisplay.screen, "GO!", self.colors.red)

            elif game_state == self.consts.game_state_playing:
                
                # 1. 점수 및 미사일 생성/경고 로직
                time_elapsed_ms = current_time - game_start_time
                score = int(time_elapsed_ms / 10) 
                
                if not first_missile_spawned and not warning_active:
                    if time_elapsed_ms >= self.consts.first_missile_delay_ms:
                        warning_active = True; warning_start_time = current_time
                        spawn_position = self.func.get_random_spawn_point(self.consts.screen_width, self.consts.screen_height)
                        first_missile_spawned = True 
                
                if score >= next_missile_score and not warning_active and first_missile_spawned:
                    warning_active = True; warning_start_time = current_time
                    spawn_position = self.func.get_random_spawn_point(self.consts.screen_width, self.consts.screen_height)
                    next_missile_score += self.consts.score_spawn_interval
                    
                if warning_active and (current_time - warning_start_time) >= self.consts.warning_time_ms:
                    new_missile = Missile(spawn_position[0], spawn_position[1])
                    missiles.append(new_missile); warning_active = False 
                    
                # 2. 플레이어 위치 및 관성 계산
                if keys[pygame.K_LEFT]: player_vx -= self.consts.player_accel_rate
                if keys[pygame.K_RIGHT]: player_vx += self.consts.player_accel_rate
                if keys[pygame.K_UP]: player_vy -= self.consts.player_accel_rate
                if keys[pygame.K_DOWN]: player_vy += self.consts.player_accel_rate
                
                player_vx *= self.consts.player_drag
                player_vy *= self.consts.player_drag
                current_player_speed = math.sqrt(player_vx**2 + player_vy**2)
                if current_player_speed > self.consts.player_max_speed:
                    ratio = self.consts.player_max_speed / current_player_speed
                    player_vx *= ratio; player_vy *= ratio
                player_x += player_vx; player_y += player_vy

                if player_x < 0: player_x = 0; player_vx = 0
                elif player_x > self.consts.screen_width - self.consts.player_size: player_x = self.consts.screen_width - self.consts.player_size; player_vx = 0
                if player_y < 0: player_y = 0; player_vy = 0
                elif player_y > self.consts.screen_height - self.consts.player_size: player_y = self.consts.screen_height - self.consts.player_size; player_vy = 0
                
                # 3. 플레어 소멸 로직
                flares_to_keep = []
                for flare in flares:
                    if not flare.is_expired(current_time):
                        flares_to_keep.append(flare)
                flares = flares_to_keep

                # 4. 미사일 업데이트 및 충돌 감지
                missiles_to_keep = []
                is_hit = False
                
                for missile in missiles:
                    missile.update(player_x, player_y, self.consts.player_size, flares) 
                    
                    player_rect = pygame.Rect(player_x, player_y, self.consts.player_size, self.consts.player_size)
                    missile_rect = pygame.Rect(missile.x, missile.y, missile.size*0.8, missile.size * 0.8) 
                    
                    if player_rect.colliderect(missile_rect):
                        is_hit = True
                    
                    hit_flare = False
                    for flare in flares:
                        dist_to_flare = math.sqrt((missile.x + missile.size/2 - flare.x)**2 + (missile.y + missile.size - flare.y)**2)
                        if dist_to_flare < (missile.size/2 + self.consts.flare_max_size / 2):
                            hit_flare = True
                            break

                    if not is_hit and not hit_flare:
                        missiles_to_keep.append(missile)

                missiles = missiles_to_keep
                
                if is_hit:
                    game_state = self.consts.game_state_gameover
                    
                # 5. 화면 그리기
                self.mydisplay.screen.fill(self.colors.black)
                
                # 플레이어 그리기
                angle = 0
                if player_vx != 0 or player_vy != 0: angle = math.degrees(math.atan2(-player_vy, player_vx)); angle -= 90 
                rotated_player_image = pygame.transform.rotate(self.img.player_image, angle)
                player_rect = rotated_player_image.get_rect(center=(int(player_x + self.consts.player_size // 2), int(player_y + self.consts.player_size // 2)))
                self.mydisplay.screen.blit(rotated_player_image, player_rect)
                
                # 플레어 그리기
                for flare in flares:
                    flare.draw(self.mydisplay.screen, current_time)
                
                # 미사일 그리기 및 화면 밖 경고 표시
                for missile in missiles:
                    missile.draw(self.mydisplay.screen)
                    
                    if missile.is_outside_screen(self.consts.screen_width, self.consts.screen_height):
                        self.func.draw_warning(self.mydisplay.screen, (missile.x, missile.y), self.consts.screen_width, self.consts.screen_height)

                if warning_active:
                    self.func.draw_warning(self.mydisplay.screen, spawn_position, self.consts.screen_width, self.consts.screen_height)
                    
                # --- UI 그리기 ---
                score_text = f"SCORE: {score}"
                self.func.draw_score(self.mydisplay.screen, score_text, self.colors.white, self.consts.screen_width - 10, 10)
                self.func.draw_flare_count(self.mydisplay.screen, flares_remaining, self.consts.max_flares)
                # ------------------

            elif game_state == self.consts.game_state_gameover:
                self.mydisplay.screen.fill(self.colors.black)
                
                self.func.draw_large_text(self.mydisplay.screen, "GAME OVER", self.colors.red, y_offset=-50)
                
                final_score_text = f"Final Score: {score}"
                final_score_surface = self.fonts.font_score.render(final_score_text, True, self.colors.white)
                final_score_rect = final_score_surface.get_rect(center=(self.consts.screen_width // 2, self.consts.screen_height // 2 + 50))
                self.mydisplay.screen.blit(final_score_surface, final_score_rect)
                
                self.func.draw_score(self.mydisplay.screen, "Press R to RESTART", self.colors.white, self.consts.screen_width // 2 + 200, self.consts.screen_height // 2 + 100)
                    
            pygame.display.flip()
            self.clock.tick(60)
        

main = Main()

main.run()
pygame.quit()
