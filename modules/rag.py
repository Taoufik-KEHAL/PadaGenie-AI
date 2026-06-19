"""Fonctions RAG pour récupérer les passages pertinents d'un document."""

from functools import lru_cache

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


def decouper_en_chunks(texte, taille_chunk=800, chevauchement=100):
    """Découpe un texte en chunks avec chevauchement pour préserver le contexte."""
    if texte is None or not str(texte).strip():
        return []

    taille_chunk = max(int(taille_chunk), 1)
    chevauchement = max(min(int(chevauchement), taille_chunk - 1), 0)
    texte = " ".join(str(texte).split())
    chunks = []
    debut = 0

    while debut < len(texte):
        fin = min(debut + taille_chunk, len(texte))

        if fin < len(texte):
            ponctuation = max(
                texte.rfind(".", debut, fin),
                texte.rfind("!", debut, fin),
                texte.rfind("?", debut, fin),
            )
            if ponctuation > debut + int(taille_chunk * 0.55):
                fin = ponctuation + 1
            else:
                espace = texte.rfind(" ", debut, fin)
                if espace > debut + int(taille_chunk * 0.55):
                    fin = espace

        chunk = texte[debut:fin].strip()
        if chunk:
            chunks.append(chunk)

        if fin >= len(texte):
            break

        debut = max(fin - chevauchement, debut + 1)

    return chunks


@lru_cache(maxsize=1)
def charger_modele_embedding_rag():
    """Charge le modèle Sentence-BERT utilisé pour les embeddings RAG."""
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def _normaliser_embeddings(embeddings):
    """Retourne des embeddings float32 normalisés pour FAISS."""
    embeddings = np.asarray(embeddings, dtype="float32")
    if embeddings.ndim == 1:
        embeddings = embeddings.reshape(1, -1)

    normes = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normes[normes == 0] = 1.0
    return embeddings / normes


def creer_embeddings_chunks(chunks):
    """Transforme les chunks en embeddings numpy compatibles avec FAISS."""
    if not chunks:
        raise ValueError("Aucun chunk disponible pour créer les embeddings.")

    modele_embedding = charger_modele_embedding_rag()
    embeddings = modele_embedding.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return _normaliser_embeddings(embeddings)


def construire_index_faiss(embeddings):
    """Construit un index FAISS en similarité cosinus via produit scalaire."""
    embeddings = _normaliser_embeddings(embeddings)
    if embeddings.size == 0:
        raise ValueError("Les embeddings sont vides, l'index FAISS est impossible.")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return index


def rechercher_chunks_pertinents(requete, chunks, index, modele_embedding, top_k=5):
    """Recherche les chunks les plus proches de la requête dans l'index FAISS."""
    if not requete or not str(requete).strip():
        raise ValueError("La requête RAG est vide.")

    if not chunks:
        raise ValueError("Aucun chunk n'est disponible pour la recherche RAG.")

    if index is None:
        raise ValueError("L'index FAISS n'est pas disponible.")

    if modele_embedding is None:
        raise ValueError("Le modèle d'embedding RAG n'est pas disponible.")

    top_k = max(1, min(int(top_k), len(chunks)))
    embedding_requete = modele_embedding.encode(
        [str(requete)],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    embedding_requete = _normaliser_embeddings(embedding_requete)
    _, indices = index.search(embedding_requete, top_k)

    chunks_pertinents = []
    for indice in indices[0]:
        if 0 <= indice < len(chunks):
            chunks_pertinents.append(chunks[indice])

    return chunks_pertinents


def construire_contexte_rag(chunks_pertinents):
    """Construit un contexte lisible à partir des chunks récupérés."""
    if not chunks_pertinents:
        return ""

    blocs = []
    for index, chunk in enumerate(chunks_pertinents, start=1):
        blocs.append(f"[Passage {index}]\n{str(chunk).strip()}")

    return "\n\n---\n\n".join(blocs)
