#MODULES
import pygame
import random
import time

#CONSTANTS
GRID_SIZE = 30 # Size of 1x1 Grid
COLUMNS, ROWS = 10,20 # No. Of Columns and Rows on the playing grid
WIDTH, HEIGHT = (COLUMNS + 10) * GRID_SIZE, ROWS * GRID_SIZE # Calculate the width and height of the screen with the columns and rows
GRID_OFFSET_X = (WIDTH - COLUMNS * GRID_SIZE) // 2 # Center the playing grid on screen

#COLORS (R,G,B)
BLACK = (0,0,0)
WHITE = (255,255,255)
GRAY = (55,55,55)

CYAN = (33,218,218)
YELLOW = (218,218,33)
PURPLE = (128,0,128)
GREEN = (33,218,33)
RED = (218,33,33)
BLUE = (33,33,218)
ORANGE = (218,156,33)

#Drop Speed Parameters (Based in Milliseconds)
BASE_DROP_SPEED = 500
MIN_DROP_SPEED = 100
LOCK_DELAY = 500 # Delay in locking the block in place

#SHAPES OF BLOCKS
SHAPES = [
    [[1,1,1,1]], # I - Cyan
    [[1,1],[1,1]], # O - Yellow
    [[0,1,0],[1,1,1]], # T - Purple
    [[0,1,1],[1,1,0]], # S - Green
    [[1,1,0],[0,1,1]], # Z - Red
    [[0,0,1],[1,1,1]], # J - Blue
    [[1,0,0],[1,1,1]], # L - Orange
]
SHAPE_COLORS = [CYAN, YELLOW, PURPLE, GREEN, RED, BLUE, ORANGE]

#BLOCK CLASS
class Tetrimono:
    def __init__(self, shape_index = None, shape = None, color = None):
        if shape_index is not None:
            self.shape = SHAPES[shape_index]
            self.color = SHAPE_COLORS[shape_index]
        elif shape is not None and color is not None:
            self.shape = shape
            self.color = color
        else:
            shape_index = random.randint(0, len(SHAPES) - 1)
            self.shape = SHAPES[shape_index]
            self.color = SHAPE_COLORS[shape_index]

        self.x, self.y = COLUMNS//2 - len(self.shape[0]) // 2, 0

    def rotate(self):
        # Rotate the Block 90 degrees clockwise:
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

#Collision Checking
def check_collision(grid, block, dx = 0, dy = 0):
    for y, row in enumerate(block.shape):
        for x, cell in enumerate(row):
            if cell:
                new_x, new_y = block.x + x + dx, block.y + y + dy
                if new_x < 0 or new_x >= COLUMNS or new_y >= ROWS or (new_y >= 0 and grid[new_y][new_x]):
                    return True
    return False

#Rotate Wall Kick
def rotate_with_wall_kick(grid, block):
    #Store Original Position and Shape
    orig_x = block.x
    orig_y = block.y
    orig_shape = [row[:] for row in block.shape]

    block.rotate()

    if not check_collision(grid, block):
        return True

    for dx in [-1, 1, -2, 2]:
        block.x += dx
        if not check_collision(grid, block):
            return True
        block.x = orig_x  

    for dy in [-1,1]:
        block.y += dy
        if not check_collision(grid,block):
            return True

        for dx in [-1, 1, -2, 2]:
            block.x += dx
            if not check_collision(grid, block):
                return True
            block.x = orig_x

        block.y = orig_y

    block.x = orig_x
    block.y = orig_y
    block.shape = orig_shape
    return False

#Merge Block to Grid
def merge_block(grid, block):
    for y, row in enumerate(block.shape):
        for x, cell in enumerate(row):
            if cell:
                grid[block.y + y][block.x + x] = block.color

#Clear Full Lines
def clear_lines(grid, score):
    new_grid = [row for row in grid if any(cell == 0 for cell in row)]
    lines_cleared = ROWS - len(new_grid)
    score += lines_cleared * 100
    return [[0]* COLUMNS for _ in range(lines_cleared)] + new_grid, score

