"""Rasterize the 12 Cburnett SVG pieces into PNG, in the two sizes the client uses.

Run once; the PNGs are committed. Nothing rasterizes SVG at runtime, so this is a
resource-generation tool, not a project dependency - which is why cairosvg was
rejected in favour of pygame's SDL_image/nanosvg path (ADR-038).

    python tools/rasterize_pieces.py

Two sizes (see ROADMAP 0.4): 80 px for the board (8 x 80 = 640 plus a side panel
fits two windows on a 1920 screen) and 32 px for the captured-piece strip in 3.7.

Why the geometry is scaled instead of the viewBox: the nanosvg rasterizer inside
SDL_image 2.0.5 honours the root width and height as the canvas size but does not
scale the drawing to fit it. Rewriting width/height (with or without a viewBox)
therefore produces a correctly sized canvas holding a piece drawn at its original
45 px scale - too small at 80 px, cropped at 32 px. Measured, not assumed: the
queen's ink spanned 39x35 px at (3,5) in both the 80 px and the 32 px render.

So the drawing itself is scaled, by wrapping the root's children in a
<g transform="scale(...)">. The scale factor comes from the file's own viewBox, or
from its width and height when it has none. It is never assumed: a file with
neither is reported and stops the run, because guessing produces a silently
cropped piece that still has the right output dimensions and non-empty pixels.

The originals on disk are never modified - the rewrite happens on an in-memory tree.

Three checks run on the result, because the first two alone let the bug above
through: every file is reloaded from disk and checked for the exact target size and
for at least one opaque pixel, and then each piece's ink is compared ACROSS sizes.
That last one is the real check. What the ink covers, as a fraction of the canvas,
must not depend on the canvas: a piece filling 31% at 80 px and 62% at 32 px is not
scaled, it is cropped. Those checks live in the tool rather than in the test suite
because the failure can only happen while generating, and that is when the tool runs.
"""

import io
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pygame

SVG_NS = "http://www.w3.org/2000/svg"

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "assets" / "pieces" / "svg"
PNG_DIR = ROOT / "assets" / "pieces" / "png"

# FEN letters: w/b prefix, then p n b r q k. Same names work in JS in phase 4.
PIECES = ("wp", "wn", "wb", "wr", "wq", "wk", "bp", "bn", "bb", "br", "bq", "bk")

SIZES = (80, 32)

# One pixel is 3.1% of a 32 px canvas, so rounding alone moves the fraction by a few
# percent. The failure this guards against moves it by tens of percent.
FILL_TOLERANCE = 0.08

_NUMBER = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*(px)?\s*$")


def _length(value: str | None) -> float | None:
    """Return `value` as a number, or None if it is absent or carries a real unit."""
    if value is None:
        return None
    match = _NUMBER.match(value)
    if match is None:
        return None
    return float(match.group(1))


def user_space(root: ET.Element) -> tuple[float, float, float, float]:
    """Return the (min_x, min_y, width, height) the file's own coordinates cover.

    Raises ValueError when the file declares neither a viewBox nor usable width and
    height - that is a finding, not something to guess at.
    """
    view_box = root.get("viewBox")
    if view_box is not None:
        parts = [_length(p) for p in re.split(r"[\s,]+", view_box.strip())]
        if len(parts) == 4 and all(p is not None for p in parts):
            return parts[0], parts[1], parts[2], parts[3]
        raise ValueError(f"unreadable viewBox {view_box!r}")

    width = _length(root.get("width"))
    height = _length(root.get("height"))
    if width is None or height is None:
        raise ValueError(
            f"no viewBox and no usable width/height "
            f"(width={root.get('width')!r}, height={root.get('height')!r})"
        )
    return 0.0, 0.0, width, height


def scaled_svg(svg_path: Path, size: int) -> bytes:
    """Return the SVG at `svg_path` rewritten to draw at `size` x `size` pixels."""
    root = ET.parse(svg_path).getroot()
    min_x, min_y, width, height = user_space(root)
    if width <= 0 or height <= 0:
        raise ValueError(f"non-positive user space {width}x{height}")

    # A transform list is applied right to left: shift the user space onto the
    # origin first, then scale it up to the target size.
    shift = f"translate({-min_x:g} {-min_y:g})"
    scale = f"scale({size / width:g} {size / height:g})"

    group = ET.Element(f"{{{SVG_NS}}}g")
    group.set("transform", f"{scale} {shift}")
    for child in list(root):
        root.remove(child)
        group.append(child)
    root.append(group)

    root.set("width", str(size))
    root.set("height", str(size))
    # The scale is baked into the transform; leaving a viewBox would apply it twice
    # in any renderer that does honour it.
    root.attrib.pop("viewBox", None)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def ink_fraction(png_path: Path, size: int) -> tuple[float, float] | str:
    """Return how much of the canvas the opaque pixels span, or a complaint."""
    surface = pygame.image.load(png_path)
    if surface.get_size() != (size, size):
        got = "x".join(str(n) for n in surface.get_size())
        return f"{png_path}: expected {size}x{size}, got {got}"

    rects = pygame.mask.from_surface(surface).get_bounding_rects()
    if not rects:
        return f"{png_path}: fully transparent - the rasterizer returned an empty surface"

    box = rects[0].unionall(rects[1:])
    return box.width / size, box.height / size


def main() -> int:
    ET.register_namespace("", SVG_NS)  # otherwise ElementTree writes ns0: prefixes

    problems: list[str] = []
    fills: dict[tuple[str, int], tuple[float, float]] = {}
    rows: list[tuple[int, str, int, tuple[float, float]]] = []

    for size in SIZES:
        out_dir = PNG_DIR / str(size)
        out_dir.mkdir(parents=True, exist_ok=True)

        for name in PIECES:
            svg_path = SVG_DIR / f"{name}.svg"
            if not svg_path.is_file():
                problems.append(f"{svg_path}: missing")
                continue

            png_path = out_dir / f"{name}.png"
            try:
                surface = pygame.image.load(io.BytesIO(scaled_svg(svg_path, size)), "piece.svg")
            except (ValueError, pygame.error) as exc:
                problems.append(f"{svg_path}: {exc}")
                continue

            pygame.image.save(surface, png_path)

            result = ink_fraction(png_path, size)
            if isinstance(result, str):
                problems.append(result)
                continue

            fills[name, size] = result
            rows.append((size, name, png_path.stat().st_size, result))

    # The check the other two miss: coverage must not depend on the canvas size.
    for name in PIECES:
        seen = [fills[name, size] for size in SIZES if (name, size) in fills]
        if len(seen) < 2:
            continue
        for axis, label in ((0, "width"), (1, "height")):
            spread = max(f[axis] for f in seen) - min(f[axis] for f in seen)
            if spread > FILL_TOLERANCE:
                covered = ", ".join(f"{size}px={fills[name, size][axis]:.0%}" for size in SIZES)
                problems.append(
                    f"{name}: ink {label} covers a different share of each canvas "
                    f"({covered}) - the drawing was not scaled, only the canvas was"
                )

    for size, name, byte_count, fill in rows:
        print(f"{size:>3}px  {name}  {byte_count:>6} B   ink {fill[0]:.0%} x {fill[1]:.0%}")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for problem in problems:
            print("  " + problem)
        return 1

    print(f"\nOK: {len(rows)} files written and verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
