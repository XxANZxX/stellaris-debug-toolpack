# -*- coding: utf-8 -*-
"""Патч совместимости Debug Toolpack + UI Overhaul Dynamic (UIOD).

UIOD целиком заменяет игровые файлы интерфейса — те же, в которые Debug Toolpack встраивает свои окна
(main.gui, planet_view.gui, fleet_view.gui, starbase_view.gui). Если UIOD стоит ниже в списке модов, окно Toolpack пропадёт;
если выше — сломается часть интерфейса UIOD. Этот скрипт берёт файлы UIOD, встраивает в них окна Toolpack
и кладёт результат в отдельный маленький мод-патч, который ставится ПОСЛЕДНИМ: UIOD → Debug Toolpack → патч.

python3 make_uiod_patch.py <папка_мода_UIOD> <interface_игры> <common_игры> <gfx/map/map_игры> <куда_положить_патч>
  <папка_мода_UIOD> — например steamapps/workshop/content/281990/1623423360
"""
import os, sys, shutil, subprocess, tempfile

UIOD, VI, VC, VMAP, DEST = sys.argv[1:6]
HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["main.gui", "planet_view.gui", "fleet_view.gui", "starbase_view.gui", "Ω_uiod_main_bottom.gui", "dtp_planet_editor.gui"]   # 11.2: редактор держав — в нижней панели UIOD
tmp = tempfile.mkdtemp(prefix="dtp_uiod_")
overlay = os.path.join(tmp, "interface")
shutil.copytree(VI, overlay)                                   # игровые файлы…
used = []
for f in FILES + ["mapicons.gui"]:                             # mapicons.wip у UIOD не активен — игра читает только .gui                             # …поверх них — файлы UIOD
    src = os.path.join(UIOD, "interface", f)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(overlay, f)); used.append(f)
out = os.path.join(tmp, "out"); os.makedirs(out)
r = subprocess.run([sys.executable, os.path.join(HERE, "gen3.py"), out, overlay, VC, VMAP], capture_output=True, text=True, env=dict(os.environ, DTP_LAYOUT="uiod"))
print(r.stdout.strip().splitlines()[-2] if r.stdout.strip() else "", r.stderr[-2000:])
if r.returncode: sys.exit("сборка не удалась")
ver = open(os.path.join(out, "descriptor.mod"), encoding="utf-8").read().split('"')[1]
pdir = os.path.join(DEST, "dtp_toolpack_uiod")
shutil.rmtree(pdir, ignore_errors=True); os.makedirs(os.path.join(pdir, "interface"))
for f in FILES:
    if os.path.exists(os.path.join(out, "interface", f)):
        shutil.copy(os.path.join(out, "interface", f), os.path.join(pdir, "interface", f))
desc = ('version="%s"\ntags={\n\t"Utilities"\n\t"Interface"\n}\nname="Debug Toolpack — UI Overhaul Dynamic patch"\n'
        'dependencies={\n\t"UI Overhaul Dynamic"\n\t"Debug Toolpack (DTP)"\n}\nsupported_version="v4.5.*"\n') % ver
open(os.path.join(pdir, "descriptor.mod"), "w", encoding="utf-8").write(desc)
open(os.path.join(DEST, "dtp_toolpack_uiod.mod"), "w", encoding="utf-8").write(desc + 'path="mod/dtp_toolpack_uiod"\n')
open(os.path.join(pdir, "README.txt"), "w", encoding="utf-8").write(
    "Патч совместимости Debug Toolpack %s и UI Overhaul Dynamic.\n"
    "Порядок модов: UI Overhaul Dynamic → Debug Toolpack (DTP) → этот патч (последним).\n"
    "Файлы UIOD, взятые за основу: %s\n" % (ver, ", ".join(used) or "нет (только игровые)"))
print("патч UIOD готов:", pdir, "· основа UIOD:", ", ".join(used) or "нет")
shutil.rmtree(tmp, ignore_errors=True)
