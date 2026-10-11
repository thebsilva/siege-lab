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
import html as _html

import brand                      # identidade visual (símbolo, favicon, PNGs) — uma fonte só

HERE = os.path.dirname(os.path.abspath(__file__))
PLAYERS_DIR = os.path.join(HERE, "players")
OUT_DIR = os.path.join(HERE, "docs")  # GitHub Pages serve daqui
SITE_URL = "https://thebsilva.github.io/siege-lab/"

LOGO_SVG = brand.symbol()         # <symbol id="sl-logo">: header, landing e card de compartilhar usam <use href="#sl-logo">


# Ícones de traço (grade 24×24, traço 1,8, pontas redondas): o mesmo desenho da navegação, no lugar dos emojis
# (que mudam de cara a cada sistema). Uma definição, vários usos: <svg class="ic"><use href="#i-nome"/></svg>.
ICONS = {
    # navegação
    "home": '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
    "coach": '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    "map": '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/>',
    "ops": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    "squad": '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 19c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5"/><circle cx="17" cy="9" r="2.6"/><path d="M14.8 14.6c.7-.4 1.4-.6 2.2-.6 2.3 0 4.1 1.5 4.6 4.3"/>',
    "evo": '<path d="M4 19h16"/><path d="M5 15l4-5 4 3 6-8"/>',
    # ações e controles
    "share": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/>',
    "chev": '<path d="M6 9l6 6 6-6"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    "image": '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><circle cx="9" cy="10" r="1.7"/><path d="M4 18l5-5 4 4 3-3 4 4"/>',
    # sentido do dado
    "ban": '<circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/>',
    "shield": '<path d="M12 3l7 3v5.5c0 4.4-2.9 8-7 9.5-4.1-1.5-7-5.1-7-9.5V6l7-3z"/>',
    "sword": '<path d="M20 4L10 14"/><path d="M8 12l4 4"/><path d="M10 14l-5 5"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r=".9" fill="currentColor"/>',
    "burst": '<circle cx="12" cy="12" r="2.6"/><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/>',
    "pause": '<circle cx="12" cy="12" r="9"/><path d="M10 9v6M14 9v6"/>',
    "flame": '<path d="M12 3c.8 3.2 5 5.4 5 10a5 5 0 0 1-10 0c0-2 1-3.4 2.2-4.4.2 1.4.9 2.1 1.9 2.4C10.6 8.6 10.8 5.6 12 3z"/>',
    "snow": '<path d="M12 3v18M4.2 7.5l15.6 9M19.8 7.5l-15.6 9"/>',
    "compare": '<path d="M4 12a8 8 0 0 1 13.7-5.6L20 8"/><path d="M20 4v4h-4"/><path d="M20 12a8 8 0 0 1-13.7 5.6L4 16"/><path d="M4 20v-4h4"/>',
    "pin": '<path d="M12 21s6-5.4 6-10a6 6 0 0 0-12 0c0 4.6 6 10 6 10z"/><circle cx="12" cy="11" r="2.2"/>',
    "up-right": '<path d="M7 17L17 7"/><path d="M9 7h8v8"/>',
    "down-right": '<path d="M7 7l10 10"/><path d="M17 9v8H9"/>',
    "warn": '<path d="M12 3.5L2.8 19.5h18.4L12 3.5z"/><path d="M12 10v4.5"/><circle cx="12" cy="17.2" r=".9" fill="currentColor"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5"/><circle cx="12" cy="7.8" r=".9" fill="currentColor"/>',
    "swap": '<path d="M8 4v16M4.5 7.5L8 4l3.5 3.5"/><path d="M16 20V4M12.5 16.5L16 20l3.5-3.5"/>',
    "medal": '<circle cx="12" cy="9" r="5"/><path d="M8.5 13.5L7 21l5-3 5 3-1.5-7.5"/>',
    "compass": '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
    "calendar": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
}


def sprite(only=None):
    """Sprite SVG inline (invisível): gradiente da marca, logo e ícones. Sem requisição externa."""
    icons = "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>'
                    for k, v in ICONS.items() if only is None or k in only)
    return ('<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>'
            + brand.GRAD + '</defs>' + LOGO_SVG + brand.symbol_mono() + icons + '</svg>')


def head_meta(title, desc, url):
    """Ícone da aba, prévia do link (WhatsApp/Telegram) e título — iguais nas duas páginas."""
    e = lambda s: _html.escape(s, quote=True)
    return "\n".join([
        '<meta name="color-scheme" content="dark">',
        f'<meta name="description" content="{e(desc)}">',
        '<meta name="apple-mobile-web-app-title" content="SIEGE·LAB">',
        f'<link rel="icon" type="image/svg+xml" href="{brand.favicon_href()}">',
        '<link rel="apple-touch-icon" href="apple-touch-icon.png">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="SIEGE·LAB">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:url" content="{e(url)}">',
        f'<meta property="og:image" content="{SITE_URL}og.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
    ])


RANK_TIERS = [("Cobre", 1000, "#b06a4b"), ("Bronze", 1500, "#b5762f"), ("Prata", 2000, "#9fb0bf"),
              ("Ouro", 2500, "#f4c20d"), ("Platina", 3000, "#37cfc0"), ("Esmeralda", 3500, "#2ecc71"),
              ("Diamante", 4000, "#6aa9ff")]


