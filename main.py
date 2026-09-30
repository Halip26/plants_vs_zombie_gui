import os
import sys
import math
import random
import pygame
from pygame import mixer

# Initialize Pygame and Mixer
pygame.init()
mixer.init()

# Screen Configuration
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors(RGB)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 100, 255)
COLOR_RED = (235, 52, 52)
COLOR_GOLD = (255, 215, 0)
COLOR_GRAY = (150, 150, 150)

# Paths configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
HIGH_SCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")


# Helper function to resolve paths safely
def get_image_path(filename):
    return os.path.join(IMAGES_DIR, filename)


def get_audio_path(filename):
    return os.path.join(AUDIO_DIR, filename)


class PlantsZombie:
    # Game States
    STATE_MENU = "MENU"
    STATE_COUNTDOWN = "COUNTDOWN"
    STATE_PLAYING = "PLAYING"
    STATE_GAME_OVER = "GAME_OVER"
    COUNTDOWN_MS = 3000  # 3 seconds countdown
    SCORE_PER_LEVEL = 10

    def __init__(self):
        # Set up the screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Plants VS Zombie")

        # Load and set icon
        try:
            icon_img = pygame.image.load(get_image_path("potato.png"))
            pygame.display.set_icon(icon_img)
        except Exception as e:
            print(f"Error loading icon: {e}")

        # Load background and sprite images
        try:
            self.bg_img = pygame.image.load(get_image_path("garden.png")).convert()
            self.bg_img = pygame.transform.scale(
                self.bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )

            self.title_bg_img = pygame.image.load(
                get_image_path("title_screen.png")
            ).convert()
            self.title_bg_img = pygame.transform.scale(
                self.title_bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
            self.plant_img = pygame.image.load(
                get_image_path("plants.png")
            ).convert_alpha()
            self.zombie_img = pygame.image.load(
                get_image_path("zombie.png")
            ).convert_alpha()
            self.bullet_img = pygame.image.load(
                get_image_path("green_peas.png")
            ).convert_alpha()
        except Exception as e:
            print(f"Error loading images: {e}")
            sys.exit(1)

        # Preload sounds to avoid game lag during play
        try:
            self.shoot_sound = mixer.Sound(get_audio_path("pop_sound.mp3"))
            self.hit_sound = mixer.Sound(get_audio_path("pop_sound.mp3"))
            # Set default sound volumes
            self.shoot_sound.set_volume(0.5)
            self.hit_sound.set_volume(0.6)
        except Exception as e:
            print(f"Error loading sound effects: {e}")
            self.shoot_sound = None
            self.hit_sound = None

        # Load background music
        self.music_loaded = False
        try:
            mixer.music.load(get_audio_path("plant_zombie.mp3"))
            mixer.music.set_volume(0.4)
            mixer.music.play(-1)
            self.music_loaded = True
        except Exception as e:
            print(f"Error loading background music: {e}")

        # Load Fonts(using system default freesasbold if available, fallback to default)
        try:
            self.font_title = pygame.font.Font("freesansbold.ttf", 50)
            self.font_subtitle = pygame.font.Font("freesansbold.ttf", 24)
            self.font_score = pygame.font.Font("freesansbold.ttf", 30)
            self.font_gameover = pygame.font.Font("freesansbold.ttf", 64)
            self.font_final_score = pygame.font.Font("freesansbold.ttf", 40)
            self.font_copyright = pygame.font.Font("freesansbold.ttf", 14)
        except Exception:
            # Fallback to system font if freesansbold is not found
            self.font_title = pygame.font.SysFont("arial", 50, bold=True)
            self.font_subtitle = pygame.font.SysFont("arial", 24)
            self.font_score = pygame.font.SysFont("arial", 30, bold=True)
            self.font_gameover = pygame.font.SysFont("arial", 64, bold=True)
            self.font_final_score = pygame.font.SysFont("arial", 40, bold=True)
            self.font_copyright = pygame.font.SysFont("arial", 14)

        # Initialize Game Settings
        self.clock = pygame.time.Clock()
        self.high_score = self.load_high_score()
        self.muted = False
        self.state = self.STATE_MENU

        # Game session variables
        self.score = 0
        self.level = 1
        self.countdown_end = 0
        self.player_x = 370
        self.player_y = 460
        self.player_speed = 6

        # Enemy settings
        self.num_enemies = 6
        self.enemies = []

        # Bullet settings
        self.bullet_x = 0
        self.bullet_y = 480
        self.bullet_speed = 20
        self.bullet_state = "ready"  # "ready" or "fire"

        # Initialize the first game setup
        self.reset_game()

    def load_high_score(self):
        """Loads the high score from highscore.txt. Returns 0 if file doesn't exist."""
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE, "r") as f:
                    content = f.read().strip()
                    if content.isdigit():
                        return int(content)
            except Exception as e:
                print(f"Error loading high score: {e}")
        return 0

    def save_high_score(self):
        """Saves the current high score to highscore.txt if it exceeds the saved high score."""
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open(HIGH_SCORE_FILE, "w") as f:
                    f.write(str(self.high_score))
            except Exception as e:
                print(f"Error saving high score: {e}")

    def reset_game(self):
        """Resets the game state for a new round."""
        self.score = 0
        self.level = 1
        self.countdown_end = 0
        self.player_x = 370
        self.player_y = 460
        self.bullet_state = "ready"
        self.bullet_y = 480

        self.create_level_zombies()

    def create_level_zombies(self):
        """Initialize enemies for the current level."""
        self.enemies = []
        base_speed = 4.0
        enemy_count = min(
            self.num_enemies + self.level - 1, 12
        )  # Increase enemies with level, max 12

        for i in range(enemy_count):
            self.enemies.append(
                {
                    "x": random.randint(0, 736),
                    "y": random.randint(50, 150),
                    "speed_x": (
                        base_speed if random.choice([True, False]) else -base_speed
                    ),
                    "speed_y": 30,
                    "active": True,
                }
            )

    def start_countdown(self):
        """starts a countdown before the current level becomes active."""
        self.countdown_end = pygame.time.get_ticks() + self.COUNTDOWN_MS
        self.state = self.STATE_COUNTDOWN

    def start_next_level(self):
        """advance to the next level and reset enemies and bullet state."""
        self.level += 1
        self.create_level_zombies()
        self.start_countdown()

    def update_countdown(self):
        """begins active gameplay after the level countdown has finished."""
        if pygame.time.get_ticks() >= self.countdown_end:
            self.state = self.STATE_PLAYING

    def get_remaining_enemies(self):
        """returns the number of enemies still alive in the current
        level"""
        return sum(enemy["active"] for enemy in self.enemies)

    def toggle_mute(self):
        """Mutes/Unmutes background music and sound effects."""
        self.muted = not self.muted
        if self.muted:
            if self.music_loaded:
                mixer.music.set_volume(0.0)
            if self.shoot_sound:
                self.shoot_sound.set_volume(0.0)
            if self.hit_sound:
                self.hit_sound.set_volume(0.0)
        else:
            if self.music_loaded:
                mixer.music.set_volume(0.4)
            if self.shoot_sound:
                self.shoot_sound.set_volume(0.5)
            if self.hit_sound:
                self.hit_sound.set_volume(0.6)

    def draw_plant(self, x, y):
        self.screen.blit(self.plant_img, (x, y))

    def draw_zombie(self, x, y):
        self.screen.blit(self.zombie_img, (x, y))

    def draw_bullet(self, x, y):
        # Center the bullet relative to the player
        self.screen.blit(self.bullet_img, (x + 53, y + 10))

    def is_collision(self, x1, y1, x2, y2):
        """Calculates distance to detect collision between bullet and enemy."""
        distance = math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))
        return distance < 27

    def run(self):
        """Main game execution loop."""
        running = True
        while running:
            # Maintain stable 60 FPS
            self.clock.tick(FPS)

            # 1. Handle events
            running = self.handle_events()

            # 2. Update logic based on state
            if self.state == self.STATE_COUNTDOWN:
                self.update_countdown()
            if self.state == self.STATE_PLAYING:
                self.update_playing()

            # 3. Render frame
            self.draw()

        pygame.quit()
        sys.exit()

    def handle_events(self):
        """Processes events in the pygame queue."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                # Quit options
                if event.key == pygame.K_ESCAPE:
                    return False

                # Toggle Mute
                if event.key == pygame.K_m:
                    self.toggle_mute()

                # State: Main Menu
                if self.state == self.STATE_MENU:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                        self.start_countdown()

                # State: Playing
                elif self.state == self.STATE_PLAYING:
                    if event.key == pygame.K_SPACE:
                        if self.bullet_state == "ready":
                            self.bullet_x = self.player_x
                            self.bullet_state = "fire"
                            if self.shoot_sound and not self.muted:
                                self.shoot_sound.play()

                # State: Game Over
                elif self.state == self.STATE_GAME_OVER:
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.start_countdown()
                    elif event.key == pygame.K_q:
                        return False

        return True

    def update_playing(self):
        """Update the game physics. positions, and collisions during active play."""
        # player movement (Continuous keyboard polling for smooth physics)
        keys = pygame.key.get_pressed()
        player_dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player_dx = -self.player_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player_dx = self.player_speed

        self.player_x += player_dx

        # Boundary checks for player
        if self.player_x < 0:
            self.player_x = 0
        elif self.player_x > 730:
            self.player_x = 730

        # Calculate current difficulty speed modifier based on score
        # for every 5 points, increase base enemy speed slightly (+0.5)
        difficlty_speed_factor = 4.0 + (self.score // 5) * 0.5

        # Update enemies
        for i, enemy in enumerate(self.enemies):
            if not enemy["active"]:
                continue

            # Check for game over (enemy reached the defense line)
            if enemy["y"] > 440:
                self.save_high_score()
                self.state = self.STATE_GAME_OVER
                break

            # Adjust horizontal direction speed dynamically based on difficulty
            # Preserve direction sign, scale magnitude
            direction = 1.0 if enemy["speed_x"] >= 0 else -1.0
            enemy["speed_x"] = direction * difficlty_speed_factor

            # Move enemy horizontally
            enemy["x"] += enemy["speed_x"]

            # Bounce enemy on boundary wall and push down
            if enemy["x"] <= 0:
                enemy["speed_x"] = difficlty_speed_factor  # move right
                enemy["y"] += enemy["speed_y"]
            elif enemy["x"] >= 736:
                enemy["speed_x"] = -difficlty_speed_factor  # move left
                enemy["y"] += enemy["speed_y"]

            # Bullet collision check
            if self.bullet_state == "fire":
                if self.is_collision(
                    enemy["x"], enemy["y"], self.bullet_x, self.bullet_y
                ):
                    # play sound
                    if self.hit_sound and not self.muted:
                        self.hit_sound.play()

                    # Reset bullet
                    self.bullet_y = 480
                    self.bullet_state = "ready"

                    # Update Score
                    self.score += 1

                    enemy["active"] = False

        # begin the next level at its score milestone or when all enemies are gone.
        if self.state == self.STATE_PLAYING and (
            self.score >= self.level * self.SCORE_PER_LEVEL
            or self.get_remaining_enemies() == 0
        ):
            self.start_next_level()

        # Bullet movement
        if self.bullet_state == "fire":
            self.bullet_y -= self.bullet_speed
            if self.bullet_y <= 0:
                self.bullet_y = 480
                self.bullet_state = "ready"

    def draw(self):
        """Reenders all elements on the screen based on the current state."""
        # Draw Title Background image
        self.screen.blit(self.title_bg_img, (0, 0))

        if self.state == self.STATE_MENU:
            self.draw_menu_screen()
        elif self.state == self.STATE_COUNTDOWN:
            self.draw_playing_screen()
            self.draw_countdown_screen()
        elif self.state == self.STATE_PLAYING:
            self.draw_playing_screen()
        elif self.state == self.STATE_GAME_OVER:
            self.draw_game_over_screen()

        # Render Copyright Footer on all screens
        self.draw_copyright()

        pygame.display.update()

    def draw_menu_screen(self):
        """Renders the main menu screen."""
        # Draw Title with a shadow effect
        title_text = "Plants VS Zombie"
        shadow = self.font_title.render(title_text, True, COLOR_BLACK)
        title = self.font_title.render(title_text, True, COLOR_GOLD)

        self.screen.blit(
            shadow, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 3, 150 + 3)
        )
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))

        # Instruction
        start_txt = self.font_subtitle.render(
            "Press SPACE to start Game", True, COLOR_WHITE
        )
        self.screen.blit(
            start_txt, (SCREEN_WIDTH // 2 - start_txt.get_width() // 2, 270)
        )

        controls_txt = self.font_subtitle.render(
            "Controls: Left/Right Arrow or A/D to Move", True, COLOR_BLUE
        )
        self.screen.blit(
            controls_txt, (SCREEN_WIDTH // 2 - controls_txt.get_width() // 2, 330)
        )

        shoot_txt = self.font_subtitle.render(
            "SPACE to shoot | M to Mute Audio", True, COLOR_BLUE
        )
        self.screen.blit(
            shoot_txt, (SCREEN_WIDTH // 2 - shoot_txt.get_width() // 2, 370)
        )

        # High score
        hs_txt = self.font_score.render(
            f"High Score: {self.high_score}", True, COLOR_GOLD
        )
        self.screen.blit(hs_txt, (SCREEN_WIDTH // 2 - hs_txt.get_width() // 2, 450))

    def draw_playing_screen(self):
        """Renders the gameplay elements."""

        # Draw Background image
        self.screen.blit(self.bg_img, (0, 0))

        # Draw Bullet
        if self.bullet_state == "fire":
            self.draw_bullet(self.bullet_x, self.bullet_y)

        # Draw player
        self.draw_plant(self.player_x, self.player_y)

        # Draw Enemies
        for enemy in self.enemies:
            if enemy["active"]:
                self.draw_zombie(enemy["x"], enemy["y"])

        # Display Score and High Score
        score_text = self.font_score.render(f"Score: {self.score}", True, COLOR_WHITE)
        self.screen.blit(score_text, (20, 20))

        # this will display the current level on the screen
        level_text = self.font_score.render(f"Level: {self.level}", True, COLOR_GREEN)
        self.screen.blit(level_text, (20, 55))

        remaining_text = self.font_score.render(
            f"Enemies: {self.get_remaining_enemies()}", True, COLOR_WHITE
        )
        self.screen.blit(remaining_text, (20, 90))

        hs_text = self.font_score.render(
            f"High Score: {self.high_score}", True, COLOR_GOLD
        )
        self.screen.blit(hs_text, (SCREEN_WIDTH - hs_text.get_width() - 20, 20))

        # Display mute status if muted
        if self.muted:
            mute_text = self.font_subtitle.render("MUTED", True, COLOR_RED)
            self.screen.blit(
                mute_text, (SCREEN_WIDTH // 2 - mute_text.get_width() // 2, 20)
            )

    def draw_countdown_screen(self):
        """Renders the countdown overlay before a level begins."""
        remaining_ms = max(0, self.countdown_end - pygame.time.get_ticks())
        seconds = max(1, math.ceil(remaining_ms / 1000))
        countdown_text = self.font_gameover.render(str(seconds), True, COLOR_GOLD)
        self.screen.blit(
            countdown_text,
            (
                SCREEN_WIDTH // 2 - countdown_text.get_width() // 2,
                SCREEN_HEIGHT // 2 - countdown_text.get_height() // 2,
            ),
        )

        level_text = self.font_subtitle.render(
            f"level {self.level} incoming", True, COLOR_GRAY
        )
        self.screen.blit(
            level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 390)
        )

    def draw_game_over_screen(self):
        """Renders the game over screen."""
        # Game Over  Title
        go_text = "GAME OVER"
        go_shadow = self.font_gameover.render(go_text, True, COLOR_BLACK)
        go_title = self.font_gameover.render(go_text, True, COLOR_BLUE)

        self.screen.blit(
            go_shadow, (SCREEN_WIDTH // 2 - go_title.get_width() // 2 + 3, 150 + 3)
        )
        self.screen.blit(go_title, (SCREEN_WIDTH // 2 - go_title.get_width() // 2, 150))

        # Scores
        final_text = f"Total Score: {self.score}"
        final_score = self.font_final_score.render(final_text, True, COLOR_GREEN)
        self.screen.blit(
            final_score, (SCREEN_WIDTH // 2 - final_score.get_width() // 2, 240)
        )

        # High Score celebration
        if self.score >= self.high_score and self.score > 0:
            new_hs_text = self.font_subtitle.render("NEW HIGH SCORE!", True, COLOR_GOLD)
            self.screen.blit(
                new_hs_text, (SCREEN_WIDTH // 2 - new_hs_text.get_width() // 2, 300)
            )
        else:
            hs_text = self.font_subtitle.render(
                f"High Score: {self.high_score}", True, COLOR_WHITE
            )
            self.screen.blit(
                hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 300)
            )

        # Instruction
        restart_text = self.font_subtitle.render(
            "Press R to Restart", True, COLOR_WHITE
        )
        self.screen.blit(
            restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 380)
        )

        quit_text = self.font_subtitle.render(
            "Press Q or ESC to QUIT", True, COLOR_GRAY
        )
        self.screen.blit(
            quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, 420)
        )

    def draw_copyright(self):
        """Renders copyright info at the bottom of the screen"""
        copyright_str = "Copyright \u00a9 2026 Mr. Halip. All Rights Reserved."
        subject = self.font_copyright.render(copyright_str, True, COLOR_GREEN)
        self.screen.blit(subject, (SCREEN_WIDTH // 2 - subject.get_width() // 2, 572))


if __name__ == "__main__":
    game = PlantsZombie()
    game.run()
