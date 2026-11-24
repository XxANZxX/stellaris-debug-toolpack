#!/usr/bin/env python3
"""11.9.9: проверка областей (scope) — «мини-CWTools», вторая часть (первая — cwtcheck.py, ссылки).

Игра пишет в error.log «Wrong scope for effect/trigger …», если эффект или условие стоит не в той области
(например, add_resource внутри планеты). CWTools ловит это по своим правилам; здесь — то же по документации самой игры:
  • <версия>_game_effects.log / _game_triggers.log (команда script_documentation): «Supported Scopes» каждого эффекта и условия;
  • <версия>_game_scopes.log: переходы (owner, capital_scope, solar_system …) — откуда можно и куда ведут;
  • правила CWTools (scope_changes.cwt, effects.cwt): «## push_scope» — куда ведут перебор (every_owned_planet → planet) и блоки.
Обход: события (country_event → страна …), кнопки (potential/allow/effect: from = держава игрока), on_actions.
Свои scripted effect/trigger проверяются в каждой области, из которой их вызывают (до неподвижной точки).
Цели event_target:X — область, в которой их сохраняют (save_event_target_as / save_global_event_target_as), если она одна.
Неизвестная область (?) — не проверяется (лучше пропустить, чем ложная тревога).

python3 scopecheck.py <правила CWTools config> <папка документации игры> <версия> <мод>
"""
import os, re, sys, glob, collections

RULES, DOCS, VER, MOD = sys.argv[1:5]

def toks(text):
    text = re.sub(r"#[^\n]*", "", text)
    return re.findall(r'"[^"]*"|[{}]|[<>!]?=|[<>]|[^\s{}=<>!"]+', text)
def parse(text):
    t = toks(text); i = 0
    def block():
        nonlocal i
        out = []
        while i < len(t):
            a = t[i]
            if a == "}": i += 1; return out
            if a == "{": i += 1; out.append((None, None, block())); continue
            if i + 1 < len(t) and t[i + 1] in ("=", "<=", ">=", "!=", "==", "<", ">"):
                op = t[i + 1]; i += 2
                if i < len(t) and t[i] == "{": i += 1; out.append((a, op, block()))
                elif i < len(t): out.append((a, op, t[i])); i += 1
            else: out.append((None, None, a)); i += 1
        return out
    return block()

# ---------- документация игры
def norm(s): return {"galacticobject": "galactic_object", "system": "galactic_object", "pop_job": "job"}.get(s, s)
SUP = {"effect": {}, "trigger": {}}
for kind in ("effect", "trigger"):
    txt = open(os.path.join(DOCS, "%s_game_%ss.log" % (VER, kind)), encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r"^([A-Za-z0-9_:]+) - .*?^Supported Scopes: ([^\n]*)", txt, re.M | re.S):
        sc = m.group(2).split()
        SUP[kind][m.group(1)] = None if ("all" in sc or "any" in sc or not sc) else {norm(x) for x in sc}
LINK = {}
txt = open(os.path.join(DOCS, "%s_game_scopes.log" % VER), encoding="utf-8", errors="ignore").read()
for m in re.finditer(r"^([A-Za-z0-9_]+) - [^\n]*\nSupported Scopes: ([^\n]*)\nOutput Scope: ([^\n]*)", txt, re.M):
    sc = m.group(2).split(); out = m.group(3).strip()
    LINK[m.group(1)] = (None if ("all" in sc or "any" in sc) else {norm(x) for x in sc}, None if out in ("various", "any", "all", "") else norm(out))
PUSH = {}
for f in glob.glob(os.path.join(RULES, "**", "*.cwt"), recursive=True):
    t = open(f, encoding="utf-8-sig", errors="ignore").read()
    for m in re.finditer(r"^## push_scope = (\w+)\s*\n(?:#[^\n]*\n)*alias\[(effect|trigger):([A-Za-z0-9_]+)\]", t, re.M):
        PUSH[(m.group(2), m.group(3))] = norm(m.group(1).lower())

# ---------- файлы мода
def read(p): return open(p, encoding="utf-8-sig", errors="ignore").read()
DEFS = {"effect": {}, "trigger": {}}
for kind, sub in (("effect", "scripted_effects"), ("trigger", "scripted_triggers")):
    for f in sorted(glob.glob(os.path.join(MOD, "common", sub, "*.txt"))):
        if re.search(r"/(00_|02_|zz_dtp_game_)", f): continue            # копии файлов игры
        for k, op, v in parse(read(f)):
            if k and isinstance(v, list): DEFS[kind][k] = (v, os.path.basename(f))
