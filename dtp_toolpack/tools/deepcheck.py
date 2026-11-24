#!/usr/bin/env python3
"""11.9.9: «глубокая» проверка готового мода — то, чего не ловят validate2 / crashcheck / cwtcheck / scopecheck.

 1. переменные в подсказках кнопок ([From.x] в tooltipText): игра в подсказке окна их не подставляет — на экране сырой текст
 2. команды [ … ] в текстах: начало — известная область или сохраняемая цель, конец — команда игры (документация
    localizations) или переменная, которую мод где-то задаёт
 3. переменные: читаются (check_variable, value = x, [x.var]), но нигде не задаются → «Variable … is not set» в error.log
 4. флаги DTP: проверяются, но нигде не ставятся (условие всегда ложно) · ставятся, но нигде не проверяются (лишние)
 5. цели event_target: используются, но нигде не сохраняются (всегда «нет цели»)
 6. свои scripted effect/trigger, которые нигде не вызываются (зря занимают память)
 7. кнопки (button_effects), на которые не ссылается ни одно окно
 8. спрайты, на которые никто не ссылается; файлы .dds без спрайта (память, размер мода)
 9. события, которые никто не вызывает
10. не-ASCII символы в файлах скриптов (кроме текстов): игра читает их как Windows-1252 → «Failed conversion of utf8 string»
11. ключи текстов, совпавшие с ключами самой игры (подменяют текст игры)
12. объекты мода с именами объектов игры в той же папке (подменяют объект игры)
13. ключ текста дважды в одном файле; поле, которое может быть одно, дважды (id, title, potential, effect …)
14. условия, ответ которых у игроков разный (local_has_dlc …) — рассинхрон в сетевой игре

python3 deepcheck.py <мод> <common игры> <localisation игры> <документация игры> <версия>
"""
import os, re, sys, glob, collections

MOD, VC, VLOC, DOCS, VER = sys.argv[1:6]
OUT = collections.defaultdict(list)
def add(cat, msg): OUT[cat].append(msg)
def read(p): return open(p, encoding="utf-8-sig", errors="replace").read()
def strip_comments(t): return re.sub(r'#[^\n"]*(?=\n|$)', "", t)

scripts = {f: read(f) for f in glob.glob(os.path.join(MOD, "common", "**", "*.txt"), recursive=True) + glob.glob(os.path.join(MOD, "events", "*.txt"))}
own_scripts = {f: t for f, t in scripts.items() if not re.search(r"/(00_|02_|zz_dtp_game_)", f)}
guis = {f: read(f) for f in glob.glob(os.path.join(MOD, "interface", "**", "*.gui"), recursive=True)}
gfxs = {f: read(f) for f in glob.glob(os.path.join(MOD, "interface", "**", "*.gfx"), recursive=True)}
locs = {}
for f in glob.glob(os.path.join(MOD, "localisation", "**", "*.yml"), recursive=True):
    locs[f] = read(f)
def loc_items(t):
    for m in re.finditer(r'^ ([\w.\-]+):\d* "(.*)"\s*$', t, re.M): yield m.group(1), m.group(2)
LOC = {}                                                     # русский — основной
for f, t in locs.items():
    if "/russian/" in f:
        for k, v in loc_items(t): LOC[k] = v
ALLSCR = "\n".join(strip_comments(t) for t in scripts.values())
ALLGUI = "\n".join(guis.values())

# ---------- 13a. ключ текста дважды в одном файле
for f, t in locs.items():
    c = collections.Counter(k for k, _ in loc_items(t))
    for k, n in c.items():
        if n > 1: add("13 дубли", "%s: ключ «%s» %d раза" % (os.path.relpath(f, MOD), k, n))

# ---------- 1. переменные в подсказках окон
tts = set(re.findall(r'tooltipText\s*=\s*"([^"]+)"', ALLGUI))
for k in sorted(tts):
    v = LOC.get(k, "")
    for m in re.finditer(r"\[((?:From|from|FROM|Root|root|This|this|Prev|prev)\.[\w.]+)\]", v):
        add("1 подсказки", "%s: [%s] — «%s»" % (k, m.group(1), v[:90]))

