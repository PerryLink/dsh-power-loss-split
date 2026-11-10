#!/usr/bin/env python3
"""Generate the README visuals for dsh-power-loss-split.

Outputs (all under docs/assets/, idempotent overwrite):

  dsh-power-loss-split-hero-zh-light.webp  1440x576  Pillow poster
  dsh-power-loss-split-hero-zh-dark.webp
  dsh-power-loss-split-hero-en-light.webp
  dsh-power-loss-split-hero-en-dark.webp
  dsh-power-loss-split-flow-v5-light.svg   1100x660  hand-written SVG
  dsh-power-loss-split-flow-v5-dark.svg

Hero -- "two rulers over one metering period".
  The right panel is the quickstart sample, not a decoration:
  samples/quickstart/input/PL-001-unsafe.json carries supplied 120000,
  sold 114000, loss 5500, lossRate 5, so PL-001 compares the declared
  5500 kWh with the derived 120000 - 114000 = 6000 kWh (gap 500 kWh,
  toleranceKwh 0) and PL-002 compares the declared 5% with
  5500 / 120000 * 100 = 4.5833% (gap 0.4167 points, tolerancePoints
  0.01, so the axis is zoomed to 4.0-5.5% to make the tolerance band
  visible). The three skipped entries below are the same run: maxRate
  is unset, the material has no meter rows, and no A/B/C phases exist.
  Every number comes from that fixture and matches
  samples/quickstart/expected/result.json (2 issues, 3 skipped).

Flow -- grammar: a SPLIT SWITCHBOARD, not a row of five boxes.
  One material bus feeds five parallel rule switches (PL-001..PL-005);
  each switch has two contacts and one realized route for this period.
  The two collector rails are issues[] (found / expected / fix / basis)
  and skipped[] (rule + reason, including rules that ran with no gap).
  Both rails end in one view: summary, issueCount, skippedCount,
  markdown, reportJson. The SVG is language-neutral (English + code
  tokens) so the same light/dark pair serves all five README languages.

Run once:  python scripts/gen-readme-assets.py
Requires:  Pillow (hero raster) + the Microsoft YaHei / Consolas fonts
           that ship with Windows; the SVG is plain text.
"""
from __future__ import annotations

import math
import os
import re
import sys
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")

# ---------------------------------------------------------------------------
# fonts
# ---------------------------------------------------------------------------
FONT_CANDIDATES = {
    "sans": [r"C:\Windows\Fonts\msyh.ttc",
             "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
             "/System/Library/Fonts/PingFang.ttc"],
    "sans_bold": [r"C:\Windows\Fonts\msyhbd.ttc",
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                  "/System/Library/Fonts/PingFang.ttc"],
    "mono": [r"C:\Windows\Fonts\consola.ttf",
             r"C:\Windows\Fonts\cour.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
             "/System/Library/Fonts/Menlo.ttc"],
}
FONT_PATH = {}
for _key, _paths in FONT_CANDIDATES.items():
    _found = next((p for p in _paths if os.path.exists(p)), None)
    if _found is None:
        sys.exit(f"FATAL: no font for {_key!r}; looked for {_paths}. "
                 "Refusing to render tofu boxes.")
    FONT_PATH[_key] = _found

_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
CJK = re.compile(r"[\u2e80-\u9fff\uf900-\ufaff\uff00-\uffef]")


