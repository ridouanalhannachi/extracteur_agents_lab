from pathlib import Path

p = Path("app.py")
if not p.exists():
    raise SystemExit("app.py introuvable. Lance ce script depuis ~/extrateur-edt-rh/edtv7")

s = p.read_text(encoding="utf-8")

anchor = "from drive_ui import render_drive_module\n"
imports = """from drive_ui import render_drive_module
from gdrive_sync import auto_upload_after_change
from edt_memory import ensure_edt_memory_db, save_version, list_memory, list_versions
"""
if "from edt_memory import" not in s:
    if anchor not in s:
        raise SystemExit("Import drive_ui introuvable")
    s = s.replace(anchor, imports, 1)

old_tabs = 'tab1, tab2, tab3 = st.tabs(["Liste des enseignants intervenants", "Séances détaillées", "🤖 Assistant IA"])'
new_tabs = 'tab1, tab2, tab3, tab4 = st.tabs(["Liste des enseignants intervenants", "Séances détaillées", "🤖 Assistant IA", "🧠 Mémoire / Versions"])'
if old_tabs in s:
    s = s.replace(old_tabs, new_tabs, 1)
elif new_tabs not in s:
    raise SystemExit("Déclaration des onglets introuvable")

marker = "\nst.divider()\nst.caption(\n"
block = r'''
with tab4:
    st.subheader("🧠 Mémoire des emplois du temps")
    st.caption("Chaque nouvel emploi différent devient V1, V2, V3... L'ancienne version reste conservée.")

    ensure_edt_memory_db()
    mem_details = details.fillna("").copy()

    pairs = []
    if not mem_details.empty:
        pairs = [
            (str(f).strip(), str(n).strip())
            for f, n in mem_details[["Filière", "Niveau"]].drop_duplicates().itertuples(index=False, name=None)
            if str(f).strip() or str(n).strip()
        ]

    if pairs:
        labels = [f"{f or 'Non précisé'} — {n or 'Non précisé'}" for f, n in pairs]
        selected = st.selectbox("Emploi à mémoriser", labels, key="edt_mem_pair")
        filiere, niveau = pairs[labels.index(selected)]
        subset = mem_details[
            (mem_details["Filière"].astype(str).str.strip() == filiere)
            & (mem_details["Niveau"].astype(str).str.strip() == niveau)
        ].copy()

        years = [str(x).strip() for x in subset.get("Année universitaire", pd.Series(dtype=str)).tolist() if str(x).strip()]
        default_year = years[0] if years else "2026-2027"

        c1m, c2m = st.columns(2)
        academic_year = c1m.text_input("Année universitaire", value=default_year, key="edt_mem_year")
        period = c2m.selectbox("Période", ["Automne", "Printemps"], key="edt_mem_period")
        comment = st.text_input("Commentaire de version (optionnel)", key="edt_mem_comment")

        st.caption(f"{len(subset)} séance(s) seront mémorisées pour {filiere} {niveau}.")
        if st.button("💾 Enregistrer comme nouvelle version", use_container_width=True, key="edt_mem_save"):
            try:
                result = save_version(subset, academic_year, period, filiere, niveau, comment)
                if result["status"] == "duplicate":
                    st.info(f"Cette version existe déjà : V{result['version']}.")
                else:
                    ok_sync, msg_sync = auto_upload_after_change()
                    st.success(f"Version V{result['version']} enregistrée et définie comme active.")
                    if ok_sync:
                        st.success(msg_sync)
                    else:
                        st.warning(msg_sync)
                    st.rerun()
            except Exception as exc:
                st.error(f"Enregistrement impossible : {exc}")
    else:
        st.info("Aucune Filière / Niveau n'est disponible dans les séances affichées.")

    st.markdown("#### Historique")
    memory = list_memory()
    if memory.empty:
        st.info("Aucun emploi du temps n'est encore mémorisé.")
    else:
        st.dataframe(memory, use_container_width=True, hide_index=True)
        opts = {}
        for _, row in memory.iterrows():
            label = f'{row["Année universitaire"]} | {row["Période"]} | {row["Filière"]} | {row["Niveau"]}'
            opts[label] = int(row["id"])
        chosen = st.selectbox("Voir les versions", list(opts.keys()), key="edt_mem_history")
        st.dataframe(list_versions(opts[chosen]), use_container_width=True, hide_index=True)

'''
if "with tab4:" not in s:
    if marker not in s:
        raise SystemExit("Point d'insertion mémoire introuvable")
    s = s.replace(marker, "\n" + block + marker, 1)

p.write_text(s, encoding="utf-8")
Path("VERSION").write_text("v7.2-edt-memory\n", encoding="utf-8")
print("✅ v7.2 appliquée : mémoire EDT + versions")
