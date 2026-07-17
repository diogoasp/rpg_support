from django.core.management import call_command
from django.core.management.base import BaseCommand
from accounts.models import User
from campaigns.models import Campaign
from characters.models import Character,CharacterCondition,CharacterFeature,CharacterSkill,CharacterTechnique,Skill
from inventory.models import InventoryItem
from ships.models import Ship
from maps.models import CampaignMap
from history.models import SessionRecord
from datetime import date
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
  Ship.objects.update_or_create(campaign=campaign,is_active=True,defaults={'name':'Brisa do Horizonte','category':'medium','description':'Navio fictício da tripulação.','max_hp':120,'current_hp':96,'resistance_class':14,'resistance_bonus':3,'speed':'8 nós','max_crew':20,'current_crew':8,'navigation_resources':'adequate','cannons':4,'facilities':'Cozinha\nEnfermaria\nSala de navegação'})
  public,_=CampaignMap.objects.update_or_create(campaign=campaign,title='Mapa do Mar de Aurora',defaults={'description':'Rota fictícia para demonstração.','map_type':'sea','is_visible_to_players':True,'is_featured':True})
  CampaignMap.objects.update_or_create(campaign=campaign,title='Ilha ainda desconhecida',defaults={'description':'Mapa privado do mestre.','map_type':'island','is_visible_to_players':False})
  specific,_=CampaignMap.objects.update_or_create(campaign=campaign,title='Carta pessoal de Lina',defaults={'description':'Mapa liberado especificamente.','map_type':'treasure','is_visible_to_players':True})
  specific.visible_to_users.set(campaign.players.filter(username='jogador1'))
  SessionRecord.objects.update_or_create(campaign=campaign,session_number=1,defaults={'title':'A partida','session_date':date(2026,1,10),'summary':'A tripulação iniciou sua jornada pelos mares fictícios.','is_published':True})
  SessionRecord.objects.update_or_create(campaign=campaign,session_number=2,defaults={'title':'A névoa','session_date':date(2026,1,17),'summary':'Uma névoa misteriosa mudou a rota.','is_published':True})
  SessionRecord.objects.update_or_create(campaign=campaign,session_number=3,defaults={'title':'Próximo horizonte','session_date':date(2026,1,24),'summary':'Rascunho para a próxima sessão.','is_published':False})
  self.stdout.write(self.style.SUCCESS('Dados das Fases 1 a 3 criados/atualizados.'))
