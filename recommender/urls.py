from django.urls import path
from . import views

app_name = "recommender"

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    path('upload/', views.upload_resume, name='upload_resume'),
    path('edit_skills/', views.edit_skills, name='edit_skills'),
    path('internships/', views.internship_list, name='internship_list'),
    path('internships/<int:internship_id>/', views.internship_detail, name='internship_detail'),
        
]
