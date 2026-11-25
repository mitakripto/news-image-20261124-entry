#!/usr/bin/env python3
"""Draw the 24 November 2026 front page (1024x1024) for the make.fun
news-image-20261124 bounty.

Same pipeline as the 17/18/19/22 Nov entries: deterministic Pillow
drawing, fixed fonts, fixed layout, no randomness, no network. 60
stories across 7 regions, colour-coded by continent: a continent bar
with counts under the masthead, region-coloured number badges on every
story, and matching map pins. Status tags on every drawn story
(CONFIRMED / REPORTED / CLAIM, with a legend) and a "THE DAY IN UTC"
timeline strip under the stats.

Run:  python3 draw.py   -> writes entry.png next to this file.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024

PAPER = (240, 233, 214)
INK = (18, 28, 30)
GRAY = (74, 82, 80)
RED = (158, 43, 37)
TEAL_DARK = (14, 42, 51)
TEAL = (31, 111, 107)
GOLD = (201, 162, 39)
GOLD_LT = (226, 190, 96)
CREAM = (247, 242, 230)
SKY = (213, 228, 226)
WATER = (140, 178, 176)
CARD_BG = (233, 226, 200)
MAP_BG = (216, 230, 224)
MAP_DOT = (96, 128, 124)

# Continent colours (muted deco): badges, kickers, map pins, bar.
ASIA = TEAL
EUROPE = (70, 100, 140)
MIDDLE_EAST = (178, 102, 32)
N_AMERICA = RED
S_AMERICA = (90, 130, 80)
AFRICA = (146, 96, 48)
OCEANIA = (110, 90, 130)

# Status-tag colours: how sure the page is of each drawn story.
TAG_CONFIRMED = TEAL
TAG_REPORTED = MIDDLE_EAST
TAG_CLAIM = RED

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIFB = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANSB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def SERIF_F(n):
    return ImageFont.truetype(SERIF, n)


def SERIF_B(n):
    return ImageFont.truetype(SERIFB, n)


def SANS_F(n):
    return ImageFont.truetype(SANS, n)


def SANS_B(n):
    return ImageFont.truetype(SANSB, n)


def wrap(draw, s, font, max_w):
    """Greedy word wrap; asserts no single word exceeds the width."""
    words = s.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            assert draw.textlength(word, font=font) <= max_w, \
                f"word too wide: {word!r}"
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text(draw, xy, s, font, fill=INK, anchor="la"):
    draw.text(xy, s, font=font, fill=fill, anchor=anchor)


def diamond(draw, x, y, r, color):
    draw.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)],
                 fill=color)


def badge(draw, x, y, n, size, color=INK):
    """Black (or continent-coloured) stamp-square with a cream number:
    the Orwell numbering device, now colour-coded by continent."""
    draw.rectangle([x, y, x + size, y + size], fill=color)
    draw.rectangle([x + 1, y + 1, x + size - 1, y + size - 1],
                   outline=GOLD_LT, width=1)
    fnt = SANS_B(11 if size >= 20 else 8)
    text(draw, (x + size / 2, y + size / 2), str(n), fnt, CREAM,
         anchor="mm")


def tag_chip(draw, x_right, y_center, label, color, fsize=8):
    """Small solid status chip, right-aligned: CONFIRMED / REPORTED /
    CLAIM. Returns the chip's left edge so callers can keep clear."""
    fnt = SANS_B(fsize)
    tw = draw.textlength(label, font=fnt)
    w, h = tw + 10, 14
    x0 = x_right - w
    y0 = y_center - h // 2
    draw.rectangle([x0, y0, x_right, y0 + h], fill=color)
    text(draw, (x0 + w / 2, y_center), label, fnt, CREAM, anchor="mm")
    return x0


def kicker(draw, x, y, n, label, color, size=20, max_w=None, fsize=None):
    badge(draw, x, y, n, size, color)
    fnt = SANS_B(fsize if fsize else (12 if size >= 20 else 9))
    if max_w is not None:
        assert draw.textlength(label, font=fnt) <= max_w - size - 6, \
            f"kicker overflows: {label!r}"
    text(draw, (x + size + 6, y + size // 2), label, fnt, color, anchor="lm")


def draw_eye(draw, x, y, w=34, h=20):
    """One small watching eye for the masthead."""
    draw.ellipse([x, y, x + w, y + h], outline=GOLD, width=2, fill=CREAM)
    cx, cy = x + w // 2, y + h // 2
    draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], outline=RED, width=2)
    draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=INK)


def caption_bar(draw, x0, y1, x1, label):
    draw.rectangle([x0, y1 - 14, x1, y1], fill=INK)
    text(draw, ((x0 + x1) // 2, y1 - 7), label, SANS_B(8), GOLD_LT,
         anchor="mm")


def draw_seats(draw, x0, y0, x1, y1):
    """The House as a semicircle of seats: 258 blue dots of 435, the
    Democrats' majority rendered as a parliament chart. Art area is
    72px tall; the caption bar takes the bottom 14."""
    bg = (30, 58, 74)
    draw.rectangle([x0, y0, x1, y1], fill=bg)
    cx = (x0 + x1) // 2
    base = y1 - 14
    blue = (88, 140, 210)
    red = (198, 84, 72)
    # Three arcs of dots; in each arc the first 59.3% (258 of 435
    # seats) are blue, so every arc reads as the same split.
    for r in (54, 46, 38):
        angles = list(range(180, 361, 5))
        n_blue = int(len(angles) * 258 / 435)
        for i, a in enumerate(angles):
            rad = math.radians(a)
            dx = cx + r * math.cos(rad)
            dy = base + r * math.sin(rad)
            col = blue if i < n_blue else red
            draw.ellipse([dx - 2.5, dy - 2.5, dx + 2.5, dy + 2.5],
                         fill=col)
    # The figure in the middle of the arc, on a clean patch.
    draw.rectangle([cx - 34, y0 + 30, cx + 34, y0 + 60], fill=bg)
    text(draw, (cx, y0 + 45), "258", SERIF_B(24), GOLD_LT, anchor="mm")
    diamond(draw, x0 + 28, y0 + 36, 4, GOLD)
    diamond(draw, x1 - 28, y0 + 36, 4, GOLD)
    caption_bar(draw, x0, y1, x1, "WASHINGTON  \u00b7  258 SEATS")


def draw_tanker(draw, x0, y0, x1, y1):
    """A supertanker burning east of Hormuz: dusk sky, fire burst,
    mine dots in dark water. Art area is 72px tall; the caption bar
    takes the bottom 14."""
    draw.rectangle([x0, y0, x1, y1 - 14], fill=(224, 178, 120))
    draw.rectangle([x0, y1 - 26, x1, y1 - 14], fill=(16, 44, 54))
    for wx in range(10, (x1 - x0) - 10, 30):
        draw.line([x0 + wx, y1 - 20, x0 + wx + 16, y1 - 20],
                  fill=WATER, width=2)
    # Hull and superstructure, silhouetted; base sits on the caption
    hx0, hx1 = x0 + 30, x1 - 30
    hy = y1 - 14
    draw.polygon([(hx0, hy - 14), (hx1, hy - 14), (hx1 - 10, hy),
                  (hx0 + 10, hy)], fill=INK)
    draw.rectangle([hx1 - 52, hy - 30, hx1 - 28, hy - 14], fill=INK)
    draw.line([hx1 - 40, hy - 37, hx1 - 40, hy - 30], fill=INK, width=2)
    # Fire burst above the bow, touching the hull
    fx, fy = hx0 + 34, y0 + 26
    for r, col in ((12, (222, 120, 40)), (8, (240, 180, 60)),
                   (5, (252, 236, 180))):
        draw.ellipse([fx - r, fy - r, fx + r, fy + r], fill=col)
    for a in (200, 250, 290, 340):
        rad = math.radians(a)
        ex = fx + 17 * math.cos(rad)
        ey = fy + 11 * math.sin(rad)
        draw.line([fx, fy, ex, ey], fill=(222, 120, 40), width=2)
    # Smoke trailing up and to the left of the fire
    for sx, sy, r in ((fx - 14, fy - 12, 5), (fx - 21, fy - 18, 6)):
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(90, 90, 88))
    # Two naval mines in the water strip
    for mx in (x0 + 18, x1 - 18):
        my = y1 - 20
        draw.ellipse([mx - 3, my - 3, mx + 3, my + 3], fill=INK)
        for a in (45, 135, 225, 315):
            rad = math.radians(a)
            draw.line([mx, my, mx + 5 * math.cos(rad),
                       my + 5 * math.sin(rad)], fill=INK, width=1)
    caption_bar(draw, x0, y1, x1, "HORMUZ  \u00b7  4 TANKERS")


