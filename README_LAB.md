# Extracteur EDT/RH — laboratoire indépendant

Copie complète des fichiers du commit source `e44dd858c5e3f0405d0f401bdf7e1d9c48f5ed56`
(proposition nº 1, v7.9.1), avec isolation ajoutée. L'historique Git source n'est pas
inclus. Dépôt du laboratoire : https://github.com/ridouanalhannachi/extracteur_agents_lab.
Aucun déploiement effectué. Les cycles sont gérés séparément : ce document ne prouve
pas leur activation.

## Démarrage local

Depuis ce dossier, dans un environnement Python dédié :

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

La base est `data-lab/estn-lab.db`. Les paramètres APP_MODE et APP_DATA_DIR hérités
sont ignorés. Google Drive est bloqué dans cette édition ; aucun secret n'est
nécessaire. Utiliser uniquement des données fictives. Ne pas exécuter les anciens
scripts apply_*, fix_* ou deploy_cloud.sh : ils sont conservés comme archives source.
Les anciennes notices concernent le projet source ; cette notice prévaut pour le lab.

## Vérification et reprise

```sh
python -m unittest discover -s tests -v
```

Lire AGENTS.md, docs/BACKLOG_LAB.md et docs/LAB_AUTONOMIE.md. Chaque cycle doit
livrer un correctif testé dans une branche dédiée, puis s'arrêter. Les fusions et
déploiements restent soumis à l'accord de l'utilisateur.