# ---------- переменные, флаги, цели
SET_VARS = set(re.findall(r"(?:set_variable|change_variable|export_trigger_value_to_variable|set_variable_to_random_value|round_variable_to_closest|multiply_variable|divide_variable|subtract_variable|modulo_variable|clamp_variable|floor_variable|ceiling_variable|round_variable|abs_variable)\s*=\s*\{[^{}]*?which\s*=\s*([\w@]+)", ALLSCR))
SET_VARS |= set(re.findall(r"(?:set_variable|change_variable|export_trigger_value_to_variable)\s*=\s*\{[^{}]*?variable\s*=\s*([\w@]+)", ALLSCR))
for blk, var in re.findall(r"(\w+)\s*=\s*\{(?:[^{}]|\{[^{}]*\})*?\b(?:which|variable)\s*=\s*(\w+)", ALLSCR):
    if blk not in ("check_variable", "is_variable_set", "limit"): SET_VARS.add(var)
CREATING = set(re.findall(r"(?:set_variable|export_trigger_value_to_variable|change_variable)\s*=\s*\{[^{}]*?which\s*=\s*([\w@]+)", ALLSCR))
READ_VARS = collections.Counter(re.findall(r"check_variable\s*=\s*\{[^{}]*?which\s*=\s*(\w+)", ALLSCR))
for v in re.findall(r"(?:check_variable|set_variable|change_variable|multiply_variable|divide_variable|subtract_variable)\s*=\s*\{[^{}]*?value\s*[<>=!]+\s*([A-Za-z_]\w*)", ALLSCR):
    if not re.fullmatch(r"(yes|no|trigger|modifier|value)", v) and not v.startswith("trigger:"): READ_VARS[v] += 1
for k, v in LOC.items():
    for m in re.finditer(r"\[[\w]+\.((?:dtp_)\w+)\]", v): READ_VARS[m.group(1)] += 1
for v, n in sorted(READ_VARS.items()):
    if v.startswith("dtp_") and v not in SET_VARS:
        add("3 переменные", "«%s» читается (%d раз), но нигде не задаётся" % (v, n))
ONLY_CHANGED = {v for v in re.findall(r"change_variable\s*=\s*\{[^{}]*?which\s*=\s*(\w+)", ALLSCR)} - set(re.findall(r"(?:set_variable|export_trigger_value_to_variable)\s*=\s*\{[^{}]*?which\s*=\s*(\w+)", ALLSCR))
for v in sorted(ONLY_CHANGED):
    if v.startswith("dtp_"): add("3 переменные", "«%s» только меняется (change_variable), но нигде не задаётся (set_variable) — первая запись идёт от 0, а условия до неё пишут «Variable is not set»" % v)

FLAG_KINDS = "country|global|planet|star|fleet|ship|leader|species|pop|pop_group|megastructure|federation|war|sector"
F_SET = collections.defaultdict(set); F_CHK = collections.defaultdict(set); F_DEL = collections.defaultdict(set)
for kind, fl in re.findall(r"set_(%s)_flag\s*=\s*([\w@$]+)" % FLAG_KINDS, ALLSCR): F_SET[kind].add(fl)
for kind, fl in re.findall(r"set_timed_(%s)_flag\s*=\s*\{[^{}]*?flag\s*=\s*([\w@$]+)" % FLAG_KINDS, ALLSCR): F_SET[kind].add(fl)
for kind, fl in re.findall(r"has_(%s)_flag\s*=\s*([\w@$]+)" % FLAG_KINDS, ALLSCR + "\n" + ALLGUI): F_CHK[kind].add(fl)
for kind, fl in re.findall(r"remove_(%s)_flag\s*=\s*([\w@$]+)" % FLAG_KINDS, ALLSCR): F_DEL[kind].add(fl)
for kind in sorted(set(F_SET) | set(F_CHK)):
    for fl in sorted(F_CHK[kind] - F_SET[kind]):
        if fl.startswith("dtp_") and "$" not in fl: add("4 флаги", "%s-флаг «%s» проверяется, но нигде не ставится (условие всегда ложно)" % (kind, fl))
    for fl in sorted(F_SET[kind] - F_CHK[kind] - F_DEL[kind]):
        if fl.startswith("dtp_") and "$" not in fl: add("4 флаги", "%s-флаг «%s» ставится, но нигде не проверяется и не снимается" % (kind, fl))
