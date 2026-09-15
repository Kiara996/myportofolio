from django.urls import path

from main.views import create_project, show_main, show_experience, show_project

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("project/", show_project, name="show_project"),
    path("project/add/", create_project, name="create_project"),
]   