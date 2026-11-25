#!/usr/bin/env python3
"""Render the 24 November 2026 front page: 60 stories, one 1024x1024 image.

A cream-paper broadsheet in an Orwell-1984 x Bioshock art-deco register:
deep teal and gold, propaganda red, serif display type. Everything is
drawn with Pillow primitives -- no network, no randomness, no external
assets -- so two runs produce byte-identical output.

Layout, top to bottom: teal masthead, red dek, continent bar with story
counts, six-number stats strip, UTC timeline, three hero stories, ten
cards, a dotted world map with numbered pins beside 47 one-line briefs,
a red DATE CHECK box, and a sources footer.
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.png")

# ---- palette -------------------------------------------------------------
PAPER = (245, 238, 220)    # cream page
CARD = (250, 244, 230)     # lighter cream for story cards
INK = (26, 26, 26)
TEAL = (14, 59, 60)
TEAL_DARK = (9, 44, 45)
NAVY = (13, 30, 46)
GOLD = (176, 141, 42)
GOLD_LIGHT = (201, 162, 60)
RED = (158, 27, 27)
RED_SOFT = (178, 52, 44)
CREAM_TEXT = (240, 230, 205)
MAP_DOT = (110, 139, 133)
HAIRLINE = (150, 128, 84)

REGION_COLORS = {
    "N. AMERICA": (49, 89, 127),
    "EUROPE": (91, 122, 94),
    "MIDDLE EAST": (166, 90, 46),
    "ASIA": (122, 90, 140),
    "AFRICA": (140, 107, 63),
    "S. AMERICA": (46, 125, 107),
    "OCEANIA": (78, 122, 138),
}
REGION_COUNTS = [
    ("N. AMERICA", 11), ("EUROPE", 11), ("MIDDLE EAST", 11),
    ("ASIA", 10), ("AFRICA", 9), ("S. AMERICA", 4), ("OCEANIA", 4),
]
TAG_COLORS = {
    "CONFIRMED": (46, 107, 52),
    "REPORTED": (176, 122, 30),
    "CLAIM": (158, 27, 27),
}

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    path = os.path.join(FONT_DIR, name)
    if not os.path.exists(path):
        path = os.path.join(FONT_DIR, "DejaVuSans.ttf")
    return ImageFont.truetype(path, size)


def serif(size):
    return font("DejaVuSerif.ttf", size)


def serif_b(size):
    return font("DejaVuSerif-Bold.ttf", size)


def sans(size):
    return font("DejaVuSans.ttf", size)


def sans_b(size):
    return font("DejaVuSans-Bold.ttf", size)


# ---- text helpers --------------------------------------------------------
def wrap(d, text, f, width):
    """Greedy word wrap; returns a list of lines that fit `width`."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=f) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_block(d, text, make_font, size, width, max_lines, floor=8):
    """Wrap text, shrinking the font until it fits in max_lines."""
    while size > floor:
        lines = wrap(d, text, make_font(size), width)
        if len(lines) <= max_lines:
            return lines, make_font(size)
        size -= 1
    lines = wrap(d, text, make_font(floor), width)
    return lines[:max_lines], make_font(floor)


def fit_line(d, text, make_font, size, width, floor=8):
    """Shrink one line to fit; truncate with an ellipsis as a last resort."""
    f = make_font(size)
    while size > floor and d.textlength(text, font=f) > width:
        size -= 1
        f = make_font(size)
    if d.textlength(text, font=f) > width:
        while text and d.textlength(text + "\u2026", font=f) > width:
            text = text[:-1]
        text = text + "\u2026"
    return text, make_font(size)


def centre(d, x0, x1, y, text, f, fill):
    w = d.textlength(text, font=f)
    d.text((x0 + (x1 - x0 - w) / 2, y), text, font=f, fill=fill)


