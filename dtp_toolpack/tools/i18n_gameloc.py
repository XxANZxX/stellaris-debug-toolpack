#!/usr/bin/env python3
"""12.0: снимки ключей локализации игры (i18n/game_*.json) — заново с перевода новой версии игры.
python3 i18n_gameloc.py <localisation игры> <common игры> <документация: *_game_modifiers.log>
  game_modloc_keys.json   — ключи названий бонусов (MOD_X, mod_x, x …), что есть в русском переводе
  game_ltrait_loc.json    — черта лидера → [есть название, есть описание]
  game_techedict_loc.json — технология / edict_<указ> → [есть название, есть описание]"""
import os, re, sys, glob, json
LOC, VC, MODLOG = sys.argv[1:4]
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n")
K = {}
for f in glob.glob(os.path.join(LOC, "russian", "**", "*.yml"), recursive=True):
    for m in re.finditer(r'^\s+([\w.\-]+):\d*\s+"(.*)"\s*$', open(f, encoding="utf-8-sig", errors="replace").read(), re.M):
        K[m.group(1)] = m.group(2)
def has(k): return bool(K.get(k, "").strip())
mods = set(re.findall(r"^- (\w+), Category", open(MODLOG, encoding="utf-8", errors="replace").read(), re.M))
old = set(json.load(open(os.path.join(HERE, "game_modloc_keys.json"), encoding="utf-8")))
cand = set()
for m in mods: cand |= {m, "mod_" + m, "MOD_" + m.upper(), "MOD_COUNTRY_" + m.upper(), m.upper()}
mk = sorted(k for k in K if (k in old or k in cand or k.lower().startswith("mod_")))
json.dump(mk, open(os.path.join(HERE, "game_modloc_keys.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
def tops(pat):
    out = []
    for f in glob.glob(os.path.join(VC, pat)):
        if re.search(r"README|documentation", f, re.I): continue
        out += re.findall(r"^([a-z]\w*)\s*=\s*\{", open(f, encoding="utf-8-sig", errors="replace").read(), re.M)
    return out
lt = {}
for f in glob.glob(os.path.join(VC, "traits", "*.txt")):
    t = open(f, encoding="utf-8-sig", errors="replace").read()
    for m in re.finditer(r"^(\w+)\s*=\s*\{", t, re.M):
        body = t[m.end():m.end() + 4000]
        if re.search(r"\bleader_trait\s*=", body.split("\n}")[0]): lt[m.group(1)] = [has(m.group(1)), has(m.group(1) + "_desc")]
oldlt = json.load(open(os.path.join(HERE, "game_ltrait_loc.json"), encoding="utf-8"))
for k in oldlt: lt.setdefault(k, [has(k), has(k + "_desc")])
json.dump(lt, open(os.path.join(HERE, "game_ltrait_loc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
te = {k: [has(k), has(k + "_desc")] for k in tops("technology/*.txt")}
for k in tops("edicts/*.txt"): te["edict_" + k] = [has("edict_" + k), has("edict_" + k + "_desc")]
oldte = json.load(open(os.path.join(HERE, "game_techedict_loc.json"), encoding="utf-8"))
for k in oldte: te.setdefault(k, [has(k), has(k + "_desc")])
json.dump(te, open(os.path.join(HERE, "game_techedict_loc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("ключей бонусов %d (было %d) · черт лидеров %d (было %d) · технологий и указов %d (было %d)" % (len(mk), len(old), len(lt), len(oldlt), len(te), len(oldte)))
