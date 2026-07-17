from django.urls import path
from . import views
app_name='ships'
urlpatterns=[path('navio/',views.detail,name='detail'),path('mestre/<slug:slug>/navio/',views.manage,name='manage'),path('mestre/<slug:slug>/navio/editar/',views.edit,name='edit'),path('mestre/<slug:slug>/navio/dano/',views.damage,name='damage'),path('mestre/<slug:slug>/navio/reparar/',views.repair,name='repair'),path('mestre/<slug:slug>/navio/recursos/',views.resources,name='resources')]
