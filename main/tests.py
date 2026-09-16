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