# ---- content -------------------------------------------------------------
# (number, region, section, tag, headline, body)
HEROES = [
    (1, "N. AMERICA", "COURTS", "CONFIRMED",
     "US jury finds Huawei guilty of trade secrets and bank fraud",
     "Guilty on 10 of 12 counts; acquitted of racketeering. Huawei to "
     "appeal; sentencing Sept 2027."),
    (2, "MIDDLE EAST", "WAR", "CLAIM",
     "Iran says four tankers hit mines in the Strait of Hormuz",
     "IRGC: three tankers hit mines and caught fire, then a fourth. "
     "Maritime centre: mine claims unconfirmed."),
    (3, "EUROPE", "WAR", "REPORTED",
     "Ukraine acknowledges strikes on Russian ships off Finland and Libya",
     "Kyiv confirms the Sparta II strike \u2014 towed to port, 16 crew "
     "out \u2014 and naval-drone hits off Libya."),
]

# (number, region, section, tag, headline, body)
CARDS = [
    (4, "N. AMERICA", "MARKETS", "CONFIRMED",
     "Asian stocks surge; Bitcoin slips below $60,000",
     "Seoul +6%, Nikkei +3.91%; Bitcoin closes $60,406 (\u22121.68%)."),
    (5, "AFRICA", "SPORT", "CONFIRMED",
     "CAS restores Senegal as Africa Cup champions",
     "CAS upholds Senegal\u2019s appeal; the 1\u20130 extra-time win over "
     "Morocco stands."),
    (6, "EUROPE", "SPORT", "CONFIRMED",
     "Real Madrid 5\u20131 PSV as Champions League kicks off",
     "Bellingham and Mbapp\u00e9 inspire the comeback; Arsenal 1\u20131 "
     "Dortmund."),
    (7, "MIDDLE EAST", "WAR", "REPORTED",
     "Houthi drone hits Riyadh PIF tower; 11 wounded",
     "A Houthi drone hits a KAFD tower in Riyadh \u2014 the second strike "
     "in a week."),
    (8, "ASIA", "DISASTER", "CONFIRMED",
     "Cikande candy factory fire toll rises to 26",
     "26 body bags recovered in Serang, Banten; about 30 workers still "
     "missing."),
    (9, "S. AMERICA", "CRIME", "CONFIRMED",
     "25 hostages held at a Cartagena supermarket",
     "Armed men seize a supermarket after a botched heist; five women "
     "released."),
    (10, "MIDDLE EAST", "WAR", "REPORTED",
     "Saudi strikes on Yemen buses: 25 dead or missing",
     "Aircraft hit buses and trucks in Wadi Maabaq, Lahj; six wounded."),
    (11, "EUROPE", "WAR", "CONFIRMED",
     "Russian drone enters Polish airspace; NATO sends AWACS",
     "A reconnaissance drone flies minutes over Dorohusk; Poland holds "
     "fire."),
    (12, "ASIA", "SPACE", "CONFIRMED",
     "Shenzhou-24 crew unveiled: first Pakistani to Tiangong",
     "China names its crew: Tang Hongbo, Wu Yi and Pakistani Zeeshan Ali, "
     "40."),
    (13, "N. AMERICA", "TECH", "CONFIRMED",
     "US blacklists Megaspeed, firm at centre of Nvidia scandal",
     "Commerce puts Megaspeed and six firms on the Entity List over Nvidia "
     "GPUs."),
]

