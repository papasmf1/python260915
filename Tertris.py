"""pygame 기반 테트리스 게임"""
#cmd 
#pip install pygame
import random
import pygame

pygame.init()

# 화면/보드 설정
CELL_SIZE = 30
COLS = 10
ROWS = 20
BOARD_WIDTH = CELL_SIZE * COLS
BOARD_HEIGHT = CELL_SIZE * ROWS
SIDE_PANEL_WIDTH = 180
SCREEN_WIDTH = BOARD_WIDTH + SIDE_PANEL_WIDTH
SCREEN_HEIGHT = BOARD_HEIGHT

BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# 테트로미노 모양(회전 상태별 좌표) 및 색상
SHAPES = {
    'I': [[(0, 1), (1, 1), (2, 1), (3, 1)],
          [(2, 0), (2, 1), (2, 2), (2, 3)]],
    'O': [[(1, 0), (2, 0), (1, 1), (2, 1)]],
    'T': [[(1, 0), (0, 1), (1, 1), (2, 1)],
          [(1, 0), (1, 1), (2, 1), (1, 2)],
          [(0, 1), (1, 1), (2, 1), (1, 2)],
          [(1, 0), (0, 1), (1, 1), (1, 2)]],
    'S': [[(1, 0), (2, 0), (0, 1), (1, 1)],
          [(1, 0), (1, 1), (2, 1), (2, 2)]],
    'Z': [[(0, 0), (1, 0), (1, 1), (2, 1)],
          [(2, 0), (1, 1), (2, 1), (1, 2)]],
    'J': [[(0, 0), (0, 1), (1, 1), (2, 1)],
          [(1, 0), (2, 0), (1, 1), (1, 2)],
          [(0, 1), (1, 1), (2, 1), (2, 2)],
          [(1, 0), (1, 1), (0, 2), (1, 2)]],
    'L': [[(2, 0), (0, 1), (1, 1), (2, 1)],
          [(1, 0), (1, 1), (1, 2), (2, 2)],
          [(0, 1), (1, 1), (2, 1), (0, 2)],
          [(0, 0), (1, 0), (1, 1), (1, 2)]],
}

COLORS = {
    'I': (0, 255, 255),
    'O': (255, 255, 0),
    'T': (160, 32, 240),
    'S': (0, 255, 0),
    'Z': (255, 0, 0),
    'J': (0, 0, 255),
    'L': (255, 165, 0),
}


class Piece:
    def __init__(self, shape_key):
        self.shape_key = shape_key
        self.rotation = 0
        self.color = COLORS[shape_key]
        self.x = 3
        self.y = 0

    def cells(self, rotation=None):
        rotation = self.rotation if rotation is None else rotation
        rotations = SHAPES[self.shape_key]
        return rotations[rotation % len(rotations)]

    def rotations_count(self):
        return len(SHAPES[self.shape_key])


