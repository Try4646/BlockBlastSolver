import time

import cv2
import numpy as np
import pyautogui

import AlgoClass
from GameClass import Game


REFRESH_SECONDS = 0.6
WINDOW_NAMES = ('game Screen', 'block', 'simulation')


while True:
    print('[!] choose mode (1 pc, 2 phone) -> ')
    choice = int(input())
    if choice == 1:
        game = Game(pc=True, phone=False)
        break
    if choice == 2:
        game = Game(phone=True, pc=False)
        break
    print('\n' * 11)
    print('enter a valid option')

for window_name in WINDOW_NAMES:
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

last_summary = None
last_signature = None
cached_views = None
while True:
    screenshot = pyautogui.screenshot(
        region=(
            game.top_left[0],
            game.top_left[1],
            game.bottom_right[0] - game.top_left[0],
            game.bottom_right[1] - game.top_left[1],
        )
    )
    screenshotb = pyautogui.screenshot(
        region=(
            game.top_left_b[0],
            game.top_left_b[1],
            game.bottom_right_b[0] - game.top_left_b[0],
            game.bottom_right_b[1] - game.top_left_b[1],
        )
    )

    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    screenshotb = cv2.cvtColor(np.array(screenshotb), cv2.COLOR_RGB2BGR)

    gamegrid = game.generate_grid(screenshot)
    givengrid, result_image = game.detect_blocks(screenshotb)
    shapes = game.extract_blocks(givengrid)
    signature = (tuple(tuple(row) for row in gamegrid), tuple(tuple(tuple(r) for r in shape) for shape in shapes))

    if signature != last_signature:
        ai = AlgoClass.AI(gamegrid, shapes, debug=False)
        best_move = ai.calculate_best_move()

        summary = 'No valid move found'
        if best_move:
            simulation = best_move['simulation']
            summary = (
                f"Block #{best_move['block_index'] + 1} at ({best_move['x']}, {best_move['y']}) "
                f"| clears: {simulation['lines_cleared']}"
            )

        if summary != last_summary:
            print(summary)
            last_summary = summary
            ai.print_gamegrid_with_move(best_move)

        board_preview = game.draw_move_preview(screenshot, gamegrid, best_move)
        simulated_grid = game.render_grid(
            best_move['simulation']['grid'] if best_move else gamegrid,
            move=best_move,
            cell_size=max(36, game.block_width // 2),
        )
        cached_views = (board_preview, result_image, simulated_grid)
        last_signature = signature
    elif cached_views is not None:
        cached_views = (cached_views[0], result_image, cached_views[2])

    if cached_views is not None:
        cv2.imshow('game Screen', cached_views[0])
        cv2.imshow('block', cached_views[1])
        cv2.imshow('simulation', cached_views[2])

    cycle_end = time.time() + REFRESH_SECONDS
    while time.time() < cycle_end:
        if cv2.waitKey(20) == 27:
            cv2.destroyAllWindows()
            raise SystemExit

cv2.destroyAllWindows()
