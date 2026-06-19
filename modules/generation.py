"""Fonctions de génération des supports pédagogiques."""

import re
from collections import Counter

from modules.modeles import generer_texte
from modules.nettoyage import limiter_texte


MOTS_VIDES = {
    "afin",
    "ainsi",
    "alors",
    "améliore",
    "apres",
    "après",
    "assez",
    "aucun",
    "aussi",
    "autre",
    "avant",
    "avec",
    "avoir",
    "bonne",
    "car",
    "cela",
    "celle",
    "celles",
    "celui",
    "cette",
    "chaque",
    "chez",
    "claire",
    "claires",
    "comme",
    "comment",
    "concevoir",
    "consiste",
    "contre",
    "dans",
    "des",
    "demandée",
    "depuis",
    "donc",
    "dont",
    "elle",
    "elles",
    "encore",
    "entre",
    "est",
    "et",
    "etre",
    "être",
    "exemple",
    "extérieur",
    "fait",
    "faire",
    "facilite",
    "fois",
    "forme",
    "fournir",
    "grace",
    "grâce",
    "leur",
    "leur",
    "leurs",
    "les",
    "une",
    "mais",
    "meme",
    "même",
    "nous",
    "peut",
    "possède",
    "plus",
    "pour",
    "précise",
    "quand",
    "que",
    "quel",
    "quelle",
    "quels",
    "quelles",
    "sans",
    "selon",
    "ses",
    "sont",
    "sous",
    "sur",
    "texte",
    "tous",
    "tout",
    "toute",
    "toutes",
    "tres",
    "très",
    "vers",
    "vous",
    "réduit",
}


CONSIGNES_NIVEAU = {
    "Débutant": (
        "Utilise un vocabulaire accessible, des définitions simples, des phrases courtes "
        "et des questions faciles centrées sur l'identification et la compréhension directe."
    ),
    "Intermédiaire": (
        "Utilise un vocabulaire académique simple, équilibre définitions et explications, "
        "et propose des questions de compréhension et d'application."
    ),
    "Avancé": (
        "Utilise un vocabulaire plus technique, approfondis les relations entre notions, "
        "et propose des questions d'analyse ou de justification plus exigeantes."
    ),
}


def _preparer_texte(texte):
    """Vérifie et limite le texte avant la création des prompts."""
    if texte is None or not str(texte).strip():
        return None, "Erreur : le texte source est vide."

    texte = str(texte).strip()
    if len(texte.split()) < 20:
        return None, "Erreur : le texte est trop court pour générer un support fiable."

    try:
        return limiter_texte(texte, longueur_max=6000), None
    except ValueError as erreur:
        return None, f"Erreur : {erreur}"


def _normaliser_niveau_difficulte(niveau_difficulte):
    """Retourne un niveau de difficulté reconnu par l'application."""
    if niveau_difficulte in CONSIGNES_NIVEAU:
        return niveau_difficulte

    return "Intermédiaire"


def _consigne_niveau(niveau_difficulte):
    """Retourne les consignes pédagogiques associées au niveau choisi."""
    niveau_difficulte = _normaliser_niveau_difficulte(niveau_difficulte)
    return CONSIGNES_NIVEAU[niveau_difficulte]


def _preparer_contexte_generation(texte, contexte_rag=None):
    """Prépare le contexte RAG ou le texte source de secours pour les prompts."""
    contexte = contexte_rag if contexte_rag and str(contexte_rag).strip() else texte
    return _preparer_texte(contexte)


def _nombre_par_niveau(niveau_difficulte, debutant, intermediaire, avance):
    """Choisit un volume de contenu selon le niveau pédagogique."""
    niveau_difficulte = _normaliser_niveau_difficulte(niveau_difficulte)
    valeurs = {
        "Débutant": debutant,
        "Intermédiaire": intermediaire,
        "Avancé": avance,
    }
    return valeurs[niveau_difficulte]


def _est_modele_local(configuration_modele):
    """Indique si le moteur choisi est le modèle local Ollama."""
    return (configuration_modele or {}).get("type_modele") == "Ollama local"


def _normaliser_mot(mot):
    """Nettoie un mot candidat pour l'analyse du document."""
    mot = mot.lower().strip("-'’_")
    for prefixe in ("l'", "d'", "qu'", "l’", "d’", "qu’"):
        if mot.startswith(prefixe):
            mot = mot[len(prefixe) :]
    return mot