def draw_cop31(draw, x0, y0, x1, y1):
    """Antalya plenary: flags over a red NO DEAL stamp, delegates at
    the long table below. Art area is 72px tall; the caption bar
    takes the bottom 14."""
    draw.rectangle([x0, y0, x1, y1], fill=TEAL_DARK)
    # Row of small flags
    fw, gap = 26, 10
    total = 7 * fw + 6 * gap
    fx = x0 + ((x1 - x0) - total) // 2
    flag_cols = [(60, 59, 110), (222, 41, 16), (0, 57, 166),
                 (0, 122, 60), (255, 205, 0), (178, 34, 52),
                 (255, 255, 255)]
    for i, col in enumerate(flag_cols):
        bx = fx + i * (fw + gap)
        draw.rectangle([bx, y0 + 5, bx + fw, y0 + 17], fill=col)
    # Long table with delegates, kept clear of the stamp's x-range
    sx0, sx1 = x0 + 78, x1 - 78
    draw.rectangle([x0 + 16, y1 - 24, x1 - 16, y1 - 14], fill=(8, 28, 36))
    for px in range(x0 + 28, x1 - 28, 30):
        if px + 10 < sx0 - 6 or px > sx1 + 6:
            draw.ellipse([px, y1 - 32, px + 10, y1 - 24], fill=GOLD_LT)
    # Red NO DEAL stamp
    sy0, sy1 = y0 + 22, y1 - 26
    draw.rectangle([sx0, sy0, sx1, sy1], outline=RED, width=3)
    draw.rectangle([sx0 + 3, sy0 + 3, sx1 - 3, sy1 - 3], outline=RED,
                   width=1)
    text(draw, ((sx0 + sx1) // 2, (sy0 + sy1) // 2), "NO DEAL",
         SANS_B(16), (232, 90, 80), anchor="mm")
    caption_bar(draw, x0, y1, x1, "ANTALYA  \u00b7  COP31")


def draw_huawei(draw, x0, y0, x1, y1):
    """US courtroom: scales of justice on navy, verdict 10/12."""
    draw.rectangle([x0, y0, x1, y1], fill=(20, 30, 60))
    cx = (x0 + x1) // 2 - 40
    cy = y0 + 36
    draw.line([cx, y0 + 8, cx, y0 + 58], fill=GOLD_LT, width=3)
    draw.line([cx - 34, y0 + 14, cx + 34, y0 + 14], fill=GOLD_LT, width=3)
    for px in (cx - 34, cx + 34):
        draw.line([px, y0 + 14, px - 9, y0 + 30], fill=GOLD_LT, width=2)
        draw.line([px, y0 + 14, px + 9, y0 + 30], fill=GOLD_LT, width=2)
        draw.arc([px - 9, y0 + 24, px + 9, y0 + 36], 0, 180,
                 fill=GOLD_LT, width=2)
    draw.ellipse([cx - 4, y0 + 4, cx + 4, y0 + 12], fill=GOLD)
    text(draw, (x1 - 10, (y0 + y1) // 2), "10/12", SERIF_B(22), CREAM,
         anchor="rm")
    caption_bar(draw, x0, y1, x1, "WASHINGTON  \u00b7  GUILTY")


def draw_ships(draw, x0, y0, x1, y1):
    """Russian ships struck in the Gulf of Finland and off Libya:
    dark sea, a cargo ship, a drone above, fire at the bow."""
    draw.rectangle([x0, y0, x1, y1 - 14], fill=(30, 58, 74))
    draw.rectangle([x0, y1 - 26, x1, y1 - 14], fill=(16, 44, 54))
    for wx in range(10, (x1 - x0) - 10, 30):
        draw.line([x0 + wx, y1 - 20, x0 + wx + 16, y1 - 20],
                  fill=WATER, width=2)
    hx0, hx1 = x0 + 30, x1 - 30
    hy = y1 - 14
    draw.polygon([(hx0, hy - 14), (hx1, hy - 14), (hx1 - 10, hy),
                  (hx0 + 10, hy)], fill=INK)
    draw.rectangle([hx1 - 52, hy - 30, hx1 - 28, hy - 14], fill=INK)
    fx, fy = hx0 + 34, y0 + 26
    for r, col in ((12, (222, 120, 40)), (8, (240, 180, 60)),
                   (5, (252, 236, 180))):
        draw.ellipse([fx - r, fy - r, fx + r, fy + r], fill=col)
    icon_drone(draw, x1 - 70, y0 + 6, 14, (240, 180, 60))
    caption_bar(draw, x0, y1, x1, "GULF OF FINLAND  \u00b7  LIBYA")


# --- small icons for the cards (30x30 glyphs) ---

def icon_scales(draw, x, y, s, color):
    cx = x + s // 2
    draw.line([cx, y + 4, cx, y + s - 4], fill=color, width=3)
    draw.line([cx - 11, y + 7, cx + 11, y + 7], fill=color, width=3)
    for px in (cx - 11, cx + 11):
        draw.line([px, y + 7, px - 5, y + 16], fill=color, width=2)
        draw.line([px, y + 7, px + 5, y + 16], fill=color, width=2)
        draw.arc([px - 5, y + 14, px + 5, y + 24], 0, 180, fill=color,
                 width=2)
    draw.line([cx - 8, y + s - 4, cx + 8, y + s - 4], fill=color, width=3)


def icon_missile(draw, x, y, s, color):
    draw.polygon([(x + 20, y + 4), (x + 26, y + 10), (x + 18, y + 20),
                  (x + 12, y + 14)], fill=color)
    draw.line([x + 12, y + 14, x + 6, y + 24], fill=color, width=3)
    draw.line([x + 6, y + 24, x + 4, y + 28], fill=RED, width=3)
    draw.line([x + 18, y + 20, x + 24, y + 24], fill=color, width=2)
    draw.line([x + 18, y + 20, x + 14, y + 26], fill=color, width=2)


def icon_pencil(draw, x, y, s, color):
    draw.polygon([(x + 8, y + 20), (x + 20, y + 8), (x + 24, y + 12),
                  (x + 12, y + 24)], fill=color)
    draw.polygon([(x + 8, y + 20), (x + 5, y + 25), (x + 12, y + 24)],
                 fill=RED)
    draw.line([x + 5, y + 25, x + 25, y + 25], fill=color, width=2)


def icon_tower(draw, x, y, s, color):
    cx = x + s // 2
    draw.rectangle([cx - 7, y + 8, cx + 7, y + s - 4], fill=color)
    draw.polygon([(cx - 7, y + 8), (cx, y + 2), (cx + 7, y + 8)], fill=color)
    for wy in range(y + 12, y + s - 6, 6):
        draw.rectangle([cx - 4, wy, cx - 1, wy + 2], fill=GOLD_LT)
        draw.rectangle([cx + 1, wy, cx + 4, wy + 2], fill=GOLD_LT)


def icon_ballot(draw, x, y, s, color):
    draw.rectangle([x + 5, y + 12, x + 25, y + 26], outline=color, width=2)
    draw.line([x + 11, y + 12, x + 19, y + 12], fill=color, width=2)
    draw.polygon([(x + 9, y + 5), (x + 15, y + 3), (x + 21, y + 5),
                  (x + 19, y + 12), (x + 11, y + 12)], fill=CARD_BG,
                 outline=color)
    draw.line([x + 9, y + 21, x + 13, y + 24], fill=RED, width=2)
    draw.line([x + 13, y + 24, x + 21, y + 15], fill=RED, width=2)


def icon_drone(draw, x, y, s, color):
    cx, cy = x + s // 2, y + s // 2
    draw.rectangle([cx - 5, cy - 4, cx + 5, cy + 4], fill=color)
    for dx, dy in ((-9, -8), (9, -8), (-9, 8), (9, 8)):
        draw.line([cx, cy, cx + dx, cy + dy], fill=color, width=2)
        draw.ellipse([cx + dx - 4, cy + dy - 2, cx + dx + 4, cy + dy + 2],
                     outline=color, width=2)
    draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=RED)


def icon_soccer(draw, x, y, s, color):
    cx, cy = x + s // 2, y + s // 2
    draw.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], outline=color,
                 width=2)
    draw.polygon([(cx, cy - 5), (cx + 5, cy - 2), (cx + 3, cy + 4),
                  (cx - 3, cy + 4), (cx - 5, cy - 2)], fill=color)
    for a in (90, 162, 234, 306, 18):
        rad = math.radians(a)
        draw.line([cx + 5 * math.cos(rad), cy + 5 * math.sin(rad),
                   cx + 10 * math.cos(rad), cy + 10 * math.sin(rad)],
                  fill=color, width=1)


