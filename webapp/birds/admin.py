from django.contrib import admin
from .models import Bird

class BirdAdmin(admin.ModelAdmin):
    list_display = ("bird_name", "recorded_datetime")
    list_filter = ['recorded_datetime']
    search_fields = ['bird_name']


admin.site.register(Bird, BirdAdmin)
