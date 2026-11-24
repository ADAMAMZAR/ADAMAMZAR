"""Generate assets/room.svg: a pixel-art desk facing a mountain window, its monitor streaming recent commits.

Usage: python scripts/generate_room.py
Reads public commits from the GitHub search API. Set GITHUB_TOKEN to raise the rate limit.
No third-party packages needed.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "ADAMAMZAR"
OUT = Path(__file__).resolve().parent.parent / "assets" / "room.svg"
SKIP_REPOS = {f"{USERNAME}/{USERNAME}"}  # profile repo commits are just README tweaks
MAX_COMMITS = 18

W, H = 1200, 600
FLOOR = 500
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

# monitor screen (inner area), terminal title bar and text metrics
SX, SY, SW, SH = 392, 150, 416, 248
BAR = 22
LH, FS, MAX_CHARS = 18, 12.5, 54
START = 7  # where in the log the stream starts (the screen is full from the first frame)
STEP = 0.9  # seconds between new lines


def fetch_commits() -> list[dict]:
    url = (
        "https://api.github.com/search/commits"
        f"?q=author:{USERNAME}&sort=author-date&order=desc&per_page=60"
    )
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-room"})
    if token := os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        items = json.load(resp)["items"]

    commits = []
    for item in items:
        repo = item["repository"]["full_name"]
        msg = item["commit"]["message"].splitlines()[0].strip()
        if repo in SKIP_REPOS or msg.lower().startswith("merge "):
            continue
        commits.append({"sha": item["sha"][:7], "repo": repo.split("/")[1], "msg": msg})
        if len(commits) == MAX_COMMITS:
            break
    return commits[::-1]  # oldest first, so the newest lands at the bottom last


def rect(x, y, w, h, fill, attrs="", inner=""):
    tag = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{attrs}'
    return f"{tag}>{inner}</rect>" if inner else f"{tag}/>"


def poly(points, fill, attrs=""):
    return f'<polygon points="{" ".join(f"{x},{y}" for x, y in points)}" fill="{fill}"{attrs}/>'


def clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def terminal(commits: list[dict]) -> str:
    lines = [f'<tspan fill="#7ee787">$</tspan> <tspan fill="#e6edf3">git log --oneline --author={USERNAME.lower()}</tspan>']
    for c in commits:
        head = clip(f'{c["repo"]}: {c["msg"]}', MAX_CHARS - len(c["sha"]) - 1)
        repo, _, msg = head.partition(": ")
        lines.append(
            f'<tspan fill="#e3b341">{c["sha"]}</tspan> <tspan fill="#79c0ff">{escape(repo)}:</tspan> '
            f'<tspan fill="#a5d6a7">{escape(msg)}</tspan>'
        )
    # Seamless loop: the log is laid out as an endless tape (row i shows lines[i % n]), so after one full
    # cycle of n steps the screen looks exactly like it did at the start and the restart is invisible.
    n = len(lines)
    bottom = SY + SH - 14  # baseline of the last visible row
    visible = (SH - BAR) // LH + 1
    texts = "".join(f'<text x="{SX + 12}" y="{bottom + i * LH}">{lines[i % n]}</text>'
                    for i in range(START - visible, START + n + 1))

    steps = list(range(START, START + n))
    key_times = ";".join(f"{i / n:.4f}" for i in range(n))
    values = ";".join(f"0 {-k * LH}" for k in steps)
    scroll = (f'<animateTransform attributeName="transform" type="translate" calcMode="discrete" '
              f'values="{values}" keyTimes="{key_times}" dur="{n * STEP:.1f}s" repeatCount="indefinite"/>')
    title = (rect(SX, SY, SW, BAR, "#1b2130") +
             "".join(f'<circle cx="{SX + 14 + i * 14}" cy="{SY + BAR // 2}" r="4" fill="{c}"/>'
                     for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840"))) +
             f'<text x="{SX + SW // 2}" y="{SY + 15}" text-anchor="middle" fill="#8b95a8">'
             f'{USERNAME.lower()}@github: ~</text>')
    return (f'<g font-family="{FONT}" font-size="{FS}" xml:space="preserve">{title}'
            f'<g clip-path="url(#screen)"><g transform="translate(0 {-steps[0] * LH})">{texts}{scroll}</g></g></g>')


def mountain_window() -> str:
    x, y, w, h = 48, 36, 1104, 300
    p = [rect(x - 10, y - 10, w + 20, h + 20, "#11131f"), rect(x, y, w, h, "url(#sky)"), aurora(x, y, w)]
    for sx, sy, d in ((90, 70, 2.3), (180, 120, 3.1), (300, 60, 2.7), (420, 110, 3.7), (560, 64, 2.1),
                      (700, 96, 3.3), (860, 58, 2.9), (980, 130, 3.5), (1100, 80, 2.5), (250, 160, 4.1), (1020, 60, 3.9)):
        p.append(rect(sx, sy, 3, 3, "#e6ecff", inner=f'<animate attributeName="opacity" values="1;0.2;1" '
                                                       f'dur="{d}s" repeatCount="indefinite"/>'))
    p += ['<circle cx="940" cy="104" r="26" fill="#f4efd9"/>', '<circle cx="932" cy="98" r="5" fill="#ddd6bc"/>',
          '<circle cx="950" cy="114" r="4" fill="#ddd6bc"/>']
    base = y + h
    far = [(x, base - 120), (140, 190), (230, 150), (330, 200), (450, 120), (560, 190), (650, 160),
           (780, 210), (900, 140), (1010, 200), (x + w, 160), (x + w, base), (x, base)]
    mid = [(x, base - 70), (120, 240), (260, 170), (380, 250), (520, 190), (640, 260), (760, 200),
           (880, 250), (1000, 180), (x + w, 240), (x + w, base), (x, base)]
    near = [(x, base - 30), (200, 290), (340, 300), (500, 270), (700, 304), (860, 280), (x + w, 300), (x + w, base), (x, base)]
    p += [poly(far, "#2b3666"), poly(mid, "#1d2549"), poly(near, "#141a33")]
    # snow caps on the mid range
    for px, py in ((260, 170), (520, 190), (760, 200), (1000, 180)):
        p.append(poly([(px, py), (px - 22, py + 22), (px - 8, py + 16), (px, py + 24), (px + 10, py + 16), (px + 24, py + 22)], "#cdd6ee"))
    # pine trees on the near ridge
    for tx in (90, 150, 400, 440, 610, 980, 1040, 1100):
        ty = 290
        p.append(poly([(tx, ty - 34), (tx - 12, ty), (tx + 12, ty)], "#0c1126"))
    p += [rect(x + w // 3 - 4, y, 8, h, "#11131f"), rect(x + 2 * w // 3 - 4, y, 8, h, "#11131f"),
          rect(x - 18, y + h + 10, w + 36, 10, "#4a3a2e"), sill_cat(y + h + 10)]
    return "".join(p)


def wave(x0, x1, y, amp, phase, n=6):
    """Smooth wave from x0 to x1 as quadratic segments; returns the list of path commands."""
    seg = (x1 - x0) / n
    cmds = [f"{x0} {y}"]
    for i in range(n):
        sign = 1 if (i + phase) % 2 == 0 else -1
        cmds.append(f"Q {x0 + (i + 0.5) * seg:.0f} {y + sign * amp} {x0 + (i + 1) * seg:.0f} {y}")
    return cmds


def ribbon(x0, x1, top, bottom, amp, phase):
    t = wave(x0, x1, top, amp, phase)
    b = wave(x0, x1, bottom, amp * 0.6, phase + 1)
    # walk the top edge left to right, then the bottom edge right to left
    back = [f"L {x1} {bottom}"] + [f"L {pt}" for pt in reversed([c.split(" ", 3)[-1] if c.startswith("Q") else c for c in b])][1:]
    return "M " + " ".join(t) + " " + " ".join(back) + " Z"


def aurora(x, y, w) -> str:
    """Northern lights: three soft ribbons that slowly ripple and pulse behind the mountains."""
    bands = (("#5cf2a6", 40, 230, 48, 0, 9, 0.95), ("#38d9e8", 80, 250, 38, 1, 12, 0.7), ("#a874ff", 20, 160, 30, 1, 15, 0.6))
    out = []
    for i, (color, top, bottom, amp, phase, dur, op) in enumerate(bands):
        a = ribbon(x - 40, x + w + 40, y + top, y + bottom, amp, phase)
        b = ribbon(x - 40, x + w + 40, y + top + 16, y + bottom - 14, amp, phase + 1)
        out.append(
            f'<path d="{a}" fill="url(#aur{i})" opacity="{op}">'
            f'<animate attributeName="d" values="{a};{b};{a}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="{op};{op * 0.55:.2f};{op}" dur="{dur * 0.7:.1f}s" repeatCount="indefinite"/></path>'
        )
    # vertical streaks turn the soft bands into hanging curtains of light
    return (f'<g clip-path="url(#win)" shape-rendering="auto"><g mask="url(#rays)" filter="url(#soft)">'
            f'{"".join(out)}</g></g>')


def sill_cat(sill: int) -> str:
    """Black cat lying along the window sill with its back to us, looking out; tail hangs over the edge."""
    c, rim = "#0b0c12", "#3d4775"  # moonlight rims the silhouette
    cx = 1000
    tail = f"M {cx + 44} {sill - 6} C {cx + 60} {sill + 6}, {cx + 50} {sill + 30}, {cx + 60} {sill + 46}"
    shape = (f'<ellipse cx="{cx}" cy="{sill - 17}" rx="52" ry="18"/>'
             f'<circle cx="{cx - 50}" cy="{sill - 30}" r="17"/>'
             f'<polygon points="{cx - 66},{sill - 36} {cx - 64},{sill - 58} {cx - 50},{sill - 44}"/>'
             f'<polygon points="{cx - 34},{sill - 36} {cx - 36},{sill - 58} {cx - 50},{sill - 44}"/>')
    sway = (f'<animateTransform attributeName="transform" type="rotate" values="0 {cx + 44} {sill};10 {cx + 44} {sill};'
            f'0 {cx + 44} {sill}" dur="4s" repeatCount="indefinite"/>')
    return (f'<g shape-rendering="auto">'
            f'<g fill="{rim}" transform="translate(0 -2)">{shape}</g><g fill="{c}">{shape}</g>'
            f'<g fill="none" stroke-linecap="round">{sway}<path d="{tail}" stroke="{rim}" stroke-width="10"/>'
            f'<path d="{tail}" stroke="{c}" stroke-width="7"/></g></g>')


HP_X, HP_Y = SX + SW + 14, SY - 14  # monitor's outer top-right corner


def headphones_back() -> str:
    """Ear cup hanging behind the monitor; only its top shows above the bezel. Drawn before the monitor."""
    return f'<rect x="{HP_X - 58}" y="{HP_Y - 14}" width="30" height="40" rx="8" fill="#1c1c22" shape-rendering="auto"/>'


def headphones() -> str:
    """Band arching over the corner and the front ear cup hanging down the monitor's right side."""
    x, y = HP_X, HP_Y
    band = f"M {x - 43} {y - 10} C {x - 40} {y - 46}, {x + 22} {y - 46}, {x + 18} {y + 22}"
    return "".join([
        f'<g shape-rendering="auto" fill="none" stroke-linecap="round">'
        f'<path d="{band}" stroke="#1c1c22" stroke-width="9"/><path d="{band}" stroke="#3a3a46" stroke-width="3"/></g>',
        f'<rect x="{x + 4}" y="{y + 18}" width="30" height="46" rx="9" fill="#1c1c22" shape-rendering="auto"/>',
        f'<rect x="{x + 2}" y="{y + 24}" width="10" height="34" rx="4" fill="#c0392b" shape-rendering="auto"/>',
        rect(x + 22, y + 30, 4, 22, "#3a3a46"),
    ])


