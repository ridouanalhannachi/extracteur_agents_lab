import json
import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd
import streamlit as st
from gdrive_sync import auto_upload_after_change

from rh_manager import (
    PRIORITY_COLUMNS,
    DB_PATH,
    deduplicate_preview,
    delete_teacher,
    export_teachers_excel,
    extract_rh_file,
    find_possible_duplicates,
    learn_column_mapping,
    load_conflicts,
    load_conflict_rules,
    delete_conflict_rule,
    load_fragments,
    load_teacher_history,
    load_teachers,
    load_unknown_headers,
    preview_tabular_file,
    resolve_conflict,
    save_teachers,
)

RH_FIELDS_FOR_MAPPING = PRIORITY_COLUMNS + ["Nom complet", "Ignorer"]


PRIMARY_PROFILE_FIELDS = [
    "Statut", "Nom", "Prénom", "Email", "Téléphone", "Diplôme", "Spécialité", "Département"
]
SECONDARY_META_FIELDS = ["Source document", "Feuille/Section", "Date import", "Date MAJ"]


def _search_norm(value):
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9@+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _initials(value):
    tokens = [x for x in _search_norm(value).split() if x]
    return "".join(x[0] for x in tokens)


def _consonant_key(value):
    text = _search_norm(value).replace(" ", "")
    return "".join(ch for ch in text if ch.isalpha() and ch not in "aeiouy")


def _teacher_search_score(row, query):
    q = _search_norm(query)
    if not q:
        return 0.0

    nom = _search_norm(row.get("Nom", ""))
    prenom = _search_norm(row.get("Prénom", ""))
    full = f"{nom} {prenom}".strip()
    reverse = f"{prenom} {nom}".strip()
    email = _search_norm(row.get("Email", ""))
    tel = _search_norm(row.get("Téléphone", ""))
    tokens = [x for x in (nom + " " + prenom).split() if x]

    if q == email or q == tel:
        return 100.0
    if any(t.startswith(q) for t in tokens):
        return 98.0
    if full.startswith(q) or reverse.startswith(q):
        return 96.0

    q_tokens = q.split()
    if len(q_tokens) > 1 and all(any(t.startswith(part) for t in tokens) for part in q_tokens):
        return 94.0

    initials = _initials(full)
    if initials and initials.startswith(q.replace(" ", "")):
        return 91.0

    if q in full or q in reverse:
        return 88.0
    if q in email or q in tel:
        return 86.0

    # Recherche tolérante aux premières consonnes : "dd" peut retrouver DAOUDI Said,
    # tout en laissant fonctionner normalement les voyelles et débuts de mots.
    q_cons = _consonant_key(q)
    name_cons = _consonant_key(full)
    if len(q_cons) >= 2 and name_cons.startswith(q_cons):
        return 82.0

    ratio = max(
        SequenceMatcher(None, q, nom).ratio() if nom else 0.0,
        SequenceMatcher(None, q, prenom).ratio() if prenom else 0.0,
        SequenceMatcher(None, q, full).ratio() if full else 0.0,
    )
    if len(q) >= 3 and ratio >= 0.68:
        return 60.0 + ratio * 20.0
    return 0.0


def _search_teachers(base, query, limit=20):
    if base.empty or not str(query or "").strip():
        return pd.DataFrame()
    scored = []
    for _, row in base.iterrows():
        score = _teacher_search_score(row, query)
        if score > 0:
            item = row.to_dict()
            item["_score"] = score
            scored.append(item)
    if not scored:
        return pd.DataFrame()
    return pd.DataFrame(scored).sort_values(["_score", "Nom", "Prénom"], ascending=[False, True, True]).head(limit)


def _parse_secondary_info(value):
    raw = str(value or "").strip()
    if not raw or raw in {"{}", "nan", "None"}:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items()}
    except Exception:
        pass
    return {"Informations complémentaires": raw}


def _render_teacher_profile(row):
    st.markdown("#### 👤 Informations principales")
    values = {field: row.get(field, "") for field in PRIMARY_PROFILE_FIELDS}
    left, right = st.columns(2)
    for idx, field in enumerate(PRIMARY_PROFILE_FIELDS):
        value = values.get(field, "")
        value = "Non précisé" if pd.isna(value) or not str(value).strip() else str(value)
        target = left if idx % 2 == 0 else right
        target.markdown(f"**{field} :** {value}")

    st.markdown("#### 🧩 Informations secondaires")
    secondary = _parse_secondary_info(row.get("Autres informations", ""))
    for field in SECONDARY_META_FIELDS:
        value = row.get(field, "")
        if not pd.isna(value) and str(value).strip():
            secondary[field] = value
    if secondary:
        sec_df = pd.DataFrame([{"Information": k, "Valeur": v} for k, v in secondary.items()])
        st.dataframe(sec_df, hide_index=True, width="stretch")
    else:
        st.info("Aucune information secondaire enregistrée pour cette fiche.")


