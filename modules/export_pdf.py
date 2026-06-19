"""Export PDF des résultats générés par PadaGenie AI."""

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


def _ajouter_section(pdf, titre, contenu):
    """Ajoute une section structurée dans le PDF."""
    contenu = _nettoyer_texte_pdf(contenu)
    if not contenu:
        return

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(0, 8, titre, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 6, contenu, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)


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
