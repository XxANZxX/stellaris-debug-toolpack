#!/usr/bin/env python3
"""Проверка ссылок мода по правилам CWTools (cwtools-stellaris-config): «мини-CWTools».

Сам CWTools (.NET) здесь не установить (NuGet закрыт), поэтому берём из его правил главное:
  • alias[effect:X] / alias[trigger:X] = <тип> | enum[...] | литерал  — какие значения допустимы у эффекта/условия;
  • type[T] = { path = "game/common/..." name_field = ... }           — где лежат объекты типа T;
  • enum[E] = { ... }                                                 — допустимые слова.
Затем каждое «ключ = значение» в скриптах мода, где ключ — известный эффект/условие с простым значением,
сверяется: значение должно быть объектом нужного типа (игра 4.5.3 + сам мод), словом из перечисления или
переменной/целью/параметром/числом. Выводит список подозрительных ссылок.

python3 cwtcheck.py <правила/config> <игра common> <мод>
"""
import os, re, sys, glob, collections

RULES, VC, MOD = sys.argv[1:4]
GAME = os.path.dirname(VC.rstrip("/"))          # .../c  (common лежит внутри)

def toks(text):
    text = re.sub(r"#[^\n]*", "", text)
    return re.findall(r'"[^"]*"|[{}]|[<>!]?=|[^\s{}=<>!"]+', text)

def parse(text):
    """Дерево [(key, op, value)] — value: str или список."""
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

# ---------- правила
alias = collections.defaultdict(list)          # ("effect", "add_edict") → ["<edict>", "random_common", ...]
types = {}                                     # тип → (path, name_field, type_per_file, skip_root)
enums = collections.defaultdict(set)
blockf = collections.defaultdict(lambda: collections.defaultdict(list))   # (kind, key) → поле → варианты
for f in glob.glob(os.path.join(RULES, "**", "*.cwt"), recursive=True):
    txt = open(f, encoding="utf-8-sig", errors="ignore").read()
    for m in re.finditer(r"^alias\[(effect|trigger):([A-Za-z0-9_]+)\]\s*=\s*([^\s{#][^\s#]*)\s*$", txt, re.M):
        alias[(m.group(1), m.group(2))].append(m.group(3))
    for m in re.finditer(r"^alias\[(effect|trigger):([A-Za-z0-9_]+)\]\s*=\s*\{", txt, re.M):
        alias[(m.group(1), m.group(2))].append("{block}")
        # поля блока первого уровня: alias[effect:create_army] = { type = <army_type> ... }
        depth, j = 1, m.end()
        while j < len(txt) and depth: depth += {"{": 1, "}": -1}.get(txt[j], 0); j += 1
        body = txt[m.end():j - 1]
        lvl = 0
        for line in body.split("\n"):
            s = line.split("#")[0]
            if lvl == 0:
                mm = re.match(r"\s*([A-Za-z0-9_]+)\s*=\s*([^\s{][^\s]*)\s*$", s)
                if mm: blockf[(m.group(1), m.group(2))][mm.group(1)].append(mm.group(2))
            lvl += s.count("{") - s.count("}")
    for m in re.finditer(r"type\[([A-Za-z0-9_]+)\]\s*=\s*\{(.*?)\n\t\}", txt, re.S):
        body = m.group(2)
        p = re.search(r'path\s*=\s*"([^"]+)"', body)
        if not p: continue
        nf = re.search(r'name_field\s*=\s*"?([A-Za-z0-9_]+)"?', body)
        sk = re.search(r'skip_root_key\s*=\s*([A-Za-z0-9_]+)', body)
        types.setdefault(m.group(1), []).append((p.group(1), nf.group(1) if nf else None, "type_per_file = yes" in body, sk.group(1) if sk else None))
    for m in re.finditer(r"enum\[([A-Za-z0-9_]+)\]\s*=\s*\{([^{}]*)\}", txt):
        enums[m.group(1)].update(w.strip('"') for w in re.findall(r'"[^"]*"|[^\s#]+', re.sub(r"#[^\n]*", "", m.group(2))))

def tdir(base, p):
    p = re.sub(r"^game/", "", p)
    if p.startswith("common/"): return os.path.join(base, "common", p[7:]) if base == MOD else os.path.join(VC, p[7:])
    return os.path.join(base, p) if base == MOD else "/nonexistent"      # не-common части игры здесь нет — такие типы не проверяем

