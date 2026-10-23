# -*- coding: utf-8 -*-
"""Значки и картинки объявлений ведущего (Мастер игры → Организатор партии).
python3 art_ann.py <папка_мода> <папка_для_превью>
Рисует:
  gfx/interface/dtp/dtp_ann_<id>.dds      — кнопка объявления (3 кадра, значок слева, скошенные углы)
  gfx/event_pictures/dtp_ann_<id>.dds     — картинка окна события 450x150 (объявляется в art3.py как GFX_evt_dtp_ann_<id>)
  interface/dtp_announce.gfx              — спрайты кнопок GFX_dtp_ann_<id>
"""
import os, sys, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT, PREV = sys.argv[1], sys.argv[2]
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
TEAL = (120, 232, 205); OR = (244, 166, 58); OR2 = (255, 206, 120); RED = (240, 90, 80); GRN = (110, 225, 130); BLU = (110, 205, 255); VIO = (180, 140, 255)

# id: (ключ значка, цвет)
ANN = {1101: ("pause", OR2), 1102: ("save", BLU), 1103: ("swords", RED), 1104: ("noswords", GRN),
       1105: ("warn", OR), 1106: ("clock", OR2), 1107: ("calendar", BLU), 1108: ("flag", GRN),
       1109: ("council", VIO), 1110: ("headset", TEAL), 1111: ("ballot", OR2), 1112: ("summit", BLU),
       1113: ("crisis", RED), 1114: ("away", (170, 180, 200)), 1115: ("back", GRN), 1116: ("ready", TEAL)}

