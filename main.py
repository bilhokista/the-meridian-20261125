"""Draw The Meridian, a one-day illustrated front page."""

from math import ceil, cos, sin, sqrt, tau
import os
from pathlib import Path
import struct
import zlib


SIZE = 1024
PAPER = "f4ecda"
INK = "172d31"
MUTED = "4a5d59"
RUST = "a33e2a"
CREAM = "fff3d6"
GOLD = "efb85c"
TEAL = "26736f"
RULE = "b0aa96"

# Hand-set display alphabet, one five-bit mask per row.
GLYPHS = {
    "A": "0e11111f111111", "B": "1e11111e11111e", "C": "0f10101010100f",
    "D": "1e11111111111e", "E": "1f10101e10101f", "F": "1f10101e101010",
    "G": "0f10101711110f", "H": "1111111f111111", "I": "0e04040404040e",
    "J": "0702020212120c", "K": "11121418141211", "L": "1010101010101f",
    "M": "111b1515111111", "N": "11191915131311", "O": "0e11111111110e",
    "P": "1e11111e101010", "Q": "0e11111115120d", "R": "1e11111e141211",
    "S": "0f10100e01011e", "T": "1f040404040404", "U": "1111111111110e",
    "V": "11111111110a04", "W": "11111115151b11", "X": "11110a040a1111",
    "Y": "11110a04040404", "Z": "1f01020408101f", "0": "0e11131519110e",
    "1": "040c040404040e", "2": "0e11010204081f", "3": "1e01010601111e",
    "4": "02060a121f0202", "5": "1f10101e01011e", "6": "0618101e11110e",
    "7": "1f010204080808", "8": "0e11110e11110e", "9": "0e11110f01020c",
    " ": "00000000000000", "-": "0000000e000000", ".": "00000000000c0c",
    "/": "01010204081010", "'": "04040800000000", ":": "000c0c000c0c00",
    "%": "191a0204080b13", ",": "00000000000c08",
}


class Sheet:
    def __init__(self):
        self.pixels = bytearray(bytes.fromhex(PAPER) * (SIZE * SIZE))

    def span(self, x0, x1, y, ink):
        if not 0 <= y < SIZE:
            return
        lo, hi = max(0, x0), min(SIZE, x1)
        if lo < hi:
            start = (y * SIZE + lo) * 3
            self.pixels[start:start + (hi - lo) * 3] = ink * (hi - lo)

    def box(self, x, y, w, h, color):
        ink = bytes.fromhex(color)
        for row in range(max(0, y), min(SIZE, y + h)):
            self.span(x, x + w, row, ink)

    def disk(self, x, y, rx, ry, color):
        ink = bytes.fromhex(color)
        for row in range(ceil(y - ry), ceil(y + ry)):
            dx = rx * sqrt(max(0, 1 - ((row + .5 - y) / ry) ** 2))
            self.span(ceil(x - dx - .5), ceil(x + dx - .5), row, ink)

    def poly(self, color, *pts):
        ink = bytes.fromhex(color)
        edges = list(zip(pts, pts[1:] + pts[:1]))
        for row in range(ceil(min(y for _, y in pts)), ceil(max(y for _, y in pts))):
            k = row + .5
            cuts = sorted(a + (k - b) * (c - a) / (d - b)
                          for (a, b), (c, d) in edges if min(b, d) <= k < max(b, d))
            for l, r in zip(cuts[::2], cuts[1::2]):
                self.span(ceil(l - .5), ceil(r - .5), row, ink)

    def line(self, x, y, a, b, width, color):
        length = ((a - x) ** 2 + (b - y) ** 2) ** .5
        if length:
            u, v = (y - b) * width / (2 * length), (a - x) * width / (2 * length)
            self.poly(color, (x + u, y + v), (a + u, b + v),
                      (a - u, b - v), (x - u, y - v))

    def text(self, x, y, words, sx, sy, color=INK, tracking=None):
        gap = sx if tracking is None else tracking
        for char in words:
            for row, bits in enumerate(bytes.fromhex(GLYPHS[char])):
                for col in range(5):
                    if bits & (16 >> col):
                        self.box(x + sx * col, y + sy * row, sx, sy, color)
            x += sx * 5 + gap

    def lines(self, x, y, rows, sx, sy, leading, color=INK):
        for row in rows:
            self.text(x, y, row, sx, sy, color)
            y += leading

    def png(self):
        def chunk(tag, body):
            return (struct.pack(">I", len(body)) + tag + body
                    + struct.pack(">I", zlib.crc32(tag + body)))

        stride = 3 * SIZE
        scanlines = b"".join(b"\0" + self.pixels[i:i + stride]
                             for i in range(0, len(self.pixels), stride))
        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(scanlines, 9)) + chunk(b"IEND", b""))


