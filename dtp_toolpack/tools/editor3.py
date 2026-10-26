# -*- coding: utf-8 -*-
# 11.2: РЕДАКТОР ДЕРЖАВЫ И ВИДА — отдельное окно (как редактор держав игры). Выполняется внутри gen3.py (exec):
# пользуется его button(), act(), B(), GUI/META/L. Окно встраивается в main_bottom.gui (нижняя панель игры всегда на экране),
# чтобы main.gui не превысил предел размера файла.
# Правила: всё, что игра обычно запрещает (условия potential/possible из файлов игры), помечено красным знаком.
# Без принудительного режима такое не нажимается; в принудительном — можно, пометка остаётся.
import eddata as _ed

EW, EH = 1120, 820
EX0, EXW = 220, EW - 220 - 14            # рабочая область
EY0 = 152                                # верх сетки карточек
ECOLS, ECW, ECH, EGAP = 3, (EXW - 12) // 3, 38, 6
EROWS = (EH - 104 - EY0) // (ECH + EGAP)
EPER = EROWS * ECOLS

EDOPEN = "has_country_flag = dtp_ed_open"
def EDP(tab=None, cat=None, pg=None, extra=""):
    c = [EDOPEN] + ([chk("dtp_edtab", tab)] if tab else []) + ([chk("dtp_edcat", cat)] if cat else []) + ([chk("dtp_edpg", pg)] if pg else [])
    return B("from", *c) + ("\n" + extra if extra else "")
def eb(name, ru, en, x, y, w, h=30, pot="", allow="", effect="", tt=None, sprite="GFX_dtp_btn", label=False, left=False, font="cg_16b", transp=False):
    tren(ru, en)
    if tt:
        tt = (tt[0].replace("\n", "\\n"), tt[1].replace("\n", "\\n"))      # в yml перевод строки пишется как \n
        tren(tt[0], tt[1])
    k = button("ed_" + name, ru, x, y, w, h, potential=pot, allow=allow, effect=effect, tt=tt[0] if tt else ("" if label else None), sprite=sprite, label=label, font=font, where="editor")
    if left: GUI[-1]["left"] = META[-1]["left"] = True
    if transp: GUI[-1]["transp"] = True
    return k
def elab(name, ru, en, x, y, w, pot="", h=24, font="cg_16b", sprite="GFX_dtp_label"):
    return eb(name, ru, en, x, y, w, h, pot=pot, sprite=sprite, label=True, font=font)

# ---- условия на державу A (у каждого игрока своя A) и на её основной вид
TRG.append(B("dtp_tcx", orchain(lambda k: B("event_target:dtp_tc_%d" % k, "$T$ = yes"))))
TRG.append(B("dtp_spx", orchain(lambda k: B("event_target:dtp_tc_%d" % k, B("owner_species", "$T$ = yes")))))
_OKN = {}
def okx(name, body, sp=False):
    """Именованное условие «игра это разрешает» (в области державы или её вида)."""
    nm = "dtp_ok_" + name
    if nm not in _OKN:
        _OKN[nm] = "trivial" if not (body or "").strip() else 1      # условий нет — красная метка не нужна
        TRG.append(B(nm, body or "always = yes"))
    return ("dtp_spx = { T = %s }" if sp else "dtp_tcx = { T = %s }") % nm
FORCE_FROM = B("from", "dtp_force_active = yes")
loc("dtp_ed_lock", "§RИгра обычно это запрещает§! (этики, правление, другие модели, вид или происхождение). Включите §Yпринудительный режим§! внизу окна, чтобы поставить всё равно.")
tren(L["dtp_ed_lock"], "§RThe game normally forbids this§! (ethics, authority, other civics, species or origin). Turn on §Yforce mode§! at the bottom of the window to set it anyway.")
def LOCKED(ok):  # нажать можно, если: уже есть (снять можно всегда) / игра разрешает / принудительный режим
    return "custom_tooltip = { fail_text = dtp_ed_lock %s }" % B("OR", FORCE_FROM, ok)
GSPR = {}
def gspr(tex):
    if not tex: return None
    return GAME_SPR.setdefault(tex, "GFX_dtp_gi_" + re.sub(r"\W", "_", tex.split("/")[-1][:-4]))
def card(name, ru, en, x, y, w, pot, tex, has, ok, effect, p, tt_ru, tt_en, sp=False, need=None):
    """Карточка как в редакторе игры: значок игры + название; зелёная рамка — есть у A; красный знак — игра запрещает."""
    allow = need_perm(p) + "\n" + (need or N_TC())
    if ok is not None: allow += "\n" + LOCKED(B("OR", has, ok) if has else ok)
    pad = "              " if tex else "  "        # 11.2.5: в русском шрифте пробел уже — отступ больше (текст наезжал на значок)
    k = eb(name, pad + ru, pad + en, x, y, w, ECH, pot=pot, allow=allow, effect=effect, tt=(tt_ru, tt_en), left=True, sprite="GFX_dtp_ec" if tex else "GFX_dtp_btn")
    GUI[-1]["quiet"] = True              # карточек сотни — без звука щелчка файл окна меньше
    if tex:
        g = dict(GUI[-1]); m = dict(META[-1])
        GUI.append(dict(g, key=k + "_ic", x=x + 5, y=y + 4, w=30, h=30, sprite=gspr(tex), label=True, eff=k, left=False, transp=True, tt=None))
        META.append(dict(m, key=k + "_ic", x=x + 5, y=y + 4, w=30, h=30, sprite=gspr(tex), label=True, text=""))
        L[k + "_ic"] = ""
    # рамка и метка лежат поверх карточки: если игра не пропустит щелчок сквозь них (alwaysTransparent), они делают то же, что карточка
    if has:
        eb(name + "_h", "", "", x, y, w, ECH, pot=pot + "\n" + has, allow=allow, effect=effect, tt=(tt_ru, tt_en), sprite="GFX_dtp_sg", transp=True)
    if ok is not None and _OKN.get(re.search(r"T = (\w+)", ok).group(1)) != "trivial":
        eb(name + "_x", "", "", x + w - 20, y + 3, 17, 17, pot=pot + "\ndtp_has_tc = yes\nNOT = { %s }" % ok, allow=allow, effect=effect, sprite="GFX_dtp_sr", transp=True)
    return k
