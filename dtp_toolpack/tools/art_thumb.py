# -*- coding: utf-8 -*-
"""Аватарка мода (thumbnail.png 512x512) для лаунчера Paradox и Мастерской Steam.
python3 art_thumb.py <папка_мода> <папка_для_превью>
Рисуется целиком здесь: космос, туманность, шестиугольная эмблема с ключом, надпись."""
import os, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT, PREV = sys.argv[1], sys.argv[2]
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"
S = 512
TEAL = (64, 224, 208); OR = (244, 166, 58); OR2 = (255, 206, 120); HI = (255, 240, 200); INK = (8, 16, 24); VIO = (150, 110, 255)
random.seed(42)

def hexpts(cx, cy, r, rot=-90):
    return [(cx + r * math.cos(math.radians(60 * j + rot)), cy + r * math.sin(math.radians(60 * j + rot))) for j in range(6)]

def background():
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    d = np.hypot(x - S * 0.5, y - S * 0.42) / S
    base = np.stack([8 + 10 * (1 - d), 12 + 16 * (1 - d), 26 + 30 * (1 - d)], -1)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    neb = Image.new("RGBA", (S, S), (0, 0, 0, 0)); nd = ImageDraw.Draw(neb)
    for _ in range(26):                                    # туманность: мягкие пятна бирюзы, фиолета и оранжа
        c = random.choice([TEAL, VIO, OR, (60, 120, 220)])
        r = random.randint(40, 140); cx, cy = random.randint(0, S), random.randint(0, int(S * 0.8))
        nd.ellipse((cx - r, cy - r * 0.6, cx + r, cy + r * 0.6), fill=c + (random.randint(14, 34),))
    img.alpha_composite(neb.filter(ImageFilter.GaussianBlur(38)))
    st = Image.new("RGBA", (S, S), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    for _ in range(420):                                   # звёзды
        x0, y0 = random.random() * S, random.random() * S; b = random.randint(90, 255); r = random.choice([0.6, 0.8, 1.0, 1.4])
        sd.ellipse((x0 - r, y0 - r, x0 + r, y0 + r), fill=(b, b, min(255, b + 20), 255))
    img.alpha_composite(st)
    # слабая спираль галактики за эмблемой
    gl = Image.new("RGBA", (S, S), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
    for arm in range(2):
        for t in np.linspace(0.2, 5.2, 260):
            rr = 18 * math.exp(0.42 * t); a = t + arm * math.pi
            px, py = S / 2 + rr * math.cos(a), S * 0.42 + rr * math.sin(a) * 0.55
            gd.ellipse((px - 2.2, py - 2.2, px + 2.2, py + 2.2), fill=(200, 220, 255, 60))
    img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(3)))
    return img

def emblem(size):
    k = 4; Z = size * k; im = Image.new("RGBA", (Z, Z), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = Z / 2
    # внешний обод: градиент оранж → светлый
    g = Image.new("RGBA", (Z, Z)); gd = ImageDraw.Draw(g)
    for i in range(Z):
        t = i / Z; col = tuple(int(OR[j] * (1 - t) + HI[j] * t) for j in range(3))
        gd.line([(0, i), (Z, i)], fill=col + (255,))
    m = Image.new("L", (Z, Z), 0); ImageDraw.Draw(m).polygon(hexpts(c, c, Z * 0.47), fill=255)
    g.putalpha(m); im.alpha_composite(g)
    d.polygon(hexpts(c, c, Z * 0.40), fill=INK + (255,))
    d.polygon(hexpts(c, c, Z * 0.36), outline=TEAL + (200,), width=int(Z * 0.008))
    # орбита и звезда
    d.ellipse((c - Z * 0.25, c - Z * 0.12, c + Z * 0.25, c + Z * 0.12), outline=TEAL + (150,), width=int(Z * 0.01))
    # ключ: рукоять + кольцо-зев
    w = int(Z * 0.07)
    d.line([(Z * 0.33, Z * 0.67), (Z * 0.58, Z * 0.42)], fill=(235, 255, 250, 255), width=w)
    d.ellipse((Z * 0.29, Z * 0.63, Z * 0.37, Z * 0.71), fill=(235, 255, 250, 255))
    d.ellipse((Z * 0.53, Z * 0.25, Z * 0.75, Z * 0.47), outline=(235, 255, 250, 255), width=int(Z * 0.055))
    d.polygon([(Z * 0.66, Z * 0.24), (Z * 0.76, Z * 0.24), (Z * 0.71, Z * 0.34)], fill=INK + (255,))   # прорезь зева
    # искра-звезда
    sx, sy, sr = Z * 0.36, Z * 0.33, Z * 0.055
    d.polygon([(sx, sy - sr), (sx + sr * 0.25, sy - sr * 0.25), (sx + sr, sy), (sx + sr * 0.25, sy + sr * 0.25),
               (sx, sy + sr), (sx - sr * 0.25, sy + sr * 0.25), (sx - sr, sy), (sx - sr * 0.25, sy - sr * 0.25)], fill=OR2 + (255,))
    return im.resize((size, size), Image.LANCZOS)

def spaced(d, xy, text, font, fill, sp):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill); x += d.textlength(ch, font=font) + sp

