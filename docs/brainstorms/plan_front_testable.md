# Plan front testable — du banc au code

> Le « quoi/comment construire + tester ». Auto-porté. Le cadrage : [CLAUDE.md](../../CLAUDE.md). Les décisions
> + risques : [decisions_et_risques.md](decisions_et_risques.md). Objectif : un front **headless-first**,
> **testable par toi à chaque jalon** (une commande `uv run` qui imprime la spec + un verdict d'oracle),
> puis on code.

## 1. Runtime (on part sérieux)

- **Produit** : un **exe par PC**, **un seul modèle GGUF en process** (librairie Python). Pas de
  swap/daemon. Mono-commande.
- **Banc (A/B modèles, toi seulement)** : un swap de modèles (type llama-swap) est commode pour comparer
  en une ligne — **outil de test, jamais embarqué**.
- Les deux derrière un **`ModelClient` (Protocol)** + un **`FakeModelClient`** (réponses scriptées) pour
  les tests harnais sans charger de modèle.
- **Principe d'architecture** : le moteur vit **derrière le contrat** (le schéma) ; runtime et UI sont des
  **adaptateurs jetables** (zéro logique métier dedans). C'est ce qui rend l'embarquement et toute reprise
  aval mécaniques.
- ⚠️ **Re-valider le modèle retenu sur le runtime embarqué (in-process)** : le banc peut différer.
- API exacte de la lib (chargement GGUF, grammaire GBNF, `maxItems`) → **Context7 au moment de coder**.

## 2. Le flux (machine à états)

```
besoin brut
  ▼ REFORMULER   "Si je comprends bien, tu veux <X>. C'est ça ?"        (miroir)
  ▼ ANCRER       "Il me manque <ces fichiers>, peux-tu les fournir ?"   (demande, pas portail)
  ▼ QUESTIONNER  2-3 cartes (risque-si-faux), pré-remplies, swipe        (friction dosée)
  ▼ VALIDER      complétude vs schéma : PRÊT | BLOQUÉ
  ▼ NORMALISER   → spec sur vocabulaire FERMÉ (type + slots)
  ▼ ARTEFACT     spec + trace append-only
```
Le miroir et la demande de fichiers **précèdent** le questionnement fin : on ancre avant de creuser.

## 3. Composants à bâtir

1. `ModelClient` (Protocol) + `FakeModelClient` (tests) + impl de banc (swap) + impl produit (in-process).
2. **Schéma d'élicitation** (JSON-schema → grammaire GBNF) borné par `maxItems` : `{reformulation,
   fichiers_declares[], hypotheses[] (risque + rang), taches[]}`.
3. **Normalisateur** : projection sur un *type de besoin* (enum fermée seedée + `AUTRE`) + slots.
4. **Ranking + sélection** des 2-3 questions par risque-si-faux = **Python déterministe**.
5. **Lecteur de fichier** : schéma seul (noms + types + enums faible-cardinalité + échantillon
   **synthétique**) + **détection bornée** de 2 patterns (rapprochement croisé, coefficient nu).
6. **Trace** append-only (dialogue, spec, hypothèses+verdicts, fichiers, provenance).
7. **Oracles (graders)** : complétude (FAE), obéissance, écoute (PUSH 2-tours).
8. **Runners** M1–M5 (§4) + tests unitaires harnais.

## 4. Jalons TESTABLES (chacun = une commande que tu lances)

- **M1 — Obéissance (réel).** `uv run … smoke_obeissance <alias>` : system prompt impératif + tâche
  tentante. Attendu vert : granite-4.1-3b. Attendu rouge : Qwen3-1.7B. Valide runtime + porte 1.
- **M2 — Élicitation 1 tour (réel, sans UI).** `… smoke_elicit "automatise ma FAE"` → imprime la spec.
  Oracle : les trous porteurs (clé, dico, coefficients, sortie) sont-ils en question ou confirmés ?
- **M3 — Écoute / PUSH 2 tours (réel).** Tour 1 (défaut assumé) → injection d'un fait contradictoire
  (« la clé c'est la Réf partenaire ») → tour 2. Oracle : la spec **honore le fait poussé**, reste
  structurée, ne spirale pas. C'est le test qu'une interface chat normale ne peut pas faire.
- **M4 — Ancre fichier (réel, sur le vrai `FAE.xlsx`).** `… smoke_fichier FAE.xlsx` → lit le schéma,
  détecte le rapprochement croisé + le coefficient, **génère les questions précises sans humain**.
- **M5 — Boucle interactive CLI (optionnelle).** `… repl` : dialogue au clavier (reformule→confirme→
  demande fichiers→capture). Le plus cheap des « je teste moi-même ». UI web = après, jetable.

## 5. Deux tiers de test — ne pas confondre

- **Tier A — harnais (fake-client, rapide, CI)** : machine à états, ranking, validation, trace, graders.
  Ne teste **pas** le modèle. `uv run pytest`.
- **Tier B — comportement modèle (GGUF réel, lent, manuel)** : M1–M4. **Seul** tier qui prouve
  obéissance / anti-spirale / écoute / qualité, et qui tranche le choix de modèle.

## 6. Limitations à anticiper (au-delà du matériel et de l'obéissance déjà actés)

1. **GBNF × *thinking*** : la grammaire contraint chaque token ; un bloc de pensée la viole ou ne se
   ferme jamais → préférer un modèle non-thinking obéissant.
2. **Budget de contexte (~4096)** : ancre (schéma) + historique + system prompt + grammaire se disputent
   la fenêtre. Tenir le schéma **compact** (noms+types, jamais les valeurs ni les formules brutes) ;
   compaction par tour.
3. **Détection Excel = gouffre potentiel** : repérer un rapprochement croisé exige de lire les
   **formules** (pas les valeurs) ; un nombre magique exige de parcourir l'AST de formule — fragile
   (versions/locales). **Borner à 2 patterns.**
4. **Amorçage du vocabulaire fermé (œuf/poule)** : seeder 2-3 types à la main + `AUTRE`, sinon tout
   besoin neuf est rejeté.
5. **Mesure de variance mal posée** : à temp 0 la stabilité est *factice*. Vrai test = **varier la
   FORMULATION** (paraphrases équivalentes) et vérifier que la spec normalise pareil.
6. **Latence cumulée** : 3 tours × (contexte qui grossit + génération) peut faire 30–90 s perçus →
   risque engagement. Leviers : sortie courte, réutiliser le KV-cache, pré-remplissage optimiste.

## 7. Ordre du premier sprint (prêt-à-coder)

> ⚠️ **La trace remonte en brique 1.** Les primitives by-construction (append-only, provenance, verbatim,
> échecs conservés) sont **irréversibles** : un run réel non tracé = verbatim perdu pour toujours. Donc la
> couche de persistance existe **avant le premier run réel (M2)**, pas en fin de sprint. C'est le minimum
> (log append-only + provenance), PAS un sous-système d'audit (l'édifice ISO/RGPD/export = plus tard).
> Bonus : tout ceci est **sans modèle** → se construit pendant qu'une autre charge sature la machine.

1. `ModelClient` (Protocol) + `FakeModelClient` + **trace append-only (les 4 primitives)** + tests
   Tier A — **avant** tout GGUF, et compatible machine occupée.
2. Impl banc + **M1 (obéissance)** sur granite → premier vrai run que tu lances.
3. Schéma + GBNF (`maxItems` vérifié) + **M2** — écrit dans la trace dès ce premier run réel.
4. PUSH 2-tours + **M3** (le test « écoute »).
5. Lecteur fichier + 2 patterns + **M4** sur le vrai `FAE.xlsx`.
6. **M5** (REPL). UI = hors sprint.
