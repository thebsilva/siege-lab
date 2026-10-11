#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIEGE·LAB — gera docs/<slug>.html (um app por jogador) e docs/index.html (squad)
a partir de players/<slug>/*.json. Cada snapshot = uma medição de UMA season.
O app embute todos, oferece um SELETOR DE SEASON e compara a season escolhida
com a anterior (deltas ▲▼). Abas: Início, Coach, Mapas, Operadores, Evolução.

Uso:  python3 build.py
Nova medição: coletar em players/<slug>/raw/, rodar `python3 ingest.py AAAA-MM-DD`
(gera os snapshots) e depois este script.
"""
import json, glob, os

HERE = os.path.dirname(os.path.abspath(__file__))
PLAYERS_DIR = os.path.join(HERE, "players")
OUT_DIR = os.path.join(HERE, "docs")  # GitHub Pages serve daqui


def rank_py(rp):
    if rp is None:
        return ("—", "#8b919c")
    if rp >= 4500:
        return ("Campeão", "#e0447a")
    T = [("Cobre", 1000, "#b06a4b"), ("Bronze", 1500, "#b5762f"), ("Prata", 2000, "#9fb0bf"),
         ("Ouro", 2500, "#f4c20d"), ("Platina", 3000, "#37cfc0"), ("Esmeralda", 3500, "#2ecc71"),
         ("Diamante", 4000, "#6aa9ff")]
    t = T[0]
    for x in T:
        if rp >= x[1]:
            t = x
    div = max(1, min(5, 5 - ((rp - t[1]) // 100)))
    R = ["", "I", "II", "III", "IV", "V"]
    return (f"{t[0]} {R[div]}", t[2])


def load_names(dirs):
    """slug -> nome de todos os perfis (a aba Coach mostra com quem foi a fila)."""
    names = {}
    for d in dirs:
        p = os.path.join(d, "profile.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                prof = json.load(fh)
            names[prof.get("slug")] = prof.get("name")
    return names


def build_player(pdir, names=None):
    prof_path = os.path.join(pdir, "profile.json")
    if not os.path.exists(prof_path):
        return None
    with open(prof_path, encoding="utf-8") as fh:
        profile = json.load(fh)
    snaps = []
    for f in sorted(glob.glob(os.path.join(pdir, "*.json"))):
        if os.path.basename(f) == "profile.json":
            continue
        with open(f, encoding="utf-8") as fh:
            snaps.append(json.load(fh))
    if not snaps:
        print(f"  (pulado {profile.get('slug')}: sem snapshots)")
        return None
    pb_path = os.path.join(HERE, "playbook.json")
    playbook = {"operators": {}, "maps": {}, "default": {"def": [], "atk": []}}
    if os.path.exists(pb_path):
        with open(pb_path, encoding="utf-8") as fh:
            playbook = json.load(fh)
    html = (TEMPLATE
            .replace("__DATA__", json.dumps(snaps, ensure_ascii=False))
            .replace("__PLAYER__", json.dumps(profile, ensure_ascii=False))
            .replace("__PLAYBOOK__", json.dumps(playbook, ensure_ascii=False))
            .replace("__NAMES__", json.dumps(names or {}, ensure_ascii=False)))
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, profile.get("slug", "player") + ".html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    seasons = sorted({s.get("season") for s in snaps})
    print(f"OK -> docs/{os.path.basename(out)}  ({profile.get('name')}: {len(snaps)} season(s): {', '.join(seasons)})")
    latest = max(snaps, key=lambda s: s.get("seasonOrder", 0))
    k = latest.get("kpis", {})
    curRP = k.get("latestRP") if k.get("latestRP") is not None else k.get("peakRP")
    rk, color = rank_py(curRP)
    dmain = (latest.get("operatorsDef") or [{}])[0]
    amain = (latest.get("operatorsAtk") or [{}])[0]
    rm = latest.get("recentMatches") or []
    rw = sum(1 for m in rm if m.get("w")); rl = len(rm) - rw
    rnet = sum(m.get("rp", 0) for m in rm)
    return {"slug": profile.get("slug"), "name": profile.get("name"), "season": latest.get("season"),
            "rank": rk, "color": color, "curRP": curRP or 0, "wr": k.get("winRate"), "kd": k.get("kd"),
            "matches": k.get("matches"), "defMain": dmain.get("name"), "defWr": dmain.get("wr") or 0,
            "atkMain": amain.get("name"), "atkWr": amain.get("wr") or 0,
            "rw": rw, "rl": rl, "rnet": rnet, "hasRecent": len(rm) > 0}


def write_index(cards):
    import html as _h
    esc = lambda s: _h.escape(str(s))
    dec = lambda v: f"{v:.2f}".replace(".", ",")
    cards = sorted(cards, key=lambda c: (c.get("curRP") or 0), reverse=True)
    chips = ""
    if cards:
        kd = max(cards, key=lambda c: c.get("kd") or 0)
        dfn = max(cards, key=lambda c: c.get("defWr") or 0)
        sup = [("🎯", "Maior K/D", kd["name"], dec(kd['kd'])),
               ("🛡", "Melhor defesa", dfn["name"], f"{dfn['defMain']} · {dfn['defWr']:.0f}%")]
        rec = [c for c in cards if c.get("hasRecent")]
        if rec:
            best = max(rec, key=lambda c: c["rw"] - c["rl"])
            cold = min(rec, key=lambda c: c["rw"] - c["rl"])
            sup.append(("🔥", "Melhor forma", best["name"], f"{best['rw']}V-{best['rl']}D nas últimas"))
            sup.append(("🧊", "Em maré fria", cold["name"], f"{cold['rw']}V-{cold['rl']}D · {cold['rnet']:+d} RP"))
        chips = "".join(
            f'<div class="sup"><div class="sup-l">{ico} {esc(lbl)}</div>'
            f'<div class="sup-n">{esc(nm)}</div><div class="sup-v">{esc(v)}</div></div>'
            for ico, lbl, nm, v in sup)
    rows = ""
    for i, c in enumerate(cards, 1):
        pill = (f'<span class="rf {"up" if c["rw"] >= c["rl"] else "dn"}">últimas {c["rw"]}V-{c["rl"]}D</span>'
                if c.get("hasRecent") else "")
        rows += (
            f'<a class="prow2" href="{esc(c["slug"])}.html">'
            f'<div class="ppos">{i}</div>'
            f'<div class="pmain"><div class="pnm">{esc(c["name"])}</div>'
            f'<div class="psub">{c["wr"]:.0f}% vitórias · K/D {dec(c["kd"])} · {esc(c["season"])} {pill}</div></div>'
            f'<div class="prk" style="background:{c["color"]}22;color:{c["color"]}">{esc(c["rank"])}</div></a>')
    out = os.path.join(OUT_DIR, "index.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(INDEX_TEMPLATE.replace("__CHIPS__", chips).replace("__ROWS__", rows))
    print(f"OK -> docs/index.html  (squad com {len(cards)} jogador(es))")


def main():
    dirs = [d for d in sorted(glob.glob(os.path.join(PLAYERS_DIR, "*"))) if os.path.isdir(d)]
    if not dirs:
        raise SystemExit("Nenhum player em players/*/")
    names = load_names(dirs)
    cards = []
    for d in dirs:
        s = build_player(d, names)
        if s:
            cards.append(s)
    cards.sort(key=lambda c: (c.get("wr") or 0), reverse=True)
    write_index(cards)