def rank_parts(rp):
    """(nome, cor, divisão 1–5, campeão?) — a mesma regra do rankInfo() do app."""
    if rp is None:
        return ("—", "#8b919c", 0, False)
    if rp >= 4500:
        return ("Campeão", "#e0447a", 0, True)
    t = RANK_TIERS[0]
    for x in RANK_TIERS:
        if rp >= x[1]:
            t = x
    div = max(1, min(5, 5 - ((rp - t[1]) // 100)))
    return (f"{t[0]} {brand.ROMAN[div]}", t[2], div, False)


def rank_py(rp):
    name, color, _, _ = rank_parts(rp)
    return (name, color)


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
    latest = max(snaps, key=lambda s: s.get("seasonOrder", 0))
    k = latest.get("kpis", {})
    curRP = k.get("latestRP") if k.get("latestRP") is not None else k.get("peakRP")
    rk, color, rdiv, rchamp = rank_parts(curRP)
    slug = profile.get("slug", "player")
    title = "SIEGE·LAB — " + str(profile.get("name"))
    rp_txt = f"{curRP or 0:,}".replace(",", ".")
    kd_txt = f"{k.get('kd') or 0:.2f}".replace(".", ",")
    desc = f"{profile.get('name')} · {rk} · {rp_txt} RP · K/D {kd_txt} — análise de ranqueada do R6 Siege: coach, mapas, operadores e squad."
    html = (TEMPLATE
            .replace("__HEAD__", head_meta(title, desc, SITE_URL + slug + ".html"))
            .replace("__TITLE__", _html.escape(title))
            .replace("__SPRITE__", sprite())
            .replace("__TOKENS__", TOKENS_CSS)
            .replace("__BRAND__", json.dumps(brand.js_parts(), ensure_ascii=False))
            .replace("__DATA__", json.dumps(snaps, ensure_ascii=False))
            .replace("__PLAYER__", json.dumps(profile, ensure_ascii=False))
            .replace("__PLAYBOOK__", json.dumps(playbook, ensure_ascii=False))
            .replace("__NAMES__", json.dumps(names or {}, ensure_ascii=False)))
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, slug + ".html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    seasons = sorted({s.get("season") for s in snaps})
    print(f"OK -> docs/{os.path.basename(out)}  ({profile.get('name')}: {len(snaps)} season(s): {', '.join(seasons)})")
    dmain = (latest.get("operatorsDef") or [{}])[0]
    amain = (latest.get("operatorsAtk") or [{}])[0]
    rm = latest.get("recentMatches") or []
    rw = sum(1 for m in rm if m.get("w")); rl = len(rm) - rw
    rnet = sum(m.get("rp", 0) for m in rm)
    return {"slug": profile.get("slug"), "name": profile.get("name"), "season": latest.get("season"),
            "rank": rk, "color": color, "div": rdiv, "champ": rchamp, "curRP": curRP or 0, "wr": k.get("winRate"), "kd": k.get("kd"),
            "matches": k.get("matches"), "defMain": dmain.get("name"), "defWr": dmain.get("wr") or 0,
            "atkMain": amain.get("name"), "atkWr": amain.get("wr") or 0,
            "rw": rw, "rl": rl, "rnet": rnet, "hasRecent": len(rm) > 0}


def _lum(hex_color):
    h = hex_color.lstrip("#")
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def text_on_panel(hex_color, bg="#14161c", want=4.5):
    """Clareia a cor (mistura com branco) até o texto pequeno ter contraste ≥ 4,5:1 sobre o card — a cor da patente
    (Cobre, por ex.) fica escura demais pra letra miúda; o emblema continua com a cor cheia."""
    h = hex_color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    lb = _lum(bg)
    for step in range(21):
        k = step / 20
        c = "#%02x%02x%02x" % tuple(round(v + (255 - v) * k) for v in rgb)
        if (_lum(c) + 0.05) / (lb + 0.05) >= want:
            return c
    return "#ffffff"


def write_index(cards):
    import html as _h
    esc = lambda s: _h.escape(str(s))
    dec = lambda v: f"{v:.2f}".replace(".", ",")
    mil = lambda n: f"{n:,}".replace(",", ".")                    # 2.702 (milhar com ponto)
    msg = lambda n: ("+" if n > 0 else ("−" if n < 0 else "")) + str(abs(n))   # menos de verdade
    ico = lambda name: f'<svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-{name}"/></svg>'
    cards = sorted(cards, key=lambda c: (c.get("curRP") or 0), reverse=True)
    chips = ""
    if cards:
        kd = max(cards, key=lambda c: c.get("kd") or 0)
        dfn = max(cards, key=lambda c: c.get("defWr") or 0)
        # (ícone, cor semântica, rótulo, jogador, valor): dourado = marca · laranja = defesa · verde = bom · vermelho = ruim
        sup = [("target", "k-gold", "Maior K/D", kd["name"], dec(kd["kd"])),
               ("shield", "k-def", "Melhor defesa", dfn["name"], f"{dfn['defMain']} · {dfn['defWr']:.0f}%")]
        rec = [c for c in cards if c.get("hasRecent")]
        if rec:
            best = max(rec, key=lambda c: c["rw"] - c["rl"])
            cold = min(rec, key=lambda c: c["rw"] - c["rl"])
            sup.append(("flame", "k-play", "Melhor forma", best["name"], f"{best['rw']}V-{best['rl']}D nas últimas"))
            sup.append(("snow", "k-ban", "Em maré fria", cold["name"], f"{cold['rw']}V-{cold['rl']}D · {msg(cold['rnet'])} RP"))
        chips = "".join(
            f'<div class="sup {cls}"><div class="sup-l"><span class="sup-i">{ico(name)}</span><span>{esc(lbl)}</span></div>'
            f'<div class="sup-n">{esc(nm)}</div><div class="sup-v">{esc(v)}</div></div>'
            for name, cls, lbl, nm, v in sup)
    rows = ""
    for i, c in enumerate(cards, 1):
        form = (f'<b class="{"up" if c["rw"] >= c["rl"] else "dn"}">{c["rw"]}V-{c["rl"]}D</b>'
                if c.get("hasRecent") else '<b class="mu">—</b>')
        rows += (
            f'<li><a class="prow2" href="{esc(c["slug"])}.html">'
            f'<span class="ppos" aria-hidden="true">{i}</span>'
            f'<span class="pemb">{brand.emblem(c["color"], c["div"], c["champ"], 40)}</span>'
            f'<span class="pwho"><span class="pnm">{esc(c["name"])}</span>'
            f'<span class="prn" style="--c:{text_on_panel(c["color"])}">{esc(c["rank"])}</span></span>'
            f'<span class="prp"><b>{mil(c["curRP"])}</b><i>RP</i></span>'
            f'<span class="pgo" aria-hidden="true">{ico("chev")}</span>'
            f'<span class="pst"><span class="stc"><i>vitórias</i><b>{c["wr"]:.0f}%</b></span>'
            f'<span class="stc"><i>K/D</i><b>{dec(c["kd"])}</b></span>'
            f'<span class="stc"><i>últimas</i>{form}</span>'
            f'<span class="stc"><i>season</i><b class="mu">{esc(c["season"])}</b></span></span></a></li>')
    out = os.path.join(OUT_DIR, "index.html")
    desc = "O squad no R6 Siege: ranking por RP, destaques do grupo e a análise completa de cada jogador (coach, mapas, operadores)."
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(INDEX_TEMPLATE
                 .replace("__HEAD__", head_meta("SIEGE·LAB — Squad", desc, SITE_URL))
                 .replace("__TOKENS__", TOKENS_CSS)
                 .replace("__SPRITE__", sprite({"target", "shield", "flame", "snow", "chev"}))
                 .replace("__CHIPS__", chips).replace("__ROWS__", rows))
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
    try:
        brand.write_pngs(OUT_DIR)
        print("  png -> docs/apple-touch-icon.png, docs/og.png")
    except ImportError:
        print("  (Pillow não instalado: apple-touch-icon.png e og.png não foram regenerados)")


TOKENS_CSS = r""":root{
    /* superfícies e linhas */
    --bg:#0a0b0e; --panel:#14161c; --panel2:#1a1d24; --inset:#101218; --chip:#1d2129; --chipline:#2b303a; --track:#20242c;
    --line:#262a33; --hair:#1f232b;
    /* texto: todos ≥ 4,5:1 sobre as superfícies acima */
    --txt:#e7e9ec; --txt-2:#cfd3d8; --muted:#8b919c;
    /* marca e semântica: verde = bom · amarelo = neutro · vermelho = ruim · azul = ataque · laranja = defesa · dourado = marca */
    --gold:#f4c20d; --atk:#3b82f6; --def:#f97316; --play:#34d399; --neu:#facc15; --ban:#f0513f;
    --atk-t:#6ea8fe; --ban-t:#ff6b5a; --neutral:#6b727e;   /* -t = versão clara pra TEXTO pequeno sobre fundo tingido; neutral = preenchimento de barra */
    /* tipografia: 7 tamanhos */
    --font:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    --fs-1:10px;    /* rótulo curto em CAIXA-ALTA */
    --fs-2:11.5px;  /* legenda, nota, tag */
    --fs-3:13px;    /* texto corrido e célula de tabela */
    --fs-4:15px;    /* nome e título de card */
    --fs-5:18px;    /* valor médio */
    --fs-6:24px;    /* KPI */
    --fs-7:32px;    /* herói e manchete */
    --ls-caps:.08em;
    /* raios: 4 no total */
    --r-1:6px; --r-2:10px; --r-3:14px; --r-pill:999px;
    --nav-h:64px;
  }"""


INDEX_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#0a0b0e">
<title>SIEGE·LAB — Squad</title>
__HEAD__
<style>
  __TOKENS__
  *{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
  body{background:var(--bg);color:var(--txt);font-family:var(--font);-webkit-font-smoothing:antialiased;line-height:1.45;
       min-height:100vh;padding:28px 16px calc(48px + env(safe-area-inset-bottom));position:relative}
  /* quadro de tática (o mesmo da prévia do link): grade fina e brilho dourado que somem pra baixo */
  body::before{content:"";position:absolute;left:0;right:0;top:0;height:440px;z-index:-1;pointer-events:none;
       background:radial-gradient(560px 280px at 14% 0,rgba(244,194,13,.14),transparent 72%),
                  linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px) 0 0/48px 48px,
                  linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px) 0 0/48px 48px;
       -webkit-mask-image:linear-gradient(#000 30%,transparent);mask-image:linear-gradient(#000 30%,transparent)}
  .wrap{max-width:820px;margin:0 auto}
  .ic{width:1.15em;height:1.15em;flex:none;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;vertical-align:-.2em}

  .hero{display:flex;align-items:center;gap:14px}
  .logo{width:56px;height:56px;flex:none;filter:drop-shadow(0 0 14px rgba(244,194,13,.32))}
  h1{font-size:var(--fs-6);font-weight:800;letter-spacing:.06em;line-height:1.05} h1 em{font-style:normal;color:var(--gold)}
  .tag{color:var(--muted);font-size:var(--fs-3);margin-top:5px}

  h2{font-size:var(--fs-3);letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin:28px 0 12px;display:flex;align-items:center;gap:9px}
  h2::before{content:"";width:4px;height:14px;background:var(--gold);border-radius:var(--r-1);flex:none}
  h2 .hint{margin-left:auto;font-size:var(--fs-2);letter-spacing:.4px;text-transform:none;font-weight:500}
  @media(max-width:539px){ h2{flex-wrap:wrap;row-gap:2px} h2 .hint{flex:1 0 100%;margin-left:13px} }

  /* destaques do grupo */
  .sups{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .sup{border:1px solid var(--line);border-radius:var(--r-3);background:var(--panel);padding:12px 14px;min-width:0}
  .sup-l{display:flex;align-items:center;gap:8px;font-size:var(--fs-1);color:var(--muted);text-transform:uppercase;letter-spacing:var(--ls-caps);font-weight:700;line-height:1.2}
  .sup-i{width:26px;height:26px;flex:none;border-radius:var(--r-1);display:grid;place-items:center;background:var(--tint);color:var(--ink)}
  .sup-i .ic{width:15px;height:15px}
  .sup-n{font-size:var(--fs-4);font-weight:800;margin-top:10px;overflow-wrap:anywhere}
  .sup-v{font-size:var(--fs-3);color:var(--muted);margin-top:1px;font-variant-numeric:tabular-nums}
  .k-gold{--tint:rgba(244,194,13,.14);--ink:var(--gold)} .k-def{--tint:rgba(249,115,22,.14);--ink:var(--def)}
  .k-play{--tint:rgba(52,211,153,.14);--ink:var(--play)} .k-ban{--tint:rgba(240,81,63,.14);--ink:var(--ban-t)}

  /* ranking */
  .rank{list-style:none;display:grid;gap:10px}
  .prow2{display:grid;grid-template-columns:auto auto minmax(0,1fr) auto auto;grid-template-areas:"pos emb who rp go" "st st st st st";
         align-items:center;column-gap:12px;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:var(--r-3);
         background:var(--panel);padding:14px 14px 12px;transition:border-color .15s,transform .1s}
  .prow2:hover{border-color:var(--gold)} .prow2:active{transform:scale(.99)}
  .prow2:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
  .rank li:first-child .prow2{border-color:rgba(244,194,13,.4)}
  .ppos{grid-area:pos;width:24px;height:24px;border-radius:var(--r-1);background:var(--chip);border:1px solid var(--chipline);display:grid;place-items:center;
        font-weight:800;font-size:var(--fs-3);color:var(--muted);font-variant-numeric:tabular-nums}
  .rank li:first-child .ppos{background:var(--gold);color:#111;border-color:var(--gold)}
  .pemb{grid-area:emb;display:flex;filter:drop-shadow(0 2px 5px rgba(0,0,0,.45))}
  .pwho{grid-area:who;min-width:0}
  .pnm{display:block;font-size:var(--fs-5);font-weight:800;line-height:1.15;overflow-wrap:anywhere}
  .prn{display:block;font-size:var(--fs-3);font-weight:700;color:var(--c);margin-top:2px}
  .prp{grid-area:rp;text-align:right;line-height:1.1;min-width:58px}
  .prp b{display:block;font-size:var(--fs-5);font-weight:800;font-variant-numeric:tabular-nums}
  .prp i{font-style:normal;font-size:var(--fs-1);letter-spacing:var(--ls-caps);text-transform:uppercase;font-weight:700;color:var(--muted)}
  .pgo{grid-area:go;display:flex;color:var(--muted)} .pgo .ic{width:18px;height:18px;transform:rotate(-90deg)}
  .prow2:hover .pgo{color:var(--gold)}
  .pst{grid-area:st;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,.85fr) minmax(0,1.3fr) minmax(0,1fr);gap:8px;margin-top:12px;padding-top:10px;border-top:1px solid var(--hair);font-variant-numeric:tabular-nums}
  .stc{min-width:0}
  .stc i{display:block;font-style:normal;font-size:var(--fs-1);letter-spacing:var(--ls-caps);text-transform:uppercase;font-weight:700;color:var(--muted)}
  .stc b{display:block;margin-top:2px;font-size:var(--fs-4);font-weight:800;white-space:nowrap}
  .stc b.up{color:var(--play)} .stc b.dn{color:var(--ban-t)} .stc b.mu{color:var(--muted);font-weight:700}
  @media(max-width:359px){
    .prow2{column-gap:8px;padding:12px 12px 10px}
    .ppos{width:20px;height:20px;font-size:var(--fs-2)}
    .pemb .remb{width:34px;height:34px} .pgo{display:none}
    .pst{gap:6px} .stc b{font-size:var(--fs-3)}
    .sup{padding:10px 12px}
  }
  @media(min-width:540px){ .pst{max-width:460px} }
  @media(min-width:640px){
    body{padding-top:48px}
    .logo{width:68px;height:68px} h1{font-size:var(--fs-7)} .tag{font-size:var(--fs-4)}
    .sups{grid-template-columns:repeat(4,1fr)}
  }
  @media(min-width:768px){      /* a linha vira uma faixa só: número da mini-tabela precisa de ~60 px por coluna */
    .prow2{grid-template-columns:auto auto minmax(0,1fr) minmax(0,1.6fr) auto auto;grid-template-areas:"pos emb who st rp go";padding:14px 18px;column-gap:16px}
    .pst{margin:0;padding:0;border-top:0;gap:12px;max-width:none}
  }
  .foot{color:var(--muted);font-size:var(--fs-2);text-align:center;margin-top:30px;line-height:1.6}
  @media(prefers-reduced-motion:reduce){ .prow2{transition:none} }
</style>
</head>
<body>
__SPRITE__
<main class="wrap">
  <header class="hero">
    <svg class="logo" viewBox="0 0 64 64" role="img" aria-label="SIEGE·LAB"><use href="#sl-logo"/></svg>
    <div><h1>SIEGE<em>·</em>LAB</h1><p class="tag">O squad · ranqueada R6</p></div>
  </header>
  <section>
    <h2>Destaques do grupo</h2>
    <div class="sups">__CHIPS__</div>
  </section>
  <section>
    <h2>Ranking por RP<span class="hint">toque num jogador pra abrir a análise completa</span></h2>
    <ol class="rank">__ROWS__</ol>
  </section>
  <p class="foot">Cada jogador abre o app completo: início, coach, mapas, operadores, squad e evolução.<br>Dados de r6.tracker.network.</p>
</main>
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
<title>__TITLE__</title>
__HEAD__
<style>
  __TOKENS__
  *{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
  body{background:var(--bg);color:var(--txt);font-family:var(--font);
       -webkit-font-smoothing:antialiased;line-height:1.45;padding-bottom:calc(var(--nav-h) + env(safe-area-inset-bottom))}
  .wrap{max-width:1100px;margin:0 auto;padding:0 16px}

  header{position:sticky;top:0;z-index:50;background:rgba(10,11,14,.86);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
  .hbar{display:flex;align-items:center;gap:6px;padding:8px 10px;max-width:1100px;margin:0 auto;min-height:56px}
  .hbrand{display:flex;align-items:center;gap:8px;min-width:0;flex:1 1 auto;color:inherit;text-decoration:none;border-radius:var(--r-2)}
  .hbrand:focus-visible,.hbar button:focus-visible,nav.bottom button:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
  .logo{width:32px;height:32px;flex:none;filter:drop-shadow(0 0 9px rgba(244,194,13,.28))}
  .brand{min-width:0;line-height:1.1}
  .brand .wm{display:block;font-weight:800;font-size:var(--fs-4);letter-spacing:.05em;white-space:nowrap}
  .brand .wm em{font-style:normal;color:var(--gold)}
  .brand small{display:block;margin-top:2px;font-weight:500;font-size:var(--fs-2);color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .seasonsel{flex:none;display:flex;align-items:center;gap:6px;min-height:40px;padding:0 10px 0 12px;border:1px solid var(--line);background:var(--panel);color:var(--txt);border-radius:var(--r-pill);font:inherit;cursor:pointer}
  .seasonsel:active{transform:scale(.97)}
  .seasonsel .sv{font-weight:800;font-size:var(--fs-3)}
  .seasonsel .rk{display:none;font-size:var(--fs-2);font-weight:700;padding:2px 8px;border-radius:var(--r-pill)}
  .seasonsel .cv{width:10px;height:10px;color:var(--muted);flex:none}
  .qbtn{flex:none;width:40px;height:40px;display:grid;place-items:center;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--muted);font:inherit;font-weight:800;font-size:var(--fs-4);cursor:pointer}
  .qbtn .ic{width:18px;height:18px}
  .qbtn:active{transform:scale(.94)}
  .desktabs{display:none;gap:4px;margin-left:14px}
  .desktabs button{background:none;border:none;color:var(--muted);font-weight:700;font-size:var(--fs-3);padding:0 14px;min-height:40px;border-radius:var(--r-2);cursor:pointer}
  .desktabs button:hover{color:var(--txt)}
  .desktabs button.on{color:#111;background:var(--gold)}
  @media(max-width:399px){ .brand small .pq{display:none} }
  @media(min-width:360px){ .hbar{padding:8px 12px;gap:8px} .hbrand{gap:9px} .logo{width:34px;height:34px} }
  @media(min-width:520px){ .hbar{padding:10px 16px;gap:10px} .seasonsel .rk{display:inline-block} }

  .screen{display:none;padding-top:16px}
  .screen.active{display:block;animation:fade .18s ease}
  @keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}

  h2.sec{font-size:var(--fs-3);letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin:22px 0 10px;display:flex;align-items:center;gap:9px}
  h2.sec::before{content:"";width:4px;height:14px;background:var(--gold);border-radius:var(--r-1)}
  h2.sec .hint{margin-left:auto;font-size:var(--fs-2);letter-spacing:.4px;color:var(--muted);text-transform:none}
  h2.sec.first{margin-top:4px}
  @media(max-width:439px){ h2.sec{flex-wrap:wrap;row-gap:2px} h2.sec .hint{flex:1 0 100%;margin-left:13px} }

  .ic{width:1.15em;height:1.15em;flex:none;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;vertical-align:-.2em}

  /* setas ▲▼ e °: tocar mostra a explicação ("antes → agora", a regra da amostra); o title só serve ao mouse */
  .d,.smp{cursor:pointer;border-radius:var(--r-1)}
  .d:focus-visible,.smp:focus-visible{outline:2px solid var(--gold);outline-offset:1px}
  .d{font-size:var(--fs-2);font-weight:800;margin-left:5px;padding:4px 3px;font-variant-numeric:tabular-nums}
  .d.up{color:var(--play)} .d.dn{color:var(--ban)} .d.eq{color:var(--muted);font-weight:600}
  .d.nt{color:#9aa3ad}                        /* contagem (partidas) ou estilo: a seta mostra o sentido, não bom nem ruim */
  .smp{color:var(--neu);font-weight:800;font-size:1.25em;line-height:0;padding:4px 2px;margin-left:1px}
  .poptip{position:fixed;z-index:120;max-width:min(260px,calc(100vw - 24px));padding:8px 11px;border-radius:var(--r-2);background:#0b0d11;border:1px solid var(--gold);
          color:var(--txt);font-size:var(--fs-3);line-height:1.35;box-shadow:0 8px 24px rgba(0,0,0,.5);pointer-events:none;opacity:0;transform:translateY(4px);transition:opacity .12s,transform .12s}
  .poptip.on{opacity:1;transform:none}
  .cdef{color:var(--def)} .catk{color:var(--atk-t)} .cgold{color:var(--gold)} .cup{color:var(--play)} .cdn{color:var(--ban)} .cnt{color:#9aa3ad} .cmut{color:var(--muted)} .cneu{color:var(--neu)}

  /* INÍCIO */
  .kgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
  .kgrid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:2px}
  .glance{display:flex;align-items:stretch;gap:12px;border:1px solid var(--line);border-radius:var(--r-3);
       background:linear-gradient(105deg,#181b23,#0d0f13);padding:12px 14px;margin-bottom:12px}
  .glance .emb{flex:none;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;min-width:64px}
  .glance .emb .remb{filter:drop-shadow(0 2px 4px rgba(0,0,0,.4))}
  .glance .emb .rn{font-size:var(--fs-3);font-weight:800;text-align:center;line-height:1.05;letter-spacing:.2px;white-space:nowrap}
  .glance .emb .pk{display:flex;flex-direction:column;align-items:center;gap:1px;font-size:var(--fs-2);color:var(--muted);line-height:1.1;white-space:nowrap}
  .glance .emb .pk i{font-style:normal;font-size:var(--fs-1);letter-spacing:var(--ls-caps);text-transform:uppercase}
  .glance .gstats{flex:1;display:flex;align-items:center;min-width:0}
  .glance .gst{flex:1;text-align:center;padding:0 4px;min-width:0}
  .glance .gst+.gst{border-left:1px solid var(--line)}
  .glance .gst .l{font-size:var(--fs-1);color:var(--muted);text-transform:uppercase;letter-spacing:1px;font-weight:700}
  .glance .gst .v{font-size:var(--fs-6);font-weight:800;font-variant-numeric:tabular-nums;line-height:1.1;margin-top:3px}
  .glance .gst .dd{height:13px;line-height:13px;margin-top:2px}
  .glance .gst .dd .d{font-size:var(--fs-2);margin-left:0}
  @media(max-width:400px){
    .glance{gap:7px;padding:11px 9px}
    .glance .emb{min-width:56px}
    .glance .emb .rn{font-size:var(--fs-2)}
    .glance .gst{padding:0 2px}
    .glance .gst .v{font-size:var(--fs-5)}
    .glance .gst .l{font-size:var(--fs-1);letter-spacing:.4px}
  }
  .card,.cgoal,.cbox,.opcard,.evo,.forma,.plan,.map,.ktile{border:1px solid var(--line);border-radius:var(--r-3);background:var(--panel)}
  .ktile{padding:14px 16px}
  .ktile .v{font-size:var(--fs-6);font-weight:800;font-variant-numeric:tabular-nums}
  .ktile .l{font-size:var(--fs-2);color:var(--muted);text-transform:uppercase;letter-spacing:.7px;margin-top:2px}
  .ktile .kn{font-size:var(--fs-2);color:var(--muted);margin-top:4px}
  .ktile .rkb{display:inline-block;font-size:var(--fs-2);font-weight:800;padding:2px 8px;border-radius:var(--r-1);margin-top:6px}
  .banner{display:flex;gap:10px;align-items:flex-start;margin-top:12px;padding:10px 14px;border-radius:var(--r-2);font-size:var(--fs-3);line-height:1.45;color:var(--muted);background:var(--inset);border:1px solid var(--line)}
  .banner>.ic{width:16px;height:16px;margin-top:2px;color:var(--muted)}
  .banner p{min-width:0;flex:1}
  .banner b{color:var(--txt)}
  .banner .bsub{display:block;margin-top:3px;font-size:var(--fs-2)}
  .banner.flat{margin-top:0} .banner.tight{margin:0 0 6px} .banner.gap{margin:0 0 12px}
  .banner.attn{background:rgba(244,194,13,.06);border-color:rgba(244,194,13,.35)} .banner.attn>.ic{color:var(--gold)}   /* aviso que muda a leitura */
  .changed{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr));gap:10px}   /* 2 colunas quando cabe; empilha em 320 */
  .chcol{border:1px solid var(--line);border-radius:var(--r-2);background:var(--panel);padding:13px 15px}
  .chcol h4{font-size:var(--fs-2);text-transform:uppercase;letter-spacing:.7px;margin-bottom:9px;display:flex;align-items:center;gap:7px}
  .chcol h4 .ic{width:14px;height:14px}
  .chcol.up h4{color:var(--play)} .chcol.dn h4{color:var(--ban)}
  .chrow{padding:8px 0;font-size:var(--fs-3);border-top:1px solid var(--hair)}
  .chrow:first-of-type{border-top:none;padding-top:0}
  .chrow .nm{display:block;font-weight:700}
  .chrow .vv{display:flex;justify-content:space-between;align-items:center;font-variant-numeric:tabular-nums;color:var(--muted)}
  .plan{padding:6px 16px}
  .plan .pi{display:flex;gap:11px;padding:11px 0;border-top:1px solid var(--hair);font-size:var(--fs-3);align-items:flex-start}
  .plan .pi:first-child{border-top:none}
  .plan .ico{width:26px;height:26px;border-radius:var(--r-1);display:grid;place-items:center;font-size:var(--fs-3);flex:none;margin-top:1px}
  .plan .ico.ban{background:rgba(240,81,63,.14);color:var(--ban)}
  .plan .ico.play{background:rgba(52,211,153,.14);color:var(--play)}
  .plan .ico.def{background:rgba(249,115,22,.14);color:var(--def)}
  .plan .ico .ic{width:16px;height:16px}
  .plan .ico.atk{background:rgba(59,130,246,.14);color:var(--atk-t)}
  .plan b{color:var(--txt)} .plan .pi span{color:var(--muted)}
  .plan.coach .pi>div:last-child{min-width:0;flex:1}
  .plan.coach .pi b{display:block;margin-bottom:2px}
  .plan a.pi{color:inherit;text-decoration:none;border-radius:var(--r-2)}
  .plan a.pi:active{background:var(--panel2)}
  .plan a.pi:focus-visible{outline:2px solid var(--gold);outline-offset:-2px}
  .plan .see{display:flex;align-items:center;gap:3px;margin-top:6px;color:var(--gold);font-size:var(--fs-2);font-weight:700}
  .plan .see .ic{width:12px;height:12px;transform:rotate(-90deg)}

  /* TIER */
  .tier{display:grid;grid-template-columns:1fr;gap:10px}
  .tcol{border:1px solid var(--line);border-radius:var(--r-2);padding:10px 12px 12px 14px;background:var(--panel)}
  .tcol .th{font-weight:800;font-size:var(--fs-3);letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;display:flex;align-items:center;gap:8px}
  .dot{width:9px;height:9px;border-radius:50%}
  .tcol.play{border-left:3px solid var(--play)} .tcol.play .dot{background:var(--play)}
  .tcol.neu{border-left:3px solid var(--neu)} .tcol.neu .dot{background:var(--neu)}
  .tcol.ban{border-left:3px solid var(--ban)} .tcol.ban .dot{background:var(--ban)}
  .chips{display:flex;flex-wrap:wrap;gap:6px}
  .chipm{display:inline-flex;align-items:center;min-height:40px;padding:0 11px;border-radius:var(--r-2);background:var(--chip);border:1px solid var(--chipline);
         font-size:var(--fs-3);font-weight:600;color:var(--txt);text-decoration:none}
  .chipm small{color:var(--muted);font-weight:500;margin-left:4px}
  .chipm.none{opacity:.6;min-height:30px}
  a.chipm:hover{border-color:var(--gold)}
  a.chipm:active{background:var(--panel2);border-color:var(--gold)}
  a.chipm:focus-visible{outline:2px solid var(--gold);outline-offset:1px}

  /* MAPAS: linha compacta (a decisão num relance) que abre o detalhe */
  .maps{display:grid;grid-template-columns:1fr;gap:10px;align-items:start}
  .map{overflow:hidden}
  .mrow{scroll-margin-top:72px}
  .mrow.play{border-left:3px solid var(--play)} .mrow.neu{border-left:3px solid var(--neu)} .mrow.ban{border-left:3px solid var(--ban)}
  .mrow.flash{animation:flash 1.4s ease-out}
  @media(prefers-reduced-motion:reduce){.mrow.flash{animation:none}}
  .mrow>summary{display:block;list-style:none;cursor:pointer;padding:12px 14px 14px 13px}
  .mrow>summary::-webkit-details-marker{display:none}
  .mrow>summary:focus-visible{outline:2px solid var(--gold);outline-offset:-2px}
  .mh{display:flex;align-items:center;gap:8px}
  .mrow .mn{flex:1;min-width:0;font-size:var(--fs-4);font-weight:800}
  .mrow .wr{flex:none;font-size:var(--fs-5);font-weight:800;font-variant-numeric:tabular-nums}
  .mrow .chev{flex:none;width:20px;height:20px;color:var(--muted);transition:transform .15s}
  .mrow[open] .chev{transform:rotate(180deg)}
  .mm{display:flex;align-items:center;flex-wrap:wrap;gap:6px 8px;margin-top:6px;font-size:var(--fs-2);color:var(--muted)}
  .verdict{font-size:var(--fs-1);font-weight:800;padding:4px 8px;border-radius:var(--r-1);letter-spacing:.6px}
  .verdict.play{background:rgba(52,211,153,.16);color:var(--play);border:1px solid rgba(52,211,153,.4)}
  .verdict.neu{background:rgba(250,204,21,.15);color:var(--neu);border:1px solid rgba(250,204,21,.4)}
  .verdict.ban{background:rgba(240,81,63,.15);color:var(--ban-t);border:1px solid rgba(240,81,63,.4)}
  .ad{display:flex;flex-direction:column;gap:7px;margin-top:12px}
  .adr{display:flex;align-items:center;gap:9px;font-size:var(--fs-2);font-weight:800}
  .adl{width:30px;letter-spacing:.5px} .adl.atk{color:var(--atk)} .adl.def{color:var(--def)}
  .adbar{flex:1;height:7px;border-radius:var(--r-1);background:var(--track);overflow:hidden}
  .adbar i{display:block;height:100%;border-radius:var(--r-1)}
  .adr.atk i{background:var(--atk)} .adr.def i{background:var(--def)}
  .adv{flex:none;min-width:56px;text-align:right;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap}
  .mpks{display:grid;grid-template-columns:1fr 1fr;margin-top:12px;border:1px solid var(--hair);border-radius:var(--r-2);background:var(--inset)}
  .mpk{min-width:0;padding:8px 10px 9px}
  .mpk+.mpk{border-left:1px solid var(--hair)}
  .mpk i{display:block;font-style:normal;font-size:var(--fs-1);font-weight:800;letter-spacing:var(--ls-caps);text-transform:uppercase}
  .mpk.def i{color:var(--def)} .mpk.atk i{color:var(--atk-t)}
  .mpk p{margin-top:3px;font-size:var(--fs-3);line-height:1.3;overflow-wrap:anywhere}
  .mpk p b{font-weight:700}
  .mpk .v{margin-left:6px;color:var(--muted);font-variant-numeric:tabular-nums}
  .mpk .v.good{color:var(--play)} .mpk .v.mid{color:var(--neu)} .mpk .v.low{color:var(--ban-t)}
  .mpk small{display:block;margin-top:1px;font-size:var(--fs-2);color:var(--muted)}
  .mwarn{display:flex;gap:8px;align-items:flex-start;margin-top:10px;padding:7px 10px;border-radius:var(--r-2);font-size:var(--fs-2);line-height:1.45}
  .mwarn .ic{width:14px;height:14px;margin-top:1px}
  .mwarn.avoid{color:#f3a99f;background:rgba(240,81,63,.08)} .mwarn.avoid .ic,.mwarn.avoid b{color:var(--ban-t)}
  .mwarn.note{color:#d9c98a;background:rgba(250,204,21,.07)} .mwarn.note .ic{color:var(--neu)}
  .strong{padding:8px 14px;font-size:var(--fs-2);color:var(--muted);display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .sbadge{font-size:var(--fs-1);font-weight:800;padding:3px 8px;border-radius:var(--r-1);letter-spacing:.4px}
  .sbadge.atk{background:rgba(59,130,246,.14);color:var(--atk-t)}
  .sbadge.def{background:rgba(249,115,22,.14);color:var(--def)}
  .sbadge.bal{background:var(--track);color:var(--muted)}
  .mrow .strong{padding:10px 14px 10px 13px;border-top:1px solid var(--line)}
  .picks{border-top:1px solid var(--line)}
  .pside{padding:11px 14px 11px 13px}
  .pside+.pside{border-top:1px solid var(--line)}
  .pside .sh{font-size:var(--fs-2);font-weight:800;letter-spacing:.8px;text-transform:uppercase;margin-bottom:8px;display:flex;flex-wrap:wrap;align-items:center;gap:2px 6px}
  .pside.def .sh{color:var(--def)} .pside.atk .sh{color:var(--atk)}
  .pside .sh .ic{width:7px;height:7px;border-radius:var(--r-1)}
  .pside.def .ic{background:var(--def)} .pside.atk .ic{background:var(--atk)}
  .prow{padding:7px 0;border-top:1px solid var(--hair)}
  .prow:first-of-type{border-top:none}
  .pline{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .pn{font-size:var(--fs-3);font-weight:700}
  .pwr{font-size:var(--fs-2);font-weight:800;padding:2px 7px;border-radius:var(--r-3);background:var(--chip);border:1px solid var(--chipline);cursor:help}
  .pwr.good{color:var(--play);border-color:rgba(52,211,153,.4)}
  .pwr.mid{color:var(--neu);border-color:rgba(250,204,21,.4)}
  .pwr.low{color:var(--ban);border-color:rgba(240,81,63,.4)}
  .pw{font-size:var(--fs-2);color:var(--muted);line-height:1.45;margin-top:2px}
  .pwhy{display:block;color:var(--txt);font-weight:600;font-variant-numeric:tabular-nums}
  .prole{display:block;margin-top:1px}
  .pside .sh .src{flex:1 0 100%;margin:0 0 0 13px;font-size:var(--fs-2);font-weight:600;letter-spacing:.2px;text-transform:none;color:var(--muted)}
  .tip{padding:9px 14px 9px 13px;font-size:var(--fs-3);color:#e0d6ae;background:rgba(244,194,13,.07);border-top:1px solid var(--line);line-height:1.5}
  .forma{padding:14px 16px 6px}
  .frec{font-size:var(--fs-4);color:var(--muted);font-weight:600;white-space:nowrap;margin-bottom:12px}
  .frec b{color:var(--txt);font-size:var(--fs-6);font-weight:800;line-height:1;font-variant-numeric:tabular-nums}
  .frec span{font-size:var(--fs-4);margin:0 1px 0 2px}
  .fpips{display:flex;gap:3px}
  .pip{flex:1 1 0;min-width:5px;max-width:16px;height:20px;border-radius:var(--r-1);cursor:pointer}
  .pip.w{background:var(--play)} .pip.l{background:var(--ban);opacity:.85}
  .faxis{display:flex;justify-content:space-between;margin-top:6px;font-size:var(--fs-1);letter-spacing:var(--ls-caps);text-transform:uppercase;color:var(--muted)}
  .fstats{display:grid;grid-template-columns:1fr 1fr;margin-top:12px;border-top:1px solid var(--hair)}
  .fk{padding:11px 0 10px;min-width:0}
  .fk+.fk{padding-left:14px;border-left:1px solid var(--hair)}
  .fk .fl{font-size:var(--fs-1);color:var(--muted);text-transform:uppercase;letter-spacing:var(--ls-caps);font-weight:700}
  .fk .fv{font-size:var(--fs-5);font-weight:800;margin-top:2px;font-variant-numeric:tabular-nums}
  .fins{display:flex;gap:10px;align-items:flex-start;padding:11px 0;border-top:1px solid var(--hair);font-size:var(--fs-3);line-height:1.5;color:var(--txt-2)}
  .fins>i{flex:none;margin-top:1px;line-height:0}
  .fins>i .ic{width:18px;height:18px}
  .fins p{min-width:0;flex:1}
  .fins b{color:var(--txt);font-weight:700}
  .fins .act{display:block;color:var(--muted)}
  .goal{margin-bottom:12px;padding:11px 14px 12px;border:1px solid var(--line);border-left:3px solid var(--gold);
       border-radius:0 var(--r-2) var(--r-2) 0;background:rgba(244,194,13,.06);font-size:var(--fs-3);color:var(--muted)}
  .goal .gtop{display:flex;align-items:center;gap:8px}
  .goal b{color:var(--txt);font-weight:700} .goal .gi{color:var(--gold);line-height:0} .goal .gi .ic{width:18px;height:18px}
  .goal .gbar{height:6px;margin:10px 0 8px;border-radius:var(--r-pill);background:var(--track);overflow:hidden}
  .goal .gbar i{display:block;height:100%;min-width:4px;border-radius:inherit;background:var(--gold)}
  .goal .gsub{font-size:var(--fs-2)}
  .rbadge{font-size:var(--fs-2);font-weight:800;padding:3px 7px;border-radius:var(--r-1);letter-spacing:.3px;background:var(--chip);border:1px solid var(--chipline);white-space:nowrap}
  .rbadge .ic{width:12px;height:12px;margin-right:3px;vertical-align:-.15em}
  .rbadge.up{color:var(--play);border-color:rgba(52,211,153,.4)} .rbadge.dn{color:var(--ban-t);border-color:rgba(240,81,63,.4)} .rbadge.eq{color:var(--muted)}
  .rnote{padding:8px 14px 8px 13px;font-size:var(--fs-2);line-height:1.5;border-top:1px solid var(--line)}
  .rnote i{font-style:normal;font-weight:800;margin-right:3px}
  .rnote i .ic{width:13px;height:13px}
  .rnote.up{color:#a6e8c9;background:rgba(52,211,153,.07)} .rnote.up i{color:var(--play)}
  .rnote.dn{color:#f3a99f;background:rgba(240,81,63,.07)} .rnote.dn i{color:var(--ban)}
  .rnote b{color:var(--txt);font-weight:600}
  /* COMPARTILHAR: o card é uma imagem 4:5 (SVG); a largura respeita a altura da folha pra caber sem rolar */
  .sharecard{width:min(100%,max(150px,calc((80vh - 262px - env(safe-area-inset-bottom,0px))*.8)));aspect-ratio:4/5;margin:6px auto 14px;border-radius:var(--r-3);overflow:hidden;
       border:1px solid var(--line);background:var(--bg)}
  .sharecard svg{display:block;width:100%;height:100%}
  .shint{font-size:var(--fs-3);color:var(--muted);text-align:center;margin-bottom:12px}
  .shbtns{display:grid;gap:8px}
  .btn-share{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;min-height:48px;padding:0 14px;border-radius:var(--r-2);
       border:1px solid var(--gold);background:rgba(244,194,13,.12);color:var(--gold);font:inherit;font-weight:800;font-size:var(--fs-4);cursor:pointer}
  .btn-share:active{transform:scale(.98)}
  .btn-share:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
  .btn-share[hidden]{display:none}
  .btn-share.pri{background:var(--gold);color:#111}
  .btn-share.sec{border-color:var(--line);background:var(--panel);color:var(--txt)}
  .btn-share:disabled{opacity:.6;cursor:default}

  /* OPERADORES */
  .ops{display:grid;grid-template-columns:1fr;gap:12px}
  .opcard{padding:15px}
  .opcard.gap{margin-top:12px}
  .opcard h3{font-size:var(--fs-3);letter-spacing:.5px;text-transform:uppercase;margin-bottom:6px;display:flex;align-items:center;gap:8px}
  .tag{display:inline-flex;align-items:center;gap:4px;font-size:var(--fs-1);font-weight:800;padding:3px 8px;border-radius:var(--r-1);letter-spacing:.5px}
  .tag .ic{width:12px;height:12px}
  .tag.def{background:rgba(249,115,22,.15);color:var(--def);border:1px solid rgba(249,115,22,.35)}
  .tag.atk{background:rgba(59,130,246,.15);color:var(--atk-t);border:1px solid rgba(59,130,246,.35)}
  .tag.cut{background:rgba(240,81,63,.13);color:var(--ban-t);border:1px solid rgba(240,81,63,.35)}
  .tag.sm{font-size:var(--fs-1);padding:1px 6px;margin-left:6px;vertical-align:1px}
  .sr{position:absolute;width:1px;height:1px;margin:-1px;padding:0;border:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap}
  /* tabela dos cards: nome à esquerda, três colunas de número à direita */
  .ot{table-layout:fixed;margin-top:0}
  .ot th{vertical-align:bottom;white-space:normal;line-height:1.2;padding:0 0 6px 4px}
  .ot td{height:44px;padding:6px 0 6px 4px;vertical-align:middle}
  .ot th:first-child,.ot td:first-child{padding-left:0}
  .ot td b{font-size:var(--fs-4)}
  .ot td small{display:block;line-height:1.25}
  .ot td.kd{color:var(--txt-2)}
  .ot td.nodata{font-size:var(--fs-2);white-space:normal}
  .ot tr.clk{cursor:pointer}
  .ot tr.clk:active td,.optable tr.clk:active td{background:var(--panel2)}
  .ot col.c-w{width:88px} .ot col.c-k{width:44px} .ot col.c-r{width:52px}
  .opcell{display:flex;align-items:center;flex-wrap:wrap;gap:3px 6px;min-width:0}
  .opn{font-weight:600;font-size:var(--fs-4);color:var(--txt);white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}
  tr.clk:focus-visible{outline:2px solid var(--gold);outline-offset:-2px}
  .sortb:focus-visible{outline:2px solid var(--gold);outline-offset:-2px;border-radius:var(--r-1)}
  .star{color:var(--gold);font-size:var(--fs-3);line-height:1}
  .chipx{font-size:var(--fs-1);font-weight:700;letter-spacing:var(--ls-caps);text-transform:uppercase;color:var(--muted);background:var(--chip);border:1px solid var(--chipline);border-radius:var(--r-1);padding:1px 5px;white-space:nowrap}
  .otag{flex:1 0 100%;font-size:var(--fs-2);color:var(--muted);line-height:1.25}
  .fchips{display:flex;gap:7px;margin-bottom:6px}
  .fchip{font-size:var(--fs-3);min-height:40px;padding:0 14px;border-radius:var(--r-1);background:var(--chip);border:1px solid var(--chipline);font-weight:600;color:var(--muted);cursor:pointer}
  .fchip.on{color:var(--txt);border-color:var(--gold);background:rgba(244,194,13,.08)}
  /* tabela geral: colunas de largura fixa, cabeçalho é botão de ordenar */
  .optable{table-layout:fixed;margin-top:4px}
  .optable td:last-child{white-space:normal}
  .optable tr.clk{cursor:pointer}
  .optable tr.dim{color:var(--muted)}
  .optable th{padding:0;white-space:normal;vertical-align:bottom;line-height:1.15}
  .optable th:first-child{padding:0 0 4px 4px}
  .optable td{padding:6px 4px}
  .optable td:first-child{padding-left:2px}
  .optable col.c-r{width:11%} .optable col.c-w{width:24%} .optable col.c-k{width:12%} .optable col.c-h{width:12%} .optable col.c-f{width:16%}
  .sortb{display:flex;align-items:flex-end;justify-content:flex-end;width:100%;min-height:40px;padding:0 4px 4px;font:inherit;font-weight:700;letter-spacing:inherit;text-transform:inherit;line-height:1.15;text-align:right;color:inherit;background:none;border:0;border-bottom:2px solid transparent;cursor:pointer}
  .optable th.on .sortb{color:var(--gold);border-bottom-color:var(--gold)}
  .sd{display:inline-flex;flex:none;line-height:0}
  .sd .ic{width:14px;height:14px;stroke-width:2.1}
  .sd.def{color:var(--def)} .sd.atk{color:var(--atk-t)}
  .otwrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
  @media(max-width:560px){
    #allops{margin-left:-16px;margin-right:-16px;border-radius:0;border-left:0;border-right:0;padding-left:6px;padding-right:6px}   /* tabela densa: encosta na borda da tela */
    .optable{min-width:346px}
    .optable col.c-r{width:52px} .optable col.c-w{width:54px} .optable col.c-k{width:40px} .optable col.c-h{width:42px} .optable col.c-f{width:66px}
    .optable th{font-size:var(--fs-1);letter-spacing:.2px}
    .sortb{padding:0 2px 4px 0}
    .optable td{font-size:var(--fs-3)}
    .optable td small{display:none}
    .optable .opn{font-size:var(--fs-3)}
    .opcell{gap:3px 4px}
  }
  @media(max-width:359px),(min-width:900px) and (max-width:1049px){      /* card estreito: celular pequeno ou 3 colunas em tela média */
    .opcard{padding:12px}
    .ot col.c-w{width:78px} .ot col.c-k{width:36px} .ot col.c-r{width:54px}
    .opn{font-size:var(--fs-3)}
  }

  /* SQUAD */
  @media(min-width:900px){ .sqgrid{display:grid;grid-template-columns:1fr 1fr;column-gap:16px} }

  /* EVOLUÇÃO */
  .evlay{display:grid;gap:12px}
  .evo{padding:16px}
  .evo h3{display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:var(--fs-3);color:var(--muted);text-transform:uppercase;letter-spacing:1px}
  .evo h3 .lg{display:inline-flex;align-items:center;gap:6px;font-size:var(--fs-2);font-weight:700;letter-spacing:0;text-transform:none;font-variant-numeric:tabular-nums}
  .evo h3 .lg i{width:18px;border-top:2px dashed currentColor;opacity:.7}
  .evo .cap{margin-top:3px;font-size:var(--fs-2);color:var(--muted)}
  .sp{--pl:22px;--pr:22px;margin-top:4px}
  .sp.g{--c:var(--play)} .sp.y{--c:var(--gold)}
  .sp .plot{position:relative;height:116px;margin:30px var(--pr) 0 var(--pl)}      /* os 30 px de cima são do número do ponto mais alto */
  .sp svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
  .sp .ln{fill:none;stroke:var(--c);stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}
  .sp .s0{stop-color:var(--c);stop-opacity:.22} .sp .s1{stop-color:var(--c);stop-opacity:0}
  .sp .ref{stroke:var(--muted);stroke-opacity:.55;stroke-width:1;stroke-dasharray:3 4}
  .sp .dot{position:absolute;width:10px;height:10px;margin:-5px 0 0 -5px;border-radius:50%;background:var(--c);box-shadow:0 0 0 2px var(--panel)}
  .sp .dot.now{width:14px;height:14px;margin:-7px 0 0 -7px;box-shadow:0 0 0 2px var(--panel),0 0 0 4px var(--c)}
  .sp .val{position:absolute;transform:translate(-50%,-100%);margin-top:-11px;font-size:var(--fs-3);font-weight:700;color:var(--c);font-variant-numeric:tabular-nums;white-space:nowrap}
  .sp .val.l{transform:translate(-82%,-100%)} .sp .val.r{transform:translate(-18%,-100%)}      /* sai de cima do traço que chega ao ponto */
  .sparklbl{position:relative;height:16px;margin:12px var(--pr) 0 var(--pl)}
  .sparklbl span{position:absolute;top:0;transform:translateX(-50%);font-size:var(--fs-2);font-weight:700;color:var(--muted);letter-spacing:.3px;white-space:nowrap}
  .sparklbl span.now{color:var(--txt)}
  .evhead,.evrow{display:flex;gap:8px;align-items:center;font-variant-numeric:tabular-nums}
  .evhead{padding-bottom:7px;font-size:var(--fs-1);color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
  .evo h3+.evhead{margin-top:12px}
  .evrow{padding:11px 0;border-top:1px solid var(--hair);font-size:var(--fs-3)}
  .evrow .sn{width:118px;flex:none;font-weight:700}
  .evrow .sn small{display:block;font-weight:500;color:var(--muted);font-size:var(--fs-2)}
  .evrow.now .sn{color:var(--gold)}
  .evhead .sn{width:118px;flex:none}
  .cell{flex:1;text-align:right;color:var(--muted)} .cell b{color:var(--txt)}
  .evhead .cell:nth-child(2),.evrow .cell:nth-child(2){text-align:left}      /* a pílula do pico alinha com o nome da season */
  .rkb2{font-size:var(--fs-2);font-weight:800;padding:2px 6px;border-radius:var(--r-1)}
  @media(max-width:560px),(min-width:900px){      /* tabela estreita (celular ou coluna do desktop): a season ocupa uma linha e os 4 números ficam embaixo */
    .evhead .sn{display:none}
    .evhead,.evrow{display:grid;grid-template-columns:minmax(78px,1.3fr) minmax(58px,1fr) minmax(36px,.7fr) minmax(56px,.9fr);column-gap:6px;row-gap:7px}
    .evhead{letter-spacing:.3px}
    .evrow .sn{grid-column:1/-1;width:auto;display:flex;align-items:baseline;gap:8px}
    .evrow .sn small{display:inline}
    .evrow .cell .d{display:block;margin-left:0}
  }
  @media(max-width:560px){ .sp.thin .alt{display:none} }       /* 7+ seasons: números e rótulos alternados saem pra não encavalar (os pontos ficam todos) */
  @media(min-width:900px){            /* gráficos empilhados à esquerda, tabela de seasons à direita */
    .evlay{grid-template-columns:1fr 1fr;align-items:start}
    .evlay .tbl{grid-column:2;grid-row:1 / span 2}
    .sp .plot{height:140px}
  }

  nav.bottom{position:fixed;left:0;right:0;bottom:0;z-index:60;background:rgba(13,14,18,.92);backdrop-filter:blur(16px);border-top:1px solid var(--line);display:flex;height:calc(var(--nav-h) + env(safe-area-inset-bottom));padding-bottom:env(safe-area-inset-bottom)}
  nav.bottom button{position:relative;flex:1 1 auto;min-width:0;padding:0 2px;background:none;border:none;color:var(--muted);font:inherit;font-size:var(--fs-1);font-weight:700;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;cursor:pointer;letter-spacing:.02em}
  nav.bottom button.on::before{content:"";position:absolute;top:-1px;left:50%;width:26px;height:3px;margin-left:-13px;border-radius:0 0 var(--r-1) var(--r-1);background:var(--gold)}
  nav.bottom button .ic{width:22px;height:22px}
  nav.bottom button.on{color:var(--gold)}

  .sheetbg{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:90;display:none}
  .sheetbg.open{display:block}
  .sheet{position:fixed;left:0;right:0;bottom:0;z-index:91;background:var(--panel2);border-top-left-radius:18px;border-top-right-radius:18px;border:1px solid var(--line);padding:18px 18px calc(18px + env(safe-area-inset-bottom));transform:translateY(105%);transition:transform .22s ease;max-width:560px;margin:0 auto;max-height:80vh;overflow:auto}
  .sheet.open{transform:none}
  .sheet h3{font-size:var(--fs-4);margin-bottom:12px}
  .sheet h3.h3s{margin:14px 0 8px}
  .fsrc.mb{margin:0 0 10px}
  .grab{width:38px;height:4px;border-radius:var(--r-1);background:#333a46;margin:0 auto 14px}
  .srow{display:flex;align-items:center;gap:11px;padding:12px 12px;border-radius:var(--r-2);border:1px solid var(--line);background:var(--panel);margin-bottom:9px;cursor:pointer}
  .srow.on{border-color:var(--gold);background:rgba(244,194,13,.06)}
  .srow .sname{font-weight:800;font-size:var(--fs-4)}
  .srow .smeta{font-size:var(--fs-2);color:var(--muted);margin-top:1px}
  .srow .srk{margin-left:auto;font-size:var(--fs-2);font-weight:800;padding:3px 9px;border-radius:var(--r-3)}
  .legrow{display:flex;gap:10px;align-items:baseline;padding:7px 0;font-size:var(--fs-3);color:var(--muted);border-top:1px solid #232833}
  .legrow:first-of-type{border-top:none}
  .legrow b{font-size:var(--fs-4);width:30px;flex:none;text-align:center}
  .legrow b .ic{width:18px;height:18px;vertical-align:-.25em}

  .foot{margin:26px 0 10px;color:var(--muted);font-size:var(--fs-2);text-align:center}

  /* COACH */
  .cgoal{padding:14px 16px;border-left:3px solid var(--gold)}
  .cg-top{display:flex;gap:12px;align-items:center}
  .cg-l{font-size:var(--fs-2);color:var(--muted);text-transform:uppercase;letter-spacing:.7px;font-weight:700}
  .cg-v{font-size:var(--fs-4);margin-top:2px} .cg-v b{font-weight:800}
  .cg-s{font-size:var(--fs-3);color:var(--muted);margin-top:3px} .cg-s b{color:var(--txt)}
  .cg-s.gap{margin-top:10px} .cg-s.gap2{margin-top:6px}
  .cg-bar{height:8px;margin:14px 0 6px;border-radius:var(--r-pill);background:var(--track);overflow:hidden}
  .cg-bar i{display:block;height:100%;min-width:4px;border-radius:inherit;background:var(--gold)}
  .cg-ends{display:flex;justify-content:space-between;font-size:var(--fs-1);font-weight:700;letter-spacing:var(--ls-caps);color:var(--muted);font-variant-numeric:tabular-nums}
  .ctable{width:100%;border-collapse:collapse;font-size:var(--fs-3);font-variant-numeric:tabular-nums;margin-top:10px}
  .ctable th{font-size:var(--fs-1);color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:700;text-align:right;padding:0 4px 6px}
  .ctable td{padding:7px 4px;border-top:1px solid var(--hair);text-align:right;color:var(--muted);white-space:nowrap}
  .ctable td b{color:var(--txt)}
  .ctable th:first-child,.ctable td:first-child{text-align:left;color:var(--txt);white-space:normal}
  .ctable small{color:var(--muted);font-size:var(--fs-2)}
  .ctable td.csub{font-size:var(--fs-1);color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:700;padding-top:12px;text-align:left}
  .cbox{padding:4px 16px 12px}
  .fcards{display:grid;grid-template-columns:1fr;gap:12px}
  .grp{display:flex;align-items:baseline;flex-wrap:wrap;gap:1px 10px;margin:24px 2px 10px;font-size:var(--fs-4);font-weight:800;color:var(--txt)}
  .grp small{font-size:var(--fs-2);font-weight:500;color:var(--muted)}
  .fc{scroll-margin-top:72px}
  .fc.flash{animation:flash 1.4s ease-out}
  @keyframes flash{0%{box-shadow:0 0 0 3px rgba(244,194,13,.9)}100%{box-shadow:0 0 0 3px rgba(244,194,13,0)}}
  @media(prefers-reduced-motion:reduce){.fc.flash{animation:none}}

  /* CARD: uma anatomia só — título · manchete · legenda · tabela ou barras · leitura · nota */
  .fc>summary{display:block;position:relative;list-style:none;cursor:pointer;min-height:44px;padding:14px 44px 14px 16px;border-radius:var(--r-3)}
  .fc>summary::-webkit-details-marker{display:none}
  .fc>summary:focus-visible{outline:2px solid var(--gold);outline-offset:-2px}
  .fc .chev{position:absolute;right:14px;top:13px;width:20px;height:20px;color:var(--muted);transition:transform .15s}
  .fc[open] .chev{transform:rotate(180deg)}
  .fc.in-plan{border-left:3px solid var(--gold)}
  .fc .cb{padding:0 16px 14px}
  .ct{display:flex;align-items:center;flex-wrap:wrap;gap:4px 8px;font-size:var(--fs-2);font-weight:700;text-transform:uppercase;letter-spacing:var(--ls-caps);color:var(--muted)}
  .ct .sub{text-transform:none;letter-spacing:0;font-weight:500}
  .mark,.exp{padding:1px 7px;border-radius:var(--r-pill);background:rgba(244,194,13,.14);color:var(--gold);font-size:var(--fs-1);letter-spacing:.06em}
  .hl{display:flex;align-items:flex-start;gap:10px;margin-top:10px}
  .hl .hs{flex:1 1 0;min-width:0}
  .hl .hs b{display:block;font-size:var(--fs-7);font-weight:800;line-height:1.05;font-variant-numeric:tabular-nums}
  .hl .hs span{display:block;margin-top:4px;font-size:var(--fs-2);color:var(--muted);line-height:1.25}
  .hl .x{flex:none;margin-top:8px;font-style:normal;font-size:var(--fs-5);font-weight:600;color:var(--muted)}
  .hl.txt .hs b{font-size:var(--fs-6)}
  .cap{font-size:var(--fs-3);color:var(--muted);line-height:1.4}
  .sub2{margin-top:14px;font-size:var(--fs-3);font-weight:700;color:var(--txt)}
  .empty{color:var(--muted);font-size:var(--fs-3)}
  .read,.fread{margin-top:10px;font-size:var(--fs-3);line-height:1.55;color:var(--txt-2)}
  .read b,.fread b{color:var(--txt)}
  .note,.fsrc{margin-top:8px;font-size:var(--fs-2);color:var(--muted);line-height:1.4}

  /* barras: a barra desenha o %, escrito ao lado; "N de M" é o apoio */
  .bars{display:flex;flex-direction:column;gap:10px;margin:12px 0 4px}
  .bu{font-size:var(--fs-1);font-weight:700;text-transform:uppercase;letter-spacing:var(--ls-caps);color:var(--muted)}
  .br .bt{display:flex;justify-content:space-between;align-items:baseline;gap:10px;font-size:var(--fs-3)}
  .br .bl{min-width:0;color:var(--muted)}
  .br.me .bl{color:var(--txt);font-weight:700}
  .br .bv{flex:none;display:flex;align-items:baseline;gap:6px;font-variant-numeric:tabular-nums}
  .br .bv b{font-size:var(--fs-4);color:var(--txt)}
  .br .bv small{font-size:var(--fs-2);color:var(--muted)}
  .br .bb{height:8px;margin-top:5px;border-radius:var(--r-1);background:var(--track);overflow:hidden}
  .br .bb i{display:block;height:100%;border-radius:var(--r-1);background:var(--neutral)}
  .br.me .bb i{background:var(--gold)}

  @media(min-width:900px){
    .fcards{grid-template-columns:repeat(2,1fr)}
    body{padding-bottom:24px}
    nav.bottom{display:none}
    .desktabs{display:flex}
    .kgrid{grid-template-columns:repeat(4,1fr)}
    .changed{grid-template-columns:1fr 1fr}
    .tier{grid-template-columns:repeat(3,1fr)}
    .maps{grid-template-columns:repeat(2,1fr)}
    .picks{display:grid;grid-template-columns:1fr 1fr}
    .pside+.pside{border-top:0;border-left:1px solid var(--line)}
    .ops{grid-template-columns:repeat(3,1fr)}
    .opcard.gap{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);column-gap:32px;align-items:start}
    .opcard.gap h3{grid-column:1/-1}
    .opcard.gap .fsrc{margin-top:10px;font-size:var(--fs-3);line-height:1.5}
  }
</style>
</head>
<body>
__SPRITE__
<header>
  <div class="hbar">
    <a class="hbrand" href="index.html" title="Ver o squad">
      <svg class="logo" viewBox="0 0 64 64" aria-hidden="true"><use href="#sl-logo"/></svg>
      <span class="brand"><b class="wm">SIEGE<em>·</em>LAB</b><small id="subline"></small></span>
    </a>
    <nav class="desktabs" id="desktabs" aria-label="Seções"></nav>
    <button class="seasonsel" id="seasonsel" type="button" aria-label="Trocar de season" aria-haspopup="dialog">
      <span class="sv" id="ss-season"></span>
      <span class="rk" id="ss-rank"></span>
      <svg class="cv" viewBox="0 0 10 10" aria-hidden="true"><path d="M2 3.5 5 6.5 8 3.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>
    <button class="qbtn" id="sharebtn" type="button" aria-label="Compartilhar"><svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-share"/></svg></button>
    <button class="qbtn" id="helpbtn" type="button" aria-label="Como ler">?</button>
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
<div class="poptip" id="poptip" role="status" aria-live="polite"></div>

<script>
const SNAPSHOTS = __DATA__;
const PLAYER = __PLAYER__;
const PLAYBOOK = __PLAYBOOK__;
const NAMES = __NAMES__;              // slug -> nome de quem é do squad
const BRAND = __BRAND__;              // geometria do logo e do emblema (brand.py): card de compartilhar e rankEmblem

/* ---------- base ---------- */
const esc = s => String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fx=(v,d)=>Number(v).toFixed(d).replace(".",",");   // decimal com vírgula; o milhar vem do nf()
const byName = l => Object.fromEntries((l||[]).map(x=>[x.name,x]));
const wrClass = w => w>=55?"good":(w>=50?"mid":"low");
const ROM=["","I","II","III","IV","V"];

/* ícone do sprite (mesmo traço da navegação) */
const ic=(n,c)=>`<svg class="ic${c?" "+c:""}" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${n}"/></svg>`;
/* ° = amostra curta; a regra aparece no toque (e no title, pro mouse) */
const SMP={m:"Menos de 4 partidas: amostra curta, indício e não veredito.",o:"Menos de 8 rounds: amostra curta, indício e não veredito."};
const smp=k=>`<span class="smp" tabindex="0" role="button" data-tip="${SMP[k]}" title="${SMP[k]}">°</span>`;
/* faixa informativa com ícone */
const bnr=(i,t,c)=>`<div class="banner${c?" "+c:""}">${ic(i)}<p>${t}</p></div>`;

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
function emblemBody(color, div, champ){      // miolo do emblema (grade 48×48): o card de compartilhar reaproveita
  const R=["","I","II","III","IV","V"], E=BRAND.emb;
  const label = champ ? "★" : (R[div]||"");
  return `<polygon points="${E.out}" fill="${color}" stroke="rgba(0,0,0,.42)" stroke-width="1.3"/>
    <polygon points="${E.hl}" fill="rgba(255,255,255,.15)"/>
    <polygon points="${E.inn}" fill="none" stroke="rgba(255,255,255,.34)" stroke-width="1.1"/>
    <text x="24" y="25.5" fill="#fff" stroke="rgba(0,0,0,.45)" stroke-width="3" paint-order="stroke"
      font-size="${champ?18:16}" font-weight="800" text-anchor="middle" dominant-baseline="central"
      font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif">${label}</text>`;
}
function rankEmblem(color, div, champ, size){
  size = size||52;
  return `<svg class="remb" width="${size}" height="${size}" viewBox="0 0 48 48" aria-hidden="true">${emblemBody(color,div,champ)}</svg>`;
}

function delta(c,p,dec=0,cnt=false){     // seta = quanto mudou; toque mostra "antes → agora". cnt = contagem (partidas): cinza, nem bom nem ruim
  if(c==null||p==null) return "";
  const d=c-p, thr=dec?0.005:0.5, pv=fx(p,dec), cv=fx(c,dec);
  if(Math.abs(d)<thr){ const t=`estável (${cv})`; return `<span class="d eq" tabindex="0" role="button" data-tip="${t}" title="${t}">=</span>`; }
  const up=d>0, t=`${up?'subiu':'caiu'}: antes ${pv} → agora ${cv}`;
  return `<span class="d ${cnt?'nt':(up?'up':'dn')}" tabindex="0" role="button" data-tip="${t}" title="${t}">${up?'▲':'▼'}${fx(Math.abs(d),dec)}</span>`;
}
const tierOf = wr => wr>=55?"play":(wr<40?"ban":"neu");

/* ---------- INÍCIO ---------- */
function renderInicio(){
  const cur=active, base=baselineOf(cur);
  const k=cur.kpis, pk=(base||{}).kpis||{};
  const curRP = (k.latestRP!=null?k.latestRP:k.peakRP);
  const rk=rankInfo(curRP), peak=rankInfo(k.peakRP);
  const pbRP = base ? (base.kpis.latestRP!=null?base.kpis.latestRP:base.kpis.peakRP) : null;
  const hasWL = k.wins!=null&&k.losses!=null;
  const wl = hasWL ? `${k.wins}-${k.losses}` : "—";
  const noRes = hasWL ? k.matches-(k.wins+k.losses) : 0;      // partida contada que não saiu como vitória nem derrota
  const banner = base
    ? bnr("compare", `Comparando <b>${esc(cur.season)}</b> com <b>${esc(base.season)}</b> (${esc(base.seasonLabel||"")}).<span class="bsub">Setas ▲▼ = quanto mudou; toque numa pra ver o antes → agora. Em porcentagem, conta em pontos (50% → 53% = ▲3).</span>`)
    : bnr("pin", `Season mais antiga carregada — sem comparação. Carregue outra season pra ver as variações.`);

  // o que mudou (mapas presentes nas duas)
  let changed = "";
  if(base){
    const pb=byName(base.maps);
    const movers = cur.maps.filter(m=>pb[m.name]&&(m.matches>=4)&&(pb[m.name].matches>=4))
      .map(m=>({name:m.name, now:m.seasonWR, was:pb[m.name].seasonWR, d:m.seasonWR-pb[m.name].seasonWR}))
      .filter(m=>Math.abs(m.d)>=3);
    const ups=movers.filter(m=>m.d>0).sort((a,b)=>b.d-a.d).slice(0,3);
    const dns=movers.filter(m=>m.d<0).sort((a,b)=>a.d-b.d).slice(0,3);
    const row=m=>`<div class="chrow"><span class="nm">${esc(m.name)}</span><span class="vv"><span>${m.was.toFixed(0)}→${m.now.toFixed(0)}%</span>${delta(m.now,m.was,0)}</span></div>`;
    const none=`<div class="chrow"><span class="vv">—</span></div>`;
    changed = `<h2 class="sec">O que mudou desde ${esc(base.season)}<span class="hint">vitórias por mapa</span></h2>
      <div class="changed">
        <div class="chcol up"><h4>${ic("up-right")} Subiram</h4>${ups.map(row).join("")||none}</div>
        <div class="chcol dn"><h4>${ic("down-right")} Caíram</h4>${dns.map(row).join("")||none}</div>
      </div>`;
  }

  const bans=cur.maps.filter(m=>tierOf(m.seasonWR)==="ban"&&m.matches>=4).sort((a,b)=>a.seasonWR-b.seasonWR);
  const plays=cur.maps.filter(m=>tierOf(m.seasonWR)==="play"&&m.matches>=6).sort((a,b)=>b.seasonWR-a.seasonWR);
  const dM=cur.operatorsDef[0], aM=cur.operatorsAtk[0], cM=cur.operatorsCut[0];
  const g=nextGoal(), pace=rpPace();
  const goal = g ? `<div class="goal"><div class="gtop"><span class="gi">${ic("up-right")}</span><span>Faltam <b>${g.need} RP</b> pra <b style="color:${g.color}">${g.name}</b></span></div>
      <div class="gbar" role="img" aria-label="${100-g.need}% da divisão"><i style="width:${100-g.need}%"></i></div>
      <div class="gsub">Cada vitória ≈ +${Math.round(pace?pace.win:25)} RP</div></div>` : "";

  document.getElementById("scr-inicio").innerHTML = `
    <div class="glance">
      <div class="emb">
        ${rankEmblem(rk.color, rk.div, rk.champ, 56)}
        <div class="rn" style="color:${rk.color}">${rk.name}</div>
        <div class="pk"><i>pico</i>${peak.name}</div>
      </div>
      <div class="gstats">
        <div class="gst"><div class="l">RP</div><div class="v">${curRP.toLocaleString('pt-BR')}</div><div class="dd">${delta(curRP,pbRP,0)}</div></div>
        <div class="gst"><div class="l">K/D</div><div class="v">${fx(k.kd,2)}</div><div class="dd">${delta(k.kd,pk.kd,2)}</div></div>
        <div class="gst"><div class="l">V / D</div><div class="v">${wl}</div><div class="dd"></div></div>
      </div>
    </div>
    ${goal}
    <h2 class="sec">Plano de jogo<span class="hint">mapas e operadores</span></h2>
    <div class="plan">
      <div class="pi"><div class="ico ban">${ic("ban")}</div><div><b>Bane ${esc(bans[0]?.name||"—")}.</b> <span>${bans.length>1?"Depois "+esc(bans.slice(1,3).map(m=>m.name).join(" / "))+". ":""}Seus piores mapas.</span></div></div>
      <div class="pi"><div class="ico play">${ic("check")}</div><div><b>Force ${esc(plays.slice(0,4).map(m=>m.name).join(", ")||"—")}.</b> <span>Vote neles sempre.</span></div></div>
      ${dM?`<div class="pi"><div class="ico def">${ic("shield")}</div><div><b>Defesa: ${esc(dM.name)} (${dM.wr}%).</b> <span>Seu melhor defensor.${cur.operatorsDef[1]?" Segunda opção: "+esc(cur.operatorsDef[1].name)+".":""}</span></div></div>`:""}
      ${aM?`<div class="pi"><div class="ico atk">${ic("sword")}</div><div><b>Ataque: ${esc(aM.name)} (${aM.wr}%).</b> <span>O pick de cada mapa está na aba Mapas.</span></div></div>`:""}
      ${cM?`<div class="pi"><div class="ico ban">${ic("x")}</div><div><b>Repense ${esc(cM.name)} (${cM.wr}%).</b> <span>Muito jogado e perde mais do que ganha — corte ou reposicione.</span></div></div>`:""}
    </div>
    <h2 class="sec">Números da season</h2>
    <div class="kgrid2">
      <div class="ktile"><div class="v">${k.matches}${delta(k.matches,pk.matches,0,true)}</div><div class="l">Partidas</div>${noRes>0?`<div class="kn">${noRes} sem resultado</div>`:""}</div>
      <div class="ktile"><div class="v">${fx(k.winRate,1)}%${delta(k.winRate,pk.winRate,1)}</div><div class="l">Vitórias</div></div>
    </div>
    ${banner}
    ${formaRecente()}
    ${changed}`;
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
  if(t==="ban" && rr.w>rr.l) return `<div class="rnote up"><i>${ic("up-right")}</i> Você vem <b>ganhando</b> aqui (${rr.w}V-${rr.l}D nas últimas partidas): o "banir" da season pode estar desatualizado — reavalie.</div>`;
  if(t==="play" && rr.l>rr.w) return `<div class="rnote dn"><i>${ic("down-right")}</i> <b>Esfriou</b> (${rr.w}V-${rr.l}D nas últimas partidas) apesar de ser mapa forte — cuidado ao forçar.</div>`;
  return "";
}

/* ---------- MAPAS ---------- */
const mapId=n=>String(n).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"");   // id estável: chip → linha do mapa
function tierChips(cur, base, tier){
  const pb = base?byName(base.maps):{};
  return cur.maps.filter(m=>tierOf(m.seasonWR)===tier)
    .sort((a,b)=>((a.matches<4)-(b.matches<4))||(b.seasonWR-a.seasonWR))
    .map(m=>{
      const inner=`${esc(m.name)}<small>${m.seasonWR.toFixed(0)}%${m.matches<4?smp("m"):""}${delta(m.seasonWR,(pb[m.name]||{}).seasonWR,0)}</small>`;
      return m.matches>=1
        ?`<a class="chipm" href="#c-map-${mapId(m.name)}" onclick="seeCard('map-${mapId(m.name)}');return false">${inner}</a>`
        :`<span class="chipm">${inner}</span>`;
    }).join("") || `<span class="chipm none">—</span>`;
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
function bestPick(m, side){            // o 1º da lista que o detalhe mostra (mesma conta de pickRows)
  const c=candidates(m, side);
  if(c.src==="playbook"){
    const n=(((PLAYBOOK.maps||{})[m.name]||PLAYBOOK.default||{})[side]||[])[0];
    return {src:c.src, name:n||""};
  }
  const base=baseOf();
  const r=c.list.map(o=>({o, sc:scoreOp(o,base)})).sort((a,b)=>b.sc.score-a.sc.score)[0];
  return r?{src:c.src, name:r.o.name, wr:r.o.wr, small:(r.o.rounds||0)<8}:{src:c.src, name:""};
}
const SRC_SHORT={season:"da sua season",playbook:"referência geral"};
function pickCell(m, side){            // o melhor de cada lado, na linha fechada do mapa
  const b=bestPick(m, side);
  return `<div class="mpk ${side}"><i>${b.src==="playbook"?"Pegue":"Melhor"} ${side==="def"?"na defesa":"no ataque"}</i>${b.name
    ?`<p><b>${esc(b.name)}</b>${b.wr!=null?`<span class="v ${wrClass(b.wr)}">${b.wr}%${b.small?smp("o"):""}</span>`:""}</p>${SRC_SHORT[b.src]?`<small>${SRC_SHORT[b.src]}</small>`:""}`
    :`<p class="empty">—</p>`}</div>`;
}
function mapTip(m){
  const a=m.atkWR||0, d=m.defWR||0, diff=a-d;
  if(diff<=-8) return `Seu ataque aqui é o ponto fraco: ${a.toFixed(0)}% contra ${d.toFixed(0)}% na defesa. Gaste utilidade pra abrir — EMP e hard breach — e entre junto, não em pinga-pinga.`;
  if(diff>=8) return `Sua defesa aqui é o ponto fraco: ${d.toFixed(0)}% contra ${a.toFixed(0)}% no ataque. Não segure passivo: atrase com roam e jogue o retake.`;
  return `Lados equilibrados (atk ${a.toFixed(0)}% / def ${d.toFixed(0)}%). O round se decide na primeira troca — entre junto.`;
}
function formaRecente(){
  const ms=active.recentMatches;
  if(!ms||!ms.length) return "";
  const n=ms.length, w=ms.filter(m=>m.w).length, l=n-w;
  const netRP=ms.reduce((s,m)=>s+(m.rp||0),0);
  const posKD=ms.filter(m=>(m.kd||0)>=1).length;
  const tip=m=>esc(`${m.map} · ${m.w?'V':'D'} · K/D ${fx(m.kd||0,2)}`);
  const pips=ms.slice().reverse().map(m=>`<span class="pip ${m.w?'w':'l'}" data-tip="${tip(m)}" title="${tip(m)}"></span>`).join("");
  const byMap={};
  ms.forEach(m=>{byMap[m.map]=byMap[m.map]||{w:0,l:0}; m.w?byMap[m.map].w++:byMap[m.map].l++;});
  const cold=Object.entries(byMap).filter(([,v])=>v.w===0&&v.l>=2).map(([k,v])=>`${esc(k)} (${v.w}V-${v.l}D)`);
  const hot=Object.entries(byMap).filter(([,v])=>v.l===0&&v.w>=2).map(([k,v])=>`${esc(k)} (${v.w}V-${v.l}D)`);
  let streak=1; const sw=ms[0].w; for(let i=1;i<ms.length;i++){ if(ms[i].w===sw) streak++; else break; }
  const ins=[];                         // cada leitura: o fato (em cima) e o que fazer com ele (embaixo)
  if(!sw && streak>=2) ins.push({i:"pause",c:"cdn",f:`Você está numa <b>maré de ${streak} derrotas</b>`,a:`Considere uma pausa antes da próxima.`});
  if(sw && streak>=3) ins.push({i:"flame",c:"cup",f:`<b>${streak} vitórias seguidas</b>`,a:`Você está quente, aproveite enquanto dura.`});
  if(posKD/n>=0.6 && Math.abs(w-l)<=2) ins.push({i:"target",c:"cneu",f:`Em <b>${posKD} das ${n}</b> partidas seu K/D foi de 1,0 ou mais, mas o placar ficou <b>${w}V-${l}D</b>`,a:`O abate sozinho não está virando vitória. Jogue junto do time em vez de buscar frag solo.`});
  if(cold.length) ins.push({i:"snow",c:"cdn",f:`Sem vitória em <b>${cold.join(", ")}</b>`,a:`Bane no ranqueado.`});
  if(hot.length) ins.push({i:"flame",c:"cup",f:`Só vitórias em <b>${hot.join(", ")}</b>`,a:`Vale votar ${hot.length>1?"nesses mapas":"nesse mapa"}.`});
  const rpCls=netRP>0?'cup':(netRP<0?'cdn':'cmut');
  return `
    <h2 class="sec">Forma recente<span class="hint">últimas ${n} partidas</span></h2>
    <div class="forma">
      <div class="frec"><b>${w}</b><span>V</span> · <b>${l}</b><span>D</span></div>
      <div class="fpips">${pips}</div>
      <div class="faxis"><span>mais antiga</span><span>mais recente</span></div>
      <div class="fstats">
        <div class="fk"><div class="fl">RP no período</div><div class="fv ${rpCls}">${sg(netRP)}</div></div>
        <div class="fk"><div class="fl">Com K/D 1,0+</div><div class="fv">${posKD}/${n}</div></div>
      </div>
      ${ins.map(x=>`<div class="fins"><i class="${x.c}">${ic(x.i)}</i><p>${x.f}<span class="act">${x.a}</span></p></div>`).join("")}
    </div>`;
}
function renderMapas(){
  const cur=active, base=baselineOf(cur), pb=base?byName(base.maps):{};
  const rbm=recentByMap();
  const row=m=>{
    const t=tierOf(m.seasonWR), v={play:"PRIORIZE",neu:"NEUTRO",ban:"BANIR"}[t];
    const pm=pb[m.name]||{}, rr=rbm[m.name], rn=recencyNote(m,rr);
    const rbadge=rr?`<span class="rbadge ${rr.w>rr.l?'up':(rr.l>rr.w?'dn':'eq')}" title="resultado nas partidas recentes">${rn?ic(rr.w>rr.l?"up-right":"down-right"):""}últ. ${rr.w}V-${rr.l}D</span>`:"";
    const adbar=(cls,val)=>`<div class="adr ${cls}"><span class="adl ${cls}">${cls.toUpperCase()}</span><div class="adbar"><i style="width:${Math.max(3,val||0)}%"></i></div><span class="adv">${(val||0).toFixed(0)}%${delta(val,(cls==='atk'?pm.atkWR:pm.defWR),0)}</span></div>`;
    const pside=(cls,pbLbl,myLbl)=>{const c=candidates(m,cls); return `<div class="pside ${cls}"><div class="sh"><span class="ic"></span>${c.src==="playbook"?pbLbl:myLbl}<span class="src">${esc(srcLabel(c.src))}</span></div>${pickRows(m,cls)}</div>`;};
    const warn=(m.avoid?`<div class="mwarn avoid">${ic("ban")}<span><b>Evite:</b> ${esc(m.avoid)}</span></div>`:"")
             +(m.note?`<div class="mwarn note">${ic("warn")}<span>${esc(m.note)}</span></div>`:"");
    return `<details class="map mrow ${t}" id="c-map-${mapId(m.name)}"${WIDE()?" open":""}>
      <summary>
        <div class="mh"><span class="mn">${esc(m.name)}</span><span class="wr">${m.seasonWR.toFixed(0)}%${delta(m.seasonWR,pm.seasonWR,0)}</span>${ic("chev","chev")}</div>
        <div class="mm"><span class="verdict ${t}">${v}</span><span>${m.matches} ${m.matches===1?"partida":"partidas"}${m.matches<4?smp("m"):""}</span>${rbadge}</div>
        <div class="ad">${adbar('atk',m.atkWR)}${adbar('def',m.defWR)}</div>
        <div class="mpks">${pickCell(m,"atk")}${pickCell(m,"def")}</div>
        ${warn}
      </summary>
      <div class="strong">${strongSide(m)} <span>K/D ${fx(m.kd||0,2)}${delta(m.kd,pm.kd,2)}</span></div>
      <div class="picks">
        ${pside("atk","Pegue no ataque","Seus melhores no ataque")}
        ${pside("def","Pegue na defesa","Seus melhores na defesa")}
      </div>
      <div class="tip">${esc(mapTip(m))}</div>
      ${rn}
    </details>`;
  };
  const list=cur.maps.filter(m=>m.matches>=1).sort((a,b)=>((a.matches<4)-(b.matches<4))||(b.seasonWR-a.seasonWR));
  const main=list.filter(m=>m.matches>=4), short=list.filter(m=>m.matches<4);
  const opsNote = bnr("target", `Em cada mapa, os operadores sugeridos pra cada lado vêm do seu histórico (quando há dado) ou de uma referência geral — o rótulo ao lado diz qual. Os números são % de rounds ganhos · rounds jogados. <b>°</b> = amostra pequena (mapa com menos de 4 partidas, operador com menos de 8 rounds): indício, não veredito.`, "gap");
  document.getElementById("scr-mapas").innerHTML = `
    <h2 class="sec">Jogar vs banir<span class="hint">% de vitórias na season · toque no mapa pra abrir</span></h2>
    <div class="tier">
      <div class="tcol play"><div class="th"><span class="dot"></span>Priorize</div><div class="chips">${tierChips(cur,base,"play")}</div></div>
      <div class="tcol neu"><div class="th"><span class="dot"></span>Neutro</div><div class="chips">${tierChips(cur,base,"neu")}</div></div>
      <div class="tcol ban"><div class="th"><span class="dot"></span>Banir</div><div class="chips">${tierChips(cur,base,"ban")}</div></div>
    </div>
    <h2 class="sec">Mapa a mapa<span class="hint">ataque × defesa · toque pra ver o top 3 de cada lado</span></h2>
    ${opsNote}
    ${main.length?`<div class="maps">${main.map(row).join("")}</div>`:""}
    ${short.length?`<h3 class="grp">Poucas partidas<small>menos de 4 partidas: indício, não veredito</small></h3><div class="maps">${short.map(row).join("")}</div>`:""}`;
}

/* ---------- OPERADORES ---------- */
function rowKey(ev,el){               // Enter/Espaço na linha abre a ficha (seta e ° dentro da linha cuidam do próprio teclado)
  if(ev.target!==el) return;
  if(ev.key==="Enter"||ev.key===" "){ ev.preventDefault(); openOpSheet(el.dataset.op); }
}
function opTag(tag){                  // "main · 128 rds — fragga e perde" → main + nota; o "N rds" já tem coluna própria
  const p=String(tag||"").split(/\s+[·—]\s+/).map(x=>x.trim()).filter(Boolean);
  return {main:p.includes("main"), notes:p.filter(x=>x!=="main"&&!/^\d+ rds$/.test(x))};
}
function opPanel(list, pl){
  const p=byName(pl);
  if(!(list||[]).length) return `<div class="empty">—</div>`;
  const rows=list.map(o=>{
    const t=opTag(o.tag);
    return `<tr class="clk" tabindex="0" data-op="${esc(o.name)}" onclick="openOpSheet(this.dataset.op)" onkeydown="rowKey(event,this)">
      <td><div class="opcell"><span class="opn">${esc(o.name)}</span>${o.star?'<span class="star" aria-hidden="true">★</span><span class="sr">destaque</span>':""}${t.main?'<span class="chipx">main</span>':""}${t.notes.length?`<span class="otag">${esc(t.notes.join(" · "))}</span>`:""}</div></td>
      <td><b>${o.wr}%</b>${o.small?smp("o"):""}${delta(o.wr,(p[o.name]||{}).wr,0)}</td>
      <td class="kd">${o.kd!=null?fx(o.kd,2):"—"}</td>
      <td>${o.rounds!=null?o.rounds:"—"}</td></tr>`;
  }).join("");
  return `<table class="ctable ot"><colgroup><col><col class="c-w"><col class="c-k"><col class="c-r"></colgroup>
    <tr><th>Operador</th><th>Rounds ganhos</th><th>K/D</th><th>Rounds</th></tr>${rows}</table>`;
}
function renderOps(){
  const cur=active, base=baselineOf(cur)||{};
  document.getElementById("scr-ops").innerHTML = `
    <h2 class="sec">Onde investir<span class="hint">${base.season?`vs ${esc(base.season)}`:"sem season anterior pra comparar"}</span></h2>
    <div class="ops">
      <div class="opcard"><h3><span class="tag def">${ic("shield")}DEFESA</span> Suas mains</h3>${opPanel(cur.operatorsDef,base.operatorsDef)}</div>
      <div class="opcard"><h3><span class="tag atk">${ic("sword")}ATAQUE</span> Suas mains</h3>${opPanel(cur.operatorsAtk,base.operatorsAtk)}</div>
      <div class="opcard"><h3><span class="tag cut">${ic("x")}CORTE / REPENSE</span></h3>${opPanel(cur.operatorsCut,base.operatorsCut)}</div>
    </div>
    <div class="fsrc">Rounds ganhos = % dos rounds que o time venceu com o operador. ★ = destaque do lado (1º da lista, 55%+ e 15+ rounds). main = o mais jogado do lado. Quem tem menos de 15 rounds vem depois na lista. Toque num operador pra abrir a ficha.</div>
    ${hardBreachCard(cur)}
    ${cur.opsAll?`<h2 class="sec">Todos os operadores<span class="hint">${cur.opsAll.length} jogados nesta season</span></h2>
    <div class="cbox" id="allops"></div>`:""}`;
  renderOpsTable();
}
let opsFilter="all", opsSort="r";
const OPS_COLS=[["r","Rounds"],["wr","Rounds ganhos"],["kd","K/D"],["hs","HS%"],["fb","1º duelo"]];
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
    .map(([v,l])=>`<button type="button" class="fchip ${opsFilter===v?"on":""}" aria-pressed="${opsFilter===v}" onclick="opsFilter='${v}';renderOpsTable()">${l}</button>`).join("");
  const th=OPS_COLS.map(([k,l])=>`<th class="${opsSort===k?"on":""}" aria-sort="${opsSort===k?"descending":"none"}"><button type="button" class="sortb" onclick="opsSort='${k}';renderOpsTable()">${l}</button></th>`).join("");
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
      return `<tr class="clk${o.r<8?" dim":""}" tabindex="0" data-op="${esc(o.n)}" onclick="openOpSheet(this.dataset.op)" onkeydown="rowKey(event,this)">
        <td><div class="opcell"><span class="sd ${o.s==="d"?"def":"atk"}">${ic(o.s==="d"?"shield":"sword")}<span class="sr">${o.s==="d"?"Defesa":"Ataque"}</span></span><span class="opn">${esc(o.n)}</span>${o.r<8?smp("o"):""}</div></td>
        <td>${o.r}</td><td><b>${pf(o.w,o.r)}%</b> <small>${o.w} de ${o.r}</small></td>
        <td>${kd}</td><td>${hs}</td><td>${fb}</td></tr>`;
    }).join("");
  el.innerHTML=`<div class="fchips">${chips}</div>
    <div class="otwrap"><table class="ctable optable"><colgroup><col class="c-n"><col class="c-r"><col class="c-w"><col class="c-k"><col class="c-h"><col class="c-f"></colgroup><tr><th>Operador</th>${th}</tr>${rows}</table></div>
    <div class="fsrc">${ic("shield","cdef")} defesa · ${ic("sword","catk")} ataque. ° abaixo de 8 rounds: indicativo, não veredito (nas ordenações por rounds ganhos, K/D, HS% e 1º duelo, esses ficam no fim). 1º duelo = first bloods × first deaths do tracker. Toque num operador pra abrir a ficha.</div>`;
}
function hardBreachCard(cur){
  if(!cur.opsAll) return "";
  const got=HARD_BREACH.map(n=>cur.opsAll.find(o=>o.n===n)).filter(Boolean);
  if(!got.length) return "";
  const rows=HARD_BREACH.map(n=>{
    const o=cur.opsAll.find(x=>x.n===n);
    if(!o) return `<tr><td><div class="opcell"><span class="opn cmut">${esc(n)}</span></div></td><td class="nodata" colspan="2">sem rounds nesta season</td></tr>`;
    const kd=fx(o.k/Math.max(1,o.d),2);
    return `<tr class="clk" tabindex="0" data-op="${esc(o.n)}" onclick="openOpSheet(this.dataset.op)" onkeydown="rowKey(event,this)">
      <td><div class="opcell"><span class="opn">${esc(o.n)}</span></div></td>
      <td><b>${pf(o.w,o.r)}%</b>${o.r<8?smp("o"):""}<small>${o.w} de ${o.r}</small></td>
      <td class="kd">${kd}</td></tr>`;
  }).join("");
  const best=got.filter(o=>o.r>=15).sort((a,b)=>b.r-a.r)[0];
  const read=best
    ? `Sua opção com amostra real: <b>${esc(best.n)}</b> (${best.w} de ${best.r}, K/D ${fx(best.k/Math.max(1,best.d),2)}). Os outros quase não têm rounds — treine um segundo pra semana de ban.`
    : `Nenhum hard breach com amostra de verdade nesta season.`;
  return `<div class="opcard gap"><h3><span class="tag atk">${ic("sword")}ATAQUE</span> Hard breach — plano B</h3>
    <table class="ctable ot"><colgroup><col><col class="c-w"><col class="c-k"></colgroup>
    <tr><th>Operador</th><th>Rounds ganhos</th><th>K/D</th></tr>${rows}</table>
    <div class="fsrc">${read} O card do coach mostra o quanto rodar sem hard breach custa.</div></div>`;
}
function openOpSheet(name){
  const cur=active, o=(cur.opsAll||[]).find(x=>x.n===name);
  if(!o) return;
  const kd=fx(o.k/Math.max(1,o.d),2);
  const duel=(o.fb+o.fd)?`<b>${o.fb} de ${o.fb+o.fd}</b> (${pf(o.fb,o.fb+o.fd)}%)`:`— <small>não entra na 1ª troca</small>`;
  const stats=`<table class="ctable">
    <tr><td>Rounds</td><td><b>${o.r}</b> <small>em ${o.m} ${o.m===1?"partida":"partidas"}</small></td></tr>
    <tr><td>Rounds ganhos</td><td><b>${pf(o.w,o.r)}%</b> <small>${o.w} de ${o.r}</small></td></tr>
    <tr><td>Partidas ganhas</td><td><b>${pf(o.mw,o.m)}%</b> <small>${o.mw} de ${o.m}</small></td></tr>
    <tr><td>K/D</td><td><b>${kd}</b> <small>${o.k} × ${o.d} · ${o.a} assist.</small></td></tr>
    <tr><td>Abates na cabeça</td><td><b>${o.k?pf(o.hs,o.k)+"%":"—"}</b> <small>${o.hs} de ${o.k}</small></td></tr>
    <tr><td>1º duelo do round</td><td>${duel}</td></tr>
    <tr><td>Clutch</td><td><b>${o.cw}</b> ganhos · ${o.cl} perdidos</td></tr></table>`;
  const evo=SEASONS.map(s=>({s,e:(s.opsAll||[]).find(x=>x.n===name)})).filter(x=>x.e&&x.e.r>0);
  const evoHtml=evo.length>1?`<h3 class="h3s">Season a season</h3><table class="ctable"><tr><th>Season</th><th>Rounds ganhos</th><th>K/D</th></tr>${
    evo.map(({s,e})=>`<tr><td>${esc(s.season)}</td><td><b>${pf(e.w,e.r)}%</b> <small>${e.r} rds</small></td><td>K/D ${fx(e.k/Math.max(1,e.d),2)}</td></tr>`).join("")}</table>`:"";
  const mm=(cur.opsMaps||{})[name];
  const mapsHtml=mm&&mm.length?`<h3 class="h3s">Por mapa</h3><table class="ctable"><tr><th>Mapa</th><th>Rounds ganhos</th><th>K/D</th></tr>${
    mm.slice().sort((a,b)=>b[1]-a[1]).slice(0,4).map(r=>`<tr><td>${esc(r[0])}</td><td><b>${pf(r[2],r[1])}%</b> <small>${r[2]} de ${r[1]}</small></td><td>K/D ${fx(r[3]/Math.max(1,r[4]),2)}</td></tr>`).join("")}</table>`:"";
  const fr=((cur.coach||{}).opsRole||{})[name];
  const feedHtml=fr?`<h3 class="h3s">O que o kill feed mostra</h3><table class="ctable">
    <tr><td>Vivo no fim do round</td><td><b>${pf(fr[2],fr[0])}%</b> <small>${fr[2]} de ${fr[0]}</small></td></tr>
    <tr><td>1ª morte do time é você</td><td><b>${pf(fr[3],fr[0])}%</b></td></tr>
    <tr><td>Kill sua na abertura do round</td><td><b>${pf(fr[4],fr[0])}%</b> <small>${fr[4]} de ${fr[0]}</small></td></tr>
    <tr><td>Kill sua no fim do round</td><td><b>${pf(fr[5],fr[0])}%</b> <small>${fr[5]} de ${fr[0]}</small></td></tr></table>
    <div class="fsrc">Kill feed desta season (${fr[0]} rounds); pode divergir 1–2% do tracker.</div>`:"";
  const why=((PLAYBOOK.operators||{})[name]||{}).why;
  openSheet(`<h3>${esc(name)} <span class="tag sm ${o.s==="d"?"def":"atk"}">${ic(o.s==="d"?"shield":"sword")}${o.s==="d"?"DEFESA":"ATAQUE"}</span></h3>
    ${o.r<8?`<div class="fsrc mb">° amostra curta (${o.r} ${o.r===1?"round":"rounds"}) — leia como indicativo, não veredito.</div>`:""}
    ${stats}${evoHtml}${mapsHtml}${feedHtml}
    ${why?`<div class="fsrc">Função: ${esc(why)}</div>`:""}`);
}

/* ---------- EVOLUÇÃO ---------- */
function spark(o){                      // só o traço é SVG (estica à vontade); pontos, números e rótulos são HTML e não deformam
  const {vals,labels,key,fmt,ref,span,now,name}=o, n=vals.length;
  if(n<2) return `<div class="empty">Só 1 season carregada — o gráfico aparece com 2+.</div>`;
  let lo=Math.min(...vals,ref.v), hi=Math.max(...vals,ref.v);
  if(hi-lo<span){ const m=(hi+lo)/2; lo=m-span/2; hi=m+span/2; }         // amplitude mínima: variação pequena não vira penhasco
  const pad=(hi-lo)*.08; lo-=pad; hi+=pad;
  const X=i=>(100*i/(n-1)).toFixed(2), Y=v=>(100*(hi-v)/(hi-lo)).toFixed(2);
  const pts=vals.map((v,i)=>`${X(i)},${Y(v)}`).join(" ");
  const thin=n>6, alt=i=>thin&&((n-1-i)%2)?" alt":"";
  const steep=(a,b)=>Math.abs(vals[a]-vals[b])/(hi-lo)*(n-1)>1.3;       // inclinação que riscaria um número centralizado
  const side=i=>{ const L=i>0&&vals[i-1]>vals[i]&&steep(i-1,i), R=i<n-1&&vals[i+1]>vals[i]&&steep(i,i+1); return L&&!R?" r":(R&&!L?" l":""); };   // o número foge do lado de onde o traço íngreme vem/vai por cima
  const dots=vals.map((v,i)=>`<i class="dot${i===now?" now":""}" style="left:${X(i)}%;top:${Y(v)}%"></i><b class="val${side(i)}${alt(i)}" style="left:${X(i)}%;top:${Y(v)}%">${fmt(v)}</b>`).join("");
  const lbl=labels.map((l,i)=>`<span class="${i===now?"now":""}${alt(i)}" style="left:${X(i)}%">${esc(l)}</span>`).join("");
  const say=labels.map((l,i)=>`${l} ${fmt(vals[i])}`).join(", ");
  return `<div class="sp ${key==="g"?"g":"y"}${thin?" thin":""}" role="img" aria-label="${esc(name)} por season: ${esc(say)}. Linha tracejada em ${esc(ref.t)}.">
    <div class="plot"><svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      <defs><linearGradient id="sg-${key}" x1="0" y1="0" x2="0" y2="1"><stop class="s0" offset="0"/><stop class="s1" offset="1"/></linearGradient></defs>
      <polygon points="0,100 ${pts} 100,100" fill="url(#sg-${key})"/>
      <line class="ref" x1="0" x2="100" y1="${Y(ref.v)}" y2="${Y(ref.v)}" vector-effect="non-scaling-stroke"/>
      <polyline class="ln" points="${pts}" vector-effect="non-scaling-stroke"/></svg>
      ${dots}</div>
    <div class="sparklbl">${lbl}</div></div>`;
}
function renderEvo(){
  const chron = SEASONS.slice().sort((a,b)=>a.seasonOrder-b.seasonOrder); // antiga→nova
  const ids=chron.map(s=>s.season), now=chron.indexOf(active);
  const chart=(key,name,cap,vals,fmt,ref,span)=>`<div class="evo"><h3>${name}<span class="lg"><i></i>${ref.t}</span></h3><div class="cap">${cap}</div>${spark({vals,labels:ids,key,fmt,ref,span,now,name})}</div>`;
  const rows = chron.slice().reverse().map(s=>{
    const older = chron[chron.indexOf(s)-1];
    const p=older?older.kpis:{};
    const rk=rankInfo(s.kpis.peakRP);
    return `<div class="evrow${s===active?" now":""}"><span class="sn">${esc(s.season)}<small>${esc(s.seasonLabel||"")}</small></span>
      <span class="cell"><span class="rkb2" style="background:${rk.color}22;color:${rk.color}">${rk.name}</span></span>
      <span class="cell"><b>${fx(s.kpis.winRate,1)}%</b>${delta(s.kpis.winRate,p.winRate,1)}</span>
      <span class="cell"><b>${fx(s.kpis.kd,2)}</b>${delta(s.kpis.kd,p.kd,2)}</span>
      <span class="cell"><b>${s.kpis.matches}</b></span></div>`;
  }).join("");
  document.getElementById("scr-evo").innerHTML = `
    <h2 class="sec">Evolução<span class="hint">season a season</span></h2>
    <div class="evlay">
      ${chart("g","Vitórias","% das partidas ganhas em cada season",chron.map(s=>s.kpis.winRate),v=>v.toFixed(0)+"%",{v:50,t:"50%"},12)}
      ${chart("y","K/D","abates ÷ mortes em cada season",chron.map(s=>s.kpis.kd),v=>fx(v,2),{v:1,t:fx(1,2)},.4)}
      <div class="evo tbl"><h3>Seasons</h3>
      <div class="evhead"><span class="sn">Season</span><span class="cell">Pico</span><span class="cell">Vitórias</span><span class="cell">K/D</span><span class="cell">Partidas</span></div>
      ${rows}</div>
    </div>`;
}

/* ---------- COACH ---------- */
const pf=(a,b)=>b?Math.round(100*a/b):0;
const nf=n=>n==null?"—":Number(n).toLocaleString('pt-BR');
const sx=(v,d)=>{const t=fx(Math.abs(v),d);return (+t.replace(",",".")===0?"":(v>0?"+":"−"))+t};   // sinal: "+" ou "−" (menos de verdade, não hífen)
const sg=v=>sx(v,0);
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
    const rpf=v=>sg(rnd(v));
    const janela=`A cada 5 partidas você pode perder até <b>${kmax(5)}</b> e ainda subir: 2V-3D dá ${rpf(2*Wp-3*Lp)} RP e 3V-2D, ${rpf(3*Wp-2*Lp)} RP (em 4 partidas: até ${kmax(4)}).`;
    body=`<div class="cg-s gap">Seu ritmo nesta season: <b>${sg(Math.round(p.win))}</b> por vitória e <b>${sg(Math.round(p.loss))}</b> por derrota (${p.n} partidas). Com ${be}% de vitórias você já não perde RP.</div>
      <div class="cg-s gap2">${janela}</div>
      <table class="ctable"><tr><th>Vitórias</th><th>RP por partida</th><th>Partidas até ${esc(g.label)}</th></tr>
      ${sc.map(([w,l])=>{const x=per(w);return `<tr><td>${l}</td><td>${sx(x,1)}</td><td><b>${x>0.05?"~"+Math.ceil(g.need/x):"não sobe"}</b></td></tr>`;}).join("")}</table>
      <div class="fsrc">Cenário, não promessa: supõe que cada vitória e cada derrota continuem valendo a média desta season.</div>`;
  }
  const start=[1000,1500,2000,2500,3000,3500,4000,4500].filter(t=>t<=g.rp).pop()||0;     // início da faixa em que você está
  const pct=Math.max(0,Math.min(100,Math.round(100*(g.rp-start)/(g.target-start))));
  return `<div class="cgoal"><div class="cg-top">${rankEmblem(g.color,g.div,g.champ,44)}<div>
      <div class="cg-l">${g.mine?"Sua meta":"Próximo rank"}</div>
      <div class="cg-v"><b style="color:${g.color}">${esc(g.label)}</b> · faltam <b>${nf(g.need)} RP</b></div>
      <div class="cg-s">${nf(g.rp)} → ${nf(g.target)} RP</div></div></div>
      <div class="cg-bar" role="img" aria-label="${pct}% do caminho até ${esc(g.label)}"><i style="width:${pct}%"></i></div>
      <div class="cg-ends"><span>${nf(start)}</span><span>${nf(g.target)}</span></div>${body}</div>`;
}

/* chave, rótulo, unidade, casas, direção (1 = subir é bom · -1 = subir é ruim · 0 = estilo) */
const STYLE_ROWS=[
  ["roundWR","Rounds ganhos","%",0,1],
  ["atkRoundWR","Rounds ganhos no ataque","%",0,1],
  ["defRoundWR","Rounds ganhos na defesa","%",0,1],
  ["esr","1º duelo que você vence","%",0,1],
  ["openPct","Rounds em que você entra no 1º duelo","%",0,0],
  ["fdPct","Rounds em que a 1ª morte do round (dos 10) é a sua","%",0,0],
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
  return card({k:"style",title:`Seu estilo em números <span class="sub">${b?"vs "+esc(base.season):esc(cur.season)}</span>`,
    body:`<table class="ctable"><tr><th>Medida</th><th>${esc(cur.season)}</th>${b?`<th>${esc(base.season)}</th>`:""}</tr>${rows}</table>`,
    note:`${nf(s.rounds)} rounds${b?` (${esc(base.season)}: ${nf(b.rounds)})`:""}. Verde = melhorou, vermelho = piorou, cinza = muda o estilo, não o resultado.`});
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
  const so=q.solo, tg=q.together;
  const head=(so&&so[1]&&tg&&tg[1])?pair([`${pf(so[0],so[1])}%`,"sozinho"],[`${pf(tg[0],tg[1])}%`,"com o squad"]):"";
  return card({k:"squad",title:"Fila",head,cap:"sozinho × com o squad",
    body:`<table class="ctable"><tr><th>Fila</th><th>Vitórias</th><th>K/D</th><th>RP</th></tr>
      <tr><td colspan="4" class="csub">${esc(cur.season)} · ${q.n} partidas</td></tr>${squadRows(q)}
      ${bq?`<tr><td colspan="4" class="csub">${esc(base.season)} · últimas ${bq.n} partidas</td></tr>${squadRows(bq)}`:""}
    </table>`,
    read:note,
    note:`Squad = partida no mesmo minuto e no mesmo mapa de outro perfil daqui${who?` (nesta season: ${who})`:""}.${few?" Fila com menos de 15 partidas é indício, não prova.":""} Detalhe por amigo na aba Squad.`});
}

function bars(rows,unit){              // [rótulo, %, "N de M", é você?]: a barra desenha o %, escrito ao lado; "N de M" é o apoio
  return `<div class="bars">${unit?`<div class="bu">${unit}</div>`:""}${rows.map(([l,v,t,me])=>`<div class="br${me?" me":""}"><div class="bt"><span class="bl">${l}</span><span class="bv"><b>${v}%</b>${t&&t.slice(-1)!=="%"?`<small>${t}</small>`:""}</span></div><div class="bb"><i style="width:${Math.max(2,Math.min(100,v))}%"></i></div></div>`).join("")}</div>`;
}
/* manchete: "A × B" com o rótulo de cada lado dentro dela, ou um valor só */
const pair=(a,b)=>`<div class="hl"><div class="hs"><b>${a[0]}</b><span>${a[1]}</span></div><i class="x" aria-hidden="true">×</i><div class="hs"><b>${b[0]}</b><span>${b[1]}</span></div></div>`;
const solo=(v,txt)=>`<div class="hl${txt?" txt":""}"><div class="hs"><b>${v}</b></div></div>`;
let PLAN={}, PLAN_OPEN="";             // chaves dos cards que sustentam uma regra do plano; PLAN_OPEN = o do 1º achado (abre sozinho)
const WIDE=()=>!!(window.matchMedia&&matchMedia("(min-width:900px)").matches);
function card(o){                      // título · manchete · legenda · tabela/barras · leitura · nota
  const plan=!!(o.k&&PLAN[o.k]);
  const body=`${o.cap?`<div class="cap">${o.cap}</div>`:""}${o.body||""}${o.read?`<div class="read">${o.read}</div>`:""}${o.note?`<div class="note">${o.note}</div>`:""}`;
  return `<details class="card fc${plan?" in-plan":""}"${o.k?` id="c-${o.k}"`:""}${(o.open||(o.k&&o.k===PLAN_OPEN)||WIDE())?" open":""}><summary><span class="ct">${o.title}${plan?`<span class="mark">no plano</span>`:""}</span>${o.head||""}${ic("chev","chev")}</summary><div class="cb">${body}</div></details>`;
}
const fcard=(title,head,cap,body,read,note,k)=>card({title,head,cap,body,read,note,k});
function seeCard(k){                   // do plano pro dado: abre o card, leva até ele e pisca
  const el=document.getElementById("c-"+k); if(!el) return;
  el.open=true;
  el.scrollIntoView({behavior:(window.matchMedia&&matchMedia("(prefers-reduced-motion:reduce)").matches)?"auto":"smooth",block:"start"});
  el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash");
}
function coachCards(cur){
  const c=cur.coach, s=cur.style, K={};
  if(c&&c.lastAlive){
    const la=c.lastAlive, lr=c.lastAliveRef, me=pf(la.atk[0],la.atk[1]), ref=pf(lr.atk[0],lr.atk[1]);
    const fd=pf(c.firstDeath.atk[0],c.firstDeath.atk[1]), fdr=pf(c.firstDeathRef.atk[0],c.firstDeathRef.atk[1]);
    const md=pf(la.def[0],la.def[1]), rd=pf(lr.def[0],lr.def[1]), al=c.alone.atk, k=c.kills;
    let read = me-ref>=10
      ? `No ataque você fica pra trás: é o 1º do seu time a morrer em só <b>${fd}%</b> dos rounds (eles, ${fdr}%) e, quando sobra, encara <b>${String(al[2]).replace(".",",")} inimigos</b> em média. Sozinho no ataque, venceu <b>${al[0]} de ${al[1]}</b>.`
      : `No ataque você sobra sozinho perto do que acontece com eles.`;
    read += ` Na defesa, quando sobra 1 do time, é você em <b>${md}%</b> das vezes (eles, ${rd}%)${Math.abs(md-rd)<8?" — normal":""}.`;
    if(k&&k.alone) read += ` Dos seus ${nf(k.total)} abates, ${k.alone} saíram com você já sozinho; ${k.aloneLost} desses, em round perdido.`;
    K.lastAlive=fcard("Último vivo no ataque",solo(`${me}%`),"das vezes em que o seu time ficou com 1 vivo no ataque, esse 1 era você",
      bars([["Você",me,`${la.atk[0]} de ${la.atk[1]}`,1],["Bons jogadores*",ref,`${lr.atk[0]} de ${lr.atk[1]}`],["Acaso (1 em 5)",20,"20%"]]),
      read,`* ${esc(c.refLabel)}. Base: ${c.matches} partidas, ${nf(c.rounds)} rounds.`,"lastAlive");
  }
  if(c&&c.killTiming&&c.killTiming.meEarly[1]>=100){
    const kt=c.killTiming, meE=pf(kt.meEarly[0],kt.meEarly[1]), rE=pf(kt.refEarly[0],kt.refEarly[1]);
    const meL=pf(kt.meLate[0],kt.meLate[1]), rL=pf(kt.refLate[0],kt.refLate[1]);
    const read = rE-meE>=8
      ? `Você quase não participa da abertura: só <b>${meE}%</b> das suas kills são um dos 2 primeiros abates do round (eles, ${rE}%). Chegue junto do entry que a abertura vira sua.`
      : `A distribuição é parecida com a dos bons jogadores (abertura ${meE}% × ${rE}%, fim ${meL}% × ${rL}%). Ou seja: o "último vivo" não vem da hora das suas kills — vem de onde você está quando os outros caem.`;
    K.killTiming=fcard("Quando suas kills acontecem",pair([`${meE}%`,"abrem o round"],[`${meL}%`,"fecham o round"]),"das suas kills abrem o round (2 primeiros abates) · fecham o round (2 últimos)",
      bars([["Você — abertura",meE,`${kt.meEarly[0]} de ${kt.meEarly[1]}`,1],["Bons — abertura",rE,`${kt.refEarly[0]} de ${nf(kt.refEarly[1])}`],
            ["Você — fim",meL,`${kt.meLate[0]} de ${kt.meLate[1]}`,1],["Bons — fim",rL,`${kt.refLate[0]} de ${nf(kt.refLate[1])}`]]),
      read,`* ${esc(c.refLabel)}.`,"killTiming");
  }
  if(c&&c.states&&(c.states["4v4"]||[0,0])[1]>=10&&(c.states["4v5"]||[0,0])[1]>=10){
    const st=c.states, a44=st["4v4"], a45=st["4v5"];
    const L=[["5v4","Vocês na frente (5v4)"],["4v4","Troca feita (4v4)"],["4v5","Um a menos (4v5)"],["5v3","Dois na frente (5v3)"],["3v5","Dois a menos (3v5)"],["3v3","3v3"],["2v2","2v2"]];
    const rows=L.filter(([k])=>(st[k]||[0,0])[1]>=8).map(([k,l])=>{const[w,n]=st[k];return `<tr><td>${l}</td><td><b>${pf(w,n)}%</b> <small>${w} de ${n}</small></td></tr>`;}).join("");
    K.states=fcard("O round pelo placar de vivos",pair([`${pf(a44[0],a44[1])}%`,"troca feita (4v4)"],[`${pf(a45[0],a45[1])}%`,"um a menos (4v5)"]),"round vencido com a troca feita (4v4) × um a menos (4v5)",
      `<table class="ctable"><tr><th>Situação</th><th>Vencidos</th></tr>${rows}</table>`,
      `Perder o 1º duelo não fecha o round se vier a troca: em 4v4 vocês vencem <b>${pf(a44[0],a44[1])}%</b>; sem a troca (4v5), <b>${pf(a45[0],a45[1])}%</b>. É o número por trás do "morreu um, troque na hora".`,
      "Primeira vez que o round chega em cada placar, pelo kill feed.","states");
  }
  if(s&&s.clutchBy){
    const cb=s.clutchBy, tot=cb.reduce((a,x)=>a+x[1],0), w=cb.reduce((a,x)=>a+x[0],0), hard=cb[3][1]+cb[4][1];
    if(tot) K.clutch=fcard("Quando você sobra sozinho",solo(`${w} de ${tot}`),"situações de 1 contra X que você venceu nesta season",
      bars(cb.map((x,i)=>[`1 contra ${i+1}`,pf(x[0],x[1]),`${x[0]} de ${x[1]}`,0])),
      hard?`<b>${hard}</b> das ${tot} foram 1 contra 4 ou 5. Ali quase ninguém vence: o ganho está em não chegar lá.`:"",
      "Contagem do r6.tracker.network.","clutch");
  }
  if(c&&c.hardBreach&&c.hardBreach.with[1]>=10&&c.hardBreach.without[1]>=10){
    const hb=c.hardBreach, a=pf(hb.with[0],hb.with[1]), b=pf(hb.without[0],hb.without[1]);
    const rows=[["Com hard breach",a,`${hb.with[0]} de ${hb.with[1]}`],["Sem hard breach",b,`${hb.without[0]} de ${hb.without[1]}`]];
    if(hb.self&&hb.self[1]) rows.push(["Você de breacher",pf(hb.self[0],hb.self[1]),`${hb.self[0]} de ${hb.self[1]}`,1]);
    K.hardBreach=fcard("Hard breach no ataque",pair([`${a}%`,"com hard breach"],[`${b}%`,"sem hard breach"]),"rounds de ataque vencidos com e sem Thermite, Hibana, Ace ou Maverick no seu time",
      bars(rows),`Em <b>${hb.without[1]} dos ${hb.with[1]+hb.without[1]}</b> rounds de ataque ninguém do seu time levou.`,"","hardBreach");
  }
  if(c&&c.score&&c.score.led20[1]>=8&&c.score.trail02[1]>=8){
    const sc=c.score, otShare=pf(sc.ot[1],c.matches);
    const row=(l,a,v)=>`<tr><td>${l}</td><td><b>${pf(a[0],a[1])}%</b> <small>${a[0]} de ${a[1]} ${v}</small></td></tr>`;
    K.score=fcard("O placar da partida",pair([`${pf(sc.led20[0],sc.led20[1])}%`,"abriu 2-0"],[`${pf(sc.trail02[0],sc.trail02[1])}%`,"levou 0-2"]),"partidas fechadas quando você abre 2-0 × viradas quando leva 0-2",
      `<table class="ctable"><tr><th>Situação</th><th>Resultado</th></tr>
        ${row("Abriu 2-0",sc.led20,"fechadas")}${row("Levou 0-2",sc.trail02,"viradas")}
        ${sc.ot[1]?row("Foi pro overtime (3-3)",sc.ot,"ganhas"):""}${sc.otRounds[1]?row("Rounds de overtime",sc.otRounds,"vencidos"):""}</table>`,
      `Quem abre 2-0 quase leva: você fechou <b>${sc.led20[0]} de ${sc.led20[1]}</b> e virou só <b>${sc.trail02[0]} de ${sc.trail02[1]}</b> — os dois primeiros rounds valem a partida, jogue eles a sério desde o pick.${otShare>=25?` E <b>${otShare}%</b> das suas partidas foram pro overtime: round 7 é rotina, não exceção.`:""}`,
      `${c.matches} partidas com kill feed.`,"score");
  }
  if(c&&c.teams){
    const t=c.teams, d=t.matesRP-t.enemiesRP, avg=Math.round((4*t.matesRP+t.meRP)/5);
    const big=Math.abs(d)<=50?"Mesmo nível":(d<0?"Um pouco abaixo":"Um pouco acima");
    const atk=pf(c.sideRounds.atk[0],c.sideRounds.atk[1]), def=pf(c.sideRounds.def[0],c.sideRounds.def[1]);
    K.teams=fcard("Seus times são mais fracos?",solo(big,1),"seu time × time inimigo, no começo de cada partida",
      `<table class="ctable"><tr><th>Medida</th><th>Colegas</th><th>Inimigos</th></tr>
        <tr><td>RP médio</td><td><b>${nf(t.matesRP)}</b></td><td><b>${nf(t.enemiesRP)}</b></td></tr>
        <tr><td>K/D</td><td><b>${fx(t.matesKD,2)}</b></td><td><b>${fx(t.enemiesKD,2)}</b></td></tr>
        <tr><td>Abates <small>(time todo)</small></td><td><b>${nf(t.teamKills)}</b></td><td><b>${nf(t.enemyKills)}</b></td></tr></table>`,
      `Você entra com <b>${nf(t.meRP)}</b> RP; com você, o time tem média de <b>${nf(avg)}</b>. O K/D dos colegas fica abaixo do dos inimigos porque o seu não entra nessa conta; com você, o time todo mata quase o mesmo que o inimigo.${def-atk>=5?` Onde o round escapa é no ataque: <b>${atk}%</b> de rounds vencidos, contra ${def}% na defesa.`:""}`,
      "Colegas = os outros 4 do seu time, sem você. RP de antes da partida.","teams");
  }
  if(c&&c.pressure&&c.pressure.mine[1]>=15&&c.pressure.theirs[1]>=15){
    const a=c.pressure.mine, b=c.pressure.theirs;
    const pa=pf(a[0],a[1]), pb=pf(b[0],b[1]);
    const lead=Math.abs(pa-pb)<=6
      ? `Fechar e sobreviver valem quase o mesmo pra você (~${Math.round((pa+pb)/20)} em 10).`
      : pa>pb ? `Você fecha melhor (${pa}%) do que segura (${pb}%).` : `Você segura melhor (${pb}%) do que fecha (${pa}%).`;
    K.pressure=fcard("Sob pressão",pair([`${pa}%`,"match point seu"],[`${pb}%`,"match point deles"]),"rounds fechados com match point seu × segurados com match point deles",
      `<table class="ctable"><tr><th>Situação</th><th>Vencidos</th></tr>
        <tr><td>Match point seu</td><td><b>${pa}%</b> <small>${a[0]} de ${a[1]}</small></td></tr>
        <tr><td>Match point deles</td><td><b>${pb}%</b> <small>${b[0]} de ${b[1]}</small></td></tr></table>`,
      `${lead} Com match point seu, jogue o round mais simples do dia: utilidade toda, zero herói — é o round que time nervoso joga pior.`,
      "Match point = um time com 3 rounds a favor e o outro com até 2 (no overtime, com 4).","pressure");
  }
  if(c&&c.trades&&c.trades.mateDeaths>0&&c.trades.myDeaths>0){
    const t=c.trades, me=pf(t.byMe,t.mateDeaths), mates=pf(t.byMe+t.byOthers,t.mateDeaths), per=Math.round(100*t.byOthers/t.mateDeaths/3), mt=pf(t.meTraded,t.myDeaths);
    const quem=Math.abs(me-per)<=2?"como um colega médio":me>per?"mais que um colega médio":"menos que um colega médio";
    let read=`Você troca ${quem} (${me}% das mortes deles; um time de 4 troca ~${per}% por cabeça).`;
    if(mt<mates) read+=` O problema é a distância: os colegas são trocados em ${mates}% das mortes e você em só ${mt}% — você morre longe. Ande a uma sala do entry: a troca dele é sua, e a sua é dele.`;
    K.trades=fcard("Trocas",pair([`${me}%`,"você troca"],[`${mt}%`,"o time te troca"]),"mortes de colegas que você trocou × suas mortes que o time trocou",
      `<table class="ctable"><tr><th>Quem morreu</th><th>Mortes</th><th>Trocadas</th></tr>
        <tr><td>Colegas</td><td><b>${nf(t.mateDeaths)}</b></td><td>você ${t.byMe} · outros ${t.byOthers}</td></tr>
        <tr><td>Você</td><td><b>${nf(t.myDeaths)}</b></td><td>${t.meTraded}</td></tr></table>`,
      read,"Troca = quem matou cai nos 2 abates seguintes do round.","trades");
  }
  if(c&&c.postClutch&&c.postClutch.afterLost[1]>=20){
    const pc=c.postClutch, l=pf(pc.afterLost[0],pc.afterLost[1]), an=pf(pc.afterAnyLost[0],pc.afterAnyLost[1]);
    K.postClutch=fcard("O round depois do clutch",solo(`${l}%`),"round seguinte vencido depois de você perder um clutch",
      bars([["Depois de clutch perdido",l,`${pc.afterLost[0]} de ${pc.afterLost[1]}`,1],
            ["Depois de round perdido comum",an,`${pc.afterAnyLost[0]} de ${pc.afterAnyLost[1]}`],
            ["Depois de clutch vencido",pf(pc.afterWon[0],pc.afterWon[1]),`${pc.afterWon[0]} de ${pc.afterWon[1]}`]]),
      l<an
        ? `Depois que você sobra sozinho e perde, o time vence o seguinte ${l}% — abaixo dos ${an}% de um round perdido comum. Meio round de pedágio: respira no próximo, não force entrada pra compensar.`
        : `Depois que você sobra sozinho e perde, o time vence o seguinte ${l}% — igual ou acima dos ${an}% de um round perdido comum: sem pedágio visível.`,
      "Clutch = você é o último vivo do seu time no round.","postClutch");
  }
  if(c&&c.noKill&&c.noKill.died[1]>=30){
    const nk=c.noKill, al=pf(nk.alive[0],nk.alive[1]), di=pf(nk.died[0],nk.died[1]), dk=pf(nk.diedWithKill[0],nk.diedWithKill[1]);
    const share=pf(nk.alive[1]+nk.died[1],c.rounds);
    const row=(l,a)=>`<tr><td>${l}</td><td><b>${pf(a[0],a[1])}%</b> <small>${a[0]} de ${a[1]}</small></td></tr>`;
    K.noKill=fcard("Seu round sem abate",pair([`${al}%`,"vivo no fim"],[`${di}%`,"morto"]),"rounds com 0 abate seu: vencidos quando você fica vivo × quando você morre",
      `<table class="ctable"><tr><th>Situação</th><th>Vencidos</th></tr>${row("0 abate, vivo no fim",nk.alive)}${row("0 abate, morto",nk.died)}${row("Morto, mesmo levando 1+",nk.diedWithKill)}</table>`,
      `${share>=40&&share<=55?"Quase metade dos seus rounds termina":`Em ${share}% dos seus rounds você termina`} sem abate seu — e tudo bem: vivo, ${al}% viram vitória. O round não pede seu frag, pede você vivo; morrer ${Math.abs(dk-di)<=8?"custa quase o mesmo":"não custa o mesmo"} levando alguém junto (${dk}%) ou não (${di}%).`,
      `Vivo no fim e vitória andam juntos por natureza (defesa que segura o relógio termina viva) — leia como "morte barata custa round", não como "esconder-se vence".`,"noKill");
  }
  if(c&&c.rival&&c.rival.with[1]>=8){
    const a=c.rival.with, b=c.rival.without, tot=a[1]+b[1];
    K.rival=fcard(`O duelo repetido <span class="exp">experimental</span>`,solo(`${a[0]} de ${a[1]}`),"partidas vencidas quando um mesmo inimigo te matou 3+ vezes",
      bars([["Com rival",pf(a[0],a[1]),`${a[0]} de ${a[1]}`,1],["Sem rival",pf(b[0],b[1]),`${b[0]} de ${b[1]}`]]),
      `Em ${a[1]} das ${tot} partidas alguém te matou 3+ vezes — você venceu ${a[0]}. Amostra curta e em ranked o adversário muda a cada partida (por isso o selo experimental); o uso é ao vivo: perdeu o MESMO duelo duas vezes, troque a rota — não volte pro mesmo ângulo.`,
      "","rival");
  }
  return K;
}
const COACH_GRUPOS=[                   // por momento do jogo: dentro do round → na partida → entre partidas
  ["No round","o que acontece dentro de cada round",["states","trades","lastAlive","hardBreach","killTiming","noKill","clutch","postClutch"]],
  ["Na partida","placar, pressão e o mesmo inimigo",["pressure","score","rival"]],
  ["Entre partidas","sequência, tendência, fila, times e seu estilo",["tilt","trend","squad","teams","style"]]
];
function trendBlock(cur){
  const t=cur.coach&&cur.coach.trend;
  if(!t||t.last.n<10) return "";
  const L=t.last, R=t.rest;
  const d2=x=>x.toFixed(2).replace(".",","), sg1=x=>sx(x,1);
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
  return card({k:"trend",title:"Tendência",head:pair([`${pf(L.w,L.n)}%`,`últimas ${L.n}`],[`${pf(R.w,R.n)}%`,`antes (${R.n})`]),
    cap:`vitórias nas últimas ${L.n} × o resto da season`,
    body:`<table class="ctable"><tr><th>Medida</th><th>Últimas ${L.n}</th><th>Antes (${R.n})</th></tr>
      <tr><td>Vitórias</td><td><b>${pf(L.w,L.n)}%</b> <small>${L.w} de ${L.n}</small></td><td>${pf(R.w,R.n)}% <small>${R.w} de ${R.n}</small></td></tr>
      <tr><td>K/D</td><td><b>${d2(L.kd)}</b></td><td>${d2(R.kd)}</td></tr>
      ${eL!=null?`<tr><td>1º duelo vencido</td><td><b>${eL}%</b> <small>${L.esr[0]} de ${L.esr[1]}</small></td><td>${eR!=null?eR+"%":"—"} <small>${R.esr[0]} de ${R.esr[1]}</small></td></tr>`:""}
      <tr><td>RP por partida</td><td><b>${sg1(L.rp)}</b></td><td>${sg1(R.rp)}</td></tr></table>`,
    read,note:`Últimas ${L.n} partidas da season × as outras ${R.n}. K/D e 1º duelo vêm do kill feed.`});
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
    bg=`<div class="sub2">Vitórias pela posição na sessão</div>
      <table class="ctable"><tr><th>Partida</th><th>Vitórias</th></tr>${G.map((x,i)=>x[1]?`<tr><td>${lbl[i]}</td><td><b>${pf(x[0],x[1])}%</b> <small>${x[0]} de ${x[1]}</small></td></tr>`:"").join("")}</table>`;
    const g1=G[0], mid=[G[1][0]+G[2][0], G[1][1]+G[2][1]];
    if(g1[1]>=10&&mid[1]>=10&&pf(mid[0],mid[1])-pf(g1[0],g1[1])>=12)
      read+=` A <b>1ª partida da sessão</b> é a sua pior: ${g1[0]} de ${g1[1]} (${pf(g1[0],g1[1])}%), contra ${pf(mid[0],mid[1])}% na 2ª e 3ª — você entra frio.`;
    const pre=[G[0][0]+mid[0], G[0][1]+mid[1]];
    if(G[3][1]>=8&&pf(pre[0],pre[1])-pf(G[3][0],G[3][1])>=12)
      read+=` Da <b>4ª em diante</b> cai pra ${pf(G[3][0],G[3][1])}% — sessão longa não paga.`;
  }
  return card({k:"tilt",title:"Sequência · depois de perder",head:solo(big,1),cap:"a partida seguinte, na mesma sessão",
    body:bars([["Depois de derrota",l,`${lw} de ${ln}`,1],["Depois de vitória",w,`${ww} de ${wn}`]],"partida seguinte vencida")+bg,
    read,note:`Sessão = partidas com menos de 75 min entre uma e outra. ${t.sessions} sessões, ${t.matches} partidas.`});
}
function coachRuleItems(cur,base){     // as regras do plano; k = card do Coach que mostra o dado por trás ("" = nenhum)
  const c=cur.coach, s=cur.style, R=[];
  const rule=(k,ico,cls,b,t)=>R.push({k,ico,cls,b,t});
  if(c&&c.lastAlive){
    const la=c.lastAlive.atk, lr=c.lastAliveRef.atk, me=pf(la[0],la[1]), ref=pf(lr[0],lr[1]), al=c.alone.atk;
    if(me-ref>=10) rule("lastAlive","sword","atk","No ataque, seja o 2º a entrar, não o 5º.",
      `Ande a uma sala do seu entry: se ele cair, você troca na hora. Hoje, quando o time fica com 1 vivo no ataque, é você ${me}% das vezes (o normal é 20%), e sozinho você venceu ${al[0]} de ${al[1]}.`);
  }
  if(s&&s.esr>=60&&(s.fb+s.fd)>=20){
    const o=c&&c.opening;
    rule("style","target","play","Confie no seu 1º duelo.",
      `Quando você entra nele, vence ${Math.round(s.esr)}% (${s.fb} de ${s.fb+s.fd}).${o?` Round que começa com abate do seu time vira vitória ${pf(o.kill[0],o.kill[1])}% das vezes; com morte, ${pf(o.death[0],o.death[1])}%.`:""}`);
  }
  if(c&&c.hardBreach){
    const hb=c.hardBreach, a=pf(hb.with[0],hb.with[1]), b=pf(hb.without[0],hb.without[1]);
    if(hb.with[1]>=10&&hb.without[1]>=10&&a-b>=8){
      const mine=(cur.operatorsAtk||[]).concat(cur.operatorsCut||[]).filter(o=>HARD_BREACH.includes(o.name)).sort((x,y)=>(y.rounds||0)-(x.rounds||0))[0];
      rule("hardBreach","burst","atk",`Sem hard breach no time? Pegue ${esc(mine?mine.name:"Thermite")}.`,
        `Com hard breach o time vence ${a}% dos rounds de ataque; sem, ${b}%. Em ${hb.without[1]} de ${hb.with[1]+hb.without[1]} rounds de ataque ninguém levou.${mine?` Seu ${esc(mine.name)}: ${mine.wr}% em ${mine.rounds} rounds${mine.kd!=null?", K/D "+fx(mine.kd,2):""}.`:""}`);
    }
  }
  const bans=(cur.maps||[]).filter(m=>m.matches>=4&&m.seasonWR<40).sort((x,y)=>x.seasonWR-y.seasonWR);
  if(bans.length){ const m=bans[0]; rule("","ban","ban",`Bane ${esc(m.name)}.`,`${m.seasonWR.toFixed(0)}% em ${m.matches} partidas.${m.note?" "+esc(m.note):""}`); }
  const t=cur.tilt;
  if(t&&t.afterLoss[1]>=8&&pf(t.afterLoss[0],t.afterLoss[1])<45)
    rule("tilt","pause","ban","Perdeu duas seguidas? Pausa antes da próxima.",`Depois de uma derrota você venceu a seguinte só ${t.afterLoss[0]} de ${t.afterLoss[1]}.`);
  if(t&&t.byGame){
    const g1=t.byGame[0], mid=[t.byGame[1][0]+t.byGame[2][0], t.byGame[1][1]+t.byGame[2][1]];
    if(g1[1]>=10&&mid[1]>=10&&pf(mid[0],mid[1])-pf(g1[0],g1[1])>=12)
      rule("tilt","flame","play","Aqueça antes da primeira ranqueada.",
        `Sua 1ª partida da sessão é a pior: ${g1[0]} de ${g1[1]} (${pf(g1[0],g1[1])}%), contra ${pf(mid[0],mid[1])}% na 2ª e 3ª. Estande de tiro ou uma casual antes de dar queue.`);
  }
  const sq=[[cur.squad,cur],[base&&base.squad,base]].find(([q])=>q&&q.solo[1]>=10&&q.together[1]>=10);
  if(sq){
    const [q,sn]=sq, a=pf(q.together[0],q.together[1]), b=pf(q.solo[0],q.solo[1]);
    if(a-b>=8) rule("squad","squad","play","Jogue com o squad quando der.",`Na ${esc(sn.season)}: ${q.together[0]} de ${q.together[1]} juntos (${a}%); sozinho, ${q.solo[0]} de ${q.solo[1]} (${b}%).`);
  }
  return R;
}
function coachRules(cur,base){
  const R=coachRuleItems(cur,base);
  const row=r=>{
    const inner=`<div class="ico ${r.cls}">${ic(r.ico)}</div><div><b>${r.b}</b><span>${r.t}</span>${r.k?`<div class="see">ver o dado ${ic("chev")}</div>`:""}</div>`;
    return r.k?`<a class="pi" href="#c-${r.k}" onclick="seeCard('${r.k}');return false">${inner}</a>`:`<div class="pi">${inner}</div>`;
  };
  return R.length?`<div class="plan coach">${R.map(row).join("")}</div>`
    :bnr("info","Nenhuma regra passou no corte dos seus números ainda. Mapas e operadores estão no Plano de jogo do Início.","flat");
}
function renderCoach(){
  const cur=active, base=baselineOf(cur), latest=cur===SEASONS[0];
  const el=document.getElementById("scr-coach");
  if(!cur.style){
    el.innerHTML=bnr("compass","O coach usa dados que só existem a partir da Y11S2. Troque a season no seletor do topo.");
    return;
  }
  PLAN={}; PLAN_OPEN="";
  if(latest) coachRuleItems(cur,base).forEach(r=>{ if(r.k){ PLAN[r.k]=1; if(!PLAN_OPEN) PLAN_OPEN=r.k; } });
  const K=coachCards(cur);
  K.trend=trendBlock(cur); K.squad=cur.squad?squadCard(cur,base):""; K.style=styleTable(cur,base); K.tilt=cur.tilt?tiltCard(cur):"";
  const grupos=COACH_GRUPOS.map(([t,sub,ks])=>{const h=ks.map(k=>K[k]||"").join(""); return h?`<h3 class="grp">${t}<small>${sub}</small></h3><div class="fcards">${h}</div>`:"";}).join("");
  el.innerHTML=`
    ${latest?`<h2 class="sec first">Plano pra próxima sessão<span class="hint">como jogar, tirado dos seus números</span></h2>${coachRules(cur,base)}
      <h2 class="sec">Meta</h2>${goalCard()}`
      :bnr("calendar",`Você está vendo a <b>${esc(cur.season)}</b>, já fechada. Meta e plano valem só pra season atual.`,"tight")}
    <h2 class="sec">O que os rounds mostram<span class="hint">${esc(cur.season)}</span></h2>
    ${cur.coach?"":bnr("search",`O diagnóstico round a round (quem fica por último, hard breach, nível dos times) ainda não foi coletado ${latest?"pra este perfil":"pra esta season"}.`,"gap")}
    ${grupos}`;
}

/* ---------- SQUAD ---------- */
const SQUAD_AVISO=`<b>Amostra pequena vira indício, não veredito.</b> Vocês jogaram pouco juntos nesta season.<span class="bsub">Squad = partida no mesmo minuto e mapa de outro perfil daqui; amigo de fora do app conta como "sozinho".</span>`;
function squadTable(sn){                // barra = % de vitórias; "N de M" ao lado é a base dessa %
  const q=sn.squad;
  const row=(l,a,me)=>a&&a[1]?[l,pf(a[0],a[1]),`${a[0]} de ${a[1]}`,me]:null;
  const friends=Object.entries(q.perFriend||{}).filter(([,a])=>a[1]>0).sort((a,b)=>b[1][1]-a[1][1])
    .map(([sl,a])=>row(esc(NAMES[sl]||sl),a));
  const rows=[row("Sozinho",q.solo,true)].concat(friends,[row("Trio",q.trio)]).filter(Boolean);
  return `<div class="cbox">${bars(rows,"Vitórias · % das partidas")}</div>`;
}
function renderSquad(){
  const el=document.getElementById("scr-squad");
  const seas=SEASONS.filter(s=>s.squad);
  if(!seas.length){ el.innerHTML=bnr("squad","Sem dados de fila carregados."); return; }
  el.innerHTML=bnr("warn",SQUAD_AVISO,"flat attn")+`<div class="sqgrid">`+seas.map(s=>`<div class="sqs"><h2 class="sec">${esc(s.season)}<span class="hint">${esc(s.seasonLabel||"")} · ${s.squad.n} partidas</span></h2>${squadTable(s)}</div>`).join("")+`</div>`;
}

/* ---------- SELETOR / SHELL ---------- */
const TABS=[
  {id:"inicio",label:"Início",icon:ic("home")},
  {id:"coach",label:"Coach",icon:ic("coach")},
  {id:"mapas",label:"Mapas",icon:ic("map")},
  {id:"ops",label:"Operadores",icon:ic("ops")},
  {id:"squad",label:"Squad",icon:ic("squad")},
  {id:"evo",label:"Evolução",icon:ic("evo")}
];
function go(id){
  document.querySelectorAll(".screen").forEach(s=>s.classList.toggle("active", s.id==="scr-"+id));
  document.querySelectorAll("nav.bottom button,.desktabs button").forEach(b=>{ const on=b.dataset.t===id; b.classList.toggle("on", on); if(on) b.setAttribute("aria-current","page"); else b.removeAttribute("aria-current"); });
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
    <div class="legrow"><b class="cup">▲</b> subiu vs a season anterior (toque na seta pra ver antes → agora)</div>
    <div class="legrow"><b class="cdn">▼</b> caiu vs a season anterior</div>
    <div class="legrow"><b class="cmut">=</b> estável</div>
    <div class="legrow"><b>°</b> amostra pequena — indicativo (mapa com menos de 4 partidas · operador com menos de 8 rounds)</div>
    <div class="legrow"><b class="cdef">■</b> defesa · <b class="catk">■</b> ataque</div>
    <div class="legrow"><b class="cgold">%</b> verde ≥55 · amarelo 50–54 · vermelho &lt;50</div>
    <div class="legrow"><b>${ic("map")}</b> Mapas: priorize = vitórias ≥55% · neutro 40–54% · banir &lt;40% (conta só a season escolhida)</div>
    <div class="legrow"><b>${ic("swap")}</b> troque a season pelo seletor no topo pra comparar épocas</div>
    <div class="legrow"><b class="cnt">▲</b> cinza: mudou o estilo ou a contagem, não o resultado (nem bom nem ruim)</div>
    <div class="legrow"><b>${ic("coach")}</b> Coach: o plano pra próxima sessão, sua meta e o que os rounds mostram — os cards marcados "no plano" são os que valem olhar durante o jogo</div>
    <div class="legrow"><b>${ic("medal")}</b> Operadores: toque em qualquer operador (mains, hard breach ou tabela) pra abrir a ficha completa</div>
    <div class="legrow"><b>${ic("squad")}</b> Squad: seu resultado sozinho × com cada amigo daqui</div>`);
}
/* ---------- COMPARTILHAR ----------
   O card é uma imagem 4:5 (1080×1350, o que o WhatsApp mostra inteiro). Uma string SVG só: é a prévia na folha e a fonte do PNG.
   SVG puro (sem foreignObject nem <use> externo): o logo e o emblema entram como desenho, e o PNG sai igual ao que se vê. */
const SC_W=1080, SC_H=1350;
function shareSVG(){
  const k=active.kpis, curRP=(k.latestRP!=null?k.latestRP:k.peakRP), rk=rankInfo(curRP);
  const rm=active.recentMatches||[], w=rm.filter(m=>m.w).length, l=rm.length-w;
  const L=BRAND.logo, X0=96, X1=SC_W-96, IW=X1-X0, CX=SC_W/2;
  const F="-apple-system,BlinkMacSystemFont,system-ui,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif";
  const rpTxt=curRP!=null?curRP.toLocaleString("pt-BR"):"—";
  const nm=String(PLAYER.name||""), nmFs=Math.round(Math.max(56,Math.min(104,840/(Math.max(6,nm.length)*.6))));
  const m=44, c=96, r=56, W=SC_W, H=SC_H;   // moldura: dois cantos cortados e dois arredondados, como a placa do logo
  const frame=`M${m+r} ${m}H${W-m-c}L${W-m} ${m+c}V${H-m-r}A${r} ${r} 0 0 1 ${W-m-r} ${H-m}H${m+c}L${m} ${H-m-c}V${m+r}A${r} ${r} 0 0 1 ${m+r} ${m}Z`;
  const stats=[{v:`${k.winRate.toFixed(0)}<tspan font-size="46">%</tspan>`,l:"vitórias"},{v:fx(k.kd,2),l:"K/D"}];
  if(rm.length) stats.push({v:`${w}<tspan font-size="60" fill="#34d399">V</tspan><tspan font-size="60" fill="#8b919c">-</tspan>${l}<tspan font-size="60" fill="#ff6b5a">D</tspan>`,l:`últimas ${rm.length}`,wt:1.4});
  const tot=stats.reduce((a,s)=>a+(s.wt||1),0); let ax=X0;      // a coluna da forma recente é mais larga ("10V-10D" tem 7 caracteres)
  const cols=stats.map((s,i)=>{ const cw=IW*(s.wt||1)/tot, cx=ax+cw/2, edge=ax; ax+=cw;
    return `<text x="${cx}" y="962" font-size="78" font-weight="800" fill="#e7e9ec" text-anchor="middle">${s.v}</text>
    <text x="${cx}" y="1010" font-size="30" font-weight="700" fill="#8b919c" letter-spacing="3" text-anchor="middle">${s.l.toUpperCase()}</text>`
    +(i?`<path d="M${edge} 902V1014" stroke="#262a33" stroke-width="2"/>`:""); }).join("");
  const n=rm.length, gap=8, pw=n?(IW-(n-1)*gap)/n:0;
  const pips=n?rm.slice().reverse().map((x,i)=>`<rect x="${(X0+i*(pw+gap)).toFixed(1)}" y="1062" width="${pw.toFixed(1)}" height="52" rx="8" fill="${x.w?"#34d399":"#f0513f"}"${x.w?"":' fill-opacity=".85"'}/>`).join("")
    +`<text x="${X0}" y="1156" font-size="26" fill="#8b919c">mais antiga</text><text x="${X1}" y="1156" font-size="26" fill="#8b919c" text-anchor="end">mais recente</text>`:"";
  const alt=`Card de ${nm}: ${rk.name}, ${rpTxt} RP, ${k.winRate.toFixed(0)}% de vitórias, K/D ${fx(k.kd,2)}`+(n?`, últimas ${w}V-${l}D`:"");
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-family="${F}" role="img" aria-label="${esc(alt)}">
  <title>${esc(alt)}</title>
  <defs>
    <linearGradient id="sc-bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#14161c"/><stop offset="1" stop-color="#0a0b0e"/></linearGradient>
    <radialGradient id="sc-glow" cx="${CX}" cy="410" r="560" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#f4c20d" stop-opacity=".2"/><stop offset="1" stop-color="#f4c20d" stop-opacity="0"/></radialGradient>
    <pattern id="sc-grid" width="54" height="54" patternUnits="userSpaceOnUse"><path d="M54 0H0V54" fill="none" stroke="#fff" stroke-opacity=".035" stroke-width="2"/></pattern>
    <linearGradient id="sc-lg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${L.top}"/><stop offset="1" stop-color="${L.bot}"/></linearGradient>
  </defs>
  <rect width="${W}" height="${H}" fill="url(#sc-bg)"/>
  <rect width="${W}" height="${H}" fill="url(#sc-grid)"/>
  <rect width="${W}" height="${H}" fill="url(#sc-glow)"/>
  <path d="${frame}" fill="none" stroke="#2b303a" stroke-width="3"/>
  <g transform="translate(${X0} 96) scale(1.1875)"><path d="${L.tile}" fill="url(#sc-lg)"/><path d="${L.glyph}" fill="${L.ink}" fill-rule="evenodd"/></g>
  <text x="${X0+98}" y="150" font-size="46" font-weight="800" letter-spacing="3" fill="#e7e9ec">SIEGE<tspan fill="#f4c20d">·</tspan>LAB</text>
  <text x="${X1}" y="148" font-size="28" font-weight="700" letter-spacing="2" fill="#8b919c" text-anchor="end">${esc(active.season)} · Ranked</text>
  <svg x="${CX-190}" y="214" width="380" height="380" viewBox="0 0 48 48">${emblemBody(rk.color,rk.div,rk.champ)}</svg>
  <text x="${CX}" y="728" font-size="${nmFs}" font-weight="800" fill="#e7e9ec" text-anchor="middle">${esc(nm)}</text>
  <text x="${CX}" y="796" font-size="44" font-weight="700" fill="${rk.color}" text-anchor="middle">${esc(rk.name)}<tspan fill="#cfd3d8" font-weight="600"> · ${rpTxt} RP</tspan></text>
  <path d="M${X0} 852H${X1}" stroke="#262a33" stroke-width="2"/>
  ${cols}
  ${pips}
  <text x="${CX}" y="1240" font-size="32" font-weight="700" fill="#f4c20d" text-anchor="middle">thebsilva.github.io/siege-lab</text>
</svg>`;
}
function svgToPng(svg){      // SVG -> canvas -> PNG 1080×1350. Tudo local (data: URI), nada de rede
  return new Promise((ok,fail)=>{
    const img=new Image();
    img.onload=()=>{ try{
      const cv=document.createElement("canvas"); cv.width=SC_W; cv.height=SC_H;
      cv.getContext("2d").drawImage(img,0,0,SC_W,SC_H);
      cv.toBlob(b=>b?ok(b):fail(new Error("png")),"image/png");
    }catch(e){ fail(e); } };
    img.onerror=()=>fail(new Error("svg"));
    img.src="data:image/svg+xml;charset=utf-8,"+encodeURIComponent(svg);
  });
}
function openShare(){
  const svg=shareSVG();
  const fname=`siege-lab-${PLAYER.slug||"card"}-${active.season}.png`.toLowerCase();
  const title="SIEGE·LAB — "+PLAYER.name;
  openSheet(`<h3>Compartilhar</h3><div class="sharecard">${svg}</div>
    <div class="shint" id="shint">Tire um print do card e mande no grupo</div>
    <div class="shbtns">
      <button class="btn-share pri" id="doimg" disabled>${ic("image")} Preparando imagem…</button>
      ${navigator.share?`<button class="btn-share sec" id="doshare">${ic("link")} Compartilhar o link</button>`:`<button class="btn-share sec" id="docopy">${ic("link")} Copiar o link</button>`}
    </div>`);
  const s=document.getElementById("doshare"); if(s) s.onclick=()=>navigator.share({title:title,text:"Minha análise de R6 no SIEGE·LAB",url:location.href}).catch(()=>{});
  const c=document.getElementById("docopy"); if(c) c.onclick=()=>{ if(navigator.clipboard) navigator.clipboard.writeText(location.href); c.innerHTML=ic("check")+" Link copiado"; };
  // a imagem já nasce pronta: o toque em "Compartilhar imagem" chama share() na hora (o navegador exige o gesto do usuário)
  svgToPng(svg).then(blob=>{
    const btn=document.getElementById("doimg"); if(!btn) return;           // folha já fechada ou trocada
    let file=null; try{ file=new File([blob],fname,{type:"image/png"}); }catch(e){}
    const hint=document.getElementById("shint");
    btn.disabled=false;
    if(file&&navigator.canShare&&navigator.canShare({files:[file]})){
      btn.innerHTML=ic("image")+" Compartilhar imagem";
      if(hint) hint.textContent="Mande a imagem no grupo, ou só o link";
      btn.onclick=()=>navigator.share({files:[file],title:title}).catch(()=>{});
    }else{
      btn.innerHTML=ic("image")+" Baixar imagem";
      if(hint) hint.textContent="Baixe a imagem (ou tire um print do card) e mande no grupo";
      btn.onclick=()=>{ const u=URL.createObjectURL(blob), a=document.createElement("a"); a.href=u; a.download=fname; document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(u),4000); };
    }
  }).catch(()=>{ const btn=document.getElementById("doimg"); if(btn) btn.hidden=true; });
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
  document.getElementById("subline").innerHTML = `<span class="pn">${esc(PLAYER.name)}</span><span class="pq"> · Ranked</span>`;
  document.title = "SIEGE·LAB — " + PLAYER.name;
  bg.onclick=closeSheet;
  const pop=document.getElementById("poptip"); let popT=0;
  const hide=()=>pop.classList.remove("on");
  const show=el=>{
    pop.textContent=el.dataset.tip; pop.classList.add("on");
    const r=el.getBoundingClientRect(), w=pop.offsetWidth, h=pop.offsetHeight, vw=document.documentElement.clientWidth;
    pop.style.left=Math.min(Math.max(8,r.left+r.width/2-w/2),vw-w-8)+"px";
    pop.style.top=(r.top-h-8>=8?r.top-h-8:r.bottom+8)+"px";
    clearTimeout(popT); popT=setTimeout(hide,3200);
  };
  document.addEventListener("click",e=>{                // captura: a dica abre sem disparar o clique da linha que a contém
    const t=e.target.closest&&e.target.closest("[data-tip]");
    if(t){ e.stopPropagation(); e.preventDefault(); show(t); } else hide();
  },true);
  document.addEventListener("keydown",e=>{
    if(e.key==="Escape") hide();
    else if((e.key==="Enter"||e.key===" ")&&e.target.dataset&&e.target.dataset.tip){ e.preventDefault(); show(e.target); }
  });
  window.addEventListener("scroll",hide,{passive:true});
}
shell(); renderAll(); go("inicio");
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
