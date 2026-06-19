"""Export PDF des résultats générés par PadaGenie AI."""

import re

from fpdf import FPDF


class PDFResultats(FPDF):
    """PDF simple avec en-tête pour les résultats pédagogiques."""

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "PadaGenie AI", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _nettoyer_texte_pdf(texte):
    """Prépare le texte pour une sortie PDF compatible Unicode."""
    if texte is None:
        return ""

    texte = str(texte).strip()
    remplacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": "-",
    }
    for source, cible in remplacements.items():
        texte = texte.replace(source, cible)

    return texte.encode("latin-1", errors="replace").decode("latin-1")


def _nettoyer_markdown_pdf(texte):
    """Retire les marqueurs Markdown simples pour le rendu PDF."""
    texte = _nettoyer_texte_pdf(texte)
    texte = re.sub(r"\*\*(.*?)\*\*", r"\1", texte)
    texte = re.sub(r"`([^`]*)`", r"\1", texte)
    texte = re.sub(r"\s+", " ", texte)
    return texte.strip()


def _titre_markdown(ligne):
    """Détecte un titre Markdown ou un titre en gras seul."""
    ligne = ligne.strip()
    correspondance = re.match(r"^#{1,6}\s+(.+)$", ligne)
    if correspondance:
        return _nettoyer_markdown_pdf(correspondance.group(1))

    correspondance = re.fullmatch(r"\*\*(.+?)\*\*", ligne)
    if correspondance:
        return _nettoyer_markdown_pdf(correspondance.group(1))

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


def _ajouter_paragraphe(pdf, texte, retrait=0, gras=False, couleur=(15, 23, 42)):
    """Ajoute un paragraphe avec indentation et couleur."""
    texte = _nettoyer_markdown_pdf(texte)
    if not texte:
        return

    marge_initiale = pdf.l_margin
    if retrait:
        pdf.set_left_margin(marge_initiale + retrait)
        pdf.set_x(marge_initiale + retrait)

    pdf.set_font("Helvetica", "B" if gras else "", 10)
    pdf.set_text_color(*couleur)
    pdf.multi_cell(0, 6, texte, new_x="LMARGIN", new_y="NEXT")

    if retrait:
        pdf.set_left_margin(marge_initiale)
        pdf.set_x(marge_initiale)


def _ajouter_titre_interne(pdf, titre):
    """Ajoute un titre interne avec respiration visuelle."""
    titre = _nettoyer_markdown_pdf(titre)
    if not titre:
        return

    pdf.ln(1.5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(37, 99, 235)
    pdf.multi_cell(0, 7, titre, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(191, 219, 254)
    x = pdf.get_x()
    y = pdf.get_y()
    pdf.line(x, y, x + 35, y)
    pdf.ln(2)


def _ajouter_contenu_formate(pdf, contenu):
    """Ajoute du contenu en respectant titres, listes et paragraphes."""
    contenu = _nettoyer_texte_pdf(contenu)
    if not contenu:
        return

    lignes = contenu.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    paragraphe = []

    def fermer_paragraphe():
        nonlocal paragraphe
        if paragraphe:
            _ajouter_paragraphe(pdf, " ".join(paragraphe))
            pdf.ln(1)
            paragraphe = []

    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne:
            fermer_paragraphe()
            continue

        titre = _titre_markdown(ligne)
        if titre:
            fermer_paragraphe()
            _ajouter_titre_interne(pdf, titre)
            continue

        element_liste = re.match(r"^[-•]\s+(.+)$", ligne)
        if element_liste:
            fermer_paragraphe()
            _ajouter_paragraphe(pdf, f"- {element_liste.group(1)}", retrait=5)
            continue

        question = re.match(r"^(\d+\.)\s+(.+)$", ligne)
        if question:
            fermer_paragraphe()
            _ajouter_paragraphe(pdf, f"{question.group(1)} {question.group(2)}", gras=True)
            continue

        option = re.match(r"^([A-D]\.)\s+(.+)$", ligne)
        if option:
            fermer_paragraphe()
            _ajouter_paragraphe(pdf, f"{option.group(1)} {option.group(2)}", retrait=6)
            continue

        if re.match(r"^(Réponse correcte|Explication|Éléments attendus)\s*:", ligne, re.IGNORECASE):
            fermer_paragraphe()
            _ajouter_paragraphe(pdf, ligne, retrait=4, gras=True, couleur=(30, 64, 175))
            continue

        paragraphe.append(ligne)

    fermer_paragraphe()


def _ajouter_section(pdf, titre, contenu):
    """Ajoute une section structurée dans le PDF."""
    contenu = _nettoyer_texte_pdf(contenu)
    if not contenu:
        return

    pdf.set_fill_color(239, 246, 255)
    pdf.set_draw_color(191, 219, 254)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 64, 175)
    pdf.multi_cell(0, 8, titre, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    _ajouter_contenu_formate(pdf, contenu)
    pdf.ln(5)


def generer_pdf_resultats(
    resume,
    quiz,
    flashcards,
    questions_examen,
):
    """Génère un PDF contenant les supports pédagogiques et retourne ses bytes."""
    pdf = PDFResultats()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Résultats générés", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    _ajouter_section(pdf, "Résumé généré", resume)
    _ajouter_section(pdf, "Quiz généré", quiz)
    _ajouter_section(pdf, "Flashcards générées", flashcards)
    _ajouter_section(pdf, "Questions d'examen générées", questions_examen)

    donnees_pdf = pdf.output(dest="S")
    if isinstance(donnees_pdf, str):
        return donnees_pdf.encode("latin-1")

    return bytes(donnees_pdf)
