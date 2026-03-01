import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from .models import UserProfile, Internship
from .utils import extract_text_from_pdf, clean_extracted_text
from .services import recommender

logger = logging.getLogger(__name__)


def register(request):
    if request.user.is_authenticated:
        return redirect('recommender:dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            messages.success(request, "Account created successfully.")
            return redirect('recommender:dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserCreationForm()

    return render(request, 'recommender/register.html', {'form': form})


@login_required
def edit_skills(request):
    profile = request.user.profile

    if request.method == "POST":
        skills_text = request.POST.get("skills", "")

        # Convert comma-separated string → list
        skills_list = [
            skill.strip().lower()
            for skill in skills_text.split(",")
            if skill.strip()
        ]

        profile.parsed_skills = skills_list
        profile.save()

        messages.success(request, "Skills updated successfully.")
        return redirect("recommender:dashboard")

    # Convert list → comma string for display
    existing_skills = ", ".join(profile.parsed_skills)

    return render(request, "recommender/edit_skills.html", {
        "existing_skills": existing_skills
    })


@login_required
def upload_resume(request):
    if request.method == 'GET':
        return render(request, 'recommender/upload.html')

    if request.method == 'POST':
        return handle_resume_upload(request)


@require_http_methods(["POST"])
@login_required
def handle_resume_upload(request):
    if 'resume' not in request.FILES:
        messages.error(request, "No resume file uploaded")
        return redirect('recommender:upload_resume')

    resume_file = request.FILES['resume']

    if not resume_file.name.endswith('.pdf'):
        messages.error(request, "Only PDF files are supported")
        return redirect('recommender:upload_resume')

    try:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.resume_file = resume_file
        profile.save()

        pdf_path = profile.resume_file.path
        raw_text = extract_text_from_pdf(pdf_path)
        cleaned_text = clean_extracted_text(raw_text)

        structured_data = recommender.clean_resume_text(cleaned_text)

        def normalize(skills):
            return [
                skill.strip().lower()
                for skill in skills
                if skill and skill.strip()
            ]

        extracted_skills = normalize(structured_data.get('skills', []))
        existing_skills = normalize(profile.parsed_skills or [])

        updated_skills = existing_skills.copy()

        for skill in extracted_skills:
            if skill not in updated_skills:
                updated_skills.append(skill)

        profile.parsed_skills = updated_skills
        
        vector_summary = recommender.create_vector_summary(structured_data)
        profile.vector_summary = vector_summary
        profile.save()

        matches = recommender.find_matching_internships(vector_summary, resume_skills=profile.parsed_skills, top_k=10)

        recommended_internships = []
        for item in matches:
            try:
                internship_id = int(item['id'])
                score = item['final_score']

                internship = Internship.objects.get(id=internship_id)
                recommended_internships.append({
                    'internship': internship,
                    'final_score': round(score, 4),
                    'match_percentage': round(item['final_score'] * 100, 2),
                    'matching_skills_count': item.get('matching_skills_count', 0),
                    'total_skills_count': item.get('total_skills_count', 0)
                })
            except Exception as e:
                print("Skipping:", item, e)


        context = {
            'structured_data': structured_data,
            'recommended_internships': recommended_internships,
            'profile': profile
        }

        messages.success(request, "Resume analyzed successfully. Matching internships found!")

        return render(request, 'recommender/results.html', context)

    except Exception as e:
        logger.error("Resume processing error", exc_info=True)
        messages.error(request, "Error processing resume. Please try again.")
        return redirect('recommender:upload_resume')


@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    recommended_internships = []
    if profile.vector_summary:
        matches = recommender.find_matching_internships(profile.vector_summary, resume_skills=profile.parsed_skills, top_k=10)

        for item in matches:
            internship_id = item.get('id')
            score = item.get('final_score')

            if internship_id:
                try:
                    internship = Internship.objects.get(id=internship_id, is_active=True)
                    recommended_internships.append({
                        'internship': internship,
                        'final_score': round(score, 4),
                        'match_percentage': round(item['final_score'] * 100, 2)

                    })
                except Internship.DoesNotExist:
                    continue


    context = {
        'profile': profile,
        'recommended_internships': recommended_internships
    }
    return render(request, 'recommender/dashboard.html', context)



@login_required
def internship_list(request):

    queryset = Internship.objects.filter(is_active=True).order_by('-id')

    selected_location = request.GET.get("location", "").strip()
    query = request.GET.get("q", "").strip()

    # Search Filter (TITLE, DESCRIPTION, COMPANY)
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company__icontains=query)
        )

    # Location Filter
    if selected_location:
        queryset = queryset.filter(
            location__icontains=selected_location
        )

    # Pagination
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')

    try:
        internships = paginator.page(page_number)
    except PageNotAnInteger:
        internships = paginator.page(1)
    except EmptyPage:
        internships = paginator.page(paginator.num_pages)

    # Build Location Dropdown
    locations = Internship.objects.filter(
        is_active=True
    ).values_list("location", flat=True)

    city_set = set()
    for loc in locations:
        if loc:
            parts = loc.split(",")
            for city in parts:
                cleaned = city.strip()
                if cleaned:
                    city_set.add(cleaned)

    city_list = sorted(list(city_set))

    context = {
        'internships': internships,
        'selected_location': selected_location,
        'city_list': city_list,
        'query': query,
    }

    return render(request, 'recommender/internship_list.html', context)


@login_required
def internship_detail(request, internship_id):
    try:
        internship = Internship.objects.get(id=internship_id, is_active=True)
        match_score = None

        profile = UserProfile.objects.filter(user=request.user).first()
        if profile and profile.vector_summary:
            matches = recommender.find_matching_internships(profile.vector_summary, resume_skills=profile.parsed_skills, top_k=10)

            for item in matches:
                if item.get('id') == internship_id:
                    score = item.get('final_score')
                    match_score = round(item['final_score'] * 100, 2)

                    break

        context = {
            'internship': internship,
            'match_score': match_score,
            'matching_skills': item.get('matching_skills', []),
            'non_matching_skills': item.get('non_matching_skills', [])
        }
        return render(request, 'recommender/internship_detail.html', context)

    except Internship.DoesNotExist:
        messages.error(request, "Internship not found")
        return redirect('recommender:internship_list')



