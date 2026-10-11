#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIEGE·LAB — identidade visual. UMA fonte para o símbolo: tudo o que aparece (header, landing,
card de compartilhar, favicon, apple-touch-icon.png, og.png) sai da geometria abaixo.

  TILE  = a "placa": quadrado com dois cantos cortados (topo-direita e base-esquerda) e dois arredondados.
  GLYPH = o "6" em blocos (algarismo de placar), com o canto superior-direito cortado igual ao da placa.

Cores: ouro da marca (gradiente) + tinta quase preta. O "6" é referência ao nome do jogo, desenhado aqui
do zero (não reproduz a marca nem a tipografia oficiais).

Uso: build.py importa este módulo. Os PNGs precisam do Pillow (sem ele o build segue, só avisa).
"""
import math
import os
import urllib.parse

GOLD_TOP, GOLD_BOT, INK = "#ffd23a", "#eeb400", "#0a0b0e"

# --- geometria (grade 64×64) -------------------------------------------------
TILE = "M14 0H46L64 18V50A14 14 0 0 1 50 64H18L0 46V14A14 14 0 0 1 14 0Z"
GLYPH = "M16 12H42L48 18V21H25V27.5H48V52H22L16 46Z M25 36.5V43H39V36.5Z"   # fill-rule evenodd (o miolo do 6 vaza)

GRAD = ('<linearGradient id="slg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{GOLD_TOP}"/><stop offset="1" stop-color="{GOLD_BOT}"/></linearGradient>')


def symbol():
    """<symbol id="sl-logo"> pra usar com <svg><use href="#sl-logo"/></svg> (uma definição, vários usos)."""
    return (f'<symbol id="sl-logo" viewBox="0 0 64 64"><path d="{TILE}" fill="url(#slg)"/>'
            f'<path d="{GLYPH}" fill="{INK}" fill-rule="evenodd"/></symbol>')


def symbol_mono():
    """Versão de uma cor só (currentColor): a placa cheia com o 6 vazado."""
    return (f'<symbol id="sl-logo-mono" viewBox="0 0 64 64"><path d="{TILE} {GLYPH}" '
            'fill="currentColor" fill-rule="evenodd"/></symbol>')


def standalone_svg():
    """SVG autônomo (favicon e qualquer uso fora do sprite)."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs>' + GRAD + '</defs>'
            f'<path d="{TILE}" fill="url(#slg)"/><path d="{GLYPH}" fill="{INK}" fill-rule="evenodd"/></svg>')


def favicon_href():
    """data: URI do favicon (SVG inline, sem requisição externa)."""
    return "data:image/svg+xml," + urllib.parse.quote(standalone_svg(), safe="")


# --- emblema de patente (hexágono com o algarismo romano da divisão) ---------------------------------------------
EMB_OUT = "24,3 5.81,13.5 5.81,34.5 24,45 42.19,34.5 42.19,13.5"
EMB_INN = "24,10.6 12.4,17.3 12.4,30.7 24,37.4 35.6,30.7 35.6,17.3"
EMB_HL = "5.81,13.5 24,3 42.19,13.5 24,24"
ROMAN = ["", "I", "II", "III", "IV", "V"]
EMB_FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif"


def emblem_body(color, div, champ=False):
    """Miolo do emblema (grade 48×48). O app tem o gêmeo em JS (emblemBody) lendo estas mesmas constantes."""
    label = "★" if champ else (ROMAN[div] if 0 <= div < len(ROMAN) else "")
    return (f'<polygon points="{EMB_OUT}" fill="{color}" stroke="rgba(0,0,0,.42)" stroke-width="1.3"/>'
            f'<polygon points="{EMB_HL}" fill="rgba(255,255,255,.15)"/>'
            f'<polygon points="{EMB_INN}" fill="none" stroke="rgba(255,255,255,.34)" stroke-width="1.1"/>'
            '<text x="24" y="25.5" fill="#fff" stroke="rgba(0,0,0,.45)" stroke-width="3" paint-order="stroke" '
            f'font-size="{18 if champ else 16}" font-weight="800" text-anchor="middle" dominant-baseline="central" '
            f'font-family="{EMB_FONT}">{label}</text>')


def emblem(color, div, champ=False, size=52):
    return (f'<svg class="remb" width="{size}" height="{size}" viewBox="0 0 48 48" aria-hidden="true">'
            f'{emblem_body(color, div, champ)}</svg>')


def js_parts():
    """Geometria que o JS do app precisa (emblema e card de compartilhar): uma fonte só, injetada no HTML."""
    return {"logo": {"tile": TILE, "glyph": GLYPH, "ink": INK, "top": GOLD_TOP, "bot": GOLD_BOT},
            "emb": {"out": EMB_OUT, "inn": EMB_INN, "hl": EMB_HL}}


# --- PNGs (Pillow) -----------------------------------------------------------
def _arc(cx, cy, r, a0, a1, n=28):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _tile_points():
    pts = [(14, 0), (46, 0), (64, 18), (64, 50)]
    pts += _arc(50, 50, 14, 0, 90)[1:]
    pts += [(18, 64), (0, 46), (0, 14)]
    pts += _arc(14, 14, 14, 180, 270)[1:]
    return pts


