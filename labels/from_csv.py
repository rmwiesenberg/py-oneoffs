import argparse
from pathlib import Path

import pandas as pd

from common import Person, address_from_str
from labels.label_maker import LabelMaker


def from_csv(csv_file: Path, output_dir: Path) -> None:
    label_fitter = LabelMaker.from_dpi(dpi=208, width_in=2.25, height_in=1.25)
    df = pd.read_csv(csv_file).dropna(subset='Address')
    df['person'] = df.apply(lambda x: Person(x.Name, address_from_str(x.Address)), axis=1)
    df['img'] = df.person.apply(label_fitter)
    df.apply(lambda x: x.img.save(output_dir / f'{x.person.name}.png'), axis=1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv-file', '-i', type=Path, required=True)
    parser.add_argument('--output-dir', '-o', type=Path, required=True)
    args = parser.parse_args()

    csv_file: Path = args.csv_file.expanduser().absolute()
    output_dir: Path = args.output_dir.expanduser().absolute()
    output_dir.mkdir(exist_ok=True, parents=True)

    from_csv(csv_file, output_dir)


if __name__ == '__main__':
    main()
