"""Configuration et appels aux moteurs de génération de texte."""

from functools import lru_cache


@lru_cache(maxsize=2)
def _charger_modele_local(nom_modele):
    """Charge un modèle Hugging Face local et le garde en mémoire."""
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(nom_modele)
    modele = AutoModelForSeq2SeqLM.from_pretrained(nom_modele)
    modele.eval()
    return tokenizer, modele


def _longueur_maximale_entree(tokenizer):
    """Détermine une limite raisonnable pour le prompt envoyé au modèle local."""
    longueur_modele = getattr(tokenizer, "model_max_length", 512)
    if longueur_modele is None or longueur_modele > 10000:
        return 512
    return min(longueur_modele, 1024)


def generer_avec_modele_local(prompt, nom_modele):
    """Génère du texte avec un modèle local Hugging Face."""
    if not nom_modele:
        return "Erreur : aucun modèle local n'a été sélectionné."

    try:
        import torch

        tokenizer, modele = _charger_modele_local(nom_modele)
        entrees = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=_longueur_maximale_entree(tokenizer),
        )

        with torch.no_grad():
            sorties = modele.generate(
                **entrees,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.15,
                no_repeat_ngram_size=3,
            )

        texte = tokenizer.decode(
            sorties[0],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        ).strip()

        if not texte:
            return "Erreur : le modèle local n'a pas généré de contenu."

        return texte
    except Exception as erreur:
        return f"Erreur avec le modèle local : {erreur}"


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


def generer_avec_gemini(prompt, cle_api, nom_modele):
    """Génère du texte avec l'API Google Gemini sans stocker la clé API."""
    if not cle_api:
        return "Erreur : veuillez renseigner une clé API Gemini."

    if not nom_modele:
        return "Erreur : aucun modèle Gemini n'a été sélectionné."

    try:
        import google.generativeai as genai

        genai.configure(api_key=cle_api)
        modele = genai.GenerativeModel(nom_modele)
        reponse = modele.generate_content(prompt)
        texte = getattr(reponse, "text", "").strip()

        if not texte:
            return "Erreur : Gemini n'a pas renvoyé de contenu exploitable."

        return texte
    except Exception as erreur:
        return f"Erreur avec l'API Gemini : {erreur}"


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


def generer_texte(prompt, configuration_modele):
    """Route la génération vers le moteur choisi par l'utilisateur."""
    if not prompt or not str(prompt).strip():
        return "Erreur : le prompt de génération est vide."

    configuration_modele = configuration_modele or {}
    type_modele = configuration_modele.get("type_modele", "")
    nom_modele = configuration_modele.get("nom_modele", "")
    cle_api = configuration_modele.get("cle_api", "")

    if type_modele == "Modèle local Hugging Face":
        return generer_avec_modele_local(prompt, nom_modele)

    if type_modele == "OpenAI API":
        return generer_avec_openai(prompt, cle_api, nom_modele)

    if type_modele == "Google Gemini API":
        return generer_avec_gemini(prompt, cle_api, nom_modele)

    if type_modele == "Groq API":
        return generer_avec_groq(prompt, cle_api, nom_modele)

    return "Erreur : type de modèle non reconnu."
