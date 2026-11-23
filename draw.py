#!/usr/bin/env python3
"""Draw the news-image-20261123 entry: a one-page newspaper front page that
sums up the world news of Monday 23 November 2026.

Run locally (PIL is only needed here, at build time):  python3 draw.py
The graded program is main.py, which only copies the finished entry.png;
the grader runs standard library only, so no drawing happens at grade time.

Stories (from the 23 November research): the US-Iran confrontation moves
to the sea with tankers struck near the Strait of Hormuz; Ukrainian sea
drones hit the Russian corvette Merkury off Benghazi; the day after COP31
collapsed in Antalya, governments trade blame; the market sell-off
deepens (KOSPI -4%, gold near $3,603); a factory fire in Cikande kills
24; Lahore's air-quality index hits 538; a South Korean minister resigns.
Also today: Shuri Castle's rebuilt main hall opens, thousands march in
Lisbon, Liverpool v Manchester United, Russia's new Dymer drone.
"""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (247, 242, 231)
INK = (28, 28, 28)
FAINT = (110, 104, 92)
RED = (179, 39, 30)
NAVY = (31, 58, 95)
TEAL = (20, 101, 90)
OCHRE = (176, 116, 28)
PLUM = (107, 58, 91)
RULE = (190, 182, 166)
WHITE = (255, 255, 255)
SEA = (214, 228, 240)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANSB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, width):
    """Greedy word wrap returning a list of lines that fit `width` px."""
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            trial = (cur + " " + w).strip()
            if draw.textlength(trial, font=fnt) <= width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


def para(draw, xy, text, fnt, width, fill=INK, leading=None):
    x, y = xy
    lh = leading or int(fnt.size * 1.32)
    for line in wrap(draw, text, fnt, width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += lh
    return y


def chip(draw, xy, text, bg):
    x, y = xy
    fnt = font(SANSB, 17)
    tw = draw.textlength(text, font=fnt)
    pad, h = 10, 26
    draw.rounded_rectangle([x, y, x + tw + 2 * pad, y + h], radius=4, fill=bg)
    draw.text((x + pad, y + 4), text, font=fnt, fill=WHITE)
    return tw + 2 * pad


def starburst(draw, cx, cy, r, color):
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=color)


def tanker(draw, cx, cy):
    """A tanker on the sea, struck: smoke rising, red burst at the bow."""
    # sea
    draw.ellipse([cx - 118, cy + 18, cx + 118, cy + 78], fill=SEA,
                 outline=NAVY, width=3)
    for k, w in ((-0.45, 3), (0.0, 3), (0.45, 3)):
        draw.arc([cx - 118, cy + 18 + k * 30, cx + 118, cy + 78 + k * 30],
                 200, 340, fill=NAVY, width=w)
    # hull
    draw.polygon([(cx - 105, cy - 8), (cx + 105, cy - 8),
                  (cx + 88, cy + 22), (cx - 88, cy + 22)], fill=RED)
    draw.rectangle([cx - 105, cy - 8, cx + 105, cy + 2], fill=(140, 28, 22))
    # containers
    for i, col in enumerate((NAVY, TEAL, OCHRE)):
        x0 = cx - 78 + i * 46
        draw.rectangle([x0, cy - 44, x0 + 40, cy - 8], fill=col,
                       outline=INK, width=2)
    # bridge tower + funnel
    draw.rectangle([cx + 62, cy - 52, cx + 100, cy - 8], fill=WHITE,
                   outline=INK, width=2)
    draw.rectangle([cx + 68, cy - 46, cx + 94, cy - 34], fill=NAVY)
    draw.rectangle([cx - 100, cy - 30, cx - 84, cy - 8], fill=INK)
    # smoke rising from the strike at the bow
    for (sx, sy, r) in ((cx - 96, cy - 74, 10), (cx - 102, cy - 92, 13),
                        (cx - 108, cy - 110, 16)):
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(120, 116, 108))
    # red burst where the strike hit
    starburst(draw, cx - 92, cy - 46, 26, RED)
    starburst(draw, cx - 92, cy - 46, 13, (255, 196, 66))


