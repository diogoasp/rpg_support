from django.urls import path
from . import views
app_name='maps'
urlpatterns=[path('mapas/',views.player_list,name='list'),path('mapas/<int:pk>/<str:kind>/',views.protected_file,name='file'),path('mestre/<slug:slug>/mapas/',views.master_list,name='master_list'),path('mestre/<slug:slug>/mapas/criar/',views.edit,name='create'),path('mestre/<slug:slug>/mapas/<int:pk>/editar/',views.edit,name='edit'),path('mestre/<slug:slug>/mapas/<int:pk>/visibilidade/',views.visibility,name='visibility'),path('mestre/<slug:slug>/mapas/<int:pk>/desativar/',views.deactivate,name='deactivate')]
