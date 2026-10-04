from pathlib import Path

app = Path("app.py")
if not app.exists():
    raise SystemExit("app.py introuvable. Exécutez ce script depuis ~/extrateur-edt-rh/edtv7.")

text = app.read_text(encoding="utf-8")

if "from edt_memory import (" not in text:
    target = "from drive_ui import render_drive_module\n"
    replacement = '''from drive_ui import render_drive_module
from gdrive_sync import auto_upload_after_change
from edt_memory import (
    ensure_edt_memory_db,
    auto_save_uploaded_timetables,
    list_timetables,
    list_versions,
    get_version_id,
    load_version_sessions,
)
'''
    if target not in text:
        raise SystemExit("Import drive_ui introuvable.")
    text = text.replace(target, replacement, 1)

anchor = '''for session in all_sessions:
    values = metadata_map[session["Source PDF"]]
    session["Filière"] = str(values["Filière"]).strip()
    session["Niveau"] = str(values["Niveau"]).strip()
'''
auto = anchor + '''

# Mémoire automatique EDT : dès l'upload, après extraction et correction des métadonnées.
# Un contenu strictement identique est reconnu et ne crée pas une nouvelle version.
if all_sessions:
    try:
        _memory_frame = build_details_dataframe(all_sessions)
        _memory_results = auto_save_uploaded_timetables(_memory_frame)
        _created = [x for x in _memory_results if x.get("status") == "created"]
        _skipped = [x for x in _memory_results if x.get("status") == "skipped"]

        if _created:
            ok_sync, sync_msg = auto_upload_after_change()
            for item in _created:
                st.success(
                    f'🧠 {item["filiere"]} {item["niveau"]} — '
                    f'{item["period"]} {item["academic_year"]} : '
                    f'V{item["version_number"]} mémorisée automatiquement.'
                )
            if not ok_sync:
                st.warning(sync_msg)

        for item in _skipped:
            st.warning(
                f'🧠 {item.get("filiere") or "?"} {item.get("niveau") or "?"} : '
                f'{item["message"]}'
            )
    except Exception as exc:
        st.warning(f"🧠 Mémoire automatique EDT non appliquée : {exc}")
'''
if "_memory_results = auto_save_uploaded_timetables" not in text:
    if anchor not in text:
        raise SystemExit("Bloc de métadonnées introuvable.")
    text = text.replace(anchor, auto, 1)

old_tabs = 'tab1, tab2, tab3 = st.tabs(["Liste des enseignants intervenants", "Séances détaillées", "🤖 Assistant IA"])'
new_tabs = 'tab1, tab2, tab3, tab4 = st.tabs(["Liste des enseignants intervenants", "Séances détaillées", "🤖 Assistant IA", "🧠 Mémoire / Versions"])'
if old_tabs in text:
    text = text.replace(old_tabs, new_tabs, 1)

marker = "\nst.divider()\nst.caption(\n"
history = '''
with tab4:
    st.subheader("🧠 Mémoire des emplois du temps")
    st.caption(
        "La mémorisation est automatique dès l'upload. "
        "Un emploi identique ne crée pas de doublon ; un emploi modifié crée V2, V3, etc."
    )

    ensure_edt_memory_db()
    memory = list_timetables()

    if memory.empty:
        st.info("Aucun emploi du temps n'est encore mémorisé.")
    else:
        st.dataframe(memory, use_container_width=True, hide_index=True)

        choices = {}
        for _, row in memory.iterrows():
            label = (
                f'{row["Année universitaire"]} | {row["Période"]} | '
                f'{row["Filière"]} | {row["Niveau"]}'
            )
            choices[label] = int(row["id"])

        selected = st.selectbox("Consulter l'historique", list(choices.keys()), key="edt_memory_history")
        timetable_id = choices[selected]
        versions = list_versions(timetable_id)
        st.dataframe(versions, use_container_width=True, hide_index=True)

        if not versions.empty:
            version_numbers = [int(str(v).replace("V", "")) for v in versions["Version"].tolist()]
            selected_version = st.selectbox(
                "Version à afficher",
                version_numbers,
                format_func=lambda v: f"V{v}",
                key="edt_memory_version",
            )
            version_id = get_version_id(timetable_id, selected_version)
            if version_id:
                st.dataframe(load_version_sessions(version_id), use_container_width=True, hide_index=True)

'''
if "with tab4:" not in text:
    if marker not in text:
        raise SystemExit("Point d'insertion avant le pied de page introuvable.")
    text = text.replace(marker, "\n" + history + marker, 1)

app.write_text(text, encoding="utf-8")
Path("VERSION").write_text("v7.2.1-edt-auto-memory\n", encoding="utf-8")

print("✅ v7.2.1 appliquée")
print("✅ Mémorisation automatique des emplois du temps activée")
print("✅ Un emploi identique ne crée pas une nouvelle version")
