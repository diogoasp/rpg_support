from django.conf import settings
from django.db import models
MAP_TYPES=[('world','Mundo'),('sea','Mar ou rota'),('island','Ilha'),('local','Local'),('ship','Navio'),('treasure','Tesouro'),('document','Documento'),('other','Outro')]
class CampaignMap(models.Model):
 campaign=models.ForeignKey('campaigns.Campaign',on_delete=models.CASCADE,related_name='maps'); title=models.CharField('título',max_length=160); description=models.TextField('descrição',blank=True); map_type=models.CharField('tipo',max_length=20,choices=MAP_TYPES,default='other')
 image=models.ImageField('imagem',upload_to='maps/images/',blank=True); file=models.FileField('arquivo PDF',upload_to='maps/files/',blank=True)
 is_visible_to_players=models.BooleanField('visível aos jogadores',default=False); visible_to_users=models.ManyToManyField(settings.AUTH_USER_MODEL,blank=True,related_name='visible_campaign_maps',limit_choices_to={'role':'player'})
 is_featured=models.BooleanField('destaque',default=False); is_active=models.BooleanField('ativo',default=True); related_inventory_item=models.ForeignKey('inventory.InventoryItem',null=True,blank=True,on_delete=models.SET_NULL,related_name='campaign_maps')
 created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
 class Meta: ordering=('-is_featured','-created_at'); indexes=[models.Index(fields=['campaign','is_active','is_visible_to_players']),models.Index(fields=['campaign','is_featured','created_at'])]
 def __str__(self): return self.title
 @property
 def visibility_label(self):
  if not self.is_visible_to_players:return 'Privado'
  return 'Visível para jogadores selecionados' if self.visible_to_users.exists() else 'Visível para todos'