def draw_icon(kind, S, c):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); C = c + (255,); lw = max(2, int(S * 0.075)); m = S * 0.14
    if kind == "pause":
        d.rounded_rectangle((S * 0.26, m, S * 0.43, S - m), S * 0.04, fill=C); d.rounded_rectangle((S * 0.57, m, S * 0.74, S - m), S * 0.04, fill=C)
    elif kind == "save":
        d.rounded_rectangle((m, m, S - m, S - m), S * 0.06, outline=C, width=lw)
        d.rectangle((S * 0.3, m, S * 0.66, S * 0.38), outline=C, width=lw); d.rectangle((S * 0.28, S * 0.56, S * 0.72, S - m), fill=C)
    elif kind in ("swords", "noswords"):
        for a, b in [((m, m), (S - m, S - m)), ((S - m, m), (m, S - m))]:
            d.line([a, b], fill=C, width=lw)
        d.line([(S * 0.18, S * 0.58), (S * 0.42, S * 0.82)], fill=C, width=lw); d.line([(S * 0.82, S * 0.58), (S * 0.58, S * 0.82)], fill=C, width=lw)
        if kind == "noswords":
            d.ellipse((m * 0.4, m * 0.4, S - m * 0.4, S - m * 0.4), outline=RED + (255,), width=lw)
            d.line([(S * 0.2, S * 0.8), (S * 0.8, S * 0.2)], fill=RED + (255,), width=lw)
    elif kind == "gavel":                                   # молоток председателя
        d.polygon([(S * 0.18, S * 0.36), (S * 0.46, S * 0.08), (S * 0.62, S * 0.24), (S * 0.34, S * 0.52)], fill=C)
        d.line([(S * 0.48, S * 0.38), (S * 0.86, S * 0.76)], fill=C, width=lw + 1); d.rectangle((S * 0.14, S * 0.8, S * 0.62, S * 0.88), fill=C)
    elif kind == "check":
        d.line([(S * 0.16, S * 0.52), (S * 0.4, S * 0.76), (S * 0.86, S * 0.24)], fill=C, width=lw + 1, joint="curve")
    elif kind == "cross":
        d.line([(S * 0.2, S * 0.2), (S * 0.8, S * 0.8)], fill=C, width=lw + 1); d.line([(S * 0.8, S * 0.2), (S * 0.2, S * 0.8)], fill=C, width=lw + 1)
    elif kind in ("plus", "minus"):
        d.ellipse((m, m, S - m, S - m), outline=C, width=lw); d.line([(S * 0.3, S / 2), (S * 0.7, S / 2)], fill=C, width=lw)
        if kind == "plus": d.line([(S / 2, S * 0.3), (S / 2, S * 0.7)], fill=C, width=lw)
    elif kind == "shield":
        d.polygon([(S / 2, m), (S - m, S * 0.26), (S * 0.78, S * 0.72), (S / 2, S - m), (S * 0.22, S * 0.72), (m, S * 0.26)], outline=C, width=lw)
        d.line([(S / 2, S * 0.3), (S / 2, S * 0.7)], fill=C, width=lw)
    elif kind == "crown":
        d.polygon([(m, S * 0.72), (m, S * 0.3), (S * 0.32, S * 0.52), (S / 2, S * 0.2), (S * 0.68, S * 0.52), (S - m, S * 0.3), (S - m, S * 0.72)], fill=C)
        d.rectangle((m, S * 0.76, S - m, S * 0.86), fill=C)
    elif kind == "seats":                                   # места совета: полукруг точек
        for j in range(5):
            a_ = math.pi * (1 - j / 4); d.ellipse((S / 2 + S * 0.32 * math.cos(a_) - S * 0.08, S * 0.66 - S * 0.32 * math.sin(a_) - S * 0.08,
                                                   S / 2 + S * 0.32 * math.cos(a_) + S * 0.08, S * 0.66 - S * 0.32 * math.sin(a_) + S * 0.08), fill=C)
        d.rectangle((S * 0.3, S * 0.74, S * 0.7, S * 0.84), fill=C)
    elif kind == "warn":
        d.polygon([(S / 2, m), (S - m, S - m), (m, S - m)], outline=C, width=lw)
        d.line([(S / 2, S * 0.38), (S / 2, S * 0.64)], fill=C, width=lw); d.ellipse((S * 0.45, S * 0.72, S * 0.55, S * 0.82), fill=C)
    elif kind == "clock":
        d.ellipse((m, m, S - m, S - m), outline=C, width=lw); d.line([(S / 2, S / 2), (S / 2, S * 0.26)], fill=C, width=lw); d.line([(S / 2, S / 2), (S * 0.7, S * 0.6)], fill=C, width=lw)
    elif kind == "calendar":
        d.rounded_rectangle((m, S * 0.22, S - m, S - m), S * 0.05, outline=C, width=lw); d.rectangle((m, S * 0.22, S - m, S * 0.38), fill=C)
        for i in range(3):
            for j in range(2):
                d.rectangle((S * (0.26 + i * 0.18), S * (0.5 + j * 0.16), S * (0.34 + i * 0.18), S * (0.58 + j * 0.16)), fill=C)
        d.line([(S * 0.32, S * 0.12), (S * 0.32, S * 0.28)], fill=C, width=lw); d.line([(S * 0.68, S * 0.12), (S * 0.68, S * 0.28)], fill=C, width=lw)
    elif kind == "flag":
        d.line([(S * 0.24, m), (S * 0.24, S - m)], fill=C, width=lw)
        for i in range(4):
            for j in range(3):
                if (i + j) % 2 == 0: d.rectangle((S * (0.27 + i * 0.12), S * (0.16 + j * 0.11), S * (0.39 + i * 0.12), S * (0.27 + j * 0.11)), fill=C)
        d.rectangle((S * 0.27, S * 0.16, S * 0.75, S * 0.49), outline=C, width=max(1, lw // 2))
    elif kind == "council":
        for i in range(8):
            a = math.radians(i * 45); x, y = S / 2 + S * 0.33 * math.cos(a), S / 2 + S * 0.33 * math.sin(a)
            d.ellipse((x - S * 0.06, y - S * 0.06, x + S * 0.06, y + S * 0.06), fill=C)
        d.ellipse((S * 0.38, S * 0.38, S * 0.62, S * 0.62), outline=C, width=lw)
    elif kind == "headset":
        d.arc((m, m, S - m, S * 0.95), 180, 360, fill=C, width=lw)
        d.rounded_rectangle((m * 0.8, S * 0.46, S * 0.3, S * 0.78), S * 0.05, fill=C); d.rounded_rectangle((S * 0.7, S * 0.46, S - m * 0.8, S * 0.78), S * 0.05, fill=C)
        d.arc((S * 0.3, S * 0.5, S * 0.86, S * 0.94), 20, 110, fill=C, width=max(1, lw // 2)); d.ellipse((S * 0.36, S * 0.82, S * 0.48, S * 0.94), fill=C)
    elif kind == "ballot":
        d.rectangle((m, S * 0.5, S - m, S - m), outline=C, width=lw); d.line([(S * 0.3, S * 0.5), (S * 0.7, S * 0.5)], fill=(0, 0, 0, 255), width=lw)
        d.polygon([(S * 0.36, S * 0.1), (S * 0.68, S * 0.1), (S * 0.68, S * 0.52), (S * 0.36, S * 0.52)], outline=C, width=lw)
        d.line([(S * 0.42, S * 0.3), (S * 0.5, S * 0.4), (S * 0.62, S * 0.2)], fill=C, width=lw)
    elif kind == "summit":
        for cx in (0.3, 0.7):
            d.ellipse((S * (cx - 0.12), S * 0.18, S * (cx + 0.12), S * 0.42), outline=C, width=lw)
            d.arc((S * (cx - 0.2), S * 0.48, S * (cx + 0.2), S * 1.0), 180, 360, fill=C, width=lw)
        d.line([(S * 0.12, S - m), (S * 0.88, S - m)], fill=C, width=lw)
    elif kind == "crisis":
        d.ellipse((S * 0.2, m, S * 0.8, S * 0.66), outline=C, width=lw)
        d.ellipse((S * 0.32, S * 0.3, S * 0.45, S * 0.43), fill=C); d.ellipse((S * 0.55, S * 0.3, S * 0.68, S * 0.43), fill=C)
        for x in (0.36, 0.5, 0.64): d.line([(S * x, S * 0.62), (S * x, S * 0.84)], fill=C, width=lw)
    elif kind == "away":
        d.ellipse((m, m, S - m, S - m), fill=C); d.ellipse((S * 0.3, m * 0.4, S * 1.0, S * 0.7), fill=(0, 0, 0, 0))
        im2 = Image.new("RGBA", (S, S), (0, 0, 0, 0)); ImageDraw.Draw(im2).ellipse((m, m, S - m, S - m), fill=C)
        mk = Image.new("L", (S, S), 255); ImageDraw.Draw(mk).ellipse((S * 0.32, m * 0.2, S * 1.05, S * 0.72), fill=0)
        im2.putalpha(Image.fromarray(np.minimum(np.array(im2.split()[3]), np.array(mk)))); im = im2
    elif kind == "back":
        d.ellipse((m, m, S - m, S - m), outline=C, width=lw); d.line([(S * 0.3, S * 0.52), (S * 0.45, S * 0.67), (S * 0.72, S * 0.36)], fill=C, width=lw)
    elif kind == "ready":
        d.polygon([(S / 2 + S * 0.42 * math.cos(math.radians(60 * j + 30)), S / 2 + S * 0.42 * math.sin(math.radians(60 * j + 30))) for j in range(6)], outline=C, width=lw)
        d.line([(S * 0.3, S * 0.52), (S * 0.45, S * 0.67), (S * 0.72, S * 0.36)], fill=C, width=lw)
    return im

def icon(kind, s, c):
    return draw_icon(kind, s * 4, c).resize((s, s), Image.LANCZOS)

def cham(w, h, c):
    return [(c, 0), (w - 1, 0), (w - 1, h - 1 - c), (w - 1 - c, h - 1), (0, h - 1), (0, c)]

def button(kind, col, size=(160, 30)):
    w, h = size; k = 4; out = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    for i in range(3):
        W2, H2 = w * k, h * k
        top = [(24, 46, 56), (34, 66, 78), (12, 24, 30)][i]; bot = [(12, 26, 34), (20, 42, 52), (6, 14, 18)][i]
        arr = np.zeros((H2, W2, 4), np.uint8)
        for yy in range(H2):
            t = yy / (H2 - 1); arr[yy, :, :3] = [int(top[j] * (1 - t) + bot[j] * t) for j in range(3)]; arr[yy, :, 3] = 238
        im = Image.fromarray(arr, "RGBA"); m = Image.new("L", (W2, H2), 0); pts = cham(W2, H2, 7 * k)
        ImageDraw.Draw(m).polygon(pts, fill=255); im.putalpha(m)
        d = ImageDraw.Draw(im); d.line(pts + [pts[0]], fill=(TEAL if i == 1 else (60, 140, 130)) + (230,), width=k)
        # цветная полоса слева и значок
        d.rectangle((0, 7 * k, 3 * k, H2 - 1), fill=col + (255,))
        fr = im.resize((w, h), Image.LANCZOS)
        fr.alpha_composite(icon(kind, 20, col), (10, (h - 20) // 2))
        out.paste(fr, (i * w, 0))
    return out

def picture(kind, col, seed):
    W, H = 450, 150; r = np.random.default_rng(seed)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.zeros((H, W, 3), np.float32) + np.array([7, 12, 22], np.float32)
    for _ in range(5):
        cx, cy, rad = r.uniform(0, W), r.uniform(0, H), r.uniform(60, 180)
        a = np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * rad ** 2))[..., None]
        img += a * np.array(col, np.float32) * r.uniform(0.12, 0.28)
    for _ in range(260):
        sx, sy = int(r.uniform(0, W)), int(r.uniform(0, H)); b = r.uniform(80, 255)
        img[sy, sx] = np.maximum(img[sy, sx], b)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    # гексагональная сетка справа
    d = ImageDraw.Draw(im)
    for row in range(8):
        for cc in range(12):
            hx, hy = 250 + cc * 17 + (8 if row % 2 else 0), row * 20
            a = int(max(0, (hx - 250) / 200) * 60)
            P = [(hx + 9 * math.cos(math.radians(60 * j + 30)), hy + 9 * math.sin(math.radians(60 * j + 30))) for j in range(6)]
            d.polygon(P, outline=col + (a,))
    # крупный значок со свечением
    big = icon(kind, 96, col)
    glow = big.filter(ImageFilter.GaussianBlur(8))
    im.alpha_composite(glow, (W - 150, 27)); im.alpha_composite(glow, (W - 150, 27)); im.alpha_composite(big, (W - 150, 27))
    # рамка-HUD
    d = ImageDraw.Draw(im); d.line([(14, 14), (90, 14)], fill=OR + (255,), width=2); d.line([(14, 14), (14, 50)], fill=OR + (255,), width=2)
    d.line([(W - 15, H - 15), (W - 90, H - 15)], fill=OR + (255,), width=2); d.line([(W - 15, H - 15), (W - 15, H - 50)], fill=OR + (255,), width=2)
    f = ImageFont.truetype(FB, 15); d.text((28, 24), "GAME MASTER", font=f, fill=OR2 + (255,)); d.text((28, 44), "DEBUG TOOLPACK", font=ImageFont.truetype(FB, 10), fill=OR + (200,))
    return im

# значки кнопок «Сената» (GFX_dtp_si_<ключ>) — тот же стиль, что у объявлений
SI = {"open": ("gavel", GRN), "close": ("gavel", (170, 180, 200)), "pass": ("check", GRN), "reject": ("cross", RED),
      "join": ("plus", TEAL), "a_in": ("plus", BLU), "a_out": ("minus", RED), "c_in": ("seats", VIO), "c_out": ("seats", RED),
      "c_perm": ("seats", OR2), "c_unperm": ("seats", (170, 180, 200)), "sz_p": ("plus", VIO), "sz_m": ("minus", VIO),
      "veto1": ("ballot", OR2), "veto0": ("ballot", (170, 180, 200)), "em1": ("warn", OR), "em0": ("warn", (170, 180, 200)),
      "cus1": ("shield", BLU), "cus0": ("shield", RED), "cus_t": ("clock", BLU), "cus_inf": ("shield", OR2),
      "emp1": ("crown", OR2), "emp0": ("crown", RED), "auth_p": ("plus", OR2), "auth_m": ("minus", OR2), "ecc1": ("crown", TEAL), "ecc0": ("crown", (170, 180, 200))}

def map_mode_icon(S=34):
    """Значок режима карты «Правила партии»: шестиугольник Stellaris с четырьмя цветами правил. 2 кадра: обычный и активный."""
    out = Image.new("RGBA", (S * 2, S), (0, 0, 0, 0))
    for f in range(2):
        k = 6; Z = S * k; im = Image.new("RGBA", (Z, Z), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        c0, r = Z / 2, Z * 0.46
        hexp = [(c0 + r * math.cos(math.radians(60 * j + 30)), c0 + r * math.sin(math.radians(60 * j + 30))) for j in range(6)]
        d.polygon(hexp, fill=(14, 30, 38, 235) if f == 0 else (24, 52, 60, 245))
        cols = [(255, 140, 30), (60, 220, 110), (230, 50, 50), (70, 140, 255)]
        rr = Z * 0.27
        for q, c in enumerate(cols):
            a = 1.0 if f else 0.85
            d.pieslice([c0 - rr, c0 - rr, c0 + rr, c0 + rr], 90 * q - 90, 90 * q, fill=tuple(int(v * a) for v in c) + (255,))
        d.ellipse([c0 - rr * 0.38, c0 - rr * 0.38, c0 + rr * 0.38, c0 + rr * 0.38], fill=(14, 30, 38, 255))
        d.line(hexp + [hexp[0]], fill=(TEAL if f == 0 else OR2) + (255,), width=k * 2)
        out.alpha_composite(im.resize((S, S), Image.LANCZOS), (f * S, 0))
    return out

def main():
    os.makedirs(os.path.join(OUT, "gfx/interface/dtp"), exist_ok=True); os.makedirs(os.path.join(OUT, "gfx/event_pictures"), exist_ok=True)
    gfx = ["spriteTypes = {"]; sheet = Image.new("RGBA", (4 * 470, 4 * 210), (10, 14, 22, 255))
    for n, (eid, (kind, col)) in enumerate(ANN.items()):
        b = button(kind, col); b.save(os.path.join(OUT, "gfx/interface/dtp/dtp_ann_%d.dds" % eid))
        gfx.append('\tcorneredTileSpriteType = {\n\t\tname = "GFX_dtp_ann_%d"\n\t\ttextureFile = "gfx/interface/dtp/dtp_ann_%d.dds"\n\t\tborderSize = { x = 36 y = 8 }\n\t\teffectFile = "gfx/FX/buttonstate.shader"\n\t\tnoOfFrames = 3\n\t}' % (eid, eid))
        p = picture(kind, col, eid); p.save(os.path.join(OUT, "gfx/event_pictures/dtp_ann_%d.dds" % eid))
        sheet.alpha_composite(p, ((n % 4) * 470 + 10, (n // 4) * 210 + 10))
        sheet.alpha_composite(b.crop((0, 0, 160, 30)).resize((320, 60)), ((n % 4) * 470 + 10, (n // 4) * 210 + 150))
    for k_, (kind, col) in SI.items():
        button(kind, col).save(os.path.join(OUT, "gfx/interface/dtp/dtp_si_%s.dds" % k_))
        gfx.append('\tcorneredTileSpriteType = {\n\t\tname = "GFX_dtp_si_%s"\n\t\ttextureFile = "gfx/interface/dtp/dtp_si_%s.dds"\n\t\tborderSize = { x = 36 y = 8 }\n\t\teffectFile = "gfx/FX/buttonstate.shader"\n\t\tnoOfFrames = 3\n\t}' % (k_, k_))
    map_mode_icon().save(os.path.join(OUT, "gfx/interface/dtp/dtp_map_mode.dds"))
    gfx.append('\tspriteType = {\n\t\tname = "GFX_dtp_map_mode"\n\t\ttexturefile = "gfx/interface/dtp/dtp_map_mode.dds"\n\t\tnoOfFrames = 2\n\t}')
    gfx.append("}")
    os.makedirs(os.path.join(OUT, "interface"), exist_ok=True)
    open(os.path.join(OUT, "interface/dtp_announce.gfx"), "w", encoding="utf-8").write("\n".join(gfx) + "\n")
    os.makedirs(PREV, exist_ok=True); sheet.convert("RGB").save(os.path.join(PREV, "dtp82_announcements.png"))
    print("объявлений:", len(ANN))

if __name__ == "__main__":
    main()
