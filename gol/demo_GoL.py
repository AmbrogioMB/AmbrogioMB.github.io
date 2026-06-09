"""
Conway's Game of Life  --  Finita / Cilindro / Toro

Comandi:
  Invio        : avvia (dopo aver disegnato la configurazione iniziale)
  Click sx     : attiva / disattiva cella
  Spazio       : pausa / riprendi
  -> (destra)  : un passo avanti (quando in pausa)
  <- (sinistra): un passo indietro (quando in pausa)
  M            : cambia topologia  Finita -> Cilindro -> Toro
  N            : mostra / nascondi coordinate (riga, colonna) nelle celle
  R            : griglia casuale
  C            : cancella griglia
  + / -        : aumenta / diminuisce velocita' (FPS)
  S            : mostra / nascondi linee griglia
  Esc          : esci

Avvio: python demo_GoL.py
"""

import pygame
import random
import sys

# ---- Impostazioni -------------------------------------------------------
CELL_SIZE     = 70    # pixel per cella (aumentare per griglie molto piccole)
GRID_COLS     = 5     # numero di colonne
GRID_ROWS     = 5     # numero di righe
FPS_DEFAULT   = 2

MIN_WIN_WIDTH = 1200   # larghezza minima finestra (garantisce HUD sempre visibile)
HUD_HEIGHT    = 200   # altezza area comandi in basso

# ---- Colori -------------------------------------------------------------
BG_COLOR   = (15, 15, 15)
CELL_ON    = (220, 220, 220)
CELL_OFF   = (15, 15, 15)
GRID_LINE  = (55, 55, 55)
TEXT_COL   = (210, 210, 210)
COORD_COL  = (110, 110, 110)
HUD_BG     = (28, 28, 28)

# ---- Topologie ----------------------------------------------------------
MODES = ["finite", "cylinder", "torus"]
MODE_IT = {
    "finite":   "Finita  (bordi fissi)",
    "cylinder": "Cilindro  (bordo sx = bordo dx)",
    "torus":    "Toro  (wrap in entrambe le direzioni)",
}

# -------------------------------------------------------------------------

def create_grid(cols, rows, fill=0):
    return [[fill] * cols for _ in range(rows)]

def random_grid(cols, rows, prob=0.25):
    return [[1 if random.random() < prob else 0 for _ in range(cols)]
            for _ in range(rows)]

def count_neighbors(grid, x, y, mode):
    rows, cols = len(grid), len(grid[0])
    n = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if mode == "torus":
                nx %= cols
                ny %= rows
            elif mode == "cylinder":
                nx %= cols
            if 0 <= nx < cols and 0 <= ny < rows:
                n += grid[ny][nx]
    return n

def step(grid, mode):
    rows, cols = len(grid), len(grid[0])
    new = create_grid(cols, rows)
    for y in range(rows):
        for x in range(cols):
            nb = count_neighbors(grid, x, y, mode)
            if grid[y][x]:
                new[y][x] = 1 if nb in (2, 3) else 0
            else:
                new[y][x] = 1 if nb == 3 else 0
    return new

def count_alive(grid):
    return sum(grid[y][x] for y in range(len(grid)) for x in range(len(grid[0])))


def draw_grid(surface, grid, cell_size, x_off, show_lines, show_coords, font_coord):
    rows, cols = len(grid), len(grid[0])
    for y in range(rows):
        for x in range(cols):
            rect = pygame.Rect(x_off + x * cell_size, y * cell_size,
                               cell_size, cell_size)
            pygame.draw.rect(surface, CELL_ON if grid[y][x] else CELL_OFF, rect)
            if show_lines:
                pygame.draw.rect(surface, GRID_LINE, rect, 1)
            if show_coords:
                lbl = font_coord.render(f"{y},{x}", True, COORD_COL)
                surface.blit(lbl, (rect.x + 4, rect.y + 4))


