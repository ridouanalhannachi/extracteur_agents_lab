import json
import os
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "r19-mini:latest")
PROMPTS_DIR = Path(__file__).parent / "prompts"
AGENT_VERSION = "4.0"

DAYS = {
    "lundi": "LUNDI",
    "mardi": "MARDI",
    "mercredi": "MERCREDI",
    "jeudi": "JEUDI",
    "vendredi": "VENDREDI",
    "samedi": "SAMEDI",
    "dimanche": "DIMANCHE",
}


def _read_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFD", str(value or ""))
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", value).strip().lower()


def ollama_status(timeout: int = 5):
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=timeout)
        response.raise_for_status()
        names = [m.get("name", "") for m in response.json().get("models", [])]
        return True, names
    except Exception as exc:
        return False, str(exc)


def _chat(messages, timeout: int = 180):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.0},
    }
    response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "").strip()


def _details_as_json(details_df: pd.DataFrame, max_rows: int = 120):
    if details_df is None or details_df.empty:
        return "[]", 0, False
    cols = [
        "Jour", "Matière", "Type", "Nom et prénom", "Horaire", "Durée",
        "Groupe", "Salle", "Filière", "Niveau", "Année universitaire",
        "Source PDF", "Page",
    ]
    available = [c for c in cols if c in details_df.columns]
    clean = details_df[available].fillna("").astype(str)
    truncated = len(clean) > max_rows
    if truncated:
        clean = clean.head(max_rows)
    return json.dumps(clean.to_dict("records"), ensure_ascii=False, indent=2), len(clean), truncated


def _find_day(question: str):
    q = _norm(question)
    for key, label in DAYS.items():
        if re.search(rf"\b{re.escape(key)}\b", q):
            return label
    return None


