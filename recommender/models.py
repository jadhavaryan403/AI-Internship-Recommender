from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile for storing resume and extracted data"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    resume_file = models.FileField(upload_to='resumes/', null=True, blank=True)
    parsed_skills = models.JSONField(default=list, blank=True, help_text="Normalized skills list")
    
    vector_summary = models.TextField(blank=True, help_text="Structured summary used for embeddings")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_skills_list(self):
        if isinstance(self.parsed_skills, list):
            return [skill.lower() for skill in self.parsed_skills]
        return []


class Internship(models.Model):
    """Internship opportunities with vector embeddings"""
    
    JOB_TYPE_CHOICES = [
        ('remote', 'Remote'),
        ('on-site', 'On-Site'),
        ('hybrid', 'Hybrid'),
    ]

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, default="Unknown Company")
    description = models.TextField()
    skills_required = models.JSONField(default=list, blank=True, help_text="List of required skills")
    
    location = models.CharField(max_length=255, blank=True)
    duration = models.CharField(max_length=100, blank=True)
    stipend = models.CharField(max_length=100, blank=True)
    
    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        default='on-site'
    )

    
    vector_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Vector store ID (FAISS/Chroma/Pinecone)"
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company}"
