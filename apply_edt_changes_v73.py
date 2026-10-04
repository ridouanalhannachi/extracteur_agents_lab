from pathlib import Path

app_path = Path("app.py")
mem_path = Path("edt_memory.py")

if not app_path.exists() or not mem_path.exists():
    raise SystemExit("app.py ou edt_memory.py introuvable. Lancez ce script depuis ~/extrateur-edt-rh/edtv7")

mem = mem_path.read_text(encoding="utf-8")
marker = "# === V7.3 CHANGE ARCHIVE ==="

if marker not in mem:
    wrapper = '''
\n# === V7.3 CHANGE ARCHIVE ===
from edt_changes import archive_new_version_changes as _archive_new_version_changes

_original_save_timetable_version_v73 = save_timetable_version


def save_timetable_version(*args, **kwargs):
    result = _original_save_timetable_version_v73(*args, **kwargs)

    if isinstance(result, dict) and result.get("status") == "created":
        try:
            result["changes"] = _archive_new_version_changes(result)
        except Exception as exc:
            result["changes_error"] = str(exc)

    return result
'''
    mem = mem.rstrip() + wrapper + "\n"
    mem_path.write_text(mem, encoding="utf-8")

app = app_path.read_text(encoding="utf-8")

import_line = "from edt_changes import changes_dataframe\n"
if import_line not in app:
    anchor = "import io\n"
    if anchor not in app:
        raise SystemExit("Import 'io' introuvable dans app.py")
    app = app.replace(anchor, anchor + import_line, 1)

report_marker = "# === V7.3 CHANGE REPORT ==="
if report_marker not in app:
    lines = app.splitlines()
    target_index = None
    for i, line in enumerate(lines):
        if "_memory_results = auto_save_uploaded_timetables(_memory_frame)" in line:
            target_index = i
            indent = line[:len(line) - len(line.lstrip())]
            break

    if target_index is None:
        raise SystemExit("Ligne _memory_results = auto_save_uploaded_timetables(...) introuvable")

    block = [
        "",
        indent + report_marker,
        indent + "for _memory_item in _memory_results:",
        indent + "    if _memory_item.get('changes_error'):",
        indent + "        st.warning('Version mémorisée, mais comparaison impossible : ' + _memory_item['changes_error'])",
        indent + "    elif _memory_item.get('status') == 'created' and _memory_item.get('changes'):",
        indent + "        _changes = _memory_item['changes']",
        indent + "        if _changes.get('baseline'):",
        indent + "            st.info(f\"🧠 V{_memory_item['version_number']} enregistrée comme version initiale.\")",
        indent + "        else:",
        indent + "            _vn = int(_memory_item['version_number'])",
        indent + "            st.markdown(f'### 🔄 Changements détectés — V{_vn - 1} → V{_vn}')",
        indent + "            _c1, _c2, _c3, _c4 = st.columns(4)",
        indent + "            _c1.metric('Identiques', int(_changes.get('unchanged_count', 0)))",
        indent + "            _c2.metric('Modifiées', int(_changes.get('modified_count', 0)))",
        indent + "            _c3.metric('Ajoutées', int(_changes.get('added_count', 0)))",
        indent + "            _c4.metric('Supprimées', int(_changes.get('removed_count', 0)))",
        indent + "            _changes_df = changes_dataframe(_changes)",
        indent + "            if not _changes_df.empty:",
        indent + "                st.dataframe(_changes_df, width='stretch', hide_index=True)",
    ]

    lines[target_index + 1:target_index + 1] = block
    app = "\n".join(lines) + "\n"

app_path.write_text(app, encoding="utf-8")
Path("VERSION").write_text("v7.3-edt-change-archive\n", encoding="utf-8")

print("✅ v7.3 appliquée")
print("✅ Changements détectés après chaque nouvelle version")
print("✅ Changements archivés dans estn.db")
print("✅ Rapport structuré affiché après upload")
