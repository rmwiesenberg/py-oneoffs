import argparse
import os

from pynput import mouse

from common import ScreenSettings

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

controller = mouse.Controller()


def curate(*, name: str):
    curation = ScreenSettings()
    curation.init()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    args = parser.parse_args()

    curate(name=args.name)


if __name__ == '__main__':
    main()
