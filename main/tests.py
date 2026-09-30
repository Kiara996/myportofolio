import json
import uuid

from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Project
from portofolio import settings


def login_as_superuser(client, username="owner"):
    """Buat akun pemilik portofolio (superuser) lalu login-kan client."""
    owner = User.objects.create_superuser(
        username=username, email=f"{username}@example.com", password="owner-pass-123"
    )
    client.force_login(owner)
    return owner


def make_editor(client=None, username="editor"):
    """Buat akun editor (anggota grup Editor) login-kan client jika diberikan."""
    editor = User.objects.create_user(username=username, password="editor-pass-123")
    group, _ = Group.objects.get_or_create(name="Editor")
    editor.groups.add(group)
    if client is not None:
        client.force_login(editor)
    return editor


def ssr_html(response):
    """HTML server-rendered saja, tanpa inline <script> yang mengandung
    teks 'Unstar'/'is-starred' sebagai literal string builder kartu AJAX."""
    return response.content.decode().split("<script>")[0]


def make_project(**overrides):
    data = {
        "title": "Golden Hour di Rooftop Fasilkom",
        "story": "Diambil saat sore terakhir sebelum UAS, mengejar cahaya yang cuma muncul sepuluh menit.",
        "camera_gear": "Fujifilm X-T30 II, lensa 35mm f/1.4",
        "capture_settings": "f/2.0, 1/500s, ISO 200",
        "editing_software": "lightroom",
        "location_taken": "Rooftop Gedung A Fasilkom UI",
    }
    data.update(overrides)
    return Project.objects.create(**data)


class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "Asisten Dosen PBP")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Sedang berlangsung")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Selesai")
        self.assertNotContains(response, "Sedang berlangsung")

    def test_experience_search_filters_by_title(self):
        Experience.objects.create(
            title="Volunteer Mengajar Coding",
            description="Mengajar dasar pemrograman untuk siswa SMA.",
            category="volunteer",
        )

        response = self.client.get(reverse("main:show_experience"), {"title": "Asisten"})

        self.assertContains(response, "Asisten Dosen PBP")
        self.assertNotContains(response, "Volunteer Mengajar Coding")

    def test_experience_search_returns_empty_state_when_no_match(self):
        response = self.client.get(reverse("main:show_experience"), {"title": "Tidak Ada Judul Ini"})

        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, "Tidak ada pengalaman dengan nama tersebut.")

    def test_experience_page_shows_edit_and_delete_controls(self):
        login_as_superuser(self.client)
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(
            response,
            f'href="{reverse("main:update_experience", args=[self.experience.id])}"',
        )
        self.assertContains(
            response,
            f'action="{reverse("main:delete_experience", args=[self.experience.id])}"',
        )


