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
        out.append(dict(key=k, icon=icon, req=req, cat=cat, mods=modlist(b, vc)))
    return out

def authorities(vc):
    out = []
    for k, (b, f) in top(os.path.join(vc, "governments/authorities/*.txt")).items():
        if not k.startswith("auth_"): continue
        pos = [r for r in gov_req(get(b, "possible")) if "has_ethic" not in r]        # этики редактор подстраивает сам
        pot = gov_req(get(b, "potential")); play = get(b, "playable")
        req = pot + pos + ([ser(play)] if isinstance(play, list) and play else [])
        out.append(dict(key=k, icon="gfx/interface/icons/governments/authorities/%s.dds" % ("auth_machine_intelligence" if k == "auth_ancient_machine_intelligence" else k), req=req, mods=modlist(b, vc)))   # у древнего разума своего значка нет (error.log)
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
        out.append(dict(key=k, icon=icon, arch=arch, opp=opp, special=(initial == "no" and mod == "no"), cat=cat, grp=grp, mods=modlist(b, vc)))
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
def modlist(b, vc, keys=("modifier", "country_modifier")):
    """11.5.5: постоянные модификаторы объекта игры (что он даёт) — [(ключ, число)]; условные (triggered_*) не берём."""
    out = []
    for key in keys:
        for blk in getall(b, key):
            if not isinstance(blk, list): continue
            for kk, op, v in blk:
                if not kk or not isinstance(v, str) or kk in ("description", "custom_tooltip"): continue
                r = resolve(v, vc)
                try: out.append((kk, float(r)))
                except (TypeError, ValueError): pass
    return out
def ethic_mods(vc):
    return {k: modlist(b, vc) for k, (b, f) in top(os.path.join(vc, "ethics/*.txt")).items()}
def perks(vc, spr):
    out = []
    for k, (b, f) in top(os.path.join(vc, "ascension_perks/*.txt")).items():
        req = [r for r in (resolve(ser(x), vc) for x in (get(b, "potential"), get(b, "possible")) if isinstance(x, list) and x) if r]
        tex = spr.get("GFX_" + k) or "gfx/interface/icons/ascension_perks/%s.dds" % k
        out.append(dict(key=k, icon=tex, req=req, mods=modlist(b, vc)))
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
            opts.append(dict(name=n, flag=(n if n in fl else (fl[0] if fl else None)), icon=spr.get(ic), mods=modlist(o, vc)))
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

# ---- 11.7: черты лидеров (редактор держав → «Лидеры»)
LT_MODS = (("councilor_modifier", "В совете", "On the council"), ("self_modifier", "Самому лидеру", "To the leader"),
           ("modifier", "Где назначен", "Where assigned"), ("planet_modifier", "Планете губернатора", "Governor's planet"),
           ("sector_modifier", "Сектору", "Sector"), ("fleet_modifier", "Флоту", "Fleet"), ("army_modifier", "Армиям", "Armies"),
           ("system_modifier", "Системе", "System"), ("federation_modifier", "Федерации", "Federation"), ("galcom_modifier", "Галактическому сообществу", "Galactic Community"))
def leader_traits(vc, spr):
    """[{key, classes, cat, icon, tier, mods:[(блок, [(мод, число)])]}]. cat: negative / special (ветеран, подкласс, судьба) / basic."""
    out = []
    for k, (b, f) in top(os.path.join(vc, "traits/*.txt")).items():
        ins = [x for x in getall(b, "inline_script") if isinstance(x, list)]
        icon_is = [x for x in ins if (get(x, "script") or "").startswith("trait/icon")]
        lc = get(b, "leader_class")
        if lc is None and not icon_is: continue                       # черта вида, не лидера
        if isinstance(lc, list): classes = sorted(x for _, _, x in lc if isinstance(x, str))
        elif lc == "all": classes = ["commander", "official", "scientist"]
        else:
            cl = [get(x, "CLASS") for x in icon_is if get(x, "CLASS")]
            classes = sorted(set(c for c in cl if c in ("commander", "official", "scientist"))) or ["commander", "official", "scientist"]
        script = (get(icon_is[0], "script") if icon_is else "") or ""
        typ = get(b, "leader_trait_type") or "basic"
        neg = typ == "negative" or "negative" in script or get(b, "negative") == "yes"
        cat = "negative" if neg else ("special" if typ in ("veteran", "subclass", "destiny") or "subclass" in script else "basic")
        gfx = None
        for x in icon_is:
            if get(x, "ICON"): gfx = get(x, "ICON").strip('"')
        if not gfx and isinstance(get(b, "icon"), list):
            for lay in getall(get(b, "icon"), "layer"):
                ic = get(lay, "icon")
                if isinstance(ic, str) and ic.strip('"') not in ("GFX_trait_bg",): gfx = ic.strip('"')
        elif isinstance(get(b, "icon"), str): gfx = get(b, "icon").strip('"')
        tex = spr.get(gfx) if gfx and gfx.startswith("GFX_") else gfx
        tier = 0
        for x in icon_is:
            try: tier = int(get(x, "TIER") or 0)
            except ValueError: pass
        mods = [(blk, modlist(b, vc, keys=(blk,))) for blk, _r, _e in LT_MODS]
        repl = [x.strip('"') for _, _, x in (get(b, "replace_traits") or []) if isinstance(x, str)]
        opp = [x.strip('"') for _, _, x in (get(b, "opposites") or []) if isinstance(x, str)] if isinstance(get(b, "opposites"), list) else []
        out.append(dict(key=k, classes=classes, cat=cat, icon=tex, tier=tier, repl=repl, opp=opp, mods=[(bk, m) for bk, m in mods if m], file=f))
    # 11.8.2: противоположные черты — в обе стороны (в файлах игры часто указаны только у одной из пары)
    by = {x["key"]: x for x in out}
    for x in out: x["opp"] = [o for o in x["opp"] if o in by and o != x["key"]]
    for x in out:
        for o in x["opp"]:
            if o in by and x["key"] not in by[o]["opp"]: by[o]["opp"].append(x["key"])
    return out

