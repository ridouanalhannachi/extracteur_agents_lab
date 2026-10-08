# Journal du laboratoire

## 2026-10-04 — Initialisation

Source : e44dd858c5e3f0405d0f401bdf7e1d9c48f5ed56, PR nº 1 v7.9.1.
Copie indépendante sans historique Git source. Deux agents ont préparé isolation
et consignes de développement. Base data-lab/estn-lab.db ; variables production
ignorées ; Drive bloqué ; formulaire Drive remplacé par un message explicite.

Validation : `python -m unittest discover -s tests -q` : 24 tests réussis.
Données fictives et services simulés. Aucun test réel de Drive ni déploiement.
Prochaine étape : L1, vérifier mémoire et corrections après redémarrage.

## 2026-10-04 — L1, persistance entre processus

Base distante examinée : 17171299d75365d9bbcc35935add8a75d383ff08.
Branche : lab/restart-persistence, dérivée de lab/bootstrap-isolation.
Un agent développe les tests ; le responsable relit les assertions et exécute la suite.

Ajout : tests/test_edt_restart.py. Deux scénarios exécutent des interpréteurs Python
séparés : création V1, correction V2 avec validation, puis réouverture sans état UI ;
migration des six colonnes historiques manquantes puis relance dans un autre processus.
Les assertions couvrent versions actives, séances historiques, source/page, notes,
historique exact de la salle modifiée, absence de doublon et intégrité SQLite.

Commande : `python -m unittest discover -s tests -q` — 26 tests réussis.
Aucun défaut reproduit sur ces scénarios : aucun correctif applicatif nécessaire.
Limites : données fictives, Streamlit et Drive simulés ; pas de test navigateur ni
de redémarrage réel Streamlit Cloud. Une base conservée sur disque ne démontre pas
la persistance d'un hébergement dont le disque est éphémère.
Prochaine étape : L2, diagnostic des remplacements distants concurrents, uniquement
sur service simulé et en maintenant Drive désactivé dans le laboratoire.

## 2026-10-05 — L2a, garde conservatrice des remplacements distants

Base examinée : `75534fc639aeaf5725d52b26e38d3b5a711114ce` (PR nº 3).
Branche : `lab/concurrent-backup-guard`. Diagnostic confirmé : un envoi pouvait
appeler `files.update` sans précondition atomique et effacer une correction distante.

Le correctif refuse tout remplacement d'une base distante existante, convertit le
refus en état `conflict` pour la synchronisation et empêche l'envoi automatique
d'annoncer un succès. La première création reste autorisée. Drive demeure désactivé
dans `app_config.py`; les données sont fictives et le service Drive est simulé.

Validation du responsable : `python -m unittest tests.test_drive_concurrency -v`
— 11 tests réussis ; `python -m unittest discover -s tests -q` — 37 tests réussis.
Vérification indépendante : mêmes 11 et 37 tests réussis, `git diff --check` réussi,
aucun secret ni donnée personnelle détecté et aucun workflow de déploiement présent.

Publication : PR nº 4, branche `lab/concurrent-backup-guard`, commit distant
`94156137db9e03302c1786fc09783f939e983f6f` au premier envoi.

Limites : aucune validation OAuth/API Drive réelle ; deux premières créations
simultanées peuvent encore produire des fichiers homonymes. L'interface d'envoi
forcé devra être adaptée avant toute activation réelle, car la garde bloque désormais
tout remplacement. Prochaine étape : traiter la chaîne de dépendances des PR sans
fusion en masse, puis diagnostiquer L3 séparément.

## 2026-10-07 — D1, accueil et navigation (reprise du 6 octobre)

Base distante revérifiée : `38bc8f839c8af5fbd59c401348aac7ea87bab676`, aucune
PR ouverte. Les PR 1–4 sont intégrées ; leurs anciens relais ne décrivent plus
l'état distant. Les copies de travail anciennes sont conservées sans modification.
Branche : `lab/design-home-navigation`. Un seul lot, design prioritaire.

Diagnostic confirmé : entrée directe sur extraction, aucun accueil ; widgets
import/OCR supprimés du rendu lors d'un changement de module. Ajout d'un accueil
avec six accès natifs aux fonctions existantes, navigation unifiée avec retour
Accueil, cartes bordées et thème clair bleu à typographie native. Options d'import
regroupées dans un panneau repliable rendu avant le routage. Aucun compteur fictif,
aucune nouvelle dépendance et aucun changement des moteurs métier.

