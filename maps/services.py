from django.core.exceptions import PermissionDenied,ValidationError
from django.db import transaction
from .models import CampaignMap
def _auth(user,campaign,obj=None):
 if not user.is_authenticated or not user.is_master or campaign.master_id!=user.pk: raise PermissionDenied
 if obj and obj.campaign_id!=campaign.pk: raise ValidationError('Mapa de outra campanha.')
@transaction.atomic
def create_campaign_map(*,user,campaign,instance=None,visible_to_users=(),**data):
 _auth(user,campaign,instance); obj=instance or CampaignMap(campaign=campaign)
 for k,v in data.items(): setattr(obj,k,v)
 obj.full_clean(); obj.save(); obj.visible_to_users.set(visible_to_users); return obj
@transaction.atomic
def change_map_visibility(*,user,campaign,campaign_map,is_visible,visible_to_users=()):
 _auth(user,campaign,campaign_map); campaign_map.is_visible_to_players=is_visible; campaign_map.save(update_fields=['is_visible_to_players','updated_at']); campaign_map.visible_to_users.set(visible_to_users if is_visible else ()); return campaign_map
@transaction.atomic
def deactivate_campaign_map(*,user,campaign,campaign_map): _auth(user,campaign,campaign_map); campaign_map.is_active=False; campaign_map.save(update_fields=['is_active','updated_at']); return campaign_map
