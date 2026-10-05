# Connexion Google Drive — v6.3

La base active reste `data/estn.db` en local. Google Drive conserve une copie synchronisée dans le dossier `Extracteur_EDT_RH`.

## Pourquoi ne pas ouvrir SQLite directement dans Drive ?

SQLite utilise des écritures et verrous fréquents. La v6.3 utilise donc une copie locale et effectue des synchronisations atomiques avec sauvegarde.

## 1. Créer l'accès Google Drive

1. Ouvrir Google Cloud Console.
2. Créer ou sélectionner un projet.
3. Activer **Google Drive API**.
4. Configurer **Google Auth Platform / OAuth consent screen**.
5. Créer un **OAuth Client ID** de type **Desktop app / Application de bureau**.
6. Télécharger le JSON et le conserver sous le nom `credentials.json`.

La portée utilisée par l'application est :

`https://www.googleapis.com/auth/drive.file`

Elle permet à l'application de gérer uniquement les fichiers qu'elle crée ou utilise elle-même.

## 2. Installer les dépendances

Dans Ubuntu/WSL :

```bash
cd ~/extrateur-edt-rh/edtv3
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Lancer l'application

```bash
streamlit run app.py --server.address=0.0.0.0
```

Ouvrir `http://localhost:8501`, puis choisir **☁️ Google Drive**.

1. Importer `credentials.json`.
2. Cliquer **Connecter mon compte Google Drive**.
3. Autoriser le compte Google dans le navigateur.
4. Cliquer **Synchroniser automatiquement**.
5. Lors de la première synchronisation sur un appareil, si une base locale et une base Drive existent toutes les deux, choisir explicitement la version de référence.

## Fonctionnement

- `PC/WSL/data/estn.db` = copie active locale.
- `Google Drive/Extracteur_EDT_RH/estn.db` = copie synchronisée centrale.
- `Google Drive/Extracteur_EDT_RH/backups/` = sauvegardes avant remplacement de la version Drive.
- `data/backups/` = sauvegardes locales avant téléchargement d'une version Drive.
- `data/gdrive/token.json` = jeton OAuth local. Ne pas le partager.
- `data/gdrive/credentials.json` = identifiants OAuth de l'application. Ne pas le publier.

## Synchronisation prudente

La v6.3 mémorise le hash de la dernière synchronisation :

- seule la copie locale a changé → upload ;
- seule la copie Drive a changé → download ;
- les deux ont changé → l'application demande quelle version utiliser ;
- identiques → aucune opération.

