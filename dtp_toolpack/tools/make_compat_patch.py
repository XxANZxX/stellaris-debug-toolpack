# -*- coding: utf-8 -*-
"""Сборщик патчей совместимости Debug Toolpack с любыми модами интерфейса (11.7).

Игра не умеет объединять окна: если два мода меняют одно окно (окно планеты, нижнюю панель…), побеждает один —
и полоса или редактор DTP пропадают. Сборщик берёт файлы других модов, находит, в каком файле какой мод объявил
нужные окна (игра берёт объявление из файла, который читает позже), встраивает в них окна DTP и кладёт в патч
только изменённые файлы. Патч ставится ПОСЛЕДНИМ: моды → Debug Toolpack → (патч UIOD) → этот патч.

python3 make_compat_patch.py --game <папка Stellaris> [--out <куда>] [--id <имя>] [--layout auto|uiod|vanilla] <мод1> [<мод2> …]
  <мод…>  — папки модов В ПОРЯДКЕ ЗАГРУЗКИ (как в лаунчере), например
            steamapps/workshop/content/281990/1623423360 (UIOD)  …/281990/<id другого мода>
  --game  — папка игры (в ней interface, common, gfx/map); или по отдельности --interface/--common/--map
  --layout — раскладка полос DTP: uiod (под UI Overhaul Dynamic), vanilla; auto — uiod, если среди модов есть UIOD
"""
import os, sys, re, json, shutil, subprocess, tempfile, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
# скриптовые файлы игры, которые DTP заменяет целиком (правка встраивается в версию другого мода с тем же именем)
COMMON_FILES = ["game_rules/00_rules.txt", "scripted_triggers/00_scripted_triggers.txt",
                "scripted_triggers/02_scripted_triggers_archaeology.txt"]
KNOWN = {"1623423360": "UI Overhaul Dynamic"}                  # моды из мастерской без descriptor.mod в копии
WINDOWS = ["maingui", "planet_view", "starbase_view", "fleet_view"]

def mod_name(d):
    for f in ("descriptor.mod",):
        p = os.path.join(d, f)
        if os.path.exists(p):
            m = re.search(r'(?m)^\s*name\s*=\s*"([^"]+)"', open(p, encoding="utf-8-sig", errors="replace").read())
            if m: return m.group(1)
    b = os.path.basename(os.path.normpath(d))
    return KNOWN.get(b, b)

def is_uiod(d):
    return os.path.exists(os.path.join(d, "interface", "Ω_uiod_main_bottom.gui")) or "UI Overhaul Dynamic" in mod_name(d)   # и варианты: «… - Triple Monitors»

def gui_files(d):
    base = os.path.join(d, "interface")
    for root, _, fs in os.walk(base):
        for f in fs:
            if f.endswith(".gui"):
                yield os.path.relpath(os.path.join(root, f), base).replace(os.sep, "/")