Pilote : objectifs/backlog ; développeur puis responsable : UI ; Éclaireur : veille
sans adoption ; vérificateur indépendant : lecture et tests, sans écriture.
Fichiers : app.py, ui_navigation.py, .streamlit/config.toml,
tests/test_navigation.py et cinq documents de suivi.

Preuves responsable : `/tmp/edt-ui-venv/bin/python -m unittest discover -s tests -q`
— 39 tests réussis (37 existants + 2 tests Streamlit réels). AppTest vérifie les six
raccourcis, retour accueil, état OCR entre modules et écran Drive désactivé.
`git diff --check` réussi. Serveur Streamlit lancé localement sur 127.0.0.1:8512.
L'ancien environnement échouait dans PyArrow ; un environnement temporaire séparé
avec Streamlit 1.45.1 fonctionne, sans modification des dépendances du dépôt.

Limites : aucune comparaison visuelle avant/après : navigateur Chromium absent,
téléchargement reçu invalide. AppTest n'est pas une capture navigateur. Mobile,
focus clavier et import de fichiers par navigateur restent à contrôler. Les tests
métier couvrent SQLite fictif et Drive simulé ; pas de données réelles ni d'appel IA.
Drive reste désactivé. Aucun workflow GitHub suivi ; absence d'intégration externe
confirmée auparavant par l'utilisateur. Aucun déploiement exécuté.

La publication et la fusion suivent les contrôles autorisés, via PR et SHA attendu.
Le lien et le SHA fusionné seront consignés dans la PR et le compte rendu après
vérification distante. Prochaine étape : contrôle visuel, puis lot D2 tableaux/filtres.

Revue indépendante : 37 tests initiaux réussis, puis deux tests UI et suite 39.
Elle a détecté un défaut d'isolation des nouveaux tests (cache des modules Python).
Corrigé avant publication : chaque scénario s'exécute en sous-processus neuf,
dossier temporaire et assertion que DB_PATH reste sous ce dossier. Revalidation
complète après correction. Contrastes théoriques palette : bleu/blanc 6,70:1,
texte/blanc 16,27:1 ; ce calcul ne remplace pas l'inspection du rendu réel.

Acceptation finale indépendante après correction : 39 tests réussis (5,493 s),
réserve isolation levée et `git diff --check` réussi. Aucun défaut bloquant trouvé.

## 2026-10-07 — D2a, catalogue et filtres de l'historique

Base distante : `58ac343581be8638bf8ab454937819bb3d4b11c9`, PR nº 5
fusionnée et aucune PR ouverte au démarrage. Branche :
`lab/design-table-filters`. Lot limité au catalogue initial de l'Historique.

Diagnostic confirmé : quatre filtres sur une seule rangée, titre non contextuel,
aucun décompte ni réinitialisation, et tableau vide affiché avant l'avertissement.
Changements : filtres sur deux rangées, compteur résultat/total, titre contextuel,
bouton de réinitialisation, état vide avant tableau. Les identifiants, lignes et
règles de filtrage sont conservés. Trois usages `width="stretch"` de cet écran ont
été remplacés par l'option Streamlit compatible `use_container_width=True` après
reproduction d'erreurs sous Streamlit 1.45.1. Aucune requête SQL ni donnée modifiée.

Validation : quatre tests ciblés réussis, dont AppTest sur SQLite temporaire (`2/2`,
filtre `1/2`, combinaison vide et réinitialisation `2/2`). Suite complète :
`/tmp/edt-d2a-venv/bin/python -m unittest discover -s tests -q` — 43 tests réussis
en 10,028 s sur l'arbre final. `git diff --check` réussi. Drive reste désactivé ; aucun workflow de
déploiement suivi et aucune nouvelle dépendance du projet.

Organisation : le Pilote a borné le lot et l'Éclaireur a conclu qu'aucune nouvelle
technologie n'était justifiée. Le développeur délégué a été bloqué par une limite
d'usage avant modification ; le responsable a développé et relu successivement.
La vérification est donc non indépendante pour ce lot. Aucun contournement ou autre
agent n'a été lancé en boucle.

Limites : AppTest ne valide ni rendu visuel réel, ni petit écran, ni navigation au
clavier. Aucune capture avant/après disponible. Publication et fusion restent à
effectuer via PR après contrôle exact du distant ; aucun déploiement.

## 2026-10-07 — D3a, guidage import, correction et export

