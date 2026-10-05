# Module RH v5.1

Amélioration de la détection CSV et retour visible après import.

# Module Ressources humaines

Le module **👥 Ressources humaines** est indépendant du module Emplois du temps.

## Données prioritaires

- Statut : Permanent / Vacataire / Non précisé
- Nom
- Prénom
- Email
- Téléphone
- Diplôme
- Spécialité
- Département

Les autres colonnes détectées dans les documents ne sont pas supprimées : elles sont stockées dans **Autres informations** au format JSON.

## Formats pris en charge

- Excel : `.xlsx`, `.xls`, `.xlsm`
- CSV
- Word : `.docx`
- PDF texte / tableaux détectables
- Texte : `.txt`, `.md`

Les PDF scannés sans couche texte pourront nécessiter un module OCR dans une version ultérieure.

## Stockage

La base locale est :

`data/estn.db`

Table principale : `enseignants`.

Les doublons exacts sont reconnus dans cet ordre : Email, Téléphone, puis Nom + Prénom. Une fiche déjà connue est mise à jour avec les nouvelles valeurs non vides.

## Utilisation

1. Lancer l'application Streamlit.
2. Dans la barre latérale, choisir **👥 Ressources humaines**.
3. Importer un ou plusieurs fichiers RH.
4. Vérifier / corriger l'aperçu détecté.
5. Cliquer sur **Enregistrer dans la base RH**.
6. Utiliser les filtres et exports Excel/CSV.


## v5.3
- Reconnaissance des en-têtes annotés comme `First Name [Required]`, `Last Name [Required]` et `Email Address [Required]`.
- `Status [READ ONLY]` est conservé comme information supplémentaire et n’est pas confondu avec le statut RH Permanent/Vacataire.
- Les fichiers partiels restent acceptés : prénom/nom/email suffisent à créer une fiche à enrichir plus tard.
