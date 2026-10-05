import datetime

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from main.forms import ProjectForm, ExperienceForm
from main.models import Experience, Project
from portofolio import settings


def can_edit(user):
    """Boleh mengubah data pemilik (superuser) atau anggota grup Editor."""
    return user.is_superuser or user.groups.filter(name="Editor").exists()


def show_main(request):
    last_login = request.COOKIES.get('last_login') or 'Belum ada sesi login / Cookie tidak ditemukan'
    context = {
        "name": "Kevin Fauzan Arjuna",
        "npm": "2506612266",
        "study_program": "S1 Sistem Informasi",
        "bio": (
            "Information System student at Universitas Indonesia. Love to writing and sometimes drawing. Living in both side logic and creativity."
        ),
        "last_login": last_login,
    }
    return render(request, "index.html", context)


def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "Kevin Fauzan Arjuna",
        "form": form,
    }
    return render(request, "register.html", context)


def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect("main:show_main")
        response.set_cookie('last_login', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return response

    context = {
        "name": "Kevin Fauzan Arjuna",
        "form": form,
    }
    return render(request, "login.html", context)


def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie('last_login')
    return response

# --------------------------------
#       EXPERIENCE FUNCTION
#---------------------------------

def show_experience(request):
    """Render halaman experience, isi diambil lewat AJAX dari get_experience_json"""
    # json_response = get_experience_json(request)
    # experiences = serializers.deserialize(
    #     "json",
    #     json_response.content.decode("utf-8"),
    # )
    # experiences = [experience.object for experience in experiences]
    # title_query = request.GET.get("title", "").strip()
    
    # context = {
    #     "name": "Kevin Fauzan Arjuna",
    #     "experience_list": experiences,
    #     "title_query": title_query,
    #     "can_edit": can_edit(request.user),
    # }
    # return render(request, "experience.html", context)
    
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.prefetch_related("starred_by")
    
    if title_query:
        experiences = experiences.filter(title__icontains=title_query)
        
    context = {
        "name": "Kevin Fauzan Arjuna",
        "experience_list": experiences,
        "title_query": title_query,
        "can_edit": can_edit(request.user),
        "form": ExperienceForm(),
    }
    return render(request, "experience.html", context)

def get_experience_json(request):
    """Endpoint json experience,  filter lewat path filter ?title="""
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.prefetch_related("starred_by")
    
    if title_query:
        experiences = experiences.filter(title__icontains=title_query)
        
    data = []
    for experience in experiences:
        starred_users = list(experience.starred_by.all())
        is_starred = request.user in starred_users if request.user.is_authenticated else False
        
        data.append({
            "pk": str(experience.id),
            "fields": {
                "title": experience.title,
                "description": experience.description,
                "category": experience.category,
                "category_display": experience.get_category_display(),
                "thumbnail": experience.thumbnail,
                "started_at": experience.started_at,
                "ended_at": experience.ended_at,
                "is_ongoing": experience.is_ongoing,
                "status_display": experience.status_display,
                "is_starred": is_starred,
                "star_count": len(starred_users),
                "starred_by_names": ", ".join(u.username for u in starred_users),
            }
        })
        
    return JsonResponse(data, safe=False)

@require_POST
def create_experience_ajax(request):
    """Add experience lewat AJAX, feedback JSON"""
    if not request.user.is_superuser:
        return JsonResponse(
            {"message": "Hanya pemilik portofolio yang dapat menambahkan pengalaman."},
            status = 403,
        )
        
    form = ExperienceForm(request.POST)
    
    if form.is_valid():
        if form.cleaned_data.get("secret_code") == settings.PORTFOLIO_SECRET:
            experience = form.save()
            return JsonResponse(
                {"message": "Pengalaman berhasil ditambahkan.", "pk": str(experience.id)},
                status=201,
            )
        form.add_error("secret_code", "Koentji tidak sesuai coba lagi wir.")        
    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

@login_required(login_url="/login/")
def toggle_experience_star(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    
    if request.method == "POST":
        if request.user in experience.starred_by.all():
            experience.starred_by.remove(request.user)
        else:
            experience.starred_by.add(request.user)
            
    return redirect("main:show_experience")

@login_required(login_url="/login/")
def delete_experience(request, experience_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    experience = get_object_or_404(Experience, pk=experience_id)
    
    if request.method == "POST":
        experience.delete()
        messages.success(request, "Experience berhasil dihapus!")
        return redirect("main:show_experience")
    
    return redirect("main:show_experience")

@login_required(login_url="/login/")
def create_experience(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    form = ExperienceForm(request.POST or None)
    
    if request.method == "POST" and form.is_valid():
        input_secret = form.cleaned_data.get("secret_code")
        
        if input_secret == settings.PORTFOLIO_SECRET:
            form.save()
            messages.success(request, "Experience baru berhasil ditambahkan!")
            return redirect("main:show_experience")
        else:
            messages.error(request, "kodemu salah wak! waduh")
            form.add_error("secret_code", "Koentji tidak sesuai coba lagi wak.")
            
    context = {
        "name": "Kevin Fauzan Arjuna",
        "form": form,
        "is_update": False,
    }
    return render(request, "experience_form.html", context)

@login_required(login_url="/login/")
def update_experience(request, experience_id):
    if not can_edit(request.user):
        raise PermissionDenied
    
    experience = get_object_or_404(Experience, pk=experience_id)
    form = ExperienceForm(request.POST or None, instance=experience)
    
    if request.method == "POST" and form.is_valid():
        input_secret = form.cleaned_data.get("secret_code")
        
        if input_secret == settings.PORTFOLIO_SECRET:
            form.save()
            messages.success(request, "Experience berhasil diperbarui!")
            return redirect("main:show_experience")
        else:
            messages.error(request, "Kodemu salah wak! waduh")
            form.add_error("secret_code", "Koentji tidak sesuai coba lagi wir.")            
        
        context = {
            "name": "Kevin Fauzan Arjuna",
            "form": form,
            "experience": experience,
            "is_update": True,
        }
        return render(request, "experience_form.html", context)





# --------------------------------
#       PROJECT FUNCTION
#---------------------------------

def show_project(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.prefetch_related('starred_by').all()

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    context = {
        "name": "Kevin Fauzan Arjuna",
        # sebagai fallback progressive enhancement kalau JS gagal.
        "featured_project": projects,
        "title_query": title_query,
        "can_edit": can_edit(request.user),
        "form": ProjectForm(),
    }
    return render(request, "project.html", context)

@require_POST
def create_project_ajax(request):
    if not request.user.is_superuser:
        return JsonResponse(
            {"message": "Hanya pemilik portofolio yang dapat menambahkan proyek."},
            status=403,
        )

    form = ProjectForm(request.POST)
    if form.is_valid():
        project = form.save()
        return JsonResponse(
            {"message": "Proyek berhasil ditambahkan.", "pk": str(project.id)},
            status=201,
        )

    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

def get_project_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.prefetch_related('starred_by').all()

    if title_query:
        projects = projects.filter(title__icontains=title_query)
        
    # Konstruksi data JSON secara manual agar bisa menyisipkan Logika Star
    data = []
    for project in projects:
        starred_users = project.starred_by.all()
        is_starred = request.user in starred_users if request.user.is_authenticated else False
        starred_by_names = ", ".join(u.username for u in starred_users)

        data.append({
            "pk": str(project.id),
            "fields": {
                "title": project.title,
                "story": project.story,
                "camera_gear": project.camera_gear,
                "capture_settings": project.capture_settings,
                "editing_software": project.editing_software,
                "editing_software_display": project.get_editing_software_display(),
                "location_taken": project.location_taken,
                "taken_at": project.taken_at,
                "image_url": project.image_url,
                "uploaded_at": project.uploaded_at,
                "is_starred": is_starred,
                "star_count": len(starred_users),
                "starred_by_names": starred_by_names,
            }
        })

    return JsonResponse(data, safe=False)

def get_experience_json(request):
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.all()
    
    if title_query:
        experiences = experiences.filter(title__icontains=title_query)
        
    experiences_json = serializers.serialize("json", experiences)
    return HttpResponse(experiences_json, content_type="application/json")




@login_required(login_url="/login/")
def delete_project(request, project_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        project.delete()
        messages.success(request, "Project berhasil dihapus!")
        return redirect("main:show_project")

    return redirect("main:show_project")

@login_required(login_url="/login/")
def create_project(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        input_secret = form.cleaned_data.get("secret_code")
        
        if input_secret == settings.PORTFOLIO_SECRET:
            form.save()
            messages.success(request, "Proyek baru berhasil ditambahkan!")
            return redirect("main:show_project")
        else:
            messages.error(request, "Kode koentji salah!")
            form.add_error("secret_code", "Koentji tidak sesuai coba lagi wir.")
    context = {
        "name": "Kevin Fauzan Arjuna",
        "form": form,
        "is_update": False,
    }
    return render(request, "projects_form.html", context)

@login_required(login_url="/login/")
def update_project(request, project_id):
    if not can_edit(request.user):
        raise PermissionDenied

    project = get_object_or_404(Project, pk=project_id)
    
    form = ProjectForm(request.POST or None, instance=project)
    
    if request.method == "POST" and form.is_valid():
        input_secret = form.cleaned_data.get("secret_code")

        if input_secret == settings.PORTFOLIO_SECRET:
            form.save()
            messages.success(request, "Proyek berhasil diperbarui!")
            return redirect("main:show_project")
        else:
            messages.error(request, "Kode koentji salah!")
            form.add_error("secret_code", "Koentji tidak sesuai coba lagi wir.")
    context = {
        "name": "Kevin Fauzan Arjuna",
        "form": form,
        "project": project,
        "is_update": True,
    }
    return render(request, "projects_form.html", context)


@login_required(login_url="/login/")
def toggle_star(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        if request.user in project.starred_by.all():
            project.starred_by.remove(request.user)
        else:
            project.starred_by.add(request.user)

    return redirect("main:show_project")