_tcache = {}
def tnames(t):
    if t in _tcache: return _tcache[t]
    s = set()
    for p, nf, per_file, skip in types.get(t, []):
        for base in (VC, MOD):
            d = tdir(base, p)
            for f in glob.glob(os.path.join(d, "**", "*.txt"), recursive=True):
                if per_file: s.add(os.path.splitext(os.path.basename(f))[0]); continue
                try: tree = parse(open(f, encoding="utf-8-sig", errors="ignore").read())
                except RecursionError: continue
                if skip: tree = [x for k, op, v in tree if isinstance(v, list) for x in v]
                for k, op, v in tree:
                    if nf and isinstance(v, list):
                        for k2, op2, v2 in v:
                            if k2 == nf and isinstance(v2, str): s.add(v2.strip('"'))
                    elif k: s.add(k)
    _tcache[t] = s
    return s

NUM = re.compile(r"^-?\d+(\.\d+)?$")
def dynamic(v):
    return (NUM.match(v) or "$" in v or v.startswith(("event_target:", "var:", "value:", "@", "trigger:", "modifier:")) or "." in v or "@" in v
            or v in ("yes", "no", "this", "root", "from", "prev", "prevprev", "fromfrom", "owner", "controller", "space_owner", "capital_scope", "solar_system", "planet",
                     "last_created_species", "last_created_leader", "last_created_country", "last_created_fleet", "last_created_ship", "last_created_pop",
                     "last_created_army", "last_created_design", "owner_species", "species", "leader", "fleet", "star", "random", "none", "any", "all"))

def valid(v, alts):
    if dynamic(v): return True
    for a in alts:
        if a == "{block}": continue
        if a.startswith(("alias_keys_field", "scope_group[")) and (a.startswith("alias_keys_field") or v.lower() in ("root", "from", "prev", "this")): return True
        if a in ("scalar", "localisation", "localisation_synced", "int", "float", "bool", "variable_field", "int_variable_field", "value_field",
                 "int_value_field", "filepath", "icon", "date_field", "colour_field") or a.startswith(("scope[", "scope_field", "value[", "event_target", "int[", "float[", "variable_field[", "filepath[", "icon[", "localisation", "value_set[", "single_alias")):
            return True
        m = re.match(r"^<([A-Za-z0-9_]+)(?:\.[A-Za-z0-9_]+)?>$", a)
        if m:
            if m.group(1) not in types or not tnames(m.group(1)): return True        # тип не описан / файлов нет — не проверяем
            if v.strip('"') in tnames(m.group(1)): return True
            continue
        m = re.match(r"^enum\[([A-Za-z0-9_]+)\]$", a)
        if m:
            if m.group(1) not in enums or v.strip('"') in enums[m.group(1)] or v in enums[m.group(1)]: return True
            continue
        if a.strip('"') == v.strip('"'): return True
    return False

# ---------- мод
files = [f for d in ("events", "common") for f in glob.glob(os.path.join(MOD, d, "**", "*.txt"), recursive=True)
         if not re.search(r"/(00_scripted_triggers|02_scripted_triggers_archaeology|zz_dtp_game_triggers)\.txt$", f)]
bad = collections.Counter(); where = {}
checked = 0
SIMPLE = {k for k, alts in alias.items() if any(a != "{block}" for a in alts)}
for f in files:
    try: tree = parse(open(f, encoding="utf-8-sig", errors="ignore").read())
    except RecursionError: continue
    stack = [tree]
    while stack:
        for k, op, v in stack.pop():
            if isinstance(v, list):
                stack.append(v)
                for kind in ("effect", "trigger"):
                    bf = blockf.get((kind, k))
                    if bf:
                        for k2, op2, v2 in v:
                            if isinstance(v2, str) and k2 in bf:
                                checked += 1
                                if not valid(v2, bf[k2]):
                                    bad[(k + "." + k2, v2)] += 1; where.setdefault((k + "." + k2, v2), os.path.relpath(f, MOD))
                        break
                continue
            if not k or not isinstance(v, str): continue
            for kind in ("effect", "trigger"):
                if (kind, k) in SIMPLE:
                    checked += 1
                    if not valid(v, alias[(kind, k)]):
                        bad[(k, v)] += 1; where.setdefault((k, v), os.path.relpath(f, MOD))
                    break
print("проверено ссылок: %d, типов в правилах: %d, эффектов/условий с простыми значениями: %d" % (checked, len(types), len(SIMPLE)))
print("подозрительных: %d (уникальных %d)" % (sum(bad.values()), len(bad)))
for (k, v), n in sorted(bad.items(), key=lambda x: (-x[1], x[0])):
    if "." in k: alts = " | ".join(blockf.get(("effect", k.split(".")[0]), {}).get(k.split(".")[1]) or blockf.get(("trigger", k.split(".")[0]), {}).get(k.split(".")[1], []))
    else: alts = " | ".join(a for a in alias[("effect", k)] or alias[("trigger", k)] if a != "{block}")
    print("  %-34s = %-40s ×%-4d ожидается %s   (%s)" % (k, v, n, alts[:60], where[(k, v)]))