def _tokeniser(texte):
    """Découpe le texte en mots utiles pour les mots-clés."""
    mots = _mots_bruts(texte)
    tokens = []

    for mot in mots:
        if len(mot) >= 4 and mot not in MOTS_VIDES:
            tokens.append(mot)

    return tokens


def _mots_bruts(texte):
    """Retourne les mots normalisés en conservant leur ordre d'origine."""
    mots = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’-]+", texte)
    return [_normaliser_mot(mot) for mot in mots]


def _mot_utile(mot):
    """Indique si un mot peut porter une notion de cours."""
    return len(mot) >= 4 and mot not in MOTS_VIDES


def _nettoyer_phrase(phrase):
    """Normalise une phrase extraite du document."""
    phrase = re.sub(r"\s+", " ", phrase).strip(" -\t")
    phrase = re.sub(r"\s+([,.;:!?])", r"\1", phrase)
    return phrase


def _decouper_phrases(texte):
    """Découpe le document en phrases ou segments significatifs."""
    lignes = [_nettoyer_phrase(ligne) for ligne in texte.splitlines()]
    lignes = [
        ligne
        for ligne in lignes
        if ligne and not re.fullmatch(r"\d+", ligne) and len(ligne) > 3
        and not (ligne.isupper() and len(ligne.split()) <= 4)
    ]

    texte_prepare = " ".join(lignes)
    morceaux = re.split(r"(?<=[.!?])\s+|;\s+", texte_prepare)
    phrases = []

    for morceau in morceaux:
        phrase = _nettoyer_phrase(morceau)
        nombre_mots = len(phrase.split())
        if 7 <= nombre_mots <= 45:
            phrases.append(phrase)

    if phrases:
        return phrases

    # Si le PDF est très mal extrait, on fabrique quand même des segments lisibles.
    mots = texte_prepare.split()
    return [
        " ".join(mots[index : index + 28])
        for index in range(0, len(mots), 28)
        if len(mots[index : index + 28]) >= 7
    ]


def _extraire_mots_cles(texte, nombre=14):
    """Extrait des mots-clés et petites expressions à partir du document."""
    tokens = _tokeniser(texte)
    if not tokens:
        return ["notion", "concept", "méthode", "objectif"]

    compteur = Counter(tokens)

    # Les expressions de deux mots donnent souvent de meilleures notions de cours,
    # mais seulement si les mots sont réellement voisins dans le texte original.
    expressions = []
    segments = re.split(r"(?<=[.!?])\s+|\n+", texte)
    for segment in segments:
        mots = _mots_bruts(segment)
        for mot_1, mot_2 in zip(mots, mots[1:]):
            if _mot_utile(mot_1) and _mot_utile(mot_2) and mot_1 != mot_2:
                expressions.append(f"{mot_1} {mot_2}")

    compteur_expressions = Counter(expressions)
    candidats = []

    for expression, frequence in compteur_expressions.most_common(nombre * 3):
        score = frequence * 3 + len(expression) / 20
        candidats.append((expression, score))

    for mot, frequence in compteur.most_common(nombre * 3):
        score = frequence + len(mot) / 15
        candidats.append((mot, score))

    candidats.sort(key=lambda item: item[1], reverse=True)

    mots_cles = []
    premiers_mots_utilises = set()
    for candidat, _ in candidats:
        if any(candidat in mot or mot in candidat for mot in mots_cles):
            continue
        premier_mot = candidat.split()[0]
        if premier_mot in premiers_mots_utilises and len(candidat.split()) == 1:
            continue
        mots_cles.append(candidat)
        premiers_mots_utilises.add(premier_mot)
        if len(mots_cles) == nombre:
            break

    return mots_cles or ["notion", "concept", "méthode", "objectif"]


def _raccourcir(texte, longueur=230):
    """Raccourcit une phrase sans couper brutalement les mots."""
    texte = _nettoyer_phrase(texte)
    if len(texte) <= longueur:
        return texte

    extrait = texte[:longueur].rsplit(" ", 1)[0]
    return extrait.strip() + "..."