def font(size: int, kind: str = "sans") -> ImageFont.FreeTypeFont:
    key = (kind, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(FONT_PATH[kind], size, index=0)
    return _cache[key]


_measure_draw = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def text_width(text: str, size: float, bold: bool = False,
               mono: bool = False) -> float:
    kind = "mono" if mono else ("sans_bold" if bold else "sans")
    return _measure_draw.textlength(text, font=font(round(size), kind))


def assert_fit(text: str, size: float, limit: float, *, bold=False, mono=False,
               where: str = "") -> float:
    """Fail loudly instead of shipping a clipped / overflowing label."""
    if mono and CJK.search(text):
        raise SystemExit(f"FATAL: CJK inside a mono label in "
                         f"{where or '?'}: {text!r}")
    width = text_width(text, size, bold, mono)
    if width > limit:
        raise SystemExit(
            f"FATAL: text overflows in {where or '?'} "
            f"({width:.0f}px > {limit:.0f}px at {size}px): {text!r}")
    return width


def fit_size(text: str, limit: float, start: float, floor: float, *,
             bold=False, mono=False) -> float:
    size = float(start)
    while size > floor and text_width(text, size, bold, mono) > limit:
        size -= 0.5
    if text_width(text, size, bold, mono) > limit:
        raise SystemExit(f"FATAL: cannot fit {text!r} into {limit}px "
                         f"(floor {floor}px)")
    return size


# ---------------------------------------------------------------------------
# palette -- family accent + the two page backgrounds the READMEs use
# ---------------------------------------------------------------------------
THEMES = {
    "light": dict(
        bg_top=(249, 246, 253), bg_bottom=(228, 234, 248),
        ink=(23, 28, 44), ink2=(64, 76, 102), muted=(100, 112, 138),
        faint=(142, 152, 176),
        surface=(255, 255, 255), surface_alt=(245, 248, 254),
        border=(208, 216, 236), grid=(226, 231, 243), track=(235, 239, 249),
        family=(75, 103, 180), family_soft=(232, 238, 252),
        warn=(168, 112, 24), warn_soft=(250, 240, 222),
        hot=(186, 66, 44), hot_soft=(252, 232, 226),
        info=(52, 92, 184), info_soft=(232, 238, 252),
        violet=(102, 76, 184), violet_soft=(240, 236, 252),
        ok=(26, 130, 92), ok_soft=(228, 244, 238),
        shadow=(38, 50, 92),
    ),
    "dark": dict(
        bg_top=(19, 26, 42), bg_bottom=(12, 16, 22),
        ink=(238, 242, 255), ink2=(178, 189, 214), muted=(146, 158, 186),
        faint=(112, 124, 152),
        surface=(23, 31, 48), surface_alt=(19, 26, 41),
        border=(43, 54, 82), grid=(35, 45, 68), track=(30, 39, 58),
        family=(132, 150, 245), family_soft=(35, 45, 74),
        warn=(226, 179, 74), warn_soft=(46, 40, 26),
        hot=(240, 138, 93), hot_soft=(52, 32, 28),
        info=(122, 162, 247), info_soft=(30, 42, 70),
        violet=(180, 158, 246), violet_soft=(40, 34, 62),
        ok=(84, 214, 165), ok_soft=(26, 48, 44),
        shadow=(0, 0, 0),
    ),
}


def mix(rgb, other, ratio):
    return tuple(round(rgb[i] + (other[i] - rgb[i]) * ratio) for i in range(3))


def over(rgb, theme, alpha):
    """Flatten `rgb` against the theme surface for alpha-style fills."""
    return mix(theme["surface"], rgb, alpha)


def hexs(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def col(value):
    """SVG colour: hex for RGB tuples, pass literal strings through."""
    return hexs(value) if isinstance(value, (tuple, list)) else value


# ---------------------------------------------------------------------------
# drawing surface with supersampling
# ---------------------------------------------------------------------------
class Sheet:
    """2x supersampled RGBA canvas; every coordinate is in final pixels."""

    def __init__(self, width: int, height: int, theme: dict, ss: int = 2):
        self.w, self.h, self.ss, self.t = width, height, ss, theme
        base = Image.new("RGB", (1, 2))
        base.putpixel((0, 0), theme["bg_top"])
        base.putpixel((0, 1), theme["bg_bottom"])
        self.img = base.resize((width * ss, height * ss),
                               Image.BILINEAR).convert("RGBA")
        self.d = ImageDraw.Draw(self.img)

    def _box(self, box):
        s = self.ss
        return [round(v * s) for v in box]

    def rounded(self, box, radius, fill=None, outline=None, width=1,
                corners=None):
        self.d.rounded_rectangle(self._box(box), radius=radius * self.ss,
                                 fill=fill, outline=outline,
                                 width=max(1, round(width * self.ss)),
                                 corners=corners)

    def rect(self, box, fill=None, outline=None, width=1):
        self.d.rectangle(self._box(box), fill=fill, outline=outline,
                         width=max(1, round(width * self.ss)))

    def line(self, xy, fill, width=1):
        s = self.ss
        self.d.line([(round(xy[0] * s), round(xy[1] * s)),
                     (round(xy[2] * s), round(xy[3] * s))],
                    fill=fill, width=max(1, round(width * s)))

    def dashed_line(self, x1, y1, x2, y2, fill, width=1.5, dash=5, gap=4):
        length = math.hypot(x2 - x1, y2 - y1)
        if length <= 0:
            return
        ux, uy = (x2 - x1) / length, (y2 - y1) / length
        pos = 0.0
        while pos < length:
            end = min(pos + dash, length)
            self.line((x1 + ux * pos, y1 + uy * pos,
                       x1 + ux * end, y1 + uy * end), fill, width)
            pos += dash + gap

    def dot(self, cx, cy, r, fill):
        s = self.ss
        self.d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s,
                        (cy + r) * s], fill=fill)

    def text(self, xy, s, size, fill, *, bold=False, mono=False, anchor="ls"):
        if mono and CJK.search(s):
            raise SystemExit(f"FATAL: CJK inside a mono label: {s!r}")
        kind = "mono" if mono else ("sans_bold" if bold else "sans")
        self.d.text((xy[0] * self.ss, xy[1] * self.ss), s,
                    font=font(round(size * self.ss), kind),
                    fill=fill, anchor=anchor)

    def shadow(self, box, radius, dy=14, blur=26, alpha=34):
        s = self.ss
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        b = self._box((box[0], box[1] + dy, box[2], box[3] + dy))
        ld.rounded_rectangle(b, radius=radius * s,
                             fill=self.t["shadow"] + (alpha,))
        layer = layer.filter(ImageFilter.GaussianBlur(blur * s))
        self.img.alpha_composite(layer)
        self.d = ImageDraw.Draw(self.img)

    def save(self, path):
        out = self.img.resize((self.w, self.h), Image.LANCZOS)
        out.convert("RGB").save(path, "WEBP", quality=94, method=6)


# ---------------------------------------------------------------------------
# hero content -- every number below is the quickstart fixture
# ---------------------------------------------------------------------------
HERO_W, HERO_H = 1440, 576