CONTROL = {"if", "else_if", "else", "AND", "OR", "NOT", "NOR", "NAND", "hidden_effect", "while", "random", "switch", "calc_true_if", "break"}
TRIG_CHILD = {"limit", "trigger", "modifier", "potential", "allow"}
SCOPE_KW = {"this", "root", "from", "prev", "fromfrom", "prevprev", "fromfromfrom", "prevprevprev"}

# цели event_target: область, где их сохраняют
TGT = collections.defaultdict(set)
PROBLEMS = collections.Counter(); EXAMPLES = {}
def report(where, msg):
    PROBLEMS[msg] += 1
    EXAMPLES.setdefault(msg, where)

class Ctx:
    __slots__ = ("this", "root", "frm", "prev")
    def __init__(s, this, root, frm, prev=()): s.this, s.root, s.frm, s.prev = this, root, frm, prev
    def push(s, new): return Ctx(new, s.root, s.frm, s.prev + (s.this,))

def resolve(ctx, key):
    """Область после перехода «key» (может быть цепочкой a.b.c); (ok, scope) — ok=False, если ключ не переход."""
    parts = key.split(".")
    cur = ctx.this; stack = ctx.prev
    for n, p in enumerate(parts):
        pl = p.lower()
        if pl == "this": continue
        if pl == "root": cur = ctx.root; continue
        if pl in ("from", "fromfrom", "fromfromfrom"): cur = ctx.frm if pl == "from" else None; continue
        if pl.startswith("prev"):
            k = (len(pl) - 2) // 2 if pl != "prev" else 1
            k = pl.count("prev")
            cur = stack[-k] if len(stack) >= k else None; continue
        if p.startswith("event_target:"):
            s = TGT.get(p[13:]); cur = next(iter(s)) if s and len(s) == 1 else None; continue
        if p in LINK:
            sup, out = LINK[p]
            if cur and sup and not compat(cur, sup): return True, None, "переход «%s» из области %s (можно: %s)" % (p, cur, " ".join(sorted(sup)))
            cur = out; continue
        if n == 0: return False, None, None
        return True, None, None
    return True, cur, None

def compat(cur, sup):
    if cur in sup: return True
    if cur in ("planet", "colony") and ({"planet", "colony"} & sup): return True
    return False

CHECKED = [0]
CALLS = {"effect": collections.defaultdict(set), "trigger": collections.defaultdict(set)}
def walk(items, ctx, kind, where):
    for k, op, v in items:
        if k is None:
            if isinstance(v, list): walk(v, ctx, kind, where)
            continue
        if k.startswith("$") or k.startswith("@") or k.startswith("dtp_") and False: pass
        # сохранение цели
        if k in ("save_event_target_as", "save_global_event_target_as") and isinstance(v, str) and ctx.this:
            TGT[v.strip('"')].add(ctx.this)
        if isinstance(v, list):
            if k in CONTROL:
                for k2, op2, v2 in v:
                    if k2 == "limit" and isinstance(v2, list): walk(v2, ctx, "trigger", where + ">" + k)
                    elif k2 is not None or isinstance(v2, list): walk([(k2, op2, v2)], ctx, kind, where + ">" + k)
                continue
            if k in TRIG_CHILD: walk(v, ctx, "trigger", where + ">" + k); continue
            if k in DEFS[kind]:                                          # вызов с параметрами
                if ctx.this: CALLS[kind][k].add(ctx.this)
                continue
            ok, new, err = resolve(ctx, k)
            if err: report(where, err)
            if ok:
                walk(v, ctx.push(new), kind, where + ">" + k); continue
            pk = PUSH.get((kind, k))
            if pk or re.match(r"(every|random|any|count|ordered)_", k):
                sup = SUP[kind].get(k, None) if k in SUP[kind] else None
                if ctx.this and sup and not compat(ctx.this, sup): report(where, "%s «%s» в области %s (можно: %s)" % ("эффект" if kind == "effect" else "условие", k, ctx.this, " ".join(sorted(sup))))
                inner = ctx.push(pk)
                for k2, op2, v2 in v:
                    if k2 == "limit" and isinstance(v2, list): walk(v2, inner, "trigger", where + ">" + k)
                    elif k2 in ("order_by", "weights", "count", "position", "max", "min"): pass
                    else: walk([(k2, op2, v2)], inner, kind, where + ">" + k)
                continue
            check(ctx, kind, k, where)
            continue
        # простое значение
        if k in DEFS[kind] and v in ("yes", "no"):
            if ctx.this: CALLS[kind][k].add(ctx.this)
            continue
        check(ctx, kind, k, where)

