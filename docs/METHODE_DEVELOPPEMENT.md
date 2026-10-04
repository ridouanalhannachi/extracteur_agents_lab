# Application du prompt de développement par agents

## Mission du premier lot

Fiabiliser la mémoire EDT de la v7.9 sans perdre les emplois ni leurs versions.
Livrable : un correctif isolé, des tests reproductibles et une proposition GitHub.
Réussite : migration conservatrice, sauvegarde manuelle fonctionnelle, échec Drive visible.

## Trois rôles et leurs passages de relais

Ces rôles structurent le travail de ce lot, réalisé successivement par l'assistant.
Ils peuvent être confiés ultérieurement à des agents distincts disposant des mêmes outils.

Lors de la relecture suivante, deux sous-agents ont été sollicités séparément pour
SQLite et la synchronisation. Leurs signalements sur les formats de durée et la reprise
du démarrage après une panne Drive ont été intégrés par l'assistant principal et testés.

| Rôle | Entrées | Sorties | Limites |
|---|---|---|---|
| Architecte | Code au commit de référence, problème reproduit | Périmètre, causes, critères de réussite | Distinguer fait vérifié et hypothèse de déploiement |
| Développeur | Périmètre validé, fichiers concernés | Correctif minimal sur branche dédiée | Préserver les données et l'interface existante |
| Vérificateur | Diff, base de test, critères | Résultats reproductibles et risques restants | Aucune donnée réelle, aucun appel Drive réel dans les tests |

Le vérificateur renvoie les échecs au développeur. Le développeur remet le correctif
au vérificateur jusqu'à satisfaction des critères. Une limite de production non vérifiable
est déclarée dans la proposition, pas remplacée par une affirmation de réussite.

## Consignes réutilisables

### Architecte

> Examine le dépôt et son commit courant avant toute proposition. Reproduis le problème.
> Définis le plus petit correctif utile, les fichiers concernés, les risques sur les données
> et les critères de validation. Identifie explicitement les informations manquantes.
> Transmets au développeur les faits vérifiés, le périmètre et les tests nécessaires.

### Développeur

> Applique le périmètre de l'architecte sur une branche dédiée. Préserve les fonctionnalités
> existantes et les données. Rends les échecs visibles à l'utilisateur. Écris les tests
> qui reproduisent les défauts réels. Transmets le diff et les commandes de validation.
> Ne fusionne pas et ne déclenche pas le déploiement de production.

### Vérificateur

> Relis le diff et exécute les scénarios de réussite et d'échec. Vérifie la conservation
> des données, la répétition d'une migration, les doublons et les erreurs réseau.
> Signale les défauts au développeur avec une reproduction. Distingue tests locaux,
> services simulés et validation réelle du déploiement. Prépare un bilan vérifiable.

## Outils et mémoire de travail

- GitHub : commit de référence, branche, diff, proposition et historique des décisions.
- Python, SQLite temporaire et unittest : exécution et vérification sans données réelles.
- Streamlit et Drive : validation d'intégration ultérieure sur une instance de test.
- `VERSION` et les notes de version : état de chaque livraison.

## Plan indicatif sur sept jours

| Jour | Résultat attendu |
|---|---|
| 1 | Audit du commit et reproduction des défauts |
| 2 | Correctif de persistance et migrations |
| 3 | Tests de régression et proposition GitHub |
| 4 | Validation sur copie de la base et comparaison des compteurs |
| 5 | Vérification Drive et redémarrage sur instance de test |
| 6 | Relecture utilisateur et décision de déploiement |
| 7 | Observation des erreurs et choix du lot suivant |

Ce calendrier est indicatif ; il ne programme aucune action automatique.
Les trois premières étapes constituent le premier lot préparé ici.

## Contrôle humain et suivi

La fusion et le déploiement restent une décision explicite de l'utilisateur. Le suivi
porte sur les erreurs de sauvegarde, les pertes de données, les doublons et le temps
nécessaire pour enregistrer/retrouver un emploi. Ne pas ajouter de nouveaux rôles tant
qu'un besoin de travail indépendant ne le justifie pas.