# (number, region, one-line brief)
BRIEFS = [
    (14, "N. AMERICA", "US \u2014 Pentagon rebukes Canada; 41.9% of its air fleet serviceable."),
    (15, "N. AMERICA", "Mexico \u2014 US drone helped catch \u2018El Chapo Isidro\u2019; Mexico to try him."),
    (16, "N. AMERICA", "El Salvador \u2014 3 soldiers killed in a blast on the Haiti mission."),
    (17, "N. AMERICA", "Cuba \u2014 WHO chief visits as health falters; WHO pledges $2m for jabs."),
    (18, "N. AMERICA", "NFL \u2014 Commanders beat Bengals 22\u201320 on a last-play field goal (MNF)."),
    (19, "N. AMERICA", "NBA \u2014 Bucks end 13-game skid, 116\u2013111 at Toronto; Herro scores 32."),
    (20, "N. AMERICA", "US \u2014 Ninth measles death in Pennsylvania; 46 counties affected."),
    (21, "N. AMERICA", "US \u2014 FBI deputy director Raia plans to retire by year-end."),
    (22, "S. AMERICA", "Colombia \u2014 Car bomb in Villavicencio injures 23; ex-FARC blamed."),
    (23, "S. AMERICA", "Venezuela \u2014 Reveals a $240bn debt pile ahead of restructuring."),
    (24, "S. AMERICA", "Brazil \u2014 Cuts 2027 growth forecast to 1.8%; raises inflation to 4.5%."),
    (25, "EUROPE", "Ukraine \u2014 Zelenskyy urges four-party talks with Russia, US, Europe."),
    (26, "EUROPE", "Ukraine \u2014 Zaporizhzhia strikes kill 2, wound 40 \u2014 incl. four children."),
    (27, "EUROPE", "Europe \u2014 Sparta II towed to St Petersburg; first Kremlin comment."),
    (28, "EUROPE", "Europe \u2014 EU proposes banning Russian symbols at sports events."),
    (29, "EUROPE", "Latvia \u2014 Rinkevics: war may reach a tipping point next year."),
    (30, "EUROPE", "Poland \u2014 Minister: peace deal won\u2019t end Russia\u2019s sabotage campaign."),
    (31, "EUROPE", "Denmark \u2014 Top court backs \u2018ghetto plan\u2019 for non-Western tenants."),
    (32, "EUROPE", "Armenia \u2014 Drops Nagorno-Karabakh reference from draft constitution."),
    (33, "AFRICA", "Libya \u2014 Tripoli demands answers from Kyiv over Benghazi ship attacks."),
    (34, "AFRICA", "Libya \u2014 Haftar visits Turkey for the first time; to meet Erdo\u011fan."),
    (35, "AFRICA", "DR Congo \u2014 Missing Cessna 208 hunted; rebels claim they shot it down."),
    (36, "AFRICA", "Senegal \u2014 About 175 migrants missing after a boat leaves Dakar."),
    (37, "AFRICA", "Zambia \u2014 Mundubile and 12 others face formal treason charges."),
    (38, "AFRICA", "Nigeria \u2014 Gunmen kill four at Delta campaign; night curfew imposed."),
    (39, "AFRICA", "Ghana \u2014 Tullow Oil to pay $112m upfront to settle tax disputes."),
    (40, "AFRICA", "South Africa \u2014 Water curbs tighten as El Ni\u00f1o drought looms."),
    (41, "MIDDLE EAST", "Gaza \u2014 Strike kills Hamas security chief Abu Nahel and six others."),
    (42, "MIDDLE EAST", "Gaza \u2014 Meningitis alert: 272 cases in October, 15 dead this year."),
    (43, "MIDDLE EAST", "Gaza \u2014 Oxfam: attacks turned the territory into a \u2018toxic land\u2019."),
    (44, "MIDDLE EAST", "Iraq \u2014 PM takes federal control of Kurdish oilfields; Barzani objects."),
    (45, "MIDDLE EAST", "Yemen \u2014 Military: Houthis are 60 km from Aden and ready to attack."),
    (46, "MIDDLE EAST", "UK \u2014 Sanctions Houthis and four officials over Red Sea attacks."),
    (47, "MIDDLE EAST", "Iran \u2014 Negotiator rules out talks until US meets seven conditions."),
    (48, "MIDDLE EAST", "Iran \u2014 Singer Ahmadi given 74 lashes in Qom for singing unveiled."),
    (49, "ASIA", "South Korea \u2014 Russian jets enter its air zone; fighters scrambled."),
    (50, "ASIA", "Nepal \u2014 M5.6 earthquake strikes Koshi province near the China border."),
    (51, "ASIA", "Vietnam \u2014 Hanoi hot-pot blast kills six, injures 10+; gas suspected."),
    (52, "ASIA", "Indonesia \u2014 Prabowo names Amran and Sugiono to replace VP Gibran."),
    (53, "ASIA", "China \u2014 Official Ma sentenced to death for spying; 35 secrets sold."),
    (54, "ASIA", "Bangladesh \u2014 Hasina plans Dec 16 return; Dhaka says handcuffs await."),
    (55, "ASIA", "Malaysia \u2014 Returning thousands of migrants to Myanmar, 1,500 by ship."),
    (56, "ASIA", "Japan \u2014 PM Takaichi: Japan will pay its full 2027 ICC share early."),
    (57, "OCEANIA", "Australia \u2014 Coalition opposes Vanuatu deal, killing bipartisanship."),
    (58, "OCEANIA", "Pacific \u2014 Island leaders despair as COP31 collapse fallout spreads."),
    (59, "OCEANIA", "Pacific \u2014 Elders accuse Australia of climate betrayal at COP31."),
    (60, "OCEANIA", "Fiji \u2014 Schools shut five days from Nov 30 as El Ni\u00f1o drought deepens."),
]

