from pathlib import Path

path = Path("app.py")
if not path.exists():
    raise SystemExit("app.py introuvable. Lancez ce script depuis ~/extrateur-edt-rh/edtv7.")

text = path.read_text(encoding="utf-8")

import_line = "from edt_statistics_ui import render_edt_statistics\n"
if import_line not in text:
    anchor = "from drive_ui import render_drive_module\n"
    if anchor not in text:
        raise SystemExit("Import drive_ui introuvable dans app.py.")
    text = text.replace(anchor, anchor + import_line, 1)

variants = [
    '["📅 Emplois du temps", "🔎 Recherche globale", "🗂️ Historique EDT", "👥 Ressources humaines", "☁️ Google Drive"]',
    '["📅 Emplois du temps", "🗂️ Historique EDT", "👥 Ressources humaines", "☁️ Google Drive"]',
    '["📅 Emplois du temps", "👥 Ressources humaines", "☁️ Google Drive"]',
]

new_list = (
    '["📅 Emplois du temps", "🔎 Recherche globale", "📊 Statistiques EDT", '
    '"🗂️ Historique EDT", "👥 Ressources humaines", "☁️ Google Drive"]'
)

replaced = False
for old in variants:
    if old in text:
        text = text.replace(old, new_list, 1)
        replaced = True
        break

if not replaced and '"📊 Statistiques EDT"' not in text:
    raise SystemExit("Liste des modules introuvable dans app.py.")

handler = (
    'if module == "📊 Statistiques EDT":\n'
    '    render_edt_statistics()\n'
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
        raise SystemExit("Point d'insertion du module Statistiques introuvable.")

path.write_text(text, encoding="utf-8")
Path("VERSION").write_text("v7.6-edt-statistics-dashboard\n", encoding="utf-8")

print("✅ v7.6 appliquée")
print("✅ Nouveau module : 📊 Statistiques EDT")
print("✅ Cartes KPI colorées")
print("✅ Graphiques enseignants, salles, matières et types")
print("✅ Statistiques des versions et changements")
print("✅ Filtres année / période / filière / semestre")
