> **Laboratoire indépendant** : commencer par [README_LAB.md](README_LAB.md).
> Base dédiée et Google Drive désactivé. La notice ci-dessous est héritée du projet source.

# Emplois du temps PDF et Word vers Excel (.xlsx)

Application locale Streamlit pour lire des emplois du temps PDF ou Word (.docx) structurés,
extraire les séances et produire un fichier Excel organisé des enseignants intervenants.

Les tableaux classiques (CM/TD/enseignant/horaire) et les nouveaux tableaux
(RT/GCCD avec « Cours · horaire · Pr./Dr. » et FBTD/MLT) sont pris en charge.
Les tableaux de MGPDI et Web Marketing (WM), où la salle peut précéder l'horaire
et où plusieurs séances se trouvent dans une cellule, sont également pris en charge.
Pour les autres tableaux, l'application essaie aussi une lecture automatique des
grilles avec jours en lignes ou colonnes et horaires comme en-têtes. Les documents
sans grille peuvent être lus par blocs de texte. Après l'extraction, vous pouvez
corriger les séances, en ajouter ou en supprimer ; les fichiers inconnus restent
exploitables par saisie manuelle.

Pour les PDF scannés, activez l'OCR dans la barre latérale. Il faut installer
Tesseract OCR sur votre ordinateur et, si nécessaire, indiquer le chemin de
`tesseract.exe` (par exemple `C:\Program Files\Tesseract-OCR\tesseract.exe`).
L'OCR peut manquer des séances ou se tromper sur les caractères des horaires :
comparez toujours le tableau détaillé au PDF avant l'export.
L'application signale les enseignants dont le nom a été laissé en pointillés
dans l'emploi du temps ; ces noms doivent être complétés manuellement.

L'objectif est de lire un large éventail d'emplois du temps, pas de garantir
une reconnaissance parfaite de tout PDF ou Word. Les fichiers Word pris en charge
sont les `.docx` ; les anciens `.doc` doivent être enregistrés en `.docx` ou PDF.

## Sortie Excel

Le bouton de téléchargement génère :

`Liste_des_Enseignants_intervenants.xlsx`

Le classeur contient :

### Feuille `Intervenants`

- Ligne 1 : `Liste des Enseignants intervenants`
- Ligne 2 : vide
- Ligne 3 : en-têtes
- Colonnes :
  - Nom et prénom
  - Statut
  - Filière
  - Niveau
  - Matière
  - CH
  - Tél
  - Email
  - Département

Cette disposition reprend la structure de la feuille `Intervenants` du fichier Global_Estn.

### Feuille `Séances détaillées`

Contient le détail de chaque séance détectée : jour, matière, type, enseignant,
horaire, durée, groupe, salle, filière, niveau, année universitaire et PDF source.

## Installation / mise à jour

Dans PowerShell, dans le dossier de l'application :

```powershell
py -m pip install -r requirements.txt
```

Puis :

```powershell
py -m streamlit run app.py
```

## Référentiel enseignants facultatif

Le fichier CSV `referentiel_enseignants_modele.csv`, ou le fichier Excel
`Global_Estn_2026 -final.xlsx` (feuille `Intervenants`), peut être utilisé uniquement comme entrée
pour compléter automatiquement Statut, Tél, Email et Département.

Vérifiez les résultats affichés avant de télécharger le fichier. Le fichier Global_Estn
peut contenir des enseignants ou matières d'une ancienne version de l'emploi du temps :
seules les identités des enseignants qui correspondent sont complétées automatiquement.
La valeur CH de 3h suit la charge nominale du modèle ; les durées réelles restent
consultables dans la feuille `Séances détaillées`.

Le fichier **généré par l'application est bien un `.xlsx` et non un `.csv`**.
