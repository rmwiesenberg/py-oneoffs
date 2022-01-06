import argparse
import math
import os
import time
from enum import Enum
from typing import Dict, List, Tuple

from PIL import ImageGrab
from pynput import mouse

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(THIS_DIR, 'data')

controller = mouse.Controller()

MAX_INPUT = 7


class Colors(Enum):
    Null = 0
    Red = 1
    Green = 2
    Blue = 3
    Grey = 4


class ScreenLoc:
    def __init__(self, xy: Tuple[int, int]):
        self.xy = xy

    def click(self):
        controller.position = self.xy
        controller.press(mouse.Button.left)
        time.sleep(0.1)
        controller.release(mouse.Button.left)
        time.sleep(0.1)

    def get_raw_color(self):
        raw = ImageGrab.grab().getpixel(self.xy)
        return raw

    def get_color(self, color_lookup: Dict[Tuple[int, int, int], Colors]) -> Colors:
        raw = self.get_raw_color()

        def dist(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
            return math.sqrt(sum((e1 - e2) ** 2 for e1, e2 in zip(a, b)))

        return min(color_lookup.items(), key=lambda x: dist(x[0], raw))[1]


class Curation:
    def __init__(self, *, name: str, ):
        self.name = name
        self.output_file = os.path.join(THIS_DIR, f'{self.name}.csv')

        self.red: ScreenLoc = None
        self.green: ScreenLoc = None
        self.blue: ScreenLoc = None
        self.grey: ScreenLoc = None
        self.backspace: ScreenLoc = None
        self.red: ScreenLoc = None
        self.ok: ScreenLoc = None

        self.color_lookup: Dict[Tuple[int, int, int], Colors] = {}
        self.valid_loc: List[ScreenLoc] = []
        self.invalid_loc: List[ScreenLoc] = []

    @staticmethod
    def wait_for_click() -> ScreenLoc:
        last_pressed: Tuple[int, int] = (-1, -1)

        def on_click(x, y, button, pressed):
            nonlocal last_pressed
            if pressed:
                last_pressed = (x, y)
                print(f'{last_pressed}: {ImageGrab.grab().getpixel(last_pressed)}')
                return False

        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
        return ScreenLoc(last_pressed)

    def valid_colors(self) -> List[Colors]:
        colors = [l.get_color(self.color_lookup) for l in self.valid_loc]
        return colors

    def invalid_colors(self) -> List[Colors]:
        colors = [l.get_color(self.color_lookup) for l in self.invalid_loc]
        return colors

    def clear(self):
        for _ in range(MAX_INPUT):
            self.backspace.click()

    def _set_input_loc(self):
        print('Click on the input buttons, left-to-right, one at a time')
        self.red = self.wait_for_click()
        self.green = self.wait_for_click()
        self.blue = self.wait_for_click()
        self.grey = self.wait_for_click()
        self.backspace = self.wait_for_click()
        self.ok = self.wait_for_click()

        self.clear()

        self.green.click()
        self.green.click()
        self.blue.click()
        self.grey.click()
        self.red.click()
        self.red.click()
        self.blue.click()

        if input('Confirm the sequence is listed as Green, Green, Blue, Grey, Red, Red, Blue. [y/n]').lower() != 'y':
            self._set_input_loc()
            return
        else:
            self.color_lookup = {
                (0, 0, 0): Colors.Null,
                self.red.get_raw_color(): Colors.Red,
                self.green.get_raw_color(): Colors.Green,
                self.blue.get_raw_color(): Colors.Blue,
                self.grey.get_raw_color(): Colors.Grey,
            }
            print(self.color_lookup)

    def _set_valid_loc(self):
        print('Click one each segment of the first valid caterpillar, left-to-right, one at a time (7 total clicks).')
        self.valid_loc = []
        for _ in range(MAX_INPUT):
            self.valid_loc.append(self.wait_for_click())

        colors = self.valid_colors()
        if input(f'Confirm the colors of the first valid caterpillar: {colors} [y/n]').lower() != 'y':
            self._set_valid_loc()

    def _set_invalid_loc(self):
        print('Click one each segment of the first invalid caterpillar, left-to-right, one at a time (7 total clicks).')
        self.invalid_loc = []
        for _ in range(MAX_INPUT):
            self.invalid_loc.append(self.wait_for_click())

        colors = self.invalid_colors()
        if input(f'Confirm the colors of the first invalid caterpillar: {colors} [y/n]').lower() != 'y':
            self._set_invalid_loc()

    def calibrate(self):
        self._set_input_loc()
        self._set_valid_loc()
        self._set_invalid_loc()

    def curate(self):
        os.makedirs(DATA_DIR, exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    args = parser.parse_args()

    curation = Curation(name=args.name)
    curation.calibrate()
    curation.curate()


if __name__ == '__main__':
    main()
