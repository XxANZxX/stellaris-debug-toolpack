# -*- coding: utf-8 -*-
"""11.5: оптимизация загрузки без изменения поведения.

1) intern(): одинаковые куски условий и эффектов, которые дословно повторяются во многих кнопках, выносятся
   в общие scripted_triggers / scripted_effects БЕЗ параметров (их игра разбирает один раз), а кнопка ссылается
   на них строкой «dzXXXXXX = yes». Выносятся только целые утверждения внутри «логических» блоков
   (AND/OR/NOT/from/if/hidden_effect …) — внутрь параметров эффектов (create_leader = { … }) не заходим.
   В allow наружу подсказки ничего не меняется: выносится только условие ВНУТРИ custom_tooltip.
2) rename(): длинные имена своих scripted_triggers / scripted_effects (не флаги, не переменные, не цели —
   те хранятся в сохранениях) заменяются короткими во всех файлах common/ и events/.
"""
import re, zlib, glob, os

_TOK = re.compile(r'"[^"]*"|#[^\n]*|[{}]|[<>!]?=|[<>]|[^\s{}=<>"#]+')

def parse(text):
    toks = [t for t in _TOK.findall(text) if not t.startswith("#")]
    pos = 0
    def block():
        nonlocal pos
        out = []
        while pos < len(toks):
            t = toks[pos]
            if t == "}":
                pos += 1; return out
            if pos + 1 < len(toks) and toks[pos + 1] in ("=", "<", ">", "<=", ">=", "!="):
                k, op = t, toks[pos + 1]; pos += 2
                if toks[pos] == "{":
                    pos += 1; out.append([k, op, block()])
                else:
                    out.append([k, op, toks[pos]]); pos += 1
            elif t == "{":
                pos += 1; out.append([None, None, block()])
            else:
                out.append([None, None, t]); pos += 1
        return out
    return block()

def ser(nodes, one_line=False):
    parts = []
    for k, op, v in nodes:
        if isinstance(v, list):
            inner = ser(v, one_line)
            s = ("%s %s {" % (k, op) if k is not None else "{") + (" " + inner + " }" if one_line else "\n" + inner + "\n}")
        else:
            s = v if k is None else "%s %s %s" % (k, op, v)
        parts.append(s)
    return (" " if one_line else "\n").join(parts)

SCOPES = re.compile(r"^(from|fromfrom|root|prev|prevprev|this|owner|controller|capital_scope|solar_system|planet|space_owner|owner_species|"
                    r"species|leader|fleet|star|orbit|event_target:\w+|(every|random|ordered)_\w+)$")
T_CONT = re.compile(r"^(AND|OR|NOT|NOR|NAND|custom_tooltip|(any|count)_\w+)$")
E_CONT = re.compile(r"^(hidden_effect|if|else_if|else|while)$")
NEVER = {"limit", "if", "else_if", "else", "effect", "potential", "allow", "trigger", "count", "fail_text", "text", "tooltip"}

def _kids_ctx(key, ctx):
    """Контекст детей блока key (или None — внутрь не заходим)."""
    if ctx == "E":
        if key == "limit": return "T"
        if E_CONT.match(key) or SCOPES.match(key): return "E"
        return None
    if ctx in ("T", "TA"):
        if key == "limit": return "T"
        if T_CONT.match(key) or SCOPES.match(key): return "T"
        return None
    if ctx == "A":                                   # верх allow: в подсказке — только содержимое custom_tooltip
        return "T" if key == "custom_tooltip" else None
    return None

def _walk(nodes, ctx, fn):
    for n in nodes:
        k, op, v = n
        if not isinstance(v, list) or k is None: continue
        fn(n, ctx)
        c = _kids_ctx(k, ctx)
        if c: _walk(v, c, fn)

def _roots(tree):
    for btn in tree:
        for sec in btn[2]:
            if isinstance(sec[2], list) and sec[0] in ("potential", "allow", "effect"):
                yield sec, {"potential": "T", "allow": "A", "effect": "E"}[sec[0]]

def _name(prefix, s, used):
    h = zlib.crc32(s.encode())
    while True:
        n, r = h % 36 ** 6, ""
        for _ in range(6): n, d = divmod(n, 36); r = "0123456789abcdefghijklmnopqrstuvwxyz"[d] + r
        nm = prefix + r
        if nm not in used or used[nm] == s: used[nm] = s; return nm
        h += 1