Base distante : `d31e253cae993b05cea31a12c0b9478c1bc7e5f2`, PR nº 6
fusionnée et aucune PR ouverte au démarrage. Branche :
`lab/design-import-guidance`. Lot limité à la présentation du parcours EDT.

Diagnostic confirmé : la barre latérale présentait « 3. Export » sans action
d'export ; l'export précédait la correction dans les onglets ; état de complétude,
métriques et contrôle documentaire étaient hors contexte. Changements : guide
avant import, libellés latéraux descriptifs, onglets ordonnés « Corriger »,
« Vérifier et exporter », « Enregistrer / Versions », puis assistant optionnel.
L'étape d'export affiche désormais « Prêt pour export », le nombre de séances à
compléter ou l'absence de séance. Aucun bouton ou indicateur fictif n'a été ajouté.

Extraction, référentiel, règles de complétude, données éditées, persistance,
versions, synchronisation, assistant et génération Excel ne sont pas modifiés.
Les 19 widgets, clés et libellés techniques ont été comparés à la base et sont
identiques. Drive reste désactivé ; aucune dépendance ni workflow ajouté.

Validation responsable :
`/tmp/edt-d2a-venv/bin/python -m unittest tests.test_import_workflow_ui -v`
— 6 tests réussis ; suite complète — 49 tests réussis en 13,347 s ; compilation
Python et `git diff --check` réussis. AppTest contrôle le guide avant import ; les
autres contrôles ciblés inspectent la structure et les clés sur l'arbre exact.

La vérification indépendante a d'abord refusé une numérotation contradictoire entre
le guide et les onglets. Le guide a été corrigé puis la vérification complète a été
reprise : 6 tests ciblés en 2,645 s, 49 tests en 11,653 s et `git diff --check`
réussis ; aucun défaut bloquant restant.

Limites : aucun navigateur local ou outil d'automatisation navigateur disponible ;
aucune comparaison visuelle avant/après, validation petit écran ou focus clavier.
Le test UI réel couvre l'écran sans import, pas un chargement de fichier complet.
Publication et fusion restent à effectuer via PR ; aucun déploiement.

## 2026-10-07 — D3b, état interactif des séances enregistrées

Base distante revérifiée : `67df619`, aucune PR ouverte. Branche
`lab/design-save-state`. Le travail commencé plus tôt n'avait produit aucun code ;
la reprise a confirmé un arbre propre et aucun agent concurrent actif.

Diagnostic : auto-save avant l'éditeur détaillé et succès manuel transitoire.
Livré localement : comparaison SQLite en lecture seule après édition/enregistrement,
messages dans les trois onglets pour la cible sélectionnée, distinction version
active/archivée, vide, cible incomplète et état inconnu. Les éditions Intervenants
restent pour Excel seulement ; Source PDF/Page exclus de l'identité métier existante.
Fichiers : app.py, edt_save_state.py, tests/test_save_state.py et cinq documents.

Preuves responsable : `/tmp/edt-ui-venv/bin/python -m unittest discover -s tests
-p test_save_state.py -v` : 6 réussis ; même commande sans filtre, `-q` : 55 tests
réussis en 8,410 s. Revue indépendante acceptée : 6 tests en 1,606 s et 55 en
8,845 s, diff-check réussi. AppTest exerce les trois messages sur import fictif,
correction injectée, sauvegarde, réexécution, échec simulé et retour V1 archivée.
SQLite temporaire couvre ajout/suppression/contexte/erreur/lecture seule et
réouverture avec export Excel de la correction. Aucun nom réel ni secret.

Limites : AppTest injecte les corrections, sans gestes réels dans la grille ;
pas de validation navigateur/mobile/clavier ni de navigation avec saisies.
Pas de nouvelle dépendance projet, extraction/écriture/export métier inchangés.
Drive désactivé. Aucun workflow suivi ; script de déploiement manuel non exécuté ;
absence de déploiement automatique externe déjà confirmée par l'utilisateur.
Publication/fusion par PR à effectuer, avec revérification SHA et arbre exact.
Prochaine priorité : diagnostic correction/annulation et maintien des saisies.

## 2026-10-07 — I2, brouillon interactif appliquer/annuler

Base distante `c0c10d2` (PR nº 8 fusionnée), aucune PR ouverte au démarrage.
Branche `lab/interactive-correction`. Le Pilote a confirmé que l'éditeur était
consommé immédiatement sans appliquer/annuler ni checkpoint durable.

