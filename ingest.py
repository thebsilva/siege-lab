#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIEGE·LAB — ingest: transforma a coleta crua do tracker em snapshots por season.

Lê  players/<slug>/raw/<data>_*.json   →   escreve players/<slug>/<data>_<season>.json
(o build.py só lê o que está direto em players/<slug>/, então o raw/ não entra no app).

Uso:  python3 ingest.py 2026-10-09        (data da coleta)

Arquivos de coleta por jogador (usa os que existirem):
  <data>_overview.json         resumo por season: KPIs, abertura, clutch por 1vX, multikill
  <data>_sNN_maps.json         mapas da season NN (linha total + linha por lado a/d)
  <data>_sNN_operators.json    operadores da season NN (por lado)
  <data>_sNN_opmaps.json       operador × mapa → "quem pegar" dentro do card de cada mapa
  <data>_matches.json          histórico de partidas → forma recente, RP por vitória/derrota, fila, tilt
  <data>_sNN_rounds.jsonl      kill feed de cada round → diagnóstico da aba Coach

Formato do rounds.jsonl (1 partida por linha):
  {"id": 8 chars, "P": [10 linhas], "R": ["<time vencedor>:<eventos>", ...]}
  P = [time(0/1), sou_eu, rp_depois, delta_rp, k, d, a, fk, fd, clutch, "ops.do.round.a.round"]
      (ops só do meu time; jogadores 0-4 = time 0, 5-9 = time 1)
  evento = 2 caracteres: índice de quem matou + índice de quem morreu, em ordem cronológica
