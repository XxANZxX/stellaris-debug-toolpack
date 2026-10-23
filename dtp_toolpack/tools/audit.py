# -*- coding: utf-8 -*-
"""Аудит логики кнопок Debug Toolpack: цели, загрузка целей, права при выполнении.
python3 audit.py <мод>"""
import re, sys, os
MOD = sys.argv[1]
import glob
s = "\n".join(open(f, encoding="utf-8").read() for f in sorted(glob.glob(os.path.join(MOD, "common/button_effects/*.txt"))))
def blocks(text):
    out = {}
    for m in re.finditer(r"^(dtp_b_\w+) = \{", text, re.M):
        i, d = m.end(), 1
        while d:
            d += {"{": 1, "}": -1}.get(text[i], 0); i += 1
        out[m.group(1)] = text[m.end():i - 1]
    return out
def part(body, name):
    m = re.search(r"\n\t%s = \{" % name, body)
    if not m: return ""
    i, d = m.end(), 1
    while d:
        d += {"{": 1, "}": -1}.get(body[i], 0); i += 1
    return body[m.end():i - 1]
B = blocks(s)
NEED = {"dtp_p": "dtp_has_tp", "dtp_s": "dtp_has_tp", "dtp_t": "dtp_has_tc", "dtp_r": "dtp_has_rcp", "dtp_f": "dtp_has_tf"}
issues = {"нет проверки цели в allow": [], "цель не загружена (нет dtp_load)": [], "право проверяется только при показе": []}
for k, body in B.items():
    eff, allow = part(body, "effect"), part(body, "allow") + part(body, "potential")
    if not eff.strip(): continue
    used = set(re.findall(r"event_target:(dtp_[ptrfs])\b", eff))
    for u in used:
        if NEED[u] not in allow and "dtp_load" in eff:
            issues["нет проверки цели в allow"].append("%s → %s" % (k, u))
    if used and "dtp_load" not in eff:
        issues["цель не загружена (нет dtp_load)"].append("%s → %s" % (k, ",".join(sorted(used))))
    if "dtp_has_perm" in allow and "dtp_has_perm" not in eff and "dtp_is_host" not in eff:
        issues["право проверяется только при показе"].append(k)
for n, v in issues.items():
    print("== %s: %d" % (n, len(v)))
    for x in v[:40]: print("   ", x)

# надписи с [цель.Свойство] без проверки, что цель существует (иначе — ошибки в error.log на каждом кадре)
import json
meta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_meta3.json")
if os.path.exists(meta):
    m = json.load(open(meta, encoding="utf-8"))
    bad = [(it["key"], t) for it in m["items"] for t in set(re.findall(r"\[(dtp_[a-z0-9_]+)\.", it["text"])) if "exists = event_target:%s" % t not in it["pot"]]
    print("== надписи без проверки цели: %d" % len(bad))
    for x in bad[:40]: print("   ", x)