class ProjectPageTest(TestCase):
    def setUp(self):
        self.project = make_project()

    def test_project_url_is_accessible(self):
        response = self.client.get(reverse("main:show_project"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "project.html")

    def test_project_story_appears_when_data_exists(self):
        response = self.client.get(reverse("main:show_project"))
        self.assertContains(response, self.project.title)
        self.assertContains(response, self.project.camera_gear)

    def test_empty_state_shown_when_no_project_yet(self):
        Project.objects.all().delete()
        response = self.client.get(reverse("main:show_project"))
        self.assertContains(response, "Belum ada cerita foto")

    def test_search_returns_matching_project(self):
        response = self.client.get(reverse("main:show_project"), {"title": "Golden Hour"})
        self.assertContains(response, self.project.title)

    def test_search_returns_empty_state_when_no_match(self):
        response = self.client.get(reverse("main:show_project"), {"title": "Judul Yang Tidak Ada"})
        self.assertNotContains(response, self.project.title)
        self.assertContains(response, "Tidak ada proyek dengan nama tersebut.")

    def test_project_page_shows_edit_control_for_owner(self):
        login_as_superuser(self.client)
        response = self.client.get(reverse("main:show_project"))

        self.assertContains(
            response,
            f'href="{reverse("main:update_project", args=[self.project.id])}"',
        )


class ProjectJsonApiTest(TestCase):
    def setUp(self):
        self.project = make_project()

    def test_api_returns_json_content_type(self):
        response = self.client.get(reverse("main:get_project_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_api_returns_all_projects(self):
        response = self.client.get(reverse("main:get_project_json"))
        data = json.loads(response.content)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["pk"], str(self.project.id))
        self.assertEqual(data[0]["fields"]["title"], self.project.title)

    def test_api_filters_by_title_query(self):
        make_project(
            title="Malam di Jalan Margonda",
            story="Long exposure lampu kendaraan.",
            camera_gear="Sony A7 III, 24mm f/1.8",
            capture_settings="f/8, 15s, ISO 100",
            editing_software="photoshop",
        )

        response = self.client.get(reverse("main:get_project_json"), {"title": "Golden"})
        data = json.loads(response.content)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["fields"]["title"], self.project.title)

    def test_api_returns_empty_list_when_no_project_matches(self):
        response = self.client.get(reverse("main:get_project_json"), {"title": "Tidak Ada"})
        data = json.loads(response.content)

        self.assertEqual(data, [])

    def test_api_starred_by_uses_usernames_not_database_ids(self):
        sasha = User.objects.create_user(username="sasha", password="pass-sasha-123")
        rian = User.objects.create_user(username="rian", password="pass-rian-123")
        self.project.starred_by.add(sasha, rian)

        response = self.client.get(reverse("main:get_project_json"))
        fields = json.loads(response.content)[0]["fields"]

        self.assertEqual(fields["star_count"], 2)
        self.assertCountEqual(fields["starred_by_names"].split(", "), ["sasha", "rian"])


class ExperienceJsonApiTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )

    def test_api_returns_json_content_type(self):
        response = self.client.get(reverse("main:get_experience_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_api_returns_all_experiences(self):
        response = self.client.get(reverse("main:get_experience_json"))
        data = json.loads(response.content)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["model"], "main.experience")
        self.assertEqual(data[0]["fields"]["title"], self.experience.title)


class CreateProjectTest(TestCase):
    def setUp(self):
        login_as_superuser(self.client)
        self.valid_payload = {
            "title": "Kabut Pagi di Puncak",
            "story": "Mendaki subuh demi melihat lautan awan sebelum matahari naik.",
            "camera_gear": "Sony A7 IV, 16-35mm f/2.8",
            "capture_settings": "f/8, 1/60s, ISO 100",
            "editing_software": "lightroom",
            "location_taken": "Gunung Gede",
        }

    def test_create_project_page_is_accessible(self):
        response = self.client.get(reverse("main:create_project"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects_form.html")

    def test_create_project_succeeds_with_correct_secret_code(self):
        payload = {**self.valid_payload, "secret_code": settings.PORTFOLIO_SECRET}
        response = self.client.post(reverse("main:create_project"), payload, follow=True)

        self.assertTrue(Project.objects.filter(title=self.valid_payload["title"]).exists())
        self.assertRedirects(response, reverse("main:show_project"))

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("berhasil ditambahkan" in str(message) for message in messages_list))

    def test_create_project_fails_with_wrong_secret_code(self):
        payload = {**self.valid_payload, "secret_code": "kode-salah"}
        response = self.client.post(reverse("main:create_project"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.filter(title=self.valid_payload["title"]).exists())
        self.assertContains(response, "Koentji tidak sesuai.")

    def test_create_project_fails_when_secret_code_is_missing(self):
        response = self.client.post(reverse("main:create_project"), self.valid_payload)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.filter(title=self.valid_payload["title"]).exists())

    def test_create_project_fails_when_required_field_is_missing(self):
        payload = {**self.valid_payload, "secret_code": settings.PORTFOLIO_SECRET}
        payload.pop("title")
        response = self.client.post(reverse("main:create_project"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Project.objects.count(), 0)

    def test_create_project_fails_with_google_drive_folder_link(self):
        payload = {
            **self.valid_payload,
            "secret_code": settings.PORTFOLIO_SECRET,
            "image_url": "https://drive.google.com/drive/u/0/folders/1kouYLSbFSqJSZvNoDgwgPptZz4DFqwHi",
        }
        response = self.client.post(reverse("main:create_project"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.filter(title=self.valid_payload["title"]).exists())
        self.assertContains(response, "format thumbnail")

    def test_create_project_succeeds_with_google_drive_thumbnail_link(self):
        payload = {
            **self.valid_payload,
            "secret_code": settings.PORTFOLIO_SECRET,
            "image_url": "https://drive.google.com/thumbnail?id=1qbdofeOckPIbbj77svGTLNa2Ps8ogMET&sz=w1000",
        }
        response = self.client.post(reverse("main:create_project"), payload, follow=True)

        self.assertTrue(Project.objects.filter(title=self.valid_payload["title"]).exists())
        self.assertRedirects(response, reverse("main:show_project"))


class UpdateProjectTest(TestCase):
    def setUp(self):
        login_as_superuser(self.client)
        self.project = make_project(story="Diambil saat sore terakhir sebelum UAS.")
        self.payload = {
            "title": "Golden Hour di Rooftop Fasilkom (Edited)",
            "story": "Diambil saat sore terakhir sebelum UAS, mengejar cahaya yang cuma muncul sepuluh menit.",
            "camera_gear": "Fujifilm X-T30 II, lensa 35mm f/1.4",
            "capture_settings": "f/2.0, 1/500s, ISO 200",
            "editing_software": "photoshop",
            "location_taken": "Rooftop Gedung A Fasilkom UI",
        }

    def test_update_project_page_is_accessible(self):
        response = self.client.get(reverse("main:update_project", args=[self.project.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects_form.html")
        self.assertContains(response, self.project.title)

    def test_update_project_form_prefills_existing_data(self):
        response = self.client.get(reverse("main:update_project", args=[self.project.id]))

        self.assertContains(response, self.project.camera_gear)
        self.assertContains(response, "Simpan Perubahan")

    def test_update_project_succeeds_with_correct_secret_code(self):
        payload = {**self.payload, "secret_code": settings.PORTFOLIO_SECRET}
        response = self.client.post(
            reverse("main:update_project", args=[self.project.id]), payload, follow=True
        )

        self.project.refresh_from_db()
        self.assertEqual(self.project.title, self.payload["title"])
        self.assertEqual(self.project.editing_software, "photoshop")
        self.assertRedirects(response, reverse("main:show_project"))

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("berhasil diperbarui" in str(message) for message in messages_list))

    def test_update_project_fails_with_wrong_secret_code(self):
        payload = {**self.payload, "secret_code": "kode-salah"}
        response = self.client.post(
            reverse("main:update_project", args=[self.project.id]), payload
        )

        self.project.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.project.title, self.payload["title"])
        self.assertContains(response, "Koentji tidak sesuai.")

    def test_update_nonexistent_project_returns_404(self):
        response = self.client.get(reverse("main:update_project", args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)


class DeleteProjectTest(TestCase):
    def setUp(self):
        login_as_superuser(self.client)
        self.project = make_project()

    def test_delete_project_via_get_does_not_delete(self):
        response = self.client.get(reverse("main:delete_project", args=[self.project.id]))

        self.assertRedirects(response, reverse("main:show_project"))
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

    def test_delete_project_via_post_deletes_project(self):
        response = self.client.post(reverse("main:delete_project", args=[self.project.id]), follow=True)

        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())
        self.assertRedirects(response, reverse("main:show_project"))

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("berhasil dihapus" in str(message) for message in messages_list))

    def test_delete_nonexistent_project_returns_404(self):
        response = self.client.post(reverse("main:delete_project", args=[uuid.uuid4()]))

        self.assertEqual(response.status_code, 404)


class CreateExperienceTest(TestCase):
    def setUp(self):
        login_as_superuser(self.client)
        self.valid_payload = {
            "title": "Freelance Photographer di Bali",
            "description": "Membantu dokumentasi acara pernikahan dan prewedding.",
            "category": "freelance",
        }

    def test_create_experience_page_is_accessible(self):
        response = self.client.get(reverse("main:create_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience_form.html")

    def test_create_experience_succeeds_with_correct_secret_code(self):
        payload = {**self.valid_payload, "secret_code": settings.PORTFOLIO_SECRET}
        response = self.client.post(reverse("main:create_experience"), payload, follow=True)

        self.assertTrue(Experience.objects.filter(title=self.valid_payload["title"]).exists())
        self.assertRedirects(response, reverse("main:show_experience"))

    def test_create_experience_fails_with_wrong_secret_code(self):
        payload = {**self.valid_payload, "secret_code": "kode-salah"}
        response = self.client.post(reverse("main:create_experience"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Experience.objects.filter(title=self.valid_payload["title"]).exists())
        self.assertContains(response, "Koentji tidak sesuai coba lagi wir.")


class UpdateExperienceTest(TestCase):
    def setUp(self):
        login_as_superuser(self.client)
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )
        self.payload = {
            "title": "Asisten Dosen PBP (Edited)",
            "description": "Membantu mahasiswa memahami pengembangan web dan Django.",
            "category": "full-time",
        }

    def test_update_experience_page_is_accessible(self):
        response = self.client.get(reverse("main:update_experience", args=[self.experience.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience_form.html")
        self.assertContains(response, self.experience.title)

    def test_update_experience_succeeds_with_correct_secret_code(self):
        payload = {**self.payload, "secret_code": settings.PORTFOLIO_SECRET}
        response = self.client.post(
            reverse("main:update_experience", args=[self.experience.id]), payload, follow=True
        )

        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, self.payload["title"])
        self.assertEqual(self.experience.category, "full-time")
        self.assertRedirects(response, reverse("main:show_experience"))

    def test_update_experience_fails_with_wrong_secret_code(self):
        payload = {**self.payload, "secret_code": "kode-salah"}
        response = self.client.post(
            reverse("main:update_experience", args=[self.experience.id]), payload
        )

        self.experience.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.experience.title, self.payload["title"])
        self.assertContains(response, "Koentji tidak sesuai coba lagi wir.")

    def test_update_nonexistent_experience_returns_404(self):
        response = self.client.get(reverse("main:update_experience", args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)


class DeleteExperienceTest(TestCase):
    def setUp(self):
        login_as_superuser(self.client)
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )

    def test_delete_experience_via_get_does_not_delete(self):
        response = self.client.get(reverse("main:delete_experience", args=[self.experience.id]))

        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

    def test_delete_experience_via_post_deletes_experience(self):
        response = self.client.post(
            reverse("main:delete_experience", args=[self.experience.id]), follow=True
        )

        self.assertFalse(Experience.objects.filter(pk=self.experience.id).exists())
        self.assertRedirects(response, reverse("main:show_experience"))

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("berhasil dihapus" in str(message) for message in messages_list))

    def test_delete_nonexistent_experience_returns_404(self):
        response = self.client.post(reverse("main:delete_experience", args=[uuid.uuid4()]))

        self.assertEqual(response.status_code, 404)


class ExperienceAuthorizationTest(TestCase):
    """Experience CRUD memakai RBAC yang sama seperti Project
    create/delete khusus owner (superuser), update boleh owner atau Editor."""

    def setUp(self):
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )
        self.regular = User.objects.create_user(username="sasha", password="Sasha-Str0ng-Pass!")
        self.create_url = reverse("main:create_experience")
        self.update_url = reverse("main:update_experience", args=[self.experience.id])
        self.delete_url = reverse("main:delete_experience", args=[self.experience.id])
        self.login_url = reverse("main:login")

    def _redirect_to_login(self, target_url):
        return f"{self.login_url}?next={target_url}"

    def test_anonymous_is_redirected_on_all_experience_actions(self):
        self.assertRedirects(self.client.get(self.create_url), self._redirect_to_login(self.create_url))
        self.assertRedirects(self.client.get(self.update_url), self._redirect_to_login(self.update_url))
        self.assertRedirects(self.client.post(self.delete_url), self._redirect_to_login(self.delete_url))
        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

    def test_regular_user_gets_403_on_all_experience_actions(self):
        self.client.force_login(self.regular)

        self.assertEqual(self.client.get(self.create_url).status_code, 403)
        self.assertEqual(self.client.get(self.update_url).status_code, 403)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)
        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

    def test_editor_can_update_but_not_create_or_delete(self):
        make_editor(self.client)

        self.assertEqual(self.client.get(self.update_url).status_code, 200)
        self.assertEqual(self.client.get(self.create_url).status_code, 403)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)
        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

    def test_owner_can_access_all_experience_actions(self):
        login_as_superuser(self.client)

        self.assertEqual(self.client.get(self.create_url).status_code, 200)
        self.assertEqual(self.client.get(self.update_url).status_code, 200)

    def test_edit_and_delete_controls_only_visible_to_can_edit_users(self):
        response = self.client.get(reverse("main:show_experience"))
        self.assertNotContains(response, self.update_url)
        self.assertNotContains(response, self.delete_url)

        self.client.force_login(self.regular)
        response = self.client.get(reverse("main:show_experience"))
        self.assertNotContains(response, self.update_url)
        self.assertNotContains(response, self.delete_url)

        login_as_superuser(self.client)
        response = self.client.get(reverse("main:show_experience"))
        self.assertContains(response, self.update_url)
        self.assertContains(response, self.delete_url)


STRONG_PASSWORD = "Sasha-Str0ng-Pass!"
class RegisterTest(TestCase):
    def test_register_page_is_accessible(self):
        response = self.client.get(reverse("main:register"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "register.html")

    def test_register_creates_account_and_redirects_to_login(self):
        response = self.client.post(
            reverse("main:register"),
            {"username": "sasha", "password1": STRONG_PASSWORD, "password2": STRONG_PASSWORD},
            follow=True,
        )

        self.assertRedirects(response, reverse("main:login"))
        self.assertTrue(User.objects.filter(username="sasha").exists())
        self.assertContains(response, "Akun berhasil dibuat")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_register_stores_hashed_password(self):
        self.client.post(
            reverse("main:register"),
            {"username": "sasha", "password1": STRONG_PASSWORD, "password2": STRONG_PASSWORD},
        )
        user = User.objects.get(username="sasha")

        self.assertNotEqual(user.password, STRONG_PASSWORD)
        self.assertTrue(user.check_password(STRONG_PASSWORD))
        self.assertFalse(user.is_superuser)

    def test_register_fails_when_passwords_do_not_match(self):
        response = self.client.post(
            reverse("main:register"),
            {"username": "sasha", "password1": STRONG_PASSWORD, "password2": "beda-sekali-123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="sasha").exists())

    def test_register_fails_when_username_already_taken(self):
        User.objects.create_user(username="sasha", password=STRONG_PASSWORD)
        response = self.client.post(
            reverse("main:register"),
            {"username": "sasha", "password1": STRONG_PASSWORD, "password2": STRONG_PASSWORD},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="sasha").count(), 1)
        self.assertContains(response, "already exists")


class LoginLogoutTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sasha", password=STRONG_PASSWORD)

    def test_login_page_is_accessible(self):
        response = self.client.get(reverse("main:login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_login_with_correct_credentials_redirects_and_sets_cookies(self):
        response = self.client.post(
            reverse("main:login"), {"username": "sasha", "password": STRONG_PASSWORD}
        )

        self.assertRedirects(response, reverse("main:show_main"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)
        self.assertIn("sessionid", response.cookies)
        self.assertIn("last_login", response.cookies)
        self.assertRegex(response.cookies["last_login"].value, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

    def test_login_with_wrong_password_shows_error(self):
        response = self.client.post(
            reverse("main:login"), {"username": "sasha", "password": "password-salah"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username and password")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("last_login", response.cookies)

    def test_login_page_shows_registration_success_message(self):
        response = self.client.post(
            reverse("main:register"),
            {"username": "baru", "password1": STRONG_PASSWORD, "password2": STRONG_PASSWORD},
            follow=True,
        )

        self.assertContains(response, "Akun berhasil dibuat. Silakan login.")

    def test_logout_ends_session_and_deletes_last_login_cookie(self):
        self.client.post(reverse("main:login"), {"username": "sasha", "password": STRONG_PASSWORD})
        response = self.client.get(reverse("main:logout"))

        self.assertRedirects(response, reverse("main:show_main"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.cookies["last_login"].value, "")
        self.assertEqual(response.cookies["last_login"]["max-age"], 0)

    def test_account_still_exists_after_logout(self):
        self.client.post(reverse("main:login"), {"username": "sasha", "password": STRONG_PASSWORD})
        self.client.get(reverse("main:logout"))

        self.assertTrue(User.objects.filter(username="sasha").exists())
        self.assertTrue(self.client.login(username="sasha", password=STRONG_PASSWORD))


class NavbarAuthStatusTest(TestCase):
    def test_anonymous_visitor_sees_login_and_register(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertContains(response, f'href="{reverse("main:login")}"')
        self.assertContains(response, f'href="{reverse("main:register")}"')
        self.assertNotContains(response, f'href="{reverse("main:logout")}"')

    def test_logged_in_user_sees_username_and_logout(self):
        user = User.objects.create_user(username="sasha", password=STRONG_PASSWORD)
        self.client.force_login(user)
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, '<span class="nav-user">sasha</span>', html=False)
        self.assertContains(response, f'href="{reverse("main:logout")}"')
        self.assertNotContains(response, f'href="{reverse("main:register")}"')

    def test_navbar_username_is_not_the_portfolio_owner_name(self):
        user = User.objects.create_user(username="sasha", password=STRONG_PASSWORD)
        self.client.force_login(user)
        response = self.client.get(reverse("main:show_main"))

        self.assertContains(response, "Kevin Fauzan Arjuna")
        self.assertContains(response, '<span class="nav-user">sasha</span>', html=False)


class LastLoginCookieDisplayTest(TestCase):
    def test_default_text_when_cookie_is_missing(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertContains(response, "Sesi Terakhir Login")
        self.assertContains(response, "Belum ada sesi login / Cookie tidak ditemukan")

    def test_cookie_value_is_displayed_on_profile(self):
        self.client.cookies["last_login"] = "2026-09-28 10:15:30"
        response = self.client.get(reverse("main:show_main"))

        self.assertContains(response, "2026-09-28 10:15:30")
        self.assertNotContains(response, "Belum ada sesi login")

    def test_full_login_flow_shows_last_login_on_profile(self):
        User.objects.create_user(username="sasha", password=STRONG_PASSWORD)
        response = self.client.post(
            reverse("main:login"),
            {"username": "sasha", "password": STRONG_PASSWORD},
            follow=True,
        )

        self.assertNotContains(response, "Belum ada sesi login")

    def test_default_text_returns_after_logout(self):
        User.objects.create_user(username="sasha", password=STRONG_PASSWORD)
        self.client.post(reverse("main:login"), {"username": "sasha", "password": STRONG_PASSWORD})
        response = self.client.get(reverse("main:logout"), follow=True)

        self.assertContains(response, "Belum ada sesi login / Cookie tidak ditemukan")


class ProjectAuthorizationTest(TestCase):
    def setUp(self):
        self.project = make_project()
        self.regular = User.objects.create_user(username="sasha", password=STRONG_PASSWORD)
        self.login_url = reverse("main:login")

    def _redirect_to_login(self, target_url):
        return f"{self.login_url}?next={target_url}"

    def test_anonymous_is_redirected_to_login_on_create_page(self):
        url = reverse("main:create_project")
        response = self.client.get(url)

        self.assertRedirects(response, self._redirect_to_login(url))

    def test_anonymous_cannot_create_project(self):
        response = self.client.post(reverse("main:create_project"), {
            "title": "Tidak Boleh Masuk", "story": "x", "camera_gear": "x",
            "capture_settings": "x", "editing_software": "lightroom",
            "secret_code": settings.PORTFOLIO_SECRET,
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Project.objects.filter(title="Tidak Boleh Masuk").exists())

    def test_anonymous_cannot_delete_project(self):
        url = reverse("main:delete_project", args=[self.project.id])
        response = self.client.post(url)

        self.assertRedirects(response, self._redirect_to_login(url))
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

    def test_anonymous_is_redirected_on_update_page(self):
        url = reverse("main:update_project", args=[self.project.id])

        self.assertRedirects(self.client.get(url), self._redirect_to_login(url))

    def test_regular_user_gets_403_on_create_page(self):
        self.client.force_login(self.regular)
        response = self.client.get(reverse("main:create_project"))

        self.assertEqual(response.status_code, 403)

    def test_regular_user_cannot_create_project(self):
        self.client.force_login(self.regular)
        response = self.client.post(reverse("main:create_project"), {
            "title": "Tidak Boleh Masuk", "story": "x", "camera_gear": "x",
            "capture_settings": "x", "editing_software": "lightroom",
            "secret_code": settings.PORTFOLIO_SECRET,
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Project.objects.filter(title="Tidak Boleh Masuk").exists())

    def test_regular_user_cannot_delete_project(self):
        self.client.force_login(self.regular)
        response = self.client.post(reverse("main:delete_project", args=[self.project.id]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

    def test_regular_user_gets_403_on_update_page(self):
        self.client.force_login(self.regular)
        response = self.client.get(reverse("main:update_project", args=[self.project.id]))

        self.assertEqual(response.status_code, 403)

    def test_owner_can_open_create_page(self):
        login_as_superuser(self.client)

        self.assertEqual(self.client.get(reverse("main:create_project")).status_code, 200)

    def test_owner_can_delete_project(self):
        login_as_superuser(self.client)
        self.client.post(reverse("main:delete_project", args=[self.project.id]))

        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())

    def test_controls_hidden_from_anonymous_visitor(self):
        response = self.client.get(reverse("main:show_project"))

        self.assertNotContains(response, reverse("main:create_project"))
        self.assertNotContains(response, reverse("main:update_project", args=[self.project.id]))
        self.assertNotContains(response, reverse("main:delete_project", args=[self.project.id]))

    def test_controls_hidden_from_regular_user(self):
        self.client.force_login(self.regular)
        response = self.client.get(reverse("main:show_project"))

        self.assertNotContains(response, reverse("main:create_project"))
        self.assertNotContains(response, reverse("main:delete_project", args=[self.project.id]))

    def test_controls_visible_to_owner(self):
        login_as_superuser(self.client)
        response = self.client.get(reverse("main:show_project"))

        self.assertContains(response, reverse("main:create_project"))
        self.assertContains(response, reverse("main:delete_project", args=[self.project.id]))

    def test_project_page_stays_readable_without_login(self):
        response = self.client.get(reverse("main:show_project"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.title)


class StarProjectTest(TestCase):
    def setUp(self):
        self.project = make_project()
        self.sasha = User.objects.create_user(username="sasha", password=STRONG_PASSWORD)
        self.rian = User.objects.create_user(username="rian", password=STRONG_PASSWORD)
        self.url = reverse("main:toggle_star", args=[self.project.id])

    def test_registered_user_can_star_project(self):
        self.client.force_login(self.sasha)
        response = self.client.post(self.url)

        self.assertRedirects(response, reverse("main:show_project"))
        self.assertIn(self.sasha, self.project.starred_by.all())

    def test_second_post_removes_star(self):
        self.client.force_login(self.sasha)
        self.client.post(self.url)
        self.client.post(self.url)

        self.assertEqual(self.project.starred_by.count(), 0)

    def test_stars_from_different_users_are_counted_separately(self):
        self.client.force_login(self.sasha)
        self.client.post(self.url)
        self.client.force_login(self.rian)
        self.client.post(self.url)

        self.assertEqual(self.project.starred_by.count(), 2)
        self.assertEqual(list(self.sasha.starred_projects.all()), [self.project])

    def test_owner_can_also_star(self):
        owner = login_as_superuser(self.client)
        self.client.post(self.url)

        self.assertIn(owner, self.project.starred_by.all())

    def test_anonymous_is_redirected_to_login_and_no_star_saved(self):
        response = self.client.post(self.url)

        self.assertRedirects(response, f'{reverse("main:login")}?next={self.url}')
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_get_request_does_not_change_star(self):
        self.client.force_login(self.sasha)
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("main:show_project"))
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_star_nonexistent_project_returns_404(self):
        self.client.force_login(self.sasha)
        response = self.client.post(reverse("main:toggle_star", args=[uuid.uuid4()]))

        self.assertEqual(response.status_code, 404)

    def test_star_button_is_visible_to_anonymous_with_count(self):
        self.project.starred_by.add(self.sasha, self.rian)
        response = self.client.get(reverse("main:show_project"))

        self.assertContains(response, f'action="{self.url}"')
        self.assertContains(response, '<span class="star-count">2</span>', html=False)

    def test_button_shows_unstar_for_user_who_already_starred(self):
        self.project.starred_by.add(self.sasha)
        self.client.force_login(self.sasha)
        response = self.client.get(reverse("main:show_project"))
        html = ssr_html(response)

        self.assertIn("Unstar", html)
        self.assertIn("is-starred", html)

    def test_button_shows_star_for_user_who_has_not_starred(self):
        self.project.starred_by.add(self.rian)
        self.client.force_login(self.sasha)
        response = self.client.get(reverse("main:show_project"))
        html = ssr_html(response)

        self.assertNotIn("Unstar", html)
        self.assertNotIn("is-starred", html)

    def test_star_button_title_lists_usernames(self):
        self.project.starred_by.add(self.sasha)
        response = self.client.get(reverse("main:show_project"))

        self.assertContains(response, 'title="sasha"')


class CsrfProtectionTest(TestCase):
    def test_forms_reject_post_without_csrf_token(self):
        from django.test import Client

        strict_client = Client(enforce_csrf_checks=True)
        user = User.objects.create_user(username="sasha", password=STRONG_PASSWORD)
        response = strict_client.post(
            reverse("main:login"), {"username": "sasha", "password": STRONG_PASSWORD}
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotIn("_auth_user_id", strict_client.session)

    def test_login_form_contains_csrf_token(self):
        response = self.client.get(reverse("main:login"))

        self.assertContains(response, "csrfmiddlewaretoken")


class EditorRoleTest(TestCase):
    """Peran Editor (grup Editor) boleh mengubah, tidak boleh membuat/menghapus."""

    def setUp(self):
        self.project = make_project()
        self.update_url = reverse("main:update_project", args=[self.project.id])
        self.create_url = reverse("main:create_project")
        self.delete_url = reverse("main:delete_project", args=[self.project.id])

    def test_editor_can_open_update_page(self):
        make_editor(self.client)

        self.assertEqual(self.client.get(self.update_url).status_code, 200)

    def test_editor_can_update_project(self):
        make_editor(self.client)
        response = self.client.post(self.update_url, {
            "title": "Diubah Editor",
            "story": self.project.story,
            "camera_gear": self.project.camera_gear,
            "capture_settings": self.project.capture_settings,
            "editing_software": "photoshop",
            "secret_code": settings.PORTFOLIO_SECRET,
        })

        self.project.refresh_from_db()
        self.assertRedirects(response, reverse("main:show_project"))
        self.assertEqual(self.project.title, "Diubah Editor")

    def test_editor_cannot_create_project(self):
        make_editor(self.client)

        self.assertEqual(self.client.get(self.create_url).status_code, 403)

    def test_editor_cannot_delete_project(self):
        make_editor(self.client)
        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

    def test_regular_user_cannot_update_project(self):
        user = User.objects.create_user(username="sasha", password=STRONG_PASSWORD)
        self.client.force_login(user)

        self.assertEqual(self.client.get(self.update_url).status_code, 403)

    def test_editor_can_also_star(self):
        editor = make_editor(self.client)
        self.client.post(reverse("main:toggle_star", args=[self.project.id]))

        self.assertIn(editor, self.project.starred_by.all())

    def test_editor_sees_edit_button_only(self):
        make_editor(self.client)
        html = self.client.get(reverse("main:show_project")).content.decode()

        self.assertIn(self.update_url, html)
        self.assertNotIn(self.create_url, html)
        self.assertNotIn(self.delete_url, html)

    def test_owner_sees_all_buttons(self):
        login_as_superuser(self.client)
        html = self.client.get(reverse("main:show_project")).content.decode()

        self.assertIn(self.update_url, html)
        self.assertIn(self.create_url, html)
        self.assertIn(self.delete_url, html)

    def test_regular_user_and_anonymous_see_no_edit_buttons(self):
        User.objects.create_user(username="sasha", password=STRONG_PASSWORD)
        for logged_in in (False, True):
            if logged_in:
                self.client.login(username="sasha", password=STRONG_PASSWORD)
            html = self.client.get(reverse("main:show_project")).content.decode()
            with self.subTest(logged_in=logged_in):
                self.assertNotIn(self.update_url, html)
                self.assertNotIn(self.create_url, html)
                self.assertNotIn(self.delete_url, html)

    def test_editor_loses_access_when_removed_from_group(self):
        editor = make_editor(self.client)
        editor.groups.clear()

        self.assertEqual(self.client.get(self.update_url).status_code, 403)


class ApiSafetyTest(TestCase):
    def test_api_does_not_leak_account_details(self):
        user = User.objects.create_user(
            username="sasha", email="sasha@example.com", password=STRONG_PASSWORD
        )
        project = make_project()
        project.starred_by.add(user)
        body = self.client.get(reverse("main:get_project_json")).content.decode()

        self.assertIn('"starred_by_names": "sasha"', body)
        for secret in ("password", "sasha@example.com", "is_superuser", settings.PORTFOLIO_SECRET):
            self.assertNotIn(secret, body)