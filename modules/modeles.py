"""Configuration et appels aux moteurs de génération de texte."""

import json
from urllib.error import URLError
from urllib.request import Request, urlopen


def generer_avec_openai(prompt, cle_api, nom_modele):
    """Génère du texte avec l'API OpenAI sans stocker la clé API."""
    if not cle_api:
        return "Erreur : veuillez renseigner une clé API OpenAI."

    if not nom_modele:
        return "Erreur : aucun modèle OpenAI n'a été sélectionné."

    try:
        from openai import OpenAI

        client = OpenAI(api_key=cle_api)
        reponse = client.chat.completions.create(
            model=nom_modele,
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant pédagogique expert. Tu réponds toujours en français.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        return reponse.choices[0].message.content.strip()
    except Exception as erreur:
        return f"Erreur avec l'API OpenAI : {erreur}"


def generer_avec_groq(prompt, cle_api, nom_modele):
    """Génère du texte avec l'API Groq sans stocker la clé API."""
    if not cle_api:
        return "Erreur : veuillez renseigner une clé API Groq."

    if not nom_modele:
        return "Erreur : aucun modèle Groq n'a été sélectionné."

    try:
        from groq import Groq

        client = Groq(api_key=cle_api)
        reponse = client.chat.completions.create(
            model=nom_modele,
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant pédagogique expert. Tu réponds toujours en français.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_completion_tokens=1600,
        )
        texte = reponse.choices[0].message.content.strip()

        if not texte:
            return "Erreur : Groq n'a pas renvoyé de contenu exploitable."

        return texte
    except Exception as erreur:
        return f"Erreur avec l'API Groq : {erreur}"


def generer_avec_ollama(prompt, nom_modele, url_ollama="http://localhost:11434"):
    """Génère du texte avec Ollama local sans clé API."""
    if not nom_modele:
        return "Erreur : aucun modèle Ollama n'a été sélectionné."

    url_ollama = (url_ollama or "http://localhost:11434").rstrip("/")
    donnees = {
        "model": nom_modele,
        "messages": [
            {
                "role": "system",
                "content": "Tu es un assistant pédagogique expert. Tu réponds toujours en français.",
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.4,
            "num_predict": 1600,
        },
    }

    try:
        requete = Request(
            f"{url_ollama}/api/chat",
            data=json.dumps(donnees).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(requete, timeout=120) as reponse:
            resultat = json.loads(reponse.read().decode("utf-8"))

        texte = resultat.get("message", {}).get("content", "").strip()
        if not texte:
            return "Erreur : Ollama n'a pas renvoyé de contenu exploitable."

        return texte
    except URLError as erreur:
        return (
            "Erreur avec Ollama : impossible de contacter le serveur local. "
            "Vérifiez que Ollama est lancé avec `ollama serve`."
            f" Détail : {erreur}"
        )
    except Exception as erreur:
        return f"Erreur avec Ollama : {erreur}"


def generer_texte(prompt, configuration_modele):
    """Route la génération vers le moteur choisi par l'utilisateur."""
    if not prompt or not str(prompt).strip():
        return "Erreur : le prompt de génération est vide."

    configuration_modele = configuration_modele or {}
    type_modele = configuration_modele.get("type_modele", "")
    nom_modele = configuration_modele.get("nom_modele", "")
    cle_api = configuration_modele.get("cle_api", "")
    url_ollama = configuration_modele.get("url_ollama", "http://localhost:11434")

    if type_modele == "OpenAI API":
        return generer_avec_openai(prompt, cle_api, nom_modele)

    if type_modele == "Groq API":
        return generer_avec_groq(prompt, cle_api, nom_modele)

    if type_modele == "Ollama local":
        return generer_avec_ollama(prompt, nom_modele, url_ollama)

    return "Erreur : type de modèle non reconnu."
