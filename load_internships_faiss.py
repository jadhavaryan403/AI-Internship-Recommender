import os
import django
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# -------------------- Django setup --------------------

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from recommender.models import Internship

# -------------------- Embeddings --------------------

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# -------------------- FAISS path (MUST match services.py) --------------------

BASE_DIR = Path(__file__).resolve().parent.parent
FAISS_PATH = BASE_DIR / "vector_db" / "faiss_index"

FAISS_PATH.parent.mkdir(parents=True, exist_ok=True)

# -------------------- Load internships --------------------

internships = Internship.objects.all().order_by("id")
print("DB rows:", internships.count())

docs = []

for internship in internships:
    skills_text = ", ".join(internship.skills_required or [])

    text = f"""
Title: {internship.title}
Company: {internship.company}
Description: {internship.description}
Skills: {skills_text}
Location: {internship.location}
Duration: {internship.duration}
Stipend: {internship.stipend}
""".strip()

    docs.append(
        Document(
            page_content=text,
            metadata={
                "id": internship.id,          # 🔥 MUST match services.py
                "title": internship.title,
                "company": internship.company,
                "location": internship.location,
                "stipend": internship.stipend,
                "duration": internship.duration
            }
        )
    )

print("Docs created:", len(docs))

# -------------------- Build FAISS --------------------

if not docs:
    print("❌ No documents found. FAISS not created.")
    exit(1)

# Remove old index if exists (clean rebuild)
if FAISS_PATH.exists():
    import shutil
    shutil.rmtree(FAISS_PATH)

vector_store = FAISS.from_documents(docs, embeddings)
vector_store.save_local(str(FAISS_PATH))

print("✅ FAISS index created successfully")
print("📦 FAISS vector count:", vector_store.index.ntotal)
