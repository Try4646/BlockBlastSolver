
import cv2
import numpy as np


class Game:
    top_left = (900, 350)
    bottom_right = (1660, 1100)
    top_left_b = (910, 1100)
    bottom_right_b = (1660, 1400)
    interval = 2
    block_width = 95
    block_height = 95
    empty_color = (82, 44, 33)
    pc = None
    phone = None

    def __init__(self, pc=True, phone=False):
        if pc is True:
            self.pc = True
            self.phone = False
            self.top_left = (900, 350)
            self.bottom_right = (1660, 1100)
            self.top_left_b = (910, 1100)
            self.bottom_right_b = (1660, 1400)
            self.interval = 2
            self.block_width = 95
            self.block_height = 95
            self.empty_color = (82, 44, 33)
        if phone is True:
            self.pc = False
            self.phone = True
            self.top_left = (1015, 335)
            self.bottom_right = (1535, 860)
            self.top_left_b = (1015, 885)
            self.bottom_right_b = (1535, 1125)
            self.interval = 2
            self.block_width = 60
            self.block_height = 60
            self.empty_color = (70, 36, 31)

    def detect_blocks(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        grid = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 30 and h > 30:
                if self.phone is True:
                    grid_x = x // 29
                    grid_y = y // 29
                elif self.pc is True:
                    grid_x = x // 50
                    grid_y = y // 50
                else:
                    continue

                while len(grid) <= grid_y:
                    grid.append([])

                while len(grid[grid_y]) <= grid_x:
                    grid[grid_y].append(0)

                grid[grid_y][grid_x] = 1

                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return grid, image

    def generate_grid(self, image):
        grid = []
        for y in range(0, image.shape[0], self.block_height):
            row = []
            for x in range(0, image.shape[1], self.block_width):
                center_y = min(y + self.block_height // 2, image.shape[0] - 1)
                center_x = min(x + self.block_width // 2, image.shape[1] - 1)
                block_center = image[center_y, center_x]
                if np.array_equal(block_center, self.empty_color):
                    row.append(0)
                else:
                    row.append(1)
            grid.append(row)
        return grid

    def extract_blocks(self, matrix):
        max_len = max((len(row) for row in matrix), default=0)
        padded_matrix = [row + [0] * (max_len - len(row)) for row in matrix]

        rows = len(padded_matrix)
        cols = len(padded_matrix[0]) if rows > 0 else 0
        visited = [[False for _ in range(cols)] for _ in range(rows)]
        blocks = []

        def dfs(r, c, coords):
            if r < 0 or r >= rows or c < 0 or c >= cols:
                return
            if padded_matrix[r][c] != 1 or visited[r][c]:
                return
            visited[r][c] = True
            coords.append((r, c))
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    dfs(r + dr, c + dc, coords)

        def normalize(coords):
            min_r = min(r for r, _ in coords)
            max_r = max(r for r, _ in coords)
            min_c = min(c for _, c in coords)
            max_c = max(c for _, c in coords)
            shape = [[0 for _ in range(min_c, max_c + 1)] for _ in range(min_r, max_r + 1)]
            for r, c in coords:
                shape[r - min_r][c - min_c] = 1
            return shape

        for r in range(rows):
            for c in range(cols):
                if padded_matrix[r][c] == 1 and not visited[r][c]:
                    coords = []
                    dfs(r, c, coords)
                    blocks.append(normalize(coords))

        return blocks

    def draw_move_preview(self, image, gamegrid, move):
        preview = image.copy()
        for row_idx, row in enumerate(gamegrid):
            for col_idx, value in enumerate(row):
                top_left = (col_idx * self.block_width, row_idx * self.block_height)
                bottom_right = (
                    min(top_left[0] + self.block_width, preview.shape[1] - 1),
                    min(top_left[1] + self.block_height, preview.shape[0] - 1),
                )
                cv2.rectangle(preview, top_left, bottom_right, (40, 40, 40), 1)
                if value != 0:
                    cv2.rectangle(preview, top_left, bottom_right, (70, 70, 180), 1)

        if not move:
            cv2.putText(preview, 'No valid move found', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return preview

        simulation = move['simulation']
        for row_idx, col_idx in simulation['placed_cells']:
            top_left = (col_idx * self.block_width, row_idx * self.block_height)
            bottom_right = (
                min(top_left[0] + self.block_width, preview.shape[1] - 1),
                min(top_left[1] + self.block_height, preview.shape[0] - 1),
            )
            overlay = preview.copy()
            cv2.rectangle(overlay, top_left, bottom_right, (0, 210, 0), -1)
            preview = cv2.addWeighted(overlay, 0.35, preview, 0.65, 0)
            cv2.rectangle(preview, top_left, bottom_right, (0, 255, 0), 2)

        for row_idx, col_idx in simulation['cleared_cells']:
            top_left = (col_idx * self.block_width, row_idx * self.block_height)
            bottom_right = (
                min(top_left[0] + self.block_width, preview.shape[1] - 1),
                min(top_left[1] + self.block_height, preview.shape[0] - 1),
            )
            overlay = preview.copy()
            cv2.rectangle(overlay, top_left, bottom_right, (0, 215, 255), -1)
            preview = cv2.addWeighted(overlay, 0.35, preview, 0.65, 0)
            cv2.rectangle(preview, top_left, bottom_right, (0, 200, 255), 2)

        label = (
            f"Block #{move['block_index'] + 1} -> ({move['x']}, {move['y']}) | "
            f"Clears: {simulation['lines_cleared']}"
        )
        cv2.putText(preview, label, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        return preview

    def render_grid(self, grid, move=None, cell_size=60):
        rows = len(grid)
        cols = len(grid[0]) if rows else 0
        if rows == 0 or cols == 0:
            return np.zeros((120, 240, 3), dtype=np.uint8)

        canvas = np.full((rows * cell_size, cols * cell_size, 3), 30, dtype=np.uint8)
        for row_idx in range(rows):
            for col_idx in range(cols):
                top_left = (col_idx * cell_size, row_idx * cell_size)
                bottom_right = ((col_idx + 1) * cell_size, (row_idx + 1) * cell_size)
                color = (60, 60, 60) if grid[row_idx][col_idx] == 0 else (200, 120, 70)
                cv2.rectangle(canvas, top_left, bottom_right, color, -1)
                cv2.rectangle(canvas, top_left, bottom_right, (25, 25, 25), 1)

        if move:
            simulation = move['simulation']
            for row_idx, col_idx in simulation['placed_cells']:
                top_left = (col_idx * cell_size, row_idx * cell_size)
                bottom_right = ((col_idx + 1) * cell_size, (row_idx + 1) * cell_size)
                cv2.rectangle(canvas, top_left, bottom_right, (0, 220, 0), -1)
                cv2.rectangle(canvas, top_left, bottom_right, (20, 20, 20), 1)
            for row_idx, col_idx in simulation['cleared_cells']:
                top_left = (col_idx * cell_size, row_idx * cell_size)
                bottom_right = ((col_idx + 1) * cell_size, (row_idx + 1) * cell_size)
                cv2.rectangle(canvas, top_left, bottom_right, (0, 215, 255), -1)
                cv2.rectangle(canvas, top_left, bottom_right, (20, 20, 20), 1)

        return canvas