# параметры $X$ — флаги вида dtp_perm_$P$: разворачиваем по известным значениям не будем (пропуск)

T_SAVE = set(re.findall(r"save_(?:global_)?event_target_as\s*=\s*([\w$]+)", ALLSCR))
T_USE = collections.Counter(re.findall(r"event_target:([\w$]+)", ALLSCR + "\n" + ALLGUI))
for k, v in LOC.items():
    for m in re.finditer(r"\[(dtp_\w+?)\.", v): T_USE[m.group(1)] += 1
for t, n in sorted(T_USE.items()):
    if "$" in t: continue
    if t not in T_SAVE: add("5 цели", "цель «%s» используется (%d раз), но нигде не сохраняется" % (t, n))

# ---------- 2. команды [ … ] в текстах
doc = read(os.path.join(DOCS, "%s_game_localizations.log" % VER))
PROPS = set(re.findall(r"^ (\w+)\s*$", doc, re.M))
CUSTOM = set()
for f in glob.glob(os.path.join(VC, "customizable_localization", "*.txt")) + glob.glob(os.path.join(MOD, "common", "customizable_localization", "*.txt")):
    CUSTOM |= set(re.findall(r"^defined_text\s*=\s*\{\s*name\s*=\s*(\w+)", read(f), re.M))
    CUSTOM |= set(re.findall(r"\bname\s*=\s*(\w+)", read(f)))
SCOPES0 = {"This", "Root", "From", "Prev", "this", "root", "from", "prev", "THIS", "ROOT", "FROM", "PREV", "FromFrom", "fromfrom", "PrevPrev", "prevprev"}
bad2 = collections.Counter(); ex2 = {}
for k, v in LOC.items():
    for m in re.finditer(r"(?<!\[)\[([^\[\]]+)\]", v):
        expr = m.group(1).strip()
        if "|" in expr: expr = expr.split("|")[0]
        parts = expr.split(".")
        head, last = parts[0], parts[-1]
        why = None
        if len(parts) == 1:
            if head not in PROPS and head not in CUSTOM: why = "неизвестная команда"
        else:
            if head not in SCOPES0 and head not in PROPS and head not in T_SAVE and not head.startswith("$"):
                why = "начало «%s» — не область и не сохраняемая цель" % head
            elif last not in PROPS and last not in CUSTOM and last not in SET_VARS and not last.startswith("$"):
                why = "конец «%s» — не команда игры и не переменная мода" % last
        if why:
            key = "%s: [%s]" % (why, re.sub(r"\d+", "N", expr)); bad2[key] += 1; ex2.setdefault(key, k)
for key, n in bad2.most_common():
    add("2 команды в текстах", "%d × %s (напр. %s)" % (n, key, ex2[key]))

# ---------- 6. неиспользуемые свои scripted effects / triggers
for sub in ("scripted_effects", "scripted_triggers"):
    names = {}
    for f, t in own_scripts.items():
        if "/common/%s/" % sub in f:
            for m in re.finditer(r"^(\w+)\s*=\s*\{", t, re.M): names[m.group(1)] = f
    body = "\n".join(t for f, t in scripts.items()) + ALLGUI
    cnt = collections.Counter(re.findall(r"\b(\w+)\s*=\s*(?:yes|no|\{)", strip_comments(body)))
    for n, f in sorted(names.items()):
        if cnt[n] <= 1: add("6 не вызываются", "%s «%s» (%s)" % ("эффект" if "effects" in sub else "условие", n, os.path.basename(f)))