"""
import collections
import glob
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLAYERS = os.path.join(HERE, "players")

SEASONS = {41: ("Y11S1", "Silent Hunt"), 42: ("Y11S2", "System Override"), 43: ("Y11S3", "Split Fire")}
CURRENT = 43
# A Y11S3 abriu em 01/09/2026 (a última partida da Y11S2 no histórico é 01/09 02:36 UTC).
# Partida antes disso conta como Y11S2: o histórico coletado só cobre ~1 mês antes.
SEASON_START = {43: "2026-09-01T12"}

HARD_BREACH = {"Thermite", "Hibana", "Ace", "Maverick"}
STATES = {"5v4", "4v5", "4v4", "5v3", "3v5", "3v3", "2v2"}  # placares de vivos (1ª vez que o round chega neles)
REF_KD = 1.2        # régua do "último vivo": outros jogadores das mesmas partidas com K/D >= 1,2 na partida
MIN_ROUNDS = 8      # operador abaixo disso não entra nas listas (é o "°" do app)
SOLID_ROUNDS = 15  # abaixo disso o operador não abre a lista nem ganha estrela
RECENT = 20         # partidas na "forma recente"
SESSION_GAP_MIN = 75


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def season_of(ts):
    return CURRENT if ts >= SEASON_START[CURRENT] else CURRENT - 1


def pct(a, b, dec=1):
    return round(100 * a / b, dec) if b else None


def side_table(players_dir):
    """Lado de cada operador: playbook + tudo que apareceu nas coletas (todas trazem a/d)."""
    side = {}
    pb = os.path.join(HERE, "playbook.json")
    if os.path.exists(pb):
        side.update({k: v.get("side") for k, v in load(pb).get("operators", {}).items()})
    for f in glob.glob(os.path.join(players_dir, "*", "raw", "*_operators.json")):
        for r in load(f)["rows"]:
            if r[1]:
                side.setdefault(r[0].strip(), "atk" if r[1] == "a" else "def")
    return side


# ---------------------------------------------------------------- overview → kpis + estilo
def overview_rows(ov):
    keys = ov["keys"]
    out = {}
    for s, row in ov.items():
        if s == "keys":
            continue
        out[int(s)] = dict(zip(keys, row[1:]))
    return out


def kpis_of(o):
    m = o["matchesPlayed"] or 0
    return {"matches": m, "wins": o["matchesWon"], "losses": o["matchesLost"],
            "winRate": pct(o["matchesWon"], m), "kd": round(o["kills"] / max(1, o["deaths"]), 2),
            "peakRP": o["maxRankPoints"], "latestRP": o["rankPoints"]}


def style_of(o, maps_rows):
    r = o["roundsPlayed"] or 0
    fb, fd = o["firstBloods"] or 0, o["firstDeaths"] or 0
    cw, cl = o["clutches"] or 0, o["clutchesLost"] or 0
    by = []
    for n in range(1, 6):
        w = o.get(f"clutches1v{n}") or 0
        by.append([w, w + (o.get(f"clutchesLost1v{n}") or 0)])
    multi = [o.get(f"kills{n}K") or 0 for n in (2, 3, 4, 5)]
    st = {"rounds": r, "roundWR": pct(o["roundsWon"], r),
          "fb": fb, "fd": fd, "openPct": pct(fb + fd, r), "esr": pct(fb, fb + fd, 0),
          "kpr": round(o["kills"] / max(1, r), 2), "dpr": round(o["deaths"] / max(1, r), 2),
          "apr": round((o["assists"] or 0) / max(1, r), 2), "hs": pct(o["headshots"] or 0, o["kills"] or 0, 0),
          "clutchW": cw, "clutchL": cl, "clutchPct": pct(cw + cl, r), "clutchBy": by,
          "multi": multi, "multiRounds": sum(multi), "multiPct": pct(sum(multi), r)}
    if maps_rows:
        for code, key in (("a", "atkRoundWR"), ("d", "defRoundWR")):
            rp = sum(x[4] for x in maps_rows if x[1] == code)
            rw = sum(x[5] for x in maps_rows if x[1] == code)
            st[key] = pct(rw, rp)
            st[key.replace("WR", "s")] = [rw, rp]
    return st


# ---------------------------------------------------------------- operadores
def score(o, base_wr, base_kd):
    """Igual ao scoreOp() do app: encolhe win% e K/D para a média do jogador conforme a amostra."""
    n = o["rounds"]
    adj_wr = (o["wr"] * n + base_wr * 10) / (n + 10)
    adj_kd = (o["kd"] * n + base_kd * 25) / (n + 25)
    return (adj_wr - base_wr) + (adj_kd - base_kd) * 12


def op_lists(rows, base_wr, base_kd):
    ops = []
    for r in rows:
        name, sd, rp, rw, k, d = r[0].strip(), r[1], r[4], r[5], r[6], r[7]
        if not sd or not rp:
            continue
        ops.append({"name": name, "side": "def" if sd == "d" else "atk", "rounds": rp,
                    "wr": round(100 * rw / rp), "kd": round(k / max(1, d), 2)})
    cut = sorted([o for o in ops if o["rounds"] >= MIN_ROUNDS and o["wr"] < 45], key=lambda o: -o["rounds"])[:5]
    cut_names = {o["name"] for o in cut}

    def side_list(sd):
        pool = [o for o in ops if o["side"] == sd and o["name"] not in cut_names]
        good = [o for o in pool if o["rounds"] >= MIN_ROUNDS]
        if len(good) < 2:                       # amostra curta: completa com o que tem
            good = sorted(pool, key=lambda o: -o["rounds"])[:3]
        # quem tem rounds de verdade vem antes; amostra curta entra depois, mesmo com % alto
        solid = [o for o in good if o["rounds"] >= SOLID_ROUNDS]
        thin = [o for o in good if o["rounds"] < SOLID_ROUNDS]
        by_score = lambda l: sorted(l, key=lambda o: -score(o, base_wr, base_kd))
        lst = (by_score(solid) + by_score(thin))[:5]
        most = max(pool, key=lambda o: o["rounds"], default=None)
        out = []
        for i, o in enumerate(lst):
            e = {"name": o["name"], "wr": o["wr"], "kd": o["kd"], "rounds": o["rounds"],
                 "tag": f"main · {o['rounds']} rds" if most and o["name"] == most["name"] else ""}
            if i == 0 and o["wr"] >= 55 and o["rounds"] >= SOLID_ROUNDS:
                e["star"] = True
            if o["rounds"] < MIN_ROUNDS:
                e["small"] = True
            out.append(e)
        return out

    cut_out = [{"name": o["name"], "wr": o["wr"], "kd": o["kd"], "rounds": o["rounds"],
                "tag": f"{o['rounds']} rds"} for o in cut]
    return side_list("def"), side_list("atk"), cut_out, {o["name"]: o["side"] for o in ops}


def ops_all(rows):
    """Lista completa de operadores da season, direto do raw do tracker (sem corte de amostra)."""
    out = []
    for r in rows:
        name, sd = r[0].strip(), r[1]
        if not sd or not r[4]:
            continue
        out.append({"n": name, "s": sd, "r": r[4], "w": r[5], "k": r[6], "d": r[7], "a": r[8],
                    "hs": r[9], "fb": r[10], "fd": r[11], "cw": r[12], "cl": r[13],
                    "m": r[2], "mw": r[3]})
    return sorted(out, key=lambda o: -o["r"])


# ---------------------------------------------------------------- mapas
def maps_of(rows, opmaps, op_side):
    tot = [r for r in rows if r[1] == ""]
    by_side = {(r[0], r[1]): r for r in rows if r[1]}
    per_map = collections.defaultdict(lambda: {"def": [], "atk": []})
    if opmaps:
        for op, lst in opmaps["ops"].items():
            sd = op_side.get(op)
            if not sd:
                continue
            for name, rp, rw, k, d in lst:
                if rp:
                    per_map[name][sd].append({"name": op, "wr": round(100 * rw / rp), "rounds": rp,
                                              "kd": round(k / max(1, d), 2)})
    out = []
    for r in tot:
        name, mp, mw, k, d = r[0], r[2], r[3], r[6], r[7]
        if not mp:
            continue
        m = {"name": name, "matches": mp, "seasonWR": pct(mw, mp), "kd": round(k / max(1, d), 2)}
        notes = []
        for code, key, label in (("a", "atkWR", "Ataque"), ("d", "defWR", "Defesa")):
            s = by_side.get((name, code))
            m[key] = pct(s[5], s[4]) if s and s[4] else None
            if s and s[4] >= 10 and s[5] / s[4] <= 0.2:
                notes.append(f"{label}: {s[5]} de {s[4]} rounds nesta season.")
        if notes:
            m["note"] = " ".join(notes)
        if name in per_map:
            worst = None
            for sd in ("def", "atk"):
                lst = sorted(per_map[name][sd], key=lambda o: -o["rounds"])
                for o in lst:
                    if o["rounds"] < MIN_ROUNDS:
                        o["small"] = True
                    if o["rounds"] >= 6 and o["wr"] <= 35 and (not worst or o["rounds"] > worst[0]["rounds"]):
                        worst = (o, sd)
                if lst:
                    m[sd] = lst[:4]
            if worst:
                o, sd = worst
                m["avoid"] = f"{o['name']} {'no ataque' if sd == 'atk' else 'na defesa'} ({o['wr']}% em {o['rounds']} rounds)."
        out.append(m)
    return sorted(out, key=lambda m: (-m["seasonWR"], -m["matches"]))


# ---------------------------------------------------------------- partidas
def match_rows(path):
    d = load(path)
    rows = [dict(zip(d["keys"], r)) for r in d["rows"]]
    for r in rows:
        r["season"] = season_of(r["timestamp"])
    return rows


def recent_of(rows):
    out = []
    for r in rows:                              # já vem da mais nova para a mais antiga
        if not r.get("map"):
            continue                            # penalidade de abandono, sem mapa
        out.append({"map": r["map"], "w": bool(r["win"]),
                    "kd": round((r["kills"] or 0) / max(1, r["deaths"] or 0), 2),
                    "rp": r["rankPointsDelta"] or 0})
        if len(out) == RECENT:
            break
    return out


def rp_rate(rows):
    w = [r["rankPointsDelta"] for r in rows if r["rankPointsDelta"] is not None and r["win"] == 1 and r.get("map")]
    l = [r["rankPointsDelta"] for r in rows if r["rankPointsDelta"] is not None and r["win"] == 0 and r.get("map")]
    if len(w) < 3 or len(l) < 3:
        return None
    return {"win": round(statistics.mean(w), 1), "loss": round(statistics.mean(l), 1), "n": len(w) + len(l)}


def ts_min(t):
    import datetime as dt
    return dt.datetime.fromisoformat(t[:16]).timestamp() / 60


def tilt_of(rows):
    """Resultado da partida seguinte dentro da mesma sessão (pausa > 75 min abre sessão nova)
    + vitórias pela posição na sessão (1ª, 2ª, 3ª, 4ª+ partida)."""
    ch = sorted([r for r in rows if r.get("map")], key=lambda r: r["timestamp"])
    after_l, after_w, sessions = [0, 0], [0, 0], 0
    by_game = [[0, 0] for _ in range(4)]
    gi, prev = 0, None
    for m in ch:
        gap = (ts_min(m["timestamp"]) - ts_min(prev["timestamp"])
               - (prev.get("durationMs") or 30 * 60000) / 60000) if prev else None
        if prev is None or gap > SESSION_GAP_MIN:
            sessions += 1
            gi = 1
        else:
            gi += 1
            t = after_w if prev["win"] else after_l
            t[0] += m["win"]
            t[1] += 1
        b = by_game[min(gi, 4) - 1]
        b[0] += m["win"]
        b[1] += 1
        prev = m
    return {"afterLoss": after_l, "afterWin": after_w, "sessions": sessions, "matches": len(ch),
            "byGame": by_game}


def hours_of(rows):
    """Vitórias por faixa de horário local (America/Sao_Paulo, UTC-3): a régua do
    'madrugada não paga'. Faixas: manhã 06-12, tarde 12-18, noite 18-24, madrugada 00-06."""
    bands = {"manha": [0, 0], "tarde": [0, 0], "noite": [0, 0], "madrugada": [0, 0]}
    for r in rows:
        if not r.get("map"):
            continue
        h = (int(r["timestamp"][11:13]) - 3) % 24
        b = bands["manha" if 6 <= h < 12 else "tarde" if 12 <= h < 18 else "noite" if 18 <= h < 24 else "madrugada"]
        b[0] += r["win"]; b[1] += 1
    return bands


def squad_of(slug, rows, others):
    """Fila: partida jogada junto com alguém do squad = mesmo minuto de início + mesmo mapa.
    Cada modo vira [vitórias, partidas, abates, mortes, soma de RP]."""
    acc = {"solo": [0, 0, 0, 0, 0], "together": [0, 0, 0, 0, 0]}
    who = collections.Counter()
    per = {o: [0, 0] for o in others if o != slug}   # [vitórias, partidas] SÓ com aquele amigo
    trio = [0, 0]                                    # com 2+ do squad na mesma partida
    for r in rows:
        if not r.get("map"):
            continue
        key = (r["timestamp"][:16], r["map"])
        mates = [o for o, keys in others.items() if o != slug and key in keys]
        a = acc["together" if mates else "solo"]
        a[0] += r["win"]; a[1] += 1; a[2] += r["kills"] or 0; a[3] += r["deaths"] or 0
        a[4] += r["rankPointsDelta"] or 0
        who.update(mates)
        grp = trio if len(mates) >= 2 else (per[mates[0]] if mates else None)
        if grp is not None:
            grp[0] += r["win"]; grp[1] += 1
    return {**acc, "with": dict(who), "n": sum(a[1] for a in acc.values()),
            "perFriend": per, "trio": trio}


def trend_of(rows, rounds_path):
    """Últimas 15 partidas × o resto da season: vitórias, K/D e 1º duelo (do kill feed,
    juntando pelo prefixo de 8 caracteres do id) e RP médio por partida."""
    feed = {}
    for l in open(rounds_path, encoding="utf-8"):
        if l.strip():
            m = json.loads(l)
            feed[m["id"]] = next(p for p in m["P"] if p[1] == 1)
    ch = sorted([r for r in rows if r.get("map")], key=lambda r: r["timestamp"])

    def agg(part):
        k = d = fk = fd = 0
        for r in part:
            p = feed.get((r.get("id") or "")[:8])
            if p:
                k += p[4]; d += p[5]; fk += p[7]; fd += p[8]
        rp = [r["rankPointsDelta"] or 0 for r in part]
        return {"w": sum(1 for r in part if r["win"]), "n": len(part), "kd": round(k / max(1, d), 2),
                "esr": [fk, fk + fd], "rp": round(statistics.mean(rp), 1) if rp else None}
    return {"last": agg(ch[-15:]), "rest": agg(ch[:-15])}


# ---------------------------------------------------------------- kill feed → coach
def coach_of(path, side_of):
    ms = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    c = collections.Counter()
    ref = collections.Counter()          # outros jogadores com K/D >= REF_KD na partida
    rp_me, rp_mates, rp_en = [], [], []
    kd_mates, kd_en = [0, 0], [0, 0]
    kills_team = kills_en = 0
    clutch_me = [[0, 0] for _ in range(5)]
    clutch_ref = [[0, 0] for _ in range(5)]
    for m in ms:
        P = m["P"]
        me = next(i for i, p in enumerate(P) if p[1] == 1)
        T = P[me][0]
        team = [i for i, p in enumerate(P) if p[0] == T]
        mates = [i for i in team if i != me]
        ens = [i for i, p in enumerate(P) if p[0] != T]
        pre = lambda p: p[2] - p[3] if p[2] is not None and p[3] is not None else None
        if pre(P[me]) is not None:
            rp_me.append(pre(P[me]))
        a = [pre(P[i]) for i in mates if pre(P[i]) is not None]
        b = [pre(P[i]) for i in ens if pre(P[i]) is not None]
        if a and b:
            rp_mates.append(statistics.mean(a))
            rp_en.append(statistics.mean(b))
        for i in mates:
            kd_mates[0] += P[i][4]; kd_mates[1] += P[i][5]
        for i in ens:
            kd_en[0] += P[i][4]; kd_en[1] += P[i][5]
        kills_team += sum(P[i][4] for i in team)
        kills_en += sum(P[i][4] for i in ens)
        ops = {i: (P[i][10].split(".") if P[i][10] else []) for i in team}
        good = {i for i in range(10) if i != me and P[i][4] / max(1, P[i][5]) >= REF_KD}
        myw = enw = 0
        mflags = set()
        prev_alone, prev_lost = None, False      # round anterior: fui o último vivo (W/L)? perdemos?
        deaths_by = collections.Counter()        # quem me matou, nesta partida
        for r, s in enumerate(m["R"]):
            w, ev = s.split(":")
            won = int(w) == T
            # match point, pelo placar ANTES do round
            if (myw == 3 and enw <= 2) or myw == 4:
                c["mp_mine"] += 1
                c["mp_mine_w"] += won
            if (enw == 3 and myw <= 2) or enw == 4:
                c["mp_theirs"] += 1
                c["mp_theirs_w"] += won
            # round decisivo ("dar a cara"): match point de qualquer lado ou overtime
            crucial = (myw == 3 and enw <= 2) or myw == 4 or (enw == 3 and myw <= 2) or enw == 4 or r >= 6
            # o round seguinte a um clutch (eu último vivo) e a qualquer derrota de round
            if prev_lost:
                c["pc_any"] += 1
                c["pc_any_w"] += won
            if prev_alone:
                c[f"pc_{prev_alone}"] += 1
                c[f"pc_{prev_alone}_w"] += won
            prev_alone, prev_lost = None, not won
            myw += won
            enw += not won
            if (myw, enw) in {(2, 0), (0, 2), (3, 3)}:
                mflags.add(f"{myw}{enw}")
            if r >= 6:
                c["ot_rounds"] += 1
                c["ot_rounds_won"] += won
            sd = None
            for i in [me] + mates:
                if r < len(ops[i]) and side_of.get(ops[i][r]):
                    sd = side_of[ops[i][r]]
                    break
            if sd is None:
                continue
            other = "def" if sd == "atk" else "atk"
            side_t = {T: sd, 1 - T: other}
            c[f"rounds_{sd}"] += 1
            c[f"won_{sd}"] += won
            if sd == "atk":
                rops = {ops[i][r] for i in team if r < len(ops[i])}
                k = "hb_with" if rops & HARD_BREACH else "hb_without"
                c[k] += 1
                c[k + "_won"] += won
                if r < len(ops[me]) and ops[me][r] in HARD_BREACH:
                    c["hb_self"] += 1
                    c["hb_self_won"] += won
            E = [(ev[i], ev[i + 1]) for i in range(0, len(ev), 2)]
            if not E:
                continue
            c["rounds_feed"] += 1
            n_die = sum(1 for _, vc in E if vc != "x")
            d_idx = 0
            reached = set()
            alive = set(range(10))
            appeared = set()                     # quem entrou no feed (matou ou morreu): "deu a cara"
            last, first, alone_me, my_k, me_died = {}, {}, False, 0, False
            first_adv = first_adv_en = None      # 1ª vez (índice de morte) com vantagem numérica nossa / deles
            best_adv = best_adv_en = 0           # maior vantagem numérica vista no round
            my_kill_after = False                # matei DEPOIS de estarmos na frente
            my_death_after = None                # None = não morri pós-vantagem; True = morri trocado; False = seco
            team_dry_after = team_deaths_after = 0   # mortes do time pós-vantagem (secas / todas)
            for j, (kc, vc) in enumerate(E):
                if vc == "x":
                    continue
                v = int(vc)
                kk = int(kc) if kc != "x" else None
                appeared.add(v)
                if kk is not None:
                    appeared.add(kk)
                if kk == me:
                    my_k += 1
                    c["kills"] += 1
                    c["kills_lost"] += not won
                    if d_idx < 2:
                        c["kt_me_early"] += 1
                    if d_idx >= n_die - 2:
                        c["kt_me_late"] += 1
                    if alone_me:
                        c["kills_alone"] += 1
                        c["kills_alone_lost"] += not won
                    if first_adv is not None:
                        my_kill_after = True
                if kk in good:
                    ref["kills"] += 1
                    if d_idx < 2:
                        ref["k_early"] += 1
                    if d_idx >= n_die - 2:
                        ref["k_late"] += 1
                nxt = E[j + 1:j + 3]
                if v in mates and kk in ens:
                    c["mate_deaths"] += 1
                    tr_me = any(x[0] != "x" and int(x[0]) == me and x[1] != "x" and int(x[1]) == kk for x in nxt)
                    tr_ot = any(x[0] != "x" and int(x[0]) in mates and x[1] != "x" and int(x[1]) == kk for x in nxt)
                    if tr_me:
                        c["traded_by_me"] += 1
                    elif tr_ot:
                        c["traded_by_others"] += 1
                    if first_adv is not None:
                        team_deaths_after += 1
                        team_dry_after += not (tr_me or tr_ot)
                if v == me and kk in ens:
                    c["my_deaths"] += 1
                    deaths_by[kk] += 1
                    tr = any(x[0] != "x" and int(x[0]) in mates and x[1] != "x" and int(x[1]) == kk for x in nxt)
                    if tr:
                        c["me_traded"] += 1
                    if first_adv is not None:
                        team_deaths_after += 1
                        team_dry_after += not tr
                        my_death_after = tr
                if v == me:
                    me_died = True
                alive.discard(v)
                d_idx += 1
                tn = sum(1 for i in team if i in alive)
                en2 = sum(1 for i in ens if i in alive)
                diff = tn - en2
                if diff >= 1 and first_adv is None:
                    first_adv = d_idx
                if diff > best_adv:
                    best_adv = diff
                if diff <= -1 and first_adv_en is None:
                    first_adv_en = d_idx
                if -diff > best_adv_en:
                    best_adv_en = -diff
                stt = f"{tn}v{en2}"
                if stt in STATES and stt not in reached:
                    reached.add(stt)
                t = P[v][0]
                first.setdefault(t, v)
                tl = [i for i in range(10) if P[i][0] == t and i in alive]
                el = [i for i in range(10) if P[i][0] != t and i in alive]
                if len(tl) == 1 and t not in last and el:
                    last[t] = tl[0]
                    x = min(len(el), 5) - 1
                    if tl[0] == me:
                        clutch_me[x][0] += won; clutch_me[x][1] += 1
                    elif tl[0] in good:
                        clutch_ref[x][0] += int(w) == t; clutch_ref[x][1] += 1
                    if tl[0] == me:
                        alone_me = True
                        c[f"alone_{sd}"] += 1
                        c[f"alone_{sd}_won"] += won
                        c[f"alone_{sd}_enemies"] += len(el)
            # abertura do round
            k0, v0 = E[0]
            if v0 != "x":
                if int(v0) in team:
                    c["open_death"] += 1
                    c["open_death_won"] += won
                else:
                    c["open_kill"] += 1
                    c["open_kill_won"] += won
            # 2+ abates seus
            k2 = "multi2" if my_k >= 2 else "multi01"
            c[k2] += 1
            c[k2 + "_won"] += won
            # round sem abate seu (vivo no fim × morto) e morto mesmo levando 1+
            nk = ("nk_died" if me_died else "nk_alive") if my_k == 0 else ("nk_dk" if me_died else None)
            if nk:
                c[nk] += 1
                c[nk + "_w"] += won
            if alone_me:
                prev_alone = "W" if won else "L"
            for stt in reached:
                c[f"st_{stt}"] += 1
                c[f"st_{stt}_won"] += won
            # "dar a cara" no round decisivo × comum (você e a régua dos bons)
            part = me in appeared
            dk = "cr" if crucial else "nm"
            c[dk] += 1
            c[dk + "_p"] += part
            if crucial:
                k3 = "cr_p" if part else "cr_np"
                c[k3 + "_n"] += 1
                c[k3 + "_w"] += won
                for i in good:
                    ref["cr"] += 1
                    ref["cr_p"] += i in appeared
            # vantagem numérica: ficamos com mais vivos — convertemos? (e o espelho do inimigo)
            if best_adv >= 1:
                c["adv"] += 1
                c["adv_w"] += won
                if best_adv >= 2:
                    c["adv2"] += 1
                    c["adv2_w"] += won
                if not won:
                    c["advL"] += 1
                    if my_death_after is not None:
                        c["advL_died"] += 1
                        c["advL_died_dry"] += my_death_after is False
                    elif my_kill_after:
                        c["advL_kill"] += 1
                    else:
                        c["advL_ghost"] += 1
                    c["advL_team_deaths"] += team_deaths_after
                    c["advL_team_dry"] += team_dry_after
            if best_adv_en >= 1:
                c["adve"] += 1
                c["adve_w"] += not won
            # último vivo / primeiro a morrer — você e a régua
            if T in last:
                c[f"to1_{sd}"] += 1
                c[f"last_{sd}"] += last[T] == me
            c[f"first_{sd}"] += first.get(T) == me
            for i in good:
                t = P[i][0]
                s2 = side_t[t]
                ref[f"rounds_{s2}"] += 1
                ref[f"first_{s2}"] += first.get(t) == i
                if t in last:
                    ref[f"to1_{s2}"] += 1
                    ref[f"last_{s2}"] += last[t] == i
        mwon = myw > enw
        for f in mflags:
            c[f"m_{f}"] += 1
            c[f"m_{f}_w"] += mwon
        rv = "rv" if deaths_by and max(deaths_by.values()) >= 3 else "norv"   # alguém me matou 3+ vezes
        c[rv] += 1
        c[rv + "_w"] += mwon
    r1 = lambda x: round(x, 1)
    out = {
        "matches": len(ms), "rounds": c["rounds_feed"],
        "lastAlive": {s: [c[f"last_{s}"], c[f"to1_{s}"]] for s in ("atk", "def")},
        "lastAliveRef": {s: [ref[f"last_{s}"], ref[f"to1_{s}"]] for s in ("atk", "def")},
        "firstDeath": {s: [c[f"first_{s}"], c[f"rounds_{s}"]] for s in ("atk", "def")},
        "firstDeathRef": {s: [ref[f"first_{s}"], ref[f"rounds_{s}"]] for s in ("atk", "def")},
        "alone": {s: [c[f"alone_{s}_won"], c[f"alone_{s}"], r1(c[f"alone_{s}_enemies"] / max(1, c[f"alone_{s}"]))]
                  for s in ("atk", "def")},
        "sideRounds": {s: [c[f"won_{s}"], c[f"rounds_{s}"]] for s in ("atk", "def")},
        "hardBreach": {"with": [c["hb_with_won"], c["hb_with"]], "without": [c["hb_without_won"], c["hb_without"]],
                       "self": [c["hb_self_won"], c["hb_self"]]},
        "opening": {"kill": [c["open_kill_won"], c["open_kill"]], "death": [c["open_death_won"], c["open_death"]]},
        "multi": {"twoPlus": [c["multi2_won"], c["multi2"]], "oneOrLess": [c["multi01_won"], c["multi01"]]},
        "kills": {"total": c["kills"], "lostRounds": c["kills_lost"], "alone": c["kills_alone"],
                  "aloneLost": c["kills_alone_lost"]},
        "trades": {"mateDeaths": c["mate_deaths"], "byMe": c["traded_by_me"], "byOthers": c["traded_by_others"],
                   "myDeaths": c["my_deaths"], "meTraded": c["me_traded"]},
        "states": {k: [c[f"st_{k}_won"], c[f"st_{k}"]] for k in ("5v4", "4v4", "4v5", "5v3", "3v5", "3v3", "2v2")},
        "killTiming": {"meEarly": [c["kt_me_early"], c["kills"]], "meLate": [c["kt_me_late"], c["kills"]],
                       "refEarly": [ref["k_early"], ref["kills"]], "refLate": [ref["k_late"], ref["kills"]]},
        "score": {"led20": [c["m_20_w"], c["m_20"]], "trail02": [c["m_02_w"], c["m_02"]],
                  "ot": [c["m_33_w"], c["m_33"]], "otRounds": [c["ot_rounds_won"], c["ot_rounds"]]},
        "pressure": {"mine": [c["mp_mine_w"], c["mp_mine"]], "theirs": [c["mp_theirs_w"], c["mp_theirs"]]},
        "decisive": {"part": [c["cr_p"], c["cr"]], "partNormal": [c["nm_p"], c["nm"]],
                     "partRef": [ref["cr_p"], ref["cr"]],
                     "withFace": [c["cr_p_w"], c["cr_p_n"]], "noFace": [c["cr_np_w"], c["cr_np_n"]]},
        "advantage": {"any": [c["adv_w"], c["adv"]], "plus2": [c["adv2_w"], c["adv2"]],
                      "enemy": [c["adve_w"], c["adve"]], "lost": c["advL"],
                      "lostMe": {"ghost": c["advL_ghost"], "died": c["advL_died"],
                                 "diedDry": c["advL_died_dry"], "kill": c["advL_kill"]},
                      "lostTeamDeaths": [c["advL_team_dry"], c["advL_team_deaths"]]},
        "postClutch": {"afterLost": [c["pc_L_w"], c["pc_L"]], "afterWon": [c["pc_W_w"], c["pc_W"]],
                       "afterAnyLost": [c["pc_any_w"], c["pc_any"]]},
        "noKill": {"alive": [c["nk_alive_w"], c["nk_alive"]], "died": [c["nk_died_w"], c["nk_died"]],
                   "diedWithKill": [c["nk_dk_w"], c["nk_dk"]]},
        "rival": {"with": [c["rv_w"], c["rv"]], "without": [c["norv_w"], c["norv"]]},
        "teams": {"meRP": round(statistics.mean(rp_me)) if rp_me else None,
                  "matesRP": round(statistics.mean(rp_mates)) if rp_mates else None,
                  "enemiesRP": round(statistics.mean(rp_en)) if rp_en else None,
                  "matesKD": round(kd_mates[0] / max(1, kd_mates[1]), 2),
                  "enemiesKD": round(kd_en[0] / max(1, kd_en[1]), 2),
                  "teamKills": kills_team, "enemyKills": kills_en},
        "clutchBy": clutch_me, "clutchByRef": clutch_ref,
        "refLabel": f"outros jogadores com K/D {str(REF_KD).replace('.', ',')}+ nessas mesmas partidas",
    }
    return out


# ---------------------------------------------------------------- main
def ops_role(path):
    """Papel por operador nos rounds do kill feed: [rounds, vencidos, vivo no fim,
    1ª morte do time, rounds com kill minha na abertura (2 primeiros abates),
    rounds com kill minha no fim (2 últimos), kills]. Só ops com 10+ rounds no feed."""
    agg = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            P = rec["P"]
            me = next(i for i, p in enumerate(P) if p[1])
            myteam, mych = P[me][0], str(me)
            team = {str(i) for i, p in enumerate(P) if p[0] == myteam}
            ops = P[me][10].split(".") if P[me][10] else []
            for j, rnd in enumerate(rec["R"]):
                if j >= len(ops) or not ops[j]:
                    continue
                win, ev = rnd.split(":", 1)
                pairs = [(ev[i], ev[i + 1]) for i in range(0, len(ev) - 1, 2)]
                a = agg.setdefault(ops[j], [0] * 7)
                a[0] += 1
                if int(win) == myteam:
                    a[1] += 1
                if not any(v == mych for _, v in pairs):
                    a[2] += 1
                for _, v in pairs:
                    if v in team:
                        if v == mych:
                            a[3] += 1
                        break
                kills = [i for i, (k, _) in enumerate(pairs) if k == mych]
                a[6] += len(kills)
                if any(i < 2 for i in kills):
                    a[4] += 1
                if any(i >= len(pairs) - 2 for i in kills):
                    a[5] += 1
    return {op: a for op, a in agg.items() if a[0] >= 10}


# ---------------------------------------------------------------- lobby (randoms × squad × adversários)
def friend_sigs(raws, date, sn):
    """match_id -> {slug: (rp, delta, k, d)} do is_me no arquivo de rounds de cada jogador.
    É a assinatura que localiza o amigo dentro do P de outro jogador na mesma partida."""
    out = {}
    for slug, raw in raws.items():
        p = os.path.join(raw, f"{date}_s{sn}_rounds.jsonl")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            for ln in fh:
                if not ln.strip():
                    continue
                m = json.loads(ln)
                me = next(pp for pp in m["P"] if pp[1] == 1)
                out.setdefault(m["id"], {})[slug] = (me[2], me[3], me[4], me[5])
    return out


def lobby_of(path, slug, sigs):
    """Quem joga COM a gente: K/D dos aliados aleatórios × dos adversários, K/D de cada
    amigo nas partidas juntos, vitória quando os randoms seguram × quando não, carry
    (top de abates do time) e o RP do lobby contra o seu. Tudo do campo P do kill feed:
    P[i] = [time, is_me, rp, delta, k, d, a, fk, fd, clutch, ops]."""
    c = collections.Counter()
    friends = {}
    rp_edge = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            if not ln.strip():
                continue
            m = json.loads(ln)
            P = m["P"]
            me = next(i for i, p in enumerate(P) if p[1] == 1)
            T = P[me][0]
            mates = [i for i, p in enumerate(P) if p[0] == T and i != me]
            ens = [i for i, p in enumerate(P) if p[0] != T]
            myw = sum(1 for s in m["R"] if int(s.split(":")[0]) == T)
            won = myw > len(m["R"]) - myw
            # identifica amigos presentes nesta partida pela assinatura (rp, delta, k, d)
            here = {s: sig for s, sig in sigs.get(m["id"], {}).items() if s != slug}
            fidx, ambiguous = {}, False
            for s, (rp, dl, k, d) in here.items():
                cand = [i for i in mates if P[i][2] == rp and P[i][3] == dl
                        and P[i][4] == k and P[i][5] == d]
                if len(cand) == 1:
                    fidx[cand[0]] = s
                else:
                    ambiguous = True
            randoms = [i for i in mates if i not in fidx]
            # amigos: K/D, entry e clutch nas partidas JUNTOS
            for i, s in fidx.items():
                f = friends.setdefault(s, [0] * 7)   # [vitórias, partidas, k, d, fk, fd, clutch]
                f[0] += won; f[1] += 1
                f[2] += P[i][4]; f[3] += P[i][5]; f[4] += P[i][7]; f[5] += P[i][8]; f[6] += P[i][9]
            # randoms e adversários (partida com amigo não identificado fica fora dos randoms)
            if not ambiguous and randoms:
                rk = sum(P[i][4] for i in randoms); rd = sum(P[i][5] for i in randoms)
                c["rand_k"] += rk; c["rand_d"] += rd
                c["rand_fk"] += sum(P[i][7] for i in randoms)
                c["rand_fd"] += sum(P[i][8] for i in randoms)
                hold = "hold" if rk >= rd else "fold"
                c[hold] += 1; c[hold + "_w"] += won
            c["en_fk"] += sum(P[i][7] for i in ens)
            c["en_fd"] += sum(P[i][8] for i in ens)
            # carry: top de abates do time (empate conta)
            top = P[me][4] >= max(P[i][4] for i in mates) if mates else True
            k2 = "top" if top else "nottop"
            c[k2] += 1; c[k2 + "_w"] += won
            # RP do lobby × o seu (antes da partida)
            pre = lambda p: p[2] - p[3] if p[2] is not None and p[3] is not None else None
            mine = pre(P[me])
            lob = [pre(P[i]) for i in range(10) if i != me and pre(P[i]) is not None]
            if mine is not None and lob:
                rp_edge.append((mine - statistics.mean(lob), bool(here)))
    kd = lambda k, d: round(k / max(1, d), 2)
    return {
        "randomKD": [c["rand_k"], c["rand_d"], kd(c["rand_k"], c["rand_d"])],
        "randomFK": [c["rand_fk"], c["rand_fd"]],
        "enemyFK": [c["en_fk"], c["en_fd"]],
        "hold": [c["hold_w"], c["hold"]], "fold": [c["fold_w"], c["fold"]],
        "meTop": [c["top_w"], c["top"]], "meNotTop": [c["nottop_w"], c["nottop"]],
        "rpEdge": round(statistics.mean([e for e, _ in rp_edge])) if rp_edge else None,
        "rpEdgeWith": round(statistics.mean([e for e, w in rp_edge if w])) if any(w for _, w in rp_edge) else None,
        "rpEdgeSolo": round(statistics.mean([e for e, w in rp_edge if not w])) if any(not w for _, w in rp_edge) else None,
        "friends": {s: {"w": f[0], "n": f[1], "k": f[2], "d": f[3], "kd": kd(f[2], f[3]),
                        "fk": f[4], "fd": f[5], "clutch": f[6]}
                    for s, f in friends.items()},
    }


def main(date):
    side_all = side_table(PLAYERS)
    raws = {}
    for pdir in sorted(glob.glob(os.path.join(PLAYERS, "*"))):
        raw = os.path.join(pdir, "raw")
        if os.path.isdir(raw) and os.path.exists(os.path.join(raw, f"{date}_overview.json")):
            raws[os.path.basename(pdir)] = raw
    match_keys = {}
    for slug, raw in raws.items():
        p = os.path.join(raw, f"{date}_matches.json")
        if os.path.exists(p):
            match_keys[slug] = {(r["timestamp"][:16], r["map"]) for r in match_rows(p) if r.get("map")}
    sigs_by_sn = {sn: friend_sigs(raws, date, sn) for sn in (CURRENT - 1, CURRENT)}
    for slug, raw in raws.items():
        ov = overview_rows(load(os.path.join(raw, f"{date}_overview.json")))
        mp = os.path.join(raw, f"{date}_matches.json")
        matches = match_rows(mp) if os.path.exists(mp) else []
        for sn in (CURRENT - 1, CURRENT):
            if sn not in ov:
                continue
            o = ov[sn]
            f = lambda kind: os.path.join(raw, f"{date}_s{sn}_{kind}.json")
            maps_rows = load(f("maps"))["rows"] if os.path.exists(f("maps")) else []
            op_rows = load(f("operators"))["rows"] if os.path.exists(f("operators")) else []
            opmaps = load(f("opmaps")) if os.path.exists(f("opmaps")) else None
            k = kpis_of(o)
            d_list, a_list, cut, op_side = op_lists(op_rows, k["winRate"], k["kd"])
            srows = [r for r in matches if r["season"] == sn]
            code, label = SEASONS[sn]
            last = max((r["timestamp"] for r in srows), default=None)
            if sn == CURRENT:
                basis = f"só {code} (em andamento, até {last[8:10]}/{last[5:7]}), ranqueada" if last else f"só {code} (em andamento), ranqueada"
            else:
                basis = f"só {code} (fechada), ranqueada"
            snap = {"date": date, "season": code, "seasonOrder": sn, "seasonLabel": label, "basis": basis,
                    "kpis": k, "operatorsDef": d_list, "operatorsAtk": a_list, "operatorsCut": cut, "opsAll": ops_all(op_rows),
                    "maps": maps_of(maps_rows, opmaps, {**side_all, **op_side}),
                    "recentMatches": recent_of(srows), "style": style_of(o, maps_rows)}
            if opmaps:
                snap["opsMaps"] = opmaps["ops"]
            rr = rp_rate(srows)
            if rr:
                snap["rpRate"] = rr
            if srows:
                snap["tilt"] = tilt_of(srows)
                snap["tilt"]["hours"] = hours_of(srows)
                snap["squad"] = squad_of(slug, srows, match_keys)
            rounds = os.path.join(raw, f"{date}_s{sn}_rounds.jsonl")
            if os.path.exists(rounds):
                snap["coach"] = coach_of(rounds, side_all)
                snap["coach"]["opsRole"] = ops_role(rounds)
                snap["coach"]["lobby"] = lobby_of(rounds, slug, sigs_by_sn[sn])
                if srows:
                    snap["coach"]["trend"] = trend_of(srows, rounds)
            out = os.path.join(PLAYERS, slug, f"{date}_{code.lower()}.json")
            with open(out, "w", encoding="utf-8") as fh:
                json.dump(snap, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            print(f"OK -> players/{slug}/{os.path.basename(out)}  ({k['matches']} partidas, {k['winRate']}%, KD {k['kd']}"
                  f"{', coach' if 'coach' in snap else ''})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("uso: python3 ingest.py AAAA-MM-DD")
    main(sys.argv[1])
