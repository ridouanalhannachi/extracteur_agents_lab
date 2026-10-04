# RH v6.2 — Mémoire des décisions de conflit

Cette version ajoute un apprentissage permanent des conflits RH.

Quand un conflit est résolu manuellement, l'application mémorise la décision pour :
- le même enseignant ;
- le même champ RH ;
- la même paire de valeurs, même si l'ordre est inversé.

Exemple :
- Département actuel : `I2IT`
- Nouvelle valeur : `Informatique`
- Décision : conserver `I2IT`

Si ce même conflit réapparaît plus tard pour le même enseignant, il est résolu automatiquement sans être redemandé.

Les applications automatiques restent tracées dans l'historique des conflits avec le statut `auto_resolved`.

Une section **Décisions de conflit mémorisées** permet de consulter les règles apprises, leur nombre d'applications automatiques et d'oublier une règle si nécessaire.

## Installation du patch

Dans Ubuntu/WSL :

```bash
cd ~/extrateur-edt-rh/edtv3
```

Arrêter Streamlit avec `Ctrl+C`, puis :

```bash
unzip -o "/mnt/c/Users/HP/Downloads/RH_patch_v6_2.zip" -d ~/extrateur-edt-rh/edtv3
rm -rf __pycache__
source .venv/bin/activate
streamlit run app.py --server.address=0.0.0.0
```

Aucune suppression de `data/estn.db` n'est nécessaire. La table de mémoire est créée automatiquement dans la base existante.
