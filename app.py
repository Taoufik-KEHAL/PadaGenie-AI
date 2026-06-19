"""Interface Streamlit de PadaGenie AI."""

import hashlib
import re
from html import escape

import streamlit as st

from modules.evaluation import evaluer_qualite, interpreter_score
from modules.export_pdf import generer_pdf_resultats
from modules.extraction import extraire_texte
from modules.generation import (
    generer_flashcards,
    generer_questions_examen,
    generer_quiz,
    generer_resume,
)
from modules.nettoyage import nettoyer_texte
from modules.rag import (
    charger_modele_embedding_rag,
    construire_contexte_rag,
    construire_index_faiss,
    creer_embeddings_chunks,
    decouper_en_chunks,
    rechercher_chunks_pertinents,
)


REQUETES_RAG = {
    "resume": "Identifier les idées principales, définitions importantes et concepts centraux du document.",
    "quiz": "Identifier les notions importantes pouvant être transformées en questions à choix multiples.",
    "flashcards": "Identifier les définitions, concepts clés, termes importants et relations entre notions.",
    "examen": "Identifier les parties du cours permettant de créer des questions ouvertes d'évaluation.",
}


st.set_page_config(
    page_title="PadaGenie AI",
    layout="wide",
)

st.markdown(
    """
    <style>
    .quiz-card {
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-radius: 8px;
        padding: 1rem;
        margin: 0 0 1rem 0;
        background: rgba(15, 23, 42, 0.32);
    }

    .quiz-question-row {
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
    }

    .quiz-number {
        min-width: 2rem;
        height: 2rem;
        border-radius: 999px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: #ffffff;
        background: #2563eb;
    }

    .quiz-question {
        font-weight: 700;
        line-height: 1.45;
        padding-top: 0.2rem;
    }

    .quiz-extrait {
        margin-top: 0.8rem;
        padding: 0.75rem 0.85rem;
        border-left: 3px solid #2563eb;
        background: rgba(148, 163, 184, 0.10);
        color: rgba(255, 255, 255, 0.86);
        line-height: 1.5;
    }

    .quiz-options {
        display: grid;
        gap: 0.55rem;
        margin-top: 0.85rem;
    }

    .quiz-option {
        display: flex;
        gap: 0.7rem;
        align-items: flex-start;
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 8px;
        padding: 0.7rem 0.8rem;
        background: rgba(2, 6, 23, 0.26);
        line-height: 1.4;
    }

    .quiz-option-correct {
        border-color: rgba(34, 197, 94, 0.7);
        background: rgba(34, 197, 94, 0.13);
    }

    .quiz-label {
        min-width: 1.7rem;
        height: 1.7rem;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        background: rgba(148, 163, 184, 0.18);
        color: #f8fafc;
    }

    .quiz-option-correct .quiz-label {
        background: #22c55e;
        color: #052e16;
    }

    .quiz-answer {
        margin-top: 0.85rem;
        font-weight: 700;
        color: #86efac;
    }

    .quiz-explanation {
        margin-top: 0.45rem;
        color: rgba(255, 255, 255, 0.78);
        line-height: 1.45;
    }

    .quiz-feedback {
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin-top: 0.85rem;
        line-height: 1.55;
    }

    .quiz-feedback-error {
        border: 1px solid rgba(239, 68, 68, 0.22);
        background: rgba(254, 226, 226, 0.95);
        color: #b91c1c;
    }

    .quiz-feedback-success {
        border: 1px solid rgba(34, 197, 94, 0.26);
        background: rgba(220, 252, 231, 0.96);
        color: #166534;
    }

    .quiz-feedback-info {
        border: 1px solid rgba(59, 130, 246, 0.22);
        background: rgba(219, 234, 254, 0.96);
        color: #1d4ed8;
    }

    .quiz-feedback-title {
        font-weight: 800;
    }

    .resume-view {
        margin-top: 0.35rem;
        max-width: 980px;
    }

    .resume-main-title {
        font-size: 1.1rem;
        font-weight: 800;
        color: #111827;
        margin: 0.25rem 0 1rem 0;
        line-height: 1.45;
    }

    .resume-section {
        margin: 1rem 0 1.1rem 0;
        padding-left: 1rem;
        border-left: 4px solid #2563eb;
    }

    .resume-section-title {
        font-weight: 850;
        color: #1f2937;
        margin-bottom: 0.45rem;
        line-height: 1.35;
    }

    .resume-body {
        color: #374151;
        line-height: 1.72;
        font-size: 1rem;
    }

    .resume-body p {
        margin: 0.25rem 0 0.65rem 0;
    }

    .resume-body ul {
        margin: 0.35rem 0 0.7rem 1.2rem;
        padding-left: 0.4rem;
    }

    .resume-body li {
        margin-bottom: 0.35rem;
    }

    .flashcard-viewer {
        border: 1px solid rgba(148, 163, 184, 0.30);
        border-radius: 8px;
        padding: 1.25rem;
        margin: 0.8rem 0 1rem 0;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.90), rgba(39, 39, 42, 0.82));
    }

    .flashcard-topline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .flashcard-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 2.2rem;
        height: 2.2rem;
        border-radius: 999px;
        font-weight: 800;
        color: #052e16;
        background: #86efac;
    }

    .flashcard-theme {
        color: rgba(255, 255, 255, 0.68);
        font-size: 0.9rem;
        text-align: right;
    }

    .flashcard-label {
        color: #86efac;
        font-size: 0.85rem;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .flashcard-question {
        font-size: 1.2rem;
        font-weight: 750;
        line-height: 1.45;
        color: #f8fafc;
    }

    .flashcard-answer {
        margin-top: 1rem;
        padding: 0.95rem 1rem;
        border-left: 3px solid #86efac;
        border-radius: 0 8px 8px 0;
        background: rgba(34, 197, 94, 0.11);
        line-height: 1.55;
        color: rgba(255, 255, 255, 0.90);
    }

    .flashcard-hidden {
        margin-top: 1rem;
        padding: 0.95rem 1rem;
        border: 1px dashed rgba(148, 163, 184, 0.45);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.58);
        background: rgba(15, 23, 42, 0.35);
    }

    .flashcard-mini {
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 8px;
        padding: 0.85rem;
        margin-bottom: 0.75rem;
        background: rgba(2, 6, 23, 0.20);
    }

    .exam-viewer {
        border: 1px solid rgba(148, 163, 184, 0.30);
        border-radius: 8px;
        padding: 1.25rem;
        margin: 0.8rem 0 1rem 0;
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.92), rgba(30, 41, 59, 0.84));
    }

    .exam-topline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .exam-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 2.2rem;
        height: 2.2rem;
        border-radius: 8px;
        font-weight: 800;
        color: #082f49;
        background: #7dd3fc;
    }

    .exam-theme {
        color: rgba(255, 255, 255, 0.68);
        font-size: 0.9rem;
        text-align: right;
    }

    .exam-label {
        color: #7dd3fc;
        font-size: 0.85rem;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .exam-question {
        font-size: 1.18rem;
        font-weight: 750;
        line-height: 1.5;
        color: #f8fafc;
    }

    .exam-answer {
        margin-top: 1rem;
        padding: 0.95rem 1rem;
        border-left: 3px solid #7dd3fc;
        border-radius: 0 8px 8px 0;
        background: rgba(14, 165, 233, 0.12);
        line-height: 1.55;
        color: rgba(255, 255, 255, 0.90);
    }

    .exam-hidden {
        margin-top: 1rem;
        padding: 0.95rem 1rem;
        border: 1px dashed rgba(148, 163, 184, 0.45);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.58);
        background: rgba(15, 23, 42, 0.35);
    }

    .exam-mini {
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 8px;
        padding: 0.85rem;
        margin-bottom: 0.75rem;
        background: rgba(2, 6, 23, 0.20);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialiser_session():
    """Initialise les données conservées pendant l'utilisation de l'application."""
    valeurs_defaut = {
        "nom_fichier": "",
        "texte_extrait": "",
        "texte_nettoye": "",
        "chunks": [],
        "modele_embedding_rag": None,
        "index_faiss": None,
        "resume": "",
        "resume_auto_signature": "",
        "quiz": "",
        "flashcards": "",
        "questions_examen": "",
        "score_qualite": None,
        "quiz_signature": "",
        "quiz_index": 0,
        "quiz_valide": False,
        "quiz_reponses": {},
        "flashcards_signature": "",
        "flashcards_index": 0,
        "flashcards_reponse_visible": False,
        "examen_signature": "",
        "examen_index": 0,
        "examen_reponse_visible": False,
    }

    for cle, valeur in valeurs_defaut.items():
        if cle not in st.session_state:
            st.session_state[cle] = valeur


def texte_source_disponible():
    """Vérifie si un texte source exploitable est présent en session."""
    texte = st.session_state.get("texte_nettoye") or st.session_state.get("texte_extrait", "")
    if not texte.strip():
        st.warning("Veuillez d'abord importer un fichier PDF ou TXT contenant du texte.")
        return False

    if len(texte.split()) < 20:
        st.warning("Le texte extrait est trop court pour générer un support fiable.")
        return False

    return True


def reinitialiser_resultats_generation():
    """Efface les contenus générés quand un nouveau document est chargé."""
    st.session_state["resume"] = ""
    st.session_state["resume_auto_signature"] = ""
    st.session_state["quiz"] = ""
    st.session_state["flashcards"] = ""
    st.session_state["questions_examen"] = ""
    st.session_state["score_qualite"] = None
    reinitialiser_quiz_interactif()
    reinitialiser_flashcards()
    reinitialiser_questions_examen()


def indexer_document_rag(texte):
    """Crée les chunks, embeddings et l'index FAISS pour le document courant."""
    chunks = decouper_en_chunks(texte)
    if not chunks:
        raise ValueError("Aucun chunk RAG n'a pu être créé à partir du document.")

    modele_embedding = charger_modele_embedding_rag()
    embeddings = creer_embeddings_chunks(chunks)
    index_faiss = construire_index_faiss(embeddings)

    st.session_state["chunks"] = chunks
    st.session_state["modele_embedding_rag"] = modele_embedding
    st.session_state["index_faiss"] = index_faiss


def contexte_rag_pour_tache(type_support):
    """Construit le contexte RAG adapté au support demandé."""
    chunks = st.session_state.get("chunks", [])
    index_faiss = st.session_state.get("index_faiss")
    modele_embedding = st.session_state.get("modele_embedding_rag")

    if not chunks or index_faiss is None or modele_embedding is None:
        st.warning(
            "L'index RAG n'est pas disponible. La génération utilisera le texte nettoyé."
        )
        return None

    chunks_pertinents = rechercher_chunks_pertinents(
        REQUETES_RAG[type_support],
        chunks,
        index_faiss,
        modele_embedding,
        top_k=5,
    )
    return construire_contexte_rag(chunks_pertinents)


def generer_support_pedagogique(type_support, fonction_generation, configuration_modele, niveau):
    """Génère un support en utilisant le contexte RAG de la tâche."""
    texte_nettoye = st.session_state.get("texte_nettoye") or st.session_state["texte_extrait"]
    contexte_rag = contexte_rag_pour_tache(type_support)
    return fonction_generation(
        texte=texte_nettoye,
        configuration_modele=configuration_modele,
        contexte_rag=contexte_rag,
        niveau_difficulte=niveau,
    )


def configuration_generation_disponible(configuration_modele):
    """Vérifie si le moteur choisi possède les informations nécessaires."""
    type_modele = configuration_modele.get("type_modele")
    if type_modele in {"OpenAI API", "Groq API"}:
        return bool(configuration_modele.get("cle_api", "").strip())

    return type_modele == "Ollama local" and bool(configuration_modele.get("nom_modele"))


def signature_resume_automatique(configuration_modele, niveau):
    """Construit une signature pour éviter les régénérations inutiles du résumé."""
    texte = st.session_state.get("texte_nettoye") or st.session_state.get("texte_extrait", "")
    empreinte_texte = hashlib.sha1(texte.encode("utf-8")).hexdigest()
    morceaux = [
        empreinte_texte,
        configuration_modele.get("type_modele", ""),
        configuration_modele.get("nom_modele", ""),
        niveau,
        "cle" if configuration_modele.get("cle_api", "").strip() else "sans-cle",
    ]
    return "|".join(morceaux)


def generer_resume_automatique(configuration_modele, niveau):
    """Génère le résumé automatiquement dès que le document et le modèle sont prêts."""
    texte = st.session_state.get("texte_nettoye") or st.session_state.get("texte_extrait", "")
    if not texte.strip() or len(texte.split()) < 20:
        return

    if not configuration_generation_disponible(configuration_modele):
        return

    signature = signature_resume_automatique(configuration_modele, niveau)
    if st.session_state.get("resume_auto_signature") == signature:
        return

    with st.spinner("Génération automatique du résumé en cours..."):
        st.session_state["resume"] = generer_support_pedagogique(
            "resume",
            generer_resume,
            configuration_modele,
            niveau,
        )
        st.session_state["score_qualite"] = None
        st.session_state["resume_auto_signature"] = signature


def contenu_exportable_disponible():
    """Indique si au moins un résultat peut être exporté."""
    champs = ["resume", "quiz", "flashcards", "questions_examen"]
    return any(st.session_state.get(champ, "").strip() for champ in champs)


def formater_resume_affichage(contenu):
    """Place les sections principales du résumé sur des lignes dédiées."""
    if not contenu:
        return ""

    motif_section_interdite = re.compile(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?"
        r"(?:questions?|questions?\s+de\s+compréhension(?:\s+et\s+d['’]application)?|"
        r"exercices?|quiz)\b.*$",
    )
    section_interdite = motif_section_interdite.search(contenu)
    if section_interdite:
        contenu = contenu[: section_interdite.start()].rstrip()

    contenu = re.sub(
        r"(?im)(\*\*)?Conclusion\s+courte(\*\*)?",
        r"**Conclusion**",
        contenu,
    )
    contenu = re.sub(r"(?im)(\*\*Conclusion\*\*)\s+courte\*\*\s*", r"\1\n\n", contenu)
    contenu = re.sub(r"(?im)^courte\*\*\s*", "", contenu)

    titres = [
        "Idée générale",
        "Notions principales",
        "Points essentiels",
        "Conclusion",
    ]
    for titre in titres:
        contenu = re.sub(
            rf"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?{re.escape(titre)}\s*:?(?:\*\*)?[ \t]+(?=\S)",
            f"**{titre}**\n\n",
            contenu,
        )

    return contenu.strip()


def _inline_markdown_html(texte):
    """Convertit un petit fragment Markdown en HTML sûr."""
    texte = escape(str(texte).strip())
    texte = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", texte)
    texte = re.sub(r"`([^`]+)`", r"<code>\1</code>", texte)
    return texte


def _bloc_resume_html(lignes):
    """Convertit les lignes d'une section de résumé en paragraphes et listes."""
    blocs = []
    liste = []

    def fermer_liste():
        nonlocal liste
        if liste:
            elements = "".join(f"<li>{_inline_markdown_html(item)}</li>" for item in liste)
            blocs.append(f"<ul>{elements}</ul>")
            liste = []

    paragraphe = []
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne:
            fermer_liste()
            if paragraphe:
                blocs.append(f"<p>{_inline_markdown_html(' '.join(paragraphe))}</p>")
                paragraphe = []
            continue

        element_liste = re.match(r"^[-•]\s+(.+)$", ligne)
        if element_liste:
            if paragraphe:
                blocs.append(f"<p>{_inline_markdown_html(' '.join(paragraphe))}</p>")
                paragraphe = []
            liste.append(element_liste.group(1))
        else:
            fermer_liste()
            paragraphe.append(ligne)

    fermer_liste()
    if paragraphe:
        blocs.append(f"<p>{_inline_markdown_html(' '.join(paragraphe))}</p>")

    return "".join(blocs)


def _titre_section_resume(ligne):
    """Détecte un titre de section dans le résumé."""
    ligne = ligne.strip()
    ligne = re.sub(r"^#{1,6}\s*", "", ligne).strip()
    correspondance = re.fullmatch(r"\*\*(.+?)\*\*", ligne)
    if correspondance:
        return correspondance.group(1).strip(" :")

    titres = [
        "Idée générale",
        "Notions principales",
        "Points essentiels",
        "Conclusion",
    ]
    for titre in titres:
        if ligne.lower().strip(" :") == titre.lower():
            return titre

    return None


def afficher_resume(contenu, afficher_titre=True):
    """Affiche le résumé avec une mise en page structurée."""
    if afficher_titre:
        st.subheader("Résumé généré")
    if not contenu:
        st.info("Aucun contenu généré pour le moment.")
        return

    if contenu.startswith("Erreur"):
        st.error(contenu)
        return

    contenu = formater_resume_affichage(contenu)
    lignes = contenu.splitlines()
    titre_principal = ""
    sections = []
    section_courante = None

    for ligne in lignes:
        titre_section = _titre_section_resume(ligne)
        if titre_section:
            if section_courante:
                sections.append(section_courante)
            section_courante = {"titre": titre_section, "lignes": []}
            continue

        if section_courante:
            section_courante["lignes"].append(ligne)
        elif ligne.strip():
            titre_principal = ligne.strip()

    if section_courante:
        sections.append(section_courante)

    html = ['<div class="resume-view">']
    if titre_principal:
        titre_principal = re.sub(r"^#{1,6}\s*", "", titre_principal).strip()
        titre_principal = re.sub(r"^\*\*(.+?)\*\*$", r"\1", titre_principal).strip()
        html.append(f'<div class="resume-main-title">{_inline_markdown_html(titre_principal)}</div>')

    if sections:
        for section in sections:
            corps = _bloc_resume_html(section["lignes"])
            if not corps:
                continue
            html.append(
                '<section class="resume-section">'
                f'<div class="resume-section-title">{escape(section["titre"])}</div>'
                f'<div class="resume-body">{corps}</div>'
                "</section>"
            )
    else:
        html.append(f'<div class="resume-body">{_bloc_resume_html(lignes)}</div>')

    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def afficher_export_pdf(type_support):
    """Affiche un bouton d'export PDF adapté au support courant."""
    configurations = {
        "resume": {
            "champ": "resume",
            "label": "Exporter le résumé en PDF",
            "file_name": "resume_padagenie_ai.pdf",
            "payload": ("resume",),
        },
        "quiz": {
            "champ": "quiz",
            "label": "Exporter le quiz en PDF",
            "file_name": "quiz_padagenie_ai.pdf",
            "payload": ("quiz",),
        },
        "flashcards": {
            "champ": "flashcards",
            "label": "Exporter les flashcards en PDF",
            "file_name": "flashcards_padagenie_ai.pdf",
            "payload": ("flashcards",),
        },
        "examen": {
            "champ": "questions_examen",
            "label": "Exporter les questions en PDF",
            "file_name": "questions_examen_padagenie_ai.pdf",
            "payload": ("questions_examen",),
        },
    }
    configuration = configurations[type_support]
    contenu = st.session_state.get(configuration["champ"], "")
    if type_support == "resume":
        contenu = formater_resume_affichage(contenu)

    if not contenu.strip():
        st.download_button(
            label=configuration["label"],
            data=b"",
            file_name=configuration["file_name"],
            mime="application/pdf",
            disabled=True,
            key=f"bouton_export_pdf_desactive_{type_support}",
        )
        return

    try:
        donnees = {
            "resume": "",
            "quiz": "",
            "flashcards": "",
            "questions_examen": "",
        }
        donnees[configuration["payload"][0]] = contenu
        pdf_bytes = generer_pdf_resultats(
            resume=donnees["resume"],
            quiz=donnees["quiz"],
            flashcards=donnees["flashcards"],
            questions_examen=donnees["questions_examen"],
        )
        st.download_button(
            label=configuration["label"],
            data=pdf_bytes,
            file_name=configuration["file_name"],
            mime="application/pdf",
            key=f"bouton_export_pdf_{type_support}",
        )
    except Exception as erreur:
        st.error(f"Erreur pendant la génération du PDF : {erreur}")


def afficher_contenu(titre, contenu):
    """Affiche un contenu généré ou un message d'attente."""
    st.subheader(titre)
    if contenu:
        if contenu.startswith("Erreur"):
            st.error(contenu)
        elif titre == "Quiz généré":
            afficher_quiz(contenu)
        elif titre == "Flashcards générées":
            afficher_flashcards(contenu)
        elif titre == "Questions d'examen générées":
            afficher_questions_examen(contenu)
        else:
            st.markdown(contenu)
    else:
        st.info("Aucun contenu généré pour le moment.")


def reinitialiser_quiz_interactif():
    """Remet à zéro la progression du quiz interactif."""
    st.session_state["quiz_index"] = 0
    st.session_state["quiz_valide"] = False
    st.session_state["quiz_reponses"] = {}


def reinitialiser_flashcards():
    """Remet à zéro la progression des flashcards."""
    st.session_state["flashcards_index"] = 0
    st.session_state["flashcards_reponse_visible"] = False


def reinitialiser_questions_examen():
    """Remet à zéro la progression des questions d'examen."""
    st.session_state["examen_index"] = 0
    st.session_state["examen_reponse_visible"] = False


def _normaliser_quiz(contenu):
    """Ajoute des retours à la ligne autour des éléments QCM."""
    contenu = contenu.replace("\r\n", "\n").replace("\r", "\n")
    contenu = re.sub(r"\s+(?=[A-D]\.\s)", "\n", contenu)
    contenu = re.sub(r"\s+(?=Réponse correcte\s*:)", "\n", contenu, flags=re.IGNORECASE)
    contenu = re.sub(r"\s+(?=Explication\s*:)", "\n", contenu, flags=re.IGNORECASE)
    contenu = re.sub(r"\n{3,}", "\n\n", contenu)
    return contenu.strip()


def _nettoyer_option_quiz(texte):
    """Retire les fragments de correction collés accidentellement à une option."""
    texte = re.split(
        r"\s+(?:Réponse correcte|Explication)\s*:",
        str(texte),
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    texte = re.sub(r"\s+", " ", texte)
    return texte.strip(" -\n\t")


def _libelle_bonne_reponse(options, reponse):
    """Construit un libellé propre pour la réponse correcte."""
    for etiquette, valeur in options:
        if etiquette == reponse:
            valeur = _nettoyer_option_quiz(valeur)
            return f"{etiquette}. {valeur}" if valeur else etiquette

    return reponse


def _analyser_quiz(contenu):
    """Transforme le texte du quiz en questions structurées pour l'affichage."""
    contenu = _normaliser_quiz(contenu)
    blocs = re.split(r"(?m)^\s*(?=\d+\.\s+)", contenu)
    questions = []

    for bloc in blocs:
        bloc = bloc.strip()
        if not bloc:
            continue

        correspondance = re.match(r"(?s)^(\d+)\.\s*(.+)$", bloc)
        if not correspondance:
            continue

        numero = correspondance.group(1)
        reste = correspondance.group(2).strip()
        avant_options = re.split(
            r"(?m)^\s*[A-D]\.\s+|^\s*Réponse correcte\s*:|^\s*Explication\s*:",
            reste,
            maxsplit=1,
        )[0].strip()

        extrait = ""
        extrait_trouve = re.search(r"«\s*(.+?)\s*»", avant_options, flags=re.DOTALL)
        if extrait_trouve:
            extrait = re.sub(r"\s+", " ", extrait_trouve.group(1)).strip()
            question = re.sub(r"«\s*.+?\s*»", "", avant_options, flags=re.DOTALL).strip()
        else:
            question = avant_options

        question = re.sub(r"\s+", " ", question).strip()
        options = re.findall(
            r"(?ms)^\s*([A-D])\.\s*(.+?)(?=^\s*[A-D]\.\s+|^\s*Réponse correcte\s*:|^\s*Explication\s*:|\Z)",
            bloc,
        )
        options = [
            (etiquette, _nettoyer_option_quiz(valeur))
            for etiquette, valeur in options
        ]

        reponse_trouvee = re.search(
            r"Réponse correcte\s*:\s*([A-D])",
            bloc,
            flags=re.IGNORECASE,
        )
        reponse = reponse_trouvee.group(1).upper() if reponse_trouvee else ""

        explication_trouvee = re.search(
            r"(?is)Explication\s*:\s*(.+)$",
            bloc,
        )
        explication = ""
        if explication_trouvee:
            explication = re.sub(r"\s+", " ", explication_trouvee.group(1)).strip()

        if question and len(options) >= 2:
            questions.append(
                {
                    "numero": numero,
                    "question": question,
                    "extrait": extrait,
                    "options": options,
                    "reponse": reponse,
                    "explication": explication,
                }
            )

    return questions


def afficher_quiz(contenu):
    """Affiche le quiz sous forme interactive."""
    questions = _analyser_quiz(contenu)
    if not questions:
        st.markdown(contenu)
        return

    signature = hashlib.sha1(contenu.encode("utf-8")).hexdigest()
    if st.session_state.get("quiz_signature") != signature:
        st.session_state["quiz_signature"] = signature
        reinitialiser_quiz_interactif()

    total_questions = len(questions)
    index = max(st.session_state.get("quiz_index", 0), 0)

    if index >= total_questions:
        bonnes_reponses = sum(
            1
            for position, item in enumerate(questions)
            if st.session_state["quiz_reponses"].get(str(position)) == item["reponse"]
        )
        st.success("Quiz terminé.")
        st.metric("Score final", f"{bonnes_reponses}/{total_questions}")
        st.progress(bonnes_reponses / total_questions)

        if st.button("Recommencer le quiz", key=f"quiz_reset_final_{signature}"):
            reinitialiser_quiz_interactif()
            st.rerun()

        with st.expander("Afficher le corrigé complet"):
            for position, item in enumerate(questions, start=1):
                bonne_option = _libelle_bonne_reponse(
                    item["options"],
                    item["reponse"],
                )
                st.markdown(f"**{position}. {item['question']}**")
                st.markdown(f"Réponse correcte : `{bonne_option}`")
        return

    st.session_state["quiz_index"] = index
    question = questions[index]
    cle_question = str(index)
    reponses = st.session_state.get("quiz_reponses", {})
    choix_deja_fait = reponses.get(cle_question)

    st.progress((index + 1) / total_questions)
    st.caption(f"Question {index + 1} sur {total_questions}")

    st.markdown(
        (
            '<div class="quiz-card">'
            '<div class="quiz-question-row">'
            f'<span class="quiz-number">{escape(str(index + 1))}</span>'
            f'<div class="quiz-question">{escape(question["question"])}</div>'
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    if question["extrait"]:
        st.markdown(
            f'<div class="quiz-extrait">« {escape(question["extrait"])} »</div>',
            unsafe_allow_html=True,
        )

    options = [etiquette for etiquette, _ in question["options"]]
    libelles_options = {
        etiquette: f"{etiquette}. {valeur}"
        for etiquette, valeur in question["options"]
    }

    index_selection = options.index(choix_deja_fait) if choix_deja_fait in options else None
    choix = st.radio(
        "Choisissez une réponse",
        options,
        index=index_selection,
        format_func=lambda etiquette: libelles_options[etiquette],
        key=f"quiz_choix_{signature}_{index}",
        disabled=st.session_state["quiz_valide"],
    )

    colonne_valider, colonne_suivant, colonne_score = st.columns([1, 1, 2])

    with colonne_valider:
        if st.button(
            "Valider",
            key=f"quiz_valider_{signature}_{index}",
            disabled=st.session_state["quiz_valide"] or choix is None,
        ):
            st.session_state["quiz_reponses"][cle_question] = choix
            st.session_state["quiz_valide"] = True
            st.rerun()

    with colonne_suivant:
        dernier_question = index == total_questions - 1
        libelle_suivant = "Terminer" if dernier_question else "Question suivante"
        if st.button(
            libelle_suivant,
            key=f"quiz_suivant_{signature}_{index}",
            disabled=not st.session_state["quiz_valide"],
        ):
            if dernier_question:
                st.session_state["quiz_index"] = total_questions
            else:
                st.session_state["quiz_index"] = index + 1
            st.session_state["quiz_valide"] = False
            st.rerun()

    bonnes_reponses = sum(
        1
        for position, item in enumerate(questions)
        if st.session_state["quiz_reponses"].get(str(position)) == item["reponse"]
    )
    with colonne_score:
        st.metric("Score", f"{bonnes_reponses}/{total_questions}")

    if st.session_state["quiz_valide"]:
        choix_valide = st.session_state["quiz_reponses"].get(cle_question)
        if choix_valide == question["reponse"]:
            st.markdown(
                (
                    '<div class="quiz-feedback quiz-feedback-success">'
                    '<span class="quiz-feedback-title">Bonne réponse.</span>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
        else:
            bonne_option = _libelle_bonne_reponse(
                question["options"],
                question["reponse"],
            )
            st.markdown(
                (
                    '<div class="quiz-feedback quiz-feedback-error">'
                    '<span class="quiz-feedback-title">Réponse incorrecte.</span><br>'
                    f'Bonne réponse : {escape(bonne_option)}'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

        if question["explication"]:
            st.markdown(
                (
                    '<div class="quiz-feedback quiz-feedback-info">'
                    '<span class="quiz-feedback-title">Explication</span><br>'
                    f'{escape(question["explication"])}'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

    if st.button("Recommencer le quiz", key=f"quiz_reset_{signature}"):
        reinitialiser_quiz_interactif()
        st.rerun()

    with st.expander("Afficher le corrigé complet"):
        for position, item in enumerate(questions, start=1):
            bonne_option = _libelle_bonne_reponse(
                item["options"],
                item["reponse"],
            )
            st.markdown(f"**{position}. {item['question']}**")
            st.markdown(f"Réponse correcte : `{bonne_option}`")


def _nettoyer_markdown_simple(texte):
    """Retire les marqueurs Markdown simples d'un fragment de texte."""
    texte = re.sub(r"\*\*(.*?)\*\*", r"\1", texte)
    texte = re.sub(r"`([^`]*)`", r"\1", texte)
    texte = re.sub(r"\s+", " ", texte)
    return texte.strip(" -\n\t")


def _extraire_flashcard_depuis_bloc(numero, bloc):
    """Extrait la question et la réponse d'un bloc de flashcard."""
    bloc = re.sub(r"\*\*(.*?)\*\*", r"\1", bloc).strip()

    question_trouvee = re.search(
        r"(?is)Question\s*:\s*(.+?)(?=\n\s*Réponse\s*:|Réponse\s*:|\Z)",
        bloc,
    )
    reponse_trouvee = re.search(r"(?is)Réponse\s*:\s*(.+)$", bloc)

    if not question_trouvee or not reponse_trouvee:
        return None

    question = _nettoyer_markdown_simple(question_trouvee.group(1))
    reponse = _nettoyer_markdown_simple(reponse_trouvee.group(1))

    if not question or not reponse:
        return None

    return {
        "numero": numero,
        "question": question,
        "reponse": reponse,
    }


def _analyser_flashcards(contenu):
    """Transforme le texte des flashcards en cartes structurées."""
    contenu = contenu.replace("\r\n", "\n").replace("\r", "\n").strip()
    marqueurs = list(
        re.finditer(
            r"(?im)^\s*(?:#{1,6}\s*)?Flashcard\s*(\d+)\s*$",
            contenu,
        )
    )
    flashcards = []

    if marqueurs:
        for position, marqueur in enumerate(marqueurs):
            debut = marqueur.end()
            fin = marqueurs[position + 1].start() if position + 1 < len(marqueurs) else len(contenu)
            carte = _extraire_flashcard_depuis_bloc(marqueur.group(1), contenu[debut:fin])
            if carte:
                flashcards.append(carte)

    if flashcards:
        return flashcards

    # Format de secours : Question/Réponse sans titre "Flashcard".
    paires = re.findall(
        r"(?is)Question\s*:\s*(.+?)\s*Réponse\s*:\s*(.+?)(?=\n\s*Question\s*:|\Z)",
        contenu,
    )
    for index, (question, reponse) in enumerate(paires, start=1):
        question = _nettoyer_markdown_simple(question)
        reponse = _nettoyer_markdown_simple(reponse)
        if question and reponse:
            flashcards.append(
                {
                    "numero": str(index),
                    "question": question,
                    "reponse": reponse,
                }
            )

    return flashcards


def _extraire_theme_flashcard(question):
    """Retourne un thème court à partir de la question."""
    theme = re.search(r"«\s*(.+?)\s*»", question)
    if theme:
        return theme.group(1)

    mots = question.split()
    return " ".join(mots[:5]) if mots else "Révision"


def afficher_flashcards(contenu):
    """Affiche les flashcards en mode révision interactif."""
    flashcards = _analyser_flashcards(contenu)
    if not flashcards:
        st.markdown(contenu)
        return

    signature = hashlib.sha1(contenu.encode("utf-8")).hexdigest()
    if st.session_state.get("flashcards_signature") != signature:
        st.session_state["flashcards_signature"] = signature
        reinitialiser_flashcards()

    total = len(flashcards)
    index = min(max(st.session_state.get("flashcards_index", 0), 0), total - 1)
    st.session_state["flashcards_index"] = index
    carte = flashcards[index]
    reponse_visible = st.session_state.get("flashcards_reponse_visible", False)

    st.progress((index + 1) / total)
    st.caption(f"Carte {index + 1} sur {total}")

    theme = _extraire_theme_flashcard(carte["question"])
    reponse_html = ""
    if reponse_visible:
        reponse_html = (
            '<div class="flashcard-answer">'
            '<div class="flashcard-label">Réponse</div>'
            f'{escape(carte["reponse"])}'
            "</div>"
        )
    else:
        reponse_html = (
            '<div class="flashcard-hidden">'
            "La réponse est masquée. Essayez de répondre avant de la révéler."
            "</div>"
        )

    st.markdown(
        (
            '<div class="flashcard-viewer">'
            '<div class="flashcard-topline">'
            f'<span class="flashcard-badge">{escape(str(index + 1))}</span>'
            f'<span class="flashcard-theme">{escape(theme)}</span>'
            "</div>"
            '<div class="flashcard-label">Question</div>'
            f'<div class="flashcard-question">{escape(carte["question"])}</div>'
            f"{reponse_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    colonne_precedent, colonne_reponse, colonne_suivant = st.columns([1, 1.4, 1])

    with colonne_precedent:
        if st.button(
            "Précédente",
            key=f"flashcard_precedente_{signature}_{index}",
            disabled=index == 0,
        ):
            st.session_state["flashcards_index"] = index - 1
            st.session_state["flashcards_reponse_visible"] = False
            st.rerun()

    with colonne_reponse:
        libelle_reponse = "Masquer la réponse" if reponse_visible else "Afficher la réponse"
        if st.button(libelle_reponse, key=f"flashcard_reponse_{signature}_{index}"):
            st.session_state["flashcards_reponse_visible"] = not reponse_visible
            st.rerun()

    with colonne_suivant:
        if st.button(
            "Suivante",
            key=f"flashcard_suivante_{signature}_{index}",
            disabled=index == total - 1,
        ):
            st.session_state["flashcards_index"] = index + 1
            st.session_state["flashcards_reponse_visible"] = False
            st.rerun()

    if st.button("Recommencer les flashcards", key=f"flashcard_reset_{signature}"):
        reinitialiser_flashcards()
        st.rerun()

    with st.expander("Voir toutes les flashcards"):
        for position, item in enumerate(flashcards, start=1):
            st.markdown(
                (
                    '<div class="flashcard-mini">'
                    f'<strong>{position}. Question :</strong> {escape(item["question"])}<br>'
                    f'<strong>Réponse :</strong> {escape(item["reponse"])}'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


def _analyser_questions_examen(contenu):
    """Transforme les questions d'examen en éléments structurés."""
    contenu = contenu.replace("\r\n", "\n").replace("\r", "\n").strip()
    blocs = re.split(r"(?m)^\s*(?=\d+\.\s+)", contenu)
    questions = []

    for bloc in blocs:
        bloc = bloc.strip()
        if not bloc:
            continue

        correspondance = re.match(r"(?s)^(\d+)\.\s*(.+)$", bloc)
        if not correspondance:
            continue

        numero = correspondance.group(1)
        reste = correspondance.group(2).strip()
        separation = re.split(
            r"(?i)\b(?:Éléments attendus|Elements attendus|Réponse attendue|Pistes de réponse|Correction|Réponse)\s*:",
            reste,
            maxsplit=1,
        )

        question = _nettoyer_markdown_simple(separation[0])
        elements = _nettoyer_markdown_simple(separation[1]) if len(separation) > 1 else ""

        if question:
            questions.append(
                {
                    "numero": numero,
                    "question": question,
                    "elements": elements,
                }
            )

    return questions


def _extraire_theme_examen(question):
    """Retourne un thème court à partir d'une question d'examen."""
    theme = re.search(r"«\s*(.+?)\s*»", question)
    if theme:
        return theme.group(1)

    mots = question.split()
    return " ".join(mots[:6]) if mots else "Question d'examen"


def afficher_questions_examen(contenu):
    """Affiche les questions d'examen en mode interactif."""
    questions = _analyser_questions_examen(contenu)
    if not questions:
        st.markdown(contenu)
        return

    signature = hashlib.sha1(contenu.encode("utf-8")).hexdigest()
    if st.session_state.get("examen_signature") != signature:
        st.session_state["examen_signature"] = signature
        reinitialiser_questions_examen()

    total = len(questions)
    index = min(max(st.session_state.get("examen_index", 0), 0), total - 1)
    st.session_state["examen_index"] = index
    item = questions[index]
    reponse_visible = st.session_state.get("examen_reponse_visible", False)

    st.progress((index + 1) / total)
    st.caption(f"Question {index + 1} sur {total}")

    theme = _extraire_theme_examen(item["question"])
    if item["elements"]:
        if reponse_visible:
            reponse_html = (
                '<div class="exam-answer">'
                '<div class="exam-label">Éléments attendus</div>'
                f'{escape(item["elements"])}'
                "</div>"
            )
        else:
            reponse_html = (
                '<div class="exam-hidden">'
                "Les éléments attendus sont masqués. Répondez d'abord, puis révélez la correction."
                "</div>"
            )
    else:
        reponse_html = (
            '<div class="exam-hidden">'
            "Aucun élément attendu n'a été détecté pour cette question."
            "</div>"
        )

    st.markdown(
        (
            '<div class="exam-viewer">'
            '<div class="exam-topline">'
            f'<span class="exam-badge">{escape(str(index + 1))}</span>'
            f'<span class="exam-theme">{escape(theme)}</span>'
            "</div>"
            '<div class="exam-label">Question ouverte</div>'
            f'<div class="exam-question">{escape(item["question"])}</div>'
            f"{reponse_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    colonne_precedent, colonne_reponse, colonne_suivant = st.columns([1, 1.4, 1])

    with colonne_precedent:
        if st.button(
            "Précédente",
            key=f"examen_precedente_{signature}_{index}",
            disabled=index == 0,
        ):
            st.session_state["examen_index"] = index - 1
            st.session_state["examen_reponse_visible"] = False
            st.rerun()

    with colonne_reponse:
        libelle_reponse = (
            "Masquer les éléments attendus"
            if reponse_visible
            else "Afficher les éléments attendus"
        )
        if st.button(
            libelle_reponse,
            key=f"examen_reponse_{signature}_{index}",
            disabled=not item["elements"],
        ):
            st.session_state["examen_reponse_visible"] = not reponse_visible
            st.rerun()

    with colonne_suivant:
        if st.button(
            "Suivante",
            key=f"examen_suivante_{signature}_{index}",
            disabled=index == total - 1,
        ):
            st.session_state["examen_index"] = index + 1
            st.session_state["examen_reponse_visible"] = False
            st.rerun()

    if st.button("Recommencer les questions", key=f"examen_reset_{signature}"):
        reinitialiser_questions_examen()
        st.rerun()

    with st.expander("Voir toutes les questions et éléments attendus"):
        for position, question in enumerate(questions, start=1):
            elements = question["elements"] or "Aucun élément attendu détecté."
            st.markdown(
                (
                    '<div class="exam-mini">'
                    f'<strong>{position}. Question :</strong> {escape(question["question"])}<br>'
                    f'<strong>Éléments attendus :</strong> {escape(elements)}'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


initialiser_session()

st.title("PadaGenie AI")
st.subheader("Générateur intelligent de supports pédagogiques")

with st.sidebar:
    st.header("Configuration du modèle IA")

    type_modele = st.selectbox(
        "Type de modèle",
        [
            "OpenAI API",
            "Groq API",
            "Ollama local",
        ],
    )

    cle_api = ""
    url_ollama = ""
    if type_modele == "OpenAI API":
        cle_api = st.text_input("Entrez votre clé API OpenAI", type="password")
        nom_modele = st.selectbox(
            "Modèle OpenAI",
            [
                "gpt-4o-mini",
                "gpt-4.1-mini",
            ],
        )
    elif type_modele == "Groq API":
        cle_api = st.text_input("Entrez votre clé API Groq", type="password")
        nom_modele = st.selectbox(
            "Modèle Groq",
            [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b",
            ],
        )
    else:
        nom_modele = st.selectbox(
            "Modèle Ollama",
            [
                "llama3.2",
                "llama3.1",
                "mistral",
                "qwen2.5",
                "gemma2",
            ],
        )

    st.sidebar.subheader("Paramètres pédagogiques")
    niveau_difficulte = st.sidebar.selectbox(
        "Choisissez le niveau de difficulté",
        ["Débutant", "Intermédiaire", "Avancé"],
        index=1,
    )

configuration_modele = {
    "type_modele": type_modele,
    "nom_modele": nom_modele,
    "cle_api": cle_api,
    "url_ollama": url_ollama,
}

fichier = st.file_uploader(
    "Importer un document de cours au format PDF ou TXT",
    type=["pdf", "txt"],
)

if fichier is not None:
    try:
        if st.session_state["nom_fichier"] != fichier.name:
            texte_brut = extraire_texte(fichier)
            texte_nettoye = nettoyer_texte(texte_brut)

            st.session_state["nom_fichier"] = fichier.name
            st.session_state["texte_extrait"] = texte_nettoye
            st.session_state["texte_nettoye"] = texte_nettoye
            st.session_state["chunks"] = []
            st.session_state["modele_embedding_rag"] = None
            st.session_state["index_faiss"] = None
            reinitialiser_resultats_generation()

            with st.spinner("Indexation RAG du document en cours..."):
                indexer_document_rag(texte_nettoye)
    except Exception as erreur:
        st.error(f"Erreur pendant l'extraction ou l'indexation RAG : {erreur}")
else:
    st.info("Importez un fichier PDF ou TXT pour commencer.")

texte_extrait = st.session_state.get("texte_extrait", "")
if texte_extrait:
    if st.session_state.get("index_faiss") is None:
        st.info("L'index FAISS n'est pas encore disponible pour ce document.")

    if st.button("Générer tous les supports pédagogiques", type="primary"):
        if texte_source_disponible():
            try:
                with st.spinner("Génération de tous les supports en cours..."):
                    st.session_state["resume"] = generer_support_pedagogique(
                        "resume",
                        generer_resume,
                        configuration_modele,
                        niveau_difficulte,
                    )
                    st.session_state["quiz"] = generer_support_pedagogique(
                        "quiz",
                        generer_quiz,
                        configuration_modele,
                        niveau_difficulte,
                    )
                    st.session_state["flashcards"] = generer_support_pedagogique(
                        "flashcards",
                        generer_flashcards,
                        configuration_modele,
                        niveau_difficulte,
                    )
                    st.session_state["questions_examen"] = generer_support_pedagogique(
                        "examen",
                        generer_questions_examen,
                        configuration_modele,
                        niveau_difficulte,
                    )
                    st.session_state["score_qualite"] = None
                    st.session_state["resume_auto_signature"] = (
                        signature_resume_automatique(
                            configuration_modele,
                            niveau_difficulte,
                        )
                    )
                st.success("Tous les supports pédagogiques ont été générés.")
            except Exception as erreur:
                st.error(f"Erreur pendant la génération complète : {erreur}")

    generer_resume_automatique(configuration_modele, niveau_difficulte)

onglet_resume, onglet_quiz, onglet_flashcards, onglet_examen, onglet_evaluation = st.tabs(
    [
        "Résumé",
        "Quiz QCM",
        "Flashcards",
        "Questions d'examen",
        "Évaluation qualité",
    ]
)

with onglet_resume:
    colonne_titre, colonne_exporter = st.columns([2.4, 1.8])
    with colonne_titre:
        st.subheader("Résumé généré")
    with colonne_exporter:
        afficher_export_pdf("resume")
    afficher_resume(st.session_state["resume"], afficher_titre=False)

with onglet_quiz:
    colonne_generer, colonne_exporter, _ = st.columns([1.55, 1.75, 2.2])
    with colonne_generer:
        if st.button("Générer le quiz", key="bouton_quiz"):
            if texte_source_disponible():
                try:
                    with st.spinner("Génération du quiz en cours..."):
                        st.session_state["quiz"] = generer_support_pedagogique(
                            "quiz",
                            generer_quiz,
                            configuration_modele,
                            niveau_difficulte,
                        )
                        st.session_state["score_qualite"] = None
                except Exception as erreur:
                    st.error(f"Erreur pendant la génération du quiz : {erreur}")
    with colonne_exporter:
        afficher_export_pdf("quiz")

    afficher_contenu("Quiz généré", st.session_state["quiz"])

with onglet_flashcards:
    colonne_generer, colonne_exporter, _ = st.columns([1.55, 1.75, 2.2])
    with colonne_generer:
        if st.button("Générer les flashcards", key="bouton_flashcards"):
            if texte_source_disponible():
                try:
                    with st.spinner("Génération des flashcards en cours..."):
                        st.session_state["flashcards"] = generer_support_pedagogique(
                            "flashcards",
                            generer_flashcards,
                            configuration_modele,
                            niveau_difficulte,
                        )
                        st.session_state["score_qualite"] = None
                except Exception as erreur:
                    st.error(f"Erreur pendant la génération des flashcards : {erreur}")
    with colonne_exporter:
        afficher_export_pdf("flashcards")

    afficher_contenu("Flashcards générées", st.session_state["flashcards"])

with onglet_examen:
    colonne_generer, colonne_exporter, _ = st.columns([1.55, 1.75, 2.2])
    with colonne_generer:
        if st.button("Générer les questions d'examen", key="bouton_examen"):
            if texte_source_disponible():
                try:
                    with st.spinner("Génération des questions d'examen en cours..."):
                        st.session_state["questions_examen"] = generer_support_pedagogique(
                            "examen",
                            generer_questions_examen,
                            configuration_modele,
                            niveau_difficulte,
                        )
                        st.session_state["score_qualite"] = None
                except Exception as erreur:
                    st.error(f"Erreur pendant la génération des questions d'examen : {erreur}")
    with colonne_exporter:
        afficher_export_pdf("examen")

    afficher_contenu("Questions d'examen générées", st.session_state["questions_examen"])

with onglet_evaluation:
    st.subheader("Évaluation de la qualité")
    st.write(
        "Le score compare le document source avec les contenus générés à l'aide "
        "d'embeddings Sentence-BERT et de la similarité cosinus."
    )

    if st.button("Évaluer la qualité", key="bouton_evaluation"):
        if texte_source_disponible():
            contenus_generes = [
                st.session_state["resume"],
                st.session_state["quiz"],
                st.session_state["flashcards"],
                st.session_state["questions_examen"],
            ]
            contenu_genere = "\n\n".join(
                contenu for contenu in contenus_generes if contenu.strip()
            )

            if not contenu_genere.strip():
                st.warning("Veuillez générer au moins un contenu avant l'évaluation.")
            else:
                try:
                    with st.spinner("Évaluation de la qualité en cours..."):
                        score = evaluer_qualite(
                            st.session_state.get("texte_nettoye")
                            or st.session_state["texte_extrait"],
                            contenu_genere,
                        )
                        st.session_state["score_qualite"] = score
                except Exception as erreur:
                    st.error(f"Erreur pendant l'évaluation : {erreur}")

    score_qualite = st.session_state.get("score_qualite")
    if score_qualite is not None:
        st.metric("Score de similarité", f"{score_qualite:.2f}")
        st.progress(score_qualite)
        st.write(interpreter_score(score_qualite))
    else:
        st.info("Aucun score calculé pour le moment.")
