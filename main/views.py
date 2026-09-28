import datetime

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

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


def show_experience(request):
    json_response = get_experience_json(request)
    experiences = serializers.deserialize(
        "json",
        json_response.content.decode("utf-8"),
    )
    experiences = [experience.object for experience in experiences]
    title_query = request.GET.get("title", "").strip()
    
    context = {
        "name": "Kevin Fauzan Arjuna",
        "experience_list": experiences,
        "title_query": title_query,
    }
    return render(request, "experience.html", context)


def get_project_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.all()

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    projects_json = serializers.serialize(
        "json", projects, use_natural_foreign_keys=True
    )
    return HttpResponse(projects_json, content_type="application/json")

def get_experience_json(request):
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.all()
    
    if title_query:
        experiences = experiences.filter(title__icontains=title_query)
        
    experiences_json = serializers.serialize("json", experiences)
    return HttpResponse(experiences_json, content_type="application/json")


def show_project(request):
    json_response = get_project_json(request)
    projects = serializers.deserialize(
        "json",
        json_response.content.decode("utf-8"),
    )
    projects = [project.object for project in projects]
    title_query = request.GET.get("title", "").strip()

    context = {
        "name": "Kevin Fauzan Arjuna",
        "featured_project": projects,
        "title_query": title_query,
        "can_edit": can_edit(request.user),
    }
    return render(request, "project.html", context)


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

def delete_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST":
        experience.delete()
        messages.success(request, "Experience berhasil dihapus!")
        return redirect("main:show_experience")

    return redirect("main:show_experience")


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
            form.add_error("secret_code", "Koentji tidak sesuai.")

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
            form.add_error("secret_code", "Koentji tidak sesuai.")

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

def create_experience(request):
    form = ExperienceForm(request.POST or None)
    
    if request.method == "POST" and form.is_valid():
        input_secret = form.cleaned_data.get("secret_code")
        
        if input_secret == settings.PORTFOLIO_SECRET:
            form.save()
            messages.success(request, "Experience baru berhasil ditambahkan!")
            return redirect("main:show_experience")
        else:
            messages.error(request, "Kodemu salah wak! Waduh")
            form.add_error("secret_code", "Koentji tidak sesuai coba lagi wir.")
            
    context = {
        "name": "Kevin Fauzan Arjuna",
        "form": form,
        "is_update": False,
    }
    return render(request, "experience_form.html", context)


def update_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    form = ExperienceForm(request.POST or None, instance=experience)

    if request.method == "POST" and form.is_valid():
        input_secret = form.cleaned_data.get("secret_code")

        if input_secret == settings.PORTFOLIO_SECRET:
            form.save()
            messages.success(request, "Experience berhasil diperbarui!")
            return redirect("main:show_experience")
        else:
            messages.error(request, "Kodemu salah wak! Waduh")
            form.add_error("secret_code", "Koentji tidak sesuai coba lagi wir.")

    context = {
        "name": "Kevin Fauzan Arjuna",
        "form": form,
        "experience": experience,
        "is_update": True,
    }
    return render(request, "experience_form.html", context)