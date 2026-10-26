# -*- coding: utf-8 -*-
"""11.2: данные для редактора держав и вида — читаются из файлов самой игры (common, interface/*.gfx).
Условия игры (potential/possible цивик и форм правления, черты видов, перки, традиции, политики) переводятся
в обычные условия державы, чтобы редактор показывал красную пометку там же, где её показывает редактор игры."""
import os, re, glob

def _strip(t): return re.sub(r"#[^\n]*", "", t)
_TOK = re.compile(r'"[^"]*"|[{}]|[<>!]=|[=<>]|[^\s{}=<>"]+')
def parse(text):
    toks = _TOK.findall(_strip(text)); i = 0
    def block():
        nonlocal i
        out = []
        while i < len(toks):
            t = toks[i]
            if t == "}": i += 1; return out
            if t == "{": i += 1; out.append((None, None, block())); continue
            if i + 1 < len(toks) and toks[i + 1] in ("=", "<", ">", "<=", ">=", "!="):
                op = toks[i + 1]; i += 2
                if i < len(toks) and toks[i] == "{": i += 1; out.append((t, op, block()))
                else: out.append((t, op, toks[i] if i < len(toks) else "")); i += 1
            else:
                out.append((None, None, t)); i += 1
        return out
    return block()
def ser(nodes):
    """Обратно в текст (для обычных условий игры)."""
    out = []
    for k, op, v in nodes:
        vs = ("{ " + ser(v) + " }") if isinstance(v, list) else v
        out.append(vs if k is None else "%s %s %s" % (k, op, vs))
    return " ".join(out)
def get(nodes, key):
    for k, op, v in nodes:
        if k == key: return v
    return None
def getall(nodes, key): return [v for k, op, v in nodes if k == key]
def top(path):
    out = {}
    for f in sorted(glob.glob(path)):
        if "README" in f.upper() or "DOCUMENTATION" in f.upper(): continue
        for k, op, v in parse(open(f, encoding="utf-8-sig").read()):
            if k and isinstance(v, list) and not k.startswith("@"): out[k] = (v, os.path.basename(f))
    return out

# ---- особый синтаксис требований правительства (99_README_GOVERNMENT.txt) → условия державы
_FIELD = {"ethics": "has_ethic = %s", "authority": "has_authority = %s", "civics": "has_civic = %s", "origin": "has_origin = %s",
          "country_type": "is_country_type = %s", "graphical_culture": "graphical_culture = %s", "species_class": "is_species_class = %s",
          "species_archetype": "owner_species = { is_archetype = %s }", "traits": "has_trait = %s", "ship_categories": "uses_ship_category = %s",
          "preferred_planet_class": None}
def _list(nodes, field):
    out = []
    for k, op, v in nodes:
        if k == "value":
            f = _FIELD[field]
            if f: out.append(f % v)
        elif k in ("OR", "NOT", "NOR", "AND", "NAND") and isinstance(v, list):
            inner = _list(v, field)
            if inner: out.append("%s = { %s }" % (k, " ".join(inner)))
        elif k == "text": pass
        elif k is None and isinstance(v, str) and field == "civics": out.append(_FIELD[field] % v)
    return out
def gov_req(nodes):
    """potential/possible цивики или формы правления → список условий (AND)."""
    out = []
    for k, op, v in nodes or []:
        if k in _FIELD and isinstance(v, list):
            out += _list(v, k)
        elif k in ("OR", "NOT", "NOR", "AND", "NAND") and isinstance(v, list):
            inner = gov_req(v)
            if inner: out.append("%s = { %s }" % (k, " ".join(inner)))
        elif k == "text": pass
        elif k:
            out.append("%s %s %s" % (k, op, ("{ " + ser(v) + " }") if isinstance(v, list) else v))
    return out

def sprite_textures(vi):
    m = {}
    for g in glob.glob(os.path.join(vi, "**", "*.gfx"), recursive=True):
        t = open(g, encoding="utf-8-sig", errors="ignore").read()
        for mm in re.finditer(r'name\s*=\s*"(GFX_\w+)"\s*\n\s*texture[fF]ile\s*=\s*"([^"]+)"', t):
            m.setdefault(mm.group(1), mm.group(2))
    return m

