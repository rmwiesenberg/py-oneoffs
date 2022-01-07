import argparse
import os
from itertools import product
from typing import List

from pynput import mouse

from common import ScreenSettings, Caterpillar, MAX_INPUT, Color

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

controller = mouse.Controller()


def gen_space() -> List[Caterpillar]:
    caterpillars = []
    for to_fill in range(MAX_INPUT):
        to_fill = to_fill + 1
        combinations = product([1, 2, 3, 4], repeat=to_fill)
        for combination in combinations:
            full_value = [Color(c) for c in combination] + [Color.Null] * (MAX_INPUT - to_fill)
            caterpillars.append(Caterpillar(full_value))
    return caterpillars


def curate(*, name: str):
    data_space = gen_space()
    print(f'Data space has {len(data_space)} possible inputs')

    curation = ScreenSettings()
    curation.init()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    args = parser.parse_args()

    curate(name=args.name)


if __name__ == '__main__':
    main()
