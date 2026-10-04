from pathlib import Path

stats = Path("edt_statistics_ui.py")
if not stats.exists():
    raise SystemExit(
        "edt_statistics_ui.py introuvable. Installez d'abord la v7.6 Statistiques EDT."
    )

text = stats.read_text(encoding="utf-8")

import_line = "from edt_advanced_statistics_ui import render_advanced_statistics\n"
if import_line not in text:
    anchor = "from app_config import DB_PATH\n"
    if anchor not in text:
        raise SystemExit("Import app_config introuvable dans edt_statistics_ui.py.")
    text = text.replace(anchor, anchor + import_line, 1)

marker = "# === v7.7 ADVANCED STATISTICS ==="

if marker not in text:
    anchor = (
        "    st.divider()\n"
        "    st.caption(\n"
        "        \"Conseil : utilisez « Versions actives uniquement » pour analyser l'état actuel. \"\n"
    )
    if anchor not in text:
        raise SystemExit(
            "Point d'insertion introuvable. Vérifiez que edt_statistics_ui.py correspond à la v7.6."
        )

    replacement = (
        "    # === v7.7 ADVANCED STATISTICS ===\n"
        "    st.divider()\n"
        "    render_advanced_statistics()\n\n"
        "    st.divider()\n"
        "    st.caption(\n"
        "        \"Conseil : utilisez « Versions actives uniquement » pour analyser l'état actuel. \"\n"
    )
    text = text.replace(anchor, replacement, 1)

stats.write_text(text, encoding="utf-8")
Path("VERSION").write_text("v7.7-advanced-statistical-analytics\n", encoding="utf-8")

print("✅ v7.7 appliquée")
print("✅ Heatmap jour × horaire")
print("✅ Boxplot + détection IQR des charges atypiques")
print("✅ Analyse de Pareto 80/20")
print("✅ Carte de contrôle 3σ des changements")
print("✅ Indice de stabilité des versions")
print("✅ Score de complétude des données")
print("✅ Insights automatiques déterministes")
