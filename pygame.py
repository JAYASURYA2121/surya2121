import pygame
import random
from enum import Enum

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Create screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple Game - Collect the Coins!")

# Clock for FPS
clock = pygame.time.Clock()
FPS = 60

# Font for text
font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 72)


class Player(pygame.sprite.Sprite):
    """Player character"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 5
        self.health = 3

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.x > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.x < SCREEN_WIDTH - self.rect.width:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.y > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.y < SCREEN_HEIGHT - self.rect.height:
            self.rect.y += self.speed

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Coin(pygame.sprite.Sprite):
    """Collectible coin"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Enemy(pygame.sprite.Sprite):
    """Enemy that chases the player"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 2

    def update(self, player):
        # Simple chase logic
        if self.rect.x < player.rect.x:
            self.rect.x += self.speed
        elif self.rect.x > player.rect.x:
            self.rect.x -= self.speed

        if self.rect.y < player.rect.y:
            self.rect.y += self.speed
        elif self.rect.y > player.rect.y:
            self.rect.y -= self.speed

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Game:
    """Main game class"""
    def __init__(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.coins = []
        self.enemies = []
        self.score = 0
        self.running = True
        self.game_over = False

        # Spawn initial coins
        for _ in range(5):
            self.spawn_coin()

        # Spawn initial enemies
        for _ in range(2):
            self.spawn_enemy()

    def spawn_coin(self):
        x = random.randint(0, SCREEN_WIDTH - 20)
        y = random.randint(0, SCREEN_HEIGHT - 20)
        self.coins.append(Coin(x, y))

    def spawn_enemy(self):
        x = random.randint(0, SCREEN_WIDTH - 30)
        y = random.randint(0, SCREEN_HEIGHT - 30)
        self.enemies.append(Enemy(x, y))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.game_over:
                    self.__init__()  # Restart game

    def update(self):
        if not self.game_over:
            self.player.update()

            # Update enemies
            for enemy in self.enemies:
                enemy.update(self.player)

            # Check coin collection
            coins_to_remove = []
            for coin in self.coins:
                if self.player.rect.colliderect(coin.rect):
                    self.score += 10
                    coins_to_remove.append(coin)
                    self.spawn_coin()

            for coin in coins_to_remove:
                self.coins.remove(coin)

            # Check enemy collision
            for enemy in self.enemies:
                if self.player.rect.colliderect(enemy.rect):
                    self.player.health -= 1
                    self.player.rect.x = SCREEN_WIDTH // 2
                    self.player.rect.y = SCREEN_HEIGHT // 2

            # Check game over
            if self.player.health <= 0:
                self.game_over = True

            # Spawn more enemies as score increases
            if self.score > 0 and self.score % 50 == 0 and len(self.enemies) < 5:
                self.spawn_enemy()

    def draw(self):
        screen.fill(BLACK)

        # Draw all game objects
        self.player.draw(screen)
        for coin in self.coins:
            coin.draw(screen)
        for enemy in self.enemies:
            enemy.draw(screen)

        # Draw UI
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        health_text = font.render(f"Health: {self.player.health}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(health_text, (10, 50))

        # Draw game over screen
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            game_over_text = large_font.render("GAME OVER", True, RED)
            final_score_text = font.render(f"Final Score: {self.score}", True, WHITE)
            restart_text = font.render("Press SPACE to restart", True, WHITE)

            screen.blit(
                game_over_text,
                (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 150),
            )
            screen.blit(
                final_score_text,
                (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, 250),
            )
            screen.blit(
                restart_text,
                (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 350),
            )

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