Changement local : brouillon de travail lié à l'empreinte des imports, conservé
pendant navigation ; checkpoint explicite « Appliquer » utilisé par export,
assistant et mémoire ; « Annuler » restaure le dernier appliqué. Un nouvel import
réinitialise le brouillon avec message. Appliquer/annuler n'appelle aucune écriture
SQLite/Drive. Le test D3b a été adapté à l'étape d'application explicite.

Preuve responsable : `/tmp/edt-i2-venv/bin/python -m unittest discover -s tests
-q` — 56 tests réussis en 10,272 s. Le nouveau AppTest utilise des fichiers et une
base fictifs ; il couvre modification, navigation, application, annulation,
ajout/suppression, nouvel import et invariance des versions. `git diff --check` à
effectuer après documentation. Revue indépendante acceptée : 7 tests ciblés en
3,265 s, 56 tests complets en 9,614 s et `git diff --check` réussis. Aucun défaut
bloquant ; le vérificateur confirme que seul le brouillon appliqué alimente export,
assistant et enregistrement et qu'appliquer/annuler ne modifie pas la base.

Limites : AppTest injecte le DataFrame car son API ne permet pas de saisir dans
`st.data_editor` ; pas de capture navigateur, validation mobile/clavier ou geste
réel. Aucune nouvelle dépendance. Drive désactivé. Aucun déploiement.

## 2026-10-07 — I3, activation contextuelle d'une version

Base distante `03425a1` (PR nº 9 fusionnée), aucune PR ouverte au démarrage.
Branche `lab/version-actions`. Diagnostic confirmé : l'Historique gardait la
sélection, mais aucune action ne permettait de réactiver une version archivée.

Changement local : bandeau de version sélectionnée, confirmation obligatoire et
bouton d'activation désactivé avant accord. Le helper SQLite sérialise l'action,
valide l'appartenance, archive l'ancienne active et active la cible. L'appel répété
est sans effet ; versions, séances, commentaires et statuts métier sont préservés.

Preuve responsable : `/tmp/edt-i3-venv/bin/python -m pytest -q` — 62 tests et
15 sous-tests réussis en 18,80 s. AppTest couvre le parcours et la relance ; cinq
tests SQLite couvrent activation, idempotence, refus sans mutation et intégrité.
`git diff --check` réussi avant documentation. Revue indépendante acceptée : 10
tests ciblés, 62 tests complets en 14,629 s, rollback sur panne injectée et
`git diff --check` réussis ; aucun défaut bloquant.

Limites : aucun navigateur réel, capture visuelle, validation mobile ou clavier.
Aucune dépendance projet ajoutée ; Drive reste désactivé ; aucun déploiement.

## 2026-10-07 — I4, export contextuel de la version sélectionnée

Base distante `b41b044` (PR nº 10 fusionnée), aucune PR ouverte au démarrage.
Branche `lab/version-export`. Diagnostic : l'Historique sélectionnait une version
précise sans permettre son export ; le générateur Excel existait déjà.

Changement local : bouton « Télécharger Vn en Excel », fichier nommé avec emploi et
version, feuilles `Intervenants` et `Séances détaillées`, état vide explicite et
légende lecture seule. L'export utilise l'identifiant sélectionné, y compris pour une
version archivée, sans activation ni enregistrement.

Preuve responsable après correction de robustesse : 13 tests ciblés, puis
`/tmp/edt-i4-final/bin/python -m pytest -q` — 65 tests et 15 sous-tests réussis en
18,02 s. Les tests relisent V1/V2, dérivent le nom depuis SQLite, refusent un identifiant
absent et comparent les snapshots. Revue indépendante acceptée : mêmes 13 tests
ciblés, 65 tests et 15 sous-tests en 20,45 s, `git diff --check` réussi et aucun blocage.

Limites : aucun navigateur réel, capture visuelle, validation mobile ou clavier.
Aucune dépendance ajoutée ; Drive désactivé ; aucun déploiement.

## 2026-10-08 — I5, filtres des séances d'une version

Base distante `a59d3cf` (PR nº 11 fusionnée), aucune PR ouverte au démarrage.
Branche `lab/session-filters`. Diagnostic : la version choisie affichait toutes ses
séances sans recherche, filtres, compteur ou réinitialisation.

Changement local : recherche matière/enseignant/groupe/salle/horaire tolérant les accents, sélections
Jour/Enseignant/Groupe, compteur, reset et état zéro. Les clés sont isolées par
emploi/version et conservées lors des allers-retours. Les vues « Toutes les versions »
restent sans contrôles dupliqués. L'Excel conserve toutes les séances.