def _classer_phrases_importantes(texte, nombre=6):
    """Classe les phrases selon leur richesse en mots-clés."""
    phrases = _decouper_phrases(texte)
    mots_cles = _extraire_mots_cles(texte, nombre=24)
    mots_simples = set()

    for mot_cle in mots_cles:
        mots_simples.update(mot_cle.split())

    scores = []
    for position, phrase in enumerate(phrases):
        tokens = _tokeniser(phrase)
        score = sum(1 for token in tokens if token in mots_simples)
        score += min(len(tokens), 25) / 25
        score += max(0, 1 - position / max(len(phrases), 1)) * 0.25
        scores.append((score, position, phrase))

    phrases_choisies = sorted(scores, reverse=True)[:nombre]
    phrases_choisies = sorted(phrases_choisies, key=lambda item: item[1])
    return [phrase for _, _, phrase in phrases_choisies]


def _trouver_phrase_pour_mot_cle(mot_cle, phrases):
    """Trouve la phrase la plus utile pour expliquer un mot-clé."""
    mots = mot_cle.split()

    for phrase in phrases:
        phrase_minuscule = phrase.lower()
        if all(mot in phrase_minuscule for mot in mots):
            return phrase

    for phrase in phrases:
        phrase_minuscule = phrase.lower()
        if any(mot in phrase_minuscule for mot in mots):
            return phrase

    return phrases[0]


def _choisir_distracteurs(mots_cles, bonne_reponse, depart=0):
    """Choisit trois propositions incorrectes différentes de la bonne réponse."""
    candidats = [
        mot_cle
        for mot_cle in mots_cles
        if mot_cle.lower() != bonne_reponse.lower()
        and mot_cle.split()[0] != bonne_reponse.split()[0]
    ]
    candidats.extend(["objectif pédagogique", "méthode d'analyse", "résultat attendu"])

    distracteurs = []
    position = depart
    while len(distracteurs) < 3:
        candidat = candidats[position % len(candidats)]
        deja_present = [mot.lower() for mot in distracteurs]
        if candidat.lower() not in deja_present:
            distracteurs.append(candidat)
        position += 1

    return distracteurs


def _remplacer_mot_cle_par_trou(phrase, mot_cle):
    """Crée une question à trou à partir d'une phrase source."""
    motif = re.compile(re.escape(mot_cle), re.IGNORECASE)
    if motif.search(phrase):
        return motif.sub("________", phrase, count=1)

    premier_mot = mot_cle.split()[0]
    motif = re.compile(re.escape(premier_mot), re.IGNORECASE)
    if motif.search(phrase):
        return motif.sub("________", phrase, count=1)

    return phrase


def _formater_option(texte):
    """Met proprement en forme une option de QCM."""
    return texte[:1].upper() + texte[1:]


def _options_qcm(bonne_reponse, distracteurs, index):
    """Place la bonne réponse à une position variable."""
    options = [bonne_reponse] + distracteurs
    decalage = index % 4
    options = options[decalage:] + options[:decalage]
    etiquettes = ["A", "B", "C", "D"]
    bonnes_etiquettes = etiquettes[options.index(bonne_reponse)]
    return list(zip(etiquettes, options)), bonnes_etiquettes


def _sortie_trop_faible(contenu, type_contenu):
    """Repère les sorties trop courtes ou mal structurées."""
    if not contenu or contenu.startswith("Erreur"):
        return False

    nombre_mots = len(contenu.split())
    if type_contenu == "resume":
        return nombre_mots < 70 or "Points essentiels" not in contenu
    if type_contenu == "quiz":
        return (
            nombre_mots < 90
            or contenu.count("Réponse correcte") < 5
            or "A." not in contenu
            or "D." not in contenu
        )
    if type_contenu == "flashcards":
        return nombre_mots < 70 or contenu.count("Flashcard") < 5
    if type_contenu == "examen":
        return nombre_mots < 45 or len(re.findall(r"^\d+\.", contenu, re.MULTILINE)) < 5

    return True