def build(mods, vi, vc, vmap, dest, folder, name, layout="auto", readme_title=None, quiet=False, deps=None, base=()):
    """Собирает патч в dest/folder (+ dest/folder.mod). Возвращает отчёт (dict).
    base — моды-основы (например UIOD), чьи окна уже покрыты своим патчем DTP: они учитываются при сборке, но их файлы в патч не кладутся."""
    sys.path.insert(0, HERE)
    import gen3_scan as scan                                  # разбор окон — тот же, что в генераторе
    log = (lambda *a: None) if quiet else print
    if layout == "auto": layout = "uiod" if any(is_uiod(m) for m in mods) else "vanilla"
    tmp = tempfile.mkdtemp(prefix="dtp_compat_")
    try:
        ov = os.path.join(tmp, "interface"); shutil.copytree(vi, ov)
        src_of = {}                                           # файл интерфейса → из какого мода
        for m in mods:
            for rel in gui_files(m):
                dst = os.path.join(ov, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(os.path.join(m, "interface", rel), dst); src_of[rel] = mod_name(m)
        base_names = {mod_name(b) for b in base}
        own = {rel for rel, nm in src_of.items() if nm not in base_names}       # файлы модов, которые не покрыты патчем основы
        cov = os.path.join(tmp, "common_ovr"); csrc = {}
        for m in mods:
            for cf in COMMON_FILES:
                p = os.path.join(m, "common", cf)
                if os.path.exists(p):
                    os.makedirs(os.path.dirname(os.path.join(cov, cf)), exist_ok=True)
                    shutil.copy(p, os.path.join(cov, cf)); csrc[cf] = mod_name(m)
        # кто победит в каждом нужном окне — для отчёта
        owners = {w: scan.owner(ov, w) for w in WINDOWS}
        out = os.path.join(tmp, "out"); rep = os.path.join(tmp, "report.json")
        env = dict(os.environ, DTP_MODDED="|".join(src_of), DTP_REPORT=rep, DTP_VC_OVR=cov if csrc else "")
        if layout == "uiod": env["DTP_LAYOUT"] = "uiod"
        else: env.pop("DTP_LAYOUT", None)
        r = subprocess.run([sys.executable, os.path.join(HERE, "gen3.py"), out, ov, vc, vmap], capture_output=True, text=True, env=env)
        if r.returncode:
            sys.exit("сборка не удалась:\n" + (r.stdout[-1500:] + r.stderr[-3000:]))
        R = json.load(open(rep, encoding="utf-8"))
        ver = re.search(r'version="([^"]+)"', open(os.path.join(out, "descriptor.mod"), encoding="utf-8").read()).group(1)
        # что класть в патч: окна из файлов других модов (+ перенесённое окно maingui); при раскладке UIOD — все окна DTP
        def from_mod(t, srcs):
            if t in srcs: return True
            if t == "dtp_planet_editor.gui": return "main.gui" in srcs
            if t.endswith("_dtp.gui"): return t[:-8] + ".gui" in srcs
            return False
        if base: take = [t for t in R["gui"] if from_mod(t, own)]
        else: take = [t for t in R["gui"] if layout == "uiod" or from_mod(t, src_of)]
        if take and "main.gui" in take and "dtp_planet_editor.gui" not in take: take.append("dtp_planet_editor.gui")
        if "dtp_planet_editor.gui" in take and "main.gui" not in take: take.append("main.gui")
        ctake = sorted(csrc)
        warn = []
        for m in mods:                                          # чего сборщик не объединит сам
            for sub in ("game_rules", "scripted_triggers"):
                d = os.path.join(m, "common", sub)
                if os.path.isdir(d):
                    for f in sorted(os.listdir(d)):
                        if "%s/%s" % (sub, f) not in COMMON_FILES:
                            warn.append("%s: common/%s/%s — свои правила/условия; если там те же имена, что в игре, проверьте вручную" % (mod_name(m), sub, f))
        pdir = os.path.join(dest, folder)
        shutil.rmtree(pdir, ignore_errors=True)
        if not take and not ctake:
            log("патч не нужен: эти моды не трогают окна и файлы, в которые встраивается DTP")
            return {"needed": False, "owners": owners, "warn": warn}
        os.makedirs(os.path.join(pdir, "interface"), exist_ok=True)
        big = []
        for t in take:
            dst = os.path.join(pdir, "interface", t); os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(out, "interface", t), dst)
            if os.path.getsize(dst) > 3500000: big.append(t)   # проверено тестом 05.11 (4.5.3): окна, события, эффекты и условия по 3,6 МБ читаются целиком
        cout = sorted(set(R["common"][cf] for cf in ctake))                 # 11.7: условия игры — один файл с изменёнными условиями
        for co in cout:
            dst = os.path.join(pdir, co); os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(out, co), dst)
        if big: warn.append("файл больше 3,5 МБ — больше в игре не проверяли: " + ", ".join(big))
        deps = (deps or [mod_name(m) for m in mods]) + ["Debug Toolpack (DTP)"]
        desc = ('version="%s"\ntags={\n\t"Utilities"\n\t"Interface"\n}\nname="%s"\ndependencies={\n%s}\nsupported_version="v4.5.*"\n'
                % (ver, name, "".join('\t"%s"\n' % d for d in deps)))
        open(os.path.join(pdir, "descriptor.mod"), "w", encoding="utf-8").write(desc)
        open(os.path.join(dest, folder + ".mod"), "w", encoding="utf-8").write(desc + 'path="mod/%s"\n' % folder)
        lines = [readme_title or ("Патч совместимости Debug Toolpack %s с модами: %s." % (ver, ", ".join(deps[:-1]))),
                 "Порядок модов: " + " → ".join(deps) + (" → патч DTP для " + ", ".join(sorted(mod_name(b) for b in base)) if base else "") + " → этот патч (последним).",
                 "Раскладка полос DTP: " + layout, "", "Окна DTP встроены в файлы:"]
        for line in R["report"]: lines.append("  " + line)
        lines.append(""); lines.append("Файлы патча и их основа:")
        for t in take: lines.append("  interface/%s ← %s" % (t, src_of.get(t, src_of.get(t[:-8] + ".gui", src_of.get("main.gui", "игра")))))
        for cf in ctake: lines.append("  %s ← %s (common/%s)" % (R["common"][cf], csrc[cf], cf))
        if warn: lines += ["", "Проверить вручную:"] + ["  " + x for x in warn]
        open(os.path.join(pdir, "README.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
        log("\n".join(lines))
        return {"needed": True, "dir": pdir, "take": take, "common": ctake, "owners": owners, "warn": warn, "report": R["report"], "version": ver}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mods", nargs="+")
    ap.add_argument("--game"); ap.add_argument("--interface"); ap.add_argument("--common"); ap.add_argument("--map")
    ap.add_argument("--out", default="compat_out"); ap.add_argument("--id"); ap.add_argument("--name")
    ap.add_argument("--layout", default="auto", choices=["auto", "uiod", "vanilla"])
    ap.add_argument("--base", action="append", default=[], help="мод-основа (например UIOD): его окна покрывает свой патч DTP — в этот патч не кладутся")
    a = ap.parse_args()
    vi = a.interface or os.path.join(a.game, "interface")
    vc = a.common or os.path.join(a.game, "common")
    vm = a.map or os.path.join(a.game, "gfx", "map")
    names = [mod_name(m) for m in a.mods if m not in a.base]
    pid = a.id or re.sub(r"[^a-z0-9]+", "_", "_".join(n.lower() for n in names)).strip("_")[:40]
    nm = a.name or "Debug Toolpack — compatibility patch (%s)" % ", ".join(names)
    build(a.base + [m for m in a.mods if m not in a.base], vi, vc, vm, a.out, "dtp_toolpack_compat_" + pid, nm, a.layout, base=a.base)
