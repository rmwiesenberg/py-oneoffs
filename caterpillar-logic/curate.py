import argparse
import json
import logging
import os
import random
from itertools import product
from typing import Dict, List

from pynput import mouse

from common import InputScreen, Caterpillar, MAX_CATERPILLAR_SIZE, Color, DATA_DIR, NUM_DEFAULT_CATERPILLARS

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
REFRESH_SPACE = 5460
DEFAULT_THRESH = 0.05

controller = mouse.Controller()


def gen_space() -> Dict[int, List[Caterpillar]]:
    caterpillars = {i + 1: [] for i in range(MAX_CATERPILLAR_SIZE)}
    for to_fill in range(MAX_CATERPILLAR_SIZE):
        to_fill = to_fill + 1
        combinations = product([1, 2, 3, 4], repeat=to_fill)
        for combination in combinations:
            full_value = [Color(c) for c in combination] + [Color.Null] * (MAX_CATERPILLAR_SIZE - to_fill)
            caterpillars[to_fill].append(Caterpillar(tuple(full_value)))
    return caterpillars


def curate_randomly(*, name: str, thresh: float = DEFAULT_THRESH, min_caterpillars: int = 2):
    game_screen = InputScreen()
    game_screen.init()

    data_space = gen_space()

    datasets = set()
    for caterpillar_len, caterpillars in data_space.items():
        logging.info(f'{len(caterpillars)} of length {caterpillar_len} caterpillars.')
        dataset_idx = []
        for idx, caterpillar in enumerate(caterpillars):
            rand_val = random.random()
            if rand_val < thresh:
                dataset_idx.append(idx)

        while len(dataset_idx) > min(min_caterpillars, len(caterpillars)):
            rand_val = random.randint(0, len(caterpillars) - 1)
            if rand_val in dataset_idx:
                continue
            dataset_idx.append(rand_val)
        datasets.update(caterpillars[idx] for idx in dataset_idx)

    logging.info(f'Collected all datasets')

    game_screen.clear()
    space_results = [(c.json(), game_screen.check_caterpillar(c)) for c in datasets]

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, f'{name}.json'), 'w') as f:
        json.dump(space_results, f)


def curate_refresh(*, name: str, thresh: float = DEFAULT_THRESH):
    game_screen = InputScreen()
    game_screen.init()

    goal = int(REFRESH_SPACE * thresh)
    print(f'Logging {goal} of {REFRESH_SPACE} total Caterpillars.')

    datasets = {}
    while len(datasets) < goal:
        game_screen.open_level()
        for idx in range(NUM_DEFAULT_CATERPILLARS):
            valid_caterpillar = game_screen.valid_caterpillar(idx)
            invalid_caterpillar = game_screen.invalid_caterpillar(idx)
            if valid_caterpillar == invalid_caterpillar:
                logging.debug('Level screen is likely open. stopping read.')
                break
            datasets[valid_caterpillar] = True
            datasets[invalid_caterpillar] = False
        print(f'Collected {len(datasets)} of {goal} caterpillars.')
        game_screen.back_out()

    space_results = [(c.json(), v) for c, v in datasets.items()]
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, f'{name}.json'), 'w') as f:
        json.dump(space_results, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--thresh', default=DEFAULT_THRESH)
    args = parser.parse_args()

    curate_refresh(
        name=input('Open the level and enter the level name'),
        thresh=args.thresh
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
