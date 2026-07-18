#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIEGE·LAB — gera app.html (produto multi-season) a partir de snapshots/*.json.
Cada snapshot = uma medição de UMA season. O app embute todos, oferece um
SELETOR DE SEASON, e compara a season escolhida com a anterior (deltas ▲▼),
derivando rank a partir do RP e o split ataque/defesa por mapa.

Uso:  python3 build.py
Nova medição/season: novo snapshots/AAAA-MM-DD_season.json (com seasonOrder) e rodar de novo.
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


def build_player(pdir):
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
    html = (TEMPLATE
            .replace("__DATA__", json.dumps(snaps, ensure_ascii=False))
            .replace("__PLAYER__", json.dumps(profile, ensure_ascii=False)))
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, profile.get("slug", "player") + ".html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    seasons = sorted({s.get("season") for s in snaps})
    print(f"OK -> docs/{os.path.basename(out)}  ({profile.get('name')}: {len(snaps)} season(s): {', '.join(seasons)})")
    latest = max(snaps, key=lambda s: s.get("seasonOrder", 0))
    k = latest.get("kpis", {})
    rk, color = rank_py(k.get("peakRP"))
    return {"slug": profile.get("slug"), "name": profile.get("name"), "season": latest.get("season"),
            "rank": rk, "color": color, "wr": k.get("winRate"), "kd": k.get("kd"), "matches": k.get("matches")}


