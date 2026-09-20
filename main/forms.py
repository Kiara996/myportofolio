from django.core.exceptions import ValidationError
from django.forms import DateInput, ModelForm, TextInput, Textarea, URLInput, Select, PasswordInput, CharField

from main.models import Experience, Project

class ProjectForm(ModelForm):
    secret_code = CharField(
        widget=PasswordInput(attrs={"placeholder": "Masukkan koentji"}),
        label="Koentji",
        required=True
    )

    def clean_image_url(self):
        image_url = self.cleaned_data.get("image_url") or ""

        if "drive.google.com" in image_url and "thumbnail?id=" not in image_url:
            raise ValidationError(
                """Link Google Drive harus dalam format thumbnail, contoh: 
                https://drive.google.com/thumbnail?id=FILE_ID&sz=w1000. 
                Link folder atau link 'file/d/.../view' tidak bisa ditampilkan 
                sebagai gambar."""
            )

        return image_url

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

        help_texts = {
            "image_url": (
                "Kalau pakai Google Drive klik kanan gambar > Share > "
                "\"Anyone with the link\", lalu ambil FILE_ID dari link tersebut "
                "dan susun jadi https://drive.google.com/thumbnail?id=FILE_ID&sz=w1000. "
                "Link folder atau link 'view' biasa tidak akan tampil."
            ),
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
        
class ExperienceForm(ModelForm):
    secret_code = CharField(
        widget=PasswordInput(attrs={"placeholder": "Masukkan koentji"}),
        label="Koentji",
        required=True
    )
    
    class Meta:
        model = Experience
        fields = [
            "title",
            "description",
            "category",
            "thumbnail",
            "ended_at",
        ]
        
        labels = {
            "title": "Nama Pengalaman",
            "description": "Deskripsi Pengalaman",
            "category": "Kategori Pengalaman",
            "thumbnail": "URL Thumbnail",
            "ended_at": "Tanggal Selesai",
        }
        
        help_texts = {
            "thumbnail": (
                "Kalau pakai Google Drive klik kanan gambar > Share > "
                "\"Anyone with the link\", lalu ambil FILE_ID dari link tersebut "
                "dan susun jadi https://drive.google.com/thumbnail?id=FILE_ID&sz=w1000. "
                "Link folder atau link 'view' biasa tidak akan tampil."
            ),
        }
        
        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Freelance Photographer di Bali",
                    "maxLength": 255,
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Ceritakan pengalamanmu...",
                    "rows": 4,
                }
            ),
            "category": Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "thumbnail": URLInput(
                attrs={
                    "placeholder": "https://drive.google.com/thumbnail?id=...&sz=w1000",
                }
            ),
            "ended_at": DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }