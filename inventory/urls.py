from django.urls import path
from . import views
app_name='inventory'
urlpatterns=[path('personagem/inventario/',views.PlayerInventoryView.as_view(),name='player'),path('mestre/personagens/<int:pk>/inventario/',views.MasterInventoryView.as_view(),name='master'),path('mestre/personagens/<int:pk>/inventario/adicionar/',views.ItemAddView.as_view(),name='add'),path('mestre/inventario/<int:pk>/desativar/',views.ItemDeactivateView.as_view(),name='deactivate'),path('personagem/inventario/<int:pk>/arquivo/',views.ProtectedFileView.as_view(),name='file')]
