import pygame
from collections import defaultdict

pygame.init()

# ---------- Configuration ----------
CELL = 8
PANEL_WIDTH = 240
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 760
FPS = 60

WHITE = (245, 245, 240)
BLACK = (24, 26, 32)
ACCENT = (255, 90, 95)
PANEL = (32, 35, 44)
TEXT = (235, 238, 245)
MUTED = (160, 168, 185)
BUTTON = (53, 58, 72)
BUTTON_HOVER = (72, 79, 98)

screen = pygame.display.set_mode(
    (WINDOW_WIDTH, WINDOW_HEIGHT),
    pygame.RESIZABLE
)
pygame.display.set_caption("Langton's Ant | Interactive Lab")

font = pygame.font.SysFont("consolas", 18)
small_font = pygame.font.SysFont("consolas", 14)
title_font = pygame.font.SysFont("consolas", 25, bold=True)
clock = pygame.time.Clock()

# ---------- Simulation ----------
grid = defaultdict(bool)

ant_x = 0
ant_y = 0
direction = 0  # 0 up, 1 right, 2 down, 3 left
steps = 0
running = True
paused = False
speed = 20

DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]


def reset():
    global grid, ant_x, ant_y, direction, steps
    grid = defaultdict(bool)
    ant_x = ant_y = direction = steps = 0


def advance():
    global ant_x, ant_y, direction, steps

    is_black = grid[(ant_x, ant_y)]
    grid[(ant_x, ant_y)] = not is_black

    # White: turn right. Black: turn left.
    if not is_black:
        direction = (direction + 1) % 4
    else:
        direction = (direction - 1) % 4

    dx, dy = DIRECTIONS[direction]
    ant_x += dx
    ant_y += dy
    steps += 1


def draw_text(text, x, y, color=TEXT, font_obj=font):
    image = font_obj.render(str(text), True, color)
    screen.blit(image, (x, y))


def draw_button(rect, label, mouse_pos):
    color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON
    pygame.draw.rect(screen, color, rect, border_radius=8)
    draw_text(label, rect.x + 12, rect.y + 9)


def main():
    global running, paused, speed, screen

    while running:
        width, height = screen.get_size()
        canvas_width = width - PANEL_WIDTH
        mouse_pos = pygame.mouse.get_pos()

        play_rect = pygame.Rect(
            canvas_width + 20, 165, PANEL_WIDTH - 40, 42
        )
        reset_rect = pygame.Rect(
            canvas_width + 20, 217, PANEL_WIDTH - 40, 42
        )
        slower_rect = pygame.Rect(
            canvas_width + 20, 300, 90, 38
        )
        faster_rect = pygame.Rect(
            canvas_width + 120, 300, 90, 38
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(
                    (event.w, event.h), pygame.RESIZABLE
                )

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    reset()
                elif event.key == pygame.K_RIGHT:
                    advance()
                elif event.key == pygame.K_UP:
                    speed = min(2000, speed * 2)
                elif event.key == pygame.K_DOWN:
                    speed = max(1, speed // 2)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if play_rect.collidepoint(event.pos):
                    paused = not paused
                elif reset_rect.collidepoint(event.pos):
                    reset()
                elif slower_rect.collidepoint(event.pos):
                    speed = max(1, speed // 2)
                elif faster_rect.collidepoint(event.pos):
                    speed = min(2000, speed * 2)

        if not paused:
            for _ in range(speed):
                advance()

        # ---------- Draw grid ----------
        screen.fill(WHITE)

        # Keep ant centered on the visible grid
        center_x = canvas_width // 2
        center_y = height // 2

        for (gx, gy), is_black in grid.items():
            if is_black:
                px = center_x + (gx - ant_x) * CELL
                py = center_y + (gy - ant_y) * CELL

                if -CELL < px < canvas_width and -CELL < py < height:
                    pygame.draw.rect(
                        screen, BLACK, (px, py, CELL, CELL)
                    )

        # Draw ant
        pygame.draw.rect(
            screen,
            ACCENT,
            (center_x, center_y, CELL, CELL),
            border_radius=2
        )

        # ---------- Draw control panel ----------
        pygame.draw.rect(
            screen, PANEL,
            (canvas_width, 0, PANEL_WIDTH, height)
        )

        draw_text("LANGTON'S ANT", canvas_width + 20, 30,
                  TEXT, title_font)
        draw_text("CELLULAR AUTOMATON", canvas_width + 20, 67,
                  MUTED, small_font)

        pygame.draw.line(
            screen, BUTTON,
            (canvas_width + 20, 105),
            (width - 20, 105), 2
        )

        draw_text("SIMULATION", canvas_width + 20, 125,
                  MUTED, small_font)

        draw_button(
            play_rect, "Resume" if paused else "Pause", mouse_pos
        )
        draw_button(reset_rect, "Reset  [R]", mouse_pos)

        draw_text("SPEED", canvas_width + 20, 275,
                  MUTED, small_font)
        draw_button(slower_rect, "- Slower", mouse_pos)
        draw_button(faster_rect, "+ Faster", mouse_pos)
        draw_text(f"{speed} steps / frame",
                  canvas_width + 20, 350)

        pygame.draw.line(
            screen, BUTTON,
            (canvas_width + 20, 390),
            (width - 20, 390), 2
        )

        draw_text("STATISTICS", canvas_width + 20, 410,
                  MUTED, small_font)
        draw_text(f"Steps: {steps:,}",
                  canvas_width + 20, 442)
        draw_text(f"Black cells: {sum(grid.values()):,}",
                  canvas_width + 20, 474)
        draw_text(f"Ant X: {ant_x}",
                  canvas_width + 20, 506)
        draw_text(f"Ant Y: {ant_y}",
                  canvas_width + 20, 538)

        draw_text("CONTROLS", canvas_width + 20, 590,
                  MUTED, small_font)
        draw_text("SPACE  Pause / resume",
                  canvas_width + 20, 618, TEXT, small_font)
        draw_text("RIGHT  Single step",
                  canvas_width + 20, 642, TEXT, small_font)
        draw_text("UP/DOWN  Change speed",
                  canvas_width + 20, 666, TEXT, small_font)
        draw_text("R  Reset",
                  canvas_width + 20, 690, TEXT, small_font)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()