def technologies(vc, spr):
    """11.7: технологии игры — [{key, area, tier, cats, rare, dangerous, repeat, start, special, icon, mods, file}].
    special — обычно не выпадают в исследовании (weight = 0 / только по событию / технологии Павших империй)."""
    out = []
    for f in sorted(glob.glob(os.path.join(vc, "technology/*.txt"))):
        if "documentation" in f or "README" in f.upper(): continue
        for k, op, b in parse(open(f, encoding="utf-8-sig").read()):
            if not k or not isinstance(b, list) or k.startswith("@") or k == "inline_script": continue
            area = get(b, "area")
            if area not in ("physics", "society", "engineering"): continue
            tr = resolve(get(b, "tier") or "0", vc)
            try: tier = int(float(tr))
            except (TypeError, ValueError): tier = 0
            cats = [x for _, _, x in (get(b, "category") or []) if isinstance(x, str)]
            lv = get(b, "levels")
            repeat = lv is not None and str(lv).strip() not in ("0", "1")
            w = get(b, "weight")
            start = get(b, "start_tech") == "yes"
            fe = "fallen_empire" in f
            special = not start and not repeat and (fe or (isinstance(w, str) and resolve(w, vc) in ("0", "0.0")))
            ic = get(b, "icon")
            ic = ic.strip('"') if isinstance(ic, str) else k
            tex = spr.get("GFX_" + ic) or "gfx/interface/icons/technologies/%s.dds" % ic
            pot = get(b, "potential")         # 11.7.6: только своё условие технологии (без предыдущих) — «держава не может её иметь вообще»
            req = resolve(ser(pot), vc) if isinstance(pot, list) and pot else None
            out.append(dict(key=k, area=area, tier=tier, cats=cats, rare=get(b, "is_rare") == "yes", dangerous=get(b, "is_dangerous") == "yes",
                            repeat=repeat, start=start, special=special, icon=tex, mods=modlist(b, vc, keys=("modifier",)), file=os.path.basename(f),
                            req=[req] if req else []))
    return out

EDICT_GRP = {"00_edicts.txt": 1, "01_campaigns.txt": 2, "02_ambitions.txt": 3, "03_sacrifices.txt": 3}   # остальные файлы (DLC) — 4
def edicts(vc, spr):
    """11.7: указы игры — [{key, grp, perpetual, icon, req, mods, file}]."""
    out = []
    for k, (b, f) in top(os.path.join(vc, "edicts/*.txt")).items():
        ln = str(get(b, "length") or "")
        pot = get(b, "potential")
        req = resolve(ser(pot), vc) if isinstance(pot, list) and pot else None
        ic = (get(b, "icon") or "").strip('"')
        out.append(dict(key=k, grp=EDICT_GRP.get(f, 4), perpetual=ln in ("@EdictPerpetual", "-1"), icon=spr.get(ic) if ic.startswith("GFX_") else (ic or None),
                        req=[req] if req else [], mods=modlist(b, vc), file=f))
    return out

# ---------------------------------------------------------------- 11.8.1: готовые проекты DTP («пребилды») для типов, которых нет ни у одной державы
def _cost(b, vc):
    r = get(b, "resources")
    if not isinstance(r, list): return 0.0
    c = get(r, "cost")
    tot = 0.0
    for blk in ([c] if isinstance(c, list) else []):
        for k, op, v in blk:
            if isinstance(v, str):
                try: tot += float(resolve(v, vc))
                except (TypeError, ValueError): pass
    return tot
