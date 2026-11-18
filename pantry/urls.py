from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("add/", views.add_ingredient, name="add_ingredient"),
    path("remove/<int:pk>/", views.remove_ingredient, name="remove_ingredient"),
]
