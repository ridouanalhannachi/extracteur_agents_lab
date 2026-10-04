# v7.1 — Streamlit Community Cloud

Cette version garde la même application EDT/RH mais adapte la persistance au stockage éphémère de Streamlit Community Cloud.

## Architecture

- Streamlit Community Cloud exécute l'application.
- Google Drive conserve `estn.db`.
- Au démarrage Cloud, `estn.db` est restaurée depuis Drive vers `/tmp/extracteur-edt-rh/estn.db`.
- En Cloud, la synchronisation RH vers Drive est obligatoire après les mutations prises en charge.
- Si Drive est absent ou invalide, l'application s'arrête au lieu de démarrer sur une base vide.

## Secrets Streamlit

Dans Advanced settings > Secrets, définir des secrets racine TOML :

```toml
APP_MODE = "streamlit"
APP_PASSWORD = "VOTRE_MOT_DE_PASSE"
GDRIVE_TOKEN_JSON = '''{...contenu JSON complet de data/gdrive/token.json...}'''
```

Ne jamais publier `token.json`, `credentials.json`, `estn.db` ou `.streamlit/secrets.toml`.

## Fichiers importants pour le déploiement

- `app.py` : point d'entrée Streamlit
- `requirements.txt` : dépendances Python
- `packages.txt` : installe Tesseract pour l'OCR
- `.streamlit/config.toml` : configuration Streamlit
- `.gitignore` : bloque les secrets et la base locale

## Avant le premier déploiement

1. Depuis la version locale, vérifier que Google Drive est connecté.
2. Dans l'onglet Google Drive, envoyer la base locale vers Drive.
3. Vérifier que `Extracteur_EDT_RH/estn.db` existe bien dans Drive.
4. Créer un dépôt GitHub privé et y envoyer uniquement le code.
5. Déployer `app.py` depuis Streamlit Community Cloud.
6. Coller les secrets dans Advanced settings.