def civics(vc):
    out = []
    for k, (b, f) in top(os.path.join(vc, "governments/civics/*.txt")).items():
        if not k.startswith("civic_") or get(b, "is_origin") == "yes": continue
        pot, pos = gov_req(get(b, "potential")), gov_req(get(b, "possible"))
        play = get(b, "playable")
        req = [r for r in (resolve(x, vc) for x in pot + pos + ([ser(play)] if isinstance(play, list) and play else [])) if r]
        posi = " ".join(r for r in pot if not r.startswith(("NOT", "NOR")))
        cat = ("machine" if "auth_machine_intelligence" in posi else "hive" if "auth_hive_mind" in posi
               else "corp" if "auth_corporate" in posi else "reg")
        if f == "01_special_civics.txt" or "always = no" in " ".join(req): cat = "special"
        icon = (get(b, "icon") or "gfx/interface/icons/governments/civics/%s.dds" % k).strip('"')
        out.append(dict(key=k, icon=icon, req=req, cat=cat))
    return out

def authorities(vc):
    out = []
    for k, (b, f) in top(os.path.join(vc, "governments/authorities/*.txt")).items():
        if not k.startswith("auth_"): continue
        pos = [r for r in gov_req(get(b, "possible")) if "has_ethic" not in r]        # этики редактор подстраивает сам
        pot = gov_req(get(b, "potential")); play = get(b, "playable")
        req = pot + pos + ([ser(play)] if isinstance(play, list) and play else [])
        out.append(dict(key=k, icon="gfx/interface/icons/governments/authorities/%s.dds" % ("auth_machine_intelligence" if k == "auth_ancient_machine_intelligence" else k), req=req))   # у древнего разума своего значка нет (error.log)
    return out

def traits(vc):
    out = []
    for k, (b, f) in top(os.path.join(vc, "traits/*.txt")).items():
        if not k.startswith("trait_") or get(b, "leader_class") is not None or get(b, "leader_trait") is not None: continue
        if k.startswith(("trait_presapient", "trait_auto_")) or "presapient" in f: continue
        arch = [x for _, _, x in (get(b, "allowed_archetypes") or []) if isinstance(x, str)]
        if arch == ["PRESAPIENT"]: continue
        opp = [x.strip('"') for _, _, x in (get(b, "opposites") or []) if isinstance(x, str)]
        icon = get(b, "icon")
        icon = icon.strip('"') if isinstance(icon, str) and not icon.startswith("@") else "gfx/interface/icons/traits/%s.dds" % k
        initial, mod = get(b, "initial"), get(b, "modification")
        cat = get(b, "category") or "normal"
        grp = ("robot" if set(arch) & {"ROBOT", "MACHINE"} and not set(arch) & {"BIOLOGICAL", "LITHOID"}
               else "ascend" if cat in ("cyborg", "psionic", "advanced_genetic", "overtuned", "malleable", "mutation") or "ascension" in f or "cyborg" in f
               else "bio")
        if re.match(r"trait_pc_\w+_preference$", k): grp = "hab"
        out.append(dict(key=k, icon=icon, arch=arch, opp=opp, special=(initial == "no" and mod == "no"), cat=cat, grp=grp))
    return out

_VARS = {}
def _vars(vc):
    if not _VARS:
        for f in glob.glob(os.path.join(vc, "**", "*.txt"), recursive=True):
            for m in re.finditer(r"(?m)^\s*(@\w+)\s*=\s*(-?[\d.]+)\s*$", _strip(open(f, encoding="utf-8-sig", errors="ignore").read())):
                _VARS.setdefault(m.group(1), m.group(2))
    return _VARS
def resolve(txt, vc):
    """@переменные игры → числа; если какую-то не нашли — условие не используем (None)."""
    v = _vars(vc)
    txt = re.sub(r"@\w+", lambda m: v.get(m.group(0), m.group(0)), txt)
    return None if "@" in txt or "$" in txt else txt
def perks(vc, spr):
    out = []
    for k, (b, f) in top(os.path.join(vc, "ascension_perks/*.txt")).items():
        req = [r for r in (resolve(ser(x), vc) for x in (get(b, "potential"), get(b, "possible")) if isinstance(x, list) and x) if r]
        tex = spr.get("GFX_" + k) or "gfx/interface/icons/ascension_perks/%s.dds" % k
        out.append(dict(key=k, icon=tex, req=req))
    return out