INDEX_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#0a0b0e">
<title>SIEGE·LAB — Squad</title>
<style>
  :root{--bg:#0a0b0e;--panel:#14161c;--panel2:#1a1d24;--line:#262a33;--txt:#e7e9ec;--muted:#8b919c;--gold:#f4c20d;--play:#34d399;--ban:#f0513f}
  *{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
  body{background:var(--bg);color:var(--txt);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
       -webkit-font-smoothing:antialiased;min-height:100vh;padding:30px 18px 60px}
  .wrap{max-width:660px;margin:0 auto}
  .top{display:flex;align-items:center;gap:13px;margin-bottom:4px}
  .logo{width:46px;height:46px;border-radius:11px;background:var(--gold);color:#111;display:grid;place-items:center;font-weight:900;font-size:26px;box-shadow:0 0 22px rgba(244,194,13,.32)}
  h1{font-size:22px;letter-spacing:.5px} h1 em{font-style:normal;color:var(--gold)}
  .sub{color:var(--muted);font-size:13px;margin:4px 0 24px}
  h2{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin:22px 0 11px;display:flex;align-items:center;gap:9px}
  h2::before{content:"";width:4px;height:14px;background:var(--gold);border-radius:2px}
  .sups{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .sup{border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:12px 14px}
  .sup-l{font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:700}
  .sup-n{font-size:16px;font-weight:800;margin-top:5px}
  .sup-v{font-size:12px;color:var(--muted);margin-top:1px;font-variant-numeric:tabular-nums}
  .prow2{display:flex;align-items:center;gap:13px;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:14px;
         background:var(--panel);padding:14px 16px;margin-bottom:10px;transition:border-color .15s,transform .1s}
  .prow2:hover{border-color:var(--gold);transform:translateY(-1px)}
  .ppos{width:24px;height:24px;flex:none;border-radius:7px;background:#1d2129;border:1px solid #2b303a;display:grid;place-items:center;font-weight:800;font-size:13px;color:var(--muted)}
  .prow2:first-of-type .ppos{background:var(--gold);color:#111;border-color:var(--gold)}
  .pmain{flex:1;min-width:0}
  .pnm{font-size:17px;font-weight:800}
  .psub{color:var(--muted);font-size:12px;margin-top:2px;font-variant-numeric:tabular-nums;display:flex;align-items:center;gap:7px;flex-wrap:wrap}
  .rf{font-size:10px;font-weight:800;padding:2px 7px;border-radius:999px;background:#1d2129;border:1px solid #2b303a}
  .rf.up{color:var(--play);border-color:rgba(52,211,153,.4)} .rf.dn{color:var(--ban);border-color:rgba(240,81,63,.4)}
  .prk{font-size:11.5px;font-weight:800;padding:4px 10px;border-radius:999px;flex:none}
  .foot{color:#5c626d;font-size:11px;text-align:center;margin-top:26px;line-height:1.6}
  @media(max-width:440px){.sups{grid-template-columns:1fr}}
</style>
</head>
<body>
  <div class="wrap">
    <div class="top"><div class="logo">6</div><h1>SIEGE<em>·</em>LAB</h1></div>
    <div class="sub">O squad · ranqueada R6 · toque num jogador pra abrir a análise completa</div>
    <h2>Destaques do grupo</h2>
    <div class="sups">__CHIPS__</div>
    <h2>Ranking por RP</h2>
    __ROWS__
    <div class="foot">Cada jogador abre o app completo: início, coach, mapas, operadores, squad e evolução.<br>Dados de r6.tracker.network.</div>
  </div>
</body>
</html>
"""


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#0a0b0e">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>SIEGE·LAB</title>
<style>
  :root{
    --bg:#0a0b0e; --panel:#14161c; --panel2:#1a1d24; --line:#262a33;
    --txt:#e7e9ec; --muted:#8b919c; --gold:#f4c20d;
    --atk:#3b82f6; --def:#f97316;
    --play:#34d399; --neu:#facc15; --ban:#f0513f;
    --nav-h:64px;
  }
  *{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
  body{background:var(--bg);color:var(--txt);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
       -webkit-font-smoothing:antialiased;line-height:1.45;padding-bottom:calc(var(--nav-h) + env(safe-area-inset-bottom))}
  .wrap{max-width:1100px;margin:0 auto;padding:0 16px}

  header{position:sticky;top:0;z-index:50;background:rgba(10,11,14,.86);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
  .hbar{display:flex;align-items:center;gap:11px;padding:11px 16px;max-width:1100px;margin:0 auto}
  .logo{width:36px;height:36px;border-radius:9px;background:var(--gold);color:#111;display:grid;place-items:center;font-weight:900;font-size:20px;box-shadow:0 0 18px rgba(244,194,13,.3);flex:none}
  .brand{font-weight:800;font-size:16px;letter-spacing:.5px;line-height:1.05}
  .brand em{font-style:normal;color:var(--gold)}
  .brand small{display:block;font-weight:500;font-size:10.5px;color:var(--muted);letter-spacing:.3px;margin-top:1px}
  .seasonsel{margin-left:auto;display:flex;align-items:center;gap:7px;cursor:pointer;border:1px solid var(--line);background:var(--panel);
       padding:5px 8px 5px 11px;border-radius:999px}
  .seasonsel:active{transform:scale(.97)}
  .seasonsel .sv{font-weight:800;font-size:13px}
  .seasonsel .rk{font-size:10px;font-weight:700;padding:2px 7px;border-radius:999px}
  .seasonsel .cv{color:var(--muted);font-size:12px;transition:transform .2s}
  .qbtn{width:30px;height:30px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--muted);font-weight:800;font-size:14px;cursor:pointer;flex:none}
  .desktabs{display:none;gap:4px;margin-left:14px}
  .desktabs button{background:none;border:none;color:var(--muted);font-weight:700;font-size:13px;padding:7px 12px;border-radius:8px;cursor:pointer}
  .desktabs button.on{color:#111;background:var(--gold)}

  .screen{display:none;padding-top:16px}
  .screen.active{display:block;animation:fade .18s ease}
  @keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}

  h2.sec{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin:22px 0 10px;display:flex;align-items:center;gap:9px}
  h2.sec::before{content:"";width:4px;height:14px;background:var(--gold);border-radius:2px}
  h2.sec .hint{margin-left:auto;font-size:10px;letter-spacing:.4px;color:#5c626d;text-transform:none}

  .d{font-size:11px;font-weight:800;margin-left:5px;font-variant-numeric:tabular-nums;cursor:help}
  .d.up{color:var(--play)} .d.dn{color:var(--ban)} .d.eq{color:#5c626d;font-weight:600}

  /* INÍCIO */
  .kgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
  .kgrid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:2px}
  .glance{display:flex;align-items:stretch;gap:12px;border:1px solid var(--line);border-radius:16px;
       background:linear-gradient(105deg,#181b23,#0d0f13);padding:12px 14px;margin-bottom:12px}
  .glance .emb{flex:none;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;width:82px}
  .glance .emb .remb{filter:drop-shadow(0 2px 4px rgba(0,0,0,.4))}
  .glance .emb .rn{font-size:10.5px;font-weight:800;text-align:center;line-height:1.05;letter-spacing:.2px}
  .glance .emb .pk{font-size:9px;color:var(--muted);text-align:center;line-height:1}
  .glance .gstats{flex:1;display:flex;align-items:center;min-width:0}
  .glance .gst{flex:1;text-align:center;padding:0 4px;min-width:0}
  .glance .gst+.gst{border-left:1px solid var(--line)}
  .glance .gst .l{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;font-weight:700}
  .glance .gst .v{font-size:24px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1.1;margin-top:3px}
  .glance .gst .dd{height:13px;line-height:13px;margin-top:2px}
  .glance .gst .dd .d{font-size:10.5px;margin-left:0}
  @media(max-width:400px){
    .glance{gap:7px;padding:11px 9px}
    .glance .emb{width:60px}
    .glance .emb .rn{font-size:10px}
    .glance .gst{padding:0 2px}
    .glance .gst .v{font-size:18px}
    .glance .gst .l{font-size:9px;letter-spacing:.4px}
  }
  .ktile{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:14px 16px}
  .ktile .v{font-size:23px;font-weight:800;font-variant-numeric:tabular-nums}
  .ktile .l{font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.7px;margin-top:2px}
  .ktile .rkb{display:inline-block;font-size:11px;font-weight:800;padding:2px 8px;border-radius:6px;margin-top:6px}
  .banner{margin-top:12px;padding:10px 14px;border-radius:11px;font-size:12.5px;color:var(--muted);background:#101218;border:1px solid var(--line)}
  .banner b{color:var(--txt)}
  .changed{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .chcol{border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:13px 15px}
  .chcol h4{font-size:11px;text-transform:uppercase;letter-spacing:.7px;margin-bottom:9px;display:flex;align-items:center;gap:7px}
  .chcol.up h4{color:var(--play)} .chcol.dn h4{color:var(--ban)}
  .chrow{display:flex;justify-content:space-between;align-items:center;padding:5px 0;font-size:13px;border-top:1px solid #1f232b}
  .chrow:first-of-type{border-top:none}
  .chrow .nm{font-weight:600}
  .chrow .vv{font-variant-numeric:tabular-nums;color:var(--muted)}
  .plan{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:6px 16px}
  .plan .pi{display:flex;gap:11px;padding:11px 0;border-top:1px solid #1f232b;font-size:13.5px;align-items:flex-start}
  .plan .pi:first-child{border-top:none}
  .plan .ico{width:26px;height:26px;border-radius:7px;display:grid;place-items:center;font-size:13px;flex:none;margin-top:1px}
  .plan .ico.ban{background:rgba(240,81,63,.14);color:var(--ban)}
  .plan .ico.play{background:rgba(52,211,153,.14);color:var(--play)}
  .plan .ico.def{background:rgba(249,115,22,.14);color:var(--def)}
  .plan .ico.atk{background:rgba(59,130,246,.14);color:var(--atk)}
  .plan b{color:var(--txt)} .plan .pi span{color:var(--muted)}

  /* TIER */
  .tier{display:grid;grid-template-columns:1fr;gap:10px}
  .tcol{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:var(--panel)}
  .tcol .th{font-weight:800;font-size:12px;letter-spacing:1px;text-transform:uppercase;margin-bottom:9px;display:flex;align-items:center;gap:8px}
  .dot{width:9px;height:9px;border-radius:50%}
  .tcol.play{border-left:3px solid var(--play)} .tcol.play .dot{background:var(--play)}
  .tcol.neu{border-left:3px solid var(--neu)} .tcol.neu .dot{background:var(--neu)}
  .tcol.ban{border-left:3px solid var(--ban)} .tcol.ban .dot{background:var(--ban)}
  .chips{display:flex;flex-wrap:wrap;gap:7px}
  .chipm{font-size:12.5px;padding:5px 10px;border-radius:7px;background:#1d2129;border:1px solid #2b303a;font-weight:600}
  .chipm small{color:var(--muted);font-weight:500;margin-left:4px}

  /* MAP CARDS */
  .maps{display:grid;grid-template-columns:1fr;gap:14px}
  .map{border:1px solid var(--line);border-radius:14px;background:var(--panel);overflow:hidden}
  .map .head{display:flex;align-items:center;gap:7px;padding:12px 14px;background:var(--panel2);border-bottom:1px solid var(--line)}
  .map .head .mn{font-size:16px;font-weight:800}
  .verdict{font-size:9.5px;font-weight:800;padding:4px 8px;border-radius:6px;letter-spacing:.6px}
  .verdict.play{background:rgba(52,211,153,.16);color:var(--play);border:1px solid rgba(52,211,153,.4)}
  .verdict.neu{background:rgba(250,204,21,.15);color:var(--neu);border:1px solid rgba(250,204,21,.4)}
  .verdict.ban{background:rgba(240,81,63,.15);color:var(--ban);border:1px solid rgba(240,81,63,.4)}
  .map .head .wr{margin-left:auto;text-align:right;font-variant-numeric:tabular-nums}
  .map .head .wr b{font-size:15px}
  .map .head .wr small{display:block;font-size:8.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
  @media(max-width:370px){.map .head{flex-wrap:wrap;row-gap:6px}}   /* telas estreitas: o bloco de win% desce em vez de estourar o card */
  .ad{padding:11px 14px;display:flex;flex-direction:column;gap:7px;border-bottom:1px solid var(--line)}
  .adr{display:flex;align-items:center;gap:9px;font-size:11px;font-weight:800}
  .adl{width:30px;letter-spacing:.5px} .adl.atk{color:var(--atk)} .adl.def{color:var(--def)}
  .adbar{flex:1;height:7px;border-radius:4px;background:#20242c;overflow:hidden}
  .adbar i{display:block;height:100%;border-radius:4px}
  .adr.atk i{background:var(--atk)} .adr.def i{background:var(--def)}
  .adv{width:56px;text-align:right;color:var(--muted);font-variant-numeric:tabular-nums}
  .strong{padding:8px 14px;font-size:11.5px;color:var(--muted);display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .sbadge{font-size:10px;font-weight:800;padding:3px 8px;border-radius:6px;letter-spacing:.4px}
  .sbadge.atk{background:rgba(59,130,246,.14);color:var(--atk)}
  .sbadge.def{background:rgba(249,115,22,.14);color:var(--def)}
  .sbadge.bal{background:#20242c;color:var(--muted)}
  .sides{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--line)}
  .side{padding:11px 14px}
  .side+.side{border-left:1px solid var(--line)}
  .side .sh{font-size:10.5px;font-weight:800;letter-spacing:.8px;text-transform:uppercase;margin-bottom:8px;display:flex;align-items:center;gap:6px}
  .side.def .sh{color:var(--def)} .side.atk .sh{color:var(--atk)}
  .side .sh .ic{width:7px;height:7px;border-radius:2px}
  .side.def .ic{background:var(--def)} .side.atk .ic{background:var(--atk)}
  .picks{border-top:1px solid var(--line)}
  .pside{padding:11px 14px}
  .pside+.pside{border-top:1px solid var(--line)}
  .pside .sh{font-size:10.5px;font-weight:800;letter-spacing:.8px;text-transform:uppercase;margin-bottom:8px;display:flex;align-items:center;gap:6px}
  .pside.def .sh{color:var(--def)} .pside.atk .sh{color:var(--atk)}
  .pside .sh .ic{width:7px;height:7px;border-radius:2px}
  .pside.def .ic{background:var(--def)} .pside.atk .ic{background:var(--atk)}
  .prow{padding:7px 0;border-top:1px solid #1f232b}
  .prow:first-of-type{border-top:none}
  .pline{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .pn{font-size:13.5px;font-weight:700}
  .pwr{font-size:10px;font-weight:800;padding:2px 7px;border-radius:999px;background:#1d2129;border:1px solid #2b303a;cursor:help}
  .pwr.good{color:var(--play);border-color:rgba(52,211,153,.4)}
  .pwr.mid{color:var(--neu);border-color:rgba(250,204,21,.4)}
  .pwr.low{color:var(--ban);border-color:rgba(240,81,63,.4)}
  .pw{font-size:11.5px;color:var(--muted);line-height:1.45;margin-top:2px}
  .pwhy{display:block;color:var(--txt);font-weight:600;font-variant-numeric:tabular-nums}
  .prole{display:block;opacity:.72;margin-top:1px}
  .pside .sh .src{margin-left:auto;font-size:9px;font-weight:600;letter-spacing:.2px;text-transform:none;color:var(--muted);opacity:.85}
  .tip{padding:9px 14px;font-size:12px;color:#e0d6ae;background:rgba(244,194,13,.07);border-top:1px solid var(--line);line-height:1.5}
  .mine{padding:8px 14px;font-size:11px;color:var(--muted);border-top:1px solid var(--line);background:#101218;line-height:1.5}
  .forma{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:14px 16px}
  .fhead{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:12px}
  .frec{font-size:14px;color:var(--muted);font-weight:600;white-space:nowrap}
  .frec b{color:var(--txt);font-size:19px;font-weight:800} .frec span{font-size:11px;margin-left:1px}
  .fpips{display:flex;gap:4px;flex-wrap:wrap}
  .pip{width:16px;height:16px;border-radius:4px;flex:none}
  .pip.w{background:var(--play)} .pip.l{background:var(--ban);opacity:.85}
  .fkpis{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:6px}
  .fk{background:#101218;border:1px solid var(--line);border-radius:10px;padding:9px 12px}
  .fk .fl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;font-weight:700}
  .fk .fv{font-size:18px;font-weight:800;margin-top:2px;font-variant-numeric:tabular-nums;margin-left:0}
  .fins{font-size:12.5px;color:var(--muted);line-height:1.5;padding:9px 0;border-top:1px solid #1f232b}
  .fins b{color:var(--txt);font-weight:600}
  .goal{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-bottom:12px;padding:9px 14px;border:1px solid var(--line);
       border-left:3px solid var(--gold);border-radius:0 10px 10px 0;background:rgba(244,194,13,.06);font-size:12.5px;color:var(--muted)}
  .goal b{color:var(--txt);font-weight:700} .goal .gi{color:var(--gold);font-weight:800} .goal .gm{opacity:.8}
  .rbadge{font-size:9.5px;font-weight:800;padding:3px 7px;border-radius:6px;letter-spacing:.3px;background:#1d2129;border:1px solid #2b303a;white-space:nowrap}
  .rbadge.up{color:var(--play);border-color:rgba(52,211,153,.4)} .rbadge.dn{color:var(--ban);border-color:rgba(240,81,63,.4)} .rbadge.eq{color:var(--muted)}
  .rnote{padding:8px 14px;font-size:11.5px;line-height:1.5;border-top:1px solid var(--line)}
  .rnote i{font-style:normal;font-weight:800;margin-right:3px}
  .rnote.up{color:#a6e8c9;background:rgba(52,211,153,.07)} .rnote.up i{color:var(--play)}
  .rnote.dn{color:#f3a99f;background:rgba(240,81,63,.07)} .rnote.dn i{color:var(--ban)}
  .rnote b{color:var(--txt);font-weight:600}
  .sharecard{border:1px solid var(--line);border-radius:16px;background:linear-gradient(160deg,#1a1d24,#0b0d11);
       padding:22px 18px 18px;text-align:center;position:relative;overflow:hidden;margin:6px 0 14px}
  .sharecard::before{content:"";position:absolute;inset:0;background:radial-gradient(120% 60% at 50% 0%,rgba(244,194,13,.12),transparent)}
  .scbrand{font-weight:800;letter-spacing:1px;font-size:14px;position:relative} .scbrand span{color:var(--gold)}
  .scemb{margin:12px 0 6px;position:relative} .scemb .remb{filter:drop-shadow(0 3px 8px rgba(0,0,0,.5))}
  .scname{font-size:22px;font-weight:800;position:relative}
  .scrank{font-size:13px;font-weight:700;margin-top:2px;position:relative}
  .scstats{display:flex;justify-content:center;gap:26px;margin:16px 0 4px;position:relative}
  .scstats b{display:block;font-size:23px;font-weight:800;font-variant-numeric:tabular-nums}
  .scstats span{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px}
  .scfoot{font-size:10.5px;color:var(--muted);margin-top:14px;position:relative}
  .shint{font-size:12.5px;color:var(--muted);text-align:center;margin-bottom:12px}
  .btn-share{width:100%;padding:12px;border-radius:11px;border:1px solid var(--gold);background:rgba(244,194,13,.12);
       color:var(--gold);font-weight:800;font-size:14px;cursor:pointer}
  .btn-share:active{transform:scale(.98)}
  .pl{display:flex;align-items:center;justify-content:space-between;padding:4px 0;font-size:13px}
  .pl .rk{color:var(--muted);font-size:10.5px;width:13px}
  .pl .nm{flex:1;margin-left:2px;font-weight:600}
  .pl .pc{color:var(--muted);font-variant-numeric:tabular-nums}
  .pc.good{color:var(--play)} .pc.mid{color:var(--neu)} .pc.low{color:var(--ban)}
  .avoid{padding:8px 14px;font-size:11.5px;color:#f3a99f;background:rgba(240,81,63,.07);border-top:1px solid var(--line)}
  .avoid b{color:var(--ban)}
  .notew{padding:8px 14px;font-size:11.5px;color:#d9c98a;background:rgba(250,204,21,.06);border-top:1px solid var(--line)}

  /* OPERADORES */
  .ops{display:grid;grid-template-columns:1fr;gap:12px}
  .opcard{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:15px}
  .opcard h3{font-size:12.5px;letter-spacing:.5px;text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:8px}
  .tag{font-size:9.5px;font-weight:800;padding:3px 8px;border-radius:5px;letter-spacing:.5px}
  .tag.def{background:rgba(249,115,22,.15);color:var(--def);border:1px solid rgba(249,115,22,.35)}
  .tag.atk{background:rgba(59,130,246,.15);color:var(--atk);border:1px solid rgba(59,130,246,.35)}
  .tag.cut{background:rgba(240,81,63,.13);color:var(--ban);border:1px solid rgba(240,81,63,.35)}
  .oprow{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-top:1px solid #1f232b}
  .oprow:first-of-type{border-top:none}
  .oprow .nm{font-weight:600;font-size:14px}
  .oprow .st{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums;text-align:right}
  .oprow .st b{color:var(--txt)} .star{color:var(--gold)}
  .oprow.clk{cursor:pointer}
  .fchips{display:flex;gap:7px;margin-bottom:10px}
  .fchip{font-size:12px;padding:5px 11px;border-radius:7px;background:#1d2129;border:1px solid #2b303a;font-weight:600;color:var(--muted);cursor:pointer}
  .fchip.on{color:var(--txt);border-color:var(--gold);background:rgba(244,194,13,.08)}
  .optable tr{cursor:pointer}
  .optable tr.dim{color:var(--muted)}
  .optable th.on{color:var(--gold)}
  .tag.sm{font-size:9px;padding:1px 5px;margin-left:6px;vertical-align:1px}
  .otwrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
  .optable th{white-space:nowrap}
  @media(max-width:560px){
    #allops{padding-left:8px;padding-right:8px}
    .ctable.optable .ar{display:none}
    .ctable.optable th{font-size:9px;letter-spacing:.2px;padding:0 3px 6px}
    .ctable.optable td{font-size:12px;padding:7px 3px}
    .ctable.optable td small{display:none}
    .ctable.optable .tag.sm{font-size:8px;padding:1px 3px;margin-left:4px}
  }

  /* EVOLUÇÃO */
  .evo{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:16px;margin-bottom:12px}
  .evo h3{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px}
  .spark{width:100%;height:96px;overflow:visible}
  .evhead,.evrow{display:flex;gap:8px;align-items:center;font-variant-numeric:tabular-nums}
  .evhead{padding-bottom:7px;font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
  .evrow{padding:11px 0;border-top:1px solid #1f232b;font-size:13px}
  .evrow .sn{width:118px;flex:none;font-weight:700}
  .evrow .sn small{display:block;font-weight:500;color:var(--muted);font-size:10.5px}
  .evhead .sn{width:118px;flex:none}
  .cell{flex:1;text-align:right;color:var(--muted)} .cell b{color:var(--txt)}
  .rkb2{font-size:10px;font-weight:800;padding:2px 6px;border-radius:5px}

  nav.bottom{position:fixed;left:0;right:0;bottom:0;z-index:60;background:rgba(13,14,18,.92);backdrop-filter:blur(16px);border-top:1px solid var(--line);display:flex;height:calc(var(--nav-h) + env(safe-area-inset-bottom));padding-bottom:env(safe-area-inset-bottom)}
  nav.bottom button{flex:1;background:none;border:none;color:var(--muted);font-size:10px;font-weight:700;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;cursor:pointer;letter-spacing:.3px}
  nav.bottom button svg{width:21px;height:21px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
  nav.bottom button.on{color:var(--gold)}

  .sheetbg{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:90;display:none}
  .sheetbg.open{display:block}
  .sheet{position:fixed;left:0;right:0;bottom:0;z-index:91;background:var(--panel2);border-top-left-radius:18px;border-top-right-radius:18px;border:1px solid var(--line);padding:18px 18px calc(18px + env(safe-area-inset-bottom));transform:translateY(105%);transition:transform .22s ease;max-width:560px;margin:0 auto;max-height:80vh;overflow:auto}
  .sheet.open{transform:none}
  .sheet h3{font-size:14px;margin-bottom:12px}
  .grab{width:38px;height:4px;border-radius:2px;background:#333a46;margin:0 auto 14px}
  .srow{display:flex;align-items:center;gap:11px;padding:12px 12px;border-radius:11px;border:1px solid var(--line);background:var(--panel);margin-bottom:9px;cursor:pointer}
  .srow.on{border-color:var(--gold);background:rgba(244,194,13,.06)}
  .srow .sname{font-weight:800;font-size:14px}
  .srow .smeta{font-size:11.5px;color:var(--muted);margin-top:1px}
  .srow .srk{margin-left:auto;font-size:11px;font-weight:800;padding:3px 9px;border-radius:999px}
  .legrow{display:flex;gap:10px;align-items:baseline;padding:7px 0;font-size:13px;color:var(--muted);border-top:1px solid #232833}
  .legrow:first-of-type{border-top:none}
  .legrow b{font-size:15px;width:30px;flex:none;text-align:center}

  .foot{margin:26px 0 10px;color:#5c626d;font-size:11px;text-align:center}

  /* COACH */
  .cgoal{border:1px solid var(--line);border-left:3px solid var(--gold);border-radius:14px;background:var(--panel);padding:14px 16px}
  .cg-top{display:flex;gap:12px;align-items:center}
  .cg-l{font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.7px;font-weight:700}
  .cg-v{font-size:16px;margin-top:2px} .cg-v b{font-weight:800}
  .cg-s{font-size:12px;color:var(--muted);margin-top:3px} .cg-s b{color:var(--txt)}
  .ctable{width:100%;border-collapse:collapse;font-size:13px;font-variant-numeric:tabular-nums;margin-top:10px}
  .ctable th{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:700;text-align:right;padding:0 4px 6px}
  .ctable td{padding:7px 4px;border-top:1px solid #1f232b;text-align:right;color:var(--muted);white-space:nowrap}
  .ctable td b{color:var(--txt)}
  .ctable th:first-child,.ctable td:first-child{text-align:left;color:var(--txt);white-space:normal}
  .ctable small{color:var(--muted);font-size:10.5px}
  .cbox{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:4px 16px 12px}
  .fcards{display:grid;grid-template-columns:1fr;gap:12px}
  .fcard{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:14px 16px}
  .fcard h4{font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);margin-bottom:6px}
  .fbig{font-size:26px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1.1}
  .fsub{font-size:12px;color:var(--muted);margin-top:3px;line-height:1.4}
  .cmp{display:flex;flex-direction:column;gap:7px;margin:12px 0 10px}
  .cmpr{display:flex;align-items:center;gap:9px;font-size:11.5px}
  .cmpr .cl{width:118px;flex:none;color:var(--muted);line-height:1.2}
  .cmpr .cb{flex:1;height:8px;border-radius:4px;background:#20242c;overflow:hidden}
  .cmpr .cb i{display:block;height:100%;border-radius:4px;background:#5c626d}
  .cmpr.me .cl{color:var(--txt);font-weight:700}
  .cmpr.me .cb i{background:var(--gold)}
  .cmpr .cv{width:84px;flex:none;text-align:right;font-variant-numeric:tabular-nums;color:var(--muted)}
  .cmpr .cv small{font-size:10px;opacity:.8}
  .cmpr.me .cv{color:var(--txt);font-weight:700}
  .fread{font-size:13px;line-height:1.55;color:#cfd3d8}
  .fread b{color:var(--txt)}
  .fsrc{font-size:10.5px;color:#5c626d;margin-top:8px;line-height:1.4}
  .ctable td.csub{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:700;padding-top:12px;text-align:left}
  .d.nt{color:#9aa3ad}
  .fcard h4 .exp{margin-left:6px;padding:1px 6px;border-radius:5px;background:rgba(244,194,13,.14);color:var(--gold);font-size:9px;letter-spacing:.6px;vertical-align:1px}
  @media(max-width:400px){ .cmpr .cl{width:92px} .cmpr .cv{width:76px} }

  @media(min-width:900px){
    .fcards{grid-template-columns:repeat(2,1fr)}
    body{padding-bottom:24px}
    nav.bottom{display:none}
    .desktabs{display:flex}
    .kgrid{grid-template-columns:repeat(4,1fr)}
    .changed{grid-template-columns:1fr 1fr}
    .tier{grid-template-columns:repeat(3,1fr)}
    .maps{grid-template-columns:repeat(2,1fr)}
    .ops{grid-template-columns:repeat(3,1fr)}
  }
</style>
</head>
<body>

<header>
  <div class="hbar">
    <div class="logo">6</div>
    <div class="brand">SIEGE<em>·</em>LAB<small id="subline"></small></div>
    <nav class="desktabs" id="desktabs"></nav>
    <div class="seasonsel" id="seasonsel">
      <span class="sv" id="ss-season"></span>
      <span class="rk" id="ss-rank"></span>
      <span class="cv">▾</span>
    </div>
    <button class="qbtn" id="sharebtn" aria-label="Compartilhar"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg></button>
    <button class="qbtn" id="helpbtn" aria-label="Como ler">?</button>
  </div>
</header>

<div class="wrap">
  <section class="screen" id="scr-inicio"></section>
  <section class="screen" id="scr-coach"></section>
  <section class="screen" id="scr-mapas"></section>
  <section class="screen" id="scr-ops"></section>
  <section class="screen" id="scr-squad"></section>
  <section class="screen" id="scr-evo"></section>
  <div class="foot" id="foot"></div>
</div>

<nav class="bottom" id="bottomnav"></nav>

<div class="sheetbg" id="sheetbg"></div>
<div class="sheet" id="sheet"></div>

<script>
const SNAPSHOTS = __DATA__;
const PLAYER = __PLAYER__;
const PLAYBOOK = __PLAYBOOK__;
const NAMES = __NAMES__;              // slug -> nome de quem é do squad

/* ---------- base ---------- */
const esc = s => String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fx=(v,d)=>Number(v).toFixed(d).replace(".",",");   // decimal com vírgula; o milhar vem do nf()
const byName = l => Object.fromEntries((l||[]).map(x=>[x.name,x]));
const wrClass = w => w>=55?"good":(w>=50?"mid":"low");
const ROM=["","I","II","III","IV","V"];

// ordena por season e depois por data
const ALL = SNAPSHOTS.slice().sort((a,b)=>(a.seasonOrder-b.seasonOrder)||String(a.date).localeCompare(String(b.date)));
// seasons distintas (última medição de cada), mais nova primeiro
const seasonMap = {};
ALL.forEach(s=>{ seasonMap[s.seasonOrder]=s; });
const SEASONS = Object.values(seasonMap).sort((a,b)=>b.seasonOrder-a.seasonOrder);
let active = SEASONS[0];              // season selecionada (default = mais recente)

function baselineOf(snap){            // última medição da season anterior (nunca uma parcial da mesma season)
  return SEASONS.find(s=>s.seasonOrder<snap.seasonOrder) || null;
}

function rankInfo(rp){
  if(rp==null) return {name:"—",color:"#8b919c",div:0};
  if(rp>=4500) return {name:"Campeão",color:"#e0447a",div:0,champ:true};
  const T=[{n:"Cobre",s:1000,c:"#b06a4b"},{n:"Bronze",s:1500,c:"#b5762f"},{n:"Prata",s:2000,c:"#9fb0bf"},
           {n:"Ouro",s:2500,c:"#f4c20d"},{n:"Platina",s:3000,c:"#37cfc0"},{n:"Esmeralda",s:3500,c:"#2ecc71"},
           {n:"Diamante",s:4000,c:"#6aa9ff"}];
  let t=T[0]; T.forEach(x=>{ if(rp>=x.s) t=x; });
  const div=Math.max(1,Math.min(5,5-Math.floor((rp-t.s)/100)));
  return {name:`${t.n} ${ROM[div]}`,tier:t.n,color:t.c,div};
}
function rankEmblem(color, div, champ, size){
  size = size||52;
  const R=["","I","II","III","IV","V"];
  const label = champ ? "★" : (R[div]||"");
  const out="24,3 5.81,13.5 5.81,34.5 24,45 42.19,34.5 42.19,13.5";
  const inn="24,10.6 12.4,17.3 12.4,30.7 24,37.4 35.6,30.7 35.6,17.3";
  const hl="5.81,13.5 24,3 42.19,13.5 24,24";
  return `<svg class="remb" width="${size}" height="${size}" viewBox="0 0 48 48" aria-hidden="true">
    <polygon points="${out}" fill="${color}" stroke="rgba(0,0,0,.42)" stroke-width="1.3"/>
    <polygon points="${hl}" fill="rgba(255,255,255,.15)"/>
    <polygon points="${inn}" fill="none" stroke="rgba(255,255,255,.34)" stroke-width="1.1"/>
    <text x="24" y="25.5" fill="#fff" stroke="rgba(0,0,0,.45)" stroke-width="3" paint-order="stroke"
      font-size="${champ?18:16}" font-weight="800" text-anchor="middle" dominant-baseline="central"
      font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif">${label}</text>
  </svg>`;
}

function delta(c,p,dec=0){
  if(c==null||p==null) return "";
  const d=c-p, thr=dec?0.005:0.5, pv=fx(p,dec), cv=fx(c,dec);
  if(Math.abs(d)<thr) return `<span class="d eq" title="estável (${cv})">=</span>`;
  const up=d>0;
  return `<span class="d ${up?'up':'dn'}" title="${up?'subiu':'caiu'}: antes ${pv} → agora ${cv}">${up?'▲':'▼'}${fx(Math.abs(d),dec)}</span>`;
}
const tierOf = wr => wr>=55?"play":(wr<40?"ban":"neu");

/* ---------- INÍCIO ---------- */
function renderInicio(){
  const cur=active, base=baselineOf(cur);
  const k=cur.kpis, pk=(base||{}).kpis||{};
  const curRP = (k.latestRP!=null?k.latestRP:k.peakRP);
  const rk=rankInfo(curRP), peak=rankInfo(k.peakRP);
  const pbRP = base ? (base.kpis.latestRP!=null?base.kpis.latestRP:base.kpis.peakRP) : null;
  const wl = (k.wins!=null&&k.losses!=null) ? `${k.wins}-${k.losses}` : "—";
  const banner = base
    ? `🔄 Comparando <b>${esc(cur.season)}</b> com <b>${esc(base.season)}</b> (${esc(base.seasonLabel||"")}). Setas ▲▼ = quanto mudou; em porcentagem, conta em pontos (50% → 53% = ▲3).`
    : `📍 Season mais antiga carregada — sem comparação. Carregue outra season pra ver as variações.`;

  // o que mudou (mapas presentes nas duas)
  let changed = "";
  if(base){
    const pb=byName(base.maps);
    const movers = cur.maps.filter(m=>pb[m.name]&&(m.matches>=4)&&(pb[m.name].matches>=4))
      .map(m=>({name:m.name, now:m.seasonWR, was:pb[m.name].seasonWR, d:m.seasonWR-pb[m.name].seasonWR}))
      .filter(m=>Math.abs(m.d)>=3);
    const ups=movers.filter(m=>m.d>0).sort((a,b)=>b.d-a.d).slice(0,3);
    const dns=movers.filter(m=>m.d<0).sort((a,b)=>a.d-b.d).slice(0,3);
    const rowsUp=ups.map(m=>`<div class="chrow"><span class="nm">${esc(m.name)}</span><span class="vv">${m.was.toFixed(0)}→${m.now.toFixed(0)}% <span class="d up">▲${m.d.toFixed(0)}</span></span></div>`).join("")||`<div class="chrow"><span class="vv">—</span></div>`;
    const rowsDn=dns.map(m=>`<div class="chrow"><span class="nm">${esc(m.name)}</span><span class="vv">${m.was.toFixed(0)}→${m.now.toFixed(0)}% <span class="d dn">▼${Math.abs(m.d).toFixed(0)}</span></span></div>`).join("")||`<div class="chrow"><span class="vv">—</span></div>`;
    changed = `<h2 class="sec">O que mudou desde ${esc(base.season)}<span class="hint">win% por mapa</span></h2>
      <div class="changed">
        <div class="chcol up"><h4>⬈ Subiram</h4>${rowsUp}</div>
        <div class="chcol dn"><h4>⬊ Caíram</h4>${rowsDn}</div>
      </div>`;
  }

  const bans=cur.maps.filter(m=>tierOf(m.seasonWR)==="ban"&&m.matches>=4).sort((a,b)=>a.seasonWR-b.seasonWR);
  const plays=cur.maps.filter(m=>tierOf(m.seasonWR)==="play"&&m.matches>=6).sort((a,b)=>b.seasonWR-a.seasonWR);
  const dM=cur.operatorsDef[0], aM=cur.operatorsAtk[0], cM=cur.operatorsCut[0];

  document.getElementById("scr-inicio").innerHTML = `
    <div class="glance">
      <div class="emb">
        ${rankEmblem(rk.color, rk.div, rk.champ, 56)}
        <div class="rn" style="color:${rk.color}">${rk.name}</div>
        <div class="pk">pico ${peak.name}</div>
      </div>
      <div class="gstats">
        <div class="gst"><div class="l">RP</div><div class="v">${curRP.toLocaleString('pt-BR')}</div><div class="dd">${delta(curRP,pbRP,0)}</div></div>
        <div class="gst"><div class="l">K/D</div><div class="v">${fx(k.kd,2)}</div><div class="dd">${delta(k.kd,pk.kd,2)}</div></div>
        <div class="gst"><div class="l">V / D</div><div class="v">${wl}</div><div class="dd"></div></div>
      </div>
    </div>
    ${(()=>{const g=nextGoal(), p=rpPace();return g?`<div class="goal"><span class="gi">▲</span> Faltam <b>+${g.need} RP</b> pra <b style="color:${g.color}">${g.name}</b><span class="gm"> · cada vitória ≈ +${p?Math.round(p.win):25} RP</span></div>`:"";})()}
    <div class="kgrid2">
      <div class="ktile"><div class="v">${k.matches}${delta(k.matches,pk.matches,0)}</div><div class="l">Partidas</div></div>
      <div class="ktile"><div class="v">${fx(k.winRate,1)}%${delta(k.winRate,pk.winRate,1)}</div><div class="l">Vitórias</div></div>
    </div>
    ${formaRecente()}
    <div class="banner">${banner}</div>
    ${changed}
    <h2 class="sec">Plano de jogo</h2>
    <div class="plan">
      <div class="pi"><div class="ico ban">⛔</div><div><b>Bane ${esc(bans[0]?.name||"—")}.</b> <span>${bans.length>1?"Depois "+esc(bans.slice(1,3).map(m=>m.name).join(" / "))+". ":""}Seus piores mapas.</span></div></div>
      <div class="pi"><div class="ico play">✔</div><div><b>Force ${esc(plays.slice(0,4).map(m=>m.name).join(", ")||"—")}.</b> <span>Vote neles sempre.</span></div></div>
      ${dM?`<div class="pi"><div class="ico def">🛡</div><div><b>Defesa: ${esc(dM.name)} (${dM.wr}%).</b> <span>Seu melhor defensor.${cur.operatorsDef[1]?" Segunda opção: "+esc(cur.operatorsDef[1].name)+".":""}</span></div></div>`:""}
      ${aM?`<div class="pi"><div class="ico atk">⚔</div><div><b>Ataque: ${esc(aM.name)} (${aM.wr}%).</b> <span>O pick de cada mapa está na aba Mapas.</span></div></div>`:""}
      ${cM?`<div class="pi"><div class="ico ban">✕</div><div><b>Repense ${esc(cM.name)} (${cM.wr}%).</b> <span>Muito jogado e perde mais do que ganha — corte ou reposicione.</span></div></div>`:""}
    </div>`;
}

function recentByMap(){
  const o={}; (active.recentMatches||[]).forEach(m=>{o[m.map]=o[m.map]||{w:0,l:0}; m.w?o[m.map].w++:o[m.map].l++;}); return o;
}
function nextGoal(){
  const rp=(active.kpis.latestRP!=null?active.kpis.latestRP:active.kpis.peakRP);
  if(rp==null||rp>=4500) return null;
  const nb=(Math.floor(rp/100)+1)*100, nr=rankInfo(nb);
  return {need:nb-rp, name:nr.name, color:nr.color};
}
function recencyNote(m, rr){
  if(!rr || (rr.w+rr.l)<2) return "";
  const t=tierOf(m.seasonWR);
  if(t==="ban" && rr.w>rr.l) return `<div class="rnote up"><i>↗</i> Você vem <b>ganhando</b> aqui (${rr.w}V-${rr.l}D nas últimas partidas): o "banir" da season pode estar desatualizado — reavalie.</div>`;
  if(t==="play" && rr.l>rr.w) return `<div class="rnote dn"><i>↘</i> <b>Esfriou</b> (${rr.w}V-${rr.l}D nas últimas partidas) apesar de ser mapa forte — cuidado ao forçar.</div>`;
  return "";
}

/* ---------- MAPAS ---------- */
function tierChips(cur, base, tier){
  const pb = base?byName(base.maps):{};
  return cur.maps.filter(m=>tierOf(m.seasonWR)===tier)
    .sort((a,b)=>((a.matches<4)-(b.matches<4))||(b.seasonWR-a.seasonWR))
    .map(m=>`<span class="chipm">${esc(m.name)}<small>${m.seasonWR.toFixed(0)}%${m.matches<4?"°":""}${delta(m.seasonWR,(pb[m.name]||{}).seasonWR,0)}</small></span>`).join("") || `<span class="chipm" style="opacity:.5">—</span>`;
}
function sideRows(list, pl){
  const p=byName(pl);
  return (list||[]).map((o,i)=>`<div class="pl"><span class="rk">${i+1}</span><span class="nm">${esc(o.name)}${o.small?"°":""}</span><span class="pc ${wrClass(o.wr)}">${o.wr}%${delta(o.wr,(p[o.name]||{}).wr,0)}</span></div>`).join("");
}
function strongSide(m){
  const dd=(m.atkWR||0)-(m.defWR||0);
  if(dd>=8) return `<span class="sbadge atk">FORTE NO ATAQUE</span>`;
  if(dd<=-8) return `<span class="sbadge def">FORTE NA DEFESA</span>`;
  return `<span class="sbadge bal">EQUILIBRADO</span>`;
}
function opSide(name){ return ((PLAYBOOK.operators||{})[name]||{}).side || null; }
function baseOf(){ return {wr:(active.kpis.winRate||50), kd:(active.kpis.kd||1)}; }
/* merge amostra x vitoria x K/D: encolhe para a media do jogador conforme a amostra */
function scoreOp(o, base){
  const P_WR=10, P_KD=25, W_KD=12, n=o.rounds||0;   /* K/D varia mais -> encolhe mais */
  const wr=(o.wr!=null?o.wr:base.wr), kd=(o.kd!=null?o.kd:base.kd);
  const adjWR=(wr*n + base.wr*P_WR)/(n+P_WR);
  const adjKD=(kd*n + base.kd*P_KD)/(n+P_KD);
  return {n, adjWR, adjKD, score:(adjWR-base.wr) + (adjKD-base.kd)*W_KD};
}
function whyData(o, sc){
  const bits=[];
  if(o.kd!=null) bits.push(`K/D ${fx(o.kd,2)}`);
  let v;
  if((o.rounds||0)<8) v="amostra curta, só indício";
  else if(sc.score>=10) v="bem acima da sua média";
  else if(sc.score>=3) v="acima da sua média";
  else if(sc.score<=-5) v="abaixo da sua média — cuidado";
  else v="na sua média";
  return bits.length?bits.join(" · ")+" — "+v:v;
}
function candidates(m, side){
  if(m[side] && m[side].length && m[side].some(o=>o.rounds!=null))
    return {src:"mapa", list:m[side].filter(o=>o.rounds!=null)};
  const seasonList = side==="def" ? (active.operatorsDef||[]) : (active.operatorsAtk||[]);
  const cut = (active.operatorsCut||[]).filter(o=>opSide(o.name)===side);
  const merged = seasonList.concat(cut).filter(o=>o.rounds!=null);
  if(merged.length) return {src:"season", list:merged};
  return {src:"playbook", list:[]};
}
function srcLabel(s){
  return s==="mapa" ? "seu histórico neste mapa"
       : s==="season" ? "sua season (ainda sem dado por mapa)"
       : "referência geral (sem dado seu)";
}
function pickRows(m, side){
  const base=baseOf(), c=candidates(m, side);
  if(c.src==="playbook"){
    const conf=(PLAYBOOK.maps||{})[m.name]||PLAYBOOK.default||{};
    return (conf[side]||[]).map(n=>
      `<div class="prow"><div class="pline"><span class="pn">${esc(n)}</span></div>`+
      `<div class="pw">${esc(((PLAYBOOK.operators||{})[n]||{}).why||"")}</div></div>`).join("");
  }
  const ranked=c.list.map(o=>({o, sc:scoreOp(o,base)})).sort((a,b)=>b.sc.score-a.sc.score).slice(0,3);
  return ranked.map(({o,sc})=>{
    const role=((PLAYBOOK.operators||{})[o.name]||{}).why||"";
    return `<div class="prow"><div class="pline"><span class="pn">${esc(o.name)}</span>`+
      `<span class="pwr ${wrClass(o.wr)}" title="amostra usada no cálculo">${o.wr}% · ${o.rounds||0} rds</span></div>`+
      `<div class="pw"><b class="pwhy">${esc(whyData(o,sc))}</b>${role?`<span class="prole">${esc(role)}</span>`:""}</div></div>`;
  }).join("");
}
function mapTip(m){
  const a=m.atkWR||0, d=m.defWR||0, diff=a-d;
  if(diff<=-8) return `Seu ataque aqui é o ponto fraco: ${a.toFixed(0)}% contra ${d.toFixed(0)}% na defesa. Gaste utilidade pra abrir — EMP e hard breach — e entre junto, não em pinga-pinga.`;
  if(diff>=8) return `Sua defesa aqui é o ponto fraco: ${d.toFixed(0)}% contra ${a.toFixed(0)}% no ataque. Não segure passivo: atrase com roam e jogue o retake.`;
  return `Lados equilibrados (atk ${a.toFixed(0)}% / def ${d.toFixed(0)}%). O round se decide na primeira troca — entre junto.`;
}
function mineLine(m){
  if(!m.def && !m.atk) return "";
  const f=l=>(l||[]).map(o=>`${esc(o.name)} ${o.wr}%`).join(" · ");
  const parts=[];
  if(m.def) parts.push(`<b style="color:var(--def)">def</b> ${f(m.def)}`);
  if(m.atk) parts.push(`<b style="color:var(--atk)">atk</b> ${f(m.atk)}`);
  return `<div class="mine">Seus melhores aqui — ${parts.join(" &nbsp;·&nbsp; ")}</div>`;
}
function formaRecente(){
  const ms=active.recentMatches;
  if(!ms||!ms.length) return "";
  const n=ms.length, w=ms.filter(m=>m.w).length, l=n-w;
  const netRP=ms.reduce((s,m)=>s+(m.rp||0),0);
  const posKD=ms.filter(m=>(m.kd||0)>=1).length;
  const pips=ms.slice().reverse().map(m=>`<span class="pip ${m.w?'w':'l'}" title="${esc(m.map)} · ${m.w?'V':'D'} · K/D ${fx(m.kd||0,2)}"></span>`).join("");
  const byMap={};
  ms.forEach(m=>{byMap[m.map]=byMap[m.map]||{w:0,l:0}; m.w?byMap[m.map].w++:byMap[m.map].l++;});
  const cold=Object.entries(byMap).filter(([,v])=>v.w===0&&v.l>=2).map(([k,v])=>`${esc(k)} (${v.w}V-${v.l}D)`);
  const hot=Object.entries(byMap).filter(([,v])=>v.l===0&&v.w>=2).map(([k,v])=>`${esc(k)} (${v.w}V-${v.l}D)`);
  let streak=1; const sw=ms[0].w; for(let i=1;i<ms.length;i++){ if(ms[i].w===sw) streak++; else break; }
  const ins=[];
  if(!sw && streak>=2) ins.push(`Você está numa <b>maré de ${streak} derrotas</b> — considere uma pausa antes da próxima.`);
  if(sw && streak>=3) ins.push(`<b>${streak} vitórias seguidas</b> — você está quente, aproveite enquanto dura.`);
  if(posKD/n>=0.6 && Math.abs(w-l)<=2) ins.push(`Em <b>${posKD} das ${n}</b> partidas seu K/D foi de 1,0 ou mais, mas o placar ficou <b>${w}V-${l}D</b>: o abate sozinho não está virando vitória. Jogue junto do time em vez de buscar frag solo.`);
  if(cold.length) ins.push(`Sem vitória nas últimas ${n} partidas em <b>${cold.join(", ")}</b> — bane no ranqueado.`);
  if(hot.length) ins.push(`Só vitórias nas últimas ${n} partidas em <b>${hot.join(", ")}</b> — vale votar ${hot.length>1?"nesses mapas":"nesse mapa"}.`);
  const rpCls=netRP>0?'up':(netRP<0?'dn':'eq');
  return `
    <h2 class="sec">Forma recente<span class="hint">últimas ${n} partidas</span></h2>
    <div class="forma">
      <div class="fhead">
        <div class="frec"><b>${w}</b><span>V</span> · <b>${l}</b><span>D</span></div>
        <div class="fpips">${pips}</div>
      </div>
      <div class="fkpis">
        <div class="fk"><div class="fl">RP no período</div><div class="fv d ${rpCls}">${netRP>0?'+':''}${netRP}</div></div>
        <div class="fk"><div class="fl">Com K/D 1,0+</div><div class="fv">${posKD}/${n}</div></div>
      </div>
      ${ins.map(t=>`<div class="fins">${t}</div>`).join("")}
    </div>`;
}
function renderMapas(){
  const cur=active, base=baselineOf(cur), pb=base?byName(base.maps):{};
  const rbm=recentByMap();
  const cards = cur.maps.filter(m=>m.matches>=1).sort((a,b)=>(a.matches<4)-(b.matches<4)).map(m=>{
    const t=tierOf(m.seasonWR), v={play:"PRIORIZE",neu:"NEUTRO",ban:"BANIR"}[t];
    const pm=pb[m.name]||{};
    const rr=rbm[m.name];
    const rbadge=rr?`<span class="rbadge ${rr.w>rr.l?'up':(rr.l>rr.w?'dn':'eq')}" title="resultado nas partidas recentes">últ. ${rr.w}V-${rr.l}D</span>`:"";
    const cD=candidates(m,"def"), cA=candidates(m,"atk");
    const opsHtml = `<div class="picks">
        <div class="pside def"><div class="sh"><span class="ic"></span>${cD.src==="playbook"?"Pegue na defesa":"Seus melhores na defesa"}<span class="src">${esc(srcLabel(cD.src))}</span></div>${pickRows(m,"def")}</div>
        <div class="pside atk"><div class="sh"><span class="ic"></span>${cA.src==="playbook"?"Pegue no ataque":"Seus melhores no ataque"}<span class="src">${esc(srcLabel(cA.src))}</span></div>${pickRows(m,"atk")}</div>
      </div>
      <div class="tip">${esc(mapTip(m))}</div>`;
    const adbar=(cls,val)=>`<div class="adr ${cls}"><span class="adl ${cls}">${cls.toUpperCase()}</span><div class="adbar"><i style="width:${Math.max(3,val||0)}%"></i></div><span class="adv">${(val||0).toFixed(0)}%${delta(val,(cls==='atk'?pm.atkWR:pm.defWR),0)}</span></div>`;
    return `<div class="map">
      <div class="head"><span class="mn">${esc(m.name)}</span><span class="verdict ${t}">${v}</span>${rbadge}
        <span class="wr"><b>${m.seasonWR.toFixed(0)}%${delta(m.seasonWR,pm.seasonWR,0)}</b><small>${m.matches} ${m.matches===1?"PARTIDA":"PARTIDAS"}${m.matches<4?" °":""}</small></span></div>
      <div class="ad">${adbar('atk',m.atkWR)}${adbar('def',m.defWR)}</div>
      <div class="strong">${strongSide(m)} <span>K/D ${fx(m.kd||0,2)}${delta(m.kd,pm.kd,2)}</span></div>
      ${opsHtml}
      ${recencyNote(m,rr)}
      ${m.note?`<div class="notew">⚠ ${esc(m.note)}</div>`:""}
      ${m.avoid?`<div class="avoid"><b>Evite:</b> ${esc(m.avoid)}</div>`:""}
    </div>`;
  }).join("");
  const opsNote = `<div class="banner" style="margin-bottom:12px">🎯 Em cada mapa, os operadores sugeridos pra cada lado vêm do seu histórico (quando há dado) ou de uma referência geral — o rótulo ao lado diz qual. Os números são % de rounds vencidos · rounds jogados. <b>°</b> = amostra pequena: indício, não veredito.</div>`;
  document.getElementById("scr-mapas").innerHTML = `
    <h2 class="sec">Jogar vs banir<span class="hint">win% da season</span></h2>
    <div class="tier">
      <div class="tcol play"><div class="th"><span class="dot"></span>Priorize</div><div class="chips">${tierChips(cur,base,"play")}</div></div>
      <div class="tcol neu"><div class="th"><span class="dot"></span>Neutro</div><div class="chips">${tierChips(cur,base,"neu")}</div></div>
      <div class="tcol ban"><div class="th"><span class="dot"></span>Banir</div><div class="chips">${tierChips(cur,base,"ban")}</div></div>
    </div>
    <h2 class="sec">Mapa a mapa<span class="hint">ataque × defesa + top 3</span></h2>
    ${opsNote}
    <div class="maps">${cards}</div>`;
}

/* ---------- OPERADORES ---------- */
function opPanel(list, pl){
  const p=byName(pl);
  return (list||[]).map(o=>{
    const kd=o.kd!=null?` · ${fx(o.kd,2)}`:"", tag=o.tag?` · ${esc(o.tag)}`:"";
    return `<div class="oprow clk" data-op="${esc(o.name)}" onclick="openOpSheet(this.dataset.op)"><span class="nm">${esc(o.name)}${o.star?' <span class="star">★</span>':""}</span><span class="st"><b>${o.wr}%</b>${o.small?"°":""}${delta(o.wr,(p[o.name]||{}).wr,0)}${kd}${tag}</span></div>`;
  }).join("");
}
function renderOps(){
  const cur=active, base=baselineOf(cur)||{};
  document.getElementById("scr-ops").innerHTML = `
    <h2 class="sec">Onde investir<span class="hint">vs ${esc((baselineOf(active)||{}).season||"—")}</span></h2>
    <div class="ops">
      <div class="opcard"><h3><span class="tag def">DEFESA</span> Suas mains</h3>${opPanel(cur.operatorsDef,base.operatorsDef)}</div>
      <div class="opcard"><h3><span class="tag atk">ATAQUE</span> Suas mains</h3>${opPanel(cur.operatorsAtk,base.operatorsAtk)}</div>
      <div class="opcard"><h3><span class="tag cut">CORTE / REPENSE</span></h3>${opPanel(cur.operatorsCut,base.operatorsCut)}</div>
    </div>
    ${hardBreachCard(cur)}
    ${cur.opsAll?`<h2 class="sec">Todos os operadores<span class="hint">${cur.opsAll.length} jogados nesta season</span></h2>
    <div class="cbox" id="allops"></div>`:""}`;
  renderOpsTable();
}
let opsFilter="all", opsSort="r";
const OPS_COLS=[["r","Rounds"],["wr","Vitórias"],["kd","K/D"],["hs","HS%"],["fb","1º duelo"]];
function opVal(o,k){
  if(k==="wr") return o.r?o.w/o.r:-1;
  if(k==="kd") return o.k/Math.max(1,o.d);
  if(k==="hs") return o.k?o.hs/o.k:-1;
  if(k==="fb") return (o.fb+o.fd)?o.fb/(o.fb+o.fd):-1;
  return o.r;
}
function renderOpsTable(){
  const cur=active, el=document.getElementById("allops");
  if(!el||!cur.opsAll) return;
  const chips=[["all","Tudo"],["d","Defesa"],["a","Ataque"]]
    .map(([v,l])=>`<button class="fchip ${opsFilter===v?"on":""}" onclick="opsFilter='${v}';renderOpsTable()">${l}</button>`).join("");
  const th=OPS_COLS.map(([k,l])=>`<th class="${opsSort===k?"on":""}" style="cursor:pointer" onclick="opsSort='${k}';renderOpsTable()">${l}${opsSort===k?'<span class="ar"> ↓</span>':""}</th>`).join("");
  const rows=cur.opsAll
    .filter(o=>opsFilter==="all"||o.s===opsFilter)
    .slice().sort((a,b)=>{
      if(opsSort!=="r"){ const sa=a.r<8?1:0, sb=b.r<8?1:0; if(sa!==sb) return sa-sb; }
      return opVal(b,opsSort)-opVal(a,opsSort)||b.r-a.r;
    })
    .map(o=>{
      const kd=fx(o.k/Math.max(1,o.d),2);
      const hs=o.k?Math.round(100*o.hs/o.k)+"%":"—";
      const fb=(o.fb+o.fd)?`${o.fb} de ${o.fb+o.fd}`:"—";
      return `<tr class="${o.r<8?"dim":""}" data-op="${esc(o.n)}" onclick="openOpSheet(this.dataset.op)">
        <td>${esc(o.n)}${o.r<8?" °":""}<span class="tag sm ${o.s==="d"?"def":"atk"}">${o.s==="d"?"DEF":"ATK"}</span></td>
        <td>${o.r}</td><td><b>${pf(o.w,o.r)}%</b> <small>${o.w} de ${o.r}</small></td>
        <td>${kd}</td><td>${hs}</td><td>${fb}</td></tr>`;
    }).join("");
  el.innerHTML=`<div class="fchips">${chips}</div>
    <div class="otwrap"><table class="ctable optable"><tr><th>Operador</th>${th}</tr>${rows}</table></div>
    <div class="fsrc">° abaixo de 8 rounds: indicativo, não veredito (nas ordenações por vitória, K/D, HS% e 1º duelo, esses ficam no fim). 1º duelo = first bloods × first deaths do tracker. Toque num operador pra abrir a ficha.</div>`;
}
function hardBreachCard(cur){
  if(!cur.opsAll) return "";
  const got=HARD_BREACH.map(n=>cur.opsAll.find(o=>o.n===n)).filter(Boolean);
  if(!got.length) return "";
  const rows=HARD_BREACH.map(n=>{
    const o=cur.opsAll.find(x=>x.n===n);
    if(!o) return `<div class="oprow"><span class="nm" style="color:var(--muted)">${n}</span><span class="st">sem rounds nesta season</span></div>`;
    const kd=fx(o.k/Math.max(1,o.d),2);
    return `<div class="oprow clk" data-op="${esc(o.n)}" onclick="openOpSheet(this.dataset.op)"><span class="nm">${esc(o.n)}</span><span class="st"><b>${pf(o.w,o.r)}%</b>${o.r<8?"°":""} · ${o.w} de ${o.r} rds · K/D ${kd}</span></div>`;
  }).join("");
  const best=got.filter(o=>o.r>=15).sort((a,b)=>b.r-a.r)[0];
  const read=best
    ? `Sua opção com amostra real: <b>${esc(best.n)}</b> (${best.w} de ${best.r}, K/D ${fx(best.k/Math.max(1,best.d),2)}). Os outros quase não têm rounds — treine um segundo pra semana de ban.`
    : `Nenhum hard breach com amostra de verdade nesta season.`;
  return `<div class="opcard" style="margin-top:12px"><h3><span class="tag atk">ATAQUE</span> Hard breach — plano B</h3>${rows}
    <div class="fsrc" style="margin-top:8px">${read} O card do coach mostra o quanto rodar sem hard breach custa.</div></div>`;
}
function openOpSheet(name){
  const cur=active, o=(cur.opsAll||[]).find(x=>x.n===name);
  if(!o) return;
  const kd=fx(o.k/Math.max(1,o.d),2);
  const duel=(o.fb+o.fd)?`<b>${o.fb} de ${o.fb+o.fd}</b> (${pf(o.fb,o.fb+o.fd)}%)`:`— <small>não entra na 1ª troca</small>`;
  const stats=`<table class="ctable">
    <tr><td>Rounds</td><td><b>${o.r}</b> <small>em ${o.m} ${o.m===1?"partida":"partidas"}</small></td></tr>
    <tr><td>Rounds vencidos</td><td><b>${pf(o.w,o.r)}%</b> <small>${o.w} de ${o.r}</small></td></tr>
    <tr><td>Partidas vencidas</td><td><b>${pf(o.mw,o.m)}%</b> <small>${o.mw} de ${o.m}</small></td></tr>
    <tr><td>K/D</td><td><b>${kd}</b> <small>${o.k} × ${o.d} · ${o.a} assist.</small></td></tr>
    <tr><td>Abates na cabeça</td><td><b>${o.k?pf(o.hs,o.k)+"%":"—"}</b> <small>${o.hs} de ${o.k}</small></td></tr>
    <tr><td>1º duelo do round</td><td>${duel}</td></tr>
    <tr><td>Clutch</td><td><b>${o.cw}</b> ganhos · ${o.cl} perdidos</td></tr></table>`;
  const evo=SEASONS.map(s=>({s,e:(s.opsAll||[]).find(x=>x.n===name)})).filter(x=>x.e&&x.e.r>0);
  const evoHtml=evo.length>1?`<h3 style="margin:14px 0 8px">Season a season</h3><table class="ctable">${
    evo.map(({s,e})=>`<tr><td>${esc(s.season)}</td><td><b>${pf(e.w,e.r)}%</b> <small>${e.r} rds</small></td><td>K/D ${fx(e.k/Math.max(1,e.d),2)}</td></tr>`).join("")}</table>`:"";
  const mm=(cur.opsMaps||{})[name];
  const mapsHtml=mm&&mm.length?`<h3 style="margin:14px 0 8px">Por mapa</h3><table class="ctable">${
    mm.slice().sort((a,b)=>b[1]-a[1]).slice(0,4).map(r=>`<tr><td>${esc(r[0])}</td><td><b>${pf(r[2],r[1])}%</b> <small>${r[2]} de ${r[1]}</small></td><td>K/D ${fx(r[3]/Math.max(1,r[4]),2)}</td></tr>`).join("")}</table>`:"";
  const fr=((cur.coach||{}).opsRole||{})[name];
  const feedHtml=fr?`<h3 style="margin:14px 0 8px">O que o kill feed mostra</h3><table class="ctable">
    <tr><td>Vivo no fim do round</td><td><b>${pf(fr[2],fr[0])}%</b> <small>${fr[2]} de ${fr[0]}</small></td></tr>
    <tr><td>1ª morte do time é você</td><td><b>${pf(fr[3],fr[0])}%</b></td></tr>
    <tr><td>Rounds com kill sua na abertura</td><td><b>${pf(fr[4],fr[0])}%</b> <small>no fim: ${pf(fr[5],fr[0])}%</small></td></tr></table>
    <div class="fsrc">Kill feed desta season (${fr[0]} rounds); pode divergir 1–2% do tracker.</div>`:"";
  const why=((PLAYBOOK.operators||{})[name]||{}).why;
  openSheet(`<h3>${esc(name)} <span class="tag sm ${o.s==="d"?"def":"atk"}">${o.s==="d"?"DEFESA":"ATAQUE"}</span></h3>
    ${o.r<8?`<div class="fsrc" style="margin-bottom:10px">° amostra curta (${o.r} ${o.r===1?"round":"rounds"}) — leia como indicativo, não veredito.</div>`:""}
    ${stats}${evoHtml}${mapsHtml}${feedHtml}
    ${why?`<div class="fsrc" style="margin-top:10px">Função: ${esc(why)}</div>`:""}`);
}

/* ---------- EVOLUÇÃO ---------- */
function spark(vals, color, fmt){
  if(vals.length<2) return `<div style="color:var(--muted);font-size:13px">Só 1 season carregada — o gráfico aparece com 2+.</div>`;
  const w=560,h=96,pad=14;
  const mn=Math.min(...vals), mx=Math.max(...vals), rg=(mx-mn)||1;
  const X=i=>pad+i*(w-2*pad)/(vals.length-1), Y=v=>h-pad-(v-mn)/rg*(h-2*pad);
  const line=vals.map((v,i)=>`${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(" ");
  const dots=vals.map((v,i)=>`<circle cx="${X(i).toFixed(1)}" cy="${Y(v).toFixed(1)}" r="3.5" fill="${color}"/><text x="${X(i).toFixed(1)}" y="${(Y(v)-9).toFixed(1)}" fill="${color}" font-size="12" font-weight="700" text-anchor="middle">${fmt(v)}</text>`).join("");
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><polyline points="${line}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>${dots}</svg>`;
}
function renderEvo(){
  const chron = SEASONS.slice().sort((a,b)=>a.seasonOrder-b.seasonOrder); // antiga→nova
  const wrVals=chron.map(s=>s.kpis.winRate), kdVals=chron.map(s=>s.kpis.kd);
  const rows = chron.slice().reverse().map((s,idx,arr)=>{
    const older = chron[chron.indexOf(s)-1];
    const p=older?older.kpis:{};
    const rk=rankInfo(s.kpis.peakRP);
    return `<div class="evrow"><span class="sn">${esc(s.season)}<small>${esc(s.seasonLabel||"")}</small></span>
      <span class="cell"><span class="rkb2" style="background:${rk.color}22;color:${rk.color}">${rk.name}</span></span>
      <span class="cell"><b>${fx(s.kpis.winRate,1)}%</b>${delta(s.kpis.winRate,p.winRate,1)}</span>
      <span class="cell"><b>${fx(s.kpis.kd,2)}</b>${delta(s.kpis.kd,p.kd,2)}</span>
      <span class="cell"><b>${s.kpis.matches}</b></span></div>`;
  }).join("");
  document.getElementById("scr-evo").innerHTML = `
    <h2 class="sec">Evolução<span class="hint">season a season</span></h2>
    <div class="evo"><h3>Win rate %</h3>${spark(wrVals,"#34d399",v=>v.toFixed(0)+"%")}</div>
    <div class="evo"><h3>K/D</h3>${spark(kdVals,"#f4c20d",v=>fx(v,2))}</div>
    <div class="evo"><h3>Seasons</h3>
      <div class="evhead"><span class="sn">Season</span><span class="cell">Pico</span><span class="cell">Win</span><span class="cell">K/D</span><span class="cell">Partidas</span></div>
      ${rows}</div>`;
}

/* ---------- COACH ---------- */
const pf=(a,b)=>b?Math.round(100*a/b):0;
const nf=n=>n==null?"—":Number(n).toLocaleString('pt-BR');
const sg=v=>(v>0?"+":"")+v;
const HARD_BREACH=["Thermite","Hibana","Ace","Maverick"];
function rpPace(){                     // RP médio por vitória e por derrota na season ativa
  if(active.rpRate&&active.rpRate.n>=6) return active.rpRate;
  const ms=active.recentMatches||[], avg=a=>a.reduce((s,x)=>s+x,0)/a.length;
  const W=ms.filter(m=>m.w&&m.rp>0).map(m=>m.rp), L=ms.filter(m=>!m.w&&m.rp<0).map(m=>m.rp);
  return (W.length>=3&&L.length>=3)?{win:avg(W),loss:avg(L),n:W.length+L.length}:null;
}
function goalOf(){                     // meta do profile.json; sem ela, a próxima cor de rank
  const k=active.kpis, rp=(k.latestRP!=null?k.latestRP:k.peakRP);
  if(rp==null||rp>=4500) return null;
  const g=PLAYER.goal, mine=!!(g&&g.rp>rp);
  const target=mine?g.rp:[1000,1500,2000,2500,3000,3500,4000,4500].find(t=>t>rp);
  const r=rankInfo(target);
  return {rp,target,need:target-rp,mine,label:(mine&&g.label)?g.label:(r.tier||r.name),color:r.color,div:r.div,champ:r.champ};
}
function goalCard(){
  const g=goalOf(); if(!g) return "";
  const p=rpPace(), k=active.kpis;
  const wNow=(k.wins!=null&&k.losses!=null&&(k.wins+k.losses))?k.wins/(k.wins+k.losses):(k.winRate||0)/100;
  let body="";
  if(p&&p.win>0&&p.loss<0){
    const per=w=>p.win*w+p.loss*(1-w);
    const sc=[[wNow,`${Math.round(wNow*100)}% <small>(hoje)</small>`]];
    [.5,.55].forEach(w=>{ if(Math.abs(w-wNow)>=.02) sc.push([w,`${Math.round(w*100)}%`]); });
    sc.sort((a,b)=>a[0]-b[0]);
    const be=Math.round(-100*p.loss/(p.win-p.loss));
    const Wp=p.win, Lp=-p.loss, rnd=x=>Math.round(+x.toFixed(6));
    const kmax=n=>{let m=0; for(let i=0;i<=n;i++) if((n-i)*Wp-i*Lp>0) m=i; return m;};
    const rpf=v=>(v>0?"+":"")+rnd(v);
    const janela=`A cada 5 partidas você pode perder até <b>${kmax(5)}</b> e ainda subir: 2V-3D dá ${rpf(2*Wp-3*Lp)} RP e 3V-2D, ${rpf(3*Wp-2*Lp)} RP (em 4 partidas: até ${kmax(4)}).`;
    body=`<div class="cg-s" style="margin-top:10px">Seu ritmo nesta season: <b>+${Math.round(p.win)}</b> por vitória e <b>${Math.round(p.loss)}</b> por derrota (${p.n} partidas). Com ${be}% de vitórias você já não perde RP.</div>
      <div class="cg-s" style="margin-top:6px">${janela}</div>
      <table class="ctable"><tr><th>Vitórias</th><th>RP por partida</th><th>Partidas até ${esc(g.label)}</th></tr>
      ${sc.map(([w,l])=>{const x=per(w);return `<tr><td>${l}</td><td>${x>0?"+":""}${fx(x,1)}</td><td><b>${x>0.05?"~"+Math.ceil(g.need/x):"não sobe"}</b></td></tr>`;}).join("")}</table>
      <div class="fsrc">Cenário, não promessa: supõe que cada vitória e cada derrota continuem valendo a média desta season.</div>`;
  }
  return `<div class="cgoal"><div class="cg-top">${rankEmblem(g.color,g.div,g.champ,44)}<div>
      <div class="cg-l">${g.mine?"Sua meta":"Próximo rank"}</div>
      <div class="cg-v"><b style="color:${g.color}">${esc(g.label)}</b> · faltam <b>+${nf(g.need)} RP</b></div>
      <div class="cg-s">${nf(g.rp)} → ${nf(g.target)} RP</div></div></div>${body}</div>`;
}

/* chave, rótulo, unidade, casas, direção (1 = subir é bom · -1 = subir é ruim · 0 = estilo) */
const STYLE_ROWS=[
  ["roundWR","Rounds vencidos","%",0,1],
  ["atkRoundWR","Rounds vencidos no ataque","%",0,1],
  ["defRoundWR","Rounds vencidos na defesa","%",0,1],
  ["esr","1º duelo que você vence","%",0,1],
  ["openPct","Rounds em que você entra no 1º duelo","%",0,0],
  ["fdPct","Rounds em que a 1ª morte é a sua","%",0,0],
  ["clutchPct","Rounds em que você sobra sozinho","%",0,-1],
  ["clutchWin","Vence quando sobra sozinho","%",0,1],
  ["hs","Abates na cabeça","%",0,1],
  ["kpr","Abates por round","",2,1],
  ["multiPct","Rounds com 2+ abates seus","%",0,1]
];
function styleVal(s,k){
  if(!s) return null;
  if(k==="fdPct") return s.rounds?100*s.fd/s.rounds:null;
  if(k==="clutchWin") return (s.clutchW+s.clutchL)?100*s.clutchW/(s.clutchW+s.clutchL):null;
  return s[k]!=null?s[k]:null;
}
function deltaDir(c,p,dec,dir){        // a seta mostra o sentido; a cor diz se foi bom, ruim ou só estilo
  const h=delta(c,p,dec); if(!h||dir===1) return h;
  return h.replace(/class="d (up|dn)"/,(m,x)=>`class="d ${dir===0?"nt":(x==="up"?"dn":"up")}"`);
}
function styleTable(cur,base){
  const s=cur.style, b=base&&base.style;
  const fmt=(v,u,d)=>v==null?"—":fx(v,d)+u;
  const rows=STYLE_ROWS.map(([k,l,u,d,dir])=>{
    const v=styleVal(s,k), pv=styleVal(b,k);
    return `<tr><td>${l}</td><td><b>${fmt(v,u,d)}</b>${deltaDir(v,pv,d,dir)}</td>${b?`<td>${fmt(pv,u,d)}</td>`:""}</tr>`;
  }).join("");
  return `<div class="cbox"><table class="ctable"><tr><th></th><th>${esc(cur.season)}</th>${b?`<th>${esc(base.season)}</th>`:""}</tr>${rows}</table>
    <div class="fsrc">${nf(s.rounds)} rounds${b?` (${esc(base.season)}: ${nf(b.rounds)})`:""}. Verde = melhorou, vermelho = piorou, cinza = muda o estilo, não o resultado.</div></div>`;
}

function squadRows(q){
  const r=(l,a)=>a&&a[1]?`<tr><td>${l}</td><td><b>${pf(a[0],a[1])}%</b> <small>${a[0]} de ${a[1]}</small></td><td>${a[3]?fx(a[2]/a[3],2):"—"}</td><td>${sg(a[4])}</td></tr>`:"";
  return r("Sozinho",q.solo)+r("Com o squad",q.together);
}
function squadCard(cur,base){
  const q=cur.squad; if(!q) return "";
  const bq=base&&base.squad;
  const who=Object.entries(q.with||{}).sort((a,b)=>b[1]-a[1]).map(([s,n])=>`${esc(NAMES[s]||s)} ${n}`).join(" · ");
  let note="";
  [[q,cur],[bq,base]].forEach(([x,sn])=>{
    if(note||!x) return;
    const so=x.solo, tg=x.together;
    if(tg[1]>=10&&so[1]>=8&&so[3]&&tg[3]&&(tg[2]/tg[3])<(so[2]/so[3])-0.3)
      note=`Com o squad o seu K/D cai (${fx(tg[2]/tg[3],2)} × ${fx(so[2]/so[3],2)} sozinho, na ${esc(sn.season)}). O provável: a partida sobe pro nível deles.`;
  });
  const few=[q,bq].some(x=>x&&(x.solo[1]<15||x.together[1]<15));
  return `<div class="cbox"><table class="ctable"><tr><th></th><th>Vitórias</th><th>K/D</th><th>RP</th></tr>
      <tr><td colspan="4" class="csub">${esc(cur.season)} · ${q.n} partidas</td></tr>${squadRows(q)}
      ${bq?`<tr><td colspan="4" class="csub">${esc(base.season)} · últimas ${bq.n} partidas</td></tr>${squadRows(bq)}`:""}
    </table>
    ${note?`<div class="fread" style="margin-top:10px">${note}</div>`:""}
    <div class="fsrc">Squad = partida no mesmo minuto e no mesmo mapa de outro perfil daqui${who?` (nesta season: ${who})`:""}.${few?" Fila com menos de 15 partidas é indício, não prova.":""} Detalhe por amigo na aba Squad.</div></div>`;
}

function bars(rows){                   // [rótulo, %, texto, é você?]
  return `<div class="cmp">${rows.map(([l,v,t,me])=>`<div class="cmpr${me?" me":""}"><span class="cl">${l}</span><span class="cb"><i style="width:${Math.max(2,Math.min(100,v))}%"></i></span><span class="cv">${t}</span></div>`).join("")}</div>`;
}
function fcard(title,big,sub,inner,read,src){
  return `<div class="fcard"><h4>${title}</h4><div class="fbig">${big}</div><div class="fsub">${sub}</div>${inner||""}${read?`<div class="fread">${read}</div>`:""}${src?`<div class="fsrc">${src}</div>`:""}</div>`;
}
function coachCards(cur){
  const c=cur.coach, s=cur.style, K={};
  if(c&&c.lastAlive){
    const la=c.lastAlive, lr=c.lastAliveRef, me=pf(la.atk[0],la.atk[1]), ref=pf(lr.atk[0],lr.atk[1]);
    const fd=pf(c.firstDeath.atk[0],c.firstDeath.atk[1]), fdr=pf(c.firstDeathRef.atk[0],c.firstDeathRef.atk[1]);
    const md=pf(la.def[0],la.def[1]), rd=pf(lr.def[0],lr.def[1]), al=c.alone.atk, k=c.kills;
    let read = me-ref>=10
      ? `No ataque você fica pra trás: é o 1º do time a morrer em só <b>${fd}%</b> dos rounds (eles, ${fdr}%) e, quando sobra, encara <b>${String(al[2]).replace(".",",")} inimigos</b> em média. Sozinho no ataque, venceu <b>${al[0]} de ${al[1]}</b>.`
      : `No ataque você sobra sozinho perto do que acontece com eles.`;
    read += ` Na defesa: ${md}% (eles, ${rd}%)${Math.abs(md-rd)<8?", normal":""}.`;
    if(k&&k.alone) read += ` Dos seus ${nf(k.total)} abates, ${k.alone} saíram com você já sozinho; ${k.aloneLost} desses, em round perdido.`;
    K.lastAlive=(fcard("Último vivo no ataque",`${me}%`,"das vezes em que o seu time ficou com 1 vivo no ataque, esse 1 era você",
      bars([["Você",me,`${la.atk[0]} de ${la.atk[1]}`,1],["Bons jogadores*",ref,`${lr.atk[0]} de ${lr.atk[1]}`],["Acaso (1 em 5)",20,"20%"]]),
      read,`* ${esc(c.refLabel)}. Base: ${c.matches} partidas, ${nf(c.rounds)} rounds.`));
  }
  if(c&&c.killTiming&&c.killTiming.meEarly[1]>=100){
    const kt=c.killTiming, meE=pf(kt.meEarly[0],kt.meEarly[1]), rE=pf(kt.refEarly[0],kt.refEarly[1]);
    const meL=pf(kt.meLate[0],kt.meLate[1]), rL=pf(kt.refLate[0],kt.refLate[1]);
    const read = rE-meE>=8
      ? `Você quase não participa da abertura: só <b>${meE}%</b> das suas kills são um dos 2 primeiros abates do round (eles, ${rE}%). Chegue junto do entry que a abertura vira sua.`
      : `A distribuição é parecida com a dos bons jogadores (abertura ${meE}% × ${rE}%, fim ${meL}% × ${rL}%). Ou seja: o "último vivo" não vem da hora das suas kills — vem de onde você está quando os outros caem.`;
    K.killTiming=(fcard("Quando suas kills acontecem",`${meE}% · ${meL}%`,"das suas kills abrem o round (2 primeiros abates) · fecham o round (2 últimos)",
      bars([["Você — abertura",meE,`${kt.meEarly[0]} de ${kt.meEarly[1]}`,1],["Bons — abertura",rE,`${kt.refEarly[0]} de ${nf(kt.refEarly[1])}`],
            ["Você — fim",meL,`${kt.meLate[0]} de ${kt.meLate[1]}`,1],["Bons — fim",rL,`${kt.refLate[0]} de ${nf(kt.refLate[1])}`]]),
      read,`* ${esc(c.refLabel)}.`));
  }
  if(c&&c.states&&(c.states["4v4"]||[0,0])[1]>=10&&(c.states["4v5"]||[0,0])[1]>=10){
    const st=c.states, a44=st["4v4"], a45=st["4v5"];
    const L=[["5v4","Vocês na frente (5v4)"],["4v4","Troca feita (4v4)"],["4v5","Um a menos (4v5)"],["5v3","Dois na frente (5v3)"],["3v5","Dois a menos (3v5)"],["3v3","3v3"],["2v2","2v2"]];
    const rows=L.filter(([k])=>(st[k]||[0,0])[1]>=8).map(([k,l])=>{const[w,n]=st[k];return `<tr><td>${l}</td><td><b>${pf(w,n)}%</b></td><td><small>${w} de ${n}</small></td></tr>`;}).join("");
    K.states=(fcard("O round pelo placar de vivos",`${pf(a44[0],a44[1])}% × ${pf(a45[0],a45[1])}%`,"round vencido com a troca feita (4v4) × um a menos (4v5)",
      `<table class="ctable"><tr><th>Situação</th><th>Vencidos</th><th></th></tr>${rows}</table>`,
      `Perder o 1º duelo não fecha o round se vier a troca: em 4v4 vocês vencem <b>${pf(a44[0],a44[1])}%</b>; sem a troca (4v5), <b>${pf(a45[0],a45[1])}%</b>. É o número por trás do "morreu um, troque na hora".`,
      "Primeira vez que o round chega em cada placar, pelo kill feed."));
  }
  if(s&&s.clutchBy){
    const cb=s.clutchBy, tot=cb.reduce((a,x)=>a+x[1],0), w=cb.reduce((a,x)=>a+x[0],0), hard=cb[3][1]+cb[4][1];
    if(tot) K.clutch=(fcard("Quando você sobra sozinho",`${w} de ${tot}`,"situações de 1 contra X que você venceu nesta season",
      bars(cb.map((x,i)=>[`1 contra ${i+1}`,pf(x[0],x[1]),`${x[0]} de ${x[1]}`,0])),
      hard?`<b>${hard}</b> das ${tot} foram 1 contra 4 ou 5. Ali quase ninguém vence: o ganho está em não chegar lá.`:"",
      "Contagem do r6.tracker.network."));
  }
  if(c&&c.hardBreach&&c.hardBreach.with[1]>=10&&c.hardBreach.without[1]>=10){
    const hb=c.hardBreach, a=pf(hb.with[0],hb.with[1]), b=pf(hb.without[0],hb.without[1]);
    const rows=[["Com hard breach",a,`${hb.with[0]} de ${hb.with[1]}`],["Sem hard breach",b,`${hb.without[0]} de ${hb.without[1]}`]];
    if(hb.self&&hb.self[1]) rows.push(["Você de breacher",pf(hb.self[0],hb.self[1]),`${hb.self[0]} de ${hb.self[1]}`,1]);
    K.hardBreach=(fcard("Hard breach no ataque",`${a}% × ${b}%`,"rounds de ataque vencidos com e sem Thermite, Hibana, Ace ou Maverick no seu time",
      bars(rows),`Em <b>${hb.without[1]} dos ${hb.with[1]+hb.without[1]}</b> rounds de ataque ninguém do seu time levou.`,""));
  }
  if(c&&c.score&&c.score.led20[1]>=8&&c.score.trail02[1]>=8){
    const sc=c.score, otShare=pf(sc.ot[1],c.matches);
    const row=(l,a,v)=>`<tr><td>${l}</td><td><b>${pf(a[0],a[1])}%</b></td><td><small>${a[0]} de ${a[1]} ${v}</small></td></tr>`;
    K.score=(fcard("O placar da partida",`${pf(sc.led20[0],sc.led20[1])}% × ${pf(sc.trail02[0],sc.trail02[1])}%`,"partidas fechadas quando você abre 2-0 × viradas quando leva 0-2",
      `<table class="ctable"><tr><th>Situação</th><th></th><th></th></tr>
        ${row("Abriu 2-0",sc.led20,"fechadas")}${row("Levou 0-2",sc.trail02,"viradas")}
        ${sc.ot[1]?row("Foi pro overtime (3-3)",sc.ot,"ganhas"):""}${sc.otRounds[1]?row("Rounds de overtime",sc.otRounds,"vencidos"):""}</table>`,
      `Quem abre 2-0 quase leva: você fechou <b>${sc.led20[0]} de ${sc.led20[1]}</b> e virou só <b>${sc.trail02[0]} de ${sc.trail02[1]}</b> — os dois primeiros rounds valem a partida, jogue eles a sério desde o pick.${otShare>=25?` E <b>${otShare}%</b> das suas partidas foram pro overtime: round 7 é rotina, não exceção.`:""}`,
      `${c.matches} partidas com kill feed.`));
  }
  if(c&&c.teams){
    const t=c.teams, d=t.matesRP-t.enemiesRP, avg=Math.round((4*t.matesRP+t.meRP)/5);
    const big=Math.abs(d)<=50?"Mesmo nível":(d<0?"Um pouco abaixo":"Um pouco acima");
    const atk=pf(c.sideRounds.atk[0],c.sideRounds.atk[1]), def=pf(c.sideRounds.def[0],c.sideRounds.def[1]);
    K.teams=(fcard("Seus times são mais fracos?",big,"seu time × time inimigo, no começo de cada partida",
      `<table class="ctable"><tr><th></th><th>Colegas</th><th>Inimigos</th></tr>
        <tr><td>RP médio</td><td><b>${nf(t.matesRP)}</b></td><td><b>${nf(t.enemiesRP)}</b></td></tr>
        <tr><td>K/D</td><td><b>${fx(t.matesKD,2)}</b></td><td><b>${fx(t.enemiesKD,2)}</b></td></tr>
        <tr><td>Abates <small>(time todo)</small></td><td><b>${nf(t.teamKills)}</b></td><td><b>${nf(t.enemyKills)}</b></td></tr></table>`,
      `Você entra com <b>${nf(t.meRP)}</b> RP; com você, o time tem média de <b>${nf(avg)}</b>. O K/D dos colegas fica abaixo do inimigo porque o seu entra na mesma conta: os dois times matam quase o mesmo.${def-atk>=5?` Onde o round escapa é no ataque: <b>${atk}%</b> de rounds vencidos, contra ${def}% na defesa.`:""}`,
      "Colegas = os outros 4 do seu time, sem você. RP de antes da partida."));
  }
  if(c&&c.pressure&&c.pressure.mine[1]>=15&&c.pressure.theirs[1]>=15){
    const a=c.pressure.mine, b=c.pressure.theirs;
    const pa=pf(a[0],a[1]), pb=pf(b[0],b[1]);
    const lead=Math.abs(pa-pb)<=6
      ? `Fechar e sobreviver valem quase o mesmo pra você (~${Math.round((pa+pb)/20)} em 10).`
      : pa>pb ? `Você fecha melhor (${pa}%) do que segura (${pb}%).` : `Você segura melhor (${pb}%) do que fecha (${pa}%).`;
    K.pressure=fcard("Sob pressão",`${pf(a[0],a[1])}% × ${pf(b[0],b[1])}%`,"rounds fechados com match point seu × segurados com match point deles",
      `<table class="ctable"><tr><th>Situação</th><th>Vencidos</th><th></th></tr>
        <tr><td>Match point seu</td><td><b>${pf(a[0],a[1])}%</b></td><td><small>${a[0]} de ${a[1]}</small></td></tr>
        <tr><td>Match point deles</td><td><b>${pf(b[0],b[1])}%</b></td><td><small>${b[0]} de ${b[1]}</small></td></tr></table>`,
      `${lead} Com match point seu, jogue o round mais simples do dia: utilidade toda, zero herói — é o round que time nervoso joga pior.`,
      "Match point = um time com 3 rounds a favor e o outro com até 2 (no overtime, com 4).");
  }
  if(c&&c.trades&&c.trades.mateDeaths>0&&c.trades.myDeaths>0){
    const t=c.trades, me=pf(t.byMe,t.mateDeaths), mates=pf(t.byMe+t.byOthers,t.mateDeaths), per=Math.round(100*t.byOthers/t.mateDeaths/3), mt=pf(t.meTraded,t.myDeaths);
    const quem=Math.abs(me-per)<=2?"como um colega médio":me>per?"mais que um colega médio":"menos que um colega médio";
    let read=`Você troca ${quem} (${me}% das mortes deles; um time de 4 troca ~${per}% por cabeça).`;
    if(mt<mates) read+=` O problema é a distância: os colegas são trocados em ${mates}% das mortes e você em só ${mt}% — você morre longe. Ande a uma sala do entry: a troca dele é sua, e a sua é dele.`;
    K.trades=fcard("Trocas",`${me}% × ${mt}%`,"mortes de colegas que você trocou × suas mortes que o time trocou",
      `<table class="ctable"><tr><th></th><th>Mortes</th><th>Trocadas</th></tr>
        <tr><td>Colegas</td><td><b>${nf(t.mateDeaths)}</b></td><td>você ${t.byMe} · outros ${t.byOthers}</td></tr>
        <tr><td>Você</td><td><b>${nf(t.myDeaths)}</b></td><td>${t.meTraded}</td></tr></table>`,
      read,"Troca = quem matou cai nos 2 abates seguintes do round.");
  }
  if(c&&c.postClutch&&c.postClutch.afterLost[1]>=20){
    const pc=c.postClutch, l=pf(pc.afterLost[0],pc.afterLost[1]), an=pf(pc.afterAnyLost[0],pc.afterAnyLost[1]);
    K.postClutch=fcard("O round depois do clutch",`${l}%`,"round seguinte vencido depois de você perder um clutch",
      bars([["Depois de clutch perdido",l,`${pc.afterLost[0]} de ${pc.afterLost[1]}`,1],
            ["Depois de round perdido comum",an,`${pc.afterAnyLost[0]} de ${pc.afterAnyLost[1]}`],
            ["Depois de clutch vencido",pf(pc.afterWon[0],pc.afterWon[1]),`${pc.afterWon[0]} de ${pc.afterWon[1]}`]]),
      l<an
        ? `Depois que você sobra sozinho e perde, o time vence o seguinte ${l}% — abaixo dos ${an}% de um round perdido comum. Meio round de pedágio: respira no próximo, não force entrada pra compensar.`
        : `Depois que você sobra sozinho e perde, o time vence o seguinte ${l}% — igual ou acima dos ${an}% de um round perdido comum: sem pedágio visível.`,
      "Clutch = você é o último vivo do seu time no round.");
  }
  if(c&&c.noKill&&c.noKill.died[1]>=30){
    const nk=c.noKill, al=pf(nk.alive[0],nk.alive[1]), di=pf(nk.died[0],nk.died[1]), dk=pf(nk.diedWithKill[0],nk.diedWithKill[1]);
    const share=pf(nk.alive[1]+nk.died[1],c.rounds);
    const row=(l,a)=>`<tr><td>${l}</td><td><b>${pf(a[0],a[1])}%</b></td><td><small>${a[0]} de ${a[1]}</small></td></tr>`;
    K.noKill=fcard("Seu round sem abate",`${al}% × ${di}%`,"rounds com 0 abate seu: vencidos quando você fica vivo × quando você morre",
      `<table class="ctable"><tr><th>Situação</th><th>Vencidos</th><th></th></tr>${row("0 abate, vivo no fim",nk.alive)}${row("0 abate, morto",nk.died)}${row("Morto, mesmo levando 1+",nk.diedWithKill)}</table>`,
      `${share>=40&&share<=55?"Quase metade dos seus rounds termina":`Em ${share}% dos seus rounds você termina`} sem abate seu — e tudo bem: vivo, ${al}% viram vitória. O round não pede seu frag, pede você vivo; morrer ${Math.abs(dk-di)<=8?"custa quase o mesmo":"não custa o mesmo"} levando alguém junto (${dk}%) ou não (${di}%).`,
      `Vivo no fim e vitória andam juntos por natureza (defesa que segura o relógio termina viva) — leia como "morte barata custa round", não como "esconder-se vence".`);
  }
  if(c&&c.rival&&c.rival.with[1]>=8){
    const a=c.rival.with, b=c.rival.without, tot=a[1]+b[1];
    K.rival=fcard(`O duelo repetido <span class="exp">experimental</span>`,`${a[0]} de ${a[1]}`,"partidas vencidas quando um mesmo inimigo te matou 3+ vezes",
      bars([["Com rival",pf(a[0],a[1]),`${a[0]} de ${a[1]}`,1],["Sem rival",pf(b[0],b[1]),`${b[0]} de ${b[1]}`]]),
      `Em ${a[1]} das ${tot} partidas alguém te matou 3+ vezes — você venceu ${a[0]}. Amostra curta e em ranked o adversário muda a cada partida (por isso o selo experimental); o uso é ao vivo: perdeu o MESMO duelo duas vezes, troque a rota — não volte pro mesmo ângulo.`,
      "");
  }
  // ordem = o que se decide DURANTE o jogo primeiro; contexto e perfil depois
  return ["states","pressure","lastAlive","hardBreach","trades","killTiming","postClutch","noKill","clutch","rival","score","teams"]
    .map(k=>K[k]||"").join("");
}
function trendBlock(cur){
  const t=cur.coach&&cur.coach.trend;
  if(!t||t.last.n<10) return "";
  const L=t.last, R=t.rest;
  const d1=x=>x.toFixed(1).replace(".",","), d2=x=>x.toFixed(2).replace(".",","), sg1=x=>(x>0?"+":"")+d1(x);
  const eL=L.esr[1]?pf(L.esr[0],L.esr[1]):null, eR=R.esr[1]?pf(R.esr[0],R.esr[1]):null;
  let read=L.rp>R.rp
    ? `As últimas ${L.n} são seu melhor trecho da season: ${sg1(L.rp)} de RP por partida contra ${sg1(R.rp)} antes.`
    : `As últimas ${L.n} renderam ${sg1(L.rp)} de RP por partida contra ${sg1(R.rp)} antes.`;
  if(eL!=null&&eR!=null&&eL<eR){
    read+=` O 1º duelo caiu (${eL}% × ${eR}%)`;
    read+=(L.esr[1]/L.n<R.esr[1]/R.n)
      ? " — você está ganhando mais entrando menos no duelo de abertura, que é exatamente o plano."
      : ".";
  }
  return `<h2 class="sec">Tendência<span class="hint">últimas ${L.n} × o resto da season</span></h2>
    <div class="cbox"><table class="ctable"><tr><th></th><th>Últimas ${L.n}</th><th>Antes (${R.n})</th></tr>
      <tr><td>Vitórias</td><td><b>${pf(L.w,L.n)}%</b> <small>${L.w} de ${L.n}</small></td><td>${pf(R.w,R.n)}% <small>${R.w} de ${R.n}</small></td></tr>
      <tr><td>K/D</td><td><b>${d2(L.kd)}</b></td><td>${d2(R.kd)}</td></tr>
      ${eL!=null?`<tr><td>1º duelo vencido</td><td><b>${eL}%</b> <small>${L.esr[0]} de ${L.esr[1]}</small></td><td>${eR!=null?eR+"%":"—"} <small>${R.esr[0]} de ${R.esr[1]}</small></td></tr>`:""}
      <tr><td>RP por partida</td><td><b>${sg1(L.rp)}</b></td><td>${sg1(R.rp)}</td></tr></table>
      <div class="fread" style="margin-top:10px">${read}</div>
      <div class="fsrc">Últimas ${L.n} partidas da season × as outras ${R.n}. K/D e 1º duelo vêm do kill feed.</div></div>`;
}
function tiltCard(cur){
  const t=cur.tilt; if(!t) return "";
  const [lw,ln]=t.afterLoss, [ww,wn]=t.afterWin, l=pf(lw,ln), w=pf(ww,wn);
  let big, read;
  if(ln<8){ big="Pouca sequência"; read="Poucas partidas seguidas na mesma sessão pra medir."; }
  else if(l>=45){ big="Sem sinal de tilt"; read=`Depois de uma derrota você venceu a seguinte <b>${lw} de ${ln}</b> (${l}%); depois de uma vitória, ${ww} de ${wn} (${w}%).`; }
  else { big="Cuidado com a sequência"; read=`Depois de uma derrota você venceu a seguinte só <b>${lw} de ${ln}</b> (${l}%); depois de uma vitória, ${ww} de ${wn} (${w}%).`; }
  let bg="";
  const G=t.byGame;
  if(G&&G.some(x=>x[1]>=5)){
    const lbl=["1ª da sessão","2ª","3ª","4ª em diante"];
    bg=`<div class="fsub" style="margin-top:12px"><b style="color:var(--txt)">Vitórias pela posição na sessão</b></div>
      <table class="ctable">${G.map((x,i)=>x[1]?`<tr><td>${lbl[i]}</td><td><b>${pf(x[0],x[1])}%</b></td><td><small>${x[0]} de ${x[1]}</small></td></tr>`:"").join("")}</table>`;
    const g1=G[0], mid=[G[1][0]+G[2][0], G[1][1]+G[2][1]];
    if(g1[1]>=10&&mid[1]>=10&&pf(mid[0],mid[1])-pf(g1[0],g1[1])>=12)
      read+=` A <b>1ª partida da sessão</b> é a sua pior: ${g1[0]} de ${g1[1]} (${pf(g1[0],g1[1])}%), contra ${pf(mid[0],mid[1])}% na 2ª e 3ª — você entra frio.`;
    const pre=[G[0][0]+mid[0], G[0][1]+mid[1]];
    if(G[3][1]>=8&&pf(pre[0],pre[1])-pf(G[3][0],G[3][1])>=12)
      read+=` Da <b>4ª em diante</b> cai pra ${pf(G[3][0],G[3][1])}% — sessão longa não paga.`;
  }
  return fcard("Depois de perder",big,"a partida seguinte, na mesma sessão",
    bars([["Depois de derrota",l,`${lw} de ${ln}`,1],["Depois de vitória",w,`${ww} de ${wn}`]])+bg,
    read,`Sessão = partidas com menos de 75 min entre uma e outra. ${t.sessions} sessões, ${t.matches} partidas.`);
}
function coachRules(cur,base){
  const c=cur.coach, s=cur.style, R=[];
  const rule=(ico,cls,b,t)=>`<div class="pi"><div class="ico ${cls}">${ico}</div><div><b>${b}</b> <span>${t}</span></div></div>`;
  if(c&&c.lastAlive){
    const la=c.lastAlive.atk, lr=c.lastAliveRef.atk, me=pf(la[0],la[1]), ref=pf(lr[0],lr[1]), al=c.alone.atk;
    if(me-ref>=10) R.push(rule("⚔","atk","No ataque, seja o 2º a entrar, não o 5º.",
      `Ande a uma sala do seu entry: se ele cair, você troca na hora. Hoje, quando o time fica com 1 vivo no ataque, é você ${me}% das vezes (o normal é 20%), e sozinho você venceu ${al[0]} de ${al[1]}.`));
  }
  if(s&&s.esr>=60&&(s.fb+s.fd)>=20){
    const o=c&&c.opening;
    R.push(rule("🎯","play","Confie no seu 1º duelo.",
      `Quando você entra nele, vence ${Math.round(s.esr)}% (${s.fb} de ${s.fb+s.fd}).${o?` Round que começa com abate do seu time vira vitória ${pf(o.kill[0],o.kill[1])}% das vezes; com morte, ${pf(o.death[0],o.death[1])}%.`:""}`));
  }
  if(c&&c.hardBreach){
    const hb=c.hardBreach, a=pf(hb.with[0],hb.with[1]), b=pf(hb.without[0],hb.without[1]);
    if(hb.with[1]>=10&&hb.without[1]>=10&&a-b>=8){
      const mine=(cur.operatorsAtk||[]).concat(cur.operatorsCut||[]).filter(o=>HARD_BREACH.includes(o.name)).sort((x,y)=>(y.rounds||0)-(x.rounds||0))[0];
      R.push(rule("🧨","atk",`Sem hard breach no time? Pegue ${esc(mine?mine.name:"Thermite")}.`,
        `Com hard breach o time vence ${a}% dos rounds de ataque; sem, ${b}%. Em ${hb.without[1]} de ${hb.with[1]+hb.without[1]} ninguém levou.${mine?` Seu ${esc(mine.name)}: ${mine.wr}% em ${mine.rounds} rounds${mine.kd!=null?", K/D "+fx(mine.kd,2):""}.`:""}`));
    }
  }
  const bans=(cur.maps||[]).filter(m=>m.matches>=4&&m.seasonWR<40).sort((x,y)=>x.seasonWR-y.seasonWR);
  if(bans.length){ const m=bans[0]; R.push(rule("⛔","ban",`Bane ${esc(m.name)}.`,`${m.seasonWR.toFixed(0)}% em ${m.matches} partidas.${m.note?" "+esc(m.note):""}`)); }
  const t=cur.tilt;
  if(t&&t.afterLoss[1]>=8&&pf(t.afterLoss[0],t.afterLoss[1])<45)
    R.push(rule("🧠","ban","Perdeu duas seguidas? Pausa antes da próxima.",`Depois de uma derrota você venceu a seguinte só ${t.afterLoss[0]} de ${t.afterLoss[1]}.`));
  if(t&&t.byGame){
    const g1=t.byGame[0], mid=[t.byGame[1][0]+t.byGame[2][0], t.byGame[1][1]+t.byGame[2][1]];
    if(g1[1]>=10&&mid[1]>=10&&pf(mid[0],mid[1])-pf(g1[0],g1[1])>=12)
      R.push(rule("🔥","play","Aqueça antes da primeira ranqueada.",
        `Sua 1ª partida da sessão é a pior: ${g1[0]} de ${g1[1]} (${pf(g1[0],g1[1])}%), contra ${pf(mid[0],mid[1])}% na 2ª e 3ª. Estande de tiro ou uma casual antes de dar queue.`));
  }
  const sq=[[cur.squad,cur],[base&&base.squad,base]].find(([q])=>q&&q.solo[1]>=10&&q.together[1]>=10);
  if(sq){
    const [q,sn]=sq, a=pf(q.together[0],q.together[1]), b=pf(q.solo[0],q.solo[1]);
    if(a-b>=8) R.push(rule("👥","play","Jogue com o squad quando der.",`Na ${esc(sn.season)}: ${q.together[0]} de ${q.together[1]} juntos (${a}%); sozinho, ${q.solo[0]} de ${q.solo[1]} (${b}%).`));
  }
  return R.length?`<div class="plan">${R.join("")}</div>`
    :`<div class="banner" style="margin-top:0">Nenhuma regra passou no corte dos seus números ainda. Mapas e operadores estão no Plano de jogo do Início.</div>`;
}
function renderCoach(){
  const cur=active, base=baselineOf(cur), latest=cur===SEASONS[0];
  const el=document.getElementById("scr-coach");
  if(!cur.style){
    el.innerHTML=`<div class="banner">🧭 O coach usa dados que só existem a partir da Y11S2. Troque a season no seletor do topo.</div>`;
    return;
  }
  el.innerHTML=`
    ${latest?`<h2 class="sec" style="margin-top:4px">Plano pra próxima sessão<span class="hint">tirado dos seus números</span></h2>${coachRules(cur,base)}
      <h2 class="sec">Meta</h2>${goalCard()}`
      :`<div class="banner" style="margin:0 0 6px">📅 Você está vendo a <b>${esc(cur.season)}</b>, já fechada. Meta e plano valem só pra season atual.</div>`}
    <h2 class="sec">O que os rounds mostram<span class="hint">${esc(cur.season)}</span></h2>
    ${cur.coach?"":`<div class="banner" style="margin:0 0 12px">🔎 O diagnóstico round a round (quem fica por último, hard breach, nível dos times) ainda não foi coletado ${latest?"pra este perfil":"pra esta season"}.</div>`}
    <div class="fcards">${coachCards(cur)}</div>
    ${trendBlock(cur)}
    ${cur.squad?`<h2 class="sec">Fila<span class="hint">sozinho × com o squad</span></h2>${squadCard(cur,base)}`:""}
    <h2 class="sec">Seu estilo em números<span class="hint">${base&&base.style?"vs "+esc(base.season):esc(cur.season)}</span></h2>${styleTable(cur,base)}
    ${cur.tilt?`<h2 class="sec">Sequência</h2>${tiltCard(cur)}`:""}`;
}

/* ---------- SQUAD ---------- */
const SQUAD_AVISO=`👥 Amostra pequena vira indício, não veredito — vocês jogaram pouco juntos nesta season. Squad = partida no mesmo minuto e mapa de outro perfil daqui; amigo de fora do app conta como "sozinho".`;
function squadTable(sn){
  const q=sn.squad;
  const row=(l,a)=>a&&a[1]?`<tr><td>${l}</td><td><b>${pf(a[0],a[1])}%</b></td><td><small>${a[0]} de ${a[1]}</small></td></tr>`:"";
  const friends=Object.entries(q.perFriend||{}).filter(([,a])=>a[1]>0).sort((a,b)=>b[1][1]-a[1][1])
    .map(([sl,a])=>row(esc(NAMES[sl]||sl),a)).join("");
  return `<div class="cbox"><table class="ctable"><tr><th>Fila</th><th>Vitórias</th><th>Partidas</th></tr>
    ${row("Sozinho",q.solo)}${friends}${row("Trio",q.trio)}</table></div>`;
}
function renderSquad(){
  const el=document.getElementById("scr-squad");
  const seas=SEASONS.filter(s=>s.squad);
  if(!seas.length){ el.innerHTML=`<div class="banner">👥 Sem dados de fila carregados.</div>`; return; }
  el.innerHTML=seas.map((s,i)=>`<h2 class="sec"${i?"":' style="margin-top:4px"'}>${esc(s.season)}<span class="hint">${esc(s.seasonLabel||"")} · ${s.squad.n} partidas</span></h2>${squadTable(s)}${i===0?`<div class="banner">${SQUAD_AVISO}</div>`:""}`).join("");
}

/* ---------- SELETOR / SHELL ---------- */
const TABS=[
  {id:"inicio",label:"Início",icon:'<svg viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg>'},
  {id:"coach",label:"Coach",icon:'<svg viewBox="0 0 24 24"><path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/></svg>'},
  {id:"mapas",label:"Mapas",icon:'<svg viewBox="0 0 24 24"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg>'},
  {id:"ops",label:"Operadores",icon:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>'},
  {id:"squad",label:"Squad",icon:'<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.2"/><path d="M3.5 19c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5"/><circle cx="17" cy="9" r="2.6"/><path d="M14.8 14.6c.7-.4 1.4-.6 2.2-.6 2.3 0 4.1 1.5 4.6 4.3"/></svg>'},
  {id:"evo",label:"Evolução",icon:'<svg viewBox="0 0 24 24"><path d="M4 19h16"/><path d="M5 15l4-5 4 3 6-8"/></svg>'}
];
function go(id){
  document.querySelectorAll(".screen").forEach(s=>s.classList.toggle("active", s.id==="scr-"+id));
  document.querySelectorAll("nav.bottom button,.desktabs button").forEach(b=>b.classList.toggle("on", b.dataset.t===id));
  window.scrollTo({top:0});
}
function renderAll(){ renderInicio(); renderCoach(); renderMapas(); renderOps(); renderSquad(); renderEvo(); syncHeader(); }
function syncHeader(){
  const rk=rankInfo(active.kpis.peakRP);
  document.getElementById("ss-season").textContent = active.season;
  const el=document.getElementById("ss-rank"); el.textContent=rk.name;
  el.style.background=rk.color+"22"; el.style.color=rk.color;
  document.getElementById("foot").textContent = `Base: ${active.basis||"—"} · Fonte: r6.tracker.network · ${SEASONS.length} season(s) carregada(s)`;
}
function openSeasons(){
  const rows = SEASONS.map(s=>{
    const rk=rankInfo(s.kpis.peakRP);
    return `<div class="srow ${s===active?'on':''}" data-so="${s.seasonOrder}">
      <div><div class="sname">${esc(s.season)} · ${esc(s.seasonLabel||"")}</div>
      <div class="smeta">${fx(s.kpis.winRate,1)}% vitórias · K/D ${fx(s.kpis.kd,2)} · ${s.kpis.matches} partidas</div></div>
      <span class="srk" style="background:${rk.color}22;color:${rk.color}">${rk.name}</span></div>`;
  }).join("");
  openSheet(`<h3>Escolher season</h3>${rows}`);
  document.querySelectorAll("#sheet .srow").forEach(r=>r.onclick=()=>{
    active = seasonMap[+r.dataset.so]; renderAll(); closeSheet();
  });
}
function openHelp(){
  openSheet(`<h3>Como ler o SIEGE·LAB</h3>
    <div class="legrow"><b style="color:var(--play)">▲</b> subiu vs a season anterior (no computador, passe o mouse na seta: antes → agora)</div>
    <div class="legrow"><b style="color:var(--ban)">▼</b> caiu vs a season anterior</div>
    <div class="legrow"><b style="color:#8b919c">=</b> estável</div>
    <div class="legrow"><b>°</b> amostra pequena — indicativo</div>
    <div class="legrow"><b style="color:var(--def)">■</b> defesa · <b style="color:var(--atk)">■</b> ataque</div>
    <div class="legrow"><b style="color:var(--gold)">%</b> verde ≥55 · amarelo 50–54 · vermelho &lt;50</div>
    <div class="legrow"><b>🗺</b> Mapas: priorize = win% ≥55 · neutro 40–54 · banir &lt;40 (conta só a season escolhida)</div>
    <div class="legrow"><b>⇅</b> troque a season pelo seletor no topo pra comparar épocas</div>
    <div class="legrow"><b style="color:#9aa3ad">▲</b> cinza no Coach: mudou o estilo, não o resultado (nem bom nem ruim)</div>
    <div class="legrow"><b>💡</b> Coach: o plano pra próxima sessão, sua meta e o que os rounds mostram — os cards de cima são os que valem olhar durante o jogo</div>
    <div class="legrow"><b>🎖</b> Operadores: toque em qualquer operador (mains, hard breach ou tabela) pra abrir a ficha completa</div>
    <div class="legrow"><b>👥</b> Squad: seu resultado sozinho × com cada amigo daqui</div>`);
}
function openShare(){
  const k=active.kpis, curRP=(k.latestRP!=null?k.latestRP:k.peakRP), rk=rankInfo(curRP);
  const rm=active.recentMatches||[]; const w=rm.filter(m=>m.w).length, l=rm.length-w;
  const card=`<div class="sharecard">
    <div class="scbrand">SIEGE<span>·</span>LAB</div>
    <div class="scemb">${rankEmblem(rk.color,rk.div,rk.champ,90)}</div>
    <div class="scname">${esc(PLAYER.name)}</div>
    <div class="scrank" style="color:${rk.color}">${rk.name} · ${curRP.toLocaleString('pt-BR')} RP</div>
    <div class="scstats">
      <div><b>${k.winRate.toFixed(0)}%</b><span>vitórias</span></div>
      <div><b>${fx(k.kd,2)}</b><span>K/D</span></div>
      ${rm.length?`<div><b>${w}-${l}</b><span>últimas</span></div>`:""}
    </div>
    <div class="scfoot">${esc(active.season)} · thebsilva.github.io/siege-lab</div>
  </div>`;
  openSheet(`<h3>Compartilhar</h3>${card}
    <div class="shint">Tire um print do card e mande no grupo 👊</div>
    ${navigator.share?`<button class="btn-share" id="doshare">Compartilhar o link</button>`:`<button class="btn-share" id="docopy">Copiar o link</button>`}`);
  const s=document.getElementById("doshare"); if(s) s.onclick=()=>navigator.share({title:"SIEGE·LAB — "+PLAYER.name,text:"Minha análise de R6 no SIEGE·LAB",url:location.href}).catch(()=>{});
  const c=document.getElementById("docopy"); if(c) c.onclick=()=>{ if(navigator.clipboard) navigator.clipboard.writeText(location.href); c.textContent="Link copiado ✓"; };
}
const bg=document.getElementById("sheetbg"), sh=document.getElementById("sheet");
function openSheet(html){ sh.innerHTML='<div class="grab"></div>'+html; bg.classList.add("open"); sh.classList.add("open"); }
function closeSheet(){ bg.classList.remove("open"); sh.classList.remove("open"); }

function shell(){
  document.getElementById("bottomnav").innerHTML = TABS.map(t=>`<button data-t="${t.id}" onclick="go('${t.id}')">${t.icon}${t.label}</button>`).join("");
  document.getElementById("desktabs").innerHTML = TABS.map(t=>`<button data-t="${t.id}" onclick="go('${t.id}')">${t.label}</button>`).join("");
  document.getElementById("seasonsel").onclick=openSeasons;
  document.getElementById("helpbtn").onclick=openHelp;
  document.getElementById("sharebtn").onclick=openShare;
  document.getElementById("subline").textContent = PLAYER.name + " · Ranked";
  document.title = "SIEGE·LAB — " + PLAYER.name;
  bg.onclick=closeSheet;
}
shell(); renderAll(); go("inicio");
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