def icon_tennis(draw, x, y, s, color):
    cx, cy = x + s // 2, y + s // 2
    draw.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], outline=color,
                 width=2)
    draw.arc([cx - 16, cy - 8, cx + 2, cy + 8], 270, 90, fill=color,
             width=2)
    draw.arc([cx - 2, cy - 8, cx + 16, cy + 8], 90, 270, fill=color,
             width=2)


def icon_plane(draw, x, y, s, color):
    draw.polygon([(x + 4, y + 18), (x + 24, y + 8), (x + 26, y + 11),
                  (x + 12, y + 20), (x + 10, y + 24), (x + 7, y + 22)],
                 fill=color)
    draw.polygon([(x + 14, y + 15), (x + 22, y + 17), (x + 22, y + 20),
                  (x + 13, y + 18)], fill=color)
    draw.line([x + 4, y + 26, x + 26, y + 26], fill=RED, width=2)
    draw.line([x + 8, y + 26, x + 6, y + 22], fill=RED, width=2)
    draw.line([x + 22, y + 26, x + 24, y + 22], fill=RED, width=2)


def icon_flame(draw, x, y, s, color):
    cx = x + s // 2
    draw.polygon([(cx, y + 3), (cx + 9, y + 16), (cx + 6, y + 24),
                  (cx - 6, y + 24), (cx - 9, y + 16)], fill=(222, 120, 40))
    draw.polygon([(cx, y + 10), (cx + 5, y + 18), (cx + 3, y + 23),
                  (cx - 3, y + 23), (cx - 5, y + 18)], fill=GOLD)
    draw.line([cx - 10, y + 26, cx + 10, y + 26], fill=color, width=2)


def _in_poly(lon, lat, poly):
    """Ray-casting point-in-polygon test for a lon/lat point."""
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            xin = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            if lon < xin:
                inside = not inside
    return inside


