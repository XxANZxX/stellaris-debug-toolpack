# -*- coding: utf-8 -*-
"""11.3: данные для редактора планеты — читаются из файлов самой игры (common, interface/*.gfx).
Условия игры (potential / allow / prerequisites) переводятся в условия планеты: редактор показывает
красную пометку там же, где игра обычно запрещает."""
import os, re
from eddata import top, get, getall, ser, resolve, sprite_textures

def _clean(nodes):
    """Условие без inline_script и пустых блоков (их нельзя перенести в scripted trigger)."""
    out = []
    for k, op, v in nodes or []:
        if k in ("inline_script", "custom_tooltip_fail", "text"): continue
        if k == "custom_tooltip" and isinstance(v, list):
            inner = _clean([x for x in v if x[0] not in ("fail_text", "success_text", "text")])
            out += inner; continue
        if isinstance(v, list):
            vv = _clean(v)
            if not vv and k in ("OR", "AND", "NOT", "NOR", "NAND", "owner", "from", "planet", "solar_system", "limit"): continue
            out.append((k, op, vv))
        else:
            out.append((k, op, v))
    return out
def _req(vc, *blocks):
    out = []
    for b in blocks:
        if isinstance(b, list) and b:
            t = resolve(ser(_clean(b)), vc)
            if t and t.strip() and "inline_script" not in t: out.append(t)
    return out
def _s(v): return v.strip('"') if isinstance(v, str) else None

def planet_classes(vc, spr):
    out = []
    for k, (b, f) in top(os.path.join(vc, "planet_classes/*.txt")).items():
        if not k.startswith("pc_") or get(b, "star") == "yes": continue
        ic = _s(get(b, "icon"))
        tex = (spr.get(ic) or ic) if ic else None
        col = get(b, "colonizable") == "yes"
        clim = _s(get(b, "climate"))
        cat = "hab" if clim in ("dry", "wet", "cold") and k not in ("pc_city", "pc_relic") else ("special" if col else "barren")
        if k in ("pc_gaia",): cat = "hab"
        out.append(dict(key=k, icon=tex, col=col, cat=cat))
    return out

def star_planet_icons(vc, spr):
    """класс звезды (sc_*) → значок её «планеты-звезды» (GFX_planet_type_*)."""
    pcs = top(os.path.join(vc, "planet_classes/*.txt"))
    out = {}
    for k, (b, f) in top(os.path.join(vc, "star_classes/*.txt")).items():
        if not k.startswith("sc_"): continue
        pl = get(b, "planet")
        pk = None
        if isinstance(pl, list):
            pk = get(pl, "key")
            if pk is None:
                for kk, op, v in pl:
                    if isinstance(v, list) and get(v, "key"): pk = get(v, "key"); break
        if pk and pk in pcs:
            ic = _s(get(pcs[pk][0], "icon"))
            if ic: out[k] = spr.get(ic) or ic
    return out

_SAFE_RES = ("energy", "minerals", "food", "alloys", "consumer_goods", "influence", "unity", "physics_research", "society_research", "engineering_research",
             "exotic_gases", "rare_crystals", "volatile_motes")
DEP_CATS = [("deposit_cat_energy", "energy"), ("deposit_cat_minerals", "minerals"), ("deposit_cat_food", "food"),
            ("deposit_cat_rare_resource", "rare"), ("deposit_cat_rare", "rare"), ("deposit_cat_misc", "rare")]
