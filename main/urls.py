from django.urls import path

from main.views import (
    create_project,
    delete_project,
    update_project,
    toggle_star,
    get_project_json,
    get_experience_json,
    show_main,
    show_experience,
    show_project,
    create_experience,
    delete_experience,
    update_experience,
    register,
    login_user,
    logout_user,
)
    
app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path("experience/", show_experience, name="show_experience"),
    path("project/", show_project, name="show_project"),
    path("project/add/", create_project, name="create_project"),
    path("project/<uuid:project_id>/edit/", update_project, name="update_project"),
    path("project/<uuid:project_id>/delete/", delete_project, name="delete_project"),
    path("project/<uuid:project_id>/star/", toggle_star, name="toggle_star"),
    path("experience/add/", create_experience, name="create_experience"),
    path("experience/<uuid:experience_id>/edit/", update_experience, name="update_experience"),
    path("experience/<uuid:experience_id>/delete/", delete_experience, name="delete_experience"),
    path("api/project/", get_project_json, name="get_project_json"),
    path("api/experience/", get_experience_json, name="get_experience_json"),
]
