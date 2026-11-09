import uuid

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from main.models import Experience, Project


class ProjectAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.visitor = User.objects.create_user(username="visitor", password="test-password")
        self.project = Project.objects.create(
            title="Portfolio", story="My website", camera_gear="Fujifilm X-T30 II",
            capture_settings="f/2.0, 1/500s, ISO 200", editing_software="lightroom",
        )
        self.list_url = reverse("api:project-list")
        self.detail_url = reverse("api:project-detail", args=[self.project.id])
        self.star_url = reverse("api:project-star", args=[self.project.id])
        self.payload = {
            "title": "New project", "story": "A useful app", "camera_gear": "Sony A7 III",
            "capture_settings": "f/8, 15s, ISO 100", "editing_software": "photoshop",
        }

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.project.id))
        self.assertFalse(response.data[0]["is_starred"])
        self.assertNotIn("fields", response.data[0])
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)

    def test_search_and_empty_results(self):
        response = self.client.get(self.list_url, {"title": "PORT"})
        self.assertEqual(len(response.data), 1)
        response = self.client.get(self.list_url, {"title": "not-found"})
        self.assertEqual(response.data, [])

    def test_missing_project(self):
        url = reverse("api:project-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_and_visitor_cannot_write(self):
        for user in (None, self.visitor):
            self.client.force_authenticate(user=user)
            self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
            self.assertEqual(self.client.patch(self.detail_url, {"title": "Changed"}, format="json").status_code, 403)
            self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertEqual(Project.objects.count(), 1)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Portfolio")

    def test_owner_can_create(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Project.objects.filter(pk=response.data["id"]).exists())

    def test_validation(self):
        self.client.force_authenticate(user=self.owner)
        for changes, field in [
            ({"title": "   "}, "title"),
            ({"title": '<img src="x" onerror="alert(1)">'}, "title"),
            ({"image_url": "javascript:alert(1)"}, "image_url"),
        ]:
            response = self.client.post(self.list_url, {**self.payload, **changes}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)
        self.assertEqual(Project.objects.count(), 1)

    def test_patch_put_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.story, "My website")
        response = self.client.put(self.detail_url, {"title": "Incomplete"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())

    def test_star_requires_login_and_toggles(self):
        self.assertEqual(self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(self.star_url)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)

    def test_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            **self.payload, "star_count": 99, "is_starred": True,
            "starred_by_names": "forged", "starred_by": [self.visitor.id],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])

    def test_staff_and_editor_cannot_manage_tutorial_projects(self):
        self.visitor.is_staff = True
        self.visitor.save()
        self.visitor.groups.add(Group.objects.create(name="Editor"))
        self.client.force_authenticate(user=self.visitor)
        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrong_method(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.delete(self.list_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Project.objects.count(), 1)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username="owner", password="test-password")
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value
        response = client.post(
            self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ExperienceAPITestBase(APITestCase):
    """Fixture bersama: empat peran dari Tugas 4 + satu experience."""

    def setUp(self):
        # Database uji selalu kosong, jadi grup Editor harus dibuat sendiri.
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.editor = User.objects.create_user(username="editor", password="test-password")
        self.editor.groups.add(Group.objects.create(name="Editor"))
        self.regular = User.objects.create_user(
            username="regular", password="test-password", email="regular@example.com",
        )
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP", description="Membantu mahasiswa.", category="part-time",
        )
        self.list_url = reverse("api:experience-list")
        self.detail_url = reverse("api:experience-detail", args=[self.experience.id])
        self.star_url = reverse("api:experience-star", args=[self.experience.id])
        self.payload = {
            "title": "Freelance Photographer",
            "description": "Dokumentasi acara.",
            "category": "freelance",
        }

    def assertExperienceUnchanged(self):
        """Pastikan database tidak berubah, bukan hanya status HTTP-nya."""
        self.assertEqual(Experience.objects.count(), 1)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Asisten Dosen PBP")
        self.assertEqual(self.experience.description, "Membantu mahasiswa.")
        self.assertEqual(self.experience.category, "part-time")