#Calculate Drop Speed based on score
def calculate_drop_speed(score):
    speed = BASE_DROP_SPEED - (score // 1000) * 50
    return max(speed, MIN_DROP_SPEED)

#Draw grid
def draw_grid(screen):
    for x in range(0, COLUMNS * GRID_SIZE + 1, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (x + GRID_OFFSET_X, 0), (x + GRID_OFFSET_X, HEIGHT))

    for y in range(0, HEIGHT + 1, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (GRID_OFFSET_X, y), (GRID_OFFSET_X + COLUMNS * GRID_SIZE, y))

#Draw Block Shadow -- Drop Location
def draw_shadow(screen, grid, piece):
    shadow = Tetrimono(shape=piece.shape, color=piece.color)
    shadow.x, shadow.y = piece.x, piece.y

    while not check_collision(grid, shadow, dy = 1) and shadow.y + 1 < ROWS:
        shadow.y += 1

    for y, row in enumerate(shadow.shape):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(screen, (100,100,100), ((shadow.x + x) * GRID_SIZE + GRID_OFFSET_X, (shadow.y + y) * GRID_SIZE, GRID_SIZE, GRID_SIZE), 2)

#Instant Drop
def instant_drop(grid, piece, score):
    while not check_collision(grid, piece, dy=1):
        piece.y += 1
    merge_block(grid, piece)
    return clear_lines(grid, score)

#Draw the block
def draw_block(screen, color, x, y):
    # Border Color
    darker_color = (max(0, color[0] - 80), max(0, color[1] - 80), max(0, color[2] - 80))

    pygame.draw.rect(screen, color, (x,y,GRID_SIZE,GRID_SIZE))

    border_width = 5
    pygame.draw.rect(screen, darker_color, (x + border_width, y + border_width, GRID_SIZE - 2*border_width, GRID_SIZE - 2*border_width))
    pygame.draw.rect(screen, color, (x + 2*border_width, y + 2*border_width, GRID_SIZE - 4*border_width, GRID_SIZE - 4*border_width))

#Draw Preview of Block
def draw_preview(screen, piece, x_offset, y_offset):
    for y, row, in enumerate(piece.shape):
        for x, cell in enumerate(row):
            if cell:
                draw_block(screen, piece.color, (x + x_offset) * GRID_SIZE, (y + y_offset) * GRID_SIZE)

#Draw Button
def draw_button(screen, text, x, y, width, height, inactive_color, active_color):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if x < mouse[0] < x + width and y < mouse[1] < y + height:
        pygame.draw.rect(screen, active_color, (x,y,width,height))
        if click[0]:
            return True
    else:
        pygame.draw.rect(screen, inactive_color, (x,y,width,height))
    
    font = pygame.font.Font(None, 36)
    text_surf = font.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center = (x + width/2, y + height/2))
    screen.blit(text_surf, text_rect)
    return False