STATS = [
    ("25", "HOSTAGES HELD", "CARTAGENA"),
    ("26", "BODY BAGS RECOVERED", "CIKANDE"),
    ("4", "TANKERS HIT", "STRAIT OF HORMUZ"),
    ("11", "WOUNDED", "RIYADH PIF TOWER"),
    ("175", "MIGRANTS MISSING", "OFF DAKAR"),
    ("$60,406", "BITCOIN, TUESDAY CLOSE", "\u22121.68%"),
]

TIMELINE = [
    ("00:00", "Iran: four tankers hit mines"),
    ("00:30", "Zelenskyy urges four-party talks"),
    ("02:09", "US drone helped capture \u2018El Chapo Isidro\u2019"),
    ("08:14", "Ukraine acknowledges ship strikes"),
    ("10:42", "Saudi strikes on Yemen buses"),
    ("14:27", "PIF tower hit in Riyadh"),
    ("17:35", "Cartagena hostages"),
    ("20:41", "Huawei guilty"),
]

DATE_CHECK = (
    "LEFT OUT \u2014 NOT 24 NOV: ICJ Myanmar ruling (Thu 19) \u00b7 \u2018El Chapo "
    "Isidro\u2019 captured (Fri 20) \u00b7 COP31 collapse (Sun 22) \u00b7 Sparta II / "
    "Benghazi strike (Sun 22) \u00b7 Shenzhou-24 launch (Wed 25) \u00b7 Huang "
    "reinstated (Mon 23) \u00b7 Trump death-penalty directive (Mon 23) \u00b7 Rep. "
    "Jimmy Gomez resigns (Mon 23) \u00b7 Trump hush-money case to federal court "
    "(Mon 23) \u00b7 Belgium austerity strike (Mon 23) \u00b7 Australia\u2013Solomon "
    "Islands pact (Wed 25) \u00b7 Vanuatu M6.5 quake (Mon 23) \u00b7 Kilauea lava "
    "episode 57 (Mon) \u00b7 Estonia border closure (21/22 Nov) \u00b7 Cikande fire "
    "itself (Sat 21) \u00b7 AFCON final, Senegal beat Morocco (Jan). "
    "COUNTED ONLY AS TUESDAY\u2019S NEWS: the Cikande toll rise (26 body bags "
    "recovered) \u00b7 the Shenzhou-24 crew unveiling \u00b7 the US drone help in "
    "the El Chapo capture. NOTE: the Nasdaq +6.51% surge was Monday\u2019s close "
    "\u2014 not Tuesday\u2019s move."
)

