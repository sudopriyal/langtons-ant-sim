import pygame
from collections import defaultdict

pygame.init()

# ==================================================
# CONFIGURATION
# ==================================================

WIDTH, HEIGHT = 1280, 900
PANEL_WIDTH = 360
MIN_CANVAS_WIDTH = 300
PANEL_PADDING = 20
PANEL_CONTENT_HEIGHT = 870
SCROLL_SPEED = 40
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("ANT / LAB — Langton's Ant")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("consolas", 15)
SMALL = pygame.font.SysFont("consolas", 12)
TITLE = pygame.font.SysFont("consolas", 25, bold=True)
BIG = pygame.font.SysFont("consolas", 22, bold=True)

# Each palette includes six contrasting colors.
LIGHT_PALETTE = [
    ("Black", (25, 27, 32)),
    ("Coral", (225, 67, 82)),
    ("Blue", (40, 100, 210)),
    ("Purple", (125, 75, 190)),
    ("Green", (25, 135, 95)),
    ("Orange", (215, 115, 35)),
]

DARK_PALETTE = [
    ("White", (245, 245, 240)),
    ("Coral", (255, 100, 115)),
    ("Cyan", (65, 210, 225)),
    ("Purple", (180, 125, 255)),
    ("Green", (100, 225, 155)),
    ("Yellow", (255, 210, 85)),
]

ANT_COLOR = (230, 55, 75)

THEMES = {
    "Light": {
        "background": (247, 245, 240),
        "panel": (232, 229, 221),
        "surface": (255, 255, 255),
        "text": (35, 38, 45),
        "muted": (105, 109, 119),
        "border": (211, 209, 201),
        "button": (255, 255, 255),
        "active": (220, 225, 235),
        "grid": (225, 223, 217),
    },
    "Dark": {
        "background": (20, 22, 28),
        "panel": (29, 32, 40),
        "surface": (37, 41, 51),
        "text": (240, 242, 247),
        "muted": (155, 163, 179),
        "border": (58, 63, 76),
        "button": (42, 47, 58),
        "active": (64, 73, 91),
        "grid": (42, 45, 53),
    },
}

DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
DIRECTION_NAMES = ["UP", "RIGHT", "DOWN", "LEFT"]

# ==================================================
# SIMULATION STATE
# ==================================================

# Missing cells are white / unvisited.
grid = defaultdict(bool)
cell_colors = {}

ant_x = 0
ant_y = 0
direction = 0
steps = 0

panel_scroll = 0

paused = True
speed = 120
zoom = 8

theme_name = "Light"
palette_index = 0
colored_trails = False
show_grid = True

start_x = 0
start_y = 0
start_direction = 0

input_focus = None
input_values = {"x": "0", "y": "0"}

# ==================================================
# HELPERS
# ==================================================

def panel_y(y):
    return y - panel_scroll

def palette():
    return LIGHT_PALETTE if theme_name == "Light" else DARK_PALETTE


def colors():
    return THEMES[theme_name]


def reset():
    global grid, cell_colors
    global ant_x, ant_y, direction, steps, paused

    grid = defaultdict(bool)
    cell_colors = {}

    ant_x = start_x
    ant_y = start_y
    direction = start_direction
    steps = 0
    paused = True


def advance():
    global ant_x, ant_y, direction, steps

    was_black = grid[(ant_x, ant_y)]

    # Flip the square, then turn based on its OLD color.
    grid[(ant_x, ant_y)] = not was_black

    if not was_black:
        direction = (direction + 1) % 4
        if colored_trails:
            cell_colors[(ant_x, ant_y)] = steps % len(palette())
        else:
            cell_colors[(ant_x, ant_y)] = palette_index
    else:
        direction = (direction - 1) % 4
        cell_colors.pop((ant_x, ant_y), None)

    dx, dy = DIRECTIONS[direction]
    ant_x += dx
    ant_y += dy
    steps += 1


def text(surface, value, pos, color=None, font=FONT):
    if color is None:
        color = colors()["text"]
    surface.blit(font.render(str(value), True, color), pos)


