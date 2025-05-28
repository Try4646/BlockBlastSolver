class AI:
    def __init__(self, gamegrid, blockgrid, debug=False):
        self.gamegrid = gamegrid  # 2D list representing the game board
        self.givenblocksgrid = blockgrid  # List of 2D blocks
        self.debug = debug  # Toggle debug output

    def is_valid_placement(self, block, x, y):
        """Check if the block can be placed at position (x, y) on the current gamegrid."""
        return self.is_valid_placement_on_grid(block, x, y, self.gamegrid)

    def is_valid_placement_on_grid(self, block, x, y, grid):
        """Check if the block can be placed at position (x, y) on the specified grid."""
        for i in range(len(block)):
            for j in range(len(block[i])):
                if block[i][j] == 1:
                    grid_x = x + i
                    grid_y = y + j
                    if not (0 <= grid_x < len(grid) and 0 <= grid_y < len(grid[0])):
                        return False
                    if grid[grid_x][grid_y] != 0:
                        return False
        return True

    def simulate_move(self, block, x, y):
        """Simulate placing the block and return a new game grid."""
        if not self.is_valid_placement(block, x, y):
            return None

        new_grid = [row[:] for row in self.gamegrid]
        for i in range(len(block)):
            for j in range(len(block[i])):
                if block[i][j] == 1:
                    new_grid[x + i][y + j] = 2  # Use 2 to mark simulated block
        return new_grid

    def evaluate_grid(self, grid):
        """Evaluate the grid by counting complete rows and columns (Block Blast scoring style)."""
        score = 0
        size = len(grid)

        # Score full rows
        for row in grid:
            if all(cell != 0 for cell in row):
                score += 1

        # Score full columns
        for col in range(len(grid[0])):
            if all(grid[row][col] != 0 for row in range(size)):
                score += 1

        return score

    def any_valid_placement(self, block, grid):
        """Return True if there is at least one valid placement for the block on the grid."""
        block_height = len(block)
        block_width = len(block[0])

        for x in range(len(grid) - block_height + 1):
            for y in range(len(grid[0]) - block_width + 1):
                if self.is_valid_placement_on_grid(block, x, y, grid):
                    return True
        return False

    def calculate_best_move(self):
        """Find the best move considering current score and possibility for future moves."""
        best_move = None
        best_score = -1

        for block in self.givenblocksgrid:
            block_height = len(block)
            block_width = len(block[0])

            for x in range(len(self.gamegrid) - block_height + 1):
                for y in range(len(self.gamegrid[0]) - block_width + 1):
                    new_grid = self.simulate_move(block, x, y)
                    if new_grid:
                        score = self.evaluate_grid(new_grid)

                        # Check if other blocks can be placed after this move
                        can_continue = False
                        for other_block in self.givenblocksgrid:
                            if other_block == block:
                                continue  # skip the current block
                            if self.any_valid_placement(other_block, new_grid):
                                can_continue = True
                                break

                        if self.debug:
                            print(f"Trying block at ({x}, {y}) -> score: {score}, can_continue: {can_continue}")

                        # Prefer higher score; among equals, prefer moves that allow future placements
                        if score > best_score or (score == best_score and can_continue):
                            best_score = score
                            best_move = (block, x, y)

        return best_move

    def print_gamegrid_with_move(self, move):
        """Print the game grid with the best move placed."""
        if not move:
            print("No valid move could be found.")
            return

        block, start_x, start_y = move
        new_grid = [row[:] for row in self.gamegrid]

        for i in range(len(block)):
            for j in range(len(block[i])):
                if block[i][j] == 1:
                    new_grid[start_x + i][start_y + j] = 2

        print("Game Grid with Best Move (Block placed as 2):")
        for row in new_grid:
            print(", ".join(map(str, row)))
