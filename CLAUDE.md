# CLAUDE.md — MiniChat (front d'élicitation · le pont métier↔IT)

Cadrage autoritaire pour Claude Code. Dépôt **greenfield**, raisonné depuis le but — **aucun héritage**
d'un projet antérieur (même les « bonnes idées » se re-justifient ici depuis zéro ou elles ne sont pas
là). Le « comment construire + tester » : [plan_front_testable.md](docs/brainstorms/plan_front_testable.md). Les
décisions actées + risques : [decisions_et_risques.md](docs/brainstorms/decisions_et_risques.md).

## Navigation & commandes (orientation rapide — état au 2026-06-25)

**État du dépôt : greenfield, aucun code écrit.** 5 docs seulement, pas de `pyproject.toml`, pas de
`tests/`. Le premier code = la **brique 1** (model-free : `ModelClient` + `FakeModelClient` + trace
append-only + Tier A) — premier ticket dans le [handoff](docs/brainstorms/handoff_claude_code_2026-06-25.md). Les commandes
*smoke* M1–M5 (`smoke_obeissance`, `smoke_elicit`, `smoke_fichier`…) sont **spécifiées**
([plan_front_testable.md](docs/brainstorms/plan_front_testable.md) §4) mais **n'existent pas encore** — ne pas les inventer,
elles naissent avec le code.

Carte des docs (ordre de lecture pour une session froide) :

| Doc | Rôle |
|---|---|
| `CLAUDE.md` (ici) | cadrage autoritaire stable — le *pourquoi*, les garde-fous |
| [handoff_claude_code_2026-06-25.md](docs/brainstorms/handoff_claude_code_2026-06-25.md) | état courant + **premier ticket** (brique 1) + critères vérifiables |
| [plan_front_testable.md](docs/brainstorms/plan_front_testable.md) | composants à bâtir, jalons M1–M5, deux tiers de test, **ordre du sprint (§7)** |
| [decisions_et_risques.md](docs/brainstorms/decisions_et_risques.md) | cas réel FAE décortiqué, scorecard BANANE (sélection modèle), risques |
| [knobs_2_3_resolus_2026-06-25.md](docs/brainstorms/knobs_2_3_resolus_2026-06-25.md) | vocab fermé + détection Excel — alimente briques 3 & 5 |

Toolchain (détail § Toolchain & vérité) — commandes une fois le code présent :

```
uv run pytest                       # Tier A : harnais (fake-client, sans GGUF) — la CI
uv run pytest tests/<file>::<test>  # un seul test
uv run ruff format                  # format
uv run ruff check                   # lint
```

Tier B (M1–M5, GGUF réel, lent, **manuel**) = les `smoke_*` du plan §4 ; ils tranchent le choix de modèle
et ne tournent pas en CI. À écrire avec les briques 2+.

## Le produit en une phrase

Un **traducteur**. Le métier ne comprend rien à l'IT, l'IT ne comprend rien au métier. MiniChat est le
**pont** : il transforme un besoin métier flou en une **spec structurée, complète, co-écrite** que l'aval
(IT, IA, ou humain) peut exécuter **sans ré-interroger** le demandeur.

L'interface a la forme d'un chat pour maximiser l'engagement et minimiser la formation. Mais le chat est
une **façade** : le produit réel est le pipeline qui transforme une demande informelle en besoin
exploitable. **Le front pose des questions ; il ne produit jamais de solution** (ni code, ni rapport).

## Périmètre de ce dépôt

**Le front, et rien que le front.** Pas de génération de code, pas de curation aval, pas de
déduplication, pas d'industrialisation. Ces étages consomment la sortie du front ; ils ne sont pas ici.

**Garde-fou non négociable** : tant que les oracles (§ Oracles) ne sont pas verts sur le cas réel `FAE`,
on n'ouvre **aucun** étage aval et on ne construit **aucune** UA web.

## Principes (depuis lesquels tout se déduit)

