# Veille technique du laboratoire

## 2026-10-05 — L2a

Aucune nouvelle dépendance n'est justifiée pour la garde conservatrice. Le défaut
est corrigé avec les primitives existantes et des tests `unittest`, compatibles
avec Python, SQLite et des PC modestes. Ajouter un outil de synchronisation ou une
base distribuée augmenterait le coût, le risque et le périmètre sans démontrer un
gain pour ce lot. Réévaluer seulement après le diagnostic de L3 ou si une écriture
conditionnelle officiellement prise en charge devient nécessaire.

## 2026-10-06 — D1, accueil et navigation

Diagnostic du code : la navigation actuelle utilise déjà les composants Streamlit
et donne accès à sept modules existants. Le premier écran concentre les consignes
d'importation et les réglages dans la barre latérale, sans accueil dédié.
Aucune nouvelle dépendance ni migration de framework n'est justifiée pour clarifier
ces accès et la hiérarchie visuelle. Conserver les composants présents, avec une
mise en forme légère ; aucun service, coût ou appel IA supplémentaire proposé.
Le bénéfice reste à vérifier sur les parcours réels : accueil compréhensible,
accès à chaque module existant et conservation des importations, corrections et
exports. La comparaison visuelle dépend de la possibilité de lancer l'interface.

## 2026-10-07 — D2, tableaux et filtres

Aucune nouvelle technologie n'est justifiée pour rendre les tableaux et filtres
plus lisibles. Les composants Streamlit déjà présents (`st.dataframe`, champs de
recherche et sélections multiples) couvrent le lot sans augmenter le temps
d'installation, la mémoire utilisée ni la maintenance sur les PC modestes. Une
grille JavaScript ou une bibliothèque de thème ajouterait une dépendance et une
surface de sécurité sans bénéfice mesuré à ce stade. Le retour arrière reste un
simple retrait des ajustements d'interface. Critère d'acceptation : filtres
compréhensibles, résultat vide explicite et colonnes essentielles lisibles, sans
régression des exports. Aucun workflow de déploiement n'est présent dans le dépôt
et `DRIVE_ENABLED` demeure fixé à `False` dans le laboratoire.

## 2026-10-07 — D3, guidage import, correction et export

Aucune nouvelle technologie n'est justifiée. Le problème observé est un parcours
réparti entre les fichiers de la barre latérale, les corrections de métadonnées,
quatre onglets et l'export ; les composants Streamlit natifs déjà installés
(conteneurs, messages d'état, onglets et boutons) suffisent à rendre les étapes et
leurs prérequis explicites. Ajouter un composant « stepper », une bibliothèque UI
ou changer de framework augmenterait installation, mémoire, maintenance et surface
de sécurité sans gain mesuré sur les PC modestes. L'alternative retenue est un
guidage léger dans `app.py`, réversible par retrait des seuls éléments de
présentation. Critère d'acceptation : sur données fictives, l'utilisateur distingue
import, correction, enregistrement et export, sans modifier extraction, persistance
ni fichier Excel ; la lisibilité visuelle reste à vérifier dans un vrai navigateur.

## 7 octobre 2026 — D3b

Besoin confirmé : état d'enregistrement fiable après correction. Le Pilote a
examiné le hash canonique existant, SQLite et les messages Streamlit : aucune
nouvelle technologie ni dépendance ne se justifie. Comparer les séances stockées
en lecture seule évite de confondre un succès UI transitoire avec une sauvegarde.
Aucun gain de performance mesuré ou nouveauté externe revendiqué.

## 7 octobre 2026 — I2

Le défaut relève de l'état d'interface : brouillon, checkpoint et annulation. Les
composants Streamlit, `session_state`, `hashlib` et pandas déjà présents suffisent.
Aucun formulaire tiers, grille JavaScript ou nouvelle dépendance n'est justifié :
ils alourdiraient l'installation sur PC modeste sans bénéfice mesuré. Le retour
arrière reste limité au helper local et aux boutons de l'éditeur.
