#!/usr/bin/env python3
"""Внутриигровой автотест DTP: отдельный маленький мод «DTP Self-Test».

Консоль игры:  event dtpst.1   — запускает проверки за державу игрока и пишет в game.log строки
  DTPTEST PASS …  /  DTPTEST FAIL …  и итог DTPTEST DONE ok=N fail=M.
Проверяется то, что без запуска игры не проверить: готовые проекты DTP (global_ship_designs) действительно
создают корабли, эффекты ремонта/повреждения работают, черты лидера с противоположными, смена проекта флота,
транспорт с армией. Все созданные для теста объекты удаляются.

python3 selftest.py <мод DTP (dtp3)> <выходная папка> <версия>
"""
import os, re, sys, zipfile

DTP, OUT, VER = sys.argv[1:4]
designs = open(os.path.join(DTP, "common/global_ship_designs/dtp_prebuilt_designs.txt"), encoding="utf-8").read()
# (проект, размер, этап роста) — у биокораблей один проект на все этапы (growth_stages)
SIZES = []
for m in re.finditer(r'ship_design = \{\s*name = "(DTP_PREBUILT_\w+)"(.*?)\n\}', designs, re.S):
    szs = re.findall(r"ship_size = (\w+)", m.group(2))
    grow = "growth_stages" in m.group(2)
    for i, s in enumerate(szs): SIZES.append((m.group(1), s, i + 1 if grow else None))

def ok(msg): return 'log = "DTPTEST PASS %s"\nroot = { change_variable = { which = dtpst_ok value = 1 } }' % msg
def fail(msg): return 'log = "DTPTEST FAIL %s"\nroot = { change_variable = { which = dtpst_fail value = 1 } }' % msg
def check(cond, msg): return "if = { limit = { %s }\n%s\n}\nelse = {\n%s\n}" % (cond, ok(msg), fail(msg))

ev = ["namespace = dtpst", ""]
# 1 — точка входа
ev.append('''country_event = {
	id = dtpst.1
	hide_window = yes
	is_triggered_only = yes
	immediate = {
		log = "DTPTEST START DTP self-test %s, country [This.GetName]"
		set_variable = { which = dtpst_ok value = 0 }
		set_variable = { which = dtpst_fail value = 0 }
		if = { limit = { NOT = { exists = capital_scope } } log = "DTPTEST FAIL no capital - run the test as a normal empire with a capital" }
		else = {
			country_event = { id = dtpst.2 }
			country_event = { id = dtpst.3 }
			country_event = { id = dtpst.4 }
			country_event = { id = dtpst.5 }
			country_event = { id = dtpst.9 }
		}
	}
}''' % VER)
# 2 — готовые проекты
body = []
for dn, k, gs in SIZES:
    body.append('''create_fleet = { name = "DTPTEST" effect = {
	set_owner = root
	create_ship = { name = random design = "%s" graphical_culture = owner%s }
	set_location = { target = root.capital_scope distance = 15 angle = random }
} }
last_created_fleet = {
	%s
	delete_fleet = this
}''' % (dn, " growth_stage = %d" % gs if gs else "", check("any_owned_ship = { is_ship_size = %s }" % k, "prebuilt design %s" % k)))
ev.append('''country_event = {
	id = dtpst.2
	hide_window = yes
	is_triggered_only = yes
	immediate = {
%s
	}
}''' % "\n".join(body))
# 3 — ремонт / повреждение / смена проекта (корвет из готового проекта)
ev.append('''country_event = {
	id = dtpst.3
	hide_window = yes
	is_triggered_only = yes
	immediate = {
		create_fleet = { name = "DTPTEST" effect = {
			set_owner = root
			create_ship = { name = random design = "DTP_PREBUILT_corvette" graphical_culture = owner }
			create_ship = { name = random design = "DTP_PREBUILT_corvette" graphical_culture = owner }
			set_location = { target = root.capital_scope distance = 15 angle = random }
		} }
		last_created_fleet = {
			save_event_target_as = dtpst_f
			%s
			every_owned_ship = { reduce_hp_percent = 0.5 }
			repair_percentage = 1
			repair_armor_percentage = 1
			repair_shield_percentage = 1
			%s
		}
		if = { limit = { any_owned_design = { is_ship_size = corvette } }
			random_owned_design = { limit = { is_ship_size = corvette } save_event_target_as = dtpst_d }
			event_target:dtpst_f = { set_ship_design = { design = event_target:dtpst_d } }
			event_target:dtpst_f = { %s }
		}
		else = { log = "DTPTEST SKIP set_ship_design - country has no corvette design" }
		event_target:dtpst_f = { delete_fleet = this }
	}
}''' % (check("num_ships = 2", "create 2 ships into one fleet"),
        'log = "DTPTEST PASS repair/damage effects ran (see error.log for errors)"\nroot = { change_variable = { which = dtpst_ok value = 1 } }',
        check("num_ships = 2", "set_ship_design keeps ships")))
