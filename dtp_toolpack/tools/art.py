# -*- coding: utf-8 -*-
"""Рисует картинки окон Debug Toolpack (450x150, как у событий Stellaris) и иконку кнопки.
Сохраняет .dds (для игры) и .png (для предпросмотра). Запуск: python3 art.py <папка_мода>"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "dtp_toolpack"
W, H = 450, 150
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
FONT_M = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
if not os.path.exists(FONT_B):
    FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

EN_LABEL = {"main": "MAIN MENU", "access": "ACCESS", "res": "RESOURCES", "mods": "MODIFIERS", "planets": "PLANETS & SYSTEMS",
            "fleets": "FLEETS", "diplo": "DIPLOMACY", "state": "STATES", "species": "SPECIES", "events": "EVENTS",
            "journal": "LOG", "confirm": "CONFIRMATION"}  # вторая (английская) подпись — картинки одни на оба языка
SECTIONS = {  # ключ: (подпись, цвет эмблемы RGB, мотив)
    "main":    ("ГЛАВНОЕ МЕНЮ", (236, 170, 74), "galaxy"),
    "access":  ("ДОСТУП", (120, 200, 255), "shield"),
    "res":     ("РЕСУРСЫ", (255, 196, 80), "crystals"),
    "mods":    ("МОДИФИКАТОРЫ", (190, 140, 255), "rings"),
    "planets": ("ПЛАНЕТЫ И СИСТЕМЫ", (110, 220, 170), "planet"),
    "fleets":  ("ФЛОТЫ", (255, 120, 90), "fleet"),
    "diplo":   ("ДИПЛОМАТИЯ", (130, 210, 255), "link"),
    "state":   ("ГОСУДАРСТВА", (240, 210, 120), "crown"),
    "species": ("РАСЫ", (150, 235, 120), "helix"),
    "events":  ("ИВЕНТЫ", (255, 150, 210), "burst"),
    "journal": ("ЖУРНАЛ", (180, 200, 220), "lines"),
    "confirm": ("ПОДТВЕРЖДЕНИЕ", (255, 110, 80), "warn"),
}

rng = np.random.default_rng(7)

def background(seed):
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.zeros((H, W, 3), np.float32)
    base = np.array([10, 16, 30], np.float32)
    img += base
    # туманность: сумма нескольких мягких пятен
    for _ in range(6):
        cx, cy = r.uniform(0, W), r.uniform(0, H)
        sx, sy = r.uniform(60, 180), r.uniform(30, 90)
        col = np.array(r.choice([[40, 60, 120], [70, 40, 110], [20, 80, 110], [90, 50, 60]]), np.float32)
        g = np.exp(-(((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2))
        img += g[..., None] * col * r.uniform(0.35, 0.8)
    # звёзды
    for _ in range(420):
        sx, sy = int(r.uniform(0, W)), int(r.uniform(0, H))
        b = r.uniform(60, 255) * (r.random() ** 2)
        img[sy, sx] += b
    return img

def glow_layer(draw_fn, color, blur=6, strength=1.6):
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    draw_fn(d, color)
    g = np.asarray(layer.filter(ImageFilter.GaussianBlur(blur)), np.float32) * strength
    s = np.asarray(layer, np.float32)
    return g + s

def motif(d, c, kind, cx=340, cy=75):
    if kind == "galaxy":
        for arm in range(3):
            pts = []
            for i in range(120):
                t = i / 120 * 3.2
                rr = 6 + t * 18
                a = t * 1.9 + arm * 2.09
                pts.append((cx + rr * math.cos(a) * 1.5, cy + rr * math.sin(a) * 0.7))
            d.line(pts, fill=c, width=2)
        d.ellipse([cx - 8, cy - 6, cx + 8, cy + 6], fill=c)
    elif kind == "shield":
        d.polygon([(cx, cy - 46), (cx + 38, cy - 30), (cx + 30, cy + 20), (cx, cy + 46), (cx - 30, cy + 20), (cx - 38, cy - 30)], outline=c, width=3)
        d.ellipse([cx - 9, cy - 18, cx + 9, cy], outline=c, width=3)
        d.rectangle([cx - 3, cy, cx + 3, cy + 22], fill=c)
    elif kind == "crystals":
        for dx, h in [(-34, 50), (0, 70), (34, 44)]:
            d.polygon([(cx + dx, cy - h / 2 - 6), (cx + dx + 15, cy - h / 2 + 12), (cx + dx + 10, cy + h / 2), (cx + dx - 10, cy + h / 2), (cx + dx - 15, cy - h / 2 + 12)], outline=c, width=3)
    elif kind == "rings":
        for k, rr in enumerate([16, 30, 44]):
            d.arc([cx - rr, cy - rr * 0.8, cx + rr, cy + rr * 0.8], 20 + k * 40, 300 + k * 40, fill=c, width=3)
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=c)
    elif kind == "planet":
        d.ellipse([cx - 32, cy - 32, cx + 32, cy + 32], outline=c, width=3)
        d.arc([cx - 60, cy - 16, cx + 60, cy + 16], 160, 380, fill=c, width=3)
        d.arc([cx - 32, cy - 12, cx + 32, cy + 30], 200, 340, fill=c, width=2)
    elif kind == "fleet":
        for oy, ox in [(-26, 0), (0, 26), (26, 0)]:
            x0, y0 = cx - 30 + ox, cy + oy
            d.polygon([(x0 + 42, y0), (x0, y0 - 9), (x0 + 8, y0), (x0, y0 + 9)], outline=c, width=2)
            d.line([(x0 - 22, y0), (x0 - 4, y0)], fill=c, width=1)
    elif kind == "link":
        d.ellipse([cx - 56, cy - 26, cx - 4, cy + 26], outline=c, width=3)
        d.ellipse([cx + 4, cy - 26, cx + 56, cy + 26], outline=c, width=3)
        d.line([(cx - 20, cy), (cx + 20, cy)], fill=c, width=3)
    elif kind == "crown":
        d.polygon([(cx - 40, cy + 22), (cx - 44, cy - 22), (cx - 18, cy), (cx, cy - 34), (cx + 18, cy), (cx + 44, cy - 22), (cx + 40, cy + 22)], outline=c, width=3)
        d.line([(cx - 40, cy + 32), (cx + 40, cy + 32)], fill=c, width=3)
    elif kind == "helix":
        p1, p2 = [], []
        for i in range(90):
            t = i / 90
            yy = cy - 48 + t * 96
            p1.append((cx + 22 * math.sin(t * 9), yy)); p2.append((cx - 22 * math.sin(t * 9), yy))
            if i % 9 == 0:
                d.line([p1[-1], p2[-1]], fill=c, width=1)
        d.line(p1, fill=c, width=3); d.line(p2, fill=c, width=3)
    elif kind == "burst":
        for k in range(12):
            a = k / 12 * math.tau
            r1, r2 = (12, 48) if k % 2 == 0 else (12, 30)
            d.line([(cx + r1 * math.cos(a), cy + r1 * math.sin(a)), (cx + r2 * math.cos(a), cy + r2 * math.sin(a))], fill=c, width=3)
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=c)
    elif kind == "lines":
        for k in range(6):
            yy = cy - 40 + k * 16
            d.line([(cx - 44, yy), (cx - 34, yy)], fill=c, width=3)
            d.line([(cx - 26, yy), (cx + 44 - (k * 13) % 40, yy)], fill=c, width=2)
    elif kind == "warn":
        d.polygon([(cx, cy - 42), (cx + 46, cy + 36), (cx - 46, cy + 36)], outline=c, width=3)
        d.rectangle([cx - 3, cy - 16, cx + 3, cy + 12], fill=c)
        d.rectangle([cx - 3, cy + 20, cx + 3, cy + 26], fill=c)

def hud(d, c):
    m, L = 8, 22
    for (x0, y0, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line([(x0, y0), (x0 + sx * L, y0)], fill=c, width=2)
        d.line([(x0, y0), (x0, y0 + sy * L)], fill=c, width=2)

def picture(key, label, color, kind, seed):
    img = background(seed)
    # сетка-голограмма у эмблемы
    grid = Image.new("RGB", (W, H), (0, 0, 0)); gd = ImageDraw.Draw(grid)
    for gx in range(250, 440, 16): gd.line([(gx, 12), (gx, H - 12)], fill=tuple(int(v * 0.18) for v in color))
    for gy in range(12, H - 12, 16): gd.line([(250, gy), (440, gy)], fill=tuple(int(v * 0.18) for v in color))
    img += np.asarray(grid, np.float32)
    img += glow_layer(lambda d, c: motif(d, c, kind), color, blur=7, strength=1.4)
    img += glow_layer(lambda d, c: hud(d, c), tuple(int(v * 0.8) for v in color), blur=3, strength=0.8)
    # лёгкие строки развёртки
    img[::3] *= 0.92
    # затемнение слева под текст
    x = np.linspace(0, 1, W)[None, :, None]
    img *= (0.55 + 0.45 * np.clip(x * 2.2, 0, 1))
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(pil)
    fb = ImageFont.truetype(FONT_B, 26)
    fm = ImageFont.truetype(FONT_M, 12)
    d.text((24, 22), "DEBUG TOOLPACK", font=fm, fill=tuple(int(v * 0.9) for v in color))
    d.line([(24, 40), (150, 40)], fill=color, width=2)
    # 11.0.8: картинки одни на оба языка — крупно английская подпись, мельче русская (раньше крупно было только по-русски)
    ru_label, label = label, EN_LABEL.get(key, label)
    # одна строка: длинную подпись уменьшаем, а не переносим (иначе налезает на нижнюю строку)
    _sz = 26
    while _sz > 16 and d.textlength(label, font=ImageFont.truetype(FONT_B, _sz)) > 225: _sz -= 1
    fb = ImageFont.truetype(FONT_B, _sz)
    # подпись раздела с переносом при необходимости
    words, lines, cur = label.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=fb) > 230 and cur:
            lines.append(cur); cur = w_
        else:
            cur = t
    lines.append(cur)
    for i, ln in enumerate(lines):
        d.text((24, 50 + i * 30), ln, font=fb, fill=(235, 240, 250))
    fr = ImageFont.truetype(FONT_M, 15)
    d.text((24, 52 + len(lines) * 30), ru_label, font=fr, fill=tuple(int(v * 0.85) for v in color))
    d.text((24, H - 28), "DTP // STELLARIS 4.5", font=fm, fill=(150, 170, 200))
    return pil

def button_icon(size=48):
    """Иконка кнопки Toolpack: шестигранник с гаечным ключом в стиле HUD."""
    s = size * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = (236, 170, 74, 255)
    hexpts = [(s / 2 + s * 0.46 * math.cos(math.radians(60 * k - 30)), s / 2 + s * 0.46 * math.sin(math.radians(60 * k - 30))) for k in range(6)]
    d.polygon(hexpts, fill=(14, 22, 40, 235), outline=c)
    d.line(hexpts + [hexpts[0]], fill=c, width=int(s * 0.05))
    # ключ
    cx, cy = s / 2, s / 2
    d.line([(cx - s * 0.18, cy + s * 0.18), (cx + s * 0.1, cy - s * 0.1)], fill=c, width=int(s * 0.09))
    r = s * 0.13
    d.ellipse([cx + s * 0.04, cy - s * 0.26, cx + s * 0.04 + 2 * r, cy - s * 0.26 + 2 * r], outline=c, width=int(s * 0.07))
    d.polygon([(cx + s * 0.17, cy - s * 0.2), (cx + s * 0.3, cy - s * 0.33), (cx + s * 0.34, cy - s * 0.12)], fill=(0, 0, 0, 0))
    return im.resize((size, size), Image.LANCZOS)

def save(img, rel):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.convert("RGBA").save(p)  # .dds без сжатия (A8R8G8B8)

def main():
    gfx = ["spriteTypes = {"]
    previews = []
    for i, (key, (label, color, kind)) in enumerate(SECTIONS.items()):
        pic = picture(key, label, color, kind, 100 + i)
        save(pic, "gfx/event_pictures/dtp_%s.dds" % key)
        previews.append(pic)
        gfx.append('\tspriteType = {\n\t\tname = "GFX_evt_dtp_%s"\n\t\ttexturefile = "gfx/event_pictures/dtp_%s.dds"\n\t}' % (key, key))
    icon = button_icon(48)
    save(icon, "gfx/interface/dtp/dtp_button.dds")
    gfx.append('\tspriteType = {\n\t\tname = "GFX_dtp_button"\n\t\ttexturefile = "gfx/interface/dtp/dtp_button.dds"\n\t}')
    gfx.append("}")
    p = os.path.join(OUT, "interface/dtp_toolpack.gfx")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write("\n".join(gfx) + "\n")
    # лист предпросмотра
    cols = 2
    sheet = Image.new("RGB", (W * cols + 10, (H + 10) * math.ceil(len(previews) / cols)), (20, 20, 28))
    for i, pv in enumerate(previews):
        sheet.paste(pv, ((i % cols) * (W + 10), (i // cols) * (H + 10)))
    big_icon = icon.resize((96, 96), Image.NEAREST)
    sheet.paste(big_icon, (sheet.width - 106, sheet.height - 106), big_icon)
    sheet.save(sys.argv[2] if len(sys.argv) > 2 else "preview.png")

if __name__ == "__main__":
    main()
