from django.forms import DateInput, ModelForm, TextInput, Textarea, URLInput, Select, PasswordInput, CharField

from main.models import Project

class ProjectForm(ModelForm):
    secret_code = CharField(
        widget=PasswordInput(attrs={"placeholder": "Masukkan koentji"}),
        label="Koentji",
        required=True
    )
    class Meta:
        model = Project
        fields = [
            "title",
            "story",
            "camera_gear",
            "capture_settings",
            "editing_software",
            "location_taken",
            "taken_at",
            "image_url",
        ]

        labels = {
            "title": "Nama Proyek",
            "story": "Cerita Proyek",
            "camera_gear": "Gear Kamera",
            "capture_settings": "Pengaturan Penyimpanan",
            "editing_software": "Software Edit",
            "location_taken": "Lokasi Foto Diambil",
            "taken_at": "Waktu Foto Diambil",
            "image_url": "URL Gambar",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Foto Landscape di Pegunungan",
                    "maxlength": 255,
                }
            ),
            "story": Textarea(
                attrs={
                    "placeholder": "Ceritakan pengalamanmu dalam proyek ini...",
                    "rows": 4,
                }
            ),
            "camera_gear": TextInput(
                attrs={
                    "placeholder": "Canon EOS R5, 24-70mm f/2.8",
                }
            ),
            "capture_settings": TextInput(
                attrs={
                    "placeholder": "ISO 1600, f/2.8, 1/125s",
                }
            ),
            "editing_software": Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "location_taken": TextInput(
                attrs={
                    "placeholder": "Pegunungan di Jawa",
                }
            ),
            "taken_at": DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "image_url": URLInput(
                attrs={
                    "placeholder": "https://drive.google.com/thumbnail?id=...&sz=w1000",
                }
            ),
        }