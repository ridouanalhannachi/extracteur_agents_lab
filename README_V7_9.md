# v7.9 — Vérification globale manuelle des emplois

Nouveau module :

`✅ Vérification globale`

Ordre imposé :

S1 :
IAID → DAWM → ILCS → IDSD → MGPDI → FBTD → WM → MLT → GCCD → GITAM → GEE → RT

puis S3 :
IAID → DAWM → ILCS → IDSD → MGPDI → FBTD → WM → MLT → GCCD → GITAM → GEE → RT

Fonctionnement :

- utilise la version active de chaque emploi ;
- affiche une seule séance à la fois ;
- cartes colorées : jour, horaire, salle, matière, enseignant, type, groupe, durée, source ;
- bouton précédente ;
- bouton `✅ Vérifier & suivante` ;
- bouton `⚠️ À revoir & suivante` ;
- bouton suivante ;
- note optionnelle ;
- progression globale ;
- progression par emploi ;
- liste des séances à revoir ;
- reprise automatique à la première séance non vérifiée ;
- sauvegarde de la progression dans `estn.db`.

Installation :

```bash
cd ~/extrateur-edt-rh/edtv7
unzip -o "/mnt/c/Users/HP/Downloads/EDT_Verification_Globale_patch_v7_9.zip" -d ~/extrateur-edt-rh/edtv7
python apply_edt_verification_v7_9.py
python -m py_compile app.py edt_verification_ui.py
streamlit run app.py
```

Après validation :

```bash
git add app.py edt_verification_ui.py VERSION
git commit -m "v7.9 add global timetable manual verification console"
git push
```
