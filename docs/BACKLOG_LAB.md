# Backlog EDT/RH — 7 octobre 2026

Base vérifiée : `c0c10d2`, PR 1 à 8 fusionnées, aucune PR ouverte au début du
cycle. Le socle de fiabilité et D1/D2a/D3a/D3b sont intégrés.

## Lot en cours : I2 — Brouillon de correction contrôlé

Diagnostic confirmé : `details_editor` alimentait immédiatement les étapes
suivantes, sans action explicite appliquer/annuler ni checkpoint indépendant de
l'état interne du widget Streamlit.

Livrable développé : brouillon de travail conservé lors des reruns et changements
de module ; boutons « Appliquer les corrections » et « Annuler les modifications
en cours » ; messages distincts pour modifications en cours, corrections appliquées
localement et version réellement enregistrée. Export, assistant et mémoire utilisent
uniquement le dernier brouillon appliqué. Changer les fichiers importés réinitialise
le brouillon avec un message explicite.

Critères : modification/ajout/suppression persistent pendant navigation ; appliquer
change le checkpoint sans écrire en base ; annuler restaure le dernier appliqué ;
nouvel import ne réutilise aucune saisie ; l'enregistrement reste l'unique création
manuelle de version ; tests D3b toujours réussis.

État : 56 tests réussis par le responsable et par le vérificateur indépendant. Pas de
capture navigateur, validation tactile/mobile ou geste réel dans la grille : AppTest
injecte le DataFrame équivalent à une édition.

## Suite

1. I3 : diagnostiquer les actions contextuelles sur les versions.
2. D5 : vérifier petit écran, clavier et contraste dans un navigateur réel.
3. L3 : restauration conservatrice, différée après les besoins interactifs.

Aucune nouvelle dépendance, donnée réelle ou secret. Drive reste désactivé. Pas de
push direct sur `main`, aucun déploiement, dépôt d'origine exclu.
