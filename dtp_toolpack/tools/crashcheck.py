# -*- coding: utf-8 -*-
"""Проверка на то, что может уронить игру или сломать окно (python3 crashcheck.py <папка_мода>)."""
import os, re, sys, glob, collections
R = sys.argv[1]; P = []
def txt(p): return open(p, encoding="utf-8-sig").read()
files = {f: txt(f) for f in glob.glob(os.path.join(R, "**/*.txt"), recursive=True) + glob.glob(os.path.join(R, "**/*.gui"), recursive=True) + glob.glob(os.path.join(R, "**/*.gfx"), recursive=True)}
for f, t in files.items():                                   # размер: игра не читает дальше ~1 МБ
    if os.path.getsize(f) > 900000: P.append("файл больше 900 КБ (игра обрежет хвост): " + f)
for f, t in files.items():                                   # записи, на которых игра сбивается и теряет остаток файла
    for bad in ("spawn_random_storm = yes", "§O"):
        if bad in t: P.append("запись «%s» ломает разбор остатка файла: %s" % (bad, f))
for f, t in files.items():                                   # скобки
    s = re.sub(r'"[^"\n]*"', '""', re.sub(r"#[^\n]*", "", t))
    d = 0
    for ch in s:
        d += (ch == "{") - (ch == "}")
        if d < 0: P.append("лишняя } в " + f); break
    if d > 0: P.append("незакрытая { в " + f)
ev = "\n".join(t for f, t in files.items() if "/events/" in f)
blocks = re.findall(r"^(country_event|planet_event|fleet_event|event) = \{(.*?)^\}", ev, re.S | re.M)
ids = collections.Counter(re.search(r"id = ([\w.]+)", b).group(1) for _, b in blocks)
for i, n in ids.items():
    if n > 1: P.append("событие дважды: " + i)
for kind, b in blocks:                                        # варианты ответа
    i = re.search(r"id = ([\w.]+)", b).group(1)
    hidden = "hide_window = yes" in b
    opts = re.findall(r"\toption = \{", b)
    if not hidden and not opts: P.append("событие без вариантов ответа: " + i)
    if not hidden and "picture =" not in b: P.append("событие без картинки: " + i)
    if not hidden and "desc =" not in b: P.append("событие без описания: " + i)
    trig_opts = len(re.findall(r"\toption = \{\s*name = [\w.]+\s*trigger = ", b))
    if opts and trig_opts == len(opts) and i not in ("dtp.1240",): P.append(   # 1240: условия покрывают все случаи (np / prot / ни того, ни другого)
        "все варианты ответа с условием (проверьте, что хотя бы один всегда виден): " + i)
alltxt = "\n".join(files.values())
for i in set(re.findall(r"(?:country_event|planet_event|fleet_event) = \{ id = (dtp\.\d+)", alltxt)) | set(re.findall(r"^\t\t(dtp\.\d+)$", alltxt, re.M)):
    if i not in ids: P.append("вызов несуществующего события: " + i)
gfx = "\n".join(t for f, t in files.items() if f.endswith(".gfx"))
sprites = set(re.findall(r'name = "(GFX_[\w]+)"', gfx))
van = set()
if len(sys.argv) > 2:
    for g in glob.glob(os.path.join(sys.argv[2], "**/*.gfx"), recursive=True): van |= set(re.findall(r'name\s*=\s*"(GFX_\w+)"', txt(g)))
for s in set(re.findall(r'(?:picture|spriteType|quadTextureSprite|icon)\s*=\s*"?(GFX_\w+)"?', alltxt)):
    if s not in sprites and s not in van: P.append("нет картинки/спрайта: " + s)
for f, t in files.items():                                    # текстуры существуют
    for tf in re.findall(r'texture[fF]ile = "([^"]+)"', t):
        if not os.path.exists(os.path.join(R, tf)) and not (tf.startswith('gfx/interface/icons/') and "dtp" not in tf): P.append("нет файла текстуры: " + tf)   # значки игры
gui = "\n".join(t for f, t in files.items() if f.endswith(".gui"))
names = collections.Counter(re.findall(r'name\s*=\s*"((?:dtp_|dq)[^"]+)"', gui))
for n, c in names.items():
    if c > 1: P.append("элемент окна дважды: %s (%d)" % (n, c))
be = "\n".join(t for f, t in files.items() if "button_effects" in f)
keys = collections.Counter(re.findall(r"^((?:dtp_|dq)\w+) = \{", be, re.M))
for k, c in keys.items():
    if c > 1: P.append("кнопка дважды: " + k)
for k in set(re.findall(r'effect\s*=\s*"((?:dtp_|dq)[^"]+)"', gui)):
    if k not in keys: P.append("у кнопки окна нет действия: " + k)
for w in re.findall(r"while = \{(.{0,60})", alltxt, re.S):     # циклы
    if "count" not in w and "limit" not in w: P.append("цикл while без ограничения")
for f, t in files.items():
    for m in re.finditer(r"destroy_country = yes", t):
        ctx = t[max(0, m.start() - 300):m.start()]
        if "is_ai = yes" not in ctx: P.append("destroy_country без проверки is_ai: " + f)
# Запись команды не так, как её пишет сама игра (например «= yes» там, где игра всегда пишет блок «= { }»),
# сбивает разбор: игра теряет все кнопки после этой в файле (они видны всегда). Сверяем с файлами игры.
# 3-й и следующие аргументы — папки с файлами игры (common, events).
if len(sys.argv) > 3:
    import collections
    tokre = re.compile(r'(?m)^\s*([A-Za-z_][\w@.:]*)\s*(?:=|<|>|>=|<=)\s*(\{|"[^"]*"|[^\s{}#]+)')
    kind = lambda v: "блок" if v == "{" else ("yes/no" if v in ("yes", "no") else "значение")
    form = collections.defaultdict(collections.Counter)
    for d in sys.argv[3:]:
        for g in glob.glob(os.path.join(d, "**/*.txt"), recursive=True):
            for k, v in tokre.findall(re.sub(r"#[^\n]*", "", txt(g))): form[k][kind(v)] += 1
    for f, t in files.items():
        if not f.endswith(".txt") or "/localisation/" in f: continue
        for k, v in tokre.findall(re.sub(r"#[^\n]*", "", t)):
            c = form.get(k)
            if k.startswith("dtp") or not c or c[kind(v)]: continue
            P.append("«%s = %s»: в игре эта запись бывает только как %s — сломает остаток файла: %s" % (k, v, "/".join(c), f))
print("файлов %d · событий %d · кнопок %d · элементов окна %d · спрайтов %d" % (len(files), len(ids), len(keys), len(names), len(sprites)))
for p in sorted(set(P)): print("ПРОБЛЕМА:", p)
print("Итого проблем:", len(set(P)))
