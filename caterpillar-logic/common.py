import json
import logging
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

MAX_CATERPILLAR_SIZE = 7
DEFAULT_CATERPILLAR_SIZE = 6
NUM_DEFAULT_CATERPILLARS = 7
CLICK_DELAY = 0.05
controller = mouse.Controller()


class Color(Enum):
    Null = 0
    Red = 1
    Green = 2
    Blue = 3
    Grey = 4

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)


class Caterpillar:
    def __init__(self, combo: Tuple[Color]):
        assert isinstance(combo, tuple)
        assert len(combo) == MAX_CATERPILLAR_SIZE, combo

        self.combo = combo

    def __str__(self):
        return f'Catepillar({",".join(str(c).rjust(5) for c in self.combo)})'

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return self.combo.__hash__()

    def __eq__(self, other):
        if not isinstance(other, Caterpillar):
            raise TypeError()
        return all(a == b for a, b in zip(other.combo, self.combo))

    def __len__(self):
        return sum(c.value > 0 for c in self.combo)

    def json(self) -> List[int]:
        return [c.value for c in self.combo]


class ScreenLoc:
    def __init__(self, xy: Tuple[int, int]):
        self.xy = xy

    def __add__(self, other):
        if not isinstance(other, ScreenLoc):
            raise TypeError()
        return ScreenLoc((other.xy[0] + self.xy[0], other.xy[1] + self.xy[1]))

    def click(self):
        controller.position = self.xy
        controller.press(mouse.Button.left)
        time.sleep(CLICK_DELAY)
        controller.release(mouse.Button.left)
        time.sleep(CLICK_DELAY)

    def get_raw_color(self):
        raw = ImageGrab.grab().getpixel(self.xy)
        return raw

    def get_color(self, color_lookup: Dict[Tuple[int, int, int], Color]) -> Color:
        raw = self.get_raw_color()

        def dist(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
            return math.sqrt(sum((e1 - e2) ** 2 for e1, e2 in zip(a, b)))

        return min(color_lookup.items(), key=lambda x: dist(x[0], raw))[1]


class GameScreen:
    def __init__(self):
        self.level: ScreenLoc = None
        self.back: ScreenLoc = None

        self.red: ScreenLoc = None
        self.green: ScreenLoc = None
        self.blue: ScreenLoc = None
        self.grey: ScreenLoc = None
        self.delete: ScreenLoc = None
        self.red: ScreenLoc = None
        self.ok: ScreenLoc = None

        self.color_lookup: Dict[Tuple[int, int, int], Color] = {}
        self.valid_loc: List[ScreenLoc] = []
        self.invalid_loc: List[ScreenLoc] = []
        self.cat_offsets: List[ScreenLoc] = []

    @staticmethod
    def wait_for_click() -> ScreenLoc:
        last_pressed: Tuple[int, int] = (-1, -1)

        def on_click(x, y, button, pressed):
            nonlocal last_pressed
            if pressed:
                last_pressed = (x, y)
                logging.debug(f'{last_pressed}: {ImageGrab.grab().getpixel(last_pressed)}')
                return False

        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
        return ScreenLoc(last_pressed)

    def open_level(self):
        while self.valid_caterpillar() == self.invalid_caterpillar():
            self.level.click()
        self.clear()

    def back_out(self):
        while self.valid_caterpillar() != self.invalid_caterpillar():
            self.back.click()
            time.sleep(1)

    def valid_caterpillar(self, idx: int = 0) -> Caterpillar:
        offset = self.cat_offsets[idx]
        colors = [(loc + offset).get_color(self.color_lookup) for loc in self.valid_loc]
        caterpillar = Caterpillar(tuple(colors))
        return caterpillar

    def invalid_caterpillar(self, idx: int = 0) -> Caterpillar:
        offset = self.cat_offsets[idx]
        colors = [(loc + offset).get_color(self.color_lookup) for loc in self.invalid_loc]
        caterpillar = Caterpillar(tuple(colors))
        return caterpillar

    def clear(self):
        for _ in range(MAX_CATERPILLAR_SIZE):
            self.delete.click()

    def _set_meta_buttons(self):
        print('Click on the back button')
        self.back = self.wait_for_click()
        print('Click on the level')
        self.level = self.wait_for_click()

    def _set_color_lookup(self):
        self.color_lookup = {
            (0, 0, 0): Color.Null,
            self.red.get_raw_color(): Color.Red,
            self.green.get_raw_color(): Color.Green,
            self.blue.get_raw_color(): Color.Blue,
            self.grey.get_raw_color(): Color.Grey,
        }
        logging.debug(self.color_lookup)

    def _set_input_loc(self):
        print('Click on the input buttons, left-to-right, one at a time')
        self.red = self.wait_for_click()
        self.green = self.wait_for_click()
        self.blue = self.wait_for_click()
        self.grey = self.wait_for_click()
        self.delete = self.wait_for_click()
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

    def _set_caterpillar_offsets(self):
        print('Click on the first segment of each valid caterpillar (7 total clicks).')
        self.cat_offsets = []
        first_y = self.wait_for_click().xy[1]
        self.cat_offsets.append(ScreenLoc((0, 0)))
        for _ in range(NUM_DEFAULT_CATERPILLARS - 1):
            screen_loc = self.wait_for_click()
            # only use the y component
            self.cat_offsets.append(ScreenLoc((0, screen_loc.xy[1] - first_y)))

    def _confirm_valid_loc(self):
        caterpillars = []
        logging.info('Please wait while reading the caterpillars from the screen...')
        for idx in range(NUM_DEFAULT_CATERPILLARS):
            caterpillars.append(self.valid_caterpillar(idx))
        fmt_str = 'Confirm the colors of the valid caterpillars:\n{}\n[y/n]'
        if input(fmt_str.format("\n".join([str(c) for c in caterpillars]))).lower() != 'y':
            self._set_caterpillar_offsets()
            self._set_valid_loc()

    def _set_valid_loc(self):
        print('Click one each segment of the first valid caterpillar, left-to-right, one at a time (7 total clicks).')
        self.valid_loc = []
        for _ in range(MAX_CATERPILLAR_SIZE):
            self.valid_loc.append(self.wait_for_click())
        self._confirm_valid_loc()

    def _confirm_invalid_loc(self):
        caterpillars = []
        logging.info('Please wait while reading the caterpillars from the screen...')
        for idx in range(NUM_DEFAULT_CATERPILLARS):
            caterpillars.append(self.invalid_caterpillar(idx))
        fmt_str = 'Confirm the colors of the invalid caterpillars:\n{}\n[y/n]'
        if input(fmt_str.format("\n".join([str(c) for c in caterpillars]))).lower() != 'y':
            self._set_invalid_loc()

    def _set_invalid_loc(self):
        print('Click one each segment of the first invalid caterpillar, left-to-right, one at a time (7 total clicks).')
        self.invalid_loc = []
        for _ in range(MAX_CATERPILLAR_SIZE):
            self.invalid_loc.append(self.wait_for_click())
        self._confirm_invalid_loc()

    def init(self):
        if not self.load():
            self._set_input_loc()
            self._set_caterpillar_offsets()
            self._set_valid_loc()
            self._set_invalid_loc()
            self.dump()
        self._set_meta_buttons()

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
            self.delete = ScreenLoc(tuple(settings['backspace']))
            if 'ok' not in settings:
                return False
            self.ok = ScreenLoc(tuple(settings['ok']))
            self._set_color_lookup()
            if 'offsets' not in settings:
                return False
            self.cat_offsets = [ScreenLoc(tuple(v)) for v in settings['offsets']]
            if 'valid' not in settings:
                return False
            self.valid_loc = [ScreenLoc(tuple(v)) for v in settings['valid']]
            if len(self.valid_loc) != MAX_CATERPILLAR_SIZE:
                return False
            self._confirm_valid_loc()
            if 'invalid' not in settings:
                return False
            self.invalid_loc = [ScreenLoc(tuple(v)) for v in settings['invalid']]
            if len(self.invalid_loc) != MAX_CATERPILLAR_SIZE:
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
                'backspace': self.delete.xy,
                'ok': self.ok.xy,
                'offsets': [o.xy for o in self.cat_offsets],
                'valid': [v.xy for v in self.valid_loc],
                'invalid': [i.xy for i in self.invalid_loc]
            }, f)

    def check_caterpillar(self, caterpillar: Caterpillar) -> bool:
        logging.info(f'Checking {caterpillar}')
        for color in caterpillar.combo:
            if color == Color.Red:
                self.red.click()
            if color == Color.Green:
                self.green.click()
            if color == Color.Blue:
                self.blue.click()
            if color == Color.Grey:
                self.grey.click()
        self.ok.click()
        # add a delay for the caterpillar to be validated lol
        iteration = 100
        for _ in range(iteration):
            if caterpillar == self.valid_caterpillar():
                logging.info(f'{caterpillar}: Valid')
                return True
            elif caterpillar == self.invalid_caterpillar():
                logging.info(f'{caterpillar}: Invalid')
                return False
            time.sleep(0.01)
        raise AssertionError(f'Could not find {caterpillar}')
