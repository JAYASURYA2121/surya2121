import pygame
import random
import math
from enum import Enum
from dataclasses import dataclass

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
DARK_GREEN = (34, 139, 34)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Create screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Battle Royale Game")

# Clock for FPS
clock = pygame.time.Clock()
FPS = 60

# Font for text
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 18)
large_font = pygame.font.Font(None, 48)


@dataclass
class Vector2:
    """2D Vector class"""
    x: float
    y: float

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)

    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def normalize(self):
        dist = math.sqrt(self.x**2 + self.y**2)
        if dist == 0:
            return Vector2(0, 0)
        return Vector2(self.x / dist, self.y / dist)


class Weapon:
    """Weapon class"""
    def __init__(self, name, damage, fire_rate, ammo):
        self.name = name
        self.damage = damage
        self.fire_rate = fire_rate  # shots per second
        self.ammo = ammo
        self.max_ammo = ammo
        self.last_shot = 0

    def can_shoot(self, current_time):
        return (current_time - self.last_shot) >= (1000 / self.fire_rate)

    def shoot(self):
        if self.ammo > 0:
            self.ammo -= 1
            return True
        return False


class Loot:
    """Loot items on the ground"""
    def __init__(self, x, y, item_type, amount=1):
        self.x = x
        self.y = y
        self.item_type = item_type  # "weapon", "ammo", "health", "armor"
        self.amount = amount
        self.width = 20
        self.height = 20
        self.collected = False

        # Item colors
        self.color_map = {
            "weapon": ORANGE,
            "ammo": YELLOW,
            "health": GREEN,
            "armor": CYAN
        }

    def draw(self, surface):
        if not self.collected:
            color = self.color_map.get(self.item_type, GRAY)
            pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(surface, WHITE, (self.x, self.y, self.width, self.height), 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Player(pygame.sprite.Sprite):
    """Player character with health, weapons, and movement"""
    def __init__(self, x, y, player_id, is_player=False):
        super().__init__()
        self.x = x
        self.y = y
        self.player_id = player_id
        self.is_player = is_player  # True if controlled by keyboard
        self.width = 30
        self.height = 30

        # Stats
        self.health = 100
        self.max_health = 100
        self.armor = 0
        self.max_armor = 100
        self.speed = 4

        # Weapons
        self.weapons = [
            Weapon("Pistol", 20, 5, 30),
            Weapon("Rifle", 35, 3, 60),
            Weapon("Shotgun", 60, 1, 12)
        ]
        self.current_weapon_index = 0
        self.current_weapon = self.weapons[0]

        # Movement
        self.vx = 0
        self.vy = 0
        self.last_shot_time = 0

        # AI
        self.ai_target = None
        self.ai_state = "roaming"  # roaming, hunting, fleeing
        self.ai_timer = 0

        # Color based on player
        if self.is_player:
            self.color = GREEN
        else:
            self.color = RED

    def update(self, game_map_center, game_map_radius, loot_list, players):
        if self.health <= 0:
            return

        if self.is_player:
            self.update_player_input(game_map_center, game_map_radius)
        else:
            self.update_ai(game_map_center, game_map_radius, loot_list, players)

        # Move
        self.x += self.vx
        self.y += self.vy

        # Keep in bounds with safe zone
        distance_from_center = math.sqrt((self.x - game_map_center.x)**2 + (self.y - game_map_center.y)**2)
        if distance_from_center > game_map_radius:
            # Push back to safe zone
            angle = math.atan2(self.y - game_map_center.y, self.x - game_map_center.x)
            self.x = game_map_center.x + math.cos(angle) * (game_map_radius - 10)
            self.y = game_map_center.y + math.sin(angle) * (game_map_radius - 10)
            # Take damage if outside zone
            self.health -= 0.5

        # Clamp to screen
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        self.y = max(0, min(self.y, SCREEN_HEIGHT - self.height))

        # Pick up loot
        self.pickup_loot(loot_list)

    def update_player_input(self, game_map_center, game_map_radius):
        keys = pygame.key.get_pressed()
        self.vx = 0
        self.vy = 0

        if keys[pygame.K_w]:
            self.vy = -self.speed
        if keys[pygame.K_s]:
            self.vy = self.speed
        if keys[pygame.K_a]:
            self.vx = -self.speed
        if keys[pygame.K_d]:
            self.vx = self.speed

    def update_ai(self, game_map_center, game_map_radius, loot_list, players):
        self.ai_timer += 1

        # Find closest enemy
        closest_enemy = None
        closest_distance = float('inf')

        for player in players:
            if player != self and player.health > 0:
                distance = math.sqrt((self.x - player.x)**2 + (self.y - player.y)**2)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_enemy = player

        # AI Decision making
        distance_from_center = math.sqrt((self.x - game_map_center.x)**2 + (self.y - game_map_center.y)**2)
        too_far_from_center = distance_from_center > game_map_radius * 0.8

        if self.ai_timer > 60:  # Change decision every second
            if closest_distance < 200 and closest_enemy:
                self.ai_state = "hunting"
                self.ai_target = closest_enemy
            elif too_far_from_center:
                self.ai_state = "fleeing"
            else:
                self.ai_state = "roaming"
            self.ai_timer = 0

        # Execute AI state
        if self.ai_state == "hunting" and self.ai_target and self.ai_target.health > 0:
            self.move_towards(self.ai_target.x, self.ai_target.y)
        elif self.ai_state == "fleeing":
            self.move_towards(game_map_center.x, game_map_center.y)
        else:
            # Random roaming
            if self.ai_timer % 60 == 0:
                self.vx = random.uniform(-self.speed, self.speed)
                self.vy = random.uniform(-self.speed, self.speed)

    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance > 0:
            self.vx = (dx / distance) * self.speed
            self.vy = (dy / distance) * self.speed

    def pickup_loot(self, loot_list):
        rect = self.get_rect()
        for loot in loot_list:
            if not loot.collected and rect.colliderect(loot.get_rect()):
                loot.collected = True
                if loot.item_type == "health":
                    self.health = min(self.max_health, self.health + 25)
                elif loot.item_type == "armor":
                    self.armor = min(self.max_armor, self.armor + 25)
                elif loot.item_type == "ammo":
                    for weapon in self.weapons:
                        weapon.ammo = min(weapon.max_ammo, weapon.ammo + 15)

    def shoot(self):
        current_time = pygame.time.get_ticks()
        if self.current_weapon.can_shoot(current_time) and self.current_weapon.shoot():
            self.current_weapon.last_shot = current_time
            return True
        return False

    def take_damage(self, damage):
        # Armor reduces damage
        damage_after_armor = damage * (1 - self.armor / (self.armor + 100))
        self.health -= damage_after_armor
        self.health = max(0, self.health)

    def draw(self, surface):
        # Draw player
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))

        # Draw health bar
        health_bar_width = 30
        health_bar_height = 5
        health_bar_x = self.x
        health_bar_y = self.y - 10

        pygame.draw.rect(surface, RED, (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        pygame.draw.rect(surface, GREEN, (health_bar_x, health_bar_y, health_bar_width * (self.health / self.max_health), health_bar_height))

        # Draw armor bar if present
        if self.armor > 0:
            pygame.draw.rect(surface, CYAN, (health_bar_x, health_bar_y - 7, health_bar_width * (self.armor / self.max_armor), 4))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Projectile:
    """Bullet/projectile"""
    def __init__(self, x, y, target_x, target_y, damage, speed=8):
        self.x = x
        self.y = y
        self.damage = damage
        self.speed = speed
        self.radius = 3
        self.active = True

        # Calculate direction
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)

        if distance > 0:
            self.vx = (dx / distance) * speed
            self.vy = (dy / distance) * speed
        else:
            self.vx = 0
            self.vy = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy

        # Check if off screen
        if self.x < 0 or self.x > SCREEN_WIDTH or self.y < 0 or self.y > SCREEN_HEIGHT:
            self.active = False

    def draw(self, surface):
        if self.active:
            pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class SafeZone:
    """Shrinking safe zone"""
    def __init__(self, center_x, center_y, initial_radius):
        self.center = Vector2(center_x, center_y)
        self.radius = initial_radius
        self.target_radius = initial_radius
        self.shrink_speed = 0.3  # pixels per frame
        self.next_shrink_time = 300  # frames

    def update(self):
        self.next_shrink_time -= 1

        if self.next_shrink_time <= 0:
            self.target_radius = max(50, self.target_radius - 200)
            self.next_shrink_time = 500

        # Smoothly shrink
        if self.radius > self.target_radius:
            self.radius -= self.shrink_speed
            self.radius = max(self.target_radius, self.radius)

    def draw(self, surface):
        # Draw outer danger zone (red)
        pygame.draw.circle(surface, RED, (int(self.center.x), int(self.center.y)), int(self.radius + 50), 2)

        # Draw safe zone (green)
        pygame.draw.circle(surface, GREEN, (int(self.center.x), int(self.center.y)), int(self.radius), 2)


class BattleRoyaleGame:
    """Main Battle Royale game"""
    def __init__(self, num_players=6):
        self.num_players = num_players
        self.players = []
        self.projectiles = []
        self.loot_list = []
        self.running = True
        self.game_over = False
        self.winner = None

        # Game map
        self.map_center = Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.safe_zone = SafeZone(self.map_center.x, self.map_center.y, 300)

        # Spawn players
        self.spawn_players(num_players)

        # Spawn initial loot
        self.spawn_loot(50)

    def spawn_players(self, num_players):
        # Spawn player (controlled by keyboard)
        self.players.append(Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 0, is_player=True))

        # Spawn AI players
        for i in range(1, num_players):
            x = random.uniform(100, SCREEN_WIDTH - 100)
            y = random.uniform(100, SCREEN_HEIGHT - 100)
            self.players.append(Player(x, y, i, is_player=False))

    def spawn_loot(self, count):
        item_types = ["health", "armor", "ammo", "weapon"]
        for _ in range(count):
            x = random.uniform(100, SCREEN_WIDTH - 100)
            y = random.uniform(100, SCREEN_HEIGHT - 100)
            item_type = random.choice(item_types)
            self.loot_list.append(Loot(x, y, item_type))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.game_over:
                    self.__init__()  # Restart
                elif event.key == pygame.K_1:
                    self.players[0].current_weapon_index = 0
                    self.players[0].current_weapon = self.players[0].weapons[0]
                elif event.key == pygame.K_2:
                    self.players[0].current_weapon_index = 1
                    self.players[0].current_weapon = self.players[0].weapons[1]
                elif event.key == pygame.K_3:
                    self.players[0].current_weapon_index = 2
                    self.players[0].current_weapon = self.players[0].weapons[2]

    def update(self):
        # Update safe zone
        self.safe_zone.update()

        # Update players
        for player in self.players:
            player.update(self.map_center, self.safe_zone.radius, self.loot_list, self.players)

        # Handle player shooting
        if self.players[0].health > 0:
            mouse_pressed = pygame.mouse.get_pressed()
            if mouse_pressed[0]:  # Left mouse button
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if self.players[0].shoot():
                    projectile = Projectile(
                        self.players[0].x + self.players[0].width // 2,
                        self.players[0].y + self.players[0].height // 2,
                        mouse_x, mouse_y,
                        self.players[0].current_weapon.damage
                    )
                    self.projectiles.append(projectile)

        # Handle AI shooting
        for player in self.players[1:]:
            if player.health > 0 and player.ai_state == "hunting" and player.ai_target and player.ai_target.health > 0:
                distance = math.sqrt((player.x - player.ai_target.x)**2 + (player.y - player.ai_target.y)**2)
                if distance < 300 and player.shoot():
                    projectile = Projectile(
                        player.x + player.width // 2,
                        player.y + player.height // 2,
                        player.ai_target.x, player.ai_target.y,
                        player.current_weapon.damage
                    )
                    self.projectiles.append(projectile)

        # Update projectiles
        for projectile in self.projectiles[:]:
            projectile.update()
            if not projectile.active:
                self.projectiles.remove(projectile)
            else:
                # Check collision with players
                for player in self.players:
                    if player.health > 0 and projectile.get_rect().colliderect(player.get_rect()):
                        player.take_damage(projectile.damage)
                        projectile.active = False
                        if projectile in self.projectiles:
                            self.projectiles.remove(projectile)
                        break

        # Remove collected loot
        self.loot_list = [loot for loot in self.loot_list if not loot.collected]

        # Check game over
        alive_players = [p for p in self.players if p.health > 0]
        if len(alive_players) == 1:
            self.game_over = True
            self.winner = alive_players[0]
        elif len(alive_players) == 0:
            self.game_over = True
            self.winner = None

    def draw(self):
        screen.fill(DARK_GREEN)

        # Draw safe zone
        self.safe_zone.draw(screen)

        # Draw loot
        for loot in self.loot_list:
            loot.draw(screen)

        # Draw projectiles
        for projectile in self.projectiles:
            projectile.draw(screen)

        # Draw players
        for player in self.players:
            player.draw(screen)

        # Draw UI
        self.draw_ui()

        if self.game_over:
            self.draw_game_over()

        pygame.display.flip()

    def draw_ui(self):
        # Player stats
        if self.players[0].health > 0:
            player = self.players[0]
            info_text = [
                f"Health: {player.health:.1f}/{player.max_health}",
                f"Armor: {player.armor:.1f}/{player.max_armor}",
                f"Weapon: {player.current_weapon.name}",
                f"Ammo: {player.current_weapon.ammo}",
                f"Players Alive: {len([p for p in self.players if p.health > 0])}"
            ]

            y_offset = 10
            for text in info_text:
                text_surface = font.render(text, True, WHITE)
                screen.blit(text_surface, (10, y_offset))
                y_offset += 25

            # Weapon selection hint
            hint_text = small_font.render("Press 1/2/3 to switch weapons | Click to shoot", True, LIGHT_GRAY)
            screen.blit(hint_text, (10, SCREEN_HEIGHT - 30))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        if self.winner and self.winner.is_player:
            text = large_font.render("YOU WIN!", True, GREEN)
        elif self.winner:
            text = large_font.render("GAME OVER - DEFEATED", True, RED)
        else:
            text = large_font.render("GAME OVER - DRAW", True, YELLOW)

        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 200))

        if self.winner:
            stats_text = font.render(f"Winner: Player {self.winner.player_id}", True, WHITE)
            screen.blit(stats_text, (SCREEN_WIDTH // 2 - stats_text.get_width() // 2, 300))

        restart_text = font.render("Press SPACE to restart", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 400))

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = BattleRoyaleGame(num_players=8)
    game.run()
