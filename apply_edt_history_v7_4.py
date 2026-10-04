from pathlib import Path

path = Path("app.py")
if not path.exists():
    raise SystemExit("app.py introuvable. Lancez ce script depuis ~/extrateur-edt-rh/edtv7.")

text = path.read_text(encoding="utf-8")

import_line = "from edt_history_ui import render_edt_history\n"
if import_line not in text:
    anchor = "from drive_ui import render_drive_module\n"
    if anchor not in text:
        raise SystemExit("Import drive_ui introuvable dans app.py.")
    text = text.replace(anchor, anchor + import_line, 1)

old_list = '["📅 Emplois du temps", "👥 Ressources humaines", "☁️ Google Drive"]'
new_list = '["📅 Emplois du temps", "🗂️ Historique EDT", "👥 Ressources humaines", "☁️ Google Drive"]'

if old_list in text:
    text = text.replace(old_list, new_list, 1)
elif '"🗂️ Historique EDT"' not in text:
    raise SystemExit("Liste des modules introuvable dans app.py.")

history_handler = (
    'if module == "🗂️ Historique EDT":\n'
    '    render_edt_history()\n'
    '    st.stop()\n\n'
)

if history_handler not in text:
    anchor = (
        'if module == "👥 Ressources humaines":\n'
        '    render_rh_module()\n'
        '    st.stop()\n\n'
    )
    if anchor not in text:
        raise SystemExit("Bloc Ressources humaines introuvable dans app.py.")
    text = text.replace(anchor, history_handler + anchor, 1)

path.write_text(text, encoding="utf-8")
Path("VERSION").write_text("v7.4-edt-history-ui\n", encoding="utf-8")

print("✅ v7.4 appliquée")
print("✅ Nouveau module : 🗂️ Historique EDT")
print("✅ Boutons V1 / V2 / V3...")
print("✅ Affichage de l'emploi complet de chaque version")
print("✅ Affichage des changements associés à chaque version")
print("✅ Option pour afficher toutes les versions")
