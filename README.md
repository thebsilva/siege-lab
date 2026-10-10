# SIEGE·LAB — companion multi-season de R6 (multi-perfil)

App single-file (por jogador) com interface de produto, **seletor de season** e
comparação season-a-season (deltas ▲▼). Rank derivado do RP, split ataque/defesa
por mapa e uma aba **Coach** com meta, plano e diagnóstico round a round.
Funciona offline. Base pra infoproduto/assinatura.

No ar: https://thebsilva.github.io/siege-lab/ (Pages publica `docs/` a cada push, via `deploy-pages.yml`).

## Estrutura (multi-perfil)
```
players/
  <slug>/
    profile.json               # { name, platform, slug, goal? }
    AAAA-MM-DD_<season>.json   # 1 snapshot por season (com seasonOrder) — é o que o app lê
    raw/AAAA-MM-DD_*.json(l)   # coleta crua do tracker (o build não lê; o ingest sim)
playbook.json                  # COMPARTILHADO: motivo por operador + picks por mapa
ingest.py                      # raw/ → snapshots (KPIs, mapas, ops, estilo, fila, tilt, coach)
build.py                       # snapshots → docs/<slug>.html + docs/index.html
docs/                          # o que o GitHub Pages serve
```
`profile.json` aceita `"goal": {"rp": 3000, "label": "Platina", "set": "AAAA-MM-DD"}`: a aba Coach
usa essa meta; sem ela, mostra a próxima cor de rank.

## playbook.json — "quem pegar e por quê"
```
{ "operators": { "Bandit": {"side":"def","why":"Eletrifica as reforçadas…"} , … },
  "default":   { "def":[3 nomes], "atk":[3 nomes] },
  "maps":      { "Oregon": {"def":[3],"atk":[3]}, … } }
```
### Como a recomendação é calculada (merge amostra × vitória × K/D)
A ordem dos picks **não** é meta/opinião: é score em `scoreOp()` (e `score()` no ingest, igual).
```
adjWR = (wr*n + baseWR*10) / (n+10)      # encolhe p/ a média do jogador
adjKD = (kd*n + baseKD*25) / (n+25)      # K/D varia mais -> encolhe mais
score = (adjWR - baseWR) + (adjKD - baseKD) * 12
```
- `n` = rounds jogados com o op (naquele mapa, senão na season); base = win% e K/D da season do jogador.
- Amostra pequena é puxada pra média → 100% em 2 rounds não fura a fila; 67% em 30 rounds passa na frente de 52% em 370.
- Nas listas de mains (aba Operadores e Início), operador com **15+ rounds vem antes** e só ele ganha ★; abaixo de 8 rounds não entra (°).
- **Fonte, em ordem:** dado do op naquele mapa → dado da season → playbook (só se não houver dado). O card rotula qual foi usada.
- O **motivo cita os números** (`"67% em 30 rounds · K/D 1.38 — bem acima da sua média"`) e abaixo vem a função do op como contexto.
- Limiares: score ≥10 "bem acima" · ≥3 "acima" · ≤-5 "abaixo — cuidado" · <8 rounds "amostra curta".
- O **motivo de função do operador** vale em qualquer mapa, então não há risco de callout errado. Deliberado: não inventamos nome de bomb site/parede.
- A **dica de estratégia por mapa é gerada no app** a partir do atk×def do próprio jogador (`mapTip()`).
- Mapa sem entrada no playbook cai no `default`.
- **Pendente/upgrade:** callouts específicos por site exigem uma rodada de pesquisa por mapa antes de entrar.

## Jogadores carregados (coleta de 09/10/2026)
- **superallfa** — Y11S3 (em andamento, Ouro III, 2.702 RP, com diagnóstico round a round) · Y11S2 (fechada) · Y11S1 · Y10S4. Meta: Platina.
- **laprufer** — Y11S3 (em andamento, Platina I) · Y11S2 (fechada) · Y11S1.
- **brunoprufer** — Y11S3 (em andamento, Esmeralda V) · Y11S2 (fechada) · Y11S1.

## Telas / features
Início (KPIs + rank + deltas, falta pro próximo rank, forma recente, "o que mudou desde {season}", plano de jogo) ·
**Coach** (meta com cenário de RP, plano pra próxima sessão, último vivo no ataque, clutch por 1vX,
hard breach, nível dos times, fila sozinho × squad, estilo em números, tilt) ·
Mapas (tier auto + card por mapa com barras atk/def e top-3 de operador) ·
Operadores (mains def/atk + corte) · Evolução (sparklines season a season) · seletor de season no topo ·
botão ? (legenda) · card de compartilhar.

