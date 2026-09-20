import json
import uuid

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Project
from portofolio import settings


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
        self.project = Project.objects.create(
            title="Golden Hour di Rooftop Fasilkom",
            story="Diambil saat sore terakhir sebelum UAS, mengejar cahaya yang cuma muncul sepuluh menit.",
            camera_gear="Fujifilm X-T30 II, lensa 35mm f/1.4",
            capture_settings="f/2.0, 1/500s, ISO 200",
            editing_software="lightroom",
            location_taken="Rooftop Gedung A Fasilkom UI",
        )

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

    def test_project_page_shows_edit_control(self):
        response = self.client.get(reverse("main:show_project"))

        self.assertContains(
            response,
            f'href="{reverse("main:update_project", args=[self.project.id])}"',
        )


class ProjectJsonApiTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title="Golden Hour di Rooftop Fasilkom",
            story="Diambil saat sore terakhir sebelum UAS, mengejar cahaya yang cuma muncul sepuluh menit.",
            camera_gear="Fujifilm X-T30 II, lensa 35mm f/1.4",
            capture_settings="f/2.0, 1/500s, ISO 200",
            editing_software="lightroom",
            location_taken="Rooftop Gedung A Fasilkom UI",
        )

    def test_api_returns_json_content_type(self):
        response = self.client.get(reverse("main:get_project_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_api_returns_all_projects(self):
        response = self.client.get(reverse("main:get_project_json"))
        data = json.loads(response.content)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["model"], "main.project")
        self.assertEqual(data[0]["fields"]["title"], self.project.title)

    def test_api_filters_by_title_query(self):
        Project.objects.create(
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
        self.project = Project.objects.create(
            title="Golden Hour di Rooftop Fasilkom",
            story="Diambil saat sore terakhir sebelum UAS.",
            camera_gear="Fujifilm X-T30 II, lensa 35mm f/1.4",
            capture_settings="f/2.0, 1/500s, ISO 200",
            editing_software="lightroom",
            location_taken="Rooftop Gedung A Fasilkom UI",
        )
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
        self.project = Project.objects.create(
            title="Golden Hour di Rooftop Fasilkom",
            story="Diambil saat sore terakhir sebelum UAS, mengejar cahaya yang cuma muncul sepuluh menit.",
            camera_gear="Fujifilm X-T30 II, lensa 35mm f/1.4",
            capture_settings="f/2.0, 1/500s, ISO 200",
            editing_software="lightroom",
            location_taken="Rooftop Gedung A Fasilkom UI",
        )

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