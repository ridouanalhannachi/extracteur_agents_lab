# Agent Pilote — objectifs EDT/RH

## Cadre et état examiné — 2026-10-06

Dépôt exclusif : `ridouanalhannachi/extracteur_agents_lab`.
Base : `38bc8f839c8af5fbd59c401348aac7ea87bab676`. Le responsable a vérifié
le distant : PR nº 1 à 4 fusionnées, aucune PR ouverte au début du cycle.
Les anciens lots L0/L1/L2a sont intégrés ; les 37 tests consignés au journal sont
les preuves historiques, pas une exécution nouvelle. Les travaux des anciennes
copies locales sont préservés ; aucun de ces fichiers n'est repris ni écrasé ici.

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
| 1 — D1 : accueil et navigation | Observé dans `app.py` : aucune page d'accueil dédiée ; premier écran centré extraction/Excel, alors que sept modules existent ; navigation et options d'import partagent la barre latérale. | Comprendre l'application et trouver immédiatement les fonctions existantes. | Faible à moyen / modéré : routage et état des widgets Streamlit à préserver. | Base intégrée ; composants Streamlit existants ; aucune dépendance ajoutée. | Accueil identifiable ; accès natifs menant aux modules existants ; libellés cohérents ; Drive explicitement désactivé ; aucun compteur fictif ; suite applicative et contrôles des routes réussis. Comparaison visuelle seulement si lancement possible. | Vérifié par AppTest et suite applicative ; rendu visuel non vérifié |
| 2 — D2 : lisibilité des tableaux et filtres | Hypothèse à vérifier : densité et intitulés techniques compliquent lecture et sélection ; plusieurs écrans utilisent des tableaux distincts. | Comparer les séances et trouver les informations utiles plus vite. | Moyen / modéré : éviter de modifier données, tris métier ou exports. | Diagnostic des écrans après D1. | Sur données fictives, filtres identifiables, colonnes essentielles lisibles, mêmes lignes et totaux avant/après ; contrôle clavier et écran étroit. | Proposé |
| 3 — D3 : parcours import, correction et validation | Observé : import dans la barre latérale puis quatre onglets et actions dispersées ; difficulté réelle à confirmer par un parcours complet. | Savoir quoi importer, vérifier et enregistrer avant export. | Moyen / modéré : widgets d'édition et persistance. | D1 ; tests de conservation L1. | Un document fictif parcourt import → correction → validation → export ; correction conservée après réouverture ; libellés des étapes et erreurs explicites. | Proposé |
| 4 — D4 : états vides et sauvegardes explicites | Hypothèse : cohérence des messages entre écrans à vérifier ; L2a interdit déjà les remplacements distants. | Distinguer absence de données, erreur et enregistrement local confirmé. | Moyen / modéré : ne pas annoncer une réussite non établie. | D1 ; garde L2a ; Drive désactivé. | Parcours vide, correction non enregistrée, succès local et échec simulé documentés ; aucun faux succès distant ; mémoire intacte. | Proposé |
| 5 — L3 : restauration conservatrice | Hypothèse conservée : une base distante valide mais ancienne peut menacer les corrections locales ; aucun nouveau défaut reproduit dans ce cycle. | Restaurer sans perdre les dernières corrections. | Moyen / élevé : remplacement de base. | Diagnostic séparé ; SQLite temporaire et Drive simulé uniquement. | Simulations d'interruption, corruption et ancienneté ; comparer séances, versions, validations et intégrité locale. | Proposé, différé après priorités design |

L'adaptation aux petits écrans, le contraste, les libellés et le focus sont des
critères transversaux des lots design ; ne pas annoncer leur validation sans preuve.
Les imports enseignants étendus et analyses de descriptifs restent des propositions
futures séparées, pas des fonctionnalités livrées par ce cycle.

## Lot retenu et fichiers attribués

Un seul lot : **D1**, branche `lab/design-home-navigation`.
Diagnostic confirmé par lecture : l'application entre directement sur le module
EDT, le titre décrit surtout l'export Excel et aucune entrée Accueil n'existe.
La difficulté d'usage est une hypothèse UX, pas le résultat d'une étude utilisateur.

- Développeur : interface d'accueil/navigation et ses contrôles ciblés, fichiers
  attribués par le responsable ; préserver extraction, corrections et exports.
- Pilote : uniquement `docs/OBJECTIFS_PILOTE.md` et `docs/BACKLOG_LAB.md`.
- Vérificateur indépendant : lecture du diff exact et exécution des contrôles ;
  ne modifie pas les fichiers du développeur.
- Éclaireur : diagnostic d'un besoin technique concret ; aucune nouvelle
  dépendance justifiée par le diagnostic d'accueil/navigation.
- Responsable : journal, relais, intégration des preuves, publication et fusion
  conditionnelle par PR ; aucune modification directe de main ni déploiement.

## Reprise

Après preuve du développeur et du vérificateur, actualiser l'état D1 et inscrire
les commandes, résultats et limites dans le journal et le relais. Une validation
AppTest seule ne vaut pas une comparaison visuelle navigateur. Ne sélectionner
D2 ou D3 qu'au cycle suivant, après vérification des branches et PR courantes.
