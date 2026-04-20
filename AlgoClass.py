class AI:
    def __init__(self, gamegrid, blockgrid, debug=False):
        self.gamegrid = [row[:] for row in gamegrid]
        self.givenblocksgrid = [[row[:] for row in block] for block in blockgrid]
        self.debug = debug
        self.size = len(gamegrid)
        self.search_depth = min(2, len(blockgrid))
        self.max_candidates_per_block = 6
        self.eval_cache = {}

    def is_valid_placement(self, block, x, y):
        return self.is_valid_placement_on_grid(block, x, y, self.gamegrid)

    def is_valid_placement_on_grid(self, block, x, y, grid):
        for i in range(len(block)):
            for j in range(len(block[i])):
                if block[i][j] != 1:
                    continue
                grid_x = x + i
                grid_y = y + j
                if not (0 <= grid_x < len(grid) and 0 <= grid_y < len(grid[0])):
                    return False
                if grid[grid_x][grid_y] != 0:
                    return False
        return True

    def grid_key(self, grid):
        return tuple(tuple(row) for row in grid)

    def block_key(self, block):
        return tuple(tuple(row) for row in block)

    def get_valid_moves(self, block, grid):
        moves = []
        block_height = len(block)
        block_width = len(block[0])
        for x in range(len(grid) - block_height + 1):
            for y in range(len(grid[0]) - block_width + 1):
                if self.is_valid_placement_on_grid(block, x, y, grid):
                    moves.append((x, y))
        return moves

    def clear_completed_lines(self, grid):
        new_grid = [row[:] for row in grid]
        full_rows = [idx for idx, row in enumerate(new_grid) if all(cell != 0 for cell in row)]
        full_cols = [idx for idx in range(len(new_grid[0])) if all(new_grid[row][idx] != 0 for row in range(len(new_grid)))]

        for row_idx in full_rows:
            for col_idx in range(len(new_grid[row_idx])):
                new_grid[row_idx][col_idx] = 0

        for col_idx in full_cols:
            for row_idx in range(len(new_grid)):
                new_grid[row_idx][col_idx] = 0

        return new_grid, full_rows, full_cols

    def simulate_move_on_grid(self, block, x, y, grid):
        if not self.is_valid_placement_on_grid(block, x, y, grid):
            return None

        placed_grid = [row[:] for row in grid]
        placed_cells = []
        for i in range(len(block)):
            for j in range(len(block[i])):
                if block[i][j] == 1:
                    row_idx = x + i
                    col_idx = y + j
                    placed_grid[row_idx][col_idx] = 1
                    placed_cells.append((row_idx, col_idx))

        cleared_grid, cleared_rows, cleared_cols = self.clear_completed_lines(placed_grid)
        cleared_cells = set()
        for row_idx in cleared_rows:
            for col_idx in range(len(placed_grid[row_idx])):
                cleared_cells.add((row_idx, col_idx))
        for col_idx in cleared_cols:
            for row_idx in range(len(placed_grid)):
                cleared_cells.add((row_idx, col_idx))

        return {
            'grid': cleared_grid,
            'placed_cells': placed_cells,
            'cleared_cells': sorted(cleared_cells),
            'lines_cleared': len(cleared_rows) + len(cleared_cols),
        }

    def simulate_move(self, block, x, y):
        result = self.simulate_move_on_grid(block, x, y, self.gamegrid)
        if result is None:
            return None
        return result['grid']

    def count_holes(self, grid):
        holes = 0
        for row_idx in range(len(grid)):
            for col_idx in range(len(grid[row_idx])):
                if grid[row_idx][col_idx] != 0:
                    continue
                neighbors = 0
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = row_idx + delta_row
                    next_col = col_idx + delta_col
                    if 0 <= next_row < len(grid) and 0 <= next_col < len(grid[row_idx]) and grid[next_row][next_col] != 0:
                        neighbors += 1
                if neighbors >= 3:
                    holes += 1
        return holes

    def count_components(self, grid):
        visited = set()
        components = 0
        for row_idx in range(len(grid)):
            for col_idx in range(len(grid[row_idx])):
                if grid[row_idx][col_idx] != 0 or (row_idx, col_idx) in visited:
                    continue
                components += 1
                stack = [(row_idx, col_idx)]
                visited.add((row_idx, col_idx))
                while stack:
                    current_row, current_col = stack.pop()
                    for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        next_row = current_row + delta_row
                        next_col = current_col + delta_col
                        if 0 <= next_row < len(grid) and 0 <= next_col < len(grid[current_row]):
                            if grid[next_row][next_col] == 0 and (next_row, next_col) not in visited:
                                visited.add((next_row, next_col))
                                stack.append((next_row, next_col))
        return components

    def count_near_complete_lines(self, grid):
        near_lines = 0
        for row in grid:
            if row.count(0) == 1:
                near_lines += 1
        for col_idx in range(len(grid[0])):
            if sum(1 for row_idx in range(len(grid)) if grid[row_idx][col_idx] == 0) == 1:
                near_lines += 1
        return near_lines

    def placement_flexibility(self, grid, remaining_blocks):
        if not remaining_blocks:
            return 0
        total = 0
        playable = 0
        for block in remaining_blocks:
            move_count = len(self.get_valid_moves(block, grid))
            total += move_count
            if move_count > 0:
                playable += 1
        return total + (playable * 4)

    def evaluate_grid(self, grid, lines_cleared=0, remaining_blocks=None):
        remaining_blocks = remaining_blocks or []
        cache_key = (self.grid_key(grid), lines_cleared, tuple(self.block_key(block) for block in remaining_blocks))
        cached_score = self.eval_cache.get(cache_key)
        if cached_score is not None:
            return cached_score

        empty_cells = sum(cell == 0 for row in grid for cell in row)
        holes = self.count_holes(grid)
        components = self.count_components(grid)
        near_lines = self.count_near_complete_lines(grid)
        flexibility = self.placement_flexibility(grid, remaining_blocks)

        score = 0
        score += lines_cleared * 120
        score += empty_cells * 3
        score += near_lines * 18
        score += flexibility * 2
        score -= holes * 14
        score -= max(0, components - 1) * 10

        self.eval_cache[cache_key] = score
        return score

    def rank_candidate_moves(self, grid, original_index, block, remaining_blocks):
        candidates = []
        for x, y in self.get_valid_moves(block, grid):
            simulation = self.simulate_move_on_grid(block, x, y, grid)
            if simulation is None:
                continue
            base_score = self.evaluate_grid(
                simulation['grid'],
                lines_cleared=simulation['lines_cleared'],
                remaining_blocks=remaining_blocks,
            )
            candidates.append((base_score, x, y, simulation))

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[:self.max_candidates_per_block]

    def search_best_sequence(self, grid, indexed_blocks, depth):
        if depth == 0 or not indexed_blocks:
            return {'score': self.evaluate_grid(grid, remaining_blocks=[block for _, block in indexed_blocks]), 'moves': []}

        best_result = None
        candidate_blocks = []
        for idx, (original_index, block) in enumerate(indexed_blocks):
            remaining = [candidate for inner_idx, (_, candidate) in enumerate(indexed_blocks) if inner_idx != idx]
            ranked_moves = self.rank_candidate_moves(grid, original_index, block, remaining)
            if ranked_moves:
                candidate_blocks.append((idx, original_index, block, remaining, ranked_moves))

        if not candidate_blocks:
            return {
                'score': self.evaluate_grid(grid, remaining_blocks=[block for _, block in indexed_blocks]) - 500,
                'moves': [],
            }

        candidate_blocks.sort(key=lambda item: item[4][0][0], reverse=True)
        candidate_blocks = candidate_blocks[: min(len(candidate_blocks), 3)]

        for _, original_index, block, remaining_blocks, ranked_moves in candidate_blocks:
            for base_score, x, y, simulation in ranked_moves:
                future_indexed_blocks = [
                    (idx, remaining_block)
                    for idx, remaining_block in indexed_blocks
                    if idx != original_index
                ]
                future = self.search_best_sequence(simulation['grid'], future_indexed_blocks, depth - 1)
                total_score = base_score + (future['score'] * 0.45)
                result = {
                    'score': total_score,
                    'moves': [
                        {
                            'block_index': original_index,
                            'block': block,
                            'x': x,
                            'y': y,
                            'simulation': simulation,
                        }
                    ] + future['moves'],
                }

                if self.debug:
                    print(
                        f"Trying block #{original_index + 1} at ({x}, {y}) -> "
                        f"lines: {simulation['lines_cleared']}, score: {total_score:.2f}"
                    )

                if best_result is None or result['score'] > best_result['score']:
                    best_result = result

        return best_result

    def calculate_best_move(self):
        indexed_blocks = list(enumerate(self.givenblocksgrid))
        best_sequence = self.search_best_sequence(self.gamegrid, indexed_blocks, self.search_depth)
        if not best_sequence or not best_sequence['moves']:
            return None
        return best_sequence['moves'][0]

    def print_gamegrid_with_move(self, move):
        if not move:
            print('No valid move could be found.')
            return

        simulation = move['simulation']
        visual_grid = [row[:] for row in self.gamegrid]
        for row_idx, col_idx in simulation['placed_cells']:
            visual_grid[row_idx][col_idx] = 2
        for row_idx, col_idx in simulation['cleared_cells']:
            visual_grid[row_idx][col_idx] = 3

        print('Game Grid with Best Move (2 = placement, 3 = cleared line):')
        for row in visual_grid:
            print(', '.join(map(str, row)))
        print(
            f"Block #{move['block_index'] + 1} at ({move['x']}, {move['y']}) | "
            f"lines cleared: {simulation['lines_cleared']}"
        )
