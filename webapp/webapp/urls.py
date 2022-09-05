"""webapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from birds import views as birds_views

urlpatterns = [
    path('', birds_views.latest_birds, name="latest_birds"),
    path('last-day/', birds_views.last_day, name="last_day"),
    path('all-birds/', birds_views.list_all_birds, name="list_all_birds"),
    path('bird/', birds_views.search_bird, name="search_bird"),
    path('admin/', admin.site.urls),
    path('<str:bird_name>/', birds_views.bird_detail, name="bird_detail"),
]
