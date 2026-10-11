# SIEGE·LAB — companion multi-season de R6 (multi-perfil)

App single-file (por jogador) com interface de produto, **seletor de season** e
comparação season-a-season (deltas ▲▼). Rank derivado do RP, split ataque/defesa
por mapa, uma aba **Coach** com plano, meta e diagnóstico round a round e uma aba **Squad**
(resultado sozinho × com cada amigo).
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
**Coach**, na ordem do que se decide *durante* a partida pro que é contexto: plano pra próxima sessão →
meta (cenário de RP + quantas derrotas cabem numa janela de 5 e de 4 partidas) → **o que os rounds mostram**
(placar de vivos · sob pressão · último vivo no ataque · hard breach · trocas · quando suas kills acontecem ·
round depois do clutch · round sem abate · clutch por 1vX · duelo repetido *(experimental)* · placar da
partida · nível dos times) → tendência (últimas 15 × o resto da season) → fila → estilo em números → tilt ·
Mapas (busca pelo nome + ordem A–Z / Vitórias / Partidas, tier auto + card por mapa com barras atk/def e top-3 de operador) ·
Operadores (mains def/atk + corte, card de hard breach "plano B", tabela completa ordenável com HS% e 1º duelo, e ficha por operador: stats, season a season, por mapa, kill feed e função do playbook) · **Squad** (vitórias sozinho × com cada amigo, uma tabela por season) ·
Evolução (sparklines season a season) · seletor de season no topo · botão ? (legenda) · card de compartilhar.

Na aba Coach as setas têm cor por direção: verde melhorou, vermelho piorou, **cinza = estilo** (nem bom nem ruim).
Meta e plano só aparecem na season mais nova; season antiga mostra só o diagnóstico daquela época.

## Design (revisão de 11/10/2026)
Tudo sai do `build.py`: um HTML estático por jogador, sem biblioteca e sem requisição externa (funciona offline).
Orçamento: ≲ 250 KB por página de jogador, ≲ 20 KB a landing. Larguras de 320 a 1100 px sem rolagem lateral na página;
botão com alvo de toque ≥ 40 px; texto de leitura ≥ 11 px (10 px só em rótulo curto em caixa-alta); contraste ≥ 4,5:1.

- **Tokens** (`TOKENS_CSS`, compartilhado entre player e landing): superfícies `--bg/--panel/--chip/--line…`, texto
  `--txt/--txt-2/--muted`, escala `--fs-1…7` (10 · 11,5 · 13 · 15 · 18 · 24 · 32 px), raios `--r-1…3`, `--nav-h`.
- **Cor é significado, não enfeite:** verde `--play` = bom · amarelo `--neu` = neutro · vermelho `--ban` = ruim ·
  azul `--atk` = ataque · laranja `--def` = defesa · dourado `--gold` = marca e seleção. Seta de contagem (nº de
  partidas, rounds) não é verde nem vermelha.
- **Tipografia:** pilha de sistema (nada de fonte externa). Fonte embutida (subset em base64, ~18 KB) fica pra
  decisão do Bruno: exige baixar o arquivo da fonte.
- **Logo e imagens:** `brand.py` é a única fonte da geometria (símbolo, emblema de rank, favicon). O `build.py` gera
  `docs/apple-touch-icon.png` e `docs/og.png` com ele (precisa do Pillow; sem Pillow só esses dois PNG não são refeitos).
- **Card de compartilhar:** SVG 1080×1350 (4:5) desenhado no navegador e convertido em PNG por `canvas`;
  "Compartilhar imagem" usa a folha de compartilhar do celular (`navigator.share` com arquivo) e, onde não houver,
  baixa o PNG.
- **Mapas — achar rápido:** campo "Buscar mapa" no topo (ignora acento e maiúscula, qualquer pedaço do nome; também
  filtra os chips de "Jogar vs banir"; sobrando um só, o card abre sozinho) + "Ordenar por" A–Z (padrão) · Vitórias
  (com o grupo "Poucas partidas") · Partidas. A ordem escolhida fica em `localStorage["siegelab.mapsort"]`
  (com `try/catch`: sem armazenamento a página funciona do mesmo jeito).
- **Convenções de texto:** vírgula decimal (`1,31`) · "K/D" · "N de M" (`4 de 10 rounds`) · `10V-10D` · `°` = amostra
  pequena (mapa < 4 partidas, operador < 8 rounds) · "cenário, não promessa" · ▲▼ pra variação.