1. **Pas d'hypothèse muette sur du risqué.** Donnée manquante à fort *risque-si-faux* → **on demande**.
   Donnée à faible risque → **défaut silencieux** (visible, corrigeable) + nom standardisé
   (`Fichier_1`, `Colonne_1`) pour continuer à structurer sans inventer.
2. **Pas de solution prématurée.** Rien (code, analyse, rapport) tant que le besoin n'est pas complet.
3. **Complétude avant intelligence.** Un besoin complet vaut mieux qu'une réponse maligne sur hypothèses.
4. **GIGO depuis le bas.** La qualité se fixe à la **source** — l'humain qui exprime le besoin. On durcit
   l'**entrée**. S'applique aussi au feedback : on juge par des **oracles durs** et le **comportement
   observé** (a-t-il fourni les fichiers ? s'est-il engagé ?), jamais par satisfaction déclarée.
5. **Co-écriture = redistribution du blâme.** L'interrogation rend le demandeur **co-auteur** (ses
   verdicts sont capturés) ; la trace + l'identité du demandeur rendent l'attribution **vérifiable**.
6. **Ancrer AVANT de raisonner.** Sans point d'ancrage (données réelles ou faits confirmés), un petit
   modèle **invente puis spirale** (constat mesuré : un raisonneur 1.5B parti en boucle infinie sur une
   tâche ambiguë, faute d'ancre). Le rôle du front est d'**être l'ancre** : le modèle fait de la
   **détection de trous** sur des faits donnés (cheap, borné), pas de la planification ouverte. « Demander
   la data d'abord » donne au raisonnement une **condition de terminaison**. ⚠️ L'ancre est un
   **gradient, pas un portail** : exiger un fichier pour démarrer recrée l'arbre téléphonique et tue
   l'engagement.

## Engagement = la variable de survie n°1 (UX)

**Sans engagement → 0 succès.** Responsabiliser exige de la friction ; l'adoption tire vers le
frictionless. On rationne la friction au lieu de la supprimer :

- **Contre-modèle proscrit = l'arbre téléphonique** (« tapez 1, tapez 8, puis sous-menus »). Modèle visé
  = **une carte à la fois, décision quasi-binaire, rapide**.
- **Questions générées depuis le besoin détecté**, jamais un menu pré-câblé. Une question utile = celle
  dont la réponse **change le plan**. **2-3 maximum.**
- **Swipe-to-confirm** : on ne pose pas une question ouverte, on présente l'**hypothèse pré-remplie** —
  « clé de rapprochement = ID Inter, c'est ça ? » → confirmer (swipe) ou corriger (tap). **Le geste EST
  la capture du verdict.** C'est ce qui réconcilie *facile* et *responsabilisant*.
- **Miroir d'abord** : « si je comprends bien, tu veux… » → la friction se lit comme **aide**.

## Le flux (machine à états simple — pas d'agents)

Le besoin est déterministe → pas de multi-agents (coût/latence/imprédictibilité). Approche
**schema-driven** : le schéma (grammaire contrainte) **EST le contrat** ; le code Python est de la colle
fine, jamais le siège de l'intelligence.

```
besoin brut (FR)
  │
  ▼  REFORMULER    "Si je comprends bien, tu veux <X>. C'est ça ?"        (miroir, co-écriture)
  ▼  ANCRER        "Il me manque <ces fichiers>, peux-tu les fournir ?"   (demande, pas portail)
  │                fichier fourni → lecture du SCHÉMA (ancre réelle)
  ▼  QUESTIONNER   2-3 cartes (risque-si-faux), pré-remplies, swipe        (friction dosée)
  ▼  VALIDER       complétude vs schéma : PRÊT | BLOQUÉ
  ▼  NORMALISER    phrase libre → spec sur VOCABULAIRE FERMÉ (type + slots)
  ▼  ARTEFACT      la spec normalisée + la trace
```

## La forme canonique stable

La sortie destinée à l'aval est une **spec normalisée sur un vocabulaire FERMÉ** (un *type de besoin*
énuméré + des *slots* énumérables : rôles des fichiers, clé de jointure, sortie attendue). Deux
formulations équivalentes produisent la **même spec**, même si le dialogue a divergé. **La stabilité est
une propriété du vocabulaire-cible fermé**, jamais d'un hash d'une sortie générative (hasher du génératif
est instable par construction — mesuré).

