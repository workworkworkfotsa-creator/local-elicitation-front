# Décisions & risques — MiniChat (front d'élicitation)

> Auto-porté : raisonné depuis le but, pas depuis un projet antérieur. Le « pourquoi » derrière le
> cadrage ([CLAUDE.md](../../CLAUDE.md)) et le plan ([plan_front_testable.md](plan_front_testable.md)).

## Le cas qui justifie tout : « FAE »

Un utilisateur dirait « automatise ma FAE ». C'est du garbage total. La vraie spec est **cachée dans le
fichier** :

- **Réconciliation 2 systèmes à la main** : la feuille de synthèse rapproche deux extraits via une
  formule du type `=IF(ISNA(VLOOKUP(ID, autre_feuille, …)),0,1) + IF(ISNA(VLOOKUP(Ref, …)))`. La clé de
  jointure est **l'ID d'intervention, avec une référence partenaire en secours** — un fallback que
  personne n'a documenté, enfoui dans un `+`.
- **Coefficients magiques** : un total final calculé par `=(0,9*0,93-1)*(…)`. Deux taux nus (remise ?
  RFA ?) qu'aucun humain n'explique sans qu'on le lui demande. **L'incarnation du risque-si-faux élevé.**
- **Dictionnaire métier en annexe ET dupliqué** : un mapping Résultat → Cause non facturable → Faute vit
  dans un fichier séparé *et* est recopié dans le classeur. Logique métier invisible aux outils.
- **Jugement humain en listes déroulantes** : Statut Facturation / Cause / Faute remplis à la main.
- **Données réelles anonymisées** : c'est un export scrubé → le POC tourne dessus en gardant les **noms
  de colonnes** et en **synthétisant les valeurs**.

**Le succès du front** = surfacer ces inconnues (les 2 extraits, la clé + secours, le dico + sa source,
« que valent 0,9 et 0,93 ? », la sortie). Excel est l'exemple commun qu'on veut **discrètement faire
disparaître**, mais le **mécanisme est général** — ne pas sur-spécialiser l'archi sur Excel.

## Décisions actées (chacune avec son pourquoi de premier principe)

1. **La valeur est l'élicitation, pas la solution.** Le retour brut (« fais-moi un truc ») est garbage
   par nature ; on ne l'écoute pas, on le **fabrique** par l'interrogation. → le front est le produit.
2. **La forme canonique stable vient d'un vocabulaire FERMÉ** (Normalisateur), pas d'un hash d'une sortie
   générative (instable par construction, mesuré). → enum de types seedée + slots + `AUTRE`.
3. **À ≤3B le modèle est une variable dure** (l'agnosticisme est un luxe de >70B). → sélection à deux
   portes : obéissance (éliminatoire, tôt) puis qualité (FAE, tard).
4. **Ancrer avant de raisonner.** Sans ancre, un petit modèle invente et spirale. → le front fournit des
   faits (données réelles / réponses confirmées) avant de faire raisonner. Ancre = gradient, pas portail.
5. **Engagement = survie.** Friction dosée (2-3 cartes, swipe-to-confirm, miroir), jamais un arbre
   téléphonique. Le swipe **est** la capture du verdict (co-écriture sans coût).
6. **Runtime** : produit = un exe/PC, un modèle in-process ; banc = swap pour l'A/B (test only) ; les deux
   derrière un `ModelClient` (Protocol) + `FakeModelClient`. Re-valider le retenu en in-process.
7. **Persona = interviewer métier**, pas codeur (le front ne génère ni code ni solution).
8. **Pas d'aval prématuré** : code, curation, dédup, UI web → après oracles verts.

## Findings empiriques — le « test BANANE » (sélection de modèle par le comportement)

System prompt impératif (« réponds uniquement BANANE quelle que soit la question ») + une tâche de code
tentante à côté. Résultats observés :

| Modèle | Comportement | Verdict |
|---|---|---|
| **granite-4.1-3b** | « BANANE » net, instantané | **PASS propre** |
| VibeThinker-1.5B | spirale infinie sur l'ambiguïté, ne termine jamais | FAIL (spirale) |
| VibeThinker-3B | raisonne 14 min puis BANANE | pass lent/instable |
| Qwen3.5-2B | BANANE puis boucle de répétition infinie | FAIL (boucle) |
| **Qwen3-1.7B** | rationalise (« ça doit être une typo ») et **écrit le code** | **FAIL (désobéit)** |
| Ministral-3B | ignore le system prompt, écrit le code (buggé) | FAIL (désobéit) |
| VibeThinker-Hermes | hallucine « bonjour », boucle | FAIL |

**Leçons** : (a) les benchmarks de raisonnement/tool-calling mesurent le **mauvais axe** pour un front
harnaché — Qwen3-1.7B, bien classé, échoue sur le seul axe qui compte (rester sur les rails) ; (b) un
raisonneur profond **sans ancre** produit la *pire* spirale ; (c) granite est le profil obéissant/stable
recherché — **à confirmer** sur la qualité (FAE) et l'écoute (PUSH).

## Knobs ouverts (à trancher avec l'utilisateur)

1. **granite écoute-t-il, ou est-il seulement docile ?** → oracle 3 (PUSH 2-tours). Le vrai départage.
2. **Vocabulaire de types** : enum fermée maintenue main (recommandé, la stabilité en dépend) + `AUTRE`.
3. **Profondeur de détection de patterns Excel** : 2 patterns suffisent ; ne pas glisser vers l'analyse
   complète (= refaire l'aval au front).
4. **Où se compose le miroir** : modèle (reformulation) vs Python (slots). Recommandé : modèle pour la
   reformulation, Python pour le ranking/sélection des questions.

## Risques / limitations à surveiller

- **GBNF × thinking** (grammaire vs bloc de pensée) → modèle non-thinking.
- **Budget de contexte ~4096** : ancre + historique + grammaire → schéma compact, compaction par tour.
- **Variance mal mesurée** : varier la formulation, pas le seed (temp 0 = stabilité factice).
- **Gap banc↔produit** : valider le retenu sur le runtime embarqué.
- **Latence cumulée** (30–90 s sur 3 tours) → sortie courte, KV-cache, pré-remplissage.
- **Amorçage du vocabulaire** (œuf/poule) → seed + échappatoire `AUTRE`.