HERO_COPY = {
    "zh": dict(
        kicker="PLUGIN · 线损核算",
        title="线损核对",
        value=("把供电量、售电量、线损电量与线损率一次核清",
               "哪一条对不上、差多少、该改什么，逐条写清楚"),
        sub="量平衡 · 线损率 · 计量点合计 · 三相不平衡度 · 5 条规则",
        meta="纯主机端 · 无网络 · 不调用模型 · 阈值未配置即跳过",
        footer="dsh-power-loss-split · Apache-2.0 · DSH ≥0.2.1 <0.3.0",
        panel_title="一个抄表周期，两把尺子",
        panel_meta="samples/quickstart · PL-001-unsafe",
        r1_label="PL-001 · 线损电量（kWh）",
        r1_formula="120 000 − 114 000 = 6 000",
        r1_fill="填报 5 500 kWh",
        r1_derived="推算 6 000",
        r1_note="推算 6 000 − 填报 5 500 = 差 500 kWh · 容差 toleranceKwh = 0",
        r2_label="PL-002 · 线损率",
        r2_formula="5 500 ÷ 120 000 × 100 = 4.5833",
        r2_note="推算 4.5833% · 填报 5% · 差 0.4167 个百分点 · 容差 ±0.01",
        issues_head="issues[] · 2 条 warn",
        skipped_head="skipped[] · 3 条",
        issue_chips=("PL-001 warn · 差 500 kWh", "PL-002 warn · 差 0.4167 pt"),
        skip_chips=("PL-003 · maxRate 未配置",
                    "PL-004 · 无带电量计量点",
                    "PL-005 · 无 A/B/C 相"),
        footer1="summary{error 0 · warn 2 · info 0} · issueCount 2 · "
                "skippedCount 3",
        footer2="空的问题列表不等于什么都没查：未配置、缺项、相别不足都写进 skipped",
    ),
    "en": dict(
        kicker="PLUGIN · LINE-LOSS AUDIT",
        title="Line-loss split",
        value=("Reconcile supplied, sold, loss and loss rate",
               "which figure is off, by how much, what to fix"),
        sub="5 rules · every finding carries its arithmetic",
        meta="local · no network · no model call · unset = skipped",
        footer="dsh-power-loss-split · Apache-2.0 · DSH ≥0.2.1 <0.3.0",
        panel_title="One period, two rulers",
        panel_meta="samples/quickstart · PL-001-unsafe",
        r1_label="PL-001 · loss energy (kWh)",
        r1_formula="120 000 − 114 000 = 6 000",
        r1_fill="declared 5 500 kWh",
        r1_derived="derived 6 000",
        r1_note="derived 6 000 − declared 5 500 = gap 500 kWh · tol 0",
        r2_label="PL-002 · loss rate",
        r2_formula="5 500 ÷ 120 000 × 100 = 4.5833",
        r2_note="derived 4.5833% · declared 5% · gap 0.4167 pt · tol ±0.01",
        issues_head="issues[] · 2 warn",
        skipped_head="skipped[] · 3",
        issue_chips=("PL-001 warn · gap 500 kWh",
                     "PL-002 warn · gap 0.4167 pt"),
        skip_chips=("PL-003 · maxRate unset",
                    "PL-004 · no meter energy",
                    "PL-005 · no A/B/C phases"),
        footer1="summary{error 0 · warn 2 · info 0} · issueCount 2 · "
                "skippedCount 3",
        footer2="an empty issue list is not proof that every check ran",
    ),
}

# hero geometry (final pixels)
LX = 72                       # left column x
PANEL = (744, 64, 1408, 520)  # right panel box
PANEL_X0, PANEL_Y0, PANEL_X1, PANEL_Y1 = PANEL
IL, IR = 772, 1380            # panel inner left / right
R1_MIN, R1_MAX = 0.0, 6200.0  # kWh axis (derived 6000 stays off the border)
R2_MIN, R2_MAX = 4.0, 5.5     # % axis, zoomed so the tolerance band is visible


