# -*- coding: utf-8 -*-
"""Проверка Debug Toolpack 2.0: синтаксис, ссылки, глубина вложенности и сверка
всех команд со справочником игры (effects/triggers/scopes/modifiers 4.5.1).
python3 validate2.py <папка_мода> <папка_справочника>"""
import os, re, sys, glob, collections
ROOT, DOCS = sys.argv[1], sys.argv[2]
errors, warns = [], []
def strip(t): return re.sub(r'#.*', '', re.sub(r'"[^"]*"', '""', t))
txt = {f: open(f, encoding="utf-8-sig").read() for f in glob.glob(os.path.join(ROOT, "**/*.txt"), recursive=True)
       if not f.replace("\\", "/").endswith(("diplomatic_actions/zz_dtp_declare_war.txt", "game_rules/00_rules.txt"))}   # копия игрового файла — проверяется отдельно ниже
gui = {f: open(f, encoding="utf-8-sig").read() for f in glob.glob(os.path.join(ROOT, "interface/*.gui"))}
gfx = {f: open(f, encoding="utf-8-sig").read() for f in glob.glob(os.path.join(ROOT, "interface/*.gfx"))}
for f, t in {**txt, **gui, **gfx}.items():
    s, d = strip(t), 0
    for ch in s:
        d += (ch == "{") - (ch == "}")
        if d < 0: errors.append("лишняя } в " + f); break
    if d > 0: errors.append("незакрытые { в " + f)
# справочник
E = set(re.findall(r'^([a-z_]\w*) - ', open(os.path.join(DOCS, "4.5.1_game_effects.log")).read(), re.M))
T = set(re.findall(r'^([a-z_]\w*) - ', open(os.path.join(DOCS, "4.5.1_game_triggers.log")).read(), re.M))
S = set(re.findall(r'^([a-z_]\w*) - ', open(os.path.join(DOCS, "4.5.1_game_scopes.log")).read(), re.M))
M = set(re.findall(r'^- (\w+), Category', open(os.path.join(DOCS, "4.5.1_game_modifiers.log")).read(), re.M))
code = "\n".join(strip(t) for f, t in txt.items() if "static_modifiers" not in f and "star_classes" not in f)
defs = lambda sub: set(re.findall(r'^(\w+)\s*=\s*\{', "\n".join(strip(txt[f]) for f in txt if sub in f), re.M))
eff, trg, btn, smod, opn = defs("scripted_effects"), defs("scripted_triggers"), defs("button_effects"), defs("static_modifiers"), defs("opinion_modifiers")
starcls = defs("star_classes")
# 10.9.1: скриптовые триггеры/эффекты самой игры (условия технологий копируются из файлов игры)
_vc = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[3]))), "vanilla_common", "common") if len(sys.argv) > 3 else ""
if _vc and os.path.isdir(_vc):
    for _sub in ("scripted_triggers", "scripted_effects"):
        for _f in os.listdir(os.path.join(_vc, _sub)):
            trg |= set(re.findall(r"(?m)^(\w+)\s*=\s*\{", open(os.path.join(_vc, _sub, _f), encoding="utf-8-sig", errors="ignore").read()))
opn |= starcls | defs("system_tooltips") | defs("megastructures")
STRUCT = set("""id title desc option name trigger limit immediate text picture is_triggered_only hide_window which value namespace else else_if if
modifier days multiplier time_multiplier who target type status amount num_of_claims show_notification resource variable species owner size fraction
country cooldown authority civics class radius scaled_size skill design min max localization_key defined_text count weight ai_weight potential allow effect attacker_war_goal opinion decay base mult add_trait remove_trait flag side on_war_beginning events event on_monthly_pulse on_game_start parameters rounded setting color condition display_claims enable_terra_incognita icon can_change_point_of_view custom_tooltip dtp_rules_map_mode spawn_random_storm_weighted has_machine_age_dlc relations event_chain location poi situation_log_category surveyed surveyor dtp_marks_chain on_entering_system_fleet random_existing_design on_claim_system num_of_claims who target count Target Count
fail_text root prev from this AND OR NOT NOR NAND K CODE RES OP P ACT R remove_invalid_civics icon icon_frame message tech angle required_component section ship_design ship_size slot template entity portrait show_in_outliner place_entity_on_planet_plane orbit_distance planet possible""".split())
RESKEYS = {"energy", "minerals", "food", "alloys", "consumer_goods", "influence", "unity", "physics_research", "society_research", "engineering_research"}
for k in sorted(set(re.findall(r'(?<![:\w.$@])([a-z_][a-z0-9_]*)\s*(?:=|>|<)', code))):
    if k in STRUCT or k in RESKEYS or k in eff or k in trg or k in btn or k in smod or k in opn or k.startswith("dtp_"): continue
    if k in E or k in T or k in S: continue
    if any(re.search(r'^%s\s*=\s*\{' % k, strip(txt[f]), re.M) for f in txt if "static_modifiers" in f):
        if k not in M: errors.append("модификатора нет в 4.5: " + k)
        continue
    errors.append("неизвестная команда/триггер (нет в справочнике 4.5.1): " + k)
