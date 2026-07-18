from django.core.management import call_command
from django.core.management.base import BaseCommand
from accounts.models import User
from campaigns.models import Campaign
from characters.models import Character,CharacterCondition,CharacterFeature,CharacterSkill,CharacterTechnique,Skill
from inventory.models import InventoryItem
from ships.models import Ship
from maps.models import CampaignMap
from history.models import SessionRecord
from enemies.models import Enemy,EnemyAction,EnemyFaction,EnemyFeature
from encounters.models import Encounter,EncounterEnemy,EncounterParticipant
from datetime import date
class Command(BaseCommand):
 def handle(self,*a,**o):
  call_command('seed_skills'); master,_=User.objects.update_or_create(username='diogo',defaults={'role':'master','email':'diogo@example.test'})
  if not master.has_usable_password(): master.set_password('demo-rpg-2026'); master.save()
  campaign,_=Campaign.objects.update_or_create(slug='tambores_libertacao',defaults={'name':'Tambores da Libertação','master':master,'description':'','is_active':True})
  for i,name in enumerate(('Lina Maré','Caio Bruma'),1):
   player,_=User.objects.update_or_create(username=f'jogador{i}',defaults={'role':'player'}); player.set_password('demo-rpg-2026'); player.save(); campaign.players.add(player)
   ch,_=Character.objects.update_or_create(campaign=campaign,user=player,defaults={'name':name,'level':3,'species':'Humano','profession':'Navegador' if i==1 else 'Médico','combat_style':'Lâminas' if i==1 else 'Corpo a corpo','max_hp':30,'current_hp':25,'max_power_points':8,'current_power_points':6,'haki_declared':i==1})
   for skill in Skill.objects.all(): CharacterSkill.objects.get_or_create(character=ch,skill=skill,defaults={'is_proficient':skill.name in ('Percepção','Atletismo')})
   CharacterTechnique.objects.update_or_create(character=ch,name='Manobra da Maré',defaults={'description':'Uma manobra original de demonstração.','is_featured':True,'cost':'2 PP'})
   CharacterFeature.objects.update_or_create(character=ch,name='Olhar do Horizonte',defaults={'source':'Antecedente','description':'Percebe mudanças distantes.'})
   CharacterCondition.objects.update_or_create(character=ch,name='Inspirado',defaults={'description':'Motivado pela tripulação.','is_active':True})
   InventoryItem.objects.update_or_create(character=ch,name='Carta do Arquipélago',defaults={'description':'Carta fictícia desenhada à mão.','quantity':1}); InventoryItem.objects.update_or_create(character=ch,name='Ordem de missão',defaults={'description':'Documento fictício da campanha.','quantity':1})
  Ship.objects.filter(campaign=campaign,belongs_to_crew=True,is_active=True).exclude(name='Caravela revolucionária de apoio').update(belongs_to_crew=False)
  Ship.objects.update_or_create(campaign=campaign,name='Caravela revolucionária de apoio',defaults={'category':'small','description':'Dimensões aproximadas: 6 m de largura × 15 m de comprimento × 18 m de altura\r\nDeques: 1\r\nVelocidade sugerida: 8 nós, aproximadamente 16 km/h\r\nVelocidade mínima após danos severos: 4 nós, aproximadamente 8 km/h\r\nMunição inicial: 5 bolas de chumbo','max_hp':150,'current_hp':44,'resistance_class':10,'resistance_bonus':10,'speed':'8','max_crew':20,'current_crew':6,'navigation_resources':'adequate','cannons':1,'facilities':'Cabine coletiva: seis redes ou beliches apertados.\r\nEnfermaria improvisada: pequena mesa, armário e dois leitos.\r\nOficina e depósito: ferramentas, madeira e peças de reposição.\r\nCozinha e despensa: provisões e água.','notes':'Estado inicial: funcional, mas antiga e com manutenção atrasada.\r\nCapacidade de provisões: 8 dias para seis pessoas.','is_active':True,'belongs_to_crew':True})
  public,_=CampaignMap.objects.update_or_create(campaign=campaign,title='Mapa do Mar de Aurora',defaults={'description':'Rota fictícia para demonstração.','map_type':'sea','is_visible_to_players':True,'is_featured':True})
  CampaignMap.objects.update_or_create(campaign=campaign,title='Ilha ainda desconhecida',defaults={'description':'Mapa privado do mestre.','map_type':'island','is_visible_to_players':False})
  specific,_=CampaignMap.objects.update_or_create(campaign=campaign,title='Carta pessoal de Lina',defaults={'description':'Mapa liberado especificamente.','map_type':'treasure','is_visible_to_players':True})
  specific.visible_to_users.set(campaign.players.filter(username='jogador1'))
  SessionRecord.objects.update_or_create(campaign=campaign,session_number=1,defaults={'title':'A partida','session_date':date(2026,1,10),'summary':'A tripulação iniciou sua jornada pelos mares fictícios.','is_published':True})
  SessionRecord.objects.update_or_create(campaign=campaign,session_number=2,defaults={'title':'A névoa','session_date':date(2026,1,17),'summary':'Uma névoa misteriosa mudou a rota.','is_published':True})
  SessionRecord.objects.update_or_create(campaign=campaign,session_number=3,defaults={'title':'Próximo horizonte','session_date':date(2026,1,24),'summary':'Rascunho para a próxima sessão.','is_published':False})
  coast,_=EnemyFaction.objects.update_or_create(slug='guarda-costeira',defaults={'name':'Guarda Costeira','description':'Patrulha fictícia.'}); raiders,_=EnemyFaction.objects.update_or_create(slug='saqueadores-do-nevoeiro',defaults={'name':'Saqueadores do Nevoeiro','description':'Grupo fictício.'})
  specs=[('vigia-do-cais','Vigia do Cais','minion','simple','normal',12,False,coast),('patrulheiro-do-farol','Patrulheiro do Farol','standard','simple','normal',20,False,coast),('batedor-da-nevoa','Batedor da Névoa','minion','simple','normal',14,False,raiders),('fera-das-dunas','Fera das Dunas','creature','simple','normal',24,False,None),('guarda-do-arsenal','Guarda do Arsenal','standard','moderate','normal',32,False,coast),('artifice-do-recife','Artífice do Recife','special','moderate','normal',36,False,raiders),('capitao-da-patrulha','Capitão da Patrulha','elite','moderate','normal',58,False,coast),('comandante-da-bruma','Comandante da Bruma','boss','complex','normal',95,True,raiders),('colosso-adormecido','Colosso Adormecido','special','complex','narrative',180,True,None),('soberano-da-tempestade','Soberano da Tempestade','special','complex','not_recommended',300,True,None)]
  made={}
  for slug,name,category,complexity,mode,hp,boss,faction in specs:
   e,_=Enemy.objects.update_or_create(slug=slug,defaults={'name':name,'category':category,'operational_complexity':complexity,'encounter_mode':mode,'max_hp':hp,'is_boss':boss,'faction':faction,'challenge_rating':max(1,hp//15),'is_available_for_generator':mode in ('normal','reduced'),'description':'Adversário original para demonstração.'}); made[slug]=e
   EnemyAction.objects.update_or_create(enemy=e,name='Investida',defaults={'description':'Ataque descrito de forma textual.','damage_text':'dano conforme a preparação do mestre'})
   EnemyFeature.objects.update_or_create(enemy=e,name='Instinto de preservação',defaults={'feature_type':'comportamento','description':'Tenta recuar quando fica em desvantagem.'})
  chars=list(campaign.characters.all())
  for name,difficulty,status,slug in [('Patrulha do cais','easy','ready','vigia-do-cais'),('Emboscada na névoa','medium','ready','guarda-do-arsenal'),('Proposta do farol','medium','draft','capitao-da-patrulha')]:
   enc,_=Encounter.objects.update_or_create(campaign=campaign,name=name,defaults={'difficulty':difficulty,'status':status,'estimated_difficulty':difficulty,'created_by':master,'generation_parameters':{'seed':'demo'}})
   for ch in chars: EncounterParticipant.objects.get_or_create(encounter=enc,character=ch)
   EncounterEnemy.objects.update_or_create(encounter=enc,enemy=made[slug],defaults={'quantity':2 if difficulty=='easy' else 1,'display_name':made[slug].name})
  self.stdout.write(self.style.SUCCESS('Dados das Fases 1 a 4 criados/atualizados.'))
