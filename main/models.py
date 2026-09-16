import uuid
from django.db import models

class Experience(models.Model):
    EXPERIENCE_CHOICES = [
        ('internship', 'Internship'),
        ('research', 'Research'),
        ('volunteer', 'Volunteer'),
        ('part-time', 'Part-Time'),
        ('full-time', 'Full-Time'),
        ('freelance', 'Freelance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='full-time')
    thumbnail = models.URLField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        return self.title
    
    @property
    def is_ongoing(self):
        return self.ended_at is None

class Project(models.Model):
    EDITING_SOFTWARE_CHOICES = [
        ('lightroom', 'Adobe Lightroom'),
        ('photoshop', 'Adobe Photoshop'),
        ('capture-one', 'Capture One'),
        ('none', 'Tanpa Editing / Straight Out of Camera'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    story = models.TextField()
    camera_gear = models.CharField(max_length=255)
    capture_settings = models.CharField(max_length=255)
    editing_software = models.CharField(max_length=20, choices=EDITING_SOFTWARE_CHOICES, default='lightroom')
    location_taken = models.CharField(max_length=255, blank=True, null=True)
    taken_at = models.DateField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-taken_at', '-uploaded_at']

    def __str__(self):
        return self.title