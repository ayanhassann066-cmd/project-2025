import pygame
import random
import sys
import os

# Always load files relative to where this script is
os.chdir(r"C:\Users\user\Downloads\groupproject")

# === Global settings ===
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)


# === Utility: Safe image loader ===
def load_image(path, size=None):
    """Try to load and scale an image. Return None if not found."""
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except Exception:
        print(f"{path} not found, using fallback.")
        return None

# === AYAN: Player Mechanics ===
class Player:
    def __init__(self, x, y, width=50, height=30, speed=5, lives=3, image=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.lives = lives
        self.image = image
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.cooldown = 0

    def handle_input(self, keys):
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        self.rect.topleft = (self.x, self.y)

    def can_shoot(self):
        return self.cooldown == 0

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1
        self.rect.topleft = (self.x, self.y)

    def shoot(self):
        self.cooldown = 5
        bullet_x = self.x + self.width // 2
        bullet_y = self.y
        return Bullet(bullet_x, bullet_y, -8, True)

    def draw(self, surface):
        if isinstance(self.image, pygame.Surface):
            surface.blit(self.image, self.rect.topleft)
        else:
            pygame.draw.rect(surface, (0, 255, 0), self.rect)

    def hit(self):
        self.lives -= 1
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - 80
        self.rect.topleft = (self.x, self.y)

# === Shared Bullet Class ===
class Bullet:
    def __init__(self, x, y, dy, from_player):
        self.x = x
        self.y = y
        self.dy = dy
        self.from_player = from_player
        self.rect = pygame.Rect(self.x, self.y, 4, 10)

    def update(self):
        self.y += self.dy
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        color = YELLOW if self.from_player else RED
        pygame.draw.rect(surface, color, self.rect)

    def off_screen(self):
        return self.y < -10 or self.y > SCREEN_HEIGHT + 10


# === AHMED: Invader AI & Speed Dynamics ===
class Invader:
    def __init__(self, x, y, inv_type=0, image=None):
        self.x = x
        self.y = y
        self.type = inv_type
        self.image = image
        self.rect = pygame.Rect(self.x, self.y, 40, 25)

    def draw(self, surface):
        if isinstance(self.image, pygame.Surface):
            surface.blit(self.image, self.rect.topleft)
        else:
            pygame.draw.rect(surface, (0, 200, 255), self.rect)


class InvaderManager:
    def __init__(self, rows=5, cols=10, invader_images=None):
        self.invaders = []
        self.direction = 1
        self.base_speed = 1.0
        self.speed = self.base_speed
        self.invader_images = invader_images or [None, None, None]
        self.create_invaders()
        self.initial_count = len(self.invaders)
        self.time_elapsed = 0

    def create_invaders(self):
        start_x, start_y = 80, 60
        for row in range(5):
            for col in range(10):
                x = start_x + col * 50
                y = start_y + row * 40
                inv_type = row % 3
                img = self.invader_images[inv_type]
                self.invaders.append(Invader(x, y, inv_type, img))

    def update(self):
        """Move invaders left and right only."""
        if not self.invaders:
            return
        hit_edge = False
        for inv in self.invaders:
            inv.x += self.speed * self.direction
            inv.rect.topleft = (inv.x, inv.y)
            if inv.rect.right >= SCREEN_WIDTH - 10 or inv.rect.left <= 10:
                hit_edge = True
        if hit_edge:
            self.direction *= -1
        self.recalculate_speed()

    def recalculate_speed(self):
        remaining = len(self.invaders)
        if remaining <= 0:
            self.speed = self.base_speed
        else:
            killed = self.initial_count - remaining
            self.speed = self.base_speed + (0.05 * killed) + (self.time_elapsed / 5000)

    def draw(self, surface):
        for inv in self.invaders:
            inv.draw(surface)

    def shoot_random(self):
        if not self.invaders:
            return None
        difficulty_scale = max(0.02, 0.08 * (1 - len(self.invaders) / self.initial_count))
        if random.random() < difficulty_scale:
            shooter = random.choice(self.invaders)
            bullet_x = shooter.x + shooter.rect.width // 2
            bullet_y = shooter.y + shooter.rect.height
            return Bullet(bullet_x, bullet_y, 5, False)
        return None

# === HADI: Barrier System (Seamless Cell-Based Destruction) ===
class Barrier:
    """Barrier looks like a single block, but internally is made of cells that can disappear individually."""

    def __init__(self, x, y, cell_size=6, cols=15, rows=10, color=(0, 255, 0)):
        self.x = x
        self.y = y
        self.cell_size = cell_size
        self.cols = cols
        self.rows = rows
        self.color = color
        self.cells = [[True for _ in range(cols)] for _ in range(rows)]
        self.width = cols * cell_size
        self.height = rows * cell_size
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.surface.get_rect(topleft=(x, y))
        self.redraw()

    def redraw(self):
        """Redraw solid surface without visible gaps, with transparent holes where destroyed."""
        self.surface.fill((0, 0, 0, 0))
        for r in range(self.rows):
            for c in range(self.cols):
                if self.cells[r][c]:
                    cell_rect = pygame.Rect(
                        c * self.cell_size,
                        r * self.cell_size,
                        self.cell_size,
                        self.cell_size,
                    )
                    pygame.draw.rect(self.surface, self.color, cell_rect)

    def draw(self, surface):
        surface.blit(self.surface, (self.x, self.y))

    def hit(self, bullet_rect):
        """Deactivate only the specific cell that was hit and update."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.cells[r][c]:
                    cell_rect = pygame.Rect(
                        self.x + c * self.cell_size,
                        self.y + r * self.cell_size,
                        self.cell_size,
                        self.cell_size,
                    )
                    if bullet_rect.colliderect(cell_rect):
                        self.cells[r][c] = False
                        self.redraw()
                        return True
        return False


def create_barriers():

# === Sound Handling ===
 def load_sound(filename):
    try:
        return pygame.mixer.Sound(filename)
    except Exception:
        print(f"Sound {filename} not found.")
        return None


# === Collision Handlers ===
def handle_bullet_invader_collisions(player_bullets, invader_manager, hit_sound):
    score = 0
    for bullet in list(player_bullets):
        for inv in list(invader_manager.invaders):
            if bullet.rect.colliderect(inv.rect):
                player_bullets.remove(bullet)
                invader_manager.invaders.remove(inv)
                if hit_sound: hit_sound.play()
                score += 10
                break
    return score


def handle_bullet_barrier_collisions(barriers, bullets, hit_sound):
    for bullet in list(bullets):
        for barrier in barriers:
            if barrier.rect.colliderect(bullet.rect):
                if barrier.hit(bullet.rect):
                    bullets.remove(bullet)
                    if hit_sound: hit_sound.play()
                    break


def handle_enemy_bullets_player_collisions(enemy_bullets, player, hit_sound):
    for bullet in list(enemy_bullets):
        if bullet.rect.colliderect(player.rect):
            enemy_bullets.remove(bullet)
            if hit_sound: hit_sound.play()
            player.hit()
            break


# === MAIN GAME ===
def main():
    pygame.init()
    pygame.display.set_caption("COM4008 Space Invaders – Final Group Project")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    background_img = load_image("background.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
    player_img = load_image("player.png", (50, 30))
    invader_images = [
        load_image("invader0.png", (40, 25)),
        load_image("invader1.png", (40, 25)),
        load_image("invader2.png", (40, 25)),
    ]

    hit_sound = load_sound("bullet_hit.wav")

    try:
        pygame.mixer.music.load("background.mp3")
        pygame.mixer.music.play(-1)
    except Exception:
        print("No background music found. Continuing silently.")

    player = Player(SCREEN_WIDTH // 2 - 25, SCREEN_HEIGHT - 80, image=player_img)
    invader_manager = InvaderManager(invader_images=invader_images)
    barriers = create_barriers()
    player_bullets, enemy_bullets = [], []
    score = 0
    font = pygame.font.SysFont("consolas", 24)
    game_over = False
    start_ticks = pygame.time.get_ticks()

    running = True
    while running:
        clock.tick(FPS)
        elapsed = pygame.time.get_ticks() - start_ticks
        invader_manager.time_elapsed = elapsed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if not game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.can_shoot():
                    player_bullets.append(player.shoot())
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif game_over and event.type == pygame.KEYDOWN:
                running = False

        keys = pygame.key.get_pressed()
        if not game_over:
            player.handle_input(keys)
            player.update()
            invader_manager.update()

            new_bullet = invader_manager.shoot_random()
            if new_bullet:
                enemy_bullets.append(new_bullet)

            for bullet in player_bullets + enemy_bullets:
                bullet.update()

            player_bullets[:] = [b for b in player_bullets if not b.off_screen()]
            enemy_bullets[:] = [b for b in enemy_bullets if not b.off_screen()]

            score += handle_bullet_invader_collisions(player_bullets, invader_manager, hit_sound)
            handle_bullet_barrier_collisions(barriers, player_bullets, hit_sound)
            handle_bullet_barrier_collisions(barriers, enemy_bullets, hit_sound)
            handle_enemy_bullets_player_collisions(enemy_bullets, player, hit_sound)

            if player.lives <= 0 or not invader_manager.invaders:
                game_over = True

        if background_img:
            screen.blit(background_img, (0, 0))
        else:
            screen.fill(BLACK)

        player.draw(screen)
        invader_manager.draw(screen)
        for b in player_bullets + enemy_bullets:
            b.draw(screen)
        for barrier in barriers:
            barrier.draw(screen)

        score_text = font.render(f"Score: {score}", True, WHITE)
        lives_text = font.render(f"Lives: {player.lives}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH - 150, 10))
        screen.blit(lives_text, (10, 10))

        if game_over:
            msg = "GAME OVER" if player.lives <= 0 else "YOU WIN!"
            msg_surface = font.render(msg, True, RED)
            info_surface = font.render("Press any key to exit", True, WHITE)
            screen.blit(msg_surface, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 20))
            screen.blit(info_surface, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


# === RUN THE GAME ===
if __name__ == "__main__":
    main()
  