class Tetris:
    def __init__(self):
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.bag = []
        self.current = self.new_piece()
        self.next_piece = self.new_piece()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.fall_time = 0
        self.fall_speed = 500  # 밀리초

    def new_piece(self):
        if not self.bag:
            self.bag = list(SHAPES.keys())
            random.shuffle(self.bag)
        return Piece(self.bag.pop())

    def valid_position(self, piece, dx=0, dy=0, rotation=None):
        for cx, cy in piece.cells(rotation):
            x = piece.x + cx + dx
            y = piece.y + cy + dy
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def lock_piece(self):
        for cx, cy in self.current.cells():
            x = self.current.x + cx
            y = self.current.y + cy
            if y < 0:
                self.game_over = True
                return
            self.board[y][x] = self.current.color
        self.clear_lines()
        self.current = self.next_piece
        self.next_piece = self.new_piece()
        if not self.valid_position(self.current):
            self.game_over = True

    def clear_lines(self):
        full_rows = [r for r in range(ROWS) if all(self.board[r])]
        for r in full_rows:
            del self.board[r]
            self.board.insert(0, [None] * COLS)
        cleared = len(full_rows)
        if cleared:
            self.lines_cleared += cleared
            self.score += (100, 300, 500, 800)[min(cleared, 4) - 1] * self.level
            self.level = 1 + self.lines_cleared // 10
            self.fall_speed = max(100, 500 - (self.level - 1) * 40)

    def move(self, dx, dy):
        if self.valid_position(self.current, dx=dx, dy=dy):
            self.current.x += dx
            self.current.y += dy
            return True
        return False

    def rotate(self):
        new_rotation = (self.current.rotation + 1) % self.current.rotations_count()
        if self.valid_position(self.current, rotation=new_rotation):
            self.current.rotation = new_rotation
        else:
            # 벽에 막히면 좌우로 살짝 밀어서 시도(간단한 킥)
            for dx in (-1, 1, -2, 2):
                if self.valid_position(self.current, dx=dx, rotation=new_rotation):
                    self.current.x += dx
                    self.current.rotation = new_rotation
                    break

    def hard_drop(self):
        while self.move(0, 1):
            pass
        self.lock_piece()

    def update(self, dt):
        if self.game_over:
            return
        self.fall_time += dt
        if self.fall_time >= self.fall_speed:
            self.fall_time = 0
            if not self.move(0, 1):
                self.lock_piece()

    def ghost_y(self):
        ghost = Piece(self.current.shape_key)
        ghost.rotation = self.current.rotation
        ghost.x = self.current.x
        ghost.y = self.current.y
        while self.valid_position(ghost, dy=1):
            ghost.y += 1
        return ghost.y


def draw_board(screen, game, font):
    screen.fill(BLACK)

    # 격자
    for r in range(ROWS):
        for c in range(COLS):
            rect = (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, GRAY, rect, 1)
            if game.board[r][c]:
                pygame.draw.rect(screen, game.board[r][c], rect)

    # 고스트 피스
    ghost_y = game.ghost_y()
    for cx, cy in game.current.cells():
        x = game.current.x + cx
        y = ghost_y + cy
        if y >= 0:
            rect = (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, game.current.color, rect, 2)

    # 현재 피스
    for cx, cy in game.current.cells():
        x = game.current.x + cx
        y = game.current.y + cy
        if y >= 0:
            rect = (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, game.current.color, rect)

    # 사이드 패널
    panel_x = BOARD_WIDTH + 20
    score_text = font.render(f"점수: {game.score}", True, WHITE)
    level_text = font.render(f"레벨: {game.level}", True, WHITE)
    lines_text = font.render(f"라인: {game.lines_cleared}", True, WHITE)
    next_text = font.render("다음:", True, WHITE)
    screen.blit(score_text, (panel_x, 20))
    screen.blit(level_text, (panel_x, 50))
    screen.blit(lines_text, (panel_x, 80))
    screen.blit(next_text, (panel_x, 120))

    for cx, cy in game.next_piece.cells():
        rect = (panel_x + cx * CELL_SIZE, 150 + cy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, game.next_piece.color, rect)

    if game.game_over:
        over_text = font.render("게임 오버", True, RED)
        screen.blit(over_text, (panel_x, 250))
        restart_text = font.render("R키로 재시작", True, WHITE)
        screen.blit(restart_text, (panel_x, 280))


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("테트리스")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("malgungothic", 20)

    game = Tetris()
    running = True

    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game.game_over:
                    if event.key == pygame.K_r:
                        game = Tetris()
                    continue
                if event.key == pygame.K_LEFT:
                    game.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    game.move(1, 0)
                elif event.key == pygame.K_DOWN:
                    game.move(0, 1)
                elif event.key == pygame.K_UP:
                    game.rotate()
                elif event.key == pygame.K_SPACE:
                    game.hard_drop()

        game.update(dt)
        draw_board(screen, game, font)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
