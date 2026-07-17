from django.core.validators import MinValueValidator
from django.db import models
from characters.validators import inventory_file_upload, inventory_image_upload, validate_document, validate_image
class InventoryItem(models.Model):
    character=models.ForeignKey('characters.Character',on_delete=models.CASCADE,related_name='inventory_items',db_index=True)
    name=models.CharField('nome',max_length=150); description=models.TextField('descrição',blank=True)
    image=models.ImageField(upload_to=inventory_image_upload,validators=[validate_image],blank=True)
    file=models.FileField(upload_to=inventory_file_upload,validators=[validate_document],blank=True)
    quantity=models.PositiveIntegerField('quantidade',null=True,blank=True,validators=[MinValueValidator(0)]); master_note=models.TextField('nota do mestre',blank=True)
    is_visible=models.BooleanField('visível',default=True,db_index=True); is_active=models.BooleanField('ativo',default=True,db_index=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=('-created_at',); indexes=[models.Index(fields=('character','is_active','is_visible'))]
    def __str__(self): return self.name
