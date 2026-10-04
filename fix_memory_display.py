from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

old = '''if not timetable_files:
    st.info("Ajoutez au moins un emploi du temps dans la barre latérale.")
    st.stop()
'''

new = '''if not timetable_files:
    st.subheader("🧠 Emplois du temps mémorisés")

    try:
        ensure_edt_memory_db()
        memory_df = list_memory()

        if memory_df.empty:
            st.info("Aucun emploi du temps n'est encore mémorisé.")
        else:
            st.dataframe(
                memory_df,
                use_container_width=True,
                hide_index=True,
            )

            memory_options = {}

            for _, row in memory_df.iterrows():
                label = (
                    f'{row["Année universitaire"]} | '
                    f'{row["Période"]} | '
                    f'{row["Filière"]} | '
                    f'{row["Niveau"]}'
                )
                memory_options[label] = int(row["id"])

            selected_memory = st.selectbox(
                "Consulter l'historique d'un emploi",
                list(memory_options.keys()),
            )

            timetable_id = memory_options[selected_memory]

            versions_df = list_versions(timetable_id)

            st.markdown("#### Versions disponibles")

            st.dataframe(
                versions_df,
                use_container_width=True,
                hide_index=True,
            )

    except Exception as exc:
        st.warning(f"Mémoire EDT indisponible : {exc}")

    st.divider()

    st.info(
        "Pour importer un nouvel emploi ou créer automatiquement une nouvelle "
        "version, ajoutez un fichier PDF ou Word dans la barre latérale."
    )

    st.stop()
'''

if old not in text:
    raise SystemExit(
        "Bloc original introuvable. app.py n'a peut-être plus exactement cette structure."
    )

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")

print("✅ Affichage permanent de la mémoire EDT activé")