def tradition_trees(vc, spr):
    out = []
    for k, (b, f) in top(os.path.join(vc, "tradition_categories/*.txt")).items():
        if "dummy" in f: continue
        trs = [x.strip('"') for _, _, x in (get(b, "traditions") or []) if isinstance(x, str)]
        ad, fin = (get(b, "adoption_bonus") or "").strip('"'), (get(b, "finish_bonus") or "").strip('"')
        if not ad: continue
        pot = get(b, "potential")
        tex = spr.get("GFX_tradition_category_icon_" + k) or "gfx/interface/icons/traditions/%s.dds" % ad
        req = resolve(ser(pot), vc) if isinstance(pot, list) and pot else None
        out.append(dict(key=k, adopt=ad, finish=fin, trads=trs, icon=tex, req=[req] if req else []))
    return out

def policies(vc, spr):
    out = []
    for k, (b, f) in top(os.path.join(vc, "policies/*.txt")).items():
        opts = []
        for o in getall(b, "option"):
            n = (get(o, "name") or "").strip('"')
            if not n or re.search(r"fallen_empire|_nomad$|_ignorant|_questioning|_eager|_fearful|_uncertain|culture_shock", n): continue
            fl = [x for _, _, x in (get(o, "policy_flags") or []) if isinstance(x, str)]
            ic = (get(o, "icon") or "").strip('"')
            opts.append(dict(name=n, flag=(n if n in fl else (fl[0] if fl else None)), icon=spr.get(ic)))
        if len(opts) >= 2:
            out.append(dict(key=k, cat=get(b, "category") or "misc", opts=opts))
    return out

SHIPSETS = ["mammalian_01", "reptilian_01", "avian_01", "arthropoid_01", "molluscoid_01", "fungoid_01", "plantoid_01", "humanoid_01",
            "lithoid_01", "necroid_01", "aquatic_01", "toxoid_01", "subterranean_01", "solarpunk_01", "cybernetics_01", "synthetics_01",
            "biogenesis_01", "biogenesis_02", "wilderness_01", "infernal_01", "psionic_01", "mindwarden_01", "caravaneer_01", "slaver_01"]
def graphical_cultures(vc):
    keys = list(top(os.path.join(vc, "graphical_culture/*.txt")).keys())
    return [k for k in SHIPSETS if k in keys], [k for k in keys if k not in SHIPSETS]

def portraits(vc):
    """класс вида → список портретов (для «◀ ▶»)."""
    out = {}
    for k, (b, f) in top(os.path.join(vc, "portrait_sets/*.txt")).items():
        cls = get(b, "species_class")
        ps = []
        def walk(nodes):
            for kk, op, v in nodes:
                if kk == "portraits" and isinstance(v, list): ps.extend(x.strip('"') for _, _, x in v if isinstance(x, str))
                elif kk in ("conditional_portraits", "non_randomized_portraits") and isinstance(v, list): walk(v)
                elif kk is None and isinstance(v, list): walk(v)
        walk(b)
        if cls and ps: out.setdefault(cls, []).extend(p for p in ps if p not in out.get(cls, []))
    return out

if __name__ == "__main__":
    import sys
    vc, vi = sys.argv[1], sys.argv[2]
    spr = sprite_textures(vi)
    c = civics(vc); print("civics", len(c), {k: sum(1 for x in c if x["cat"] == k) for k in ("reg", "corp", "hive", "machine", "special")})
    for x in c[:3]: print("  ", x)
    a = authorities(vc); print("auth", [(x["key"], x["req"]) for x in a])
    t = traits(vc); print("traits", len(t), {g: sum(1 for x in t if x["grp"] == g) for g in ("bio", "robot", "ascend", "hab")})
    p = perks(vc, spr); print("perks", len(p), p[0])
    tt = tradition_trees(vc, spr); print("trees", len(tt), tt[0]["key"], tt[0]["icon"], tt[0]["req"][:1])
    po = policies(vc, spr); print("policies", len(po), sum(len(x["opts"]) for x in po), po[0]["opts"][:2])
    print("gc", graphical_cultures(vc))
    pr = portraits(vc); print("portrait classes", {k: len(v) for k, v in pr.items()})
