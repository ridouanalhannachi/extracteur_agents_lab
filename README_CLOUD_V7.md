# Extracteur EDT + RH — v7 Cloud Run

## Objectif

- développement local sous WSL/Streamlit ;
- version stable déployée sur Google Cloud Run ;
- `estn.db` restaurée/synchronisée avec Google Drive ;
- application protégée par un mot de passe personnel ;
- maximum 1 instance Cloud Run et concurrence 1 pour protéger SQLite.

## Données sensibles

Ne jamais inclure dans Git, ZIP public ou image Docker :
- `data/gdrive/token.json`
- `credentials.json`
- `estn.db`
- mots de passe

Le `.dockerignore` exclut `data/` du déploiement.

## Avant le premier déploiement

1. En mode local, vérifier que Google Drive est connecté et que `data/gdrive/token.json` existe.
2. Installer Google Cloud CLI (`gcloud`) dans Ubuntu/WSL.
3. Exécuter `gcloud auth login` puis choisir le projet Google Cloud.
4. Définir :

```bash
export GOOGLE_CLOUD_PROJECT="ID_DU_PROJET"
export APP_PASSWORD="UN_MOT_DE_PASSE_FORT"
```

5. Lancer :

```bash
./deploy_cloud.sh
```

Le script active les API nécessaires, place le token Drive et le mot de passe dans Secret Manager, puis déploie Cloud Run.

## Développement après déploiement

Continuez à travailler localement. Une nouvelle version stable est publiée simplement en relançant :

```bash
./deploy_cloud.sh
```

Cloud Run crée une nouvelle révision ; l'ancienne reste dans l'historique des révisions.

## Limite actuelle de la v7

- Le module RH est persistant via SQLite + Google Drive.
- L'extraction EDT fonctionne dans Cloud Run, mais les affectations EDT ne sont pas encore archivées dans SQLite.
- Ollama/r19-mini reste local. Dans le cloud, les réponses factuelles Python restent utilisables ; une IA cloud sera ajoutée dans une étape ultérieure.
