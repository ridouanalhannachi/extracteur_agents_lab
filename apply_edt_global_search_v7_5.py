from pathlib import Path

path = Path("app.py")
if not path.exists():
    raise SystemExit("app.py introuvable. Lancez ce script depuis ~/extrateur-edt-rh/edtv7.")

text = path.read_text(encoding="utf-8")

import_line = "from edt_global_search_ui import render_global_edt_search\n"
if import_line not in text:
    anchor = "from drive_ui import render_drive_module\n"
    if anchor not in text:
        raise SystemExit("Import drive_ui introuvable dans app.py.")
    text = text.replace(anchor, anchor + import_line, 1)

old_variants = [
    '["📅 Emplois du temps", "🗂️ Historique EDT", "👥 Ressources humaines", "☁️ Google Drive"]',
    '["📅 Emplois du temps", "👥 Ressources humaines", "☁️ Google Drive"]',
]

new_list = '["📅 Emplois du temps", "🔎 Recherche globale", "🗂️ Historique EDT", "👥 Ressources humaines", "☁️ Google Drive"]'

changed = False
for old in old_variants:
    if old in text:
        text = text.replace(old, new_list, 1)
        changed = True
        break

if not changed and '"🔎 Recherche globale"' not in text:
    raise SystemExit("Liste des modules introuvable dans app.py.")

handler = (
    'if module == "🔎 Recherche globale":\n'
    '    render_global_edt_search()\n'
    '    st.stop()\n\n'
)

if handler not in text:
    anchors = [
        (
            'if module == "🗂️ Historique EDT":\n'
            '    render_edt_history()\n'
            '    st.stop()\n\n'
        ),
        (
            'if module == "👥 Ressources humaines":\n'
            '    render_rh_module()\n'
            '    st.stop()\n\n'
        ),
    ]

    inserted = False
    for anchor in anchors:
        if anchor in text:
            text = text.replace(anchor, handler + anchor, 1)
            inserted = True
            break

    if not inserted:
        raise SystemExit("Point d'insertion du module Recherche globale introuvable.")

path.write_text(text, encoding="utf-8")
Path("VERSION").write_text("v7.5-global-edt-search\n", encoding="utf-8")

print("✅ v7.5 appliquée")
print("✅ Nouveau module : 🔎 Recherche globale")
print("✅ Recherche dans séances, versions et changements")
print("✅ Exemples : DAOUDI, Salle A12, RT S3, Réseaux")
print("✅ Ouverture détaillée d'une version trouvée")
