import os
import django
import pandas as pd
from django.db import connection

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from recommender.models import Internship  # adjust import path

Internship.objects.all().delete()
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='recommender_internship';")



# Load CSV
df = pd.read_csv(r"C:\Users\aryan jadhav\Downloads\intenship_data_project.xls")
df = df.dropna(subset=['Skills'])
df = df.iloc[:7000]  

# Iterate and create Internship objects
for idx, row in df.iterrows():
    skills = str(row['Skills']).strip()
    skills_list = skills.split('  ')[1:]

    Internship.objects.create(
        title=row['Title'],
        description=row['Description'],
        company=row.get('Company', ''),
        location=row.get('Locations', ''),
        duration=row.get('Duration', ''),
        stipend=row.get('Stipend', ''),
        job_type=row.get('Job Type', 'on-site'),
        skills_required=skills_list,
        vector_id=idx
    )

print(f"{len(df)} internships imported successfully!")