ROSE = (  # 10x9 bloom: spiral petals from dark centre to light edges
    "...RRRR...",
    "..RLLLRR..",
    ".RLRDDLRR.",
    "RLRDLLDRLR",
    "RLRDDLDRLR",
    "RLLRRDRLLR",
    ".RLLLLLLR.",
    "..DRRRRD..",
    "G..DDDD..G",
)
LEAF = ("..GG", ".GLG", "GLG.", "GG..")
PALETTE = {"R": "#d7263d", "L": "#ff6b7d", "D": "#8e0e3c", "G": "#3fa35b"}


def pixels(x, y, rows, cell=4, flip=False) -> str:
    out = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row[::-1] if flip else row):
            if ch != ".":
                out.append(rect(x + c * cell, y + r * cell, cell, cell, PALETTE.get(ch, "#2f7d45")))
    return "".join(out)


def rose_plant() -> str:
    p = []
    # two stems with thorns and leaves, each topped by a bloom
    for stem_x, top, leaf_y, flip in ((150, 330, 372, True), (178, 362, 396, False)):
        p.append(rect(stem_x, top, 4, 428 - top, "#2f7d45"))
        p += [rect(stem_x - 3, top + 30, 3, 3, "#2f7d45"), rect(stem_x + 4, top + 52, 3, 3, "#2f7d45")]
        p.append(pixels(stem_x + (-16 if flip else 4), leaf_y, LEAF, flip=flip))
        p.append(pixels(stem_x - 18, top - 34, ROSE))
    p += [rect(124, 428, 80, 12, "#9a5230"), rect(132, 440, 64, 60, "#b5643b"), rect(140, 452, 48, 4, "#9a5230")]
    return "".join(p)


