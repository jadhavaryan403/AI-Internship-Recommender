import os
import logging
from typing import List, Dict, Tuple
from pathlib import Path
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from .models import Internship
from .onnx_embeddings import ONNXEmbeddings


from django.conf import settings

logger = logging.getLogger(__name__)


# -------------------- Pydantic Schemas --------------------

class Education(BaseModel):
    degree: str = Field(description="Degree or certification")
    institution: str = Field(description="University or college name", default="")


class Experience(BaseModel):
    title: str = Field(description="Job title or role")
    company: str = Field(description="Company or organization name", default="")
    description: str = Field(description="Responsibilities and achievements")


class Project(BaseModel):
    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    technologies: str = Field(description="Technologies used")


class ResumeData(BaseModel):
    skills: List[str] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    summary: str = Field(default="")


# -------------------- Core Service --------------------

class RecommenderService:
    """
    Internship Recommendation Engine using:
    Resume → Gemini Structuring → Embeddings → FAISS Similarity Search
    """

    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY') or settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=api_key,
            temperature=0.2,
            max_output_tokens=2048
        )

        self.embeddings = ONNXEmbeddings(
        model_path=os.path.join(settings.BASE_DIR, "onnx_model")
    )

        self.vector_store_path = Path(settings.BASE_DIR) / "vector_db" / "faiss_index"
        self.vector_store = None

    # -------------------- Resume Parsing --------------------

    def clean_resume_text(self, raw_text: str) -> dict:
        """
        Use Gemini to clean messy resume text and extract structured information.
        Args:
            raw_text (str): Raw text extracted from PDF 
        Returns:
            dict: Structured resume data with skills, experience, education, etc.
        """

        parser = JsonOutputParser(pydantic_object=ResumeData)

        prompt_template = PromptTemplate(
                input_variables=["resume_text"],
                partial_variables={"format_instructions": parser.get_format_instructions()},
                template="""You are an expert resume parser. Extract structured information from the following resume text.
        The text may be messy due to 2 columns PDF extraction. Please parse it carefully and return a clean JSON object.

        Resume Text:
        {resume_text}

        {format_instructions}

        Important:
        - Extract ALL skills mentioned (technical, programming languages, frameworks, tools, soft skills) as name by removing irregular words like machine learning and not basics of machine learning.
        - For education, include degree
        - For experience, include job title, key responsibilities
        - For projects, include project name, description, and technologies used
        - As summary extract the bio if present
        - If a field is not found, use appropriate default values (empty string or empty list)

        Return ONLY the JSON object, no additional text."""
            )

        try:
            chain = prompt_template | self.llm | parser
            structured_data = chain.invoke({"resume_text": raw_text})

            return structured_data

        except Exception as e:
            logger.error(f"Resume parsing failed: {e}", exc_info=True)
            return {
                    "skills": [],
                    "education": [],
                    "experience": [],
                    "projects": [],
                    "summary": raw_text if raw_text else "Unable to parse resume"
            }


    # -------------------- Vector Summary --------------------

    def create_vector_summary(self, data: Dict) -> str:
        parts = []

        if data.get("summary"):
            parts.append(f"Summary: {data['summary']}")

        if data.get("skills"):
            parts.append("Skills: " + ", ".join(data["skills"]))

        if data.get("experience"):
            exp_blocks = []
            for e in data["experience"][:3]:
                exp_blocks.append(f"{e['title']} at {e['company']}: {e['description'][:150]}")
            parts.append("Experience: " + " | ".join(exp_blocks))

        if data.get("projects"):
            proj_blocks = []
            for p in data["projects"][:3]:
                proj_blocks.append(f"{p['name']}: {p['description']} ({p['technologies']})")
            parts.append("Projects: " + " | ".join(proj_blocks))

        if data.get("education"):
            edu_blocks = []
            for e in data["education"][:2]:
                edu_blocks.append(f"{e['degree']} from {e['institution']}")
            parts.append("Education: " + " | ".join(edu_blocks))

        return "\n".join(parts)

    # -------------------- FAISS Vector Store --------------------

    def load_or_create_vector_store(self):
        if self.vector_store:
            return self.vector_store

        if not (self.vector_store_path / "index.faiss").exists():
            raise RuntimeError(
                f"FAISS index not found at {self.vector_store_path}. "
                "Run load_internships_faiss.py first."
            )

        self.vector_store = FAISS.load_local(
            str(self.vector_store_path),
            self.embeddings,
            allow_dangerous_deserialization=True
        )

        logger.info(f"FAISS loaded with {self.vector_store.index.ntotal} vectors")
        return self.vector_store


    # -------------------- Internship Embedding --------------------

    def add_internships_to_vector_store(self, internships):
        self.load_or_create_vector_store()

        documents = []
        for internship in internships:
            content = f"""
Title: {internship.title}
Company: {internship.company}
Description: {internship.description}
Location: {internship.location}
Job Type: {internship.job_type}
Duration: {internship.duration}
Stipend: {internship.stipend}
""".strip()

            doc = Document(
                page_content=content,
                metadata={
                    "vector_id": internship.vector_id,
                    "title": internship.title,
                    "company": internship.company,
                    "id": internship.id
                }
            )
            documents.append(doc)

        if documents:
            self.vector_store.add_documents(documents)
            self.vector_store.save_local(str(self.vector_store_path))


    def get_matching_skills(self ,internship_skills_required: str ,resume_skills: str):
        matching ,non_matching = [] ,[]
        for skill in internship_skills_required:
            if skill in resume_skills:
                matching.append(skill)
            else:
                non_matching.append(skill)

        return matching ,non_matching


    # -------------------- Similarity Search --------------------

    def find_matching_internships(self, vector_summary: str, resume_skills: list, top_k: int = 10):
        self.load_or_create_vector_store()

        results = self.vector_store.similarity_search_with_score(
            vector_summary,
            k=top_k 
        )

        matches = []
        resume_skills_lower = [s.lower().strip() for s in resume_skills]

        for doc, distance in results:
            internship_id = doc.metadata.get("id")

            if internship_id is None:
                continue

            internship = Internship.objects.filter(id=internship_id).first()
            if not internship:
                continue

            # FAISS similarity
            faiss_similarity = 1 / (1 + float(distance))

            # Skill similarity
            if internship and internship.skills_required: 
                internship_skills = [s.lower() for s in internship.skills_required] 
                matched = len(set(resume_skills_lower) & set(internship_skills)) 
                skill_score = matched / len(internship_skills) if internship_skills else 0 
            else: 
                skill_score = 0

            final_score = 0.8 * skill_score + 0.2 * faiss_similarity

            matching_skills, non_matching_skills = self.get_matching_skills(internship_skills, resume_skills_lower)

            matches.append({
                "id": internship_id,
                "title": doc.metadata.get("title"),
                "company": doc.metadata.get("company"),
                "faiss_score": round(faiss_similarity, 4),
                "skill_score": round(skill_score, 4),
                "final_score": round(final_score, 4),
                "matching_skills": matching_skills,
                "non_matching_skills": non_matching_skills,
                "matching_skills_count": len(matching_skills),
                "total_skills_count": len(non_matching_skills) + len(matching_skills)
            })

        matches.sort(key=lambda x: x["final_score"], reverse=True)
        print(f"Found {len(matches)} matches,{matches}")

        return matches[:top_k]




# Global instance
recommender = RecommenderService()