def components(vc):
    out = []
    for f in sorted(glob.glob(os.path.join(vc, "component_templates/*.txt"))):
        if "documentation" in f: continue
        for k, op, b in parse(open(f, encoding="utf-8-sig", errors="ignore").read()):
            if not (isinstance(b, list) and k and k.endswith("component_template")): continue
            pot = get(b, "potential")
            pr = get(b, "prerequisites")
            pr = [x.strip('"') for _, _, x in pr if isinstance(x, str)] if isinstance(pr, list) else []
            out.append(dict(kind=k, key=(get(b, "key") or "").strip('"'), size=(get(b, "size") or "").lower(), set=(get(b, "component_set") or "").strip('"'),
                            pre=bool(pr), prl=pr, pot=pot if isinstance(pot, list) else [], cost=_cost(b, vc), hidden=get(b, "hidden") == "yes"))
    return out
def _ship_triggers(vc):
    """ship_uses_* (scripted triggers игры) → множество размеров кораблей, для которых условие верно."""
    defs = {}
    for f in glob.glob(os.path.join(vc, "scripted_triggers/*.txt")):
        for k, op, b in parse(open(f, encoding="utf-8-sig", errors="ignore").read()):
            if k and k.startswith("ship_uses_") and isinstance(b, list): defs[k] = b
    memo = {}
    def sizes(name, seen=()):
        if name in memo: return memo[name]
        acc = set()
        def walk(nodes):
            for k, op, v in nodes:
                if k == "is_ship_size" and isinstance(v, str): acc.add(v)
                elif k in defs and v == "yes" and k not in seen: acc.update(sizes(k, seen + (name,)))
                elif isinstance(v, list) and k not in ("NOT", "NOR"): walk(v)
        walk(defs.get(name, []))
        memo[name] = acc
        return acc
    return {k: sizes(k) for k in defs}
def _pot_ok(nodes, size, bio, ST):
    """Мини-проверка potential детали для размера корабля: ship_uses_*, is_ship_size, country_uses_bio_ships; прочее — «да»."""
    def ev(k, op, v):
        if k in ("OR",): return any(ev(*n) for n in v) if isinstance(v, list) and v else True
        if k in ("NOR",): return not any(ev(*n) for n in v) if isinstance(v, list) else True
        if k in ("NOT",): return not all(ev(*n) for n in v) if isinstance(v, list) else True
        if k in ("NAND",): return not all(ev(*n) for n in v) if isinstance(v, list) else True
        if isinstance(v, list): return all(ev(*n) for n in v)
        if k in ST: return (size in ST[k]) == (v == "yes")
        if k == "is_ship_size": return size == v
        if k == "country_uses_bio_ships": return bio == (v == "yes")
        if k == "is_arkship_ship": return v == "no"
        return True
    return all(ev(*n) for n in nodes)
