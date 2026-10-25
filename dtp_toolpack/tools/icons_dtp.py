# -*- coding: utf-8 -*-
"""11.1: значки кнопок Debug Toolpack. draw(kind, size) -> RGBA (рисуется в 4x и уменьшается).
Цвет по умолчанию — COL[kind]; ресурсы окрашены как в игре."""
import math
from PIL import Image, ImageDraw, ImageFont

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
GOLD = (245, 196, 80); TEAL = (120, 225, 200); BLUE = (130, 200, 255); RED = (255, 110, 100); GREEN = (120, 225, 140)
GREY = (175, 195, 200); VIO = (190, 150, 255); ORANGE = (250, 160, 70)

COL = {
    # ресурсы
    "energy": (255, 214, 60), "minerals": (232, 92, 80), "food": (128, 214, 90), "alloys": (196, 128, 236), "goods": (242, 162, 70),
    "influence": (206, 112, 226), "unity": (110, 222, 186), "physics": (92, 172, 255), "society": (104, 222, 132), "engineering": (242, 152, 62),
    "gases": (150, 220, 120), "crystals": (255, 120, 170), "motes": (230, 160, 90), "dark_matter": (170, 120, 255), "living_metal": (170, 210, 230),
    "zro": (120, 200, 255), "nanites": (190, 200, 210), "artifacts": (230, 190, 110), "threads": (210, 160, 255),
    # действия
    "plus": GREEN, "minus": RED, "equal": BLUE, "repeat": GOLD, "undo": ORANGE, "trash": RED, "give": BLUE, "jump": BLUE, "wrench": BLUE,
    "mark": (255, 110, 95), "unmark": GREY, "map": TEAL, "eye": TEAL, "check": GREEN, "cross": RED, "people": GOLD, "crown": GOLD,
    "shield": BLUE, "swords": RED, "dove": GREEN, "handshake": GOLD, "gate": TEAL, "gate_closed": ORANGE, "heart": (255, 120, 150),
    "heart_broken": RED, "clock": GOLD, "flask": (104, 222, 132), "gear": ORANGE, "flag": GOLD, "warn": ORANGE, "skull": RED,
    "leader": GOLD, "unlock": GOLD, "chip": BLUE, "book": GOLD, "dna": GREEN, "chain": GREY, "house": TEAL, "grid": TEAL, "cloud": VIO,
    "storm": VIO, "tentacle": VIO, "planet": TEAL, "star": GOLD, "hex": TEAL, "arrow_l": GREY, "arrow_r": GREY, "refresh": GREEN,
    "home": TEAL, "target": GOLD, "keyboard": GREY, "ship1": (170, 210, 225), "ship2": (170, 210, 225), "ship3": (170, 210, 225),
    "ship4": (170, 210, 225), "ship5": (170, 210, 225), "ship6": (170, 210, 225), "ship7": (170, 210, 225), "ship8": (130, 220, 200),
    "ship9": (240, 190, 110), "fleet": BLUE, "ethic": VIO, "build": TEAL, "district": TEAL, "pct": BLUE, "log": GREY, "test": GREEN,
    "gavel": GREEN, "ballot": GOLD, "bolt": ORANGE, "station": TEAL, "colony": GREEN, "stab": BLUE, "growth": GREEN, "speed": BLUE,
    "armor": GREY, "range": ORANGE, "happy": GOLD, "crime": RED, "anchor": BLUE, "gm": GOLD, "power": ORANGE, "sun": GOLD,
}

def _poly_star(cx, cy, r1, r2, n=5, rot=-90):
    return [(cx + math.cos(math.radians(rot + i * 180 / n)) * (r1 if i % 2 == 0 else r2),
             cy + math.sin(math.radians(rot + i * 180 / n)) * (r1 if i % 2 == 0 else r2)) for i in range(2 * n)]

