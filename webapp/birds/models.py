from django.db import models


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