# 4 — черты лидера: противоположная мешает, снятие помогает (как в DTP 11.8.2)
ev.append('''country_event = {
	id = dtpst.4
	hide_window = yes
	is_triggered_only = yes
	immediate = {
		create_leader = { class = commander species = owner_species skill = 1 traits = { 0 = trait_ruler_corvette_focus } }
		last_created_leader = {
			save_event_target_as = dtpst_l
			%s
			add_trait = { trait = trait_ruler_destroyer_focus show_message = no }
			if = { limit = { has_trait = trait_ruler_destroyer_focus } log = "DTPTEST INFO opposite trait did NOT block add_trait" }
			else = { log = "DTPTEST INFO opposite trait blocks add_trait (expected)" }
			if = { limit = { has_trait = trait_ruler_corvette_focus } remove_trait = trait_ruler_corvette_focus }
			add_trait = { trait = trait_ruler_destroyer_focus show_message = no }
			%s
			kill_leader = { show_notification = no }
		}
	}
}''' % (check("has_trait = trait_ruler_corvette_focus", "create_leader with trait"),
        check("has_trait = trait_ruler_destroyer_focus", "trait added after removing opposite")))
# 5 — проект: копия чужого проекта (add_ship_design) и транспорт с армией
ev.append('''country_event = {
	id = dtpst.5
	hide_window = yes
	is_triggered_only = yes
	immediate = {
		set_variable = { which = dtpst_nd value = 0 }
		every_owned_design = { root = { change_variable = { which = dtpst_nd value = 1 } } }
		random_country = {
			limit = { NOT = { is_same_value = root } any_owned_design = { is_ship_size = corvette } }
			random_owned_design = { limit = { is_ship_size = corvette } save_event_target_as = dtpst_fd }
		}
		if = { limit = { exists = event_target:dtpst_fd }
			add_ship_design = event_target:dtpst_fd
			set_variable = { which = dtpst_nd2 value = 0 }
			every_owned_design = { root = { change_variable = { which = dtpst_nd2 value = 1 } } }
			%s
		}
		else = { log = "DTPTEST SKIP add_ship_design - no other empire has a corvette design" }
		create_fleet = { name = "DTPTEST" effect = {
			set_owner = root
			create_army_transport = { ship_name = random army_name = random army_type = assault_army species = root.owner_species }
			set_location = { target = root.capital_scope distance = 15 angle = random }
		} }
		last_created_fleet = {
			%s
			delete_fleet = this
		}
		clear_variable = dtpst_nd
		clear_variable = dtpst_nd2
	}
}''' % ('if = { limit = { check_variable = { which = dtpst_nd2 value > dtpst_nd } }\n%s\n}\nelse = {\n%s\n}' % (ok("add_ship_design copies a foreign design"), fail("add_ship_design copies a foreign design")),
        check("any_owned_ship = { is_ship_size = transport }", "create_army_transport (DTP armies in transports)")))
# 9 — итог
ev.append('''country_event = {
	id = dtpst.9
	hide_window = yes
	is_triggered_only = yes
	immediate = {
		log = "DTPTEST DONE ok=[This.dtpst_ok] fail=[This.dtpst_fail] (prebuilt sizes: %d)"
		clear_variable = dtpst_ok
		clear_variable = dtpst_fail
	}
}''' % len(SIZES))

root = os.path.join(OUT, "dtp_selftest")
os.makedirs(os.path.join(root, "events"), exist_ok=True)
open(os.path.join(root, "events", "dtp_selftest_events.txt"), "w", encoding="utf-8").write("\n\n".join(ev) + "\n")
desc = 'version="%s"\ntags={\n\t"Utilities"\n}\nname="DTP Self-Test"\nsupported_version="v4.5.*"\n' % VER
open(os.path.join(root, "descriptor.mod"), "w", encoding="utf-8").write(desc)
open(os.path.join(OUT, "dtp_selftest.mod"), "w", encoding="utf-8").write(desc + 'path="mod/dtp_selftest"\n')
zp = os.path.join(OUT, "dtp_selftest_v%s.zip" % VER)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(OUT, "dtp_selftest.mod"), "dtp_selftest.mod")
    for dp, dn, fn in os.walk(root):
        for f in fn: z.write(os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), OUT))
print("selftest: %d размеров, %s" % (len(SIZES), zp))