GLYPH_OUTER = [(16, 12), (42, 12), (48, 18), (48, 21), (25, 21), (25, 27.5), (48, 27.5), (48, 52), (22, 52), (16, 46)]
GLYPH_HOLE = [(25, 36.5), (25, 43), (39, 43), (39, 36.5)]


def _font(size, bold=True):
    """Fonte do sistema (só pro og.png, que é imagem). Procura uma sem serifa; cai na padrão do Pillow."""
    from PIL import ImageFont
    cands = [("/System/Library/Fonts/HelveticaNeue.ttc", ["Bold", "Heavy"]),
             ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", [None]),
             ("/Library/Fonts/Arial Unicode.ttf", [None])]
    for path, names in cands:
        if not os.path.exists(path):
            continue
        if path.endswith(".ttc"):
            for i in range(0, 12):
                try:
                    f = ImageFont.truetype(path, size, index=i)
                except Exception:
                    break
                if any(n and n in " ".join(f.getname()) for n in names) and "Condensed" not in " ".join(f.getname()):
                    return f
        else:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _gradient(w, h, top, bot):
    from PIL import Image
    g = Image.new("RGB", (1, h))
    t = tuple(int(top[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(bot[i:i + 2], 16) for i in (1, 3, 5))
    for y in range(h):
        k = y / max(1, h - 1)
        g.putpixel((0, y), tuple(round(t[j] + (b[j] - t[j]) * k) for j in range(3)))
    return g.resize((w, h))


def _plate(size, ss=4):
    """Placa + 6 em RGBA (size×size), com antisserrilhado por supersampling."""
    from PIL import Image, ImageDraw
    S = size * ss
    k = S / 64
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon([(x * k, y * k) for x, y in _tile_points()], fill=255)
    base = _gradient(S, S, GOLD_TOP, GOLD_BOT).convert("RGBA")
    plate = base.copy()
    plate.putalpha(mask)
    ImageDraw.Draw(plate).polygon([(x * k, y * k) for x, y in GLYPH_OUTER], fill=INK)
    hole = Image.new("L", (S, S), 0)                             # o miolo do 6 vaza: volta o ouro por cima
    ImageDraw.Draw(hole).polygon([(x * k, y * k) for x, y in GLYPH_HOLE], fill=255)
    plate.paste(base, (0, 0), hole)
    return plate.resize((size, size), Image.LANCZOS)


def write_pngs(out_dir):
    """docs/apple-touch-icon.png (180×180) e docs/og.png (1200×630). Determinístico (mesmo arquivo a cada build)."""
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(out_dir, exist_ok=True)

    # --- ícone de tela inicial: fundo escuro cheio (o iOS arredonda sozinho) com a placa no centro ---
    A = 180
    icon = Image.new("RGB", (A, A), INK)
    glow = Image.new("RGBA", (A, A), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((26, 30, A - 26, A - 22), fill=(244, 194, 13, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(16))
    icon.paste(glow, (0, 0), glow)
    p = _plate(124)
    icon.paste(p, ((A - 124) // 2, (A - 124) // 2), p)
    icon.save(os.path.join(out_dir, "apple-touch-icon.png"), optimize=True)

    # --- prévia do link (WhatsApp, etc.): 1200×630 ---
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 48):                                   # quadro de tática: grade fina
        d.line([(x, 0), (x, H)], fill=(20, 22, 28))
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill=(20, 22, 28))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((20, 110, 520, 560), fill=(244, 194, 13, 64))
    gb = glow.filter(ImageFilter.GaussianBlur(70))
    img.paste(gb, (0, 0), gb)
    d = ImageDraw.Draw(img)
    plate = _plate(300)
    img.paste(plate, (110, 165), plate)

    def tracked(x, y, text, font, fill, track=0):
        for ch in text:
            d.text((x, y), ch, font=font, fill=fill)
            x += d.textlength(ch, font=font) + track
        return x
    f_big, f_sub, f_small = _font(112), _font(34), _font(28)
    x0 = 470
    x = tracked(x0, 188, "SIEGE", f_big, (231, 233, 236), track=5)
    x = tracked(x, 188, "·", f_big, (244, 194, 13), track=5)
    tracked(x, 188, "LAB", f_big, (231, 233, 236), track=5)
    d.rectangle((x0 + 2, 340, x0 + 84, 345), fill=(244, 194, 13))
    d.text((x0, 372), "Seu coach de ranqueada no R6 Siege", font=f_sub, fill=(231, 233, 236))
    d.text((x0, 428), "Mapas, operadores e rounds, pelos seus números.", font=f_small, fill=(139, 145, 156))
    d.text((x0, 520), "thebsilva.github.io/siege-lab", font=f_small, fill=(244, 194, 13))
    img.save(os.path.join(out_dir, "og.png"), optimize=True)
