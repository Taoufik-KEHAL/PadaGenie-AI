"""Évaluation de la qualité sémantique du contenu généré."""

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


@lru_cache(maxsize=1)
def charger_modele_embedding():
    """Charge le modèle Sentence-BERT utilisé pour les embeddings."""
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def evaluer_qualite(texte_source, contenu_genere):
    """Compare le contenu généré au document source avec la similarité cosinus."""
    if texte_source is None or not str(texte_source).strip():
        raise ValueError("Le texte source est vide, l'évaluation est impossible.")

    if contenu_genere is None or not str(contenu_genere).strip():
        raise ValueError("Le contenu généré est vide, l'évaluation est impossible.")

    try:
        modele = charger_modele_embedding()

        # Sentence-BERT transforme les textes en vecteurs sémantiques comparables.
        embeddings = modele.encode([str(texte_source), str(contenu_genere)])
        score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

        return float(np.clip(score, 0.0, 1.0))
    except Exception as erreur:
        raise RuntimeError(f"Erreur pendant l'évaluation de la qualité : {erreur}") from erreur


def interpreter_score(score):
    """Retourne une interprétation pédagogique du score de qualité."""
    if score >= 0.75:
        return "Bonne qualité : le contenu généré est fortement lié au document source."

    if score >= 0.50:
        return "Qualité moyenne : le contenu généré est partiellement lié au document source."

    return "Qualité faible : le contenu généré semble peu lié au document source."