def intern(btns, eff_depth, min_len=40, call_len=14):
    """btns — тексты кнопок; eff_depth(text) → глубина вызовов scripted effects в куске эффекта.
    Возвращает (новые тексты кнопок, [определения триггеров], [определения эффектов])."""
    tree = [parse(b)[0] for b in btns]
    cnt = {}
    def count(n, ctx):
        k, op, v = n
        if k in NEVER or ctx == "A": return
        key = ("E" if ctx == "E" else "T", ser([n], True))
        cnt[key] = cnt.get(key, 0) + 1
    for sec, ctx in _roots(tree):
        if ctx == "T" and len(sec[2]) > 1:                         # всё содержимое potential целиком
            key = ("T", ser(sec[2], True)); cnt[key] = cnt.get(key, 0) + 1
        _walk(sec[2], ctx, count)
    used, trg, eff, made = {}, [], [], {}
    def good(key):
        c, L = cnt.get(key, 0), len(key[1])
        if "[" in key[1]: return False            # «[» в scripted_effects игра читает как макрос
        return c >= 2 and L >= min_len and (c - 1) * L > c * call_len + 20
    def call(key, body_nodes):
        if key not in made:
            nm = _name("dz" if key[0] == "T" else "dy", key[0] + key[1], used)
            made[key] = nm
            (trg if key[0] == "T" else eff).append(nm + " = {\n" + ser(body_nodes) + "\n}")
        return [made[key], "=", "yes"]
    def rewrite(nodes, ctx):
        for i, n in enumerate(nodes):
            k, op, v = n
            if not isinstance(v, list) or k is None: continue
            if k not in NEVER and ctx != "A":
                key = ("E" if ctx == "E" else "T", ser([n], True))
                if good(key) and (key[0] == "T" or eff_depth(key[1]) <= 2):
                    nodes[i] = call(key, [n]); continue
            c = _kids_ctx(k, ctx)
            if c: rewrite(v, c)
    for sec, ctx in _roots(tree):
        if ctx == "T" and len(sec[2]) > 1:
            key = ("T", ser(sec[2], True))
            if good(key):
                sec[2][:] = [call(key, list(sec[2]))]; continue
        if ctx == "E":                                  # верхний hidden_effect кнопки не выносим — он прячет эффект из подсказки
            for n in sec[2]:
                if isinstance(n[2], list) and n[0] == "hidden_effect": rewrite(n[2], "E")
                else: rewrite([n], "E")
            continue
        rewrite(sec[2], ctx)
    return [ser([b]) for b in tree], trg, eff

# ---------------------------------------------------------------- короткие имена
def rename(out_dir, keep_prefixes=("dtp_custom_",), min_len=12):
    files = [f for f in glob.glob(os.path.join(out_dir, "common", "**", "*.txt"), recursive=True) +
             glob.glob(os.path.join(out_dir, "events", "*.txt")) if not f.endswith(("00_scripted_triggers.txt", "02_scripted_triggers_archaeology.txt", "zz_dtp_game_triggers.txt"))]
    raw = {f: open(f, "rb").read() for f in files}
    txt = {f: raw[f].decode("utf-8-sig") for f in files}
    defs = set()
    for f in txt:
        if "/scripted_triggers/" in f or "/scripted_effects/" in f:
            defs |= set(re.findall(r"(?m)^(dtp_\w+)\s*=\s*\{", txt[f]))
    alltxt = "\n".join(txt.values())
    # имена, которые собираются из параметров ($X$) — не трогаем всё семейство
    fams = [re.compile("^" + re.sub(r"\\\$\w+\\\$", r"\\w+", re.escape(p)) + "$")
            for p in set(re.findall(r"\b\w*\$\w+\$\w*", alltxt)) if re.sub(r"\$\w+\$", "", p)]
    occ = re.compile(r"(?<![\w:.$])(dtp_\w+)(?![\w$])")
    bad = set()
    for f, t in txt.items():
        for m in occ.finditer(t):
            nm = m.group(1)
            if nm not in defs: continue
            pre = t[max(0, m.start() - 40):m.start()].split("\n")[-1]
            post = t[m.end():m.end() + 12]
            key_pos = re.search(r"(^|[{\s])$", pre) and re.match(r"\s*=\s*(yes|no|\{)", post) and not re.search(r"=\s*$", pre)
            val_pos = re.search(r"\b[A-Z][A-Z_]*\s*=\s*$", pre)
            if not (key_pos or val_pos): bad.add(nm)
    ren, used = {}, set()
    for nm in sorted(defs):
        if len(nm) < min_len or nm in bad or nm.startswith(keep_prefixes) or any(r.match(nm) for r in fams): continue
        h = zlib.crc32(nm.encode())
        while True:
            n, r = h % 36 ** 5, ""
            for _ in range(5): n, d = divmod(n, 36); r = "0123456789abcdefghijklmnopqrstuvwxyz"[d] + r
            s = "dx" + r
            if s not in used and s not in defs: break
            h += 1
        used.add(s); ren[nm] = s
    if not ren: return {}
    rx = re.compile(r"(?<![\w:.$])(%s)(?![\w$])" % "|".join(re.escape(k) for k in sorted(ren, key=len, reverse=True)))
    for f, t in txt.items():
        nt = rx.sub(lambda m: ren[m.group(1)], t)
        if nt != t:
            with open(f, "w", encoding="utf-8-sig" if t.startswith("﻿") else "utf-8", newline="\n") as fh: fh.write(nt)
    return ren