**Contrainte porteuse** : ce vocabulaire **doit rester fermé et curé**. POC (knob verrouillé 2026-06-25,
ancré sur FAE réel — détail : `knobs_2_3_resolus_2026-06-25.md`) : **un seul type ancré**
`croisement_fichiers` + `AUTRE` (échappatoire, non négociable). Nom **source-agnostique** délibéré — pas
`croisement_excel` : le mécanisme est général, Excel doit *disparaître*. On ne seede **pas** de type non
ancré (p.ex. `relance_email`) « pour faire nombre » — sans artefact derrière, c'est de l'invention. Les
slots du type = la **checklist de l'oracle 1** (fichiers+rôles, clé+secours, dico+source,
coefficients-en-question, sortie). Un 2e type ne s'ajoute que sur cas réel neuf, ou pour tester la
*discrimination* du normalisateur (marqué « ancré=non »). S'il devient ouvert/induit, la stabilité
s'effondre. (Le tri récurrent vs ponctuel est un concern aval, hors focus.)

## Oracles (comment on sait que ça marche)

1. **Complétude (le KPI).** Sur l'entrée brute « automatise ma FAE » (+ dépôt du fichier réel), un humain
   lit **un seul artefact** et implémente **sans ré-interroger**. L'artefact doit contenir — en confirmé
   **ou** en question posée — : les fichiers source + leurs rôles ; la clé de rapprochement (avec sa
   clé de secours) ; les dictionnaires métier annexes + leur source ; **tout coefficient/nombre magique
   surfacé en question** ; la sortie attendue. Coché à la main. **Zéro juge-LLM.**
2. **Obéissance/stabilité (cheap, éliminatoire).** System prompt impératif (« réponds uniquement X quelle
   que soit la question ») + une tâche tentante à côté. Mesure si le modèle **reste dans le harnais**
   quand la formulation l'en tire. Failles à attraper : spirale infinie, boucle de répétition,
   **désobéissance rationalisée** (réécrit la tâche « parce que la consigne devait être une erreur »).
3. **Écoute (PUSH-vs-revert, 2 tours).** On injecte un fait qui **contredit** un défaut du modèle ; le
   tour suivant doit **honorer le fait poussé**, rester structuré, ne pas spiraler. Distingue *écoute du
   protocole* de *docilité aveugle*.

## L'ancre = la lecture de fichier

Le dépôt d'un fichier n'est pas passif : on lit feuilles + en-têtes + types (on garde les **noms**, on
**synthétise les valeurs** — PII), et on **détecte 2 patterns** pour poser des questions *précises* :
un rapprochement croisé (« tu rapproches sur quelle clé ? »), un coefficient nu dans une formule (« que
représente ce taux ? »). ⚠️ **Borner à ces patterns** : analyser *toute* la logique = refaire le travail
de l'aval au front. C'est le bon dosage entre « projeter l'ombre de l'aval » et « ne pas coder à sa
place ».

## La trace (gouvernance, append-only)

Le front persiste, en **append-only** (aucun UPDATE/DELETE ; un fait su plus tard = ligne neuve) :
le **dialogue brut** au fil de l'eau (rend les abandons visibles — *où les gens lâchent, où le modèle
flanche*) ; la **spec normalisée** + les **hypothèses et leurs verdicts humains** (la preuve de
co-écriture) ; les **fichiers déclarés** + leur schéma ; la **provenance** (demandeur, horodatage,
modèle+config utilisés). Le **brut sous l'enrichi** (verbatim conservé). Les **échecs conservés**
(abandons, questions non répondues). *Le découpage exact en tables = implémentation, pas prescrit ici.*