# Simplified continent outlines (lon/lat rings) for a realistic
# dotted map: real coastlines, not blobs. Drawn from geography.
POLYS = [
    # North America, incl. Central America
    [(-168, 66), (-165, 60), (-158, 58), (-152, 60), (-140, 60),
     (-135, 57), (-130, 54), (-125, 49), (-124, 42), (-120, 34),
     (-114, 29), (-110, 23), (-105, 20), (-97, 16), (-94, 17),
     (-90, 14), (-87, 13), (-83, 9), (-79, 9), (-81, 13),
     (-83, 16), (-87, 21), (-90, 21), (-91, 19), (-97, 26),
     (-93, 30), (-89, 30), (-84, 30), (-81, 25), (-80, 32),
     (-76, 35), (-74, 40), (-70, 42), (-68, 44), (-65, 45),
     (-60, 47), (-65, 50), (-60, 52), (-64, 58), (-68, 58),
     (-72, 62), (-78, 62), (-85, 66), (-92, 66), (-95, 69),
     (-110, 68), (-125, 70), (-140, 70), (-155, 71), (-165, 68)],
    # Greenland
    [(-58, 64), (-52, 60), (-43, 60), (-40, 65), (-32, 68),
     (-22, 70), (-20, 76), (-30, 80), (-45, 80), (-58, 76),
     (-62, 70)],
    # South America
    [(-79, 9), (-75, 11), (-72, 12), (-64, 10), (-60, 8),
     (-52, 5), (-50, 0), (-44, -3), (-35, -8), (-35, -15),
     (-39, -22), (-48, -28), (-52, -32), (-58, -38), (-62, -41),
     (-65, -45), (-68, -50), (-69, -54), (-72, -54), (-73, -45),
     (-73, -37), (-71, -30), (-70, -20), (-75, -15), (-77, -12),
     (-81, -6), (-81, 0), (-80, 5)],
    # Europe, with Italy's boot suggested
    [(-10, 36), (-9, 43), (-2, 48), (-4, 49), (0, 50), (3, 53),
     (5, 58), (5, 62), (10, 64), (12, 66), (18, 69), (25, 71),
     (30, 70), (32, 66), (28, 61), (24, 58), (21, 55), (24, 52),
     (28, 50), (30, 46), (29, 44), (23, 40), (22, 37), (26, 38),
     (28, 41), (30, 42), (28, 45), (24, 46), (19, 46), (18, 42),
     (16, 40), (18, 39), (15, 38), (16, 41), (14, 42), (10, 44),
     (8, 44), (3, 42), (0, 39), (-2, 37), (-6, 36), (-9, 37)],
    # Britain
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (0, 53), (1, 51)],
    # Africa
    [(-6, 35), (-10, 31), (-15, 25), (-17, 15), (-16, 12),
     (-13, 8), (-8, 5), (-4, 5), (2, 6), (6, 4), (9, 4),
     (9, -1), (12, -6), (13, -12), (12, -18), (14, -22),
     (16, -28), (18, -34), (20, -35), (26, -34), (28, -32),
     (32, -28), (35, -23), (36, -18), (35, -12), (40, -10),
     (40, -5), (42, -2), (46, 0), (51, 2), (51, 10), (44, 11),
     (40, 15), (38, 18), (35, 22), (32, 28), (30, 31), (25, 32),
     (20, 32), (15, 32), (10, 34), (5, 35), (0, 36)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24),
     (45, -25), (44, -20)],
    # Asia: Levant around to Chukotka, back along the Arctic coast
    [(30, 36), (35, 36), (36, 33), (42, 30), (48, 30), (50, 26),
     (54, 26), (57, 25), (61, 25), (66, 25), (70, 23), (72, 20),
     (75, 15), (77, 8), (80, 10), (80, 16), (84, 19), (88, 22),
     (91, 22), (92, 16), (94, 17), (97, 16), (98, 10), (100, 8),
     (103, 1), (104, 8), (105, 10), (109, 13), (109, 15),
     (106, 20), (108, 22), (110, 21), (114, 22), (118, 25),
     (120, 28), (122, 32), (120, 35), (122, 38), (126, 40),
     (130, 42), (135, 44), (140, 48), (142, 54), (140, 60),
     (142, 63), (145, 68), (150, 70), (158, 70), (165, 68),
     (170, 67), (178, 65), (178, 68), (170, 70), (160, 70),
     (150, 72), (140, 72), (130, 72), (120, 73), (110, 74),
     (100, 77), (90, 75), (80, 73), (72, 72), (68, 69),
     (60, 69), (55, 68), (50, 68), (45, 67), (40, 66),
     (35, 65), (32, 62), (30, 58), (28, 55), (30, 50),
     (32, 46), (30, 42), (35, 42), (38, 40), (40, 38),
     (35, 38), (32, 36)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (138, 35), (140, 36),
     (141, 39), (141, 42), (143, 43), (145, 44), (142, 45),
     (140, 40), (138, 37), (135, 34), (132, 33)],
    # Philippines
    [(117, 16), (120, 18), (122, 18), (122, 14), (124, 12),
     (126, 10), (126, 6), (124, 6), (122, 8), (120, 10),
     (119, 12), (118, 14)],
    # Sumatra, Java, Borneo, New Guinea
    [(95, 5), (100, 0), (105, -5), (106, -6), (103, -4), (99, 2)],
    [(105, -6), (110, -7), (114, -8), (114, -9), (108, -8)],
    [(109, 1), (113, 4), (118, 2), (119, -2), (117, -4), (112, -3)],
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -10),
     (147, -9), (142, -8), (136, -6), (131, -3)],
    # Australia
    [(114, -22), (114, -28), (115, -33), (118, -35), (124, -33),
     (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (151, -24),
     (146, -19), (142, -15), (142, -11), (140, -17), (136, -15),
     (135, -12), (132, -11), (130, -13), (126, -14), (122, -17),
     (118, -20)],
    # New Zealand
    [(167, -45), (170, -42), (173, -39), (175, -38), (178, -38),
     (175, -41), (172, -44)],
]


