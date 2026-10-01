import pygame
from pathlib import Path
from .bird import Bird
from .pipe import Pipe

# Game Engine

WHITE = (255, 255, 255)
GREEN = (0, 150, 0)

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.bird = Bird(width // 4, height // 2)
        self.pipe_speed = 4
        self.pipe_gap = 150
        self.pipe_interval = 90  # frames between pipe spawns

        self.score = 0
        self.font = pygame.font.SysFont("Arial", 30)
        self._load_sounds()
        self.game_over = False
        self._exit_requested = False
        self.difficulty = "Medium"

        self._reset_game()

    def _load_sounds(self):
        self.flap_sound = None
        self.score_sound = None
        self.death_sound = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            sound_dir = Path(__file__).resolve().parent / "sounds"
            self.flap_sound = pygame.mixer.Sound(str(sound_dir / "flap.wav"))
            self.score_sound = pygame.mixer.Sound(str(sound_dir / "score.wav"))
            self.death_sound = pygame.mixer.Sound(str(sound_dir / "death.wav"))
        except (pygame.error, FileNotFoundError):
            # Keep the game playable if audio is unavailable.
            self.flap_sound = None
            self.score_sound = None
            self.death_sound = None

    def _play_sound(self, sound):
        if sound is not None:
            sound.play()

    def _set_game_over(self):
        if not self.game_over:
            self.game_over = True
            self._play_sound(self.death_sound)

    def handle_event(self, event):
        # After Game Over, choose a difficulty or exit without restarting
        # the Python program.
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_KP1):
                    self._reset_game("Easy")
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self._reset_game("Medium")
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self._reset_game("Hard")
                elif event.key in (pygame.K_4, pygame.K_KP4, pygame.K_ESCAPE):
                    self._exit_requested = True
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        # Flap is edge-triggered (KEYDOWN / MOUSEBUTTONDOWN), not held.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.bird.flap()
            self._play_sound(self.flap_sound)
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.bird.flap()
            self._play_sound(self.flap_sound)

    def _reset_game(self, difficulty="Medium"):
        settings = {
            "Easy": {"speed": 3, "gap": 180},
            "Medium": {"speed": 4, "gap": 150},
            "Hard": {"speed": 6, "gap": 120},
        }

        self.difficulty = difficulty
        self.pipe_speed = settings[difficulty]["speed"]
        self.pipe_gap = settings[difficulty]["gap"]

        self.bird = Bird(self.width // 4, self.height // 2)
        self.pipes = [
            Pipe(
                self.width + 100,
                self.height,
                gap=self.pipe_gap,
                speed=self.pipe_speed,
            )
        ]
        self.score = 0
        self._spawn_timer = 0
        self.game_over = False
        self._exit_requested = False

    def handle_input(self):
        # Reserved for continuously-held-key input; flapping is handled
        # in handle_event instead, so there's nothing to poll here.
        pass

    def exit_requested(self):
        return self._exit_requested

    def update(self):
        if self.game_over:
            return

        self.bird.update()

        if self.bird.y - self.bird.radius <= 0 or self.bird.y + self.bird.radius >= self.height:
            self._set_game_over()
            return

        self._spawn_timer += 1
        if self._spawn_timer >= self.pipe_interval:
            self._spawn_timer = 0
            self.pipes.append(
                Pipe(
                    self.width,
                    self.height,
                    gap=self.pipe_gap,
                    speed=self.pipe_speed,
                )
            )

        for pipe in self.pipes:
            pipe.move()

            # Check the bird's full bounding rectangle against both
            # pipe rectangles so edge overlaps are detected reliably.
            bird_rect = self.bird.rect()
            if bird_rect.colliderect(pipe.top_rect()) or bird_rect.colliderect(pipe.bottom_rect()):
                self._set_game_over()
                break

            if not pipe.scored and pipe.x + pipe.width < self.bird.x:
                pipe.scored = True
                self.score += 1
                self._play_sound(self.score_sound)

        self.pipes = [p for p in self.pipes if not p.off_screen()]

    def render(self, screen):
        for pipe in self.pipes:
            pygame.draw.rect(screen, GREEN, pipe.top_rect())
            pygame.draw.rect(screen, GREEN, pipe.bottom_rect())

        pygame.draw.circle(screen, WHITE, (int(self.bird.x), int(self.bird.y)), self.bird.radius)

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        if self.game_over:
            # Overlay the Game Over screen without changing the gameplay state.
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            title_font = pygame.font.SysFont("Arial", 48, bold=True)
            instruction_font = pygame.font.SysFont("Arial", 24)

            game_over_text = title_font.render("Game Over", True, WHITE)
            final_score_text = self.font.render(
                f"Final Score: {self.score}", True, WHITE
            )
            menu_title_text = instruction_font.render(
                "Choose a difficulty:", True, WHITE
            )
            easy_text = instruction_font.render(
                "1 - Easy   (Speed 3, Gap 180)", True, WHITE
            )
            medium_text = instruction_font.render(
                "2 - Medium (Speed 4, Gap 150)", True, WHITE
            )
            hard_text = instruction_font.render(
                "3 - Hard   (Speed 6, Gap 120)", True, WHITE
            )
            exit_text = instruction_font.render(
                "4 - Exit", True, WHITE
            )

            screen.blit(
                game_over_text,
                game_over_text.get_rect(center=(self.width // 2, self.height // 2 - 150)),
            )
            screen.blit(
                final_score_text,
                final_score_text.get_rect(center=(self.width // 2, self.height // 2 - 95)),
            )
            screen.blit(
                menu_title_text,
                menu_title_text.get_rect(center=(self.width // 2, self.height // 2 - 45)),
            )
            screen.blit(
                easy_text,
                easy_text.get_rect(center=(self.width // 2, self.height // 2 - 5)),
            )
            screen.blit(
                medium_text,
                medium_text.get_rect(center=(self.width // 2, self.height // 2 + 30)),
            )
            screen.blit(
                hard_text,
                hard_text.get_rect(center=(self.width // 2, self.height // 2 + 65)),
            )
            screen.blit(
                exit_text,
                exit_text.get_rect(center=(self.width // 2, self.height // 2 + 100)),
            )