# Dotted world map: continents as ellipses in a 100 x 70 grid.
LAND = [
    (16, 16, 13, 9),    # North America
    (30, 6, 4, 3),      # Greenland
    (27, 44, 6, 11),    # South America
    (50, 14, 9, 8),     # Europe
    (52, 36, 8, 12),    # Africa
    (60, 26, 6, 6),     # Middle East
    (72, 14, 16, 9),    # Asia
    (84, 24, 7, 7),     # East Asia
    (80, 40, 9, 6),     # SE Asia / Indonesia
    (86, 52, 6, 4.5),   # Australia
]

# (story number, lon, lat, dx, dy) -- dx/dy nudge the pin so clusters separate.
PINS = [
    (1, -77.0, 39.0, 0, 0),
    (2, 56.5, 26.5, 5, -6),
    (3, 24.0, 59.5, -4, -5),
    (4, 139.7, 35.7, 3, 5),
    (5, -17.4, 14.7, 0, 0),
    (6, -3.7, 40.4, -5, 3),
    (7, 46.7, 24.6, -6, 4),
    (8, 106.1, -6.1, 0, 0),
    (9, -75.5, 10.4, 0, 0),
    (10, 44.5, 13.0, 2, 7),
    (11, 23.8, 51.2, 5, -3),
    (12, 116.4, 39.9, -5, -5),
    (13, 103.8, 1.35, 3, 6),
]


# ---- hero illustrations (deco panels, Pillow primitives only) -------------
def art_court(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=TEAL_DARK)
    cx, cy = x + w // 2, y + h
    for ang in range(-75, 76, 15):
        rad = math.radians(ang - 90)
        ex = cx + int(160 * math.cos(rad))
        ey = cy + int(160 * math.sin(rad))
        d.line([cx, cy, ex, ey], fill=GOLD, width=2)
    d.polygon([(cx - 58, y + 16), (cx + 58, y + 16), (cx, y + 2)], fill=GOLD)
    for dx in (-40, 0, 40):
        d.rectangle([cx + dx - 5, y + 20, cx + dx + 5, y + 52],
                    fill=CREAM_TEXT)
    d.rectangle([x + 20, y + 56, x + w - 20, y + 60], fill=CREAM_TEXT)
    d.line([x + 8, y + 66 - 2, x + w - 8, y + 66 - 2], fill=GOLD, width=2)


def art_tankers(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=NAVY)
    d.ellipse([x + w - 78, y + 6, x + w - 48, y + 36], fill=RED_SOFT)
    d.rectangle([x, y + 44, x + w, y + h], fill=(10, 24, 38))
    d.line([x, y + 44, x + w, y + 44], fill=GOLD, width=2)
    ships = [(x + 12, 54), (x + 90, 48), (x + 166, 56), (x + 238, 46)]
    for sx, sw in ships:
        d.rectangle([sx, y + 52, sx + sw, y + 64], fill=(52, 66, 84))
        d.rectangle([sx + 8, y + 44, sx + 24, y + 52], fill=(52, 66, 84))
        d.rectangle([sx + 30, y + 40, sx + 36, y + 52], fill=(52, 66, 84))
    for sx in (x + 20, x + 174):
        d.polygon([(sx, y + 40), (sx + 10, y + 22), (sx + 20, y + 40)],
                  fill=(214, 120, 40))
        d.polygon([(sx + 4, y + 40), (sx + 10, y + 30), (sx + 16, y + 40)],
                  fill=RED_SOFT)


def art_drone_ship(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(38, 74, 84))
    d.ellipse([x + 16, y + 8, x + 36, y + 28], fill=GOLD)
    d.rectangle([x, y + 46, x + w, y + h], fill=(24, 52, 62))
    d.line([x, y + 46, x + w, y + 46], fill=GOLD, width=2)
    dx, dy = x + w - 70, y + 14
    d.rectangle([dx - 8, dy - 4, dx + 8, dy + 4], fill=(20, 20, 20))
    for ox, oy in [(-16, -10), (16, -10), (-16, 10), (16, 10)]:
        d.line([dx, dy, dx + ox, dy + oy], fill=CREAM_TEXT, width=1)
        d.ellipse([dx + ox - 6, dy + oy - 3, dx + ox + 6, dy + oy + 3],
                  outline=CREAM_TEXT, width=1)
    sx = x + 24
    d.polygon([(sx, y + 56), (sx + 96, y + 56), (sx + 84, y + 66),
               (sx + 12, y + 66)], fill=(16, 16, 16))
    d.rectangle([sx + 40, y + 42, sx + 46, y + 56], fill=(16, 16, 16))
    for cx, cy, r in [(sx + 43, y + 34, 5), (sx + 48, y + 26, 7),
                      (sx + 40, y + 18, 6)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(200, 200, 190))