def draw_map(draw, x0, y0, x1, y1, spots):
    draw.rectangle([x0, y0, x1, y1], fill=MAP_BG)
    draw.rectangle([x0, y0, x1, y1], outline=GOLD, width=2)
    # The panel is nearly square but the world is wide: stretching the
    # map to fill the panel pulled every continent tall. Draw it at the
    # reference front page's dotted-region ratio, 1.71:1, letterboxed
    # and centred vertically in the panel instead.
    map_w = x1 - x0
    map_h = map_w / 1.71
    mx0, mx1 = x0, x1
    my0 = y0 + (y1 - y0 - map_h) / 2
    my1 = my0 + map_h

    def to_xy(lon, lat):
        return (mx0 + (lon + 180) / 360 * (mx1 - mx0),
                my0 + (75 - lat) / 135 * (my1 - my0))

    step = 5
    yy = my0 + 3
    while yy < my1 - 2:
        xx = mx0 + 3
        while xx < mx1 - 2:
            lon = (xx - mx0) / (mx1 - mx0) * 360 - 180
            lat = 75 - (yy - my0) / (my1 - my0) * 135
            for poly in POLYS:
                if _in_poly(lon, lat, poly):
                    draw.ellipse([xx - 1.3, yy - 1.3, xx + 1.3, yy + 1.3],
                                 fill=MAP_DOT)
                    break
            xx += step
        yy += step
    for n, lon, lat, dx, dy, color in spots:
        px, py = to_xy(lon, lat)
        px += dx
        py += dy
        draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=color,
                     outline=CREAM, width=1)
        text(draw, (px, py), str(n), SANS_B(8), CREAM, anchor="mm")
    text(draw, ((x0 + x1) // 2, y1 - 10),
         "Dots mark stories 1\u201313; pin colour = continent.", SANS_F(9),
         GRAY, anchor="mm")


def lead(draw, x, y, w, n, kick, color, headline, sub, art, tag, tag_color):
    art(draw, x, y, x + w, y + 72)
    draw.rectangle([x, y, x + w, y + 72], outline=GOLD, width=1)
    chip_left = tag_chip(draw, x + w, y + 90, tag, tag_color)
    kicker(draw, x, y + 80, n, kick, color, max_w=chip_left - x - 4)
    lines = wrap(draw, headline, SERIF_B(20), w)
    assert len(lines) <= 3, f"lead headline overflows: {headline!r}"
    yy = y + 106
    for line in lines:
        text(draw, (x, yy), line, SERIF_B(20))
        yy += 24
    slines = wrap(draw, sub, SANS_F(12.5), w)
    assert len(slines) <= 3, f"lead sub overflows: {sub!r}"
    for line in slines:
        text(draw, (x, yy + 3), line, SANS_F(12.5), GRAY)
        yy += 16


# --- Card illustrations: one small scene per card, with the story's
# number or verdict set large, the way the top entries do it. Each
# fills a 156x44 strip. ---

def art_ballot(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=TEAL)
    draw.rectangle([x0 + 12, y0 + 14, x0 + 46, y1 - 8], fill=CREAM)
    draw.line([x0 + 20, y0 + 14, x0 + 38, y0 + 14], fill=INK, width=2)
    draw.line([x0 + 22, y0 + 26, x0 + 28, y0 + 32], fill=RED, width=3)
    draw.line([x0 + 28, y0 + 32, x0 + 40, y0 + 18], fill=RED, width=3)
    text(draw, (x1 - 8, (y0 + y1) // 2), "98.79%", SERIF_B(17), GOLD_LT,
         anchor="rm")


def art_corvette(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(16, 44, 54))
    draw.polygon([(x0 + 10, y1 - 16), (x0 + 66, y1 - 16), (x0 + 60, y1 - 8),
                  (x0 + 16, y1 - 8)], fill=INK)
    draw.rectangle([x0 + 46, y1 - 26, x0 + 58, y1 - 16], fill=INK)
    icon_drone(draw, x0 + 74, y0 + 6, 14, (240, 180, 60))
    text(draw, (x1 - 8, (y0 + y1) // 2), "HIT", SANS_B(13), (232, 90, 80),
         anchor="rm")


def art_drones(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(20, 30, 60))
    for sx, sy in ((14, 8), (34, 14), (52, 6), (66, 18), (24, 30)):
        draw.ellipse([x0 + sx, y0 + sy, x0 + sx + 2, y0 + sy + 2],
                     fill=CREAM)
    icon_drone(draw, x0 + 10, y0 + 8, 14, CREAM)
    icon_drone(draw, x0 + 34, y0 + 18, 14, CREAM)
    icon_drone(draw, x0 + 56, y0 + 6, 14, (240, 180, 60))
    text(draw, (x1 - 8, (y0 + y1) // 2), "186", SERIF_B(20), CREAM,
         anchor="rm")


def art_exam(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(60, 60, 90))
    draw.rectangle([x0 + 12, y0 + 8, x0 + 40, y1 - 8], fill=CREAM)
    for ly in (14, 20, 26):
        draw.line([x0 + 16, y0 + ly, x0 + 36, y0 + ly], fill=GRAY, width=1)
    icon_pencil(draw, x0 + 44, y0 + 10, 22, GOLD)
    draw.ellipse([x1 - 36, y0 + 8, x1 - 10, y0 + 34], outline=RED, width=3)
    draw.line([x1 - 32, y0 + 30, x1 - 14, y0 + 12], fill=RED, width=3)
    text(draw, (x1 - 23, y0 + 21), "AI", SANS_B(10), CREAM, anchor="mm")


def art_soccer(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(20, 90, 50))
    icon_soccer(draw, x0 + 10, y0 + 7, 30, CREAM)
    text(draw, (x1 - 8, (y0 + y1) // 2), "4–0", SERIF_B(20), CREAM,
         anchor="rm")


def art_tennis(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(40, 80, 140))
    icon_tennis(draw, x0 + 10, y0 + 7, 30, (210, 230, 90))
    text(draw, (x1 - 8, y0 + 12), "6–2", SANS_B(12), CREAM, anchor="ra")
    text(draw, (x1 - 8, y0 + 26), "7–6", SANS_B(12), CREAM, anchor="ra")


def art_plane(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(140, 180, 210))
    icon_plane(draw, x0 + 8, y0 + 8, 28, INK)
    text(draw, (x1 - 8, (y0 + y1) // 2), "1,600+", SERIF_B(15), INK,
         anchor="rm")


def art_sudan(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(200, 170, 120))
    draw.rectangle([x0 + 12, y0 + 16, x0 + 34, y1 - 8], fill=(120, 90, 60))
    draw.rectangle([x0 + 38, y0 + 22, x0 + 54, y1 - 8], fill=(120, 90, 60))
    icon_drone(draw, x0 + 56, y0 + 6, 14, INK)
    text(draw, (x1 - 8, (y0 + y1) // 2), "4 DEAD", SANS_B(11), RED,
         anchor="rm")


def art_fire(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(40, 30, 30))
    icon_flame(draw, x0 + 12, y0 + 6, 32, (240, 140, 40))
    text(draw, (x1 - 8, (y0 + y1) // 2), "3 DEAD", SANS_B(11), GOLD_LT,
         anchor="rm")


def art_ice(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(90, 110, 130))
    icon_plane(draw, x0 + 8, y0 + 8, 28, CREAM)
    text(draw, (x1 - 8, (y0 + y1) // 2), "2 HELD", SANS_B(12), CREAM,
         anchor="rm")


def art_cricket(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(30, 100, 60))
    draw.polygon([(x0 + 16, y0 + 8), (x0 + 24, y0 + 8), (x0 + 30, y1 - 10),
                  (x0 + 22, y1 - 10)], fill=(220, 190, 140))
    draw.ellipse([x0 + 38, y0 + 12, x0 + 50, y0 + 24], fill=(200, 60, 50))
    text(draw, (x1 - 8, (y0 + y1) // 2), "720/9", SERIF_B(18), CREAM,
         anchor="rm")


def art_quake(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(120, 90, 60))
    draw.line([x0 + 8, y1 - 14, x0 + 70, y1 - 14], fill=INK, width=3)
    draw.line([x0 + 30, y1 - 14, x0 + 36, y1 - 24, x0 + 30, y1 - 30,
               x0 + 38, y1 - 36], fill=INK, width=2)
    draw.polygon([(x0 + 48, y1 - 14), (x0 + 62, y1 - 28), (x0 + 70, y1 - 14)],
                 fill=(90, 65, 40))
    text(draw, (x1 - 8, (y0 + y1) // 2), "1 DEAD", SANS_B(11), CREAM,
         anchor="rm")


def art_chart(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(20, 60, 50))
    pts = [(x0 + 10, y1 - 12), (x0 + 40, y1 - 26), (x0 + 70, y1 - 18),
           (x0 + 100, y1 - 32), (x0 + 128, y1 - 14)]
    draw.line(pts, fill=(240, 180, 60), width=3)
    draw.polygon([(x0 + 128, y1 - 14), (x0 + 118, y1 - 14),
                  (x0 + 128, y1 - 24)], fill=(240, 180, 60))
    text(draw, (x1 - 8, y0 + 12), "$60,406", SANS_B(11), CREAM,
         anchor="ra")


def art_trophy(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(20, 90, 50))
    draw.rectangle([x0 + 14, y0 + 8, x0 + 34, y0 + 28], fill=GOLD)
    draw.rectangle([x0 + 20, y0 + 28, x0 + 28, y0 + 36], fill=GOLD)
    draw.rectangle([x0 + 12, y0 + 36, x0 + 36, y1 - 8], fill=GOLD)
    icon_soccer(draw, x0 + 52, y0 + 7, 30, CREAM)
    text(draw, (x1 - 8, (y0 + y1) // 2), "CAS", SANS_B(13), CREAM,
         anchor="rm")


def art_goals(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(20, 90, 50))
    icon_soccer(draw, x0 + 10, y0 + 7, 30, CREAM)
    text(draw, (x1 - 8, (y0 + y1) // 2), "5\u20131", SERIF_B(20), CREAM,
         anchor="rm")


def art_pif(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(40, 40, 60))
    icon_tower(draw, x0 + 12, y0 + 6, 30, GOLD_LT)
    icon_flame(draw, x0 + 48, y0 + 6, 30, (240, 140, 40))
    text(draw, (x1 - 8, (y0 + y1) // 2), "11 HURT", SANS_B(11), GOLD_LT,
         anchor="rm")


def art_cikande(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(40, 30, 30))
    icon_flame(draw, x0 + 12, y0 + 6, 32, (240, 140, 40))
    text(draw, (x1 - 8, (y0 + y1) // 2), "26 BAGS", SANS_B(11), GOLD_LT,
         anchor="rm")


def art_shop(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(90, 60, 40))
    draw.rectangle([x0 + 12, y0 + 12, x0 + 56, y1 - 8], fill=CREAM)
    draw.polygon([(x0 + 8, y0 + 12), (x0 + 60, y0 + 12), (x0 + 54, y0 + 4),
                  (x0 + 14, y0 + 4)], fill=RED)
    text(draw, (x1 - 8, (y0 + y1) // 2), "25 HELD", SANS_B(11), CREAM,
         anchor="rm")


def art_bus(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(60, 50, 40))
    draw.rectangle([x0 + 10, y0 + 10, x0 + 58, y1 - 12], fill=(200, 170, 90))
    for wx in range(x0 + 16, x0 + 54, 12):
        draw.rectangle([wx, y0 + 14, wx + 7, y0 + 22], fill=INK)
    draw.ellipse([x0 + 16, y1 - 14, x0 + 24, y1 - 6], fill=INK)
    draw.ellipse([x0 + 44, y1 - 14, x0 + 52, y1 - 6], fill=INK)
    text(draw, (x1 - 8, (y0 + y1) // 2), "25", SANS_B(13), RED,
         anchor="rm")


def art_awacs(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(140, 180, 210))
    icon_drone(draw, x0 + 10, y0 + 6, 14, INK)
    icon_plane(draw, x0 + 40, y0 + 8, 28, INK)
    text(draw, (x1 - 8, (y0 + y1) // 2), "AWACS", SANS_B(11), INK,
         anchor="rm")


def art_crew(draw, x0, y0, x1, y1):
    # Crew unveiling only — no launch, no flame: three astronauts
    # under stars, Tiangong above.
    draw.rectangle([x0, y0, x1, y1], fill=(20, 30, 60))
    for sx, sy in ((14, 8), (34, 14), (52, 6), (66, 18)):
        draw.ellipse([x0 + sx, y0 + sy, x0 + sx + 2, y0 + sy + 2],
                     fill=CREAM)
    for px in (x0 + 18, x0 + 38, x0 + 58):
        draw.ellipse([px, y0 + 20, px + 10, y0 + 30], fill=GOLD_LT)
        draw.rectangle([px + 1, y0 + 30, px + 9, y1 - 8], fill=CREAM)
    text(draw, (x1 - 8, (y0 + y1) // 2), "3 CREW", SANS_B(11), CREAM,
         anchor="rm")


def art_chip(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(30, 30, 50))
    draw.rectangle([x0 + 12, y0 + 10, x0 + 38, y1 - 10], fill=TEAL)
    draw.rectangle([x0 + 19, y0 + 17, x0 + 31, y1 - 17], fill=GOLD)
    draw.ellipse([x1 - 38, y0 + 6, x1 - 8, y0 + 36], outline=RED, width=3)
    draw.line([x1 - 32, y0 + 30, x1 - 14, y0 + 12], fill=RED, width=3)
    text(draw, (x1 - 23, y0 + 21), "X", SANS_B(10), CREAM, anchor="mm")


def card(draw, x, y, w, n, region, color, headline, sub, art, tag,
         tag_color):
    """A small illustrated card: 44px scene, kicker + status tag,
    two-line headline, two-line sub. Total height 116."""
    art(draw, x, y, x + w, y + 44)
    draw.rectangle([x, y, x + w, y + 44], outline=GOLD, width=1)
    chip_left = tag_chip(draw, x + w, y + 55, tag, tag_color, fsize=7)
    kicker(draw, x, y + 48, n, region, color, size=15,
           max_w=chip_left - x - 4, fsize=8)
    lines = wrap(draw, headline, SERIF_B(12), w)
    assert len(lines) <= 2, f"card headline overflows: {headline!r}"
    yy = y + 66
    for line in lines:
        text(draw, (x, yy), line, SERIF_B(12))
        yy += 14
    slines = wrap(draw, sub, SANS_F(8.5), w)
    assert len(slines) <= 2, f"card sub overflows: {sub!r}"
    for line in slines:
        text(draw, (x, yy + 1), line, SANS_F(8.5), GRAY)
        yy += 10


def numbers_strip(draw, x, y, w, stats):
    text(draw, (x, y + 2), "BY THE", SANS_B(12), RED)
    text(draw, (x, y + 16), "NUMBERS", SANS_B(12), RED)
    col_w = (w - 92) // 6
    for i, (num, cap) in enumerate(stats):
        cx = x + 92 + i * col_w
        if i:
            draw.line([cx - 8, y, cx - 8, y + 36], fill=GOLD, width=1)
        text(draw, (cx, y), num, SERIF_B(22), INK)
        lines = wrap(draw, cap, SANS_F(9.5), col_w - 12)
        assert len(lines) <= 1, f"stat caption overflows: {cap!r}"
        yy = y + 26
        for line in lines:
            text(draw, (cx, yy), line, SANS_F(9.5), GRAY)
            yy += 12


def timeline_strip(draw, x, y, w, beats):
    """One-line UTC timeline: the day's arc, dawn to night."""
    draw.line([x, y, x + w, y], fill=GOLD, width=1)
    draw.line([x, y + 18, x + w, y + 18], fill=GOLD, width=1)
    label = "THE DAY IN UTC  "
    lfnt, bfnt = SANS_B(10), SANS_F(9.5)
    text(draw, (x, y + 9), label, lfnt, RED, anchor="lm")
    lx = x + draw.textlength(label, font=lfnt)
    body = "  \u00b7  ".join(f"{t}  {s}" for t, s in beats)
    assert draw.textlength(body, font=bfnt) <= w - (lx - x), \
        f"timeline overflows: {body!r}"
    text(draw, (lx, y + 9), body, bfnt, INK, anchor="lm")


def continent_bar(draw, x0, y0, x1, y1, segments):
    """Colour bar under the masthead: one segment per continent with its
    story count. The bar is the legend for badges and map pins."""
    n = len(segments)
    total = x1 - x0
    for i, (label, count, color) in enumerate(segments):
        sx0 = x0 + i * total // n
        sx1 = x0 + (i + 1) * total // n
        draw.rectangle([sx0, y0, sx1, y1], fill=color)
        if i:
            draw.line([sx0, y0, sx0, y1], fill=PAPER, width=2)
        text(draw, ((sx0 + sx1) // 2, (y0 + y1) // 2),
             f"{label} \u00b7 {count}", SANS_B(11), CREAM, anchor="mm")


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # --- art-deco frame: gold outer rule, ink inner rule, stepped corners ---
    d.rectangle([5, 5, W - 6, H - 6], outline=GOLD, width=3)
    d.rectangle([11, 11, W - 12, H - 12], outline=INK, width=1)
    # Stepped corners on the top only: the bottom ones crossed the footer.
    for cx, cy, sx, sy in ((11, 11, 1, 1), (W - 12, 11, -1, 1)):
        for k in range(3):
            o = 18 + k * 6
            d.line([cx + sx * o, cy, cx + sx * o, cy + sy * 10],
                   fill=GOLD, width=2)
            d.line([cx, cy + sy * o, cx + sx * 10, cy + sy * o],
                   fill=GOLD, width=2)

    # --- masthead: deep-sea teal, gold lettering, one watching eye ---
    d.rectangle([14, 14, 1010, 124], fill=TEAL_DARK)
    draw_eye(d, 512 - 17, 18)
    text(d, (24, 22), "THE DAY IN WORLD NEWS", SANS_B(13), GOLD_LT)
    text(d, (1000, 22), "60 STORIES  \u00b7  7 REGIONS  \u00b7  ONE PAGE",
         SANS_B(13), GOLD_LT, anchor="ra")
    date = "Tuesday 24 November 2026"
    dfnt = SERIF_B(54)
    assert d.textlength(date, font=dfnt) <= 976, "masthead date too wide"
    text(d, (24, 42), date, dfnt, CREAM)
    text(d, (24, 100),
         "Every story on this page happened, or was first reported, on this day.",
         SERIF_F(16), CREAM)
    diamond(d, 990, 106, 5, GOLD)
    d.rectangle([14, 124, 1010, 126], fill=GOLD)
    d.rectangle([14, 127, 1010, 129], fill=RED)

    # --- continent bar: colour-coding legend with counts ---
    continent_bar(d, 14, 132, 1010, 156, [
        ("N. AMERICA", 11, N_AMERICA),
        ("EUROPE", 11, EUROPE),
        ("MIDDLE EAST", 11, MIDDLE_EAST),
        ("ASIA", 10, ASIA),
        ("AFRICA", 9, AFRICA),
        ("S. AMERICA", 4, S_AMERICA),
        ("OCEANIA", 4, OCEANIA),
    ])

    # --- by the numbers ---
    numbers_strip(d, 24, 160, 976, [
        ("25", "Hostages, Cartagena"),
        ("26", "Body bags, Cikande"),
        ("4", "Tankers hit, Hormuz"),
        ("11", "Wounded, Riyadh tower"),
        ("175", "Migrants missing, Dakar"),
        ("$60,406", "Bitcoin close, \u22121.68%"),
    ])

    # --- the day in UTC ---
    timeline_strip(d, 24, 198, 976, [
        ("00:00", "Hormuz tankers"),
        ("02:09", "El Chapo drone"),
        ("08:14", "Ukraine ship strikes"),
        ("10:42", "Yemen bus strikes"),
        ("14:27", "PIF tower hit"),
        ("20:41", "Huawei guilty"),
    ])

    # --- top row: three illustrated leads ---
    lead(d, 24, 222, 317, 1, "N. AMERICA  \u00b7  COURTS", N_AMERICA,
         "US jury finds Huawei guilty of trade secrets and bank fraud",
         "Guilty on 10 of 12 counts, incl. sanctions violations; "
         "acquitted of racketeering. Huawei to appeal; sentencing "
         "Sept 2027. (Reuters)", draw_huawei, "CONFIRMED", TAG_CONFIRMED)
    lead(d, 353, 222, 317, 2, "MIDDLE EAST  \u00b7  WAR", MIDDLE_EAST,
         "Iran says four tankers hit mines in the Strait of Hormuz",
         "IRGC: three tankers hit mines and caught fire, then a "
         "fourth. Maritime centre: the mine claims are "
         "unconfirmed.", draw_tanker, "CLAIM",
         TAG_CLAIM)
    lead(d, 682, 222, 317, 3, "EUROPE  \u00b7  WAR", EUROPE,
         "Ukraine acknowledges strikes on Russian ships in the Gulf and off Libya",
         "Kyiv confirms the Sparta II drone strike \u2014 16 crew "
         "evacuated \u2014 and naval drones off Libya; Kyiv claims "
         "the corvette sunk, Libya says damaged.", draw_ships,
         "REPORTED", TAG_REPORTED)
    d.line([24, 454, 1000, 454], fill=INK, width=2)

    # --- middle rows: ten illustrated cards, five per row ---
    xs = [24, 221, 418, 615, 812]
    row1 = [
        (4, "N. AMERICA", N_AMERICA,
         "Asian stocks surge; Bitcoin below $60,000",
         "Seoul +6%, Nikkei +3.91% Tuesday; Bitcoin close $60,406, "
         "\u22121.68%. (CoinDesk)", art_chart, "CONFIRMED", TAG_CONFIRMED),
        (5, "AFRICA", AFRICA,
         "CAS restores Senegal as AFCON champions",
         "Referee did not err resuming the final; 1\u20130 win "
         "stands. (Reuters)", art_trophy, "CONFIRMED",
         TAG_CONFIRMED),
        (6, "EUROPE", EUROPE,
         "Real Madrid 5\u20131 PSV as UCL resumes",
         "Bellingham, Mbapp\u00e9 inspire comeback win. (UEFA)",
         art_goals, "CONFIRMED",
         TAG_CONFIRMED),
        (7, "MIDDLE EAST", MIDDLE_EAST,
         "Houthi drone hits Riyadh PIF tower",
         "11 wounded in King Abdullah district. (Wires)",
         art_pif, "REPORTED",
         TAG_REPORTED),
        (8, "ASIA", ASIA,
         "Cikande fire toll: 26 body bags found",
         "26 body bags found at Serang factory. (Xinhua)",
         art_cikande, "CONFIRMED",
         TAG_CONFIRMED),
    ]
    for (n, region, col, head, sub, art, tag, tcol), x in zip(row1, xs):
        card(d, x, 460, 188, n, region, col, head, sub, art, tag, tcol)
    row2 = [
        (9, "S. AMERICA", S_AMERICA,
         "25 hostages held at Cartagena shop",
         "Armed men seize a supermarket; five women freed. (Wires)",
         art_shop, "CONFIRMED",
         TAG_CONFIRMED),
        (10, "MIDDLE EAST", MIDDLE_EAST,
         "Saudi strikes on Yemen buses: 25 dead/missing",
         "Buses and trucks hit in Lahj; six wounded. (Saba)",
         art_bus, "REPORTED", TAG_REPORTED),
        (11, "EUROPE", EUROPE,
         "Russian drone over Poland; NATO AWACS",
         "Recon drone flies minutes over Dorohusk. (Wires)",
         art_awacs, "CONFIRMED",
         TAG_CONFIRMED),
        (12, "ASIA", ASIA,
         "Shenzhou-24 crew unveiled: Pakistani first",
         "Tang, Wu and Zeeshan Ali named for Tiangong. (Reuters)",
         art_crew, "CONFIRMED",
         TAG_CONFIRMED),
        (13, "N. AMERICA", N_AMERICA,
         "US blacklists Megaspeed in Nvidia case",
         "Singapore firm and six others on Entity List. (Commerce)",
         art_chip, "CONFIRMED",
         TAG_CONFIRMED),
    ]
    for (n, region, col, head, sub, art, tag, tcol), x in zip(row2, xs):
        card(d, x, 584, 188, n, region, col, head, sub, art, tag, tcol)
    d.line([24, 706, 1000, 706], fill=INK, width=2)

    # --- bottom left: where the news happened ---
    text(d, (24, 710), "WHERE THE NEWS HAPPENED", SANS_B(13), INK)
    draw_map(d, 24, 728, 324, 930, [
        (1, -77, 38.9, 6, -6, N_AMERICA),
        (2, 56.5, 26.6, 0, 0, MIDDLE_EAST),
        (3, 27, 60, 8, -4, EUROPE),
        (4, 127, 37.5, 0, 0, ASIA),
        (5, -17.4, 14.7, -8, 4, AFRICA),
        (6, -3.7, 40.4, 6, 4, EUROPE),
        (7, 46.7, 24.7, 0, 0, MIDDLE_EAST),
        (8, 106.1, -6.1, 0, 0, ASIA),
        (9, -75.5, 10.4, -6, 6, S_AMERICA),
        (10, 45, 13, 0, 0, MIDDLE_EAST),
        (11, 23.8, 51.2, 0, -6, EUROPE),
        (12, 100.3, 40.9, 0, 0, ASIA),
        (13, 103.8, 1.35, 0, 0, N_AMERICA),
    ])

    # --- bottom right: 47 more stories, numbered, colour-coded ---
    text(d, (336, 710),
         "ALSO ON TUESDAY 24 NOVEMBER  \u2014  47 MORE STORIES",
         SANS_B(13), INK)
    briefs = [
        (14, "US: Pentagon rebukes Canada defence", N_AMERICA),
        (15, "Mexico: US drone helped catch El Chapo", N_AMERICA),
        (16, "El Salvador: Bukele names 3 Haiti dead", N_AMERICA),
        (17, "Cuba: WHO chief visits ailing system", N_AMERICA),
        (18, "NFL: Commanders beat Bengals 22-20", N_AMERICA),
        (19, "NBA: Bucks end 13-game skid, 116-111", N_AMERICA),
        (20, "US: Ninth measles death in PA", N_AMERICA),
        (21, "US: FBI deputy Raia plans to retire", N_AMERICA),
        (22, "Colombia: Car bomb injures 23", S_AMERICA),
        (23, "Venezuela: Reveals $240bn debt pile", S_AMERICA),
        (24, "Brazil: Cuts 2027 growth to 1.8%", S_AMERICA),
        (25, "Ukraine: Zelenskyy urges 4-party talks", EUROPE),
        (26, "Ukraine: Zaporizhzhia strikes kill 2", EUROPE),
        (27, "Europe: Sparta II towed to St Petersburg", EUROPE),
        (28, "Europe: EU to ban Russian symbols", EUROPE),
        (29, "Latvia: War may tip to Russian defeat", EUROPE),
        (30, "Poland: Peace deal won't end sabotage", EUROPE),
        (31, "Denmark: Top court backs 'ghetto plan'", EUROPE),
        (32, "Armenia: Drops Karabakh reference", EUROPE),
        (33, "Libya: Tripoli demands Kyiv explain", AFRICA),
        (34, "Libya: Haftar visits Turkey first time", AFRICA),
        (35, "DR Congo: Search for missing plane", AFRICA),
        (36, "Senegal: 175 migrants missing off Dakar", AFRICA),
        (37, "Zambia: Opposition leader faces treason", AFRICA),
        (38, "Nigeria: Gunmen kill 4 at Delta campaign", AFRICA),
        (39, "Ghana: Tullow pays $112m to settle taxes", AFRICA),
        (40, "S. Africa: Cities tighten water limits", AFRICA),
        (41, "Gaza: Strike kills Hamas security chief", MIDDLE_EAST),
        (42, "Gaza: Meningitis alert, 272 cases in Oct", MIDDLE_EAST),
        (43, "Gaza: Oxfam calls it a 'toxic land'", MIDDLE_EAST),
        (44, "Iraq: Baghdad seizes Kurdish oilfields", MIDDLE_EAST),
        (45, "Yemen: Houthis 60 km from Aden, ready", MIDDLE_EAST),
        (46, "UK: Sanctions Houthis, four officials", MIDDLE_EAST),
        (47, "Iran: No talks until US meets 7 demands", MIDDLE_EAST),
        (48, "Iran: Singer gets 74 lashes for singing", MIDDLE_EAST),
        (49, "S. Korea: Russian jets enter defence zone", ASIA),
        (50, "Nepal: M5.6 quake hits Koshi province", ASIA),
        (51, "Vietnam: Hanoi restaurant blast kills 6", ASIA),
        (52, "Indonesia: Prabowo names VP candidates", ASIA),
        (53, "China: Official sentenced to death", ASIA),
        (54, "Bangladesh: Hasina to return Dec 16", ASIA),
        (55, "Malaysia: To return migrants to Myanmar", ASIA),
        (56, "Japan: PM to pay ICC dues early", ASIA),
        (57, "Australia: Coalition kills Vanuatu treaty", OCEANIA),
        (58, "Pacific: Leaders despair at COP31", OCEANIA),
        (59, "Pacific: Elders accuse Australia", OCEANIA),
        (60, "Fiji: Schools close 5 days in drought", OCEANIA),
    ]
    assert len(briefs) == 47, f"expected 47 briefs, got {len(briefs)}"
    bfnt = SANS_F(9)
    for i, (n, s, col) in enumerate(briefs):
        col_i = i // 16
        row = i % 16
        bx = 336 + col_i * 222
        by = 728 + row * 13
        assert d.textlength(s, font=bfnt) <= 195, f"brief too wide: {s!r}"
        badge(d, bx, by, n, size=11, color=col)
        text(d, (bx + 15, by), s, bfnt)

    # --- date check: what was deliberately left out ---
    d.rectangle([24, 932, 1000, 976], outline=RED, width=2)
    text(d, (32, 938), "DATE CHECK \u2014 NOT SUNDAY NEWS", SANS_B(11), RED)
    text(d, (992, 938),
         "TAGS: CONFIRMED = 2+ outlets \u00b7 REPORTED = one outlet \u00b7 "
         "CLAIM = one side's account", SANS_F(9), GRAY, anchor="ra")
    text(d, (32, 954),
         "Left out on purpose: ICJ Myanmar ruling (Thu 19 Nov) \u00b7 "
         "'El Chapo Isidro' captured (Fri 20 Nov) \u00b7 COP31 collapse "
         "(Sun 22 Nov) \u00b7 Sparta II / Benghazi strike (Sun 22 Nov)",
         SANS_F(10), INK)
    text(d, (32, 968),
         "Shenzhou-24 launch (Wed 25 Nov) \u00b7 Huang reinstated "
         "(Mon 23 Nov) \u00b7 Trump death-penalty directive (Mon) \u00b7 "
         "Belgium strike (Mon) \u00b7 AFCON final (Jan) \u00b7 Cikande "
         "fire itself (Sat 21 Nov)", SANS_F(10), INK)

    # --- footer ---
    d.line([24, 982, 1000, 982], fill=INK, width=1)
    text(d, (24, 986),
         "Every story on this page happened, or was first reported, on "
         "Tuesday 24 November 2026. Claims are attributed, not stated as "
         "fact. Wires read to 01:30 UTC, Wed 25 Nov 2026.", SANS_F(10), GRAY)
    text(d, (24, 1000),
         "Sources: Daily Summary Of, Horizon, Just Security, Reuters, AP, "
         "UEFA, CAS, Xinhua, CoinDesk. Original drawings.", SANS_F(10), GRAY)

    out = os.path.join(HERE, "entry.png")
    img.save(out, "PNG", optimize=True)
    print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
