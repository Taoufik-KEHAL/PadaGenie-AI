# PadaGenie AI

PadaGenie AI est une application Streamlit modulaire qui génère automatiquement des supports pédagogiques en français à partir d'un document de cours PDF ou TXT.

## 1. Présentation du projet

Le projet propose un pipeline IA pédagogique : extraction du texte, nettoyage, indexation RAG, génération de contenus, évaluation sémantique et export PDF des résultats.

## 2. Objectifs

- Extraire le contenu textuel d'un fichier PDF ou TXT.
- Générer un résumé du cours.
- Générer un quiz sous forme de QCM.
- Générer des flashcards de révision.
- Générer des questions ouvertes de type examen.
- Adapter les résultats au niveau de difficulté choisi.
- Évaluer la qualité des contenus générés.
- Exporter les résultats au format PDF.

## 3. Fonctionnalités

- Upload de fichiers PDF ou TXT.
- Aperçu du texte extrait.
- Choix dynamique du moteur IA.
- Mode local avec Ollama sans clé API.
- Architecture RAG avec Sentence-BERT et FAISS.
- Choix du niveau de difficulté : débutant, intermédiaire ou avancé.
- Génération de supports pédagogiques en français.
- Score de qualité entre 0 et 1.
- Téléchargement des résultats générés en PDF.

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
│   ├── rag.py
│   ├── export_pdf.py
│   ├── modeles.py
│   ├── generation.py
│   └── evaluation.py
└── rapport/
    └── rapport_scientifique.md
```

Le fichier `app.py` gère l'interface Streamlit. La logique métier est séparée dans les modules Python.

## 5. Architecture RAG

PadaGenie AI utilise une approche RAG, Retrieval-Augmented Generation, afin de ne pas envoyer tout le document directement au modèle génératif.

Le pipeline RAG suit les étapes suivantes :

1. extraction du texte ;
2. nettoyage ;
3. découpage en chunks ;
4. création d'embeddings avec Sentence-BERT ;
5. indexation vectorielle avec FAISS ;
6. récupération des passages pertinents selon la tâche ;
7. génération du contenu pédagogique à partir du contexte récupéré.

Cette approche aide le modèle à rester lié au document source et réduit le risque de réponses hors contexte.

## 6. Choix du niveau de difficulté

L'utilisateur peut choisir le niveau pédagogique dans la sidebar :

- Débutant : vocabulaire accessible, définitions claires et questions faciles.
- Intermédiaire : contenu équilibré, compréhension et vocabulaire académique simple.
- Avancé : contenu plus approfondi, analyse et vocabulaire plus technique.

Le niveau choisi est transmis aux fonctions de génération et influence directement les prompts.

## 7. Export PDF

Après la génération d'au moins un contenu, l'utilisateur peut télécharger un fichier `resultats_padagenie_ai.pdf`.

Le PDF contient :

- le titre du projet ;
- le résumé généré ;
- le quiz généré ;
- les flashcards générées ;
- les questions d'examen générées.

## 8. Technologies utilisées

- Python 3.10 ou version supérieure
- Streamlit pour l'interface utilisateur
- pdfplumber pour l'extraction de texte PDF
- Sentence-Transformers pour les embeddings
- FAISS pour l'indexation vectorielle
- scikit-learn pour la similarité cosinus
- OpenAI API, Groq API ou Ollama local pour la génération
- fpdf2 pour l'export PDF
- uv pour la gestion des dépendances

## 9. Choix du modèle IA

L'utilisateur peut choisir entre trois moteurs de génération :

- OpenAI API : `gpt-4o-mini` ou `gpt-4.1-mini`.
- Groq API : `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `openai/gpt-oss-120b` ou `openai/gpt-oss-20b`.
- Ollama local : `llama3.2`, `llama3.1`, `mistral`, `qwen2.5`, `gemma2` ou un modèle personnalisé installé localement.

Pour utiliser Ollama localement :

```bash
ollama pull llama3.2
ollama serve
```

Les clés API sont saisies dans des champs sécurisés. Elles ne sont jamais stockées dans le code, dans un fichier ou affichées dans l'interface.

## 10. Gestion des dépendances avec uv

Le projet utilise `uv` comme gestionnaire moderne de dépendances Python. Il permet de créer l'environnement virtuel, d'installer les dépendances et de lancer l'application à partir du fichier `pyproject.toml`.

Installer les dépendances :

```bash
uv sync
```

Lancer l'application :

```bash
uv run streamlit run app.py
```

## 11. Évaluation qualité

Le module `evaluation.py` calcule un score entre 0 et 1 en comparant le document source et les contenus générés avec des embeddings Sentence-BERT et la similarité cosinus.

- Score supérieur ou égal à 0.75 : bonne qualité.
- Score entre 0.50 et 0.75 : qualité moyenne.
- Score inférieur à 0.50 : qualité faible.

## 12. Limites du projet

- Les modèles locaux Ollama peuvent produire des réponses moins détaillées que les grands modèles via API.
- L'évaluation sémantique ne garantit pas l'exactitude pédagogique complète.
- Les PDF scannés sous forme d'image peuvent nécessiter une étape OCR non incluse.
- La qualité dépend du modèle choisi, de la structure du document et de la qualité de l'extraction.