HERO_ART = [art_court, art_tankers, art_drone_ship]


# ---- drawing -------------------------------------------------------------
def tag_chip(d, x, y, tag):
    f = sans_b(8)
    tw = d.textlength(tag, font=f)
    d.rounded_rectangle([x, y, x + tw + 12, y + 13], radius=3,
                        fill=TAG_COLORS[tag])
    d.text((x + 6, y + 2), tag, font=f, fill=(255, 255, 255))


def draw_masthead(d):
    d.rectangle([26, 20, 998, 88], fill=TEAL)
    d.line([26, 20, 998, 20], fill=GOLD, width=2)
    d.line([26, 88, 998, 88], fill=GOLD, width=2)
    d.text((40, 28), "THE WORLD IN ONE DAY", font=serif_b(34),
           fill=CREAM_TEXT)
    date = "TUESDAY 24 NOVEMBER 2026"
    dw = d.textlength(date, font=serif_b(19))
    d.text((984 - dw, 34), date, font=serif_b(19), fill=GOLD_LIGHT)
    d.text((40, 66), "60 STORIES \u00b7 7 REGIONS \u00b7 EVERY ONE DATED "
                     "TUESDAY 24 NOVEMBER 2026", font=sans_b(11),
           fill=CREAM_TEXT)
    press = "PRESS TIME 01:30 UTC \u00b7 WED 25 NOV 2026"
    pw = d.textlength(press, font=sans_b(10))
    d.text((984 - pw, 68), press, font=sans_b(10), fill=GOLD_LIGHT)


def draw_dek(d):
    dek = ("Huawei guilty on 10 counts  \u00b7  Four tankers hit in the Strait "
           "of Hormuz  \u00b7  Ukraine owns up to the ship strikes")
    centre(d, 26, 998, 96, dek, serif(15), RED)


def draw_continent_bar(d):
    total = sum(c for _, c in REGION_COUNTS)
    x = 26
    for name, count in REGION_COUNTS:
        w = round(count / total * 972)
        col = REGION_COLORS[name]
        d.rectangle([x, 116, x + w - 1, 142], fill=col)
        centre(d, x, x + w, 120, name, sans_b(9), (255, 255, 255))
        centre(d, x, x + w, 130, str(count), serif_b(14), (255, 255, 255))
        x += w


def draw_stats(d):
    centre(d, 26, 998, 144, "\u2014  THE DAY IN NUMBERS  \u2014",
           sans_b(10), TEAL)
    cell = 972 / 6
    for i, (num, lab1, lab2) in enumerate(STATS):
        x0 = 26 + i * cell
        if i:
            d.line([x0, 158, x0, 196], fill=HAIRLINE, width=1)
        centre(d, x0, x0 + cell, 156, num, serif_b(22), TEAL)
        centre(d, x0, x0 + cell, 182, lab1, sans_b(8), INK)
        centre(d, x0, x0 + cell, 192, lab2, sans(8), INK)


def draw_timeline(d):
    d.text((26, 202), "THE DAY IN UTC", font=sans_b(10), fill=TEAL)
    d.line([168, 218, 984, 218], fill=GOLD, width=2)
    for i, (time, text) in enumerate(TIMELINE):
        x = 196 + i * 104
        d.ellipse([x - 4, 214, x + 4, 222], fill=GOLD)
        centre(d, x - 50, x + 50, 202, time, sans_b(10), INK)
        lines = wrap(d, text, sans(8), 100)
        for j, line in enumerate(lines[:2]):
            centre(d, x - 50, x + 50, 226 + j * 10, line, sans(8), INK)


