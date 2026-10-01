import pygame
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
        self.pipe_interval = 90  # frames between pipe spawns
        self._spawn_timer = 0
        self.pipes = [Pipe(width + 100, height, speed=self.pipe_speed)]

        self.score = 0
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over = False
        self._exit_requested = False

    def handle_event(self, event):
        # Once the game is over, wait for a key press before exiting.
        if self.game_over:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                self._exit_requested = True
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        # Flap is edge-triggered (KEYDOWN / MOUSEBUTTONDOWN), not held.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.bird.flap()
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.bird.flap()

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
            self.game_over = True
            return

        self._spawn_timer += 1
        if self._spawn_timer >= self.pipe_interval:
            self._spawn_timer = 0
            self.pipes.append(Pipe(self.width, self.height, speed=self.pipe_speed))

        for pipe in self.pipes:
            pipe.move()

            # Check the bird's full bounding rectangle against both
            # pipe rectangles so edge overlaps are detected reliably.
            bird_rect = self.bird.rect()
            if bird_rect.colliderect(pipe.top_rect()) or bird_rect.colliderect(pipe.bottom_rect()):
                self.game_over = True

            if not pipe.scored and pipe.x + pipe.width < self.bird.x:
                pipe.scored = True
                self.score += 1

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
            instruction_text = instruction_font.render(
                "Press any key to exit", True, WHITE
            )

            screen.blit(
                game_over_text,
                game_over_text.get_rect(center=(self.width // 2, self.height // 2 - 70)),
            )
            screen.blit(
                final_score_text,
                final_score_text.get_rect(center=(self.width // 2, self.height // 2)),
            )
            screen.blit(
                instruction_text,
                instruction_text.get_rect(center=(self.width // 2, self.height // 2 + 60)),
            )
