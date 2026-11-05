# -*- coding: utf-8 -*-
"""11.7: разбор файлов интерфейса — какие окна объявлены в файле и какой файл победит (общий для gen3.py и make_compat_patch.py).
Если одно окно объявлено в нескольких файлах, игра берёт то, что читает ПОЗЖЕ (по имени файла)."""
import os, re
def read_gui(p):
    b = open(p, "rb").read()
    try: s = b.decode("utf-8-sig")
    except UnicodeDecodeError: s = b.decode("cp1252")
    return s.replace("\r\n", "\n").replace("\r", "\n")          # как текстовый режим open(): переводы строк Windows → \n
def _gui_clean(s):
    """Та же длина; комментарии стёрты, скобки внутри строк заменены — для подсчёта вложенности."""
    return re.sub(r'"[^"\n]*"|#[^\n]*', lambda m: re.sub(r"[{}]", "_", m.group(0)) if m.group(0)[0] == '"' else " " * len(m.group(0)), s)
def top_windows(src):
    """{имя окна верхнего уровня: (начало, позиция закрывающей скобки)} — окна прямо внутри guiTypes."""
    c = _gui_clean(src); out = {}; d = 0; i = 0
    rx = re.compile(r"[{}]|\bcontainerWindowType\s*=\s*\{")
    while True:
        m = rx.search(c, i)
        if not m: break
        tok = m.group(0)
        if tok == "{": d += 1; i = m.end(); continue
        if tok == "}": d -= 1; i = m.end(); continue
        if d != 1: d += 1; i = m.end(); continue                 # вложенное окно — просто ещё одна скобка
        j, dd, name = m.end(), 1, None
        while dd:
            ch = c[j]
            if ch == "{": dd += 1
            elif ch == "}": dd -= 1
            elif dd == 1 and name is None and c.startswith("name", j) and not (c[j - 1].isalnum() or c[j - 1] == "_"):
                mm = re.match(r'name\s*=\s*"([^"]*)"', src[j:j + 300])
                if mm: name = mm.group(1)
            j += 1
        if name is not None and name not in out: out[name] = (m.start(), j - 1)
        i = j
    return out
_IDX = {}
def owner(vi, window, default=None):
    """Файл (путь от папки interface), чьё объявление окна `window` победит в игре; если окна нигде нет — default."""
    if vi not in _IDX:
        lst = []
        for root, _, fs in os.walk(vi):
            for f in fs:
                if f.endswith(".gui"):
                    rel = os.path.relpath(os.path.join(root, f), vi).replace(os.sep, "/")
                    lst.append((rel.lower(), rel))
        _IDX[vi] = sorted(lst)
    best = None
    for _, rel in _IDX[vi]:
        src = read_gui(os.path.join(vi, rel))
        if ('"%s"' % window) in src and window in top_windows(src): best = rel
    return best or default
