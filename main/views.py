from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from main.forms import ProjectForm
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
    context = {
        "name": "Kevin Fauzan Arjuna",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)


def show_project(request):
    context = {
        "name": "Kevin Fauzan Arjuna",
        "featured_project": Project.objects.all(),
    }
    return render(request, "project.html", context)

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