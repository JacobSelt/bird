from django.db import models
from django.contrib import admin
from django.utils import timezone
from datetime import datetime



class Bird(models.Model):
    bird_id = models.IntegerField()
    bird_name = models.CharField(max_length=200)
    recorded_datetime = models.DateTimeField()
    probability = models.FloatField()

    def get_image_path(self):
        return f"birds/{self.bird_name}.jpg"  # TODO

    image_path = property(get_image_path)

    def __str__(self):
        return self.bird_name
    
    @admin.display(
        boolean=True,
        ordering='recorded_datetime',
        description='Published recently?',
    )
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.recorded_datetime <= now
