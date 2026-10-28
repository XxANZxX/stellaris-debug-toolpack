# -*- coding: utf-8 -*-
# 11.3: РЕДАКТОР ПЛАНЕТЫ И СИСТЕМЫ — отдельное окно (как «Редактор держав и вида»). Выполняется внутри gen3.py (exec),
# после editor3.py: пользуется его card-раскладкой и общими помощниками (button, act, B, GUI/META/L, gspr, EW/EH…).
# Окно живёт в своём файле интерфейса (dtp_planet_editor.gui — главное окно игры «maingui», перенесённое из main.gui),
# поэтому не занимает место в main.gui и main_bottom.gui (у каждого файла предел ~1 МБ).
# Работает с ЛЮБОЙ планетой: выбранной в окне планеты (полоса Toolpack → «Выбрать» или «Редактор планеты»).
# Правила игры (potential / allow / prerequisites зданий, районов, зон, залежей, специализаций) — красная пометка;
# такое ставится только в принудительном режиме.
import pedata as _pd

PEOPEN = "has_country_flag = dtp_pe_open"
def PEP(tab=None, cat=None, pg=None, extra=""):
    c = [PEOPEN] + ([chk("dtp_petab", tab)] if tab else []) + ([chk("dtp_pecat", cat)] if cat else []) + ([chk("dtp_pepg", pg)] if pg else [])
    return B("from", *c) + ("\n" + extra if extra else "")
def pb(name, ru, en, x, y, w, h=30, pot="", allow="", effect="", tt=None, sprite="GFX_dtp_btn", label=False, left=False, font="cg_16b", transp=False):
    tren(ru, en)
    if tt:
        tt = (tt[0].replace("\n", "\\n"), tt[1].replace("\n", "\\n"))
        tren(tt[0], tt[1])
    k = button("pe_" + name, ru, x, y, w, h, potential=pot, allow=allow, effect=effect, tt=tt[0] if tt else ("" if label else None), sprite=sprite, label=label, font=font, where="peditor")
    if left: GUI[-1]["left"] = META[-1]["left"] = True
    if transp: GUI[-1]["transp"] = True
    return k
def plab(name, ru, en, x, y, w, pot="", h=24, font="cg_16b", sprite="GFX_dtp_label"):
    return pb(name, ru, en, x, y, w, h, pot=pot, sprite=sprite, label=True, font=font)
def pdeco(name, x, y, w, h, sprite, pot):
    lab("pe_" + name, "", x, y, w, h=h, potential=pot, where="peditor"); GUI[-1]["sprite"] = META[-1]["sprite"] = sprite

# ---- условия на выбранную планету игрока (у каждого игрока своя)
TRG.append(B("dtp_tpx", orchain(lambda k: B("event_target:dtp_tp_%d" % k, "$T$ = yes"))))
_POK = {}
def pok(name, body):
    """Именованное условие «игра это разрешает» в области выбранной планеты."""
    nm = "dtp_pok_" + name
    if nm not in _POK:
        _POK[nm] = "trivial" if not (body or "").strip() else 1
        TRG.append(B(nm, body or "always = yes"))
    return "dtp_tpx = { T = %s }" % nm
_PHS = set()
def phas(name, body):
    nm = "dtp_ph_" + name
    if nm not in _PHS: _PHS.add(nm); TRG.append(B(nm, body))
    return "dtp_tpx = { T = %s }" % nm
loc("dtp_pe_lock", "§RИгра обычно это запрещает§! (тип или размер планеты, владелец, технологии, особые условия). Включите §Yпринудительный режим§! внизу окна, чтобы поставить всё равно.")
tren(L["dtp_pe_lock"], "§RThe game normally forbids this§! (planet type or size, owner, technologies, special conditions). Turn on §Yforce mode§! at the bottom of the window to set it anyway.")
def PLOCKED(ok):
    return "custom_tooltip = { fail_text = dtp_pe_lock %s }" % B("OR", FORCE_FROM, ok)
RMODE = B("from", "has_country_flag = dtp_pe_rm")
PSPRITE = {}
def picon(tex):
    if not tex: return None
    return tex if tex.startswith("GFX_") else gspr(tex)
_PSLOT = [None]                       # номер ячейки сетки (0…35) у текущей карточки — ставит pgrid
PSLOTS = {}                           # ячейка → [(условие страницы, есть, разрешено, эффект, rm)]
def pcard(name, ru, en, x, y, w, pot, tex, has, ok, effect, tt_ru, tt_en, rm=False):
    """Карточка как в редакторе держав: значок игры + название. Зелёная рамка (уже есть на планете) и красный знак
    (игра запрещает) — общие для ячейки сетки (36 штук на все разделы): их условия — в файлах скриптов, а не в файле окна
    (у файла окна предел ~1 МБ, у скриптов — нет)."""
    allow = need_perm("planet") + "\n" + N_TP()
    if ok is not None:
        allow += "\n" + PLOCKED(B("OR", *([has] if has else []), ok, *([RMODE] if rm else [])))
    pad = "              " if tex else "  "
    tgt_, body_, code_ = effect
    inner = B("event_target:%s" % tgt_, body_)
    eff = act("planet", inner, code_)  # прямо в кнопке: вложенность scripted effects у игры ограничена
    k = pb(name, pad + ru, pad + en, x, y, w, ECH, pot=pot, allow=allow, effect=eff, tt=(tt_ru, tt_en), left=True, sprite="GFX_dtp_ec" if tex else "GFX_dtp_btn")
    GUI[-1]["quiet"] = True
    if tex:
        spr = picon(tex)
        g = dict(GUI[-1]); m = dict(META[-1])
        GUI.append(dict(g, key=k + "_ic", x=x + 5, y=y + 4, w=30, h=30, sprite=spr, label=True, eff=k, left=False, transp=True, tt=None,
                        scale="0.75" if spr.startswith("GFX_planet_type") else None))
        META.append(dict(m, key=k + "_ic", x=x + 5, y=y + 4, w=30, h=30, sprite=spr, label=True, text=""))
        L[k + "_ic"] = ""
    bad = ok if (ok is not None and _POK.get(re.search(r"T = (\w+)", ok).group(1)) != "trivial") else None
    if _PSLOT[0] is not None and (has or bad):
        PSLOTS.setdefault(_PSLOT[0], (x, y, w, []))[3].append((pot, has, bad, inner, rm))
    return k
def pslots():
    """Общие рамки и красные знаки ячеек: видны, если на открытой странице в этой ячейке — карточка, которая есть / запрещена."""
    for j, (_sk, (x, y, w, ents)) in enumerate(sorted(PSLOTS.items())):
        hs = [(c, h, e) for c, h, b, e, r in ents if h]
        if hs:
            pb("sl%d_h" % j, "", "", x, y, w, ECH, pot=B("from", PEOPEN) + "\n" + B("OR", *[B("AND", c, h) for c, h, e in hs]), allow=need_perm("planet") + "\n" + N_TP(),
               effect=act("planet", "\n".join(B("if" if i == 0 else "else_if", B("limit", c), e) for i, (c, h, e) in enumerate(hs)), 76), sprite="GFX_dtp_sg", transp=True,
               tt=("§GУже есть на выбранной планете.§! Нажмите — то же, что карточка: в режиме «Убирать» — убрать, иначе — добавить ещё (или снять, где это переключатель).",
                   "§GAlready on the selected planet.§! Click — same as the card: in 'Remove' mode — remove, otherwise — add another (or remove, where it is a toggle)."))
            GUI[-1]["quiet"] = True
        bs = [(c, b, e, h, r) for c, h, b, e, r in ents if b]
        if bs:
            pb("sl%d_x" % j, "", "", x + w - 20, y + 3, 17, 17, pot=B("from", PEOPEN) + "\ndtp_has_tp = yes\n" + B("OR", *[B("AND", c, "NOT = { %s }" % b) for c, b, e, h, r in bs]),
               allow=need_perm("planet") + "\n" + N_TP() + "\n" + PLOCKED(B("OR", *[B("AND", c, B("OR", b, *([h] if h else []), *([RMODE] if r else []))) for c, b, e, h, r in bs])),
               effect=act("planet", "\n".join(B("if" if i == 0 else "else_if", B("limit", c), e) for i, (c, b, e, h, r) in enumerate(bs)), 76), sprite="GFX_dtp_sr", transp=True,
               tt=("§RИгра обычно это запрещает§! для выбранной планеты. Поставить можно в принудительном режиме.", "§RThe game normally forbids this§! for the selected planet. Force mode allows it."))
            GUI[-1]["quiet"] = True
def ppages(name, tab, cat, n):
    if n <= 1: return
    y = EH - 96
    plab("%s_pl" % name, "Страница:", "Page:", EX0, y + 4, 100, pot=PEP(tab, cat))
    for p in range(1, n + 1):
        x = EX0 + 104 + (p - 1) * 40
        pb("%s_p%d_on" % (name, p), str(p), str(p), x, y, 36, 30, pot=PEP(tab, cat, p), sprite="GFX_dtp_btn_on", tt=("Открыта страница %d." % p, "Page %d is open." % p))
        pb("%s_p%d" % (name, p), str(p), str(p), x, y, 36, 30, pot=PEP(tab, cat, extra=B("from", "NOT = { %s }" % chk("dtp_pepg", p))),
           effect=B("from", setv("dtp_pepg", p)), tt=("Открыть страницу %d." % p, "Open page %d." % p))
def psubtabs(tab, items, dy=0):
    w = (EXW - 6 * (len(items) - 1)) // len(items)
    for i, (c, ru, en) in enumerate(items):
        x = EX0 + i * (w + 6)
        pb("t%d_c%d_on" % (tab, c), ru, en, x, EY0 - 42 + dy, w, 34, pot=PEP(tab, c), sprite="GFX_dtp_tab_on", tt=("Открыт подраздел «%s»." % ru, "Sub-section '%s' is open." % en))
        pb("t%d_c%d" % (tab, c), ru, en, x, EY0 - 42 + dy, w, 34, pot=PEP(tab, extra=B("from", "NOT = { %s }" % chk("dtp_pecat", c))),
           effect=B("from", setv("dtp_pecat", c), setv("dtp_pepg", 1)), sprite="GFX_dtp_tab", tt=("Открыть подраздел «%s»." % ru, "Open the '%s' sub-section." % en))
