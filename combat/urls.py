from django.urls import path
from . import views
app_name="combat"
urlpatterns=[
 path("mestre/<slug:slug>/encontros/<int:pk>/iniciar-combate/",views.start,name="start"),
 path("mestre/combates/<int:pk>/",views.panel,name="panel"), path("mestre/combates/<int:pk>/pausar/",views.pause,name="pause"), path("mestre/combates/<int:pk>/retomar/",views.resume,name="resume"), path("mestre/combates/<int:pk>/encerrar/",views.finish,name="finish"), path("mestre/combates/<int:pk>/reabrir/",views.reopen,name="reopen"), path("mestre/combates/<int:pk>/modo/",views.mode,name="mode"), path("mestre/combates/<int:pk>/turno/",views.turn,name="turn"),
 path("mestre/combates/<int:combat_id>/combatentes/<int:pk>/dano/",views.damage,name="damage"), path("mestre/combates/<int:combat_id>/combatentes/<int:pk>/cura/",views.heal,name="heal"), path("mestre/combates/<int:combat_id>/combatentes/<int:pk>/estado/",views.state,name="state"), path("mestre/combates/<int:combat_id>/combatentes/<int:pk>/nota/",views.note,name="note"), path("mestre/combates/<int:combat_id>/combatentes/<int:pk>/derrotar/",views.defeat,name="defeat"), path("mestre/combates/<int:combat_id>/combatentes/<int:pk>/reativar/",views.reactivate,name="reactivate"), path("mestre/combates/<int:combat_id>/combatentes/<int:pk>/desfazer/",views.undo,name="undo"), path("mestre/combates/<int:combat_id>/combatentes/<int:pk>/ficha/",views.sheet,name="sheet"),
]
