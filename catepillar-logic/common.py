import json
import math
import os
import time
from enum import Enum
from typing import Dict, List, Tuple

from PIL import ImageGrab
from pynput import mouse

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(THIS_DIR, 'data')
CALIBRATION_FILE = os.path.join(THIS_DIR, 'calibration.json')

MAX_INPUT = 7
controller = mouse.Controller()


class Color(Enum):
    Null = 0
    Red = 1
    Green = 2
    Blue = 3
    Grey = 4


class Caterpillar:
    def __init__(self, combo: List[Color]):
        assert len(combo) == MAX_INPUT, combo
        assert combo[0] != Color.Null, combo

        null_started = False
        for color in combo:
            if color == Color.Null:
                null_started = True
            elif null_started:
                raise AssertionError('Poorly constructed caterpillar', combo)

        self.combo = combo


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

    def get_color(self, color_lookup: Dict[Tuple[int, int, int], Color]) -> Color:
        raw = self.get_raw_color()

        def dist(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
            return math.sqrt(sum((e1 - e2) ** 2 for e1, e2 in zip(a, b)))

        return min(color_lookup.items(), key=lambda x: dist(x[0], raw))[1]


class ScreenSettings:
    def __init__(self):
        self.red: ScreenLoc = None
        self.green: ScreenLoc = None
        self.blue: ScreenLoc = None
        self.grey: ScreenLoc = None
        self.backspace: ScreenLoc = None
        self.red: ScreenLoc = None
        self.ok: ScreenLoc = None

        self.color_lookup: Dict[Tuple[int, int, int], Color] = {}
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

    def valid_colors(self) -> List[Color]:
        colors = [l.get_color(self.color_lookup) for l in self.valid_loc]
        return colors

    def invalid_colors(self) -> List[Color]:
        colors = [l.get_color(self.color_lookup) for l in self.invalid_loc]
        return colors

    def clear(self):
        for _ in range(MAX_INPUT):
            self.backspace.click()

    def _set_color_lookup(self):
        self.color_lookup = {
            (0, 0, 0): Color.Null,
            self.red.get_raw_color(): Color.Red,
            self.green.get_raw_color(): Color.Green,
            self.blue.get_raw_color(): Color.Blue,
            self.grey.get_raw_color(): Color.Grey,
        }
        print(self.color_lookup)

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
            self._set_color_lookup()

    def _confirm_valid_loc(self):
        colors = self.valid_colors()
        if input(f'Confirm the colors of the first valid caterpillar: {colors} [y/n]').lower() != 'y':
            self._set_valid_loc()

    def _set_valid_loc(self):
        print('Click one each segment of the first valid caterpillar, left-to-right, one at a time (7 total clicks).')
        self.valid_loc = []
        for _ in range(MAX_INPUT):
            self.valid_loc.append(self.wait_for_click())
        self._confirm_valid_loc()

    def _confirm_invalid_loc(self):
        colors = self.invalid_colors()
        if input(f'Confirm the colors of the first invalid caterpillar: {colors} [y/n]').lower() != 'y':
            self._set_invalid_loc()

    def _set_invalid_loc(self):
        print('Click one each segment of the first invalid caterpillar, left-to-right, one at a time (7 total clicks).')
        self.invalid_loc = []
        for _ in range(MAX_INPUT):
            self.invalid_loc.append(self.wait_for_click())
        self._confirm_invalid_loc()

    def init(self):
        if not self.load():
            self._set_input_loc()
            self._set_valid_loc()
            self._set_invalid_loc()
            self.dump()

    def load(self) -> bool:
        if not os.path.exists(CALIBRATION_FILE):
            return False

        with open(CALIBRATION_FILE, 'r') as f:
            settings = json.load(f)
            if 'red' not in settings:
                return False
            self.red = ScreenLoc(tuple(settings['red']))
            if 'green' not in settings:
                return False
            self.green = ScreenLoc(tuple(settings['green']))
            if 'blue' not in settings:
                return False
            self.blue = ScreenLoc(tuple(settings['blue']))
            if 'grey' not in settings:
                return False
            self.grey = ScreenLoc(tuple(settings['grey']))
            if 'backspace' not in settings:
                return False
            self.backspace = ScreenLoc(tuple(settings['backspace']))
            if 'ok' not in settings:
                return False
            self.ok = ScreenLoc(tuple(settings['ok']))
            self._set_color_lookup()
            if 'valid' not in settings:
                return False
            self.valid_loc = [ScreenLoc(tuple(v)) for v in settings['valid']]
            if len(self.valid_loc) != MAX_INPUT:
                return False
            self._confirm_valid_loc()
            if 'invalid' not in settings:
                return False
            self.invalid_loc = [ScreenLoc(tuple(v)) for v in settings['invalid']]
            if len(self.invalid_loc) != MAX_INPUT:
                return False
            self._confirm_invalid_loc()
        self.dump()
        return True

    def dump(self):
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump({
                'red': self.red.xy,
                'green': self.green.xy,
                'blue': self.blue.xy,
                'grey': self.grey.xy,
                'backspace': self.backspace.xy,
                'ok': self.ok.xy,
                'valid': [v.xy for v in self.valid_loc],
                'invalid': [i.xy for i in self.invalid_loc]
            }, f)