def check(ctx, kind, k, where):
    if not ctx.this: return
    sup = SUP[kind].get(k, "?")
    if sup == "?":
        other = "trigger" if kind == "effect" else "effect"
        if k in SUP[other] and k not in DEFS[kind] and not k.startswith("dtp_"):
            report(where, "%s «%s» стоит там, где ждут %s" % ("условие" if other == "trigger" else "эффект", k, "эффекты" if kind == "effect" else "условия"))
        return
    CHECKED[0] += 1
    if sup and not compat(ctx.this, sup):
        report(where, "%s «%s» в области %s (можно: %s)" % ("эффект" if kind == "effect" else "условие", k, ctx.this, " ".join(sorted(sup))))

# ---------- точки входа
ONACT_FROM = {"on_war_beginning": "war"}                     # события из on_actions: from задаёт игра
ONACT = {}
for f in glob.glob(os.path.join(MOD, "common", "on_actions", "*.txt")):
    for k, op, v in parse(read(f)):
        if isinstance(v, list):
            for k2, op2, v2 in v:
                if k2 == "events" and isinstance(v2, list):
                    for _, _, e in v2: ONACT[e] = ONACT_FROM.get(k)
def entries():
    for f in sorted(glob.glob(os.path.join(MOD, "events", "*.txt"))):
        for k, op, v in parse(read(f)):
            if not isinstance(v, list): continue
            sc = {"country_event": "country", "planet_event": "planet", "fleet_event": "fleet", "ship_event": "ship", "pop_event": "pop", "event": None}.get(k, "x")
            if sc == "x": continue
            eid = next((b for a, _, b in v if a == "id"), "?")
            ctx = Ctx(sc, sc, ONACT[eid] if eid in ONACT else ("country" if sc == "country" else None))      # события DTP вызывает держава игрока (from — она)
            for k2, op2, v2 in v:
                if not isinstance(v2, list): continue
                if k2 == "trigger": yield (v2, ctx, "trigger", "%s:%s>trigger" % (os.path.basename(f), eid))
                elif k2 in ("immediate", "after"): yield (v2, ctx, "effect", "%s:%s>%s" % (os.path.basename(f), eid, k2))
                elif k2 == "option":
                    for k3, op3, v3 in v2:
                        if k3 == "trigger" and isinstance(v3, list): yield (v3, ctx, "trigger", "%s:%s>option>trigger" % (os.path.basename(f), eid))
                        elif k3 not in ("name", "custom_gui", "custom_tooltip", "trigger", "default_hide_option", "response_text", "is_dialog_only", "ai_chance"):
                            yield ([(k3, op3, v3)], ctx, "effect", "%s:%s>option" % (os.path.basename(f), eid))
    for f in sorted(glob.glob(os.path.join(MOD, "common", "button_effects", "*.txt"))):
        for k, op, v in parse(read(f)):
            if not isinstance(v, list): continue
            ctx = Ctx(None, None, "country")                   # область кнопки — окно (разная), from — держава игрока
            for k2, op2, v2 in v:
                if isinstance(v2, list):
                    yield (v2, ctx, "effect" if k2 == "effect" else "trigger", "%s:%s>%s" % (os.path.basename(f), k, k2))

def run():
    for _pass in range(2):                                     # 1-й проход собирает цели, 2-й проверяет с ними
        PROBLEMS.clear(); EXAMPLES.clear(); CHECKED[0] = 0
        for kind in CALLS: CALLS[kind].clear()
        for items, ctx, kind, where in entries(): walk(items, ctx, kind, where)
        done = {"effect": collections.defaultdict(set), "trigger": collections.defaultdict(set)}
        changed = True
        while changed:
            changed = False
            for kind in ("effect", "trigger"):
                for name, scopes in list(CALLS[kind].items()):
                    for sc in list(scopes):
                        if sc in done[kind][name] or name not in DEFS[kind]: continue
                        done[kind][name].add(sc); changed = True
                        walk(DEFS[kind][name][0], Ctx(sc, None, None), kind, "%s:%s[%s]" % (DEFS[kind][name][1], name, sc))
    return done

done = run()
n_def = sum(len(v) for v in done.values())
print("проверено: событий и кнопок — все; своих эффектов/условий в известной области: %d; целей с известной областью: %d" %
      (n_def, sum(1 for s in TGT.values() if len(s) == 1)))
multi = {k: v for k, v in TGT.items() if len(v) > 1}
if multi: print("цели, сохраняемые в разных областях (не проверяются): " + ", ".join("%s=%s" % (k, "/".join(sorted(v))) for k, v in sorted(multi.items())[:20]))
print("проверено эффектов/условий в известной области: %d" % CHECKED[0])
print("замечаний: %d (разных %d)" % (sum(PROBLEMS.values()), len(PROBLEMS)))
for msg, n in PROBLEMS.most_common(60):
    print("  %4d × %s   — напр. %s" % (n, msg, EXAMPLES[msg]))
