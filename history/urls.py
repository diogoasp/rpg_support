from django.urls import path
from . import views
app_name='history'
urlpatterns=[path('historia/',views.record_list,name='list'),path('historia/<int:pk>/',views.detail,name='detail'),path('historia/<int:pk>/midia/<str:kind>/',views.protected_media,name='media'),path('mestre/<slug:slug>/historia/',views.master_list,name='master_list'),path('mestre/<slug:slug>/historia/criar/',views.edit,name='create'),path('mestre/<slug:slug>/historia/<int:pk>/editar/',views.edit,name='edit'),path('mestre/<slug:slug>/historia/<int:pk>/publicar/',views.publication,name='publication')]
