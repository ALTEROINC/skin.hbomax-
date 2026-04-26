#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "tools" / "_vendor"
if VENDOR.exists():
    sys.path.insert(0, str(VENDOR))

from PIL import Image, ImageDraw, ImageFont  # type: ignore


PURPLE = (0x6B, 0x3F, 0xA0, 255)
BACKGROUND = (0x0A, 0x0A, 0x0F, 255)
WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_png(path: Path, image: Image.Image) -> None:
    ensure_parent(path)
    image.save(path, format="PNG")


def save_jpg(path: Path, image: Image.Image) -> None:
    ensure_parent(path)
    image.convert("RGB").save(path, format="JPEG", quality=90)


def make_solid_png(path: Path, size: tuple[int, int], color: tuple[int, int, int, int]) -> None:
    save_png(path, Image.new("RGBA", size, color))


def make_solid_jpg(path: Path, size: tuple[int, int], color: tuple[int, int, int, int]) -> None:
    save_jpg(path, Image.new("RGBA", size, color))


def make_icon_png(path: Path, size: tuple[int, int]) -> None:
    image = Image.new("RGBA", size, PURPLE)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = "HM"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size[0] - text_width) / 2
    y = (size[1] - text_height) / 2 - 4
    draw.text((x, y), text, font=font, fill=WHITE)
    save_png(path, image)


def make_gradient_png(path: Path, size: tuple[int, int], top_alpha: int, bottom_alpha: int) -> None:
    image = Image.new("RGBA", size, TRANSPARENT)
    for y in range(size[1]):
        ratio = y / max(size[1] - 1, 1)
        alpha = int(top_alpha + (bottom_alpha - top_alpha) * ratio)
        row = Image.new("RGBA", (size[0], 1), (BACKGROUND[0], BACKGROUND[1], BACKGROUND[2], alpha))
        image.paste(row, (0, y))
    save_png(path, image)


def make_circle_mask(path: Path, size: tuple[int, int]) -> None:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, size[0] - 1, size[1] - 1), fill=WHITE)
    save_png(path, image)


def make_focus_ring(path: Path, size: tuple[int, int], border: int = 8) -> None:
    image = Image.new("RGBA", size, TRANSPARENT)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((border // 2, border // 2, size[0] - border // 2 - 1, size[1] - border // 2 - 1), radius=18, outline=WHITE, width=border)
    save_png(path, image)


def make_shadow(path: Path, size: tuple[int, int]) -> None:
    image = Image.new("RGBA", size, (0, 0, 0, 96))
    save_png(path, image)


def make_scrubber(path: Path, size: tuple[int, int]) -> None:
    image = Image.new("RGBA", size, TRANSPARENT)
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, size[0] - 1, size[1] - 1), fill=WHITE)
    save_png(path, image)


def make_dot(path: Path, size: tuple[int, int]) -> None:
    image = Image.new("RGBA", size, TRANSPARENT)
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, size[0] - 1, size[1] - 1), fill=WHITE)
    save_png(path, image)


def make_placeholder_poster(path: Path, size: tuple[int, int], label: str) -> None:
    image = Image.new("RGBA", size, BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), label, font=font)
    x = (size[0] - (bbox[2] - bbox[0])) / 2
    y = (size[1] - (bbox[3] - bbox[1])) / 2
    draw.text((x, y), label, font=font, fill=WHITE)
    save_png(path, image)


def make_simple_icon(path: Path, size: tuple[int, int], label: str) -> None:
    image = Image.new("RGBA", size, TRANSPARENT)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), label, font=font)
    x = (size[0] - (bbox[2] - bbox[0])) / 2
    y = (size[1] - (bbox[3] - bbox[1])) / 2 - 1
    draw.text((x, y), label, font=font, fill=WHITE)
    save_png(path, image)


def main() -> None:
    resources_dir = ROOT / "resources"
    media_dir = ROOT / "media" / "hbomax"
    backgrounds_dir = media_dir / "backgrounds"
    icons_dir = media_dir / "icons"

    make_icon_png(resources_dir / "icon.png", (256, 256))
    make_solid_jpg(resources_dir / "fanart.jpg", (1280, 720), BACKGROUND)

    make_gradient_png(media_dir / "hero-gradient.png", (1920, 300), 0, 242)
    make_gradient_png(media_dir / "osd-top-gradient.png", (1920, 120), 242, 0)
    make_focus_ring(media_dir / "card-focus.png", (64, 64))
    make_shadow(media_dir / "card-shadow.png", (64, 64))
    make_solid_png(media_dir / "nav-background.png", (1920, 72), (18, 16, 26, 224))
    make_icon_png(media_dir / "logo.png", (512, 256))
    make_solid_png(media_dir / "btn-primary.png", (200, 56), PURPLE)
    make_solid_png(media_dir / "btn-secondary.png", (200, 56), (28, 24, 48, 255))
    make_circle_mask(media_dir / "circle-mask.png", (100, 100))
    make_scrubber(media_dir / "osd-scrubber.png", (28, 28))
    make_solid_png(media_dir / "progress-bar-bg.png", (140, 4), (255, 255, 255, 51))
    make_solid_png(media_dir / "progress-bar-fill.png", (140, 4), PURPLE)
    make_placeholder_poster(media_dir / "placeholder-poster.png", (280, 420), "POSTER")
    make_placeholder_poster(media_dir / "placeholder-landscape.png", (640, 360), "LANDSCAPE")
    make_dot(media_dir / "dot.png", (16, 16))
    make_solid_jpg(backgrounds_dir / "default-bg.jpg", (1920, 1080), BACKGROUND)

    icons = {
        "play.png": "P",
        "pause.png": "II",
        "plus.png": "+",
        "download.png": "D",
        "close.png": "X",
        "back.png": "<",
        "settings.png": "S",
        "search.png": "?",
        "home.png": "H",
        "movies.png": "M",
        "tvshows.png": "TV",
        "livetv.png": "L",
        "dropdown.png": "V",
        "previous.png": "|<",
        "next.png": ">|",
        "rewind.png": "<<",
        "forward.png": ">>",
        "volume.png": "V",
        "subtitles.png": "CC",
        "audio.png": "A",
        "info.png": "i",
    }
    for filename, label in icons.items():
        make_simple_icon(icons_dir / filename, (64, 64), label)

    print("Created placeholder assets in resources/ and media/hbomax/")


if __name__ == "__main__":
    main()
