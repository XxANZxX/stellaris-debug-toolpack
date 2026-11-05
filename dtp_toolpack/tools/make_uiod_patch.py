# -*- coding: utf-8 -*-
"""Патч совместимости Debug Toolpack + UI Overhaul Dynamic (UIOD).

UIOD целиком заменяет игровые файлы интерфейса — те же, в которые Debug Toolpack встраивает свои окна
(main.gui, planet_view.gui, fleet_view.gui, starbase_view.gui, нижняя панель). Если UIOD стоит ниже в списке модов, окно Toolpack
пропадёт; если выше — сломается часть интерфейса UIOD. Патч собирает общий сборщик make_compat_patch.py (11.7):
он берёт файлы UIOD, встраивает в них окна Toolpack и кладёт результат в маленький мод, который ставится ПОСЛЕДНИМ:
UIOD → Debug Toolpack → патч.

python3 make_uiod_patch.py <папка_мода_UIOD> <interface_игры> <common_игры> <gfx/map_игры> <куда_положить_патч>
  <папка_мода_UIOD> — например steamapps/workshop/content/281990/1623423360
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_compat_patch as mcp

UIOD, VI, VC, VMAP, DEST = sys.argv[1:6]
r = mcp.build([UIOD], VI, VC, VMAP, DEST, "dtp_toolpack_uiod", "Debug Toolpack — UI Overhaul Dynamic patch", layout="uiod",
              quiet=True, deps=["UI Overhaul Dynamic"])
assert r["needed"], "UIOD не меняет окна, в которые встраивается DTP — проверьте папку UIOD"
print("патч UIOD готов:", r["dir"], "· файлы:", ", ".join(r["take"]))
for x in r["warn"]: print("  проверить:", x)
