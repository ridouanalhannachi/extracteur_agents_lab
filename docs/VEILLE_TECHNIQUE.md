# Veille technique du laboratoire

## 2026-10-05 — L2a

Aucune nouvelle dépendance n'est justifiée pour la garde conservatrice. Le défaut
est corrigé avec les primitives existantes et des tests `unittest`, compatibles
avec Python, SQLite et des PC modestes. Ajouter un outil de synchronisation ou une
base distribuée augmenterait le coût, le risque et le périmètre sans démontrer un
gain pour ce lot. Réévaluer seulement après le diagnostic de L3 ou si une écriture
conditionnelle officiellement prise en charge devient nécessaire.