def draw_heroes(d, img):
    for i, (num, region, section, tag, head, body) in enumerate(HEROES):
        x = 26 + i * 327
        y, w, h = 258, 317, 168
        d.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=1)
        # Art is painted on its own layer so rays and shapes can never
        # bleed past the panel edge into the strips above.
        layer = Image.new("RGB", (w - 2, 66), TEAL_DARK)
        ld = ImageDraw.Draw(layer)
        HERO_ART[i](ld, 0, 0, w - 2, 66)
        img.paste(layer, (x + 1, y + 1))
        d.ellipse([x + 10, y + 10, x + 30, y + 30], fill=GOLD)
        centre(d, x + 10, x + 30, y + 15, str(num), sans_b(11),
               (255, 255, 255))
        d.text((x + 10, y + 74), region + " \u00b7 " + section,
               font=sans_b(9), fill=REGION_COLORS[region])
        tag_w = d.textlength(tag, font=sans_b(8)) + 12
        tag_chip(d, x + w - 10 - tag_w, y + 72, tag)
        lines, f = fit_block(d, head, serif_b, 15, w - 20, 3)
        for j, line in enumerate(lines):
            d.text((x + 10, y + 90 + j * 18), line, font=f, fill=INK)
        blines, bf = fit_block(d, body, sans, 10, w - 20, 2)
        for j, line in enumerate(blines):
            d.text((x + 10, y + 142 + j * 12), line, font=bf, fill=INK)


def draw_cards(d):
    for i, (num, region, section, tag, head, body) in enumerate(CARDS):
        col, row = i % 5, i // 5
        x = 26 + col * 196
        y = 434 + row * 88
        w, h = 188, 82
        colr = REGION_COLORS[region]
        d.rectangle([x, y, x + w, y + h], fill=CARD,
                    outline=(180, 160, 120), width=1)
        d.rectangle([x, y, x + w, y + 4], fill=colr)
        d.ellipse([x + 8, y + 12, x + 28, y + 32], fill=colr)
        centre(d, x + 8, x + 28, y + 17, str(num), sans_b(11),
               (255, 255, 255))
        d.text((x + 33, y + 12), region + " \u00b7 " + section,
               font=sans_b(8), fill=colr)
        tag_w = d.textlength(tag, font=sans_b(8)) + 12
        tag_chip(d, x + w - 6 - tag_w, y + 26, tag)
        lines, f = fit_block(d, head, serif_b, 11, w - 16, 2)
        for j, line in enumerate(lines):
            d.text((x + 8, y + 36 + j * 13), line, font=f, fill=INK)
        blines, bf = fit_block(d, body, sans, 9, w - 16, 2)
        for j, line in enumerate(blines):
            d.text((x + 8, y + 62 + j * 11), line, font=bf, fill=INK)


def draw_map(d, x0, y0, x1, y1):
    """Dotted world map with numbered pins for stories 1-13."""
    d.text((x0, y0), "WHERE IT HAPPENED", font=sans_b(11), fill=TEAL)
    d.text((x0, y0 + 14), "PINS MATCH STORY NUMBERS 1\u201313",
           font=sans(8), fill=INK)
    mx0, my0, mx1, my1 = x0 + 10, y0 + 34, x1 - 10, y1 - 6
    step = 2.4
    ny = 0.0
    while ny <= 70:
        nx = 0.0
        while nx <= 100:
            inside = any(
                ((nx - cx) / rx) ** 2 + ((ny - cy) / ry) ** 2 <= 1
                for cx, cy, rx, ry in LAND
            )
            if inside:
                px = mx0 + nx / 100 * (mx1 - mx0)
                py = my0 + ny / 70 * (my1 - my0)
                d.ellipse([px - 1.6, py - 1.6, px + 1.6, py + 1.6],
                          fill=MAP_DOT)
            nx += step
        ny += step
    for num, lon, lat, dx, dy in PINS:
        nx = (lon + 170) / 360 * 100
        ny = (83 - lat) / 143 * 70
        px = mx0 + nx / 100 * (mx1 - mx0)
        py = my0 + ny / 70 * (my1 - my0)
        qx = px + dx * (mx1 - mx0) / 100
        qy = py + dy * (my1 - my0) / 70
        if dx or dy:
            d.line([px, py, qx, qy], fill=RED, width=1)
        d.ellipse([qx - 7.5, qy - 7.5, qx + 7.5, qy + 7.5], fill=RED)
        centre(d, qx - 7.5, qx + 7.5, qy - 5, str(num), sans_b(9),
               (255, 255, 255))


