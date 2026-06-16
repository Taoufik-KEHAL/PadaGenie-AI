"""Fonctions d'extraction de texte depuis des documents PDF ou TXT."""

from pathlib import Path

import pdfplumber


def _remettre_au_debut(fichier):
    """Replace le curseur du fichier au début quand l'objet le permet."""
    if hasattr(fichier, "seek"):
        fichier.seek(0)


def extraire_texte_depuis_pdf(fichier):
    """Extrait le texte d'un fichier PDF avec pdfplumber."""
    try:
        _remettre_au_debut(fichier)

        textes_pages = []
        with pdfplumber.open(fichier) as pdf:
            if not pdf.pages:
                raise ValueError("Le fichier PDF ne contient aucune page.")

            for page in pdf.pages:
                texte_page = page.extract_text() or ""
                if texte_page.strip():
                    textes_pages.append(texte_page.strip())

        texte = "\n\n".join(textes_pages).strip()
        if not texte:
            raise ValueError("Le texte du PDF n'a pas pu être extrait.")

        return texte
    except ValueError:
        raise
    except Exception as erreur:
        raise ValueError(f"Erreur pendant l'extraction du PDF : {erreur}") from erreur


def extraire_texte_depuis_txt(fichier):
    """Lit le contenu d'un fichier TXT et retourne son texte."""
    try:
        _remettre_au_debut(fichier)

        if hasattr(fichier, "getvalue"):
            contenu = fichier.getvalue()
        else:
            contenu = fichier.read()

        if not contenu:
            raise ValueError("Le fichier TXT est vide.")

        if isinstance(contenu, bytes):
            try:
                texte = contenu.decode("utf-8")
            except UnicodeDecodeError:
                texte = contenu.decode("latin-1")
        else:
            texte = str(contenu)

        texte = texte.strip()
        if not texte:
            raise ValueError("Le fichier TXT ne contient pas de texte exploitable.")

        return texte
    except ValueError:
        raise
    except Exception as erreur:
        raise ValueError(f"Erreur pendant la lecture du fichier TXT : {erreur}") from erreur


def extraire_texte(fichier):
    """Détecte le format du fichier puis lance la bonne extraction."""
    if fichier is None:
        raise ValueError("Aucun fichier n'a été fourni.")

    nom_fichier = getattr(fichier, "name", "")
    extension = Path(nom_fichier).suffix.lower()

    if extension == ".pdf":
        return extraire_texte_depuis_pdf(fichier)

    if extension == ".txt":
        return extraire_texte_depuis_txt(fichier)

    raise ValueError("Format non supporté. Veuillez importer un fichier PDF ou TXT.")
