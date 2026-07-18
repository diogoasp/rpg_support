from config.protected_media import protected_file_response
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import TemplateView
from campaigns.mixins import MasterRequiredMixin, PlayerRequiredMixin
from characters.views import master_character, own_character
from .forms import InventoryItemForm
from .models import InventoryItem
from .services import add_inventory_item,deactivate_inventory_item
class PlayerInventoryView(PlayerRequiredMixin,TemplateView):
    template_name='inventory/player.html'
    def get_context_data(self,**kw): c=super().get_context_data(**kw); c['character']=own_character(self.request,self.kwargs.get('slug')); return c
class MasterInventoryView(MasterRequiredMixin,TemplateView):
    template_name='inventory/master.html'
    def get_context_data(self,**kw): c=super().get_context_data(**kw); c['character']=master_character(self.request,self.kwargs['pk']); return c
class ItemAddView(MasterRequiredMixin,View):
    def get(self,r,pk): return render(r,'inventory/partials/item_form.html',{'form':InventoryItemForm(),'character':master_character(r,pk)})
    def post(self,r,pk):
        ch=master_character(r,pk); form=InventoryItemForm(r.POST,r.FILES)
        if form.is_valid(): add_inventory_item(actor=r.user,character=ch,**form.cleaned_data); return render(r,'inventory/partials/item_list.html',{'character':master_character(r,pk),'is_master':True})
        return render(r,'inventory/partials/item_form.html',{'form':form,'character':ch},status=422)
class ItemDeactivateView(MasterRequiredMixin,View):
    def post(self,r,pk):
        item=get_object_or_404(InventoryItem.objects.select_related('character__campaign'),pk=pk,character__campaign__master=r.user); deactivate_inventory_item(actor=r.user,item=item); return render(r,'inventory/partials/item_list.html',{'character':master_character(r,item.character_id),'is_master':True})
class ProtectedFileView(PlayerRequiredMixin,View):
    def get(self,r,pk):
        item=get_object_or_404(InventoryItem,pk=pk,character__user=r.user,is_active=True,is_visible=True); return protected_file_response(item.file,attachment=True)
