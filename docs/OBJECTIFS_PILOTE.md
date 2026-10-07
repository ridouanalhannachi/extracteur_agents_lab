# Agent Pilote — objectifs EDT/RH

## Cadre et état examiné — 2026-10-07

Dépôt exclusif : `ridouanalhannachi/extracteur_agents_lab`.
Base : `58ac343` (`main`, fusion de la PR nº 5). Le responsable a vérifié le
distant : PR nº 1 à 5 fusionnées, aucune PR ouverte au début du cycle. D1 est
donc intégré ; ses 39 tests consignés au journal sont des preuves historiques,
pas une exécution nouvelle. Les travaux des anciennes copies locales sont
préservés ; aucun de ces fichiers n'est repris ni écrasé ici.

La priorité explicite du 6 octobre est le design et l'ergonomie. Elle remplace
L3 pour le choix du lot après préservation des travaux inachevés. Pas de migration,
de dépendance nouvelle, de déploiement ou de modification du dépôt d'origine.
Drive reste désactivé. Les fusions par PR du laboratoire sont autorisées par
l'utilisateur après tests de la version exacte, revue indépendante, contrôle du
SHA distant et des protections ; cette autorisation prévaut sur les anciennes
mentions demandant un nouvel accord pour chaque fusion. Aucun push direct sur main.

## Objectifs actifs (maximum cinq)

| Priorité / objectif | Problème observé ou hypothèse | Bénéfice utilisateur | Coût / risque | Dépendances | Critère mesurable | État |
|---|---|---|---|---|---|---|
| 1 — D2a : catalogue de l'historique | Observé dans `edt_history_ui.py` : quatre filtres sont alignés sur une seule rangée, le titre du tableau reste « Tous les emplois » après filtrage, et aucun décompte visible ni action de réinitialisation n'aide à comprendre le résultat. | Retrouver un emploi mémorisé plus vite et savoir immédiatement si un filtre est actif. | Faible / faible à modéré : préserver exactement la sélection des emplois, versions et données affichées. | D1 intégré ; composants Streamlit natifs ; données fictives. | Sur une fixture d'au moins deux emplois : état initial `2/2`, un filtre donne le même sous-ensemble métier attendu (`1/2`), la réinitialisation revient à `2/2`, et le cas sans résultat reste explicite ; suite complète réussie. Le rendu étroit/clavier n'est déclaré validé qu'avec un navigateur réel. | Vérifié localement : 43 tests réussis, dont parcours AppTest ; revue indépendante indisponible |
| 2 — D1 : accueil et navigation | L'absence d'accueil et la perte visuelle des options d'import ont été corrigées dans la PR nº 5. | Comprendre l'application et trouver immédiatement les fonctions existantes. | Faible / résiduel : inspection navigateur non faite. | Intégré à `main` au commit `58ac343`. | 39 tests, dont deux AppTest ; six accès réels, retour accueil, OCR conservé et Drive désactivé. | Intégré et vérifié ; rendu visuel/mobile non vérifié |
| 3 — D3 : parcours import, correction et validation | Observé : import dans la barre latérale puis quatre onglets et actions dispersées ; difficulté réelle à confirmer par un parcours complet. | Savoir quoi importer, vérifier et enregistrer avant export. | Moyen / modéré : widgets d'édition et persistance. | D1 ; tests de conservation L1. | Un document fictif parcourt import → correction → validation → export ; correction conservée après réouverture ; libellés des étapes et erreurs explicites. | Proposé |
| 4 — D4 : états vides et sauvegardes explicites | Hypothèse : cohérence des messages entre écrans à vérifier ; L2a interdit déjà les remplacements distants. | Distinguer absence de données, erreur et enregistrement local confirmé. | Moyen / modéré : ne pas annoncer une réussite non établie. | D1 ; garde L2a ; Drive désactivé. | Parcours vide, correction non enregistrée, succès local et échec simulé documentés ; aucun faux succès distant ; mémoire intacte. | Proposé |
| 5 — L3 : restauration conservatrice | Hypothèse conservée : une base distante valide mais ancienne peut menacer les corrections locales ; aucun nouveau défaut reproduit dans ce cycle. | Restaurer sans perdre les dernières corrections. | Moyen / élevé : remplacement de base. | Diagnostic séparé ; SQLite temporaire et Drive simulé uniquement. | Simulations d'interruption, corruption et ancienneté ; comparer séances, versions, validations et intégrité locale. | Proposé, différé après priorités design |

L'adaptation aux petits écrans, le contraste, les libellés et le focus sont des
critères transversaux des lots design ; ne pas annoncer leur validation sans preuve.
Les imports enseignants étendus et analyses de descriptifs restent des propositions
futures séparées, pas des fonctionnalités livrées par ce cycle.

## Lot retenu et fichiers attribués

Un seul lot : **D2a — catalogue de l'historique**, branche
`lab/design-table-filters`. Le périmètre est volontairement limité au premier
tableau de `render_edt_history()` et à ses quatre filtres. Les tableaux de
statistiques, RH, séances, versions et changements restent hors lot.

Diagnostic confirmé par lecture : les quatre filtres sont présentés sur une seule
ligne ; le tableau filtré conserve le titre « Tous les emplois mémorisés » ; aucun
décompte résultat/total ni commande de réinitialisation n'est présent. Une gêne
réelle sur petit écran reste une hypothèse tant qu'un navigateur n'a pas permis de
la constater.

- Développeur : `edt_history_ui.py` et un test UI ciblé attribué par le
  responsable ; améliorer la hiérarchie des filtres et du catalogue sans changer
  requêtes SQL, règles de filtrage, choix d'emploi, versions ni exports.
- Pilote : uniquement `docs/OBJECTIFS_PILOTE.md` et `docs/BACKLOG_LAB.md`.
- Vérificateur indépendant : lecture du diff exact et exécution des contrôles ;
  ne modifie pas les fichiers du développeur.
- Éclaireur : diagnostic d'un besoin technique concret ; aucune nouvelle
  dépendance n'est a priori nécessaire pour les composants Streamlit natifs.
- Responsable : journal, relais, intégration des preuves, publication et fusion
  conditionnelle par PR ; aucune modification directe de main ni déploiement.

## Reprise

D2a a été vérifié localement sur données fictives. La délégation de développement
a rencontré une limite d'usage ; le responsable a repris le code puis effectué une
revue successive non indépendante. Une validation AppTest ne vaut pas une comparaison
visuelle navigateur. Publier via PR seulement après nouvelle vérification distante.
