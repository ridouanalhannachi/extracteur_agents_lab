# Consignes du laboratoire EDT/RH

## Périmètre

Ce projet est une copie de développement séparée. Sa référence initiale est le commit
`e44dd858c5e3f0405d0f401bdf7e1d9c48f5ed56` de la proposition nº 1 du projet
`ridouanalhannachi/extracteur-edt-rh` : correctif v7.9.1 préparé, non fusionné au moment
de la copie. Ne pas présenter cette copie comme la version déployée.

Le dépôt autorisé est `ridouanalhannachi/extracteur_agents_lab`, public avec accord
explicite de l’utilisateur du 4 octobre 2026. Vérifier cette destination avant toute
écriture. Ne publier aucune donnée réelle ni aucun secret.

- Modifier exclusivement le laboratoire et ses branches dédiées.
- Ne jamais pousser, commenter ou ouvrir une proposition dans le dépôt d'origine
  au titre d'un cycle du laboratoire.
- Ne pas utiliser de base réelle, de sauvegarde Drive de production, de secrets
  de production ou de données personnelles. Utiliser des données fictives et SQLite
  temporaire. Ne pas copier des secrets depuis le projet d'origine.
- Ne pas ajouter d'API payante ni d'appel IA externe sans autorisation.
- Une fusion ou un déploiement nécessite l'accord explicite de l'utilisateur.

## Déroulement d'un cycle

1. Lire ces consignes, `docs/BACKLOG_LAB.md`, l'état Git et les propositions ouvertes
   du laboratoire. Vérifier la destination des remotes avant une écriture.
2. Reprendre en priorité une proposition inachevée pertinente. Ne pas dupliquer un lot
   déjà ouvert, ni recommencer les correctifs hérités sans défaut reproduit.
3. Choisir un seul lot de portée maîtrisée. Consigner sa cause, son critère de réussite
   et la branche dédiée. Ne pas écraser des modifications inconnues.
4. Développer, vérifier, puis préparer ou mettre à jour une proposition en brouillon.
   Si GitHub est inaccessible, conserver le travail local et déclarer le blocage.
5. Consigner le résultat dans `docs/JOURNAL_LAB.md` avec la date, la branche, le commit
   examiné, les fichiers modifiés, les commandes exécutées, leurs résultats exacts,
   les limites et l'étape suivante. Mettre à jour le backlog sans inventer de succès.
6. Terminer le cycle après ce lot. Si un autre cycle travaille déjà sur le même lot,
   ne pas démarrer de modifications concurrentes. En cas de doute, rester en lecture.
   Si aucun lot autorisé n'est disponible, signaler cet état et s'arrêter.

## Agents et passages de relais

Le responsable conserve la vue d'ensemble et coordonne les modifications.
Utiliser des sous-agents pour des tâches indépendantes qui le justifient, avec des
fichiers attribués et un résultat attendu. Leur disponibilité n'est pas garantie :
sinon appliquer les rôles successivement et le dire.

| Rôle | Mission et entrées | Livrable et critère de réussite | Outils et limites |
|---|---|---|---|
| Pilote | Lire les résultats, PR et besoins ; classer les objectifs par bénéfice, coût et risque | Au plus cinq objectifs actifs dans docs/OBJECTIFS_PILOTE.md, un lot sélectionné avec critère mesurable et missions distribuées | Lecture, planification et coordination du laboratoire ; pas de fusion, déploiement ou extension des accès |
| Architecte | Examiner le code courant et reproduire le défaut choisi | Diagnostic, périmètre et critères observables transmis au développeur | Lecture du laboratoire, tests fictifs ; aucune modification de données réelles |
| Développeur | Appliquer le diagnostic sur une branche dédiée | Diff minimal et commandes de test transmis au vérificateur | Python, SQLite temporaire, Git du laboratoire ; aucune fusion ni mise en production |
| Vérificateur | Relire le diff et vérifier les comportements attendus | Résultats reproductibles, régressions et limites explicites | Tests locaux, services simulés ; ne pas annoncer une validation réelle de Drive |

Le vérificateur transmet chaque défaut avec sa reproduction. Le développeur corrige
avant une nouvelle vérification ciblée. Un blocage d'accès, une ambiguïté destructive
ou un besoin de données réelles est remonté à l'utilisateur, jamais contourné.

## Exigences de fiabilité

- Préserver séances, versions, corrections et vérifications ; migrations répétables.
- Ne pas remplacer une base par une autre sans comparer leurs contenus et prévoir
  une restauration. Une base valide n'est pas nécessairement la plus récente.
- Distinguer écriture locale confirmée, échec de synchronisation et confirmation distante.
- Signaler une correction non enregistrée ; ne pas afficher de faux succès Drive.
- Conserver provenance et incertitudes sans inventer de champs manquants.
- Tester les défauts réellement corrigés et la conservation des données. Une syntaxe
  valide ne suffit pas à prouver le fonctionnement de l'application.
- Les tests simulés ne prouvent ni l'accès OAuth ni la sauvegarde réelle sur Drive.

## Pilotage des améliorations

À chaque cycle, confier le pilotage à un sous-agent si disponible. Il réévalue les
objectifs sur preuves, reprend les PR existantes et attribue des fichiers distincts.
Il peut proposer et faire réaliser des améliorations simples et réversibles du
périmètre EDT/RH autorisé. Maximum cinq objectifs actifs et un lot développé par cycle.
Les évolutions majeures, coûts, données réelles, fusions et déploiements restent soumis
à accord explicite. Voir docs/OBJECTIFS_PILOTE.md. Les agents ne restent pas actifs
entre les cycles et ne créent pas d’autre tâche planifiée.
