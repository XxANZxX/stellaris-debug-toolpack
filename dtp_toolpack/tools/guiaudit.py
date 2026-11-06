# -*- coding: utf-8 -*-
"""11.6.7: проверка интерфейса готового мода (без игры).
python3 guiaudit.py <mod_dir> <localisation игры>
 1) текст на кнопках по языкам (RU/EN/ZH) — помещается ли в ширину кнопки (оценка ширины шрифтом, как в генераторе);
 2) перекрытие: кликабельные кнопки с одинаковым условием показа (potential) заходят друг на друга;
 3) выход элементов за пределы своего окна DTP;
 4) ключи текстов и подсказок есть во всех языках.
"""
import sys, os, re, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optimize as O
from PIL import ImageFont
MOD, VLOC = sys.argv[1], sys.argv[2]
LANGS = ("russian", "english", "simp_chinese")
_F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", 14)
_FZ = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 14) if os.path.exists("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc") else _F
def width(t, lang):
    f = _FZ if lang == "simp_chinese" else _F
    return f.getlength(t) * (0.95 if lang == "simp_chinese" else 0.9)

def load_loc(paths):
    d = {}
    for p in paths:
        for line in open(p, encoding="utf-8-sig", errors="replace"):
            m = re.match(r'\s*([\w.\-]+):\d*\s*"(.*)"\s*$', line)
            if m: d[m.group(1)] = m.group(2)
    return d
LOC = {}
for lg in LANGS:
    van = load_loc(glob.glob(os.path.join(VLOC, lg, "**", "*.yml"), recursive=True))
    own = load_loc(glob.glob(os.path.join(MOD, "localisation", lg, "*.yml")))
    LOC[lg] = (van, own)
SAMPLE = {"russian": "Объединённая Земля", "english": "United Nations of Earth", "simp_chinese": "地球联合国"}
def render(key, lg, depth=0):
    van, own = LOC[lg]
    t = own.get(key, van.get(key))
    if t is None: return None
    if depth < 3:
        t = re.sub(r"\$([\w.\-]+)(\|[^$]*)?\$", lambda m: (render(m.group(1), lg, depth + 1) or m.group(1)), t)
    t = re.sub(r"\[[^\]]*\]", SAMPLE[lg], t)
    t = re.sub(r"§[!\w]", "", t).replace("\\n", "\n")
    t = re.sub(r"£\w+£?", "  ", t)              # значки ресурсов ~ ширина двух пробелов
    return t

# ---- кнопки и условия показа
POT = {}
for f in glob.glob(os.path.join(MOD, "common", "button_effects", "*.txt")):
    for k, op, v in O.parse(open(f, encoding="utf-8-sig").read()):
        if isinstance(v, list):
            pot = [s for s in v if s[0] == "potential"]
            POT[k] = O.ser(pot[0][2], True) if pot else ""
# ---- элементы окон DTP с абсолютными координатами внутри своего окна верхнего уровня DTP
ROOTS = ("dtp_root", "dtp_editor", "dtp_peditor", "dtp_planet_strip", "dtp_fleet_strip", "dtp_starbase_strip")
EL = []
def num(v, d=0):
    try: return float(str(v).rstrip("%"))
    except Exception: return d
def attr(blk, k):
    for kk, op, v in blk:
        if kk == k: return v
    return None
def xy(v):
    if not isinstance(v, list): return 0, 0
    a = {kk: vv for kk, op, vv in v}
    return num(a.get("x", 0)), num(a.get("y", a.get("height", 0)))
def wh(v):
    if not isinstance(v, list): return 0, 0
    a = {kk: vv for kk, op, vv in v}
    return num(a.get("x", a.get("width", 0))), num(a.get("y", a.get("height", 0)))
def walk(nodes, ox, oy, root, cont):
    for k, op, v in nodes:
        if not isinstance(v, list): continue
        nm = (attr(v, "name") or "").strip('"')
        x, y = xy(attr(v, "position")); w, h = wh(attr(v, "size"))
        if k == "containerWindowType":
            r = root or (nm if nm in ROOTS else None)
            if r:
                c = dict(name=nm, x=0 if not root else ox + x, y=0 if not root else oy + y, w=w, h=h, root=r)
                if root: EL.append(dict(kind="cont", name=nm, x=c["x"], y=c["y"], w=w, h=h, root=r, parent=cont))
                walk(v, c["x"], c["y"], r, c)
            else:
                walk(v, ox, oy, None, None)
        elif not root and k == "guiTypes":
            walk(v, 0, 0, None, None)
        elif root and k in ("effectbuttonType", "buttonType", "iconType", "instantTextBoxType"):
            EL.append(dict(kind=k, name=nm, x=ox + x, y=oy + y, w=w, h=h, root=root, parent=cont,
                           eff=(attr(v, "effect") or "").strip('"'), text=(attr(v, "buttonText") or attr(v, "text") or "").strip('"'),
                           tip=(attr(v, "tooltipText") or "").strip('"'), transp=attr(v, "alwaysTransparent") == "yes",
                           font=(attr(v, "font") or "").strip('"')))
