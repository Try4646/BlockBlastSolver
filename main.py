import os

import cv2
import numpy as np
import pyautogui
import time
import AlgoClass
from GameClass import Game


while True:
    print("[!] ayri wähl ma (1 pc, 2 handy) -> ")
    choice = int(input())
    if choice == 1:
        game = Game(pc=True, phone=False)
        break
    if choice == 2:
        game = Game(phone=True, pc=False)
        break
    else:
        print("\n" * 11)
        print("gib mal richtig ein")
        continue


debounce = False
while True:
    if debounce == True:
        print("\n" * 9)

    time.sleep(2)
    screenshot = pyautogui.screenshot(
        region=(game.top_left[0], game.top_left[1], game.bottom_right[0] - game.top_left[0], game.bottom_right[1] - game.top_left[1]))

    screenshotb = pyautogui.screenshot(
        region=(game.top_left_b[0], game.top_left_b[1], game.bottom_right_b[0] - game.top_left_b[0], game.bottom_right_b[1] - game.top_left_b[1]))

    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    screenshotb = cv2.cvtColor(np.array(screenshotb), cv2.COLOR_RGB2BGR)

    cv2.imshow("game Screen", screenshot)
    cv2.imshow("block", screenshotb)

    gamegrid = game.generate_grid(screenshot)
    print("Game Area:")
    for row in gamegrid:
        print(row)

    givengrid, result_image = game.detect_blocks(screenshotb)

    print("given blocks")
    for row in givengrid:
        print(row)
    game_area = gamegrid
    given_blocks = givengrid

    shapes = game.extract_blocks(given_blocks)

    for i, shape in enumerate(shapes):
        print(f"Shape {i + 1}:")
        for row in shape:
            print(row)
        print()

    #ki kacke
    ai = AlgoClass.AI(gamegrid, shapes, debug=True)
    best_move = ai.calculate_best_move()
    ai.print_gamegrid_with_move(best_move)

    debounce = True
    if cv2.waitKey(1) == 27:
        break

cv2.destroyAllWindows()
