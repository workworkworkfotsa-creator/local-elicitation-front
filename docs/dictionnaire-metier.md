# Dictionnaire métier — MiniChat (front d'élicitation)

Glossaire **curé à la main + confirmé** (jamais supposé). But : tuer les télescopages de vocabulaire
**avant** qu'ils ne se bétonnent dans les noms de packages/code.

> **Ancrage (état greenfield, 2026-06-25)** : pas encore de code → la *source de vérité* de chaque terme
> est un **doc de cadrage** (`CLAUDE.md` à la racine ; les docs de brainstorm sous `docs/brainstorms/`).
> Quand le code existera, ré-ancrer sur `fichier:ligne`. Convention : terme → définition terrain →
> source ancrée → liens `[[terme]]`.

## Le découpage fondateur : l'ARTEFACT ≠ les BLOCS

Le mot **« EB » / « Expression de Besoin » portait 3 sens** (entrée brute, sortie normalisée, bloc du
pipeline) — racine de toute la confusion. Résolu : **« expression de besoin » = l'ARTEFACT** (ce qui
circule) ; **jamais un nom de bloc**.

### L'artefact (ce qui circule — vit dans `contract`)

**besoin_brut** :
La demande informelle initiale du demandeur (« automatise ma FAE ») **+ les fichiers déposés**. Garbage
par nature, incomplète. C'est l'**entrée** de [[MiniChat]].
_Source_ : `CLAUDE.md` §Le flux (« besoin brut (FR) ») ; `decisions_et_risques.md` §Le cas FAE.
_Avoid_ : « la demande », « EB », « input » (trop générique).

**expression_de_besoin** (abrév. tolérée en prose : EB) :
La **spec normalisée** sur vocabulaire fermé — un [[type_de_besoin]] + des [[slot]]s + les hypothèses et
leurs **verdicts humains**. Complète, co-écrite, exécutable par l'aval **sans ré-interroger**. C'est la
**sortie** de [[MiniChat]] et **l'artefact qui traverse les frontières (= le contrat)**.
_Source_ : `CLAUDE.md` §La forme canonique stable.
_Avoid_ : « spec » seul, « besoin », et **surtout pas comme nom de bloc** (c'est l'artefact).

### Les blocs (ce qui transforme un état en un autre)

**MiniChat** (le front · bloc 1 · **= le périmètre de ce repo**, « focusUser ») :
Le bloc d'élicitation user-facing. Transforme [[besoin_brut]] → [[expression_de_besoin]] par
l'interrogation (reformuler → ancrer → questionner → valider → normaliser). **Demande, ne résout jamais.**
_Source_ : `CLAUDE.md` §Le produit en une phrase, §Le flux.
_Avoid_ : « chat » (le chat est la *façade*, pas le bloc), « EB ».

**consolidation** (bloc 2 · **hors scope → stub**) :
Le registre central qui collecte plusieurs [[expression_de_besoin]], les **dédoublonne**, priorise et
**achemine** vers la [[génération]]. Cross-demande / multi-demandeur. C'était le nœud « EB » ambigu du
diagramme initial — renommé par ce qu'il **fait**, pas par l'artefact qu'il manipule.
_Source_ : `CLAUDE.md` §Hors scope (« curation, déduplication, acheminement vers un étage central »).
_Avoid_ : « EB » (télescopage artefact/bloc), « curation » seul.

**génération** (bloc 3 · **hors scope → stub**) :
La fabrique aval : génère la solution depuis une [[expression_de_besoin]] curée, **valide**, **déploie**.
_Source_ : pipeline du demandeur (handoff) ; `CLAUDE.md` §Hors scope.
_Avoid_ : « le back », « l'IA » (la génération n'est qu'un consommateur du contrat).

## Le vocabulaire fermé (le cœur volatil — « curé à la main = temporaire »)

**type_de_besoin** :
La catégorie **énumérée et fermée** d'une [[expression_de_besoin]]. Le **curé-à-la-main est un
échafaudage TEMPORAIRE** jusqu'à trouver « la bonne sauce ». → vit **en data dans `contract`**, un seul
endroit à changer.
_Source_ : `knobs_2_3_resolus_2026-06-25.md` §Knob (2).
_Avoid_ : « catégorie », « intent ».

**slot** :
Un champ **énumérable** d'un [[type_de_besoin]]. Pour [[croisement_fichiers]] : `fichiers_sources`+rôles,
`cle_jointure`, `cle_secours`, `dictionnaires_annexes`+source, `coefficients_a_expliciter`,
`sortie_attendue`. **Les slots = la checklist de l'oracle de complétude.**
_Source_ : `knobs_2_3_resolus_2026-06-25.md` §Knob (2), tableau des slots.

**croisement_fichiers** :
Le **seul** [[type_de_besoin]] réellement **ancré** (sur le cas FAE réel). Nom **source-agnostique**
délibéré (PAS `croisement_excel` : Excel doit « discrètement disparaître »).
_Source_ : `knobs_2_3_resolus_2026-06-25.md` §Knob (2).

**AUTRE** :
L'**échappatoire non négociable** du vocabulaire de [[type_de_besoin]] : tout besoin neuf non reconnu y
tombe (anti œuf/poule — sans elle, tout besoin neuf est rejeté).
_Source_ : `CLAUDE.md` §La forme canonique stable ; `knobs_2_3_resolus_2026-06-25.md` §Knob (2).

## Concepts transverses

**risque-si-faux** :
Le critère qui décide si une donnée manquante devient une **question** (fort risque → on demande) ou un
**défaut silencieux** (faible risque, visible/corrigeable). Pilote la sélection des 2-3 cartes.
_Source_ : `CLAUDE.md` §Principes (1), §Engagement.
_Avoid_ : « priorité », « criticité ».

**ancre** :
Le **fait réel** (données lues du fichier, ou réponse humaine confirmée) qui donne au modèle une
**condition de terminaison** — l'empêche d'inventer puis de spiraler. **Gradient, pas portail** (ne pas
exiger un fichier pour démarrer).
_Source_ : `CLAUDE.md` §Principes (6), §L'ancre = la lecture de fichier.

**trace** :
Le journal **append-only** (aucun UPDATE/DELETE ; un fait su plus tard = ligne neuve) : dialogue brut,
[[expression_de_besoin]] + verdicts, fichiers déclarés + schéma, provenance. **Irréversible → câblée en
brique 1.**
_Source_ : `CLAUDE.md` §La trace.
_Avoid_ : « log », « historique » (sous-entendent mutable/jetable).