def fan(cx, cy, r, dur) -> str:
    blades = "".join(f'<rect x="{cx - 2}" y="{cy - r + 2}" width="4" height="{r - 2}" rx="2" fill="#5b6273" '
                     f'transform="rotate({a} {cx} {cy})"/>' for a in (0, 90, 180, 270))
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#0f1117"/><g>{blades}<animateTransform attributeName="transform" '
            f'type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="{dur}s" repeatCount="indefinite"/></g>'
            f'<circle cx="{cx}" cy="{cy}" r="3" fill="#7c5cff"/>')


def gpu_with_bubble() -> str:
    """A graphics card on the floor, insisting on what it is not for."""
    x, y = 212, 470  # card lies on the floor, fans facing us
    card = [rect(x, y, 84, 30, "#1c1f2b"), rect(x + 2, y + 2, 80, 26, "#2a2f3f"), rect(x - 6, y - 2, 6, 32, "#8a93a6"),
            rect(x + 4, y + 4, 76, 2, "#7c5cff", ' opacity="0.8"')]
    card.append(f'<g shape-rendering="auto">{fan(x + 24, y + 16, 11, 0.6)}{fan(x + 60, y + 16, 11, 0.5)}</g>')
    bx, by, bw, bh = 214, 372, 146, 44
    bubble = (f'<g shape-rendering="auto"><g><animateTransform attributeName="transform" type="translate" '
              f'values="0 0;0 -3;0 0" dur="2.6s" repeatCount="indefinite"/>'
              f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="8" fill="#f3e9d2" stroke="#2b2118" stroke-width="2"/>'
              f'<polygon points="{bx + 34},{by + bh - 1} {bx + 50},{by + bh - 1} {bx + 36},{by + bh + 16}" fill="#f3e9d2" '
              f'stroke="#2b2118" stroke-width="2" stroke-linejoin="round"/>'
              f'<rect x="{bx + 33}" y="{by + bh - 3}" width="18" height="5" fill="#f3e9d2"/>'
              f'<text x="{bx + bw / 2}" y="{by + 18}" text-anchor="middle" font-family="{FONT}" font-size="12" '
              f'font-weight="700" fill="#2b2118">Not for</text>'
              f'<text x="{bx + bw / 2}" y="{by + 34}" text-anchor="middle" font-family="{FONT}" font-size="12" '
              f'font-weight="700" fill="#c0392b">Chinese Honeypot</text></g></g>')
    return "".join(card) + bubble