class ExperienceReadAPITest(ExperienceAPITestBase):
    def test_visitor_can_read_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.experience.id))
        self.assertEqual(response.data[0]["category_display"], "Part-Time")
        self.assertEqual(response.data[0]["status_display"], "Sedang berlangsung")
        self.assertFalse(response.data[0]["is_starred"])
        self.assertNotIn("fields", response.data[0])
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)

    def test_search_is_case_insensitive_and_can_be_empty(self):
        Experience.objects.create(title="Volunteer Mengajar", description="x", category="volunteer")
        response = self.client.get(self.list_url, {"title": "ASISTEN"})
        self.assertEqual([item["title"] for item in response.data], ["Asisten Dosen PBP"])
        self.assertEqual(self.client.get(self.list_url, {"title": "tidak-ada"}).data, [])

    def test_missing_experience_returns_404(self):
        self.client.force_authenticate(user=self.owner)
        missing = uuid.uuid4()
        detail = self.client.get(reverse("api:experience-detail", args=[missing]))
        star = self.client.post(reverse("api:experience-star", args=[missing]))
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(star.status_code, status.HTTP_404_NOT_FOUND)

    def test_response_does_not_leak_account_data(self):
        self.experience.starred_by.add(self.regular)
        body = self.client.get(self.list_url).content.decode()
        self.assertIn("regular", body)  # username boleh tampil
        for secret in ("regular@example.com", "owner@example.com", "password"):
            self.assertNotIn(secret, body)

    def test_is_starred_reflects_logged_in_user(self):
        self.experience.starred_by.add(self.regular)
        self.client.force_authenticate(user=self.regular)
        self.assertTrue(self.client.get(self.detail_url).data["is_starred"])
        self.client.force_authenticate(user=self.editor)
        self.assertFalse(self.client.get(self.detail_url).data["is_starred"])


