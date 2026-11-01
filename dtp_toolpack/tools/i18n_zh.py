import re
TOK = re.compile(r"\$[A-Za-z0-9_.|]+\$|\[[^\]]*\]|\d+(?:[.,]\d+)?")
def tmpl(s):
    lead = s[:len(s) - len(s.lstrip(" "))]
    body = s[len(lead):]
    args = []
    def rep(m):
        args.append(m.group(0)); return "{%d}" % (len(args) - 1)
    t = TOK.sub(rep, body.replace("{", "⦃").replace("}", "⦄"))
    return lead, t, args
def fill(lead, t, args):
    out = re.sub(r"\{(\d+)\}", lambda m: args[int(m.group(1))] if int(m.group(1)) < len(args) else "", t)
    return lead + out.replace("⦃", "{").replace("⦄", "}")