def render_rh_module():
    st.title("👥 Ressources humaines — Enseignants")
    flash = st.session_state.pop("rh_flash", None)
    if flash:
        st.success(flash)
    st.caption(
        "Import multi-format robuste avec mémoire permanente. L'application extrait en priorité "
        "Statut, Nom, Prénom, Email, Téléphone, Diplôme, Spécialité et Département. "
        "Les autres informations sont conservées, les colonnes inconnues peuvent être apprises, "
        "et les valeurs contradictoires sont envoyées dans un gestionnaire de conflits au lieu d'être écrasées."
    )
    st.info(f"🧠 Mémoire RH permanente : {DB_PATH}")

    files = st.file_uploader(
        "Fichiers RH",
        type=["xlsx", "xls", "xlsm", "ods", "csv", "tsv", "json", "docx", "pdf", "txt", "md",
              "png", "jpg", "jpeg", "tif", "tiff", "bmp", "webp"],
        accept_multiple_files=True,
        key="rh_files",
        help="Les fichiers peuvent être incomplets et ne doivent pas contenir tous les champs."
    )

    extracted, warnings = [], []
    per_file = []
    if files:
        for f in files:
            rows, warns = extract_rh_file(f.getvalue(), f.name)
            extracted.extend(rows)
            warnings.extend(warns)
            per_file.append((f.name, len(rows)))
        st.success(f"{len(files)} fichier(s) reçu(s). Analyse automatique terminée.")
        for name, count in per_file:
            if count:
                st.success(f"✅ {name} : {count} fiche(s) ou fragment(s) RH détecté(s).")
            else:
                st.warning(f"⚠️ {name} : 0 fiche RH détectée automatiquement.")

    if warnings:
        with st.expander("⚠️ Vérifications / fichiers partiellement lus", expanded=True):
            for warning in warnings:
                st.warning(warning)

    if files and not extracted:
        st.warning("Les fichiers sont chargés mais aucune fiche n'a été reconnue. Utilisez la section « Mémoire des colonnes » ci-dessous si les intitulés sont personnalisés.")
        first = files[0]
        preview = preview_tabular_file(first.getvalue(), first.name)
        if not preview.empty:
            st.markdown("#### 🔎 Aperçu brut du premier fichier")
            st.dataframe(preview, hide_index=True, width="stretch")

    if extracted:
        df = deduplicate_preview(pd.DataFrame(extracted))
        ordered = PRIORITY_COLUMNS + ["Autres informations", "Source document", "Feuille/Section"]
        for col in ordered:
            if col not in df.columns:
                df[col] = ""
        df = df[ordered]

        st.subheader("🧾 Aperçu détecté avant enregistrement")
        st.caption(
            "Aucun champ métier n'est obligatoire. Corrigez si nécessaire. Les données déjà présentes dans la base "
            "ne seront jamais écrasées silencieusement : une contradiction créera un conflit à résoudre."
        )
        edited = st.data_editor(
            df,
            hide_index=True,
            num_rows="dynamic",
            width="stretch",
            key="rh_editor",
            column_config={
                "Statut": st.column_config.SelectboxColumn("Statut", options=["Permanent", "Vacataire", "Non précisé"]),
                "Autres informations": st.column_config.TextColumn("Autres informations", help="Tous les champs supplémentaires sont conservés ici."),
            },
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Fichiers importés", len(files))
        c2.metric("Fiches/Fragments détectés", len(edited))
        c3.metric("Départements détectés", edited["Département"].replace("", pd.NA).dropna().nunique())

        if st.button("💾 Enregistrer / enrichir la mémoire RH", type="primary", width="stretch"):
            inserted, updated, pending, conflicts = save_teachers(edited)
            st.success(
                f"Mémoire RH mise à jour : {inserted} nouvelle(s) fiche(s), {updated} fiche(s) enrichie(s), "
                f"{pending} fragment(s) non rattaché(s), {conflicts} conflit(s) créé(s)."
            )
            synced, sync_msg = auto_upload_after_change()
            if synced:
                st.caption("☁️ " + sync_msg)
            if conflicts:
                st.warning("Des informations contradictoires ont été détectées. Ouvrez « Gestion des conflits » ci-dessous.")

    st.divider()
    st.subheader("🧠 Mémoire des colonnes")
    st.caption(
        "Quand un nouveau fichier utilise un intitulé inconnu, vous l'associez une seule fois. "
        "Cette correspondance est mémorisée dans SQLite et réutilisée automatiquement lors des prochains imports."
    )
    unknown = load_unknown_headers()
    if unknown.empty:
        st.info("Aucune colonne inconnue en attente d'apprentissage.")
    else:
        st.dataframe(unknown, hide_index=True, width="stretch")
        labels = unknown["Colonne source"].tolist()
        c1, c2, c3 = st.columns([2, 2, 1])
        header = c1.selectbox("Colonne à apprendre", labels, key="rh_unknown_header")
        target = c2.selectbox("Correspond à", RH_FIELDS_FOR_MAPPING, key="rh_mapping_target")
        if c3.button("🧠 Mémoriser", width="stretch"):
            learn_column_mapping(header, target)
            auto_upload_after_change()
            st.session_state["rh_flash"] = f"Correspondance mémorisée : « {header} » → « {target} »."
            st.rerun()

    st.divider()
    st.subheader("⚖️ Gestion des conflits RH")
    st.caption(
        "Chaque décision est mémorisée pour cet enseignant, ce champ et cette paire de valeurs. "
        "Si exactement le même conflit réapparaît plus tard, l'application applique automatiquement "
        "la décision déjà prise et ne vous repose pas la question."
    )
    conflicts = load_conflicts("open")
    if conflicts.empty:
        st.success("Aucun conflit RH non résolu.")
    else:
        st.warning(f"{len(conflicts)} conflit(s) à examiner. Aucune valeur existante n'a été écrasée automatiquement.")
        for row in conflicts.itertuples(index=False):
            cid = int(row.id)
            with st.expander(f"Conflit #{cid} — {row.Enseignant} — {row.Champ}", expanded=False):
                st.write(f"**Valeur actuelle :** {getattr(row, '_4') if False else row[4]}")
                st.write(f"**Nouvelle valeur :** {row[5]}")
                st.write(f"**Source :** {row.Source}")
                decision = st.radio(
                    "Décision",
                    ["Conserver la valeur actuelle", "Adopter la nouvelle valeur", "Conserver actuelle + archiver la nouvelle"],
                    key=f"conflict_decision_{cid}",
                )
                if st.button("Résoudre ce conflit", key=f"resolve_conflict_{cid}"):
                    code = {
                        "Conserver la valeur actuelle": "actuelle",
                        "Adopter la nouvelle valeur": "nouvelle",
                        "Conserver actuelle + archiver la nouvelle": "les_deux",
                    }[decision]
                    resolve_conflict(cid, code)
                    auto_upload_after_change()
                    st.session_state["rh_flash"] = (
                        f"Conflit #{cid} résolu. La décision a été mémorisée : "
                        "si le même conflit réapparaît, il sera résolu automatiquement."
                    )
                    st.rerun()

    with st.expander("🧠 Décisions de conflit mémorisées", expanded=False):
        rules = load_conflict_rules()
        if rules.empty:
            st.info("Aucune règle de résolution mémorisée pour le moment.")
        else:
            st.caption(
                "Ces règles sont appliquées automatiquement uniquement au même enseignant, "
                "au même champ et à la même paire de valeurs. Vous pouvez oublier une règle si nécessaire."
            )
            st.dataframe(rules, hide_index=True, width="stretch")
            rule_options = {
                f"#{int(r['id'])} — {r['Enseignant']} — {r['Champ']} : {r['Valeur A']} ↔ {r['Valeur B']}": int(r['id'])
                for _, r in rules.iterrows()
            }
            selected_rule_label = st.selectbox(
                "Règle à oublier", list(rule_options.keys()), key="rh_rule_to_forget"
            )
            if st.button("🗑️ Oublier cette règle", key="rh_forget_conflict_rule"):
                delete_conflict_rule(rule_options[selected_rule_label])
                auto_upload_after_change()
                st.session_state["rh_flash"] = "Règle de résolution oubliée. Un futur conflit identique sera de nouveau demandé."
                st.rerun()

    st.divider()
    st.subheader("📚 Base RH locale")
    base = load_teachers()
    if base.empty:
        st.info("La base RH est vide pour le moment.")
    else:
        st.markdown("### 🔎 Rechercher un enseignant")
        teacher_query = st.text_input(
            "Nom ou début du nom/prénom",
            placeholder="Ex. D, Da, DAO, Said, DS, email ou téléphone…",
            key="rh_teacher_search",
            help="La recherche commence dès les premières lettres, qu'il s'agisse de consonnes ou de voyelles. Elle accepte aussi les initiales et de petites variations d'écriture.",
        )
        matches = _search_teachers(base, teacher_query)
        if teacher_query.strip():
            if matches.empty:
                st.warning("Aucun enseignant correspondant trouvé.")
            else:
                options = {}
                for _, r in matches.iterrows():
                    label = f"{str(r.get('Nom','')).strip()} {str(r.get('Prénom','')).strip()}".strip()
                    email = str(r.get('Email', '') or '').strip()
                    dept = str(r.get('Département', '') or '').strip()
                    suffix = " — ".join(x for x in [email, dept] if x)
                    if suffix:
                        label = f"{label} — {suffix}"
                    options[f"#{int(r['id'])} — {label}"] = int(r["id"])
                selected_label = st.selectbox(
                    f"Résultats ({len(matches)})",
                    list(options.keys()),
                    key="rh_teacher_search_result",
                )
                selected_id = options[selected_label]
                selected = base[base["id"] == selected_id].iloc[0].to_dict()
                _render_teacher_profile(selected)

                hist = load_teacher_history(selected_id)
                with st.expander("🕘 Historique de cette fiche"):
                    if hist.empty:
                        st.info("Aucun historique enregistré.")
                    else:
                        st.dataframe(hist, hide_index=True, width="stretch")

        st.markdown("### 📋 Liste et filtres")
        f1, f2, f3 = st.columns(3)
        status_values = ["Tous"] + sorted(x for x in base["Statut"].fillna("").unique() if str(x).strip())
        dept_values = ["Tous"] + sorted(x for x in base["Département"].fillna("").unique() if str(x).strip())
        selected_status = f1.selectbox("Statut", status_values, key="rh_filter_status")
        selected_dept = f2.selectbox("Département", dept_values, key="rh_filter_dept")
        search = f3.text_input("Filtrer la liste", placeholder="Email, spécialité, autre information...", key="rh_search")

        filtered = base.copy()
        if selected_status != "Tous":
            filtered = filtered[filtered["Statut"] == selected_status]
        if selected_dept != "Tous":
            filtered = filtered[filtered["Département"] == selected_dept]
        if search.strip():
            needle = _search_norm(search)
            def _row_contains(row):
                return any(needle in _search_norm(v) for v in row.values if str(v).strip())
            filtered = filtered[filtered.apply(_row_contains, axis=1)]

        st.dataframe(filtered, hide_index=True, width="stretch")

        c1, c2 = st.columns(2)
        c1.download_button(
            "⬇️ Exporter la base RH en Excel",
            data=export_teachers_excel(filtered),
            file_name="Base_RH_Enseignants.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
        c2.download_button(
            "⬇️ Exporter en CSV",
            data=filtered.to_csv(index=False, sep=";").encode("utf-8-sig"),
            file_name="Base_RH_Enseignants.csv",
            mime="text/csv",
            width="stretch",
        )

        with st.expander("🕘 Historique permanent d'une fiche"):
            choices = {
                f"#{int(row.id)} — {row.Nom} {getattr(row, 'Prénom')} ({row.Email or 'sans email'})": int(row.id)
                for row in base.itertuples(index=False)
            }
            if choices:
                label = st.selectbox("Enseignant", list(choices), key="rh_history_teacher")
                hist = load_teacher_history(choices[label])
                st.dataframe(hist, hide_index=True, width="stretch")

        dup = find_possible_duplicates()
        with st.expander("🔎 Doublons possibles"):
            if dup.empty:
                st.info("Aucun doublon proche détecté.")
            else:
                st.warning("Ces rapprochements sont seulement des suggestions ; aucune fusion automatique n'est effectuée.")
                st.dataframe(dup, hide_index=True, width="stretch")

        with st.expander("🗑️ Supprimer une fiche"):
            choices = {
                f"#{int(row.id)} — {row.Nom} {getattr(row, 'Prénom')} ({row.Email or 'sans email'})": int(row.id)
                for row in base.itertuples(index=False)
            }
            if choices:
                label = st.selectbox("Enseignant", list(choices), key="rh_delete_choice")
                if st.button("Supprimer définitivement", type="secondary"):
                    delete_teacher(choices[label])
                    auto_upload_after_change()
                    st.session_state["rh_flash"] = "Fiche supprimée et liste actualisée automatiquement."
                    st.rerun()

    fragments = load_fragments()
    with st.expander("🧩 Fragments RH non encore rattachés"):
        if fragments.empty:
            st.info("Aucun fragment non rattaché.")
        else:
            st.caption("Ces données sont conservées en permanence afin de pouvoir être rattachées plus tard.")
            st.dataframe(fragments, hide_index=True, width="stretch")