def deposits(vc):
    out = []
    seen_icons = set()
    for k, (b, f) in top(os.path.join(vc, "deposits/*.txt")).items():
        if not k.startswith("d_") or k == "d_null_deposit": continue
        cat = _s(get(b, "category")) or ""
        res = get(b, "resources")
        rcat = _s(get(res, "category")) if isinstance(res, list) else None
        ic = _s(get(b, "icon"))                 # 11.3.1: без своего значка у залежи файла "<ключ>.dds" нет (error.log) — значок ресурса
        if ic and ic.startswith("unused/"): ic = None
        rtex = None
        if not ic:
            prod = get(res, "produces") if isinstance(res, list) else None
            rr = [kk for kk, op, v in (prod or []) if kk in _SAFE_RES]
            pm = ser(get(b, "planet_modifier") or [])
            if rr: rtex = "gfx/interface/icons/resources/%s.dds" % rr[0]
            elif "generator" in pm: rtex = "gfx/interface/icons/resources/energy.dds"
            elif "mining" in pm: rtex = "gfx/interface/icons/resources/minerals.dds"
            elif "farming" in pm: rtex = "gfx/interface/icons/resources/food.dds"
        blocker = "blocker" in cat
        orbital = (rcat or "").startswith("orbital") or get(b, "is_for_colonizable") == "no" or (not cat and rcat)
        if blocker: g = "block"
        elif orbital: g = "orbit"
        else: g = dict(DEP_CATS).get(cat, "rare")
        if g == "rare" and not cat: g = "other"
        req = _req(vc, get(b, "potential"))
        tex = ("gfx/interface/icons/deposits/%s.dds" % ic) if ic else (rtex or ("gfx/interface/icons/deposits/default_blocker.dds" if blocker else "gfx/interface/icons/deposits/default.dds"))
        out.append(dict(key=k, icon=tex, grp=g, req=req, file=f))
    return out

def districts(vc):
    out = []
    for k, (b, f) in top(os.path.join(vc, "districts/*.txt")).items():
        if not k.startswith("district_") or "DOCUMENTATION" in f: continue
        ic = _s(get(b, "icon")) or k
        req = _req(vc, get(b, "potential"), get(b, "allow"))
        slots = [_s(x) for _, _, x in (get(b, "zone_slots") or []) if isinstance(x, str)]
        grp = {"00_urban_districts.txt": "urban", "02_rural_districts.txt": "rural", "01_arcology_districts.txt": "arc",
               "03_habitat_districts.txt": "hab", "04_ringworld_districts.txt": "ring"}.get(f, "other")
        out.append(dict(key=k, icon="gfx/interface/icons/districts/%s.dds" % ic, req=req, slots=slots, grp=grp))
    return out

def zones(vc, spr, dists):
    zs = top(os.path.join(vc, "zones/*.txt"))
    slots = top(os.path.join(vc, "zone_slots/*.txt"))
    slot_sets = {k: [_s(x) for _, _, x in (get(b, "included_zone_sets") or []) if isinstance(x, str)] for k, (b, f) in slots.items()}
    out = []
    for k, (b, f) in zs.items():
        if not k.startswith("zone_"): continue
        sets = [_s(x) for _, _, x in (get(b, "zone_sets") or []) if isinstance(x, str)]
        ds = []
        for d in dists:
            for sl in d["slots"]:
                if set(slot_sets.get(sl, [])) & set(sets) and d["key"] not in ds: ds.append(d["key"])
        if not ds: continue
        ic = _s(get(b, "icon"))
        req = _req(vc, get(b, "potential"), get(b, "unlock"))
        out.append(dict(key=k, icon=(spr.get(ic) or ic) if ic else None, req=req, dists=ds[:6]))
    return out

BLD_GRP = {"research": "science", "resource": "resource", "manufacturing": "industry", "unity": "unity", "amenity": "amenity",
           "army": "army", "government": "gov", "trade": "gov", "pop_assembly": "gov"}