def pc_tower() -> str:
    return "".join([
        rect(912, 372, 72, 128, "#1c1f2b"), rect(916, 376, 64, 120, "#252a3a"),
        rect(924, 388, 48, 4, "#3a4054"), rect(924, 396, 48, 4, "#3a4054"),
        '<circle cx="948" cy="444" r="18" fill="none" stroke="#7c5cff" stroke-width="3" shape-rendering="auto">'
        '<animate attributeName="stroke" values="#7c5cff;#00d1ff;#7ee787;#7c5cff" dur="6s" repeatCount="indefinite"/></circle>',
        rect(964, 380, 6, 4, "#7ee787"),
    ])


def scene(commits: list[dict]) -> str:
    p = [rect(0, 0, W, FLOOR, "#1a1d2e"), mountain_window()]
    p.append('<ellipse cx="600" cy="290" rx="330" ry="200" fill="url(#glow)"/>')

    # floor
    p += [rect(0, FLOOR - 8, W, 8, "#4a3a2e"), rect(0, FLOOR, W, H - FLOOR, "#33261d")]
    for i, fy in enumerate(range(FLOOR + 24, H, 24)):
        p.append(rect(0, fy, W, 3, "#281d16"))
        p += [rect(fx + (i % 2) * 90, fy - 21, 3, 21, "#281d16") for fx in range(140, W, 180)]

    p.append(rose_plant())

    # desk: top surface, front edge, legs
    p += [rect(296, 436, 608, 18, "#6e5038"), rect(296, 454, 608, 10, "#54392a"),
          rect(316, 464, 14, FLOOR - 464, "#45301f"), rect(870, 464, 14, FLOOR - 464, "#45301f")]

    # monitor
    p.append(headphones_back())
    p += [rect(SX - 14, SY - 14, SW + 28, SH + 28, "#2e3240"), rect(SX - 6, SY - 6, SW + 12, SH + 12, "#20232d"),
          rect(SX, SY, SW, SH, "#0b1020"), rect(588, SY + SH + 14, 24, 26, "#2e3240"), rect(548, 432, 104, 8, "#2e3240"),
          rect(SX + SW - 4, SY + SH + 4, 4, 4, "#7ee787")]
    p.append(terminal(commits))
    p.append(f'<rect x="{SX}" y="{SY}" width="{SW}" height="{SH}" fill="url(#scanlines)"/>')
    p.append(headphones())

    # desk mat with keyboard and mouse
    p += [rect(452, 440, 352, 12, "#1e2230"), rect(452, 450, 352, 2, "#7c5cff", ' opacity="0.6"'),
          rect(480, 441, 200, 8, "#3a4054"), rect(484, 442, 192, 2, "#5b6273")]
    p += [rect(486 + i * 12, 445, 8, 2, "#6b7388") for i in range(16)]
    p += [rect(728, 440, 20, 10, "#3a4054"), rect(736, 440, 4, 4, "#7c5cff"),
          rect(737, 434, 2, 6, "#3a4054")]

    p.append(pc_tower())
    p.append(gpu_with_bubble())
    return "".join(p)