def draw_hud(surface, mode, paused, fps, generation, alive, total, font, waiting):
    surface.fill(HUD_BG)
    if waiting:
        status = "Premi Invio per iniziare"
    elif paused:
        status = "In pausa"
    else:
        status = "In esecuzione"

    lines = [
        f"  Stato: {status}   |   Modo: {MODE_IT[mode]}",
        f"  Generazione: {generation}   |   Celle vive: {alive} / {total}   |   FPS: {fps}",
        "",
        "  Invio: avvia   |   Click sx: attiva/disattiva   |   Spazio: pausa / riprendi",
        "  ->: passo avanti   |   <-: passo indietro   |   M: cambia topologia",
        "  R: casuale   |   C: cancella   |   N: coord.   |   +/-: velocita'   |   Esc: esci",
    ]
    y = 8
    for line in lines:
        t = font.render(line, True, TEXT_COL)
        surface.blit(t, (0, y))
        y += t.get_height() + 6


def main():
    pygame.init()
    cell_size = CELL_SIZE

    grid_px_w = GRID_COLS * cell_size
    grid_px_h = GRID_ROWS * cell_size
    win_w     = max(grid_px_w, MIN_WIN_WIDTH)   # finestra mai piu' stretta di MIN_WIN_WIDTH
    win_h     = grid_px_h + HUD_HEIGHT
    x_off     = (win_w - grid_px_w) // 2        # centra la griglia orizzontalmente

    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption("Game of Life  --  Finita / Cilindro / Toro")
    clock = pygame.time.Clock()

    font       = pygame.font.SysFont("monospace", 21)
    font_coord = pygame.font.SysFont("monospace", max(12, cell_size // 5))

    grid        = create_grid(GRID_COLS, GRID_ROWS)
    mode_idx    = 0
    mode        = MODES[mode_idx]
    paused      = True
    waiting     = True
    show_lines  = True
    show_coords = False
    generation  = 0
    fps         = FPS_DEFAULT
    history     = []

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_ESCAPE:
                    running = False
                elif k == pygame.K_RETURN and waiting:
                    waiting = False
                    paused  = True
                elif k == pygame.K_SPACE and not waiting:
                    paused = not paused
                elif k == pygame.K_RIGHT and paused and not waiting:
                    history.append([row[:] for row in grid])
                    grid = step(grid, mode)
                    generation += 1
                elif k == pygame.K_LEFT and paused and not waiting and history:
                    grid = history.pop()
                    generation = max(0, generation - 1)
                elif k == pygame.K_r:
                    grid = random_grid(GRID_COLS, GRID_ROWS)
                    generation = 0
                    history.clear()
                elif k == pygame.K_c:
                    grid = create_grid(GRID_COLS, GRID_ROWS)
                    generation = 0
                    history.clear()
                elif k == pygame.K_m:
                    mode_idx = (mode_idx + 1) % len(MODES)
                    mode = MODES[mode_idx]
                elif k == pygame.K_s:
                    show_lines = not show_lines
                elif k == pygame.K_n:
                    show_coords = not show_coords
                elif k in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    fps += 1
                elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    fps = max(1, fps - 1)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                gx = (mx - x_off) // cell_size
                gy = my // cell_size
                if not waiting and 0 <= gx < GRID_COLS and 0 <= gy < GRID_ROWS:
                    grid[gy][gx] ^= 1

        if not paused and not waiting:
            history.append([row[:] for row in grid])
            grid = step(grid, mode)
            generation += 1

        screen.fill(BG_COLOR)
        draw_grid(screen, grid, cell_size, x_off, show_lines, show_coords, font_coord)
        hud = screen.subsurface(pygame.Rect(0, grid_px_h, win_w, HUD_HEIGHT))
        draw_hud(hud, mode, paused, fps, generation,
                 count_alive(grid), GRID_ROWS * GRID_COLS, font, waiting)
        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
