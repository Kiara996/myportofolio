from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from main.forms import ProjectForm, ExperienceForm
from main.models import Experience, Project
from portofolio import settings


def show_main(request):
    context = {
        "name": "Kevin Fauzan Arjuna",
        "npm": "2506612266",
        "study_program": "S1 Sistem Informasi",
        "bio": (
            "Information System student at Universitas Indonesia. Love to writing and sometimes drawing. Living in both side logic and creativity."
        ),
    }
    return render(request, "index.html", context)


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

    projects_json = serializers.serialize("json", projects)
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
    }
    return render(request, "project.html", context)


def delete_project(request, project_id):
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


def create_project(request):
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
    }
    return render(request, "projects_form.html", context)

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
        "name" : "Kevin Fauzan Arjuna",
        "form" : form,
    }
    return render(request, "experience_form.html", context)