def compass(p, x, y, radius):
    p.disk(x, y, radius, radius, INK)
    p.disk(x, y, radius - 2, radius - 2, PAPER)
    for i in range(4):
        angle = tau * i / 4
        u, v = cos(angle), sin(angle)
        p.poly(RUST if i % 2 == 0 else INK, (x + (radius - 5) * u, y + (radius - 5) * v),
               (x - 5 * v, y + 5 * u), (x + 5 * v, y - 5 * u))


def freighter(p):
    p.disk(823, 274, 97, 97, "b65b40")
    p.disk(823, 274, 79, 79, "df8b53")
    for y in range(243, 337, 10):
        dx = int(sqrt(79**2 - (y - 274)**2))
        p.box(823 - dx, y, 2 * dx, 2, "d07a48")
    p.poly("204449", (557, 379), (643, 367), (738, 379), (829, 370), (984, 365),
           (984, 443), (557, 443))
    for x, y, w in [(575, 401, 66), (631, 422, 100), (739, 413, 148),
                    (905, 398, 53), (841, 429, 106), (572, 433, 45)]:
        p.box(x, y, w, 2, "42807b")
    p.poly("0d2329", (594, 348), (629, 355), (955, 349), (917, 395), (635, 395))
    p.poly("b15037", (621, 379), (930, 379), (917, 395), (635, 395))
    p.poly(CREAM, (608, 358), (947, 358), (943, 363), (612, 363))
    p.box(631, 309, 45, 46, CREAM)
    p.box(626, 307, 56, 9, GOLD)
    p.box(645, 291, 22, 16, "0d2329")
    p.box(653, 276, 3, 17, CREAM)
    for x in range(636, 670, 11):
        p.box(x, 320, 7, 8, INK)
    for row, colors in enumerate([("df8b53", "529b8b", "c55c43", "eab966"),
                                  ("529b8b", "eab966", "df8b53"),
                                  ("c55c43", "eab966")]):
        for j, color in enumerate(colors):
            x, y = 684 + j * 60 + row * 21, 331 - row * 20
            p.box(x, y, 56, 17, color)
            for offset in range(5, 55, 8):
                p.box(x + offset, y + 3, 2, 11, "435952")


def orbit(p):
    x, y = 132, 587
    p.disk(x, y, 78, 78, "153a43")
    for a, b in [(90, 543), (151, 529), (172, 548), (78, 610), (182, 620), (114, 652)]:
        p.box(a, b, 3, 3, GOLD)
    p.disk(132, 594, 44, 44, "32948b")
    p.poly("84bd9f", (95, 578), (113, 559), (129, 553), (135, 570), (155, 573),
           (150, 589), (134, 598), (123, 592), (114, 608), (105, 602))
    p.poly("84bd9f", (150, 605), (166, 592), (174, 600), (167, 616), (151, 632), (144, 619))
    pts = [(x + 67 * cos(t) + 5 * sin(t), y - 43 * cos(t) + 23 * sin(t))
           for t in (i * tau / 96 for i in range(97))]
    for a, b in zip(pts, pts[1:]):
        p.line(*a, *b, 2, CREAM)
    p.disk(183, 560, 7, 7, GOLD)
    p.line(176, 546, 191, 573, 3, CREAM)
    p.line(169, 551, 182, 544, 5, "84bd9f")
    p.line(185, 576, 198, 569, 5, "84bd9f")


def treaty(p):
    p.disk(614, 587, 78, 78, "d2cfac")
    for x, y, r in [(567, 552, 9), (575, 565, 5), (657, 588, 8), (671, 595, 4), (650, 608, 5)]:
        p.disk(x, y, r, r - 2, "83978a")
    p.poly("375a54", (573, 557), (636, 551), (656, 627), (581, 639))
    p.poly(CREAM, (581, 546), (635, 546), (648, 620), (586, 630))
    for y, w in [(562, 35), (573, 43), (583, 30)]:
        p.line(592, y, 592 + w, y - 2, 3, "83978a")
    p.disk(612, 608, 9, 9, RUST)
    p.poly("183e43", (621, 601), (660, 550), (669, 557), (629, 606), (618, 611))
    p.line(628, 597, 662, 555, 2, GOLD)