for f in txt:
    if "static_modifiers" in f:
        for k in re.findall(r'^[ \t]+(\w+)\s*=', strip(txt[f]), re.M):
            if k not in M and k not in ("icon", "icon_frame"): errors.append("модификатора нет в 4.5: " + k)
# вызовы своих эффектов/триггеров существуют
for u in set(re.findall(r'(?<![:\w])(dtp_\w+)\s*=\s*(?:yes|no|\{)', code)):
    if u in eff or u in trg or u in btn or u in smod or u in opn: continue
    if re.match(r'dtp_(res_op|act)_', u): continue
    if re.search(r'^%s\s*=\s*\{' % u, "".join(txt[f] for f in txt if "map_modes" in f or "event_chains" in f), re.M): continue   # объявление режима карты
    errors.append("не определено: " + u)
for op in ("add", "sub", "set"):
    if "dtp_res_op_" + op not in eff: errors.append("нет dtp_res_op_" + op)
acts = set(re.findall(r'ACT = (\w+)', code))
for a in acts:
    if "dtp_act_" + a not in eff: errors.append("нет действия dtp_act_" + a)
# глубина вложенности scripted effects (в 1.1 упёрлись в предел 5)
calls = collections.defaultdict(set)
for f in txt:
    if "scripted_effects" not in f: continue
    for m in re.finditer(r'^(\w+)\s*=\s*\{(.*?)^\}', strip(txt[f]), re.M | re.S):
        for c in re.findall(r'(?<![:\w])(dtp_\w+)\s*=\s*(?:yes|\{)', m.group(2)):
            if c in eff: calls[m.group(1)].add(c)
        for a in re.findall(r'dtp_act_\$ACT\$|dtp_res_op_\$OP\$', m.group(2)):
            calls[m.group(1)] |= {e for e in eff if e.startswith(a.split("$")[0])}
def depth(e, seen=()):
    if e in seen: errors.append("рекурсия: " + e); return 0
    return 1 + max([depth(c, seen + (e,)) for c in calls[e]] or [0])
maxd = max(depth(e) for e in eff)
if maxd > 4: errors.append("вложенность scripted effects %d (> 4)" % maxd)
# GUI: эффект кнопки существует, спрайт объявлен, текстура на месте, текст в локализации
VANILLA_SPR = set()
if len(sys.argv) > 3:                      # папка interface игры — для спрайтов игры (стиль «как в Stellaris»)
    for _p in glob.glob(os.path.join(sys.argv[3], "**", "*.gfx"), recursive=True):
        VANILLA_SPR |= set(re.findall(r'name\s*=\s*"(GFX_\w+)"', open(_p, encoding="utf-8-sig", errors="ignore").read()))
sprites = dict(re.findall(r'name\s*=\s*"(GFX_\w+)"\s*\n\s*texturefile\s*=\s*"([^"]+)"', "\n".join(gfx.values()), re.I))
loc = {}
for f in glob.glob(os.path.join(ROOT, "localisation/russian/*.yml")):
    for m in re.finditer(r'^\s+([\w.\-]+):0 "(.*)"\s*$', open(f, encoding="utf-8-sig").read(), re.M): loc[m.group(1)] = m.group(2)
for g in gui.values():
    part = g[g.find("DEBUG TOOLPACK"):]
    for m in re.finditer(r'name = "(dtp_b_\w+)".*?quadTextureSprite = "(\w+)".*?buttonText = "(\w+)".*?effect = "(\w+)"', part, re.S):
        n, spr, bt, ef = m.groups()
        if ef not in btn: errors.append("кнопка без эффекта: " + ef)
        if spr not in sprites and spr not in VANILLA_SPR: errors.append("спрайт не объявлен (ни в моде, ни в игре): " + spr)
        if bt not in loc: errors.append("нет текста кнопки: " + bt)
for n, f in sprites.items():
    if not os.path.exists(os.path.join(ROOT, f)): errors.append("нет текстуры " + f)
