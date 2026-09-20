from django.urls import path

from main.views import (
    create_project,
    delete_project,
    get_project_json,
    get_experience_json,
    show_main,
    show_experience,
    show_project,
    create_experience,
    delete_experience,
)
    
app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("project/", show_project, name="show_project"),
    path("project/add/", create_project, name="create_project"),
    path("project/<uuid:project_id>/delete/", delete_project, name="delete_project"),
    path("experience/<uuid:experience_id>/delete/", delete_experience, name="delete_experience"),
    path("experience/add/", create_experience, name="create_experience"),
    path("api/project/", get_project_json, name="get_project_json"),
    path("api/experience/", get_experience_json, name="get_experience_json"),
]
