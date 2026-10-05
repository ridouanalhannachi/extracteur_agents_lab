from pathlib import Path

path = Path("app.py")
if not path.exists():
    raise SystemExit("app.py introuvable. Lancez ce script depuis ~/extrateur-edt-rh/edtv7.")

text = path.read_text(encoding="utf-8")

import_line = "from edt_verification_ui import render_global_verification\n"
if import_line not in text:
    anchor = "from drive_ui import render_drive_module\n"
    if anchor not in text:
        raise SystemExit("Import drive_ui introuvable dans app.py.")
    text = text.replace(anchor, anchor + import_line, 1)

known_lists = [
    '["📅 Emplois du temps", "🔎 Recherche globale", "📊 Statistiques EDT", "🗂️ Historique EDT", "👥 Ressources humaines", "☁️ Google Drive"]',
    '["📅 Emplois du temps", "🔎 Recherche globale", "🗂️ Historique EDT", "👥 Ressources humaines", "☁️ Google Drive"]',
    '["📅 Emplois du temps", "🗂️ Historique EDT", "👥 Ressources humaines", "☁️ Google Drive"]',
    '["📅 Emplois du temps", "👥 Ressources humaines", "☁️ Google Drive"]',
]

new_list = (
    '["📅 Emplois du temps", "✅ Vérification globale", "🔎 Recherche globale", '
    '"📊 Statistiques EDT", "🗂️ Historique EDT", "👥 Ressources humaines", "☁️ Google Drive"]'
)

replaced = False
for old in known_lists:
    if old in text:
        text = text.replace(old, new_list, 1)
        replaced = True
        break

if not replaced and '"✅ Vérification globale"' not in text:
    raise SystemExit("Liste des modules introuvable dans app.py.")

handler = (
    'if module == "✅ Vérification globale":\n'
    '    render_global_verification()\n'
    '    st.stop()\n\n'
)

if handler not in text:
    anchors = [
        (
            'if module == "🔎 Recherche globale":\n'
            '    render_global_edt_search()\n'
            '    st.stop()\n\n'
        ),
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
        raise SystemExit("Point d'insertion du module de vérification introuvable.")

path.write_text(text, encoding="utf-8")
Path("VERSION").write_text("v7.9-global-manual-verification\n", encoding="utf-8")

print("✅ v7.9 appliquée")
print("✅ Nouveau module : ✅ Vérification globale")
print("✅ Ordre S1 puis S3 respecté")
print("✅ Console colorée séance par séance")
print("✅ Navigation précédente / suivante")
print("✅ Vérifiée / À revoir mémorisés dans estn.db")
print("✅ Progression globale et par emploi")