def write_index(cards):
    import html as _h
    cells = "".join(
        f'''<a class="pcard" href="{_h.escape(c['slug'])}.html">
      <div class="pc-top"><span class="pc-name">{_h.escape(c['name'])}</span>
        <span class="pc-rank" style="background:{c['color']}22;color:{c['color']}">{_h.escape(c['rank'])}</span></div>
      <div class="pc-meta">{_h.escape(c['season'])} · {c['wr']:.1f}% vitórias · KD {c['kd']:.2f} · {c['matches']} partidas</div>
      <div class="pc-go">Abrir análise →</div></a>''' for c in cards)
    out = os.path.join(OUT_DIR, "index.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(INDEX_TEMPLATE.replace("__CARDS__", cells))
    print(f"OK -> docs/index.html  (landing com {len(cards)} jogador(es))")


def main():
    dirs = [d for d in sorted(glob.glob(os.path.join(PLAYERS_DIR, "*"))) if os.path.isdir(d)]
    if not dirs:
        raise SystemExit("Nenhum player em players/*/")
    cards = []
    for d in dirs:
        s = build_player(d)
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
<title>SIEGE·LAB</title>
<style>
  :root{--bg:#0a0b0e;--panel:#14161c;--panel2:#1a1d24;--line:#262a33;--txt:#e7e9ec;--muted:#8b919c;--gold:#f4c20d}
  *{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
  body{background:var(--bg);color:var(--txt);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
       -webkit-font-smoothing:antialiased;min-height:100vh;padding:32px 18px 60px}
  .wrap{max-width:640px;margin:0 auto}
  .top{display:flex;align-items:center;gap:13px;margin-bottom:6px}
  .logo{width:46px;height:46px;border-radius:11px;background:var(--gold);color:#111;display:grid;place-items:center;font-weight:900;font-size:26px;box-shadow:0 0 22px rgba(244,194,13,.32)}
  h1{font-size:22px;letter-spacing:.5px} h1 em{font-style:normal;color:var(--gold)}
  .sub{color:var(--muted);font-size:13px;margin:4px 0 26px}
  .pcard{display:block;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:14px;background:var(--panel);
         padding:16px 18px;margin-bottom:13px;transition:border-color .15s,transform .1s}
  .pcard:hover{border-color:var(--gold);transform:translateY(-1px)}
  .pc-top{display:flex;align-items:center;gap:10px}
  .pc-name{font-size:18px;font-weight:800}
  .pc-rank{margin-left:auto;font-size:11.5px;font-weight:800;padding:4px 10px;border-radius:999px}
  .pc-meta{color:var(--muted);font-size:12.5px;margin-top:6px;font-variant-numeric:tabular-nums}
  .pc-go{color:var(--gold);font-size:12.5px;font-weight:700;margin-top:11px}
  .foot{color:#5c626d;font-size:11px;text-align:center;margin-top:28px}
</style>
</head>
<body>
  <div class="wrap">
    <div class="top"><div class="logo">6</div><h1>SIEGE<em>·</em>LAB</h1></div>
    <div class="sub">Análise de ranqueada · R6 Siege · dados de r6.tracker.network</div>
    __CARDS__
    <div class="foot">Cada card abre o app completo do jogador — season, mapas, operadores e evolução.</div>
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
  .map .head{display:flex;align-items:center;gap:9px;padding:12px 14px;background:var(--panel2);border-bottom:1px solid var(--line)}
  .map .head .mn{font-size:16px;font-weight:800}
  .verdict{font-size:9.5px;font-weight:800;padding:4px 8px;border-radius:6px;letter-spacing:.6px}
  .verdict.play{background:rgba(52,211,153,.16);color:var(--play);border:1px solid rgba(52,211,153,.4)}
  .verdict.neu{background:rgba(250,204,21,.15);color:var(--neu);border:1px solid rgba(250,204,21,.4)}
  .verdict.ban{background:rgba(240,81,63,.15);color:var(--ban);border:1px solid rgba(240,81,63,.4)}
  .map .head .wr{margin-left:auto;text-align:right;font-variant-numeric:tabular-nums}
  .map .head .wr b{font-size:15px}
  .map .head .wr small{display:block;font-size:8.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
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

  @media(min-width:900px){
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
    <button class="qbtn" id="helpbtn" aria-label="Como ler">?</button>
  </div>
</header>

<div class="wrap">
  <section class="screen" id="scr-inicio"></section>
  <section class="screen" id="scr-mapas"></section>
  <section class="screen" id="scr-ops"></section>
  <section class="screen" id="scr-evo"></section>
  <div class="foot" id="foot"></div>
</div>

<nav class="bottom" id="bottomnav"></nav>

<div class="sheetbg" id="sheetbg"></div>
<div class="sheet" id="sheet"></div>

<script>
const SNAPSHOTS = __DATA__;
const PLAYER = __PLAYER__;

/* ---------- base ---------- */
const esc = s => String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
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

function baselineOf(snap){            // medição imediatamente anterior no tempo
  const i = ALL.indexOf(snap);
  return i>0 ? ALL[i-1] : null;
}

function rankInfo(rp){
  if(rp==null) return {name:"—",color:"#8b919c"};
  if(rp>=4500) return {name:"Campeão",color:"#e0447a"};
  const T=[{n:"Cobre",s:1000,c:"#b06a4b"},{n:"Bronze",s:1500,c:"#b5762f"},{n:"Prata",s:2000,c:"#9fb0bf"},
           {n:"Ouro",s:2500,c:"#f4c20d"},{n:"Platina",s:3000,c:"#37cfc0"},{n:"Esmeralda",s:3500,c:"#2ecc71"},
           {n:"Diamante",s:4000,c:"#6aa9ff"}];
  let t=T[0]; T.forEach(x=>{ if(rp>=x.s) t=x; });
  const div=Math.max(1,Math.min(5,5-Math.floor((rp-t.s)/100)));
  return {name:`${t.n} ${ROM[div]}`,tier:t.n,color:t.c};
}

function delta(c,p,dec=0){
  if(c==null||p==null) return "";
  const d=c-p, thr=dec?0.005:0.5, pv=p.toFixed(dec), cv=c.toFixed(dec);
  if(Math.abs(d)<thr) return `<span class="d eq" title="estável (${cv})">=</span>`;
  const up=d>0;
  return `<span class="d ${up?'up':'dn'}" title="${up?'subiu':'caiu'}: antes ${pv} → agora ${cv}">${up?'▲':'▼'}${Math.abs(d).toFixed(dec)}</span>`;
}
const tierOf = wr => wr>=55?"play":(wr<40?"ban":"neu");

/* ---------- INÍCIO ---------- */
function renderInicio(){
  const cur=active, base=baselineOf(cur);
  const k=cur.kpis, pk=(base||{}).kpis||{};
  const rk=rankInfo(k.peakRP), prk=base?rankInfo((base.kpis||{}).peakRP):null;
  const banner = base
    ? `🔄 Comparando <b>${esc(cur.season)}</b> com <b>${esc(base.season)}</b> (${esc(base.seasonLabel||"")}). Setas ▲▼ = variação entre as duas.`
    : `📍 Season mais antiga carregada — sem comparação. Carregue outra season pra ver as variações.`;

  // o que mudou (mapas presentes nas duas)
  let changed = "";
  if(base){
    const pb=byName(base.maps);
    const movers = cur.maps.filter(m=>pb[m.name]&&(m.matches>=4)&&(pb[m.name].matches>=4))
      .map(m=>({name:m.name, now:m.seasonWR, was:pb[m.name].seasonWR, d:m.seasonWR-pb[m.name].seasonWR}))
      .filter(m=>Math.abs(m.d)>=3);
    const ups=movers.slice().sort((a,b)=>b.d-a.d).slice(0,3);
    const dns=movers.slice().sort((a,b)=>a.d-b.d).slice(0,3);
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
    <div class="kgrid">
      <div class="ktile"><div class="v">${k.matches}${delta(k.matches,pk.matches,0)}</div><div class="l">Partidas</div></div>
      <div class="ktile"><div class="v">${k.winRate.toFixed(1)}%${delta(k.winRate,pk.winRate,1)}</div><div class="l">Vitórias</div></div>
      <div class="ktile"><div class="v">${k.kd.toFixed(2)}${delta(k.kd,pk.kd,2)}</div><div class="l">K/D</div></div>
      <div class="ktile"><div class="v" style="font-size:15px">${k.peakRP.toLocaleString('pt-BR')}${delta(k.peakRP,pk.peakRP,0)}</div><div class="l">Pico RP</div><span class="rkb" style="background:${rk.color}22;color:${rk.color}">${rk.name}</span></div>
    </div>
    <div class="banner">${banner}</div>
    ${changed}
    <h2 class="sec">Plano de jogo</h2>
    <div class="plan">
      <div class="pi"><div class="ico ban">⛔</div><div><b>Bane ${esc(bans[0]?.name||"—")}.</b> <span>${bans.length>1?"Depois "+esc(bans.slice(1,3).map(m=>m.name).join(" / "))+". ":""}Seus piores mapas.</span></div></div>
      <div class="pi"><div class="ico play">✔</div><div><b>Force ${esc(plays.slice(0,4).map(m=>m.name).join(", ")||"—")}.</b> <span>Vote neles sempre.</span></div></div>
      <div class="pi"><div class="ico def">🛡</div><div><b>Defesa: ${esc(dM.name)} (${dM.wr}%).</b> <span>Seu melhor defensor${cur.operatorsDef[1]?" — "+esc(cur.operatorsDef[1].name)+" de apoio":""}.</span></div></div>
      <div class="pi"><div class="ico atk">⚔</div><div><b>Ataque: ${esc(aM.name)} (${aM.wr}%).</b> <span>Pick certo por mapa na aba Mapas.</span></div></div>
      <div class="pi"><div class="ico ban">✕</div><div><b>Repense ${esc(cM.name)} (${cM.wr}%).</b> <span>Muito jogado e negativo — corte ou reposicione.</span></div></div>
    </div>`;
}

/* ---------- MAPAS ---------- */
function tierChips(cur, base, tier){
  const pb = base?byName(base.maps):{};
  return cur.maps.filter(m=>tierOf(m.seasonWR)===tier)
    .sort((a,b)=>b.seasonWR-a.seasonWR)
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
function renderMapas(){
  const cur=active, base=baselineOf(cur), pb=base?byName(base.maps):{};
  const cards = cur.maps.filter(m=>m.matches>=1).map(m=>{
    const t=tierOf(m.seasonWR), v={play:"PRIORIZE",neu:"NEUTRO",ban:"BANIR"}[t];
    const pm=pb[m.name]||{};
    const hasOps = m.def && m.atk;
    const opsHtml = hasOps ? `<div class="sides">
        <div class="side def"><div class="sh"><span class="ic"></span>Defesa</div>${sideRows(m.def,pm.def)}</div>
        <div class="side atk"><div class="sh"><span class="ic"></span>Ataque</div>${sideRows(m.atk,pm.atk)}</div></div>` : "";
    const adbar=(cls,val)=>`<div class="adr ${cls}"><span class="adl ${cls}">${cls.toUpperCase()}</span><div class="adbar"><i style="width:${Math.max(3,val||0)}%"></i></div><span class="adv">${(val||0).toFixed(0)}%${delta(val,(cls==='atk'?pm.atkWR:pm.defWR),0)}</span></div>`;
    return `<div class="map">
      <div class="head"><span class="mn">${esc(m.name)}</span><span class="verdict ${t}">${v}</span>
        <span class="wr"><b>${m.seasonWR.toFixed(1)}%${delta(m.seasonWR,pm.seasonWR,1)}</b><small>${m.matches} PARTIDAS${m.matches<4?" °":""}</small></span></div>
      <div class="ad">${adbar('atk',m.atkWR)}${adbar('def',m.defWR)}</div>
      <div class="strong">${strongSide(m)} <span>KD ${(m.kd||0).toFixed(2)}${delta(m.kd,pm.kd,2)}</span></div>
      ${opsHtml}
      ${m.note?`<div class="notew">⚠ ${esc(m.note)}</div>`:""}
      ${m.avoid?`<div class="avoid"><b>Evite:</b> ${esc(m.avoid)}</div>`:""}
    </div>`;
  }).join("");
  const opsNote = cur.maps.some(m=>m.def)?"":`<div class="banner" style="margin-bottom:12px">ℹ Top 3 de operador por mapa ainda não coletado pra ${esc(cur.season)} — mostrando o split ataque/defesa (já dá o diagnóstico do lado fraco).</div>`;
  document.getElementById("scr-mapas").innerHTML = `
    <h2 class="sec">Jogar vs banir<span class="hint">tier por win% da season</span></h2>
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
    const kd=o.kd!=null?` · ${o.kd.toFixed(2)}`:"", tag=o.tag?` · ${esc(o.tag)}`:"";
    return `<div class="oprow"><span class="nm">${esc(o.name)}${o.star?' <span class="star">★</span>':""}</span><span class="st"><b>${o.wr}%</b>${o.small?"°":""}${delta(o.wr,(p[o.name]||{}).wr,0)}${kd}${tag}</span></div>`;
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
    </div>`;
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
      <span class="cell"><b>${s.kpis.winRate.toFixed(1)}%</b>${delta(s.kpis.winRate,p.winRate,1)}</span>
      <span class="cell"><b>${s.kpis.kd.toFixed(2)}</b>${delta(s.kpis.kd,p.kd,2)}</span>
      <span class="cell"><b>${s.kpis.matches}</b></span></div>`;
  }).join("");
  document.getElementById("scr-evo").innerHTML = `
    <h2 class="sec">Evolução<span class="hint">season a season</span></h2>
    <div class="evo"><h3>Win rate %</h3>${spark(wrVals,"#34d399",v=>v.toFixed(0)+"%")}</div>
    <div class="evo"><h3>K/D</h3>${spark(kdVals,"#f4c20d",v=>v.toFixed(2))}</div>
    <div class="evo"><h3>Seasons</h3>
      <div class="evhead"><span class="sn">Season</span><span class="cell">Pico</span><span class="cell">Win</span><span class="cell">K/D</span><span class="cell">Partidas</span></div>
      ${rows}</div>`;
}

/* ---------- SELETOR / SHELL ---------- */
const TABS=[
  {id:"inicio",label:"Início",icon:'<svg viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg>'},
  {id:"mapas",label:"Mapas",icon:'<svg viewBox="0 0 24 24"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg>'},
  {id:"ops",label:"Operadores",icon:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>'},
  {id:"evo",label:"Evolução",icon:'<svg viewBox="0 0 24 24"><path d="M4 19h16"/><path d="M5 15l4-5 4 3 6-8"/></svg>'}
];
function go(id){
  document.querySelectorAll(".screen").forEach(s=>s.classList.toggle("active", s.id==="scr-"+id));
  document.querySelectorAll("nav.bottom button,.desktabs button").forEach(b=>b.classList.toggle("on", b.dataset.t===id));
  window.scrollTo({top:0});
}
function renderAll(){ renderInicio(); renderMapas(); renderOps(); renderEvo(); syncHeader(); }
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
      <div class="smeta">${s.kpis.winRate.toFixed(1)}% vitórias · KD ${s.kpis.kd.toFixed(2)} · ${s.kpis.matches} partidas</div></div>
      <span class="srk" style="background:${rk.color}22;color:${rk.color}">${rk.name}</span></div>`;
  }).join("");
  openSheet(`<h3>Escolher season</h3>${rows}`);
  document.querySelectorAll("#sheet .srow").forEach(r=>r.onclick=()=>{
    active = seasonMap[+r.dataset.so]; renderAll(); closeSheet();
  });
}
function openHelp(){
  openSheet(`<h3>Como ler o SIEGE·LAB</h3>
    <div class="legrow"><b style="color:var(--play)">▲</b> subiu vs a season anterior (toque na seta: antes → agora)</div>
    <div class="legrow"><b style="color:var(--ban)">▼</b> caiu vs a season anterior</div>
    <div class="legrow"><b style="color:#8b919c">=</b> estável</div>
    <div class="legrow"><b>°</b> amostra pequena — indicativo</div>
    <div class="legrow"><b style="color:var(--def)">■</b> defesa · <b style="color:var(--atk)">■</b> ataque</div>
    <div class="legrow"><b style="color:var(--gold)">%</b> verde ≥55 · amarelo 50–54 · vermelho &lt;50</div>
    <div class="legrow"><b>⇅</b> troque a season pelo seletor no topo pra comparar épocas</div>`);
}
const bg=document.getElementById("sheetbg"), sh=document.getElementById("sheet");
function openSheet(html){ sh.innerHTML='<div class="grab"></div>'+html; bg.classList.add("open"); sh.classList.add("open"); }
function closeSheet(){ bg.classList.remove("open"); sh.classList.remove("open"); }

function shell(){
  document.getElementById("bottomnav").innerHTML = TABS.map(t=>`<button data-t="${t.id}" onclick="go('${t.id}')">${t.icon}${t.label}</button>`).join("");
  document.getElementById("desktabs").innerHTML = TABS.map(t=>`<button data-t="${t.id}" onclick="go('${t.id}')">${t.label}</button>`).join("");
  document.getElementById("seasonsel").onclick=openSeasons;
  document.getElementById("helpbtn").onclick=openHelp;
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