- **Não renomear:** `#scr-inicio|coach|mapas|ops|squad|evo`, `go('id')`, `renderAll()`, `openSheet/closeSheet/openHelp/
  openSeasons/openShare/openOpSheet`, `SEASONS`, `active`, `TABS`, nem as funções de corte (`tierOf`, `wrClass`).
  Cortes e fórmulas são regra de negócio: mexer em visual não muda número.

## Modelo de dados (snapshot)
```
{ date, season, seasonOrder, seasonLabel, basis,
  kpis:{matches,wins,losses,winRate,kd,peakRP,latestRP?},
  operatorsDef[], operatorsAtk[], operatorsCut[],   # {name,wr,kd,rounds,tag,star?,small?}
  maps:[ {name,matches,seasonWR,kd,atkWR,defWR, def?[], atk?[], avoid?, note?} ],
  recentMatches:[ {map,w,kd,rp} ],                  # últimas 20, mais nova primeiro
  style:{rounds,roundWR,fb,fd,openPct,esr,kpr,hs,clutchW,clutchL,clutchPct,clutchBy[[w,n]×5],multiPct,atkRoundWR,defRoundWR,…},
  rpRate:{win,loss,n}, tilt:{afterLoss[w,n],afterWin[w,n],sessions,matches},
  squad:{solo[w,n,k,d,rp], together[…], with{slug:n}, perFriend{slug:[w,n]}, trio[w,n], n},
  opsAll:[ {n,s,r,w,k,d,a,hs,fb,fd,cw,cl,m,mw} ],   # todos os ops da season (tracker)
  opsMaps:{op:[[mapa,rounds,won,k,d]]},              # só com opmaps coletado
  coach?:{lastAlive,lastAliveRef,firstDeath,alone,hardBreach,opening,teams,trades,kills,
          pressure{mine,theirs}, postClutch{afterLost,afterWon,afterAnyLost}, noKill{alive,died,diedWithKill},
          rival{with,without}, trend{last,rest},
          opsRole{op:[r,w,vivoFim,1ªmorteTime,killAbre,killFecha,kills]}, …} }   # só com rounds.jsonl
```
- Tier do mapa = auto (win% ≥55 priorize · <40 banir · resto neutro).
- Rank = derivado do RP (bandas 500: Prata 2000/Ouro 2500/Platina 3000/Esmeralda 3500/Diamante 4000 + divisão de 100 RP, I alta → V baixa).
- "Squad" = partida no mesmo minuto e mapa de outro perfil daqui. Amigo fora do app conta como sozinho.
  `perFriend` = partidas **só com aquele amigo**; `trio` = com 2+ amigos (não se sobrepõem). A aba Squad lista só as linhas com partida.
- Régua do "último vivo": outros jogadores das mesmas partidas com K/D 1,2+ na partida (`REF_KD` no ingest).
- Chaves novas do `coach` (todas `[vitórias, partidas ou rounds]`, exceto `trend`):
  `pressure` = rounds com match point seu / deles (3 rounds a favor e o outro com até 2; no overtime, 4) ·
  `postClutch` = round seguinte a um clutch perdido, a um vencido e a qualquer round perdido ·
  `noKill` = rounds com 0 abate seu: vivo no fim / morto / morto mesmo levando 1+ ·
  `rival` = partidas em que um mesmo inimigo te matou 3+ vezes × as demais ·
  `trend` = `{last, rest}` das últimas 15 partidas × o resto, cada um `{w,n,kd,esr[fk,fk+fd],rp}` · `opsRole` = papel por operador no feed (ops com 10+ rounds).

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
3. `python3 build.py` (refaz `docs/*.html`, a landing e os dois PNG de `docs/`)
4. Commit + push → o Pages publica sozinho.

Preview local: o macOS bloqueia o servidor de preview dentro de `~/Documents`; copiar `docs/` pra uma pasta temporária e servir de lá.

## Próximos (roadmap do Bruno)
- Pesquisa profunda: resolver a COLETA em escala (tracker é Cloudflare + sem API aberta; hoje via navegador, manual).
  Opções: API paga tracker.gg (USD), coletor headless próprio, login Ubisoft do usuário. → gargalo #1 do SaaS.
- Rodar o Fable pra achar pontos fracos do produto.
- Escada de produto: briefing avulso ↔ assinatura (deep per-map e coach round a round = tier pago).
- Coletar rounds dos amigos pra ligar o diagnóstico completo do Coach neles.
