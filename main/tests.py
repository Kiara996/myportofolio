from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Project


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