def story(draw, x, y, w, kicker, color, headline, body):
    """One column story. Returns the y just below the body text."""
    chip(draw, (x, y), kicker, color)
    y += 36
    y = para(draw, (x, y), headline, font(SANSB, 26), w, leading=31)
    y += 6
    y = para(draw, (x, y), body, font(SANS, 17), w, leading=22)
    return y


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    m = 36  # margin

    # ---- masthead ----
    d.text((W // 2, 24), "THE WORLD IN ONE PAGE", font=font(SERIF, 56),
           fill=INK, anchor="ma")
    d.line([m, 96, W - m, 96], fill=RED, width=5)
    d.text((m, 106), "MONDAY  ·  23 NOVEMBER 2026", font=font(SANSB, 22), fill=INK)
    d.text((W - m, 106), "ONE DAY — ONE IMAGE", font=font(SANSB, 22),
           fill=FAINT, anchor="ra")
    d.line([m, 140, W - m, 140], fill=INK, width=2)

    # ---- lead story: war at sea ----
    y = 156
    chip(d, (m, y), "CONFLICT  ·  STRAIT OF HORMUZ", RED)
    d.text((m, y + 36), "WAR AT SEA:", font=font(SERIF, 54), fill=INK)
    d.text((m, y + 100), "TANKERS HIT", font=font(SERIF, 54), fill=INK)
    dek = ("Tankers are struck near the Strait of Hormuz as the confrontation "
           "between the United States and Iran moves to the sea, a day after "
           "Iranian missiles hit US bases in Bahrain.")
    para(d, (m, y + 168), dek, font(SANS, 21), 600, leading=27)
    tanker(d, 830, y + 115)
    d.text((830, y + 218), "THE GULF CONFLICT SPREADS", font=font(SANSB, 15),
           fill=FAINT, anchor="ma")
    d.line([m, 418, W - m, 418], fill=RULE, width=2)

    # ---- rows of three, laid out from measured story bottoms ----
    col_w = 304
    xs = [m, m + col_w + 20, m + 2 * (col_w + 20)]
    y2 = 436
    ends = []
    ends.append(story(d, xs[0], y2, col_w, "UKRAINE · BENGHAZI", NAVY,
                      "Sea drones hit Russian corvette off Libya",
                      "Ukrainian sea drones strike the Russian corvette "
                      "Merkury off Benghazi, Libya."))
    ends.append(story(d, xs[1], y2, col_w, "CLIMATE · ANTALYA", TEAL,
                      "After COP31 fails, the blame game begins",
                      "A day after the UN climate summit ended with no deal, "
                      "governments trade blame over a final draft that made "
                      "no mention of fossil fuels."))
    ends.append(story(d, xs[2], y2, col_w, "MARKETS", RED,
                      "Sell-off deepens; gold nears record",
                      "South Korea's KOSPI falls 4% as the AI sell-off "
                      "spreads, while gold holds near $3,603 an ounce."))
    div2 = max(ends) + 12
    d.line([m, div2, W - m, div2], fill=RULE, width=2)

    y3 = div2 + 14
    ends = []
    ends.append(story(d, xs[0], y3, col_w, "INDONESIA · CIKANDE", RED,
                      "Factory fire kills 24 near Jakarta",
                      "A fire at a factory in Cikande kills 24 people."))
    ends.append(story(d, xs[1], y3, col_w, "ASIA · LAHORE", OCHRE,
                      "Lahore chokes as air index hits 538",
                      "Pakistan's second city records an air-quality index "
                      "of 538, deep in the hazardous range, as smog "
                      "blankets Punjab."))
    ends.append(story(d, xs[2], y3, col_w, "SOUTH KOREA · SEOUL", NAVY,
                      "Minister quits in Seoul",
                      "A South Korean minister resigns from the cabinet on "
                      "Monday."))
    div3 = max(ends) + 12
    d.line([m, div3, W - m, div3], fill=INK, width=2)

    # ---- also today ----
    ay = div3 + 12
    d.text((m, ay), "ALSO TODAY", font=font(SANSB, 18), fill=RED)
    also = ("Shuri Castle's rebuilt main hall opens in Okinawa  ·  Thousands "
            "march in Lisbon  ·  Liverpool v Manchester United in the Premier "
            "League  ·  Russia's new Dymer drone draws attention")
    para(d, (m + 152, ay), also, font(SANS, 17), W - m - 152 - m, leading=22)
    d.text((W // 2, 998),
           "Summarised from Reuters, AP, AFP, Al Jazeera and Euronews  ·  "
           "All events of Monday 23 November 2026",
           font=font(SANS, 12), fill=FAINT, anchor="ma")

    img.save("entry.png", optimize=True)
    print("wrote entry.png", img.size)


if __name__ == "__main__":
    main()