def slot(i, cols=ECOLS, w=None, row0=0, x0=EX0, cw=None):
    w = w or ECW
    return x0 + (i % cols) * (w + EGAP), EY0 + (row0 + i // cols) * (ECH + EGAP), w
def pages(name, tab, cat, n):
    """Кнопки страниц внизу рабочей области."""
    if n <= 1: return
    y = EH - 96
    elab("%s_pl" % name, "Страница:", "Page:", EX0, y + 4, 100, pot=EDP(tab, cat))
    for p in range(1, n + 1):
        x = EX0 + 104 + (p - 1) * 46
        eb("%s_p%d_on" % (name, p), str(p), str(p), x, y, 42, 30, pot=EDP(tab, cat, p), sprite="GFX_dtp_btn_on",
           tt=("Открыта страница %d." % p, "Page %d is open." % p))
        eb("%s_p%d" % (name, p), str(p), str(p), x, y, 42, 30, pot=EDP(tab, cat, extra=B("from", "NOT = { %s }" % chk("dtp_edpg", p))),
           effect=B("from", setv("dtp_edpg", p)), tt=("Открыть страницу %d." % p, "Open page %d." % p))
def subtabs(tab, items):
    """Подразделы (как вкладки «Обычные / Корпорации / …» в редакторе игры)."""
    w = (EXW - 6 * (len(items) - 1)) // len(items)
    for i, (c, ru, en) in enumerate(items):
        x = EX0 + i * (w + 6)
        eb("t%d_c%d_on" % (tab, c), ru, en, x, EY0 - 42, w, 34, pot=EDP(tab, c), sprite="GFX_dtp_tab_on", tt=("Открыт подраздел «%s»." % ru, "Sub-section '%s' is open." % en))
        eb("t%d_c%d" % (tab, c), ru, en, x, EY0 - 42, w, 34, pot=EDP(tab, extra=B("from", "NOT = { %s }" % chk("dtp_edcat", c))),
           effect=B("from", setv("dtp_edcat", c), setv("dtp_edpg", 1)), sprite="GFX_dtp_tab", tt=("Открыть подраздел «%s»." % ru, "Open the '%s' sub-section." % en))
def grid_items(tab, cat, items, mk, cols=ECOLS, w=None):
    """Раскладка карточек по страницам: mk(i, item, x, y, w, pot)."""
    per = EROWS * cols
    for i, it in enumerate(items):
        pg, j = i // per + 1, i % per
        x, y, ww = slot(j, cols=cols, w=w)
        mk(i, it, x, y, ww, EDP(tab, cat, pg))
    pages("g%d_%s" % (tab, cat or 0), tab, cat, (len(items) + per - 1) // per)

HINT = ("§gзелёная рамка — есть у державы A · §R●§!§g — игра обычно запрещает (только в принудительном режиме)§!",
        "§ggreen frame — empire A has it · §R●§!§g — normally forbidden by the game (force mode only)§!")
SPX = SP   # основной вид A → event_target:dtp_sp

# ================================================================ КАРКАС ОКНА (в стиле главной панели: шапка, карточка A, навигация, баннер раздела, рамка группы)
lab("ed_bg", "", 0, 0, EW, h=EH, potential=B("from", EDOPEN), where="editor"); GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_panel"
lab("ed_decor", "", EW - 186, 4, 180, h=90, potential=B("from", EDOPEN), where="editor"); GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_decor"
lab("ed_logo", "", 16, 12, 34, h=34, potential=B("from", EDOPEN), where="editor"); GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_ico9"
elab("title", "§YРЕДАКТОР§!", "§YEDITOR§!", 58, 8, 200, pot=EDP(), h=24, font="malgun_goth_24")
elab("title2", "§gдержавы и её вида§!", "§gempire & species§!", 60, 32, 200, pot=EDP(), h=20)
# карточка A — как в главной панели: значок «A», название, вид и форма правления
lab("ed_card", "", 268, 6, 520, h=52, potential=B("from", EDOPEN), where="editor"); GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_card"
lab("ed_badge", "", 280, 18, 28, h=28, potential=B("from", EDOPEN), where="editor"); GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_badge_a"
for k in range(1, MAXP + 1):
    pk = EDP(extra=B("from", chk("dtp_pidx", k)))
    elab("a_%d" % k, "§Y[dtp_tc_%d.GetName]§!" % k, "§Y[dtp_tc_%d.GetName]§!" % k, 318, 8, 350, pot=pk + "\nexists = event_target:dtp_tc_%d" % k, h=26, font="malgun_goth_24")
    elab("s_%d" % k, "§gдержава A ·§! [dtp_tc_%d.GetSpeciesName] §g·§! [dtp_tc_%d.GetGovernmentName]" % (k, k), "§gempire A ·§! [dtp_tc_%d.GetSpeciesName] §g·§! [dtp_tc_%d.GetGovernmentName]" % (k, k),
         318, 34, 360, pot=pk + "\nexists = event_target:dtp_tc_%d" % k, h=20)
    elab("a_%d_x" % k, "§gДержава A не выбрана — нажмите «Я» или выберите в панели DTP§!", "§gEmpire A is not selected — press 'Me' or pick one in the DTP panel§!", 318, 18, 360,
         pot=pk + "\nNOT = { exists = event_target:dtp_tc_%d }" % k)
eb("me", "Я", "Me", 734, 14, 46, 36, pot=EDP(), effect=INIT + "\n" + B("from", "dtp_set_tc = yes") + "\ndtp_result = { CODE = 29 }",
   tt=("Редактировать вашу собственную державу. Другую державу выберите в панели DTP (раздел «Держава») или кнопкой «Изменять эту державу» в окне планеты/флота.",
       "Edit your own empire. Pick another empire in the DTP panel (Empire section) or with 'Edit this empire' in a planet/fleet window."))
eb("back", "← Панель DTP", "← DTP panel", EW - 228, 14, 166, 36, pot=EDP(), effect=B("from", "remove_country_flag = dtp_ed_open", "set_country_flag = dtp_open"),
   tt=("Закрыть редактор и вернуться в главную панель Debug Toolpack.", "Close the editor and return to the main Debug Toolpack panel."))
eb("close", "✕", "✕", EW - 54, 14, 40, 36, pot=EDP(), effect=B("from", "remove_country_flag = dtp_ed_open"), sprite="GFX_dtp_btn_danger",
   tt=("Закрыть редактор.", "Close the editor."))
ETABS = [(1, "Этика и правление", "Ethics & authority"), (2, "Гражданские модели", "Civics"), (3, "Традиции", "Traditions"),
         (4, "Перки возвышения", "Ascension perks"), (5, "Политика", "Policies"), (6, "Черты вида", "Species traits"),
         (7, "Права вида", "Species rights"), (10, "Портрет вида", "Species portrait"), (8, "Облик и название", "Look & name"), (9, "Модификаторы", "Modifiers")]
ETT = {1: ("Этики державы (обычные и фанатичные), коллективное сознание и форма правления.", "Empire ethics (regular and fanatic), gestalt consciousness and authority."),
       2: ("Все гражданские модели игры: обычные, корпоративные, коллективного разума, машинные и особые.", "All civics in the game: regular, corporate, hive mind, machine and special."),
       3: ("Деревья традиций: принять целиком или убрать.", "Tradition trees: adopt fully or remove."),
       4: ("Перки возвышения: добавить или убрать.", "Ascension perks: add or remove."),
       5: ("Политики державы: выбрать вариант каждой политики.", "Empire policies: pick an option for each policy."),
       6: ("Черты основного вида державы A.", "Traits of empire A's main species."),
       7: ("Гражданство, уровень жизни, служба, рабство, чистки основного вида A.", "Citizenship, living standard, service, slavery, purge of A's main species."),
       10: ("Класс вида и все портреты класса — как в редакторе вида игры.", "Species class and all portraits of the class — like the game's species editor."),
       8: ("Облик кораблей и городов, флаг, название державы и вида.", "Ship and city style, flag, empire and species name."),
       9: ("Бонусы и штрафы державы A: свои модификаторы Toolpack и модификаторы самой игры.", "Bonuses and penalties for empire A: Toolpack modifiers and the game's own modifiers.")}
ESUB = {1: ("этики · коллективное сознание · правление", "ethics · gestalt · authority"), 2: ("как при создании державы", "as in empire creation"),
        3: ("деревья целиком", "whole trees"), 4: ("добавить или убрать", "add or remove"), 5: ("вариант каждой политики", "an option for each policy"),
        6: ("черты основного вида A", "traits of A's main species"), 7: ("гражданство · жизнь · служба · рабство · чистка", "citizenship · living · service · slavery · purge"), 10: ("класс · все портреты класса", "class · all portraits of the class"),
        8: ("корабли · города · флаг · название", "ships · cities · flag · name"), 9: ("бонусы и штрафы державы A", "bonuses and penalties of empire A")}
lab("ed_navbg", "", 8, 64, 206, h=EH - 72, potential=B("from", EDOPEN), where="editor"); GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_frame"
elab("navh", "§gРАЗДЕЛЫ§!", "§gSECTIONS§!", 22, 70, 180, pot=EDP(), h=22)
for i, (t, ru, en) in enumerate(ETABS):
    y = 96 + i * 42
    eb("tab%d_on" % t, ru, en, 14, y, 194, 38, pot=EDP(t), sprite="GFX_dtp_ednav_on", tt=ETT[t])
    eb("tab%d" % t, ru, en, 14, y, 194, 38, pot=EDP(extra=B("from", "NOT = { %s }" % chk("dtp_edtab", t))),
       effect=B("from", setv("dtp_edtab", t), setv("dtp_edcat", 1), setv("dtp_edpg", 1)) + ("\n" + INIT + "\ndtp_load = yes\ndtp_esl_fill = yes" if t == 7 else ""), sprite="GFX_dtp_ednav", tt=ETT[t])
    # шапка раздела — баннер, как в главной панели (значок раздела — значок самой игры)
    lab("ed_ban%d" % t, "", EX0, 62, EXW, h=40, potential=B("from", EDOPEN, chk("dtp_edtab", t)), where="editor"); GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_ebanner_%d" % t
    elab("bt%d" % t, ru.upper(), en.upper(), EX0 + 50, 66, 500, pot=EDP(t), h=30, font="large_title_font")
    elab("bs%d" % t, "§g%s§!" % ESUB[t][0], "§g%s§!" % ESUB[t][1], EX0 + 560, 72, EXW - 570, pot=EDP(t), h=22)
lab("ed_grp", "", EX0 - 6, EY0 - 46, EXW + 12, h=EH - 104 - EY0 + 50, potential=B("from", EDOPEN, "NOT = { %s }" % chk("dtp_edtab", 1)), where="editor"); GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_group"
# раздел 1: две отдельные рамки — «Этика» слева, «Форма правления» справа
ETW = 2 * 280 + EGAP                      # ширина блока этик
AUX = EX0 + ETW + 26                      # левый край блока правления
AUW = EX0 + EXW - AUX
lab("ed_grp_e", "", EX0 - 6, EY0 - 46, ETW + 12, h=EH - 104 - EY0 + 50, potential=B("from", EDOPEN, chk("dtp_edtab", 1)), where="editor"); GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_group"
lab("ed_grp_a", "", AUX - 6, EY0 - 46, AUW + 12, h=EH - 104 - EY0 + 50, potential=B("from", EDOPEN, chk("dtp_edtab", 1)), where="editor"); GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_group"
elab("lg1", "§Gзелёная рамка§! — есть у A", "§Ggreen frame§! — A has it", 18, EH - 150, 190, pot=EDP())
elab("lg2", "§R●§! — игра обычно запрещает", "§R●§! — normally forbidden", 18, EH - 126, 190, pot=EDP())
# низ окна: итог действия и принудительный режим
for nm, ru, en, cond, spr in [("r_idle", "   §gИтог последнего действия появится здесь§!", "   §gThe result of your last action will appear here§!", "NOT = { is_variable_set = dtp_last_ok }", "GFX_dtp_res_idle"),
                              ("r_ok", "   §GГОТОВО§!  ·  изменение применено к державе A", "   §GDONE§!  ·  the change was applied to empire A", chk("dtp_last_ok", 1), "GFX_dtp_res_ok"),
                              ("r_deny", "   §RОТКАЗАНО§!  ·  нет права — его выдаёт ХОСТ в разделе «Доступ»", "   §RDENIED§!  ·  no permission — the HOST grants it in the Access section", chk("dtp_last_ok", 0), "GFX_dtp_res_bad"),
                              ("r_fail", "   §HНЕ ВЫПОЛНЕНО§!  ·  держава A не выбрана или исчезла", "   §HNOT DONE§!  ·  empire A is not selected or no longer exists", chk("dtp_last_ok", 2), "GFX_dtp_res_warn")]:
    elab(nm, ru, en, EX0, EH - 54, EXW - 330, pot=EDP(extra=B("from", cond)), h=44, sprite=spr)
eb("force_on", "Принудительный режим: ВЫКЛ", "Force mode: OFF", EW - 324, EH - 54, 310, 44, pot=EDP(extra=B("from", "NOT = { has_country_flag = dtp_force_mode }")),
   allow=need_perm("force"), effect=B("from", B("if", B("limit", "dtp_has_perm = { P = force }"), "set_country_flag = dtp_force_mode")) + "\ndtp_result = { CODE = 30 }",
   tt=("Сейчас действуют правила игры: помеченное §R●§! поставить нельзя. Нажмите, чтобы включить принудительный режим — тогда можно всё.",
       "The game's rules apply now: items marked §R●§! cannot be set. Click to turn on force mode — then everything is allowed."))
eb("force_off", "Принудительный режим: ВКЛ", "Force mode: ON", EW - 324, EH - 54, 310, 44, pot=EDP(extra=B("from", "has_country_flag = dtp_force_mode")),
   effect=B("from", "remove_country_flag = dtp_force_mode") + "\ndtp_result = { CODE = 30 }", sprite="GFX_dtp_btn_warn",
   tt=("Принудительный режим включён: можно ставить и то, что игра обычно запрещает (помечено §R●§!). Нажмите, чтобы выключить.",
       "Force mode is on: you can set things the game normally forbids (marked §R●§!). Click to turn it off."))
def head(tab, ru, en, y=EY0 - 40):
    elab("h%d" % tab, ru, en, EX0 + 6, y + 4, EXW - 12, pot=EDP(tab), h=28)

# ================================================================ 1. ЭТИКА И ПРАВЛЕНИЕ
AXES = [("militarist", "pacifist"), ("pacifist", "militarist"), ("xenophobe", "xenophile"), ("xenophile", "xenophobe"),
        ("authoritarian", "egalitarian"), ("egalitarian", "authoritarian"), ("spiritualist", "materialist"), ("materialist", "spiritualist")]
ETH_RU = dict(ETHICS)
ETH_EN = {"militarist": "Militarist", "pacifist": "Pacifist", "xenophobe": "Xenophobe", "xenophile": "Xenophile", "authoritarian": "Authoritarian",
          "egalitarian": "Egalitarian", "spiritualist": "Spiritualist", "materialist": "Materialist"}
def _pts(excl, amount):
    """«очков этик у остальных осей не меньше amount» (фанатичная = 2)."""
    ts = []
    for a, _o in AXES:
        if a in excl: continue
        ts += ["has_ethic = ethic_%s" % a, "has_ethic = ethic_fanatic_%s" % a, B("AND", "has_ethic = ethic_fanatic_%s" % a)]
    return B("calc_true_if", "amount >= %d" % amount, *ts)        # «amount = N» у игры — ровно N; нужно «не меньше»
elab("e1h", "§YЭТИКА§!  §gвсего 3 очка · противоположные несовместимы§!", "§YETHICS§!  §g3 points total · opposites are incompatible§!", EX0 + 4, EY0 - 42, ETW - 8, pot=EDP(1), h=24)
elab("e1c1", "§gобычная — 1 очко§!", "§gregular — 1 point§!", EX0 + 44, EY0 - 20, 230, pot=EDP(1), h=18)
elab("e1c2", "§gфанатичная — 2 очка§!", "§gfanatic — 2 points§!", EX0 + 280 + EGAP + 44, EY0 - 20, 230, pot=EDP(1), h=18)
elab("a1h", "§YФОРМА ПРАВЛЕНИЯ§!", "§YAUTHORITY§!", AUX + 4, EY0 - 42, AUW - 8, pot=EDP(1), h=24)
elab("a1c", "§gэтики подстроятся сами§!", "§gethics adjust automatically§!", AUX + 4, EY0 - 20, AUW - 8, pot=EDP(1), h=18)
for i, (a, o) in enumerate(AXES):
    y = EY0 + i * (ECH + EGAP) + (i // 2) * 10          # противоположные этики — парой, между парами промежуток
    ex = "has_ethic = ethic_%s" % a; fx = "has_ethic = ethic_fanatic_%s" % a
    base = ["NOT = { has_ethic = ethic_gestalt_consciousness }", "NOR = { has_ethic = ethic_%s has_ethic = ethic_fanatic_%s }" % (o, o)]
    ok_n = okx("eth_" + a, "\n".join(base + ["NOT = { %s }" % _pts((a, o), 3)]))
    ok_f = okx("eth_f_" + a, "\n".join(base + ["NOT = { %s }" % _pts((a, o), 2)]))
    tx = "gfx/interface/icons/ethics/ethic_%s.dds" % a; tf = "gfx/interface/icons/ethics/ethic_fanatic_%s.dds" % a
    card("eth_" + a, ETH_RU[a], ETH_EN[a], EX0, y, 280, EDP(1), tx, "dtp_tcx = { T = dtp_has_e_%s }" % a, ok_n,
         act("state", B("event_target:dtp_t", B("if", B("limit", ex), "country_remove_ethic = ethic_%s" % a),
                         B("else_if", B("limit", fx), "country_remove_ethic = ethic_fanatic_%s" % a, "country_add_ethic = ethic_%s" % a),
                         B("else", "country_add_ethic = ethic_%s" % a)), 20), "state",
         "§Y$ethic_%s$§!\n$ethic_%s_desc$\n\n§gНажмите: добавить этику (у фанатичной — сделать обычной); если уже есть — убрать.§!" % (a, a),
         "§Y$ethic_%s$§!\n$ethic_%s_desc$\n\n§gClick: add the ethic (a fanatic one becomes regular); if already present — remove it.§!" % (a, a))
    TRG.append(B("dtp_has_e_%s" % a, ex))
    TRG.append(B("dtp_has_ef_%s" % a, fx))
    card("ethf_" + a, "Фанат. " + ETH_RU[a].lower(), "Fanatic " + ETH_EN[a].lower(), EX0 + 280 + EGAP, y, 280, EDP(1), tf, "dtp_tcx = { T = dtp_has_ef_%s }" % a, ok_f,
         act("state", B("event_target:dtp_t", B("if", B("limit", fx), "country_remove_ethic = ethic_fanatic_%s" % a),
                         B("else", B("if", B("limit", ex), "country_remove_ethic = ethic_%s" % a), "country_add_ethic = ethic_fanatic_%s" % a)), 20), "state",
         "§Y$ethic_fanatic_%s$§!\n$ethic_fanatic_%s_desc$\n\n§gНажмите: сделать этику фанатичной (2 очка); если уже есть — убрать.§!" % (a, a),
         "§Y$ethic_fanatic_%s$§!\n$ethic_fanatic_%s_desc$\n\n§gClick: make the ethic fanatic (2 points); if already present — remove it.§!" % (a, a))
TRG.append(B("dtp_has_e_gestalt", "has_ethic = ethic_gestalt_consciousness"))
_REGULAR_ETH = ["ethic_%s" % a for a, _o in AXES] + ["ethic_fanatic_%s" % a for a, _o in AXES]
ok_g = okx("eth_gestalt", "OR = { has_authority = auth_hive_mind has_authority = auth_machine_intelligence }")
elab("e1g", "§gили, для коллективного и машинного разума:§!", "§gor, for hive minds and machine intelligences:§!", EX0 + 4, EY0 + 8 * (ECH + EGAP) + 3 * 10 + 6, ETW - 8, pot=EDP(1), h=18)
card("eth_gestalt", "Коллективное сознание", "Gestalt Consciousness", EX0, EY0 + 8 * (ECH + EGAP) + 3 * 10 + 28, ETW, EDP(1), "gfx/interface/icons/ethics/ethic_gestalt_consciousness.dds",
     "dtp_tcx = { T = dtp_has_e_gestalt }", ok_g,
     act("state", B("event_target:dtp_t", B("if", B("limit", "has_ethic = ethic_gestalt_consciousness"), "country_remove_ethic = ethic_gestalt_consciousness"),
                     B("else", *[B("if", B("limit", "has_ethic = %s" % e), "country_remove_ethic = %s" % e) for e in _REGULAR_ETH], "country_add_ethic = ethic_gestalt_consciousness")), 20), "state",
     "§Y$ethic_gestalt_consciousness$§!\n$ethic_gestalt_consciousness_desc$\n\n§gНажмите: заменить все этики на коллективное сознание; если уже есть — убрать. Игра разрешает его только при коллективном или машинном разуме.§!",
     "§Y$ethic_gestalt_consciousness$§!\n$ethic_gestalt_consciousness_desc$\n\n§gClick: replace all ethics with gestalt consciousness; if present — remove it. The game allows it only for hive minds and machine intelligences.§!")
_AUTH_RU = dict(AUTHS); _AUTH_RU["auth_ancient_machine_intelligence"] = "Древний машинный разум"
_AUTH_EN = {"auth_democratic": "Democratic", "auth_oligarchic": "Oligarchic", "auth_dictatorial": "Dictatorial", "auth_imperial": "Imperial",
            "auth_corporate": "Corporate", "auth_hive_mind": "Hive Mind", "auth_machine_intelligence": "Machine Intelligence", "auth_ancient_machine_intelligence": "Ancient Machine Intelligence"}
TRG.append(B("dtp_has_auth_x", "has_authority = $A$"))
# 11.2.3: перед сменой правления снимаем гражданские модели, которые с ним заведомо несовместимы — иначе игра не может
# подобрать правительство (error.log: «change_government … ethic_gestalt_consciousness is excluded by restrictions» при имперском культе)
_CIV0 = _ed.civics(VC)
def _civ_bad(c, k):
    req = " ".join(c["req"])
    gest = k in ("auth_hive_mind", "auth_machine_intelligence")
    if c["cat"] == "special":
        if gest and "NOT = { has_ethic = ethic_gestalt_consciousness }" in req: return True
        if not gest and re.search(r"(?<!NOT = \{ )has_ethic = ethic_gestalt_consciousness", req) and "NOT = { has_ethic = ethic_gestalt_consciousness }" not in req: return True
        return False
    want = {"auth_hive_mind": "hive", "auth_machine_intelligence": "machine", "auth_corporate": "corp"}.get(k, "reg")
    if want == "corp" and c["cat"] == "reg": return "NOT = { has_authority = auth_corporate }" in req
    return c["cat"] != want
for _au in _ed.authorities(VC):
    _k = _au["key"]
    EFF.append(B("dtp_ed_civfix_%s" % _k[5:], *[B("if", B("limit", "has_civic = %s" % c["key"]), "force_remove_civic = %s" % c["key"]) for c in _CIV0 if _civ_bad(c, _k)] or ['log = "DTP civfix: nothing"']))
for i, au in enumerate(_ed.authorities(VC)):
    k = au["key"]
    y = EY0 + i * (ECH + EGAP)
    _req = [r.replace("owner_species = { is_archetype = MACHINE }", "owner_species = { dtp_sp_robotlook = yes }") for r in au["req"]]
    ok = okx(k, "\n".join(_req))
    hive = k == "auth_hive_mind"
    fx = [*gov_prep(k)]
    if hive:
        fx += [B("owner_species", B("if", B("limit", "NOT = { has_trait = trait_hive_mind }"), "change_species_characteristics = { add_trait = trait_hive_mind }"))]
    else:
        fx += [B("owner_species", B("if", B("limit", "has_trait = trait_hive_mind", "NOT = { is_archetype = MACHINE }"), "change_species_characteristics = { remove_trait = trait_hive_mind }"))] if k != "auth_machine_intelligence" else []
    if k in ("auth_hive_mind", "auth_machine_intelligence"):     # разумы: все этики → коллективное сознание
        fx = [*[B("if", B("limit", "has_ethic = %s" % e), "country_remove_ethic = %s" % e) for e in _REGULAR_ETH],
              B("if", B("limit", "NOT = { has_ethic = ethic_gestalt_consciousness }"), "country_add_ethic = ethic_gestalt_consciousness")] + fx[1:]
    card(k, _AUTH_RU.get(k, k), _AUTH_EN.get(k, k), AUX, y, AUW, EDP(1), au["icon"], "dtp_tcx = { T = dtp_has_au_%s }" % k[5:], ok,
         act("state", B("event_target:dtp_t", B("if", B("limit", "NOT = { has_authority = %s }" % k), *fx,
                                                 "dtp_ed_civfix_%s = yes" % k[5:], "change_government = { authority = %s cooldown = no remove_invalid_civics = yes }" % k)), 39), "state",
         "§Y$%s$§!\n$%s_desc$\n\n§gНажмите: сменить форму правления. Этики подстраиваются сами (разумы получают коллективное сознание, вид — черту коллективного разума), несовместимые гражданские модели снимаются.§!" % (k, k),
         "§Y$%s$§!\n$%s_desc$\n\n§gClick: change the authority. Ethics adjust automatically (hive and machine minds get gestalt consciousness, the species gets the hive-mind trait), incompatible civics are removed.§!" % (k, k))
    TRG.append(B("dtp_has_au_%s" % k[5:], "has_authority = %s" % k))

# ================================================================ 2. ГРАЖДАНСКИЕ МОДЕЛИ
CIV_CATS = [(1, "reg", "Обычные", "Regular"), (2, "corp", "Корпорации", "Megacorp"), (3, "hive", "Разум-улей", "Hive mind"),
            (4, "machine", "Машинный разум", "Machine"), (5, "special", "Особые", "Special")]
subtabs(2, [(c, ru, en) for c, _k, ru, en in CIV_CATS])
_CIV = _ed.civics(VC)
for c, ck, ru, en in CIV_CATS:
    items = sorted([x for x in _CIV if x["cat"] == ck], key=lambda x: x["key"])
    def mk(i, it, x, y, w, pot):
        k = it["key"]
        TRG.append(B("dtp_has_cv_%s" % k[6:], "has_civic = %s" % k))
        card(k, "$%s$" % k, "$%s$" % k, x, y, w, pot, it["icon"], "dtp_tcx = { T = dtp_has_cv_%s }" % k[6:], okx(k, "\n".join(it["req"])),
             act("state", B("event_target:dtp_t", B("if", B("limit", "has_civic = %s" % k), "force_remove_civic = %s" % k), B("else", "force_add_civic = %s" % k)), 40), "state",
             "§Y$%s$§!\n\n§gНажмите: добавить гражданскую модель; если уже есть — убрать.§!" % k,
             "§Y$%s$§!\n\n§gClick: add the civic; if already present — remove it.§!" % k)
    grid_items(2, c, items, mk)

# ================================================================ 3. ТРАДИЦИИ
_SPRT = _ed.sprite_textures(VI)
head(3, "§YДЕРЕВЬЯ ТРАДИЦИЙ§!  §gнажать — принять дерево целиком (все традиции и бонус завершения); если уже принято — убрать§!",
     "§YTRADITION TREES§!  §gclick — adopt the whole tree (all traditions and the finisher); if adopted — remove it§!")
def mk(i, it, x, y, w, pot):
    k = it["key"]
    TRG.append(B("dtp_has_tt_%s" % k, "has_tradition = %s" % it["adopt"]))
    add = ["add_tradition = %s" % it["adopt"]] + ["add_tradition = %s" % t for t in it["trads"]] + (["add_tradition = %s" % it["finish"]] if it["finish"] else [])
    card(k, "$%s$" % k, "$%s$" % k, x, y, w, pot, it["icon"], "dtp_tcx = { T = dtp_has_tt_%s }" % k, okx(k, "\n".join(it["req"])),
         act("state", B("event_target:dtp_t", B("if", B("limit", "has_tradition = %s" % it["adopt"]), "remove_tradition_tree = %s" % k), B("else", *add)), 63), "state",
         "§Y$%s$§!\n\n§gНажмите: принять всё дерево традиций; если уже принято — убрать дерево.§!" % k, "§Y$%s$§!\n\n§gClick: adopt the whole tradition tree; if adopted — remove the tree.§!" % k)
grid_items(3, None, sorted(_ed.tradition_trees(VC, _SPRT), key=lambda x: x["key"]), mk)

# ================================================================ 4. ПЕРКИ ВОЗВЫШЕНИЯ
head(4, "§YПЕРКИ ВОЗВЫШЕНИЯ§!  §gнажать — добавить перк; если уже есть — убрать§!", "§YASCENSION PERKS§!  §gclick — add the perk; if present — remove it§!")
def mk(i, it, x, y, w, pot):
    k = it["key"]
    TRG.append(B("dtp_has_ap_%s" % k, "has_ascension_perk = %s" % k))
    card(k, "$%s$" % k, "$%s$" % k, x, y, w, pot, it["icon"], "dtp_tcx = { T = dtp_has_ap_%s }" % k, okx(k, "\n".join(it["req"])),
         act("state", B("event_target:dtp_t", B("if", B("limit", "has_ascension_perk = %s" % k), "remove_ascension_perk = %s" % k), B("else", "add_ascension_perk = %s" % k)), 64), "state",
         "§Y$%s$§!\n$%s_desc$\n\n§gНажмите: добавить перк; если уже есть — убрать.§!" % (k, k), "§Y$%s$§!\n$%s_desc$\n\n§gClick: add the perk; if present — remove it.§!" % (k, k))
grid_items(4, None, sorted(_ed.perks(VC, _SPRT), key=lambda x: x["key"]), mk)

# ================================================================ 5. ПОЛИТИКА: слева название политики, справа её варианты
head(5, "§YПОЛИТИКА§!  §gвыбранный вариант — в зелёной рамке; без отката смены§!", "§YPOLICIES§!  §gthe active option has a green frame; no change cooldown§!")
_POL = _ed.policies(VC, _SPRT)
_PW, _OW = 230, (EXW - 236 - 2 * EGAP) // 3
rows, pg, r = [], 1, 0
for po in _POL:
    need_rows = (len(po["opts"]) + 2) // 3
    if r + need_rows > EROWS: pg += 1; r = 0
    rows.append((po, pg, r)); r += need_rows
for po, pg, r in rows:
    k = po["key"]; pot = EDP(5, None, pg)
    elab("pl_" + k, "§Y$policy_%s$§!" % k, "§Y$policy_%s$§!" % k, EX0, EY0 + r * (ECH + EGAP) + 6, _PW, pot=pot, h=ECH - 8)
    for j, o in enumerate(po["opts"]):
        x = EX0 + 236 + (j % 3) * (_OW + EGAP); y = EY0 + (r + j // 3) * (ECH + EGAP)
        n = o["name"]
        has = None
        if o["flag"]:
            TRG.append(B("dtp_has_po_%s" % n, "has_policy_flag = %s" % o["flag"])); has = "dtp_tcx = { T = dtp_has_po_%s }" % n
        card("po_%s_%s" % (k, n), "$%s$" % n, "$%s$" % n, x, y, _OW, pot, o["icon"], has, okx("po_%s_%s" % (k, n), "can_set_policy = { policy = %s option = %s }" % (k, n)),
             act("state", B("event_target:dtp_t", "set_policy = { policy = %s option = %s cooldown = no }" % (k, n)), 65), "state",
             "§Y$%s$§!\n\n§gНажмите: выбрать этот вариант политики.§!" % n, "§Y$%s$§!\n\n§gClick: choose this policy option.§!" % n)
pages("g5", 5, None, pg)

# ================================================================ 6. ЧЕРТЫ ВИДА
TR_CATS = [(1, "bio", "Органические и литоиды", "Organic & lithoid"), (2, "robot", "Роботы и машины", "Robots & machines"),
           (3, "ascend", "Возвышение и особые", "Ascension & special"), (4, "hab", "Пригодность", "Habitability")]
subtabs(6, [(c, ru, en) for c, _k, ru, en in TR_CATS])
_TRS = _ed.traits(VC)
_PR0 = _ed.portraits(VC)
# 11.2: «облик робота» — портрет класса ROBOT/MACHINE (после смены портрета в редакторе вид считается роботом для черт)
TRG.append(B("dtp_sp_robotlook", B("OR", "is_archetype = ROBOT", "is_archetype = MACHINE", *["species_portrait = %s" % p for p in _PR0.get("ROBOT", []) + _PR0.get("MACHINE", [])])))
for c, ck, ru, en in TR_CATS:
    items = sorted([x for x in _TRS if x["grp"] == ck], key=lambda x: x["key"])
    def mk(i, it, x, y, w, pot):
        k = it["key"]
        TRG.append(B("dtp_has_tr_%s" % k[6:], "has_trait = %s" % k))
        cond = []
        if it["special"]: cond.append("always = no")
        robo = set(it["arch"]) & {"ROBOT", "MACHINE"}; bio = set(it["arch"]) & {"BIOLOGICAL", "LITHOID"}
        if it["arch"] and robo and not bio: cond.append("dtp_sp_robotlook = yes")
        elif it["arch"] and bio and not robo: cond += [B("OR", *["is_archetype = %s" % a for a in it["arch"]]), "dtp_sp_robotlook = no"]
        elif it["arch"]: cond.append(B("OR", *["is_archetype = %s" % a for a in it["arch"]]))
        if it["opp"]: cond.append(B("NOR", *["has_trait = %s" % o for o in it["opp"]]))
        card(k, "$%s$" % k, "$%s$" % k, x, y, w, pot, it["icon"], "dtp_spx = { T = dtp_has_tr_%s }" % k[6:], okx("t_" + k, "\n".join(cond), sp=True),
             act("species", SPX + "\n" + B("event_target:dtp_sp", B("if", B("limit", "has_trait = %s" % k), "change_species_characteristics = { remove_trait = %s }" % k),
                                              B("else", "change_species_characteristics = { add_trait = %s }" % k)), 22), "species",
             "§Y$%s$§!\n$%s_desc$\n\n§gНажмите: добавить черту всему виду; если уже есть — убрать. Игра разрешает черту только своему типу вида (органики, литоиды, роботы, машины) и без противоположных черт.§!" % (k, k),
             "§Y$%s$§!\n$%s_desc$\n\n§gClick: add the trait to the whole species; if present — remove it. The game allows a trait only for its species type (organic, lithoid, robot, machine) and without opposite traits.§!" % (k, k), sp=True)
    grid_items(6, c, items, mk)

# ================================================================ 7. ПРАВА И ПОРТРЕТ
_RIGHTS_EN = {"citizenship_full": "Full citizenship", "citizenship_slavery": "Slavery", "citizenship_purge": "Purge",
              "living_standard_utopian": "Utopian abundance", "living_standard_good": "Social welfare", "living_standard_normal": "Stratified (normal)",
              "living_standard_academic_privilege": "Academic privilege", "living_standard_stratified": "Stratified economy", "living_standard_decadent": "Decadent lifestyle",
              "living_standard_subsistence": "Basic subsistence", "living_standard_none": "Living standard: none", "military_service_full": "Service: full",
              "military_service_limited": "Service: limited", "military_service_none": "Service: none", "slavery_normal": "Chattel slavery", "slavery_domestic": "Domestic servitude",
              "slavery_military": "Battle thralls", "slavery_indentured": "Indentured servitude", "slavery_livestock": "Livestock", "purge_normal": "Extermination",
              "purge_displacement": "Displacement", "purge_labor_camps": "Forced labor", "purge_neutering": "Neutering", "purge_processing": "Processing"}
head(7, "§YВИД§!  §gвыберите вид державы A — права ниже меняются для него; без отката; несовместимое с этиками игра может отменить§!",
     "§YSPECIES§!  §gpick a species of empire A — the rights below change for it; no cooldown; the game may revert what conflicts with ethics§!")
# 11.2.5: список видов державы A (общий для всех: заполняется при входе в раздел) и выбранный вид — у каждого игрока свой (dtp_tsp_<номер>)
ESL_N = 9
_fill = [B("if", B("limit", "exists = event_target:dtp_esl_%d" % j), "clear_global_event_target = dtp_esl_%d" % j) for j in range(1, ESL_N + 1)]
_inner = [B("owner_species", "save_global_event_target_as = dtp_esl_1")]
for j in range(2, ESL_N + 1):
    _inner.append(B("if", B("limit", "exists = event_target:dtp_esl_%d" % (j - 1)),
                    B("random_owned_species", B("limit", *["NOT = { is_same_species = event_target:dtp_esl_%d }" % i for i in range(1, j)]), "save_global_event_target_as = dtp_esl_%d" % j)))
EFF.append(B("dtp_esl_fill", *_fill, B("if", B("limit", "exists = event_target:dtp_t"), B("event_target:dtp_t", *_inner))))
EFF.append(B("dtp_sp_load", chain(lambda k: B("if", B("limit", "exists = event_target:dtp_tsp_%d" % k), B("event_target:dtp_tsp_%d" % k, "save_event_target_as = dtp_sp")) + "\n" +
                                            B("else", B("event_target:dtp_t", B("owner_species", "save_event_target_as = dtp_sp"))), None)))
TRG.append(B("dtp_esl_sel", orchain(lambda k: "exists = event_target:dtp_esl_$J$\n" + B("event_target:dtp_tsp_%d" % k, "is_same_species = event_target:dtp_esl_$J$"))))
TRG.append(B("dtp_tsp_none", orchain(lambda k: "NOT = { exists = event_target:dtp_tsp_%d }" % k)))
ESL_FILL = INIT + "\ndtp_load = yes\ndtp_esl_fill = yes"
for k in range(1, MAXP + 1):
    pk = EDP(7, extra=B("from", chk("dtp_pidx", k)))
    elab("sp_sel_%d" % k, "Права меняются для вида: §Y[dtp_tsp_%d.GetName]§!" % k, "Rights change for species: §Y[dtp_tsp_%d.GetName]§!" % k, EX0, EY0 - 4, EXW, pot=pk + "\nexists = event_target:dtp_tsp_%d" % k, h=24)
    elab("sp_sel_%d_x" % k, "Права меняются для §Yосновного вида§! державы A", "Rights change for empire A's §Ymain species§!", EX0, EY0 - 4, EXW,
         pot=pk + "\nNOT = { exists = event_target:dtp_tsp_%d }" % k, h=24)
_sw = (EXW - 24) // 5
eb("sp_main_on", "Основной вид", "Main species", EX0, EY0 + 24, _sw, 32, pot=EDP(7, extra="dtp_tsp_none = yes"), sprite="GFX_dtp_btn_on",
   tt=("Выбран основной вид державы A.", "Empire A's main species is selected."))
eb("sp_main", "Основной вид", "Main species", EX0, EY0 + 24, _sw, 32, pot=EDP(7, extra="NOT = { dtp_tsp_none = yes }"),
   effect=chain(lambda k: B("if", B("limit", "exists = event_target:dtp_tsp_%d" % k), "clear_global_event_target = dtp_tsp_%d" % k), None),
   tt=("Менять права основного вида державы A.", "Change the rights of empire A's main species."))
for j in range(1, ESL_N + 1):
    x = EX0 + (j % 5) * (_sw + EGAP); y = EY0 + 24 + (j // 5) * 36
    pe = "exists = event_target:dtp_esl_%d" % j
    eb("sp_l%d_on" % j, "[dtp_esl_%d.GetName]" % j, "[dtp_esl_%d.GetName]" % j, x, y, _sw, 32, pot=EDP(7, extra=pe + "\ndtp_esl_sel = { J = %d }" % j), sprite="GFX_dtp_btn_on",
       tt=("Выбран этот вид: права ниже меняются для него.", "This species is selected: the rights below change for it."))
    eb("sp_l%d" % j, "[dtp_esl_%d.GetName]" % j, "[dtp_esl_%d.GetName]" % j, x, y, _sw, 32, pot=EDP(7, extra=pe + "\nNOT = { dtp_esl_sel = { J = %d } }" % j),
       effect=B("if", B("limit", pe), chain(lambda k, j=j: B("event_target:dtp_esl_%d" % j, "save_global_event_target_as = dtp_tsp_%d" % k), None)),
       tt=("Выбрать этот вид державы A: права ниже будут меняться для него.", "Pick this species of empire A: the rights below will change for it."))
eb("sp_refresh", "Обновить список", "Refresh list", EX0 + 4 * (_sw + EGAP), EY0 + 24 + 36, _sw, 32, pot=EDP(7), effect=ESL_FILL, sprite="GFX_dtp_btn_go",
   tt=("Перечитать виды державы A (список заполняется сам при входе в раздел).", "Re-read empire A's species (the list fills itself when you open this section)."))
_r = 3
for lst, eff, code, nm_ru, nm_en in [(CITIZEN, "set_citizenship_type", 23, "Гражданство", "Citizenship"), (LIVING, "set_living_standard", 44, "Уровень жизни", "Living standard"),
                                     (MILSRV, "set_military_service_type", 45, "Военная служба", "Military service"), (SLAVE, "set_slavery_type", 46, "Рабство", "Slavery"),
                                     (PURGE, "set_purge_type", 47, "Чистка", "Purge")]:
    for j, (k, n) in enumerate(lst):
        x = EX0 + (j % 4) * ((EXW - 18) // 4 + EGAP); y = EY0 + 12 + (_r + j // 4) * 36
        eb("rt_" + k, n, _RIGHTS_EN.get(k, n), x, y, (EXW - 18) // 4, 32, pot=EDP(7), allow=need_perm("species") + "\n" + N_TC(),
           effect=act("species", "dtp_sp_load = yes\n" + B("if", B("limit", "exists = event_target:dtp_sp"), B("event_target:dtp_sp", "%s = { country = event_target:dtp_t type = %s cooldown = no }" % (eff, k))), code),
           sprite="GFX_dtp_btn_danger" if code == 47 else "GFX_dtp_btn",
           tt=("%s выбранного вида (выше) в державе A: «%s»." % (nm_ru, n), "%s of the selected species (above) in empire A: '%s'." % (nm_en, _RIGHTS_EN.get(k, n))))
    _r += (len(lst) + 3) // 4
_PR = _ed.portraits(VC)
CLS = [("MAM", "Млекопитающие", "Mammalian"), ("REP", "Рептилоиды", "Reptilian"), ("AVI", "Птицеподобные", "Avian"), ("ART", "Членистоногие", "Arthropoid"),
       ("MOL", "Моллюски", "Molluscoid"), ("FUN", "Грибовидные", "Fungoid"), ("PLANT", "Растениеподобные", "Plantoid"), ("LITHOID", "Литоиды", "Lithoid"),
       ("NECROID", "Некроиды", "Necroid"), ("AQUATIC", "Водные", "Aquatic"), ("TOX", "Токсоиды", "Toxoid"), ("HUM", "Люди", "Human"), ("INF", "Инферналы", "Infernal"),
       ("ROBOT", "Роботы", "Robot"), ("MACHINE", "Машины", "Machine")]
CLS = [c for c in CLS if _PR.get(c[0])]

# ================================================================ 8. ОБЛИК И НАЗВАНИЕ
_SHIP, _OTHER = _ed.graphical_cultures(VC)
GC_NAMES = {"mammalian_01": ("Млекопитающие", "Mammalian"), "reptilian_01": ("Рептилоиды", "Reptilian"), "avian_01": ("Птицеподобные", "Avian"),
            "arthropoid_01": ("Членистоногие", "Arthropoid"), "molluscoid_01": ("Моллюски", "Molluscoid"), "fungoid_01": ("Грибовидные", "Fungoid"),
            "plantoid_01": ("Растениеподобные", "Plantoid"), "humanoid_01": ("Люди", "Humanoid"), "lithoid_01": ("Литоиды", "Lithoid"), "necroid_01": ("Некроиды", "Necroid"),
            "aquatic_01": ("Водные", "Aquatic"), "toxoid_01": ("Токсоиды", "Toxoid"), "subterranean_01": ("Подземные", "Subterranean"), "solarpunk_01": ("Соларпанк", "Solarpunk"),
            "cybernetics_01": ("Кибернетика", "Cybernetic"), "synthetics_01": ("Синтетики", "Synthetic"), "biogenesis_01": ("Биокорабли", "Bio-ships"),
            "biogenesis_02": ("Биокорабли 2", "Bio-ships 2"), "wilderness_01": ("Дикая природа", "Wilderness"), "infernal_01": ("Инферналы", "Infernal"),
            "psionic_01": ("Псионики", "Psionic"), "mindwarden_01": ("Хранители разума", "Mindwarden"), "caravaneer_01": ("Караванщики", "Caravaneer"), "slaver_01": ("Работорговцы", "Slaver")}
head(8, "§YОБЛИК КОРАБЛЕЙ§!  §gтекущий — в рамке§!", "§YSHIP STYLE§!  §gthe current one has a frame§!")
_r = 0
for j, g in enumerate(_SHIP):
    x = EX0 + (j % 6) * ((EXW - 30) // 6 + EGAP); y = EY0 + (_r + j // 6) * 36
    ru, en = GC_NAMES.get(g, (g, g))
    TRG.append(B("dtp_has_gc_%s" % g, "graphical_culture = %s" % g))
    eb("gc_%s_on" % g, ru, en, x, y, (EXW - 30) // 6, 32, pot=EDP(8, extra="dtp_tcx = { T = dtp_has_gc_%s }" % g), sprite="GFX_dtp_btn_on", tt=("Текущий облик кораблей A: «%s»." % ru, "A's current ship style: '%s'." % en))
    eb("gc_" + g, ru, en, x, y, (EXW - 30) // 6, 32, pot=EDP(8, extra="NOT = { dtp_tcx = { T = dtp_has_gc_%s } }" % g), allow=need_perm("state") + "\n" + N_TC(),
       effect=act("state", B("event_target:dtp_t", "set_graphical_culture = %s" % g), 66), tt=("Облик кораблей и станций державы A: «%s»." % ru, "Ship and starbase style for empire A: '%s'." % en))
_r += (len(_SHIP) + 5) // 6
elab("cg_h", "§YОБЛИК ГОРОДОВ§!", "§YCITY STYLE§!", EX0, EY0 + _r * 36 + 4, EXW, pot=EDP(8), h=28); _r += 1
for j, g in enumerate(_SHIP):
    x = EX0 + (j % 6) * ((EXW - 30) // 6 + EGAP); y = EY0 + (_r + j // 6) * 36
    ru, en = GC_NAMES.get(g, (g, g))
    TRG.append(B("dtp_has_cg_%s" % g, "city_graphical_culture = %s" % g))
    eb("cg_%s_on" % g, ru, en, x, y, (EXW - 30) // 6, 32, pot=EDP(8, extra="dtp_tcx = { T = dtp_has_cg_%s }" % g), sprite="GFX_dtp_btn_on", tt=("Текущий облик городов A: «%s»." % ru, "A's current city style: '%s'." % en))
    eb("cg_" + g, ru, en, x, y, (EXW - 30) // 6, 32, pot=EDP(8, extra="NOT = { dtp_tcx = { T = dtp_has_cg_%s } }" % g), allow=need_perm("state") + "\n" + N_TC(),
       effect=act("state", B("event_target:dtp_t", "set_city_graphical_culture = %s" % g), 66), tt=("Облик городов на планетах державы A: «%s»." % ru, "City look on empire A's planets: '%s'." % en))
_r += (len(_SHIP) + 5) // 6
elab("nm_h", "§YФЛАГ И НАЗВАНИЕ§!  §gслучайно или из готовых названий§!", "§YFLAG & NAME§!  §grandom or from preset names§!", EX0, EY0 + _r * 36 + 4, EXW, pot=EDP(8), h=28); _r += 1
_w4 = (EXW - 18) // 4
ALLNAMES = [("Галактическая Империя", "Galactic Empire"), ("Объединённая Республика", "United Republic"), ("Звёздный Союз", "Stellar Union"),
            ("Свободная Конфедерация", "Free Confederacy"), ("Священный Доминион", "Holy Dominion"), ("Торговая Лига", "Trade League"),
            ("Вечная Гегемония", "Eternal Hegemony"), ("Содружество Миров", "Commonwealth of Worlds"), ("Звёздная Директория", "Stellar Directorate"),
            ("Великий Альянс", "Grand Alliance"), ("Солнечный Протекторат", "Solar Protectorate"), ("Народный Коллектив", "People's Collective"),
            ("Технократический Совет", "Technocratic Council"), ("Небесная Династия", "Celestial Dynasty"), ("Свободные Колонии", "Free Colonies"),
            ("Железный Легион", "Iron Legion"), ("Пограничный Синдикат", "Frontier Syndicate"), ("Орден Звёзд", "Order of the Stars"),
            ("Ассамблея Миров", "Assembly of Worlds"), ("Новая Империя", "New Empire"), ("Объединённые Системы", "United Systems"),
            ("Королевство Глубин", "Kingdom of the Deep"), ("Сияющая Гегемония", "Radiant Hegemony"), ("Вольная Федерация", "Free Federation"),
            ("Межзвёздная Корпорация", "Interstellar Corporation"), ("Верховный Конклав", "High Conclave"), ("Звёздная Республика", "Star Republic"),
            ("Космический Халифат", "Cosmic Caliphate"), ("Северная Конфедерация", "Northern Confederacy"), ("Тёмный Доминион", "Dark Dominion"),
            ("Галактический Консорциум", "Galactic Consortium"), ("Империя Рассвета", "Dawn Empire")]
for _j, (_ru, _en) in enumerate(ALLNAMES):
    loc("dtp_nm_%d" % (_j + 1), _ru); tren(_ru, _en)
for j, (k, ru, en, eff, tt_ru, tt_en, sp) in enumerate([
        ("flag", "Случайный флаг", "Random flag", "change_country_flag = random", "Новый случайный флаг державы A.", "A new random flag for empire A.", False),
        ("name", "Случайное название", "Random name", "RANDOM_NAME", "Новое случайное название державы A (из 32 готовых названий).", "A new random name for empire A (from 32 preset names).", False),
        ("spname", "Случайное имя вида", "Random species name", "rename_species = { name = random }", "Новое случайное название основного вида A.", "A new random name for A's main species.", True)]):
    x = EX0 + j * (_w4 + EGAP); y = EY0 + _r * 36
    if eff == "RANDOM_NAME":       # set_name = random у игры не работает для многих форм правления (error.log: «Failed to find name format»)
        eff = B("random_list", *[B("10", "set_name = dtp_nm_%d" % (n + 1)) for n in range(len(ALLNAMES))])
    body = (SPX + "\n" + B("event_target:dtp_sp", eff)) if sp else B("event_target:dtp_t", eff)
    eb(k, ru, en, x, y, _w4, 32, pot=EDP(8), allow=need_perm("species" if sp else "state") + "\n" + N_TC(), effect=act("species" if sp else "state", body, 66),
       sprite="GFX_dtp_btn_go", tt=(tt_ru, tt_en))
_r += 1
PRESETS = ALLNAMES[:8]
for j, (ru, en) in enumerate(PRESETS):
    lk = "dtp_nm_%d" % (j + 1)
    x = EX0 + (j % 4) * (_w4 + EGAP); y = EY0 + (_r + j // 4) * 36
    eb("nm%d" % (j + 1), ru, en, x, y, _w4, 32, pot=EDP(8), allow=need_perm("state") + "\n" + N_TC(), effect=act("state", B("event_target:dtp_t", "set_name = %s" % lk), 66),
       tt=("Назвать державу A: «%s»." % ru, "Rename empire A to '%s'." % en))

# ================================================================ 9. МОДИФИКАТОРЫ: подразделы «Свои» / «Из игры», справа калькулятор силы и срока
LW9 = EXW - 300                                  # ширина левой части
RX9, RW9 = EX0 + LW9 + 14, EXW - LW9 - 14        # калькулятор
_c3 = (LW9 - 12) // 3
for i, (c, ru, en) in enumerate([(1, "Свои модификаторы", "Toolpack modifiers"), (2, "Модификаторы игры", "Game modifiers")]):
    x = EX0 + i * ((LW9 - 6) // 2 + 6)
    eb("t9_c%d_on" % c, ru, en, x, EY0 - 42, (LW9 - 6) // 2, 34, pot=EDP(9, c), sprite="GFX_dtp_tab_on", tt=("Открыт подраздел «%s»." % ru, "Sub-section '%s' is open." % en))
    eb("t9_c%d" % c, ru, en, x, EY0 - 42, (LW9 - 6) // 2, 34, pot=EDP(9, extra=B("from", "NOT = { %s }" % chk("dtp_edcat", c))),
       effect=B("from", setv("dtp_edcat", c)), sprite="GFX_dtp_tab", tt=("Открыть подраздел «%s»." % ru, "Open the '%s' sub-section." % en))
# свои модификаторы: прежние 12 + новые (только в редакторе; значения — «за единицу силы»)
UM_EXTRA = [("energy", "Энергия", "Energy", "country_energy_produces_mult", 0.01, "%"), ("minerals", "Минералы", "Minerals", "country_minerals_produces_mult", 0.01, "%"),
            ("food", "Пища", "Food", "country_food_produces_mult", 0.01, "%"), ("alloys", "Сплавы", "Alloys", "country_alloys_produces_mult", 0.01, "%"),
            ("cg", "Товары", "Consumer goods", "country_consumer_goods_produces_mult", 0.01, "%"), ("unity", "Единство", "Unity", "country_unity_produces_mult", 0.01, "%"),
            ("phys", "Физика", "Physics", "country_physics_research_produces_mult", 0.01, "%"), ("soc", "Социология", "Society", "country_society_research_produces_mult", 0.01, "%"),
            ("eng", "Инженерия", "Engineering", "country_engineering_research_produces_mult", 0.01, "%"), ("speed", "Скорость кораблей", "Ship speed", "ship_speed_mult", 0.01, "%"),
            ("shield", "Щиты кораблей", "Ship shields", "ship_shield_mult", 0.01, "%"), ("armor", "Броня кораблей", "Ship armor", "ship_armor_mult", 0.01, "%"),
            ("range", "Дальность оружия", "Weapon range", "ship_weapon_range_mult", 0.01, "%"), ("upkeep", "Содержание флота", "Fleet upkeep", "ships_upkeep_mult", 0.01, "%"),
            ("army", "Урон армий", "Army damage", "army_damage_mult", 0.01, "%"), ("diplo", "Дипл. вес", "Diplomatic weight", "diplo_weight_mult", 0.01, "%"),
            ("wex", "Усталость от войны", "War exhaustion", "country_war_exhaustion_mult", 0.01, "%"), ("yard", "Скорость верфей", "Shipyard speed", "starbase_shipyard_build_speed_mult", 0.01, "%"),
            ("mega", "Стройка мегасооруж.", "Megastructure speed", "megastructure_build_speed_mult", 0.01, "%"), ("sbcap", "Лимит станций", "Starbase capacity", "country_starbase_capacity_add", 1, "ед."),
            ("leaders", "Лимит лидеров", "Leader capacity", "country_leader_cap_add", 1, "ед."), ("envoys", "Посланники", "Envoys", "envoys_add", 1, "ед."),
            ("crime", "Преступность", "Crime", "planet_crime_add", 1, "ед."), ("housing", "Жильё", "Housing", "planet_housing_add", 1, "ед.")]
_UMEN = {"research": "Research speed", "output": "Job output", "stab": "Stability", "naval": "Naval capacity", "fire": "Fleet fire rate", "hull": "Ship hull",
         "growth": "Pop growth", "build": "Build speed", "happy": "Approval", "amen": "Amenities", "habit": "Habitability", "storage": "Storage limit"}
_UMALL = [(k, UMSHORT.get(n, n), _UMEN.get(k, n), mk, unit, u) for k, n, mk, unit, u in UMODS["c"]]
for k, ru, en, mk, unit, u in UM_EXTRA:
    key = "dtp_uc_%s" % k
    UMOD_STATIC.append("%s = {\n\t%s = %s\n}" % (key, mk, unit))
    loc(key, "Toolpack: " + ru); tren("Toolpack: " + ru, "Toolpack: " + en)
    loc(key + "_desc", "Модификатор выдан через Debug Toolpack.")
    _UMALL.append((k, ru, en, mk, unit, u))
elab("um_h", "§YСИЛА 1 = 1%§!  §gу «%» · у «ед.» — 1 единица · минус — штраф · ещё раз — снять§!",
     "§YSTRENGTH 1 = 1%§!  §gfor '%' · for 'units' — 1 unit · minus is a penalty · click again to remove§!", EX0, EY0 - 4, LW9, pot=EDP(9, 1), h=26)
for i, (k, ru, en, mk, unit, u) in enumerate(_UMALL):
    key = "dtp_uc_%s" % k
    x = EX0 + (i % 3) * (_c3 + EGAP); y = EY0 + 26 + (i // 3) * 34
    hasT = "dtp_c_hasmod = { M = %s }" % key
    tag = " %" if u == "%" else " ед."; tag_en = " %" if u == "%" else " u."
    add = "\n".join([B("event_target:dtp_t", setv("dtp_tv", "from.dtp_val"), setv("dtp_ty", "from.dtp_years"), "remove_modifier = %s" % key),
                     B("if", B("limit", B("from", chk("dtp_years", 0, "<="))), B("event_target:dtp_t", "add_modifier = { modifier = %s days = -1 multiplier = dtp_tv }" % key)),
                     B("else", B("event_target:dtp_t", "add_modifier = { modifier = %s days = 360 time_multiplier = dtp_ty multiplier = dtp_tv }" % key))])
    expl = ("сила 10 = +10%%, сила −25 = −25%%" if u == "%" else "сила 10 = +10, сила −5 = −5")
    expl_en = ("strength 10 = +10%%, strength −25 = −25%%" if u == "%" else "strength 10 = +10, strength −5 = −5")
    eb("um_%s_on" % k, "● " + ru + tag, "● " + en + tag_en, x, y, _c3, 30, pot=EDP(9, 1, extra=hasT), allow=need_perm("res") + "\n" + N_TC(),
       effect=act("res", B("event_target:dtp_t", "remove_modifier = %s" % key), 6), sprite="GFX_dtp_btn_on",
       tt=("Действует у A. Нажмите, чтобы СНЯТЬ «%s»." % ru, "Active on A. Click to REMOVE '%s'." % en))
    eb("um_" + k, ru + tag, en + tag_en, x, y, _c3, 30, pot=EDP(9, 1, extra="NOT = { %s }" % hasT), allow=need_perm("res") + "\n" + N_TC(),
       effect=act("res", add, 5), tt=("«%s» для державы A: сила из калькулятора справа (%s). Отрицательная сила — штраф. Срок — там же." % (ru, expl.replace("%%", "%")),
                                      "'%s' for empire A: strength from the calculator on the right (%s). Negative strength is a penalty. Duration is set there too." % (en, expl_en.replace("%%", "%"))))
# модификаторы игры: прежние 12 + ещё 12 (у всех свои значки игры)
VM_EXTRA = [("c", "§YДЕРЖАВА A — БОНУСЫ ИГРЫ§!", "GFX_dtp_btn_go", [("sacrifice_bounty_mod", "Щедрость", "Bounty"), ("sacrifice_togetherness_mod", "Единение", "Togetherness"),
              ("food_abundance", "Изобилие пищи", "Food abundance"), ("rock_abundance", "Изобилие руды", "Ore abundance"), ("support_the_revolution", "Поддержка революции", "Revolution support"),
              ("singularity_situation_06", "Научный подъём", "Science surge")]),
            ("c", "§YДЕРЖАВА A — ШТРАФЫ ИГРЫ§!", "GFX_dtp_btn_danger", [("country_defaulted", "Дефолт", "Defaulted"), ("food_crisis", "Голод", "Food crisis"),
              ("rock_crisis", "Нехватка руды", "Ore crisis"), ("cost_of_freedom_11", "Цена свободы", "Cost of freedom"), ("nwo_situation_03", "Новый порядок", "New order"),
              ("art_is_dead", "Искусство мертво", "Art is dead")])]
_VEN = {"fleet_maneuvers": "Fleet maneuvers", "new_resonance_music_art": "New Resonance", "luminous_blades": "Luminous Blades", "gal_custodian": "Custodian",
        "manifesti_reflections_mod": "Manifesti", "hero_redivivus": "Hero Redivivus", "humiliated": "Humiliated", "maneuvers_no_protest": "Maneuver protests",
        "shroud_neg_influence": "Shroud: influence", "shroud_neg_unity": "Shroud: unity", "whisperers_psychosis": "Whisperers' psychosis", "left_galactic_community": "Outside the Community"}
_VGRP = {}
for c, hd, spr, lst in VMODS:
    if c == "c": _VGRP.setdefault("БОНУСЫ" in hd, []).extend([(k, n, _VEN.get(k, n)) for k, n in lst])
for c, hd, spr, lst in VM_EXTRA:
    _VGRP.setdefault("БОНУСЫ" in hd, []).extend(lst)
_r = EY0 - 4
for _bon in (True, False):
    elab("vm_h%d" % int(_bon), "§YМОДИФИКАТОРЫ ИГРЫ: %s§!  §gсила не нужна — только срок§!" % ("БОНУСЫ" if _bon else "ШТРАФЫ"),
         "§YGAME MODIFIERS: %s§!  §gno strength — duration only§!" % ("BONUSES" if _bon else "PENALTIES"), EX0, _r, LW9, pot=EDP(9, 2), h=26)
    _r += 30
    spr = "GFX_dtp_btn_go" if _bon else "GFX_dtp_btn_danger"
    items = [x for x in _VGRP[_bon] if x[0] in VSRC]
    for i, (key, n, n_en) in enumerate(items):
        n = {"Манифест: размышления": "Манифест", "Протесты против учений": "Протесты учений"}.get(n, n)
        x = EX0 + (i % 3) * (_c3 + EGAP); y = _r + (i // 3) * 34
        hasT = "dtp_c_hasmod = { M = %s }" % key
        eb("vm_%s_on" % key, "● " + n, "● " + n_en, x, y, _c3, 30, pot=EDP(9, 2, extra=hasT), allow=need_perm("res") + "\n" + N_TC(),
           effect=act("res", B("event_target:dtp_t", "remove_modifier = %s" % key), 6), sprite="GFX_dtp_btn_on",
           tt=("Действует: %s. Нажмите, чтобы СНЯТЬ." % vdesc(key), "Active (%s). Click to REMOVE." % key))
        eb("vm_" + key, n, n_en, x, y, _c3, 30, pot=EDP(9, 2, extra="NOT = { %s }" % hasT), allow=need_perm("res") + "\n" + N_TC(),
           effect=act("res", VAPPLY("dtp_t", key), 5), sprite=spr, tt=("Модификатор игры «%s» (%s): %s. Срок — калькулятор справа." % (n, key, vdesc(key)), "Game modifier '%s' (%s). Duration — calculator on the right." % (n_en, key)))
    _r += ((len(items) + 2) // 3) * 34 + 8
# ---- калькулятор (как панель «Число» в главном окне: то же число dtp_in, сила = число)
P9 = EDP(9)
lab("ed_kcard", "", RX9, EY0 - 42, RW9, h=EH - 104 - EY0 + 40, potential=B("from", EDOPEN, chk("dtp_edtab", 9)), where="editor"); GUI[-1]["sprite"] = META[-1]["sprite"] = "GFX_dtp_card"
elab("k_h", "§YСИЛА§!  §gсейчас: §Y[From.dtp_val]§!§!", "§YSTRENGTH§!  §gnow: §Y[From.dtp_val]§!§!", RX9 + 12, EY0 - 36, RW9 - 24, pot=P9, h=22)
eb("k_in", "  §Y[From.dtp_in]§!", "  §Y[From.dtp_in]§!", RX9 + 10, EY0 - 10, RW9 - 20, 40, pot=P9, sprite="GFX_dtp_field", label=True, font="malgun_goth_24")
_KW = (RW9 - 24 - 12) // 3
def _kx(c): return RX9 + 12 + c * (_KW + 6)
for i, dg in enumerate([7, 8, 9, 4, 5, 6, 1, 2, 3, 0]):
    digit = "\n".join([B("if", B("limit", KNEG), "multiply_variable = { which = dtp_in value = 10 }", "change_variable = { which = dtp_in value = %d }" % (-dg)),
                       B("else", "multiply_variable = { which = dtp_in value = 10 }", "change_variable = { which = dtp_in value = %d }" % dg)])
    c, r = (i % 3, i // 3) if dg != 0 else (1, 3)
    eb("k%d" % dg, str(dg), str(dg), _kx(c), EY0 + 38 + r * 36, _KW, 32, pot=P9, effect=B("from", digit, CAP, SYNC), sprite="GFX_dtp_btn_key",
       tt=("Цифра %d: число = число × 10 + %d. Сила модификаторов = это число." % (dg, dg), "Digit %d: number = number × 10 + %d. Modifier strength = this number." % (dg, dg)))
eb("k_neg", "−", "−", _kx(0), EY0 + 38 + 3 * 36, _KW, 32, pot=P9, effect=B("from", KMINUS, SYNC), sprite="GFX_dtp_btn_key",
   tt=(KMINUS_TT, ED_EN[KMINUS_TT]))
eb("k_bs", "←", "←", _kx(2), EY0 + 38 + 3 * 36, _KW, 32, pot=P9, effect=B("from", "divide_variable = { which = dtp_in value = 10 }",
   B("if", B("limit", chk("dtp_in", 0, "<")), "ceiling_variable = dtp_in"), B("else", "floor_variable = dtp_in"), SYNC), sprite="GFX_dtp_btn_key",
   tt=("Стереть последнюю цифру.", "Erase the last digit."))
eb("k_c", "Очистить", "Clear", _kx(0), EY0 + 38 + 4 * 36, RW9 - 24, 32, pot=P9, effect=B("from", setv("dtp_in", 0), "remove_country_flag = dtp_kneg", SYNC), sprite="GFX_dtp_btn_danger",
   tt=("Число = 0.", "Number = 0."))
_qy = EY0 + 38 + 5 * 36 + 4
_qw = (RW9 - 24 - 3 * 6) // 4
for j, v in enumerate([-50, -10, 25, 100]):
    eb("kq%d" % j, ("%+d" % v).replace("-", "−"), "%+d" % v, RX9 + 12 + j * (_qw + 6), _qy, _qw, 30, pot=P9,
       effect=B("from", setv("dtp_in", v), "set_country_flag = dtp_kneg" if v < 0 else "remove_country_flag = dtp_kneg", SYNC),
       sprite="GFX_dtp_btn_danger" if v < 0 else "GFX_dtp_btn_go", tt=("Число = %d." % v, "Number = %d." % v))
elab("k_y", "§YСРОК§!  §g[From.dtp_years] лет (0 — навсегда)§!", "§YDURATION§!  §g[From.dtp_years] years (0 — forever)§!", RX9 + 12, _qy + 40, RW9 - 24, pot=P9, h=22)
for j, (v, ru, en) in enumerate([(1, "1 год", "1 yr"), (5, "5 лет", "5 yrs"), (10, "10 лет", "10 yrs"), (0, "Всегда", "Forever")]):
    x = RX9 + 12 + j * (_qw + 6)
    eb("my%d" % j, ru, en, x, _qy + 64, _qw, 30, pot=EDP(9, extra=B("from", "NOT = { %s }" % chk("dtp_years", v))), effect=B("from", setv("dtp_years", v)),
       tt=("Срок модификатора: %s." % ru, "Modifier duration: %s." % en))
    eb("my%d_on" % j, ru, en, x, _qy + 64, _qw, 30, pot=EDP(9, extra=B("from", chk("dtp_years", v))), sprite="GFX_dtp_btn_on", tt=("Выбран срок: %s." % ru, "Selected duration: %s." % en))
eb("k_yr", "Срок = число (лет)", "Duration = number (years)", RX9 + 12, _qy + 100, RW9 - 24, 30, pot=P9,
   effect=B("from", setv("dtp_years", "dtp_in"), B("if", B("limit", chk("dtp_years", 0, "<")), setv("dtp_years", 0))), sprite="GFX_dtp_btn_go",
   tt=("Сделать число сроком модификаторов в годах.", "Use the number as the modifier duration in years."))

# ================================================================ 10. ПОРТРЕТ ВИДА: класс → все портреты этого класса
head(10, "§YКЛАСС ВИДА§!  §gвыберите класс — ниже появятся все его портреты; текущий портрет и его класс — в зелёной рамке§!",
     "§YSPECIES CLASS§!  §gpick a class — all its portraits appear below; the current portrait and its class have a green frame§!")
_cw5 = (EXW - 24) // 5
for j, (c, ru, en) in enumerate(CLS):
    x = EX0 + (j % 5) * (_cw5 + EGAP); y = EY0 + (j // 5) * 36
    TRG.append(B("dtp_pcls_%s" % c, B("OR", *["species_portrait = %s" % p_ for p_ in _PR[c]])))
    eb("cls_%s_on" % c, ru, en, x, y, _cw5, 32, pot=EDP(10, j + 1), sprite="GFX_dtp_btn_on", tt=("Открыты портреты класса «%s»." % ru, "Showing '%s' portraits." % en))
    eb("cls_" + c, ru, en, x, y, _cw5, 32, pot=EDP(10, extra=B("from", "NOT = { %s }" % chk("dtp_edcat", j + 1))),
       effect=B("from", setv("dtp_edcat", j + 1)), tt=("Показать все портреты класса «%s»." % ru, "Show all '%s' portraits." % en))
    # рамка лежит поверх кнопки класса — щелчок по ней делает то же самое (11.2.5: раньше рамка «съедала» щелчок)
    eb("cls_%s_h" % c, "", "", x, y, _cw5, 32, pot=EDP(10, extra="dtp_spx = { T = dtp_pcls_%s }" % c), effect=B("from", setv("dtp_edcat", j + 1)),
       sprite="GFX_dtp_sg", transp=True, tt=("Текущий портрет вида — из класса «%s». Нажмите, чтобы показать все портреты этого класса." % ru,
                                               "The species' current portrait is from the '%s' class. Click to show all portraits of this class." % en))
elab("pt_h2", "§YПОРТРЕТЫ КЛАССА§!  §gнажмите — портрет сменится у всего вида; виден в окнах игры (вид, правительство, дипломатия)§!",
     "§YCLASS PORTRAITS§!  §gclick — the whole species gets this portrait; it shows in the game windows (species, government, diplomacy)§!", EX0, EY0 + 3 * 36 + 6, EXW, pot=EDP(10), h=28)
_pw6 = (EXW - 5 * EGAP) // 6
_PTSEEN = set()
for j, (c, ru, en) in enumerate(CLS):
    for i, p_ in enumerate(_PR[c]):
        x = EX0 + (i % 6) * (_pw6 + EGAP); y = EY0 + 3 * 36 + 40 + (i // 6) * (ECH + EGAP)
        if p_ not in _PTSEEN: _PTSEEN.add(p_); TRG.append(B("dtp_pt_%s" % p_, "species_portrait = %s" % p_))
        card("pt_%s_%d" % (c, i), "%s %d" % (ru, i + 1), "%s %d" % (en, i + 1), x, y, _pw6, EDP(10, j + 1), None, "dtp_spx = { T = dtp_pt_%s }" % p_, None,
             act("species", SPX + "\n" + B("event_target:dtp_sp", "change_species_portrait = %s" % p_), 67), "species",
             "Портрет «%s» (%s, №%d). Нажмите, чтобы поставить его основному виду A." % (p_, ru, i + 1), "Portrait '%s' (%s, #%d). Click to give it to A's main species." % (p_, en, i + 1))

# ---- кнопка «Открыть редактор» (главная панель) — эффект общий
ED_OPEN_EFF = INIT + "\n" + B("from", "set_country_flag = dtp_ed_open", "remove_country_flag = dtp_open",
                               B("if", B("limit", "NOT = { is_variable_set = dtp_edtab }"), setv("dtp_edtab", 1), setv("dtp_edcat", 1), setv("dtp_edpg", 1)))
print("редактор: элементов %d, условий «разрешено игрой» %d" % (sum(1 for g in GUI if g["where"] == "editor"), len(_OKN)))

# ================================================================ ЗНАЧКИ ИГРЫ на кнопках редактора (вкладки, подразделы, права, облик, модификаторы)
_SMI = {}
for _f in sorted(os.listdir(os.path.join(VC, "static_modifiers"))):
    _s = re.sub(r"#.*", "", open(os.path.join(VC, "static_modifiers", _f), encoding="utf-8-sig").read())
    for _m in re.finditer(r"^(\w+)\s*=\s*\{", _s, re.M):
        _i, _d = _m.end(), 1
        while _d and _i < len(_s): _d += {"{": 1, "}": -1}.get(_s[_i], 0); _i += 1
        _ic = re.search(r'icon\s*=\s*"([^"]+\.dds)"', _s[_m.end():_i])
        if _ic: _SMI[_m.group(1)] = _ic.group(1)
_GI = "gfx/interface/icons/"
_TRI = {g: next((x["icon"] for x in _TRS if x["grp"] == g and x["icon"].startswith(_GI + "traits/")), None) for g in ("bio", "robot", "ascend", "hab")}
_TRI["bio"] = _GI + "traits/trait_intelligent.dds"
NAVTEX = {1: _GI + "governments/authorities/auth_imperial.dds", 2: _GI + "governments/civics/civic_technocracy.dds", 3: _GI + "resources/unity.dds",
          4: _GI + "ascension_perks/slot_available.dds", 5: _GI + "resources/influence.dds", 6: _GI + "traits/trait_intelligent.dds",
          7: _GI + "species_right_living_standards.dds", 10: _GI + "species_right_citizenship.dds", 8: _GI + "resources/alloys.dds", 9: _GI + "resources/society_research.dds"}
CIVTEX = {1: _GI + "governments/authorities/auth_democratic.dds", 2: _GI + "governments/authorities/auth_corporate.dds", 3: _GI + "governments/authorities/auth_hive_mind.dds",
          4: _GI + "governments/authorities/auth_machine_intelligence.dds", 5: _GI + "resources/minor_artifacts.dds"}
TRTEX = {1: _TRI["bio"], 2: _TRI["robot"], 3: _TRI["ascend"], 4: _TRI["hab"]}
RIGHTTEX = {"citizenship": "species_right_citizenship", "living_standard": "species_right_living_standards", "military_service": "species_right_military_service",
            "slavery": "species_right_slavery_type", "purge": "species_right_purge_type"}
UMTEX = {"research": "physics_research", "output": "minerals", "stab": "unity", "naval": "alloys", "fire": "alloys", "hull": "alloys", "growth": "food",
         "build": "minerals", "happy": "unity", "amen": "consumer_goods", "habit": "food", "storage": "energy"}
UMTEX.update({"energy": "energy", "minerals": "minerals", "food": "food", "alloys": "alloys", "cg": "consumer_goods", "unity": "unity", "phys": "physics_research",
              "soc": "society_research", "eng": "engineering_research", "speed": "alloys", "shield": "alloys", "armor": "alloys", "range": "alloys", "upkeep": "energy",
              "army": "alloys", "diplo": "diplomatic_weight", "wex": "influence", "yard": "alloys", "mega": "minerals", "sbcap": "influence", "leaders": "unity",
              "envoys": "influence", "crime": "trade_value", "housing": "consumer_goods"})
def _etex(nm):
    m = re.match(r"tab(\d+)(_on)?$", nm)
    if m: return NAVTEX.get(int(m.group(1)))
    m = re.match(r"t2_c(\d)(_on)?$", nm)
    if m: return CIVTEX.get(int(m.group(1)))
    m = re.match(r"t6_c(\d)(_on)?$", nm)
    if m: return TRTEX.get(int(m.group(1)))
    m = re.match(r"rt_(citizenship|living_standard|military_service|slavery|purge)_", nm)
    if m: return _GI + RIGHTTEX[m.group(1)] + ".dds"
    if re.match(r"gc_", nm): return _GI + "resources/alloys.dds"
    if re.match(r"cg_", nm): return _GI + "resources/consumer_goods.dds"
    if nm in ("flag", "name") or re.match(r"nm\d$", nm): return _GI + "resources/influence.dds"
    if nm in ("spname", "pt_prev", "pt_next") or re.match(r"cls_", nm): return _GI + "species_right_citizenship.dds"
    m = re.match(r"um_(\w+?)(_on)?$", nm)
    if m and m.group(1) in UMTEX: return _GI + "resources/%s.dds" % UMTEX[m.group(1)]
    m = re.match(r"vm_(\w+?)(_on)?$", nm)
    if m: return _SMI.get(m.group(1))
    return None
_n_ic = 0
for _g, _m in list(zip(GUI, META)):
    if _g["where"] != "editor" or _g["label"] or not _g["key"].startswith("dtp_b_ed_"): continue
    _tex = _etex(_g["key"][9:])
    if not _tex: continue
    _pad = "            "
    _ru = L[_g["key"]]; _en = ED_EN.get(_ru, _ru)
    L[_g["key"]] = _m["text"] = _pad + _ru.lstrip(" "); ED_EN[_pad + _ru.lstrip(" ")] = _pad + _en.lstrip(" ")
    _g["left"] = _m["left"] = True
    _sz = 22 if _g["h"] < 36 else 26
    _dx = 6
    if re.match(r"dtp_b_ed_tab\d+", _g["key"]): _sz, _dx = 20, 9             # навигация: значок игры внутри гекса
    GUI.append(dict(_g, key=_g["key"] + "_ic", x=_g["x"] + _dx, y=_g["y"] + (_g["h"] - _sz) // 2, w=_sz, h=_sz, sprite=gspr(_tex), label=True, eff=_g["key"], left=False, transp=True, tt=None))
    META.append(dict(_m, key=_g["key"] + "_ic", x=_g["x"] + _dx, y=_g["y"] + (_g["h"] - _sz) // 2, w=_sz, h=_sz, sprite=gspr(_tex), label=True, text=""))
    L[_g["key"] + "_ic"] = ""; _n_ic += 1
for _t in NAVTEX:                                                     # значок раздела в гексе баннера
    lab("ed_ban%d_ic" % _t, "", EX0 + 13, 62 + 9, 22, h=22, potential=B("from", EDOPEN, chk("dtp_edtab", _t)), where="editor")
    GUI[-1]["sprite"] = META[-1]["sprite"] = gspr(NAVTEX[_t]); GUI[-1]["transp"] = True
print("редактор: значков игры на кнопках %d" % _n_ic)
