from django.contrib import admin
from .models import SessionRecord
@admin.register(SessionRecord)
class SessionRecordAdmin(admin.ModelAdmin):
 list_display=('session_number','title','campaign','session_date','is_published','published_at'); list_filter=('campaign','is_published','session_date'); search_fields=('title','summary'); list_select_related=('campaign',); readonly_fields=('created_at','updated_at','published_at'); ordering=('-session_date','-session_number')