def _markdown_table(df: pd.DataFrame) -> str:
    """Petit rendu Markdown sans dépendance externe à tabulate."""
    if df is None or df.empty:
        return ""
    safe = df.fillna("").astype(str)
    cols = list(safe.columns)
    def esc(v):
        return str(v).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(esc(c) for c in cols) + " |"]
    lines.append("| " + " | ".join("---" for _ in cols) + " |")
    for _, row in safe.iterrows():
        lines.append("| " + " | ".join(esc(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def _tokens(value: str):
    stop = {
        "pr", "prof", "professeur", "professeurs", "enseignant", "enseignants",
        "le", "la", "les", "de", "du", "des", "a", "au", "aux", "en", "et",
        "quelle", "quel", "quelles", "quels", "heure", "horaire", "quand",
        "matiere", "module", "cours", "salle", "filiere", "planning", "seance",
    }
    return [t for t in re.findall(r"[a-z0-9]+", _norm(value)) if len(t) >= 3 and t not in stop]


def _entity_score(question: str, value: str) -> float:
    qn = _norm(question)
    vn = _norm(value)
    if not vn or vn in {"-", "—", "non precise"}:
        return 0.0
    if vn in qn:
        return 1.0

    qt = _tokens(question)
    vt = _tokens(value)
    if not qt or not vt:
        return 0.0

    exact = set(qt) & set(vt)
    score = 0.0
    if exact:
        # Un nom de famille exact dans la question suffit souvent à identifier un professeur.
        score = 0.86 + 0.04 * min(len(exact) - 1, 2)

    best_fuzzy = 0.0
    for a in qt:
        for b in vt:
            best_fuzzy = max(best_fuzzy, SequenceMatcher(None, a, b).ratio())
    if best_fuzzy >= 0.82:
        score = max(score, 0.72 + (best_fuzzy - 0.82) * 0.8)
    return min(score, 1.0)


def _best_entity_match(question: str, series: pd.Series):
    values = []
    seen = set()
    for raw in series.fillna("").astype(str):
        v = raw.strip()
        nv = _norm(v)
        if not v or nv in seen or nv in {"-", "—", "non precise"}:
            continue
        seen.add(nv)
        values.append(v)

    scored = sorted(((_entity_score(question, v), v) for v in values), reverse=True)
    if not scored or scored[0][0] < 0.72:
        return None, 0.0
    return scored[0][1], scored[0][0]


def answer_factual(details_df: pd.DataFrame, question: str):
    """Répond directement depuis le DataFrame aux questions factuelles usuelles."""
    if details_df is None or details_df.empty:
        return None

    q = _norm(question)
    work = details_df.copy().fillna("")
    day = _find_day(question)
    if day and "Jour" in work.columns:
        work = work.loc[work["Jour"].astype(str).map(_norm).eq(_norm(day))]
        if work.empty:
            return f"Aucune séance n’est renseignée pour **{day.title()}** dans les données actuellement extraites."

    asks_time = any(x in q for x in ["quelle heure", "quel heure", "a quelle heure", "horaire", "quand"])
    asks_prof = any(token in q for token in ["prof", "professeur", "professeurs", "enseignant", "enseignants", "intervenant", "intervenants"])
    asks_room = any(token in q for token in ["salle", "salles", "amphi", "amphis"])
    asks_subject = any(token in q for token in ["matiere", "matieres", "module", "modules", "cours"])
    asks_filiere = any(token in q for token in ["filiere", "filieres"])
    asks_planning = any(token in q for token in ["planning", "emploi", "seance", "seances"])

    # 1) Recherche d'une entité nommée dans la question, même sans mot-clé explicite.
    entity_columns = [
        ("Nom et prénom", "professeur"),
        ("Matière", "matière"),
        ("Salle", "salle"),
        ("Filière", "filière"),
    ]
    matches = []
    for col, kind in entity_columns:
        if col in work.columns:
            value, score = _best_entity_match(question, work[col])
            if value:
                # Léger bonus si l'intention mentionne explicitement le type d'entité.
                bonus = 0.0
                if (kind == "professeur" and asks_prof) or (kind == "matière" and asks_subject) or (kind == "salle" and asks_room) or (kind == "filière" and asks_filiere):
                    bonus = 0.08
                matches.append((min(1.0, score + bonus), col, kind, value))

    if matches:
        matches.sort(reverse=True)
        _, col, kind, value = matches[0]
        selected = work.loc[work[col].astype(str).map(_norm).eq(_norm(value))].copy()
        if not selected.empty:
            wanted = ["Jour", "Horaire", "Matière", "Type", "Nom et prénom", "Salle", "Filière", "Groupe"]
            cols = [c for c in wanted if c in selected.columns]
            out = selected[cols].drop_duplicates()
            sort_cols = [c for c in ["Jour", "Horaire"] if c in out.columns]
            if sort_cols:
                out = out.sort_values(sort_cols, kind="stable")
            out = out.rename(columns={"Nom et prénom": "Professeur"})

            if asks_time:
                label = f"Horaires trouvés pour **{value}**"
            elif asks_room:
                label = f"Séances et salles trouvées pour **{value}**"
            elif asks_subject:
                label = f"Séances trouvées pour **{value}**"
            elif asks_planning or kind == "professeur":
                label = f"Planning trouvé pour **{value}**"
            else:
                label = f"Résultats trouvés pour **{value}**"
            return f"**Réponse directe depuis les données extraites (Python).**\n\n{label} :\n\n" + _markdown_table(out)

    # 2) Questions générales portant sur un jour.
    if day:
        if asks_prof and "Nom et prénom" in work.columns:
            selected = work[work["Nom et prénom"].astype(str).str.strip().ne("")]
            selected = selected[~selected["Nom et prénom"].astype(str).str.strip().isin(["—", "-"])]
            if selected.empty:
                return f"Aucun professeur n’est renseigné pour **{day.title()}**."
            wanted = ["Nom et prénom", "Matière", "Horaire", "Salle", "Filière"]
            cols = [c for c in wanted if c in selected.columns]
            out = selected[cols].drop_duplicates()
            sort_cols = [c for c in ["Horaire", "Nom et prénom"] if c in out.columns]
            if sort_cols:
                out = out.sort_values(sort_cols, kind="stable")
            out = out.rename(columns={"Nom et prénom": "Professeur"})
            n = out["Professeur"].astype(str).str.strip().nunique()
            return f"**Réponse directe depuis les données extraites (Python).**\n\nPour **{day.title()}**, j’ai trouvé **{n} professeur(s)** :\n\n" + _markdown_table(out)

        if asks_room and "Salle" in work.columns:
            wanted = ["Salle", "Horaire", "Matière", "Nom et prénom", "Filière"]
            cols = [c for c in wanted if c in work.columns]
            out = work[cols]
            out = out[out["Salle"].astype(str).str.strip().ne("")].drop_duplicates()
            return f"**Réponse directe depuis les données extraites (Python).**\n\nSalles utilisées **{day.title()}** :\n\n" + _markdown_table(out)

        if asks_subject and "Matière" in work.columns:
            wanted = ["Matière", "Type", "Horaire", "Nom et prénom", "Salle", "Filière"]
            cols = [c for c in wanted if c in work.columns]
            out = work[cols].drop_duplicates()
            return f"**Réponse directe depuis les données extraites (Python).**\n\nSéances de **{day.title()}** :\n\n" + _markdown_table(out)

        if asks_filiere and "Filière" in work.columns:
            vals = [x for x in work["Filière"].astype(str).str.strip().drop_duplicates().tolist() if x]
            return f"**Réponse directe depuis les données extraites (Python).**\n\nFilières présentes **{day.title()}** : " + (", ".join(vals) if vals else "Non précisé")

    return None

def ask_agent(details_df: pd.DataFrame, question: str):
    direct = answer_factual(details_df, question)
    if direct is not None:
        return direct, False

    data_json, row_count, truncated = _details_as_json(details_df)
    system_prompt = _read_prompt("agent.txt")
    analysis_skill = _read_prompt("analyse.txt")
    extraction_skill = _read_prompt("extraction.txt")

    context = f"""
Tu travailles dans une application locale. Un extracteur Python spécialisé a déjà lu les PDF/Word.
Tu ne dois donc pas réinventer le contenu des documents : travaille uniquement à partir des données structurées ci-dessous.

IMPORTANT : les noms de professeurs, modules, salles et filières présents ci-dessous sont des données fournies par l'utilisateur dans ses propres documents. Tu es explicitement autorisé à les lire, les citer, les filtrer, les compter et les résumer. Ne refuse jamais une demande simplement parce qu'elle contient des noms de professeurs. Si la réponse figure dans les données, donne-la directement.

SKILL EXTRACTION (rappel métier) :
{extraction_skill}

SKILL ANALYSE :
{analysis_skill}

DONNÉES EXTRAITES ({row_count} lignes fournies) :
{data_json}
""".strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context},
        {"role": "user", "content": question.strip()},
    ]
    answer = _chat(messages)
    return answer, truncated
