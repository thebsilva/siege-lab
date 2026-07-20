# SIEGE·LAB — companion multi-season de R6 (multi-perfil)

App single-file (por jogador) com interface de produto, **seletor de season** e
comparação season-a-season (deltas ▲▼). Rank derivado do RP, split ataque/defesa
por mapa. Estética R6 Stats. Funciona offline. Base pra infoproduto/assinatura.

## Estrutura (multi-perfil)
```
players/
  <slug>/
    profile.json           # { name, platform, slug }
    AAAA-MM-DD_<season>.json   # 1 arquivo por season (com seasonOrder)
playbook.json              # COMPARTILHADO: motivo por operador + picks por mapa
build.py                   # gera 1 app por jogador
docs/<slug>.html           # os apps publicados (GitHub Pages serve daqui)
```
`build.py` varre `players/*/`, embute snapshots + profile + playbook, e escreve `docs/<slug>.html`.

## playbook.json — "quem pegar e por quê"
```
{ "operators": { "Bandit": {"side":"def","why":"Eletrifica as reforçadas…"} , … },
  "default":   { "def":[3 nomes], "atk":[3 nomes] },
  "maps":      { "Oregon": {"def":[3],"atk":[3]}, … } }
```
- O **motivo é por FUNÇÃO do operador** (negar hard breach, atrasar entrada, abrir parede…) — vale em qualquer mapa, então não há risco de callout errado. Deliberado: não inventamos nome de bomb site/parede de mapas novos.
- A **dica de estratégia por mapa é gerada no app** a partir do atk×def do próprio jogador (`mapTip()`), então é sempre correta e pessoal.
- O selo **"você X%"** ao lado do pick vem dos dados do jogador: primeiro o aproveitamento naquele mapa (se coletado), senão o da season.
- Mapa sem entrada no playbook cai no `default` — todo jogador tem recomendação em todo mapa, mesmo sem coleta por mapa.
- **Pendente/upgrade:** callouts específicos por site (ex.: "Aruni fecha as duas escadas do basement") exigem uma rodada de pesquisa por mapa antes de entrar.

## Jogadores carregados
- **superallfa** — Y11S1 (Ouro II, com top-3/mapa) + Y10S4 (Platina IV).
- **laprufer** — Y11S2 (Platina III, atual) + Y11S1 (Diamante, pico).
- **brunoprufer** — Y11S2 (Esmeralda III, atual) + Y11S1 (Diamante, pico).

## Telas / features
Início (KPIs+rank+deltas, "o que mudou desde {season}", plano de jogo) · Mapas (tier
auto + card por mapa com barras atk/def e, se coletado, top-3 de operador) ·
Operadores (mains def/atk + corte) · Evolução (sparklines season a season) · seletor
de season no topo · botão ? (legenda).

## Modelo de dados (snapshot)
```
{ date, season, seasonOrder, seasonLabel, basis,
  kpis:{matches,wins,losses,winRate,kd,peakRP,latestRP?},
  operatorsDef[], operatorsAtk[], operatorsCut[],   # {name,wr,kd,tag,star?,small?}
  maps:[ {name,matches,seasonWR,kd,atkWR,defWR, def?[], atk?[], avoid?, note?} ] }
```
- Tier do mapa = auto (win% ≥55 priorize · <40 banir · resto neutro).
- Rank = derivado do peakRP (bandas 500: Prata2000/Ouro2500/Platina3000/Esmeralda3500/Diamante4000 + divisão 100RP, I alta→V baixa).
- `def/atk` (top-3 operador por mapa) é OPCIONAL — sem ele, o card mostra só o split atk/def (usado nos amigos = MVP enxuto).

## Como adicionar jogador / atualizar season
1. No r6.tracker.network/<plataforma>/<perfil>, filtro **Ranked** + a season:
   aba **Seasons** (KPIs+RP), **Maps** (tier + atk/def), **Operators** (mains).
   Nº de season na URL: Y10S4=40, Y11S1=41, Y11S2=42…
2. Criar `players/<slug>/profile.json` + `players/<slug>/AAAA-MM-DD_<season>.json`.
3. `cd ~/Documents/R6-SuperAllfa && python3 build.py`
4. Abrir `out/<slug>.html`.

## Colocar online
`out/*.html` são estáticos e self-contained → hospedar em GitHub Pages / Netlify / Cloudflare Pages
é só subir a pasta. Cada amigo abre `.../<slug>.html`.

## Próximos (roadmap do Bruno)
- Pesquisa profunda: resolver a COLETA (tracker é Cloudflare + sem API aberta; hoje via browser, manual).
  Opções: API paga tracker.gg (USD), coletor headless próprio, login Ubisoft do usuário. → gargalo #1 do SaaS.
- Rodar o Fable pra achar pontos fracos do produto.
- Escada de produto: briefing avulso ↔ assinatura (deep per-map = tier pago).
