from django.urls import path
from . import views

app_name = "audio_panel"
urlpatterns = [
    path("mestre/audios/", views.library, name="library"),
    path("mestre/audios/criar/", views.edit, name="create"),
    path("mestre/audios/<int:pk>/editar/", views.edit, name="update"),
    path("mestre/audios/<int:pk>/desativar/", views.deactivate, name="deactivate"),
    path("mestre/audios/<int:pk>/favoritar/", views.favorite, name="favorite"),
    path("mestre/audios/<int:pk>/arquivo/", views.protected_file, name="file"),
    path("mestre/audios/<int:pk>/registrar-reproducao/", views.register_play, name="register_play"),
]