Preuve responsable : 17 tests ciblés, puis `/tmp/edt-i5-final/bin/python -m pytest -q`
— 69 tests et 15 sous-tests réussis en 11,87 s. Les tests couvrent filtres combinés,
zéro/reset, isolation V1/V2, contenu Excel complet et snapshot SQLite. La comparaison
porte sur les feuilles, car les octets XLSX contiennent un horodatage interne.
Revue indépendante acceptée après ajout de la recherche sans distinction d'accents :
4 tests ciblés, 69 tests complets, compilation et `git diff --check` réussis.

Limites : aucun navigateur réel, capture visuelle, validation mobile ou clavier.
Aucune dépendance ajoutée ; Drive désactivé ; aucun déploiement.

## 2026-10-08 — I6, correction ciblée depuis la Vérification globale

Base distante `5f981ea` (PR nº 12 fusionnée), aucune PR ouverte au démarrage.
Branche `lab/verification-correction`. Diagnostic : la console permettait de choisir,
noter et marquer une séance « À revoir », mais pas de la corriger.

Changement local : formulaire prérempli pour la séance courante, étape « Correction
préparée — non enregistrée », diff visible, annulation sans écriture et confirmation
avant création d'une version. Le mécanisme existant crée une nouvelle version active,
conserve l'ancienne, déduplique les soumissions identiques et archive les changements.
Une durée non numérique, non finie ou non positive est refusée. L'échec de
synchronisation est signalé séparément de la sauvegarde SQLite réussie.

La revue indépendante a reproduit un risque multi-onglet : une correction encore
fondée sur V1 pouvait créer V3 après qu'une autre action avait créé V2, et perdre les
changements propres à V2. Le versionnage accepte désormais un identifiant actif
attendu et sérialise contrôle + création avec `BEGIN IMMEDIATE`. Une base devenue
inactive est refusée sans mutation ; un contenu déjà existant reste dédupliqué.

Preuves finales responsable : 7 tests ciblés et 6 sous-tests, puis
`/tmp/edt-i6-venv/bin/python -m pytest -q` — 76 tests et 21 sous-tests en 56,73 s ;
compilation et `git diff --check` réussis. Revue indépendante acceptée : mêmes tests
ciblés, 76 tests et 21 sous-tests en 67,87 s, compilation et diff-check réussis.
Limites : pas de navigateur Windows réel, capture, test mobile ou clavier. Aucune
dépendance ; Drive désactivé ; aucun déploiement.

## 2026-10-08 — I7, ouverture contextuelle d'une séance trouvée

Base distante `0bdf629` (PR nº 13 fusionnée), aucune PR ouverte au démarrage.
Branche `lab/search-result-context`. Diagnostic : la Recherche globale exposait déjà
les identifiants de séance, version et emploi, mais seulement dans un tableau sans
action vers l'Historique.

Changement local : sélecteur natif des séances trouvées et bouton « Ouvrir dans
l'historique ». La cible transporte uniquement les trois IDs, est validée par jointure
SQLite et ouvre l'emploi et la version exacts, même archivés. Une ligne dédiée marque
la séance. L'intention de navigation est consommée une fois ; le focus reste conservé
aux reruns, est revalidé à chaque affichage et peut être quitté explicitement. Une
cible absente ou croisée entre versions est refusée sans faux contexte.

Preuves responsable finales : 16 tests ciblés en 5,175 s ; puis `.venv/bin/python -m
pytest -q` — 81 tests et 21 sous-tests en 15,81 s. AppTest couvre V1 archivée alors que V2
est active, persistance puis effacement du focus, filtres d'une autre version et
erreur de cible. Snapshot SQLite avant/après identique ; `git diff --check` réussi.

Organisation : Pilote et Éclaireur distincts ; aucune dépendance justifiée. Le
développeur a corrigé après revue responsable la perte initiale du focus au rerun.
La revue indépendante a ensuite détecté des libellés identiques pour deux séances
distinctes au même créneau ; l'ajout enseignant/groupe/salle et un AppTest de sélection
exacte ont levé la réserve. Revue finale : 16 tests ciblés en 5,75 s, puis 81 tests et
21 sous-tests en 16,76 s, compilation et diff-check réussis. Limite : aucun navigateur
Windows réel, capture, petit écran ou navigation clavier. Drive désactivé ; aucun
déploiement.
