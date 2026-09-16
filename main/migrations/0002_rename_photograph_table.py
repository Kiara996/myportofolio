from django.db import migrations


def rename_photograph_to_project(apps, schema_editor):
    table_names = schema_editor.connection.introspection.table_names()

    if "main_photograph" in table_names and "main_project" not in table_names:
        Project = apps.get_model("main", "Project")
        schema_editor.alter_db_table(Project, "main_photograph", "main_project")


def rename_project_to_photograph(apps, schema_editor):
    table_names = schema_editor.connection.introspection.table_names()

    if "main_project" in table_names and "main_photograph" not in table_names:
        Project = apps.get_model("main", "Project")
        schema_editor.alter_db_table(Project, "main_project", "main_photograph")


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(rename_photograph_to_project, rename_project_to_photograph),
    ]
