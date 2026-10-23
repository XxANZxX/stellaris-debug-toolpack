# -*- coding: utf-8 -*-
"""Нормализация строк локализации для перевода: цифры внутри [...] и номер строки журнала → #."""
import re, json, sys
def norm(v):
    v = re.sub(r"\[([^\]]*)\]", lambda m: "[" + re.sub(r"\d+", "#", m.group(1)) + "]", v)
    v = re.sub(r"^(\d+)\. ", "#. ", v)
    return v
def digits(v):
    out = []
    for m in re.finditer(r"\[([^\]]*)\]", v):
        out += re.findall(r"\d+", m.group(1))
    lead = re.match(r"^(\d+)\. ", v)
    return ([lead.group(1)] if lead else []) + out
def denorm(t, ds):
    ds = list(ds); lead = None
    if t.startswith("#. "):
        lead = ds.pop(0) if ds else "1"; t = t[3:]
    t = re.sub(r"\[([^\]]*)\]", lambda m: "[" + re.sub(r"#", lambda _: ds.pop(0) if ds else "1", m.group(1)) + "]", t)
    return (lead + ". " + t) if lead else t
if __name__ == "__main__":
    s = open(sys.argv[1], encoding="utf-8-sig").read()
    vals = re.findall(r'^ (\S+):0 "(.*)"$', s, re.M)
    uniq = sorted({norm(v) for k, v in vals if re.search(r"[А-Яа-яЁё]", v)})
    json.dump(uniq, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(uniq))