for p in set(re.findall(r'picture = (GFX_\w+)', code)):
    if p not in sprites: errors.append("картинка события не объявлена: " + p)
# локализация: ссылки и недопустимая одиночная [ (в 4.5 начинает команду)
for k, v in loc.items():
    for r in re.findall(r'\$(\w+)\$', v):
        if r not in loc: errors.append("нет $%s$ в %s" % (r, k))
    for br in re.findall(r'(?<!\[)\[([^\[\]]*)\]', v):
        if not re.match(r'^[\w.]+$', br): errors.append("подозрительные скобки [%s] в %s" % (br, k))
for k in set(re.findall(r'(?:title|desc|name|localization_key|fail_text)\s*=\s*(dtp[\w.]+)', code)):
    if k not in loc and k not in btn and k not in eff and k not in trg and k not in smod and k not in opn:
        if not k.startswith("dtp_custom_"): errors.append("нет ключа локализации " + k)
for sub in ("scripted_effects", "scripted_triggers"):
    d = os.path.join(ROOT, "common", sub)
    for f in os.listdir(d) if os.path.isdir(d) else []:
        if "[" in re.sub(r"#.*", "", open(os.path.join(d, f), encoding="utf-8-sig").read()):
            errors.append("[ в %s/%s: игра читает его как макрос (Invalid macro entry)" % (sub, f))
# двуязычность: одинаковые ключи в RU и EN, в EN нет кириллицы, ключи только ASCII, теги §/[ ] совпадают
LOCS = {}
for lang in ("russian", "english"):
    d = os.path.join(ROOT, "localisation", lang); LOCS[lang] = {}
    for f in os.listdir(d) if os.path.isdir(d) else []:
        LOCS[lang].update(dict(re.findall(r'^ (\S+):0 "(.*)"$', open(os.path.join(d, f), encoding="utf-8-sig").read(), re.M)))
ru_, en_ = LOCS["russian"], LOCS["english"]
for k in set(ru_) ^ set(en_): errors.append("ключ %s есть только в одном языке" % k)
for k, v in en_.items():
    if not k.isascii(): errors.append("не-ASCII ключ локализации " + k)
    if re.search(r"[А-Яа-яЁё]", v): errors.append("EN: русский текст в %s" % k)
    if k in ru_:
        for pat in (r"\[[^\]]*\]", r"\$\w+\$", r"§[A-Za-z!]"):
            if sorted(re.findall(pat, v)) != sorted(re.findall(pat, ru_[k])): errors.append("EN/RU: разные теги %s в %s" % (pat, k))
print("локализация: RU %d · EN %d" % (len(ru_), len(en_)))
# копия игровых дипломатических действий: только наши вставки (ключи подсказок есть, скобки сбалансированы)
_da = os.path.join(ROOT, "common", "diplomatic_actions", "zz_dtp_declare_war.txt")
if os.path.exists(os.path.join(ROOT, "common", "diplomatic_actions", "00_actions.txt")): errors.append("00_actions.txt в моде: не подменяйте весь игровой файл")
if os.path.exists(_da):
    _t = open(_da, encoding="utf-8-sig").read()
    if _t.count("{") != _t.count("}"): errors.append("zz_dtp_declare_war.txt: несбалансированные скобки")
    for k in re.findall(r"fail_text = (dtp_\w+)", _t):
        if k not in ru_ or k not in en_: errors.append("zz_dtp_declare_war.txt: нет локализации " + k)
    if not re.search(r"action_declare_war = \{.*?possible = \{\s*# --- Debug Toolpack", _t, re.S): errors.append("zz_dtp_declare_war.txt: проверки правил не стоят в action_declare_war")
print("эффектов %d · триггеров %d · кнопок %d · спрайтов %d · ключей %d · макс. вложенность %d" % (len(eff), len(trg), len(btn), len(sprites), len(loc), maxd))
for e in sorted(set(errors)): print("ОШИБКА:", e)
_gr = os.path.join(ROOT, "common", "game_rules", "00_rules.txt")
if os.path.exists(_gr):
    _t = re.sub(r"#[^\n]*", "", open(_gr, encoding="utf-8").read())
    if _t.count("{") != _t.count("}"): errors.append("00_rules.txt: несбалансированные скобки")
    if "fail_text = dtp_war_banned" not in _t: errors.append("00_rules.txt: нет запрета войн ведущего в can_declare_war")
    print("правила игры: копия игры + запрет войн ведущего в can_declare_war — проверено")

print("Итого ошибок:", len(set(errors)))
