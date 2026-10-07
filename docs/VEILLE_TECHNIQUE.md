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
