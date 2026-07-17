from django.core.management import call_command
from django.core.management.base import BaseCommand
from accounts.models import User
from campaigns.models import Campaign
from characters.models import Character,CharacterCondition,CharacterFeature,CharacterSkill,CharacterTechnique,Skill
from inventory.models import InventoryItem
class Command(BaseCommand):
 def handle(self,*a,**o):
  call_command('seed_skills'); master,_=User.objects.update_or_create(username='mestre_demo',defaults={'role':'master','email':'mestre@example.test'}); master.set_password('demo-rpg-2026'); master.save()
  campaign,_=Campaign.objects.update_or_create(slug='mares-de-aurora',defaults={'name':'Mares de Aurora','master':master,'description':'Campanha demonstrativa original.'})
  for i,name in enumerate(('Lina Maré','Caio Bruma'),1):
   player,_=User.objects.update_or_create(username=f'jogador{i}',defaults={'role':'player'}); player.set_password('demo-rpg-2026'); player.save(); campaign.players.add(player)
   ch,_=Character.objects.update_or_create(campaign=campaign,user=player,defaults={'name':name,'level':3,'species':'Humano','profession':'Navegador' if i==1 else 'Médico','combat_style':'Lâminas' if i==1 else 'Corpo a corpo','max_hp':30,'current_hp':25,'max_power_points':8,'current_power_points':6,'haki_declared':i==1})
   for skill in Skill.objects.all(): CharacterSkill.objects.get_or_create(character=ch,skill=skill,defaults={'is_proficient':skill.name in ('Percepção','Atletismo')})
   CharacterTechnique.objects.update_or_create(character=ch,name='Manobra da Maré',defaults={'description':'Uma manobra original de demonstração.','is_featured':True,'cost':'2 PP'})
   CharacterFeature.objects.update_or_create(character=ch,name='Olhar do Horizonte',defaults={'source':'Antecedente','description':'Percebe mudanças distantes.'})
   CharacterCondition.objects.update_or_create(character=ch,name='Inspirado',defaults={'description':'Motivado pela tripulação.','is_active':True})
   InventoryItem.objects.update_or_create(character=ch,name='Carta do Arquipélago',defaults={'description':'Carta fictícia desenhada à mão.','quantity':1}); InventoryItem.objects.update_or_create(character=ch,name='Ordem de missão',defaults={'description':'Documento fictício da campanha.','quantity':1})
  self.stdout.write(self.style.SUCCESS('Dados da Fase 2 criados/atualizados.'))
