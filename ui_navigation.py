"""Native Streamlit navigation for the existing laboratory modules."""
import streamlit as st


HOME = "🏠 Accueil"
TIMETABLES = "📅 Emplois du temps"
MODULES = (
    HOME,
    TIMETABLES,
    "✅ Vérification globale",
    "🔎 Recherche globale",
    "📊 Statistiques EDT",
    "🗂️ Historique EDT",
    "👥 Ressources humaines",
    "☁️ Google Drive",
)

HISTORY_SESSION_INTENT_KEY = "history_session_open_intent"
HISTORY_SESSION_FOCUS_KEY = "history_session_focus"


def open_module(module):
    # Callbacks run before the radio is instantiated on the next rerun.
    st.session_state["main_module"] = module


def open_history_session(timetable_id, version_id, session_id):
    """Queue one read-only session target, then switch to History."""
    st.session_state[HISTORY_SESSION_INTENT_KEY] = {
        "timetable_id": int(timetable_id),
        "version_id": int(version_id),
        "session_id": int(session_id),
    }
    open_module(MODULES[5])


def render_navigation():
    st.sidebar.title("EDT / RH")
    st.sidebar.caption("Laboratoire · gestion des emplois du temps")
    module = st.sidebar.radio("Navigation", MODULES, key="main_module")
    st.sidebar.caption("Stockage local · Google Drive désactivé")
    st.sidebar.divider()
    return module


def render_home():
    st.caption("ESPACE DE TRAVAIL")
    st.title("Vos emplois du temps, au même endroit")
    st.markdown(
        "Importez vos documents, vérifiez les séances et retrouvez votre travail. "
        "Choisissez une étape pour commencer."
    )
    st.info(
        "Les données sont conservées dans la base locale de ce laboratoire. "
        "Google Drive est désactivé : aucune sauvegarde distante n'est effectuée."
    )
    st.subheader("Préparer et vérifier")
    cards = (
        (TIMETABLES, "1 · Importer et corriger", "Ajoutez des PDF ou Word, corrigez les séances puis exportez en Excel.", "Ouvrir les emplois du temps"),
        (MODULES[2], "2 · Vérifier les séances", "Consultez les séances mémorisées et leur état de vérification.", "Ouvrir la vérification"),
    )
    _render_cards(cards)
    st.subheader("Consulter et suivre")
    _render_cards((
        (MODULES[3], "Rechercher", "Retrouvez les séances dans les emplois du temps mémorisés.", "Ouvrir la recherche"),
        (MODULES[4], "Analyser", "Consultez les statistiques calculées à partir de vos données EDT.", "Ouvrir les statistiques"),
    ))
    _render_cards((
        (MODULES[5], "Retrouver les versions", "Consultez l'historique des emplois et les versions enregistrées.", "Ouvrir l'historique"),
        (MODULES[6], "Ressources humaines", "Accédez au module de gestion des ressources humaines existant.", "Ouvrir les ressources humaines"),
    ))
    st.divider()
    st.caption(
        "Premier import ? Ouvrez « Emplois du temps », puis ajoutez vos fichiers "
        "dans « Fichiers et options d’import » à gauche. "
        "Vous pouvez revenir à cet accueil depuis la navigation."
    )


def _render_cards(cards):
    for column, (module, title, description, label) in zip(st.columns(2), cards):
        with column:
            with st.container(border=True):
                st.markdown(f"### {title}")
                st.write(description)
                st.button(
                    label,
                    key=f"home_{module}",
                    use_container_width=True,
                    on_click=open_module,
                    args=(module,),
                )