# ---------- 7. кнопки без окна
BE = set()
for f, t in scripts.items():
    if "/button_effects/" in f: BE |= set(re.findall(r"^(\w+)\s*=\s*\{", t, re.M))
REF = set(re.findall(r'effect\s*=\s*"(\w+)"', ALLGUI))
for b in sorted(BE - REF): add("7 кнопки без окна", b)
for b in sorted(REF - BE): add("7 кнопки без окна", "окно ссылается на несуществующую кнопку: %s" % b)

# ---------- 8. спрайты и текстуры
SPR = {}; TEXF = collections.defaultdict(set)
for f, t in gfxs.items():
    for m in re.finditer(r'name\s*=\s*"(GFX_\w+)"(.*?)(?=name\s*=\s*"GFX_|\Z)', t, re.S):
        SPR[m.group(1)] = f
        for tf in re.findall(r'texture[fF]ile\s*=\s*"([^"]+)"', m.group(2)): TEXF[tf.replace("\\", "/")].add(m.group(1))
allref = ALLGUI + "\n" + ALLSCR + "\n" + "\n".join(locs.values()) + "\n" + "\n".join(gfxs.values())
used_spr = collections.Counter(re.findall(r"GFX_\w+", allref))
unused = [s for s in SPR if used_spr[s] <= 1 and not re.match(r"GFX_(ethic|ethics|evt)_", s)]      # значки этик и картинки событий игра ищет по имени
if unused:
    size = 0
    for s in unused:
        for tf, ss in TEXF.items():
            if s in ss and ss <= set(unused) and os.path.exists(os.path.join(MOD, tf)): size += os.path.getsize(os.path.join(MOD, tf))
    add("8 спрайты", "спрайтов без ссылок: %d (их текстуры %.1f МБ): %s" % (len(unused), size / 1e6, ", ".join(sorted(unused)[:25]) + (" …" if len(unused) > 25 else "")))
dds = [os.path.relpath(p, MOD).replace("\\", "/") for p in glob.glob(os.path.join(MOD, "gfx", "**", "*.dds"), recursive=True)]
orphan = [d for d in dds if d not in TEXF and not re.search(r"gfx/(event_pictures|map/star_classes|models|portraits|interface/flags)/", d)]
if orphan:
    add("8 спрайты", ".dds без спрайта: %d (%.1f МБ): %s" % (len(orphan), sum(os.path.getsize(os.path.join(MOD, d)) for d in orphan) / 1e6, ", ".join(orphan[:15]) + (" …" if len(orphan) > 15 else "")))

# ---------- 9. события, которые никто не вызывает
EV = {}
for f, t in scripts.items():
    if "/events/" in f:
        for m in re.finditer(r"^\s*id\s*=\s*([\w.]+)", t, re.M): EV[m.group(1)] = f
fired = set(re.findall(r"(?:country_event|planet_event|fleet_event|ship_event|pop_event|event)\s*=\s*\{\s*id\s*=\s*([\w.]+)", ALLSCR))
fired |= set(re.findall(r"^\s+(dtp\.\d+)\s*$", ALLSCR, re.M))                                   # on_actions events = { … }
fired |= set(re.findall(r"\b(dtp\.\d+)\b", "\n".join(t for f, t in scripts.items() if "/on_actions/" in f or "/situations/" in f)))
for e in sorted(EV, key=lambda x: (len(x), x)):
    if e not in fired: add("9 события", "%s никто не вызывает (%s)" % (e, os.path.basename(EV[e])))

# ---------- 10. не-ASCII в скриптах
for f, t in list(scripts.items()) + list(guis.items()) + list(gfxs.items()):
    for n, line in enumerate(t.split("\n"), 1):
        code = re.sub(r'"[^"]*"', '""', line).split("#")[0]
        if re.search(r"[^\x00-\x7f]", code):
            add("10 не-ASCII", "%s:%d вне кавычек: %s" % (os.path.relpath(f, MOD), n, line.strip()[:80])); break
    for n, line in enumerate(t.split("\n"), 1):
        q = "".join(re.findall(r'"([^"]*)"', line.split("#")[0]))
        if re.search(r"[^\x00-\x7f]", q) and not f.endswith(".gui"):
            add("10 не-ASCII", "%s:%d в кавычках (log/имя/текст в скрипте): %s" % (os.path.relpath(f, MOD), n, line.strip()[:80])); break

