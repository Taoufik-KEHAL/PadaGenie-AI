# PadaGenie AI

PadaGenie AI est une application Streamlit modulaire qui génère automatiquement des supports pédagogiques à partir d'un document de cours au format PDF ou TXT.

## 1. Présentation du projet

Le projet propose un pipeline IA simple et compréhensible pour un projet de fin de module en intelligence artificielle avancée. L'application extrait le texte d'un document, nettoie le contenu, génère des supports pédagogiques, puis évalue la qualité sémantique des résultats.

## 2. Objectifs

- Extraire le contenu textuel d'un fichier PDF ou TXT.
- Générer un résumé du cours.
- Générer un quiz sous forme de QCM.
- Générer des flashcards de révision.
- Générer des questions ouvertes de type examen.
- Évaluer la qualité des contenus générés avec une approche Deep Learning.

## 3. Fonctionnalités

- Upload de fichiers PDF ou TXT.
- Aperçu du texte extrait.
- Choix dynamique du moteur IA.
- Mode local fiable sans clé API pour produire des supports structurés même avec un petit modèle local.
- Génération de supports pédagogiques en français.
- Conservation des résultats avec `st.session_state`.
- Score de qualité entre 0 et 1.

Exemple de sortie attendue pour une flashcard :

```text
Flashcard 1
Question : Qu'est-ce qu'un embedding sémantique ?
Réponse : C'est une représentation vectorielle qui encode le sens d'un texte.
```

## 4. Architecture modulaire

```text
PadaGenie-AI/
├── app.py
├── pyproject.toml
├── README.md
├── modules/
│   ├── __init__.py
│   ├── extraction.py
│   ├── nettoyage.py
│   ├── modeles.py
│   ├── generation.py
│   └── evaluation.py
└── rapport/
    ├── rapport_scientifique.md
    ├── diagrammes_uml.md
    ├── diagrammes_uml_padaGenie_ai.pdf
    └── generer_pdf_uml.py
```

Le fichier `app.py` gère uniquement l'interface Streamlit. La logique métier est séparée dans les modules Python.

Remarque : le dossier `rapport/` contient les livrables académiques générés localement. Il est ignoré par Git dans ce dépôt.

## 5. Technologies utilisées

- Python 3.10 ou version supérieure
- Streamlit pour l'interface utilisateur
- pdfplumber pour l'extraction de texte PDF
- transformers et torch pour les modèles locaux Hugging Face
- OpenAI API pour la génération via modèle externe
- Google Gemini API pour la génération via modèle externe
- Groq API pour la génération rapide via modèle externe
- Sentence-Transformers pour les embeddings
- scikit-learn pour la similarité cosinus
- uv pour la gestion des dépendances

## 6. Choix du modèle IA

L'utilisateur peut choisir entre quatre moteurs de génération :

- Modèle local Hugging Face : `google/flan-t5-small` ou `google/flan-t5-base`.
- OpenAI API : `gpt-4o-mini` ou `gpt-4.1-mini`.
- Google Gemini API : `gemini-1.5-flash` ou `gemini-1.5-pro`.
- Groq API : `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `openai/gpt-oss-120b` ou `openai/gpt-oss-20b`.

Pour rendre la démonstration utilisable sans clé API, le mode local propose un mode fiable sans API. Ce mode exploite directement le document source pour construire un résumé, des QCM, des flashcards et des questions d'examen structurés. L'utilisateur peut aussi lancer un essai direct du modèle Hugging Face.

Les clés API sont saisies dans des champs sécurisés et ne sont jamais stockées dans le code, dans un fichier ou affichées dans l'interface.

## 7. Gestion des dépendances avec uv

Le projet utilise `uv` comme gestionnaire moderne de dépendances Python. Il permet :

- de créer et gérer l'environnement virtuel ;
- d'installer les dépendances ;
- de gérer le projet à partir du fichier `pyproject.toml` ;
- de lancer l'application sans activer manuellement l'environnement virtuel.

Ce projet utilise `pyproject.toml` au lieu de `requirements.txt` comme solution principale de gestion des dépendances.

## 8. Installation

Installer `uv` si nécessaire :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Installer les dépendances :

```bash
uv sync
```

## 9. Lancement de l'application

Lancer l'application avec :

```bash
uv run streamlit run app.py
```

## 10. Explication de la partie Deep Learning

La partie Deep Learning repose sur Sentence-BERT, un modèle capable de transformer un texte en vecteur numérique appelé embedding sémantique. Deux textes qui parlent du même sujet auront des vecteurs proches dans l'espace vectoriel.

Dans PadaGenie AI, le document source et les contenus générés sont transformés en embeddings. La similarité cosinus mesure ensuite leur proximité sémantique.

## 11. Explication de la partie IA générative

La génération utilise des prompts en français. Chaque fonction construit une consigne adaptée :

- résumé clair et structuré ;
- quiz QCM avec quatre propositions ;
- flashcards question-réponse ;
- questions ouvertes de type examen.

Ces prompts sont envoyés au moteur choisi par l'utilisateur : modèle local Hugging Face, OpenAI API, Google Gemini API ou Groq API.

## 12. Explication de l'évaluation qualité

Le module `evaluation.py` calcule un score entre 0 et 1 :

- score supérieur ou égal à 0.75 : bonne qualité ;
- score entre 0.50 et 0.75 : qualité moyenne ;
- score inférieur à 0.50 : qualité faible.

Ce score indique si le contenu généré reste sémantiquement lié au document original.

## 13. Limites du projet

- Les modèles locaux légers peuvent produire des réponses moins détaillées que les grands modèles via API.
- L'évaluation par similarité cosinus mesure la proximité sémantique, mais ne garantit pas l'exactitude pédagogique complète.
- Les documents PDF scannés sous forme d'image peuvent nécessiter une étape OCR non incluse.
- Les très longs documents sont limités afin d'éviter les erreurs de contexte des modèles.
