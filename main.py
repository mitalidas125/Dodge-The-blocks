# doge_dodge.py
# Simple "Doge: Dodge the Blocks" endless dodger using pygame.
# Requires: pygame (pip install pygame)
# Optional: place a doge image named 'doge.png' in the same folder to use as player sprite.

import pygame
import random
import os
import sys

# --------- Config ----------
WIDTH, HEIGHT = 640, 480
FPS = 60
PLAYER_SPEED = 6
BLOCK_MIN_SIZE = 30
BLOCK_MAX_SIZE = 70
BLOCK_BASE_SPEED = 3
SPAWN_INTERVAL = 900  # milliseconds initial
DIFFICULTY_INCREASE_EVERY_MS = 8000  # increase difficulty every X ms
MAX_SPAWN_SPEEDUP = 0.65
FONT_NAME = None  # default font
DOGE_IMAGE = "doge.png"  # optional file
# ---------------------------

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Doge: Dodge the Blocks")
clock = pygame.time.Clock()
font = pygame.font.Font(FONT_NAME, 24)
big_font = pygame.font.Font(FONT_NAME, 48)

# Load doge image if available
player_image = None
if os.path.exists(DOGE_IMAGE):
    try:
        img = pygame.image.load(DOGE_IMAGE).convert_alpha()
        # scale image reasonably
        img = pygame.transform.smoothscale(img, (64, 64))
        player_image = img
    except Exception as e:
        print("Failed to load doge image:", e)

# Helper functions
def draw_text(surf, text, size, x, y, center=False):
    if size >= 36:
        f = pygame.font.Font(FONT_NAME, size)
    else:
        f = font
    text_surf = f.render(str(text), True, (255,255,255))
    text_rect = text_surf.get_rect()
    if center:
        text_rect.center = (x,y)
    else:
        text_rect.topleft = (x,y)
    surf.blit(text_surf, text_rect)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.width = 48
        self.height = 48
        if player_image:
            self.image = player_image
            self.rect = self.image.get_rect()
        else:
            self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, (200,180,60), (0,0,self.width,self.height))
            # draw DOGE text
            small = pygame.font.Font(FONT_NAME, 16)
            txt = small.render("DOGE", True, (0,0,0))
            trect = txt.get_rect(center=(self.width//2, self.height//2))
            self.image.blit(txt, trect)
            self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10
        self.speed = PLAYER_SPEED

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        # keep inside screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

class Block(pygame.sprite.Sprite):
    def __init__(self, speed_multiplier=1.0):
        super().__init__()
        sz = random.randint(BLOCK_MIN_SIZE, BLOCK_MAX_SIZE)
        self.image = pygame.Surface((sz, sz))
        self.color = (random.randint(40,220), random.randint(40,220), random.randint(40,220))
        self.image.fill(self.color)
        # add darker border
        pygame.draw.rect(self.image, (max(0,self.color[0]-40),max(0,self.color[1]-40),max(0,self.color[2]-40)), self.image.get_rect(), 3)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = -self.rect.height
        base = BLOCK_BASE_SPEED
        self.speed = base + random.random()*2
        self.speed *= speed_multiplier

    def update(self):
        self.rect.y += self.speed
        # remove if off-screen
        if self.rect.top > HEIGHT + 50:
            self.kill()

def game_loop():
    # groups
    player = Player()
    player_group = pygame.sprite.GroupSingle(player)
    blocks = pygame.sprite.Group()

    score = 0
    start_ticks = pygame.time.get_ticks()
    last_spawn = pygame.time.get_ticks()
    spawn_interval = SPAWN_INTERVAL
    running = True
    game_over = False
    last_difficulty = start_ticks

    # Sounds (optional) - simple beep using pygame.mixer if available
    # (we won't fail if mixer init or files missing)
    try:
        pygame.mixer.init()
        hit_sound = None
        # If you want, add sound files and load them here.
    except:
        hit_sound = None

    while running:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True  # restart
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        keys = pygame.key.get_pressed()
        if not game_over:
            player.update(keys)
            blocks.update()

            # spawn blocks
            if now - last_spawn > spawn_interval:
                # speed multiplier scales up as time passes
                elapsed = now - start_ticks
                speed_mult = 1.0 + min(2.0, elapsed / 20000.0)
                b = Block(speed_multiplier=speed_mult)
                blocks.add(b)
                last_spawn = now

            # difficulty ramp: every DIFFICULTY_INCREASE_EVERY_MS, lower spawn_interval
            if now - last_difficulty > DIFFICULTY_INCREASE_EVERY_MS:
                spawn_interval = int(max(200, spawn_interval * 0.92))
                last_difficulty = now

            # scoring: time-based + small bonus per dodged block
            score = int((now - start_ticks) / 100)

            # collision detection
            if pygame.sprite.spritecollide(player, blocks, dokill=False):
                game_over = True
                # optional sound
                if hit_sound:
                    try:
                        hit_sound.play()
                    except:
                        pass

        # drawing
        screen.fill((25, 25, 30))
        # ground
        pygame.draw.rect(screen, (40,40,50), (0, HEIGHT-8, WIDTH, 8))

        blocks.draw(screen)
        player_group.draw(screen)

        # HUD
        draw_text(screen, f"Score: {score}", 24, 8, 8)
        draw_text(screen, "Move: ← → or A D  —  Restart: R  Quit: Esc", 16, 8, HEIGHT-28)

        if game_over:
            # overlay
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0,0,0,150))
            screen.blit(s, (0,0))
            draw_text(screen, "GAME OVER", 56, WIDTH//2, HEIGHT//2 - 40, center=True)
            draw_text(screen, f"Final score: {score}", 28, WIDTH//2, HEIGHT//2 + 10, center=True)
            draw_text(screen, "Press R to restart or Esc to quit", 20, WIDTH//2, HEIGHT//2 + 50, center=True)

        pygame.display.flip()

    return False

def main_menu():
    while True:
        screen.fill((12,12,14))
        draw_text(screen, "Doge: Dodge the Blocks", 48, WIDTH//2, HEIGHT//3, center=True)
        draw_text(screen, "Avoid falling blocks. Use left/right. Press Space to start.", 20, WIDTH//2, HEIGHT//2, center=True)
        draw_text(screen, "Optional: put a 'doge.png' image in the folder to use as the player sprite.", 18, WIDTH//2, HEIGHT//2 + 40, center=True)
        draw_text(screen, "Press Space to start, Esc to quit", 20, WIDTH//2, HEIGHT//2 + 90, center=True)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
        clock.tick(30)

if __name__ == "__main__":
    # simple loop: show menu, run game, optionally restart
    while True:
        main_menu()
        restart = game_loop()
        if not restart:
            break
