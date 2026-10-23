# -*- coding: utf-8 -*-
"""Текстуры окна Debug Toolpack 2.0 + объявления спрайтов + схема окна.
python3 art2.py <папка_мода> <gui_meta.json> <папка_для_схем>"""
import os, sys, json, re, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT, META, PREV, STARTEX = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"
NAVY = (13, 21, 38); STEEL = (34, 52, 82); AMBER = (236, 170, 74); CYAN = (110, 200, 240)

def rr(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)

def button_frames(fill, edge, hover_edge, size=(64, 32), r=5):
    """3 кадра (обычный, наведение, нажатие) для corneredTileSpriteType с buttonstate.shader."""
    w, h = size
    im = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    for i in range(3):
        fr = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
        f = tuple(min(255, int(c * (1.0, 1.25, 0.8)[i])) for c in fill)
        rr(d, (0, 0, w - 1, h - 1), r, fill=f + (235,), outline=(hover_edge if i == 1 else edge) + (255,), width=2)
        # верхний блик
        d.line([(r, 2), (w - r, 2)], fill=(255, 255, 255, 40 if i != 2 else 10), width=1)
        im.paste(fr, (i * w, 0))
    return im

def panel(size=(128, 128)):
    w, h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 0, w - 1, h - 1), 8, fill=NAVY + (252,), outline=(58, 84, 124, 255), width=2)
    for (x, y, sx, sy) in [(3, 3, 1, 1), (w - 4, 3, -1, 1), (3, h - 4, 1, -1), (w - 4, h - 4, -1, -1)]:
        d.line([(x, y), (x + sx * 18, y)], fill=AMBER + (255,), width=2)
        d.line([(x, y), (x, y + sy * 18)], fill=AMBER + (255,), width=2)
    return im

def toggle_frames(size=48):
    s = size * 4
    frames = []
    for i in range(3):
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        hexpts = [(s / 2 + s * 0.46 * math.cos(math.radians(60 * k - 30)), s / 2 + s * 0.46 * math.sin(math.radians(60 * k - 30))) for k in range(6)]
        c = (AMBER if i != 1 else (255, 205, 120)) + (255,)
        d.polygon(hexpts, fill=(NAVY if i != 2 else (6, 10, 20)) + (240,))
        d.line(hexpts + [hexpts[0]], fill=c, width=int(s * 0.05))
        cx, cy = s / 2, s / 2
        d.line([(cx - s * 0.18, cy + s * 0.18), (cx + s * 0.08, cy - s * 0.08)], fill=c, width=int(s * 0.09))
        r = s * 0.13
        d.ellipse([cx + s * 0.02, cy - s * 0.27, cx + s * 0.02 + 2 * r, cy - s * 0.27 + 2 * r], outline=c, width=int(s * 0.07))
        frames.append(im.resize((size, size), Image.LANCZOS))
    out = Image.new("RGBA", (size * 3, size), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.paste(f, (i * size, 0))
    return out

def handle(w=210, h=52):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 4, w - 1, h - 5), 8, fill=NAVY + (245,), outline=(58, 84, 124, 255), width=2)
    for k in range(3):
        for j in range(2):
            d.ellipse((12 + j * 7, 16 + k * 8, 16 + j * 7, 20 + k * 8), fill=(150, 170, 200, 255))
    f1 = ImageFont.truetype(FB, 14); f2 = ImageFont.truetype(FR, 10)
    d.text((32, 12), "DEBUG TOOLPACK", font=f1, fill=AMBER + (255,))
    d.text((32, 30), "drag to move", font=f2, fill=(150, 165, 190, 255))
    return im


def dot_frames(core, ring, size=24):
    """Точка-метка над звездой на галактической карте (3 кадра)."""
    s = size * 4; out = Image.new("RGBA", (size * 3, size), (0, 0, 0, 0))
    for i in range(3):
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        k = (1.0, 1.3, 0.8)[i]
        c = tuple(min(255, int(v * k)) for v in core)
        d.ellipse((s * 0.08, s * 0.08, s * 0.92, s * 0.92), fill=(0, 0, 0, 170))
        d.ellipse((s * 0.16, s * 0.16, s * 0.84, s * 0.84), fill=c + (255,), outline=(255, 255, 255, 255) if i == 1 else ring + (255,), width=int(s * 0.09))
        out.paste(im.resize((size, size), Image.LANCZOS), (i * size, 0))
    return out

def mapmode_frames(on, size=40):
    s = size * 4; out = Image.new("RGBA", (size * 3, size), (0, 0, 0, 0))
    col = (235, 60, 50) if on else (170, 180, 200)
    for i in range(3):
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        c = tuple(min(255, int(v * (1.0, 1.2, 0.8)[i])) for v in col) + (255,)
        rr(d, (4, 4, s - 5, s - 5), 22, fill=((70, 16, 14) if on else NAVY) + (240,), outline=c, width=int(s * 0.05))
        cx = cy = s / 2; r = s * 0.24
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=int(s * 0.06))
        d.ellipse((cx - s * 0.07, cy - s * 0.07, cx + s * 0.07, cy + s * 0.07), fill=c)
        for a, b in [((cx, s * 0.12), (cx, cy - r * 0.6)), ((cx, s * 0.88), (cx, cy + r * 0.6)), ((s * 0.12, cy), (cx - r * 0.6, cy)), ((s * 0.88, cy), (cx + r * 0.6, cy))]:
            d.line([a, b], fill=c, width=int(s * 0.05))
        out.paste(im.resize((size, size), Image.LANCZOS), (i * size, 0))
    return out

def field(size=(64, 32)):
    """Поле ввода числа: тёмное, с голубой рамкой и курсором справа."""
    w, h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 0, w - 1, h - 1), 5, fill=(4, 8, 16, 250), outline=CYAN + (255,), width=2)
    d.line([(4, 3), (w - 5, 3)], fill=(0, 0, 0, 160), width=2)
    return im


def tab_frames(on, size=(64, 32)):
    """Вкладка: тёмная плашка; выбранная — светлее, с голубой полосой слева."""
    w, h = size
    im = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    for i in range(3):
        fr = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
        base = (34, 58, 94) if on else (18, 28, 46)
        f = tuple(min(255, int(c * (1.0, 1.3, 0.85)[i])) for c in base)
        rr(d, (0, 0, w - 1, h - 1), 4, fill=f + (240,), outline=(CYAN if on else ((70, 100, 140) if i == 1 else (40, 58, 86))) + (255,), width=1)
        if on:
            d.rectangle((0, 3, 4, h - 4), fill=CYAN + (255,))
        im.paste(fr, (i * w, 0))
    return im

def band(size=(128, 128)):
    w, h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 0, w - 1, h - 1), 6, fill=(8, 13, 25, 235), outline=(44, 64, 96, 255), width=1)
    return im

def frame(size=(128, 128)):
    w, h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 0, w - 1, h - 1), 6, fill=(17, 27, 46, 230), outline=(52, 76, 112, 255), width=1)
    d.line([(8, 1), (w - 9, 1)], fill=CYAN + (120,), width=1)
    return im


# ======================= СТИЛЬ 5.0: глубокий космос, бирюзовый акцент, янтарь для главного
TEAL = (78, 214, 214); DEEP = (7, 12, 22); SLATE = (22, 34, 56)

def grad_btn(top, bot, edge, hover_edge, size=(64, 32), r=5, glow=None):
    w, h = size
    im = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    for i in range(3):
        fr = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
        k = (1.0, 1.22, 0.78)[i]
        for yy in range(h):
            t = yy / (h - 1)
            c = tuple(min(255, int((top[j] * (1 - t) + bot[j] * t) * k)) for j in range(3))
            d.line([(1, yy), (w - 2, yy)], fill=c + (245,))
        mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
        fr.putalpha(Image.fromarray(np.minimum(np.array(fr.split()[3]), np.array(mask))))
        d = ImageDraw.Draw(fr)
        d.rounded_rectangle((0, 0, w - 1, h - 1), r, outline=(hover_edge if i == 1 else edge) + (255,), width=1)
        d.line([(r, 1), (w - r, 1)], fill=(255, 255, 255, 50 if i != 2 else 12))
        if glow and i == 1:
            d.rounded_rectangle((1, 1, w - 2, h - 2), r, outline=glow + (110,), width=1)
        im.paste(fr, (i * w, 0))
    return im

def card(size=(128, 128)):
    w, h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, (0, 0, w - 1, h - 1), 7, fill=(14, 23, 40, 235), outline=(46, 70, 104, 255), width=1)
    d.line([(10, 0), (40, 0)], fill=TEAL + (255,), width=2)
    return im

