# Knobs (2) & (3) résolus — ancré sur le vrai `FAE.xlsx`/`dico.xlsx` — 2026-06-25

> Verrouille deux des trois questions ouvertes du `/resume`. Décidé depuis l'évidence réelle, pas au
> feeling (principe GIGO : on juge par le réel). Le knob (1) — granite écoute vs docile — reste ouvert :
> il est empirique, verdict à M3 sur machine libre. Alimente : brique 3 (normalisateur) et brique 5
> (lecteur fichier). Ne change PAS la brique 1 (model-free, découplée).

## Ce que le fichier réel contient (décodé, formules lues — pas les valeurs)

Réconciliation **2 systèmes** : `SYNTHESE` (= extract **Système-A**, 12693 lignes) ↔ `PX_CLIENT par Inter`
(= extract **Système-B**, 50000 lignes). Confirmé par les labels du `BILAN-DICO`.

- **Clé de jointure = `ID Inter`** ; **clé de secours = `Réf partenaire`** — exactement comme prédit, et
  le fallback est **enfoui** : `PX_CLIENT!E = IF(ISNA(VLOOKUP(A,SYNTHESE!D:D,1,0)), IF(ISNA(VLOOKUP(A,SYNTHESE!E:E,1,0)),0,1),1)`
  et `SYNTHESE!Q = IF(ISNA(VLOOKUP(D,…!A:A,1,0)),0,1) + IF(ISNA(VLOOKUP(E,…!A:A,1,0)),0,1)` — le secours
  vit dans un `IF` imbriqué et dans un `+`. Personne ne l'a documenté.
- **Coefficients magiques** : `BILAN-DICO!"Autres" = (0.9*0.93-1)*(B9+B12)`. Deux taux nus. Le `BILAN`
  liste « RFA non affectable » et « Pénalité » comme catégories → 0,93 ressemble à un RFA, 0,9 à une
  remise, mais **aucun humain ne le confirme sans qu'on le demande**. C'est LE risque-si-faux élevé.
- **Dico métier annexe** : `dico.xlsx` (Résultat → Cause non facturable → Faute, 11 mappings) **ET**
  recopié dans `VARIABLES`. Logique métier dupliquée, invisible aux outils.
- **Jugement humain** : `Statut Facturation` / `Cause` / `Faute` = listes déroulantes remplies main.
- **Sortie** = le `BILAN` : comptes de réconciliation + totaux prix + ventilation des ajustements → TOTAL.

## Knob (2) — seed du vocabulaire fermé : VERROUILLÉ

**Décision : seeder UN type réel + l'échappatoire. Pas d'invention.**

```
request_type ∈ { croisement_fichiers , AUTRE }
```

- **`croisement_fichiers`** (PAS `croisement_excel`). On dé-Excel-ise le nom : le cadrage dit que le
  mécanisme est général et qu'Excel doit « discrètement disparaître ». Mettre « excel » dans le
  vocabulaire canonique sur-spécialise exactement ce qu'on veut éviter.
- **`AUTRE`** : non négociable (bootstrap œuf/poule — sans échappatoire, tout besoin neuf est rejeté).

**Slots de `croisement_fichiers` = la checklist de l'oracle 1 (complétude), 1:1 :**

| slot | source FAE | dans l'artefact comme |
|---|---|---|
| `fichiers_sources[]` (+ `role`) | SYNTHESE=Système-A, PX_CLIENT=Système-B | confirmé ou question |
| `cle_jointure` | `ID Inter` | hypothèse pré-remplie → swipe |
| `cle_secours` | `Réf partenaire` | hypothèse pré-remplie → swipe |
| `dictionnaires_annexes[]` (+ `source`) | dico.xlsx + copie VARIABLES | confirmé ou question |
| `coefficients_a_expliciter[]` | 0,9 et 0,93 | **toujours en question** |
| `sortie_attendue` | le BILAN | confirmé ou question |

**Honnêteté / skepticisme** : ce seed repose sur **un seul** cas réel. `relance_email` (2e exemple des
docs) est **non ancré** — aucun artefact derrière. Ne PAS le seeder « pour faire nombre ». Deux options
défendables pour M2 :
- **(recommandé)** 1 type réel + `AUTRE`. M2 teste la complétude sur FAE.
- Ajouter un 2e type **uniquement** pour tester que le normalisateur *discrimine* (un besoin non-croisement
  tombe-t-il en `AUTRE` et pas en `croisement_fichiers` ?). Si on le fait, le marquer « ancré=non ».

## Knob (3) — profondeur détection Excel : VERROUILLÉ à 2 patterns + règle de bornage

Les 2 patterns **suffisent** et **apparaissent tous deux** dans FAE. Mais le réel a livré un piège concret
à coder correctement (sinon faux positifs massifs) :

- **Pattern A — rapprochement croisé.** Détecter `VLOOKUP/MATCH/INDEX/HLOOKUP` référençant **une autre
  feuille** ; extraire la/les colonne(s) clé. Gérer le secours imbriqué (`IF(ISNA(VLOOKUP…))` chaîné, et
  somme de présences via `+`). → génère « tu rapproches sur quelle clé ? ID Inter, secours Réf partenaire ? ».

- **Pattern B — coefficient nu.** ⚠️ **Leçon mesurée** : un détecteur naïf « trouve les décimaux »
  produit du **bruit massif**. Sur FAE, regex décimal a remonté `1,0`/`0,1` **1740 fois** (ce sont les
  arguments `,1,0` de VLOOKUP : col_index=1, exact_match=0) et noyé les 2 vrais coefficients (`0.9`,
  `0.93`, **1 occurrence chacun**). C'est exactement la fragilité d'AST que les docs annonçaient.
  **Règle de bornage robuste et cheap** : ne flagger que les littéraux **à partie fractionnaire**
  (décimale-point en syntaxe formule normalisée en-US : `0.9`, `0.93`) **en contexte arithmétique**
  (`* / + -`), **en excluant** les positions d'arguments entiers des fonctions de lookup. Les flags
  entiers `1`/`0` disparaissent par la seule condition « a une partie fractionnaire ». → génère « que
  représentent 0,9 et 0,93 ? remise ? RFA ? ».

**Bornage explicite — ce que le lecteur NE fait PAS** (sinon il refait l'aval au front) :
- ne PAS évaluer tout le graphe de formules du BILAN (COUNTIF/COUNTA/SUM = agrégations, hors cible) ;
- ne PAS *résoudre* ce que valent 0,9/0,93 — les **surfacer en question**, pas les interpréter ;
- ne PAS chasser au-delà des 2 patterns. « Projeter l'ombre de l'aval », pas coder à sa place.

## Ce qui ne bouge pas

- Brique 1 (ModelClient + FakeModelClient + trace + Tier A) reste **inchangée et prioritaire** : ces
  décisions alimentent les briques 3 et 5, pas la 1.
- Knob (1) reste **ouvert** : seul M3 (PUSH, granite réel) le tranche.