def draw(kind, s, col=None):
    S = s * 4; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = col or COL.get(kind, GOLD); C = tuple(col) + (255,)
    dark = tuple(int(v * 0.55) for v in col) + (255,); hole = (0, 0, 0, 0)
    m = S * 0.1; lw = max(4, int(S * 0.1)); h2 = S / 2
    def ln(pts, w=lw, c=C): d.line(pts, fill=c, width=int(w), joint="curve")
    def circ(cx, cy, r, **kw): d.ellipse((cx - r, cy - r, cx + r, cy + r), **kw)
    k = kind
    # ---------------- ресурсы
    if k in ("energy", "bolt", "power"):
        d.polygon([(S*.6, m), (S*.2, S*.56), (S*.46, S*.56), (S*.38, S-m), (S*.82, S*.42), (S*.55, S*.42), (S*.68, m)], fill=C)
    elif k == "minerals":
        d.polygon([(h2, m), (S*.86, S*.38), (S*.68, S-m), (S*.32, S-m), (S*.14, S*.38)], fill=C)
        ln([(S*.14, S*.38), (h2, S*.52), (S*.86, S*.38)], lw*.5, dark); ln([(h2, S*.52), (h2, S-m)], lw*.5, dark)
    elif k == "food":
        circ(h2, S*.56, S*.34, fill=C); ln([(h2, m), (h2, S*.3)], lw*.8, dark)
        d.ellipse((S*.5, m, S*.82, S*.3), fill=dark)
    elif k == "alloys":
        d.polygon([(S*.1, S*.58), (S*.32, S*.32), (S*.9, S*.32), (S*.68, S*.58)], fill=C)
        d.polygon([(S*.1, S*.58), (S*.68, S*.58), (S*.68, S*.8), (S*.1, S*.8)], fill=dark)
        d.polygon([(S*.68, S*.58), (S*.9, S*.32), (S*.9, S*.54), (S*.68, S*.8)], fill=tuple(int(v*.4) for v in col) + (255,))
    elif k == "goods":
        d.rectangle((S*.18, S*.32, S*.82, S*.88), fill=C); d.rectangle((S*.12, S*.18, S*.88, S*.34), fill=dark)
        ln([(h2, S*.18), (h2, S*.88)], lw*.5, dark)
    elif k == "influence":
        d.polygon(_poly_star(h2, h2, S*.44, S*.18, 4, -90), fill=C)
    elif k == "unity":
        circ(h2, h2, S*.38, outline=C, width=lw); circ(h2, h2, S*.14, fill=C)
    elif k == "physics":
        for a in (0, 60, 120):
            e = Image.new("RGBA", (S, S)); ImageDraw.Draw(e).ellipse((m, S*.36, S-m, S*.64), outline=C, width=int(lw*.6))
            im.alpha_composite(e.rotate(a, resample=Image.BICUBIC))
        circ(h2, h2, S*.09, fill=C)
    elif k in ("society", "flask"):
        d.polygon([(S*.38, m), (S*.62, m), (S*.62, S*.4), (S*.86, S-m), (S*.14, S-m), (S*.38, S*.4)], fill=C)
        d.rectangle((S*.3, S*.62, S*.7, S*.68), fill=dark)
    elif k in ("engineering", "gear"):
        for i in range(8):
            a = i * math.pi / 4; ln([(h2, h2), (h2 + math.cos(a)*S*.43, h2 + math.sin(a)*S*.43)], S*.15)
        circ(h2, h2, S*.3, fill=C); circ(h2, h2, S*.12, fill=hole)
    elif k == "gases":
        for cx, cy, r in ((.35, .58, .22), (.6, .5, .26), (.5, .68, .2), (.72, .66, .17)): circ(S*cx, S*cy, S*r, fill=C)
        d.rectangle((S*.15, S*.72, S*.88, S*.86), fill=hole)
    elif k == "crystals":
        d.polygon([(h2, m), (S*.82, S*.42), (h2, S-m), (S*.18, S*.42)], outline=C, width=lw)
        ln([(S*.18, S*.42), (S*.82, S*.42)], lw*.6)
    elif k == "motes":
        for cx, cy, r in ((.3, .3, .12), (.62, .25, .09), (.7, .6, .14), (.36, .68, .1), (.5, .48, .07)): circ(S*cx, S*cy, S*r, fill=C)
    elif k == "dark_matter":
        circ(h2, h2, S*.24, fill=C); d.arc((m, S*.3, S-m, S*.7), 200, 340, fill=C, width=int(lw*.6)); d.arc((m, S*.3, S-m, S*.7), 20, 160, fill=C, width=int(lw*.6))
    elif k == "living_metal":
        d.polygon([(S*.2, S*.7), (S*.3, S*.3), (S*.55, S*.18), (S*.82, S*.36), (S*.78, S*.72), (S*.5, S*.84)], fill=C)
        circ(S*.45, S*.45, S*.08, fill=dark)
    elif k == "zro":
        for i in range(3): d.arc((S*(.12 + i*.11), S*(.12 + i*.11), S*(.88 - i*.11), S*(.88 - i*.11)), 30 + i*90, 300 + i*90, fill=C, width=int(lw*.6))
    elif k == "nanites":
        for i in range(3):
            for j in range(3): circ(S*(.25 + i*.25), S*(.25 + j*.25), S*.08, fill=C)
    elif k == "artifacts":
        d.polygon([(S*.36, m), (S*.64, m), (S*.6, S*.24), (S*.8, S*.5), (S*.66, S*.9), (S*.34, S*.9), (S*.2, S*.5), (S*.4, S*.24)], fill=C)
        ln([(S*.28, S*.52), (S*.72, S*.52)], lw*.5, dark)
    elif k == "threads":
        for i in range(3):
            pts = [(S*(.1 + t*.08), S*(.3 + i*.2) + math.sin(t*.9) * S*.06) for t in range(11)]; ln(pts, lw*.55)
    # ---------------- действия
    elif k == "plus":
        d.rectangle((S*.41, m, S*.59, S-m), fill=C); d.rectangle((m, S*.41, S-m, S*.59), fill=C)
    elif k == "minus":
        d.rectangle((m, S*.41, S-m, S*.59), fill=C)
    elif k == "equal":
        d.rectangle((m, S*.28, S-m, S*.42), fill=C); d.rectangle((m, S*.58, S-m, S*.72), fill=C)
    elif k in ("repeat", "refresh"):
        d.arc((m*1.3, m*1.3, S-m*1.3, S-m*1.3), 40, 330, fill=C, width=lw); d.polygon([(S*.92, S*.22), (S*.92, S*.52), (S*.64, S*.42)], fill=C)
    elif k == "undo":
        d.arc((S*.2, S*.25, S*.9, S*.9), 190, 90, fill=C, width=lw); d.polygon([(m, S*.5), (S*.38, S*.28), (S*.38, S*.68)], fill=C)
    elif k == "trash":
        d.rectangle((S*.24, S*.32, S*.76, S-m), outline=C, width=lw); d.rectangle((S*.14, S*.18, S*.86, S*.27), fill=C)
        d.rectangle((S*.4, m*.8, S*.6, S*.2), fill=C)
        for x in (.41, .59): ln([(S*x, S*.44), (S*x, S*.78)], lw*.45)
    elif k == "give":
        ln([(m, h2), (S*.72, h2)]); d.polygon([(S-m*.6, h2), (S*.62, S*.22), (S*.62, S*.78)], fill=C)
    elif k == "arrow_r":
        d.polygon([(S*.3, S*.18), (S*.78, h2), (S*.3, S*.82)], fill=C)
    elif k == "arrow_l":
        d.polygon([(S*.7, S*.18), (S*.22, h2), (S*.7, S*.82)], fill=C)
    elif k == "jump":
        circ(S*.27, h2, S*.17, outline=C, width=int(lw*.8)); ln([(S*.44, h2), (S*.78, h2)]); d.polygon([(S-m*.6, h2), (S*.7, S*.28), (S*.7, S*.72)], fill=C)
    elif k == "wrench":
        ln([(S*.2, S*.8), (S*.6, S*.4)], S*.17); circ(S*.66, S*.34, S*.24, fill=C); d.polygon([(S*.66, S*.34), (S*.95, S*.05), (S*.95, S*.4)], fill=hole)
        circ(S*.66, S*.34, S*.08, fill=hole)
    elif k == "mark":
        circ(h2, S*.4, S*.3, fill=C); d.polygon([(S*.26, S*.5), (S*.74, S*.5), (h2, S-m*.5)], fill=C); circ(h2, S*.4, S*.12, fill=hole)
    elif k in ("unmark", "cross"):
        ln([(S*.2, S*.2), (S*.8, S*.8)], lw*1.2); ln([(S*.8, S*.2), (S*.2, S*.8)], lw*1.2)
    elif k == "check":
        ln([(S*.14, S*.52), (S*.4, S*.78), (S*.88, S*.22)], lw*1.2)
    elif k == "map":
        d.polygon([(m, S*.22), (S*.36, m), (S*.64, S*.22), (S-m, m), (S-m, S*.78), (S*.64, S-m), (S*.36, S*.78), (m, S-m)], outline=C, width=int(lw*.7))
        ln([(S*.36, m), (S*.36, S*.78)], lw*.5); ln([(S*.64, S*.22), (S*.64, S-m)], lw*.5)
    elif k == "eye":
        d.chord((m, S*.22, S-m, S*.95), 200, 340, fill=C); d.chord((m, S*.05, S-m, S*.78), 20, 160, fill=C)
        circ(h2, h2, S*.17, fill=hole); circ(h2, h2, S*.09, fill=C)
    elif k == "people":
        for cx, sc in ((.32, .8), (.68, .8), (.5, 1.0)):
            circ(S*cx, S*(.3 if sc == 1 else .34), S*.12*sc, fill=C)
            d.chord((S*(cx - .2*sc), S*(.5 if sc == 1 else .54), S*(cx + .2*sc), S*(1.1)), 180, 360, fill=C)
    elif k == "leader":
        circ(h2, S*.3, S*.18, fill=C); d.chord((S*.18, S*.54, S*.82, S*1.2), 180, 360, fill=C)
    elif k in ("crown", "gm"):
        d.polygon([(m, S*.74), (m, S*.28), (S*.32, S*.5), (h2, S*.16), (S*.68, S*.5), (S-m, S*.28), (S-m, S*.74)], fill=C)
        d.rectangle((m, S*.78, S-m, S*.88), fill=C)
    elif k in ("shield", "stab"):
        d.polygon([(h2, m), (S-m, S*.24), (S*.8, S*.7), (h2, S-m*.6), (S*.2, S*.7), (m, S*.24)], fill=C)
        d.polygon([(h2, S*.22), (S*.74, S*.32), (S*.62, S*.66), (h2, S*.8)], fill=dark)
    elif k == "armor":
        d.polygon([(S*.2, m), (S*.8, m), (S-m, S*.4), (h2, S-m), (m, S*.4)], fill=C); ln([(S*.2, S*.4), (S*.8, S*.4)], lw*.5, dark)
    elif k == "swords":
        for a, b in (((m, m), (S-m, S-m)), ((S-m, m), (m, S-m))): ln([a, b])
        ln([(S*.16, S*.6), (S*.4, S*.84)]); ln([(S*.84, S*.6), (S*.6, S*.84)])
    elif k == "dove":
        d.polygon([(m, S*.5), (S*.4, S*.36), (S*.7, m), (S*.66, S*.42), (S-m, S*.5), (S*.6, S*.7), (S*.3, S*.66)], fill=C)
    elif k == "handshake":
        ln([(m, S*.62), (S*.36, S*.42), (S*.64, S*.6), (S-m, S*.4)], lw*1.2); ln([(S*.36, S*.42), (S*.6, S*.36), (S*.8, S*.5)], lw*.8)
    elif k in ("gate", "gate_closed"):
        d.rectangle((m, S*.2, S*.26, S-m), fill=C); d.rectangle((S*.74, S*.2, S-m, S-m), fill=C); d.rectangle((m, m, S-m, S*.24), fill=C)
        if k == "gate_closed":
            for x in (.38, .5, .62): d.rectangle((S*(x - .04), S*.3, S*(x + .04), S-m), fill=C)
    elif k in ("heart", "heart_broken", "happy"):
        circ(S*.33, S*.38, S*.21, fill=C); circ(S*.67, S*.38, S*.21, fill=C); d.polygon([(S*.13, S*.45), (S*.87, S*.45), (h2, S*.9)], fill=C)
        if k == "heart_broken": ln([(S*.52, S*.22), (S*.42, S*.48), (S*.58, S*.6), (S*.48, S*.88)], lw*.5, hole)
    elif k == "clock":
        circ(h2, h2, S*.4, outline=C, width=lw); ln([(h2, h2), (h2, S*.24)], lw*.8); ln([(h2, h2), (S*.7, S*.62)], lw*.8)
    elif k == "flag":
        ln([(S*.22, m), (S*.22, S-m)], lw*.8); d.polygon([(S*.26, m), (S*.86, S*.26), (S*.26, S*.48)], fill=C)
    elif k == "warn":
        d.polygon([(h2, m), (S-m, S-m), (m, S-m)], fill=C); d.rectangle((S*.46, S*.36, S*.54, S*.66), fill=hole); circ(h2, S*.77, S*.05, fill=hole)
    elif k in ("skull", "crime"):
        circ(h2, S*.42, S*.32, fill=C); d.rectangle((S*.32, S*.6, S*.68, S*.86), fill=C)
        circ(S*.38, S*.42, S*.08, fill=hole); circ(S*.62, S*.42, S*.08, fill=hole)
        for x in (.42, .58): ln([(S*x, S*.72), (S*x, S*.86)], lw*.4, hole)
    elif k == "unlock":
        d.rectangle((S*.18, S*.46, S*.82, S-m), fill=C); d.arc((S*.28, m, S*.72, S*.62), 180, 330, fill=C, width=lw)
        circ(h2, S*.66, S*.06, fill=hole)
    elif k == "chip":
        d.rectangle((S*.24, S*.24, S*.76, S*.76), fill=C); d.rectangle((S*.38, S*.38, S*.62, S*.62), fill=dark)
        for t in (.34, .5, .66):
            ln([(S*t, m), (S*t, S*.24)], lw*.4); ln([(S*t, S*.76), (S*t, S-m)], lw*.4); ln([(m, S*t), (S*.24, S*t)], lw*.4); ln([(S*.76, S*t), (S-m, S*t)], lw*.4)
    elif k == "book":
        d.polygon([(m, S*.2), (h2, S*.3), (h2, S-m), (m, S*.8)], fill=C); d.polygon([(S-m, S*.2), (h2, S*.3), (h2, S-m), (S-m, S*.8)], fill=dark)
    elif k == "dna":
        for t in range(13):
            y = m + t * (S - 2*m) / 12; a = t * 0.55
            x1 = h2 + math.sin(a) * S*.28; x2 = h2 - math.sin(a) * S*.28
            if t % 2 == 0: ln([(x1, y), (x2, y)], lw*.35)
            circ(x1, y, S*.05, fill=C); circ(x2, y, S*.05, fill=dark)
    elif k == "chain":
        for cx, cy in ((.32, .36), (.68, .64)): d.ellipse((S*(cx - .22), S*(cy - .15), S*(cx + .22), S*(cy + .15)), outline=C, width=int(lw*.8))
    elif k in ("house", "build"):
        d.polygon([(h2, m), (S-m, S*.48), (m, S*.48)], fill=C); d.rectangle((S*.22, S*.48, S*.78, S-m), fill=C); d.rectangle((S*.42, S*.64, S*.58, S-m), fill=hole)
    elif k in ("grid", "district"):
        for i in range(3):
            for j in range(3): d.rectangle((S*(.14 + i*.25), S*(.14 + j*.25), S*(.34 + i*.25), S*(.34 + j*.25)), fill=C if (i + j) % 2 == 0 else dark)
    elif k in ("cloud",):
        for cx, cy, r in ((.32, .6, .2), (.55, .45, .26), (.74, .62, .18)): circ(S*cx, S*cy, S*r, fill=C)
        d.rectangle((S*.12, S*.62, S*.92, S*.8), fill=C)
    elif k == "storm":
        for cx, cy, r in ((.32, .42, .18), (.55, .32, .22), (.74, .44, .16)): circ(S*cx, S*cy, S*r, fill=C)
        d.rectangle((S*.14, S*.42, S*.9, S*.56), fill=C); d.polygon([(S*.56, S*.56), (S*.4, S*.8), (S*.52, S*.8), (S*.44, S-m*.3), (S*.68, S*.7), (S*.56, S*.7), (S*.64, S*.56)], fill=GOLD + (255,))
    elif k == "tentacle":
        for i, x in enumerate((.25, .5, .75)):
            pts = [(S*x + math.sin(t*.8 + i) * S*.08, S*(.12 + t*.08)) for t in range(10)]; ln(pts, lw*(1 - i*.15))
    elif k in ("planet", "colony"):
        circ(h2, h2, S*.28, fill=C); d.arc((m*.5, S*.32, S-m*.5, S*.68), 160, 380, fill=C, width=int(lw*.55))
        if k == "colony": circ(S*.42, S*.42, S*.07, fill=dark)
    elif k in ("star", "sun"):
        d.polygon(_poly_star(h2, h2, S*.44, S*.2, 5), fill=C)
    elif k == "hex":
        d.polygon([(h2 + S*.42*math.cos(math.radians(60*j + 30)), h2 + S*.42*math.sin(math.radians(60*j + 30))) for j in range(6)], outline=C, width=lw)
    elif k == "home":
        d.polygon([(h2, m), (S-m, S*.48), (m, S*.48)], outline=C, width=lw); d.rectangle((S*.26, S*.48, S*.74, S-m), outline=C, width=lw)
    elif k == "target":
        circ(h2, h2, S*.4, outline=C, width=lw); circ(h2, h2, S*.13, fill=C)
    elif k == "keyboard":
        d.rectangle((m, S*.28, S-m, S*.74), outline=C, width=int(lw*.7))
        for i in range(4): d.rectangle((S*(.2 + i*.16), S*.38, S*(.3 + i*.16), S*.48), fill=C)
        d.rectangle((S*.26, S*.56, S*.74, S*.64), fill=C)
    elif k == "station":
        circ(h2, h2, S*.16, fill=C); d.rectangle((m, S*.45, S-m, S*.55), fill=C); d.rectangle((S*.45, m, S*.55, S-m), fill=C)
        for cx, cy in ((m, h2), (S-m, h2), (h2, m), (h2, S-m)): circ(cx, cy, S*.07, fill=C)
    elif k == "growth":
        ln([(m, S*.8), (S*.4, S*.48), (S*.58, S*.62), (S*.86, S*.24)], lw); d.polygon([(S-m*.4, S*.12), (S*.66, S*.2), (S*.86, S*.4)], fill=C)
    elif k == "speed":
        for y, w_ in ((.32, .5), (.5, .7), (.68, .5)): ln([(S*(.9 - w_), S*y), (S*.9, S*y)], lw*.8)
    elif k == "range":
        circ(h2, h2, S*.4, outline=C, width=int(lw*.6)); circ(h2, h2, S*.22, outline=C, width=int(lw*.6)); circ(h2, h2, S*.07, fill=C)
    elif k == "anchor":
        circ(h2, S*.2, S*.09, outline=C, width=int(lw*.6)); ln([(h2, S*.28), (h2, S*.88)], lw*.8); ln([(S*.3, S*.42), (S*.7, S*.42)], lw*.7)
        d.arc((S*.18, S*.4, S*.82, S*.92), 20, 160, fill=C, width=int(lw*.8))
    elif k == "pct":
        f = ImageFont.truetype(FB, int(S * .82)); d.text((h2, h2), "%", font=f, fill=C, anchor="mm")
    elif k == "log":
        for i in range(4): d.rectangle((S*.18, S*(.18 + i*.18), S*(.82 if i % 2 == 0 else .64), S*(.27 + i*.18)), fill=C)
    elif k == "test":
        d.polygon([(S*.38, m), (S*.62, m), (S*.62, S*.4), (S*.86, S-m), (S*.14, S-m), (S*.38, S*.4)], outline=C, width=int(lw*.7))
        d.polygon([(S*.26, S*.68), (S*.74, S*.68), (S*.84, S-m*1.2), (S*.16, S-m*1.2)], fill=C)
    elif k == "ethic":
        circ(h2, h2, S*.38, outline=C, width=int(lw*.7)); d.polygon(_poly_star(h2, h2, S*.24, S*.1, 4, -90), fill=C)
    elif k == "gavel":
        d.polygon([(S*.14, S*.36), (S*.44, S*.06), (S*.62, S*.24), (S*.32, S*.54)], fill=C); ln([(S*.48, S*.4), (S*.88, S*.8)], lw*1.1)
        d.rectangle((S*.1, S*.82, S*.6, S*.92), fill=C)
    elif k == "ballot":
        d.rectangle((m, S*.5, S-m, S-m), outline=C, width=int(lw*.8)); d.rectangle((S*.34, m, S*.66, S*.56), fill=C)
        ln([(S*.4, S*.32), (S*.48, S*.42), (S*.6, S*.2)], lw*.5, dark)
    elif k == "fleet":
        for dx, dy in ((0, -.18), (-.2, .14), (.2, .14)):
            d.polygon([(S*(.5 + dx) + S*.16, S*(.5 + dy)), (S*(.5 + dx) - S*.12, S*(.5 + dy) - S*.09), (S*(.5 + dx) - S*.12, S*(.5 + dy) + S*.09)], fill=C)
    elif k.startswith("ship"):
        L = {"ship1": .5, "ship2": .62, "ship3": .74, "ship4": .84, "ship5": .92, "ship6": .98}.get(k, .7)
        x0 = S*(1 - L)/2; x1 = S - x0; hh = S*(.12 + L*.2)
        if k == "ship7":
            circ(h2, h2, S*.36, outline=C, width=lw); circ(h2, h2, S*.12, fill=C)
        elif k == "ship8":
            d.ellipse((S*.24, S*.4, S*.76, S*.66), fill=C); ln([(h2, S*.16), (h2, S*.4)], lw*.6); circ(h2, S*.16, S*.08, outline=C, width=int(lw*.6))
        elif k == "ship9":
            d.rectangle((S*.18, S*.44, S*.62, S*.68), fill=C); ln([(S*.62, S*.5), (S*.82, S*.22)], lw*.7); ln([(S*.82, S*.22), (S*.92, S*.4)], lw*.6)
        else:
            d.polygon([(x1, h2), (x1 - S*.2, h2 - hh/2), (x0 + S*.08, h2 - hh/2), (x0, h2 - hh*.25), (x0, h2 + hh*.25), (x0 + S*.08, h2 + hh/2), (x1 - S*.2, h2 + hh/2)], fill=C)
            if L > .7:
                for sg in (-1, 1): d.polygon([(x0 + S*.16, h2 + sg*hh/2), (x0 + S*.26, h2 + sg*(hh/2 + S*.12)), (x0 + S*.4, h2 + sg*hh/2)], fill=C)
            circ(x0, h2, S*.05, fill=(140, 230, 255, 255))
    else:
        circ(h2, h2, S*.3, fill=C)
    return im.resize((s, s), Image.LANCZOS)

KINDS = sorted(set(COL))

if __name__ == "__main__":
    import sys
    n = len(KINDS); cols = 12; rows = (n + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 60, rows * 60), (16, 26, 32, 255)); dd = ImageDraw.Draw(sheet)
    for i, k in enumerate(KINDS):
        sheet.alpha_composite(draw(k, 32), ((i % cols) * 60 + 14, (i // cols) * 60 + 6))
        dd.text(((i % cols) * 60 + 30, (i // cols) * 60 + 50), k[:10], fill=(200, 200, 200), anchor="mm", font=ImageFont.truetype(FB, 8))
    sheet.save(sys.argv[1] if len(sys.argv) > 1 else "icons.png")