def hero(lang: str, theme_name: str) -> Sheet:
    c = HERO_COPY[lang]
    t = THEMES[theme_name]
    light = theme_name == "light"
    s = Sheet(HERO_W, HERO_H, t)

    # ---- left column: kicker / title / two value lines / sub / meta ------
    pill = c["kicker"]
    psize = fit_size(pill, 330, 17, 14, bold=True)
    pw = text_width(pill, psize, bold=True) + 54
    s.rounded((LX, 74, LX + pw, 116), 21,
              fill=over(t["family"], t, 0.10),
              outline=over(t["family"], t, 0.40), width=1.2)
    s.dot(LX + 23, 95, 3.6, t["family"])
    s.text((LX + 38, 95), pill, psize, t["family"], bold=True, anchor="lm")

    assert_fit(c["title"], 88, 640, bold=True, where="hero title")
    s.text((LX, 232), c["title"], 88, t["ink"], bold=True)

    v1, v2 = c["value"]
    assert_fit(v1, 27, 628, where="hero value 1")
    assert_fit(v2, 27, 628, where="hero value 2")
    s.text((LX, 288), v1, 27, t["ink2"])
    s.text((LX, 326), v2, 27, t["ink2"])

    assert_fit(c["sub"], 25, 628, where="hero subtitle")
    s.text((LX, 378), c["sub"], 25, t["muted"])

    s.line((LX, 412, LX + 560, 412), over(t["border"], t, 0.95), width=1.2)
    assert_fit(c["meta"], 20, 628, where="hero meta")
    s.text((LX, 452), c["meta"], 20, t["faint"])

    s.line((LX, 508, LX + 560, 508), over(t["border"], t, 0.95), width=1.2)
    assert_fit(c["footer"], 15.5, 628, where="hero footer")
    s.text((LX, 536), c["footer"], 15.5, t["faint"])

    # ---- right panel ------------------------------------------------------
    s.shadow(PANEL, 22, dy=16, blur=28, alpha=40 if light else 120)
    s.rounded(PANEL, 22, fill=t["surface"],
              outline=over(t["border"], t, 0.95), width=1.4)
    il, ir = IL, IR

    # header
    psize = fit_size(c["panel_title"], 330, 18.5, 15, bold=True)
    s.text((il, 102), c["panel_title"], psize, t["ink"], bold=True)
    assert_fit(c["panel_meta"], 12.5, 300, mono=True, where="panel meta")
    s.text((ir, 102), c["panel_meta"], 12.5, t["muted"], mono=True,
           anchor="rs")
    s.line((il, 116, ir, 116), over(t["border"], t, 0.9), width=1.1)

    def xr1(value: float) -> float:
        return il + (value - R1_MIN) / (R1_MAX - R1_MIN) * (ir - il)

    def xr2(value: float) -> float:
        return il + (value - R2_MIN) / (R2_MAX - R2_MIN) * (ir - il)

    # ---- ruler 1: declared loss energy vs derived loss energy ------------
    assert_fit(c["r1_label"], 14, 320, bold=True, where="r1 label")
    s.text((il, 144), c["r1_label"], 14, t["ink"], bold=True)
    assert_fit(c["r1_formula"], 12.5, 320, mono=True, where="r1 formula")
    s.text((ir, 144), c["r1_formula"], 12.5, t["muted"], mono=True,
           anchor="rs")

    bar_top, bar_bot = 158, 186
    s.rounded((il, bar_top, ir, bar_bot), 10, fill=t["track"])
    gap_fill = over(t["hot"], t, 0.22)
    s.rect((xr1(5500), bar_top, xr1(6000), bar_bot), fill=gap_fill)
    s.rounded((il, bar_top, xr1(5500), bar_bot), 10, fill=t["family"],
              corners=(True, False, False, True))
    s.dashed_line(xr1(6000), bar_top - 7, xr1(6000), bar_bot + 7,
                  over(t["hot"], t, 0.90), width=1.6, dash=4, gap=3)
    s.dot(xr1(6000), (bar_top + bar_bot) / 2, 4.2, t["hot"])
    s.text((xr1(5500) - 12, 178), c["r1_fill"], 11.5, (255, 255, 255),
           bold=True, anchor="rs")

    s.line((il, 192, ir, 192), over(t["grid"], t, 0.95), width=1)
    for value in (0, 2000, 4000, 6000):
        x = xr1(value)
        s.line((x, 192, x, 197), over(t["muted"], t, 0.60), width=1)
        if value == 6000:
            # mark the derived figure, not just the axis end
            s.text((x, 208), c["r1_derived"], 10.5, t["hot"], anchor="ms")
        else:
            label = f"{value:,}".replace(",", " ")
            anchor = "ls" if value == 0 else "ms"
            s.text((x, 208), label, 11, t["faint"], mono=True, anchor=anchor)

    assert_fit(c["r1_note"], 11.5, 608, where="r1 note")
    s.text((il, 228), c["r1_note"], 11.5, t["ink2"])

    # ---- ruler 2: declared rate vs derived rate, tolerance band ----------
    assert_fit(c["r2_label"], 14, 320, bold=True, where="r2 label")
    s.text((il, 252), c["r2_label"], 14, t["ink"], bold=True)
    assert_fit(c["r2_formula"], 12.5, 320, mono=True, where="r2 formula")
    s.text((ir, 252), c["r2_formula"], 12.5, t["muted"], mono=True,
           anchor="rs")

    # a gauge, not a second bar: a rate is a position on a scale, not volume
    axis_y = 280
    s.line((il, axis_y, ir, axis_y), over(t["border"], t, 1.0), width=2.6)
    for value, label in ((4.0, "4.0"), (4.5, "4.5"), (5.0, "5.0"),
                         (5.5, "5.5")):
        x = xr2(value)
        s.line((x, axis_y - 4, x, axis_y + 6), over(t["muted"], t, 0.55),
               width=1.2)
        anchor = "ls" if value == 4.0 else ("rs" if value == 5.5 else "ms")
        s.text((x, 302), label, 11, t["faint"], mono=True, anchor=anchor)

    # tolerance band around the derived rate (4.5833 ± 0.01 -> ~8 px wide)
    band0, band1 = xr2(4.5833 - 0.01), xr2(4.5833 + 0.01)
    s.rounded((band0, axis_y - 14, band1, axis_y + 14), 4,
              fill=over(t["violet"], t, 0.30),
              outline=over(t["violet"], t, 0.75), width=1.2)
    s.text((band1 + 14, 258), "±0.01", 9.8, t["violet"])
    # declared marker
    s.line((xr2(5.0), axis_y - 14, xr2(5.0), axis_y + 14),
           over(t["hot"], t, 0.95), width=2.2)
    s.dot(xr2(5.0), axis_y, 3.6, t["hot"])
    # derived marker, ringed so it reads through the tolerance band
    s.dot(xr2(4.5833), axis_y, 6.2, over(t["family"], t, 0.20))
    s.dot(xr2(4.5833), axis_y, 4.0, t["family"])

    assert_fit(c["r2_note"], 11.5, 608, where="r2 note")
    s.text((il, 324), c["r2_note"], 11.5, t["ink2"])

    s.line((il, 348, ir, 348), over(t["border"], t, 0.9), width=1.1)

    # ---- verdict chips: the split (issues / skipped) ---------------------
    warn, violet = t["warn"], t["violet"]
    assert_fit(c["issues_head"], 12, 280, where="issues head")
    s.text((il, 366), c["issues_head"], 12, warn, bold=True)
    assert_fit(c["skipped_head"], 12, 280, where="skipped head")
    s.text((1076, 366), c["skipped_head"], 12, violet, bold=True)

    chip_w = 1064 - il
    for index, (text, top) in enumerate(zip(c["issue_chips"], (376, 412))):
        s.rounded((il, top, il + chip_w, top + 30), 9,
                  fill=t["warn_soft"], outline=over(warn, t, 0.55), width=1.2)
        s.rect((il, top + 6, il + 3.4, top + 24), fill=warn)
        size = fit_size(text, chip_w - 26, 11.8, 10, bold=True)
        s.text((il + 14, top + 20), text, size, warn, bold=True)

    for text, top, height in zip(c["skip_chips"], (376, 406, 436),
                                 (24, 24, 24)):
        s.rounded((1076, top, 1380, top + height), 8,
                  fill=t["surface_alt"],
                  outline=over(t["border"], t, 1.0), width=1.1)
        size = fit_size(text, 304 - 20, 11, 10)
        s.text((1088, top + 16), text, size, t["muted"])

    s.line((il, 470, ir, 470), over(t["border"], t, 0.9), width=1.1)
    assert_fit(c["footer1"], 11.5, 608, mono=True, where="hero footer1")
    s.text((il, 488), c["footer1"], 11.5, t["muted"], mono=True)
    assert_fit(c["footer2"], 11.5, 608, where="hero footer2")
    s.text((il, 506), c["footer2"], 11.5, t["faint"])
    return s


