# -*- coding: utf-8 -*-
"""Debug Toolpack 3.0 для Stellaris 4.5.x.

Что выяснено в игре (зонд DTP Probe, 21.10.2026):
  * кнопки на верхней/нижней панелях получают This = страна игрока, а не выделение;
  * текст из scripted loc (defined_text) в этих местах мигает — в 3.0 он не используется,
    состояние показывается видимостью надписей (potential), имена — через [X.GetName];
  * potential с from и нажатия (From = нажавший) работают надёжно.
Поэтому:
  * объект выбирается кнопками в ОКНЕ ПЛАНЕТЫ/ЗВЕЗДЫ и ОКНЕ ФЛОТА (там This = объект);
  * цели игрока хранятся в глобальных целях по номеру игрока (dtp_tc_K, dtp_tp_K, …);
  * отмеченные системы видны на галактической карте: класс звезды меняется на «отмеченную»
    копию (тот же свет, та же звезда, свойства — но значок с красным кольцом);
  * главное окно — dropDownBoxType (открывается значком, перетаскивается).

python3 gen3.py <мод> <vanilla interface> <vanilla common> <vanilla gfx/models/map>"""
import os, sys, re, json, glob

OUT, VI, VC, VMAP = sys.argv[1:5]
VERSION = "11.0.10"
UIOD = os.environ.get("DTP_LAYOUT") == "uiod"   # раскладка под UI Overhaul Dynamic (ставит make_uiod_patch.py)
MAXP = 16
L, BTN, GUI, META, EFF, TRG, EVENTS = {}, [], [], [], [], [], []

def loc(k, v): L[k] = v; return k
def B(head, *body): return head + " = {\n" + "\n".join(b for b in body if b) + "\n}"
def chk(var, val, op="="): return "check_variable = { which = %s value %s %s }" % (var, op, val)
def setv(var, val): return "set_variable = { which = %s value = %s }" % (var, val)
def pretty(text):
    out, depth = [], 0
    for raw in text.split("\n"):
        line = raw.strip()
        if not line: continue
        s = re.sub(r'"[^"]*"', '""', line)
        lead = len(s) - len(s.lstrip("}"))
        out.append("\t" * max(depth - lead, 0) + line)
        depth = max(depth + s.count("{") - s.count("}"), 0)
    return "\n".join(out) + "\n"
def chain(fn, kbody):
    """if/else_if по номеру игрока (from.dtp_pidx) — плоско, без вложенных scripted effects."""
    return "\n".join(B("if" if k == 1 else "else_if", B("limit", B("from", chk("dtp_pidx", k))), fn(k)) for k in range(1, MAXP + 1))
def orchain(fn):
    """OR по номеру игрока. Перед обращением к цели игрока проверяется, что она существует —
    иначе игра пишет в error.log ошибку на каждом кадре, пока окно открыто."""
    def guarded(k):
        body = fn(k)
        tg = sorted(set(re.findall(r"event_target:(dtp_[a-z]+_\d+)\b", body)))
        pre = "\n".join("exists = event_target:%s" % t for t in tg if "exists = event_target:%s" % t not in body)
        return (pre + "\n" + body) if pre else body
    return B("OR", *[B("AND", B("from", chk("dtp_pidx", k)), guarded(k)) for k in range(1, MAXP + 1)])

# ================================================================ ДАННЫЕ
PERMS = [("res", "Ресурсы и бонусы"), ("planet", "Планеты и системы"), ("state", "Государства"), ("species", "Расы"),
         ("diplo", "Дипломатия"), ("fleet", "Флоты"), ("event", "Ивенты"), ("force", "Принудительный режим"), ("gm", "Мастер игры")]
PSHORT = {"res": "Ресурсы", "planet": "Планеты", "state": "Государства", "species": "Расы", "diplo": "Дипломатия",
          "fleet": "Флоты", "event": "Ивенты", "force": "Принуд.", "gm": "Мастер"}
RES = [("energy", "Энергия", 1), ("minerals", "Минералы", 1), ("food", "Пища", 1), ("alloys", "Сплавы", 1),
       ("consumer_goods", "Товары", 1), ("influence", "Влияние", 1), ("unity", "Единство", 1),
       ("physics_research", "Физика", 0), ("society_research", "Социология", 0), ("engineering_research", "Инженерия", 0),
       ("exotic_gases", "Экзот. газы", 1), ("rare_crystals", "Кристаллы", 1), ("volatile_motes", "Летучая пыль", 1),
       ("sr_dark_matter", "Тёмная материя", 1), ("sr_living_metal", "Живой металл", 1), ("sr_zro", "Зро", 1),
       ("nanites", "Наниты", 1), ("minor_artifacts", "Артефакты", 1), ("astral_threads", "Астр. нити", 1)]
# Модификаторы «на единицу»: итог = значение × введённое число (поддерживаются отрицательные)
UMODS = {
    "c": [("research", "Скорость исследований", "all_technology_research_speed", 0.01, "%"),
          ("output", "Выработка работ", "planet_jobs_produces_mult", 0.01, "%"),
          ("stab", "Стабильность", "planet_stability_add", 1, "ед."),
          ("naval", "Флотский лимит", "country_naval_cap_add", 1, "ед."),
          ("fire", "Скорострельность флота", "ship_fire_rate_mult", 0.01, "%"),
          ("hull", "Корпус кораблей", "ship_hull_mult", 0.01, "%"),
          ("growth", "Рост населения", "logistic_growth_mult", 0.01, "%"),
          ("build", "Скорость стройки", "planet_building_build_speed_mult", 0.01, "%"),
          ("happy", "Одобрение", "pop_happiness", 0.01, "%"),
          ("amen", "Удобства", "planet_amenities_add", 1, "ед."),
          ("habit", "Пригодность", "pop_environment_tolerance", 0.01, "%"),
          ("storage", "Лимит складов", "country_resource_max_add", 1, "ед.")],
    "p": [("stab", "Стабильность", "planet_stability_add", 1, "ед."),
          ("habit", "Пригодность", "pop_environment_tolerance", 0.01, "%"),
          ("output", "Выработка работ", "planet_jobs_produces_mult", 0.01, "%"),
          ("amen", "Удобства", "planet_amenities_add", 1, "ед."),
          ("crime", "Преступность", "planet_crime_add", 1, "ед."),
          ("growth", "Рост населения", "logistic_growth_mult", 0.01, "%"),
          ("build", "Скорость стройки", "planet_building_build_speed_mult", 0.01, "%")],
    "f": [("fire", "Скорострельность", "ship_fire_rate_mult", 0.01, "%"),
          ("hull", "Корпус", "ship_hull_mult", 0.01, "%"),
          ("shield", "Щиты", "ship_shield_mult", 0.01, "%"),
          ("armor", "Броня", "ship_armor_mult", 0.01, "%"),
          ("speed", "Скорость", "ship_speed_mult", 0.01, "%"),
          ("evasion", "Уклонение", "ship_evasion_add", 1, "ед."),
          ("range", "Дальность оружия", "ship_weapon_range_mult", 0.01, "%")],
}
UCAT = {"c": ("dtp_t", "res", "державы"), "p": ("dtp_p", "planet", "планеты"), "f": ("dtp_f", "fleet", "флота")}
PC_NORMAL = [("pc_desert", "Пустынная"), ("pc_arid", "Засушливая"), ("pc_savannah", "Саванна"), ("pc_tropical", "Тропическая"),
             ("pc_continental", "Континент."), ("pc_ocean", "Океаническая"), ("pc_tundra", "Тундра"), ("pc_arctic", "Арктическая"),
             ("pc_alpine", "Альпийская"), ("pc_gaia", "Гайя")]
PC_SPECIAL = [("pc_nuked", "Гробница"), ("pc_city", "Экуменополис"), ("pc_hive", "Улей"), ("pc_machine", "Машинный"),
              ("pc_relic", "Реликвия"), ("pc_barren", "Бесплодная"), ("pc_barren_cold", "Хол. бесплодная"), ("pc_molten", "Расплавленная"),
              ("pc_frozen", "Замёрзшая"), ("pc_toxic", "Токсичная"), ("pc_gas_giant", "Газ. гигант")]
STARS = [("sc_b", "Голубая B"), ("sc_a", "Белая A"), ("sc_f", "Жёлто-белая F"), ("sc_g", "Жёлтая G"), ("sc_k", "Оранжевая K"),
         ("sc_m", "Красная M"), ("sc_m_giant", "Красный гигант"), ("sc_t", "Коричневый карлик"), ("sc_black_hole", "Чёрная дыра"),
         ("sc_neutron_star", "Нейтронная"), ("sc_pulsar", "Пульсар")]
ETHICS = [("militarist", "Милитаризм"), ("pacifist", "Пацифизм"), ("xenophobe", "Ксенофобия"), ("xenophile", "Ксенофилия"),
          ("authoritarian", "Авторитаризм"), ("egalitarian", "Эгалитаризм"), ("spiritualist", "Спиритуализм"), ("materialist", "Материализм")]
TRAITS = [("trait_intelligent", "Интеллектуальные"), ("trait_natural_engineers", "Инженеры"), ("trait_natural_physicists", "Физики"),
          ("trait_natural_sociologists", "Социологи"), ("trait_industrious", "Трудолюбивые"), ("trait_strong", "Сильные"),
          ("trait_rapid_breeders", "Быстрорастущие"), ("trait_thrifty", "Бережливые"), ("trait_adaptive", "Адаптивные"),
          ("trait_charismatic", "Харизматичные"), ("trait_talented", "Талантливые"), ("trait_venerable", "Долгоживущие")]
CITIZEN = [("citizenship_full", "Полное гражданство"), ("citizenship_slavery", "Рабство"), ("citizenship_purge", "Чистка")]
CODES = {1: "ресурсы добавлены", 2: "ресурсы вычтены", 3: "запас установлен", 5: "модификатор добавлен", 6: "модификатор снят",
         7: "системы переданы", 8: "планета передана", 9: "тип планеты изменён", 10: "залежи/препятствия изменены",
         11: "размер планеты изменён", 12: "население добавлено", 13: "событие вызвано", 14: "флот передан", 15: "флот удалён",
         16: "флоты отремонтированы", 17: "флот создан", 18: "флот перемещён", 19: "дипломатия изменена", 20: "этика изменена",
         21: "скопированы технологии/традиции/перки", 22: "признак вида изменён", 23: "права вида изменены", 24: "права игрока изменены",
         25: "статус ХОСТа изменён", 28: "откаты сняты", 29: "цель выбрана", 30: "принудительный режим переключён",
         31: "модификаторы Toolpack сняты", 32: "системы освобождены", 33: "колония уничтожена", 34: "заставы созданы",
         36: "отметки систем изменены", 57: "нарушение правил закрыто", 58: "правило войн изменено", 59: "сводка игроков обновлена", 60: "таймер сессии изменён", 61: "кризис: команда отправлена", 62: "сенат: команда выполнена", 56: "самопроверка пройдена — смотрите строку теста в журнале", 37: "класс звезды изменён", 38: "претензии выставлены",
         48: "монстры появились у выбранной планеты", 49: "карта и разведка обновлены", 50: "лидер создан", 51: "столица перенесена",
         52: "держава уничтожена", 53: "колония основана", 54: "станция системы изменена", 55: "галактика изменена",
         39: "правление изменено", 40: "гражданская модель изменена", 41: "указ включён", 42: "район изменён", 43: "здание изменено",
         44: "уровень жизни изменён", 45: "военная служба изменена", 46: "вид рабства изменён", 47: "вид чистки изменён"}
CATALOG = [(1, "Проверка связи", "Тестовое окно, ничего не меняет.", "country"),
           (2, "Дар Хранителей", "Выбор: энергия, сплавы или единство.", "country"),
           (3, "Волнения в столице", "Подавить (−стабильность) или откупиться.", "country"),
           (4, "Геологическое открытие", "Новая залежь на выбранной планете.", "planet"),
           (5, "Ремонтная бригада", "Полный ремонт выбранного флота.", "fleet"),
           (6, "Научный прорыв", "+2000 всех исследований.", "country"),
           (7, "Мирное предложение", "Держава решает, принять ли перемирие с вами.", "country"),
           (8, "Объявление администратора", "Уведомление всем игрокам.", "all")] + [(k, None, None, "custom") for k in range(9, 17)]
TABS = [(1, "Системы", "planet"), (2, "Держава", None), (3, "Ресурсы", "res"), (4, "Модификаторы", None), (5, "Планета", "planet"),
        (6, "Флот", "fleet"), (7, "Дипломатия", "diplo"), (8, "Государство", "state"), (9, "Расы", "species"), (10, "Ивенты", "event"),
        (11, "Доступ", None), (12, "Журнал", None), (13, "Правление", "state"), (14, "Постройки", "planet"), (15, "Главная", None), (16, "Мастер игры", "gm")]

# ================================================================ ОТМЕЧЕННЫЕ КЛАССЫ ЗВЁЗД
sc_src = open(os.path.join(VC, "star_classes/00_star_classes.txt"), encoding="utf-8-sig").read()
sc_nc = re.sub(r"#.*", "", sc_src)
STARCLS, MARKED_SC = [], []
star_tex_dir = os.path.join(VMAP, "star_classes")
for m in re.finditer(r"^(sc_\w+)\s*=\s*\{", sc_nc, re.M):
    i, d = m.end(), 1
    while d:
        d += {"{": 1, "}": -1}.get(sc_nc[i], 0); i += 1
    key, body = m.group(1), sc_nc[m.end():i - 1]
    cls = re.search(r"\bclass\s*=\s*(\w+)", body).group(1)
    ic = re.search(r"\bicon\s*=\s*(\w+)", body)
    icon = ic.group(1) if ic else (key if os.path.exists(os.path.join(star_tex_dir, key + ".dds")) else cls)
    if not os.path.exists(os.path.join(star_tex_dir, icon + ".dds")):
        continue                                 # значок не найден — систему можно отметить, но без кольца
    nb = re.sub(r"\bspawn_odds\s*=\s*[\d.]+", "spawn_odds = 0", body, count=1)
    nb = re.sub(r"\bicon\s*=\s*\w+", "", nb)
    isc = re.search(r"\bicon_scale\s*=\s*([\d.]+)", nb)
    nb = re.sub(r"\bicon_scale\s*=\s*[\d.]+", "", nb)
    nb = "\ticon_scale = %.2f\n" % (float(isc.group(1)) * 1.6 if isc else 1.6) + nb
    nb = nb.replace("{", "{", 1)
    MARKED_SC.append("dtp_mk_%s = {\n\ticon = dtp_mk_%s\n%s\n}" % (key, icon, nb.strip("\n")))
    # «режим отметки»: та же звезда с серым кольцом — так на большой карте видно все системы, которые можно отметить
    MARKED_SC.append("dtp_gy_%s = {\n\ticon = dtp_gy_%s\n%s\n}" % (key, icon, nb.strip("\n")))
    STARCLS.append((key, icon))
    loc("dtp_mk_" + key, "Отмечено в Toolpack")
    loc("dtp_mk_%s_desc" % key, "Система отмечена в Debug Toolpack. Снимите отметку, чтобы вернуть исходный класс звезды.")
    loc("dtp_gy_" + key, "Не отмечено (режим отметки)")
    loc("dtp_gy_%s_desc" % key, "Включён режим отметки Debug Toolpack: серое кольцо — систему можно отметить, красное — уже отмечена. Выключите режим во вкладке «Системы», чтобы вернуть обычные звёзды.")
# 10.7.6: исходный класс звезды запоминается ФЛАГОМ системы (dtp_oc_<класс>) и возвращается по нему.
# В 4.5.2 is_star_class не узнаёт классы-копии мода (dtp_gy_/dtp_mk_): серые кольца не снимались (game.log 22.10, «DTP GRAY off» без эффекта).
OCK = lambda k: "dtp_oc_" + k
REMEMBER = B("if", B("limit", "NOT = { has_star_flag = dtp_oc_known }"),
    *[B("if" if j == 0 else "else_if", B("limit", "is_star_class = %s" % k), "set_star_flag = dtp_oc_known", "set_star_flag = %s" % OCK(k)) for j, (k, ic) in enumerate(STARCLS)])
def BY_ORIG(fmt):
    return [B("if" if j == 0 else "else_if", B("limit", "has_star_flag = %s" % OCK(k)), fmt % k) for j, (k, ic) in enumerate(STARCLS)]
# 10.9.5: возврат звезды в ДВА шага — сначала другой класс игры, потом исходный. Похоже, игра считала систему всё ещё
# «исходного» класса (is_star_class не видит копии мода) и пропускала set_star_class как «без изменений» — круг оставался (22.10).
def RESTORE():
    return [B("if" if j == 0 else "else_if", B("limit", "has_star_flag = %s" % OCK(k)),
              "set_star_class = %s" % ("sc_m" if k != "sc_m" else "sc_k"), "set_star_class = %s" % k) for j, (k, ic) in enumerate(STARCLS)]
# 10.8.4: запасной способ узнать исходный класс — по звёздам системы (классы планет-звёзд). Нужен, когда флага dtp_oc_ нет:
# система покраснела в старой версии мода или флаг потерялся — раньше такие красные звёзды не снимались никогда.
def _sc_keys():
    out = {}
    for _f in sorted(os.listdir(os.path.join(VC, "star_classes"))):
        _p = os.path.join(VC, "star_classes", _f)
        if not os.path.isfile(_p): continue
        _s = re.sub(r"#.*", "", open(_p, encoding="utf-8-sig").read())
        for _m in re.finditer(r"(?m)^(\w+) = \{", _s):
            _i, _d = _m.end(), 1
            while _d: _d += {"{": 1, "}": -1}.get(_s[_i], 0); _i += 1
            out[_m.group(1)] = re.findall(r"\bkey = (\w+)", _s[_m.end():_i])
    return out
_SCK = _sc_keys()
_GUESS = sorted([(k, _SCK[k]) for k, ic in STARCLS if _SCK.get(k)], key=lambda t: (-len(t[1]), "crisis" in t[0], t[0]))
def GUESS(fmt):
    """Цепочка if/else_if: класс звезды по набору звёзд системы (сначала тройные, потом двойные, потом одиночные)."""
    out = []
    for j, (k, keys) in enumerate(_GUESS):
        conds = ["count_system_planet = { limit = { is_planet_class = %s } count >= %d }" % (pk, keys.count(pk)) for pk in sorted(set(keys))]
        out.append(B("if" if j == 0 else "else_if", B("limit", *conds), fmt % k))
    return out
ORIG_ANY = "OR = { %s }" % " ".join("is_star_class = %s" % k for k, ic in STARCLS)
EFF.append(B("dtp_remember_class", REMEMBER,
    B("if", B("limit", "NOT = { has_star_flag = dtp_oc_known }"), *GUESS("set_star_flag = dtp_oc_known set_star_flag = dtp_oc_%s"))))
# починка: звезда-копия мода (красная/серая), а система не отмечена — вернуть исходный класс
EFF.append(B("dtp_star_fix", B("if", B("limit", "NOT = { has_star_flag = dtp_marked }", "NOT = { %s }" % ORIG_ANY),
    "dtp_remember_class = yes", *RESTORE(), "remove_star_flag = dtp_gray", 'log = "DTP STARFIX restored"')))
# Навигатор (10.7.7): курсор = система; соседи по гиперлиниям — в dtp_nb_1..12. Работает для любых систем, и ничьих.
NB_N = 12
EFF.append(B("dtp_nav_set", "save_global_event_target_as = dtp_cur",
    *[B("if", B("limit", "exists = event_target:dtp_nb_%d" % k), "clear_global_event_target = dtp_nb_%d" % k) for k in range(1, NB_N + 1)],
    setv("dtp_nbn", 0),
    B("every_neighbor_system", B("prev", "change_variable = { which = dtp_nbn value = 1 }"),
      *[B("if", B("limit", B("prev", chk("dtp_nbn", k))), "save_global_event_target_as = dtp_nb_%d" % k) for k in range(1, NB_N + 1)])))
EFF.append(B("dtp_mark_sys", 'log = "DTP MARK start"',
    B("if", B("limit", "NOT = { has_star_flag = dtp_marked }"), "set_star_flag = dtp_marked", 'log = "DTP MARK flag set"',
      "dtp_flag_add = yes")))
# 10.9.8: КРАСНАЯ МЕТКА НАД СИСТЕМОЙ — своё мегасооружение мода с невидимой моделью: на большой карте над системой
# появляется значок с надписью «● ОТМЕЧЕНО». Снять — remove_megastructure (объект удаляется по-настоящему, значок пропадает).
# Перекраска звезды больше не используется: игра не перерисовывала звезду обратно до перезагрузки (22.10).
EFF.append(B("dtp_flag_add", B("if", B("limit", "NOT = { has_global_flag = dtp_starhide }", "exists = star",
      "NOT = { any_system_megastructure = { is_megastructure_type = dtp_mark_mega } }"),
    B("star", "save_global_event_target_as = dtp_mm_loc"),
    'spawn_megastructure = { type = dtp_mark_mega name = "dtp_mark_mega_name" planet = event_target:dtp_mm_loc orbit_distance = 0 }',
    'log = "DTP MARK: red marker placed"')))
EFF.append(B("dtp_flag_del", B("every_system_megastructure", B("limit", "is_megastructure_type = dtp_mark_mega"), "remove_megastructure = this")))
# 10.9.2: «маяк» — невидимый для других (маскировка 1000) корабль ХОСТа в каждой отмеченной системе: видит только ХОСТ.
EFF.append(B("dtp_beacon_add", B("if", B("limit", "exists = event_target:dtp_host", "NOT = { has_global_flag = dtp_nobeacon }",
      "NOT = { any_fleet_in_system = { has_fleet_flag = dtp_beacon } }"),
    "save_global_event_target_as = dtp_bc_sys", B("if", B("limit", "exists = star"), B("star", "save_global_event_target_as = dtp_bc_sys")),
    B("event_target:dtp_host", B("create_fleet", 'name = "dtp_beacon_fleet"', B("effect", "set_owner = event_target:dtp_host",
        B("create_ship", 'name = "dtp_beacon_ship"', 'design = "DTP_Marker"'),
        "set_location = { target = event_target:dtp_bc_sys distance = 6 angle = random }",
        "set_fleet_flag = dtp_beacon", "set_fleet_stance = passive", "set_cloaking_active = yes",
        B("every_owned_ship", "add_modifier = { modifier = dtp_beacon_ship days = -1 }")))))))
EFF.append(B("dtp_beacon_del", B("every_fleet_in_system", B("limit", "has_fleet_flag = dtp_beacon"), "delete_fleet = this")))
EFF.append(B("dtp_unmark_sys", 'log = "DTP UNMARK"', "dtp_beacon_del = yes", "dtp_flag_del = yes",
    B("if", B("limit", "has_star_flag = dtp_marked"), "remove_star_flag = dtp_marked",
      B("if", B("limit", "has_global_flag = dtp_graymode"), *BY_ORIG("set_star_class = dtp_gy_%s"), "set_star_flag = dtp_gray"),
      B("else", "dtp_remember_class = yes", *RESTORE(), B("else", 'log = "DTP UNMARK: original class unknown"'), "remove_star_flag = dtp_gray",
        B("if", B("limit", "NOT = { %s }" % ORIG_ANY), 'log = "DTP UNMARK: star still NOT original after set_star_class"'),
        B("else", 'log = "DTP UNMARK: star restored"')),
      B("if", B("limit", "has_star_flag = dtp_renamed"), "remove_star_flag = dtp_renamed",
        B("star", "save_event_target_as = dtp_star"), "set_name = event_target:dtp_star", 'log = "DTP UNMARK name restored"'))))
# имя отмеченной системы на карте: значок + имя её звезды (звезда носит исходное имя системы — им же имя и возвращается)
loc("dtp_mk_sysname", "»» [This.GetStarName] ««")
TRG.append(B("dtp_sys_marked", "has_star_flag = dtp_marked"))
EFF.append(B("dtp_gray_on", "set_global_flag = dtp_graymode", B("every_system", B("limit", "NOT = { has_star_flag = dtp_marked }"),
    "dtp_remember_class = yes", *BY_ORIG("set_star_class = dtp_gy_%s"), "set_star_flag = dtp_gray"), 'log = "DTP GRAY on"'))
EFF.append(B("dtp_gray_off", "remove_global_flag = dtp_graymode", B("every_system", B("limit", "has_star_flag = dtp_gray", "NOT = { has_star_flag = dtp_marked }"),
    *RESTORE(), "remove_star_flag = dtp_gray"), 'log = "DTP GRAY off"'))
# список отмеченных (глобальный, общий для администраторов) — 10 строк
# 10.7.8: внутри every_system — только prev (держава на шаг выше). Временные цели (save_event_target_as) там игра не видит:
# error.log 22.10 — «Undefined event target: dtp_me / dtp_poi_who / dtp_cm», 615 тыс. строк, счётчик отметок всегда 0.
def _mlist(name, sc):
  EFF.append(B(name, *[B("if", B("limit", "exists = event_target:dtp_ml_%d" % j), "clear_global_event_target = dtp_ml_%d" % j) for j in range(1, 11)],
    B(sc, setv("dtp_mcount", 0),
      B("every_system", B("limit", "has_star_flag = dtp_marked"),
        B("prev", "change_variable = { which = dtp_mcount value = 1 }"),
        *[B("if", B("limit", B("prev", chk("dtp_mcount", j))), "save_global_event_target_as = dtp_ml_%d" % j) for j in range(1, 11)])),
    "dtp_poi_sync_all = yes",
    'log = "DTP MLIST done"'))
_mlist("dtp_mlist", "from")
_mlist("dtp_mlist_root", "root")      # 10.8.5: из событий корабля-метки (root = держава-владелец)
# Метки «только для меня»: точки интереса (видит только их владелец) над отмеченными системами, до 30 штук.
POI_N = 30
EFF.append(B("dtp_poi_sync",
    *[B("if", B("limit", "has_point_of_interest = { poi = dtp_mk_poi.%d }" % k), "remove_point_of_interest = dtp_mk_poi.%d" % k) for k in range(1, POI_N + 1)],
    B("if", B("limit", "NOT = { has_country_flag = dtp_poi_off }", "dtp_has_any_perm = yes"),
      B("if", B("limit", "NOT = { has_event_chain = dtp_marks_chain }"), "begin_event_chain = { event_chain = dtp_marks_chain target = this }"),
      setv("dtp_poi_n", 0),
      B("every_system", B("limit", "has_star_flag = dtp_marked"),
        B("prev", "change_variable = { which = dtp_poi_n value = 1 }"),
        *[B("if", B("limit", B("prev", chk("dtp_poi_n", k))),
            B("prev", "create_point_of_interest = { id = dtp_mk_poi.%d name = dtp_mk_poi_name desc = dtp_mk_poi_desc event_chain = dtp_marks_chain location = prev }" % k))
          for k in range(1, POI_N + 1)]),
      'log = "DTP POI sync done"'),
    B("else", B("if", B("limit", "has_event_chain = dtp_marks_chain"), "end_event_chain = dtp_marks_chain"))))
LOCK_C = "NOT = { has_global_flag = dtp_war_soft } OR = { AND = { OR = { is_ai = no has_global_flag = dtp_war_ai } has_global_flag = dtp_rule_nopvp } has_country_flag = dtp_rule_np }"
SHLD_C = "NOT = { has_global_flag = dtp_war_soft } has_country_flag = dtp_rule_prot"
# 10.8.2: жёсткий режим запрета войн — видимые модификаторы державам (сам запрет — правило игры can_declare_war + действие «Объявить войну»)
EFF.append(B("dtp_war_sync", *[B("every_country", B("limit", "OR = { has_modifier = %s AND = { %s } }" % (m, c)),
    B("if", B("limit", c), B("if", B("limit", "NOT = { has_modifier = %s }" % m), "add_modifier = { modifier = %s days = -1 }" % m)),
    B("else", "remove_modifier = %s" % m)) for m, c in (("dtp_war_lock", LOCK_C), ("dtp_war_shield", SHLD_C))]))
def _all_techs():
    out, n = [], 0
    for _f in sorted(os.listdir(os.path.join(VC, "technology"))):
        _p = os.path.join(VC, "technology", _f)
        if not _f.endswith(".txt") or not os.path.isfile(_p): continue
        _s = re.sub(r"#[^\n]*", "", open(_p, encoding="utf-8-sig").read())
        for _m in re.finditer(r"(?m)^(tech_\w+)\s*=\s*\{", _s):
            _i, _d = _m.end(), 1
            while _d: _d += {"{": 1, "}": -1}.get(_s[_i], 0); _i += 1
            _b, k = _s[_m.end():_i - 1], _m.group(1)
            if re.search(r"\blevels\s*=\s*-1", _b) or "repeatable" in k or k.startswith("tech_fe_") or k == "tech_lgate_activation" or "$" in _b or "@" in _b.split("potential")[-1][:0]: continue
            pm = re.search(r"(?m)^\s*potential\s*=\s*\{", _b)
            pot = ""
            if pm:
                _j, _d = pm.end(), 1
                while _d: _d += {"{": 1, "}": -1}.get(_b[_j], 0); _j += 1
                pot = _b[pm.end():_j - 1].strip()
                if "@" in pot or "$" in pot or "always = no" in pot: continue
            out.append(B("if", B("limit", "NOT = { has_technology = %s }" % k, *( [pot] if pot else [] )), "give_technology = { tech = %s message = no }" % k)); n += 1
    return out, n
_AT, _ATN = _all_techs()
EFF.append(B("dtp_all_techs", *_AT, 'log = "DTP GM: all technologies (%d)"' % _ATN))
EFF.append(B("dtp_poi_sync_all", B("every_country", B("limit", "is_ai = no", "OR = { dtp_has_any_perm = yes has_event_chain = dtp_marks_chain }"), "dtp_poi_sync = yes")))
loc("dtp_mk_poi_name", "Отмечено (Debug Toolpack)")
loc("dtp_mk_poi_desc", "Система отмечена в Debug Toolpack. Эту метку видите только вы. Снять отметку — во вкладке «Системы».")
loc("dtp_marks_chain_title", "Отметки ведущего")
loc("dtp_marks_chain_desc", "Системы, отмеченные в Debug Toolpack (видны только вам). Метки обновляются при каждой отметке или снятии.")

# ================================================================ ТРИГГЕРЫ
TRG.append(B("dtp_has_perm", B("OR", "has_country_flag = dtp_host", B("AND", "is_ai = no", "has_country_flag = dtp_perm_$P$"))))
TRG.append(B("dtp_has_any_perm", B("OR", *["dtp_has_perm = { P = %s }" % p for p, _ in PERMS])))
TRG.append(B("dtp_is_host", "has_country_flag = dtp_host"))
TRG.append(B("dtp_force_active", "has_country_flag = dtp_force_mode", "dtp_has_perm = { P = force }"))
TRG.append(B("dtp_military_fleet", B("any_owned_ship", "is_ship_class = shipclass_military")))
for nm, par, tr in [("dtp_tc_has_auth", "A", "has_authority"), ("dtp_tc_has_civic", "C", "has_civic"), ("dtp_tc_has_edict", "E", "has_edict")]:
    TRG.append(B(nm, orchain(lambda k, tr=tr, par=par: B("event_target:dtp_tc_%d" % k, "%s = $%s$" % (tr, par)))))
TRG.append(B("dtp_cl_is", orchain(lambda k: "exists = event_target:dtp_$T$_%d\n" % k + B("event_target:dtp_cl_$J$", "is_same_value = event_target:dtp_$T$_%d" % k))))
TRG.append(B("dtp_tc_ai", orchain(lambda k: B("event_target:dtp_tc_%d" % k, "is_ai = yes"))))
TRG.append(B("dtp_target_country", B("OR", "dtp_listed_country = yes", "is_primitive = yes")))
TRG.append(B("dtp_listed_country", B("OR", "is_country_type = default", "is_country_type = fallen_empire", "is_country_type = awakened_fallen_empire", "is_country_type = dtp_gamemaster")))
for t in ("tc", "rcp", "tp", "tf"):
    TRG.append(B("dtp_has_%s" % t, orchain(lambda k, t=t: "exists = event_target:dtp_%s_%d" % (t, k))))
TRG.append(B("dtp_tr_differs", orchain(lambda k: B("event_target:dtp_tc_%d" % k, "NOT = { is_same_value = event_target:dtp_rcp_%d }" % k))))
for c, (obj, p, n) in UCAT.items():
    tgt = {"c": "tc", "p": "tp", "f": "tf"}[c]
    TRG.append(B("dtp_%s_hasmod" % c, orchain(lambda k, tgt=tgt: B("event_target:dtp_%s_%d" % (tgt, k), "has_modifier = $M$"))))
TRG.append(B("dtp_tp_star", orchain(lambda k: B("event_target:dtp_tp_%d" % k, "is_star = yes"))))
TRG.append(B("dtp_tp_colony", orchain(lambda k: B("event_target:dtp_tp_%d" % k, "is_colony = yes"))))
TRG.append(B("dtp_tp_marked", orchain(lambda k: B("event_target:dtp_tp_%d" % k, B("solar_system", "has_star_flag = dtp_marked")))))
TRG.append(B("dtp_sp_hastrait", orchain(lambda k: B("event_target:dtp_tc_%d" % k, B("owner_species", "has_trait = $T$")))))
TRG.append(B("dtp_tc_human", orchain(lambda k: B("event_target:dtp_tc_%d" % k, "is_ai = no"))))
TRG.append(B("dtp_tc_hasperm", orchain(lambda k: B("event_target:dtp_tc_%d" % k, "has_country_flag = dtp_perm_$P$"))))
TRG.append(B("dtp_tc_hasflag", orchain(lambda k: B("event_target:dtp_tc_%d" % k, "has_country_flag = $F$"))))

# ================================================================ ЭФФЕКТЫ
EFF.append(B("dtp_pidx_ensure", B("if", B("limit", "NOT = { is_variable_set = dtp_pidx }"),
    "set_country_flag = dtp_pidx_self", setv("dtp_pidx", 1),
    B("every_country", B("limit", "is_variable_set = dtp_pidx", "NOT = { has_country_flag = dtp_pidx_self }"),
      B("prev", "change_variable = { which = dtp_pidx value = 1 }")),
    "remove_country_flag = dtp_pidx_self",
    B("if", B("limit", chk("dtp_pidx", MAXP, ">")), setv("dtp_pidx", MAXP)),
    setv("dtp_amount", 1000), setv("dtp_val", 10), setv("dtp_years", 0), setv("dtp_res", 1), setv("dtp_tab", 15), setv("dtp_in", 0), setv("dtp_cpage", 0),
    setv("dtp_cn", 0), setv("dtp_coff", 0), setv("dtp_shn", 1), setv("dtp_shz", 0), setv("dtp_amt", 0), setv("dtp_stock", 0), *[setv("dtp_log%s_%d" % (n, k), 0) for n in ("code", "res") for k in range(1, 9)])))  # без пустых переменных — чище error.log
# назначение целей (вызывается в области объекта; номер игрока — из from)
for t in ("tc", "rcp", "tp", "tf"):
    EFF.append(B("dtp_set_%s" % t, chain(None, None) if False else "\n".join(
        B("if" if k == 1 else "else_if", B("limit", B("from", chk("dtp_pidx", k))), "save_global_event_target_as = dtp_%s_%d" % (t, k)) for k in range(1, MAXP + 1))))
EFF.append(B("dtp_init_targets", "\n".join(B("if" if k == 1 else "else_if", B("limit", chk("dtp_pidx", k)),
    B("if", B("limit", "NOT = { exists = event_target:dtp_tc_%d }" % k), "save_global_event_target_as = dtp_tc_%d" % k),
    B("if", B("limit", "NOT = { exists = event_target:dtp_rcp_%d }" % k), "save_global_event_target_as = dtp_rcp_%d" % k)) for k in range(1, MAXP + 1))))
# загрузка целей игрока в event targets текущего нажатия: dtp_t, dtp_r, dtp_p, dtp_f, dtp_s
EFF.append(B("dtp_load", "\n".join(B("if" if k == 1 else "else_if", B("limit", B("from", chk("dtp_pidx", k))),
    B("if", B("limit", "exists = event_target:dtp_tc_%d" % k), B("event_target:dtp_tc_%d" % k, "save_event_target_as = dtp_t")),
    B("if", B("limit", "exists = event_target:dtp_rcp_%d" % k), B("event_target:dtp_rcp_%d" % k, "save_event_target_as = dtp_r")),
    B("if", B("limit", "exists = event_target:dtp_tp_%d" % k), B("event_target:dtp_tp_%d" % k, "save_event_target_as = dtp_p", B("solar_system", "save_event_target_as = dtp_s"))),
    B("if", B("limit", "exists = event_target:dtp_tf_%d" % k), B("event_target:dtp_tf_%d" % k, "save_event_target_as = dtp_f"))) for k in range(1, MAXP + 1))))
# журнал (8 строк, актор = From, цель = dtp_t)
def log_effect():
    shift = []
    for k in range(7, 0, -1):
        shift.append(B("event_target:dtp_log%d_actor" % k, "save_global_event_target_as = dtp_log%d_actor" % (k + 1),
                       setv("dtp_logcode_%d" % (k + 1), "dtp_logcode_%d" % k), setv("dtp_logres_%d" % (k + 1), "dtp_logres_%d" % k)))
        shift.append(B("event_target:dtp_log%d_tgt" % k, "save_global_event_target_as = dtp_log%d_tgt" % (k + 1)))
    init = B("if", B("limit", "NOT = { exists = event_target:dtp_log8_actor }"), B("from", *["save_global_event_target_as = dtp_log%d_actor\nsave_global_event_target_as = dtp_log%d_tgt\n%s\n%s"
             % (k, k, setv("dtp_logcode_%d" % k, 0), setv("dtp_logres_%d" % k, 0)) for k in range(1, 9)]))
    return B("dtp_log", init, *shift,
             B("from", "save_global_event_target_as = dtp_log1_actor", setv("dtp_logcode_1", "$CODE$"), setv("dtp_logres_1", "$RES$"),
               setv("dtp_last_code", "$CODE$"), setv("dtp_last_ok", "$RES$")),
             B("if", B("limit", "exists = event_target:dtp_t"), B("event_target:dtp_t", "save_global_event_target_as = dtp_log1_tgt")),
             B("else", B("from", "save_global_event_target_as = dtp_log1_tgt")),
             'log = "DTP | code $CODE$ | result $RES$"')
EFF.append(log_effect())
EFF.append(B("dtp_result", B("hidden_effect", "dtp_log = { CODE = $CODE$ RES = 1 }")))
EFF.append(B("dtp_deny", B("hidden_effect", "dtp_log = { CODE = $CODE$ RES = 0 }")))
EFF.append(B("dtp_fail", B("hidden_effect", "dtp_log = { CODE = $CODE$ RES = 2 }")))
ARMS = ["cr_pre", "cr_unb", "cr_con", "cr_cet", "cr_khan", "gm_kill", "m_tr", "m_free", "pl_tr", "colony_rm", "fl_tr", "fl_del", "mass_fl", "subj", "fed", "war", "m_free2", "bd_clrb", "bd_clrd"]
EFF.append(B("dtp_auto_host", B("if", B("limit", "NOT = { has_global_flag = dtp_host_set }"),
    "remove_global_flag = dtp_auto_pick",
    B("every_country", B("limit", "is_ai = no", "is_country_type = default"),
      B("if", B("limit", "NOT = { has_global_flag = dtp_auto_pick }"), "set_global_flag = dtp_auto_pick", "dtp_make_host = yes",
        'log = "DTP HOST: auto -> first player country"')),
    "remove_global_flag = dtp_auto_pick",
    B("if", B("limit", "has_global_flag = dtp_host_set"), B("every_country", B("limit", "is_ai = no"), "country_event = { id = dtp.18 }")))))
EFF.append(B("dtp_disarm", B("from", *["remove_country_flag = dtp_arm_%s" % a for a in ARMS])))
# ресурсы
EFF.append(B("dtp_res_do", *[B("if" if i == 0 else "else_if", B("limit", B("from", chk("dtp_res", i + 1))), "dtp_res_op_$OP$ = { RES = %s }" % k)
                             for i, (k, n, s) in enumerate(RES)]))
cp = setv("dtp_amt", "from.dtp_amount")
EFF.append(B("dtp_res_op_add", B("event_target:dtp_t", cp, "add_resource = { $RES$ = 1 mult = dtp_amt }")))
EFF.append(B("dtp_res_op_sub", B("event_target:dtp_t", cp, "export_resource_stockpile_to_variable = { resource = $RES$ variable = dtp_stock }",
    B("if", B("limit", "check_variable = { which = dtp_amt value > dtp_stock }"), setv("dtp_amt", "dtp_stock")),
    "multiply_variable = { which = dtp_amt value = -1 }", "add_resource = { $RES$ = 1 mult = dtp_amt }")))
EFF.append(B("dtp_res_op_set", B("event_target:dtp_t", cp, "export_resource_stockpile_to_variable = { resource = $RES$ variable = dtp_stock }",
    "subtract_variable = { which = dtp_amt value = dtp_stock }", "add_resource = { $RES$ = 1 mult = dtp_amt }")))
# списки держав (страница по 10) — глобальные строки dtp_cl_1..10
EFF.append(B("dtp_clist", *["clear_global_event_target = dtp_cl_%d" % j for j in range(1, 11)],
    B("from", setv("dtp_cn", 0), setv("dtp_coff", "dtp_cpage"), "multiply_variable = { which = dtp_coff value = 10 }"),
    B("every_country", B("limit", "dtp_listed_country = yes"),
      B("from", "change_variable = { which = dtp_cn value = 1 }", setv("dtp_crel", "dtp_cn"), "subtract_variable = { which = dtp_crel value = dtp_coff }"),
      *[B("if", B("limit", B("from", chk("dtp_crel", j))), "save_global_event_target_as = dtp_cl_%d" % j) for j in range(1, 11)]),
    B("from", setv("dtp_cmore", "dtp_cn"), "subtract_variable = { which = dtp_cmore value = dtp_coff }", "subtract_variable = { which = dtp_cmore value = 10 }")))
# ХОСТ
# 11.0: РОЛЬ ГЕЙМ-МАСТЕРА. Держава ведущего получает свой тип dtp_gamemaster (копия обычного, но «неигровой», как у угасших империй):
# Галактическое сообщество её не учитывает (не запускает голосование о создании, не принимает в члены), рост населения выключен.
# Плюс закрытая этика «Гейм-мастер» (её нельзя выбрать при создании державы), огромные бонусы, разведка/шифровка 1000,
# полный обзор сенсорами (правило игры has_full_sensor_range), вся карта и контакт со всеми; войну, гарантии и закрытие границ — нельзя.
EFF.append(B("dtp_gm_on", B("if", B("limit", "NOT = { has_country_flag = dtp_gm_role }"),
    "set_country_flag = dtp_gm_role", "set_country_type = dtp_gamemaster",
    B("if", B("limit", "NOT = { has_ethic = ethic_gestalt_consciousness }"), "country_add_ethic = ethic_dtp_gamemaster"),
    "add_modifier = { modifier = dtp_gm_role days = -1 }",
    B("if", B("limit", "is_galactic_community_member = yes"), "remove_from_galactic_community = yes"),
    B("every_owned_planet", B("limit", "has_branch_office = yes"), "close_branch_office = yes"),
    B("every_system", B("prev", "set_visited = prev")),
    B("every_country", B("limit", "dtp_listed_country = yes", "NOT = { is_same_value = prev }"), "establish_communications_no_message = prev",
      "set_closed_borders = { who = prev status = no }", B("prev", "set_closed_borders = { who = prev status = no }")),
    'log = "DTP GM ROLE: on"')))
EFF.append(B("dtp_gm_off", B("if", B("limit", "has_country_flag = dtp_gm_role"),
    "remove_country_flag = dtp_gm_role", "set_country_type = default",
    B("if", B("limit", "has_ethic = ethic_dtp_gamemaster"), "country_remove_ethic = ethic_dtp_gamemaster"),
    "remove_modifier = dtp_gm_role", 'log = "DTP GM ROLE: off"')))
EFF.append(B("dtp_make_host", B("every_country", B("limit", "has_country_flag = dtp_host"), "remove_country_flag = dtp_host", "dtp_gm_off = yes"),
    "set_country_flag = dtp_host", "set_global_flag = dtp_host_set", "save_global_event_target_as = dtp_host",
    B("if", B("limit", "is_ai = no", "NOT = { has_country_flag = dtp_gm_role }"), "country_event = { id = dtp.19 }")))
# 11.0.7: окно «Роль Гейм-мастера» — только после ЯВНОГО действия игрока (кнопка «Стать ХОСТом», «Назначить», победа в голосовании,
# принятие передачи статуса), а не при автоматическом назначении на старте партии.
GM_OFFER = ""  # 11.0.10: предложение снова шлёт сам dtp_make_host
EFF.append(B("dtp_close_vote", "remove_global_flag = dtp_vote_open",
    B("every_country", B("limit", "has_country_flag = dtp_vote_pending"), "remove_country_flag = dtp_vote_pending")))
# пользовательский каталог событий
fire = []
for c, n, d, t in CATALOG:
    eff = {"country": "event_target:dtp_t = { country_event = { id = dtp.%d } }" % (1000 + c),
           "planet": "event_target:dtp_p = { planet_event = { id = dtp.%d } }" % (1000 + c),
           "fleet": "event_target:dtp_f = { fleet_event = { id = dtp.%d } }" % (1000 + c),
           "all": "every_country = { limit = { is_ai = no } country_event = { id = dtp.%d } }" % (1000 + c),
           "custom": "dtp_custom_fire_%d = yes" % c}[t]
    ok = {"country": "exists = event_target:dtp_t", "planet": "event_target:dtp_p = { exists = owner }", "fleet": "exists = event_target:dtp_f",
          "all": "always = yes", "custom": "dtp_custom_valid_%d = yes" % c}[t]
    fire.append(B("if", B("limit", B("from", chk("dtp_cat", c)), ok), eff, setv("dtp_fired", 1)))
EFF.append(B("dtp_fire_catalog", B("from", "save_global_event_target_as = dtp_last_actor"), setv("dtp_fired", 0), *fire,
             B("if", B("limit", chk("dtp_fired", 1)), "dtp_result = { CODE = 13 }"), B("else", "dtp_fail = { CODE = 13 }")))
for c, n, d, t in CATALOG:
    if n: loc("dtp_cat_%d_name" % c, n); loc("dtp_cat_%d_desc" % c, d)

# ================================================================ ОКНО И КНОПКИ
def need(key, text, trig):
    loc(key, text)
    return "custom_tooltip = { fail_text = %s %s }" % (key, trig)
def need_perm(p):
    return need("dtp_need_perm_%s" % p, "Нужно право «%s» — его выдаёт ХОСТ во вкладке «Доступ»" % dict(PERMS)[p], B("from", "dtp_has_perm = { P = %s }" % p))
N_TC = lambda: need("dtp_need_tc", "Выберите державу: вкладка «Держава» или кнопка в окне планеты/флота", "dtp_has_tc = yes")
N_RCP = lambda: need("dtp_need_rcp", "Выберите получателя: вкладка «Держава» → «Получатель» или кнопка в окне планеты/флота", "dtp_has_rcp = yes")
N_TP = lambda: need("dtp_need_tp", "Выберите планету: откройте окно планеты или звезды и нажмите «Выбрать»", "dtp_has_tp = yes")
N_TF = lambda: need("dtp_need_tf", "Выберите флот: откройте окно флота и нажмите «Выбрать флот»", "dtp_has_tf = yes")
N_FORCE = lambda: need("dtp_need_force", "Нужен принудительный режим (вкладка «Государство»)", B("from", "dtp_force_active = yes"))
N_DIFF = lambda: need("dtp_need_diff", "Держава и получатель совпадают", "dtp_tr_differs = yes")

OPEN = B("from", "has_country_flag = dtp_open")
GMPG_TT = {1: "Монстры, карта и разведка, лидеры, планета и система, судьбы держав, ситуации игры.",
           2: "Объявления всем игрокам, пакеты поддержки, мир между игроками, восстановление после сбоя.",
           3: "Запрет войн для игроков: на всю галактику или для одной державы, срок, нарушения и санкции.",
           4: "Сводка игроков, настройки партии, кризисы конца игры, таймер сессии.",
           5: "Сенат — Галактическое сообщество: заседание, текущая резолюция, Совет, Хранитель."}
PF_TT = {"pf_dep": "Добавить случайную залежь ресурса на выбранную планету.", "pf_reroll": "Перегенерировать залежи выбранной планеты.",
         "pf_clear": "Убрать все препятствия (блокираторы) на выбранной планете.", "pf_pmods": "Перегенерировать особенности выбранной планеты.",
         "pf_size_p": "Увеличить размер выбранной планеты на 1.", "pf_size_m": "Уменьшить размер выбранной планеты на 1.",
         "pf_pop": "Добавить население на выбранную колонию.", "pf_terra": "Мгновенно завершить идущее терраформирование выбранной планеты.",
         "fl_rep": "Полностью отремонтировать выбранный флот.", "fl_mrep": "Отремонтировать все флоты державы.",
         "mb_mrefresh": "Перечитать список отмеченных систем.", "cl_prev": "Предыдущая страница списка держав.", "cl_next": "Следующая страница списка держав.",
         "cl_me": "Сделать вашу империю и целью A, и получателем B.", "pl_sys": "Отметить на карте систему выбранной планеты.",
         "pl_sys_x": "Снять отметку с системы выбранной планеты.", "dp_contact": "Установить контакт между A и B.",
         "dp_op_p": "Мнение A о B +100 (затухает со временем).", "dp_op_m": "Мнение A о B −100 (затухает со временем).", "dp_op_0": "Сбросить отношения A и B.",
         "dp_trust": "Доверие A к B +25.", "dp_truce": "Перемирие между A и B, как после войны.", "dp_untruce": "Снять перемирие между A и B.",
         "dp_close": "A закрывает границы для B.", "dp_open": "A открывает границы для B.", "dp_guar": "A гарантирует независимость B.",
         "st_tech": "A получает все технологии, которые есть у B.", "st_trad": "A получает все традиции, которые есть у B.", "st_perk": "A получает перки возвышения, которые есть у B.",
         "st_pol": "Снять откаты смены политик у державы A.", "st_gov": "Снять откат смены правительства у державы A.",
         "st_force_off": "Принудительный режим выключен. Нажмите, чтобы включить: снимаются проверки игры — особые типы планет, класс звезды, этики, правление, война.",
         "hm_f_off": "Выключить принудительный режим — игра снова проверяет ограничения.", "bd_rep": "Починить все повреждённые здания выбранной планеты.",
         "hm_log": "Открыть журнал действий всех игроков.", "hm_sys": "Открыть раздел «Системы» со списком отмеченных систем.",
         "gm_l_xp": "Дать всем лидерам державы A по 1000 опыта.", "ac_solo": "Если вы единственный живой игрок — стать ХОСТом сразу, без голосования.",
         "ac_resign": "Отказаться от статуса ХОСТа: инструменты закроются для всех, пока не будет нового ХОСТа.",
         "um_pg1": "Модификаторы Toolpack: свои бонусы и штрафы с выбранным сроком.", "um_pg2": "Настоящие модификаторы игры: бонусы и штрафы для державы и планеты."}
def auto_tt(name, text):
    """Подсказка по умолчанию для кнопок без своей подсказки — чтобы ни одна кнопка не была «немой»."""
    t = re.sub(r"§.", "", text or "").strip()
    m = re.match(r"tab(\d+)(_on)?$", name)
    if m and int(m.group(1)) in TABD_FULL: return ("Открыт раздел «%s». %s" if m.group(2) else "Открыть раздел «%s». %s") % (t, TABD_FULL[int(m.group(1))])
    m = re.match(r"gm_pg(\d)(_on)?$", name)
    if m: return "Страница «%s»: %s" % (t, GMPG_TT[int(m.group(1))])
    if name in PF_TT: return PF_TT[name]
    if re.match(r"r\d+_on$", name): return "Выбран ресурс «%s» — кнопки ниже действуют на него." % t
    if re.match(r"r\d+$", name): return "Выбрать ресурс «%s»: кнопки ниже будут добавлять, вычитать или задавать именно его." % t
    if name.startswith("hm_rr_"): return "Повторить последнее действие с ресурсом для державы A с тем же числом, что в прошлый раз."
    if re.match(r"eth_5_", name): return "Добавить державе A этику «%s» (принудительный режим, игра может снять несовместимое)." % t[2:]
    if re.match(r"eth_7_", name): return "Добавить державе A фанатичную этику «%s» (принудительный режим)." % t[3:]
    if re.match(r"eth_9_", name): return "Убрать у державы A этику «%s» — обычную и фанатичную (принудительный режим)." % t[2:]
    if re.match(r"cl\d+_t(_on)?$", name): return "Эта держава — цель A." if name.endswith("_on") else "Сделать эту державу целью A: на неё будут действовать инструменты."
    if re.match(r"cl\d+_r(_on)?$", name): return "Эта держава — получатель B." if name.endswith("_on") else "Сделать эту державу получателем B: ей передаются планеты, флоты и системы."
    if re.match(r"ml\d+_x$", name): return "Снять отметку с этой системы."
    if name.endswith("_ok_x"): return "Отменить — ничего не менять."
    if name.endswith("_ok") or re.search(r"_ok$", name): return "Подтвердить и выполнить действие, указанное на кнопке. «Отмена» справа — ничего не менять."
    if re.match(r"um_pg\d_on$", name): return "Открыта эта страница модификаторов."
    if name.startswith("tr_trait_"): return "Добавить виду державы A признак «%s»." % t.lstrip("+ ")
    if name.startswith("cit_"): return "Установить основному виду державы A: «%s»." % t
    if name.startswith("sr_living_standard_"): return "Уровень жизни основного вида державы A: «%s»." % t
    if name.startswith("sr_military_service_"): return "Военная служба основного вида державы A: «%s»." % t
    if name.startswith("sr_slavery_"): return "Вид рабства для основного вида державы A: «%s»." % t
    if name.startswith("sr_purge_"): return "Вид чистки для основного вида державы A: «%s»." % t
    if name.startswith("au_auth_") and name.endswith("_on"): return "Это текущая форма правления державы A."
    if name.startswith("ed_") and name.endswith("_on"): return "Этот указ сейчас действует у державы A."
    if re.match(r"(kp|kq|gr_k|gr_q)\d$", name): return "Цифра %s. На клавиатуре: %s (ряд над буквами) или Alt+%s." % (t, t, t)
    return None
# Кнопки, которые действуют ТОЛЬКО на живых игроков (ИИ не трогают) — в подсказке отдельная строка об этом.
HUMANS_NOTE = {k: "dtp_note_humans" for k in ("ri_all", "res_all", "go_pack_all", "go_rep_all", "go_truce", "go_contact", "go_open", "go_relmax", "sb_refresh")}
HUMANS_NOTE.update({k: "dtp_note_pvp" for k in ("gr_onv", "gr_on0", "gr_off", "gr_p_np", "gr_p_prot", "gr_p_clr")})
def button(name, text, x, y, w, h=30, potential="", allow="", effect="", tt=None, sprite="GFX_dtp_btn", label=False, font="cg_16b", where="main", shortcut=None):
    key = "dtp_b_%s" % name
    if tt is None and not label: tt = auto_tt(name, text)
    if tt and name in HUMANS_NOTE: tt = tt + "\\n\\n$%s$" % HUMANS_NOTE[name]
    if where == "main":                      # всё окно видно только у игрока, открывшего его
        potential = OPEN + ("\n" + potential if potential else "")
    loc(key, text)
    tkey = loc(key + "_tt", tt) if tt else None
    # 10.7.6: у каждой кнопки своя подсказка (tt); автоматический разбор эффекта игрой показывал служебное
    # («Устанавливает переменную dtp_tab…») — эффект целиком скрыт от подсказки, работает так же.
    BTN.append(B(key, B("potential", potential or "always = yes"), B("allow", allow or "always = yes"), B("effect", B("hidden_effect", effect) if effect.strip() else effect)))
    GUI.append(dict(key=key, x=x, y=y, w=w, h=h, sprite=sprite, tt=tkey, label=label, font=font, where=where, shortcut=shortcut))
    META.append(dict(key=key, x=x, y=y, w=w, h=h, sprite=sprite, text=text, pot=potential or "", label=label, where=where, font=font))
    return key
def lab(name, text, x, y, w, potential="", h=24, where="main", font="cg_16b"):
    return button(name, text, x, y, w, h, potential=potential, sprite="GFX_dtp_label", label=True, where=where, font=font)

INIT = B("from", "dtp_pidx_ensure = yes", "dtp_init_targets = yes")
def act(p, body, code, need_load=True):
    """Тело действия: загрузка целей, проверка прав и наличия целей В МОМЕНТ выполнения, журнал.
    Если выбранная цель исчезла (планета уничтожена, флот погиб, держава пала) — «НЕ ВЫПОЛНЕНО», а не ложное «ГОТОВО»."""
    used = sorted(set(re.findall(r"event_target:(dtp_[ptrfs])\b", body))) if need_load else []
    # расчёты на переменных прячем от подсказки: игра просчитывает её при наведении мыши, когда переменные ещё не заданы
    # (error.log: «Variable … is not set»), и выводит служебные строки «Устанавливает переменную …»
    if re.search(r"\b(set_variable|change_variable|multiply_variable|divide_variable|export_trigger_value_to_variable|dtp_res_do|while)\b", body):
        body = B("hidden_effect", body)
    ok = B("if", B("limit", *["exists = event_target:%s" % u for u in used]), body, "dtp_result = { CODE = %d }" % code) + "\n" + \
         B("else", "dtp_fail = { CODE = %d }" % code) if used else body + "\ndtp_result = { CODE = %d }" % code
    return "\n".join([B("hidden_effect", INIT, "dtp_load = yes" if need_load else "", "dtp_disarm = yes"),
        B("if", B("limit", B("from", "dtp_has_perm = { P = %s }" % p)), ok),
        B("else", "dtp_deny = { CODE = %d }" % code)])

W, H = 1100, 720                # окно 8.0: навигация · раздел (цель сверху, инструменты, итог снизу) · параметры
NX, NW = 12, 196                # навигация
CX0, CWF = 222, 866             # рабочая область во всю ширину
CWN = 596                       # ширина, когда справа открыта панель параметров
PX, PW = 832, 256               # панель параметров (только в разделах с числами)
NUMTABS = (3, 4, 15)
CX, CY, CW, ROW = CX0, 176, CWF, 36
BAR_Y = H - 58                  # строка итога
def area(t):
    """Ширина рабочей области раздела: уже, если справа панель параметров."""
    global CX, CW
    CX, CW = CX0, (CWN if t in NUMTABS else CWF)
def grid(i, cols=3, gap=6, row0=0, w=None):
    w = w or (CW - gap * (cols - 1)) // cols
    return CX + (i % cols) * (w + gap), CY + (row0 + i // cols) * ROW, w
def T(t, extra=""):
    return B("from", chk("dtp_tab", t)) + ("\n" + extra if extra else "")
def per_k_label(name, fmt, x, y, w, pot_extra="", none_text=None, tgt=None, font="cg_16b", h=24):
    """Надпись с именем глобальной цели игрока: 16 вариантов, видим только свой."""
    for k in range(1, MAXP + 1):
        lab("%s_%d" % (name, k), fmt.replace("#", str(k)), x, y, w, font=font, h=h,
            potential=B("from", chk("dtp_pidx", k)) + ("\nexists = event_target:%s_%d" % (tgt, k) if tgt else "") + ("\n" + pot_extra if pot_extra else ""))
        if none_text and tgt:
            lab("%s_%d_x" % (name, k), none_text, x, y, w, font=font, h=h,
                potential=B("from", chk("dtp_pidx", k)) + "\nNOT = { exists = event_target:%s_%d }" % (tgt, k) + ("\n" + pot_extra if pot_extra else ""))
def TS(tabs, extra=""):
    """Видимость в нескольких разделах."""
    return B("from", B("OR", *[chk("dtp_tab", t) for t in tabs])) + ("\n" + extra if extra else "")

# ---------- шапка (координаты внутри перетаскиваемого окна)
button("bg", "", 0, 0, W, H, sprite="GFX_dtp_panel", label=True)
HW, HH = 210, 52                            # ручка перетаскивания со значком
# 10.8.2: значок и ручка Debug Toolpack видны только тем, у кого есть доступ (ХОСТ или права от ХОСТа),
# а пока живого ХОСТа нет — всем живым игрокам (чтобы кто-то мог им стать). Фон окна-ручки прозрачный,
# сама картинка ручки — кнопка-надпись с условием; под ней 10 px прозрачной полосы — за неё окно тоже тянется.
ACC = B("from", B("OR", "dtp_has_any_perm = yes", B("AND", "is_ai = no", "NOT = { any_country = { has_country_flag = dtp_host is_ai = no } }")))
HDRAG = 0
button("handle_img", "", 0, 0, HW, HH, where="handle", sprite="GFX_dtp_handle", label=True, potential=ACC)
button("toggle", "", HW - 50, 2, 48, 48, where="handle", sprite="GFX_dtp_toggle", potential=ACC,
       effect=INIT + "\n" + B("from", B("if", B("limit", "has_country_flag = dtp_open"), "remove_country_flag = dtp_open"),
                               B("else", "set_country_flag = dtp_open")),
       tt="Debug Toolpack: открыть или закрыть окно.")
# ---------- зонд режима наблюдателя: видна, только если кнопку смотрит не держава (обсервер)
OBS = "NOT = { from = { is_scope_type = country } }"
button("obs_probe", "§YOBSERVER§! · this: [This.GetName] · from: [From.GetName]", 0, 54, 300, 26, where="handle", sprite="GFX_dtp_btn_warn", potential=OBS,
       effect='log = "DTP OBSERVER click | this=[This.GetName] | from=[From.GetName]"',
       tt="Проверка режима наблюдателя для Debug Toolpack: нажмите и пришлите game.log (строка DTP OBSERVER).")
# ---------- точки на карте: проверка, какой объект игра даёт кнопкам в значках карты
# (в значке звезды — только империю игрока; проверяем остальные значки: станции, флоты, планеты, мегасооружения...)
MP_TT = "Точки на карте. Включите и посмотрите на галактическую карту: на значках станций, флотов, планет и т. п. появятся метки с названием. Клик по метке пытается отметить систему этого объекта."
# Проверено в 3.7 (game.log): во ВСЕХ значках карты (звезда, флоты, планеты...) игра даёт кнопке только империю игрока,
# а не объект. Поэтому кнопок в значках карты нет; список оставлен пустым для истории.
MAP_ICONS = []   # 4.5.2, game.log 22.10: «DTP MAPCLICK | this=from=root=держава игрока» — система кнопке недоступна
TOG = B("if", B("limit", "has_star_flag = dtp_marked"), "dtp_unmark_sys = yes") + "\n" + B("else", "dtp_mark_sys = yes")
# 10.7: значок системы на большой карте. Если игра даёт кнопке систему — серая/красная точка, клик ставит/снимает отметку.
# Если даёт только державу игрока (так было в 3.7) — жёлтый «?»: кнопка сама показывает, что клик по карте не работает.
MAPON = "has_global_flag = dtp_graymode"
MCLICK = "\n".join(['log = "DTP MAPCLICK | this=[This.GetName] | from=[From.GetName] | root=[Root.GetName]"',
    B("if", B("limit", "is_scope_type = galactic_object"), TOG, 'log = "DTP MAPCLICK -> system toggled"'),
    B("else", 'log = "DTP MAPCLICK -> not a system (engine gives country)"')])
if MAP_ICONS: button("mp_off", "", -112, 10, 22, 22, where="map:star_mapicon", sprite="GFX_dtp_dot_off", potential=MAPON + "\nis_scope_type = galactic_object\nNOT = { has_star_flag = dtp_marked }",
       effect=MCLICK, tt="Debug Toolpack: [This.GetName] — не отмечена. Клик — отметить.")
if MAP_ICONS: button("mp_on", "", -112, 10, 22, 22, where="map:star_mapicon", sprite="GFX_dtp_dot_on", potential=MAPON + "\nis_scope_type = galactic_object\nhas_star_flag = dtp_marked",
       effect=MCLICK, tt="Debug Toolpack: [This.GetName] — отмечена. Клик — снять отметку.")
if MAP_ICONS: button("mp_q", "§Y?§!", -112, 10, 22, 22, where="map:star_mapicon", sprite="GFX_dtp_field", potential=MAPON + "\nNOT = { is_scope_type = galactic_object }",
       effect=MCLICK, tt="Debug Toolpack: игра не передаёт этой кнопке систему, поэтому отмечать кликом по карте нельзя. Отмечайте через окно звезды или планеты (Alt+M). Пришлите автору game.log (строки DTP MAPCLICK).")

# ======================================================================= КОМПОЗИЦИЯ 8.0
# [заголовок окна                                                               ]
# [навигация] [НАЗВАНИЕ РАЗДЕЛА                                  ] [параметры: число,]
# [ разделы ] [карточка цели: имя крупно · владелец · «Сменить»   ] [ срок — только в  ]
# [ со      ] [группы инструментов: заголовок + крупные кнопки    ] [ Ресурсах, Модифи-]
# [ значками] [строка итога (ГОТОВО / ОТКАЗАНО / НЕ ВЫПОЛНЕНО)    ] [ каторах, Главной ]
button("nav_bg", "", 8, 52, NW + 8, H - 60, sprite="GFX_dtp_band", label=True)
CARD_SLOT = len(GUI)                                # сюда вставляются линии-разделители групп (под кнопками)
button("decor", "", W - 196, 6, 180, 90, sprite="GFX_dtp_decor", label=True)
button("logo", "", 16, 12, 30, 30, sprite="GFX_dtp_logo", label=True)
lab("title", "DEBUG TOOLPACK", 54, 12, 240, h=30, font="large_title_font")
lab("ver", "§g%s§!" % VERSION, 300, 18, 80)
lab("role_h", "§Y« ХОСТ »§!", 400, 18, 120, potential=B("from", "dtp_is_host = yes"))
lab("role_p", "§Gдоступ по правам ХОСТа§!", 400, 18, 220, potential=B("from", "NOT = { dtp_is_host = yes }\ndtp_has_any_perm = yes"))
lab("role_n", "§Rнет доступа — раздел «Доступ»§!", 400, 18, 280, potential=B("from", "NOT = { dtp_has_any_perm = yes }"))
lab("mode_f", "§R!! ПРИНУДИТЕЛЬНЫЙ РЕЖИМ !!§!", 660, 18, 240, potential=B("from", "dtp_force_active = yes"))

# ---------------- навигация
NAV = [("ГЛАВНОЕ", [15, 16]), ("ЦЕЛИ", [2, 1]), ("ЭКОНОМИКА", [3, 4]), ("МИРЫ", [5, 14, 6]), ("ДЕРЖАВА", [8, 13, 9, 7]), ("СЛУЖЕБНОЕ", [11, 12])]
TABD = {16: "для ведущего",
        15: "цель, разделы, быстрые действия",
        1: "отметки и действия над отмеченными",
        2: "A — над кем действуем, B — кому передаём",
        3: "склад державы A",
        4: "бонусы и штрафы",
        5: "тип, залежи, размер, передача",
        6: "ремонт, перенос, передача, создание",
        7: "отношения и договоры A и B",
        8: "этики, технологии, откаты",
        9: "признаки и права вида A",
        10: "события для цели или всех",
        11: "ХОСТ и права игроков",
        12: "последние действия",
        13: "правление, модели, указы",
        14: "районы и здания планеты"}
TN = {t: n for t, n, p in TABS}
TABD_FULL = {1: "Отметки систем на карте, список отмеченных, передача, освобождение и претензии.", 2: "Выбор державы A и получателя B для всех инструментов.",
             3: "Ресурсы державы A: добавить, вычесть, задать запас, доход каждый месяц на срок.", 4: "Бонусы и штрафы: свои модификаторы Toolpack и настоящие модификаторы игры.",
             5: "Выбранная планета: тип, размер, залежи, население, звезда, передача и колонии.", 6: "Выбранный флот: ремонт, перемещение, передача, удаление, новые флоты.",
             7: "Дипломатия между A и B: отношения, договоры, перемирие, война, вассалитет.", 8: "Этики, технологии, традиции, откаты и принудительный режим.",
             9: "Вид державы A: признаки и права.", 10: "Настоящие события игры и свои события для цели или для всех.",
             11: "ХОСТ, голосование за ХОСТа и права игроков.", 12: "Журнал действий всех игроков и самопроверки мода.",
             13: "Правление державы A: форма правления, цивики, политики, уровень жизни, рабство.", 14: "Районы и здания выбранной планеты.",
             15: "Быстрые действия, число, принудительный режим.", 16: "Инструменты ведущего: угрозы, объявления, правила партии, сводка, кризисы."}
y = 58
for _gi, (grp, ids) in enumerate(NAV):
    lab("nav_g%d" % _gi, "§g%s§!" % grp, NX + 10, y, 170, h=18)
    y += 19
    for t in ids:
        button("tab%d_on" % t, TN[t], NX, y, NW, 30, potential=B("from", chk("dtp_tab", t)), sprite="GFX_dtp_nav%d_on" % t)
        eff = INIT + "\n" + B("from", setv("dtp_tab", t)) + "\ndtp_disarm = yes" + ("\ndtp_mlist = yes" if t in (1, 15) else "") + ("\ndtp_clist = yes" if t == 2 else "")
        button("tab%d" % t, TN[t], NX, y, NW, 30, potential=B("from", "NOT = { %s }" % chk("dtp_tab", t)), effect=eff, sprite="GFX_dtp_nav%d" % t)
        y += 32
    y += 3

# ---------------- заголовок раздела
for t, d in TABD.items():
    cw = CWN if t in NUMTABS else CWF
    button("tta%d" % t, "", CX0, 58, 4, 30, sprite="GFX_dtp_accent", label=True, potential=T(t))
    lab("tt%d" % t, TN[t].upper(), CX0 + 14, 54, 240, potential=T(t), h=30, font="large_title_font")
    if t != 4:
        lab("ts%d" % t, "§g%s§!" % d, CX0 + 260, 60, cw - 260 - (506 if t == 16 else 0), potential=T(t), h=22)

# ---------------- карточка цели: кого изменят инструменты раздела
GOTO = lambda t: INIT + "\n" + B("from", setv("dtp_tab", t)) + "\ndtp_disarm = yes" + ("\ndtp_clist = yes" if t == 2 else "")
CARD_Y, CARD_H = 92, 70
def tcard(tabs, cw):
    button("tcard_%d" % cw, "", CX0, CARD_Y, cw, CARD_H, sprite="GFX_dtp_card", label=True, potential=TS(tabs))
A_TABS = [2, 3, 4, 8, 9, 11, 12, 13, 15, 16, 7]   # главная цель — держава A
B_TABS = [2, 7, 1, 5, 6, 16]                          # нужен ещё получатель B
P_TABS = [5, 14]; F_TABS = [6]; S_TABS = [1]
for cw in (CWF, CWN):
    tabs = [t for t in set(A_TABS + P_TABS + F_TABS + S_TABS) if (t in NUMTABS) == (cw == CWN)]
    if tabs: tcard(tabs, cw)
def a_block(tabs, x, w, suffix):
    button("ca_badge" + suffix, "", x + 12, CARD_Y + 22, 28, 28, sprite="GFX_dtp_badge_a", label=True, potential=TS(tabs))
    per_k_label("ca_name" + suffix, "§Y[dtp_tc_#.GetName]§!", x + 48, CARD_Y + 8, w - 220, pot_extra=TS(tabs), none_text="§gДержава не выбрана§!", tgt="dtp_tc", font="malgun_goth_24", h=32)
    lab("ca_role" + suffix, "§gдержава A — на неё подействуют инструменты§!", x + 48, CARD_Y + 42, w - 220, potential=TS(tabs), h=20)
    button("ca_me" + suffix, "Я", x + w - 166, CARD_Y + 20, 50, 32, potential=TS(tabs), sprite="GFX_dtp_btn_key",
           effect=INIT + "\n" + B("from", "dtp_set_tc = yes") + "\ndtp_result = { CODE = 29 }", tt="A = ваша империя")
    button("ca_chg" + suffix, "Сменить →", x + w - 110, CARD_Y + 20, 100, 32, potential=TS(tabs), sprite="GFX_dtp_btn_go",
           effect=GOTO(2), tt="Открыть список держав и выбрать A")
def b_block(tabs, x, w, suffix):
    button("cb_badge" + suffix, "", x + 12, CARD_Y + 22, 28, 28, sprite="GFX_dtp_badge_b", label=True, potential=TS(tabs))
    per_k_label("cb_name" + suffix, "§B[dtp_rcp_#.GetName]§!", x + 48, CARD_Y + 10, w - 170, pot_extra=TS(tabs), none_text="§gПолучатель не выбран§!", tgt="dtp_rcp")
    lab("cb_role" + suffix, "§gполучатель B — кому передаём§!", x + 48, CARD_Y + 38, w - 170, potential=TS(tabs), h=20)
    button("cb_chg" + suffix, "Сменить →", x + w - 110, CARD_Y + 20, 100, 32, potential=TS(tabs), effect=GOTO(2), tt="Открыть список держав и выбрать B")
# держава A: на всю карточку там, где B не нужен; в половину — где нужен
a_full = [t for t in A_TABS if t not in B_TABS]
for cw in (CWF, CWN):
    tabs = [t for t in a_full if (t in NUMTABS) == (cw == CWN)]
    if tabs: a_block(tabs, CX0, cw, "_f%d" % cw)
a_half = [t for t in A_TABS if t in B_TABS]                 # 2, 7, 16
a_block(a_half, CX0, CWF // 2, "_h")
b_block([2, 7, 1, 5, 6, 16], CX0 + CWF // 2, CWF // 2, "_h")
# планета
pt = P_TABS
button("cp_badge", "", CX0 + 12, CARD_Y + 21, 30, 30, sprite="GFX_dtp_ico5", label=True, potential=TS(pt))
per_k_label("cp_name", "§Y[dtp_tp_#.GetName]§!", CX0 + 50, CARD_Y + 8, 360, pot_extra=TS(pt), none_text="§gПланета не выбрана§!", tgt="dtp_tp", font="malgun_goth_24", h=32)
for k in range(1, MAXP + 1):                       # владелец есть не у каждой планеты — два варианта надписи
    base = B("from", chk("dtp_pidx", k)) + "\nexists = event_target:dtp_tp_%d\n" % k + TS(pt)
    lab("cp_sub_%d" % k, "§gсистема§! [dtp_tp_%d.System.GetName] §g· владелец§! [dtp_tp_%d.Owner.GetName]" % (k, k), CX0 + 50, CARD_Y + 42, 380,
        potential=base + "\n" + B("event_target:dtp_tp_%d" % k, "exists = owner"))
    lab("cp_sub_%d_n" % k, "§gсистема§! [dtp_tp_%d.System.GetName] §g· без владельца§!" % k, CX0 + 50, CARD_Y + 42, 380,
        potential=base + "\n" + B("event_target:dtp_tp_%d" % k, "NOT = { exists = owner }"))
    lab("cp_sub_%d_x" % k, "§gоткройте окно планеты или звезды → «Выбрать»§!", CX0 + 50, CARD_Y + 42, 380,
        potential=B("from", chk("dtp_pidx", k)) + "\nNOT = { exists = event_target:dtp_tp_%d }\n" % k + TS(pt))
# флот
button("cf_badge", "", CX0 + 12, CARD_Y + 21, 30, 30, sprite="GFX_dtp_ico6", label=True, potential=TS(F_TABS))
per_k_label("cf_name", "§Y[dtp_tf_#.GetName]§!", CX0 + 50, CARD_Y + 8, 360, pot_extra=TS(F_TABS), none_text="§gФлот не выбран§!", tgt="dtp_tf", font="malgun_goth_24", h=32)
per_k_label("cf_sub", "§gвладелец§! [dtp_tf_#.Owner.GetName]", CX0 + 50, CARD_Y + 42, 380, pot_extra=TS(F_TABS), none_text="§gоткройте окно флота → «Выбрать флот»§!", tgt="dtp_tf")
# системы
button("cs_badge", "", CX0 + 12, CARD_Y + 21, 30, 30, sprite="GFX_dtp_ico1", label=True, potential=TS(S_TABS))
lab("cs_name", "§YОтмечено систем: [From.dtp_mcount]§!", CX0 + 50, CARD_Y + 8, 380, potential=TS(S_TABS), h=32, font="malgun_goth_24")
lab("cs_sub", "§gотметить: окно планеты, звезды или станции → Alt+M§!", CX0 + 50, CARD_Y + 42, 380, potential=TS(S_TABS), h=20)
# планета в разделе «Постройки» на всю ширину; в «Планете» и «Флоте» справа — получатель B
# ---------------- панель параметров (Ресурсы, Модификаторы, Главная)
PP = TS(NUMTABS)
button("card_num", "", PX, 52, PW, 330, sprite="GFX_dtp_card", label=True, potential=PP)
lab("i_num", "§YЧИСЛО§!  §gколичество и значение§!", PX + 12, 60, PW - 24, h=22, potential=PP)
button("in", "  §Y[From.dtp_in]§!", PX + 10, 86, PW - 20, 40, sprite="GFX_dtp_field", label=True, font="malgun_goth_24", potential=PP,
       tt="Количество ресурса и значение модификатора. Печатайте цифры на клавиатуре (ряд над буквами): Backspace — стереть, Delete — очистить, «-» на NumPad — знак.")
SYNC = "\n".join([setv("dtp_val", "dtp_in"), setv("dtp_amount", "dtp_in"),
                  B("if", B("limit", chk("dtp_amount", 0, "<")), "multiply_variable = { which = dtp_amount value = -1 }")])
CAP = B("if", B("limit", chk("dtp_in", 999999999, ">")), setv("dtp_in", 999999999)) + "\n" + B("if", B("limit", chk("dtp_in", -999999999, "<")), setv("dtp_in", -999999999))
KW, KH = 74, 32
def kx(c): return PX + 12 + c * (KW + 6)
for i, d in enumerate([7, 8, 9, 4, 5, 6, 1, 2, 3, 0]):
    digit = "\n".join([B("if", B("limit", chk("dtp_in", 0, "<")), "multiply_variable = { which = dtp_in value = 10 }", "change_variable = { which = dtp_in value = %d }" % (-d)),
                       B("else", "multiply_variable = { which = dtp_in value = 10 }", "change_variable = { which = dtp_in value = %d }" % d)])
    c, r = (i % 3, i // 3) if d != 0 else (1, 3)
    KON = PP + "\n" + B("from", "NOT = { has_country_flag = dtp_kbd_off }")
    KOFF = PP + "\n" + B("from", "has_country_flag = dtp_kbd_off")
    # цифры ряда над буквами — только пока включён «ввод с клавиатуры» (иначе срабатывают и горячие клавиши игры)
    button("kp%d" % i, str(d), kx(c), 136 + r * 38, KW, KH, shortcut=str(d), effect=B("from", digit, CAP, SYNC), sprite="GFX_dtp_btn_key", potential=KON)
    button("kq%d" % i, str(d), kx(c), 136 + r * 38, KW, KH, effect=B("from", digit, CAP, SYNC), sprite="GFX_dtp_btn_key", potential=KOFF)
    # Alt+цифра работает всегда (у игры таких горячих клавиш нет) и пробные имена клавиш NumPad
    button("ka%d" % i, "", kx(c), 136 + r * 38, 1, 1, shortcut="alt+%d" % d, effect=B("from", digit, CAP, SYNC), sprite="GFX_dtp_label", label=True, potential=PP)
button("kp_neg", "±", kx(0), 136 + 3 * 38, KW, KH, shortcut="KP_MINUS", effect=B("from", "multiply_variable = { which = dtp_in value = -1 }", SYNC), sprite="GFX_dtp_btn_key", potential=PP, tt="Сменить знак")
button("kp_000", "000", kx(2), 136 + 3 * 38, KW, KH, effect=B("from", "multiply_variable = { which = dtp_in value = 1000 }", CAP, SYNC), sprite="GFX_dtp_btn_key", potential=PP, tt="Умножить на 1000")
button("kp_bs", "← Стереть", kx(0), 288, KW * 2 + 6, KH, shortcut="BACKSPACE", effect=B("from", "divide_variable = { which = dtp_in value = 10 }",
       B("if", B("limit", chk("dtp_in", 0, "<")), "ceiling_variable = dtp_in"), B("else", "floor_variable = dtp_in"), SYNC), sprite="GFX_dtp_btn_key", potential=PP, tt="Backspace")
button("kp_c", "C", kx(2), 288, KW, KH, shortcut="DEL", effect=B("from", setv("dtp_in", 0), SYNC), sprite="GFX_dtp_btn_danger", potential=PP, tt="Очистить (Delete)")
for i, (k, n, v) in enumerate([("q1k", "1к", 1000), ("q10k", "10к", 10000), ("q100k", "100к", 100000), ("q1m", "1 млн", 1000000)]):
    button("rq_" + k, n, PX + 12 + i * 58, 334, 54, 32, effect=B("from", setv("dtp_in", v), SYNC), potential=PP, tt="Число = %d" % v)
PY2 = PP + "\n" + T(4) if False else T(4)
button("card_yr", "", PX, 390, PW, 112, sprite="GFX_dtp_card", label=True, potential=PP)
lab("yr_l", "§YСРОК§!  §g[From.dtp_years] лет (0 = вечно)§!", PX + 12, 398, PW - 24, h=22, potential=PP)
for i, (k, n, v) in enumerate([("y0", "вечно", 0), ("y1", "1 год", 1), ("y5", "5 лет", 5), ("y10", "10 лет", 10)]):
    button("uy_" + k, n, PX + 12 + i * 58, 426, 54, 32, effect=B("from", setv("dtp_years", v)), potential=PP, tt="Срок модификаторов")
button("kp_yr", "Срок = число", PX + 12, 464, PW - 24, 30, effect=B("from", setv("dtp_years", "dtp_in"), B("if", B("limit", chk("dtp_years", 0, "<")), setv("dtp_years", 0))),
       sprite="GFX_dtp_btn_go", potential=PP, tt="Сделать число сроком модификаторов в годах.")
button("kbd_on", "Клавиатура: цифры ВКЛ", PX + 12, 512, PW - 24, 30, potential=PP + "\n" + B("from", "NOT = { has_country_flag = dtp_kbd_off }"),
       effect=B("from", "set_country_flag = dtp_kbd_off"), sprite="GFX_dtp_btn_on",
       tt="Цифры 0–9 над буквами набирают число. Игра при этом тоже видит нажатия (свои горячие клавиши она не отдаёт моду). Нажмите, чтобы выключить — тогда набирайте Alt+цифра или мышью.")
button("kbd_off", "Клавиатура: только Alt+цифра", PX + 12, 512, PW - 24, 30, potential=PP + "\n" + B("from", "has_country_flag = dtp_kbd_off"),
       effect=B("from", "remove_country_flag = dtp_kbd_off"), tt="Сейчас число набирается Alt+цифра (игра на это не реагирует). Нажмите, чтобы снова набирать просто цифрами.")
lab("p_hint", "§gAlt+цифра — без горячих клавиш игры§!", PX + 12, 548, PW - 24, potential=PP)

# ---------------- строка итога под рабочей областью
button("bar_idle", "   §gИтог последнего действия появится здесь§!", CX0, BAR_Y, CWF, 44, sprite="GFX_dtp_res_idle", label=True,
       potential=B("from", "NOT = { is_variable_set = dtp_last_ok }"))
button("bar_deny", "   §RОТКАЗАНО§!  ·  у вас нет права на это действие — его выдаёт ХОСТ в разделе «Доступ»", CX0, BAR_Y, CWF, 44, sprite="GFX_dtp_res_bad", label=True,
       potential=B("from", chk("dtp_last_ok", 0)))
button("bar_fail", "   §OНЕ ВЫПОЛНЕНО§!  ·  цель не выбрана или исчезла — выберите её в карточке сверху", CX0, BAR_Y, CWF, 44, sprite="GFX_dtp_res_warn", label=True,
       potential=B("from", chk("dtp_last_ok", 2)))
for c, t in CODES.items():
    button("bar_ok_%d" % c, "   §GГОТОВО§!  ·  " + t, CX0, BAR_Y, CWF, 44, sprite="GFX_dtp_res_ok", label=True,
           potential=B("from", chk("dtp_last_ok", 1), chk("dtp_last_code", c)))
for t, name, p in TABS:
    if p:
        cw = CWN if t in NUMTABS else CWF
        lab("noperm%d" % t, "§RНет права «%s».§! Его выдаёт ХОСТ в разделе «Доступ»." % dict(PERMS)[p], CX0, BAR_Y - 30, cw,
            potential=T(t, B("from", "NOT = { dtp_has_perm = { P = %s } }" % p)))

def armed(a): return B("from", "has_country_flag = dtp_arm_%s" % a)
ARMS_USED = set()
def arm_btn(name, text, x, y, w, pot, allow, a, tt, sprite="GFX_dtp_btn"):
    ARMS_USED.add(a)
    button(name, text, x, y, w, potential=pot + "\nNOT = { %s }" % armed(a), allow=allow, sprite=sprite,
           effect="dtp_disarm = yes\n" + B("from", "set_country_flag = dtp_arm_%s" % a), tt=tt + " Нужно подтверждение.")
def confirm(name, text, row, pot, allow, a, body, p, code):
    """Подтверждение опасного действия — на месте строки итога, во всю ширину."""
    button(name, "§YПОДТВЕРДИТЬ:§! " + text, CX0, BAR_Y, CWF - 186, 44, potential=pot + "\n" + armed(a), allow=allow, effect=act(p, body, code), sprite="GFX_dtp_btn_danger")
    button(name + "_x", "Отмена", CX0 + CWF - 180, BAR_Y, 180, 44, potential=pot + "\n" + armed(a), effect="dtp_disarm = yes")

# ---------- 1. Отмеченное
area(1)
x, y, w = grid(0, cols=1)
pass  # подсказка перенесена в карточку цели
LISTP = B("from", "NOT = { %s }" % chk("dtp_spage", 1))
NAVP = B("from", chk("dtp_spage", 1))
for j in range(1, 11):
    x, y, w = grid((j - 1) % 2, cols=2, row0=(j - 1) // 2)
    lab("ml%d_o" % j, "§R●§! §Y[dtp_ml_%d.GetName]§! §g· [dtp_ml_%d.Owner.GetName]§!" % (j, j), x + 4, y + 3, w - 100,
        potential=T(1, LISTP + "\nexists = event_target:dtp_ml_%d\nevent_target:dtp_ml_%d = { exists = owner }" % (j, j)))
    lab("ml%d_n" % j, "§R●§! §Y[dtp_ml_%d.GetName]§! §g· ничья§!" % j, x + 4, y + 3, w - 100,
        potential=T(1, LISTP + "\nexists = event_target:dtp_ml_%d\nevent_target:dtp_ml_%d = { NOT = { exists = owner } }" % (j, j)))
    button("ml%d_x" % j, "Снять", x + w - 92, y, 92, potential=T(1, LISTP + "\nexists = event_target:dtp_ml_%d" % j), allow=need_perm("planet"),
           effect=act("planet", B("event_target:dtp_ml_%d" % j, "dtp_unmark_sys = yes"), 36, False) + "\ndtp_mlist = yes")
x, y, w = grid(0, cols=1, row0=5)
lab("ml_more", "§g…и ещё системы — показаны первые 10§!", x, y, w - 300, potential=T(1, LISTP + "\n" + B("from", chk("dtp_mcount", 10, ">"))))
lab("ml_empty", "§gПока ничего не отмечено. Откройте окно планеты, звезды или станции и нажмите Alt+M — или включите навигатор (кнопка справа внизу).§!", x, CY, w, potential=T(1, LISTP + "\n" + B("from", chk("dtp_mcount", 0))))
NAVHOME = B("from", B("capital_star", B("solar_system", "dtp_nav_set = yes")))
button("nav_open", "Навигатор по карте →", x + w - 290, y, 290, potential=T(1, LISTP), sprite="GFX_dtp_btn_go",
       effect=B("from", setv("dtp_spage", 1)) + "\n" + B("if", B("limit", "NOT = { exists = event_target:dtp_cur }"), NAVHOME),
       tt="Навигатор: курсор на системе и кнопки всех соседних систем по гиперлиниям. Переходите от системы к системе и отмечайте любую — и ничью — прямо из окна.")
button("nav_close", "← Список отметок", x + w - 290, y, 290, potential=T(1, NAVP), effect=B("from", setv("dtp_spage", 0)) + "\ndtp_mlist = yes",
       tt="Вернуться к списку отмеченных систем.")
# --- навигатор
x, y, w = grid(0, cols=1, row0=0)
lab("nav_cur_o", "§YКУРСОР:§! §Y[dtp_cur.GetName]§! §g· [dtp_cur.Owner.GetName]§!", x + 4, y + 3, w - 200, potential=T(1, NAVP + "\nexists = event_target:dtp_cur\nevent_target:dtp_cur = { exists = owner }"))
lab("nav_cur_n", "§YКУРСОР:§! §Y[dtp_cur.GetName]§! §g· ничья§!", x + 4, y + 3, w - 200, potential=T(1, NAVP + "\nexists = event_target:dtp_cur\nevent_target:dtp_cur = { NOT = { exists = owner } }"))
NAVTOG = B("event_target:dtp_cur", B("if", B("limit", "has_star_flag = dtp_marked"), "dtp_unmark_sys = yes"), B("else", "dtp_mark_sys = yes"))
button("nav_tog", "§R●§! Отметить / снять", x + w - 190, y, 190, potential=T(1, NAVP + "\nexists = event_target:dtp_cur"),
       allow=need_perm("planet"), sprite="GFX_dtp_btn_warn", effect=act("planet", NAVTOG, 36, False) + "\ndtp_mlist = yes",
       tt="Отметить систему под курсором (и ничью), а если уже отмечена — снять отметку.")
x, y, w = grid(0, cols=1, row0=1)
lab("nav_h", "§gСоседние системы (клик — перейти курсором):§!", x + 4, y + 3, w - 200, potential=T(1, NAVP))
lab("nav_st1", "§R● СИСТЕМА ОТМЕЧЕНА§!", x + w - 200, y + 3, 200, potential=T(1, NAVP + "\nexists = event_target:dtp_cur\nevent_target:dtp_cur = { has_star_flag = dtp_marked }"))
lab("nav_st0", "§gне отмечена§!", x + w - 200, y + 3, 200, potential=T(1, NAVP + "\nexists = event_target:dtp_cur\nevent_target:dtp_cur = { NOT = { has_star_flag = dtp_marked } }"))
for k in range(1, NB_N + 1):
    x, y, w = grid((k - 1) % 4, cols=4, row0=2 + (k - 1) // 4)
    pe = NAVP + "\nexists = event_target:dtp_nb_%d" % k
    button("nav_nb%d" % k, "→ [dtp_nb_%d.GetName]" % k, x, y, w, potential=T(1, pe + "\nevent_target:dtp_nb_%d = { NOT = { has_star_flag = dtp_marked } }" % k),
           effect=B("event_target:dtp_nb_%d" % k, "dtp_nav_set = yes"), tt="Перевести курсор в эту систему.")
    button("nav_nm%d" % k, "§R●§! [dtp_nb_%d.GetName]" % k, x, y, w, potential=T(1, pe + "\nevent_target:dtp_nb_%d = { has_star_flag = dtp_marked }" % k),
           effect=B("event_target:dtp_nb_%d" % k, "dtp_nav_set = yes"), tt="Перевести курсор в эту систему (она уже отмечена).")
x, y, w = grid(0, cols=5, row0=5)
button("nav_home", "⌂ К моей столице", x, y, w, potential=T(1, NAVP), effect=NAVHOME, tt="Курсор — в систему вашей столицы.")
x, y, w = grid(1, cols=5, row0=5)
button("nav_tc", "К столице A", x, y, w, potential=T(1, NAVP), allow=N_TC(), effect="dtp_load = yes\n" + B("if", B("limit", "exists = event_target:dtp_t"), B("event_target:dtp_t", B("capital_star", B("solar_system", "dtp_nav_set = yes")))),
       tt="Курсор — в столичную систему державы A (выбранной цели).")
x, y, w = grid(2, cols=5, row0=5)
button("nav_p", "К системе планеты P", x, y, w, potential=T(1, NAVP), allow=N_TP(), effect="dtp_load = yes\n" + B("if", B("limit", "exists = event_target:dtp_p"), B("event_target:dtp_p", B("solar_system", "dtp_nav_set = yes"))),
       tt="Курсор — в систему выбранной планеты P (окно планеты → «Выбрать»).")
MK = "every_system = { limit = { has_star_flag = dtp_marked } %s }"
# как make_system_ownerless_effect игры 4.5: орбитальные станции разобрать, все станции в системе уничтожить
FREE = "\n".join(['log = "DTP FREE system"', "every_system_planet = { limit = { exists = orbital_station } orbital_station = { dismantle = yes } }",
                  "every_starbase_in_system = { ship = { destroy_fleet = this } }"])
bulk = [
    ("mrefresh", "Обновить список", "", 36, "", ""),
    ("mall_t", "Все системы A", B("event_target:dtp_t", B("every_system_within_border", "dtp_mark_sys = yes")), 36, N_TC(), "Отметить все системы выбранной державы."),
    ("mgrow", "Расширить на соседние", "\n".join(["every_system = { limit = { has_star_flag = dtp_marked } set_star_flag = dtp_grow }",
        "every_system = { limit = { has_star_flag = dtp_grow } every_neighbor_system = { dtp_mark_sys = yes } remove_star_flag = dtp_grow }"]), 36, "", "Отметить все системы, соседние с уже отмеченными (по гиперкоридорам)."),
    ("mclaim", "Претензии B", MK % "add_claims = { who = event_target:dtp_r num_of_claims = 1 show_notification = no }", 38, N_RCP(), "Получатель получает претензии на все отмеченные системы."),
    ("mop", "Заставы B", MK % "if = { limit = { NOT = { exists = starbase } } create_starbase = { owner = event_target:dtp_r size = starbase_outpost } }", 34, N_RCP(), "Построить заставы получателя во всех ничьих отмеченных системах."),
    ("mclear", "Снять все отметки", MK % "dtp_unmark_sys = yes" + "\ndtp_gray_off = yes\n" + B("every_system", "dtp_star_fix = yes"), 36, "", "Вернуть всем отмеченным системам исходный класс звезды. Заодно чинит «застрявшие» красные и серые звёзды по всей галактике."),
]
x, y, w = grid(0, cols=1, row0=6)
lab("mb_h", "§YСО ВСЕМИ ОТМЕЧЕННЫМИ§!", x, y, w, potential=T(1))
for i, (k, n, body, code, al, tt) in enumerate(bulk):
    x, y, w = grid(i, row0=7)
    button("mb_" + k, n, x, y, w, potential=T(1), allow=need_perm("planet") + ("\n" + al if al else ""),
           effect=(act("planet", body, code) if body else "") + "\ndtp_mlist = yes\n" + B("from", 'log = "DTP MLIST count=[This.dtp_mcount]"'), tt=tt or None, sprite="GFX_dtp_btn_danger" if k == "mclear" else "GFX_dtp_btn")
x, y, w = grid(0, row0=9)
arm_btn("m_tr", "Передать отмеченные → B", x, y, w, T(1), need_perm("planet") + "\n" + N_RCP(), "m_tr", "Передать получателю все отмеченные системы со станциями и планетами (до 100).")
x, y, w = grid(1, row0=9)
arm_btn("m_free", "Сделать ничьими", x, y, w, T(1), need_perm("planet"), "m_free", "Снести станции во всех отмеченных системах — они станут ничьими. Если в системе есть колония, игра оставит систему за владельцем колонии — для этого есть «Ничьи + снести колонии».")
MTR = "\n".join([setv("dtp_n", 0), B("every_system", B("limit", "has_star_flag = dtp_marked", chk("dtp_n", 100, "<")), "change_variable = { which = dtp_n value = 1 }"
    if False else "", "prev = { change_variable = { which = dtp_n value = 1 } }" if False else "",
    B("if", B("limit", "exists = starbase"), B("starbase", "set_owner = event_target:dtp_r")),
    B("else", "create_starbase = { owner = event_target:dtp_r size = starbase_outpost }"),
    B("every_system_planet", B("limit", "exists = owner"), "set_owner = event_target:dtp_r", B("if", B("limit", "is_colony = yes"), "set_controller = event_target:dtp_r")))])
MTR = "every_system = { limit = { has_star_flag = dtp_marked } %s }" % "\n".join([
    B("if", B("limit", "exists = starbase"), B("starbase", "set_owner = event_target:dtp_r")),
    B("else", "create_starbase = { owner = event_target:dtp_r size = starbase_outpost }"),
    B("every_system_planet", B("limit", "exists = owner"), "set_owner = event_target:dtp_r", B("if", B("limit", "is_colony = yes"), "set_controller = event_target:dtp_r"))])
confirm("m_tr_ok", "передать ВСЕ отмеченные системы получателю", 15, T(1), need_perm("planet") + "\n" + N_RCP(), "m_tr", MTR, "planet", 7)
confirm("m_free_ok", "снести станции во всех отмеченных системах", 15, T(1), need_perm("planet"), "m_free",
        MK % FREE, "planet", 32)
x, y, w = grid(1, cols=2, row0=10)
# 10.9.5: красные звёзды с кольцом вернулись (по умолчанию ВКЛ; их видят все игроки). Метки «только для меня» (точки интереса) работают фоном.
button("m_star_on", "Красные метки над системами: ВКЛ", x, y, w, potential=T(1, "NOT = { has_global_flag = dtp_starhide }"), allow=need_perm("planet"), sprite="GFX_dtp_btn_on",
       effect=act("planet", "set_global_flag = dtp_starhide\n" + MK % "dtp_flag_del = yes" + "\n" + B("every_system", "dtp_star_fix = yes"), 36, False) + "\ndtp_mlist = yes",
       tt="Сейчас над каждой отмеченной системой на большой карте — красная метка «● ОТМЕЧЕНО». Её видят ВСЕ игроки. Снял отметку — метка пропадает. Нажмите, чтобы убрать метки (отметки останутся в списке).")
button("m_star_off", "Красные метки над системами: ВЫКЛ", x, y, w, potential=T(1, "has_global_flag = dtp_starhide"), allow=need_perm("planet"),
       effect=act("planet", "remove_global_flag = dtp_starhide\n" + MK % "dtp_flag_add = yes", 36, False) + "\ndtp_mlist = yes",
       tt="Включить: над каждой отмеченной системой на большой карте появится красная метка «● ОТМЕЧЕНО» (видят все игроки).")
x, y, w = grid(0, cols=3, row0=11)
# 10.8.8: перекраска звёзд убрана — её видели все, а после снятия отметки красный круг на карте оставался до перезагрузки (22.10).
x, y, w = grid(1, cols=3, row0=11)
button("m_reveal", "Открыть мне всю карту", x, y, w, potential=T(1), allow=need_perm("planet"), sprite="GFX_dtp_btn_go",
       effect=act("planet", B("every_system", B("from", "set_visited = prev")), 36, False),
       tt="Все системы галактики становятся для вашей державы посещёнными: пропадает «неизведанное пространство», видны звёзды, гиперлинии и владельцы. Это игровое действие — только для вас.")
x, y, w = grid(2, cols=3, row0=11)
button("m_survey", "Изучить мне все планеты", x, y, w, potential=T(1), allow=need_perm("planet"),
       effect=act("planet", B("from", B("every_system", B("every_system_planet", "set_surveyed = { surveyed = yes surveyor = prevprev }"))), 36, False),
       tt="Все планеты галактики становятся исследованными для вашей державы (видны ресурсы и пригодность). Это игровое действие — только для вас.")
# 10.8.5: КОРАБЛЬ-МЕТКА ведущего. Невидимый для других (маскировка 1000), очень быстрый, с пси-прыжковым двигателем.
# Выделить корабль → ПКМ по любой системе (и ничьей) на большой карте → долетает почти сразу → через день после остановки
# система отмечается; привести снова в отмеченную — отметка снимется. События: on_entering_system_fleet → dtp.1280 → dtp.1281.
HASM = B("from", "any_owned_fleet = { has_fleet_flag = dtp_marker }")
MSPAWN = B("from", "save_event_target_as = dtp_mk_own", B("capital_scope", "save_event_target_as = dtp_mk_cap"),
    B("create_fleet", 'name = "dtp_marker_fleet"', B("effect", "set_owner = event_target:dtp_mk_own",
        B("create_ship", 'name = "dtp_marker_ship"', 'design = "DTP_Marker"', "graphical_culture = owner"),
        "set_location = { target = event_target:dtp_mk_cap distance = 20 angle = random }",
        "set_fleet_flag = dtp_marker", "set_fleet_stance = passive", "set_cloaking_active = yes",
        B("every_owned_ship", "add_modifier = { modifier = dtp_marker_ship days = -1 }"),
        "fleet_event = { id = dtp.1281 days = 1 }")),
    'log = "DTP MARKER: ship created"')
MKILL = B("from", B("every_owned_fleet", B("limit", "has_fleet_flag = dtp_marker"), "destroy_fleet = this"), 'log = "DTP MARKER: ship removed"')
x, y, w = grid(0, cols=2, row0=10)
UNMODE = B("from", "has_country_flag = dtp_mk_unmode")
button("mk_mode_m", "Корабль: §RОТМЕЧАЕТ§! системы", x, y, w, potential=T(1, HASM + "\nNOT = { %s }" % UNMODE), sprite="GFX_dtp_btn_warn",
       effect=B("from", "set_country_flag = dtp_mk_unmode"),
       tt="Сейчас корабль-метка ОТМЕЧАЕТ системы: залетел — система отмечена (уже отмеченные не трогает). Нажмите — режим СНИМАТЬ отметки.")
button("mk_mode_u", "Корабль: §GСНИМАЕТ§! отметки", x, y, w, potential=T(1, HASM + "\n" + UNMODE), sprite="GFX_dtp_btn_on",
       effect=B("from", "remove_country_flag = dtp_mk_unmode"),
       tt="Сейчас корабль-метка СНИМАЕТ отметки: залетел в отмеченную систему — отметка снята (неотмеченные не трогает). Нажмите — режим ОТМЕЧАТЬ.")
lab("mk_how0", "§gКорабль-метка — отмечать системы прямо на карте§!", x, y + 4, w, potential=T(1, "NOT = { %s }" % HASM))
x, y, w = grid(0, cols=3, row0=12)
button("mk_new", "Корабль-метка: создать", x, y, w, potential=T(1, "NOT = { %s }" % HASM), allow=need_perm("planet"), sprite="GFX_dtp_btn_go",
       effect=act("planet", MSPAWN, 36, False),
       tt="Создать у вашей столицы корабль-метку. Его видите только вы: маскировка 1000 — ни игроки, ни ИИ его не обнаружат. Скорость ×5000, прыжок без разгона и перезарядки, дальность прыжка ×1000. Как отмечать: выделите корабль, ПКМ по любой системе на большой карте (и ничьей) — отмечается каждая система, в которую корабль входит, — весь путь (лишнее снимается кнопкой «Снять все отметки» или режимом «СНИМАЕТ»). Режим «СНИМАЕТ» (кнопка слева сверху) — корабль, наоборот, убирает отметки.")
button("mk_del", "Корабль-метка: убрать", x, y, w, potential=T(1, HASM), allow=need_perm("planet"), sprite="GFX_dtp_btn_danger",
       effect=act("planet", MKILL, 36, False), tt="Убрать корабль-метку. Отметки систем останутся.")
x, y, w = grid(1, cols=3, row0=12)
button("mk_cur", "Корабль → к курсору навигатора", x, y, w, potential=T(1, HASM), allow=need_perm("planet") + "\n" + need("dtp_need_cur", "Сначала выберите систему в навигаторе", "exists = event_target:dtp_cur"),
       effect=act("planet", B("from", B("every_owned_fleet", B("limit", "has_fleet_flag = dtp_marker"), "set_timed_fleet_flag = { flag = dtp_mk_tp days = 1 }", "set_location = { target = event_target:dtp_cur distance = 25 angle = random }")), 36, False),
       tt="Мгновенно перенести корабль-метку в систему под курсором навигатора (без отметки).")
x, y, w = grid(2, cols=3, row0=12)
button("mk_home", "Корабль → к моей столице", x, y, w, potential=T(1, HASM), allow=need_perm("planet"),
       effect=act("planet", B("from", B("capital_scope", "save_event_target_as = dtp_mk_cap"),
                  B("every_owned_fleet", B("limit", "has_fleet_flag = dtp_marker"), "set_timed_fleet_flag = { flag = dtp_mk_tp days = 1 }", "set_location = { target = event_target:dtp_mk_cap distance = 20 angle = random }")), 36, False),
       tt="Мгновенно вернуть корабль-метку к вашей столице (без отметки).")
x, y, w = grid(2, row0=9)
arm_btn("m_free2", "Ничьи + снести колонии", x, y, w, T(1), need_perm("planet") + "\n" + N_FORCE(), "m_free2",
        "Уничтожить колонии в отмеченных системах и снести станции: системы станут полностью ничьими (принудительный режим).")
confirm("m_free2_ok", "УНИЧТОЖИТЬ колонии и станции в отмеченных системах", 15, T(1), need_perm("planet") + "\n" + N_FORCE(), "m_free2",
        MK % ("every_system_planet = { limit = { is_colony = yes } destroy_colony = yes }\n" + FREE), "planet", 32)

# ---------- 2. Держава (список)
area(2)
x, y, w = grid(0, cols=1)
pass  # подсказка перенесена в карточку цели
for j in range(1, 11):
    x, y, w = grid(0, cols=1, row0=j - 1)
    pe = T(2, "exists = event_target:dtp_cl_%d" % j)
    lab("cl%d" % j, "[dtp_cl_%d.GetName]" % j, x, y, w - 250, potential=pe + "\nevent_target:dtp_cl_%d = { is_ai = yes }" % j)
    lab("cl%d_h" % j, "[dtp_cl_%d.GetName] §G(игрок)§!" % j, x, y, w - 250, potential=pe + "\nevent_target:dtp_cl_%d = { is_ai = no NOT = { has_country_flag = dtp_host } }" % j)
    lab("cl%d_x" % j, "[dtp_cl_%d.GetName] §Y— ХОСТ§!" % j, x, y, w - 250, potential=pe + "\nevent_target:dtp_cl_%d = { has_country_flag = dtp_host }" % j)
    isA = "dtp_cl_is = { J = %d T = tc }" % j
    isB = "dtp_cl_is = { J = %d T = rcp }" % j
    button("cl%d_t_on" % j, "§Yэто A§!", x + w - 244, y, 120, potential=pe + "\n" + isA, sprite="GFX_dtp_btn_on")
    button("cl%d_r_on" % j, "§Bэто B§!", x + w - 118, y, 118, potential=pe + "\n" + isB, sprite="GFX_dtp_btn_on")
    pa, pb = pe + "\nNOT = { %s }" % isA, pe + "\nNOT = { %s }" % isB
    button("cl%d_t" % j, "Сделать A", x + w - 244, y, 120, potential=pa, effect=B("event_target:dtp_cl_%d" % j, "dtp_set_tc = yes") + "\ndtp_result = { CODE = 29 }")
    button("cl%d_r" % j, "Сделать B", x + w - 118, y, 118, potential=pb, effect=B("event_target:dtp_cl_%d" % j, "dtp_set_rcp = yes") + "\ndtp_result = { CODE = 29 }")
x, y, w = grid(0, row0=11)
button("cl_prev", "‹ Назад", x, y, w, potential=T(2, B("from", chk("dtp_cpage", 0, ">"))), effect=B("from", "change_variable = { which = dtp_cpage value = -1 }") + "\ndtp_clist = yes")
x, y, w = grid(1, row0=11)
button("cl_me", "A и B = моя империя", x, y, w, potential=T(2), effect=B("from", "dtp_set_tc = yes", "dtp_set_rcp = yes") + "\ndtp_result = { CODE = 29 }")
x, y, w = grid(2, row0=11)
button("cl_next", "Вперёд ›", x, y, w, potential=T(2, B("from", chk("dtp_cmore", 0, ">"))), effect=B("from", "change_variable = { which = dtp_cpage value = 1 }") + "\ndtp_clist = yes")

# ---------- 3. Ресурсы
area(3)
x, y, w = grid(0, cols=1)
lab("r_h0", "§YРЕСУРС§!  §gвыбранный подсвечен§!", x, y, w, potential=T(3))
for i, (k, n, s) in enumerate(RES):
    x, y, w = grid(i, cols=4, row0=1)
    button("r%d_on" % (i + 1), n, x, y, w, potential=T(3, B("from", chk("dtp_res", i + 1))), sprite="GFX_dtp_btn_on")
    button("r%d" % (i + 1), n, x, y, w, potential=T(3, B("from", "NOT = { %s }" % chk("dtp_res", i + 1))), effect=B("from", setv("dtp_res", i + 1)))
x, y, w = grid(0, cols=1, row0=6)
lab("r_hint", "§YДЕЙСТВИЕ§!  §gколичество §Y[From.dtp_amount]§! — из панели «Число» справа§!", x, y, w, potential=T(3))
stockable = B("from", "OR = { %s }" % " ".join(chk("dtp_res", i + 1) for i, (k, n, s) in enumerate(RES) if s))
for i, (k, n, e, code, ex, tt) in enumerate([
        ("add", "+ Добавить [From.dtp_amount]", "dtp_res_do = { OP = add }", 1, "", "Добавить выбранной державе."),
        ("sub", "− Вычесть [From.dtp_amount]", "dtp_res_do = { OP = sub }", 2, stockable, "Вычесть, но не больше, чем на складе."),
        ("set", "= Сделать ровно [From.dtp_amount]", "dtp_res_do = { OP = set }", 3, stockable, "Сделать запас ровно равным числу (в пределах лимита).")]):
    x, y, w = grid(i, row0=7)
    al = "\n".join([need_perm("res"), N_TC()] + ([need("dtp_need_stock", "У исследований нет склада", ex)] if ex else []))
    button("res_" + k, n, x, y, w, potential=T(3), allow=al, tt=tt, sprite="GFX_dtp_btn_go",
           effect=B("from", setv("dtp_lastop", i + 1), setv("dtp_lastres", "dtp_res"), setv("dtp_lastamt", "dtp_amount")) + "\n" + act("res", e, code))
x, y, w = grid(1, row0=8)
for oi, (op, sign) in enumerate([("add", "+"), ("sub", "−"), ("set", "=")]):
    for ri, (rk, rn, rs) in enumerate(RES):
        button("rr_%s_%d" % (op, ri + 1), "↻ Повторить: %s [From.dtp_lastamt] %s" % (sign, rn), x, y, 2 * w + 6,
               potential=T(3, B("from", chk("dtp_lastop", oi + 1), chk("dtp_lastres", ri + 1))), allow=need_perm("res") + "\n" + N_TC(),
               effect=B("from", setv("dtp_res", ri + 1), setv("dtp_amount", "dtp_lastamt")) + "\n" + act("res", "dtp_res_do = { OP = %s }" % op, oi + 1),
               tt="Повторить последнее действие с ресурсом для державы A.")
for oi, (op, inv) in enumerate([("add", "sub"), ("sub", "add")]):
    for ri, (rk, rn, rs) in enumerate(RES):
        x2, y2, w2 = grid(2, row0=9)
        button("ru_%s_%d" % (op, ri + 1), "↶ Отменить: %s" % rn, x2, y2, w2, potential=T(3, B("from", chk("dtp_lastop", oi + 1), chk("dtp_lastres", ri + 1))),
               allow=need_perm("res") + "\n" + N_TC(), sprite="GFX_dtp_btn_warn",
               effect=B("from", setv("dtp_res", ri + 1), setv("dtp_amount", "dtp_lastamt"), "remove_variable = dtp_lastop" if False else setv("dtp_lastop", 9)) + "\n" + act("res", "dtp_res_do = { OP = %s }" % inv, 2 if op == "add" else 1),
               tt="Вернуть склад: обратное действие на [From.dtp_lastamt] (%s). Отменить можно один раз." % rn)
# ---- доход в месяц на срок: модификатор «+N ресурса в месяц», срок — из панели «Срок»
INC_STATIC = []
x, y, w = grid(0, cols=1, row0=10)
lab("ri_h", "§YДОХОД В МЕСЯЦ§!  §gвыбранный ресурс, §Y[From.dtp_amount]§! в месяц, срок §Y[From.dtp_years]§! лет (0 — навсегда)§!", x, y, w, potential=T(3))
for ri, (rk, rn, rs) in enumerate(RES):
    INC_STATIC.append("dtp_inc_%s = {\n\tcountry_base_%s_produces_add = 1\n}" % (rk, rk))
    loc("dtp_inc_%s" % rk, "Toolpack: доход — %s" % rn); loc("dtp_inc_%s_desc" % rk, "Ежемесячный доход, выданный через Debug Toolpack.")
INC_CHAIN = lambda sign: "\n".join(B("if" if i == 0 else "else_if", B("limit", B("from", chk("dtp_res", i + 1))),
    B("event_target:dtp_t", "remove_modifier = dtp_inc_%s" % rk, setv("dtp_amt", "from.dtp_amount"), setv("dtp_ty", "from.dtp_years"),
      "multiply_variable = { which = dtp_amt value = %d }" % sign,
      B("if", B("limit", chk("dtp_ty", 0, "<=")), "add_modifier = { modifier = dtp_inc_%s days = -1 multiplier = dtp_amt }" % rk),
      B("else", "add_modifier = { modifier = dtp_inc_%s days = 360 time_multiplier = dtp_ty multiplier = dtp_amt }" % rk)))
    for i, (rk, rn, rs) in enumerate(RES))
INC_DEL = "\n".join(B("if" if i == 0 else "else_if", B("limit", B("from", chk("dtp_res", i + 1))), B("event_target:dtp_t", "remove_modifier = dtp_inc_%s" % rk))
    for i, (rk, rn, rs) in enumerate(RES))
for i, (k, n, eff, code, spr, tt) in enumerate([
        ("p", "+ [From.dtp_amount] в месяц", INC_CHAIN(1), 5, "GFX_dtp_btn_go", "Держава A каждый месяц получает выбранный ресурс в количестве «Числа», пока не кончится срок. Повторное нажатие заменяет прежний доход по этому ресурсу."),
        ("m", "− [From.dtp_amount] в месяц", INC_CHAIN(-1), 5, "GFX_dtp_btn_danger", "Штраф: держава A каждый месяц теряет выбранный ресурс."),
        ("x", "Убрать доход", INC_DEL, 6, "GFX_dtp_btn", "Снять ежемесячный доход/штраф Toolpack по выбранному ресурсу у A."),
        ("all", "+ в месяц всем игрокам", B("every_country", B("limit", "is_ai = no", "dtp_listed_country = yes"), "save_event_target_as = dtp_t", INC_CHAIN(1)), 5, "GFX_dtp_btn_go",
         "Каждый живой игрок получает выбранный ресурс в количестве «Числа» каждый месяц на заданный срок.")]):
    x, y, w = grid(i, cols=4, row0=11)
    button("ri_" + k, n, x, y, w, potential=T(3), allow=need_perm("res") + ("" if k == "all" else "\n" + N_TC()), effect=act("res", eff, code), sprite=spr, tt=tt)
x, y, w = grid(0, row0=8)
button("res_all", "Добавить всем игрокам", x, y, w, potential=T(3), allow=need_perm("res"),
       effect=act("res", B("every_country", B("limit", "is_ai = no"), "save_event_target_as = dtp_t", "dtp_res_do = { OP = add }"), 1), tt="Добавить количество выбранного ресурса каждому живому игроку.")

# ---------- 4. Модификаторы
area(4)
M1 = T(4, B("from", "NOT = { check_variable = { which = dtp_modpage value = 2 } }"))
M2 = T(4, B("from", chk("dtp_modpage", 2)))
x, y, w = grid(0, cols=1)
lab("um_hint", "§YСВОИ МОДИФИКАТОРЫ§!  §gзначение §Y[From.dtp_val]§!, срок §Y[From.dtp_years]§! лет — панель справа§!", x, y, w, potential=M1)
UMOD_STATIC = []
row = 2
for c, lst in UMODS.items():
    obj, p, nm = UCAT[c]
    x, y, w = grid(0, cols=1, row0=row)
    lab("um_h_" + c, {"c": "§HДержава§! (выбранная во вкладке «Держава»):", "p": "§HПланета§! (выбранная в окне планеты):", "f": "§HФлот§! (выбранный в окне флота):"}[c], x, y, w, potential=M1)
    row += 1
    need_obj = {"c": N_TC(), "p": N_TP(), "f": N_TF()}[c]
    for i, (k, n, mk, unit, u) in enumerate(lst):
        key = "dtp_u%s_%s" % (c, k)
        UMOD_STATIC.append("%s = {\n\t%s = %s\n}" % (key, mk, unit))
        loc(key, "Toolpack: " + n); loc(key + "_desc", "Модификатор выдан через Debug Toolpack.")
        x, y, w = grid(i, cols=4, row0=row)
        hasT = "dtp_%s_hasmod = { M = %s }" % (c, key)
        add = "\n".join([B("event_target:%s" % obj, setv("dtp_tv", "from.dtp_val"), setv("dtp_ty", "from.dtp_years"), "remove_modifier = %s" % key),
                         B("if", B("limit", B("from", chk("dtp_years", 0, "<="))), B("event_target:%s" % obj, "add_modifier = { modifier = %s days = -1 multiplier = dtp_tv }" % key)),
                         B("else", B("event_target:%s" % obj, "add_modifier = { modifier = %s days = 360 time_multiplier = dtp_ty multiplier = dtp_tv }" % key))])
        button("um_%s_%s_on" % (c, k), "✔ " + n, x, y, w, potential=T(4, hasT + "\n" + B("from", "NOT = { check_variable = { which = dtp_modpage value = 2 } }")), allow=need_perm(p) + "\n" + need_obj,
               effect=act(p, B("event_target:%s" % obj, "remove_modifier = %s" % key), 6), sprite="GFX_dtp_btn_on",
               tt="Действует. Нажмите, чтобы СНЯТЬ «%s»." % n)
        button("um_%s_%s" % (c, k), n, x, y, w, potential=T(4, "NOT = { %s }" % hasT + "\n" + B("from", "NOT = { check_variable = { which = dtp_modpage value = 2 } }")), allow=need_perm(p) + "\n" + need_obj,
               effect=act(p, add, 5), tt="Добавить «%s»: значение × %s %s (%s за единицу)." % (n, unit, u, mk))
    row += (len(lst) + 3) // 4


# страницы раздела: свои модификаторы / баффы и дебаффы из самой игры
for pg, n in [(1, "Свои"), (2, "Из игры")]:
    cond = B("from", chk("dtp_modpage", 2)) if pg == 2 else B("from", "NOT = { check_variable = { which = dtp_modpage value = 2 } }")
    xx = CX0 + CWN - (2 - pg + 1) * 126
    button("um_pg%d_on" % pg, n, xx, 54, 120, 30, potential=T(4, cond), sprite="GFX_dtp_btn_on")
    button("um_pg%d" % pg, n, xx, 54, 120, 30, potential=T(4, "NOT = { %s }" % cond), effect=B("from", setv("dtp_modpage", pg)), sprite="GFX_dtp_btn")
# ---- страница 2: настоящие модификаторы игры (со своими значками и описаниями в игре)
VSRC = {}
for _f in sorted(os.listdir(os.path.join(VC, "static_modifiers"))):
    _s = re.sub(r"#.*", "", open(os.path.join(VC, "static_modifiers", _f), encoding="utf-8-sig").read())
    for _m in re.finditer(r"^(\w+)\s*=\s*\{", _s, re.M):
        _i, _d = _m.end(), 1
        while _d and _i < len(_s):
            _d += {"{": 1, "}": -1}.get(_s[_i], 0); _i += 1
        VSRC[_m.group(1)] = re.findall(r"^\s*([a-z_]+)\s*=\s*(-?[\d.]+)\s*$", _s[_m.end():_i - 1], re.M)
MODRU = {"ship_fire_rate_mult": "скорострельность кораблей", "country_unity_produces_mult": "единство", "army_damage_mult": "урон армий",
         "country_commander_cap_add": "лимит командиров", "commander_initial_skill": "уровень новых командиров", "country_custodian_influence_produces_add": "влияние",
         "diplo_weight_mult": "дипломатический вес", "country_society_research_produces_mult": "социология", "pop_happiness": "счастье населения",
         "pop_ethic_pacifist_attraction_mult": "привлекательность пацифизма", "country_influence_produces_mult": "влияние", "pop_ethics_shift_speed_mult": "скорость смены этик",
         "pop_government_ethic_attraction": "привлекательность этики правительства", "pop_amenities_usage_mult": "потребление удобств",
         "planet_resettlement_unemployed_destination_mult": "приток переселенцев", "logistic_growth_mult": "рост населения", "planet_stability_add": "стабильность",
         "planet_jobs_produces_mult": "выработка рабочих мест", "species_empire_size_mult": "размер империи от видов", "pop_environment_tolerance": "пригодность",
         "planet_crime_add": "преступность", "planet_crime_mult": "преступность", "planet_building_build_speed_mult": "скорость строительства",
         "country_engineering_research_produces_mult": "инженерия", "biological_pop_happiness": "счастье органиков", "lithoid_pop_happiness": "счастье литоидов"}
def vdesc(key):
    parts = []
    for k, v in VSRC.get(key, []):
        if k in ("icon", "icon_frame"): continue
        fv = float(v); pct = k.endswith(("_mult", "pop_happiness", "_tolerance")) and abs(fv) < 5
        parts.append("%s %s%s" % (MODRU.get(k, k), ("+" if fv > 0 else "−"), ("%d%%" % round(abs(fv) * 100)) if pct else ("%g" % abs(fv))))
    return ", ".join(parts) or "эффект модификатора игры"
VMODS = [("c", "§YДЕРЖАВА A — БОНУСЫ ИГРЫ§!", "GFX_dtp_btn_go", [("fleet_maneuvers", "Учения флота"), ("new_resonance_music_art", "Новый резонанс"), ("luminous_blades", "Сияющие клинки"),
                                                       ("gal_custodian", "Кустодиан"), ("manifesti_reflections_mod", "Манифест: размышления"), ("hero_redivivus", "Возрождённый герой")]),
         ("c", "§YДЕРЖАВА A — ШТРАФЫ ИГРЫ§!", "GFX_dtp_btn_danger", [("humiliated", "Унижение"), ("maneuvers_no_protest", "Протесты против учений"), ("shroud_neg_influence", "Пустота: влияние"),
                                                        ("shroud_neg_unity", "Пустота: единство"), ("whisperers_psychosis", "Психоз шепчущих"), ("left_galactic_community", "Вне сообщества")]),
         ("p", "§YПЛАНЕТА — БОНУСЫ ИГРЫ§!", "GFX_dtp_btn_go", [("friendly_trees", "Дружелюбные деревья"), ("shooting_stars", "Звездопад"), ("food_rich_planet", "Плодородие"),
                                                   ("natural_beauty", "Природная красота"), ("free_at_last", "Свобода!"), ("great_schism_01", "Духовный подъём")]),
         ("p", "§YПЛАНЕТА — ШТРАФЫ ИГРЫ§!", "GFX_dtp_btn_danger", [("damaged_ecology", "Разрушенная экология"), ("hostile_environment", "Враждебная среда"), ("pyramid_wars", "Пирамидные войны"),
                                                     ("pop_disappearances", "Исчезновения"), ("corrupt_administration", "Коррупция"), ("planet_culture_shock", "Культурный шок")])]
VAPPLY = lambda obj, key: "\n".join([B("event_target:%s" % obj, setv("dtp_ty", "from.dtp_years"), "remove_modifier = %s" % key),
                                     B("if", B("limit", B("from", chk("dtp_years", 0, "<="))), B("event_target:%s" % obj, "add_modifier = { modifier = %s days = -1 }" % key)),
                                     B("else", B("event_target:%s" % obj, "add_modifier = { modifier = %s days = 360 time_multiplier = dtp_ty }" % key))])
for gi, (c, head, spr, lst) in enumerate(VMODS):
    x, y, w = grid(0, cols=1, row0=gi * 3)
    lab("vm_h%d" % gi, head + "  §g%s, срок — панель справа§!" % ("держава A" if c == "c" else "выбранная планета"), x, y, w, potential=M2)
    obj, p = ("dtp_t", "res") if c == "c" else ("dtp_p", "planet")
    need_obj = N_TC() if c == "c" else N_TP()
    for i, (key, n) in enumerate(lst):
        x, y, w = grid(i, cols=3, row0=gi * 3 + 1)
        if key not in VSRC:
            continue                                          # модификатора нет в этой версии игры — кнопку не делаем
        hasT = "dtp_%s_hasmod = { M = %s }" % (c, key)
        button("vm_%s_on" % key, "✔ " + n, x, y, w, potential=T(4, hasT + "\n" + B("from", chk("dtp_modpage", 2))), allow=need_perm(p) + "\n" + need_obj,
               effect=act(p, B("event_target:%s" % obj, "remove_modifier = %s" % key), 6), sprite="GFX_dtp_btn_on",
               tt="Действует: %s. Нажмите, чтобы СНЯТЬ." % vdesc(key))
        button("vm_" + key, n, x, y, w, potential=T(4, "NOT = { %s }" % hasT + "\n" + B("from", chk("dtp_modpage", 2))), allow=need_perm(p) + "\n" + need_obj,
               effect=act(p, VAPPLY(obj, key), 5), sprite=spr, tt="Модификатор из игры «%s» (%s): %s." % (n, key, vdesc(key)))
# ---------- 5. Планета (выбранная в окне планеты/звезды)
area(5)
TP = "dtp_has_tp = yes"
x, y, w = grid(0, cols=1)
pass  # подсказка перенесена в карточку цели
x, y, w = grid(0, cols=1, row0=0)
lab("pl_h0", "§YДЕЙСТВИЯ С ПЛАНЕТОЙ§!", x, y, w, potential=T(5))
x, y, w = grid(0, cols=1, row0=2)
lab("pl_empty", "§YПланета не выбрана.§! Кликните по любой планете или звезде — под её окном появится полоса Toolpack — нажмите «Выбрать».", x, y, w,
    potential=T(5, "NOT = { dtp_has_tp = yes }"))
x, y, w = grid(0, cols=1, row0=3)
lab("pl_empty2", "§gС галактической карты: клик по значку станции → полоса Toolpack → «Выбрать звезду».§!", x, y, w, potential=T(5, "NOT = { dtp_has_tp = yes }"))
button("pl_mods", "Бонусы и штрафы планеты →", CX0 + CWF - 280, CY, 280, 26, potential=T(5), sprite="GFX_dtp_btn_go",
       effect=GOTO(4) + "\n" + B("from", setv("dtp_modpage", 2)), tt="Открыть «Модификаторы → Из игры»: бонусы и штрафы для этой планеты.")
x, y, w = grid(0, row0=1)
arm_btn("pl_tr", "Передать планету → B", x, y, w, T(5, "dtp_tp_colony = yes"), need_perm("planet") + "\n" + N_RCP(), "pl_tr", "Передать колонию получателю.")
x, y, w = grid(1, row0=1)
button("pl_sys", "Отметить её систему", x, y, w, potential=T(5, TP + "\nNOT = { dtp_tp_marked = yes }"), allow=need_perm("planet"),
       effect=act("planet", B("event_target:dtp_s", "dtp_mark_sys = yes"), 36) + "\ndtp_mlist = yes")
button("pl_sys_x", "Снять отметку системы", x, y, w, potential=T(5, "dtp_tp_marked = yes"), allow=need_perm("planet"),
       effect=act("planet", B("event_target:dtp_s", "dtp_unmark_sys = yes"), 36) + "\ndtp_mlist = yes", sprite="GFX_dtp_btn_on")
x, y, w = grid(2, row0=1)
arm_btn("colony_rm", "Уничтожить колонию", x, y, w, T(5, "dtp_tp_colony = yes"), need_perm("planet") + "\n" + N_FORCE(), "colony_rm", "Удалить колонию с населением (принудительный режим).")
PLP = T(5, TP + "\nNOT = { dtp_tp_star = yes }")
for r, txt in [(2, "§YТИП ПЛАНЕТЫ§!  §gколонию — только в обитаемый тип, иначе нужен принудительный режим§!"), (5, "§YОСОБЫЕ ТИПЫ§!  §gпринудительный режим§!"), (9, "§YПРИРОДА И РАЗМЕР§!")]:
    x, y, w = grid(0, cols=1, row0=r)
    lab("pl_h%d" % r, txt, x, y, w, potential=PLP)
x, y, w = grid(0, cols=1, row0=2)
lab("pl_hs", "§YКЛАСС ЗВЕЗДЫ§!  §gпринудительный режим; отметка системы сохраняется§!", x, y, w, potential=T(5, "dtp_tp_star = yes"))
for i, (k, n) in enumerate(PC_NORMAL):
    x, y, w = grid(i, cols=5, row0=3)
    button("pc_" + k, n, x, y, w, potential=PLP, allow=need_perm("planet") + "\n" + need("dtp_need_pc", "Колонию можно перевести только в обитаемый тип; иначе — принудительный режим",
           B("OR", B("from", "dtp_force_active = yes"), "NOT = { dtp_tp_colony = yes }",
             orchain(lambda kk: B("event_target:dtp_tp_%d" % kk, B("OR", *["is_planet_class = %s" % c for c, _ in PC_NORMAL]))))),
           effect=act("planet", B("event_target:dtp_p", "change_pc = %s" % k), 9), tt="Тип «%s»." % n)
for i, (k, n) in enumerate(PC_SPECIAL):
    x, y, w = grid(i, cols=5, row0=6)
    button("pc_" + k, n, x, y, w, potential=PLP, allow=need_perm("planet") + "\n" + N_FORCE(),
           effect=act("planet", B("event_target:dtp_p", "change_pc = %s" % k), 9), sprite="GFX_dtp_btn_warn", tt="Особый тип «%s» (принудительный режим)." % n)
for i, (k, n, e, code) in enumerate([("dep", "Новая залежь", "add_random_non_blocker_deposit = yes", 10), ("reroll", "Перегенер. залежи", "reroll_deposits = yes", 10),
        ("clear", "Убрать препятствия", "clear_blockers = yes", 10), ("pmods", "Перегенер. природу", "reroll_planet_modifiers = yes", 10),
        ("size_p", "Размер +1", "change_planet_size = 1", 11), ("size_m", "Размер −1", "change_planet_size = -1", 11),
        ("pop", "+ Население", B("owner", B("owner_species", "save_event_target_as = dtp_popsp")) + "\ncreate_pop_group = { species = event_target:dtp_popsp }", 12),
        ("terra", "Завершить терраформирование", "finish_terraformation = yes", 9)]):
    x, y, w = grid(i, cols=4, row0=10)
    al = need_perm("planet") + ("\n" + need("dtp_need_colony", "Это не колония", "dtp_tp_colony = yes") if k == "pop" else "")
    button("pf_" + k, n, x, y, w, potential=PLP, allow=al, effect=act("planet", B("event_target:dtp_p", e), code))
for i, (k, n) in enumerate(STARS):
    x, y, w = grid(i, cols=4, row0=3)
    rem = "\n".join([setv("dtp_wm", 0), B("if", B("limit", "has_star_flag = dtp_marked"), setv("dtp_wm", 1), "dtp_unmark_sys = yes"),
                     "set_star_class = %s" % k, B("if", B("limit", chk("dtp_wm", 1)), "dtp_mark_sys = yes")])
    button("sc_" + k, n, x, y, w, potential=T(5, "dtp_tp_star = yes"), allow=need_perm("planet") + "\n" + N_FORCE(),
           effect=act("planet", B("event_target:dtp_s", rem), 37), sprite="GFX_dtp_btn_warn",
           tt="Сменить класс звезды системы на «%s» (меняет вид звезды и её свойства). Принудительный режим." % n)
confirm("pl_tr_ok", "передать планету получателю", 15, T(5), need_perm("planet") + "\n" + N_RCP(), "pl_tr",
        B("event_target:dtp_p", "set_owner = event_target:dtp_r", "set_controller = event_target:dtp_r"), "planet", 8)
confirm("colony_rm_ok", "уничтожить колонию", 15, T(5), need_perm("planet") + "\n" + N_FORCE(), "colony_rm", B("event_target:dtp_p", "destroy_colony = yes"), "planet", 33)

# ---------- 6. Флот
area(6)
TF = "dtp_has_tf = yes"
x, y, w = grid(0, cols=1)
pass  # подсказка перенесена в карточку цели
for i, (k, n, e, code, al, tt) in enumerate([
        ("rep", "Ремонт флота", B("event_target:dtp_f", "repair_percentage = 1"), 16, N_TF(), None),
        ("move", "Перенести к планете", B("event_target:dtp_f", "set_location = event_target:dtp_p"), 18, N_TF() + "\n" + N_TP(), "Мгновенно перенести флот к выбранной планете.")]):
    x, y, w = grid(i, row0=1)
    button("fl_" + k, n, x, y, w, potential=T(6), allow=need_perm("fleet") + "\n" + al, effect=act("fleet", e, code), tt=tt)
x, y, w = grid(2, row0=1)
arm_btn("fl_tr", "Передать флот → B", x, y, w, T(6), need_perm("fleet") + "\n" + N_TF() + "\n" + N_RCP(), "fl_tr", "Передать флот получателю.")
x, y, w = grid(0, row0=2)
arm_btn("fl_del", "Удалить флот", x, y, w, T(6), need_perm("fleet") + "\n" + N_TF(), "fl_del", "Удалить флот без обломков.")
for i, (fr, n) in enumerate([("0.1", "10%"), ("0.25", "25%"), ("0.5", "50%")]):
    x, y, w = grid(i, row0=3)
    button("fl_new%d" % i, "Новый флот державы: %s" % n, x, y, w, potential=T(6), allow=need_perm("fleet") + "\n" + N_TC(),
           effect=act("fleet", B("event_target:dtp_t", "create_fleet_from_naval_cap = { fraction = %s }" % fr), 17), tt="Флот из актуальных проектов кораблей державы (доля флотского лимита).")
x, y, w = grid(0, cols=2, row0=4)
button("fl_mrep", "Ремонт всех флотов державы", x, y, w, potential=T(6), allow=need_perm("fleet") + "\n" + N_TC(),
       effect=act("fleet", B("event_target:dtp_t", B("every_owned_fleet", "repair_percentage = 1")), 16))
x, y, w = grid(1, cols=2, row0=4)
arm_btn("mass_fl", "Все военные флоты державы → B", x, y, w, T(6), need_perm("fleet") + "\n" + N_TC() + "\n" + N_RCP() + "\n" + N_DIFF(), "mass_fl", "Передать все военные флоты.")
# 10.9.0: КОНСТРУКТОР ФЛОТА — тип корабля, количество, место; шаблон — проект державы A этого типа (как в её редакторе кораблей).
SH_SIZES = [('corvette', 'Корвет'), ('destroyer', 'Эсминец'), ('cruiser', 'Крейсер'), ('battleship', 'Линкор'), ('titan', 'Титан'), ('juggernaut', 'Джаггернаут'), ('colossus', 'Колосс'), ('science', 'Научный'), ('constructor', 'Строитель')]
SH_MAX = 100
x, y, w = grid(0, cols=1, row0=5)
lab("sh_h", "§YКОНСТРУКТОР ФЛОТА§!  §gполучает держава A · шаблон — её проект кораблей выбранного типа§!", x, y, w, potential=T(6))
for i, (k, n) in enumerate(SH_SIZES):
    x, y, w = grid(i, cols=5, row0=6)
    button("sh_%s_on" % k, "● " + n, x, y, w, potential=T(6, B("from", chk("dtp_shz", i))), sprite="GFX_dtp_btn_on", tt="Выбран тип: %s." % n)
    button("sh_" + k, n, x, y, w, potential=T(6, B("from", "NOT = { %s }" % chk("dtp_shz", i))), effect=B("from", setv("dtp_shz", i)), tt="Выбрать тип корабля: %s." % n)
SHCAP = B("if", B("limit", chk("dtp_shn", SH_MAX, ">")), setv("dtp_shn", SH_MAX)) + "\n" + B("if", B("limit", chk("dtp_shn", 1, "<")), setv("dtp_shn", 1))
x, y, w = grid(0, cols=6, row0=8)
lab("sh_cnt_l", "§gКоличество:§!", x + 4, y + 4, w, potential=T(6))
for i, (k, d) in enumerate([("m10", -10), ("m1", -1)]):
    x, y, w = grid(1 + i, cols=6, row0=8)
    button("sh_" + k, "%d" % d, x, y, w, potential=T(6), effect=B("from", "change_variable = { which = dtp_shn value = %d }" % d, SHCAP))
x, y, w = grid(3, cols=6, row0=8)
button("sh_cnt", "  §Y[From.dtp_shn]§!  §gшт.§!", x, y - 3, w, 36, sprite="GFX_dtp_field", label=True, font="malgun_goth_24", potential=T(6), tt="Сколько кораблей создать (1–%d)." % SH_MAX)
for i, (k, d) in enumerate([("p1", 1), ("p10", 10)]):
    x, y, w = grid(4 + i, cols=6, row0=8)
    button("sh_" + k, "+%d" % d, x, y, w, potential=T(6), effect=B("from", "change_variable = { which = dtp_shn value = %d }" % d, SHCAP))
ATP = B("from", "has_country_flag = dtp_sh_atp")
x, y, w = grid(0, cols=2, row0=9)
button("sh_loc_c", "● У столицы A", x, y, w, potential=T(6, "NOT = { %s }" % ATP), sprite="GFX_dtp_btn_on", tt="Флот появится у столицы державы A. Нажмите — у выбранной планеты P.",
       effect=B("from", "set_country_flag = dtp_sh_atp"))
button("sh_loc_p", "● У выбранной планеты P", x, y, w, potential=T(6, ATP), sprite="GFX_dtp_btn_on", tt="Флот появится у выбранной планеты P (окно планеты → «Выбрать»). Нажмите — у столицы A.",
       effect=B("from", "remove_country_flag = dtp_sh_atp"))
x, y, w = grid(1, cols=2, row0=9)
lab("sh_tpl", "§gШаблон — корабль/проект A этого типа. §HТип не изучен у A — кораблей не будет.§!§!", x + 4, y + 4, w, potential=T(6))
def SH_PROTO(owner):
    """10.9.2: образец — любой корабль владельца этого типа (game.log 22.10: random_existing_design → «invalid design»)."""
    return "\n".join([B("if", B("limit", "exists = event_target:dtp_sh_proto"), "clear_global_event_target = dtp_sh_proto")] + [B("if", B("limit", B(owner, chk("dtp_shk", i))),
        B(owner, B("random_controlled_ship", B("limit", "is_ship_size = %s" % k), "save_global_event_target_as = dtp_sh_proto"))) for i, (k, n) in enumerate(SH_SIZES)])
def SH_ONE(chk_owner):
    return B("if", B("limit", "exists = event_target:dtp_sh_proto"), B("create_ship", "name = random", "design = event_target:dtp_sh_proto")) + "\n" + \
        B("else", *[B("if" if i == 0 else "else_if", B("limit", B(chk_owner, chk("dtp_shk", i))), B("create_ship", "name = random", "random_existing_design = %s" % k)) for i, (k, n) in enumerate(SH_SIZES)])
SHIPS = SH_ONE("event_target:dtp_t")
SHBUILD = "\n".join([
    B("event_target:dtp_t", setv("dtp_shc", "from.dtp_shn"), setv("dtp_shk", "from.dtp_shz"), B("capital_scope", "save_event_target_as = dtp_sh_loc")),
    B("if", B("limit", ATP, "exists = event_target:dtp_p"), B("event_target:dtp_p", "save_event_target_as = dtp_sh_loc")),
    SH_PROTO("event_target:dtp_t"),
    B("event_target:dtp_t", B("create_fleet", "name = random", B("effect", "set_owner = event_target:dtp_t",
        B("while", B("limit", B("event_target:dtp_t", chk("dtp_shc", 0, ">"))), SHIPS, B("event_target:dtp_t", "change_variable = { which = dtp_shc value = -1 }")),
        "set_location = { target = event_target:dtp_sh_loc distance = 15 angle = random }"))),
    'log = "DTP FLEET: constructor"'])
x, y, w = grid(0, cols=1, row0=10)
for i, (k, n) in enumerate(SH_SIZES):
    button("sh_go_" + k, "Создать: §Y[From.dtp_shn]§! × %s" % n, x, y, w, potential=T(6, B("from", chk("dtp_shz", i))), sprite="GFX_dtp_btn_go",
           allow=need_perm("fleet") + "\n" + N_TC() + "\n" + B("if", B("limit", ATP), N_TP()), effect=act("fleet", SHBUILD, 17),
           tt="Создать новый флот державы A: %s — столько, сколько набрано (до %d). Шаблон — проект любого корабля A этого типа; если таких кораблей у A нет — её сохранённый проект. §HВажно:§! если у A этот тип корабля ещё не изучен (нет технологии, например титанов или джаггернаутов), кораблей не будет." % (n, SH_MAX))
confirm("fl_tr_ok", "передать флот получателю", 15, T(6), need_perm("fleet") + "\n" + N_RCP(), "fl_tr", B("event_target:dtp_f", "set_owner = event_target:dtp_r"), "fleet", 14)
confirm("fl_del_ok", "удалить флот", 15, T(6), need_perm("fleet"), "fl_del", B("event_target:dtp_f", "delete_fleet = this"), "fleet", 15)
confirm("mass_fl_ok", "все военные флоты державы → получатель", 15, T(6), need_perm("fleet") + "\n" + N_RCP(), "mass_fl",
        B("event_target:dtp_t", B("every_owned_fleet", B("limit", "dtp_military_fleet = yes"), "set_owner = event_target:dtp_r")), "fleet", 14)

# ---------- 7. Дипломатия (A = держава, B = получатель)
area(7)
R = "event_target:dtp_r"
DIPLO = [("contact", "Установить контакт", "establish_communications = %s" % R),
         ("op_p", "Отношение A→B +100", "add_opinion_modifier = { modifier = dtp_opinion_good who = %s }" % R),
         ("op_m", "Отношение A→B −100", "add_opinion_modifier = { modifier = dtp_opinion_bad who = %s }" % R),
         ("op_0", "Сбросить отношения", "remove_opinion_modifier = { modifier = dtp_opinion_good who = %s }\nremove_opinion_modifier = { modifier = dtp_opinion_bad who = %s }" % (R, R)),
         ("trust", "Доверие A→B +25", "add_trust = { amount = 25 who = %s }" % R),
         ("truce", "Перемирие A↔B", "set_truce = { target = %s type = war }" % R),
         ("untruce", "Снять перемирие", "end_truce = %s" % R),
         ("close", "Закрыть границы для B", "set_closed_borders = { who = %s status = yes }" % R),
         ("open", "Открыть границы для B", "set_closed_borders = { who = %s status = no }" % R),
         ("guar", "A гарантирует B", "guarantee_country = %s" % R)]
x, y, w = grid(0, cols=1)
pass  # подсказка перенесена в карточку цели
for i, (k, n, e) in enumerate(DIPLO):
    x, y, w = grid(i, row0=1)
    button("dp_" + k, n, x, y, w, potential=T(7), allow=need_perm("diplo") + "\n" + N_TC() + "\n" + N_RCP() + "\n" + N_DIFF(),
           effect=act("diplo", B("event_target:dtp_t", e), 19))
for i, (a, n, al, tt) in enumerate([("subj", "A → субъект B", N_DIFF(), "Сделать A вассалом B."), ("fed", "A выходит из федерации", "", "Убрать A из федерации."),
                                    ("war", "Война A → B", N_DIFF() + "\n" + N_FORCE(), "Объявить войну (цель — унижение), принудительный режим.")]):
    x, y, w = grid(i, row0=5)
    arm_btn(a, n, x, y, w, T(7), need_perm("diplo") + "\n" + N_TC() + ("\n" + N_RCP() if a != "fed" else "") + ("\n" + al if al else ""), a, tt)
# 10.9.0: БЕЛЫЙ МИР — как в игре при «статус-кво»: война A и B завершается без передачи систем, всем её участникам — выход из войны,
# A и B получают перемирие; всем игрокам — окно ведущего. Механика та же, что у резолюций сообщества (remove_war_participant).
WARSIDE = "OR = { AND = { is_war_participant = { who = event_target:dtp_t side = attackers } is_war_participant = { who = event_target:dtp_r side = defenders } } AND = { is_war_participant = { who = event_target:dtp_t side = defenders } is_war_participant = { who = event_target:dtp_r side = attackers } } }"
x, y, w = grid(0, row0=6)
button("dp_wpeace", "Белый мир A ↔ B", x, y, w, potential=T(7), sprite="GFX_dtp_btn_go",
       allow=need_perm("diplo") + "\n" + N_TC() + "\n" + N_RCP() + "\n" + N_DIFF() + "\n" + need("dtp_need_atwar", "A и B сейчас не воюют друг с другом", "event_target:dtp_t = { is_at_war_with = event_target:dtp_r }"),
       effect=act("diplo", "\n".join([
           B("event_target:dtp_t", "save_global_event_target_as = dtp_wp_a"), B("event_target:dtp_r", "save_global_event_target_as = dtp_wp_b"),
           B("event_target:dtp_t", B("every_war", B("limit", WARSIDE), B("every_war_participant", B("prev", "remove_war_participant = prev"))),
             "set_truce = { target = event_target:dtp_r type = war }"),
           'log = "DTP DIPLO: white peace"',
           B("every_country", B("limit", "is_ai = no", "dtp_listed_country = yes"), "country_event = { id = dtp.1009 }")]), 19),
       tt="Завершить войну между A и B белым миром (статус-кво): никто ничего не получает, все участники этой войны выходят из неё, A и B получают перемирие. Всем игрокам придёт окно ведущего. Работает и между игроками, и с ИИ.")
x, y, w = grid(1, cols=3, row0=6)
lab("dp_lim", "§gдержава A и получатель B — в карточке сверху§!", x + 4, y + 4, 2 * w + 6, potential=T(7))
confirm("subj_ok", "A становится субъектом B", 15, T(7), need_perm("diplo") + "\n" + N_RCP(), "subj", B("event_target:dtp_t", "set_subject_of = { who = %s }" % R), "diplo", 19)
confirm("fed_ok", "A выходит из федерации", 15, T(7), need_perm("diplo"), "fed", B("event_target:dtp_t", "remove_from_federation = yes"), "diplo", 19)
confirm("war_ok", "объявить войну A → B", 15, T(7), need_perm("diplo") + "\n" + N_FORCE(), "war",
        B("event_target:dtp_t", "declare_war = { target = %s attacker_war_goal = wg_humiliation }" % R), "diplo", 19)

# ---------- 8. Государство
area(8)
for i, (k, n, e, code, al) in enumerate([
        ("tech", "Копировать технологии у B", "copy_techs_from = { target = %s }" % R, 21, N_RCP()),
        ("trad", "Копировать традиции у B", "copy_traditions_from = { target = %s }" % R, 21, N_RCP()),
        ("perk", "Копировать перки у B", "copy_ascension_perks_from = { target = %s }" % R, 21, N_RCP()),
        ("pol", "Сбросить откаты политик", "reset_policy_cooldowns = yes", 28, ""),
        ("gov", "Разблокировать правительство", "set_government_cooldown = no", 28, "")]):
    x, y, w = grid(i)
    button("st_" + k, n, x, y, w, potential=T(8), allow=need_perm("state") + "\n" + N_TC() + ("\n" + al if al else ""),
           effect=act("state", B("event_target:dtp_t", e), code))
x, y, w = grid(5)
button("st_force_on", "Принуд. режим: ВКЛ", x, y, w, potential=T(8, B("from", "NOT = { has_country_flag = dtp_force_mode }")), allow=need_perm("force"),
       effect=B("from", B("if", B("limit", "dtp_has_perm = { P = force }"), "set_country_flag = dtp_force_mode")) + "\ndtp_result = { CODE = 30 }", sprite="GFX_dtp_btn_warn",
       tt="Действия в обход правил игры: особые типы планет, класс звезды, этики без проверок, война, уничтожение колоний.")
button("st_force_off", "Принуд. режим: ВЫКЛ", x, y, w, potential=T(8, B("from", "has_country_flag = dtp_force_mode")),
       effect=B("from", "remove_country_flag = dtp_force_mode") + "\ndtp_result = { CODE = 30 }", sprite="GFX_dtp_btn_on")
for i, (k, n) in enumerate(ETHICS):
    x, y, w = grid(i, cols=4, row0=3)
    button("eth_s_" + k, "→ " + n, x, y, w, potential=T(8), allow=need_perm("state") + "\n" + N_TC(),
           effect=act("state", B("event_target:dtp_t", "shift_ethic = ethic_%s" % k), 20), tt="Штатный сдвиг к «%s»." % n)
for row0, pre, eff, spr in [(5, "+ ", "country_add_ethic = ethic_%s", "GFX_dtp_btn_warn"), (7, "++ ", "country_add_ethic = ethic_fanatic_%s", "GFX_dtp_btn_warn"),
                            (9, "− ", "country_remove_ethic = ethic_%s\ncountry_remove_ethic = ethic_fanatic_%s", "GFX_dtp_btn_danger")]:
    for i, (k, n) in enumerate(ETHICS):
        x, y, w = grid(i, cols=4, row0=row0)
        button("eth_%d_%s" % (row0, k), pre + n, x, y, w, potential=T(8), allow=need_perm("state") + "\n" + N_TC() + "\n" + N_FORCE(),
               effect=act("state", B("event_target:dtp_t", eff % ((k, k) if eff.count("%s") == 2 else k)), 20), sprite=spr)

x, y, w = grid(0, cols=1, row0=11)
for i, (k, n, e, tt) in enumerate([("fin", "Завершить исследования A", "finish_all_researches = yes", "Мгновенно завершить все текущие исследования державы A."),
                                   ("half", "Исследования A +50%", "progress_all_researches = 0.5", "Продвинуть текущие исследования A на половину."),
                                   ("inc_e", "A: +год дохода энергии", "add_monthly_resource_mult = { resource = energy value = 12 min = 0 max = 1000000 }", "Единовременно — 12 месячных доходов энергии."),
                                   ("inc_a", "A: +год дохода сплавов", "add_monthly_resource_mult = { resource = alloys value = 12 min = 0 max = 1000000 }", "Единовременно — 12 месячных доходов сплавов.")]):
    x, y, w = grid(i, cols=4, row0=11)
    button("st2_" + k, n, x, y, w, potential=T(8), allow=need_perm("state") + "\n" + N_TC(), effect=act("state", B("event_target:dtp_t", e), 21 if i < 2 else 1),
           sprite="GFX_dtp_btn_go", tt=tt)

# ---------- 9. Расы
area(9)
SP = B("event_target:dtp_t", B("owner_species", "save_event_target_as = dtp_sp"))
x, y, w = grid(0, cols=1)
lab("sp_warn", "§YПРИЗНАКИ ВИДА§!  §R— меняются у всего вида, во всех империях§!", x, y, w, potential=T(9))
for i, (k, n) in enumerate(TRAITS):
    x, y, w = grid(i, cols=4, row0=1)
    has = "dtp_sp_hastrait = { T = %s }" % k
    button("tr_%s_on" % k, "✔ " + n, x, y, w, potential=T(9, has), allow=need_perm("species") + "\n" + N_TC(),
           effect=act("species", SP + "\n" + B("event_target:dtp_sp", "change_species_characteristics = { remove_trait = %s }" % k), 22), sprite="GFX_dtp_btn_on",
           tt="Есть у вида. Нажмите, чтобы УБРАТЬ «%s»." % n)
    button("tr_" + k, "+ " + n, x, y, w, potential=T(9, "NOT = { %s }" % has), allow=need_perm("species") + "\n" + N_TC(),
           effect=act("species", SP + "\n" + B("event_target:dtp_sp", "change_species_characteristics = { add_trait = %s }" % k), 22))
x, y, w = grid(0, cols=1, row0=4)
lab("sp_hc", "§YГРАЖДАНСТВО§!", x, y, w, potential=T(9))
for i, (k, n) in enumerate(CITIZEN):
    x, y, w = grid(i, row0=5)
    button("cit_" + k, n, x, y, w, potential=T(9), allow=need_perm("species") + "\n" + N_TC(),
           effect=act("species", SP + "\n" + B("event_target:dtp_sp", "set_citizenship_type = { country = event_target:dtp_t type = %s cooldown = no }" % k), 23))


LIVING = [("living_standard_utopian", "Жизнь: утопия"), ("living_standard_good", "Жизнь: высокий"), ("living_standard_normal", "Жизнь: обычный"), ("living_standard_academic_privilege", "Академ. привил."),
          ("living_standard_stratified", "Жизнь: стратиф."), ("living_standard_decadent", "Декадентский"), ("living_standard_subsistence", "Жизнь: выживание"), ("living_standard_none", "Жизнь: нет")]
MILSRV = [("military_service_full", "Служба: полная"), ("military_service_limited", "Служба: ограничена"), ("military_service_none", "Служба: нет")]
SLAVE = [("slavery_normal", "Рабы: труд"), ("slavery_domestic", "Рабы: домашние"), ("slavery_military", "Рабы: боевые"), ("slavery_indentured", "Рабы: кабала"), ("slavery_livestock", "Рабы: скот")]
PURGE = [("purge_normal", "Чистка: обычная"), ("purge_displacement", "Выселение"), ("purge_labor_camps", "Трудлагеря"), ("purge_neutering", "Стерилизация"), ("purge_processing", "Переработка")]
x, y, w = grid(0, cols=1, row0=6)
lab("sp_h2", "§YПРАВА ВИДА§!  §gбез отката; несовместимое с этиками игра может отменить§!", x, y, w, potential=T(9))
for rows, cols, lst, eff, code in [(7, 4, LIVING, "set_living_standard", 44), (9, 3, MILSRV, "set_military_service_type", 45),
                                   (10, 5, SLAVE, "set_slavery_type", 46), (11, 5, PURGE, "set_purge_type", 47)]:
    for i, (k, n) in enumerate(lst):
        x, y, w = grid(i, cols=cols, row0=rows)
        button("sr_" + k, n, x, y, w, potential=T(9), allow=need_perm("species") + "\n" + N_TC(),
               effect=act("species", SP + "\n" + B("event_target:dtp_sp", "%s = { country = event_target:dtp_t type = %s cooldown = no }" % (eff, k)), code),
               sprite="GFX_dtp_btn_danger" if code == 47 else "GFX_dtp_btn")

# ---------- 10. Ивенты — 10.9.0: раздел убран. Его кнопки дублировали другие разделы: залежь — «Планета», ремонт — «Флот»,
# ресурсы/наука — «Ресурсы», стабильность — «Модификаторы», объявления — «Мастер игры»; «Мирное предложение» стало
# настоящим «Белым миром» в «Дипломатии». События каталога (dtp.1001…) остаются в файлах для старых сохранений.


# ---------- 13. Правление (форма правления, гражданские модели, указы)
area(13)
AUTHS = [("auth_democratic", "Демократия"), ("auth_oligarchic", "Олигархия"), ("auth_dictatorial", "Диктатура"), ("auth_imperial", "Империя"),
         ("auth_corporate", "Корпорация"), ("auth_hive_mind", "Коллективный разум"), ("auth_machine_intelligence", "Машинный разум")]
CIVICS = [("civic_technocracy", "Технократия"), ("civic_meritocracy", "Меритократия"), ("civic_mining_guilds", "Гильдии шахтёров"), ("civic_agrarian_idyll", "Аграрная идиллия"),
          ("civic_beacon_of_liberty", "Маяк свободы"), ("civic_imperial_cult", "Имперский культ"), ("civic_police_state", "Полицейское государство"), ("civic_warrior_culture", "Культура воинов"),
          ("civic_distinguished_admiralty", "Адмиралтейство"), ("civic_citizen_service", "Гражданская служба"), ("civic_efficient_bureaucracy", "Эффект. бюрократия"), ("civic_parliamentary_system", "Парламент"),
          ("civic_slaver_guilds", "Гильдии работорговцев"), ("civic_exalted_priesthood", "Жречество"), ("civic_philosopher_king", "Король-философ"), ("civic_merchant_guilds", "Гильдии торговцев"),
          ("civic_inwards_perfection", "Внутр. совершенство"), ("civic_fanatic_purifiers", "Фанатичные очистители"), ("civic_barbaric_despoilers", "Варвары-грабители"), ("civic_functional_architecture", "Функц. архитектура")]
EDICTS = [("map_the_stars", "Карта звёзд"), ("research_subsidies", "Субс. науке"), ("mining_subsidies", "Субс. добыче"), ("farming_subsidies", "Субс. фермам"),
          ("industrial_subsidies", "Субс. промышл."), ("capacity_subsidies", "Субс. энергии"), ("fleet_supremacy", "Флот превыше"), ("diplomatic_grants", "Диплом. гранты")]
def gov_prep(k):
    """10.8.2: change_government молча не срабатывает, если этики запрещены формой правления (possible в authorities) —
    сначала приводим этики к допустимым (замена с тем же числом очков)."""
    def swap(pairs): return [B("if", B("limit", "has_ethic = %s" % a), "country_remove_ethic = %s" % a, "country_add_ethic = %s" % b) for a, b in pairs]
    if k in ("auth_hive_mind", "auth_machine_intelligence"):
        return [B("if", B("limit", "NOT = { has_ethic = ethic_gestalt_consciousness }"), "shift_ethic = ethic_gestalt_consciousness")]
    out = [B("if", B("limit", "has_ethic = ethic_gestalt_consciousness"), "country_remove_ethic = ethic_gestalt_consciousness",
             "country_add_ethic = ethic_fanatic_pacifist", "country_add_ethic = ethic_materialist")]
    if k == "auth_democratic":
        out += swap([("ethic_fanatic_authoritarian", "ethic_fanatic_egalitarian"), ("ethic_authoritarian", "ethic_egalitarian")])
    elif k in ("auth_dictatorial", "auth_imperial"):
        out += swap([("ethic_fanatic_egalitarian", "ethic_fanatic_authoritarian"), ("ethic_egalitarian", "ethic_authoritarian")])
    else:   # олигархия, корпорация: нельзя фанатичные эгалитаризм/авторитаризм
        out += swap([("ethic_fanatic_egalitarian", "ethic_egalitarian"), ("ethic_fanatic_authoritarian", "ethic_authoritarian")])
    return out
x, y, w = grid(0, cols=1)
lab("gv_h1", "§YФОРМА ПРАВЛЕНИЯ§!  §gпринудительно, без отката; действующая подсвечена§!", x, y, w, potential=T(13))
for i, (k, n) in enumerate(AUTHS):
    x, y, w = grid(i, cols=4, row0=1)
    button("au_%s_on" % k, "✔ " + n, x, y, w, potential=T(13, "dtp_tc_has_auth = { A = %s }" % k), sprite="GFX_dtp_btn_on")
    button("au_" + k, n, x, y, w, potential=T(13, "NOT = { dtp_tc_has_auth = { A = %s } }" % k), allow=need_perm("state") + "\n" + N_TC() + "\n" + N_FORCE(),
           effect=act("state", B("event_target:dtp_t", *gov_prep(k), "change_government = { authority = %s cooldown = no remove_invalid_civics = yes }" % k), 39), sprite="GFX_dtp_btn_warn",
           tt="Сменить форму правления на «%s» (принудительный режим). Игра не даёт сменить правление при несовместимых этиках — поэтому мод сначала подправляет этики (например, авторитаризм → эгалитаризм для демократии, коллективное сознание для разумов), а несовместимые гражданские модели снимаются." % n)
x, y, w = grid(0, cols=1, row0=3)
lab("gv_h2", "§YГРАЖДАНСКИЕ МОДЕЛИ§!  §gподсвечена — есть (нажать — убрать), «+» — добавить§!", x, y, w, potential=T(13))
for i, (k, n) in enumerate(CIVICS):
    x, y, w = grid(i, cols=4, row0=4)
    has = "dtp_tc_has_civic = { C = %s }" % k
    button("cv_%s_on" % k, "✔ " + n, x, y, w, potential=T(13, has), allow=need_perm("state") + "\n" + N_TC() + "\n" + N_FORCE(),
           effect=act("state", B("event_target:dtp_t", "force_remove_civic = %s" % k), 40), sprite="GFX_dtp_btn_on", tt="Есть у A. Нажмите, чтобы УБРАТЬ «%s»." % n)
    button("cv_" + k, "+ " + n, x, y, w, potential=T(13, "NOT = { %s }" % has), allow=need_perm("state") + "\n" + N_TC() + "\n" + N_FORCE(),
           effect=act("state", B("event_target:dtp_t", "force_add_civic = %s" % k), 40), tt="Добавить «%s» державе A без проверок (принудительный режим)." % n)
x, y, w = grid(0, cols=1, row0=9)
lab("gv_h3", "§YУКАЗЫ§!  §gвключить у A бесплатно; выключаются в окне указов игры§!", x, y, w, potential=T(13))
for i, (k, n) in enumerate(EDICTS):
    x, y, w = grid(i, cols=4, row0=10)
    button("ed_%s_on" % k, "✔ " + n, x, y, w, potential=T(13, "dtp_tc_has_edict = { E = %s }" % k), sprite="GFX_dtp_btn_on")
    button("ed_" + k, "+ " + n, x, y, w, potential=T(13, "NOT = { dtp_tc_has_edict = { E = %s } }" % k), allow=need_perm("state") + "\n" + N_TC(),
           effect=act("state", B("event_target:dtp_t", "add_edict = %s" % k), 41), tt="Включить указ «%s» державе A." % n)
x, y, w = grid(0, cols=1, row0=12)
lab("gv_lim", "Политики меняются в окне политик игры; откат снимается во вкладке «Государство».", x, y, w, potential=T(13))

# ---------- 14. Постройки (выбранная планета)
area(14)
DISTR = [("district_city", "Город"), ("district_generator", "Энергия"), ("district_mining", "Добыча"), ("district_farming", "Фермы"),
         ("district_hive", "Улей"), ("district_nexus", "Нексус")]
BLDG = [("building_research_lab_1", "Лаборатория"), ("building_foundry_1", "Литейная"), ("building_factory_1", "Фабрика"), ("building_hydroponics_farm", "Гидропоника"),
        ("building_commercial_zone", "Торговая зона"), ("building_holo_theatres", "Голотеатры"), ("building_bureaucratic_1", "Администрация"), ("building_military_academy", "Воен. академия"),
        ("building_stronghold", "Крепость"), ("building_planetary_shield_generator", "Планетар. щит"), ("building_refinery", "Переработка газа"), ("building_medical_1", "Медцентр")]
PL = lambda: need_perm("planet") + "\n" + N_TP()
x, y, w = grid(0, cols=1)
per_k_label("bd_t", "Колония: §Y[dtp_tp_#.GetName]§! — районы и здания добавляются без стоимости, если есть место", x, y, w, pot_extra=T(14), none_text="§RСначала выберите планету§!: окно планеты → «Выбрать»", tgt="dtp_tp")
for i, (k, n) in enumerate(DISTR):
    x, y, w = grid(i, cols=3, row0=1)
    hw = (w - 6) // 2
    button("di_a_" + k, "+ " + n, x, y, hw, potential=T(14), allow=PL(), effect=act("planet", B("event_target:dtp_p", B("if", B("limit", "exists = owner"), "add_district = %s" % k)), 42),
           tt="Добавить район «%s» на выбранную колонию." % n)
    button("di_r_" + k, "− " + n, x + hw + 6, y, hw, potential=T(14), allow=PL(), effect=act("planet", B("event_target:dtp_p", "remove_district = %s" % k), 42), sprite="GFX_dtp_btn_danger",
           tt="Убрать один район «%s»." % n)
x, y, w = grid(0, cols=1, row0=3)
lab("bd_h", "§YЗдания§!: + построить сразу, − снести одно.", x, y, w, potential=T(14))
for i, (k, n) in enumerate(BLDG):
    x, y, w = grid(i, cols=3, row0=4)
    hw = w - 46
    button("bu_a_" + k, "+ " + n, x, y, hw, potential=T(14), allow=PL(), effect=act("planet", B("event_target:dtp_p", B("if", B("limit", "exists = owner"), "add_building = %s" % k)), 43),
           tt="Построить «%s» сразу (если есть свободный слот)." % n)
    button("bu_r_" + k, "−", x + hw + 6, y, w - hw - 6, potential=T(14), allow=PL(), effect=act("planet", B("event_target:dtp_p", "remove_building = %s" % k), 43), sprite="GFX_dtp_btn_danger",
           tt="Снести одно здание «%s»." % n)
x, y, w = grid(0, cols=3, row0=9)
button("bd_rep", "Починить все здания", x, y, w, potential=T(14), allow=PL(), effect=act("planet", B("event_target:dtp_p", "repair_all_buildings = yes"), 43))
x, y, w = grid(1, cols=3, row0=9)
arm_btn("bd_clrb", "Снести ВСЕ здания", x, y, w, T(14), PL(), "bd_clrb", "Снести все здания на выбранной планете.")
x, y, w = grid(2, cols=3, row0=9)
arm_btn("bd_clrd", "Снести ВСЕ районы", x, y, w, T(14), PL(), "bd_clrd", "Убрать все районы на выбранной планете.")
confirm("bd_clrb_ok", "снести все здания на планете", 15, T(14), PL(), "bd_clrb", B("event_target:dtp_p", "remove_all_buildings = yes"), "planet", 43)
confirm("bd_clrd_ok", "убрать все районы на планете", 15, T(14), PL(), "bd_clrd", B("event_target:dtp_p", "remove_all_districts = yes"), "planet", 42)
x, y, w = grid(0, cols=1, row0=11)
lab("bd_lim", "Очередь строительства скриптам недоступна — постройки ставятся сразу, минуя очередь.", x, y, w, potential=T(14))


# ---------- 15. Главная: стартовая точка — цель (карточка сверху), разделы, быстрые и недавние действия
area(15)
RI = {k: i + 1 for i, (k, n, s) in enumerate(RES)}
x, y, w = grid(0, cols=1, row0=0)
lab("hm_h0", "§YРАЗДЕЛЫ§!  §gкуда перейти§!", x, y, w, potential=T(15))
CATS = [(3, "Экономика", "ресурсы и бонусы"), (5, "Миры", "планеты, постройки"), (6, "Флоты", "ремонт и передача"),
        (8, "Держава", "этики, правление, виды"), (1, "Системы", "отметки на карте"), (16, "Мастер игры", "для ведущего")]
for i, (t, n, d) in enumerate(CATS):
    x, y, w = grid(i, cols=3, row0=1)
    button("hm_cat%d" % t, n, x, y, w, 32, potential=T(15), effect=GOTO(t) + ("\ndtp_mlist = yes" if t == 1 else ""),
           sprite="GFX_dtp_tile%d" % t, tt="«%s» — %s" % (n, d))
x, y, w = grid(0, cols=1, row0=3)
lab("hm_h1", "§YБЫСТРО: + РЕСУРСЫ ДЕРЖАВЕ A§!  §gколичество — в панели «Число» справа§!", x, y, w, potential=T(15))
for i, rk in enumerate(["energy", "minerals", "alloys", "influence", "unity", "consumer_goods"]):
    x, y, w = grid(i, cols=3, row0=4)
    rn = dict((k, n) for k, n, s in RES)[rk]
    button("hm_r_" + rk, "+ " + rn, x, y, w, potential=T(15), allow=need_perm("res") + "\n" + N_TC(), sprite="GFX_dtp_btn_go",
           effect=B("from", setv("dtp_res", RI[rk]), setv("dtp_lastop", 1), setv("dtp_lastres", RI[rk]), setv("dtp_lastamt", "dtp_amount")) + "\n" + act("res", "dtp_res_do = { OP = add }", 1),
           tt="Добавить державе A: %s × число из панели «Число» (сейчас [From.dtp_amount])." % rn)
x, y, w = grid(0, cols=1, row0=6)
lab("hm_h4", "§YНЕДАВНЕЕ§!", x, y, w, potential=T(15))
x, y, w = grid(0, cols=1, row0=7)
lab("hm_rr0", "§gВы ещё ничего не делали с ресурсами — здесь появится кнопка повтора.§!", x, y, w, potential=T(15, B("from", "NOT = { is_variable_set = dtp_lastop }")))
for oi, (op, sign) in enumerate([("add", "+"), ("sub", "−"), ("set", "=")]):
    for ri, (rk, rn, rs) in enumerate(RES):
        button("hm_rr_%s_%d" % (op, ri + 1), "↻ Повторить: %s [From.dtp_lastamt] %s для A" % (sign, rn), x, y, w,
               potential=T(15, B("from", chk("dtp_lastop", oi + 1), chk("dtp_lastres", ri + 1))), allow=need_perm("res") + "\n" + N_TC(),
               effect=B("from", setv("dtp_res", ri + 1), setv("dtp_amount", "dtp_lastamt")) + "\n" + act("res", "dtp_res_do = { OP = %s }" % op, oi + 1), sprite="GFX_dtp_btn_go")
x, y, w = grid(0, cols=3, row0=8)
button("hm_log", "Журнал действий →", x, y, w, potential=T(15), effect=GOTO(12))
x, y, w = grid(1, cols=3, row0=8)
button("hm_sys", "Отмечено: [From.dtp_mcount] →", x, y, w, potential=T(15), effect=GOTO(1) + "\ndtp_mlist = yes")
x, y, w = grid(2, cols=3, row0=8)
button("hm_rules", "Правила партии", x, y, w, potential=T(15), effect=B("from", "country_event = { id = dtp.1240 }"), sprite="GFX_dtp_btn_go",
       tt="Открыть окно с правилами, которые сейчас действуют: запрет войн и срок, таймер сессии, личные запрет или защита вашей державы. Доступно всем игрокам, права не нужны.")
x, y, w = grid(0, cols=1, row0=9)
lab("hm_h5", "§YРЕЖИМ§!", x, y, w, potential=T(15))
x, y, w = grid(0, cols=1, row0=10)
button("hm_f_on", "Принудительный режим: выключен — включить", x, y, w, potential=T(15, B("from", "NOT = { has_country_flag = dtp_force_mode }")), allow=need_perm("force"),
       effect=B("from", B("if", B("limit", "dtp_has_perm = { P = force }"), "set_country_flag = dtp_force_mode")) + "\ndtp_result = { CODE = 30 }", sprite="GFX_dtp_btn_warn",
       tt="Снимает проверки игры: особые типы планет, класс звезды, этики, правление, война.")
button("hm_f_off", "Принудительный режим ВКЛЮЧЁН — выключить", x, y, w, potential=T(15, B("from", "has_country_flag = dtp_force_mode")),
       effect=B("from", "remove_country_flag = dtp_force_mode") + "\ndtp_result = { CODE = 30 }", sprite="GFX_dtp_btn_on")
x, y, w = grid(0, cols=1, row0=11)
lab("hm_noacc", "§RУ вас нет прав.§! Раздел «Доступ»: станьте ХОСТом или попросите права у ХОСТа.", x, y, w, potential=T(15, B("from", "NOT = { dtp_has_any_perm = yes }")))


# ---------- 16. Мастер игры: инструменты ведущего партии (право «Мастер игры», у ХОСТа — всегда)
area(16)
G1 = T(16, B("from", "NOT = { check_variable = { which = dtp_gmpage value >= 2 } }"))
G2 = T(16, B("from", chk("dtp_gmpage", 2)))
GM = lambda: need_perm("gm")
P = "event_target:dtp_p"
def monster(country, fleetname, ships):
    """Флот монстров как в игре (spawn_from_location_* из grand_archive_effects), у выбранной планеты."""
    body = "\n".join(B("while", "count = %d" % n, B("create_ship", 'design = "%s"' % d)) if n > 1 else B("create_ship", 'design = "%s"' % d) for d, n in ships)
    return B("if", B("limit", "exists = event_target:%s" % country),
             B("event_target:%s" % country, B("create_fleet", 'name = "%s"' % fleetname,
               B("effect", "set_owner = event_target:%s" % country, body, "set_location = %s" % P)))) + "\n" + \
           B("else", 'log = "DTP GM: no %s in this galaxy"' % country)
MON = [("amoeba", "Космические амёбы", monster("amoeba_country", "NAME_Space_Amoeba_plural", [("NAME_Small_Space_Organism_Orange", 2), ("NAME_Large_Space_Organism_Orange", 4)])),
       ("crystal", "Кристаллические сущности", monster("crystal_country", "NAME_Sapphire_Lurkers", [("NAME_Small_Crystal_Entity_Blue", 1), ("NAME_Medium_Crystal_Entity_Blue", 2), ("NAME_Large_Crystal_Entity_Blue", 4)])),
       ("tiyanki", "Стадо тиянки", monster("tiyanki_country", "NAME_Tiyanki_Space_Whale", [("NAME_Tiyanki_Cow", 1), ("NAME_Tiyanki_Bull", 2), ("NAME_Tiyanki_Calf", 4)])),
       ("afleet", "Флот державы A", B("create_military_fleet", "owner = event_target:dtp_t", "scaled_size = 0.5", B("effect", "set_location = %s" % P)))]
x, y, w = grid(0, cols=1)
lab("gm_h1", "§YУГРОЗЫ И ФЛОТЫ§!  §gпоявятся у выбранной планеты (окно планеты → «Выбрать»)§!", x, y, w, potential=G1)
for i, (k, n, body) in enumerate(MON):
    x, y, w = grid(i, cols=4, row0=1)
    button("gm_m_" + k, n, x, y, w, potential=G1, allow=GM() + "\n" + N_TP() + ("\n" + N_TC() if k == "afleet" else ""),
           effect=act("gm", body, 48), sprite="GFX_dtp_btn_warn" if k != "afleet" else "GFX_dtp_btn",
           tt="Создать у выбранной планеты: %s. Монстры появляются, только если такие существа есть в этой галактике (настройки при создании партии)." % n)
x, y, w = grid(0, cols=1, row0=2)
lab("gm_h2", "§YКАРТА И РАЗВЕДКА§!", x, y, w, potential=G1)
for i, (k, n, body, al, tt) in enumerate([
        ("map", "Открыть карту для A", B("event_target:dtp_t", "clear_uncharted_space = event_target:dtp_s"), N_TC() + "\n" + N_TP(), "Убрать «неизведанное» для A вокруг системы выбранной планеты."),
        ("intel", "Разведка A о B +100", B("event_target:dtp_t", "add_intel = { amount = 100 who = event_target:dtp_r }"), N_TC() + "\n" + N_RCP(), "A узнаёт о B: +100 разведданных."),
        ("comm", "Контакт A со всеми", B("event_target:dtp_t", B("every_country", B("limit", "dtp_listed_country = yes", "NOT = { is_same_value = prev }"),
            "establish_communications = prev")), N_TC(), "A устанавливает контакт со всеми державами галактики."),
        ("nebula", "Туманность у системы", B("event_target:dtp_s", B("create_nebula", "radius = 60")), N_TP(), "Создать туманность радиусом 60 вокруг системы выбранной планеты.")]):
    x, y, w = grid(i, cols=4, row0=3)
    button("gm_c_" + k, n, x, y, w, potential=G1, allow=GM() + "\n" + al, effect=act("gm", body, 49 if k != "nebula" else 55), tt=tt)
x, y, w = grid(0, cols=1, row0=4)
lab("gm_h3", "§YЛИДЕРЫ ДЕРЖАВЫ A§!", x, y, w, potential=G1)
LSP = B("event_target:dtp_t", B("owner_species", "save_event_target_as = dtp_lsp"))
for i, (k, n) in enumerate([("official", "Чиновник"), ("commander", "Командир"), ("scientist", "Учёный")]):
    x, y, w = grid(i, cols=4, row0=5)
    button("gm_l_" + k, "+ " + n + " (ур. 5)", x, y, w, potential=G1, allow=GM() + "\n" + N_TC(),
           effect=act("gm", LSP + "\n" + B("event_target:dtp_t", B("create_leader", "class = %s" % k, "species = event_target:dtp_lsp", "name = random", "skill = 5")), 50),
           tt="Создать державе A лидера класса «%s» 5-го уровня." % n)
x, y, w = grid(3, cols=4, row0=5)
button("gm_l_xp", "Опыт всем лидерам +1000", x, y, w, potential=G1, allow=GM() + "\n" + N_TC(),
       effect=act("gm", B("event_target:dtp_t", B("every_owned_leader", "add_experience = 1000")), 50))
x, y, w = grid(0, cols=1, row0=6)
lab("gm_h4", "§YПЛАНЕТА И СИСТЕМА§!  §gвыбранная планета§!", x, y, w, potential=G1)
for i, (k, n, body, al, code, tt) in enumerate([
        ("col", "Колония державы A здесь", LSP + "\n" + B(P, B("if", B("limit", "NOT = { exists = owner }"), "create_colony = { owner = event_target:dtp_t species = event_target:dtp_lsp }")),
            N_TC() + "\n" + N_TP(), 53, "Основать колонию A на выбранной незаселённой планете (основной вид A)."),
        ("cap", "Сделать столицей A", B(P, B("if", B("limit", "exists = owner", "owner = { is_same_value = event_target:dtp_t }"), "set_capital = yes")),
            N_TC() + "\n" + N_TP(), 51, "Перенести столицу A на выбранную планету (она должна принадлежать A)."),
        ("sb_up", "Станция системы → цитадель", B("event_target:dtp_s", B("if", B("limit", "exists = starbase"), B("starbase", "set_starbase_size = starbase_citadel"))),
            N_TP(), 54, "Поднять главную станцию системы выбранной планеты до цитадели."),
        ("sb_new", "Застава державы A", B("event_target:dtp_s", B("if", B("limit", "NOT = { exists = starbase }"), "create_starbase = { owner = event_target:dtp_t size = starbase_outpost }")),
            N_TC() + "\n" + N_TP(), 54, "Построить заставу A в ничьей системе выбранной планеты.")]):
    x, y, w = grid(i, cols=4, row0=7)
    button("gm_p_" + k, n, x, y, w, potential=G1, allow=GM() + "\n" + al, effect=act("gm", body, code), tt=tt)
x, y, w = grid(0, cols=1, row0=8)
lab("gm_h5", "§YСУДЬБЫ ДЕРЖАВ§!  §gнеобратимо — с подтверждением§!", x, y, w, potential=G1)
x, y, w = grid(0, cols=4, row0=9)
button("gm_storm", "Космический шторм", x, y, w, potential=G1, allow=GM(), effect=act("gm", "spawn_random_storm_weighted = yes", 55),
       tt="Запустить случайный космический шторм (нужно дополнение Cosmic Storms; без него ничего не произойдёт).")
x, y, w = grid(1, cols=4, row0=9)
button("gm_peace", "Сбросить отношения A со всеми", x, y, w, potential=G1, allow=GM() + "\n" + N_TC(),
       effect=act("gm", B("every_country", B("limit", "NOT = { is_same_value = event_target:dtp_t }"),
                          "clear_relations = { target = event_target:dtp_t relations = { defensive_pact migration_access } }"), 19),
       tt="Разорвать оборонительные пакты и миграционные договоры державы A со всеми.")
x, y, w = grid(2, cols=4, row0=9)
arm_btn("gm_kill", "Уничтожить державу A", x, y, 2 * w + 6, G1, GM() + "\n" + N_TC() + "\n" + N_FORCE() + "\n" +
        need("dtp_need_ai", "Нельзя уничтожить державу живого игрока", B("event_target:dtp_t", "is_ai = yes") if False else "dtp_tc_ai = yes"),
        "gm_kill", "Полностью удалить державу A из игры (только ИИ, принудительный режим).", sprite="GFX_dtp_btn_danger")
confirm("gm_kill_ok", "УНИЧТОЖИТЬ державу A — это необратимо", 15, G1, GM() + "\n" + N_FORCE(), "gm_kill",
        B("event_target:dtp_t", B("if", B("limit", "is_ai = yes"), "destroy_country = yes")), "gm", 52)
x, y, w = grid(0, cols=1, row0=10)
lab("gm_h6", "§YСИТУАЦИИ ИГРЫ§!  §gнастоящие ситуации Stellaris — появятся в журнале ситуаций державы§!", x, y, w, potential=G1)
for i, (k, n, body, al, tt) in enumerate([
        ("energy", "Энергетический кризис A", B("event_target:dtp_t", "start_situation = { type = situation_energy_deficit target = event_target:dtp_t }"), N_TC(), "Запустить у A ситуацию «дефицит энергии»."),
        ("food", "Голод у A", B("event_target:dtp_t", "start_situation = { type = situation_food_deficit target = event_target:dtp_t }"), N_TC(), "Запустить у A ситуацию «дефицит пищи»."),
        ("minerals", "Нехватка минералов A", B("event_target:dtp_t", "start_situation = { type = situation_mineral_deficit target = event_target:dtp_t }"), N_TC(), "Запустить у A ситуацию «дефицит минералов»."),
        ("revolt", "Восстание на планете", B(P, B("if", B("limit", "exists = owner"), B("owner", "start_situation = { type = situation_planetary_revolt target = %s }" % P))), N_TP(),
            "Запустить восстание на выбранной планете (у её владельца).")]):
    x, y, w = grid(i, cols=4, row0=11)
    button("gm_s_" + k, n, x, y, w, potential=G1, allow=GM() + "\n" + al, effect=act("gm", body, 55), sprite="GFX_dtp_btn_danger", tt=tt)


# страницы раздела
GMP = lambda pg: B("from", "NOT = { check_variable = { which = dtp_gmpage value >= 2 } }") if pg == 1 else B("from", chk("dtp_gmpage", pg))
for pg, n in [(1, "Угрозы"), (2, "Организатор"), (3, "Правила"), (4, "Сводка"), (5, "Сенат")]:
    xx = CX0 + CWF - (5 - pg + 1) * 100
    button("gm_pg%d_on" % pg, n, xx, 54, 96, 30, potential=T(16, GMP(pg)), sprite="GFX_dtp_btn_on")
    button("gm_pg%d" % pg, n, xx, 54, 96, 30, potential=T(16, "NOT = { %s }" % GMP(pg)), sprite="GFX_dtp_btn",
           effect=B("from", setv("dtp_gmpage", pg), B("if", B("limit", "NOT = { is_variable_set = dtp_ry }"), setv("dtp_ry", 5)) if pg == 3 else
           B("if", B("limit", "NOT = { is_variable_set = dtp_cst }"), setv("dtp_cst", 1)) if pg == 4 else ""))
# ---- страница 2: организатор партии
PLAYERS = lambda body: B("every_country", B("limit", "is_ai = no", "dtp_listed_country = yes"), body)
ANN = [(1101, "Перерыв", "Перерыв в игре", "Ведущий объявил перерыв. Игра на паузе — вернёмся примерно через 10 минут."),
       (1102, "Сохраняемся", "Сохранение и перезапуск", "Ведущий сохраняет партию и перезапускает сессию. Не выходите из лобби."),
       (1103, "Войны разрешены", "Войны игроков разрешены", "С этого момента игроки могут объявлять войны. Правило запрета войн больше не действует."),
       (1104, "Войны запрещены", "Войны игроков запрещены", "Войны игроков запрещены до особого объявления ведущего. §RПравило работает:§! кнопка «Объявить войну» заблокирована; если война всё же начнётся, все получат оповещение, а ведущий может наказать нарушителя."),
       (1105, "Предупреждение", "Предупреждение ведущего", "Ведущий напоминает о правилах партии. Повторное нарушение может привести к санкциям."),
       (1106, "Скоро конец сессии", "Сессия скоро закончится", "До конца сегодняшней сессии осталось немного времени. Завершайте дела."),
       (1107, "Следующая сессия", "Сессия окончена", "Сессия окончена. Сохранение у ХОСТа, продолжим в следующий раз в то же время."),
       (1108, "Игра окончена", "Игра окончена", "Партия завершена. Спасибо всем за игру!"),
       (1109, "Созыв сообщества", "Созыв Галактического сообщества", "Созывается Галактическое сообщество! Делегаты всех держав — к столу переговоров: обсуждаем резолюции и голосуем."),
       (1110, "Зайдите в войс", "Все в голосовой канал", "Ведущий просит всех игроков зайти в голосовой канал. Нужно обсудить важное."),
       (1111, "Голосование", "Голосование игроков", "Ведущий проводит голосование. Ответьте в голосовом канале или в чате партии."),
       (1112, "Саммит держав", "Дипломатический саммит", "Лидеры держав, соберитесь на саммит в голосовом канале для переговоров."),
       (1113, "Кризис близко", "Надвигается кризис", "Ведущий предупреждает: надвигается кризис галактического масштаба. Готовьте флоты и союзы."),
       (1114, "Ведущий отошёл", "Ведущий отошёл", "Ведущий ненадолго отошёл. Не начинайте войн и крупных операций до его возвращения."),
       (1115, "Ведущий вернулся", "Ведущий вернулся", "Ведущий снова в игре. Партия продолжается."),
       (1116, "Проверка готовности", "Проверка готовности", "Ведущий проверяет, все ли готовы продолжать. Ответьте кнопкой ниже — ведущий увидит ваш ответ.")]
x, y, w = grid(0, cols=1)
lab("go_h1", "§YОБЪЯВЛЕНИЯ ВСЕМ ИГРОКАМ§!  §gокно с текстом откроется у каждого игрока§!", x, y, w, potential=G2)
for i, (eid, n, t, d) in enumerate(ANN):
    x, y, w = grid(i, cols=4, row0=1)
    _rule = {1103: "remove_global_flag = dtp_rule_nopvp\nremove_global_flag = dtp_rule_forever\nremove_global_flag = dtp_rule_was",
             1104: "set_global_flag = dtp_rule_nopvp\nset_global_flag = dtp_rule_forever\nset_global_flag = dtp_rule_was"}.get(eid, "")
    _rtt = ""
    button("go_a%d" % eid, n, x, y, w, potential=G2, allow=GM(), effect=act("gm", (_rule + "\n" if _rule else "") + PLAYERS("country_event = { id = dtp.%d }" % eid), 13, False),
           sprite="GFX_dtp_ann_%d" % eid, tt="Показать всем игрокам окно «%s»: %s%s" % (t, d, _rtt))
x, y, w = grid(0, cols=1, row0=5)
lab("go_h2", "§YБАЛАНС ИГРОКОВ§!", x, y, w, potential=G2)
PACK = "add_resource = { energy = 5000 minerals = 5000 alloys = 2000 influence = 300 unity = 1000 }"
for i, (k, n, body, al, code, tt) in enumerate([
        ("pack_a", "Пакет поддержки A", B("event_target:dtp_t", PACK), N_TC(), 1, "A получает: 5000 энергии, 5000 минералов, 2000 сплавов, 300 влияния, 1000 единства."),
        ("pack_all", "Пакет поддержки всем игрокам", PLAYERS(PACK), "", 1, "Каждый живой игрок получает тот же пакет."),
        ("rep_all", "Ремонт всех флотов игроков", PLAYERS(B("every_owned_fleet", "repair_percentage = 1")), "", 16, "Полный ремонт всех флотов всех живых игроков."),
        ("tech_a", "A: технологии получателя B", B("event_target:dtp_t", "copy_techs_from = { target = event_target:dtp_r }"), N_TC() + "\n" + N_RCP(), 21, "Догоняющий: A получает все технологии, которые есть у B.")]):
    x, y, w = grid(i, cols=5, row0=6)
    button("go_" + k, n, x, y, w, potential=G2, allow=GM() + ("\n" + al if al else ""), effect=act("gm", body, code), tt=tt, sprite="GFX_dtp_btn_go")
# 10.9.1: все технологии игры — каждая со своим условием доступности (potential из файлов игры), без повторяемых и спецтехнологий
x, y, w = grid(4, cols=5, row0=6)
button("go_techall", "A: все технологии", x, y, w, potential=G2, allow=GM() + "\n" + N_TC(), effect=act("gm", B("event_target:dtp_t", "dtp_all_techs = yes"), 21), sprite="GFX_dtp_btn_warn",
       tt="Державе A — сразу все технологии игры, которые ей вообще доступны (как в её дереве исследований: машинам — машинные, биокораблям — био и т. п.). Без повторяемых, технологий павших империй и L-врат. Чтобы получить самому — в карточке сверху нажмите «Я».")
x, y, w = grid(0, cols=1, row0=7)
lab("go_h3", "§YМЕЖДУ ВСЕМИ ИГРОКАМИ§!  §gперемирие, знакомство, границы, отношения — сразу для всех живых игроков§!", x, y, w, potential=T(7))   # 10.7.9: перенесено в «Дипломатию»
for i, (k, n, body, code, tt) in enumerate([
        ("truce", "Перемирие всем игрокам", PLAYERS(B("every_country", B("limit", "is_ai = no", "dtp_listed_country = yes", "NOT = { is_same_value = prev }"),
            "set_truce = { target = prev type = war }")), 19, "Каждая пара живых игроков получает перемирие (как после войны)."),
        ("contact", "Все игроки знакомы", PLAYERS(B("every_country", B("limit", "is_ai = no", "dtp_listed_country = yes", "NOT = { is_same_value = prev }"),
            "establish_communications = prev")), 19, "Все живые игроки устанавливают контакт друг с другом."),
        ("open", "Открыть границы игрокам", PLAYERS(B("every_country", B("limit", "is_ai = no", "dtp_listed_country = yes", "NOT = { is_same_value = prev }"),
            "set_closed_borders = { who = prev status = no }")), 19, "Все игроки открывают границы друг для друга."),
        ("relmax", "Отношения игроков +100", PLAYERS(B("every_country", B("limit", "is_ai = no", "dtp_listed_country = yes", "NOT = { is_same_value = prev }"),
            "add_opinion_modifier = { modifier = dtp_opinion_good who = prev }")), 19, "Все игроки получают +100 к мнению друг о друге (затухает).")]):
    x, y, w = grid(i, cols=4, row0=8)
    button("go_" + k, n, x, y, w, potential=T(7), allow=GM() + "\n" + need("dtp_need_2pl", "Нужно минимум 2 живых игрока: эти кнопки действуют только МЕЖДУ игроками (в одиночной игре делать нечего)",
           "count_country = { limit = { is_ai = no dtp_listed_country = yes } count >= 2 }"), effect=act("gm", body, code), tt=tt)
x, y, w = grid(0, cols=1, row0=9)
lab("go_h4", "§YВОССТАНОВЛЕНИЕ ПОСЛЕ СБОЯ§!  §gдержава A§!", x, y, w, potential=G2)
for i, (k, n, body, al, code, tt) in enumerate([
        ("fix_rep", "Флоты A: полный ремонт", B("event_target:dtp_t", B("every_owned_fleet", "repair_percentage = 1")), N_TC(), 16, "Отремонтировать все флоты A."),
        ("fix_cd", "A: снять все откаты", B("event_target:dtp_t", "reset_policy_cooldowns = yes", "set_government_cooldown = no"), N_TC(), 28, "Снять откаты политик и правительства у A."),
        ("fix_mods", "A: снять бонусы Toolpack", B("event_target:dtp_t", *["remove_modifier = dtp_uc_%s" % k2 for k2, *_ in UMODS["c"]]), N_TC(), 31, "Убрать у A все модификаторы, выданные Toolpack."),
        ("fix_marks", "Снять все отметки систем", MK % "dtp_unmark_sys = yes" + "\n" + B("every_system", "dtp_star_fix = yes"), "", 36, "Вернуть всем отмеченным системам имя и звезду. Заодно чинит «застрявшие» красные и серые звёзды по всей галактике.")]):
    x, y, w = grid(i, cols=4, row0=10)
    button("go_" + k, n, x, y, w, potential=G2, allow=GM() + ("\n" + al if al else ""), effect=act("gm", body, code) + ("\ndtp_mlist = yes" if k == "fix_marks" else ""), tt=tt)
# ---- страница 2, последняя строка: состояние правила войн и переход на страницу «Правила партии»
RULE, VOPEN = "has_global_flag = dtp_rule_nopvp", "has_global_flag = dtp_viol_open"
G3 = T(16, B("from", chk("dtp_gmpage", 3)))
TOP3 = B("from", setv("dtp_gmpage", 3))
x, y, w = grid(0, cols=4, row0=11)
lab("go_r_off", "§gЗапрет войн для игроков:§! §Oне действует§!", x, y, 3 * w + 12, potential=G2 + "\nNOT = { %s }\nNOT = { %s }" % (RULE, VOPEN))
lab("go_r_on", "§gЗапрет войн для игроков:§! §GДЕЙСТВУЕТ — мод следит за войнами§!", x, y, 3 * w + 12, potential=G2 + "\n%s\nNOT = { %s }" % (RULE, VOPEN))
lab("go_r_v", "§RНАРУШЕНИЕ запрета войн — решите на странице «Правила партии»§!", x, y, 3 * w + 12, potential=G2 + "\n" + VOPEN)
x, y, w = grid(3, cols=4, row0=11)
button("go_r_go", "Правила партии →", x, y, w, potential=G2, effect=TOP3 + "\n" + B("from", B("if", B("limit", "NOT = { is_variable_set = dtp_ry }"), setv("dtp_ry", 5))), sprite="GFX_dtp_btn_go",
       tt="Срок запрета войн, его состояние и нарушения.")


# ---------- 16, страница 3: ПРАВИЛА ПАРТИИ — запрет войн для игроков со сроком
OWN = "exists = event_target:dtp_rule_owner"
x, y, w = grid(0, cols=1)
lab("gr_h1", "§YЗАПРЕТ ВОЙН§!  §gЖЁСТКИЙ — объявить войну нельзя, кнопка серая · МЯГКИЙ — можно, но это нарушение и ведущий наказывает§!", x, y, w, potential=G3)
x, y, w = grid(0, cols=1, row0=1)
lab("gr_st_off", "§gСейчас:§! §Oне действует§! §g— игроки могут воевать друг с другом§!", x, y, w - 430, potential=G3 + "\nNOT = { %s }" % RULE)
lab("gr_st_inf", "§gСейчас:§! §GДЕЙСТВУЕТ бессрочно§! §g— пока ведущий не снимет запрет§!", x, y, w - 430, potential=G3 + "\n%s\nhas_global_flag = dtp_rule_forever" % RULE)
lab("gr_st_t", "§gСейчас:§! §GДЕЙСТВУЕТ до [dtp_rule_owner.dtp_rule_endy] г.§! §g(лет: [dtp_rule_owner.dtp_rule_len]), потом снимется сам§!", x, y, w - 430,
    potential=G3 + "\n%s\nNOT = { has_global_flag = dtp_rule_forever }\n%s" % (RULE, OWN))
lab("gr_st_t2", "§gСейчас:§! §GДЕЙСТВУЕТ§! §g— на срок, выбранный ведущим; потом снимется сам§!", x, y, w - 430,
    potential=G3 + "\n%s\nNOT = { has_global_flag = dtp_rule_forever }\nNOT = { %s }" % (RULE, OWN))
button("gr_soft1", "Режим: МЯГКИЙ", x + w - 384, y, 220, potential=G3 + "\nhas_global_flag = dtp_war_soft", allow=GM(), sprite="GFX_dtp_btn_warn",
       effect=act("gm", "remove_global_flag = dtp_war_soft", 58, False) + "\ndtp_war_sync = yes",
       tt="§YСейчас МЯГКИЙ режим.§! Кнопка «Объявить войну» работает как обычно. Если держава под запретом всё-таки объявит войну — это нарушение: всем игрокам придёт окно, а ведущий на этой странице решает — наказать («Унижение» на 5 лет) или простить. Модификаторов запрета нет. §gНажмите — включить ЖЁСТКИЙ режим.§!")
button("gr_soft0", "Режим: ЖЁСТКИЙ", x + w - 384, y, 220, potential=G3 + "\nNOT = { has_global_flag = dtp_war_soft }", allow=GM(), sprite="GFX_dtp_btn_on",
       effect=act("gm", "set_global_flag = dtp_war_soft", 58, False) + "\ndtp_war_sync = yes",
       tt="§YСейчас ЖЁСТКИЙ режим.§! Как политика «Оборонительные войны», только политику менять не нужно: держава под запретом не может объявить войну никому — кнопка «Объявить войну» серая, причина — в подсказке. Запрет вписан в правило игры «можно ли объявить войну», его не обходят ни игроки, ни ИИ. Держава под запретом получает модификатор §R«Запрет войн ведущего»§!, держава под защитой — §G«Защита ведущего»§! (видны в модификаторах державы). §gНажмите — включить МЯГКИЙ режим.§!")
button("gr_ai1", "ИИ: тоже под запретом", x + w - 160, y, 160, potential=G3 + "\nhas_global_flag = dtp_war_ai", allow=GM(), sprite="GFX_dtp_btn_warn",
       effect=act("gm", "remove_global_flag = dtp_war_ai", 58, False),
       tt="Сейчас общий запрет касается и держав ИИ: они тоже не могут объявлять войны, а нападать на защищённые державы им тоже нельзя. Нажмите — запрет только для живых игроков.")
button("gr_ai0", "ИИ: не касается", x + w - 160, y, 160, potential=G3 + "\nNOT = { has_global_flag = dtp_war_ai }", allow=GM(),
       effect=act("gm", "set_global_flag = dtp_war_ai", 58, False),
       tt="Сейчас общий запрет касается только живых игроков: они не могут объявить войну никому — ни игрокам, ни ИИ. Державы ИИ воюют как обычно. Нажмите — запрет и для держав ИИ.")
x, y, w = grid(0, cols=1, row0=2)
lab("gr_h2", "§YВВЕСТИ ЗАПРЕТ НА СРОК§!  §gнаберите число лет — мышью или цифрами на клавиатуре (Backspace — стереть, Delete — очистить)§!", x, y, w, potential=G3)
def rule_on(n):
    """Ввести запрет. n = 0 — бессрочно; n = "var" — на число лет из поля ввода (переменная dtp_ry нажавшего).
    Таймер — сам флаг: истечёт без участия ведущего."""
    common = ["remove_global_flag = dtp_rule_nopvp", "set_global_flag = dtp_rule_was",
              B("from", "save_global_event_target_as = dtp_rule_owner")]
    if n == "var":
        body = common + ["remove_global_flag = dtp_rule_forever",
                         B("from", setv("dtp_ryd", "dtp_ry"), "multiply_variable = { which = dtp_ryd value = 360 }",
                           "set_timed_global_flag = { flag = dtp_rule_nopvp days = dtp_ryd }",
                           "export_trigger_value_to_variable = { trigger = years_passed variable = dtp_rule_endy }",
                           "change_variable = { which = dtp_rule_endy value = 2200 }", "change_variable = { which = dtp_rule_endy value = dtp_ry }",
                           setv("dtp_rule_len", "dtp_ry")),
                         PLAYERS("country_event = { id = dtp.1205 }")]
        return act("gm", B("if", B("limit", B("from", chk("dtp_ry", 1, ">="))), *body), 58, False) + "\ndtp_war_sync = yes"
    else:
        body = common + ["set_global_flag = dtp_rule_forever", "set_global_flag = dtp_rule_nopvp", PLAYERS("country_event = { id = dtp.1104 }")]
    return act("gm", "\n".join(body), 58, False) + "\ndtp_war_sync = yes"
# поле ввода срока + цифры (свои, на этой странице нет общей панели «Число»)
RY_MAX = 500
y3 = CY + 3 * ROW
button("gr_in", "  §Y[From.dtp_ry]§!  §gг.§!", CX0, y3 - 3, 170, 36, sprite="GFX_dtp_field", label=True, font="malgun_goth_24", potential=G3,
       tt="Срок запрета в годах (1–%d). Цифры на клавиатуре: ряд над буквами или Alt+цифра." % RY_MAX)
RYCAP = B("if", B("limit", chk("dtp_ry", RY_MAX, ">")), setv("dtp_ry", RY_MAX))
for i, d in enumerate([1, 2, 3, 4, 5, 6, 7, 8, 9, 0]):
    xx = CX0 + 178 + i * 46
    dig = B("from", "multiply_variable = { which = dtp_ry value = 10 }", "change_variable = { which = dtp_ry value = %d }" % d, RYCAP)
    button("gr_k%d" % d, str(d), xx, y3, 42, 30, shortcut=str(d), effect=dig, sprite="GFX_dtp_btn_key", potential=G3 + "\n" + B("from", "NOT = { has_country_flag = dtp_kbd_off }"))
    button("gr_q%d" % d, str(d), xx, y3, 42, 30, effect=dig, sprite="GFX_dtp_btn_key", potential=G3 + "\n" + B("from", "has_country_flag = dtp_kbd_off"))
    button("gr_a%d" % d, "", xx, y3, 1, 1, shortcut="alt+%d" % d, effect=dig, sprite="GFX_dtp_label", label=True, potential=G3)
xx = CX0 + 178 + 10 * 46
button("gr_bs", "← Стереть", xx, y3, 104, 30, shortcut="BACKSPACE", sprite="GFX_dtp_btn_key", potential=G3, tt="Backspace",
       effect=B("from", "divide_variable = { which = dtp_ry value = 10 }", "floor_variable = dtp_ry"))
button("gr_c", "C", xx + 110, y3, 46, 30, shortcut="DEL", sprite="GFX_dtp_btn_danger", potential=G3, tt="Очистить (Delete)", effect=B("from", setv("dtp_ry", 0)))
x, y, w = grid(0, cols=4, row0=4)
NRY = need("dtp_need_ry", "Наберите срок: от 1 до %d лет" % RY_MAX, B("from", chk("dtp_ry", 1, ">=")))
button("gr_onv", "Вся галактика: запрет на §Y[From.dtp_ry]§! г.", x, y, 2 * w + 6, potential=G3, allow=GM() + "\n" + NRY, effect=rule_on("var"), sprite="GFX_dtp_btn_go",
       tt="Запретить войны игроков на набранное число лет. По истечении срока запрет снимется сам и все игроки получат окно. Повторное нажатие задаёт новый срок с сегодняшнего дня.")
x, y, w = grid(2, cols=4, row0=4)
button("gr_on0", "Вся галактика: бессрочно", x, y, w, potential=G3, allow=GM(), effect=rule_on(0), sprite="GFX_dtp_btn_go",
       tt="Запретить войны игроков бессрочно — до тех пор, пока ведущий не снимет запрет.")
x, y, w = grid(3, cols=4, row0=4)
button("gr_off", "Снять общий запрет", x, y, w, potential=G3 + "\n" + RULE, allow=GM(), sprite="GFX_dtp_btn_danger",
       effect=act("gm", "\n".join(["remove_global_flag = dtp_rule_nopvp", "remove_global_flag = dtp_rule_forever", "remove_global_flag = dtp_rule_was",
                                   PLAYERS("country_event = { id = dtp.1103 }")]), 58, False) + "\ndtp_war_sync = yes",
       tt="Снять запрет сейчас — войны разрешены. Всем игрокам придёт окно «Войны игроков разрешены».")
lab("gr_off_x", "§gобщего запрета нет§!", x + 10, y + 3, w - 10, potential=G3 + "\nNOT = { %s }" % RULE)
# ---- личные правила для державы A: «не нападает на игроков» и «защита от нападения» (срок — из того же поля)
x, y, w = grid(0, cols=1, row0=5)
lab("gr_h4", "§YДЕРЖАВА A — ЛИЧНО§!  §gсрок — из поля выше, держава A — в карточке сверху; общий запрет при этом не нужен§!", x, y, w, potential=G3)
y6 = CY + 6 * ROW
per_k_label("gr_a", "§YA:§! [dtp_tc_#.GetName]", CX0, y6, 230, pot_extra=G3, tgt="dtp_tc", none_text="§gдержава A не выбрана§!")
for fl, xx, on_t, off_t in [("np", CX0 + 236, "§Rобъявлять войну нельзя§! §gдо [dtp_tc_#.dtp_np_endy]§!", "§gобъявлять войну: можно§!"),
                            ("prot", CX0 + 552, "§Gпод защитой§! §gдо [dtp_tc_#.dtp_prot_endy]§!", "§gзащиты от нападения нет§!")]:
    per_k_label("gr_%s_on" % fl, on_t, xx, y6, 310, pot_extra=G3 + "\ndtp_tc_hasflag = { F = dtp_rule_%s }" % fl, tgt="dtp_tc")
    lab("gr_%s_off" % fl, off_t, xx, y6, 310, potential=G3 + "\nNOT = { dtp_tc_hasflag = { F = dtp_rule_%s } }" % fl)
def personal(fl, ev):
    """Личное правило державе A на dtp_ry лет: временный флаг страны + год окончания для надписи."""
    return act("gm", B("if", B("limit", B("from", chk("dtp_ry", 1, ">="))),
        B("event_target:dtp_t", setv("dtp_ryd", "from.dtp_ry"), "multiply_variable = { which = dtp_ryd value = 360 }",
          "remove_country_flag = dtp_rule_%s" % fl, "set_timed_country_flag = { flag = dtp_rule_%s days = dtp_ryd }" % fl, "set_country_flag = dtp_rule_%s_was" % fl,
          "export_trigger_value_to_variable = { trigger = years_passed variable = dtp_%s_endy }" % fl,
          "change_variable = { which = dtp_%s_endy value = 2200 }" % fl, "change_variable = { which = dtp_%s_endy value = from.dtp_ry }" % fl,
          "save_global_event_target_as = dtp_rule_subj"),
        PLAYERS("country_event = { id = dtp.%d }" % ev)), 58) + "\ndtp_war_sync = yes"
for i, (fl, n, ev, tt) in enumerate([
        ("np", "A не объявляет войн: §Y[From.dtp_ry]§! г.", 1211, "Держава A не может объявлять войну никому на набранный срок. Если объявит — это нарушение: всем окно, здесь кнопки санкций. Все игроки получат окно о запрете."),
        ("prot", "Защита A: §Y[From.dtp_ry]§! г.", 1212, "На державу A нельзя нападать игрокам на набранный срок (например, защита новичка). Нападение — нарушение. Все игроки получат окно о защите.")]):
    x, y, w = grid(i, cols=3, row0=7)
    button("gr_p_" + fl, n, x, y, w, potential=G3, allow=GM() + "\n" + N_TC() + "\n" + NRY, effect=personal(fl, ev), sprite="GFX_dtp_btn_go", tt=tt)
x, y, w = grid(2, cols=3, row0=7)
button("gr_p_clr", "Снять с A личные правила", x, y, w, potential=G3 + "\nOR = { dtp_tc_hasflag = { F = dtp_rule_np } dtp_tc_hasflag = { F = dtp_rule_prot } }",
       allow=GM() + "\n" + N_TC(), sprite="GFX_dtp_btn_danger",
       effect=act("gm", B("event_target:dtp_t", *["remove_country_flag = dtp_rule_%s" % f for f in ("np", "prot", "np_was", "prot_was")],
                          "save_global_event_target_as = dtp_rule_subj") + "\n" + PLAYERS("country_event = { id = dtp.1215 }"), 58) + "\ndtp_war_sync = yes",
       tt="Снять с державы A запрет нападать и защиту. Всем игрокам придёт окно.")
lab("gr_p_clr_x", "§gу A нет личных правил§!", x + 10, y + 3, w - 10, potential=G3 + "\nNOT = { dtp_tc_hasflag = { F = dtp_rule_np } }\nNOT = { dtp_tc_hasflag = { F = dtp_rule_prot } }")
x, y, w = grid(0, cols=1, row0=8)
lab("gr_h3", "§YНАРУШЕНИЯ§!  §gкто напал на игрока вопреки общему запрету, личному запрету или защите§!", x, y, w, potential=G3)
x, y, w = grid(0, cols=4, row0=9)
VT = "exists = event_target:dtp_violator\nexists = event_target:dtp_victim"
lab("gr_none", "§gНарушений нет.§!", x, y, w * 4 + 18, potential=G3 + "\nNOT = { %s }" % VOPEN)
lab("go_r_viol", "§RНАРУШЕНИЕ:§! §Y[dtp_violator.GetName]§! → [dtp_victim.GetName] §g· раз: [dtp_violator.dtp_viol]§!", x, y, 2 * w + 6, potential=G3 + "\n%s\n%s" % (VOPEN, VT))
lab("go_r_viol2", "§RНАРУШЕНИЕ записано§! §g— держава уже не существует§!", x, y, 2 * w + 6, potential=G3 + "\n%s\nNOT = { AND = { %s } }" % (VOPEN, VT.replace("\n", " ")))
NVIOL = need("dtp_need_viol", "Нарушитель больше не существует", "exists = event_target:dtp_violator")
x, y, w = grid(2, cols=4, row0=9)
button("go_r_punish", "Унизить нарушителя (5 лет)", x, y, w, potential=G3 + "\n" + VOPEN, allow=GM() + "\n" + NVIOL, sprite="GFX_dtp_btn_danger",
       effect=act("gm", B("if", B("limit", "exists = event_target:dtp_violator"),
                          B("event_target:dtp_violator", "add_modifier = { modifier = humiliated days = 1800 }", "country_event = { id = dtp.1203 }"),
                          B("every_country", B("limit", "is_ai = no", "NOT = { is_same_value = event_target:dtp_violator }"), "country_event = { id = dtp.1208 }")) +
                  "\nremove_global_flag = dtp_viol_open", 5, False),
       tt="Наложить на нарушителя модификатор игры «Унижение» на 5 лет (влияние −33%, дипломатический вес −25%, одобрение −10%). Нарушитель получит окно с объяснением, остальные игроки — окно «Нарушитель наказан».")
x, y, w = grid(3, cols=4, row0=9)
button("go_r_forgive", "Простить и закрыть", x, y, w, potential=G3 + "\n" + VOPEN, allow=GM(),
       effect=act("gm", "remove_global_flag = dtp_viol_open\n" + B("if", B("limit", "exists = event_target:dtp_violator"), PLAYERS("country_event = { id = dtp.1209 }")), 57, False),
       tt="Закрыть нарушение без санкций — всем игрокам придёт окно «Нарушение прощено». Счётчик нарушений державы сохраняется.")
for i, t in enumerate(["§gЖёсткий режим: кнопка «Объявить войну» серая. Мягкий: объявить можно, но это нарушение — всем окно, здесь санкции.§!",
                       "§gВойны с ИИ нарушением не считаются, пока справа сверху не выбрано «ИИ: тоже под запретом». Начатую войну скрипт не останавливает.§!"]):
    x, y, w = grid(0, cols=1, row0=10 + i)
    lab("gr_how%d" % (i + 2), t, x, y, w, potential=G3)

# ---------- 16, страница 4: СВОДКА ИГРОКОВ (снимок по кнопке), НАСТРОЙКИ ПАРТИИ, КРИЗИСЫ, ТАЙМЕР СЕССИИ
G4 = T(16, B("from", chk("dtp_gmpage", 4)))
SB_N, SB_H = 7, 26
SBVIS = lambda k: B("from", chk("dtp_sbv", k)) if k else "NOT = { %s }" % B("from", chk("dtp_sbv", 1, ">="))
SBFIX = [("fp", "Флот", "fleet_power", ""), ("dw", "Дип. вес", "diplomacy_weight", "")]      # видны всегда
INC = lambda v, n, r: (v, n, "has_monthly_income", "resource = %s" % r)
STK = lambda v, n, r: (v, n, "has_resource", "resource = %s" % r)
SBCOLS = [("tech", "Техн.", "num_researched_techs", ""), ("ap", "Перки", "num_ascension_perks", ""), ("col", "Колонии", "num_owned_planets", ""),
          ("sys", "Системы", "num_starbases", ""), ("nav", "Лимит", "used_naval_capacity_integer", ""), ("size", "Размер", "empire_size", ""),
          ("comm", "Конт.", "num_communications", "")]
SBCOLS2 = [INC("en", "Энергия", "energy"), INC("i_mi", "Минер.", "minerals"), INC("i_fo", "Пища", "food"), INC("al", "Сплавы", "alloys"),
           INC("i_cg", "Товары", "consumer_goods"), INC("inf", "Влияние", "influence"), INC("un", "Единство", "unity")]
SBCOLS3 = [("sc", "Наука", None, ""), INC("i_vm", "Пыль", "volatile_motes"), INC("i_eg", "Газы", "exotic_gases"), INC("i_rc", "Крист.", "rare_crystals"),
           INC("i_dm", "Т.мат.", "sr_dark_matter"), INC("i_zr", "Зро", "sr_zro"), INC("i_lm", "Ж.мет.", "sr_living_metal")]
SBCOLS4 = [STK("s_en", "Энергия", "energy"), STK("s_mi", "Минер.", "minerals"), STK("s_fo", "Пища", "food"), STK("s_al", "Сплавы", "alloys"),
           STK("s_cg", "Товары", "consumer_goods"), STK("s_in", "Влияние", "influence"), STK("s_un", "Единство", "unity")]
SBSETS = [SBCOLS, SBCOLS2, SBCOLS3, SBCOLS4]
SBFULL = {"fp": "Мощь всех военных флотов (как в игре)", "dw": "Дипломатический вес державы", "tech": "Изучено технологий", "ap": "Взято перков возвышения",
          "col": "Колоний (планеты и корабли-колонии)", "sys": "Систем: станций и застав", "nav": "Занятый флотский лимит", "size": "Размер империи (разрастание)",
          "comm": "Установлено контактов", "sc": "Наука в месяц: физика + социология + инженерия", "i_vm": "Летучая пыль в месяц", "i_eg": "Экзотические газы в месяц",
          "i_rc": "Редкие кристаллы в месяц", "i_dm": "Тёмная материя в месяц", "i_zr": "Зро в месяц", "i_lm": "Живой металл в месяц"}
SBNAMES = ["Развитие", "Доход в месяц", "Наука и редкие в месяц", "Запасы на складе"]
SBSHORT = ["Развитие", "Доход/мес", "Наука, редкие", "Запасы"]
def sb_export(v, trig, par, var=None):
    return "export_trigger_value_to_variable = { trigger = %s %svariable = %s rounded = yes }" % (trig, ("parameters = { %s } " % par) if par else "", var or "dtp_sb_" + v)
SCI = [sb_export("", "has_monthly_income", "resource = %s_research" % r, "dtp_sb_t%d" % k) for k, r in enumerate(("physics", "society", "engineering"))] + \
      [setv("dtp_sb_sc", "dtp_sb_t0"), "change_variable = { which = dtp_sb_sc value = dtp_sb_t1 }", "change_variable = { which = dtp_sb_sc value = dtp_sb_t2 }"]
SB_REFRESH = "\n".join(
    [B("if", B("limit", "exists = event_target:dtp_sb_%d" % i), "clear_global_event_target = dtp_sb_%d" % i) for i in range(1, SB_N + 2)] +
    [B("from", setv("dtp_sbn", 0), "save_global_event_target_as = dtp_sb_owner",
       "export_trigger_value_to_variable = { trigger = years_passed variable = dtp_sb_y }", "change_variable = { which = dtp_sb_y value = 2200 }",
       "get_galaxy_setup_value = { which = dtp_g_end setting = end_game_year }", "get_galaxy_setup_value = { which = dtp_g_vic setting = victory_year }",
       "get_galaxy_setup_value = { which = dtp_g_cs setting = crisis_strength_scale }"),
     B("every_country", B("limit", "OR = { is_ai = no has_global_flag = dtp_sb_ai }", "dtp_listed_country = yes", "is_country_type = default"),
       setv("dtp_sb_t0", 0), setv("dtp_sb_t1", 0), setv("dtp_sb_t2", 0),
       *[sb_export(v, t_, pr) for v, _, t_, pr in SBFIX + SBCOLS + SBCOLS2 + SBCOLS3 + SBCOLS4 if t_], *SCI,
       B("from", "change_variable = { which = dtp_sbn value = 1 }", setv("dtp_sbk", "dtp_sbn"), "subtract_variable = { which = dtp_sbk value = dtp_sbo }"),
       setv("dtp_sb_no", "from.dtp_sbn"),
       # 10.7.9: прокрутка — строка i показывает державу номер dtp_sbo + i
       *[B("if", B("limit", B("from", chk("dtp_sbk", i))), "save_global_event_target_as = dtp_sb_%d" % i) for i in range(1, SB_N + 2)])])
SB_TOP = B("from", setv("dtp_sbo", 0))
x, y, w = grid(0, cols=1)
for k in range(4):
    lab("sb_h%d" % k, "§YСВОДКА ИГРОКОВ§!  §g· %s§!" % SBNAMES[k].lower(), x, y, w, potential=G4 + "\n" + SBVIS(k))
lab("sb_when", "§gснимок: [dtp_sb_owner.dtp_sb_y] г.§!", x + w - 456, y, 130, potential=G4 + "\nexists = event_target:dtp_sb_owner")
for k in range(4):
    nk = (k + 1) % 4
    button("sb_v%d" % k, "⇄ %s" % SBSHORT[nk], x + w - 322, y - 2, 158, potential=G4 + "\n" + SBVIS(k), effect=B("from", setv("dtp_sbv", nk)),
           tt="Сейчас: «%s». Нажмите, чтобы показать «%s». Флот и дипломатический вес видны всегда; наборы: развитие → доход в месяц → наука и редкие ресурсы → запасы на складе." % (SBNAMES[k], SBNAMES[nk]))
button("sb_refresh", "↻ Обновить", x + w - 160, y - 2, 160, potential=G4, allow=GM(), effect=act("gm", SB_TOP + "\n" + SB_REFRESH, 59, False), sprite="GFX_dtp_btn_go",
       tt="Собрать свежие цифры по всем живым игрокам (все четыре набора столбцов) и настройки партии.")
CXN, CWN_ = CX0 + 4, 190
FXW, COLW = 74, 66
CX1 = CXN + CWN_ + len(SBFIX) * FXW + 6          # начало сменных столбцов
yh = CY + ROW
lab("sb_c_name", "§gДержава§!", CXN, yh, CWN_, potential=G4)
for j, (v, n, _, _) in enumerate(SBFIX):
    button("sb_c_" + v, "§Y%s§!" % n, CXN + CWN_ + j * FXW, yh, FXW - 4, 24, potential=G4, sprite="GFX_dtp_label", label=True, tt=SBFULL.get(v))
for cols, vis in ((c_, SBVIS(k)) for k, c_ in enumerate(SBSETS)):
    for j, (v, n, _, _) in enumerate(cols):
        button("sb_c_" + v, "§g%s§!" % n, CX1 + j * COLW, yh, COLW - 4, 24, potential=G4 + "\n" + vis, sprite="GFX_dtp_label", label=True, tt=SBFULL.get(v))
for i in range(1, SB_N + 1):
    yy = CY + ROW + 30 + (i - 1) * SB_H
    pe = G4 + "\nexists = event_target:dtp_sb_%d" % i
    lab("sb_%d_n" % i, "[dtp_sb_%d.dtp_sb_no]. §Y[dtp_sb_%d.GetName]§!" % (i, i), CXN, yy, CWN_ - 6, potential=pe)
    for j, (v, n, _, _) in enumerate(SBFIX):
        lab("sb_%d_%s" % (i, v), "§Y[dtp_sb_%d.dtp_sb_%s]§!" % (i, v), CXN + CWN_ + j * FXW, yy, FXW - 4, potential=pe)
    for cols, vis in ((c_, SBVIS(k)) for k, c_ in enumerate(SBSETS)):
        for j, (v, n, _, _) in enumerate(cols):
            lab("sb_%d_%s" % (i, v), "[dtp_sb_%d.dtp_sb_%s]" % (i, v), CX1 + j * COLW, yy, COLW - 4, potential=pe + "\n" + vis)
    button("sb_%d_a" % i, "→ A", CX1 + 7 * COLW + 2, yy - 2, 52, 24, potential=pe,
           effect=INIT + "\n" + B("event_target:dtp_sb_%d" % i, "dtp_set_tc = yes") + "\ndtp_result = { CODE = 29 }",
           tt="Сделать эту державу целью A (карточка сверху) — например, чтобы дать пакет поддержки или взять под защиту.")

lab("sb_empty", "§gНажмите «Обновить», чтобы собрать цифры по игрокам.§!", CXN, CY + ROW + 30, 600, potential=G4 + "\nNOT = { exists = event_target:dtp_sb_1 }")
x, y, w = grid(0, cols=1, row0=7)
lab("sb_galaxy", "§gкризис§! §Y[dtp_sb_owner.dtp_g_end]§! §g· победа§! §Y[dtp_sb_owner.dtp_g_vic]§! §g· сила§! ×§Y[dtp_sb_owner.dtp_g_cs]§!",
    x, y + 4, 314, potential=G4 + "\nexists = event_target:dtp_sb_owner")
button("sb_up", "← Выше", x + 318, y, 76, 30, potential=G4 + "\n" + B("from", chk("dtp_sbo", 0, ">")), allow=GM(),
       effect=act("gm", B("from", "subtract_variable = { which = dtp_sbo value = %d }" % SB_N, B("if", B("limit", chk("dtp_sbo", 0, "<")), setv("dtp_sbo", 0))) + "\n" + SB_REFRESH, 59, False),
       tt="Показать предыдущие %d держав." % SB_N)
button("sb_down", "Ниже →", x + 398, y, 76, 30, potential=G4 + "\nexists = event_target:dtp_sb_%d" % (SB_N + 1), allow=GM(),
       effect=act("gm", B("from", "change_variable = { which = dtp_sbo value = %d }" % SB_N) + "\n" + SB_REFRESH, 59, False),
       tt="Показать следующие %d держав." % SB_N)
button("sb_ai_on", "ИИ в сводке: показаны", x + w - 392, y, 180, potential=G4 + "\nhas_global_flag = dtp_sb_ai", allow=GM(), sprite="GFX_dtp_btn_on",
       effect=act("gm", "remove_global_flag = dtp_sb_ai\n" + SB_TOP + "\n" + SB_REFRESH, 59, False), tt="Сейчас в сводке игроки и ИИ-державы. Нажмите, чтобы оставить только игроков (сводка обновится).")
button("sb_ai_off", "ИИ в сводке: скрыты", x + w - 392, y, 180, potential=G4 + "\nNOT = { has_global_flag = dtp_sb_ai }", allow=GM(),
       effect=act("gm", "set_global_flag = dtp_sb_ai\n" + SB_TOP + "\n" + SB_REFRESH, 59, False), tt="Сейчас в сводке только живые игроки. Нажмите, чтобы добавить и ИИ-державы (удобно для проверки в одиночной игре; сводка обновится).")
button("sb_meet", "Ведущий: контакт со всеми", x + w - 206, y, 206, potential=G4, allow=GM(),
       effect=act("gm", B("every_country", B("limit", "is_country_type = default", "NOT = { is_same_value = from }"), "establish_communications_no_message = from"), 59, False),
       tt="Вместо «Неизвестная держава» будут видны названия: держава ведущего устанавливает контакт со всеми державами галактики. Это игровое действие — откроет ведущему знакомство со всеми.")
# ---- кризисы конца игры: запуск (с подтверждением, через 2 дня — проверка) и сила кризиса
x, y, w = grid(0, cols=1, row0=8)
lab("cr_h", "§YКРИЗИСЫ КОНЦА ИГРЫ§!  §gнеобратимо — с подтверждением; через 2 дня ведущему придёт окно: начался ли кризис§!", x, y, w, potential=G4)
_CR_EV = []
CRISES = [("pre", "Преторины", "crisis.10", "OR = { has_global_flag = prethoryn_invasion_happened has_global_flag = ongoing_prethoryn_invasion any_country = { is_country_type = swarm } }", 1221, ""),
          ("unb", "Незваные", "crisis.1000", "OR = { has_global_flag = extradimensional_invasion_happened any_country = { is_country_type = extradimensional } }", 1223, ""),
          ("con", "Контингенция", "crisis.2005", "OR = { has_global_flag = ai_invasion_happened any_country = { is_country_type = ai_empire } }", 1225, ""),
          ("cet", "Цетана", "crisis.8005", "OR = { has_global_flag = synth_queen_happened any_country = { is_country_type = synth_queen } any_country = { is_country_type = awakened_synth_queen } }", 1227, ""),
          ("khan", "Великий хан", "marauder.500", "OR = { has_global_flag = marauder_crisis_started has_global_flag = marauder_crisis_ongoing any_country = { is_country_type = awakened_marauders } }", 1229,
           "dormant_marauders")]
for i, (k, n, ev, flag, chk_ev, scope_type) in enumerate(CRISES):
    x, y, w = CX0 + i * 122, CY + 9 * ROW, 118
    arm_btn("cr_" + k, n, x, y, w, G4, GM() + ("\n" + need("dtp_need_khan", "В галактике нет спящих мародёров", "any_country = { is_country_type = dormant_marauders }") if scope_type else "")
            + "\n" + need("dtp_need_cr_started", "Этот кризис уже запущен — второй раз игра его не запускает", "NOT = { %s }" % flag)
            + ("\n" + need("dtp_need_dlc_ma", "Нужно дополнение The Machine Age — без него игра этот кризис не запускает", "has_machine_age_dlc = yes") if k == "cet" else "")
            + ("" if ev else "\n" + need("dtp_need_cr_ev", "Номер события этого кризиса в игре 4.5.2 ещё не найден — кнопка временно выключена. Пришлите автору мода файлы events/*.txt, где упоминается этот кризис.", "always = no")),
            "cr_" + k, ("Запустить кризис «%s» (событие игры %s%s). Работает так же, как консольная команда «event %s»." % (n, ev, ", от имени спящих мародёров" if scope_type else "", ev)) if ev else "Кризис «%s»: номер события в игре 4.5.2 ещё не найден — кнопка временно выключена." % n, sprite="GFX_dtp_btn_danger")
    confirm("cr_%s_ok" % k, "запустить кризис «%s» — его нельзя отменить" % n, 0, G4, GM(), "cr_" + k,
            "\n".join(['log = "DTP CRISIS: firing %s (%s)"' % (ev, k)] + ([] if not ev else [
                       ("set_global_flag = horde_triggered   # как в самой игре (marauder_events.txt): иначе marauder.500 молча не сработает до середины партии\n" +
                         B("random_country", B("limit", "is_country_type = %s" % scope_type), "country_event = { id = %s }" % ev) if scope_type
                        else B("from", "country_event = { id = %s }" % ev)),
                       B("from", "country_event = { id = dtp.%d days = 2 }" % chk_ev, "country_event = { id = dtp.%d days = 2 }" % (chk_ev + 1))])), "gm", 61)
    _CR_EV.append(B("country_event", "id = dtp.%d" % chk_ev, "title = %s" % loc("dtp.%d.name" % chk_ev, "§Y«ВЕДУЩИЙ»§! Кризис запущен"),
        "desc = %s" % loc("dtp.%d.desc" % chk_ev, "Проверка Debug Toolpack: кризис «%s» §Gначался§! — в игре появились его признаки.\\n\\n§gСообщение видит только ведущий.§!" % n),
        "picture = GFX_evt_dtp_ann_1113", "is_triggered_only = yes", B("trigger", flag),
        B("immediate", 'log = "DTP CRISIS: %s OK"' % k), B("option", "name = %s" % loc("dtp.%d.o0" % chk_ev, "Понятно"))))
    _CR_EV.append(B("country_event", "id = dtp.%d" % (chk_ev + 1), "title = %s" % loc("dtp.%d.name" % (chk_ev + 1), "§Y«ВЕДУЩИЙ»§! Кризис не обнаружен"),
        "desc = %s" % loc("dtp.%d.desc" % (chk_ev + 1), "Проверка Debug Toolpack: признаков кризиса «%s» пока §Oнет§!. Возможно, игра не разрешает его сейчас (условия события, настройки партии, уже был другой кризис) или номер события в этой версии другой.\\n\\nПришлите автору мода game.log (строки DTP CRISIS) и файлы events/crisis_*.txt из папки игры.\\n\\n§gСообщение видит только ведущий.§!" % n),
        "picture = GFX_evt_dtp_ann_1105", "is_triggered_only = yes", B("trigger", "NOT = { %s }" % flag),
        B("immediate", 'log = "DTP CRISIS: %s NOT DETECTED"' % k), B("option", "name = %s" % loc("dtp.%d.o0" % (chk_ev + 1), "Понятно"))))
CSU = lambda f: act("gm", "\n".join([B("if", B("limit", "NOT = { exists = event_target:dtp_cs_owner }"), B("from", "save_global_event_target_as = dtp_cs_owner", setv("dtp_cs_mult", 1))),
    "multiply_crisis_strength = %s" % f,
    B("event_target:dtp_cs_owner", "multiply_variable = { which = dtp_cs_mult value = %s }" % f,
      "get_galaxy_setup_value = { which = dtp_cs_base setting = crisis_strength_scale }", setv("dtp_cs_eff", "dtp_cs_base"), "multiply_variable = { which = dtp_cs_eff value = dtp_cs_mult }")]), 61, False)
# сила кризиса: ведущий выбирает желаемую ИТОГОВУЮ силу (как в настройках партии: 1 = обычная), мод подбирает множитель.
# Игра умеет только умножать силу (multiply_crisis_strength), поэтому шаги ×2/×0.5, затем ×1.25/×0.8 — итог около ±10% от цели.
def cs_apply(des_from_field):
    own = ["get_galaxy_setup_value = { which = dtp_cs_base setting = crisis_strength_scale }",
           (setv("dtp_cs_des", "from.dtp_cst") + "\ndivide_variable = { which = dtp_cs_des value = dtp_cs_base }") if des_from_field else setv("dtp_cs_des", 1)]
    def step(f, cmp_f, op, rel):
        # пока mult*f [op] des*rel: умножить силу на f
        return B("while", "count = 40",
                 setv("dtp_cs_t", "dtp_cs_mult"), "multiply_variable = { which = dtp_cs_t value = %s }" % cmp_f,
                 setv("dtp_cs_d", "dtp_cs_des"), "multiply_variable = { which = dtp_cs_d value = %s }" % rel,
                 B("if", B("limit", "check_variable = { which = dtp_cs_t value %s dtp_cs_d }" % op),
                   "multiply_crisis_strength = %s" % f, "multiply_variable = { which = dtp_cs_mult value = %s }" % f))
    own += [step("2", "2", "<=", "1"), step("0.5", "1", ">=", "2"), step("1.25", "1.25", "<=", "1.1"), step("0.8", "1", ">=", "1.125"),
            setv("dtp_cs_eff", "dtp_cs_base"), "multiply_variable = { which = dtp_cs_eff value = dtp_cs_mult }"]
    return act("gm", "\n".join([B("if", B("limit", "NOT = { exists = event_target:dtp_cs_owner }"), B("from", "save_global_event_target_as = dtp_cs_owner", setv("dtp_cs_mult", 1))),
                                 B("from", B("if", B("limit", "NOT = { is_variable_set = dtp_cst }"), setv("dtp_cst", 1))),
                                 B("event_target:dtp_cs_owner", *own), 'log = "DTP CRISIS: strength set"']), 61, False)
CSX = CX0 + 5 * 122
CSTI = B("from", B("if", B("limit", "NOT = { is_variable_set = dtp_cst }"), setv("dtp_cst", 1)))
button("cr_m", "−", CSX, CY + 9 * ROW, 30, potential=G4, sprite="GFX_dtp_btn_key", tt="Уменьшить желаемую силу кризиса на 0.25.",
       effect=CSTI + "\n" + B("from", "change_variable = { which = dtp_cst value = -0.25 }", B("if", B("limit", chk("dtp_cst", 0.25, "<")), setv("dtp_cst", 0.25))))
button("cr_v", "§Y×[From.dtp_cst]§!", CSX + 34, CY + 9 * ROW, 66, 30, sprite="GFX_dtp_field", label=True, potential=G4,
       tt="Желаемая итоговая сила кризиса: 1 — как в обычной игре, 2 — вдвое сильнее, 0.5 — вдвое слабее. Меняйте кнопками − и +, затем «Задать силу».")
button("cr_p", "+", CSX + 104, CY + 9 * ROW, 30, potential=G4, sprite="GFX_dtp_btn_key", tt="Увеличить желаемую силу кризиса на 0.25.",
       effect=CSTI + "\n" + B("from", "change_variable = { which = dtp_cst value = 0.25 }", B("if", B("limit", chk("dtp_cst", 10, ">")), setv("dtp_cst", 10))))
button("cr_set", "Задать силу", CSX + 138, CY + 9 * ROW, CWF - 5 * 122 - 138, potential=G4, allow=GM(), effect=cs_apply(True), sprite="GFX_dtp_btn_warn",
       tt="Сделать итоговую силу кризиса примерно равной выбранному числу (точность около ±10%: игра умеет только умножать силу). Действует на текущий и будущие кризисы.")
x, y, w = grid(0, cols=1, row0=10)
CRNOW = [("swarm", "Преторины"), ("extradimensional", "Незваные"), ("ai_empire", "Контингенция"), ("synth_queen", "Цетана"), ("awakened_synth_queen", "Цетана"),
         ("gray_goo", "Серая буря"), ("awakened_marauders", "Великий хан")]
seen = set()
for ct, n in CRNOW:
    if n in seen: continue
    seen.add(n); cts = [c for c, nn in CRNOW if nn == n]
    lab("cr_now_" + ct, "§gСейчас:§! §Rидёт кризис «%s»§!" % n, x, y + 2, 330, potential=G4 + "\n" + B("OR", *["any_country = { is_country_type = %s }" % c for c in cts]))
lab("cr_now_none", "§gСейчас:§! §Gкризисов нет§!", x, y + 2, 330, potential=G4 + "\nNOT = { any_country = { OR = { %s } } }" % " ".join("is_country_type = %s" % c for c, _ in CRNOW))
button("cr_reset", "↺ Как в настройках", x + w - 150, y, 150, potential=G4 + "\nexists = event_target:dtp_cs_owner", allow=GM(), effect=cs_apply(False),
       tt="Вернуть силу кризиса к значению из настроек партии (снять множитель Toolpack).")
lab("cr_str", "§gСила:§! ×[dtp_cs_owner.dtp_cs_base] настр. · ×[dtp_cs_owner.dtp_cs_mult] Toolpack = §Y×[dtp_cs_owner.dtp_cs_eff]§!", x + 336, y + 2, w - 336 - 156,
    potential=G4 + "\nexists = event_target:dtp_cs_owner")
lab("cr_str0", "§gСила кризиса:§! как в настройках партии §g(Toolpack не менял)§!", x + 336, y + 2, w - 336, potential=G4 + "\nNOT = { exists = event_target:dtp_cs_owner }")

# ---- таймер сессии: «через N лет — конец сессии», за месяц — предупреждение
ys = CY + 11 * ROW
button("ss_h", "§YТАЙМЕР СЕССИИ§!", CX0, ys + 3, 150, 24, potential=G4, sprite="GFX_dtp_label", label=True,
       tt="Конец сессии через выбранный срок игрового времени. За месяц до конца всем игрокам — предупреждение, в конце — окно «Сессия окончена: ставим паузу и сохраняемся».")
SX0 = CX0 + 152
SESS = "has_global_flag = dtp_sess"
def sess_on(months):
    return act("gm", "\n".join(["remove_global_flag = dtp_sess", "remove_global_flag = dtp_sess_warn",
        "set_timed_global_flag = { flag = dtp_sess days = %d }" % (months * 30),
        "set_timed_global_flag = { flag = dtp_sess_warn days = %d }" % (months * 30 - 30), "set_global_flag = dtp_sess_was", "set_global_flag = dtp_sess_warn_was",
        B("from", "save_global_event_target_as = dtp_sess_owner", "export_trigger_value_to_variable = { trigger = years_passed variable = dtp_sess_y }",
          "change_variable = { which = dtp_sess_y value = %d }" % (2200 + months // 12), setv("dtp_sess_m", months)),
        PLAYERS("country_event = { id = dtp.1216 }")]), 60, False)
for i, (mo, n) in enumerate([(12, "1 год"), (24, "2 года"), (36, "3 года"), (48, "4 года"), (60, "5 лет")]):
    button("ss_%d" % mo, n, SX0 + i * 96, ys, 90, 30, potential=G4, allow=GM(), effect=sess_on(mo), sprite="GFX_dtp_btn_go",
           tt="Сессия закончится через %s игрового времени. Всем игрокам придёт окно с годом окончания." % n)
button("ss_off", "✕ Отменить (до [dtp_sess_owner.dtp_sess_y] г.)", SX0 + 5 * 96, ys, CWF - 152 - 5 * 96, 30, potential=G4 + "\n" + SESS + "\nexists = event_target:dtp_sess_owner", allow=GM(), sprite="GFX_dtp_btn_danger",
       tt="Таймер идёт: сессия закончится примерно в указанном году. Нажмите, чтобы отменить.",
       effect=act("gm", "\n".join(["remove_global_flag = dtp_sess", "remove_global_flag = dtp_sess_warn", "remove_global_flag = dtp_sess_was", "remove_global_flag = dtp_sess_warn_was"]), 60, False))
lab("ss_st_off", "§gтаймер не запущен§!", SX0 + 5 * 96 + 10, ys + 3, 300, potential=G4 + "\nNOT = { %s }" % SESS)

# ---------- 16, страница 5: СЕНАТ — Галактическое сообщество
# Игра сама ведёт заседания и голосования (команды «начать голосование» в 4.5 нет). Ведущий объявляет начало/конец заседания,
# может сразу принять текущую резолюцию (тип ищется перебором всех резолюций игры) и управляет Советом и Хранителем.
G5 = T(16, B("from", chk("dtp_gmpage", 5)))
RES_KEYS = []
for _f in sorted(glob.glob(os.path.join(VC, "resolutions", "*.txt"))):
    if "README" in _f: continue
    RES_KEYS += re.findall(r"^([a-z][a-z0-9_]*) = \{", open(_f, encoding="utf-8-sig").read(), re.M)
RES_KEYS = [k for k in dict.fromkeys(RES_KEYS) if k.startswith("resolution_")]   # «any = {» в 00_resolutions — не резолюция
_pc = [B("if" if i == 0 else "else_if", B("limit", "is_voting_on_resolution = %s" % r), "pass_resolution = %s" % r, 'log = "DTP SENATE: passed %s"' % r)
       for i, r in enumerate(RES_KEYS)]
EFF.append(B("dtp_gc_pass_current", *_pc))
_cc = [B("if" if i == 0 else "else_if", B("limit", "is_voting_on_resolution = %s" % r), "cancel_resolution = %s" % r, 'log = "DTP SENATE: rejected %s"' % r)
       for i, r in enumerate(RES_KEYS)]
EFF.append(B("dtp_gc_reject_current", *_cc))
GCM = lambda: need("dtp_need_gc", "Галактическое сообщество ещё не создано", "is_galactic_community_formed = yes")
GCV = lambda: need("dtp_need_gcvote", "Сейчас в Галактическом сообществе нет голосования", "is_voting_on_resolution = any")
SESS_ON = "has_global_flag = dtp_gc_session"
x, y, w = grid(0, cols=1)
lab("se_h", "§YСЕНАТ — ГАЛАКТИЧЕСКОЕ СООБЩЕСТВО§!  §gрабочие кнопки; голосования по расписанию ведёт игра§!", x, y, w, potential=G5)
for i, (k, on, off, cond) in enumerate([("gc", "§gСообщество:§! §Gсоздано§!", "§gСообщество:§! §Oнет§!", "is_galactic_community_formed = yes"),
                                        ("v", "§gГолосование:§! §Yидёт§!", "§gГолосование:§! §gнет§!", "is_voting_on_resolution = any"),
                                        ("c", "§gСовет:§! §Gсоздан§!", "§gСовет:§! §gнет§!", "is_galactic_council_established = yes")]):
    x, y, w = grid(i, cols=4, row0=1)
    lab("se_s_%s1" % k, on, x, y + 2, w, potential=G5 + "\n" + cond)
    lab("se_s_%s0" % k, off, x, y + 2, w, potential=G5 + "\nNOT = { %s }" % cond)
x, y, w = grid(0, cols=1, row0=2)
lab("se_h2", "§YГОЛОСОВАНИЕ§!  §gначать сейчас — консоль (~): §Yforce_senate_vote§!§g · завершить — §Yend_senate_session§!§g или кнопки ниже§!", x, y, w, potential=G5)
SE = []   # (ключ, подпись, тело, условие, код, подсказка, нужна ли цель A)
SE += [
       ("pass", "Досрочно: принять", B("from", "dtp_gc_pass_current = yes") + "\n" + PLAYERS("country_event = { id = dtp.1261 }"), GCM() + "\n" + GCV(), 62,
        "По-настоящему завершить текущее голосование досрочно: резолюция принимается сразу (как будто голосование закончилось «за»). Всем игрокам — окно «Резолюция принята».", False),
       ("reject", "Досрочно: отклонить", B("from", "dtp_gc_reject_current = yes") + "\n" + PLAYERS("country_event = { id = dtp.1263 }"), GCM() + "\n" + GCV(), 62,
        "По-настоящему завершить текущее голосование досрочно: резолюция снимается и не принимается. Всем игрокам — окно «Резолюция отклонена».", False),
       ("join", "Все — в сообщество", PLAYERS(B("if", B("limit", "NOT = { is_galactic_community_member = yes }"), "add_to_galactic_community = yes")), GCM(), 62,
        "Принять в Галактическое сообщество всех живых игроков, которые ещё не в нём.", False)]
TA = lambda eff: B("event_target:dtp_t", eff)
SE += [("a_in", "A — в сообщество", TA("add_to_galactic_community = yes"), GCM() + "\n" + N_TC(), 62, "Принять державу A в Галактическое сообщество.", True),
       ("a_out", "A — из сообщества", TA("remove_from_galactic_community = yes"), GCM() + "\n" + N_TC(), 62, "Исключить державу A из Галактического сообщества.", True)]
SE2 = [("c_in", "A — в Совет", TA("add_to_galactic_council = yes"), GCM() + "\n" + N_TC(), "Добавить державу A в Галактический совет."),
       ("c_out", "A — из Совета", TA("remove_from_galactic_council = yes"), GCM() + "\n" + N_TC(), "Убрать державу A из Галактического совета."),
       ("c_perm", "A — постоянный член", TA("add_permanent_councillor = yes"), GCM() + "\n" + N_TC(), "Дать державе A постоянное место в Совете."),
       ("c_unperm", "Снять постоянное место", TA("remove_permanent_councillor = yes"), GCM() + "\n" + N_TC(), "Забрать у державы A постоянное место в Совете."),
       ("sz_p", "Совет: +1 место", "increase_council_size = yes", GCM(), "Добавить одно место в Галактическом совете."),
       ("sz_m", "Совет: −1 место", "decrease_council_size = yes", GCM(), "Убрать одно место в Галактическом совете."),
       ("veto1", "Вето: включить", "set_council_veto = yes\nset_global_flag = galactic_council_veto", GCM() + "\n" + need("dtp_need_gcc", "Галактический совет ещё не создан (он появляется позже сообщества)", "is_galactic_council_established = yes"), "Члены Галактического совета смогут накладывать вето на резолюции (как после резолюции «Право вето»). Нужен созданный Совет."),
       ("veto0", "Вето: выключить", "set_council_veto = no\nremove_global_flag = galactic_council_veto", GCM() + "\n" + need("dtp_need_gcc", "Галактический совет ещё не создан (он появляется позже сообщества)", "is_galactic_council_established = yes"), "Члены Галактического совета больше не смогут накладывать вето. Нужен созданный Совет."),
       ("em1", "Чрезв. меры: вкл", "set_council_emergency_measures = yes", GCM() + "\n" + need("dtp_need_gcc", "Галактический совет ещё не создан (он появляется позже сообщества)", "is_galactic_council_established = yes"), "Члены Совета смогут предлагать чрезвычайные меры. Нужен созданный Совет."),
       ("em0", "Чрезв. меры: выкл", "set_council_emergency_measures = no", GCM() + "\n" + need("dtp_need_gcc", "Галактический совет ещё не создан (он появляется позже сообщества)", "is_galactic_council_established = yes"), "Члены Совета не смогут предлагать чрезвычайные меры. Нужен созданный Совет."),
       ("cus1", "A — Хранитель", TA("set_galactic_custodian = yes"), GCM() + "\n" + N_TC(), "Сделать державу A Хранителем Галактики (Кастодианом)."),
       ("cus0", "Снять Хранителя", TA("set_galactic_custodian = no"), GCM() + "\n" + N_TC(), "Лишить державу A статуса Хранителя."),
       ("cus_t", "Хранитель +10 лет", "add_custodian_term_days = 3600", GCM(), "Продлить срок текущего Хранителя на 10 лет."),
       ("cus_inf", "Хранитель навсегда", "set_custodian_term_days = -1", GCM(), "Сделать полномочия текущего Хранителя бессрочными."),
       ("emp1", "A — Император", TA("set_galactic_emperor = yes") + "\n" + B("event_target:dtp_t", "save_global_event_target_as = dtp_emp_new") + "\n" + PLAYERS("country_event = { id = dtp.1264 }"),
        N_TC(), "Провозгласить державу A Галактическим императором. Всем игрокам придёт окно."),
       ("emp0", "Снять Императора", TA("set_galactic_emperor = no"), N_TC(), "Лишить державу A титула Галактического императора."),
       ("auth_p", "Авторитет +25", "add_imperial_authority = 25", "", "Имперский авторитет +25 (влияет на власть императора над членами империи)."),
       ("auth_m", "Авторитет −25", "add_imperial_authority = -25", "", "Имперский авторитет −25."),
       ("ecc1", "Имп. меняет Совет: да", "set_emperor_can_change_council_members = yes", "", "Император сможет менять членов Имперского совета."),
       ("ecc0", "Имп. меняет Совет: нет", "set_emperor_can_change_council_members = no", "", "Император не сможет менять членов Имперского совета.")]
for i, (k, n, body, al, code, tt, needs_t) in enumerate(SE):
    x, y, w = grid(i, cols=4, row0=3)
    button("se_" + k, n, x, y, w, potential=G5, allow=GM() + ("\n" + al if al else ""), effect=act("gm", body, code, needs_t), sprite="GFX_dtp_si_" + k, tt=tt)
x, y, w = grid(0, cols=1, row0=5)
lab("se_h3", "§YСОВЕТ, ХРАНИТЕЛЬ, ИМПЕРАТОР§!  §gдержава A — в карточке сверху§!", x, y, w, potential=G5)
for i, (k, n, body, al, tt) in enumerate(SE2):
    x, y, w = grid(i, cols=4, row0=6)
    button("se_" + k, n, x, y, w, potential=G5, allow=GM() + ("\n" + al if al else ""), effect=act("gm", body, 62, "dtp_t" in body), tt=tt, sprite="GFX_dtp_si_" + k)

# ---------- 11. Доступ
area(11)
humans = "count_country = { limit = { is_ai = no } count %s }"
x, y, w = grid(0, cols=1)
lab("ac_h", "ХОСТ партии: §Y[dtp_host.GetName]§!", x, y, w, potential=T(11, "has_global_flag = dtp_host_set\nexists = event_target:dtp_host"))
lab("ac_0", "§RХОСТ не назначен§! — инструменты закрыты для всех.", x, y, w, potential=T(11, "NOT = { has_global_flag = dtp_host_set }"))
x, y, w = grid(0, row0=1)
button("ac_solo", "Стать ХОСТом", x, y, w, potential=T(11, "NOT = { has_global_flag = dtp_host_set }"),
       allow=need("dtp_need_solo", "Только если вы единственный живой игрок", humans % "= 1"),
       effect=B("if", B("limit", "NOT = { has_global_flag = dtp_host_set }", humans % "= 1"), B("from", "dtp_make_host = yes"), GM_OFFER, "dtp_result = { CODE = 25 }"))
x, y, w = grid(1, cols=3, row0=1)
button("ac_claim", "Запросить статус (голосование)", x, y, 2 * w + 6, potential=T(11, "NOT = { has_global_flag = dtp_host_set }"),
       allow=need("dtp_need_multi", "В партии один игрок — используйте «Стать ХОСТом»", humans % "> 1") + "\n" + need("dtp_need_novote", "Голосование уже идёт", "NOT = { has_global_flag = dtp_vote_open }"),
       effect=B("from", B("if", B("limit", "NOT = { has_global_flag = dtp_host_set }", "NOT = { has_global_flag = dtp_vote_open }"),
                "set_global_flag = dtp_vote_open", "save_global_event_target_as = dtp_claimant", setv("dtp_votes_yes", 0), setv("dtp_votes_need", 0),
                "set_country_flag = dtp_claimant_self",
                B("every_country", B("limit", "is_ai = no", "NOT = { has_country_flag = dtp_claimant_self }"), "set_country_flag = dtp_vote_pending",
                  B("prev", "change_variable = { which = dtp_votes_need value = 1 }"), "country_event = { id = dtp.13 }"),
                "remove_country_flag = dtp_claimant_self", "country_event = { id = dtp.14 days = 30 }")),
       tt="Статус подтверждают все игроки: каждому придёт окно «За/Против».")
x, y, w = grid(0, row0=1)
button("ac_resign", "Сложить полномочия", x, y, w, potential=T(11, B("from", "dtp_is_host = yes")),
       effect=B("from", "remove_country_flag = dtp_host", "dtp_gm_off = yes") + "\nremove_global_flag = dtp_host_set\ndtp_result = { CODE = 25 }", sprite="GFX_dtp_btn_danger",
       tt="Сложить статус ХОСТа. Если у вас роль Гейм-мастера — она тоже снимается, держава становится обычной.")
x, y, w = grid(0, cols=1, row0=2)
button("ac_auto", "Назначить ХОСТом первую державу игроков (держава хоста)", x, y, w, potential=T(11, "NOT = { has_global_flag = dtp_host_set }"),
       effect="dtp_auto_host = yes\n" + GM_OFFER + "\ndtp_result = { CODE = 25 }", sprite="GFX_dtp_btn_go",
       tt="ХОСТом станет держава игрока с самым маленьким номером. В новой сетевой партии это держава хоста (номер 0) — даже если нажал другой игрок, статус получит хост, а не он. В загруженном сохранении проверьте имя в окне «Назначен ХОСТ»: если это не хост, он может передать статус.")
per_k_label("ac_who", "Права державы-цели: §Y[dtp_tc_#.GetName]§!", CX, CY + 2 * ROW, CW, pot_extra=T(11, B("from", "dtp_is_host = yes")), tgt="dtp_tc")
HOST = need("dtp_need_host", "Права выдаёт только ХОСТ", B("from", "dtp_is_host = yes")) + "\n" + need("dtp_need_human", "Выбранная держава — не живой игрок", "dtp_tc_human = yes")
for i, (p, n) in enumerate(PERMS):
    x, y, w = grid(i, cols=4, row0=3)
    hp = "dtp_tc_hasperm = { P = %s }" % p
    button("pm_%s_on" % p, "✔ " + PSHORT[p], x, y, w, potential=T(11, B("from", "dtp_is_host = yes") + "\n" + hp), allow=HOST,
           effect=act("force", B("event_target:dtp_t", "remove_country_flag = dtp_perm_%s" % p), 24).replace("dtp_has_perm = { P = force }", "dtp_is_host = yes"),
           sprite="GFX_dtp_btn_on", tt="Право «%s» выдано. Нажмите, чтобы ОТОЗВАТЬ." % n)
    button("pm_" + p, "– " + PSHORT[p], x, y, w, potential=T(11, B("from", "dtp_is_host = yes") + "\nNOT = { %s }" % hp), allow=HOST,
           effect=act("force", B("event_target:dtp_t", "set_country_flag = dtp_perm_%s" % p), 24).replace("dtp_has_perm = { P = force }", "dtp_is_host = yes"),
           tt="Право «%s» не выдано. Нажмите, чтобы ВЫДАТЬ." % n)
x, y, w = grid(0, cols=1, row0=6)
button("ac_transfer", "Передать статус ХОСТа державе-цели", x, y, w, potential=T(11, B("from", "dtp_is_host = yes")), allow=HOST,
       effect="dtp_load = yes\n" + B("from", "save_global_event_target_as = dtp_offer_from") + "\n" + B("event_target:dtp_t", "country_event = { id = dtp.15 }"),
       tt="Игроку придёт запрос; статус перейдёт после его согласия.")
x, y, w = grid(0, cols=2, row0=7)
GMR = B("from", "has_country_flag = dtp_gm_role")
button("ac_gm_on", "Принять роль Гейм-мастера", x, y, w, potential=T(11, B("from", "dtp_is_host = yes") + "\nNOT = { %s }" % GMR), sprite="GFX_dtp_btn_go",
       allow=need("dtp_need_host2", "Роль Гейм-мастера может взять только ХОСТ", B("from", "dtp_is_host = yes")),
       effect=B("from", "dtp_gm_on = yes") + "\ndtp_result = { CODE = 25 }",
       tt="Ваша держава становится державой Гейм-мастера: видит всю галактику и все державы, разведка и шифровка 1000, огромные бонусы к науке и ресурсам, население не растёт. Галактическое сообщество вас не учитывает (как угасшую империю) и не принимает. Вам нельзя объявить войну и закрыть для вас границы (все открывают их вам и вы — им); филиалы мегакорпораций и синдикатов на ваших планетах запрещены (имеющиеся закрываются). Сами вы можете всё. Снимается кнопкой «Сложить роль».")
button("ac_gm_off", "Сложить роль Гейм-мастера", x, y, w, potential=T(11, GMR), sprite="GFX_dtp_btn_danger",
       effect=B("from", "dtp_gm_off = yes") + "\ndtp_result = { CODE = 25 }",
       tt="Держава снова становится обычной: этика, бонусы и особые правила Гейм-мастера снимаются.")
x, y, w = grid(1, cols=2, row0=7)
lab("ac_gm_st1", "§YРоль Гейм-мастера: ВЗЯТА§!", x + 4, y + 4, w, potential=T(11, GMR))
lab("ac_gm_st0", "§gРоль Гейм-мастера: не взята§!", x + 4, y + 4, w, potential=T(11, "NOT = { %s }" % GMR))
x, y, w = grid(0, cols=1, row0=8)
lab("ac_note", "Проверка прав настоящая: игра сообщает кнопке, кто её нажал, права проверяются при выполнении.", x, y, w, potential=T(11))
for i, t in enumerate(["§YКАК НАЗНАЧАЕТСЯ ХОСТ§!  §gтолько хост партии, без голосования§!",
                       "§g1. Новая партия: через день после старта ХОСТом сам становится хост — его держава первая (номер 0).§!",
                       "§g2. Загруженное сохранение: «Назначить ХОСТом первую державу игроков» или заранее в одиночной игре «Стать ХОСТом».§!",
                       "§g3. Дальше ХОСТ сам выдаёт права (кнопки выше) и может передать статус. Голосование — только если ХОСТа нет.§!"]):
    x, y, w = grid(0, cols=1, row0=9 + i)
    lab("ac_how%d" % i, t, x, y, w, potential=T(11))

# ---------- 12. Журнал
area(12)
for k in range(1, 9):
    x, y, w = grid(0, cols=1, row0=k - 1)
    pe = T(12, "exists = event_target:dtp_log%d_actor" % k)
    lab("log%d" % k, "%d. §Y[dtp_log%d_actor.GetName]§! → [dtp_log%d_tgt.GetName]" % (k, k, k), x, y, 300, potential=pe + "\nexists = event_target:dtp_log%d_tgt" % k)
    lab("log%d_nt" % k, "%d. §Y[dtp_log%d_actor.GetName]§!" % (k, k), x, y, 300, potential=pe + "\nNOT = { exists = event_target:dtp_log%d_tgt }" % k)
    for c, t in CODES.items():
        lab("log%d_c%d" % (k, c), t, x + 306, y, w - 450, potential=pe + "\n" + B("event_target:dtp_log%d_actor" % k, chk("dtp_logcode_%d" % k, c)))
    for r, rt in [(1, "§GОК§!"), (0, "§RОТКАЗ§!"), (2, "§OНЕ ВЫПОЛНЕНО§!")]:
        lab("log%d_r%d" % (k, r), rt, x + w - 140, y, 140, potential=pe + "\n" + B("event_target:dtp_log%d_actor" % k, chk("dtp_logres_%d" % k, r)))

# ---- самопроверка: тест ставит и сразу убирает изменение, итог — в строке итога и в журнале
x, y, w = grid(0, cols=1, row0=8)
lab("ts_h", "§YПРОВЕРКА РАБОТЫ МОДА§!  §gтесты, а не инструменты: каждый сам всё возвращает; итог — в строке снизу§!", x, y, w, potential=T(12))
def selftest(name, p, setup, check, undo, need_obj):
    eff = "\n".join([INIT, "dtp_load = yes", "dtp_disarm = yes",
        B("if", B("limit", B("from", "dtp_has_perm = { P = %s }" % p)), setup,
          B("if", B("limit", check), 'log = "DTP TEST %s: OK"' % name, "dtp_result = { CODE = 56 }"),
          B("else", 'log = "DTP TEST %s: FAIL"' % name, "dtp_fail = { CODE = 56 }"), undo),
        B("else", "dtp_deny = { CODE = 56 }")])
    return eff
TESTS = [("pmod", "Тест: бонус планеты", "planet", N_TP(),
          B("event_target:dtp_p", "add_modifier = { modifier = dtp_up_stab days = 30 }"), B("event_target:dtp_p", "has_modifier = dtp_up_stab"),
          B("event_target:dtp_p", "remove_modifier = dtp_up_stab"), "Ставит выбранной планете модификатор Toolpack, проверяет, что он есть, и убирает."),
         ("cmod", "Тест: бонус державы A", "res", N_TC(),
          B("event_target:dtp_t", "add_modifier = { modifier = fleet_maneuvers days = 30 }"), B("event_target:dtp_t", "has_modifier = fleet_maneuvers"),
          B("event_target:dtp_t", "remove_modifier = fleet_maneuvers"), "Ставит державе A модификатор игры «Учения флота», проверяет и убирает."),
         ("mark", "Тест: отметка системы", "planet", N_TP(),
          B("event_target:dtp_s", "set_variable = { which = dtp_wasm value = 0 }", B("if", B("limit", "has_star_flag = dtp_marked"), "set_variable = { which = dtp_wasm value = 1 }"),
            B("if", B("limit", "NOT = { has_star_flag = dtp_marked }"), "dtp_mark_sys = yes")),
          B("event_target:dtp_s", "has_star_flag = dtp_marked"),
          B("event_target:dtp_s", B("if", B("limit", chk("dtp_wasm", 0)), "dtp_unmark_sys = yes")),
          "Отмечает систему выбранной планеты, проверяет отметку и снимает её (если система не была отмечена). Строки DTP MARK в game.log покажут, сменились ли звезда и имя."),
         ("res", "Тест: ресурсы A", "res", N_TC(),
          B("event_target:dtp_t", "export_resource_stockpile_to_variable = { resource = energy variable = dtp_e0 }", "add_resource = { energy = 1 }",
            "export_resource_stockpile_to_variable = { resource = energy variable = dtp_e1 }", "subtract_variable = { which = dtp_e1 value = dtp_e0 }"),
          B("event_target:dtp_t", chk("dtp_e1", 0, ">")),
          B("event_target:dtp_t", "add_resource = { energy = -1 }"), "Добавляет державе A 1 энергию, проверяет склад и возвращает обратно.")]
for i, (k, n, p, need_obj, setup, check, undo, tt) in enumerate(TESTS):
    x, y, w = grid(i, cols=4, row0=9)
    button("st_" + k, n, x, y, w, potential=T(12), allow=need_perm(p) + "\n" + need_obj, effect=selftest(k, p, setup, check, undo, need_obj), tt=tt, sprite="GFX_dtp_btn_go")

# ================================================================ ПОЛОСЫ В ОКНАХ ОБЪЕКТОВ
ANY = B("from", "dtp_has_any_perm = yes")
SPL = "is_scope_type = planet\n" + ANY
lab("ps_title", "§YDEBUG TOOLPACK§! · [This.GetName] §g— полосу можно тянуть§!", 0, 0, 510 if UIOD else 600, potential=SPL, where="planet")
button("ps_pick", "Выбрать", 0, 26, 130, potential=SPL, effect="dtp_set_tp = yes\ndtp_result = { CODE = 29 }", where="planet", sprite="GFX_dtp_btn_go",
       tt="Сделать эту планету (или звезду) выбранной в Toolpack — вкладка «Планета».")
button("ps_tc", "Держава ← владелец", 136, 26, 170, potential=SPL + "\nexists = owner\n" + B("owner", "dtp_target_country = yes"), effect=B("owner", "dtp_set_tc = yes") + "\ndtp_result = { CODE = 29 }", where="planet")
button("ps_rcp", "Получатель ← владелец", 312, 26, 190, potential=SPL + "\nexists = owner\n" + B("owner", "dtp_target_country = yes"), effect=B("owner", "dtp_set_rcp = yes") + "\ndtp_result = { CODE = 29 }", where="planet")
DIAG = "\n".join(['log = "DTP STRIP click | this=[This.GetName]"', B("solar_system", 'log = "DTP STRIP system=[This.GetName]"',
    B("if", B("limit", "has_star_flag = dtp_marked"), 'log = "DTP STRIP system now MARKED"'), B("else", 'log = "DTP STRIP system NOT marked"'))])
MKTOG = B("solar_system", B("if", B("limit", "has_star_flag = dtp_marked"), "dtp_unmark_sys = yes"), B("else", "dtp_mark_sys = yes"))
button("ps_mark", "§R●§! ОТМЕТИТЬ систему   Alt+M", 0, 60, 250 if UIOD else 300, shortcut="alt+m", potential=SPL + "\n" + B("solar_system", "NOT = { has_star_flag = dtp_marked }"), allow=need_perm("planet"),
       effect=act("planet", MKTOG, 36, False) + "\n" + DIAG + "\ndtp_mlist = yes", where="planet", sprite="GFX_dtp_btn_warn",
       tt="Отметить эту систему (Alt+M, пока открыто окно планеты или звезды). На галактической карте звезда станет красной с кольцом, в подсказке системы — строка «Отмечено». Все отметки — во вкладке «Отмеченное».")
button("ps_unmark", "✕ Снять отметку   Alt+M", 0, 60, 250 if UIOD else 300, shortcut="alt+m", potential=SPL + "\n" + B("solar_system", "has_star_flag = dtp_marked"), allow=need_perm("planet"),
       effect=act("planet", MKTOG, 36, False) + "\ndtp_mlist = yes", where="planet", sprite="GFX_dtp_btn_on",
       tt="Снять отметку с этой системы (Alt+M). Звезда вернёт свой обычный вид.")
lab("ps_st_on", "§R● СИСТЕМА ОТМЕЧЕНА§!", 256 if UIOD else 306, 62, 250 if UIOD else 300, potential=SPL + "\n" + B("solar_system", "has_star_flag = dtp_marked"), where="planet")
lab("ps_st_off", "§gсистема не отмечена§!", 256 if UIOD else 306, 62, 250 if UIOD else 300, potential=SPL + "\n" + B("solar_system", "NOT = { has_star_flag = dtp_marked }"), where="planet")
SFL = "OR = { is_scope_type = fleet is_scope_type = ship }\n" + ANY
lab("fs_title", "§YDEBUG TOOLPACK§! · флот", 0, 0, 260, potential=SFL, where="fleet")
FLSAVE = B("if", B("limit", "is_scope_type = ship"), B("fleet", "dtp_set_tf = yes")) + "\n" + B("else", "dtp_set_tf = yes")
button("fs_pick", "Выбрать флот", 0, 26, 140, potential=SFL, effect=FLSAVE + "\ndtp_result = { CODE = 29 }", where="fleet", sprite="GFX_dtp_btn_go")
button("fs_tc", "Держава ← владелец", 146, 26, 170, potential=SFL + "\nexists = owner\n" + B("owner", "dtp_target_country = yes"), effect=B("owner", "dtp_set_tc = yes") + "\ndtp_result = { CODE = 29 }", where="fleet")
button("fs_rep", "Ремонт", 322, 26, 100, potential=SFL, allow=need_perm("fleet"), effect=act("fleet", "repair_percentage = 1", 16, False), where="fleet")
button("fs_mark", "§R●§! Отметить систему флота", 0, 60, 260, potential=SFL + "\nexists = solar_system\n" + B("solar_system", "NOT = { has_star_flag = dtp_marked }"), allow=need_perm("planet"),
       effect=act("planet", B("solar_system", "dtp_mark_sys = yes"), 36, False) + "\ndtp_mlist = yes", where="fleet", sprite="GFX_dtp_btn_warn")
SH_ADD = "\n".join([B("owner", setv("dtp_shc", "from.dtp_shn"), setv("dtp_shk", "from.dtp_shz")), SH_PROTO("owner"),
    B("while", B("limit", B("owner", chk("dtp_shc", 0, ">"))), SH_ONE("owner"), B("owner", "change_variable = { which = dtp_shc value = -1 }")),
    'log = "DTP FLEET: ships added to fleet"'])
button("fs_add", "+ §Y[From.dtp_shn]§! кораблей", 266, 60, 166, potential="is_scope_type = fleet\n" + ANY, allow=need_perm("fleet"), sprite="GFX_dtp_btn_go",
       effect=act("fleet", SH_ADD, 17, False), where="fleet",
       tt="Добавить в ЭТОТ флот корабли из конструктора (Debug Toolpack → «Флот»): тип и количество — как выбрано там. Строятся по кораблю/проекту владельца флота этого типа. §HЕсли у владельца этот тип корабля не изучен — кораблей не будет.§!")
button("fs_unmark", "✕ Снять отметку системы", 0, 60, 260, potential=SFL + "\nexists = solar_system\n" + B("solar_system", "has_star_flag = dtp_marked"), allow=need_perm("planet"),
       effect=act("planet", B("solar_system", "dtp_unmark_sys = yes"), 36, False) + "\ndtp_mlist = yes", where="fleet", sprite="GFX_dtp_btn_on")


# ---------- полоса в окне станции (открывается кликом по значку станции прямо на галактической карте)
SSB = "OR = { is_scope_type = starbase is_scope_type = ship }\nexists = solar_system\n" + ANY
SBOWN = "\nexists = owner\n" + B("owner", "dtp_target_country = yes")
lab("sb_title", "§YDEBUG TOOLPACK§! · [This.GetName] §g— полосу можно тянуть§!", 0, 0, 520, potential=SSB, where="starbase")
SBTOG = B("solar_system", B("if", B("limit", "has_star_flag = dtp_marked"), "dtp_unmark_sys = yes"), B("else", "dtp_mark_sys = yes"))
button("sb_mark", "§R●§! ОТМЕТИТЬ систему   Alt+M", 0, 26, 260, shortcut="alt+m", potential=SSB + "\n" + B("solar_system", "NOT = { has_star_flag = dtp_marked }"), allow=need_perm("planet"),
       effect=act("planet", SBTOG, 36, False) + "\n" + DIAG + "\ndtp_mlist = yes", where="starbase", sprite="GFX_dtp_btn_warn",
       tt="Отметить систему этой станции. Окно станции открывается кликом по значку станции на галактической карте — в систему заходить не нужно.")
button("sb_unmark", "✕ Снять отметку   Alt+M", 0, 26, 260, shortcut="alt+m", potential=SSB + "\n" + B("solar_system", "has_star_flag = dtp_marked"), allow=need_perm("planet"),
       effect=act("planet", SBTOG, 36, False) + "\ndtp_mlist = yes", where="starbase", sprite="GFX_dtp_btn_on")
lab("sb_st_on", "§R● СИСТЕМА ОТМЕЧЕНА§!", 268, 28, 250, potential=SSB + "\n" + B("solar_system", "has_star_flag = dtp_marked"), where="starbase")
lab("sb_st_off", "§gсистема не отмечена§!", 268, 28, 250, potential=SSB + "\n" + B("solar_system", "NOT = { has_star_flag = dtp_marked }"), where="starbase")
button("sb_pick", "Выбрать звезду", 0, 60, 150, potential=SSB, effect=B("star", "dtp_set_tp = yes") + "\ndtp_result = { CODE = 29 }", where="starbase", sprite="GFX_dtp_btn_go",
       tt="Звезда этой системы станет выбранной планетой Toolpack (вкладка «Планета»: класс звезды и т. п.).")
button("sb_tc", "Держава ← владелец", 156, 60, 170, potential=SSB + SBOWN, effect=B("owner", "dtp_set_tc = yes") + "\ndtp_result = { CODE = 29 }", where="starbase")
button("sb_rcp", "Получатель ← владелец", 332, 60, 188, potential=SSB + SBOWN, effect=B("owner", "dtp_set_rcp = yes") + "\ndtp_result = { CODE = 29 }", where="starbase")

# ================================================================ СОБЫТИЯ (голосование + каталог)
def event(eid, title, desc, opts, immediate="", extra="", kind="country_event", pic="access"):
    tk = loc("dtp.%d.name" % eid, title); dk = loc("dtp.%d.desc" % eid, desc)
    body = ["id = dtp.%d" % eid, "title = %s" % tk, "desc = %s" % dk, "picture = GFX_evt_dtp_%s" % pic, "is_triggered_only = yes"]
    if extra: body.append(extra)
    if immediate: body.append(B("immediate", immediate))
    for j, (t, e) in enumerate(opts):
        body.append(B("option", "name = %s" % loc("dtp.%d.o%d" % (eid, j), t), e))
    EVENTS.append(B(kind, *body))
event(13, "Запрос статуса ХОСТа", "Игрок §Y[dtp_claimant.GetName]§! запрашивает статус §YХОСТа§! Debug Toolpack.\\n\\nХОСТ получит полный доступ к инструментам для всех государств, включая ваше. Голосуйте «За», только если это действительно хост партии.", [
    ("Против", B("if", B("limit", "has_global_flag = dtp_vote_open", "has_country_flag = dtp_vote_pending"), "dtp_close_vote = yes",
                 B("every_country", B("limit", "is_ai = no"), "country_event = { id = dtp.17 }"))),
    ("За — это хост партии", B("if", B("limit", "has_global_flag = dtp_vote_open", "has_country_flag = dtp_vote_pending"), "remove_country_flag = dtp_vote_pending",
        B("event_target:dtp_claimant", "change_variable = { which = dtp_votes_yes value = 1 }",
          B("if", B("limit", "check_variable = { which = dtp_votes_yes value >= dtp_votes_need }"), "dtp_make_host = yes", "dtp_close_vote = yes",
            B("every_country", B("limit", "is_ai = no"), "country_event = { id = dtp.18 }")))))])
event(14, "Голосование истекло", "Не все игроки ответили за 30 дней. Запрос отменён.", [("Понятно", "")],
      immediate=B("if", B("limit", "has_global_flag = dtp_vote_open", "NOT = { has_global_flag = dtp_host_set }"), "dtp_close_vote = yes"), extra="trigger = { has_global_flag = dtp_vote_open }")
event(15, "Передача статуса ХОСТа", "ХОСТ §Y[dtp_offer_from.GetName]§! предлагает передать вам статус §YХОСТа§! Debug Toolpack.", [
    ("Отказаться", ""), ("Принять", B("if", B("limit", "event_target:dtp_offer_from = { dtp_is_host = yes }", "is_ai = no"), "dtp_make_host = yes",
        B("every_country", B("limit", "is_ai = no"), "country_event = { id = dtp.18 }")))])
event(19, "Роль Гейм-мастера", "Вы стали §YХОСТОМ§! партии. Debug Toolpack предлагает взять §YРОЛЬ ГЕЙМ-МАСТЕРА§! — ведущего, который управляет партией, а не соревнуется с игроками.\\n\\n§YЧТО ДАЁТ РОЛЬ§!\\n§G+§! вы видите всю галактику: все системы, флоты и державы (полный обзор, вся карта, контакт со всеми)\\n§G+§! разведка, шифровка и дешифровка 1000 — от вас ничего не скрыто, вас не разведать\\n§G+§! наука и все ресурсы ×1000, склады +1 000 000, стабильность +50\\n§G+§! закрытая этика «Гейм-мастер» — её нельзя выбрать при создании державы\\n§G+§! вам нельзя объявить войну и закрыть для вас границы; филиалы мегакорпораций и синдикатов на ваших планетах запрещены\\n§G+§! сами вы можете всё: войны, договоры, границы\\n\\n§RВАЖНО: ИГРАТЬ КАК ОБЫЧНАЯ ДЕРЖАВА ВЫ НЕ СМОЖЕТЕ§!\\n§R−§! ваша держава становится особым типом «Гейм-мастер», как угасшая империя: население не растёт\\n§R−§! в Галактическое сообщество вас не примут, и вы не участвуете в его создании\\n§R−§! часть обычных механик (политики, дипломатические позиции, специализации планет) может быть недоступна\\n§R−§! это роль ведущего: соревноваться с игроками за победу вы не будете\\n\\nРоль можно сложить в любой момент: Debug Toolpack → «Доступ» → «Сложить роль Гейм-мастера» — держава снова станет обычной.", [
    ("Принять роль Гейм-мастера", B("if", B("limit", "has_country_flag = dtp_host"), "dtp_gm_on = yes")), ("Не сейчас", "")])
event(17, "Статус ХОСТа не подтверждён", "Запрос отклонён одним из игроков.", [("Понятно", "")])
event(18, "Назначен ХОСТ", "Новый §YХОСТ§! Debug Toolpack: §Y[dtp_host.GetName]§!.", [("Понятно", "")])
CAT = list(_CR_EV)
def cev(eid, kind, title, desc, opts, pic="GFX_evt_dtp_events"):
    body = ["id = dtp.%d" % eid, "title = %s" % loc("dtp.%d.name" % eid, title), "desc = %s" % loc("dtp.%d.desc" % eid, desc), "picture = %s" % pic, "is_triggered_only = yes"]
    for j, (t, e) in enumerate(opts):
        body.append(B("option", "name = %s" % loc("dtp.%d.o%d" % (eid, j), t), e))
    CAT.append(B(kind, *body))
cev(1001, "country_event", "Проверка связи", "Тестовое событие Debug Toolpack от §Y[dtp_last_actor.GetName]§!.", [("Связь есть", "")])
cev(1002, "country_event", "Дар Хранителей", "Хранители предлагают вашей империи дар.", [("Энергия (+5000)", "add_resource = { energy = 5000 }"), ("Сплавы (+2000)", "add_resource = { alloys = 2000 }"), ("Единство (+1000)", "add_resource = { unity = 1000 }")])
cev(1003, "country_event", "Волнения в столице", "В столице вспыхнули волнения.", [("Подавить силой", "capital_scope = { add_modifier = { modifier = dtp_up_stab days = 360 multiplier = -20 } }"), ("Откупиться (−1000 энергии)", "add_resource = { energy = -1000 }")])
cev(1004, "planet_event", "Геологическое открытие", "На планете §Y[Root.GetName]§! найдены новые залежи.", [("Отлично", "add_random_non_blocker_deposit = yes")])
cev(1005, "fleet_event", "Ремонтная бригада", "К флоту §Y[Root.GetName]§! прибыла ремонтная бригада.", [("Приступить", "repair_percentage = 1")])
cev(1006, "country_event", "Научный прорыв", "Учёные совершили прорыв.", [("Превосходно", "add_resource = { physics_research = 2000 society_research = 2000 engineering_research = 2000 }")])
cev(1007, "country_event", "Мирное предложение", "§Y[dtp_last_actor.GetName]§! предлагает перемирие.", [("Отклонить", ""), ("Принять", "set_truce = { target = event_target:dtp_last_actor type = war }")])
TOHOST = lambda eid: B("if", B("limit", "exists = event_target:dtp_host"), B("event_target:dtp_host", "country_event = { id = dtp.%d }" % eid))
for _eid, _n, _t, _d in ANN:
    _opts = [("Понятно", "")] if _eid != 1116 else [("§GГотов!§!", TOHOST(1117)), ("§OНужно ещё время§!", TOHOST(1118))]
    cev(_eid, "country_event", "§Y«ВЕДУЩИЙ»§! " + _t, _d + "\\n\\n§gОбъявление ведущего партии через Debug Toolpack.§!", _opts, pic="GFX_evt_dtp_ann_%d" % _eid)
cev(1117, "country_event", "Игрок готов", "§Y[From.GetName]§! §Gготов продолжать§!.", [("Хорошо", "")], pic="GFX_evt_dtp_ann_1116")
cev(1118, "country_event", "Игроку нужно время", "§Y[From.GetName]§! §Oпросит ещё немного времени§!.", [("Хорошо", "")], pic="GFX_evt_dtp_ann_1114")
# контроль правил: on_war_beginning вызывается для каждой страны в войне (Root = страна, From = война)
WHUM = "OR = { AND = { is_ai = no from = { is_ai = no } } AND = { has_global_flag = dtp_war_ai OR = { is_ai = no from = { is_ai = no } } } }"
CAT.append(B("country_event", "id = dtp.1201", "hide_window = yes", "is_triggered_only = yes",
    # нарушение: нападает игрок, и (общий запрет или личный запрет нападающему) и среди защищающихся есть игрок, либо защищающийся под защитой
    B("trigger", "NOT = { has_global_flag = dtp_viol_cd }",
      B("from", "is_war_participant = { who = root side = attackers }"),
      # 10.8.3: нарушение — держава под запретом объявила войну кому угодно, или напали на защищённую
      B("OR", "AND = { OR = { is_ai = no has_global_flag = dtp_war_ai } has_global_flag = dtp_rule_nopvp }",
              "has_country_flag = dtp_rule_np",
              "AND = { OR = { is_ai = no has_global_flag = dtp_war_ai } from = { any_defender = { has_country_flag = dtp_rule_prot } } }")),
    B("immediate", "set_timed_global_flag = { flag = dtp_viol_cd days = 3 }", "set_global_flag = dtp_viol_open", "save_global_event_target_as = dtp_violator",
      B("from", B("random_defender", B("limit", "is_ai = no"), "save_global_event_target_as = dtp_victim"),
                B("random_defender", B("limit", "has_country_flag = dtp_rule_prot"), "save_global_event_target_as = dtp_victim"),
                B("if", B("limit", "NOT = { exists = event_target:dtp_victim }"), B("random_defender", "save_global_event_target_as = dtp_victim"))),
      "change_variable = { which = dtp_viol value = 1 }", 'log = "DTP RULES: a player declared war on a player while wars are forbidden"',
      B("every_country", B("limit", "is_ai = no"), "country_event = { id = dtp.1202 }"))))
cev(1202, "country_event", "§R«ВЕДУЩИЙ»§! Нарушение правил партии",
    "§Y[dtp_violator.GetName]§! объявил войну державе §Y[dtp_victim.GetName]§! вопреки запрету ведущего (общий запрет войн, личный запрет нападать или защита державы).\\n\\nВедущий решит, будут ли санкции.\\n\\n§gКонтроль правил Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1104")
cev(1203, "country_event", "§R«ВЕДУЩИЙ»§! Санкции ведущего",
    "За нарушение запрета войн для игроков ведущий наложил на вашу державу «Унижение» на 5 лет.\\n\\n§gКонтроль правил Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1105")
cev(1208, "country_event", "§R«ВЕДУЩИЙ»§! Нарушитель наказан",
    "Ведущий наказал §Y[dtp_violator.GetName]§! за нарушение запрета войн для игроков: «Унижение» на 5 лет (влияние −33%, дипломатический вес −25%, одобрение −10%).\\n\\n§gКонтроль правил Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1105")
cev(1209, "country_event", "§Y«ВЕДУЩИЙ»§! Нарушение прощено",
    "Ведущий простил §Y[dtp_violator.GetName]§! нарушение запрета войн для игроков — без санкций. Запрет войн продолжает действовать.\\n\\n§gКонтроль правил Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1115")
# старт новой партии: через день ХОСТом становится первая держава игроков (держава хоста, номер 0)
CAT.append(B("event", "id = dtp.1250", "hide_window = yes", "is_triggered_only = yes",
    B("immediate", B("random_country", B("limit", "is_ai = no"), "country_event = { id = dtp.1251 days = 1 }"))))
CAT.append(B("country_event", "id = dtp.1251", "hide_window = yes", "is_triggered_only = yes",
    B("trigger", "NOT = { has_global_flag = dtp_host_set }"), B("immediate", "dtp_auto_host = yes")))
# окно «Правила партии» для любого игрока: описание — одно из 6 сочетаний (общий запрет × таймер сессии),
# личные правила зрителя — отдельными вариантами ответа (показываются только те, что относятся к нему)
G_RULES = [("none", "NOT = { has_global_flag = dtp_rule_nopvp }", "§GВойны игроков разрешены.§! Общего запрета сейчас нет."),
           ("inf", "has_global_flag = dtp_rule_nopvp\nhas_global_flag = dtp_rule_forever", "§RВойны игроков запрещены бессрочно§! — пока ведущий не снимет запрет. Кнопка «Объявить войну» заблокирована."),
           ("t", "has_global_flag = dtp_rule_nopvp\nNOT = { has_global_flag = dtp_rule_forever }", "§RВойны игроков запрещены§! до §Y[dtp_rule_owner.dtp_rule_endy]§! года. Кнопка «Объявить войну» заблокирована, потом запрет снимется сам.")]
S_RULES = [("s0", "NOT = { has_global_flag = dtp_sess }", "Таймер сессии не запущен."),
           ("s1", "has_global_flag = dtp_sess", "Сессия закончится примерно в §Y[dtp_sess_owner.dtp_sess_y]§! году — за месяц до конца придёт напоминание.")]
R_OPTS = [("np", "has_country_flag = dtp_rule_np", "Понятно. Вам лично запрещено объявлять войну до [Root.dtp_np_endy] г."),
          ("prot", "has_country_flag = dtp_rule_prot", "Понятно. Ваша держава под защитой ведущего до [Root.dtp_prot_endy] г."),
          ("ok", "NOT = { has_country_flag = dtp_rule_np }\nNOT = { has_country_flag = dtp_rule_prot }", "Понятно. Личных запретов и защиты у вашей державы нет.")]
R_BLK = []
for gk, gt, gtx in G_RULES:
    for sk, st, stx in S_RULES:
        key = loc("dtp.1240.desc_%s_%s" % (gk, sk), "§YПРАВИЛА ПАРТИИ§!\\n\\n" + gtx + "\\n\\n" + stx +
                  "\\n\\nНарушения видят все игроки, решение о санкциях принимает ведущий.\\n\\n§gDebug Toolpack · ниже — ваши личные правила, если есть.§!")
        R_BLK.append(B("desc", B("trigger", gt, st), "text = %s" % key))
CAT.append(B("country_event", "id = dtp.1240", "title = %s" % loc("dtp.1240.name", "§Y«ВЕДУЩИЙ»§! Правила партии"), *R_BLK,
    "picture = GFX_evt_dtp_ann_1105", "is_triggered_only = yes",
    *[B("option", "name = %s" % loc("dtp.1240.o_%s" % k_, t_), B("trigger", tr_)) for k_, tr_, t_ in R_OPTS]))
cev(1260, "country_event", "§Y«ВЕДУЩИЙ»§! Заседание закрыто",
    "Заседание Галактического сообщества закрыто. Принятые решения вступают в силу; следующие голосования — по расписанию сообщества.\\n\\n§gОбъявление ведущего партии через Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1109")
cev(1262, "country_event", "§Y«ВЕДУЩИЙ»§! Заседание открыто",
    "Ведущий открыл заседание сената Галактического сообщества. Делегаты держав, ваше слово: предлагайте резолюции и голосуйте.\\n\\n§gОбъявление ведущего партии через Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1111")
cev(1263, "country_event", "§Y«ВЕДУЩИЙ»§! Резолюция отклонена",
    "Ведущий снял с голосования резолюцию Галактического сообщества — она §Rне принята§!.\\n\\n§gОбъявление ведущего партии через Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1105")
cev(1264, "country_event", "§Y«ВЕДУЩИЙ»§! Новый Галактический император",
    "Ведущий провозгласил §Y[dtp_emp_new.GetName]§! Галактическим императором.\\n\\n§gОбъявление ведущего партии через Debug Toolpack.§!",
    [("Да здравствует Император", "")], pic="GFX_evt_dtp_ann_1112")
cev(1261, "country_event", "§Y«ВЕДУЩИЙ»§! Резолюция принята",
    "Ведущий завершил голосование: резолюция, за которую голосовало Галактическое сообщество, §Gпринята§! и вступает в силу.\\n\\n§gОбъявление ведущего партии через Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1109")
cev(1205, "country_event", "§Y«ВЕДУЩИЙ»§! Войны игроков запрещены",
    "Ведущий запретил войны игроков до §Y[dtp_rule_owner.dtp_rule_endy]§! года (лет: §Y[dtp_rule_owner.dtp_rule_len]§!).\\n\\n§RПравило работает:§! кнопка «Объявить войну» заблокирована; если война всё же начнётся, все получат оповещение, а ведущий может наказать нарушителя. По истечении срока запрет снимется сам.\\n\\n§gОбъявление ведущего партии через Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1104")
cev(1206, "country_event", "§Y«ВЕДУЩИЙ»§! Срок запрета войн истёк",
    "Срок запрета войн для игроков закончился. С этого момента игроки снова могут объявлять войны.\\n\\n§gКонтроль правил Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1103")
# раз в месяц: запрет с таймером истёк → сообщить всем (on_monthly_pulse — без области)
# 10.8.5: корабль-метка (Scope = флот, From = система). Отметка — через день после остановки, один раз за остановку.
# 10.8.6: on_entering_system_fleet в игре не сработал (game.log 22.10) — вместо него ежедневная проверка корабля.
# Корабль летит (есть приказ движения/прыжка) → флаг dtp_mk_moving; приказа больше нет, а флаг есть → остановился: отметить/снять.
MOVING = "OR = { has_fleet_order = move_to_system_point_order has_fleet_order = jumpdrive_order has_fleet_order = jumpdrive_windup }"
# 10.8.7: отметка СРАЗУ при входе в систему (on_entering_system_fleet, From = система) — «предварительная».
# Пролетел дальше, не остановившись → в следующей системе предварительная отметка прежней откатывается.
# Остановился (ежедневная проверка: нет приказа движения) → отметка подтверждается. Если вход в систему игра не сообщила —
# запасной путь как в 10.8.6: отметить по остановке.
CAT.append(B("fleet_event", "id = dtp.1280", "hide_window = yes", "is_triggered_only = yes",
    B("trigger", "has_fleet_flag = dtp_marker"),
    B("immediate", "set_fleet_flag = dtp_mk_entered",
      B("if", B("limit", "has_fleet_flag = dtp_mk_tp"), "remove_fleet_flag = dtp_mk_tp", 'log = "DTP MARKER: teleport - no mark"'),
      # 10.9.7: корабль отмечает ВЕСЬ путь — без отката промежуточных систем (по просьбе: лишнее снимается «Снять все отметки»)
      B("else",
        # 10.9.1: режим корабля — ОТМЕЧАЕТ (только ставит) или СНИМАЕТ (только убирает), без переключения туда-обратно
        B("from", B("if", B("limit", "prev = { owner = { has_country_flag = dtp_mk_unmode } }", "has_star_flag = dtp_marked"), "dtp_unmark_sys = yes", 'log = "DTP MARKER: entered [This.GetName] - unmarked"'),
          B("else_if", B("limit", "NOT = { prev = { owner = { has_country_flag = dtp_mk_unmode } } }", "NOT = { has_star_flag = dtp_marked }"), "dtp_mark_sys = yes", 'log = "DTP MARKER: entered [This.GetName] - marked"')),
        B("owner", "country_event = { id = dtp.1282 }")))))
CAT.append(B("fleet_event", "id = dtp.1281", "hide_window = yes", "is_triggered_only = yes",
    B("trigger", "has_fleet_flag = dtp_marker"),
    B("immediate", "set_timed_fleet_flag = { flag = dtp_mk_alive days = 5 }", "fleet_event = { id = dtp.1281 days = 1 }",
      B("if", B("limit", MOVING), "set_fleet_flag = dtp_mk_moving"),
      B("else_if", B("limit", "exists = solar_system", "exists = event_target:dtp_mk_tent_sys", B("solar_system", "is_same_value = event_target:dtp_mk_tent_sys")),
        B("event_target:dtp_mk_tent_sys", "remove_star_flag = dtp_mk_tm", "remove_star_flag = dtp_mk_tu", 'log = "DTP MARKER: stopped in [This.GetName] - confirmed"'),
        "clear_global_event_target = dtp_mk_tent_sys", "remove_fleet_flag = dtp_mk_moving", "remove_fleet_flag = dtp_mk_entered",
        B("solar_system", "save_global_event_target_as = dtp_mk_last_sys")),
      B("else_if", B("limit", "has_fleet_flag = dtp_mk_moving", "NOT = { has_fleet_flag = dtp_mk_entered }", "exists = solar_system", "exists = owner",
                     "NOT = { AND = { exists = event_target:dtp_mk_last_sys solar_system = { is_same_value = event_target:dtp_mk_last_sys } } }"),
        "remove_fleet_flag = dtp_mk_moving", B("solar_system", "save_global_event_target_as = dtp_mk_last_sys"),
        B("solar_system", B("if", B("limit", "prev = { owner = { has_country_flag = dtp_mk_unmode } }", "has_star_flag = dtp_marked"), "dtp_unmark_sys = yes", 'log = "DTP MARKER: (fallback) unmarked [This.GetName]"'),
          B("else_if", B("limit", "NOT = { prev = { owner = { has_country_flag = dtp_mk_unmode } } }", "NOT = { has_star_flag = dtp_marked }"), "dtp_mark_sys = yes", 'log = "DTP MARKER: (fallback) marked [This.GetName]"')),
        B("owner", "country_event = { id = dtp.1282 }")),
      B("else", "remove_fleet_flag = dtp_mk_moving", "remove_fleet_flag = dtp_mk_entered"))))
CAT.append(B("country_event", "id = dtp.1282", "hide_window = yes", "is_triggered_only = yes", B("immediate", "dtp_mlist_root = yes")))
# правило игры «можно ли поставить претензию»: для ведущего в режиме отметки — можно всегда и везде (в т. ч. на ничьи системы);
# для всех остальных — правило игры без изменений (копируется из файлов игры при сборке).
_rules = open(os.path.join(VC, "game_rules", "00_rules.txt"), encoding="utf-8-sig").read()
_m = re.search(r"(?m)^can_add_claim = \{", _rules); _i = _m.end(); _d = 1
while _d:
    _d += {"{": 1, "}": -1}.get(_rules[_i], 0); _i += 1
CLAIM_RULE = "can_add_claim = {\n\tOR = {\n\t\troot = { has_country_flag = dtp_claimmark }\n\t\tAND = {" + _rules[_m.end():_i - 1] + "\t\t}\n\t}\n}"
# 10.7.5: у правил игры при совпадении имени файл zz_ НЕ побеждает (в error.log нет «already exists», а претензии не заработали) —
# поэтому мод заменяет весь файл правил игры 00_rules.txt: копия игры, где изменено только правило can_add_claim.
RULES_FILE = _rules      # 10.8.5: отметка претензией убрана — can_add_claim как в игре
# 11.0: тип Гейм-мастера в правилах игры считается обычной державой — кроме сообщества/совета/империи (там он не участвует)
def _gm_regular(text, skip):
    out, pos = [], 0
    for _m in re.finditer(r"(?m)^(\w+) = \{", text):
        if _m.start() < pos: continue
        _i, _d = _m.end(), 1
        while _d: _d += {"{": 1, "}": -1}.get(text[_i], 0); _i += 1
        blk = text[_m.start():_i]
        if _m.group(1) not in skip:
            blk = blk.replace("is_country_type = default", "OR = { is_country_type = default is_country_type = dtp_gamemaster }")
        out.append(text[pos:_m.start()] + blk); pos = _i
    return "".join(out) + text[pos:]
RULES_FILE = _gm_regular(RULES_FILE, {"can_be_part_of_galactic_community", "can_be_part_of_galactic_council", "can_be_part_of_galactic_empire"})
assert RULES_FILE.count("can_see_galactic_community = {\n\tOR = {\n") == 1   # 11.0.6: Гейм-мастер видит окно сообщества (не член — голосовать не может)
RULES_FILE = RULES_FILE.replace("can_see_galactic_community = {\n\tOR = {\n", "can_see_galactic_community = {\n\tOR = {\n\t\thas_country_flag = dtp_gm_role\t# Debug Toolpack: the Game Master sees the Community\n", 1)
assert RULES_FILE.count("can_support_branch_offices = {\n") == 1
RULES_FILE = RULES_FILE.replace("can_support_branch_offices = {\n", "can_support_branch_offices = {\n\tcustom_tooltip = { fail_text = dtp_gm_nobranch NOT = { has_country_flag = dtp_gm_role } }\t# Debug Toolpack\n", 1)
assert RULES_FILE.count("has_full_sensor_range = {\n\tOR = {\n") == 1
RULES_FILE = RULES_FILE.replace("has_full_sensor_range = {\n\tOR = {\n", "has_full_sensor_range = {\n\tOR = {\n\t\thas_country_flag = dtp_gm_role\t# Debug Toolpack: Game Master sees everything\n", 1)
# 10.8.2: жёсткий запрет войн — и в правиле игры can_declare_war (root = нападающий, this = цель): кнопка серая везде, ИИ тоже не обходит
_RH = "OR = { AND = { root = { is_ai = no } is_ai = no } AND = { has_global_flag = dtp_war_ai OR = { root = { is_ai = no } is_ai = no } } }"
_SOFT = "NOT = { has_global_flag = dtp_war_soft }"
assert RULES_FILE.count("can_declare_war = {\n") == 1
RULES_FILE = RULES_FILE.replace("can_declare_war = {\n", "can_declare_war = {\n\t# --- Debug Toolpack: game master war ban, hard mode ---\n\tif = {\n\t\tlimit = { exists = root }\n" + "\n".join([
    # 11.0.3: Гейм-мастеру войну объявлять НЕЛЬЗЯ (this = цель); сам Гейм-мастер может всё
    "\t\tcustom_tooltip = { fail_text = dtp_gm_nowar NOT = { has_country_flag = dtp_gm_role } }",
    "\t\tcustom_tooltip = { fail_text = dtp_war_banned NOT = { AND = { root = { OR = { is_ai = no has_global_flag = dtp_war_ai } } has_global_flag = dtp_rule_nopvp %s } } }" % _SOFT,
    "\t\tcustom_tooltip = { fail_text = dtp_war_np NOT = { AND = { root = { has_country_flag = dtp_rule_np } %s } } }" % _SOFT,
    "\t\tcustom_tooltip = { fail_text = dtp_war_prot NOT = { AND = { OR = { root = { is_ai = no } has_global_flag = dtp_war_ai } has_country_flag = dtp_rule_prot %s } } }" % _SOFT]) + "\n\t}\n", 1)
CAT.append(B("event", "id = dtp.1207", "hide_window = yes", "is_triggered_only = yes",
    B("immediate", "dtp_war_sync = yes",
      B("every_country", B("limit", "has_country_flag = dtp_gm_role"),
        B("every_country", B("limit", "has_closed_borders = prev"), "set_closed_borders = { who = prev status = no }")),
      B("every_country", B("limit", "has_country_flag = dtp_claimmark"), "remove_country_flag = dtp_claimmark", "remove_modifier = dtp_claimfree"),
      B("every_country", B("limit", "is_ai = no"), B("every_owned_fleet", B("limit", "has_fleet_flag = dtp_beacon"), "delete_fleet = this")),
      B("every_country", B("limit", "is_ai = no"), B("every_owned_fleet", B("limit", "has_fleet_flag = dtp_marker", "NOT = { has_fleet_flag = dtp_mk_alive }"),
        "fleet_event = { id = dtp.1281 }", B("every_owned_ship", "add_modifier = { modifier = dtp_marker_ship days = -1 }"))),
      B("every_country", B("limit", "has_country_flag = dtp_open", "NOT = { dtp_has_any_perm = yes }", "any_country = { has_country_flag = dtp_host is_ai = no }"),
        "remove_country_flag = dtp_open"),
      B("if", B("limit", "has_global_flag = dtp_rule_was", "NOT = { has_global_flag = dtp_rule_nopvp }"),
        "remove_global_flag = dtp_rule_was", 'log = "DTP RULES: war ban expired"', B("every_country", B("limit", "is_ai = no"), "country_event = { id = dtp.1206 }")),
      B("if", B("limit", "has_global_flag = dtp_sess_warn_was", "NOT = { has_global_flag = dtp_sess_warn }"), "remove_global_flag = dtp_sess_warn_was",
        'log = "DTP SESSION: one month left"', B("every_country", B("limit", "is_ai = no"), "country_event = { id = dtp.1217 }")),
      B("if", B("limit", "has_global_flag = dtp_sess_was", "NOT = { has_global_flag = dtp_sess }"), "remove_global_flag = dtp_sess_was",
        'log = "DTP SESSION: time is up"', B("every_country", B("limit", "is_ai = no"), "country_event = { id = dtp.1218 }")),
      *[B("every_country", B("limit", "has_country_flag = dtp_rule_%s_was" % fl, "NOT = { has_country_flag = dtp_rule_%s }" % fl),
          "remove_country_flag = dtp_rule_%s_was" % fl, "save_global_event_target_as = dtp_rule_subj", 'log = "DTP RULES: personal rule %s expired"' % fl,
          B("every_country", B("limit", "is_ai = no"), "country_event = { id = dtp.%d }" % ev)) for fl, ev in (("np", 1213), ("prot", 1214))])))
cev(1216, "country_event", "§Y«ВЕДУЩИЙ»§! Таймер сессии",
    "Ведущий поставил таймер: сегодняшняя сессия закончится примерно в §Y[dtp_sess_owner.dtp_sess_y]§! году (через §Y[dtp_sess_owner.dtp_sess_m]§! мес. игрового времени). За месяц до конца придёт напоминание.\\n\\n§gОбъявление ведущего партии через Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1106")
cev(1217, "country_event", "§Y«ВЕДУЩИЙ»§! Сессия скоро закончится",
    "До конца сессии остался §Yодин месяц§! игрового времени. Завершайте дела, не начинайте крупных операций.\\n\\n§gТаймер сессии Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1106")
cev(1218, "country_event", "§Y«ВЕДУЩИЙ»§! Сессия окончена",
    "Время сессии вышло. §YСтавим паузу и сохраняемся§! — ХОСТ сохранит игру, продолжим в следующий раз.\\n\\n§gТаймер сессии Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1107")
cev(1211, "country_event", "§Y«ВЕДУЩИЙ»§! Личный запрет на войну",
    "Ведущий запретил державе §Y[dtp_rule_subj.GetName]§! объявлять войну до §Y[dtp_rule_subj.dtp_np_endy]§! года.\\n\\n§RПравило работает:§! её кнопка «Объявить войну» заблокирована; если война всё же начнётся, все получат оповещение, а ведущий может наказать нарушителя.\\n\\n§gОбъявление ведущего партии через Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1104")
cev(1212, "country_event", "§Y«ВЕДУЩИЙ»§! Держава под защитой",
    "Ведущий взял державу §Y[dtp_rule_subj.GetName]§! под защиту до §Y[dtp_rule_subj.dtp_prot_endy]§! года: игрокам нельзя объявлять ей войну.\\n\\n§RПравило работает:§! кнопка «Объявить войну» против неё у игроков заблокирована; если война всё же начнётся, все получат оповещение, а ведущий может наказать нарушителя.\\n\\n§gОбъявление ведущего партии через Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1104")
cev(1213, "country_event", "§Y«ВЕДУЩИЙ»§! Личный запрет истёк",
    "Срок личного запрета на войну для державы §Y[dtp_rule_subj.GetName]§! закончился.\\n\\n§gКонтроль правил Debug Toolpack.§!", [("Понятно", "")], pic="GFX_evt_dtp_ann_1103")
cev(1214, "country_event", "§Y«ВЕДУЩИЙ»§! Защита истекла",
    "Срок защиты державы §Y[dtp_rule_subj.GetName]§! закончился — на неё снова можно нападать.\\n\\n§gКонтроль правил Debug Toolpack.§!", [("Понятно", "")], pic="GFX_evt_dtp_ann_1103")
cev(1215, "country_event", "§Y«ВЕДУЩИЙ»§! Личные правила сняты",
    "Ведущий снял с державы §Y[dtp_rule_subj.GetName]§! личный запрет на войну и защиту.\\n\\n§gКонтроль правил Debug Toolpack.§!", [("Понятно", "")], pic="GFX_evt_dtp_ann_1103")
cev(1009, "country_event", "§Y«ВЕДУЩИЙ»§! Белый мир",
    "Ведущий завершил войну между §Y[dtp_wp_a.GetName]§! и §Y[dtp_wp_b.GetName]§! белым миром: никто ничего не получает, стороны заключают перемирие.\\n\\n§gОбъявление ведущего партии через Debug Toolpack.§!",
    [("Понятно", "")], pic="GFX_evt_dtp_ann_1115")
cev(1008, "country_event", "Объявление администратора", "Администратор §Y[dtp_last_actor.GetName]§! вносит изменения через Debug Toolpack.", [("Понятно", "")])


# ======================================================================= КАРТОЧКИ (автоматически по рядам каждого раздела)
def build_cards():
    """8.0: без рамок вокруг групп — только оранжевая метка и тонкая линия под заголовком группы.
    9.2: метка видна только на той странице раздела, где стоит заголовок (Мастер игры, Модификаторы)."""
    out = []
    PG = re.compile(r"NOT = \{ check_variable = \{ which = dtp_(?:gm|mod)page value >?= \d \} \}|check_variable = \{ which = dtp_(?:gm|mod)page value = \d \}")
    for t, name, p in TABS:
        tag = "which = dtp_tab value = %d }" % t
        cw = CWN if t in NUMTABS else CWF
        heads = {}
        for g_ in GUI:
            m_ = META[GUI.index(g_)]
            if g_["where"] == "main" and g_["label"] and g_["w"] >= cw - 4 and CY <= g_["y"] < BAR_Y - 40 and "noperm" not in g_["key"] \
                    and m_["pot"].find(tag) >= 0 and m_["text"].startswith("§Y"):
                pm = PG.search(m_["pot"]); heads[((g_["y"] - CY) // ROW, pm.group(0) if pm else "")] = 1
        for hr, cond in sorted(heads):
            suf = "" if not cond else "_p" + re.sub(r"\D", "", cond.split("value")[1]) + ("n" if cond.startswith("NOT") else "")
            pot = OPEN + "\n" + T(t) + ("\n" + B("from", cond) if cond else "")
            for kind, x, y, w, h, spr in [("acc", CX0, CY + hr * ROW + 6, 3, 18, "GFX_dtp_accent"), ("line", CX0, CY + hr * ROW + 28, cw, 2, "GFX_dtp_divider")]:
                out.append(dict(key="dtp_b_h%s_%d_%d%s" % (kind, t, hr, suf), x=x, y=y, w=w, h=h, sprite=spr, tt=None, label=True, font="cg_16b", where="main", shortcut=None, text="", pot=pot))
                BTN.append(B(out[-1]["key"], B("potential", pot), B("allow", "always = yes"), B("effect", "")))
                L[out[-1]["key"]] = ""
    return out
_cards = build_cards()
GUI[CARD_SLOT:CARD_SLOT] = _cards
META[CARD_SLOT:CARD_SLOT] = [dict(c, text="") for c in _cards]
for _c in _cards: _c.pop("pot", None); _c.pop("text", None)

# ================================================================ ФАЙЛЫ
SKIN = {}   # 7.1: все текстуры окна рисует сам мод (art3.py) в стиле интерфейса Stellaris
def gui_el(g, extra=()):
    parts = ['name = "%s"' % g["key"], "position = { x = %d y = %d }" % (g["x"], g["y"]), "size = { x = %d y = %d }" % (g["w"], g["h"]),
             'quadTextureSprite = "%s"' % SKIN.get(g["sprite"], g["sprite"]), 'font = "%s"' % g["font"], 'buttonText = "%s"' % g["key"], 'effect = "%s"' % g["key"]]
    if g["tt"]: parts.append('tooltipText = "%s"' % g["tt"])
    if g.get("shortcut"): parts.append('shortcut = "%s"' % g["shortcut"])
    parts += ["format = left"] if g["label"] else ["clicksound = interface", "oversound = mouse_over"]
    return B("effectbuttonType", *parts, *extra)
main_children = [gui_el(g) for g in GUI if g["where"] == "main"]
# Главное окно: dropDownBoxType. Значок = expandButton (открыть/закрыть без скрипта),
# expandedWindow = перетаскиваемое окно с фоном. Отдельная невидимая кнопка-эффект поверх значка
# при первом нажатии выдаёт игроку номер и цели по умолчанию.
# Окно: маленькая перетаскиваемая ручка (как корень окна флота в игре: корень 45 px, содержимое выше).
# Само окно — кнопки-эффекты, видимые по флагу dtp_open, висят под ручкой за её границами (clipping = no).
DX, DY = HW - W, HH + 4
dtp_root = B("containerWindowType", 'name = "dtp_root"', ("position = { x = -360 y = 50 }" if UIOD else "position = { x = -360 y = 40 }"), "size = { width = %d height = %d }" % (HW, HH + HDRAG),
    "orientation = UPPER_RIGHT", "origo = UPPER_RIGHT", "moveable = yes", "clipping = no",
    B("background", 'name = "bg"', 'quadTextureSprite = "GFX_dtp_label"'),
    *[gui_el(g) for g in GUI if g["where"] == "handle"],
    *[gui_el(dict(g, x=g["x"] + DX, y=g["y"] + DY)) for g in GUI if g["where"] == "main"])
loc("dtp_toggle_tt", "Debug Toolpack: открыть или закрыть окно. Окно перетаскивается за шапку.")
for _nm, _cond, _w in (("planet", SPL, 520 if UIOD else 620), ("fleet", SFL, 440), ("starbase", SSB, 536)):
    lab("%s_bg" % _nm[:2], "", -8, -2, _w, h=96, where=_nm, potential=_cond)
    GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_panel"
    GUI.insert(0, GUI.pop()); META.insert(0, META.pop())      # первым — рисуется под кнопками полосы
planet_strip = B("containerWindowType", 'name = "dtp_planet_strip"', ("position = { x = 362 y = 112 }" if UIOD else "position = { x = 14 y = 686 }"), ("size = { width = 520 height = 96 }" if UIOD else "size = { width = 620 height = 96 }"), "moveable = yes",
    B("background", 'name = "bg"', 'quadTextureSprite = "GFX_dtp_label"'), *[gui_el(dict(g, x=g["x"] + 8, y=g["y"] + 2)) for g in GUI if g["where"] == "planet"])
fleet_strip = B("containerWindowType", 'name = "dtp_fleet_strip"', ("position = { x = 606 y = -60 }" if UIOD else "position = { x = 516 y = -60 }"), "size = { width = 440 height = 96 }", "moveable = yes",
    B("background", 'name = "bg"', 'quadTextureSprite = "GFX_dtp_label"'), *[gui_el(dict(g, x=g["x"] + 8, y=g["y"] + 2)) for g in GUI if g["where"] == "fleet"])

starbase_strip = B("containerWindowType", 'name = "dtp_starbase_strip"', *(["position = { x = 62 y = 134 }"] if UIOD else ["position = { x = 14 y = -330 }", "orientation = lower_left"]), "size = { width = 536 height = 96 }", "moveable = yes",
    B("background", 'name = "bg"', 'quadTextureSprite = "GFX_dtp_label"'), *[gui_el(dict(g, x=g["x"] + 8, y=g["y"] + 2)) for g in GUI if g["where"] == "starbase"])
def w(path, text, bom=False):
    p = os.path.join(OUT, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    text = text.replace("§O", "§H")                              # §O в игре нет (error.log: «no coloring for 'O'») — оранжевый это §H
    if path.endswith(".yml"):                                    # 10.7.9: этих значков нет в шрифте игры — на экране квадратики (скриншоты 22.10)
        for _a, _b in (("✔ ", "§G●§! "), ("✔", "§G●§!"), ("↻ ", ""), ("↻", ""), ("⇄ ", "→ "), ("⇄", "→"), ("↶", "←"), ("✕", "×"),
                       ("⌂ ", ""), ("⌂", ""), ("‹", "<"), ("›", ">"), ("↔", "/"), ("↺ ", ""), ("↺", ""), ("◎ ", ""), ("◎", "")):
            text = text.replace(_a, _b)
        if "english" in path:                                    # 10.9.9: в английском шрифте игры нет этих знаков — на экране «?» (22.10)
            for _a, _b in (("—", "-"), ("–", "-"), ("→", "->"), ("←", "<-"), ("−", "-"), ("…", "..."), ("●", "*")):
                text = text.replace(_a, _b)
    with open(p, "w", encoding="utf-8-sig" if bom else "utf-8", newline="\n") as f: f.write(text)
GUI_REPORT = []
def end_of_window(src, name):
    """Позиция перед закрывающей скобкой окна верхнего уровня `name` (вставка поверх его содержимого)."""
    m = re.search(r'\n\tcontainerWindowType = \{\s*\n\t\tname = "%s"' % name, src)
    if not m: return None
    i = src.index("{", m.start()) + 1; d = 1
    while d:
        d += {"{": 1, "}": -1}.get(src[i], 0); i += 1
    return src.rindex("\n", 0, i - 1) + 1
def inject(fname, rx, block, indent, window):
    """Вставка окна мода в игровой файл интерфейса. Сначала — в привычное место (rx); если файл другой
    (например, UI Overhaul Dynamic) и места нет — в конец окна `window` верхнего уровня. Если нет и его — сборка останавливается."""
    src = open(os.path.join(VI, fname), encoding="utf-8-sig").read()
    ins = "\n".join(indent + l for l in pretty(block).splitlines()) + "\n"
    m = re.search(rx, src, re.S) if rx else None
    if m:
        pos, how = m.end(), "обычное место"
        ins = "\n" + indent + "### DEBUG TOOLPACK (DTP) — добавлено модом\n" + ins
    else:
        pos, how = end_of_window(src, window), "конец окна %s" % window
        assert pos is not None, "%s: нет окна %s — нужен ручной патч" % (fname, window)
        ins = indent + "### DEBUG TOOLPACK (DTP) — добавлено модом\n" + ins
    GUI_REPORT.append("%s → %s" % (fname, how))
    w("interface/" + fname, src[:pos] + ins + src[pos:])
inject("main.gui", r'name = "maingui_flag".*?button_topbar_government.*?\n\t\t\}\n', dtp_root, "\t\t", "maingui_flag")
inject("planet_view.gui", r'name = "planet_view_bg".*?\n\t\t\}\n', planet_strip, "\t\t", "planet_view")
_mi = open(os.path.join(VI, "mapicons.gui"), encoding="utf-8-sig").read()
for ic in MAP_ICONS:
    els = [gui_el(g) for g in GUI if g["where"] == "map:" + ic]
    end = end_of_window(_mi, ic); assert end, ic
    _mi = _mi[:end] + "\t\t### DEBUG TOOLPACK (DTP)\n" + "\n".join("\t\t" + l for l in pretty("\n".join(els)).splitlines()) + "\n" + _mi[end:]
if MAP_ICONS: w("interface/mapicons.gui", _mi)
inject("starbase_view.gui", None, starbase_strip, "\t\t", "starbase_view")     # окно станции: в конец корневого контейнера (поверх содержимого)
inject("fleet_view.gui", r'\tcontainerWindowType = \{\n\t\tname = "fleet_view".*?name = "header".*?\n\t\t\}\n', fleet_strip, "\t\t", "fleet_view")
print("встраивание в окна игры: " + "; ".join(GUI_REPORT))
# 10.8.0: каждая кнопка с подтверждением должна сбрасываться dtp_disarm (иначе бар «ПОДТВЕРДИТЬ» висит — так было у Цетаны и Хана)
assert not (ARMS_USED - set(ARMS)), "кнопки с подтверждением не сбрасываются dtp_disarm: %s" % sorted(ARMS_USED - set(ARMS))
HDR = "# Debug Toolpack %s — сгенерировано tools/gen3.py. Правьте генератор, а не этот файл.\n" % VERSION
# Игра читает из одного файла не больше ~1 МБ — всё дальше молча теряется (кнопки без описания видны всегда).
# Кнопки раскладываются по файлам до ~120 КБ: если игра споткнётся на одной кнопке, она теряет только хвост своего файла.
_parts, _cur, _sz = [], [], 0
for _b in BTN:
    _t = pretty(_b) + "\n"
    if _cur and _sz + len(_t.encode()) > 120000:
        _parts.append(_cur); _cur, _sz = [], 0
    _cur.append(_t); _sz += len(_t.encode())
_parts.append(_cur)
for _i, _c in enumerate(_parts, 1):
    w("common/button_effects/dtp_buttons_%02d.txt" % _i, HDR + "".join(_c))
w("common/scripted_effects/dtp_scripted_effects.txt", HDR + pretty("\n".join(EFF)))
w("common/scripted_triggers/dtp_scripted_triggers.txt", HDR + pretty("\n".join(TRG)))
w("common/game_rules/00_rules.txt", RULES_FILE)
_st = open(os.path.join(VC, "scripted_triggers", "00_scripted_triggers.txt"), encoding="utf-8-sig").read()
assert "is_regular_empire = {" in _st
w("common/scripted_triggers/00_scripted_triggers.txt", "# Debug Toolpack " + VERSION + ": copy of the game file; the Game Master country type (dtp_gamemaster) counts as a regular empire.\n" +
  _st.replace("is_country_type = default", "OR = { is_country_type = default is_country_type = dtp_gamemaster }"))
# тип державы Гейм-мастера: копия обычного (default), «неигровой» как у угасших, без роста населения и без дипломатических войн
_ct = open(os.path.join(VC, "country_types", "00_country_types.txt"), encoding="utf-8-sig").read()
_m = re.search(r"(?m)^default = \{", _ct); _i, _d = _m.end(), 1
while _d: _d += {"{": 1, "}": -1}.get(_ct[_i], 0); _i += 1
_gm = "dtp_gamemaster" + _ct[_m.start() + len("default"):_i]
for _a, _b in (("playable = yes", "playable = no"), ("pop_growth = yes", "pop_growth = no"), ("counts_for_victory = yes", "counts_for_victory = no"), ("needs_survey = yes", "needs_survey = yes")):
    assert _gm.count("\t" + _a) == 1, _a; _gm = _gm.replace("\t" + _a, "\t" + _b, 1)
_ctv = "\n".join(sorted(set(v for v in re.findall(r"^@\w+ = .*$", _ct, re.M) if v.split()[0] in _gm)))
w("common/country_types/dtp_country_types.txt", "# Debug Toolpack " + VERSION + ": Game Master country type (copy of 'default', not playable like Fallen Empires)\n" + (_ctv + "\n\n" if _ctv else "") + _gm + "\n")
# закрытая этика: выбрать при создании нельзя, выдаётся только ролью Гейм-мастера
w("common/ethics/dtp_ethics.txt", "# Debug Toolpack " + VERSION + ": closed Game Master ethic (only via the Game Master role)\n" + pretty(B("ethic_dtp_gamemaster",
    "cost = 1", 'category = "hive"', "category_value = 1", "use_for_pops = no", B("playable", "always = no"),
    B("country_modifier", "intel_encryption_add = 5"), B("random_weight", "base = 0"))))
w("common/event_chains/dtp_event_chains.txt", HDR + pretty(B("dtp_marks_chain", 'icon = "gfx/interface/icons/situation_log/situation_log_quest.dds"',
    "picture = GFX_evt_dtp_events", "situation_log_category = developments")))
w("common/star_classes/dtp_marked_star_classes.txt", HDR + "# Копии классов звёзд игры 4.5.2 со значком «отмечено» (красное кольцо) для галактической карты.\n"
  "# spawn_odds = 0: при генерации галактики не выпадают. Свет, звезда, модификаторы — как у исходного класса.\n" + pretty("\n".join(MARKED_SC)))
MARKER_STATIC = ["dtp_gm_role = {\n" + "\n".join("\t%s = %s" % kv for kv in [
        ("country_physics_research_produces_mult", 999), ("country_society_research_produces_mult", 999), ("country_engineering_research_produces_mult", 999),
        ("country_energy_produces_mult", 999), ("country_minerals_produces_mult", 999), ("country_food_produces_mult", 999), ("country_alloys_produces_mult", 999),
        ("country_consumer_goods_produces_mult", 999), ("country_unity_produces_mult", 999), ("country_influence_produces_mult", 999),
        ("add_base_country_intel", 1000), ("intel_encryption_add", 1000), ("intel_decryption_add", 1000),
        ("planet_stability_add", 50), ("country_resource_max_add", 10000000), ("logistic_growth_mult", -1), ("planet_pop_assembly_mult", -1), ("bonus_pop_growth_mult", -1)]) + "\n}",
                 "dtp_marker_ship = {\n\tship_speed_mult = 5000\n\tship_interstellar_speed_mult = 5000\n\tship_base_speed_mult = 50\n\tship_windup_mult = -0.999\n\tship_cloaking_strength_add = 1000\n\tship_ftl_jumpdrive_range_mult = 1000\n\tship_jumpdrive_cooldown_mult = -0.999\n\tship_emergency_ftl_min_days_mult = -0.999\n\tship_evasion_add = 90\n}",
                 "dtp_beacon_ship = {\n\tship_cloaking_strength_add = 1000\n\tship_evasion_add = 90\n}",
                 "dtp_war_lock = {\n\ticon = \"gfx/interface/icons/modifiers/mod_war_economy_offensive.dds\"\n}",
                 "dtp_war_shield = {\n\ticon = \"gfx/interface/icons/modifiers/mod_war_economy_defensive.dds\"\n}",
                 "dtp_claimfree = {\n\tcountry_claim_influence_cost_mult = -1\n\tcountry_hostile_claim_influence_cost_mult = -1\n}"]
loc("dtp_claimfree", "Отметка претензией (Debug Toolpack)")
loc("dtp_war_lock", "Запрет войн ведущего")
loc("dtp_marker_ship", "Корабль-метка Debug Toolpack")
loc("dtp_marker_ship_desc", "Служебный корабль ведущего для отметки систем: маскировка 1000, очень высокая скорость.")
loc("dtp_marker_fleet", "Метка ведущего")
loc("dtp_marker_ship_name", "Метка DTP")
loc("dtp_beacon_fleet", "● Отмечено")
loc("dtp_mark_mega", "§R●  ОТМЕЧЕНО§!")
loc("dtp_mark_mega_name", "§R●  ОТМЕЧЕНО§!")
loc("dtp_mark_mega_MEGASTRUCTURE_DETAILS", "Метка ведущего партии (Debug Toolpack). Ничего не делает.")
loc("dtp_mark_mega_DESC", "Метка ведущего партии (Debug Toolpack): система отмечена. Ничего не делает, снимается кнопкой мода.")
w("common/megastructures/dtp_mark_megastructure.txt", "# Debug Toolpack " + VERSION + ": red map marker over a marked system (invisible model, only the galaxy map label)\n" + pretty(B("dtp_mark_mega",
    'entity = "invisible_turret_entity"', 'portrait = "GFX_megastructure_construction_background"', "show_in_outliner = no",
    "place_entity_on_planet_plane = no", B("potential", "always = no"), B("possible", "always = no"))))
loc("dtp_beacon_ship", "Маяк DTP")
loc("dtp_beacon_ship_desc", "Маяк отметки ведущего: маскировка 1000 — виден только ХОСТу.")
loc("DTP_Marker", "Метка DTP")
w("common/global_ship_designs/dtp_marker_design.txt", "# Debug Toolpack " + VERSION + ": generated by tools/gen3.py\n# 10.8.5: marker ship of the game master (science hull, psi jump drive, psi cloak)\n" + pretty(B("ship_design", 'name = "DTP_Marker"', "ship_size = science",
    B("section", 'template = "DEFAULT_SCIENCESHIP_SECTION"', 'slot = "mid"'),
    'required_component = "SHIP_THRUSTER_4"', 'required_component = "SENSOR_1"', 'required_component = "PSI_JUMP_DRIVE_1"', 'required_component = "SCIENCE_CLOAKING_PSI"')))
loc("dtp_war_lock_desc", "Ведущий партии запретил этой державе объявлять войну (Debug Toolpack, жёсткий режим). Кнопка «Объявить войну» недоступна, пока действует запрет; модификатор снимется сам, когда запрет закончится или ведущий его снимет.")
loc("dtp_war_shield", "Защита ведущего")
loc("dtp_war_shield_desc", "Ведущий партии взял эту державу под защиту (Debug Toolpack, жёсткий режим): игроки не могут объявить ей войну, пока действует защита.")
loc("dtp_claimfree_desc", "Пока включён режим отметки претензией, претензии ведущего бесплатны: каждая сразу превращается в отметку системы и убирается.")
w("common/static_modifiers/dtp_static_modifiers.txt", HDR + pretty("\n".join(UMOD_STATIC + INC_STATIC + MARKER_STATIC)))
w("common/system_tooltips/dtp_system_tooltips.txt", HDR + "# root = система, from = смотрящий игрок\n" + pretty(B("dtp_marked_tooltip", B("custom_tooltip", "success_text = dtp_marked_tt", "has_star_flag = dtp_marked"))))
loc("dtp_marked_tt", "§R●§! Отмечено в Debug Toolpack")
w("common/opinion_modifiers/dtp_opinion_modifiers.txt", HDR + "dtp_opinion_good = {\n\topinion = { base = 100 }\n\tdecay = { base = 1 }\n}\ndtp_opinion_bad = {\n\topinion = { base = -100 }\n\tdecay = { base = 1 }\n}\n")
loc("dtp_opinion_good", "Toolpack: улучшение отношений"); loc("dtp_opinion_bad", "Toolpack: ухудшение отношений")
w("events/dtp_events.txt", HDR + "namespace = dtp\n\n" + pretty("\n".join(EVENTS)))
w("common/on_actions/dtp_on_actions.txt", HDR + "on_game_start = {\n\tevents = {\n\t\tdtp.1250\n\t}\n}\non_war_beginning = {\n\tevents = {\n\t\tdtp.1201\n\t}\n}\non_monthly_pulse = {\n\tevents = {\n\t\tdtp.1207\n\t}\n}\non_entering_system_fleet = {\n\tevents = {\n\t\tdtp.1280\n\t}\n}\n")
# 9.4: запрет блокирует саму кнопку «Объявить войну». Игровой файл дипломатических действий копируется целиком
# (тот же путь — заменяет оригинал) и в action_declare_war → possible дописываются проверки правил партии.
loc("dtp_note_humans", "§Y● Только живые игроки§! §g— державы ИИ не затрагиваются.§!")
loc("dtp_note_pvp", "§Y● Только между живыми игроками§! §g— войны с ИИ и между ИИ идут как обычно.§!")
loc("dtp_gm_nowar", "§RЭто держава Гейм-мастера:§! ей нельзя объявить войну (Debug Toolpack).")
loc("dtp_gm_noclose", "§RЭто держава Гейм-мастера:§! закрывать для неё границы нельзя (Debug Toolpack).")
loc("dtp_gm_nobranch", "§RЭто держава Гейм-мастера:§! филиалы мегакорпораций и синдикатов на её планетах запрещены (Debug Toolpack).")
loc("ethic_dtp_gamemaster", "Гейм-мастер")
loc("ethic_dtp_gamemaster_desc", "Закрытая этика ведущего партии (Debug Toolpack). Её нельзя выбрать при создании державы — только взять роль Гейм-мастера.")
loc("dtp_gm_role", "Роль Гейм-мастера")
loc("dtp_gm_role_desc", "Держава ведущего партии (Debug Toolpack): видит всю галактику, огромные бонусы к науке и ресурсам, население не растёт, в Галактическом сообществе не участвует.")
loc("dtp_gamemaster", "Гейм-мастер")
loc("dtp_war_banned", "§RЗапрещено ведущим партии:§! сейчас объявлять войну нельзя никому — как при политике «Оборонительные войны» (Debug Toolpack → «Правила партии»).")
loc("dtp_war_np", "§RЗапрещено ведущим партии:§! вашей державе лично запрещено объявлять войну (Debug Toolpack).")
loc("dtp_war_prot", "§RЗапрещено ведущим партии:§! эта держава под защитой ведущего — на неё нельзя нападать (Debug Toolpack).")
DA = os.path.join(VC, "diplomatic_actions", "00_actions.txt")
def _gm_action(key, tip, cond="NOT = { has_country_flag = dtp_gm_role }"):
    """11.0: копия действия игры + запрет для Гейм-мастера (root = тот, кто действует)."""
    _t = open(DA, encoding="utf-8-sig").read()
    _a = _t.index("%s = {" % key); _b, _d = _t.index("{", _a) + 1, 1
    while _d: _d += {"{": 1, "}": -1}.get(_t[_b], 0); _b += 1
    blk = _t[_a:_b]; _p = blk.index("possible = {") + len("possible = {")
    return "\n" + blk[:_p] + "\n\t\tcustom_tooltip = { fail_text = %s %s }" % (tip, cond) + blk[_p:] + "\n"
_da = open(DA, encoding="utf-8-sig").read()
_i = _da.index("action_declare_war = {")
_k, _depth = _da.index("{", _i), 0                       # конец блока по балансу скобок
for _e in range(_k, len(_da)):
    _depth += {"{": 1, "}": -1}.get(_da[_e], 0)
    if _depth == 0: break
_blk = _da[_i:_e + 1]
_j = _blk.index("possible = {") + len("possible = {")
_ins = "\n".join(["", "\t\t# --- Debug Toolpack: game master war rules (dtp_rule_nopvp / dtp_rule_np / dtp_rule_prot) ---",
    "\t\tcustom_tooltip = { fail_text = dtp_gm_nowar NOT = { from = { has_country_flag = dtp_gm_role } } }",
    # 10.7.9: «мягкий» режим (dtp_war_soft) — кнопка доступна, нарушение фиксируется и решает ведущий; dtp_war_ai — правило и для войн с ИИ
    # 10.8.3: жёсткий запрет — как политика «Оборонительные войны»: держава под запретом не объявляет войну НИКОМУ (root = actor, from = recipient)
    "\t\tcustom_tooltip = { fail_text = dtp_war_banned NOT = { AND = { OR = { is_ai = no has_global_flag = dtp_war_ai } has_global_flag = dtp_rule_nopvp NOT = { has_global_flag = dtp_war_soft } } } }",
    "\t\tcustom_tooltip = { fail_text = dtp_war_np NOT = { AND = { has_country_flag = dtp_rule_np NOT = { has_global_flag = dtp_war_soft } } } }",
    "\t\tcustom_tooltip = { fail_text = dtp_war_prot NOT = { AND = { OR = { is_ai = no has_global_flag = dtp_war_ai } from = { has_country_flag = dtp_rule_prot } NOT = { has_global_flag = dtp_war_soft } } } }"])
_vars = "\n".join(sorted(set(re.findall(r"^@\w+ = .*$", _da, re.M))))   # переменные @..., если блок их использует
w("common/diplomatic_actions/zz_dtp_declare_war.txt",
  "# Debug Toolpack %s: action_declare_war from the game (4.5) + game master war rules in possible.\n"
  "# diplomatic_actions are LIOS: this later-loaded file replaces only this one action, the rest of the game file stays untouched.\n" % VERSION +
  (_vars + "\n\n" if "@" in _blk else "") + _blk[:_j] + _ins + _blk[_j:] + "\n" +
  _gm_action("action_close_borders", "dtp_gm_noclose", "NOT = { from = { has_country_flag = dtp_gm_role } }"))   # 11.0.4: закрыть границы ДЛЯ Гейм-мастера нельзя
# 10.0: режим карты «Правила партии» — раскраска держав по правилам ведущего (this = держава, from = смотрящий игрок)
MMC = [("dtp_mm_viol", "rgb { 255 140 30 255 }", "has_global_flag = dtp_viol_open\nexists = event_target:dtp_violator\nis_same_value = event_target:dtp_violator",
        "§O[This.GetName]§! — нарушил запрет войн, ведущий решает о санкциях"),
       ("dtp_mm_prot", "rgb { 60 220 110 255 }", "has_country_flag = dtp_rule_prot", "§G[This.GetName]§! — под защитой ведущего: игрокам нельзя нападать"),
       ("dtp_mm_np", "rgb { 230 50 50 255 }", "has_country_flag = dtp_rule_np", "§R[This.GetName]§! — ведущий лично запретил объявлять войну"),
       ("dtp_mm_ban", "rgb { 70 140 255 255 }", "is_ai = no\nhas_global_flag = dtp_rule_nopvp", "§B[This.GetName]§! — игрок, действует общий запрет войн"),
       ("dtp_mm_pl", "rgb { 220 220 235 255 }", "is_ai = no", "§Y[This.GetName]§! — игрок, войны разрешены"),
       ("dtp_mm_ai", "rgb { 70 70 80 255 }", "always = yes", "[This.GetName] — держава ИИ")]
for k_, _, _, t_ in MMC: loc(k_, t_)
loc("dtp_rules_map_mode", "Правила партии (Debug Toolpack)")
loc("dtp_rules_map_mode_desc", "Режим карты ведущего: §Oоранжевый§! — нарушитель, §Gзелёный§! — под защитой, §Rкрасный§! — лично запрещено нападать, §Bсиний§! — игрок при общем запрете войн, светлый — игрок, тёмный — ИИ.")
w("common/map_modes/dtp_map_modes.txt", HDR + pretty(B("dtp_rules_map_mode", 'icon = "GFX_dtp_map_mode"', "enable_terra_incognita = yes", "can_change_point_of_view = no",
    "display_claims = no", *[B("color", "type = country_and_borders", "value = %s" % c_, "custom_tooltip = %s" % k_, B("condition", cond_)) for k_, c_, cond_, _ in MMC])) + "\n")
w("events/dtp_catalog_events.txt", HDR + "namespace = dtp\n\n" + pretty("\n".join(CAT)))
CUSTOM = ["# Перезаписывается редактором шаблонов (tools/event_template_editor.html).",
          "# Контекст: кнопка в окне Toolpack. From = нажавший игрок; event_target:dtp_t — выбранная держава,",
          "# dtp_p — выбранная планета, dtp_f — выбранный флот, dtp_r — получатель."]
CUSTOM_T, CUSTOM_L = [], {}
for k in range(9, 17):
    CUSTOM.append('dtp_custom_fire_%d = {\n\tlog = "DTP: custom slot %d is empty"\n}' % (k, k - 8))
    CUSTOM_T.append("dtp_custom_valid_%d = {\n\talways = no\n}" % k)
    CUSTOM_L["dtp_cat_%d_name" % k] = "Слот %d" % (k - 8); CUSTOM_L["dtp_cat_%d_desc" % k] = "Пустой пользовательский слот."
w("common/scripted_effects/dtp_custom_catalog.txt", pretty("\n".join(CUSTOM)))
w("common/scripted_triggers/dtp_custom_triggers.txt", pretty("\n".join(CUSTOM_T)))
w("descriptor.mod", 'version="%s"\ntags={\n\t"Utilities"\n\t"Gameplay"\n\t"Graphics"\n}\nname="Debug Toolpack (DTP)"\npicture="thumbnail.png"\nsupported_version="v4.5.*"\n' % VERSION)
import re as _re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_extract import norm as _norm, digits as _digits, denorm as _denorm
_ENMAP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", "en_map.json"), encoding="utf-8"))
_EN_MISS = []
def _en(v):
    """Русская строка → английская по словарю i18n/en_map.json (цифры в [...] и отступ сохраняются)."""
    m_note = _re.match(r"^(.*?)(\\n\\n\$dtp_note_\w+\$)$", v, _re.S)
    if m_note: return _en(m_note.group(1)) + m_note.group(2)      # пометка «только игроки» — отдельный ключ перевода
    if not _re.search(r"[А-Яа-яЁё]", v): return v
    n = _norm(v)
    t = _ENMAP.get(n)
    if t is None:
        m = _re.match(r"^Слот (\d+)$", v)
        if m: return "Slot %s" % m.group(1)
        if v == "Пустой пользовательский слот.": return "Empty custom slot."
        _EN_MISS.append(v); return v
    lead = v[:len(v) - len(v.lstrip(" "))]
    return lead + _denorm(t.lstrip(" "), _digits(v))
def yml(lang, d):
    rows = []
    for k, v in d.items():
        v = v.replace('"', "'")
        if lang == "english":
            v = _en(v)
            for _a, _b in (("—", "-"), ("–", "-"), ("→", "->"), ("←", "<-"), ("−", "-"), ("…", "..."), ("●", "*")):
                v = v.replace(_a, _b)
        rows.append(' %s:0 "%s"' % (k, v))
    return "l_%s:\n" % lang + "\n".join(rows) + "\n"
for lang in ("russian", "english"):
    w("localisation/%s/dtp_l_%s.yml" % (lang, lang), yml(lang, L), True)
    w("localisation/%s/dtp_custom_l_%s.yml" % (lang, lang), yml(lang, CUSTOM_L), True)
json.dump({"W": W, "H": H, "items": META, "stars": STARCLS}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_meta3.json"), "w", encoding="utf-8"), ensure_ascii=False)
if _EN_MISS:
    print("!! нет английского перевода для %d строк:" % len(_EN_MISS)); [print("   ", s) for s in sorted(set(_EN_MISS))[:40]]
    json.dump(sorted({_norm(s) for s in _EN_MISS}), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", "missing.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("кнопок %d · отмеченных классов звёзд %d · ключей %d" % (len(BTN), len(STARCLS), len(L)))
