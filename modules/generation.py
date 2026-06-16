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


def _generer_resume_fiable(texte):
    """Construit un résumé pédagogique fiable à partir des phrases importantes."""
    phrases_importantes = _classer_phrases_importantes(texte, nombre=6)
    mots_cles = _extraire_mots_cles(texte, nombre=8)

    lignes = [
        "### Résumé du cours",
        "",
        "**Idée générale**",
        _raccourcir(phrases_importantes[0], 280),
        "",
        "**Notions principales**",
    ]

    for mot_cle in mots_cles[:5]:
        phrase = _trouver_phrase_pour_mot_cle(mot_cle, phrases_importantes)
        lignes.append(f"- **{_formater_option(mot_cle)}** : {_raccourcir(phrase, 210)}")

    lignes.extend(["", "**Points essentiels**"])
    for phrase in phrases_importantes[:5]:
        lignes.append(f"- {_raccourcir(phrase, 230)}")

    lignes.extend(
        [
            "",
            "**À retenir**",
            "Le document doit être révisé autour des notions clés, de leurs définitions, "
            "de leurs rôles et de leurs exemples d'application.",
        ]
    )
    return "\n".join(lignes)


def _generer_quiz_fiable(texte):
    """Construit un QCM exploitable avec questions à trous et explications."""
    phrases = _classer_phrases_importantes(texte, nombre=10)
    mots_cles = _extraire_mots_cles(texte, nombre=18)
    lignes = []

    for index in range(5):
        mot_cle = mots_cles[index % len(mots_cles)]
        phrase = _trouver_phrase_pour_mot_cle(mot_cle, phrases)
        phrase_trouee = _remplacer_mot_cle_par_trou(phrase, mot_cle)
        distracteurs = _choisir_distracteurs(mots_cles, mot_cle, index + 1)
        options, bonne_etiquette = _options_qcm(mot_cle, distracteurs, index)

        lignes.append(
            f"{index + 1}. Quelle réponse complète correctement l'extrait suivant ?"
        )
        lignes.append(f"   « {_raccourcir(phrase_trouee, 180)} »")
        for etiquette, option in options:
            lignes.append(f"   {etiquette}. {_formater_option(option)}")
        lignes.append(f"   Réponse correcte : {bonne_etiquette}")
        lignes.append(f"   Explication : {_raccourcir(phrase, 210)}")
        lignes.append("")

    return "\n".join(lignes).strip()


def _generer_flashcards_fiables(texte):
    """Construit des flashcards centrées sur les notions importantes."""
    phrases = _classer_phrases_importantes(texte, nombre=10)
    mots_cles = _extraire_mots_cles(texte, nombre=10)
    lignes = []

    for index, mot_cle in enumerate(mots_cles[:5]):
        phrase = _trouver_phrase_pour_mot_cle(mot_cle, phrases)
        lignes.extend(
            [
                f"### Flashcard {index + 1}",
                f"**Question :** Que faut-il retenir sur « {_formater_option(mot_cle)} » ?",
                f"**Réponse :** {_raccourcir(phrase, 230)}",
                "",
            ]
        )

    return "\n".join(lignes).strip()


def _generer_questions_examen_fiables(texte):
    """Construit des questions ouvertes avec éléments de réponse attendus."""
    phrases = _classer_phrases_importantes(texte, nombre=8)
    mots_cles = _extraire_mots_cles(texte, nombre=8)
    modeles_questions = [
        "Expliquez le principe de « {mot} » et son intérêt dans le cours.",
        "Analysez le rôle de « {mot} » dans la compréhension du document.",
        "Comparez « {mot} » avec une autre notion importante du cours.",
        "Montrez, à partir du document, comment « {mot} » peut être appliqué.",
        "Discutez les avantages, limites ou conditions d'utilisation de « {mot} ».",
    ]

    lignes = []
    for index, modele_question in enumerate(modeles_questions):
        mot_cle = mots_cles[index % len(mots_cles)]
        phrase = _trouver_phrase_pour_mot_cle(mot_cle, phrases)
        lignes.append(f"{index + 1}. {modele_question.format(mot=_formater_option(mot_cle))}")
        lignes.append(f"   Éléments attendus : {_raccourcir(phrase, 230)}")
        lignes.append("")

    return "\n".join(lignes).strip()