# ---------------------------------------------------------------------------
# flow SVG -- split switchboard (one bus, five rule switches, two rails)
# ---------------------------------------------------------------------------
FLOW_W, FLOW_H = 1100, 660

FLOW_TITLE = "One period → five parallel taps → two rails"
FLOW_SUB = ("Five rules read the same period — no ordering, no short-circuit. "
            "A rule that cannot run, or runs with no gap, lands in skipped[] "
            "with its reason.")
FLOW_META = "rules 2026.1 · 2 warn · 3 skipped"

MATERIAL_ROWS = [("supplied", "120000"), ("sold", "114000"),
                 ("loss", "5500"), ("lossRate", "5"), ("meters[]", "0 rows")]
RULESET_ROWS = [("version", "2026.1"), ("rules", "5 · PL-001…PL-005")]
KIND_ROWS = [("derived", "cap warn"), ("institutional", "cap info")]
SELECT_ROWS = [("only[] · disabledRules", "[]"),
               ("rulesFile", "path override"),
               ("timeoutMs", "120000")]

RULES = [
    dict(id="PL-001", role="warn", formula="supplied − sold − loss",
         decision="|120000−114000−5500| = 500 > tol 0", outcome="issue"),
    dict(id="PL-002", role="warn", formula="loss ÷ supplied × 100",
         decision="|4.5833−5| = 0.4167 > tol 0.01", outcome="issue"),
    dict(id="PL-003", role="info", formula="minRate ≤ lossRate ≤ maxRate",
         decision="maxRate = 0 → not configured", outcome="skipped"),
    dict(id="PL-004", role="warn", formula="Σ meters.energy vs sold",
         decision="no meter row carries energy", outcome="skipped"),
    dict(id="PL-005", role="info", formula="(max − min) ÷ max × 100",
         decision="A/B/C phases present: 0 of 3", outcome="skipped"),
]

ISSUES = [
    dict(rule="PL-001", locator="locator: column",
         found=("120000 − 114000 = 6000 · declared 5500",
                "gap 500 kWh > tol 0"),
         expected="expected  loss = supplied − sold · tol 0 kWh",
         fix="fix  recheck source figures & metering period",
         basis="basis  DL/T 686-2018 §3 · derived (cap warn)"),
    dict(rule="PL-002", locator="locator: column",
         found=("5500 ÷ 120000 × 100 = 4.5833% · declared 5%",
                "gap 0.4167 pt > tol 0.01"),
         expected="expected  rate = loss ÷ supplied × 100 · tol 0.01 pt",
         fix="fix  recheck the denominator",
         basis="basis  DL/T 686-2018 §3 · GB/T 8170 · derived"),
]

SKIPPED = [
    ("PL-003", "maxRate = 0 → band not configured"),
    ("PL-004", "no meter row carries energy"),
    ("PL-005", "A/B/C phases not all present"),
]

WHY_LINES = [
    "five taps read one period — no ordering, no short-circuit.",
    "each tap has two contacts; one route is live this period.",
    "skipped[] also lists rules that ran clean.",
    "empty issues[] never means everything was checked.",
]

SANS = ("'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',"
        "'Source Han Sans SC',sans-serif")
MONO = "Consolas,'Cascadia Mono','SFMono-Regular',ui-monospace,monospace"


