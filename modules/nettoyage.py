"""Fonctions de nettoyage et de limitation du texte."""

import re


def _recoller_fragments_pdf(lignes):
    """Recolle certains mots découpés par l'extraction PDF."""
    lignes_recollees = []
    index = 0

    while index < len(lignes):
        ligne = lignes[index]

        # Certains PDF extraient un titre comme deux lignes : "P" puis "ROMPT".
        if (
            re.fullmatch(r"[A-ZÀ-Ÿ]", ligne)
            and index + 1 < len(lignes)
            and re.fullmatch(r"[A-ZÀ-Ÿ]{2,}", lignes[index + 1])
        ):
            lignes_recollees.append(ligne + lignes[index + 1])
            index += 2
            continue

        # Même correction quand les fragments sont sur une seule ligne.
        ligne = re.sub(r"\b([A-ZÀ-Ÿ])\s+([A-ZÀ-Ÿ]{2,})\b", r"\1\2", ligne)
        lignes_recollees.append(ligne)
        index += 1

    return lignes_recollees


def nettoyer_texte(texte):
    """Nettoie le texte extrait pour le rendre exploitable par les modèles."""
    if texte is None:
        raise ValueError("Le texte fourni est vide.")

    texte = str(texte).replace("\r\n", "\n").replace("\r", "\n")
    texte = re.sub(r"-\n(?=\w)", "", texte)

    # On supprime les lignes vides et les espaces inutiles dans chaque ligne.
    lignes_nettoyees = []
    for ligne in texte.split("\n"):
        ligne = re.sub(r"[ \t]+", " ", ligne).strip()
        if ligne and not re.fullmatch(r"\d+", ligne):
            lignes_nettoyees.append(ligne)

    lignes_nettoyees = _recoller_fragments_pdf(lignes_nettoyees)
    texte_nettoye = "\n".join(lignes_nettoyees).strip()
    if not texte_nettoye:
        raise ValueError("Le texte est vide après nettoyage.")

    return texte_nettoye


def limiter_texte(texte, longueur_max=4000):
    """Limite la longueur du texte pour éviter les erreurs des modèles."""
    if texte is None or not str(texte).strip():
        raise ValueError("Impossible de limiter un texte vide.")

    if longueur_max <= 0:
        raise ValueError("La longueur maximale doit être supérieure à zéro.")

    texte = str(texte).strip()
    if len(texte) <= longueur_max:
        return texte

    texte_coupe = texte[:longueur_max]
    dernier_espace = texte_coupe.rfind(" ")

    # On évite de couper au milieu d'un mot quand c'est possible.
    if dernier_espace > int(longueur_max * 0.8):
        texte_coupe = texte_coupe[:dernier_espace]

    return texte_coupe.strip() + "\n\n[Texte limité pour respecter la taille maximale du modèle.]"