def draw_briefs(d, x0, y0, x1, y1):
    d.text((x0, y0), "IN BRIEF \u2014 47 MORE STORIES OF THE DAY",
           font=sans_b(11), fill=TEAL)
    d.text((x0, y0 + 14), "EVERY ONE DATED TUESDAY 24 NOVEMBER 2026",
           font=sans(8), fill=INK)
    col_w = (x1 - x0 - 8) // 2
    top = y0 + 34
    row_h = (y1 - top) / 24
    for i, (num, region, text) in enumerate(BRIEFS):
        col = 0 if i < 24 else 1
        row = i if i < 24 else i - 24
        bx = x0 + col * (col_w + 8)
        by = top + row * row_h
        num_s = str(num) + "."
        d.text((bx, by), num_s, font=sans_b(9),
               fill=REGION_COLORS[region])
        nw = d.textlength(num_s, font=sans_b(9))
        fitted, f = fit_line(d, text, sans, 9, col_w - nw - 5, floor=8)
        d.text((bx + nw + 4, by), fitted, font=f, fill=INK)


def draw_date_check(d):
    x0, y0, x1, y1 = 26, 884, 998, 962
    d.rectangle([x0, y0, x1, y1], outline=RED, width=2)
    d.text((x0 + 10, y0 + 5), "DATE CHECK \u2014 READ THIS FIRST",
           font=sans_b(11), fill=RED)
    lines = wrap(d, DATE_CHECK, sans(9), x1 - x0 - 20)
    for j, line in enumerate(lines[:5]):
        d.text((x0 + 10, y0 + 22 + j * 11), line, font=sans(9), fill=INK)


def draw_footer(d):
    y = 970
    centre(d, 26, 998, y,
           "HOW TO READ THE TAGS \u2014 CONFIRMED: verified by two or more "
           "outlets \u00b7 REPORTED: carried by the day\u2019s wires \u00b7 CLAIM: "
           "one side\u2019s account, not independently confirmed",
           sans(9), INK)
    centre(d, 26, 998, y + 12,
           "SOURCES \u2014 dailysummaryof.com/world/2026-11-24 \u00b7 "
           "horizonapp.link \u00b7 Just Security Early Edition \u00b7 UEFA \u00b7 "
           "CAS \u00b7 Reuters \u00b7 Xinhua \u00b7 CoinDesk",
           sans(9), INK)
    centre(d, 26, 998, y + 24,
           "Every story here happened, or was first reported, on Tuesday "
           "24 November 2026. Wires read to 01:30 UTC, Wednesday 25 "
           "November 2026.",
           sans_b(9), TEAL)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, 1015, 1015], outline=GOLD, width=2)
    d.rectangle([12, 12, 1011, 1011], outline=HAIRLINE, width=1)
    draw_masthead(d)
    draw_dek(d)
    draw_continent_bar(d)
    draw_stats(d)
    draw_timeline(d)
    draw_heroes(d, img)
    draw_cards(d)
    draw_map(d, 26, 610, 336, 878)
    draw_briefs(d, 346, 610, 998, 878)
    draw_date_check(d)
    draw_footer(d)
    img.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