class Flow:
    def __init__(self, theme_name: str):
        self.t = THEMES[theme_name]
        self.theme_name = theme_name
        self.lines: list[str] = []
        t = self.t
        self.head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{FLOW_W}" '
            f'height="{FLOW_H}" viewBox="0 0 {FLOW_W} {FLOW_H}" '
            f'role="img" aria-labelledby="flowTitle flowDesc">'
            f'<title id="flowTitle">dsh-power-loss-split split switchboard</title>'
            f'<desc id="flowDesc">One material bus feeds five parallel rule '
            f'switches; each rule routes to one of two rails — issues[] with '
            f'found, expected, fix and basis, or skipped[] with its reason. '
            f'Both rails end in one report view: summary, issueCount, '
            f'skippedCount, markdown and reportJson.</desc>'
            f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{hexs(t["bg_top"])}"/>'
            f'<stop offset="1" stop-color="{hexs(t["bg_bottom"])}"/>'
            f'</linearGradient></defs>'
            f'<rect width="{FLOW_W}" height="{FLOW_H}" rx="20" fill="url(#bg)"/>'
        )

    # -- primitives --------------------------------------------------------
    def rect(self, x, y, w, h, r=0, fill="none", stroke=None, sw=1.2,
             dash=None):
        out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}"'
               + (f' rx="{r}"' if r else "")
               + f' fill="{col(fill)}"')
        if stroke:
            out += f' stroke="{col(stroke)}" stroke-width="{sw}"'
        if dash:
            out += f' stroke-dasharray="{dash}"'
        return out + "/>"

    def text(self, x, y, s, size, fill, *, bold=False, mono=False,
             anchor="start", opacity=None):
        fam = MONO if mono else SANS
        weight = 700 if bold else 400
        op = f' opacity="{opacity}"' if opacity is not None else ""
        return (f'<text x="{x}" y="{y}" font-family="{fam}" '
                f'font-size="{size}" font-weight="{weight}" fill="{col(fill)}" '
                f'text-anchor="{anchor}"{op}>{escape(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke, sw=1.4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{col(stroke)}" stroke-width="{sw}" '
                f'stroke-linecap="round"{d}/>')

    def path(self, d, stroke, sw=1.5, dash=None, fill="none"):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        return (f'<path d="{d}" fill="{fill}" stroke="{col(stroke)}" '
                f'stroke-width="{sw}" stroke-linecap="round" '
                f'stroke-linejoin="round"{da}/>')

    def arrow(self, x1, y1, x2, y2, stroke, sw=1.6, head=5.0):
        stroke = col(stroke)
        ang = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
        out = [self.line(x1, y1, bx, by, stroke, sw)]
        p2 = (bx - head * 0.55 * math.sin(ang), by + head * 0.55 * math.cos(ang))
        p3 = (bx + head * 0.55 * math.sin(ang), by - head * 0.55 * math.cos(ang))
        pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in ((x2, y2), p2, p3))
        out.append(f'<polygon points="{pts}" fill="{stroke}"/>')
        return "".join(out)

    # -- composites --------------------------------------------------------
    def card(self, x, y, w, h, title, tag="", *, mono_title=False):
        t = self.t
        L = self.lines
        L.append(self.rect(x, y, w, h, 18, t["surface"],
                           over(t["border"], t, 0.95), 1.3))
        size = fit_size(title, w - 32, 16, 13, bold=True, mono=mono_title)
        assert_fit(title, size, w - 32, bold=True, mono=mono_title,
                   where=f"card {title}")
        L.append(self.text(x + 16, y + 28, title, size, t["ink"], bold=True,
                           mono=mono_title))
        if tag:
            tag_size = fit_size(tag, w - 32, 11, 9.5, mono=True)
            L.append(self.text(x + 16, y + 47, tag, tag_size, t["muted"],
                               mono=True))

    def build(self) -> str:
        t = self.t
        L = self.lines
        L.append(self.head)
        ink, ink2, muted, faint = t["ink"], t["ink2"], t["muted"], t["faint"]
        family = t["family"]
        arrow_c = over(muted, t, 0.85)

        # header ------------------------------------------------------------
        assert_fit(FLOW_TITLE, 25, 700, bold=True, where="flow title")
        assert_fit(FLOW_SUB, 14, 1010, where="flow subtitle")
        assert_fit(FLOW_META, 12.5, 330, mono=True, where="flow meta")
        L.append(self.text(40, 46, FLOW_TITLE, 25, ink, bold=True))
        L.append(self.text(1060, 46, FLOW_META, 12.5, muted, mono=True,
                           anchor="end"))
        L.append(self.text(40, 70, FLOW_SUB, 14, muted))

        # left column: material / ruleset / select --------------------------
        self.card(40, 88, 236, 196, "MATERIAL · parseMaterial()",
                  "JSON | YAML · file | material")
        for index, (key, value) in enumerate(MATERIAL_ROWS):
            y = 168 + index * 21
            L.append(self.text(56, y, key, 11.5, muted, mono=True))
            L.append(self.text(260, y, value, 12.5, ink, mono=True,
                               anchor="end"))
        L.append(self.text(56, 272, "numbers: 1,200.5 · 1200 kWh · 5%", 11,
                           faint))

        self.card(40, 296, 236, 252, "RULESET · validated on load",
                  "rules/power-loss-split.yaml")
        for index, (key, value) in enumerate(RULESET_ROWS):
            y = 368 + index * 20
            L.append(self.text(56, y, key, 11.5, muted, mono=True))
            L.append(self.text(260, y, value, 11.5, ink, mono=True,
                               anchor="end"))
        L.append(self.line(56, 402, 260, 402, over(t["grid"], t, 0.95), 1))
        for index, (key, value) in enumerate(KIND_ROWS):
            y = 422 + index * 18
            L.append(self.text(56, y, key, 11, muted))
            L.append(self.text(260, y, value, 11, ink2, mono=True,
                               anchor="end"))
        L.append(self.line(56, 450, 260, 450, over(t["grid"], t, 0.95), 1))
        L.append(self.text(56, 470, "SELECT · per call", 12, ink, bold=True))
        for index, (key, value) in enumerate(SELECT_ROWS):
            y = 492 + index * 18
            L.append(self.text(56, y, key, 11, muted, mono=True))
            L.append(self.text(260, y, value, 11, ink2, anchor="end"))

        # material bus ------------------------------------------------------
        bus_x = 286
        first_cy = 120 + 24
        last_cy = 120 + 4 * 54 + 24
        L.append(self.line(276, 252, bus_x, 252, over(muted, t, 0.55), 1.6))
        L.append(self.line(bus_x, first_cy, bus_x, last_cy,
                           over(muted, t, 0.55), 1.6))
        for index in range(5):
            cy = 120 + index * 54 + 24
            L.append(self.line(bus_x, cy, 296, cy, over(muted, t, 0.7), 1.4))

        # rule bank ---------------------------------------------------------
        L.append(self.text(296, 104, "RULE BANK · five taps, one period", 12.5,
                           ink2, bold=True))
        for index, rule in enumerate(RULES):
            top = 120 + index * 54
            cy = top + 24
            color = t[rule["role"]]
            L.append(self.rect(296, top, 360, 48, 12, t["surface"],
                               over(t["border"], t, 0.95), 1.2))
            L.append(self.rect(296, top + 9, 3.2, 30, 1.6, color))
            L.append(self.rect(304, top + 10, 56, 28, 9,
                               over(color, t, 0.14), over(color, t, 0.55), 1.2))
            L.append(self.text(332, top + 28, rule["id"], 12.5, color,
                               bold=True, mono=True, anchor="middle"))
            assert_fit(rule["formula"], 13.2, 262, mono=True,
                       where=f"{rule['id']} formula")
            L.append(self.text(368, top + 21, rule["formula"], 13.2, ink,
                               mono=True))
            assert_fit(rule["decision"], 11, 262, mono=True,
                       where=f"{rule['id']} decision")
            L.append(self.text(368, top + 38, rule["decision"], 11, muted,
                               mono=True))
            # two-position switch: one live contact, one idle contact
            live = cy - 11 if rule["outcome"] == "issue" else cy + 11
            idle = cy + 11 if rule["outcome"] == "issue" else cy - 11
            L.append(f'<circle cx="640" cy="{cy}" r="3.4" fill="{hexs(t["surface"])}" '
                     f'stroke="{hexs(over(muted, t, 0.9))}" stroke-width="1.4"/>')
            L.append(self.line(640, cy, 652, live, color, 2.1))
            L.append(f'<circle cx="652" cy="{live}" r="3.1" fill="{hexs(color)}"/>')
            L.append(f'<circle cx="652" cy="{idle}" r="2.6" fill="{hexs(t["surface"])}" '
                     f'stroke="{hexs(over(faint, t, 0.9))}" stroke-width="1.2"/>')

        # the two rails -----------------------------------------------------
        issue_rail, skip_rail = 676, 700
        issue_entry, skip_entry = 240, 476
        issue_ys = [120 + 0 * 54 + 24 - 11, 120 + 1 * 54 + 24 - 11]
        skip_ys = [120 + i * 54 + 24 + 11 for i in (2, 3, 4)]
        for y in issue_ys:
            L.append(self.line(652, y, issue_rail, y,
                               over(t["warn"], t, 0.8), 1.8))
        L.append(self.line(issue_rail, issue_ys[0], issue_rail, issue_entry,
                           over(t["warn"], t, 0.8), 1.8))
        L.append(self.arrow(issue_rail, issue_entry, 714, issue_entry,
                            over(t["warn"], t, 0.85), sw=1.8, head=5.0))
        for y in skip_ys:
            L.append(self.line(652, y, skip_rail, y,
                               over(t["violet"], t, 0.8), 1.8))
        L.append(self.line(skip_rail, skip_ys[0], skip_rail, skip_entry,
                           over(t["violet"], t, 0.8), 1.8))
        L.append(self.arrow(skip_rail, skip_entry, 714, skip_entry,
                            over(t["violet"], t, 0.85), sw=1.8, head=5.0))

        # issues[] panel ----------------------------------------------------
        px, pw = 716, 344
        L.append(self.rect(px, 88, pw, 304, 18, t["surface"],
                           over(t["border"], t, 0.95), 1.3))
        L.append(self.text(px + 16, 116, "issues[] · 2 warn", 15.5, ink,
                           bold=True))
        assert_fit("found · expected · fix", 11, 150, mono=True,
                   where="issues tag")
        L.append(self.text(px + pw - 16, 116, "found · expected · fix",
                           11, muted, mono=True, anchor="end"))
        L.append(self.line(px + 16, 126, px + pw - 16, 126,
                           over(t["border"], t, 0.9), 1))

        for index, issue in enumerate(ISSUES):
            top = 134 + index * 124
            hue = t["warn"]
            L.append(self.rect(px + 12, top, pw - 24, 118, 13,
                               t["surface_alt"], over(hue, t, 0.35), 1.2))
            L.append(self.text(px + 26, top + 20, issue["rule"], 13, hue,
                               bold=True, mono=True))
            L.append(self.rect(px + 84, top + 9, 40, 18, 9, over(hue, t, 0.16),
                               over(hue, t, 0.55), 1))
            L.append(self.text(px + 104, top + 22, "warn", 11, hue,
                               bold=True, anchor="middle"))
            assert_fit(issue["locator"], 11, 120, mono=True,
                       where="locator")
            L.append(self.text(px + pw - 26, top + 20, issue["locator"], 11,
                               faint, mono=True, anchor="end"))
            for line_index, line in enumerate(issue["found"]):
                assert_fit(line, 11.2, pw - 52, mono=True,
                           where=f"{issue['rule']} found")
                L.append(self.text(px + 26, top + 40 + line_index * 15, line,
                                   11.2, ink2, mono=True))
            assert_fit(issue["expected"], 11, pw - 52,
                       where=f"{issue['rule']} expected")
            L.append(self.text(px + 26, top + 78, issue["expected"], 11,
                               muted))
            assert_fit(issue["fix"], 11, pw - 52,
                       where=f"{issue['rule']} fix")
            L.append(self.text(px + 26, top + 94, issue["fix"], 11, ink2))
            assert_fit(issue["basis"], 11, pw - 52, mono=True,
                       where=f"{issue['rule']} basis")
            L.append(self.text(px + 26, top + 108, issue["basis"], 11, faint,
                               mono=True))

        # skipped[] panel ---------------------------------------------------
        L.append(self.rect(px, 404, pw, 144, 18, t["surface"],
                           over(t["border"], t, 0.95), 1.3))
        L.append(self.text(px + 16, 432, "skipped[] · 3", 15.5, ink,
                           bold=True))
        L.append(self.text(px + pw - 16, 432, "rule + reason", 11, muted,
                           mono=True, anchor="end"))
        L.append(self.line(px + 16, 442, px + pw - 16, 442,
                           over(t["border"], t, 0.9), 1))
        for index, (rule, reason) in enumerate(SKIPPED):
            y = 460 + index * 26
            L.append(self.rect(px + 16, y - 15, 52, 20, 7,
                               over(t["violet"], t, 0.12),
                               over(t["violet"], t, 0.45), 1, dash="3 3"))
            L.append(self.text(px + 42, y, rule, 11.5, t["violet"], bold=True,
                               mono=True, anchor="middle"))
            assert_fit(reason, 11, pw - 90, where=f"{rule} reason")
            L.append(self.text(px + 78, y, reason, 11, muted))
        L.append(self.text(px + 16, 536,
                           "ran clean? also listed here, with that reason",
                           11, faint))

        # why two rails (middle note) --------------------------------------
        L.append(self.rect(296, 404, 360, 144, 18, t["surface_alt"],
                           over(t["border"], t, 0.95), 1.2))
        L.append(self.text(312, 430, "WHY TWO RAILS", 12.5, ink2, bold=True))
        for index, line in enumerate(WHY_LINES):
            assert_fit(line, 11, 328, where=f"why {index}")
            L.append(self.text(312, 456 + index * 22, line, 11,
                               ink2 if index else muted))

        # exit band ---------------------------------------------------------
        L.append(self.rect(40, 558, 1020, 74, 18, t["surface"],
                           over(t["border"], t, 0.95), 1.3))
        L.append(self.text(56, 584, "view = buildView(report)", 14, ink,
                           bold=True, mono=True))
        L.append(self.text(1044, 584, "read-only · no network · no model call",
                           11, muted, mono=True, anchor="end"))
        assert_fit("checkedAt · rulesetVersion 2026.1 · summary{error 0 · "
                   "warn 2 · info 0} · issueCount 2 · skippedCount 3",
                   11.2, 970, mono=True, where="view line 1")
        L.append(self.text(56, 604,
                           "checkedAt · rulesetVersion 2026.1 · "
                           "summary{error 0 · warn 2 · info 0} · "
                           "issueCount 2 · skippedCount 3",
                           11.2, ink2, mono=True))
        assert_fit("markdown: findings + not-executed sections · reportJson: "
                   "canonical report · disclaimer attached", 11, 970,
                   where="view line 2")
        L.append(self.text(56, 624,
                           "markdown: findings + not-executed sections · "
                           "reportJson: canonical report · disclaimer attached",
                           11, muted))

        L.append("</svg>")
        return "\n".join(L) + "\n"


def flow_svg(theme_name: str) -> str:
    return Flow(theme_name).build()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
LEGACY = ("dsh-power-loss-split-flow-light.svg",
          "dsh-power-loss-split-flow-dark.svg",
          "dsh-power-loss-split-flow.svg")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    written = []
    for lang in ("zh", "en"):
        for theme in ("light", "dark"):
            name = f"dsh-power-loss-split-hero-{lang}-{theme}.webp"
            hero(lang, theme).save(os.path.join(OUT, name))
            written.append(name)
    for theme in ("light", "dark"):
        name = f"dsh-power-loss-split-flow-v5-{theme}.svg"
        with open(os.path.join(OUT, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(flow_svg(theme))
        written.append(name)
    for legacy in LEGACY:
        path = os.path.join(OUT, legacy)
        if os.path.exists(path):
            os.remove(path)
            print(f"removed legacy {legacy}")
    print("wrote " + ", ".join(written))


if __name__ == "__main__":
    main()
