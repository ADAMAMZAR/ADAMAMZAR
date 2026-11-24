"""Generate assets/hero.svg: name on the left, GitHub avatar with an ASCII overlay on the right.

Usage: python scripts/generate_hero.py [path/to/avatar.jpg]
Without an argument the avatar is downloaded from GitHub. Requires Pillow.
"""

import base64
import io
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageEnhance

USERNAME = "ADAMAMZAR"
FIRST, LAST = "Adam", "Amzar"
ROLE = "AI Engineer · Computer Science Undergraduate"
TAGLINE = "RAG Pipelines / AI Systems / Full-Stack"
OUT = Path(__file__).resolve().parent.parent / "assets" / "hero.svg"

W, H = 1200, 520
CX, CY, R = 880, 260, 205  # avatar circle
COLS = 64  # ASCII grid columns across the circle diameter
RAMP = " .:-=+*#%@"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"


def load_avatar() -> Image.Image:
    if len(sys.argv) > 1:
        return Image.open(sys.argv[1]).convert("RGB")
    url = f"https://github.com/{USERNAME}.png?size=460"
    with urllib.request.urlopen(url) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGB")


def ascii_overlay(img: Image.Image) -> str:
    size = 2 * R
    cell = size / COLS
    rows = int(size / (cell * 1.6))
    row_h = size / rows
    small = ImageEnhance.Contrast(img).enhance(1.4).resize((COLS, rows), Image.LANCZOS)
    pal = small.quantize(colors=10, method=Image.Quantize.MEDIANCUT)
    palette = pal.getpalette()[:30]
    gray = small.convert("L")

    groups = defaultdict(list)  # (row, color index) -> [(x, char)]
    for r in range(rows):
        for c in range(COLS):
            x = CX - R + (c + 0.5) * cell
            y = CY - R + (r + 0.5) * row_h
            if (x - CX) ** 2 + (y - CY) ** 2 > (R - 6) ** 2:
                continue
            lum = gray.getpixel((c, r)) / 255
            ch = RAMP[min(len(RAMP) - 1, int(lum * len(RAMP)))]
            if ch == " ":
                continue
            groups[(r, pal.getpixel((c, r)))].append((x, ch))

    out = []
    for (r, ci), cells in sorted(groups.items()):
        rr, gg, bb = palette[ci * 3: ci * 3 + 3]
        # lighten so the characters stay readable over the dimmed photo
        rr, gg, bb = (int(v + (255 - v) * 0.45) for v in (rr, gg, bb))
        y = CY - R + (r + 0.5) * row_h + cell * 0.35
        xs = " ".join(f"{x:.1f}" for x, _ in cells)
        text = escape("".join(ch for _, ch in cells))
        out.append(f'<text x="{xs}" y="{y:.1f}" fill="rgb({rr},{gg},{bb})">{text}</text>')
    return f'<g font-family="{FONT}" font-size="{cell * 1.15:.1f}" font-weight="700" opacity="0.55">' + "".join(out) + "</g>"


def photo_data(img: Image.Image) -> str:
    side = min(img.size)
    left, top = (img.width - side) // 2, (img.height - side) // 2
    img = img.crop((left, top, left + side, top + side)).resize((2 * R, 2 * R), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=82)
    return base64.b64encode(buf.getvalue()).decode()


def ticks() -> str:
    arcs = []
    for start, length in ((-80, 50), (10, 70), (120, 40), (200, 60)):
        arcs.append(
            f'<circle cx="{CX}" cy="{CY}" r="{R + 22}" fill="none" stroke="#7c83c9" stroke-width="2" '
            f'stroke-dasharray="{length * 3.95:.0f} 2000" transform="rotate({start} {CX} {CY})" opacity="0.7"/>'
        )
    return "".join(arcs)


def build() -> str:
    img = load_avatar()
    photo = photo_data(img)
    overlay = ascii_overlay(img)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{FIRST} {LAST}, {escape(ROLE)}">
<defs>
  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
    <path d="M32 0H0V32" fill="none" stroke="#121a2b" stroke-width="1"/>
  </pattern>
  <pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="5" height="5" fill="#0a0f1a"/>
    <rect width="2" height="5" fill="#c9d1e3"/>
  </pattern>
  <clipPath id="disc"><circle cx="{CX}" cy="{CY}" r="{R}"/></clipPath>
  <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
    <stop offset="55%" stop-color="#0a0f1a" stop-opacity="0.15"/>
    <stop offset="100%" stop-color="#0a0f1a" stop-opacity="0.95"/>
  </radialGradient>
  <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#7dd3fc" stop-opacity="0"/>
    <stop offset="1" stop-color="#7dd3fc" stop-opacity="0.35"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="18" fill="#0a0f1a"/>
<rect width="{W}" height="{H}" rx="18" fill="url(#grid)"/>
<text x="40" y="52" fill="#5b6b8c" font-family="{FONT}" font-size="13" letter-spacing="4">{USERNAME}</text>
<text x="{W - 40}" y="52" fill="#5b6b8c" font-family="{FONT}" font-size="13" text-anchor="end">@{USERNAME.lower()}</text>

<text x="40" y="150" fill="#3b82c4" font-family="{FONT}" font-size="15" letter-spacing="6">HELLO, WORLD. I'M</text>
<g font-family="{FONT}" font-size="104" font-weight="800" fill="url(#hatch)" stroke="#e5e9f2" stroke-width="2.2">
  <text x="36" y="262">{FIRST}</text>
  <text x="36" y="372">{LAST}</text>
</g>
<text x="40" y="428" fill="#f1f5f9" font-family="{FONT}" font-size="20" font-weight="700">{escape(ROLE)}</text>
<text x="40" y="460" fill="#7d8fb3" font-family="{FONT}" font-size="15">{escape(TAGLINE)}<tspan fill="#7dd3fc">_<animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/></tspan></text>

<circle cx="{CX}" cy="{CY}" r="{R + 40}" fill="none" stroke="#1e2740" stroke-width="1"/>
<g>{ticks()}<animateTransform attributeName="transform" type="rotate" from="0 {CX} {CY}" to="360 {CX} {CY}" dur="40s" repeatCount="indefinite"/></g>
<g clip-path="url(#disc)">
  <image x="{CX - R}" y="{CY - R}" width="{2 * R}" height="{2 * R}" opacity="0.9" xlink:href="data:image/jpeg;base64,{photo}"/>
  <rect x="{CX - R}" y="{CY - R}" width="{2 * R}" height="{2 * R}" fill="#0a0f1a" opacity="0.25"/>
  {overlay}
  <circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#vignette)"/>
  <rect x="{CX - R}" y="{CY - R - 60}" width="{2 * R}" height="60" fill="url(#scan)">
    <animate attributeName="y" values="{CY - R - 60};{CY + R}" dur="4s" repeatCount="indefinite"/>
  </rect>
</g>
<circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="#2a3552" stroke-width="1.5"/>
<text x="{W - 40}" y="{H - 24}" fill="#5b6b8c" font-family="{FONT}" font-size="12" text-anchor="end">github.com/{USERNAME}</text>
</svg>
"""


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