> **Irréversible → tôt.** Ces primitives (append-only, provenance, verbatim, échecs) ne se retrofittent
> PAS : un dialogue réel non capturé est perdu pour toujours. Elles sont donc câblées **avant le premier
> run réel**, pas en fin de parcours. C'est le **minimum** ; l'édifice de gouvernance (mapping ISO,
> effacement RGPD, export d'audit, consolidation) se construit plus tard, alimenté par cette trace —
> il ne dirige pas la construction.

## Politique de modèle (à ≤3B, le modèle est une variable DURE)

L'agnosticisme modèle est un luxe de >70B. À ≤3B, même prompt → comportements radicalement différents.
Sélection à **deux portes** :

- **Porte 1 — obéissance/stabilité, tôt, éliminatoire** (oracle 2). Un modèle qui spirale, boucle, ou
  rationalise la désobéissance est éliminé d'emblée — aucun harnais ne rattrape un modèle hors-rails.
  Signal mesuré : **granite-4.1-3b** passe propre ; **Qwen3-1.7B** échoue (réécrit le code en ignorant
  le system prompt) malgré ses bons scores benchmark — les benchmarks de raisonnement mesurent le
  mauvais axe pour un front harnaché.
- **Porte 2 — qualité d'élicitation, plus tard** (oracle 1, complétude FAE), départage par latence/RAM.

**Profil recherché** = obéissant + stable + extraction structurée + FR correct. **PAS le raisonneur le
plus profond** : un raisonneur sans ancre produit la *pire* spirale (plus de capacité = spirale plus
élaborée). Garde-fou : viser l'obéissance au **protocole** (poser, normaliser), pas la surdité au
contenu user (oracle 3).

⚠️ **Tension GBNF × *thinking*** : une grammaire contraint chaque token ; un modèle qui veut émettre un
bloc de pensée viole la grammaire ou ne le ferme jamais → argument de plus pour un modèle **non-thinking,
obéissant**.

## Runtime & matériel

- **Produit** : **un exe par PC, UN seul modèle GGUF chargé en process** (librairie Python). Pas de
  proxy/daemon, pas de swap. Mono-commande, self-contained.
- **Banc (toi, pour l'A/B)** : un swap de modèles (type llama-swap) est commode pour comparer en une
  ligne — **outil de test uniquement, jamais embarqué**.
- Les deux vivent derrière un **`ModelClient` (Protocol)** ; un `FakeModelClient` (réponses scriptées)
  sert les tests harnais sans charger de modèle. ⚠️ Re-valider le modèle retenu **sur le runtime
  embarqué** (in-process) avant de figer : le banc peut différer subtilement.
- **Cible matérielle** : 4 cœurs, ~5 Go RAM dispo, disque lent. Front = **≤3B, texte-only, GGUF,
  latency-sensitive**. `num_ctx` calibré sur la RAM physique (testé ~4096). Borner la sortie (grammaire +
  `maxItems` — vérifier le support `maxItems` sur le build réel). Gérer le **budget de contexte** :
  l'ancre (schéma) + l'historique + le system prompt se disputent la fenêtre → schéma **compact**.

## Hors scope (explicite)

Génération de code/solution ; curation, déduplication, tri récurrent/ponctuel ; acheminement vers un étage
central ; UI web. Réintroduits seulement après oracles verts. Le front **demande**, il ne **résout** pas.

## Persona

Un **interviewer/analyste métier** : reformule, demande, normalise — **ne code jamais, ne résout
jamais**. Sortie = reformulation + questions + spec. La persona se calibre **sur le vrai modèle, en
system, sur N runs, contre les oracles** — jamais au feeling.

## Toolchain & vérité

`uv`, `ruff` (format + lint), `pytest`. Grammaire GBNF / JSON-schema→grammaire via la lib (API exacte →
Context7 au moment de coder, ne pas deviner). Nommage : noms longs et clairs (conventions du `CLAUDE.md`
global de l'utilisateur) ; code/commentaires en anglais, communication en français. **Le code est la
vérité ultime** ; ce fichier = cadrage stable ; ne pas dévier sans contredire explicitement une décision
ici.