# ---------- 11. ключи текстов как у игры
vkeys = set()
for f in glob.glob(os.path.join(VLOC, "english", "**", "*.yml"), recursive=True):
    vkeys |= {k for k, _ in loc_items(read(f))}
same = sorted(k for k in LOC if k in vkeys)
if same: add("11 ключи игры", "%d ключей совпадают с ключами игры (текст игры подменяется): %s" % (len(same), ", ".join(same[:30]) + (" …" if len(same) > 30 else "")))

# ---------- 12. объекты с именами объектов игры
for f, t in own_scripts.items():
    rel = os.path.relpath(f, os.path.join(MOD, "common")).replace("\\", "/")
    if rel.startswith("..") or "/" not in rel: continue
    folder = rel.split("/")[0]
    if folder in ("on_actions", "button_effects", "global_ship_designs") or re.search(r"/zz_dtp_", f): continue      # zz_dtp_ — намеренная подмена (правила, объявление войны)
    van = set()
    for g in glob.glob(os.path.join(VC, folder, "*.txt")): van |= set(re.findall(r"^(\w+)\s*=\s*\{", read(g), re.M))
    for m in re.finditer(r"^(\w+)\s*=\s*\{", t, re.M):
        if m.group(1) in van: add("12 объекты игры", "%s: «%s» — как у игры (подменяет объект игры)" % (rel, m.group(1)))

# ---------- 13b. поля, которые могут быть одни
ONE = {"events": ("id", "title", "picture", "hide_window", "is_triggered_only", "diplomatic", "custom_gui", "immediate", "trigger"),
       "button_effects": ("potential", "allow", "effect")}
def top_blocks(t):
    d, st = 0, None
    for k, ch in enumerate(t):
        if ch == "{":
            if d == 0: st = k
            d += 1
        elif ch == "}":
            d -= 1
            if d == 0 and st is not None: yield t[st + 1:k]
def first_level_keys(b):
    d, keys = 0, []
    for m in re.finditer(r"\{|\}|(\w+)\s*=", b):
        if m.group(0) == "{": d += 1
        elif m.group(0) == "}": d -= 1
        elif d == 0: keys.append(m.group(1))
    return keys
for f, t in scripts.items():
    kind = "events" if "/events/" in f else ("button_effects" if "/button_effects/" in f else None)
    if not kind: continue
    for b in top_blocks(strip_comments(t)):
        c = collections.Counter(first_level_keys(b))
        for k in ONE[kind]:
            if c[k] > 1: add("13 дубли", "%s: «%s» %d раза в одном блоке (%s)" % (os.path.basename(f), k, c[k], (re.search(r"id\s*=\s*([\w.]+)", b) or [0, "?"])[1]))
        if kind == "events":
            for ob in re.findall(r"\boption\s*=\s*\{", b): pass

# ---------- 14. условия, которые у игроков в сетевой игре дают разный ответ (рассинхрон, если от них зависит эффект)
for f, t in own_scripts.items():
    for m in re.finditer(r"\b(local_has_dlc|logged_in_to_pdx_account|is_local_player|has_local_player)\b", strip_comments(t)):
        add("14 рассинхрон", "%s: «%s» — разный ответ у разных игроков" % (os.path.relpath(f, MOD), m.group(1)))

# ---------- итог
total = 0
for cat in sorted(OUT, key=lambda c: int(c.split()[0])):
    items = OUT[cat]; total += len(items)
    print("== %s: %d" % (cat, len(items)))
    for x in items[:40]: print("   " + x)
    if len(items) > 40: print("   … ещё %d" % (len(items) - 40))
print("ИТОГО замечаний: %d" % total)
