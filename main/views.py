from django.shortcuts import render

from main.models import Experience, Photograph


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


def show_photography(request):
    context = {
        "name": "Kevin Fauzan Arjuna",
        "featured_photographs": Photograph.objects.all(),
    }
    return render(request, "photography.html", context)