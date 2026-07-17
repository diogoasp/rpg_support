from django.core.exceptions import PermissionDenied,ValidationError
from django.db import transaction
from django.utils import timezone
from .models import SessionRecord
def _auth(user,campaign,obj=None):
 if not user.is_authenticated or not user.is_master or campaign.master_id!=user.pk: raise PermissionDenied
 if obj and obj.campaign_id!=campaign.pk: raise ValidationError('Registro de outra campanha.')
@transaction.atomic
def create_session_record(*,user,campaign,instance=None,**data):
 _auth(user,campaign,instance); obj=instance or SessionRecord(campaign=campaign)
 for k,v in data.items(): setattr(obj,k,v)
 obj.full_clean(); obj.save(); return obj
@transaction.atomic
def publish_session_record(*,user,campaign,record): _auth(user,campaign,record); record.is_published=True; record.published_at=timezone.now(); record.save(update_fields=['is_published','published_at','updated_at']); return record
@transaction.atomic
def unpublish_session_record(*,user,campaign,record): _auth(user,campaign,record); record.is_published=False; record.save(update_fields=['is_published','updated_at']); return record