Na aba Coach as setas têm cor por direção: verde melhorou, vermelho piorou, **cinza = estilo** (nem bom nem ruim).
Meta e plano só aparecem na season mais nova; season antiga mostra só o diagnóstico daquela época.

## Modelo de dados (snapshot)
```
{ date, season, seasonOrder, seasonLabel, basis,
  kpis:{matches,wins,losses,winRate,kd,peakRP,latestRP?},
  operatorsDef[], operatorsAtk[], operatorsCut[],   # {name,wr,kd,rounds,tag,star?,small?}
  maps:[ {name,matches,seasonWR,kd,atkWR,defWR, def?[], atk?[], avoid?, note?} ],
  recentMatches:[ {map,w,kd,rp} ],                  # últimas 20, mais nova primeiro
  style:{rounds,roundWR,fb,fd,openPct,esr,kpr,hs,clutchW,clutchL,clutchPct,clutchBy[[w,n]×5],multiPct,atkRoundWR,defRoundWR,…},
  rpRate:{win,loss,n}, tilt:{afterLoss[w,n],afterWin[w,n],sessions,matches},
  squad:{solo[w,n,k,d,rp], together[…], with{slug:n}, n},
  coach?:{lastAlive,lastAliveRef,firstDeath,alone,hardBreach,opening,teams,trades,kills,…} }   # só com rounds.jsonl
```
- Tier do mapa = auto (win% ≥55 priorize · <40 banir · resto neutro).
- Rank = derivado do RP (bandas 500: Prata 2000/Ouro 2500/Platina 3000/Esmeralda 3500/Diamante 4000 + divisão de 100 RP, I alta → V baixa).
- "Squad" = partida no mesmo minuto e mapa de outro perfil daqui. Amigo fora do app conta como sozinho.
- Régua do "último vivo": outros jogadores das mesmas partidas com K/D 1,2+ na partida (`REF_KD` no ingest).

## Como atualizar (coleta → ingest → build)
1. **Coletar** no r6.tracker.network (o Claude faz pelo navegador do app; o Cloudflare bloqueia fetch direto).
   Cada página traz os dados em `window.__INITIAL_STATE__`. Esperar 3–5 s entre páginas, senão cai no "Just a moment...".
   Season na URL: Y10S4=40, Y11S1=41, Y11S2=42, Y11S3=43 (abriu em 01/09/2026).
   ```
   /r6siege/profile/psn/<perfil>/overview                                         → raw/<data>_overview.json
   /r6siege/profile/psn/<perfil>/maps?season=NN&gamemode=pvp_ranked&playlist=ranked      → raw/<data>_sNN_maps.json
   /r6siege/profile/psn/<perfil>/operators?season=NN&gamemode=pvp_ranked&playlist=ranked → raw/<data>_sNN_operators.json
   …/maps?season=NN&…&operator=<op>   (1 por operador)                            → raw/<data>_sNN_opmaps.json
   /r6siege/profile/psn/<perfil>/matches?gamemode=pvp_ranked&playlist=ranked      → raw/<data>_matches.json ("Load More" até cobrir a season)
   /r6siege/matches/<id>?tab=match-rounds   (1 por partida)                       → raw/<data>_sNN_rounds.jsonl
   ```
   O formato de cada arquivo está no topo do `ingest.py`. opmaps e rounds são opcionais (sem eles, o card do
   mapa usa os dados da season e a aba Coach mostra só estilo, fila e tilt).
2. `python3 ingest.py AAAA-MM-DD` (gera os snapshots; season nova = acrescentar em `SEASONS`/`CURRENT`/`SEASON_START`).
3. `python3 build.py`
4. Commit + push → o Pages publica sozinho.

Preview local: o macOS bloqueia o servidor de preview dentro de `~/Documents`; copiar `docs/` pra uma pasta temporária e servir de lá.

## Próximos (roadmap do Bruno)
- Pesquisa profunda: resolver a COLETA em escala (tracker é Cloudflare + sem API aberta; hoje via navegador, manual).
  Opções: API paga tracker.gg (USD), coletor headless próprio, login Ubisoft do usuário. → gargalo #1 do SaaS.
- Rodar o Fable pra achar pontos fracos do produto.
- Escada de produto: briefing avulso ↔ assinatura (deep per-map e coach round a round = tier pago).
- Coletar rounds dos amigos pra ligar o diagnóstico completo do Coach neles.
