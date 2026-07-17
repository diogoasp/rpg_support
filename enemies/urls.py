from django.urls import path
from . import views
app_name='enemies'
urlpatterns=[path('mestre/inimigos/',views.enemy_list,name='list'),path('mestre/inimigos/criar/',views.edit,name='create'),path('mestre/inimigos/<int:pk>/',views.detail,name='detail'),path('mestre/inimigos/<int:pk>/editar/',views.edit,name='edit'),path('mestre/inimigos/<int:pk>/desativar/',views.deactivate,name='deactivate')]
