from django import forms
from .models import InventoryItem
class InventoryItemForm(forms.ModelForm):
    class Meta: model=InventoryItem; fields=('name','description','image','file','quantity','master_note','is_visible')