def _generer_resume_fiable(texte, niveau_difficulte="Intermédiaire"):
    """Construit un résumé pédagogique fiable à partir des phrases importantes."""
    niveau_difficulte = _normaliser_niveau_difficulte(niveau_difficulte)
    nombre_notions = _nombre_par_niveau(niveau_difficulte, 4, 5, 6)
    phrases_importantes = _classer_phrases_importantes(
        texte,
        nombre=max(6, nombre_notions + 2),
    )
    mots_cles = _extraire_mots_cles(texte, nombre=nombre_notions + 3)

    lignes = [
        f"### Résumé du cours - niveau {niveau_difficulte}",
        "",
        "**Idée générale**",
        _raccourcir(phrases_importantes[0], 280),
        "",
        "**Notions principales**",
    ]

    for mot_cle in mots_cles[:nombre_notions]:
        phrase = _trouver_phrase_pour_mot_cle(mot_cle, phrases_importantes)
        lignes.append(f"- **{_formater_option(mot_cle)}** : {_raccourcir(phrase, 210)}")

    lignes.extend(["", "**Points essentiels**"])
    for phrase in phrases_importantes[:nombre_notions]:
        lignes.append(f"- {_raccourcir(phrase, 230)}")

    if niveau_difficulte == "Débutant":
        conclusion = (
            "À retenir : commencez par maîtriser les définitions simples et les idées "
            "principales avant de passer aux détails."
        )
    elif niveau_difficulte == "Avancé":
        conclusion = (
            "À retenir : reliez les notions entre elles, justifiez leurs rôles et repérez "
            "les conditions ou limites indiquées par le document."
        )
    else:
        conclusion = (
            "À retenir : révisez les notions clés, leurs définitions, leurs rôles et leurs "
            "exemples d'application."
        )

    lignes.extend(
        [
            "",
            "**À retenir**",
            conclusion,
        ]
    )
    return "\n".join(lignes)


def _generer_quiz_fiable(texte, niveau_difficulte="Intermédiaire"):
    """Construit un QCM exploitable avec questions à trous et explications."""
    niveau_difficulte = _normaliser_niveau_difficulte(niveau_difficulte)
    phrases = _classer_phrases_importantes(texte, nombre=10)
    mots_cles = _extraire_mots_cles(texte, nombre=18)
    lignes = []

    for index in range(5):
        mot_cle = mots_cles[index % len(mots_cles)]
        phrase = _trouver_phrase_pour_mot_cle(mot_cle, phrases)
        phrase_trouee = _remplacer_mot_cle_par_trou(phrase, mot_cle)
        distracteurs = _choisir_distracteurs(mots_cles, mot_cle, index + 1)
        options, bonne_etiquette = _options_qcm(mot_cle, distracteurs, index)

        if niveau_difficulte == "Débutant":
            question = "Quel terme complète correctement l'extrait suivant ?"
            longueur_extrait = 165
        elif niveau_difficulte == "Avancé":
            question = (
                "Quelle notion complète l'extrait et permet d'en interpréter le rôle "
                "dans le document ?"
            )
            longueur_extrait = 210
        else:
            question = "Quelle réponse complète correctement l'extrait suivant ?"
            longueur_extrait = 180

        lignes.append(f"{index + 1}. {question}")
        lignes.append(f"   « {_raccourcir(phrase_trouee, longueur_extrait)} »")
        for etiquette, option in options:
            lignes.append(f"   {etiquette}. {_formater_option(option)}")
        lignes.append(f"   Réponse correcte : {bonne_etiquette}")
        lignes.append(
            f"   Explication : niveau {niveau_difficulte} - {_raccourcir(phrase, 230)}"
        )
        lignes.append("")

    return "\n".join(lignes).strip()


def _generer_flashcards_fiables(texte, niveau_difficulte="Intermédiaire"):
    """Construit des flashcards centrées sur les notions importantes."""
    niveau_difficulte = _normaliser_niveau_difficulte(niveau_difficulte)
    phrases = _classer_phrases_importantes(texte, nombre=10)
    mots_cles = _extraire_mots_cles(texte, nombre=10)
    lignes = []

    for index, mot_cle in enumerate(mots_cles[:5]):
        phrase = _trouver_phrase_pour_mot_cle(mot_cle, phrases)
        if niveau_difficulte == "Débutant":
            question = f"Que signifie simplement « {_formater_option(mot_cle)} » ?"
            longueur_reponse = 190
        elif niveau_difficulte == "Avancé":
            question = (
                f"Quel rôle joue « {_formater_option(mot_cle)} » dans le raisonnement "
                "du document ?"
            )
            longueur_reponse = 260
        else:
            question = f"Que faut-il retenir sur « {_formater_option(mot_cle)} » ?"
            longueur_reponse = 230

        lignes.extend(
            [
                f"### Flashcard {index + 1}",
                f"**Question :** {question}",
                f"**Réponse :** {_raccourcir(phrase, longueur_reponse)}",
                "",
            ]
        )

    return "\n".join(lignes).strip()