def button(surface, rect, label, active=False):
    c = colors()
    mouse = pygame.mouse.get_pos()

    fill = c["active"] if active else c["button"]
    if rect.collidepoint(mouse):
        fill = c["active"]

    pygame.draw.rect(surface, fill, rect, border_radius=9)
    pygame.draw.rect(
        surface, c["border"], rect, width=1, border_radius=9
    )

    image = FONT.render(label, True, c["text"])
    surface.blit(image, image.get_rect(center=rect.center))


def panel_title(surface, label, y, x):
    c = colors()
    text(
        surface, label.upper(),
        (x + 20, panel_y(y)),
        c["muted"], SMALL
    )


def draw_slider(surface, rect, value, minimum, maximum):
    c = colors()
    pygame.draw.line(
        surface, c["border"],
        (rect.x, rect.centery),
        (rect.right, rect.centery), 5
    )

    ratio = (value - minimum) / (maximum - minimum)
    ratio = max(0, min(1, ratio))
    knob_x = rect.x + int(ratio * rect.width)

    pygame.draw.line(
        surface, c["text"],
        (rect.x, rect.centery),
        (knob_x, rect.centery), 5
    )
    pygame.draw.circle(surface, c["text"], (knob_x, rect.centery), 9)
    pygame.draw.circle(surface, c["panel"], (knob_x, rect.centery), 4)


def slider_value(mouse_x, rect, minimum, maximum):
    ratio = (mouse_x - rect.x) / rect.width
    ratio = max(0, min(1, ratio))
    return round(minimum + ratio * (maximum - minimum))


# ==================================================
# MAIN LOOP
# ==================================================

running = True
dragging_speed = False
dragging_zoom = False

