Патч совместимости Debug Toolpack 11.6.6 с модами: UI Overhaul Dynamic.
Порядок модов: UI Overhaul Dynamic → Debug Toolpack (DTP) → этот патч (последним).
Раскладка полос DTP: uiod

Окна DTP встроены в файлы:
  main.gui → окно maingui перенесено в dtp_planet_editor.gui (+ панель DTP и редактор планеты)
  planet_view.gui → конец окна planet_view
  Ω_uiod_main_bottom.gui → конец окна maingui_bottombar
  starbase_view.gui → конец окна starbase_view
  fleet_view.gui → обычное место

Файлы патча и их основа:
  interface/main.gui ← uiod_src
  interface/dtp_planet_editor.gui ← uiod_src
  interface/planet_view.gui ← uiod_src
  interface/Ω_uiod_main_bottom.gui ← uiod_src
  interface/starbase_view.gui ← uiod_src
  interface/fleet_view.gui ← uiod_src
