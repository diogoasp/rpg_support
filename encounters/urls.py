from django.urls import path
from . import views
app_name='encounters'
urlpatterns=[path('mestre/<slug:slug>/encontros/',views.encounter_list,name='list'),path('mestre/<slug:slug>/encontros/gerar/',views.generator,name='generator'),path('mestre/<slug:slug>/encontros/proposta/',views.revise,name='revise'),path('mestre/<slug:slug>/encontros/salvar/',views.save,name='save'),path('mestre/<slug:slug>/encontros/<int:pk>/',views.detail,name='detail'),path('mestre/<slug:slug>/encontros/<int:pk>/duplicar/',views.duplicate,name='duplicate'),path('mestre/<slug:slug>/encontros/<int:pk>/cancelar/',views.cancel,name='cancel')]