class ExperienceRolePermissionAPITest(ExperienceAPITestBase):
    def test_guest_and_regular_user_cannot_write(self):
        for user in (None, self.regular):
            self.client.force_authenticate(user=user)
            for response in (
                self.client.post(self.list_url, self.payload, format="json"),
                self.client.put(self.detail_url, self.payload, format="json"),
                self.client.patch(self.detail_url, {"title": "Diretas"}, format="json"),
                self.client.delete(self.detail_url),
            ):
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertExperienceUnchanged()

    def test_editor_can_patch_and_put(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {"title": "Diubah Editor"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Diubah Editor")
        self.assertEqual(self.experience.description, "Membantu mahasiswa.")  # PATCH parsial

        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.category, "freelance")

    def test_editor_cannot_create_or_delete(self):
        self.client.force_authenticate(user=self.editor)
        self.assertEqual(
            self.client.post(self.list_url, self.payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(self.client.delete(self.detail_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertExperienceUnchanged()

    def test_owner_can_create_update_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        create = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Experience.objects.filter(pk=create.data["id"], title="Freelance Photographer").exists()
        )

        patch = self.client.patch(self.detail_url, {"title": "Diubah Owner"}, format="json")
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Diubah Owner")

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Experience.objects.filter(pk=self.experience.id).exists())

    def test_staff_without_editor_group_cannot_write(self):
        self.regular.is_staff = True
        self.regular.save()
        self.client.force_authenticate(user=self.regular)
        response = self.client.patch(self.detail_url, {"title": "Diretas"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertExperienceUnchanged()

    def test_wrong_method_returns_405(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.delete(self.list_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.get(self.star_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ExperienceValidationAPITest(ExperienceAPITestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.owner)

    def test_invalid_input_returns_400_and_saves_nothing(self):
        for changes, field in [
            ({"title": ""}, "title"),
            ({"title": "   "}, "title"),
            ({"title": "<b></b>"}, "title"),
            ({"description": "<script></script>"}, "description"),
            ({"category": "astronaut"}, "category"),
            ({"thumbnail": "javascript:alert(1)"}, "thumbnail"),
            ({"thumbnail": "https://drive.google.com/file/d/ABC/view"}, "thumbnail"),
            ({"ended_at": "bukan-tanggal"}, "ended_at"),
        ]:
            with self.subTest(field=field, changes=changes):
                response = self.client.post(self.list_url, {**self.payload, **changes}, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)
        self.assertExperienceUnchanged()

    def test_missing_required_fields_returns_400(self):
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)
        self.assertIn("description", response.data)

    def test_put_requires_full_payload_but_patch_does_not(self):
        put = self.client.put(self.detail_url, {"title": "Sebagian"}, format="json")
        self.assertEqual(put.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertExperienceUnchanged()
        patch = self.client.patch(self.detail_url, {"title": "Sebagian"}, format="json")
        self.assertEqual(patch.status_code, status.HTTP_200_OK)

    def test_patch_with_invalid_value_does_not_change_database(self):
        response = self.client.patch(self.detail_url, {"title": "<i></i>"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertExperienceUnchanged()

    def test_html_tags_are_stripped_before_saving(self):
        response = self.client.post(self.list_url, {
            **self.payload,
            "title": '<img src=x onerror="alert(1)">Fotografer',
            "description": "<script>alert(1)</script>Meliput acara",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        saved = Experience.objects.get(pk=response.data["id"])
        self.assertEqual(saved.title, "Fotografer")
        self.assertNotIn("<", saved.description)

    def test_valid_drive_thumbnail_and_ended_at_are_accepted(self):
        response = self.client.post(self.list_url, {
            **self.payload,
            "thumbnail": "https://drive.google.com/thumbnail?id=ABC&sz=w1000",
            "ended_at": "2026-10-01",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status_display"], "Selesai")
        self.assertFalse(response.data["is_ongoing"])

    def test_ended_at_can_be_cleared_with_null(self):
        self.client.patch(self.detail_url, {"ended_at": "2026-10-01"}, format="json")
        response = self.client.patch(self.detail_url, {"ended_at": None}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.experience.refresh_from_db()
        self.assertIsNone(self.experience.ended_at)

    def test_computed_and_server_fields_are_read_only(self):
        forged_id = uuid.uuid4()
        response = self.client.post(self.list_url, {
            **self.payload, "id": str(forged_id), "started_at": "2000-01-01T00:00:00Z",
            "star_count": 99, "is_starred": True, "starred_by_names": "forged",
            "starred_by": [self.regular.id], "is_ongoing": False, "status_display": "Selesai",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        saved = Experience.objects.get(title="Freelance Photographer")
        self.assertNotEqual(saved.id, forged_id)
        self.assertNotEqual(saved.started_at.year, 2000)
        self.assertEqual(saved.starred_by.count(), 0)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["status_display"], "Sedang berlangsung")


class ExperienceStarAPITest(ExperienceAPITestBase):
    def test_guest_cannot_star(self):
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.experience.starred_by.count(), 0)

    def test_every_logged_in_role_can_star_and_unstar(self):
        for user in (self.regular, self.editor, self.owner):
            self.client.force_authenticate(user=user)
            on = self.client.post(self.star_url)
            self.assertEqual(on.status_code, status.HTTP_200_OK)
            self.assertTrue(on.data["is_starred"])
            self.assertTrue(self.experience.starred_by.filter(pk=user.pk).exists())
            off = self.client.post(self.star_url)
            self.assertFalse(off.data["is_starred"])
            self.assertFalse(self.experience.starred_by.filter(pk=user.pk).exists())

    def test_star_counts_each_user_separately(self):
        self.client.force_authenticate(user=self.regular)
        self.client.post(self.star_url)
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(self.star_url)
        self.assertEqual(response.data["star_count"], 2)
        self.assertEqual(set(response.data["starred_by_names"].split(", ")), {"regular", "editor"})

    def test_star_user_comes_from_request_not_body(self):
        self.client.force_authenticate(user=self.regular)
        self.client.post(self.star_url, {"user": self.owner.id, "starred_by": [self.owner.id]}, format="json")
        self.assertEqual(list(self.experience.starred_by.all()), [self.regular])

    def test_star_does_not_change_other_fields(self):
        self.client.force_authenticate(user=self.regular)
        self.client.post(self.star_url)
        self.assertExperienceUnchanged()


class ExperienceCsrfAPITest(ExperienceAPITestBase):
    """force_authenticate melewati login dan CSRF, jadi CSRF diuji lewat .login()."""

    def logged_in_client(self, username):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username=username, password="test-password"))
        return client

    def csrf_token(self, client):
        # Halaman Experience (ensure_csrf_cookie) menyetel cookie csrftoken.
        client.get(reverse("main:show_experience"))
        return client.cookies["csrftoken"].value

    def test_session_write_without_csrf_token_is_rejected(self):
        owner = self.logged_in_client("owner")
        editor = self.logged_in_client("editor")
        regular = self.logged_in_client("regular")
        for response in (
            owner.post(self.list_url, self.payload, format="json"),
            owner.delete(self.detail_url),
            editor.patch(self.detail_url, {"title": "Diubah"}, format="json"),
            regular.post(self.star_url),
        ):
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertIn("CSRF", str(response.data["detail"]))
        self.assertExperienceUnchanged()
        self.assertEqual(self.experience.starred_by.count(), 0)

    def test_session_write_with_csrf_token_succeeds(self):
        owner = self.logged_in_client("owner")
        token = self.csrf_token(owner)
        response = owner.post(self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        regular = self.logged_in_client("regular")
        token = self.csrf_token(regular)
        response = regular.post(self.star_url, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_wrong_csrf_token_is_rejected(self):
        owner = self.logged_in_client("owner")
        self.csrf_token(owner)
        response = owner.post(self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN="salah")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertExperienceUnchanged()

    def test_read_does_not_require_csrf_token(self):
        owner = self.logged_in_client("owner")
        self.assertEqual(owner.get(self.list_url).status_code, status.HTTP_200_OK)
