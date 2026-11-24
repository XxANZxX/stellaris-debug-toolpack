#!/usr/bin/env python3
"""11.9.9: удалить из готового мода текстуры .dds, на которые ничто не ссылается (ни путь, ни имя файла):
это остатки прежних сборок (генератор пишет в ту же папку и старые файлы не стирает) — в 11.9.9 их было 132 (7,3 МБ).
python3 prune_unused.py <мод>"""
import os, sys, glob
MOD = sys.argv[1]
txt = "\n".join(open(f, encoding="utf-8-sig", errors="replace").read() for f in glob.glob(os.path.join(MOD, "**", "*.*"), recursive=True)
                if f.endswith((".gui", ".txt", ".yml", ".gfx", ".asset", ".mod")))
gone, size = 0, 0
for p in glob.glob(os.path.join(MOD, "gfx", "**", "*.dds"), recursive=True):
    rel = os.path.relpath(p, MOD).replace("\\", "/")
    if rel in txt or os.path.basename(p)[:-4] in txt: continue
    size += os.path.getsize(p); os.remove(p); gone += 1
print("удалено неиспользуемых текстур: %d (%.1f МБ)" % (gone, size / 1e6))
