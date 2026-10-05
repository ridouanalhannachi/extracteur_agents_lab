# Reprises automatiques du laboratoire

Le laboratoire vise des cycles de développement bornés et traçables. Ce document
ne crée aucune tâche et ne garantit pas des agents actifs en permanence. Une tâche
planifiée, si elle est disponible et activée, relance un travail ; elle ne fournit pas
une exécution continue sans interruption.

## Prérequis avant activation

1. Vérifier le dépôt distinct autorisé (public avec accord utilisateur) `ridouanalhannachi/extracteur_agents_lab`.
2. Y placer la copie complète du code et les consignes, sans base réelle ni secrets.
3. Confirmer par une lecture réussie que l'outil de la tâche peut accéder à ce dépôt.
4. Vérifier que le mode laboratoire reste séparé de la base et du Drive de production.
5. Choisir une cadence compatible avec le service de planification et vérifier la
   confirmation de création de la tâche. Ne pas annoncer son activation auparavant.

La référence initiale est le commit `e44dd858c5e3f0405d0f401bdf7e1d9c48f5ed56`
du correctif v7.9.1 proposé dans le projet d'origine. Ce n'est pas une preuve de fusion
ou de déploiement. Les développements ultérieurs du projet d'origine ne doivent pas
être importés automatiquement sans examen.

## Consigne prête à réutiliser dans une tâche

```text
Effectue un seul cycle borné de développement dans le dépôt privé
ridouanalhannachi/extracteur_agents_lab. Vérifie d'abord son accès et sa destination.
N'effectue aucune écriture dans ridouanalhannachi/extracteur-edt-rh.

Lis AGENTS.md, docs/BACKLOG_LAB.md, le journal disponible, l'état du code et les
propositions ouvertes. Reprends d'abord le lot inachevé pertinent. Si un autre cycle
travaille sur le même lot, ne lance pas de modifications concurrentes. Si les accès
nécessaires manquent ou si aucun lot autorisé n'est disponible, explique et termine.

Choisis au maximum un lot prioritaire de fiabilité de la mémoire EDT, de sauvegarde
des corrections ou de récupération après redémarrage. Vérifie le défaut avant de
modifier le code ; ne recommence pas un correctif déjà présent sans reproduction.

Coordonne les rôles architecte, développeur et vérificateur. Utilise des sous-agents
pour les tâches indépendantes utiles si l'environnement les permet ; sinon applique
les rôles successivement et indique cette limite. Attribue clairement les fichiers.

Travaille sur une branche dédiée du laboratoire. Utilise seulement des données
fictives, des bases SQLite temporaires et des services simulés. N'utilise aucune base,
aucune sauvegarde Drive ni aucun secret de production. N'ajoute pas d'API payante.
Préserve les fonctionnalités, versions, corrections et vérifications existantes.

Exécute les tests ciblés nécessaires, corrige les régressions détectées, puis prépare
ou actualise une proposition en brouillon dans le laboratoire. Ne fusionne pas et
ne déploie pas sans accord explicite de l'utilisateur. En cas de blocage, conserve le
travail et indique précisément ce qui reste nécessaire.

Consigne le résultat dans docs/JOURNAL_LAB.md et actualise le backlog : référence,
branche, cause vérifiée, modifications, commandes réellement exécutées et résultats,
limites, proposition éventuelle et prochaine étape. Distingue les tests simulés d'une
validation réelle de Drive. Donne un bilan bref en français puis termine ce cycle.
```

## Contrôle et arrêt

Les propositions en brouillon et le journal permettent de suivre les résultats.
Un lot nécessitant une décision humaine reste bloqué avec une question précise.
Suspendre la tâche via le service de planification pour interrompre les reprises.
La cadence et les notifications dépendent de la tâche effectivement créée.