for f in glob.glob(os.path.join(MOD, "interface", "*.gui")):
    walk(O.parse(open(f, encoding="utf-8-sig").read()), 0, 0, None, None)
print("элементов DTP:", len(EL), dict(collections.Counter(e["root"] for e in EL)))

R = collections.defaultdict(list)
# 1) текст. Подставляемые имена ([…]) — по короткому образцу; если весь текст — подстановка, не проверяем (длина неизвестна).
SHORT = {"russian": "Земля", "english": "Earth", "simp_chinese": "地球"}
RAWKEY = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+){2,}\b")
for e in EL:
    if e["kind"] != "effectbuttonType" or not e["text"] or e["w"] <= 0: continue
    for lg in LANGS:
        van, own = LOC[lg]
        raw = own.get(e["text"], van.get(e["text"]))
        if raw is None: R["нет текста (%s)" % lg].append(e["text"]); continue
        if not re.sub(r"\[[^\]]*\]|§[!\w]|\s", "", raw): continue
        SAMPLE[lg] = SHORT[lg]
        t = render(e["text"], lg)
        for k in RAWKEY.findall(t): R["служебное имя вместо текста (%s)" % lg].append("%s «%s»" % (e["eff"], k))
        line = max(t.split("\n"), key=lambda s: width(s, lg))
        tw = width(line, lg)
        if tw > e["w"] - 6 + 8:
            R["текст шире кнопки (%s)" % lg].append("%s: %d > %d «%s»" % (e["eff"], tw, e["w"] - 6, line.strip()[:60]))
    if e["tip"]:
        for lg in LANGS:
            if render(e["tip"], lg) is None: R["нет подсказки (%s)" % lg].append(e["tip"])
# 2) перекрытие кликабельных кнопок с одним условием показа в одном окне (не считая плитку и её значок — одно действие;
#    рамку группы и кнопки внутри неё; тонкие полоски-акценты)
grp = collections.defaultdict(list)
for e in EL:
    if e["kind"] == "effectbuttonType" and not e["transp"] and e["w"] > 4 and e["h"] > 4:
        grp[(e["root"], POT.get(e["eff"], "?"))].append(e)
for (root, pot), es in grp.items():
    for i in range(len(es)):
        a = es[i]
        for b in es[i + 1:]:
            if a["eff"] == b["eff"]: continue
            ix = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]); iy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
            if ix <= 2 or iy <= 2: continue
            sa, sb = a["w"] * a["h"], b["w"] * b["h"]
            if max(sa, sb) >= 3 * min(sa, sb) and ix * iy >= 0.9 * min(sa, sb): continue     # рамка/фон и кнопка внутри
            R["кнопки перекрываются (%s)" % root].append("%s @%d,%d %dx%d ↔ %s @%d,%d %dx%d" % (a["eff"], a["x"], a["y"], a["w"], a["h"], b["eff"], b["x"], b["y"], b["w"], b["h"]))
# 3) выход за пределы окна DTP: граница — фон окна (самый большой элемент окна)
RS = {}
for e in EL:
    if e["kind"] != "cont" and e["w"] > 0 and (e["root"] not in RS or e["w"] * e["h"] > RS[e["root"]][2] * RS[e["root"]][3]):
        RS[e["root"]] = (e["x"], e["y"], e["w"], e["h"])
for e in EL:
    if e["root"] in RS and e["kind"] != "cont" and e["w"] > 0:
        X, Y, W, H = RS[e["root"]]
        if e["x"] < X - 2 or e["y"] < Y - 2 or e["x"] + e["w"] > X + W + 2 or e["y"] + e["h"] > Y + H + 2:
            R["за пределами фона окна %s" % e["root"]].append("%s %s @%d,%d %dx%d" % (e["kind"], e["eff"] or e["name"], e["x"], e["y"], e["w"], e["h"]))
print("размеры окон:", RS)
tot = 0
for k in sorted(R):
    v = sorted(set(R[k])); tot += len(v)
    print("\n== %s: %d" % (k, len(v)))
    for x in v[:25]: print("   ", x)
print("\nИТОГО замечаний:", tot)
