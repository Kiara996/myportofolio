from django.utils.html import strip_tags
from rest_framework import serializers

from main.models import Experience, Project


def validate_drive_thumbnail_url(value):
    """Link Google Drive harus format thumbnail, selaras dengan ProjectForm/ExperienceForm."""
    if "drive.google.com" in value and "thumbnail?id=" not in value:
        raise serializers.ValidationError(
            "Link Google Drive harus dalam format thumbnail, contoh: "
            "https://drive.google.com/thumbnail?id=FILE_ID&sz=w1000."
        )
    return value


class ProjectSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()
    editing_software_display = serializers.ReadOnlyField(source="get_editing_software_display")

    class Meta:
        model = Project
        fields = [
            "id", "title", "story", "camera_gear", "capture_settings",
            "editing_software", "editing_software_display", "location_taken",
            "taken_at", "image_url", "star_count", "is_starred", "starred_by_names",
        ]
        read_only_fields = ["id"]

    def validate_title(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Nama proyek tidak boleh hanya berisi tag HTML.")
        return value

    def validate_story(self, value):
        return strip_tags(value).strip()

    def validate_camera_gear(self, value):
        return strip_tags(value).strip()

    def validate_capture_settings(self, value):
        return strip_tags(value).strip()

    def validate_location_taken(self, value):
        return strip_tags(value).strip()

    def validate_image_url(self, value):
        return validate_drive_thumbnail_url(value or "")

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user in obj.starred_by.all()

    def get_starred_by_names(self, obj):
        return ", ".join(user.username for user in obj.starred_by.all())


class ExperienceSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()
    category_display = serializers.ReadOnlyField(source="get_category_display")
    is_ongoing = serializers.ReadOnlyField()
    status_display = serializers.ReadOnlyField()

    class Meta:
        model = Experience
        fields = [
            "id", "title", "description", "category", "category_display",
            "thumbnail", "started_at", "ended_at", "is_ongoing", "status_display",
            "star_count", "is_starred", "starred_by_names",
        ]
        read_only_fields = ["id", "started_at"]

    def validate_title(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Nama pengalaman tidak boleh hanya berisi tag HTML.")
        return value

    def validate_description(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Deskripsi pengalaman tidak boleh hanya berisi tag HTML.")
        return value

    def validate_thumbnail(self, value):
        return validate_drive_thumbnail_url(value or "")

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user in obj.starred_by.all()

    def get_starred_by_names(self, obj):
        return ", ".join(user.username for user in obj.starred_by.all())