def brief_art(p, x, y, kind):
    if kind == "court":
        p.poly("d1a56a", (x + 3, y + 30), (x + 37, y + 9), (x + 71, y + 30))
        for i in range(4):
            p.box(x + 11 + 15 * i, y + 34, 8, 23, INK)
        p.box(x + 5, y + 60, 64, 5, RUST)
    elif kind == "wave":
        p.poly(TEAL, (x + 1, y + 63), (x + 7, y + 45), (x + 16, y + 30),
               (x + 29, y + 21), (x + 44, y + 19), (x + 55, y + 24), (x + 60, y + 34),
               (x + 49, y + 32), (x + 39, y + 40), (x + 41, y + 48), (x + 56, y + 54),
               (x + 72, y + 52), (x + 72, y + 65))
        p.line(x + 3, y + 66, x + 72, y + 66, 3, INK)
    else:
        p.poly("926149", (x + 1, y + 60), (x + 20, y + 26), (x + 34, y + 20),
               (x + 44, y + 27), (x + 56, y + 18), (x + 73, y + 60))
        p.disk(x + 39, y + 54, 16, 14, INK)
        p.box(x + 23, y + 54, 32, 10, INK)
        p.box(x + 3, y + 62, 69, 5, TEAL)


def front_page(p):
    p.box(40, 34, 944, 5, INK)
    compass(p, 66, 82, 24)
    p.text(106, 55, "THE MERIDIAN", 7, 7)
    p.text(742, 54, "WORLD EDITION", 3, 3, RUST)
    p.text(625, 88, "WED 25 NOVEMBER 2026", 3, 3)
    p.box(40, 122, 944, 2, RULE)

    p.box(40, 144, 944, 299, INK)
    p.box(40, 144, 944, 5, RUST)
    freighter(p)
    p.text(65, 174, "01 / UNITED STATES", 3, 3, GOLD)
    p.lines(65, 215, ("US PREPARES", "NEW TARIFFS"), 7, 8, 69, CREAM)
    p.lines(65, 366, ("AT LEAST 14 JURISDICTIONS", "COULD FACE NEW IMPORT TAXES"),
            3, 3, 27, CREAM)

    p.box(509, 465, 2, 240, RULE)
    p.text(40, 468, "02 / PAKISTAN", 3, 3, RUST)
    p.text(532, 468, "03 / PACIFIC", 3, 3, RUST)
    orbit(p)
    treaty(p)
    p.lines(220, 525, ("PAKISTAN'S", "FIRST ASTRONAUT", "REACHES ORBIT"), 3, 5, 42)
    p.lines(40, 673, ("ZEESHAN ALI DOCKS AT", "CHINA'S TIANGONG STATION"), 3, 3, 25, MUTED)
    p.lines(700, 525, ("SOLOMON ISLANDS", "SIGNS PACT WITH", "AUSTRALIA"), 3, 5, 42)
    p.lines(532, 673, ("CHINA PACT REPORTEDLY", "WILL NOT BE RENEWED"), 3, 3, 25, MUTED)

    p.box(40, 733, 944, 3, INK)
    p.box(351, 753, 2, 201, RULE)
    p.box(671, 753, 2, 201, RULE)
    briefs = [
        (40, "04 / SOUTH AFRICA", "court", ("RAMAPHOSA", "WINS IN COURT"),
         ("JUDGES SET ASIDE", "IMPEACHMENT REPORT")),
        (367, "05 / PERU", "wave", ("SWELLS CLOSE", "DOZENS OF PORTS"),
         ("POWERFUL WAVES", "DAMAGE THE COAST")),
        (688, "06 / INDONESIA", "mine", ("FLOODED MINE", "SEARCH ON"),
         ("WEST JAVA GOLD MINE:", "26 STILL TO EVACUATE")),
    ]
    for x, label, art, title, deck in briefs:
        p.text(x, 754, label, 2, 3, RUST)
        brief_art(p, x + 216, 742, art)
        p.lines(x, 813, title, 3, 4, 34)
        p.lines(x, 899, deck, 2, 3, 25, MUTED)
    p.box(40, 967, 944, 2, INK)
    p.text(40, 981, "ILLUSTRATED WORLD NEWS", 2, 2, MUTED)
    p.text(706, 981, "BBC / AL JAZEERA / REUTERS / AFP", 1, 2, MUTED, tracking=3)


def main():
    sheet = Sheet()
    front_page(sheet)
    out = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "entry.png").write_bytes(sheet.png())


if __name__ == "__main__":
    main()
