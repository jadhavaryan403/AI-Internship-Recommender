# 🚀 AI-Powered Resume-Based Internship Recommender

## 📌 Project Overview

This project is an AI-driven web application that recommends internships based on a user’s uploaded resume. Instead of manually searching through listings, users upload their resume, and the system intelligently analyzes it to generate personalized internship recommendations.

The application combines resume parsing, Large Language Models (LLMs), structured output validation, embedding generation, and hybrid similarity search to rank internships by relevance.

---

## 🎯 System Workflow

### 1️⃣ Resume Upload

The user uploads their resume (PDF/DOC format).
The system extracts raw text from the document using a document parsing library.

---

### 2️⃣ LLM-Based Structured Information Extraction

The extracted resume text is sent to a Large Language Model (LLM) using **LangChain**.

Instead of receiving free-form text output, the LLM is constrained using a **Pydantic model schema**, ensuring structured and validated output.

The structured response includes fields such as:

* Technical skills
* Tools & technologies
* Domains of expertise
* Frameworks
* Soft skills

This guarantees consistency and reduces parsing errors.

---

### 3️⃣ Skill Normalization & Text Merging

The structured output from the LLM is:

* Cleaned
* Normalized
* Deduplicated
* Converted into a standardized text representation

All extracted fields are merged into a single consolidated text representation of the user profile.

Example:

```
skills : [machine learning, deep learning, python, tensorflow, data analysis]
```

This merged representation acts as the semantic identity of the user.

---

### 4️⃣ User Embedding Generation

The consolidated user profile text is converted into a single embedding vector using an embedding model.

This embedding represents the semantic meaning of the user’s skills and expertise in vector space.

---

### 5️⃣ Internship Embedding Storage

Each internship in the database has:

* Structured metadata (title, description, skills)
* Precomputed embedding vectors

These embeddings represent internship semantic meaning.
They are stored in FAISS database.
---

### 6️⃣ Hybrid Similarity Search

The system uses a hybrid ranking approach combining:

### A. Semantic Similarity Score

* Cosine similarity between:

  * User embedding
  * Internship embedding
* Captures contextual meaning

### B. Skills Match Score

* Counts direct overlap between:

  * Extracted resume skills
  * Internship required skills
* Provides explicit keyword alignment

---

### 7️⃣ Final Ranking Formula

The final internship ranking is computed using a weighted hybrid score:

```
final_score = a*similarity_score + b*skills_match_score
```

This ensures recommendations are:

* Semantically relevant
* Skill-aligned
* Context-aware
* Precisely ranked

Internships are then sorted by final score and displayed to the user.

---

## ⚙️ Core Features

### 🔐 Authentication

* User registration and login
* Protected dashboard
* Resume upload restricted to authenticated users

---

### 📄 Resume Processing Pipeline

* Resume file upload
* Text extraction
* LLM-based structured parsing (via LangChain)
* Pydantic schema validation
* Skill normalization

---

### 🧠 AI Recommendation Engine

* Embedding generation for users
* Precomputed internship embeddings
* Hybrid similarity search
* Weighted ranking mechanism

---

### 🔎 Filtering & Search

* Keyword search
* Location filtering
* Combined filtering with pagination
* Query persistence across pages

---

### 📍 Location Normalization

Internship locations are:

* Split by comma
* Cleaned and deduplicated
* Displayed in searchable dropdown

---

## 🏗️ System Architecture

The project follows Django’s MVC architecture:

### Models

* Internship model
* User model
* Resume / skill storage
* Embedding storage

### Views

* Resume processing logic
* LLM invocation
* Embedding generation
* Hybrid ranking algorithm
* Pagination & filtering

### Templates

* Responsive Bootstrap UI
* Card-based internship display
* Filter and search forms

---

## 🛠️ Tech Stack

### Backend

* Python
* Django
* Django ORM
* SQLite (development)

### AI & NLP

* LangChain
* LLM (structured output generation)
* Pydantic (schema validation)
* Open source Embedding model from hugging face
* FAISS

### Frontend

* HTML5
* Bootstrap 5
* jQuery

---

## 📂 End-to-End Flow

1. User logs in
2. User uploads resume
3. Resume text is extracted
4. Text is sent to LLM via LangChain
5. LLM returns structured output validated by Pydantic
6. Structured data is merged into unified profile text
7. Embedding is generated for the user
8. Hybrid similarity search is performed
9. Internships are ranked by combined score
10. Top recommendations are displayed

---

## 📈 Extensibility

The system is designed to support:

* Vector database integration from FAISS to (pinecone / chroma)
* Cover letter generation using LLM
* Booming career and high valued skills at present time
* Conversational career assistant (RAG-based)

---


## 🚀 How to Run the Project

### 1️⃣ Clone Repository

```bash
git clone <repository_url>
cd project_folder
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5️⃣ Run Development Server

```bash
python manage.py runserver
```

### 5️⃣ Live project link :
https://ai-internship-recommender-quh0.onrender.com

---

## 📌 Conclusion

This project implements a complete AI-powered internship recommendation pipeline that leverages structured LLM outputs, embedding-based semantic understanding, and hybrid similarity scoring to deliver personalized internship recommendations.

It bridges traditional filtering systems with modern LLM-driven intelligence to create a scalable and extensible recommendation platform.


It serves as a strong foundation for building advanced AI-powered recruitment and career recommendation systems.