def text_w(d, text, font, sp): return sum(d.textlength(ch, font=font) + sp for ch in text) - sp

def main():
    img = background()
    E = 270; ex, ey = (S - E) // 2, 52
    glow = emblem(E); gl = Image.new("RGBA", (S, S), (0, 0, 0, 0)); gl.alpha_composite(glow, (ex, ey))
    halo = gl.filter(ImageFilter.GaussianBlur(22)); img.alpha_composite(halo); img.alpha_composite(halo)
    d = ImageDraw.Draw(img)
    # кольцо-HUD вокруг эмблемы
    hp = hexpts(S / 2, ey + E / 2, E * 0.60)
    d.line(hp + [hp[0]], fill=TEAL + (120,), width=2)
    for (x0, y0) in hp:
        d.ellipse((x0 - 4, y0 - 4, x0 + 4, y0 + 4), fill=TEAL + (230,))
    img.alpha_composite(gl)
    d = ImageDraw.Draw(img)
    # подложка под надпись
    band = Image.new("RGBA", (S, S), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
    bd.rectangle((0, 352, S, 470), fill=(4, 10, 18, 190)); img.alpha_composite(band.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(FB, 64); f2 = ImageFont.truetype(FB, 38); f3 = ImageFont.truetype(FR, 19)
    for txt, f, y, col, sp in [("DEBUG", f1, 352, HI, 6), ("TOOLPACK", f2, 418, OR2, 7)]:
        tw = text_w(d, txt, f, sp); x = (S - tw) / 2
        sh = Image.new("RGBA", (S, S), (0, 0, 0, 0)); spaced(ImageDraw.Draw(sh), (x, y), txt, f, (244, 166, 58, 255), sp)
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
        d = ImageDraw.Draw(img); spaced(d, (x, y), txt, f, col + (255,), sp)
    sub = "STELLARIS 4.5  ·  GAME MASTER  ·  RU / EN"
    tw = d.textlength(sub, font=f3); d.text(((S - tw) / 2, 474), sub, font=f3, fill=TEAL + (255,))
    # уголки-скобки как в окне мода
    L, Wd = 46, 4
    for (x0, y0, sx, sy) in [(12, 12, 1, 1), (S - 13, 12, -1, 1), (12, S - 13, 1, -1), (S - 13, S - 13, -1, -1)]:
        d.line([(x0, y0), (x0 + L * sx, y0)], fill=OR + (255,), width=Wd); d.line([(x0, y0), (x0, y0 + L * sy)], fill=OR + (255,), width=Wd)
    d.rectangle((6, 6, S - 7, S - 7), outline=TEAL + (90,), width=2)
    img.convert("RGB").save(os.path.join(OUT, "thumbnail.png"), optimize=True)
    os.makedirs(PREV, exist_ok=True); img.convert("RGB").save(os.path.join(PREV, "dtp_thumbnail.png"))
    print("аватарка:", os.path.getsize(os.path.join(OUT, "thumbnail.png")) // 1024, "КБ")

if __name__ == "__main__":
    main()
