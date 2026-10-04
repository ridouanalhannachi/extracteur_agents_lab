import re
import unicodedata
import pandas as pd


def _key(value):
    s = str(value or "").strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"^(?:PROF|PR|DR)\.?\s*", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _time_range(value):
    s = str(value or "").lower().replace(" ", "")
    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    m = re.search(r"(\d{1,2})(?:[h:.](\d{0,2}))?-(\d{1,2})(?:[h:.](\d{0,2}))?", s)
    if not m:
        return None
    h1, m1 = int(m.group(1)), int(m.group(2) or 0)
    h2, m2 = int(m.group(3)), int(m.group(4) or 0)
    start, end = h1 * 60 + m1, h2 * 60 + m2
    return (start, end) if end > start else None


def _overlap(a, b):
    return a[0] < b[1] and b[0] < a[1]


def detect_conflicts(details_df: pd.DataFrame):
    columns = [
        "Type de conflit", "Ressource", "Jour", "Horaire",
        "Séance 1", "Séance 2", "Statut",
    ]
    if details_df is None or details_df.empty:
        return pd.DataFrame(columns=columns)

    rows = details_df.fillna("").to_dict("records")
    conflicts = []

    for i, a in enumerate(rows):
        ta = _time_range(a.get("Horaire"))
        if not ta:
            continue
        for b in rows[i + 1:]:
            if _key(a.get("Jour")) != _key(b.get("Jour")):
                continue
            tb = _time_range(b.get("Horaire"))
            if not tb or not _overlap(ta, tb):
                continue

            same_session = all(
                _key(a.get(k)) == _key(b.get(k))
                for k in ("Matière", "Nom et prénom", "Salle", "Horaire")
            )
            if same_session:
                continue

            s1 = f"{a.get('Filière','')} {a.get('Niveau','')} – {a.get('Matière','')} ({a.get('Horaire','')})"
            s2 = f"{b.get('Filière','')} {b.get('Niveau','')} – {b.get('Matière','')} ({b.get('Horaire','')})"
            combined = f"{max(ta[0], tb[0])//60:02d}h{max(ta[0], tb[0])%60:02d}–{min(ta[1], tb[1])//60:02d}h{min(ta[1], tb[1])%60:02d}"

            teacher_a, teacher_b = _key(a.get("Nom et prénom")), _key(b.get("Nom et prénom"))
            if teacher_a and teacher_b and teacher_a not in {"-", "—", "A COMPLETER", "NON PRECISE"} and teacher_a == teacher_b:
                conflicts.append({
                    "Type de conflit": "Professeur", "Ressource": a.get("Nom et prénom", ""),
                    "Jour": a.get("Jour", ""), "Horaire": combined,
                    "Séance 1": s1, "Séance 2": s2, "Statut": "À vérifier",
                })

            room_a, room_b = _key(a.get("Salle")), _key(b.get("Salle"))
            if room_a and room_b and room_a not in {"-", "—", "NON PRECISE"} and room_a == room_b:
                conflicts.append({
                    "Type de conflit": "Salle", "Ressource": a.get("Salle", ""),
                    "Jour": a.get("Jour", ""), "Horaire": combined,
                    "Séance 1": s1, "Séance 2": s2, "Statut": "À vérifier",
                })

    return pd.DataFrame(conflicts, columns=columns).drop_duplicates()