def icon(kind, s, col):
    """Простые векторные значки разделов (рисуются в 4x, затем уменьшаются)."""
    im = Image.new("RGBA", (s * 4, s * 4), (0, 0, 0, 0)); d = ImageDraw.Draw(im); S = s * 4; lw = int(S * 0.09); c = col + (255,)
    m = S * 0.12
    if kind == "home":
        d.polygon([(S / 2, m), (S - m, S * 0.48), (m, S * 0.48)], outline=c, width=lw); d.rectangle((S * 0.26, S * 0.48, S * 0.74, S - m), outline=c, width=lw)
    elif kind == "target":
        d.ellipse((m, m, S - m, S - m), outline=c, width=lw); d.ellipse((S * 0.38, S * 0.38, S * 0.62, S * 0.62), fill=c)
    elif kind == "systems":
        d.ellipse((S * 0.3, S * 0.3, S * 0.7, S * 0.7), fill=c); d.ellipse((m, S * 0.38, S - m, S * 0.62), outline=c, width=lw // 2 + 1)
    elif kind == "res":
        d.polygon([(S / 2, m), (S - m, S * 0.4), (S / 2, S - m), (m, S * 0.4)], outline=c, width=lw); d.line([(m, S * 0.4), (S - m, S * 0.4)], fill=c, width=lw // 2 + 1)
    elif kind == "mod":
        d.line([(S / 2, S - m), (S / 2, m)], fill=c, width=lw); d.polygon([(S / 2, m * 0.6), (S * 0.75, S * 0.38), (S * 0.25, S * 0.38)], fill=c)
    elif kind == "planet":
        d.ellipse((S * 0.24, S * 0.24, S * 0.76, S * 0.76), outline=c, width=lw); d.arc((m * 0.5, S * 0.36, S - m * 0.5, S * 0.64), 200, 340, fill=c, width=lw // 2 + 1)
    elif kind == "build":
        for (a, b, h2) in [(0.14, 0.38, 0.5), (0.42, 0.62, 0.2), (0.66, 0.86, 0.38)]: d.rectangle((S * a, S * h2, S * b, S - m), outline=c, width=lw // 2 + 1)
    elif kind == "fleet":
        d.polygon([(S - m, S / 2), (m, S * 0.2), (S * 0.3, S / 2), (m, S * 0.8)], outline=c, width=lw)
    elif kind == "state":
        d.polygon([(S / 2, m), (S - m, S * 0.32), (m, S * 0.32)], fill=c)
        for a in (0.24, 0.44, 0.64): d.rectangle((S * a, S * 0.38, S * a + S * 0.1, S * 0.78), fill=c)
        d.rectangle((m, S * 0.8, S - m, S - m), fill=c)
    elif kind == "gov":
        d.polygon([(m, S * 0.75), (m, S * 0.3), (S * 0.32, S * 0.5), (S / 2, m), (S * 0.68, S * 0.5), (S - m, S * 0.3), (S - m, S * 0.75)], outline=c, width=lw)
    elif kind == "species":
        d.ellipse((S * 0.32, m, S * 0.68, S * 0.48), outline=c, width=lw); d.arc((S * 0.16, S * 0.52, S * 0.84, S * 1.2), 180, 360, fill=c, width=lw)
    elif kind == "diplo":
        d.ellipse((m, S * 0.3, S * 0.58, S * 0.7), outline=c, width=lw); d.ellipse((S * 0.42, S * 0.3, S - m, S * 0.7), outline=c, width=lw)
    elif kind == "event":
        d.ellipse((m, m, S - m, S - m), outline=c, width=lw); d.line([(S / 2, S * 0.26), (S / 2, S * 0.6)], fill=c, width=lw); d.ellipse((S * 0.44, S * 0.68, S * 0.56, S * 0.8), fill=c)
    elif kind == "access":
        d.ellipse((m, S * 0.3, S * 0.5, S * 0.7), outline=c, width=lw); d.line([(S * 0.5, S / 2), (S - m, S / 2)], fill=c, width=lw); d.line([(S * 0.78, S / 2), (S * 0.78, S * 0.7)], fill=c, width=lw)
    elif kind == "gm":
        P = [(S / 2 + (S * 0.44 if j % 2 == 0 else S * 0.19) * math.cos(math.radians(-90 + 36 * j)), S / 2 + (S * 0.44 if j % 2 == 0 else S * 0.19) * math.sin(math.radians(-90 + 36 * j))) for j in range(10)]
        d.polygon(P, outline=c, width=lw)
    elif kind == "log":
        for k2 in range(4): d.line([(m, S * (0.22 + k2 * 0.19)), (S - m, S * (0.22 + k2 * 0.19))], fill=c, width=lw // 2 + 2)
    return im.resize((s, s), Image.LANCZOS)

NAV_ICONS = {16: "gm", 15: "home", 2: "target", 1: "systems", 3: "res", 4: "mod", 5: "planet", 14: "build", 6: "fleet",
             8: "state", 13: "gov", 9: "species", 7: "diplo", 10: "event", 11: "access", 12: "log"}
def nav_frames(kind, on, size=(96, 32)):
    w, h = size
    im = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    for i in range(3):
        fr = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
        if on:
            rr(d, (0, 0, w - 1, h - 1), 5, fill=(26, 52, 72, 245), outline=TEAL + (255,), width=1)
            d.rectangle((0, 4, 3, h - 5), fill=TEAL + (255,))
        else:
            base = [(0, 0, 0, 0), (30, 46, 72, 220), (14, 22, 36, 220)][i]
            rr(d, (0, 0, w - 1, h - 1), 5, fill=base, outline=((60, 90, 130, 255) if i == 1 else (0, 0, 0, 0)), width=1)
        col = TEAL if on else ((200, 214, 232) if i == 1 else (140, 158, 186))
        fr.alpha_composite(icon(kind, 20, col), (8, (h - 20) // 2))
        im.paste(fr, (i * w, 0))
    return im

# ======================= СТИЛЬ 5.1 «2026»: стекло, мягкие градиенты, бирюза → индиго
VIOLET = (132, 108, 255); TEAL2 = (64, 224, 208); INK = (5, 9, 18)
def _ss(w, h, k=4):
    return Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
def _down(im, w, h):
    return im.resize((w, h), Image.LANCZOS)
def _vgrad(w, h, top, bot, a0=255, a1=255):
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for yy in range(h):
        t = yy / max(1, h - 1)
        arr[yy, :, :3] = [min(255, int(top[j] * (1 - t) + bot[j] * t)) for j in range(3)]
        arr[yy, :, 3] = int(a0 * (1 - t) + a1 * t)
    return Image.fromarray(arr, "RGBA")
def _hgrad(w, h, left, right, a=255):
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for xx in range(w):
        t = xx / max(1, w - 1)
        arr[:, xx, :3] = [min(255, int(left[j] * (1 - t) + right[j] * t)) for j in range(3)]
        arr[:, xx, 3] = a
    return Image.fromarray(arr, "RGBA")
def _rmask(w, h, r):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); return m
def glass(w, h, r, top, bot, edge_a=(110, 140, 190, 90), hi=True, accent=False, a0=235, a1=235):
    k = 4; W2, H2 = w * k, h * k
    body = _vgrad(W2, H2, top, bot, a0, a1)
    m = _rmask(W2, H2, r * k)
    body.putalpha(Image.fromarray(np.minimum(np.array(body.split()[3]), np.array(m))))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle((0, 0, W2 - 1, H2 - 1), r * k, outline=edge_a, width=k)
    if hi:
        d.rounded_rectangle((k, k, W2 - 1 - k, H2 - 1 - k), r * k - k, outline=(255, 255, 255, 18), width=k)
        d.line([(r * k, k * 1.5), (W2 - r * k, k * 1.5)], fill=(255, 255, 255, 40), width=k)
    if accent:
        acc = _hgrad(W2 // 3, k * 2, TEAL2, VIOLET)
        body.alpha_composite(acc, (r * k, 0))
    return _down(body, w, h)

def panel5(size=(256, 256)):
    w, h = size
    return glass(w, h, 14, (12, 20, 36), (5, 9, 18), edge_a=(90, 130, 190, 140), accent=True, a0=246, a1=250)
def band5(size=(128, 64)):
    w, h = size
    return glass(w, h, 10, (14, 24, 42), (8, 14, 26), edge_a=(80, 110, 160, 70), hi=True, a0=200, a1=200)
def frame5(size=(128, 128)):
    w, h = size
    return glass(w, h, 12, (13, 21, 38), (9, 15, 28), edge_a=(80, 112, 168, 80), hi=False, a0=170, a1=200)
def card5(size=(128, 96)):
    w, h = size
    return glass(w, h, 10, (24, 36, 60), (16, 26, 46), edge_a=(110, 150, 210, 70), hi=True, a0=200, a1=210)
def btn5(top, bot, edge, hover_edge, size=(96, 40), r=8, glowc=None, text_dark=False):
    w, h = size
    out = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    for i in range(3):
        k = (1.0, 1.18, 0.82)[i]
        t2 = tuple(min(255, int(c * k)) for c in top); b2 = tuple(min(255, int(c * k)) for c in bot)
        fr = glass(w, h, r, t2, b2, edge_a=(hover_edge if i == 1 else edge) + ((255,) if i == 1 else (200,)), hi=(i != 2), a0=240, a1=240)
        if glowc and i == 1:
            g = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle((1, 1, w - 2, h - 2), r, outline=glowc + (120,), width=2)
            fr.alpha_composite(g.filter(ImageFilter.GaussianBlur(1)))
        out.paste(fr, (i * w, 0))
    return out
def nav5(kind, on, size=(120, 32)):
    w, h = size
    out = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    for i in range(3):
        fr = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        if on:
            g = glass(w, h, 10, (34, 62, 92), (26, 40, 84), edge_a=(120, 220, 230, 200), hi=True, a0=235, a1=235)
            fr.alpha_composite(g)
            bar = _vgrad(3, h - 12, TEAL2, VIOLET); fr.alpha_composite(bar, (0, 6))
        elif i > 0:
            g = glass(w, h, 10, (30, 44, 70) if i == 1 else (16, 24, 40), (22, 32, 54) if i == 1 else (12, 18, 30), edge_a=(100, 140, 200, 90), hi=False, a0=200, a1=200)
            fr.alpha_composite(g)
        # круглая подложка значка
        k = 4; disc = Image.new("RGBA", (24 * k, 24 * k), (0, 0, 0, 0)); dd = ImageDraw.Draw(disc)
        dd.ellipse((0, 0, 24 * k - 1, 24 * k - 1), fill=((40, 90, 110, 255) if on else (24, 36, 58, 255)), outline=((120, 230, 230, 255) if on else (70, 96, 140, 200)), width=k)
        fr.alpha_composite(_down(disc, 24, 24), (8, (h - 24) // 2))
        col = (210, 255, 250) if on else ((220, 230, 245) if i == 1 else (150, 168, 196))
        fr.alpha_composite(icon(kind, 14, col), (13, (h - 14) // 2))
        out.paste(fr, (i * w, 0))
    return out
def badge5(letter, col, s=26):
    k = 4; im = Image.new("RGBA", (s * k, s * k), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, s * k - 1, s * k - 1), fill=tuple(int(c * 0.35) for c in col) + (255,), outline=col + (255,), width=2 * k)
    f = ImageFont.truetype(FB, int(s * k * 0.56))
    tw = d.textlength(letter, font=f); d.text(((s * k - tw) / 2, s * k * 0.17), letter, font=f, fill=col + (255,))
    return _down(im, s, s)
def logo5(s=32):
    k = 4; S = s * k; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(S / 2 + S * 0.47 * math.cos(math.radians(60 * j - 90)), S / 2 + S * 0.47 * math.sin(math.radians(60 * j - 90))) for j in range(6)]
    g = _hgrad(S, S, S_OR2, S_HI); m = Image.new("L", (S, S), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    g.putalpha(m); im.alpha_composite(g)
    inner = [(S / 2 + S * 0.33 * math.cos(math.radians(60 * j - 90)), S / 2 + S * 0.33 * math.sin(math.radians(60 * j - 90))) for j in range(6)]
    d.polygon(inner, fill=INK + (255,))
    d.line([(S * 0.36, S * 0.64), (S * 0.6, S * 0.4)], fill=(230, 255, 250, 255), width=int(S * 0.08))
    d.ellipse((S * 0.55, S * 0.27, S * 0.73, S * 0.45), outline=(230, 255, 250, 255), width=int(S * 0.06))
    return _down(im, s, s)
def accent5(w=4, h=20):
    im = _vgrad(w, h, TEAL2, VIOLET); return im
def field5(size=(96, 40)):
    w, h = size
    im = glass(w, h, 8, (3, 6, 12), (6, 10, 20), edge_a=(64, 224, 208, 230), hi=False, a0=250, a1=250)
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle((2, 2, w - 3, h - 3), 7, outline=(64, 224, 208, 60), width=2)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(1.2)))
    return im
def grip(d, x, y, col):
    """Языконезависимая подсказка «тяни»: ряд точек-захвата и стрелки ◂ ▸ (без текста — подходит и для RU, и для EN)."""
    d.polygon([(x, y + 3), (x + 6, y), (x + 6, y + 6)], fill=col)
    for i in range(12):
        for j in range(2):
            d.ellipse([x + 12 + i * 8, y + j * 5 - 1, x + 14 + i * 8, y + j * 5 + 1], fill=col)
    xe = x + 12 + 12 * 8 + 4
    d.polygon([(xe + 6, y + 3), (xe, y), (xe, y + 6)], fill=col)
def handle5(w=210, h=52):
    im = glass(w, h - 8, 12, (16, 28, 48), (8, 14, 26), edge_a=(100, 150, 210, 160), accent=True, a0=245, a1=245)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); out.alpha_composite(im, (0, 4))
    d = ImageDraw.Draw(out)
    out.alpha_composite(logo5(26), (10, 13))
    f1 = ImageFont.truetype(FB, 13); f2 = ImageFont.truetype(FR, 10)
    d.text((44, 12), "DEBUG TOOLPACK", font=f1, fill=(225, 240, 255, 255))
    grip(d, 44, 32, (140, 170, 205, 255))
    return out
def toggle5(size=44):
    out = Image.new("RGBA", (size * 3, size), (0, 0, 0, 0))
    for i in range(3):
        k = 4; S = size * k; im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        g = _hgrad(S, S, tuple(int(c * (1.0, 1.2, 0.8)[i]) for c in TEAL2), tuple(min(255, int(c * (1.0, 1.2, 0.8)[i])) for c in VIOLET))
        m = Image.new("L", (S, S), 0); ImageDraw.Draw(m).rounded_rectangle((2 * k, 2 * k, S - 2 * k, S - 2 * k), 12 * k, fill=255); g.putalpha(m); im.alpha_composite(g)
        d = ImageDraw.Draw(im); c = INK + (255,)
        for yy in (0.34, 0.5, 0.66): d.line([(S * 0.28, S * yy), (S * 0.72, S * yy)], fill=c, width=int(S * 0.07))
        out.paste(_down(im, size, size), (i * size, 0))
    return out

# ======================= СТИЛЬ 6.0 «Stellaris»: скошенные углы, светящиеся линии, оранжевые акценты, гексы
S_BG0 = (5, 11, 17); S_BG1 = (13, 26, 36); S_LINE = (52, 128, 120); S_HI = (120, 232, 205); S_OR = (244, 166, 58); S_OR2 = (255, 206, 120)
def _cham(w, h, c, tl=True, tr=True, br=True, bl=True):
    return [(c if tl else 0, 0), (w - 1 - (c if tr else 0), 0), (w - 1, c if tr else 0), (w - 1, h - 1 - (c if br else 0)),
            (w - 1 - (c if br else 0), h - 1), (c if bl else 0, h - 1), (0, h - 1 - (c if bl else 0)), (0, c if tl else 0)]
def sci_panel(w, h, c, top, bot, line, a=240, brackets=None, glow_top=True, corners=(True, True, True, True), lw=1):
    k = 4; W2, H2 = w * k, h * k
    body = _vgrad(W2, H2, top, bot, a, a)
    # лёгкое зерно и мягкая виньетка — панель не выглядит плоской заливкой
    rng = np.random.default_rng(w * 7 + h)
    arr = np.array(body).astype(np.int16)
    arr[..., :3] += rng.integers(-3, 4, size=(H2, W2, 1))
    yy, xx = np.mgrid[0:H2, 0:W2]
    vig = (((xx - W2 / 2) / (W2 / 2)) ** 2 + ((yy - H2 / 2) / (H2 / 2)) ** 2) * 6
    arr[..., :3] -= vig[..., None].astype(np.int16)
    body = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    m = Image.new("L", (W2, H2), 0); pts = _cham(W2, H2, c * k, *corners)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    body.putalpha(Image.fromarray(np.minimum(np.array(body.split()[3]), np.array(m))))
    d = ImageDraw.Draw(body)
    d.line(pts + [pts[0]], fill=line + (230,), width=lw * k)
    inner = _cham(W2 - 4 * k, H2 - 4 * k, max(1, c * k - 2 * k), *corners)
    inner = [(px + 2 * k, py + 2 * k) for px, py in inner]
    d.line(inner + [inner[0]], fill=line + (55,), width=k)
    if glow_top:
        d.line([(c * k + 2 * k, 2 * k), (W2 - c * k - 2 * k, 2 * k)], fill=(255, 255, 255, 34), width=k)
        d.line([(c * k + 4 * k, H2 - 3 * k), (W2 - c * k - 4 * k, H2 - 3 * k)], fill=line + (70,), width=k)
    if brackets:
        L = min(W2, H2) // 3
        for (x0, y0, sx, sy) in [(0, 0, 1, 1), (W2 - 1, H2 - 1, -1, -1)]:
            d.line([(x0 + sx * c * k, y0), (x0 + sx * (c * k + L), y0)], fill=brackets + (255,), width=2 * k)
            d.line([(x0, y0 + sy * c * k), (x0, y0 + sy * (c * k + L))], fill=brackets + (255,), width=2 * k)
            d.line([(x0 + sx * c * k, y0), (x0, y0 + sy * c * k)], fill=brackets + (255,), width=2 * k)
    return _down(body, w, h)
def sbtn(top, bot, line, hover, size=(96, 36), c=7, txtglow=None):
    w, h = size; out = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    for i in range(3):
        kk = (1.0, 1.25, 0.8)[i]
        t2 = tuple(min(255, int(v * kk)) for v in top); b2 = tuple(min(255, int(v * kk)) for v in bot)
        fr = sci_panel(w, h, c, t2, b2, hover if i == 1 else line, a=238, glow_top=(i != 2), corners=(True, False, True, False))
        if i == 1:
            g = Image.new("RGBA", (w, h), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
            gd.polygon(_cham(w, h, c, True, False, True, False), outline=hover + (150,))
            fr.alpha_composite(g.filter(ImageFilter.GaussianBlur(1.5)))
        out.paste(fr, (i * w, 0))
    return out
def snav(kind, on, size=(120, 32)):
    w, h = size; out = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    for i in range(3):
        fr = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        if on:
            fr.alpha_composite(sci_panel(w, h, 6, (54, 42, 20), (26, 22, 14), S_OR, a=235, corners=(True, False, True, False)))
            fr.alpha_composite(Image.new("RGBA", (3, h - 10), S_OR + (255,)), (0, 5))
        elif i > 0:
            fr.alpha_composite(sci_panel(w, h, 6, (22, 44, 52) if i == 1 else (10, 20, 26), (12, 26, 32) if i == 1 else (6, 12, 16), S_LINE, a=210, corners=(True, False, True, False)))
        hexpts = [(12 + 11 * math.cos(math.radians(60 * j)), h / 2 + 11 * math.sin(math.radians(60 * j))) for j in range(6)]
        k = 4; hx = Image.new("RGBA", (24 * k, 24 * k), (0, 0, 0, 0)); hd = ImageDraw.Draw(hx)
        P = [(12 * k + 11.5 * k * math.cos(math.radians(60 * j)), 12 * k + 11.5 * k * math.sin(math.radians(60 * j))) for j in range(6)]
        hd.polygon(P, fill=((70, 52, 20, 255) if on else (14, 30, 38, 255)), outline=((S_OR2 if on else S_LINE) + (255,)))
        fr.alpha_composite(_down(hx, 24, 24), (7, (h - 24) // 2))
        col = S_OR2 if on else ((220, 240, 235) if i == 1 else (150, 190, 185))
        fr.alpha_composite(icon(kind, 14, col), (12, (h - 14) // 2))
        out.paste(fr, (i * w, 0))
    return out
def shex_badge(letter, col, s=28):
    k = 4; S = s * k; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = [(S / 2 + S * 0.48 * math.cos(math.radians(60 * j + 30)), S / 2 + S * 0.48 * math.sin(math.radians(60 * j + 30))) for j in range(6)]
    d.polygon(P, fill=tuple(int(v * 0.28) for v in col) + (255,), outline=col + (255,))
    d.line(P + [P[0]], fill=col + (255,), width=2 * k)
    f = ImageFont.truetype(FB, int(S * 0.5)); tw = d.textlength(letter, font=f)
    d.text(((S - tw) / 2, S * 0.2), letter, font=f, fill=col + (255,))
    return _down(im, s, s)
def shex_decor(w=180, h=90):
    """Россыпь гексов — декоративный угол окна (не растягивается)."""
    k = 2; im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0)); d = ImageDraw.Draw(im); r = 9 * k
    for row in range(8):
        for col in range(14):
            cx = col * r * 1.75 + (r * 0.875 if row % 2 else 0); cy = row * r * 1.52
            dist = math.hypot(cx - w * k, cy) / (w * k)
            a = int(max(0, 1 - dist) * 70)
            if a <= 4: continue
            P = [(cx + r * 0.9 * math.cos(math.radians(60 * j + 30)), cy + r * 0.9 * math.sin(math.radians(60 * j + 30))) for j in range(6)]
            d.polygon(P, outline=S_HI + (a,))
    return _down(im, w, h)
def sfield(size=(96, 40)):
    w, h = size
    im = sci_panel(w, h, 8, (2, 6, 10), (5, 12, 18), S_HI, a=250, glow_top=False, corners=(True, False, True, False))
    return im
def shandle(w=210, h=52):
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(sci_panel(w, h - 8, 10, (14, 30, 40), (6, 14, 20), S_LINE, a=245, brackets=S_OR, corners=(True, False, True, False)), (0, 4))
    out.alpha_composite(logo5(26), (12, 13))
    d = ImageDraw.Draw(out); f1 = ImageFont.truetype(FB, 13); f2 = ImageFont.truetype(FR, 10)
    d.text((46, 12), "DEBUG TOOLPACK", font=f1, fill=S_OR2 + (255,))
    grip(d, 46, 32, (140, 190, 185, 255))
    return out
def stoggle(size=48):
    out = Image.new("RGBA", (size * 3, size), (0, 0, 0, 0))
    for i in range(3):
        k = 4; S = size * k; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        P = [(S / 2 + S * 0.46 * math.cos(math.radians(60 * j + 30)), S / 2 + S * 0.46 * math.sin(math.radians(60 * j + 30))) for j in range(6)]
        fill = [(40, 30, 12), (70, 52, 18), (24, 18, 8)][i]
        d.polygon(P, fill=fill + (245,)); d.line(P + [P[0]], fill=(S_OR2 if i == 1 else S_OR) + (255,), width=int(S * 0.05))
        for yy in (0.36, 0.5, 0.64): d.line([(S * 0.32, S * yy), (S * 0.68, S * yy)], fill=(S_OR2 if i == 1 else S_OR) + (255,), width=int(S * 0.06))
        out.paste(_down(im, size, size), (i * size, 0))
    return out

def res_bar(col, size=(256, 44)):
    w, h = size
    im = sci_panel(w, h, 8, tuple(int(c * 0.22) + 6 for c in col), tuple(int(c * 0.12) + 4 for c in col), tuple(int(c * 0.8) for c in col), a=240, corners=(True, False, True, False))
    im.alpha_composite(Image.new("RGBA", (4, h - 12), col + (255,)), (2, 6))
    return im
def divider(w=256, h=2):
    return _hgrad(w, h, S_OR, (40, 90, 86), a=170)

def stile(kind, size=(160, 32)):
    """Плитка раздела на главной: видимый фон во всех состояниях + значок в гексе."""
    w, h = size; out = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    for i in range(3):
        fr = sci_panel(w, h, 7, [(22, 44, 54), (32, 64, 76), (12, 26, 32)][i], [(12, 26, 34), (18, 40, 50), (8, 16, 20)][i],
                       S_HI if i == 1 else (60, 140, 130), a=235, corners=(True, False, True, False))
        k = 4; hx = Image.new("RGBA", (24 * k, 24 * k), (0, 0, 0, 0)); hd = ImageDraw.Draw(hx)
        P = [(12 * k + 11.5 * k * math.cos(math.radians(60 * j)), 12 * k + 11.5 * k * math.sin(math.radians(60 * j))) for j in range(6)]
        hd.polygon(P, fill=(40, 30, 12, 255), outline=S_OR + (255,))
        fr.alpha_composite(_down(hx, 24, 24), (8, (h - 24) // 2))
        fr.alpha_composite(icon(kind, 14, S_OR2), (13, (h - 14) // 2))
        out.paste(fr, (i * w, 0))
    return out

SPR = {  # имя: (файл, изображение, тип, borderSize, кадры, шейдер)
    "GFX_dtp_btn": ("dtp_btn", grad_btn((36, 54, 84), (22, 34, 56), (64, 92, 132), TEAL, glow=TEAL), "corner", 8, 3, "buttonstate"),
    "GFX_dtp_btn_go": ("dtp_btn_go", grad_btn((32, 104, 92), (16, 62, 58), (70, 190, 170), (160, 250, 230), glow=TEAL), "corner", 8, 3, "buttonstate"),
    "GFX_dtp_btn_on": ("dtp_btn_on", grad_btn((110, 80, 30), (70, 48, 16), AMBER, (255, 215, 140), glow=AMBER), "corner", 8, 3, "buttonstate"),
    "GFX_dtp_btn_warn": ("dtp_btn_warn", grad_btn((96, 64, 22), (58, 36, 12), (220, 150, 60), (255, 200, 110), glow=AMBER), "corner", 8, 3, "buttonstate"),
    "GFX_dtp_btn_danger": ("dtp_btn_danger", grad_btn((112, 34, 34), (66, 18, 20), (220, 90, 80), (255, 150, 130)), "corner", 8, 3, "buttonstate"),
    "GFX_dtp_tab": ("dtp_tab", tab_frames(False), "corner", 8, 3, "buttonstate"),
    "GFX_dtp_tab_on": ("dtp_tab_on", tab_frames(True), "corner", 8, 3, "buttonstate"),
    "GFX_dtp_btn_key": ("dtp_btn_key", grad_btn((24, 36, 58), (12, 20, 34), (58, 84, 120), TEAL, glow=TEAL), "corner", 6, 3, "buttonstate"),
    "GFX_dtp_card": ("dtp_card", card(), "corner", 12, 1, "buttonstate_onlydisable"),
    "GFX_dtp_band": ("dtp_band", band(), "corner", 12, 1, "buttonstate_onlydisable"),
    "GFX_dtp_frame": ("dtp_frame", frame(), "corner", 12, 1, "buttonstate_onlydisable"),
    "GFX_dtp_field": ("dtp_field", field(), "corner", 8, 1, "buttonstate_onlydisable"),
    "GFX_dtp_panel": ("dtp_panel", panel(), "corner", 24, 1, "buttonstate_onlydisable"),
    "GFX_dtp_label": ("dtp_label", Image.new("RGBA", (16, 16), (0, 0, 0, 0)), "corner", 4, 1, "buttonstate_onlydisable"),
    "GFX_dtp_toggle": ("dtp_toggle", toggle_frames(), "sprite", 0, 3, "buttonstate"),
    "GFX_dtp_handle": ("dtp_handle", handle(), "sprite", 0, 1, "buttonstate_onlydisable"),
    "GFX_dtp_dot_off": ("dtp_dot_off", dot_frames((120, 128, 140), (200, 205, 215)), "sprite", 0, 3, "buttonstate"),
    "GFX_dtp_dot_on": ("dtp_dot_on", dot_frames((235, 40, 30), (255, 150, 140)), "sprite", 0, 3, "buttonstate"),
    "GFX_dtp_mapmode_off": ("dtp_mapmode_off", mapmode_frames(False), "sprite", 0, 3, "buttonstate"),
    "GFX_dtp_mapmode_on": ("dtp_mapmode_on", mapmode_frames(True), "sprite", 0, 3, "buttonstate"),
}
SPR.update({
    "GFX_dtp_panel": ("dtp_panel", panel5(), "corner", 28, 1, "buttonstate_onlydisable"),
    "GFX_dtp_band": ("dtp_band", band5(), "corner", 14, 1, "buttonstate_onlydisable"),
    "GFX_dtp_frame": ("dtp_frame", frame5(), "corner", 16, 1, "buttonstate_onlydisable"),
    "GFX_dtp_card": ("dtp_card", card5(), "corner", 14, 1, "buttonstate_onlydisable"),
    "GFX_dtp_field": ("dtp_field", field5(), "corner", 12, 1, "buttonstate_onlydisable"),
    "GFX_dtp_btn": ("dtp_btn", btn5((40, 56, 88), (28, 40, 66), (92, 120, 170), TEAL2, glowc=TEAL2), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_btn_go": ("dtp_btn_go", btn5((30, 150, 140), (20, 96, 110), (90, 230, 210), (190, 255, 245), glowc=TEAL2), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_btn_on": ("dtp_btn_on", btn5((90, 72, 200), (58, 44, 140), (170, 150, 255), (220, 210, 255), glowc=VIOLET), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_btn_warn": ("dtp_btn_warn", btn5((150, 100, 30), (100, 62, 18), (240, 180, 90), (255, 220, 150), glowc=AMBER), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_btn_danger": ("dtp_btn_danger", btn5((150, 40, 56), (92, 22, 36), (240, 110, 120), (255, 170, 175)), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_btn_key": ("dtp_btn_key", btn5((26, 38, 62), (16, 24, 42), (70, 96, 140), TEAL2, glowc=TEAL2), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_handle": ("dtp_handle", handle5(), "sprite", 0, 1, "buttonstate_onlydisable"),
    "GFX_dtp_toggle": ("dtp_toggle", toggle5(48), "sprite", 0, 3, "buttonstate"),
    "GFX_dtp_badge_a": ("dtp_badge_a", badge5("A", (255, 200, 80)), "sprite", 0, 1, "buttonstate_onlydisable"),
    "GFX_dtp_badge_b": ("dtp_badge_b", badge5("B", (90, 210, 255)), "sprite", 0, 1, "buttonstate_onlydisable"),
    "GFX_dtp_logo": ("dtp_logo", logo5(30), "sprite", 0, 1, "buttonstate_onlydisable"),
    "GFX_dtp_accent": ("dtp_accent", accent5(), "corner", (1, 4), 1, "buttonstate_onlydisable"),
})
SPR.update({
    "GFX_dtp_panel": ("dtp_panel", sci_panel(256, 256, 18, (10, 20, 28), (4, 9, 14), S_LINE, a=246, brackets=S_OR), "corner", 34, 1, "buttonstate_onlydisable"),
    "GFX_dtp_band": ("dtp_band", sci_panel(128, 64, 8, (12, 26, 34), (7, 15, 21), (38, 92, 88), a=215), "corner", 12, 1, "buttonstate_onlydisable"),
    "GFX_dtp_frame": ("dtp_frame", sci_panel(128, 128, 10, (9, 19, 26), (6, 13, 19), (38, 92, 88), a=200), "corner", 14, 1, "buttonstate_onlydisable"),
    "GFX_dtp_card": ("dtp_card", sci_panel(128, 96, 8, (17, 34, 42), (11, 23, 30), (46, 112, 104), a=215, corners=(True, False, True, False)), "corner", 12, 1, "buttonstate_onlydisable"),
    "GFX_dtp_field": ("dtp_field", sfield(), "corner", 12, 1, "buttonstate_onlydisable"),
    "GFX_dtp_btn": ("dtp_btn", sbtn((30, 56, 64), (16, 32, 40), (70, 150, 140), S_HI), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_btn_go": ("dtp_btn_go", sbtn((32, 120, 100), (16, 70, 62), (110, 230, 190), (200, 255, 235)), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_btn_on": ("dtp_btn_on", sbtn((120, 82, 22), (70, 46, 12), S_OR, S_OR2), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_btn_warn": ("dtp_btn_warn", sbtn((110, 70, 20), (64, 40, 10), (230, 150, 60), S_OR2), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_btn_danger": ("dtp_btn_danger", sbtn((124, 32, 36), (70, 16, 20), (230, 96, 96), (255, 170, 160)), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_btn_key": ("dtp_btn_key", sbtn((20, 40, 48), (10, 22, 28), (56, 120, 112), S_HI), "corner", 10, 3, "buttonstate"),
    "GFX_dtp_handle": ("dtp_handle", shandle(), "sprite", 0, 1, "buttonstate_onlydisable"),
    "GFX_dtp_toggle": ("dtp_toggle", stoggle(48), "sprite", 0, 3, "buttonstate"),
    "GFX_dtp_badge_a": ("dtp_badge_a", shex_badge("A", S_OR2), "sprite", 0, 1, "buttonstate_onlydisable"),
    "GFX_dtp_badge_b": ("dtp_badge_b", shex_badge("B", (110, 220, 255)), "sprite", 0, 1, "buttonstate_onlydisable"),
    "GFX_dtp_accent": ("dtp_accent", _vgrad(4, 20, S_OR2, S_OR), "corner", (1, 4), 1, "buttonstate_onlydisable"),
    "GFX_dtp_decor": ("dtp_decor", shex_decor(), "sprite", 0, 1, "buttonstate_onlydisable"),
    "GFX_dtp_res_idle": ("dtp_res_idle", res_bar((90, 130, 130)), "corner", (14, 10), 1, "buttonstate_onlydisable"),
    "GFX_dtp_res_ok": ("dtp_res_ok", res_bar((90, 220, 120)), "corner", (14, 10), 1, "buttonstate_onlydisable"),
    "GFX_dtp_res_bad": ("dtp_res_bad", res_bar((240, 80, 80)), "corner", (14, 10), 1, "buttonstate_onlydisable"),
    "GFX_dtp_res_warn": ("dtp_res_warn", res_bar((245, 160, 60)), "corner", (14, 10), 1, "buttonstate_onlydisable"),
    "GFX_dtp_divider": ("dtp_divider", divider(), "corner", (2, 0), 1, "buttonstate_onlydisable"),
})
for _t, _k in NAV_ICONS.items():
    SPR["GFX_dtp_ico%d" % _t] = ("dtp_ico%d" % _t, (lambda kk: (lambda b: (b.alpha_composite(icon(kk, 16, S_OR2), (7, 7)), b)[1])(shex_badge("", S_OR2, 30)))(_k), "sprite", 0, 1, "buttonstate_onlydisable")
    SPR["GFX_dtp_tile%d" % _t] = ("dtp_tile%d" % _t, stile(_k), "corner", (40, 8), 3, "buttonstate")
    SPR["GFX_dtp_nav%d" % _t] = ("dtp_nav%d" % _t, snav(_k, False), "corner", (40, 8), 3, "buttonstate")
    SPR["GFX_dtp_nav%d_on" % _t] = ("dtp_nav%d_on" % _t, snav(_k, True), "corner", (40, 8), 3, "buttonstate")
os.makedirs(os.path.join(OUT, "gfx/interface/dtp"), exist_ok=True)
gfx = ["spriteTypes = {"]
for name, (fn, img, kind, border, frames, shader) in SPR.items():
    img.save(os.path.join(OUT, "gfx/interface/dtp/%s.dds" % fn))
    if kind == "corner":
        bx, by = border if isinstance(border, tuple) else (border, border)
        gfx.append('\tcorneredTileSpriteType = {\n\t\tname = "%s"\n\t\ttextureFile = "gfx/interface/dtp/%s.dds"\n\t\tborderSize = { x = %d y = %d }\n\t\teffectFile = "gfx/FX/%s.shader"\n%s\t}'
                   % (name, fn, bx, by, shader, ("\t\tnoOfFrames = %d\n" % frames) if frames > 1 else ""))
    else:
        gfx.append('\tspriteType = {\n\t\tname = "%s"\n\t\ttexturefile = "gfx/interface/dtp/%s.dds"\n\t\teffectFile = "gfx/FX/%s.shader"\n\t\tnoOfFrames = %d\n\t}' % (name, fn, shader, frames))
# картинки событий (их рисует art.py) — объявляем, если есть
for f in sorted(os.listdir(os.path.join(OUT, "gfx/event_pictures"))) if os.path.isdir(os.path.join(OUT, "gfx/event_pictures")) else []:
    if f.endswith(".dds"):
        gfx.append('\tspriteType = {\n\t\tname = "GFX_evt_%s"\n\t\ttexturefile = "gfx/event_pictures/%s"\n\t}' % (f[:-4], f))
gfx.append("}")
os.makedirs(os.path.join(OUT, "interface"), exist_ok=True)
open(os.path.join(OUT, "interface/dtp_toolpack.gfx"), "w", encoding="utf-8").write("\n".join(gfx) + "\n")


# ---------------- красные кольца для значков звёзд на галактической карте
meta = json.load(open(META, encoding="utf-8"))
os.makedirs(os.path.join(OUT, "gfx/map/star_classes"), exist_ok=True)
done = set()
def save_dds_mips(img, path):
    """RGBA → DDS A8R8G8B8 с полной цепочкой мипмапов, как у звёзд игры (иначе на отдалении значок пропадает)."""
    import struct
    w, h = img.size
    levels, lw, lh = [], w, h
    cur = img
    while True:
        levels.append(cur)
        if lw == 1 and lh == 1: break
        lw, lh = max(1, lw // 2), max(1, lh // 2)
        cur = img.resize((lw, lh), Image.LANCZOS)
    hdr = struct.pack("<4s31I", b"DDS ", 124, 0x1 | 0x2 | 0x4 | 0x1000 | 0x8 | 0x20000, h, w, w * 4, 0, len(levels),
                      *([0] * 11), 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000,
                      0x1000 | 0x400000 | 0x8, 0, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(hdr)
        for lv in levels:
            r, g, b, a = lv.split()
            f.write(Image.merge("RGBA", (b, g, r, a)).tobytes())
for key, icon in meta["stars"]:
    if icon in done: continue
    done.add(icon)
    src = Image.open(os.path.join(STARTEX, icon + ".dds")).convert("RGBA")
    S = src.width
    # звезда перекрашивается в красный (видно на любом отдалении) + толстое кольцо и точка-маркер
    lum = src.convert("L")
    red = Image.merge("RGBA", (lum.point(lambda v: min(255, int(v * 1.15) + (40 if v > 8 else 0))),
                              lum.point(lambda v: int(v * 0.30)), lum.point(lambda v: int(v * 0.22)), Image.new("L", src.size, 255)))
    big = Image.new("RGBA", (S * 4, S * 4), (0, 0, 0, 0)); dr = ImageDraw.Draw(big)
    c = S * 2; r = S * 1.58
    for wdt, alpha in [(int(S * 0.46), 90), (int(S * 0.30), 170), (int(S * 0.18), 255)]:
        dr.ellipse([c - r, c - r, c + r, c + r], outline=(255, 40, 30, alpha), width=wdt)
    ring = big.resize((S, S), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8))
    out = Image.alpha_composite(red, ring)
    out.putalpha(255)
    save_dds_mips(out, os.path.join(OUT, "gfx/map/star_classes/dtp_mk_%s.dds" % icon))
    # серое кольцо для «режима отметки»: звезда своего цвета + тонкое светлое кольцо
    bg = Image.new("RGBA", (S * 4, S * 4), (0, 0, 0, 0)); dg = ImageDraw.Draw(bg)
    for wdt, alpha in [(int(S * 0.26), 80), (int(S * 0.14), 200)]:
        dg.ellipse([c - r, c - r, c + r, c + r], outline=(200, 205, 215, alpha), width=wdt)
    gout = Image.alpha_composite(src.copy(), bg.resize((S, S), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8)))
    gout.putalpha(255)
    save_dds_mips(gout, os.path.join(OUT, "gfx/map/star_classes/dtp_gy_%s.dds" % icon))
print("колец:", len(done))

GMPAGE = 1
SBK = None
SBV = {}
for _k, _cols in enumerate([["tech", "ap", "col", "sys", "nav", "size", "comm"], ["en", "i_mi", "i_fo", "al", "i_cg", "inf", "un"], ["sc", "i_vm", "i_eg", "i_rc", "i_dm", "i_zr", "i_lm"], ["s_en", "s_mi", "s_fo", "s_al", "s_cg", "s_in", "s_un"]]):
    for _c in _cols: SBV[_c] = _k
def render(fname, tab, sel_lines):
    W, H = meta["W"], meta["H"]
    img = Image.new("RGBA", (W + 40, H + 40), (12, 16, 26, 255))
    tex = {n: Image.open(os.path.join(OUT, "gfx/interface/dtp/%s.dds" % v[0])).convert("RGBA") for n, v in SPR.items() if v[1] is not None}
    fB, fR, fT = ImageFont.truetype(FB, 12), ImageFont.truetype(FR, 12), ImageFont.truetype(FB, 20)
    d = ImageDraw.Draw(img)
    def nine(name, x, y, w, h, b):
        if name not in tex and (name.startswith("GFX_dtp_ann_") or name.startswith("GFX_dtp_si_")):          # значки объявлений рисует art_ann.py
            SPR[name] = (name[4:].lower(), None, "corner", (36, 8), 3, "buttonstate")
            tex[name] = Image.open(os.path.join(OUT, "gfx/interface/dtp/%s.dds" % SPR[name][0])).convert("RGBA")
        spr = tex[name]; fr_n = SPR[name][4]
        fw = spr.width // fr_n; frame = spr.crop((0, 0, fw, spr.height)); fh = frame.height
        if SPR[name][2] != "corner":
            img.alpha_composite(frame.resize((w, h), Image.LANCZOS), (x, y)); return
        bb = SPR[name][3]; bx, by = bb if isinstance(bb, tuple) else (bb, bb)
        bx, by = min(bx, w // 2, fw // 2), min(by, h // 2, fh // 2)
        t = Image.new("RGBA", (w, h))
        for sx0, sx1, dx0, dx1 in [(0, bx, 0, bx), (bx, fw - bx, bx, w - bx), (fw - bx, fw, w - bx, w)]:
            for sy0, sy1, dy0, dy1 in [(0, by, 0, by), (by, fh - by, by, h - by), (fh - by, fh, h - by, h)]:
                if dx1 > dx0 and dy1 > dy0 and sx1 > sx0 and sy1 > sy0: t.paste(frame.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0)), (dx0, dy0))
        img.alpha_composite(t, (x, y))
    nine("GFX_dtp_panel", 20, 20, W, H, 24)
    def vis(it):
        p = it["pot"]; key = it["key"]
        if it["where"] != "main": return False
        if key in ("dtp_b_go_r_off", "dtp_b_go_r_on", "dtp_b_go_r_viol2", "dtp_b_gr_none", "dtp_b_gr_st_off", "dtp_b_gr_st_inf", "dtp_b_gr_st_t2", "dtp_b_gr_off_x", "dtp_b_gr_np_off", "dtp_b_gr_p_clr_x"): return False
        if key.startswith("dtp_b_gr_prot_on_"): return False
        if key in ("dtp_b_se_s_gc0", "dtp_b_se_s_ss1", "dtp_b_se_s_v0", "dtp_b_se_s_c0", "dtp_b_sb_empty", "dtp_b_sb_more", "dtp_b_ss_st_off", "dtp_b_cr_str0", "dtp_b_cr_now_none") or (key.startswith("dtp_b_cr_now_") and key != "dtp_b_cr_now_synth_queen"): return False
        _sb = re.match(r"dtp_b_sb_(\d+)_", key)
        if _sb and int(_sb.group(1)) > 5: return False
        if SBK is not None:
            if re.match(r"dtp_b_sb_(v|h)\d$", key) and key[-1] != str(SBK): return False
            _sbc = re.match(r"dtp_b_sb_(?:c|\d+)_(\w+)$", key)
            if _sbc and _sbc.group(1) in SBV and SBV[_sbc.group(1)] != SBK: return False
        _gk = re.match(r"dtp_b_gr_(a|np_on)_(\d+)(_x)?$", key)
        if _gk and (_gk.group(2) != "1" or _gk.group(3)): return False   # макет показывает состояние «нарушение»
        m = re.findall(r"which = dtp_tab value = (\d+)", p)
        on = "NOT = { check_variable = { which = dtp_tab" in p
        if key.startswith("dtp_b_tab"): return (key.endswith("_on") and key == "dtp_b_tab%d_on" % tab) or (not key.endswith("_on") and key != "dtp_b_tab%d" % tab)
        if m and tab not in [int(v) for v in m]: return False
        notp2 = bool(re.search(r"NOT = \{ check_variable = \{ which = dtp_modpage value = 2 \} \}", p))
        isp2 = bool(re.search(r"which = dtp_modpage value = 2", p)) and not notp2
        if GMPAGE == 1 and isp2: return False
        if GMPAGE >= 2 and notp2: return False
        if not key.startswith("dtp_b_gm_pg"):                      # страницы «Мастера игры»: 1, 2, 3
            if "which = dtp_gmpage value >= 2" in p and GMPAGE != 1: return False
            gp = re.search(r"which = dtp_gmpage value = (\d)", p)
            if gp and int(gp.group(1)) != GMPAGE: return False
        if re.search(r"(?<!NOT = \{ )from = \{\nhas_country_flag = dtp_arm_", p): return False
        for bad in ("dtp_pidx value = 2", "dtp_pidx value = 3", "NOT = { is_variable_set = dtp_pidx }", "role_p", "role_n", "mode_f", "res_none", "res_deny", "res_fail", "noperm", "_on\"", "ac_0", "ac_solo", "ac_claim"):
            if bad in p or bad.strip('"') in key: 
                if bad == "_on\"" and not key.endswith("_on"): continue
                if bad == "_x\"" and not key.endswith("_x"): continue
                return False
        if key.endswith("_on") and not key.startswith("dtp_b_r1_on"): return False
        if key.startswith("dtp_b_r1") and key != "dtp_b_r1_on": return False
        if re.match(r"dtp_b_res_ok_\d+", key) and key != "dtp_b_res_ok_36": return False
        if re.match(r"dtp_b_hd_\w+_\d+_x", key): return False
        if re.search(r"_(name|sub)\w*_\d+_x$", key): return False
        mm = re.search(r"_(name|sub)\w*_(\d+)$", key)
        if mm and mm.group(2) != "1": return False
        if re.match(r"dtp_b_hd_\w+_(\d+)$", key) and not key.endswith("_1"): return False
        if re.match(r"dtp_b_ml(\d+)_n", key) and key not in ("dtp_b_ml3_n",): return False
        if re.match(r"dtp_b_ml(\d+)", key) and int(re.match(r"dtp_b_ml(\d+)", key).group(1)) > 4: return False
        if key.startswith("dtp_b_ml3_o"): return False
        if "dtp_tp_star = yes" in p and "NOT = { dtp_tp_star" not in p: return False
        if "dtp_tp_marked = yes" in p and "NOT = { dtp_tp_marked" not in p: return False
        if key == "dtp_b_ml_more" or key.startswith("dtp_b_cl_prev") or "_h\"" in key: return False
        return True
    subs = {"[dtp_tp_1.Owner.GetName]": "Республика Кзинти", "[dtp_tf_1.Owner.GetName]": "Создатели галактики", "[From.dtp_lastamt]": "25 000", "[From.dtp_in]": "250", "[From.dtp_amount]": "25 000", "[From.dtp_val]": "15", "[From.dtp_years]": "0", "[From.dtp_mcount]": "4",
            "[dtp_tc_1.GetName]": "Республика Кзинти", "[dtp_rcp_1.GetName]": "Создатели галактики", "[dtp_tp_1.GetName]": "Цитадель Бонта",
            "[dtp_tp_1.System.GetName]": "Элион", "[dtp_tf_1.GetName]": "Перекова армада", "[dtp_host.GetName]": "Создатели галактики", "[From.dtp_cpage]": "0", "[dtp_violator.GetName]": "Республика Кзинти", "[dtp_victim.GetName]": "Создатели галактики", "[dtp_violator.dtp_viol]": "1", "[dtp_rule_owner.dtp_rule_endy]": "2245", "[dtp_rule_owner.dtp_rule_len]": "5", "[From.dtp_ry]": "15", "[dtp_sb_owner.dtp_sb_y]": "2231", "[dtp_sess_owner.dtp_sess_y]": "2234", "[dtp_sb_1.dtp_sb_dw]": "451", "[dtp_sb_1.dtp_sb_nav]": "117", "[dtp_sb_1.dtp_sb_size]": "262", "[dtp_sb_1.dtp_sb_comm]": "13", "[dtp_sb_1.dtp_sb_sc]": "497", "[dtp_sb_1.dtp_sb_inf]": "3", "[dtp_sb_1.dtp_sb_un]": "314", "[dtp_sb_1.dtp_sb_i_zr]": "0", "[dtp_sb_1.dtp_sb_i_lm]": "2", "[dtp_sb_2.dtp_sb_dw]": "716", "[dtp_sb_2.dtp_sb_nav]": "69", "[dtp_sb_2.dtp_sb_size]": "319", "[dtp_sb_2.dtp_sb_comm]": "6", "[dtp_sb_2.dtp_sb_sc]": "453", "[dtp_sb_2.dtp_sb_inf]": "3", "[dtp_sb_2.dtp_sb_un]": "262", "[dtp_sb_2.dtp_sb_i_zr]": "3", "[dtp_sb_2.dtp_sb_i_lm]": "0", "[dtp_sb_3.dtp_sb_dw]": "366", "[dtp_sb_3.dtp_sb_nav]": "86", "[dtp_sb_3.dtp_sb_size]": "342", "[dtp_sb_3.dtp_sb_comm]": "9", "[dtp_sb_3.dtp_sb_sc]": "542", "[dtp_sb_3.dtp_sb_inf]": "3", "[dtp_sb_3.dtp_sb_un]": "154", "[dtp_sb_3.dtp_sb_i_zr]": "5", "[dtp_sb_3.dtp_sb_i_lm]": "5", "[dtp_sb_4.dtp_sb_dw]": "716", "[dtp_sb_4.dtp_sb_nav]": "71", "[dtp_sb_4.dtp_sb_size]": "355", "[dtp_sb_4.dtp_sb_comm]": "12", "[dtp_sb_4.dtp_sb_sc]": "1924", "[dtp_sb_4.dtp_sb_inf]": "2", "[dtp_sb_4.dtp_sb_un]": "153", "[dtp_sb_4.dtp_sb_i_zr]": "0", "[dtp_sb_4.dtp_sb_i_lm]": "4", "[dtp_sb_5.dtp_sb_dw]": "256", "[dtp_sb_5.dtp_sb_nav]": "188", "[dtp_sb_5.dtp_sb_size]": "274", "[dtp_sb_5.dtp_sb_comm]": "5", "[dtp_sb_5.dtp_sb_sc]": "782", "[dtp_sb_5.dtp_sb_inf]": "6", "[dtp_sb_5.dtp_sb_un]": "326", "[dtp_sb_5.dtp_sb_i_zr]": "6", "[dtp_sb_5.dtp_sb_i_lm]": "5", "[dtp_sb_1.dtp_sb_s_en]": "8534", "[dtp_sb_1.dtp_sb_s_mi]": "4180", "[dtp_sb_1.dtp_sb_s_fo]": "16491", "[dtp_sb_1.dtp_sb_s_al]": "3752", "[dtp_sb_1.dtp_sb_s_cg]": "1449", "[dtp_sb_1.dtp_sb_s_in]": "642", "[dtp_sb_1.dtp_sb_s_un]": "10282", "[dtp_sb_1.dtp_sb_i_mi]": "76", "[dtp_sb_1.dtp_sb_i_fo]": "153", "[dtp_sb_1.dtp_sb_i_cg]": "157", "[dtp_sb_1.dtp_sb_i_vm]": "5", "[dtp_sb_1.dtp_sb_i_eg]": "4", "[dtp_sb_1.dtp_sb_i_rc]": "12", "[dtp_sb_1.dtp_sb_i_dm]": "2", "[dtp_sb_2.dtp_sb_s_en]": "4279", "[dtp_sb_2.dtp_sb_s_mi]": "7825", "[dtp_sb_2.dtp_sb_s_fo]": "21794", "[dtp_sb_2.dtp_sb_s_al]": "9704", "[dtp_sb_2.dtp_sb_s_cg]": "6200", "[dtp_sb_2.dtp_sb_s_in]": "376", "[dtp_sb_2.dtp_sb_s_un]": "21344", "[dtp_sb_2.dtp_sb_i_mi]": "42", "[dtp_sb_2.dtp_sb_i_fo]": "236", "[dtp_sb_2.dtp_sb_i_cg]": "175", "[dtp_sb_2.dtp_sb_i_vm]": "5", "[dtp_sb_2.dtp_sb_i_eg]": "10", "[dtp_sb_2.dtp_sb_i_rc]": "6", "[dtp_sb_2.dtp_sb_i_dm]": "8", "[dtp_sb_3.dtp_sb_s_en]": "8955", "[dtp_sb_3.dtp_sb_s_mi]": "8904", "[dtp_sb_3.dtp_sb_s_fo]": "9974", "[dtp_sb_3.dtp_sb_s_al]": "18745", "[dtp_sb_3.dtp_sb_s_cg]": "1036", "[dtp_sb_3.dtp_sb_s_in]": "666", "[dtp_sb_3.dtp_sb_s_un]": "23898", "[dtp_sb_3.dtp_sb_i_mi]": "237", "[dtp_sb_3.dtp_sb_i_fo]": "215", "[dtp_sb_3.dtp_sb_i_cg]": "150", "[dtp_sb_3.dtp_sb_i_vm]": "3", "[dtp_sb_3.dtp_sb_i_eg]": "6", "[dtp_sb_3.dtp_sb_i_rc]": "6", "[dtp_sb_3.dtp_sb_i_dm]": "9", "[dtp_sb_4.dtp_sb_s_en]": "10243", "[dtp_sb_4.dtp_sb_s_mi]": "15590", "[dtp_sb_4.dtp_sb_s_fo]": "8442", "[dtp_sb_4.dtp_sb_s_al]": "9308", "[dtp_sb_4.dtp_sb_s_cg]": "3456", "[dtp_sb_4.dtp_sb_s_in]": "553", "[dtp_sb_4.dtp_sb_s_un]": "21324", "[dtp_sb_4.dtp_sb_i_mi]": "152", "[dtp_sb_4.dtp_sb_i_fo]": "156", "[dtp_sb_4.dtp_sb_i_cg]": "185", "[dtp_sb_4.dtp_sb_i_vm]": "7", "[dtp_sb_4.dtp_sb_i_eg]": "11", "[dtp_sb_4.dtp_sb_i_rc]": "5", "[dtp_sb_4.dtp_sb_i_dm]": "2", "[dtp_sb_5.dtp_sb_s_en]": "22878", "[dtp_sb_5.dtp_sb_s_mi]": "2977", "[dtp_sb_5.dtp_sb_s_fo]": "7441", "[dtp_sb_5.dtp_sb_s_al]": "9853", "[dtp_sb_5.dtp_sb_s_cg]": "12459", "[dtp_sb_5.dtp_sb_s_in]": "844", "[dtp_sb_5.dtp_sb_s_un]": "20092", "[dtp_sb_5.dtp_sb_i_mi]": "182", "[dtp_sb_5.dtp_sb_i_fo]": "162", "[dtp_sb_5.dtp_sb_i_cg]": "70", "[dtp_sb_5.dtp_sb_i_vm]": "5", "[dtp_sb_5.dtp_sb_i_eg]": "1", "[dtp_sb_5.dtp_sb_i_rc]": "0", "[dtp_sb_5.dtp_sb_i_dm]": "11", "[dtp_sb_owner.dtp_g_end]": "2400", "[dtp_sb_owner.dtp_g_vic]": "2500", "[dtp_sb_owner.dtp_g_cs]": "1", "[dtp_cs_owner.dtp_cs_base]": "1", "[dtp_cs_owner.dtp_cs_mult]": "2", "[dtp_cs_owner.dtp_cs_eff]": "2", "[From.dtp_cst]": "2", "[dtp_sess_owner.dtp_sess_y]": "2234", "[dtp_sb_1.GetName]": "Республика Кзинти", "[dtp_sb_1.dtp_sb_fp]": "18450", "[dtp_sb_1.dtp_sb_al]": "62", "[dtp_sb_1.dtp_sb_en]": "140", "[dtp_sb_1.dtp_sb_col]": "9", "[dtp_sb_1.dtp_sb_sys]": "24", "[dtp_sb_1.dtp_sb_tech]": "71", "[dtp_sb_1.dtp_sb_ap]": "2", "[dtp_sb_2.GetName]": "Создатели галактики", "[dtp_sb_2.dtp_sb_fp]": "26210", "[dtp_sb_2.dtp_sb_al]": "88", "[dtp_sb_2.dtp_sb_en]": "212", "[dtp_sb_2.dtp_sb_col]": "12", "[dtp_sb_2.dtp_sb_sys]": "31", "[dtp_sb_2.dtp_sb_tech]": "84", "[dtp_sb_2.dtp_sb_ap]": "3", "[dtp_sb_3.GetName]": "Орден Вейла", "[dtp_sb_3.dtp_sb_fp]": "9800", "[dtp_sb_3.dtp_sb_al]": "35", "[dtp_sb_3.dtp_sb_en]": "96", "[dtp_sb_3.dtp_sb_col]": "6", "[dtp_sb_3.dtp_sb_sys]": "17", "[dtp_sb_3.dtp_sb_tech]": "58", "[dtp_sb_3.dtp_sb_ap]": "1", "[dtp_sb_4.GetName]": "Улей Тракс", "[dtp_sb_4.dtp_sb_fp]": "31200", "[dtp_sb_4.dtp_sb_al]": "104", "[dtp_sb_4.dtp_sb_en]": "180", "[dtp_sb_4.dtp_sb_col]": "15", "[dtp_sb_4.dtp_sb_sys]": "38", "[dtp_sb_4.dtp_sb_tech]": "90", "[dtp_sb_4.dtp_sb_ap]": "3", "[dtp_sb_5.GetName]": "Корпорация Нова", "[dtp_sb_5.dtp_sb_fp]": "14070", "[dtp_sb_5.dtp_sb_al]": "51", "[dtp_sb_5.dtp_sb_en]": "175", "[dtp_sb_5.dtp_sb_col]": "8", "[dtp_sb_5.dtp_sb_sys]": "22", "[dtp_sb_5.dtp_sb_tech]": "66", "[dtp_sb_5.dtp_sb_ap]": "2",  "[dtp_tc_1.dtp_np_endy]": "2240", "[dtp_tc_1.dtp_prot_endy]": "2240"}
    names = ["Элион", "Тиуз", "Эбих", "Кирдата"]; owners = ["Создатели галактики", "Республика Кзинти", "", "Республика Кзинти"]
    for it in meta["items"]:
        if not vis(it): continue
        x, y, w, h = it["x"] + 20, it["y"] + 20, it["w"], it["h"]
        if it["sprite"] != "GFX_dtp_label": nine(it["sprite"], x, y, w, h, 8)
        t = it["text"]
        for k, v in subs.items(): t = t.replace(k, v)
        m = re.match(r"dtp_b_ml(\d+)", it["key"])
        if m:
            j = int(m.group(1)) - 1
            t = t.replace("[dtp_ml_%d.GetName]" % (j + 1), names[j]).replace("[dtp_ml_%d.Owner.GetName]" % (j + 1), owners[j])
        t = re.sub(r"\$dtp_cat_(\d+)_name\$", lambda mm: {"1": "Проверка связи", "2": "Дар Хранителей", "3": "Волнения в столице", "4": "Геологическое открытие", "5": "Ремонтная бригада", "6": "Научный прорыв", "7": "Мирное предложение", "8": "Объявление администратора"}.get(mm.group(1), "Слот"), t)
        t = re.sub(r"\[[^\]]*\]", "…", t)
        big = it.get("font") in ("large_title_font", "malgun_goth_24") or it["key"] == "dtp_b_title"
        f = fT if big else (fR if it["label"] else fB)
        base = (230, 236, 245)
        COL = {"Y": (255, 205, 90), "G": (120, 225, 130), "R": (245, 95, 85), "B": (110, 205, 255), "g": (135, 155, 165), "O": (255, 160, 60), "H": (255, 200, 120)}
        segs, cur, col = [], "", base
        i2 = 0
        while i2 < len(t):
            if t[i2] == "§" and i2 + 1 < len(t):
                if cur: segs.append((cur, col)); cur = ""
                col = base if t[i2 + 1] == "!" else COL.get(t[i2 + 1], base); i2 += 2; continue
            cur += t[i2]; i2 += 1
        if cur: segs.append((cur, col))
        if big: segs = [(sx, (255, 205, 90) if it["key"] == "dtp_b_title" or it["key"].startswith("dtp_b_tt") else c) for sx, c in segs]
        plain = "".join(sx for sx, c in segs)
        while d.textlength(plain, font=f) > w - 8 and len(plain) > 3:
            plain = plain[:-2]
        tw = d.textlength(plain, font=f)
        tx = x + 4 if it["label"] else x + (w - tw) / 2
        ty = y + (h - (24 if big else 14)) / 2
        left = len(plain)
        for sx, c in segs:
            if left <= 0: break
            sx = sx[:left]; left -= len(sx)
            if "●" in sx: c = (255, 110, 95)
            d.text((tx, ty), sx, font=f, fill=c); tx += d.textlength(sx, font=f)
    img.convert("RGB").save(os.path.join(PREV, fname))
os.makedirs(PREV, exist_ok=True)

GMPAGE = 2
render("dtp8_gm_org.png", 16, None)
GMPAGE = 3
render("dtp92_gm_rules.png", 16, None)
GMPAGE = 4
SBK = 0
render("dtp96_gm_summary.png", 16, None)
SBK = 1
render("dtp991_gm_income.png", 16, None)
SBK = 2
render("dtp991_gm_science.png", 16, None)
SBK = 3
render("dtp991_gm_stock.png", 16, None)
GMPAGE = 5
render("dtp105_gm_senate.png", 16, None)
render("dtp84_mods_game.png", 4, None)
GMPAGE = 1
for _f, _t in [("dtp85_log.png", 12), ("dtp8_gm.png", 16), ("dtp5_home.png", 15), ("dtp5_resources.png", 3), ("dtp5_systems.png", 1), ("dtp5_planet.png", 5), ("dtp5_country.png", 2), ("dtp5_govern.png", 13), ("dtp5_species.png", 9), ("dtp5_access.png", 11), ("dtp109_fleet.png", 6), ("dtp109_diplo.png", 7)]:
    render(_f, _t, None)