while running:
    W, H = screen.get_size()
    canvas_width = max(300, W - PANEL_WIDTH)
    c = colors()

    # All controls are placed relative to the panel.
    px = canvas_width

    play_rect = pygame.Rect(px + 20, panel_y(100), 154, 42)
    step_rect = pygame.Rect(px + 186, panel_y(100), 154, 42)
    reset_rect = pygame.Rect(px + 20, panel_y(151), 320, 38)

    speed_rect = pygame.Rect(px + 24, panel_y(240), 310, 8)
    zoom_rect = pygame.Rect(px + 24, panel_y(310), 310, 8)

    theme_rect = pygame.Rect(px + 20, panel_y(344), 154, 38)
    grid_rect = pygame.Rect(px + 186, panel_y(344), 154, 38)

    trail_rect = pygame.Rect(px + 20, panel_y(405), 320, 38)

    swatches = []
    for i in range(len(palette())):
        col = i % 3
        row = i // 3
        swatches.append(
            pygame.Rect(
                px + 22 + col * 108,
                panel_y(480 + row * 43),
                96, 34
            )
        )

    x_rect = pygame.Rect(px + 20, panel_y(590), 145, 35)
    y_rect = pygame.Rect(px + 186, panel_y(590), 154, 35)

    direction_rects = []
    for i in range(4):
        direction_rects.append(
            pygame.Rect(
                px + 20 + i * 82,
                panel_y(665),
                74, 35
            )
        )

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode(
                (event.w, event.h), pygame.RESIZABLE
            )

        elif event.type == pygame.KEYDOWN:
            if input_focus in ("x", "y"):
                if event.key == pygame.K_RETURN:
                    try:
                        value = int(input_values[input_focus])
                        if abs(value) > 1_000_000:
                            raise ValueError
                        if input_focus == "x":
                            start_x = value
                        else:
                            start_y = value
                    except ValueError:
                        input_values[input_focus] = str(
                            start_x if input_focus == "x" else start_y
                        )
                    input_focus = None

                elif event.key == pygame.K_ESCAPE:
                    input_focus = None

                elif event.key == pygame.K_BACKSPACE:
                    input_values[input_focus] = input_values[input_focus][:-1]

                elif event.unicode in "0123456789-" and event.unicode:
                    current = input_values[input_focus]
                    if event.unicode == "-":
                        if not current:
                            input_values[input_focus] = "-"
                    elif len(current) < 9:
                        input_values[input_focus] += event.unicode

            else:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_RIGHT and paused:
                    advance()
                elif event.key == pygame.K_r:
                    reset()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if event.button == 1:
                if play_rect.collidepoint(event.pos):
                    paused = not paused

                elif step_rect.collidepoint(event.pos):
                    paused = True
                    advance()

                elif reset_rect.collidepoint(event.pos):
                    reset()

                elif speed_rect.inflate(0, 20).collidepoint(event.pos):
                    dragging_speed = True
                    speed = slider_value(mx, speed_rect, 1, 2000)

                elif zoom_rect.inflate(0, 20).collidepoint(event.pos):
                    dragging_zoom = True
                    zoom = slider_value(mx, zoom_rect, 3, 24)

                elif theme_rect.collidepoint(event.pos):
                    theme_name = "Dark" if theme_name == "Light" else "Light"
                    palette_index = min(palette_index, len(palette()) - 1)

                elif grid_rect.collidepoint(event.pos):
                    show_grid = not show_grid

                elif trail_rect.collidepoint(event.pos):
                    colored_trails = not colored_trails

                elif any(r.collidepoint(event.pos) for r in swatches):
                    palette_index = next(
                        i for i, r in enumerate(swatches)
                        if r.collidepoint(event.pos)
                    )

                elif x_rect.collidepoint(event.pos):
                    input_focus = "x"

                elif y_rect.collidepoint(event.pos):
                    input_focus = "y"

                elif any(r.collidepoint(event.pos) for r in direction_rects):
                    start_direction = next(
                        i for i, r in enumerate(direction_rects)
                        if r.collidepoint(event.pos)
                    )

                else:
                    input_focus = None

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging_speed = False
                dragging_zoom = False

        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if dragging_speed:
                speed = slider_value(mx, speed_rect, 1, 2000)
            if dragging_zoom:
                zoom = slider_value(mx, zoom_rect, 3, 24)

        elif event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()

            if mx >= canvas_width:
                panel_scroll = max(
                    0,
                    min(
                        max(0, PANEL_CONTENT_HEIGHT - H),
                        panel_scroll - event.y * SCROLL_SPEED
                    )
                )
            else:
                zoom = max(3, min(24, zoom + event.y))

    # Update coordinate fields after edits are committed.
    input_values["x"] = str(start_x) if input_focus != "x" else input_values["x"]
    input_values["y"] = str(start_y) if input_focus != "y" else input_values["y"]

    # Run simulation at a controllable number of steps per second.
    if not paused:
        steps_this_frame = min(2000, speed)
        for _ in range(steps_this_frame):
            advance()

    # ==================================================
    # DRAW CANVAS
    # ==================================================

    screen.fill(c["background"])

    center_x = canvas_width // 2
    center_y = H // 2

    # Camera follows the ant. The world itself is unbounded.
    left = ant_x - center_x // zoom - 1
    right = ant_x + center_x // zoom + 2
    top = ant_y - center_y // zoom - 1
    bottom = ant_y + (H - center_y) // zoom + 2

    if show_grid and zoom >= 6:
        for gx in range(left, right):
            sx = center_x + (gx - ant_x) * zoom
            pygame.draw.line(
                screen, c["grid"], (sx, 0), (sx, H), 1
            )

        for gy in range(top, bottom):
            sy = center_y + (gy - ant_y) * zoom
            pygame.draw.line(
                screen, c["grid"], (0, sy), (canvas_width, sy), 1
            )

    # Draw only visited black cells in the visible region.
    for (gx, gy), is_black in grid.items():
        if not is_black:
            continue

        sx = center_x + (gx - ant_x) * zoom
        sy = center_y + (gy - ant_y) * zoom

        if -zoom < sx < canvas_width and -zoom < sy < H:
            idx = cell_colors.get((gx, gy), palette_index)
            if colored_trails:
                cell_color = palette()[idx % len(palette())][1]
            else:
                cell_color = palette()[palette_index][1]

            pygame.draw.rect(
                screen, cell_color,
                (sx, sy, zoom, zoom)
            )

    # Ant marker
    pygame.draw.rect(
        screen, ANT_COLOR,
        (center_x, center_y, zoom, zoom),
        border_radius=max(1, zoom // 4)
    )

    # Direction indicator
    dx, dy = DIRECTIONS[direction]
    tip = (
        center_x + zoom // 2 + dx * zoom,
        center_y + zoom // 2 + dy * zoom
    )
    pygame.draw.line(
        screen, ANT_COLOR,
        (center_x + zoom // 2, center_y + zoom // 2),
        tip, max(2, zoom // 4)
    )

    # ==================================================
    # DRAW CONTROL PANEL
    # ==================================================

    pygame.draw.rect(
        screen, c["panel"],
        (canvas_width, 0, PANEL_WIDTH, H)
    )

    panel_clip = pygame.Rect(
        canvas_width, 0,
        W - canvas_width, H
    )
    screen.set_clip(panel_clip)

    text(screen, "ANT / LAB", (px + 20, panel_y(20)), c["text"], TITLE)
    text(screen, "CELLULAR AUTOMATON", (px + 20, panel_y(54)), c["muted"], SMALL)

    status = "PAUSED" if paused else "RUNNING"
    status_color = ANT_COLOR if paused else (50, 175, 115)
    text(screen, f"● {status}", (px + 20, panel_y(76)), status_color, SMALL)

    button(screen, play_rect, "RESUME" if paused else "PAUSE")
    button(screen, step_rect, "STEP  +1")
    button(screen, reset_rect, "RESET  [R]")

    panel_title(screen, "SIMULATION SPEED", 195, px)
    text(screen, f"{speed} steps / frame", (px + 20, panel_y(211)))
    draw_slider(screen, speed_rect, speed, 1, 2000)

    text(screen, "2000", (speed_rect.right - 36, panel_y(253)), c["muted"], SMALL)  

    panel_title(screen, "CANVAS ZOOM", 260, px)
    text(screen, f"{zoom} px / cell", (px + 20, panel_y(278)))
    draw_slider(screen, zoom_rect, zoom, 3, 24)

    button(screen, theme_rect, f"THEME: {theme_name.upper()}")
    button(screen, grid_rect, f"GRID: {'ON' if show_grid else 'OFF'}")

    panel_title(screen, "Trail rendering", 387, px)
    button(
        screen, trail_rect,
        f"COLORED TRAILS: {'ON' if colored_trails else 'OFF'}",
        colored_trails
    )

    panel_title(screen, "Cell color palette", 458, px)

    for i, rect in enumerate(swatches):
        name, rgb = palette()[i]
        pygame.draw.rect(screen, rgb, rect, border_radius=7)

        if i == palette_index:
            pygame.draw.rect(
                screen, c["text"], rect, width=2, border_radius=7
            )

        label_color = (
            (255, 255, 255)
            if sum(rgb) < 390
            else (25, 27, 32)
        )
        image = SMALL.render(name, True, label_color)
        screen.blit(image, image.get_rect(center=rect.center))

    panel_title(screen, "Starting coordinates (apply with reset)", 570, px)

    pygame.draw.rect(
        screen, c["surface"], x_rect, border_radius=7
    )
    pygame.draw.rect(
        screen, ANT_COLOR if input_focus == "x" else c["border"],
        x_rect, width=2, border_radius=7
    )
    text(screen, f"X: {input_values['x']}", (x_rect.x + 10, x_rect.y + 9))

    pygame.draw.rect(
        screen, c["surface"], y_rect, border_radius=7
    )
    pygame.draw.rect(
        screen, ANT_COLOR if input_focus == "y" else c["border"],
        y_rect, width=2, border_radius=7
    )
    text(screen, f"Y: {input_values['y']}", (y_rect.x + 10, y_rect.y + 9))

    panel_title(screen, "Starting direction", 642, px)

    for i, rect in enumerate(direction_rects):
        button(
            screen, rect, DIRECTION_NAMES[i],
            start_direction == i
        )

    # Live statistics
    panel_title(screen, "Live statistics", 720, px)
    text(screen, f"STEPS       {steps:,}", (px + 20, 744), c["text"], BIG)
    text(screen, f"STEPS       {steps:,}", (px + 20, panel_y(744)), c["text"], BIG)
    text(screen, f"BLACK CELLS {sum(grid.values()):,}", (px + 20, panel_y(776)))
    text(screen, f"ANT X       {ant_x}", (px + 20, panel_y(800)))
    text(screen, f"ANT Y       {ant_y}", (px + 20, panel_y(822)))
    screen.set_clip(None)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()