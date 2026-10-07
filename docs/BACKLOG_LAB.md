# Backlog EDT/RH — 7 octobre 2026

Base vérifiée : `67df619`, PR 1 à 7 fusionnées, aucune ouverte au début du lot.
La priorité utilisateur est l'interactivité. Le socle L1/L2a et les lots design
D1/D2a/D3a sont intégrés ; leurs tests passés ne sont pas des tests de ce cycle.

## Lot en cours : D3b — État des séances enregistrées

Diagnostic : l'import automatique précède l'éditeur détaillé, tandis que la
confirmation manuelle disparaît à la réexécution. L'utilisateur ne sait pas si
ses corrections correspondent à une version locale.

Livrable : messages réactifs dans Correction, Export et Enregistrement pour
l'emploi et la cible explicitement sélectionnés. Distinguer non enregistré,
version locale active, ancienne version archivée, cible incomplète, aucune séance
et état non vérifiable. Télécharger Excel ne remplace pas l'enregistrement.

Critères : édition/ajout/suppression détectés ; sauvegarde puis réexécution et
réouverture conserve correction ; export contient correction ; erreur n'affiche
pas de faux succès ; contexte année/période/filière/semestre respecté ; aucune
écriture par la comparaison ; anciennes versions non réactivées implicitement.

État : vérifié : 6 tests ciblés, 55 tests complets, revue indépendante acceptée. Voir JOURNAL_LAB et
REPRISE_AGENTS pour les preuves finales. Comparaison visuelle, mobile et clavier
non validés en l'absence de navigateur local.

## Suite (maximum cinq objectifs actifs avec D3b)

1. I2 : diagnostiquer correction/annulation sans perte des saisies.
2. I3 : diagnostiquer actions contextuelles et maintien de sélection des versions.
3. D5 : vérifier petit écran, clavier, contraste dans un navigateur réel.
4. L3 : restauration conservatrice, différée après besoins interactifs.

Aucune nouvelle dépendance, migration, donnée réelle ou secret. Drive reste
désactivé. Publication en branche et fusion via PR selon autorisation existante ;
pas de push direct main, aucun déploiement, dépôt d'origine exclu.