def _generer_questions_examen_fiables(texte, niveau_difficulte="Intermédiaire"):
    """Construit des questions ouvertes avec éléments de réponse attendus."""
    niveau_difficulte = _normaliser_niveau_difficulte(niveau_difficulte)
    phrases = _classer_phrases_importantes(texte, nombre=8)
    mots_cles = _extraire_mots_cles(texte, nombre=8)
    if niveau_difficulte == "Débutant":
        modeles_questions = [
            "Définissez « {mot} » avec vos propres mots.",
            "Expliquez pourquoi « {mot} » est important dans le document.",
            "Citez une information du document liée à « {mot} ».",
            "Présentez simplement le rôle de « {mot} ».",
            "Résumez l'idée principale associée à « {mot} ».",
        ]
        longueur_elements = 190
    elif niveau_difficulte == "Avancé":
        modeles_questions = [
            "Analysez le rôle de « {mot} » dans la logique générale du document.",
            "Discutez les conditions, limites ou implications de « {mot} ».",
            "Comparez « {mot} » avec une autre notion centrale du document.",
            "Justifiez l'intérêt de « {mot} » à partir des éléments du contexte.",
            "Construisez une réponse argumentée montrant comment « {mot} » structure le cours.",
        ]
        longueur_elements = 270
    else:
        modeles_questions = [
            "Expliquez le principe de « {mot} » et son intérêt dans le cours.",
            "Analysez le rôle de « {mot} » dans la compréhension du document.",
            "Comparez « {mot} » avec une autre notion importante du cours.",
            "Montrez, à partir du document, comment « {mot} » peut être appliqué.",
            "Discutez les avantages, limites ou conditions d'utilisation de « {mot} ».",
        ]
        longueur_elements = 230

    lignes = []
    for index, modele_question in enumerate(modeles_questions):
        mot_cle = mots_cles[index % len(mots_cles)]
        phrase = _trouver_phrase_pour_mot_cle(mot_cle, phrases)
        lignes.append(f"{index + 1}. {modele_question.format(mot=_formater_option(mot_cle))}")
        lignes.append(f"   Éléments attendus : {_raccourcir(phrase, longueur_elements)}")
        lignes.append("")

    return "\n".join(lignes).strip()


def _generer_contenu_fiable(texte, type_contenu, niveau_difficulte="Intermédiaire"):
    """Route la génération extractive vers le bon support pédagogique."""
    generateurs = {
        "resume": _generer_resume_fiable,
        "quiz": _generer_quiz_fiable,
        "flashcards": _generer_flashcards_fiables,
        "examen": _generer_questions_examen_fiables,
    }
    return generateurs[type_contenu](texte, niveau_difficulte)


def _corriger_sortie_locale(
    contenu,
    texte,
    type_contenu,
    configuration_modele,
    niveau_difficulte="Intermédiaire",
):
    """Remplace une sortie locale faible par un support pédagogique fiable."""
    if not _est_modele_local(configuration_modele):
        return contenu

    if _sortie_trop_faible(contenu, type_contenu):
        return _generer_contenu_fiable(texte, type_contenu, niveau_difficulte)

    return contenu


def generer_resume(
    texte,
    configuration_modele,
    contexte_rag=None,
    niveau_difficulte="Intermédiaire",
):
    """Génère un résumé clair et structuré du cours."""
    contexte_utilisable, erreur = _preparer_contexte_generation(texte, contexte_rag)
    if erreur:
        return erreur

    niveau_difficulte = _normaliser_niveau_difficulte(niveau_difficulte)
    consigne_niveau = _consigne_niveau(niveau_difficulte)
    prompt = f"""
Tu es un assistant pédagogique.
À partir du contexte suivant, génère un résumé clair, structuré et adapté au niveau {niveau_difficulte}.
N'utilise pas d'informations extérieures au contexte.
Réponds uniquement en français.

Consignes pour le niveau {niveau_difficulte} :
{consigne_niveau}

Contexte :
{contexte_utilisable}

Format attendu :
- Titre du résumé
- Idée générale
- Notions principales
- Points essentiels
- Conclusion courte
"""
    contenu = generer_texte(prompt, configuration_modele)
    return _corriger_sortie_locale(
        contenu,
        contexte_utilisable,
        "resume",
        configuration_modele,
        niveau_difficulte,
    )