def buildings(vc):
    out = []
    for k, (b, f) in top(os.path.join(vc, "buildings/*.txt")).items():
        if not k.startswith("building_") or "example" in f or "holding" in f: continue
        if get(b, "owner_type") not in (None, "normal"): continue      # 11.3.1: филиалы корпораций и владения — не обычные здания (error.log)
        cat = _s(get(b, "category")) or ""
        ic = _s(get(b, "icon")) or k
        prereq = [_s(x) for _, _, x in (get(b, "prerequisites") or []) if isinstance(x, str)]
        req = _req(vc, get(b, "potential"), get(b, "allow"))
        if prereq: req.append("owner = { %s }" % " ".join("has_technology = %s" % t for t in prereq))
        if "capital" in f or k.endswith("_capital") or "capital" in k: g = "capital"
        elif any(s in f for s in ("event", "fallen_empire", "first_contact", "paragon", "astral", "cosmic", "machine_age", "grand_archive", "wilderness", "biogenesis", "extreme_frontiers", "shroud", "nomads", "primitive", "branch_office", "deposit")): g = "special"
        else: g = BLD_GRP.get(cat, "special")
        out.append(dict(key=k, icon="gfx/interface/icons/buildings/%s.dds" % ic, req=req, grp=g))
    return out

def anomalies(vc, spr):
    out = []
    for k, (b, f) in top(os.path.join(vc, "anomalies/*.txt")).items():
        if "README" in f or "tutorial" in f or "TODO" in f: continue
        pic = _s(get(b, "picture"))
        lv = get(b, "level")
        out.append(dict(key=k, icon=spr.get(pic) if pic else None, level=lv))
    return out

def arc_sites(vc, spr):
    out = []
    for k, (b, f) in top(os.path.join(vc, "archaeological_site_types/*.txt")).items():
        if k == "random": continue
        pic = _s(get(b, "picture"))
        out.append(dict(key=k, icon=spr.get(pic) if pic else None))
    return out

def colony_types(vc, spr):
    out = []
    for k, (b, f) in top(os.path.join(vc, "colony_types/*.txt")).items():
        if not k.startswith("col_"): continue
        ic = _s(get(b, "icon"))
        req = _req(vc, get(b, "potential"))
        grp = {"00_colony_types.txt": "main", "01_habitat_colony_types.txt": "hab"}.get(f, "special")
        out.append(dict(key=k, icon=(spr.get(ic) or ic) if ic else None, req=req, grp=grp))
    return out

def planet_modifiers(vc):
    """Особенности природы планеты (pm_*) — статические модификаторы с собственными значками."""
    sm = top(os.path.join(vc, "static_modifiers/*.txt"))
    pms = top(os.path.join(vc, "planet_modifiers/*.txt"))
    out = []
    for k, (b, f) in pms.items():
        mod = _s(get(b, "modifier")) or k
        if mod not in sm: continue
        ic = _s(get(sm[mod][0], "icon"))
        if not ic: continue
        out.append(dict(key=mod, icon=ic if ic.endswith(".dds") else None))
    return out

if __name__ == "__main__":
    import sys
    vc, vi = sys.argv[1], sys.argv[2]
    spr = sprite_textures(vi)
    import collections
    pc = planet_classes(vc, spr); print("pc", len(pc), collections.Counter(x["cat"] for x in pc), sum(1 for x in pc if not x["icon"]))
    print("stars", star_planet_icons(vc, spr))
    d = deposits(vc); print("dep", len(d), collections.Counter(x["grp"] for x in d))
    ds = districts(vc); print("dist", len(ds), collections.Counter(x["grp"] for x in ds))
    z = zones(vc, spr, ds); print("zones", len(z), sum(1 for x in z if not x["icon"]))
    bl = buildings(vc); print("bld", len(bl), collections.Counter(x["grp"] for x in bl))
    an = anomalies(vc, spr); print("anom", len(an), sum(1 for x in an if not x["icon"]))
    a = arc_sites(vc, spr); print("arc", len(a), sum(1 for x in a if not x["icon"]))
    ct = colony_types(vc, spr); print("col", len(ct), collections.Counter(x["grp"] for x in ct), sum(1 for x in ct if not x["icon"]))
    pm = planet_modifiers(vc); print("pm", len(pm), pm[:3])
    print(d[0], bl[0]["req"][:2], z[0])
