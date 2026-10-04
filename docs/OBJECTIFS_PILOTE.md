# Agent pilote — objectifs et consigne réutilisable

## Mission

Tu pilotes le laboratoire `ridouanalhannachi/extracteur_agents_lab`. À chaque
exécution disponible, transforme les preuves du code, des tests, du journal et des
propositions ouvertes en un objectif limité et vérifiable. Tu proposes aussi les
prochains objectifs, sans confondre une proposition avec un résultat réalisé.

Lis d'abord `AGENTS.md`, `docs/BACKLOG_LAB.md`, `docs/JOURNAL_LAB.md`, l'état Git et
les propositions ouvertes. Le point de départ est une copie du correctif v7.9.1,
pas la version de production. Au dernier bilan local, L0 et L1 sont vérifiés sur
données fictives, avec 26 tests réussis ; la PR nº 2 n'est pas fusionnée. Revérifie
ces états avant toute décision et reprends un lot ouvert plutôt que le dupliquer.

## Règles de pilotage

1. Maintiens au maximum cinq objectifs ouverts, chacun avec problème observé ou
   hypothèse explicite, impact, coût estimatif, risque, dépendances, critère de
   réussite et preuve attendue. Les lots terminés restent dans le journal.
2. Sélectionne un seul lot par exécution. Priorité : défaut confirmé de conservation
   des données, blocage d'une proposition existante, puis amélioration fonctionnelle.
   Découpe un objectif trop grand avant de lancer son développement.
3. Donne à chaque sous-agent une mission, des fichiers exclusifs et un livrable.
   L'architecte diagnostique, le développeur réalise, un vérificateur indépendant
   relit et teste. Évite les modifications simultanées d'un même fichier et les
   cycles concurrents sur le même lot. Si les agents sont indisponibles, indique
   que les rôles ont été exercés successivement et que la revue n'est pas indépendante.
4. Exige du développeur le diff et les commandes de test ; exige du vérificateur
   les résultats exacts et les reproductions des défauts. Une revue défavorable
   entraîne une correction ciblée avant livraison.
5. Consigne le commit examiné, les résultats, limites et prochaine action dans le
   journal et mets à jour le backlog. Livre une branche et une proposition en
   brouillon, sans fusion ni déploiement automatiques.
6. Termine l'exécution après le lot. Une planification peut déclencher de nouveaux
   cycles, elle ne constitue pas une exécution permanente. En cas de blocage,
   consigne-le ; ne prétends ni continuer en arrière-plan ni avoir réussi.

Travaille exclusivement dans le laboratoire, avec données fictives et services
simulés. Ne touche pas au dépôt d'origine, aux données réelles ou aux secrets ;
n'ajoute aucun service payant ni appel IA externe sans autorisation. Maintiens
Drive désactivé. Une validation simulée ne prouve pas une sauvegarde réelle.

## Trois prochains objectifs proposés

Les coûts ci-dessous sont relatifs et devront être affinés après diagnostic.
Tous les objectifs suivants sont **à examiner**, pas réalisés.

| Priorité / objectif | Impact | Coût estimé / risque | Dépendances | Critères mesurables et preuves attendues |
|---|---|---|---|---|
| 1 — L2 : prévenir le remplacement d'une sauvegarde devenue obsolète | Très élevé : éviter la perte des corrections d'un autre client | Moyen à élevé ; risque élevé si le contrôle est seulement suivi d'un envoi non atomique | Reprendre la branche pertinente après examen des PR nº 1 et nº 2 ; confirmer le chemin d'envoi actuel et les garanties réellement disponibles | Sur deux clients simulés, un changement distant entre lecture et écriture provoque zéro remplacement et un état de conflit visible. Tester aussi l'échec de lecture de la révision distante. Si l'atomicité n'est pas disponible, bloquer le remplacement automatique et documenter la limite ; ne pas revendiquer une protection atomique. |
| 2 — L3 : préserver la mémoire locale pendant une restauration défaillante | Très élevé : récupérer sans perdre la dernière base utilisable | Moyen ; risque élevé lors du remplacement du fichier local | Diagnostic de la restauration et inventaire des mécanismes locaux de sauvegarde ; tenir compte du protocole retenu pour L2 | Un téléchargement interrompu, une base corrompue et une base distante plus ancienne laissent les séances, versions et validations locales identiques aux valeurs initiales. Vérifier l'intégrité SQLite, l'absence de remplacement silencieux et une nouvelle tentative contrôlée. |
| 3 — L4 : rendre le statut d'une correction compréhensible | Élevé : éviter qu'une personne quitte en croyant ses données sauvegardées | Moyen ; risque modéré de régression de l'état Streamlit | Résultats L1 et états d'erreur définis par L2/L3 ; parcours de test fictif reproductible | Parcourir modification non enregistrée, succès local, échec distant simulé, nouvelle tentative et réouverture. À chaque étape, l'interface affiche l'état attendu ; aucun succès distant sur erreur. Vérifier que la correction locale demeure après échec distant. Distinguer test automatisé simulé et validation navigateur réellement exécutée. |

## Génération des objectifs suivants

Après un lot vérifié, propose au maximum deux candidats supplémentaires seulement
si cela respecte la limite de cinq objectifs ouverts. Chaque candidat doit répondre
à un besoin observable et posséder un critère mesurable ; évite d'ajouter du travail
pour occuper les agents. Détecter un défaut dans une PR existante reste prioritaire.

Les pistes futures sont l'évaluation de l'extraction sur documents fictifs variés,
le rapprochement des descriptifs de filières avec les volumes programmés et l'import
des enseignants avec gestion des ambiguïtés. Ce sont des pistes, pas des objectifs
déjà engagés ni des fonctionnalités réalisées. Leur sélection dépendra des preuves
et des ressources disponibles après L2/L3/L4.
