# Handoff → Claude Code (le « frère code ») — MiniChat front — 2026-06-25

> Kickoff d'implémentation. Ce doc **oriente** et donne le premier ticket ; il **ne duplique pas** les
> artefacts — lis-les, ils sont la vérité. Aucun PII (cas FAE déjà anonymisé).

## État en deux lignes

Conception terminée, de-biaisée (greenfield, zéro héritage). **Aucun code écrit.** Cette session a
verrouillé 2 des 3 knobs ouverts. Prêt à coder la brique 1, qui est **sans modèle** (compatible machine
occupée par le stress-test CP-SAT).

## À lire EN PREMIER (vérité de record — ne pas réexpliquer, lire)

1. `CLAUDE.md` — cadrage autoritaire (lu d'office par toi). **Mis à jour ce jour** : ligne vocab.
2. `plan_front_testable.md` — composants, jalons M1–M5, deux tiers de test, **ordre du sprint (§7)**.
3. `decisions_et_risques.md` — le cas FAE décortiqué, scorecard BANANE, risques.
4. `knobs_2_3_resolus_2026-06-25.md` — **décisions de cette session** (vocab + détection Excel), ancrées
   sur le vrai fichier. Alimente briques 3 et 5.
5. Banc réel : `FAE.xlsx` + `dico.xlsx` (project knowledge).

## PREMIER TICKET — Brique 1 (sans GGUF). Critères vérifiables.

Périmètre exact (plan §7.1) : `ModelClient` (Protocol) + `FakeModelClient` + **trace append-only
(4 primitives)** + tests Tier A. **Aucun chargement de modèle.**

Transformé en critères (un test = un critère) :

1. **`ModelClient` (Protocol)** — contrat minimal d'appel modèle (entrée = messages + grammaire
   optionnelle ; sortie = texte contraint). → test : un type concret le satisfait statiquement.
2. **`FakeModelClient`** — réponses **scriptées** (file d'attente de sorties prédéfinies, scénarisables
   pour le PUSH 2-tours plus tard). → tests : rend les réponses dans l'ordre ; lève si file vide.
3. **Trace append-only, les 4 primitives** (CLAUDE.md § La trace) :
   (a) dialogue verbatim au fil de l'eau ; (b) spec normalisée + hypothèses **et leurs verdicts** ;
   (c) fichiers déclarés + schéma ; (d) provenance (demandeur, horodatage, modèle+config).
   → tests : **aucun UPDATE/DELETE possible** (un fait tardif = ligne neuve) ; le brut survit sous
   l'enrichi ; un échec/abandon laisse une trace partielle lisible. **Le découpage en tables est libre**
   (CLAUDE.md ne le prescrit pas) — choisis, justifie en commentaire.
4. **Tier A** (`uv run pytest`) — teste la plomberie (fake-client, trace, futurs ranking/validation).
   **Ne teste pas le modèle.** Doit tourner sans aucun GGUF présent.

Définition de « fini » : `uv run pytest` vert, `uv run ruff` propre, zéro dépendance à un modèle.

## Garde-fous NON négociables (détail dans les docs — ne pas violer)

- **Front uniquement** : pas de génération de code/solution, pas de curation/dédup, pas d'UI web tant que
  les oracles ne sont pas verts. Le front **demande**, il ne **résout** pas.
- **Trace en brique 1** : primitives irréversibles (verbatim non capturé = perdu). C'est le **minimum**
  (append-only + provenance), PAS un sous-système d'audit ISO/RGPD (plus tard).
- **`ModelClient` partout** : produit = un GGUF in-process ; banc = swap (test only) ; les deux derrière
  le Protocol. Re-valider le retenu en in-process avant de figer.
- **Zéro remnant** d'un ancien système ; tout se justifie depuis le but.
- **Avant tout code GGUF/GBNF** (briques 2+) : **Context7** pour l'API exacte de la lib (chargement,
  grammaire, support `maxItems` sur le build réel). Ne pas deviner les signatures.

## Specs résolues — où elles servent (PAS en brique 1)

- **Brique 3 (normalisateur)** : `request_type ∈ {croisement_fichiers, AUTRE}`. Slots = checklist
  oracle 1. Détail + justification : `knobs_2_3_resolus_2026-06-25.md` § knob (2).
- **Brique 5 (lecteur fichier)** : 2 patterns (rapprochement croisé, coefficient nu). **Règle de bornage
  mesurée** pour éviter 1740 faux positifs : ne flagger que littéraux à **partie fractionnaire** en
  contexte arithmétique, hors arguments entiers de lookup. Détail : `knobs_2_3_resolus_…` § knob (3).

## Knob encore ouvert (ne te concerne pas avant M3)

granite **écoute** vs seulement **docile** → tranché empiriquement à M3 (PUSH 2-tours), Tier B, granite
réel sur machine libre. La brique 1 ne fait que **bâtir le harnais** sur lequel M3 tournera.

## Conventions (rappel — global CLAUDE.md utilisateur)

- **Noms longs et clairs, zéro abréviation** (`intervention_id` pas `iid`, `config` pas `cfg`). Non
  négociable. Exceptions : indices de boucle courts, acronymes établis (SQL, API, JSON…).
- Code + commentaires en **anglais** ; communication en **français**.
- Toolchain : `uv`, `ruff` (format + lint), `pytest`. Types/hints toujours. Defaults sécurisés.
- Changements chirurgicaux, simplicité d'abord, pas de features non demandées.

## Suggested skills

- **En fin de session importante** : `handoff` (garder la chaîne de reprise vivante).
- **Au démarrage d'une session fraîche** : `resume` (reconstruit le contexte).
- Lecture/analyse de fichiers tabulaires : skill `xlsx` (formules via openpyxl `data_only=False`).