def pgrid(tab, cat, items, mk, cols=ECOLS, dy=0, tw=None):
    per = (EROWS - (dy + ECH + EGAP - 1) // (ECH + EGAP)) * cols
    w = ((tw or EXW) - (cols - 1) * EGAP) // cols
    for i, it in enumerate(items):
        pg, j = i // per + 1, i % per
        x = EX0 + (j % cols) * (w + EGAP); y = EY0 + dy + (j // cols) * (ECH + EGAP)
        _PSLOT[0] = (cols, dy, w, j)
        mk(i, it, x, y, w, PEP(tab, cat, pg))
        _PSLOT[0] = None
    ppages("g%d_%s" % (tab, cat or 0), tab, cat, (len(items) + per - 1) // per)
def phead(tab, ru, en, y=EY0 - 40, cat=None):
    plab("h%d_%s" % (tab, cat or 0), ru, en, EX0 + 6, y + 4, EXW - 12, pot=PEP(tab, cat), h=28)
def PACT(body, code):
    return act("planet", B("event_target:dtp_p", body), code)
def PT(body, code):
    """Действие карточки: (цель, тело, итог) — общие рамки ячеек собирают тела в одну цепочку под одним act()."""
    return ("dtp_p", body, code)
# новые итоги действий
for _c, _ru, _en in [(68, "зона изменена", "zone changed"), (69, "аномалия добавлена", "anomaly added"), (70, "раскопки добавлены", "dig site added"),
                     (71, "специализация изменена", "designation changed"), (72, "особенность планеты изменена", "planet feature changed"),
                     (73, "население изменено", "population changed"), (74, "уровень возвышения планеты изменён", "planetary ascension changed"),
                     (75, "станция создана", "station created"), (76, "планета изменена", "planet changed")]:
    CODES[_c] = _ru; CODES_EN[_c] = _en
for _c, _en in [(9, "planet type changed"), (10, "deposits or blockers changed"), (11, "planet size changed"), (12, "population added"), (37, "star class changed"),
                (42, "district changed"), (43, "building changed"), (8, "planet transferred"), (33, "colony destroyed"), (53, "colony founded"), (36, "system marks changed")]:
    CODES_EN.setdefault(_c, _en)

# ================================================================ КАРКАС ОКНА
PO = B("from", PEOPEN)
pdeco("bg", 0, 0, EW, EH, "GFX_dtp_panel", PO)
pdeco("decor", EW - 186, 4, 180, 90, "GFX_dtp_decor", PO)
pdeco("logo", 16, 12, 34, 34, "GFX_dtp_ico5", PO)
plab("title", "§YРЕДАКТОР§!", "§YEDITOR§!", 58, 8, 180, pot=PEP(), h=24, font="malgun_goth_24")
plab("title2", "§gпланеты и системы§!", "§gplanet & system§!", 60, 32, 200, pot=PEP(), h=20)
pdeco("card", 268, 6, 520, 52, "GFX_dtp_card", PO)
for k in range(1, MAXP + 1):
    pk = PEP(extra=B("from", chk("dtp_pidx", k)))
    ex = "\nexists = event_target:dtp_tp_%d" % k
    plab("p_%d" % k, "§Y[dtp_tp_%d.GetName]§!" % k, "§Y[dtp_tp_%d.GetName]§!" % k, 282, 8, 380, pot=pk + ex, h=26, font="malgun_goth_24")
    plab("ps_%d" % k, "[dtp_tp_%d.GetClassName] §g· система§! [dtp_tp_%d.System.GetName] §g·§! [dtp_tp_%d.Owner.GetRealName]" % (k, k, k),
         "[dtp_tp_%d.GetClassName] §g· system§! [dtp_tp_%d.System.GetName] §g·§! [dtp_tp_%d.Owner.GetRealName]" % (k, k, k), 282, 34, 400,
         pot=pk + ex + "\n" + B("event_target:dtp_tp_%d" % k, "exists = owner"), h=20)
    plab("pn_%d" % k, "[dtp_tp_%d.GetClassName] §g· система§! [dtp_tp_%d.System.GetName] §g· без владельца§!" % (k, k),
         "[dtp_tp_%d.GetClassName] §g· system§! [dtp_tp_%d.System.GetName] §g· no owner§!" % (k, k), 282, 34, 400,
         pot=pk + ex + "\n" + B("event_target:dtp_tp_%d" % k, "NOT = { exists = owner }"), h=20)
    plab("p_%d_x" % k, "§gПланета не выбрана — откройте окно любой планеты и нажмите «Редактор планеты» на полосе Toolpack§!",
         "§gNo planet selected — open any planet window and press 'Planet editor' on the Toolpack strip§!", 282, 12, 490,
         pot=pk + "\nNOT = { exists = event_target:dtp_tp_%d }" % k, h=40)
pb("back", "← Панель DTP", "← DTP panel", EW - 228, 14, 166, 36, pot=PEP(), effect=B("from", "remove_country_flag = dtp_pe_open", "set_country_flag = dtp_open"),
   tt=("Закрыть редактор планеты и вернуться в главную панель Debug Toolpack.", "Close the planet editor and return to the main Debug Toolpack panel."))
pb("close", "✕", "✕", EW - 54, 14, 40, 36, pot=PEP(), effect=B("from", "remove_country_flag = dtp_pe_open"), sprite="GFX_dtp_btn_danger",
   tt=("Закрыть редактор планеты.", "Close the planet editor."))
PTABS = [(1, "Тип планеты", "Planet type"), (2, "Размер и колония", "Size & colony"), (3, "Звезда и система", "Star & system"),
         (4, "Залежи", "Deposits"), (5, "Районы", "Districts"), (6, "Зоны районов", "District zones"), (7, "Здания", "Buildings"),
         (8, "Аномалии и раскопки", "Anomalies & dig sites"), (9, "Специализация", "Designation"), (10, "Природа планеты", "Planet features"),
         (11, "Население", "Population"), (12, "Модификаторы", "Modifiers")]
PTT = {1: ("Тип (класс) планеты: обитаемые, особые и необитаемые — все типы игры.", "Planet type (class): habitable, special and uninhabitable — every type in the game."),
       2: ("Размер планеты, уровень возвышения, колонизация, передача, уничтожение колонии, терраформирование.", "Planet size, ascension tier, colonization, transfer, destroying the colony, terraforming."),
       3: ("Класс звезды системы и объекты в системе: станции, разлом, отметка.", "The system's star class and objects in the system: stations, rift, mark."),
       4: ("Все залежи игры: ресурсы, препятствия, орбитальные.", "Every deposit in the game: resources, blockers, orbital."),
       5: ("Все районы игры: городские, сельские, аркологии, места обитания, кольцо и особые.", "Every district in the game: urban, rural, arcology, habitat, ring world and special."),
       6: ("Зоны (специализации) районов — как в окне планеты игры.", "District zones (specializations) — as in the game's planet window."),
       7: ("Все здания игры — по категориям.", "Every building in the game — by category."),
       8: ("Аномалии (для исследования) и места раскопок — все виды игры.", "Anomalies (to research) and dig sites — every kind in the game."),
       9: ("Специализация (назначение) колонии — все варианты игры.", "Colony designation — every option in the game."),
       10: ("Особенности природы планеты: опасная погода, богатая жизнь и т. д.", "Natural planet features: hazardous weather, rich wildlife and so on."),
       11: ("Население планеты: добавить группы населения, убрать часть или всех.", "Planet population: add pop groups, remove part or all of them."),
       12: ("Бонусы и штрафы планеты: модификаторы Toolpack (сила и срок — калькулятор справа) и модификаторы самой игры.", "Planet bonuses and penalties: Toolpack modifiers (strength and duration — calculator on the right) and the game's own modifiers.")}
PSUB = {1: ("класс планеты · как у игры", "planet class · as in the game"), 2: ("размер · колония · владелец", "size · colony · owner"),
        3: ("звезда · станции · разлом", "star · stations · rift"), 4: ("ресурсы · препятствия · орбита", "resources · blockers · orbit"),
        5: ("добавить или убрать", "add or remove"), 6: ("в подходящий район планеты", "into a fitting district of the planet"),
        7: ("добавить или снести", "add or demolish"), 8: ("аномалии · раскопки", "anomalies · dig sites"), 9: ("назначение колонии", "colony designation"),
        10: ("особенности природы", "natural features"), 11: ("группы населения", "pop groups"), 12: ("бонусы и штрафы планеты", "planet bonuses and penalties")}
pdeco("navbg", 8, 64, 206, EH - 72, "GFX_dtp_frame", PO)
plab("navh", "§gРАЗДЕЛЫ§!", "§gSECTIONS§!", 22, 70, 180, pot=PEP(), h=22)
for i, (t, ru, en) in enumerate(PTABS):
    y = 96 + i * 42
    pb("tab%d_on" % t, ru, en, 14, y, 194, 38, pot=PEP(t), sprite="GFX_dtp_ednav_on", tt=PTT[t])
    pb("tab%d" % t, ru, en, 14, y, 194, 38, pot=PEP(extra=B("from", "NOT = { %s }" % chk("dtp_petab", t))),
       effect=B("from", setv("dtp_petab", t), setv("dtp_pecat", 1), setv("dtp_pepg", 1)) + ("\n" + INIT + "\ndtp_load = yes\ndtp_esl_fill = yes" if t == 11 else ""), sprite="GFX_dtp_ednav", tt=PTT[t])
    pdeco("ban%d" % t, EX0, 62, EXW, 40, "GFX_dtp_pbanner_%d" % t, B("from", PEOPEN, chk("dtp_petab", t)))
    plab("bt%d" % t, ru.upper(), en.upper(), EX0 + 50, 66, 500, pot=PEP(t), h=30, font="large_title_font")
    plab("bs%d" % t, "§g%s§!" % PSUB[t][0], "§g%s§!" % PSUB[t][1], EX0 + 560, 72, EXW - 570, pot=PEP(t), h=22)
pdeco("grp", EX0 - 6, EY0 - 46, EXW + 12, EH - 104 - EY0 + 50, "GFX_dtp_group", PO)
plab("lg1", "§Gзелёная рамка§! — уже есть", "§Ggreen frame§! — already there", 18, EH - 150, 190, pot=PEP())
plab("lg2", "§R●§! — игра обычно запрещает", "§R●§! — normally forbidden", 18, EH - 126, 190, pot=PEP())
# низ окна: итог, режим «добавлять / убирать», принудительный режим
_RW = EXW - 330 - 250
for nm, ru, en, cond, spr in [("r_idle", "   §gИтог последнего действия появится здесь§!", "   §gThe result of your last action will appear here§!", "NOT = { is_variable_set = dtp_last_ok }", "GFX_dtp_res_idle"),
                              ("r_ok", "   §GГОТОВО§!  ·  изменение применено", "   §GDONE§!  ·  the change was applied", chk("dtp_last_ok", 1), "GFX_dtp_res_ok"),
                              ("r_deny", "   §RОТКАЗАНО§!  ·  нет права «Планеты»", "   §RDENIED§!  ·  no 'Planets' permission", chk("dtp_last_ok", 0), "GFX_dtp_res_bad"),
                              ("r_fail", "   §HНЕ ВЫПОЛНЕНО§!  ·  планета не выбрана", "   §HNOT DONE§!  ·  no planet selected", chk("dtp_last_ok", 2), "GFX_dtp_res_warn")]:
    plab(nm, ru, en, EX0, EH - 54, _RW, pot=PEP(extra=B("from", cond)), h=44, sprite=spr)
RMTABS = (4, 5, 6, 7)
_RMP = B("from", PEOPEN, B("OR", *[chk("dtp_petab", t) for t in RMTABS]))
pb("rm_off", "Режим: + ДОБАВЛЯТЬ", "Mode: + ADD", EX0 + _RW + 6, EH - 54, 244, 44, pot=_RMP + "\n" + B("from", "NOT = { has_country_flag = dtp_pe_rm }"),
   effect=B("from", "set_country_flag = dtp_pe_rm"), sprite="GFX_dtp_btn_go",
   tt=("Сейчас нажатие на карточку §GДОБАВЛЯЕТ§! (залежь, район, зону, здание). Нажмите, чтобы переключить на «Убирать».",
       "Clicking a card now §GADDS§! it (deposit, district, zone, building). Click to switch to 'Remove'."))
pb("rm_on", "Режим: − УБИРАТЬ", "Mode: − REMOVE", EX0 + _RW + 6, EH - 54, 244, 44, pot=_RMP + "\n" + B("from", "has_country_flag = dtp_pe_rm"),
   effect=B("from", "remove_country_flag = dtp_pe_rm"), sprite="GFX_dtp_btn_danger",
   tt=("Сейчас нажатие на карточку §RУБИРАЕТ§! одну штуку (залежь, район, зону, здание). Нажмите, чтобы снова добавлять.",
       "Clicking a card now §RREMOVES§! one (deposit, district, zone, building). Click to add again."))
pb("force_on", "Принудительный режим: ВЫКЛ", "Force mode: OFF", EW - 324, EH - 54, 310, 44, pot=PEP(extra=B("from", "NOT = { has_country_flag = dtp_force_mode }")),
   allow=need_perm("force"), effect=B("from", B("if", B("limit", "dtp_has_perm = { P = force }"), "set_country_flag = dtp_force_mode")) + "\ndtp_result = { CODE = 30 }",
   tt=("Сейчас действуют правила игры: помеченное §R●§! поставить нельзя. Нажмите, чтобы включить принудительный режим — тогда можно всё.",
       "The game's rules apply now: items marked §R●§! cannot be set. Click to turn on force mode — then everything is allowed."))
pb("force_off", "Принудительный режим: ВКЛ", "Force mode: ON", EW - 324, EH - 54, 310, 44, pot=PEP(extra=B("from", "has_country_flag = dtp_force_mode")),
   effect=B("from", "remove_country_flag = dtp_force_mode") + "\ndtp_result = { CODE = 30 }", sprite="GFX_dtp_btn_warn",
   tt=("Принудительный режим включён: можно ставить и то, что игра обычно запрещает (помечено §R●§!). Нажмите, чтобы выключить.",
       "Force mode is on: you can set things the game normally forbids (marked §R●§!). Click to turn it off."))

_SPR = _ed.sprite_textures(VI)
_GI = "gfx/interface/icons/"
def _nm(k): return "$%s$" % k
def ADDRM(add, rm):
    return B("if", B("limit", RMODE), rm) + "\n" + B("else", add)

# ================================================================ 1. ТИП ПЛАНЕТЫ
_PC = _pd.planet_classes(VC, _SPR)
_HAB = [k for k, n in PC_NORMAL]
psubtabs(1, [(1, "Обитаемые", "Habitable"), (2, "Особые обитаемые", "Special habitable"), (3, "Необитаемые", "Uninhabitable")])
for c, cat in ((1, "hab"), (2, "special"), (3, "barren")):
    items = [x for x in _PC if x["cat"] == cat]
    def mk(i, it, x, y, w, pot):
        k = it["key"]
        # колонию игра переводит только в обитаемый тип; особые типы (кольцо, обиталище, ковчег…) — только своими путями
        body = "" if (it["col"] and cat == "hab") else ("NOT = { is_colony = yes }" if not it["col"] else "always = no")
        pcard("pc_" + k, _nm(k), _nm(k), x, y, w, pot, it["icon"], phas("pc_" + k, "is_planet_class = %s" % k), pok("pc_" + k, body),
              PT(B("if", B("limit", "is_star = no", "NOT = { is_planet_class = %s }" % k), "change_pc = %s" % k), 9),
              "§Y$%s$§!\n$%s_desc$\n\n§gНажмите: сменить тип выбранной планеты (внешний вид, пригодность, районы).§!" % (k, k),
              "§Y$%s$§!\n$%s_desc$\n\n§gClick: change the selected planet's type (look, habitability, districts).§!" % (k, k))
    pgrid(1, c, items, mk)

# ================================================================ 2. РАЗМЕР И КОЛОНИЯ
_C2 = (EXW - 2 * EGAP) // 3
phead(2, "§YРАЗМЕР ПЛАНЕТЫ§!  §gнажмите число — размер станет таким; −1 и +1 — на единицу§!", "§YPLANET SIZE§!  §gclick a number — the size becomes it; −1 and +1 — by one§!", y=EY0 - 46)
_SZ = [1, 3, 5, 8, 10, 12, 15, 18, 20, 22, 25, 30]
_sw = (EXW - 2 * 70 - 13 * 4) // len(_SZ)
pb("sz_m", "−1", "−1", EX0, EY0 - 10, 66, 34, pot=PEP(2), allow=need_perm("planet") + "\n" + N_TP(), effect=PACT("change_planet_size = -1", 11), sprite="GFX_dtp_btn_danger",
   tt=("Уменьшить размер выбранной планеты на 1.", "Reduce the selected planet's size by 1."))
for j, s in enumerate(_SZ):
    TRG.append(B("dtp_ph_sz%d" % s, "planet_size = %d" % s))
    x = EX0 + 70 + j * (_sw + 4)
    pb("sz%d" % s, str(s), str(s), x, EY0 - 10, _sw, 34, pot=PEP(2), allow=need_perm("planet") + "\n" + N_TP(), effect=PACT("set_planet_size = %d" % s, 11),
       tt=("Сделать размер выбранной планеты %d." % s, "Set the selected planet's size to %d." % s))
    pb("sz%d_h" % s, "", "", x, EY0 - 10, _sw, 34, pot=PEP(2, extra="dtp_tpx = { T = dtp_ph_sz%d }" % s), allow=need_perm("planet") + "\n" + N_TP(),
       effect=PACT("set_planet_size = %d" % s, 11), sprite="GFX_dtp_sg", transp=True, tt=("Сейчас размер планеты — %d." % s, "The planet's size is %d now." % s))
pb("sz_p", "+1", "+1", EX0 + EXW - 66, EY0 - 10, 66, 34, pot=PEP(2), allow=need_perm("planet") + "\n" + N_TP(), effect=PACT("change_planet_size = 1", 11), sprite="GFX_dtp_btn_go",
   tt=("Увеличить размер выбранной планеты на 1.", "Increase the selected planet's size by 1."))
plab("h2b", "§YКОЛОНИЯ И ВЛАДЕЛЕЦ§!  §gдержава A и получатель B — из главной панели DTP§!", "§YCOLONY & OWNER§!  §gempire A and recipient B — from the main DTP panel§!", EX0 + 6, EY0 + 36, EXW - 12, pot=PEP(2), h=26)
_COLSP = B("event_target:dtp_t", B("owner_species", "save_event_target_as = dtp_popsp"))
P2 = [
    ("col_a", "Колония для державы A", "Colony for empire A", need_perm("planet") + "\n" + N_TP() + "\n" + N_TC() + "\n" + PLOCKED(pok("col_new", "NOT = { exists = owner }\nis_colonizable = yes")),
     act("planet", _COLSP + "\n" + B("event_target:dtp_p", B("if", B("limit", "NOT = { exists = owner }"), "create_colony = { owner = event_target:dtp_t }", "create_pop_group = { species = event_target:dtp_popsp size = 100 }"),
         B("else", "set_owner = event_target:dtp_t", "set_controller = event_target:dtp_t")), 53),
     "Сделать выбранную планету колонией державы A (её основной вид). Если у планеты уже есть владелец — передать её A. Необитаемую и чужую — только в принудительном режиме.",
     "Make the selected planet a colony of empire A (its main species). If the planet already has an owner — give it to A. Uninhabitable or owned — force mode only.", "GFX_dtp_btn_go"),
    ("to_b", "Передать получателю B", "Give to recipient B", need_perm("planet") + "\n" + N_TP() + "\n" + N_RCP(),
     act("planet", B("event_target:dtp_p", B("if", B("limit", "exists = owner"), "set_owner = event_target:dtp_r", "set_controller = event_target:dtp_r")), 8),
     "Передать выбранную колонию получателю B (вместе с населением и постройками).", "Give the selected colony to recipient B (with pops and buildings).", None),
    ("kill", "Уничтожить колонию", "Destroy the colony", need_perm("planet") + "\n" + N_TP() + "\n" + N_FORCE(),
     PACT(B("if", B("limit", "is_colony = yes"), "destroy_colony = yes"), 33),
     "Уничтожить колонию на выбранной планете — население и постройки исчезнут (принудительный режим).", "Destroy the colony on the selected planet — pops and buildings disappear (force mode).", "GFX_dtp_btn_danger"),
    ("terra", "Завершить терраформирование", "Finish terraforming", need_perm("planet") + "\n" + N_TP() + "\n" + need("dtp_need_terra", "На выбранной планете сейчас не идёт терраформирование", orchain(lambda q: B("event_target:dtp_tp_%d" % q, "is_terraforming = yes"))),
     PACT("finish_terraformation = yes", 9), "Мгновенно завершить идущее терраформирование.", "Instantly finish the ongoing terraforming.", None),
    ("repair", "Починить все здания", "Repair all buildings", need_perm("planet") + "\n" + N_TP(), PACT("repair_all_buildings = yes", 43),
     "Починить все разрушенные здания выбранной планеты.", "Repair all ruined buildings on the selected planet.", None),
    ("validate", "Убрать недопустимое", "Remove invalid", need_perm("planet") + "\n" + N_TP(), PACT("validate_and_repair_planet_buildings_and_districts = yes", 43),
     "Игра проверит здания и районы: недопустимые для планеты заменит или уберёт, разрушенные починит.", "The game checks buildings and districts: invalid ones are replaced or removed, ruined ones repaired.", None),
    ("clrb", "Снести ВСЕ здания", "Demolish ALL buildings", need_perm("planet") + "\n" + N_TP(), PACT("remove_all_buildings = yes", 43),
     "Снести все здания выбранной планеты.", "Demolish all buildings on the selected planet.", "GFX_dtp_btn_danger"),
    ("clrd", "Убрать ВСЕ районы", "Remove ALL districts", need_perm("planet") + "\n" + N_TP(), PACT("remove_all_districts = yes", 42),
     "Убрать все районы выбранной планеты.", "Remove all districts on the selected planet.", "GFX_dtp_btn_danger"),
    ("dev", "Опустошение +25", "Devastation +25", need_perm("planet") + "\n" + N_TP(), PACT("add_planet_devastation = 25", 76),
     "Добавить выбранной планете 25 опустошения (как после бомбардировки).", "Add 25 devastation to the selected planet (as after bombardment).", "GFX_dtp_btn_warn"),
    ("noanom", "Запретить аномалии", "Block anomalies", need_perm("planet") + "\n" + N_TP(),
     PACT(B("if", B("limit", "is_preventing_anomaly = yes"), "prevent_anomaly = no") + "\n" + B("else", "prevent_anomaly = yes"), 76),
     "Запретить (или снова разрешить) появление аномалий на выбранной планете.", "Block (or allow again) anomalies on the selected planet.", None),
    ("mark", "§R●§! Отметить систему", "§R●§! Mark the system", need_perm("planet") + "\n" + N_TP(),
     act("planet", B("event_target:dtp_s", B("if", B("limit", "has_star_flag = dtp_marked"), "dtp_unmark_sys = yes"), B("else", "dtp_mark_sys = yes")), 36) + "\ndtp_mlist = yes",
     "Отметить систему выбранной планеты на карте (или снять отметку).", "Mark the selected planet's system on the map (or unmark it).", "GFX_dtp_btn_warn"),
]
for j, (k, ru, en, al, ef, tru, ten, spr) in enumerate(P2):
    x = EX0 + (j % 3) * (_C2 + EGAP); y = EY0 + 66 + (j // 3) * 40
    pb("a_" + k, ru, en, x, y, _C2, 34, pot=PEP(2), allow=al, effect=ef, sprite=spr or "GFX_dtp_btn", tt=(tru, ten))
_ya = EY0 + 66 + ((len(P2) + 2) // 3) * 40 + 6
plab("h2c", "§YУРОВЕНЬ ВОЗВЫШЕНИЯ ПЛАНЕТЫ§!  §gдля колоний; 0 — без возвышения§!", "§YPLANETARY ASCENSION TIER§!  §gfor colonies; 0 — none§!", EX0 + 6, _ya, EXW - 12, pot=PEP(2), h=26)
_aw = (EXW - 10 * 4) // 11
for t_ in range(11):
    x = EX0 + t_ * (_aw + 4)
    TRG.append(B("dtp_ph_asc%d" % t_, "has_planetary_ascension_tier = %d" % t_))
    pb("asc%d" % t_, str(t_), str(t_), x, _ya + 30, _aw, 32, pot=PEP(2), allow=need_perm("planet") + "\n" + N_TP() + "\n" + need("dtp_need_colony", "Это не колония", "dtp_tp_colony = yes"),
       effect=PACT("set_planetary_ascension_tier = %d" % t_, 74), tt=("Уровень возвышения планеты = %d." % t_, "Planetary ascension tier = %d." % t_))
    pb("asc%d_h" % t_, "", "", x, _ya + 30, _aw, 32, pot=PEP(2, extra="dtp_tpx = { T = dtp_ph_asc%d }" % t_), allow=need_perm("planet") + "\n" + N_TP(),
       effect=PACT("set_planetary_ascension_tier = %d" % t_, 74), sprite="GFX_dtp_sg", transp=True, tt=("Сейчас уровень возвышения — %d." % t_, "The ascension tier is %d now." % t_))
_yb = _ya + 72
plab("h2d", "§YЗАЛЕЖИ ЦЕЛИКОМ§!", "§YDEPOSITS AS A WHOLE§!", EX0 + 6, _yb, EXW - 12, pot=PEP(2), h=26)
for j, (k, ru, en, ef, tru, ten) in enumerate([
        ("dep_r", "Случайная залежь", "Random deposit", "add_random_non_blocker_deposit = yes", "Добавить случайную залежь ресурса.", "Add a random resource deposit."),
        ("dep_re", "Перегенерировать залежи", "Reroll deposits", "reroll_deposits = yes", "Создать залежи планеты заново.", "Generate the planet's deposits anew."),
        ("dep_cb", "Убрать препятствия", "Clear blockers", "clear_blockers = yes", "Убрать все препятствия (блокираторы).", "Remove all blockers."),
        ("dep_ca", "Убрать ВСЕ залежи", "Remove ALL deposits", "clear_deposits = yes", "Убрать все залежи и препятствия выбранной планеты.", "Remove all deposits and blockers of the selected planet."),
        ("pm_re", "Перегенерировать природу", "Reroll features", "reroll_planet_modifiers = yes", "Создать особенности природы планеты заново.", "Generate the planet's natural features anew."),
        ("pm_ca", "Убрать особенности природы", "Clear features", "clear_planet_modifiers = yes", "Убрать все особенности природы планеты.", "Remove all natural features of the planet.")]):
    x = EX0 + (j % 3) * (_C2 + EGAP); y = _yb + 30 + (j // 3) * 40
    pb("a_" + k, ru, en, x, y, _C2, 34, pot=PEP(2), allow=need_perm("planet") + "\n" + N_TP(), effect=PACT(ef, 10 if k.startswith("dep") else 72),
       sprite="GFX_dtp_btn_danger" if k.endswith("_ca") else "GFX_dtp_btn", tt=(tru, ten))

# ================================================================ 3. ЗВЕЗДА И СИСТЕМА
_STRU = {"sc_b": "Голубая B", "sc_a": "Белая A", "sc_f": "Жёлто-белая F", "sc_g": "Жёлтая G", "sc_k": "Оранжевая K", "sc_m": "Красная M", "sc_m_giant": "Красный гигант",
         "sc_t": "Коричневый карлик", "sc_black_hole": "Чёрная дыра", "sc_neutron_star": "Нейтронная звезда", "sc_pulsar": "Пульсар",
         "sc_binary_1": "Двойная: голубая и пульсар", "sc_binary_2": "Двойная: голубая и нейтронная", "sc_binary_3": "Двойная: красная и белая",
         "sc_binary_4": "Двойная: красная и белый карлик", "sc_binary_5": "Двойная: две голубые", "sc_binary_6": "Двойная: красная и жёлтая",
         "sc_binary_7": "Двойная: оранжевая и жёлто-белая", "sc_binary_8": "Двойная: жёлтая и жёлто-белая", "sc_binary_9": "Двойная: Сириус",
         "sc_binary_10": "Двойная: коричневый карлик", "sc_trinary_1": "Тройная 1", "sc_trinary_2": "Тройная 2", "sc_trinary_3": "Тройная 3", "sc_trinary_4": "Тройная 4",
         "sc_toxoid_star": "Токсоидная звезда", "sc_rift_star": "Звезда разлома"}
_STEN = {"sc_b": "Blue B", "sc_a": "White A", "sc_f": "Yellow-white F", "sc_g": "Yellow G", "sc_k": "Orange K", "sc_m": "Red M", "sc_m_giant": "Red giant",
         "sc_t": "Brown dwarf", "sc_black_hole": "Black hole", "sc_neutron_star": "Neutron star", "sc_pulsar": "Pulsar",
         "sc_binary_1": "Binary: blue & pulsar", "sc_binary_2": "Binary: blue & neutron", "sc_binary_3": "Binary: red & white", "sc_binary_4": "Binary: red & white dwarf",
         "sc_binary_5": "Binary: two blue", "sc_binary_6": "Binary: red & yellow", "sc_binary_7": "Binary: orange & yellow-white", "sc_binary_8": "Binary: yellow & yellow-white",
         "sc_binary_9": "Binary: Sirius", "sc_binary_10": "Binary: brown dwarf", "sc_trinary_1": "Trinary 1", "sc_trinary_2": "Trinary 2", "sc_trinary_3": "Trinary 3",
         "sc_trinary_4": "Trinary 4", "sc_toxoid_star": "Toxoid star", "sc_rift_star": "Rift star"}
_STI = _pd.star_planet_icons(VC, _SPR)
_SCS = [k for k in _ed.top(os.path.join(VC, "star_classes/*.txt")) if k.startswith("sc_") and k in _STRU]
phead(3, "§YКЛАСС ЗВЕЗДЫ СИСТЕМЫ§!  §gвыбранной планеты; отметка системы сохраняется§!", "§YSYSTEM STAR CLASS§!  §gof the selected planet; the system mark is kept§!")
def mk(i, k, x, y, w, pot):
    rem = "\n".join([setv("dtp_wm", 0), B("if", B("limit", "has_star_flag = dtp_marked"), setv("dtp_wm", 1), "dtp_unmark_sys = yes"),
                     "set_star_class = %s" % k, B("if", B("limit", chk("dtp_wm", 1)), "dtp_mark_sys = yes")])
    pcard("sc_" + k, _STRU[k], _STEN[k], x, y, w, pot, _STI.get(k), phas("sc_" + k, B("solar_system", "is_star_class = %s" % k)), None,
          ("dtp_s", rem, 37),
          "Сменить класс звезды системы на «%s»: меняются вид звезды, свет и её свойства." % _STRU[k], "Change the system's star class to '%s': the star's look, light and properties change." % _STEN[k])
pgrid(3, None, _SCS, mk)
_ys = EY0 + ((len(_SCS) + 2) // 3) * (ECH + EGAP) + 10
plab("h3b", "§YОБЪЕКТЫ В СИСТЕМЕ§!", "§YOBJECTS IN THE SYSTEM§!", EX0 + 6, _ys, EXW - 12, pot=PEP(3), h=26)
for j, (k, ru, en, al, ef, tru, ten) in enumerate([
        ("mst", "Добывающая станция A", "Mining station for A", N_TC(), B("event_target:dtp_p", "create_mining_station = { owner = event_target:dtp_t }"), "Построить у выбранной планеты добывающую станцию державы A.", "Build a mining station of empire A at the selected planet."),
        ("rst", "Научная станция A", "Research station for A", N_TC(), B("event_target:dtp_p", "create_research_station = { owner = event_target:dtp_t }"), "Построить у выбранной планеты научную станцию державы A.", "Build a research station of empire A at the selected planet."),
        ("rift", "Астральный разлом", "Astral rift", "", B("event_target:dtp_s", "spawn_astral_rift = { random_pos = yes }"), "Создать в системе случайный астральный разлом (нужно дополнение Astral Planes).", "Spawn a random astral rift in the system (needs the Astral Planes DLC)."),
        ("ranom", "Случайная аномалия", "Random anomaly", N_TC(), B("event_target:dtp_p", "spawn_random_anomaly = { target = event_target:dtp_t }"), "Создать на выбранной планете случайную аномалию.", "Spawn a random anomaly on the selected planet."),
        ("rarc", "Случайные раскопки", "Random dig site", "", B("event_target:dtp_p", "create_archaeological_site = random"), "Создать на выбранной планете случайное место раскопок.", "Create a random dig site on the selected planet."),
        ("survey", "Исследовать для A", "Survey for A", N_TC(), B("event_target:dtp_p", "set_surveyed = { surveyed = yes surveyor = event_target:dtp_t }"), "Отметить выбранную планету как исследованную державой A.", "Mark the selected planet as surveyed by empire A.")]):
    x = EX0 + (j % 3) * (_C2 + EGAP); y = _ys + 30 + (j // 3) * 40
    pb("s_" + k, ru, en, x, y, _C2, 34, pot=PEP(3), allow=need_perm("planet") + "\n" + N_TP() + ("\n" + al if al else ""), effect=act("planet", ef, 75 if "st" in k else 76), tt=(tru, ten))

# ================================================================ 4. ЗАЛЕЖИ
_DEP = _pd.deposits(VC)
DEPCATS = [(1, "energy", "Энергия", "Energy"), (2, "minerals", "Минералы", "Minerals"), (3, "food", "Пища", "Food"), (4, "rare", "Особые", "Special"),
           (5, "block", "Препятствия", "Blockers"), (6, "orbit", "Орбитальные", "Orbital")]
for x_ in _DEP:
    if x_["grp"] == "other": x_["grp"] = "rare"
psubtabs(4, [(c, ru, en) for c, g, ru, en in DEPCATS])
for c, g, ru, en in DEPCATS:
    items = sorted([x for x in _DEP if x["grp"] == g], key=lambda x: x["key"])
    def mk(i, it, x, y, w, pot):
        k = it["key"]
        add = "add_deposit = %s" % k
        pcard("d_" + k, _nm(k), _nm(k), x, y, w, pot, it["icon"], phas("d_" + k, "has_deposit = %s" % k), pok("d_" + k, "\n".join(it["req"])),
              PT(ADDRM(add, B("if", B("limit", "has_deposit = %s" % k), "remove_deposit = %s" % k)), 10),
              "§Y$%s$§!\n$%s_desc$\n\n§gНажмите: добавить залежь на выбранную планету (в режиме «Убирать» — убрать одну такую).§!" % (k, k),
              "§Y$%s$§!\n$%s_desc$\n\n§gClick: add the deposit to the selected planet ('Remove' mode — remove one).§!" % (k, k), rm=True)
    pgrid(4, c, items, mk)

# ================================================================ 5. РАЙОНЫ
_DIS = _pd.districts(VC)
DISCATS = [(1, "urban", "Городские", "Urban"), (2, "rural", "Сельские", "Rural"), (3, "arc", "Аркологии", "Arcology"), (4, "ring", "Кольцо и обиталища", "Ring & habitat"), (5, "other", "Особые", "Special")]
for x_ in _DIS:
    if x_["grp"] == "hab": x_["grp"] = "ring"
psubtabs(5, [(c, ru, en) for c, g, ru, en in DISCATS])
for c, g, ru, en in DISCATS:
    items = sorted([x for x in _DIS if x["grp"] == g], key=lambda x: x["key"])
    def mk(i, it, x, y, w, pot):
        k = it["key"]
        add = B("if", B("limit", B("from", "dtp_force_active = yes")), "add_district = { district_type = %s ignore_cap = yes }" % k) + "\n" + B("else", "add_district = %s" % k)
        pcard("di_" + k, _nm(k), _nm(k), x, y, w, pot, it["icon"], phas("di_" + k, "has_district = %s" % k), pok("di_" + k, "\n".join(it["req"])),
              PT(ADDRM(add, B("if", B("limit", "has_district = %s" % k), "remove_district = %s" % k)), 42),
              "§Y$%s$§!\n$%s_desc$\n\n§gНажмите: добавить район (в принудительном режиме — сверх лимита); в режиме «Убирать» — убрать один.§!" % (k, k),
              "§Y$%s$§!\n$%s_desc$\n\n§gClick: add the district (in force mode — over the cap); 'Remove' mode — remove one.§!" % (k, k), rm=True)
    pgrid(5, c, items, mk)

# ================================================================ 6. ЗОНЫ РАЙОНОВ
_ZON = sorted(_pd.zones(VC, _SPR, _DIS), key=lambda x: x["key"])
phead(6, "§YЗОНЫ РАЙОНОВ§!  §gзона встаёт в первый подходящий район планеты (если в нём есть место)§!", "§YDISTRICT ZONES§!  §gthe zone goes into the first fitting district of the planet (if it has room)§!")
def mk(i, it, x, y, w, pot):
    k = it["key"]
    _az = lambda rep: "\n".join(B("if" if j == 0 else "else_if", B("limit", "has_district = %s" % d), "add_zone = { district = %s zone = %s%s }" % (d, k, " replace = yes" if rep else "")) for j, d in enumerate(it["dists"]))
    add = B("if", B("limit", B("from", "dtp_force_active = yes")), _az(True)) + "\n" + B("else", _az(False))     # 11.3.2: в принудительном — заменить зону, если мест нет
    rm = "\n".join(B("if" if j == 0 else "else_if", B("limit", "has_district = %s" % d), "remove_zone = { district = %s zone = %s }" % (d, k)) for j, d in enumerate(it["dists"]))
    pcard("z_" + k, _nm(k), _nm(k), x, y, w, pot, it["icon"], phas("z_" + k, "num_zones = { type = %s value > 0 }" % k),
          pok("z_" + k, "\n".join(it["req"] + [B("OR", *["has_district = %s" % d for d in it["dists"]])])),
          PT(ADDRM(add, rm), 68),
          "§Y$%s$§!\n\n§gНажмите: поставить зону в подходящий район (%s); в режиме «Убирать» — убрать её. Нужно свободное место для зоны; в принудительном режиме зона заменит другую.§!" % (k, ", ".join("$%s$" % d for d in it["dists"][:3])),
          "§Y$%s$§!\n\n§gClick: put the zone into a fitting district (%s); 'Remove' mode — remove it. Needs a free zone slot; in force mode it replaces another zone.§!" % (k, ", ".join("$%s$" % d for d in it["dists"][:3])), rm=True)
pgrid(6, None, _ZON, mk, dy=0)

# ================================================================ 7. ЗДАНИЯ
_BLD = _pd.buildings(VC)
BLDCATS = [(1, "science", "Наука", "Science"), (2, "resource", "Ресурсы", "Resources"), (3, "industry", "Промышленность", "Industry"), (4, "unity", "Единство", "Unity"),
           (5, "amenity", "Удобства", "Amenities"), (6, "gov", "Управление", "Government"), (7, "capital", "Столицы", "Capitals"), (8, "special", "Особые", "Special")]
for x_ in _BLD:
    if x_["grp"] == "army": x_["grp"] = "gov"
psubtabs(7, [(c, ru, en) for c, g, ru, en in BLDCATS])
for c, g, ru, en in BLDCATS:
    items = sorted([x for x in _BLD if x["grp"] == g], key=lambda x: x["key"])
    def mk(i, it, x, y, w, pot):
        k = it["key"]
        pcard("b_" + k, _nm(k), _nm(k), x, y, w, pot, it["icon"], phas("b_" + k, "has_building = %s" % k), pok("b_" + k, "\n".join(it["req"])),
              PT(ADDRM("add_building = %s" % k, B("if", B("limit", "has_building = %s" % k), "remove_building = %s" % k)), 43),
              "§Y$%s$§!\n$%s_desc$\n\n§gНажмите: построить сразу, без стоимости (нужно свободное место в зоне); в режиме «Убирать» — снести одно.§!" % (k, k),
              "§Y$%s$§!\n$%s_desc$\n\n§gClick: build it instantly, for free (needs a free slot in a zone); 'Remove' mode — demolish one.§!" % (k, k), rm=True)
    pgrid(7, c, items, mk)

# ================================================================ 8. АНОМАЛИИ И РАСКОПКИ
psubtabs(8, [(1, "Аномалии", "Anomalies"), (2, "Места раскопок", "Dig sites")])
_ANO = sorted(_pd.anomalies(VC, _SPR), key=lambda x: x["key"])
def mk(i, it, x, y, w, pot):
    k = it["key"]
    pcard("an_" + k, _nm(k), _nm(k), x, y, w, pot, None, None, pok("anom_free", "has_anomaly = no"),
          PT(B("if", B("limit", "is_preventing_anomaly = yes"), "prevent_anomaly = no") + "\nadd_anomaly = { category = %s target = event_target:dtp_t }" % k, 69),
          "§Y$%s$§!\n\n§gНажмите: добавить на выбранную планету эту аномалию для державы A — её сможет исследовать научный корабль.§!\n§HНа планете может быть только одна аномалия: пока старая не исследована, новая не появится (красный «!»).§!" % k,
          "§Y$%s$§!\n\n§gClick: add this anomaly to the selected planet for empire A — a science ship can research it.§!\n§HA planet can hold only one anomaly: until the old one is researched, a new one won't appear (red '!').§!" % k)
pgrid(8, 1, _ANO, mk)
_ARC = sorted(_pd.arc_sites(VC, _SPR), key=lambda x: x["key"])
def mk(i, it, x, y, w, pot):
    k = it["key"]
    pcard("ar_" + k, _nm(k), _nm(k), x, y, w, pot, None, None, None,
          PT("create_archaeological_site = %s" % k, 70),
          "§Y$%s$§!\n\n§gНажмите: создать на выбранной планете это место раскопок.§!" % k, "§Y$%s$§!\n\n§gClick: create this dig site on the selected planet.§!" % k)
pgrid(8, 2, _ARC, mk)

# ================================================================ 9. СПЕЦИАЛИЗАЦИЯ
_COL = _pd.colony_types(VC, _SPR)
psubtabs(9, [(1, "Основные", "Main"), (2, "Обиталища", "Habitats"), (3, "Особые", "Special")])
for c, g in ((1, "main"), (2, "hab"), (3, "special")):
    items = sorted([x for x in _COL if x["grp"] == g], key=lambda x: x["key"])
    def mk(i, it, x, y, w, pot):
        k = it["key"]
        pcard("ct_" + k, _nm(k), _nm(k), x, y, w, pot, it["icon"], phas("ct_" + k, "has_designation = %s" % k), pok("ct_" + k, "\n".join(it["req"] + ["is_colony = yes"])),
              PT(B("if", B("limit", "is_colony = yes"), "set_colony_type = %s" % k), 71),
              "§Y$%s$§!\n$%s_desc$\n\n§gНажмите: сделать эту специализацию у выбранной колонии. Игра может пересчитать её позже, если условия не подходят.§!" % (k, k),
              "§Y$%s$§!\n$%s_desc$\n\n§gClick: give the selected colony this designation. The game may recalculate it later if the conditions don't fit.§!" % (k, k))
    pgrid(9, c, items, mk)

# ================================================================ 10. ПРИРОДА ПЛАНЕТЫ
_PM = sorted(_pd.planet_modifiers(VC), key=lambda x: x["key"])
phead(10, "§YОСОБЕННОСТИ ПРИРОДЫ§!  §gнажать — добавить навсегда; если уже есть — убрать§!", "§YNATURAL FEATURES§!  §gclick — add permanently; if present — remove§!")
def mk(i, it, x, y, w, pot):
    k = it["key"]
    pcard("pm_" + k, _nm(k), _nm(k), x, y, w, pot, it["icon"], phas("pm_" + k, "has_modifier = %s" % k), None,
          PT(B("if", B("limit", "has_modifier = %s" % k), "remove_modifier = %s" % k) + "\n" + B("else", "add_modifier = { modifier = %s days = -1 }" % k), 72),
          "§Y$%s$§!\n$%s_desc$\n\n§gНажмите: добавить особенность выбранной планете; если уже есть — убрать.§!" % (k, k),
          "§Y$%s$§!\n$%s_desc$\n\n§gClick: add the feature to the selected planet; if present — remove it.§!" % (k, k))
pgrid(10, None, _PM, mk)

# ================================================================ 11. НАСЕЛЕНИЕ: вид (любой вид державы A) · количество — калькулятор справа
LW11 = EXW - 300
RX11, RW11 = EX0 + LW11 + 14, EXW - LW11 - 14
_C11 = (LW11 - 2 * EGAP) // 3
PSL_N, PSL_PG = 30, 6
TABOPEN_11 = INIT + "\ndtp_load = yes\ndtp_esl_fill = yes"
plab("h11", "§YВИД§!  §gлюбой вид державы A (её список видов); выбранный вид — общий с «Редактором держав»§!", "§YSPECIES§!  §gany species of empire A (its species list); the selection is shared with the empire editor§!",
     EX0 + 6, EY0 - 40, LW11 - 12, pot=PEP(11), h=26)
_SPW = (LW11 - 2 * 44 - 5 * EGAP) // 3
pb("sp_prev", "‹", "‹", EX0, EY0 - 8, 40, 34, pot=PEP(11, extra=B("from", chk("dtp_espg", 1, ">"))), effect=B("from", "change_variable = { which = dtp_espg value = -1 }"),
   tt=("Предыдущие виды державы A.", "Previous species of empire A."))
pb("sp_main_on", "Основной вид A", "A's main species", EX0 + 44, EY0 - 8, LW11 - 2 * 44 - 8, 34, pot=PEP(11, extra="dtp_tsp_none = yes"), sprite="GFX_dtp_btn_on",
   tt=("Выбран основной вид державы A.", "Empire A's main species is selected."))
pb("sp_main", "Основной вид A", "A's main species", EX0 + 44, EY0 - 8, LW11 - 2 * 44 - 8, 34, pot=PEP(11, extra="NOT = { dtp_tsp_none = yes }"),
   effect=chain(lambda k: B("if", B("limit", "exists = event_target:dtp_tsp_%d" % k), "clear_global_event_target = dtp_tsp_%d" % k), None),
   tt=("Добавлять основной вид державы A.", "Add empire A's main species."))
pb("sp_ref", "↻", "↻", EX0 + LW11 - 40, EY0 - 8, 40, 34, pot=PEP(11), effect=TABOPEN_11,
   tt=("Обновить список видов державы A (если A сменилась или появились новые виды).", "Refresh empire A's species list (if A changed or new species appeared)."))
for j in range(1, PSL_N + 1):
    pgj = (j - 1) // PSL_PG + 1
    i_ = (j - 1) % PSL_PG
    x = EX0 + (i_ % 3) * (_C11 + EGAP); y = EY0 + 30 + (i_ // 3) * 38
    pe = "exists = event_target:dtp_esl_%d" % j
    pot_pg = B("from", chk("dtp_espg", pgj)) if pgj > 1 else B("from", B("OR", chk("dtp_espg", 1), "NOT = { is_variable_set = dtp_espg }"))
    pb("sp%d_on" % j, "[dtp_esl_%d.GetName]" % j, "[dtp_esl_%d.GetName]" % j, x, y, _C11, 34, pot=PEP(11, extra=pot_pg + "\n" + pe + "\ndtp_esl_sel = { J = %d }" % j), sprite="GFX_dtp_btn_on",
       tt=("Выбран этот вид — население будет этого вида.", "This species is selected — new pops will be of it."))
    pb("sp%d" % j, "[dtp_esl_%d.GetName]" % j, "[dtp_esl_%d.GetName]" % j, x, y, _C11, 34, pot=PEP(11, extra=pot_pg + "\n" + pe + "\nNOT = { dtp_esl_sel = { J = %d } }" % j),
       effect=B("if", B("limit", pe), chain(lambda k, j=j: B("event_target:dtp_esl_%d" % j, "save_global_event_target_as = dtp_tsp_%d" % k), None)),
       tt=("Выбрать этот вид державы A для нового населения.", "Pick this species of empire A for new pops."))
pb("sp_next", "›", "›", EX0 + LW11 - 40 - 44, EY0 - 8, 40, 34,
   pot=PEP(11, extra=B("OR", *[B("AND", B("from", chk("dtp_espg", p_) if p_ > 1 else B("OR", chk("dtp_espg", 1), "NOT = { is_variable_set = dtp_espg }")),
                                       "exists = event_target:dtp_esl_%d" % (p_ * PSL_PG + 1)) for p_ in range(1, PSL_N // PSL_PG)])),
   effect=B("from", B("if", B("limit", "NOT = { is_variable_set = dtp_espg }"), setv("dtp_espg", 1)), "change_variable = { which = dtp_espg value = 1 }"),
   tt=("Следующие виды державы A.", "Next species of empire A."))
plab("sp_empty", "§gСписок видов пуст — нажмите ↻ (нужна выбранная держава A)§!", "§gThe species list is empty — press ↻ (empire A must be selected)§!", EX0 + 6, EY0 + 36, LW11 - 12,
     pot=PEP(11, extra="NOT = { exists = event_target:dtp_esl_1 }"), h=26)
_ya11 = EY0 + 30 + 2 * 38 + 10
plab("h11a", "§YДОБАВИТЬ§!  §gколичество — число калькулятора справа (100 = одна обычная группа)§!", "§YADD§!  §gamount — the calculator number on the right (100 = one regular group)§!",
     EX0 + 6, _ya11, LW11 - 12, pot=PEP(11), h=26)
# количество из числа калькулятора: по разрядам (не больше 9 групп на разряд), без отрицательных
_POPADD = "\n".join(["dtp_sp_load = yes", B("event_target:dtp_p", setv("dtp_pn", "from.dtp_in")),
    B("event_target:dtp_p", B("if", B("limit", "is_colony = yes", "exists = event_target:dtp_sp"),
        *[B("while", B("limit", chk("dtp_pn", n_, ">=")), "create_pop_group = { species = event_target:dtp_sp size = %d }" % n_, "change_variable = { which = dtp_pn value = -%d }" % n_)
          for n_ in (100000, 10000, 1000, 100, 10, 1)]))])
_POPFIX = lambda n_: "\n".join(["dtp_sp_load = yes", B("event_target:dtp_p", B("if", B("limit", "is_colony = yes", "exists = event_target:dtp_sp"), "create_pop_group = { species = event_target:dtp_sp size = %d }" % n_))])
_AL11 = need_perm("planet") + "\n" + N_TP() + "\n" + N_TC() + "\n" + need("dtp_need_colony", "Это не колония", "dtp_tp_colony = yes")
pb("pop_n", "+ §Y[From.dtp_in]§! населения выбранного вида", "+ §Y[From.dtp_in]§! pops of the selected species", EX0, _ya11 + 30, LW11, 38, pot=PEP(11), allow=_AL11,
   effect=act("planet", _POPADD, 73), sprite="GFX_dtp_btn_go",
   tt=("Добавить на выбранную колонию столько населения выбранного вида, сколько набрано в калькуляторе справа.", "Add as many pops of the selected species to the selected colony as the calculator on the right shows."))
_C4 = (LW11 - 3 * EGAP) // 4
for j, n in enumerate([100, 500, 1000, 5000]):
    pb("pop_f%d" % n, "+%d" % n, "+%d" % n, EX0 + j * (_C4 + EGAP), _ya11 + 74, _C4, 34, pot=PEP(11), allow=_AL11, effect=act("planet", _POPFIX(n), 73), sprite="GFX_dtp_btn_go",
       tt=("Добавить %d населения выбранного вида." % n, "Add %d pops of the selected species." % n))
_yk11 = _ya11 + 124
plab("h11b", "§YУБРАТЬ НАСЕЛЕНИЕ§!  §gиз всех групп колонии§!", "§YREMOVE POPULATION§!  §gfrom every group of the colony§!", EX0 + 6, _yk11, LW11 - 12, pot=PEP(11), h=26)
for j, (p, ru, en) in enumerate([(0.1, "−10%", "−10%"), (0.25, "−25%", "−25%"), (0.5, "−50%", "−50%"), (1, "Убрать всех", "Remove all")]):
    pb("popk%d" % j, ru, en, EX0 + j * (_C4 + EGAP), _yk11 + 30, _C4, 34, pot=PEP(11), allow=need_perm("planet") + "\n" + N_TP() + "\n" + need("dtp_need_colony", "Это не колония", "dtp_tp_colony = yes"),
       effect=PACT(B("every_owned_pop_group", "kill_pop_group = { pop_group = this percentage = %s }" % p), 73), sprite="GFX_dtp_btn_danger",
       tt=("Убрать %s всех групп населения выбранной колонии." % ("всё население" if p == 1 else "%d%% населения" % int(p * 100)),
           "Remove %s of every pop group on the selected colony." % ("all pops" if p == 1 else "%d%%" % int(p * 100))))

# ================================================================ 12. МОДИФИКАТОРЫ ПЛАНЕТЫ: «Свои» / «Бонусы игры» / «Штрафы игры», справа калькулятор силы и срока
LW12 = EXW - 300
RX12, RW12 = EX0 + LW12 + 14, EXW - LW12 - 14
_c12 = (LW12 - 12) // 3
_ts = (LW12 - 12) // 3
for i, (c, ru, en) in enumerate([(1, "Свои модификаторы", "Toolpack modifiers"), (2, "Бонусы игры", "Game bonuses"), (3, "Штрафы игры", "Game penalties")]):
    x = EX0 + i * (_ts + 6)
    pb("t12_c%d_on" % c, ru, en, x, EY0 - 42, _ts, 34, pot=PEP(12, c), sprite="GFX_dtp_tab_on", tt=("Открыт подраздел «%s»." % ru, "Sub-section '%s' is open." % en))
    pb("t12_c%d" % c, ru, en, x, EY0 - 42, _ts, 34, pot=PEP(12, extra=B("from", "NOT = { %s }" % chk("dtp_pecat", c))),
       effect=B("from", setv("dtp_pecat", c), setv("dtp_pepg", 1)), sprite="GFX_dtp_tab", tt=("Открыть подраздел «%s»." % ru, "Open the '%s' sub-section." % en))
# свои: прежние 7 (как в главной панели) + новые
_UMP_EN = {"stab": "Stability", "habit": "Habitability", "output": "Job output", "amen": "Amenities", "crime": "Crime", "growth": "Pop growth", "build": "Build speed"}
UMP_EXTRA = [("energy", "Энергия", "Energy", "planet_jobs_energy_produces_mult", 0.01, "%"), ("minerals", "Минералы", "Minerals", "planet_jobs_minerals_produces_mult", 0.01, "%"),
             ("food", "Пища", "Food", "planet_jobs_food_produces_mult", 0.01, "%"), ("alloys", "Сплавы", "Alloys", "planet_jobs_alloys_produces_mult", 0.01, "%"),
             ("cg", "Товары", "Consumer goods", "planet_jobs_consumer_goods_produces_mult", 0.01, "%"), ("unity", "Единство", "Unity", "planet_jobs_unity_produces_mult", 0.01, "%"),
             ("phys", "Физика", "Physics", "planet_jobs_physics_research_produces_mult", 0.01, "%"), ("soc", "Социология", "Society", "planet_jobs_society_research_produces_mult", 0.01, "%"),
             ("eng", "Инженерия", "Engineering", "planet_jobs_engineering_research_produces_mult", 0.01, "%"), ("infl", "Влияние", "Influence", "planet_jobs_influence_produces_mult", 0.01, "%"),
             ("trade", "Торговля", "Trade", "planet_jobs_trade_produces_mult", 0.01, "%"), ("gases", "Экзотич. газы", "Exotic gases", "planet_jobs_exotic_gases_produces_mult", 0.01, "%"),
             ("crystals", "Редкие кристаллы", "Rare crystals", "planet_jobs_rare_crystals_produces_mult", 0.01, "%"), ("motes", "Летучая пыль", "Volatile motes", "planet_jobs_volatile_motes_produces_mult", 0.01, "%"),
             ("housing", "Жильё", "Housing", "planet_housing_add", 1, "ед."), ("districts", "Лимит районов", "District cap", "planet_max_districts_add", 1, "ед."),
             ("dcost", "Цена районов", "District cost", "planet_districts_cost_mult", 0.01, "%"), ("bcost", "Цена зданий", "Building cost", "planet_buildings_cost_mult", 0.01, "%"),
             ("upkeep", "Содержание населения", "Pop upkeep", "planet_pops_upkeep_mult", 0.01, "%"), ("jupkeep", "Содержание работ", "Job upkeep", "planet_jobs_upkeep_mult", 0.01, "%"),
             ("happy", "Одобрение", "Approval", "pop_happiness", 0.01, "%"), ("work", "Рабочая сила", "Workforce", "pop_workforce_mult", 0.01, "%"),
             ("armies", "Армии обороны", "Defense armies", "planet_defense_armies_add", 1, "ед."), ("armyhp", "Здоровье армий", "Army health", "army_defense_health_mult", 0.01, "%"),
             ("bomb", "Урон бомбардировки", "Bombardment damage", "planet_orbital_bombardment_damage", 0.01, "%"), ("assembly", "Сборка населения", "Pop assembly", "planet_pop_assembly_mult", 0.01, "%"),
             ("terra", "Цена терраформ.", "Terraforming cost", "terraforming_cost_mult", 0.01, "%"), ("decision", "Скорость решений", "Decision speed", "planet_decision_enact_speed_mult", 0.01, "%"),
             ("stabm", "Стаб. множитель", "Stability mult.", "planet_stability_mult", 0.01, "%")]
loc("mod_planet_jobs_influence_produces_mult", "Влияние от работ")       # у игры нет строки (error.log)
tren(L["mod_planet_jobs_influence_produces_mult"], "Influence from Jobs")
_UMP = [(k, UMSHORT.get(n, n), _UMP_EN.get(k, n), mk, unit, u) for k, n, mk, unit, u in UMODS["p"]]
for k, ru, en, mk, unit, u in UMP_EXTRA:
    key = "dtp_up_%s" % k
    UMOD_STATIC.append("%s = {\n\t%s = %s\n}" % (key, mk, unit))
    loc(key, "Toolpack: " + ru); tren("Toolpack: " + ru, "Toolpack: " + en)
    loc(key + "_desc", "Модификатор выдан через Debug Toolpack.")
    _UMP.append((k, ru, en, mk, unit, u))
plab("um_h", "§YСИЛА 1 = 1%§!  §gу «%» · у «ед.» — 1 единица · минус — штраф · ещё раз — снять§!",
     "§YSTRENGTH 1 = 1%§!  §gfor '%' · for 'units' — 1 unit · minus is a penalty · click again to remove§!", EX0, EY0 - 4, LW12, pot=PEP(12, 1), h=26)
_UMPTEX = {"energy": "energy", "minerals": "minerals", "food": "food", "alloys": "alloys", "cg": "consumer_goods", "unity": "unity", "phys": "physics_research", "soc": "society_research",
           "eng": "engineering_research", "infl": "influence", "trade": "trade_value", "gases": "exotic_gases", "crystals": "rare_crystals", "motes": "volatile_motes",
           "housing": "consumer_goods", "districts": "minerals", "dcost": "minerals", "bcost": "minerals", "upkeep": "energy", "jupkeep": "energy", "happy": "unity", "work": "minerals",
           "armies": "alloys", "armyhp": "alloys", "bomb": "alloys", "assembly": "food", "terra": "minerals", "decision": "influence", "stabm": "unity",
           "stab": "unity", "habit": "food", "output": "minerals", "amen": "consumer_goods", "crime": "trade_value", "growth": "food", "build": "minerals"}
for i, (k, ru, en, mk, unit, u) in enumerate(_UMP):
    key = "dtp_up_%s" % k
    x = EX0 + (i % 3) * (_c12 + EGAP); y = EY0 + 26 + (i // 3) * 34
    hasT = "dtp_p_hasmod = { M = %s }" % key
    tag = "  §g%§!" if u == "%" else "  §gед.§!"; tag_en = "  §g%§!" if u == "%" else "  §gu.§!"
    add = "\n".join([B("event_target:dtp_p", setv("dtp_tv", "from.dtp_val"), setv("dtp_ty", "from.dtp_years"), "remove_modifier = %s" % key),
                     B("if", B("limit", B("from", chk("dtp_years", 0, "<="))), B("event_target:dtp_p", "add_modifier = { modifier = %s days = -1 multiplier = dtp_tv }" % key)),
                     B("else", B("event_target:dtp_p", "add_modifier = { modifier = %s days = 360 time_multiplier = dtp_ty multiplier = dtp_tv }" % key))])
    expl = ("сила 10 = +10%, сила −25 = −25%" if u == "%" else "сила 10 = +10, сила −5 = −5")
    expl_en = ("strength 10 = +10%, strength −25 = −25%" if u == "%" else "strength 10 = +10, strength −5 = −5")
    _pad = "            "
    pb("um_%s_on" % k, _pad + "§G●§! " + ru + tag, _pad + "§G●§! " + en + tag_en, x, y, _c12, 30, pot=PEP(12, 1, extra=hasT), allow=need_perm("planet") + "\n" + N_TP(),
       effect=act("planet", B("event_target:dtp_p", "remove_modifier = %s" % key), 6), sprite="GFX_dtp_btn_on", left=True,
       tt=("Действует на выбранной планете. Нажмите, чтобы СНЯТЬ «%s»." % ru, "Active on the selected planet. Click to REMOVE '%s'." % en))
    pb("um_" + k, _pad + ru + tag, _pad + en + tag_en, x, y, _c12, 30, pot=PEP(12, 1, extra="NOT = { %s }" % hasT), allow=need_perm("planet") + "\n" + N_TP(),
       effect=act("planet", add, 5), left=True, tt=("«%s» для выбранной планеты: сила из калькулятора справа (%s). Отрицательная сила — штраф. Срок — там же." % (ru, expl),
                                       "'%s' for the selected planet: strength from the calculator on the right (%s). Negative strength is a penalty. Duration is set there too." % (en, expl_en)))
    for nm_ in ("um_%s_on" % k, "um_" + k):
        g_ = [g for g in GUI if g["key"] == "dtp_b_pe_" + nm_][0]; m_ = [m for m in META if m["key"] == "dtp_b_pe_" + nm_][0]
        _s = gspr(_GI + "resources/%s.dds" % _UMPTEX.get(k, "minerals"))
        GUI.append(dict(g_, key=g_["key"] + "_ic", x=x + 6, y=y + 4, w=22, h=22, sprite=_s, label=True, eff=g_["key"], left=False, transp=True, tt=None))
        META.append(dict(m_, key=g_["key"] + "_ic", x=x + 6, y=y + 4, w=22, h=22, sprite=_s, label=True, text=""))
        L[g_["key"] + "_ic"] = ""
# модификаторы игры для планеты — из файлов игры (static_modifiers): бонусы и штрафы, у каждого свой значок
_BADK = ("crime", "upkeep", "cost", "usage", "devastation", "unemployment", "decline")
def _sm_sign(eff):
    sc = 0
    for kk, v in eff:
        try: fv = float(v)
        except ValueError: continue
        bad = any(b_ in kk for b_ in _BADK)
        sc += (-fv if bad else fv) * (0.05 if abs(fv) > 3 else 1)
    return sc
_SMALL = _ed.top(os.path.join(VC, "static_modifiers/*.txt"))
def vpretty(key):
    """Действие модификатора строками: значение цветом (зелёный — хорошо, красный — плохо) и название из самой игры ($mod_…$)."""
    out = []
    for kk, op, v in (_SMALL[key][0] if key in _SMALL else []):
        if not kk or kk in ("icon", "icon_frame") or not isinstance(v, str): continue
        try: fv = float(v)
        except ValueError: continue
        pct = kk.endswith(("_mult", "pop_happiness", "_tolerance")) and abs(fv) < 5
        good = (fv > 0) != any(b_ in kk for b_ in _BADK)
        val = ("%+d%%" % round(fv * 100)) if pct else ("%+g" % fv)
        out.append("%s%s§! $mod_%s$" % ("§G" if good else "§R", val.replace("-", "−"), kk))
    return "\n".join(out)
_PMK = {x["key"] for x in _PM}
_GB, _GP = [], []
for k, (b, f) in _SMALL.items():
    ic = _ed.get(b, "icon")
    if not isinstance(ic, str) or not ic.strip('"').endswith(".dds") or k in _PMK or k.startswith("dtp"): continue
    eff = [(kk, v) for kk, op, v in b if kk and kk not in ("icon", "icon_frame", "custom_tooltip", "show_only_custom_tooltip", "description") and isinstance(v, str)]
    if not eff or not all(kk.startswith(("planet_", "pop_", "logistic", "army_defense")) for kk, v in eff): continue
    sc = _sm_sign(eff)
    if sc > 0: _GB.append((k, ic.strip('"')))
    elif sc < 0: _GP.append((k, ic.strip('"')))
_GB, _GP = _GB[:150], _GP[:150]
for c, lst in ((2, _GB), (3, _GP)):
    def mk(i, it, x, y, w, pot):
        k, ic = it
        pcard("gm_" + k, _nm(k), _nm(k), x, y, w, pot, ic, phas("gm_" + k, "has_modifier = %s" % k), None,
              PT(B("if", B("limit", "has_modifier = %s" % k), "remove_modifier = %s" % k) + "\n" + B("else", B("if", B("limit", B("from", chk("dtp_years", 0, "<="))), "add_modifier = { modifier = %s days = -1 }" % k),
                                                                                            B("else", setv("dtp_ty", "from.dtp_years"), "add_modifier = { modifier = %s days = 360 time_multiplier = dtp_ty }" % k)), 5),
              "§Y$%s$§!\n%s\n\n§gНажмите: дать выбранной планете (срок — калькулятор справа, 0 — навсегда); если уже есть — снять.§!" % (k, vpretty(k)),
              "§Y$%s$§!\n%s\n\n§gClick: give it to the selected planet (duration — calculator on the right, 0 — forever); if present — remove it.§!" % (k, vpretty(k)))
    pgrid(12, c, lst, mk, cols=2, tw=LW12)
# ---- калькулятор (то же число dtp_in и срок, что в главной панели и редакторе держав): у «Модификаторов» и у «Населения»
def pcalc(tab, pfx, rx, rw, years, head_ru, head_en, quick):
    P_ = PEP(tab)
    pdeco(pfx + "card", rx, EY0 - 42, rw, EH - 104 - EY0 + 40, "GFX_dtp_card", B("from", PEOPEN, chk("dtp_petab", tab)))
    plab(pfx + "_h", head_ru, head_en, rx + 12, EY0 - 36, rw - 24, pot=P_, h=22)
    pb(pfx + "_in", "  §Y[From.dtp_in]§!", "  §Y[From.dtp_in]§!", rx + 10, EY0 - 10, rw - 20, 40, pot=P_, sprite="GFX_dtp_field", label=True, font="malgun_goth_24")
    kw = (rw - 24 - 12) // 3
    kx = lambda c: rx + 12 + c * (kw + 6)
    for i, dg in enumerate([7, 8, 9, 4, 5, 6, 1, 2, 3, 0]):
        digit = "\n".join([B("if", B("limit", KNEG), "multiply_variable = { which = dtp_in value = 10 }", "change_variable = { which = dtp_in value = %d }" % (-dg)),
                           B("else", "multiply_variable = { which = dtp_in value = 10 }", "change_variable = { which = dtp_in value = %d }" % dg)])
        c, r = (i % 3, i // 3) if dg != 0 else (1, 3)
        pb("%s%d" % (pfx, dg), str(dg), str(dg), kx(c), EY0 + 38 + r * 36, kw, 32, pot=P_, effect=B("from", digit, CAP, SYNC), sprite="GFX_dtp_btn_key",
           tt=("Цифра %d: число = число × 10 + %d." % (dg, dg), "Digit %d: number = number × 10 + %d." % (dg, dg)))
    pb(pfx + "_neg", "−", "−", kx(0), EY0 + 38 + 3 * 36, kw, 32, pot=P_, effect=B("from", KMINUS, SYNC), sprite="GFX_dtp_btn_key", tt=(KMINUS_TT, ED_EN[KMINUS_TT]))
    pb(pfx + "_bs", "←", "←", kx(2), EY0 + 38 + 3 * 36, kw, 32, pot=P_, effect=B("from", "divide_variable = { which = dtp_in value = 10 }",
       B("if", B("limit", chk("dtp_in", 0, "<")), "ceiling_variable = dtp_in"), B("else", "floor_variable = dtp_in"), SYNC), sprite="GFX_dtp_btn_key",
       tt=("Стереть последнюю цифру.", "Erase the last digit."))
    pb(pfx + "_c", "Очистить", "Clear", kx(0), EY0 + 38 + 4 * 36, rw - 24, 32, pot=P_, effect=B("from", setv("dtp_in", 0), "remove_country_flag = dtp_kneg", SYNC), sprite="GFX_dtp_btn_danger",
       tt=("Число = 0.", "Number = 0."))
    qy = EY0 + 38 + 5 * 36 + 4
    qw = (rw - 24 - 3 * 6) // 4
    for j, v in enumerate(quick):
        lbl = (("%+d" % v) if years else str(v)).replace("-", "−")
        pb("%sq%d" % (pfx, j), lbl, lbl, rx + 12 + j * (qw + 6), qy, qw, 30, pot=P_,
           effect=B("from", setv("dtp_in", v), "set_country_flag = dtp_kneg" if v < 0 else "remove_country_flag = dtp_kneg", SYNC),
           sprite="GFX_dtp_btn_danger" if v < 0 else "GFX_dtp_btn_go", tt=("Число = %d." % v, "Number = %d." % v))
    if not years: return
    plab(pfx + "_y", "§YСРОК§!  §g[From.dtp_years] лет (0 — навсегда)§!", "§YDURATION§!  §g[From.dtp_years] years (0 — forever)§!", rx + 12, qy + 40, rw - 24, pot=P_, h=22)
    for j, (v, ru, en) in enumerate([(1, "1 год", "1 yr"), (5, "5 лет", "5 yrs"), (10, "10 лет", "10 yrs"), (0, "Всегда", "Forever")]):
        x = rx + 12 + j * (qw + 6)
        pb("%sy%d" % (pfx, j), ru, en, x, qy + 64, qw, 30, pot=PEP(tab, extra=B("from", "NOT = { %s }" % chk("dtp_years", v))), effect=B("from", setv("dtp_years", v)),
           tt=("Срок модификатора: %s." % ru, "Modifier duration: %s." % en))
        pb("%sy%d_on" % (pfx, j), ru, en, x, qy + 64, qw, 30, pot=PEP(tab, extra=B("from", chk("dtp_years", v))), sprite="GFX_dtp_btn_on", tt=("Выбран срок: %s." % ru, "Selected duration: %s." % en))
    pb(pfx + "_yr", "Срок = число (лет)", "Duration = number (years)", rx + 12, qy + 100, rw - 24, 30, pot=P_,
       effect=B("from", setv("dtp_years", "dtp_in"), B("if", B("limit", chk("dtp_years", 0, "<")), setv("dtp_years", 0))), sprite="GFX_dtp_btn_go",
       tt=("Сделать число сроком модификаторов в годах.", "Use the number as the modifier duration in years."))
pcalc(12, "k", RX12, RW12, True, "§YСИЛА§!  §gсейчас: §Y[From.dtp_val]§!§!", "§YSTRENGTH§!  §gnow: §Y[From.dtp_val]§!§!", [-50, -10, 25, 100])
pcalc(11, "n", RX11, RW11, False, "§YКОЛИЧЕСТВО§!  §gнаселения§!", "§YAMOUNT§!  §gof pops§!", [100, 500, 1000, 5000])

pslots()
# ---- открыть редактор планеты (из главной панели и из окна планеты)
PE_OPEN_EFF = B("from", "dtp_pidx_ensure = yes", "dtp_init_targets = yes", "dtp_host_check = yes") + "\n" + B("from", "set_country_flag = dtp_pe_open", "remove_country_flag = dtp_open", "remove_country_flag = dtp_ed_open",
    B("if", B("limit", "NOT = { is_variable_set = dtp_petab }"), setv("dtp_petab", 1), setv("dtp_pecat", 1), setv("dtp_pepg", 1)))
print("редактор планеты: элементов %d, условий «разрешено игрой» %d" % (sum(1 for g in GUI if g["where"] == "peditor"), len(_POK)))

# ---- значки игры на вкладках и в баннерах
_GI = "gfx/interface/icons/"
PNAVTEX = {1: _GI + "planet_modifiers/pm_extensive_moon_system.dds", 2: _GI + "resources/minerals.dds", 3: _GI + "resources/energy.dds", 4: _GI + "deposits/default.dds",
           5: _GI + "districts/district_city.dds", 6: _GI + "districts/district_specialization_icons/district_specialization_urban.dds", 7: _GI + "buildings/building_research_lab_1.dds",
           8: _GI + "resources/physics_research.dds", 9: _GI + "resources/influence.dds", 10: _GI + "planet_modifiers/pm_lush.dds", 11: _GI + "resources/food.dds",
           12: _GI + "resources/unity.dds"}
for _g, _m in list(zip(GUI, META)):
    if _g["where"] != "peditor" or _g["label"]: continue
    mm = re.match(r"dtp_b_pe_tab(\d+)(_on)?$", _g["key"])
    if not mm or int(mm.group(1)) not in PNAVTEX: continue
    _ru = L[_g["key"]]; _en = ED_EN.get(_ru, _ru); _pad = "            "
    L[_g["key"]] = _m["text"] = _pad + _ru.lstrip(" "); ED_EN[_pad + _ru.lstrip(" ")] = _pad + _en.lstrip(" ")
    _g["left"] = _m["left"] = True
    _s = picon(PNAVTEX[int(mm.group(1))])
    GUI.append(dict(_g, key=_g["key"] + "_ic", x=_g["x"] + 9, y=_g["y"] + 9, w=20, h=20, sprite=_s, label=True, eff=_g["key"], left=False, transp=True, tt=None))
    META.append(dict(_m, key=_g["key"] + "_ic", x=_g["x"] + 9, y=_g["y"] + 9, w=20, h=20, sprite=_s, label=True, text=""))
    L[_g["key"] + "_ic"] = ""
for _t in PNAVTEX:
    lab("pe_ban%d_ic" % _t, "", EX0 + 13, 62 + 9, 22, h=22, potential=B("from", PEOPEN, chk("dtp_petab", _t)), where="peditor")
    GUI[-1]["sprite"] = META[-1]["sprite"] = picon(PNAVTEX[_t]); GUI[-1]["transp"] = True
