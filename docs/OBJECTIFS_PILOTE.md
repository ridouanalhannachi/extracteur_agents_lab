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

## Objectifs actifs — cycle du 2026-10-05

Référence examinée : `75534fc639aeaf5725d52b26e38d3b5a711114ce` (PR nº 3).
Le responsable a revérifié les PR ouvertes nº 1, nº 2 et nº 3 ; aucun L2 distant.
L1 est déjà livré dans la PR nº 2 : il ne sera pas redéveloppé.
Les coûts sont relatifs ; une hypothèse ci-dessous ne constitue pas un défaut prouvé.

| Priorité / objectif | Problème observé ou hypothèse | Bénéfice utilisateur | Coût / risque | Dépendances | Critère mesurable et état |
|---|---|---|---|---|---|
| 1 — L2a : interdire le remplacement distant sans garantie atomique | Observé dans le code : `auto_upload_after_change` appelait `upload_database(False)` ; l'envoi remplaçait le fichier existant sans précondition. Le contrôle MD5 de `sync_database` ne rendait pas cet envoi atomique. | Préserver les corrections d'un autre client et annoncer clairement le refus de synchronisation. | Moyen / réduction volontaire des envois : même un fichier inchangé reste protégé tant qu'une écriture conditionnelle fiable n'est pas établie. | Base des PR nº 1–3 ; Drive désactivé ; service simulé et SQLite temporaire. | **Vérifié sur simulation.** 11 tests ciblés et 37 tests au total réussis ; zéro remplacement, marqueurs intacts, erreur de lecture sans écriture et aucun faux succès. Créations initiales simultanées et adaptation de l'UI avant activation réelle restent hors lot. |
| 2 — L3 : préserver la mémoire locale pendant une restauration défaillante | Hypothèse à vérifier : les interruptions, bases invalides ou anciennes peuvent menacer la copie locale ; le code valide déjà SQLite avant remplacement, mais ne compare pas l'ancienneté métier. | Récupérer sans perdre les dernières corrections utilisables. | Moyen / élevé lors du remplacement local. | Garde L2a ; diagnostic de `download_database` et sauvegardes locales. | **Proposé.** Simuler interruption, corruption et base distante ancienne ; comparer séances, versions et validations locales, intégrité SQLite et nouvelle tentative. Découper le lot après diagnostic. |
| 3 — L4 : rendre le statut d'une correction compréhensible | Hypothèse à vérifier : un parcours complet peut confondre enregistrement local et réussite distante ; les tests existants couvrent déjà plusieurs erreurs simulées. | Savoir si une correction est enregistrée et où elle se trouve. | Moyen / modéré, état Streamlit. | Résultats L1, L2a et restauration L3. | **Proposé.** Parcourir non enregistré, succès local, échec distant, nouvelle tentative et réouverture ; aucun faux succès distant, correction locale conservée. Distinguer simulations et validation navigateur. |

## Lot retenu et attribution

Un seul lot : **L2a**, branche `lab/concurrent-backup-guard`.
Sans garantie atomique établie, la stratégie est de refuser le remplacement d'un
fichier existant, y compris lorsqu'un simple contrôle le juge inchangé. Ce lot
n'implémente ni fusion de bases ni protocole multi-client complet. La création
simultanée de plusieurs fichiers de même nom et la reprise d'envois autorisés
restent des limites à examiner séparément ; le refus n'est pas un faux succès.

- Développeur : `gdrive_sync.py` et `tests/test_drive_concurrency.py` ; reproduire
  le risque sur service fictif, développer la garde et ses régressions.
- Vérificateur indépendant : lecture du diff et exécution de contrôles ; aucun
  fichier du développeur modifié simultanément.
- Pilote : uniquement `docs/OBJECTIFS_PILOTE.md` et `docs/BACKLOG_LAB.md` ; ajuster
  le statut après réception des preuves du développeur et du vérificateur.
- Responsable : journal, contrôles globaux et proposition en brouillon ; aucune
  fusion, modification de `main`, ni déploiement.

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