def _generer_contenu_fiable(texte, type_contenu):
    """Route la génération extractive vers le bon support pédagogique."""
    generateurs = {
        "resume": _generer_resume_fiable,
        "quiz": _generer_quiz_fiable,
        "flashcards": _generer_flashcards_fiables,
        "examen": _generer_questions_examen_fiables,
    }
    return generateurs[type_contenu](texte)


def _corriger_sortie_locale(contenu, texte, type_contenu, configuration_modele):
    """Remplace une sortie locale faible par un support pédagogique fiable."""
    if not _est_modele_local(configuration_modele):
        return contenu

    if _sortie_trop_faible(contenu, type_contenu):
        return _generer_contenu_fiable(texte, type_contenu)

    return contenu


def generer_resume(texte, configuration_modele):
    """Génère un résumé clair et structuré du cours."""
    texte_utilisable, erreur = _preparer_texte(texte)
    if erreur:
        return erreur

    prompt = f"""
Génère un résumé clair, structuré et compréhensible en français du document suivant.
Le résumé doit présenter les idées principales, les notions importantes et les relations entre les concepts.

Document source :
{texte_utilisable}

Format attendu :
- Titre du résumé
- Points essentiels
- Conclusion courte
"""
    contenu = generer_texte(prompt, configuration_modele)
    return _corriger_sortie_locale(contenu, texte_utilisable, "resume", configuration_modele)


def generer_quiz(texte, configuration_modele):
    """Génère un quiz QCM basé sur le document source."""
    texte_utilisable, erreur = _preparer_texte(texte)
    if erreur:
        return erreur

    prompt = f"""
À partir du document suivant, génère un quiz de révision en français.
Le quiz doit contenir au moins 5 questions sous forme de QCM.
Chaque question doit contenir exactement 4 propositions : A, B, C et D.
Après chaque question, indique clairement la réponse correcte.

Document source :
{texte_utilisable}

Format attendu :
1. Question ...
   A. ...
   B. ...
   C. ...
   D. ...
   Réponse correcte : ...
"""
    contenu = generer_texte(prompt, configuration_modele)
    return _corriger_sortie_locale(contenu, texte_utilisable, "quiz", configuration_modele)


def generer_flashcards(texte, configuration_modele):
    """Génère des flashcards de révision."""
    texte_utilisable, erreur = _preparer_texte(texte)
    if erreur:
        return erreur

    prompt = f"""
À partir du document suivant, génère au moins 5 flashcards en français.
Chaque flashcard doit contenir une question et une réponse courte, claire et utile pour la révision.

Document source :
{texte_utilisable}

Format attendu :
Flashcard 1
Question : ...
Réponse : ...
"""
    contenu = generer_texte(prompt, configuration_modele)
    return _corriger_sortie_locale(contenu, texte_utilisable, "flashcards", configuration_modele)


def generer_questions_examen(texte, configuration_modele):
    """Génère des questions ouvertes de type examen."""
    texte_utilisable, erreur = _preparer_texte(texte)
    if erreur:
        return erreur

    prompt = f"""
À partir du document suivant, génère au moins 5 questions ouvertes de type examen en français.
Les questions doivent évaluer la compréhension, l'analyse et la capacité à expliquer les notions du cours.

Document source :
{texte_utilisable}

Format attendu :
1. Question ouverte ...
2. Question ouverte ...
3. Question ouverte ...
4. Question ouverte ...
5. Question ouverte ...
"""
    contenu = generer_texte(prompt, configuration_modele)
    return _corriger_sortie_locale(contenu, texte_utilisable, "examen", configuration_modele)
