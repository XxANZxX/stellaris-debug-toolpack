# -*- coding: utf-8 -*-
"""Эскиз окна «Редактор держав и вида» по gui_meta3.json (без текстур игры): python3 edprev.py <out.png> <tab> [cat] [page]"""
import sys, json, re, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
m = json.load(open(os.path.join(HERE, "gui_meta3.json"), encoding="utf-8"))
out, tab = sys.argv[1], int(sys.argv[2]); cat = int(sys.argv[3]) if len(sys.argv) > 3 else 1; pg = int(sys.argv[4]) if len(sys.argv) > 4 else 1
items = [i for i in m["items"] if i["where"] == "editor"]
W = max(i["x"] + i["w"] for i in items) + 4; H = max(i["y"] + i["h"] for i in items) + 4
im = Image.new("RGB", (W, H), (14, 22, 30)); d = ImageDraw.Draw(im)
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", 13)
FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", 20)
def vis(p):
    for var, val in (("dtp_edtab", tab), ("dtp_edcat", cat), ("dtp_edpg", pg)):
        for mm in re.finditer(r"NOT = \{ check_variable = \{ which = %s value = (\d+) \} \}" % var, p):
            if int(mm.group(1)) == val: return False
        p2 = re.sub(r"NOT = \{ check_variable = \{ which = %s value = \d+ \} \}" % var, "", p)
        for mm in re.finditer(r"check_variable = \{ which = %s value = (\d+) \}" % var, p2):
            if int(mm.group(1)) != val: return False
    if re.search(r"check_variable = \{ which = dtp_pidx value = (\d+)", p) and "value = 1 }" not in re.search(r"check_variable = \{ which = dtp_pidx value = \d+ \}", p).group(0): return False
    if "NOT = { exists = event_target:dtp_tc_1 }" in p: return False
    if "dtp_last_ok" in p and "NOT = { is_variable_set = dtp_last_ok }" not in p: return False
    if "has_country_flag = dtp_force_mode" in p and "NOT = { has_country_flag = dtp_force_mode }" not in p: return False
    if re.search(r"check_variable = \{ which = dtp_(val|years) value", p) and "NOT" not in p: return False
    return True
def clean(t):
    t = re.sub(r"§.", "", t).replace("§!", "")
    t = re.sub(r"\$(\w+)\$", lambda mm: re.sub(r"^(civic|trait|ap|tradition|policy|auth|ethic)_", "", mm.group(1)).replace("_", " ").capitalize(), t)
    t = re.sub(r"\[dtp_tc_\d+\.GetName\]", "Объединённая Земля", t).replace("[dtp_tc_1.GetSpeciesName]", "Люди")
    return re.sub(r"\[From\.dtp_\w+\]", "10", t)
import random
random.seed(tab * 7 + cat)
for it in items:
    if not vis(it["pot"]): continue
    x, y, w, h = it["x"], it["y"], it["w"], it["h"]; s = it["sprite"]
    if "_has_" in it["pot"] and s == "GFX_dtp_sel_g":
        if random.random() > 0.12: continue
    if s == "GFX_dtp_sel_r" and random.random() > 0.25: continue
    if re.search(r"_on$", it["key"]) and ("dtp_tcx" in it["pot"] or "hasmod" in it["pot"]) and random.random() > 0.15: continue
    if s == "GFX_dtp_panel": d.rectangle((x, y, x + w, y + h), fill=(18, 30, 40), outline=(60, 110, 120), width=2)
    elif s == "GFX_dtp_sel_g": d.rounded_rectangle((x, y, x + w - 1, y + h - 1), radius=5, outline=(90, 235, 120), width=3)
    elif s == "GFX_dtp_sel_r": d.ellipse((x, y, x + w, y + h), fill=(200, 30, 30), outline=(255, 190, 180)); d.text((x + w // 2 - 2, y + 1), "!", fill="white", font=F)
    elif s.startswith("GFX_dtp_gi") or s.startswith("GFX_dtp_g"):
        c = (90 + hash(s) % 120, 80 + hash(s[::-1]) % 120, 140); d.ellipse((x, y, x + w, y + h), fill=c, outline=(230, 230, 230))
    elif s != "GFX_dtp_label":
        fill = {"GFX_dtp_btn_on": (70, 56, 150), "GFX_dtp_tab_on": (70, 56, 150), "GFX_dtp_btn_go": (24, 110, 104), "GFX_dtp_btn_warn": (120, 80, 24),
                "GFX_dtp_btn_danger": (120, 32, 44), "GFX_dtp_res_idle": (24, 34, 44)}.get(s, (34, 48, 76))
        d.rounded_rectangle((x, y, x + w, y + h), radius=4, fill=fill, outline=(90, 130, 170))
    t = clean(it.get("text", ""))
    if t.strip():
        f = FB if it.get("font") == "malgun_goth_24" else F
        tw = d.textlength(t.strip(), font=f)
        left = it.get("label") or t.startswith("  ")
        tx = x + (len(t) - len(t.lstrip(" "))) * 4 if left else x + (w - tw) / 2
        d.text((tx, y + (h - 15) / 2), t.strip(), fill=(235, 225, 190) if it.get("label") else (235, 240, 245), font=f)
im.save(out)
print(out, W, H)
