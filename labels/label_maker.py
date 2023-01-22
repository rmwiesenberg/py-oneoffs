from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from labels.common import Person

THIS_DIR = Path(__file__).absolute().parent
SANS_FONT = THIS_DIR / 'OpenSans-Regular.ttf'


@dataclass
class LabelMaker:
    width: int
    height: int

    img_fraction = 0.95

    @classmethod
    def from_dpi(cls, dpi: float, width_in: float, height_in: float) -> 'LabelMaker':
        return LabelMaker(width=int(dpi * width_in), height=int(dpi * height_in))

    def get_font(self, fontsize: int) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(str(SANS_FONT), fontsize)

    def does_fit(self, font, str_to_fit: str) -> bool:
        text_size = font.getsize_multiline(str_to_fit)

        return (text_size[0] < (self.img_fraction * self.width) and
                text_size[1] < (self.img_fraction * self.height))

    def __call__(self, person: Person) -> Image.Image:
        img = Image.new('1', size=(self.width, self.height), color=True)
        draw = ImageDraw.Draw(img)

        label_str = str(person)

        fontsize = 1
        while self.does_fit(self.get_font(fontsize), label_str):
            fontsize += 1

        # De-increment to be sure it is less than image size.
        fontsize = max(fontsize - 1, 1)
        font = self.get_font(fontsize)

        draw.multiline_text((10, int(self.height / 2)), label_str, anchor='lm', font=font)

        return img