def aurora_gradients() -> str:
    colors = ("#5cf2a6", "#38d9e8", "#a874ff")
    return "".join(
        f'<linearGradient id="aur{i}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c}" stop-opacity="0"/>'
        f'<stop offset="0.35" stop-color="{c}" stop-opacity="0.9"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></linearGradient>'
        for i, c in enumerate(colors))


def build(commits: list[dict]) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" shape-rendering="crispEdges" role="img" aria-label="Pixel-art desk by a mountain window; the monitor streams {USERNAME}'s latest commits">
<defs>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  <clipPath id="screen"><rect x="{SX}" y="{SY + BAR}" width="{SW}" height="{SH - BAR - 9}"/></clipPath>
  <clipPath id="win"><rect x="48" y="36" width="1104" height="300"/></clipPath>
  <filter id="soft" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="4"/></filter>
  {aurora_gradients()}
  <pattern id="streaks" width="14" height="10" patternUnits="userSpaceOnUse"><rect width="14" height="10" fill="#fff" opacity="0.55"/><rect x="2" width="5" height="10" fill="#fff"/><rect x="10" width="2" height="10" fill="#fff" opacity="0.8"/></pattern>
  <mask id="rays"><rect x="0" y="0" width="{W}" height="{H}" fill="url(#streaks)"/></mask>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a1030"/><stop offset="1" stop-color="#2a2f5e"/></linearGradient>
  <radialGradient id="glow"><stop offset="0" stop-color="#7ee787" stop-opacity="0.06"/><stop offset="1" stop-color="#7ee787" stop-opacity="0"/></radialGradient>
  <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity="0.25"/></pattern>
</defs>
<g clip-path="url(#card)">{scene(commits)}</g>
</svg>
"""


if __name__ == "__main__":
    try:
        commits = fetch_commits()
    except Exception as exc:  # keep the existing SVG rather than publish an empty screen
        sys.exit(f"could not fetch commits: {exc}")
    OUT.write_text(build(commits), encoding="utf-8")
    print(f"wrote {OUT} with {len(commits)} commits")