def generer_quiz(
    texte,
    configuration_modele,
    contexte_rag=None,
    niveau_difficulte="Intermédiaire",
):
    """Génère un quiz QCM basé sur le document source."""
    contexte_utilisable, erreur = _preparer_contexte_generation(texte, contexte_rag)
    if erreur:
        return erreur

    niveau_difficulte = _normaliser_niveau_difficulte(niveau_difficulte)
    consigne_niveau = _consigne_niveau(niveau_difficulte)
    prompt = f"""
Tu es un assistant pédagogique.
À partir du contexte suivant, génère 5 questions QCM en français adaptées au niveau {niveau_difficulte}.
Chaque question doit contenir exactement 4 propositions : A, B, C et D.
Après chaque question, indique clairement la réponse correcte.
Ajoute une courte explication fondée sur le contexte.
N'utilise pas d'informations extérieures au contexte.

Consignes pour le niveau {niveau_difficulte} :
{consigne_niveau}

Contexte :
{contexte_utilisable}

Format attendu :
1. Question ...
   A. ...
   B. ...
   C. ...
   D. ...
   Réponse correcte : ...
   Explication : ...
"""
    contenu = generer_texte(prompt, configuration_modele)
    return _corriger_sortie_locale(
        contenu,
        contexte_utilisable,
        "quiz",
        configuration_modele,
        niveau_difficulte,
    )


def generer_flashcards(
    texte,
    configuration_modele,
    contexte_rag=None,
    niveau_difficulte="Intermédiaire",
):
    """Génère des flashcards de révision."""
    contexte_utilisable, erreur = _preparer_contexte_generation(texte, contexte_rag)
    if erreur:
        return erreur

    niveau_difficulte = _normaliser_niveau_difficulte(niveau_difficulte)
    consigne_niveau = _consigne_niveau(niveau_difficulte)
    prompt = f"""
Tu es un assistant pédagogique.
À partir du contexte suivant, génère 5 flashcards en français adaptées au niveau {niveau_difficulte}.
Chaque flashcard doit contenir une question et une réponse courte, claire et utile pour la révision.
N'utilise pas d'informations extérieures au contexte.

Consignes pour le niveau {niveau_difficulte} :
{consigne_niveau}

Contexte :
{contexte_utilisable}

Format attendu :
Flashcard 1
Question : ...
Réponse : ...
"""
    contenu = generer_texte(prompt, configuration_modele)
    return _corriger_sortie_locale(
        contenu,
        contexte_utilisable,
        "flashcards",
        configuration_modele,
        niveau_difficulte,
    )


def generer_questions_examen(
    texte,
    configuration_modele,
    contexte_rag=None,
    niveau_difficulte="Intermédiaire",
):
    """Génère des questions ouvertes de type examen."""
    contexte_utilisable, erreur = _preparer_contexte_generation(texte, contexte_rag)
    if erreur:
        return erreur

    niveau_difficulte = _normaliser_niveau_difficulte(niveau_difficulte)
    consigne_niveau = _consigne_niveau(niveau_difficulte)
    prompt = f"""
Tu es un assistant pédagogique.
À partir du contexte suivant, génère 5 questions ouvertes de type examen en français adaptées au niveau {niveau_difficulte}.
Les questions doivent évaluer la compréhension, l'analyse et la capacité à expliquer les notions du cours selon le niveau choisi.
Ajoute des éléments attendus après chaque question.
N'utilise pas d'informations extérieures au contexte.

Consignes pour le niveau {niveau_difficulte} :
{consigne_niveau}

Contexte :
{contexte_utilisable}

Format attendu :
1. Question ouverte ...
   Éléments attendus : ...
"""
    contenu = generer_texte(prompt, configuration_modele)
    return _corriger_sortie_locale(
        contenu,
        contexte_utilisable,
        "examen",
        configuration_modele,
        niveau_difficulte,
    )