#Create a Start Screen
def start_screen(screen):
    # Add falling blocks in the background
    background_blocks = []
    for _ in range(15):
        shape_index = random.randint(0, len(SHAPES) - 1)
        piece = Tetrimono(shape_index)
        piece.x = random.randint(0, COLUMNS - len(piece.shape[0]))
        piece.y = random.randint(-ROWS, 0)
        background_blocks.append(piece)

    while True:
        screen.fill((20,20,40))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return True
        
        for piece in background_blocks:
            for y, row in enumerate(piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        draw_block(screen, piece.color, (piece.x + x) * GRID_SIZE + GRID_OFFSET_X, (piece.y + y) * GRID_SIZE)

            piece.y += 0.05
            if piece.y > ROWS:
                piece.y = - len(piece.shape)
                piece.x = random.randint(0, COLUMNS - len(piece.shape[0]))

        title_text = "TETRIS"
        font_large = pygame.font.Font(None, 120)
        stroke_offsets = [(x,y) for x in range(-3,4) for y in range (-3,4) if (x,y) != (0,0)]

        for offset_x, offset_y in stroke_offsets:
            title_stroke = font_large.render(title_text, True, WHITE)
            screen.blit(title_stroke, (WIDTH//2 - title_stroke.get_width()//2 + offset_x, HEIGHT//4 - title_stroke.get_height()//2 + offset_y))
        
        title_main = font_large.render(title_text, True, (65,65,65))
        screen.blit(title_main, (WIDTH//2 - title_stroke.get_width()//2, HEIGHT//4 - title_stroke.get_height()//2))

        start_clicked = draw_button(screen, "Play", WIDTH//2 - 100, HEIGHT//2, 200, 50, (0,100,0), (0,200,0))
        if start_clicked:
            return True

        instructions = [
            "Controls:",
            "Left/Right Arrow : Move left/right",
            "Up Arrow : Rotate",
            "Down Arrow : Move Down",
            "SPACE : Drop Instantly",
            "C : Hold Piece"
        ]

        y_offset = HEIGHT//2 + 80
        font_small = pygame.font.Font(None, 36)
        instructions_stroke = [(x,y) for x in range (-2,3) for y in range(-2,3) if (x,y) != (0,0)]

        for instruction in instructions:
            for offset_x, offset_y in instructions_stroke:
                text_stroke = font_small.render(instruction, True, WHITE)
                screen.blit(text_stroke, (WIDTH//2 - text_stroke.get_width()//2 + offset_x, y_offset + offset_y))

            text_main = font_small.render(instruction, True, (65,65,65))
            screen.blit(text_main, (WIDTH//2 - text_main.get_width()//2, y_offset))

            y_offset += 30
        
        pygame.display.flip()
        pygame.time.delay(30)

def game_over_screen(screen, score):
    screen.fill((20,20,40))

    font_large = pygame.font.Font(None, 72)
    font_small = pygame.font.Font(None, 36)

    game_over_text = font_large.render("GAME OVER", True, WHITE)
    score_text = font_small.render(f"Final Score: {score}", True, WHITE)

    screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//4))
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//3))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, True # False - Retry | True - Quit
    
    button_width, button_height, button_spacing = 150, 50, 30

    total_width = (2 * button_width) + button_spacing
    start_x = (WIDTH - total_width)//2

    retry_clicked = draw_button(screen, "Retry", start_x, HEIGHT//2, button_width, button_height, (0,100,0),(0,200,0))
    quit_clicked = draw_button(screen, "Quit", start_x + button_width + button_spacing, HEIGHT//2, button_width, button_height, (100,0,0),(200,0,0))

    pygame.display.flip()
    return retry_clicked, quit_clicked

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    def reset_game():
        return {
            'grid' : [[0] * COLUMNS for _ in range(ROWS)],
            'current_piece' : Tetrimono(),
            'next_piece' : Tetrimono(),
            'hold_piece' : None,
            'can_hold' : True,
            'drop_time' : 0,
            'lock_time' : 0,
            'lock_delay_active' : False,
            'score' : 0
        }

    if not start_screen(screen):
        pygame.quit()
        return
    
    game_state = reset_game()
    game_over = False
    running = True

    while running:
        if not game_over:
            screen.fill(BLACK)
            delta_time = clock.get_time()
            game_state['drop_time'] += delta_time
            drop_speed = calculate_drop_speed(game_state['score'])

            landed = check_collision(game_state['grid'], game_state['current_piece'], dy=1)

            if landed:
                if not game_state['lock_delay_active']:
                    game_state['lock_delay_active'] = True
                    game_state['lock_time'] = 0
                else:
                    game_state['lock_time'] += delta_time
            else:
                game_state['lock_delay_active'] = False
                game_state['lock_time'] = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT and not check_collision(game_state['grid'], game_state['current_piece'], dx = -1):
                        game_state['current_piece'].x -= 1
                        if game_state['lock_delay_active']:
                            game_state['lock_time'] = 0
                    if event.key == pygame.K_RIGHT and not check_collision(game_state['grid'], game_state['current_piece'], dx = 1):
                        game_state['current_piece'].x += 1
                        if game_state['lock_delay_active']:
                            game_state['lock_time'] = 0
                    if event.key == pygame.K_DOWN and not check_collision(game_state['grid'], game_state['current_piece'], dy = 1):
                        game_state['current_piece'].y += 1
                    if event.key == pygame.K_UP:
                        if rotate_with_wall_kick(game_state['grid'], game_state['current_piece']):
                            if game_state['lock_delay_active']:
                                game_state['lock_time'] = 0
                    if event.key == pygame.K_c and game_state['can_hold']:
                        if game_state['hold_piece'] is None:
                            game_state['hold_piece'] = Tetrimono(shape = game_state['current_piece'].shape, color = game_state['current_piece'].color)
                            game_state['current_piece'] = game_state['next_piece']
                            game_state['next_piece'] = Tetrimono()
                        else:
                            game_state['hold_piece'], game_state['current_piece'] = Tetrimono(shape = game_state['current_piece'].shape, color = game_state['current_piece'].color), Tetrimono(shape = game_state['hold_piece'].shape, color = game_state['hold_piece'].color)
                        
                        game_state['current_piece'].x = COLUMNS//2 - len(game_state['current_piece'].shape[0]) // 2 
                        game_state['current_piece'].y = 0

                        game_state['can_hold'] = False

                    if event.key == pygame.K_SPACE:
                        game_state['grid'], game_state['score'] = instant_drop(game_state['grid'], game_state['current_piece'], game_state['score'])
                        game_state['current_piece'] = game_state['next_piece']
                        game_state['next_piece'] = Tetrimono()
                        game_state['can_hold'] = True
                        game_state['lock_delay_active'] = False

                        if check_collision(game_state['grid'], game_state['current_piece']):
                            game_over = True


            if game_state['drop_time'] > drop_speed:
                if not check_collision(game_state['grid'], game_state['current_piece'], dy=1):
                    game_state['current_piece'].y += 1
                game_state['drop_time'] = 0

            if game_state['lock_delay_active'] and game_state['lock_time'] >= LOCK_DELAY:
                merge_block(game_state['grid'], game_state['current_piece'])
                game_state['grid'], game_state['score'] = clear_lines(game_state['grid'], game_state['score'])
                game_state['current_piece'] = game_state['next_piece']
                game_state['next_piece'] = Tetrimono()
                game_state['can_hold'] = True
                game_state['lock_delay_active'] = False

                if check_collision(game_state['grid'], game_state['current_piece']):
                    game_over = True
        
            draw_grid(screen)
            draw_shadow(screen, game_state['grid'], game_state['current_piece'])

            for y, row in enumerate(game_state['grid']):
                for x, cell in enumerate(row):
                    if cell:
                        draw_block(screen, cell, x* GRID_SIZE + GRID_OFFSET_X, y * GRID_SIZE)

            for y, row in enumerate(game_state['current_piece'].shape):
                for x, cell in enumerate(row):
                    if cell:
                        draw_block(screen, game_state['current_piece'].color, (game_state['current_piece'].x + x)* GRID_SIZE + GRID_OFFSET_X, (game_state['current_piece'].y + y) * GRID_SIZE)

            score_text = font.render(f"Score: {game_state['score']}", True, WHITE)
            level_text = font.render(f"Level: {min(9, game_state['score']// 1000 + 1)}", True, WHITE)
            screen.blit(score_text, (10,10))
            screen.blit(level_text, (10,50))

            hold_text = font.render("HOLD", True, WHITE)
            next_text = font.render("NEXT", True, WHITE)
            screen.blit(hold_text, (GRID_SIZE, GRID_SIZE * 3))
            screen.blit(next_text, (WIDTH - 3.5 * GRID_SIZE, GRID_SIZE * 3))

            if game_state['hold_piece']:
                draw_preview(screen, game_state['hold_piece'], 1, 6)

            draw_preview(screen, game_state['next_piece'], COLUMNS + GRID_OFFSET_X // GRID_SIZE + 1, 6)

        else:

            retry, quit_game = game_over_screen(screen, game_state['score'])
            if retry:
                game_state = reset_game()
                game_over = False
            if quit_game:
                running = False
    
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()