# Module RH v6 — mémoire permanente et conflits

## Objectif
Le module RH v6 accepte des fichiers partiels et hétérogènes. Aucun fichier n'a besoin de contenir toutes les informations.

Champs prioritaires : Statut, Nom, Prénom, Email, Téléphone, Diplôme, Spécialité, Département.
Toutes les autres colonnes sont conservées dans `Autres informations`.

## Formats pris en charge
- Excel : XLSX, XLS, XLSM, ODS
- CSV / TSV
- JSON
- Word DOCX
- PDF texte et tableaux
- TXT / Markdown
- Images PNG/JPG/JPEG/TIFF/BMP/WEBP avec OCR Tesseract
- PDF scanné : OCR automatique si Tesseract est disponible

Pour l'OCR sous Ubuntu/WSL :

```bash
sudo apt install -y tesseract-ocr tesseract-ocr-fra
```

## Mémoire permanente
Toutes les données sont stockées dans `data/estn.db` (SQLite) :
- fiches enseignants
- historique de chaque valeur observée
- sources/imports
- fragments non rattachés
- correspondances de colonnes apprises
- conflits RH et décisions prises

## Apprentissage des colonnes
Une colonne inconnue est conservée et apparaît dans `Mémoire des colonnes`.
L'utilisateur l'associe une seule fois à un champ RH. Cette association est ensuite réutilisée automatiquement pour les futurs fichiers.

## Gestion des conflits
Une nouvelle valeur différente d'une valeur existante n'écrase jamais silencieusement la base.
Elle crée un conflit avec :
- enseignant
- champ
- valeur actuelle
- nouvelle valeur
- source
- date

Trois décisions sont proposées :
1. garder la valeur actuelle ;
2. adopter la nouvelle valeur ;
3. garder l'actuelle et archiver la nouvelle comme alternative.

## Important
"Tous les formats" au sens littéral n'est pas possible : un format propriétaire inconnu nécessite un nouvel adaptateur. La v6 couvre les formats bureautiques et documents usuels et conserve les données non reconnues pour apprentissage futur.