_DEFKW = ("ARMOR", "SHIELD", "CARAPACE", "SKIN", "EPIDERMIS", "DEFLECTOR", "HULL")
def prebuilt_designs(vc, sizes):
    """{ship_size: текст ship_design} — секции с наибольшим числом слотов, лучшие (по цене) изучаемые детали подходящего размера."""
    S = top(os.path.join(vc, "ship_sizes/*.txt"))
    slot_t = {}
    for f in glob.glob(os.path.join(vc, "component_slot_templates/*.txt")):
        for k, op, b in parse(open(f, encoding="utf-8-sig", errors="ignore").read()):
            if isinstance(b, list): slot_t[k] = ((get(b, "size") or "").lower(), (get(b, "component") or "").lower())
    secs = []
    for f in glob.glob(os.path.join(vc, "section_templates/*.txt")):
        for k, op, b in parse(open(f, encoding="utf-8-sig", errors="ignore").read()):
            if k != "ship_section_template" or not isinstance(b, list): continue
            ss = get(b, "ship_size")
            ss = [x for _, _, x in ss if isinstance(x, str)] if isinstance(ss, list) else [ss]
            secs.append(dict(key=(get(b, "key") or "").strip('"'), sizes=ss, slot=(get(b, "fits_on_slot") or "").strip('"'),
                             comps=[((get(c, "name") or "").strip('"'), (get(c, "template") or "").strip('"')) for c in getall(b, "component_slot") if isinstance(c, list)],
                             util={u: int(get(b, "%s_utility_slots" % u) or 0) for u in ("small", "medium", "large", "aux")}))
    C = components(vc)
    ST = _ship_triggers(vc)
    # «обычные» технологии дерева: не редкие, не особые (weight 0 / Павшие), не стартовые-событийные
    TN = {x["key"] for x in technologies(vc, {}) if not x["rare"] and not x["special"]}
    for c in C: c["norm"] = bool(c["prl"]) and all(p in TN for p in c["prl"])
    cur = {}
    def pick(cands, bio):
        cands = [c for c in cands if not c["hidden"] and c["key"] and _pot_ok(c["pot"], cur["size"], bio, ST)]
        pref = [c for c in cands if c["norm"]] or [c for c in cands if c["pre"]] or cands
        exo = lambda k: any(w in k for w in ("LM_", "PSI", "ARCHAEO", "DARK_MATTER", "_ED_", "ED_WEAPON", "NANITE", "CRYSTAL", "DRAGON", "AMOEBA"))
        return max(pref, key=lambda c: (not exo(c["key"]), c["cost"], c["key"]))["key"] if pref else None
    body = {}
    allsz = list(sizes) + [s for s in S if re.match(r"^(.+)_stage_\d+$", s) and get(S[s][0], "growth_stage_descriptor")
                            and any(s.rsplit("_stage_", 1)[0] == x.rsplit("_stage_", 1)[0] for x in sizes)]
    for size in dict.fromkeys(allsz):
        if size not in S: continue
        b, f = S[size]
        cur["size"] = size
        bio = any(x in size for x in ("mauler", "weaver", "harbinger", "stinger", "bio_titan"))
        slots = [k_ for k_, op_, v_ in get(b, "section_slots")] if isinstance(get(b, "section_slots"), list) else []
        slots = [s.strip('"') for s in slots if s]
        parts = []
        ok = True
        for sl in slots:
            cand = [s for s in secs if size in s["sizes"] and s["slot"] == sl]
            if not cand: ok = False; break
            sec = max(cand, key=lambda s: (len(s["comps"]) + sum(s["util"].values()), s["key"]))
            comps = []
            for nm, st in sec["comps"]:
                sz, kind = slot_t.get(st, ("", ""))
                if not sz: continue
                if kind == "weapon":
                    k_ = pick([c for c in C if c["kind"] == "weapon_component_template" and c["size"] == sz], bio)
                else:
                    k_ = pick([c for c in C if c["kind"] == "strike_craft_component_template" and c["size"] == sz], bio)
                if k_: comps.append((nm, k_))
            for u in ("small", "medium", "large"):
                for n in range(1, sec["util"][u] + 1):
                    cands = [c for c in C if c["kind"] == "utility_component_template" and c["size"] == u and any(w in c["key"] for w in _DEFKW)]
                    want = "SHIELD" if n % 2 else "ARMOR"
                    k_ = pick([c for c in cands if want in c["key"]], bio) or pick(cands, bio)
                    if k_: comps.append(("%s_UTILITY_%d" % (u.upper(), n), k_))
            parts.append('\tsection = {\n\t\ttemplate = "%s"\n\t\tslot = "%s"\n%s\t}\n' % (sec["key"], sl, "".join('\t\tcomponent = { slot = "%s" template = "%s" }\n' % c for c in comps)))
        if not ok or not parts: continue
        req = []
        for rs in [x.strip('"') for x in getall(b, "required_component_set") if isinstance(x, str)]:
            k_ = pick([c for c in C if c["set"] == rs], bio)
            if k_: req.append(k_)
        body[size] = "\tship_size = %s\n%s%s" % (size, "".join(parts), "".join('\trequired_component = "%s"\n' % r for r in req))
    # 11.9.1: биокорабли с этапами роста (Мучитель, Ткач, Предвестник, Жало и их отпрыски) — проект игры обязан описать ВСЕ этапы
    # в growth_stages = { {этап 1} {этап 2} {этап 3} } (иначе «Invalid Ship Design»); корабль нужного этапа — create_ship growth_stage = N.
    out = {}
    for size in sizes:
        if size not in body: continue
        m = re.match(r"^(.+)_stage_(\d+)$", size)
        if m and get(S[size][0], "growth_stage_descriptor"):
            fam, n = m.group(1), int(m.group(2))
            stages = []
            k = 1
            while "%s_stage_%d" % (fam, k) in S:
                st = "%s_stage_%d" % (fam, k)
                if st not in body: break
                stages.append(st); k += 1
            if n > len(stages): continue
            nm = "DTP_PREBUILT_%s" % fam
            txt = 'ship_design = {\n\tname = "%s"\n\tis_event_design = yes\n\tgrowth_stages = {\n%s\t}\n}\n' % (
                nm, "".join("\t\t{\n%s\t\t}\n" % "".join("\t\t" + l + "\n" for l in body[st].rstrip("\n").split("\n")) for st in stages))
            out[size] = dict(name=nm, stage=n, text=txt, first=stages[0])
        else:
            nm = "DTP_PREBUILT_%s" % size
            out[size] = dict(name=nm, stage=None, first=size,
                             text='ship_design = {\n\tname = "%s"\n\tis_event_design = yes\n%s}\n' % (nm, body[size]))
    return out
