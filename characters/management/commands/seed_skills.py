from django.core.management.base import BaseCommand
from django.utils.text import slugify
from characters.models import Skill
SKILLS=[('Acrobacia','dexterity'),('Adestrar Animais','wisdom'),('Arcanismo','intelligence'),('Atletismo','strength'),('Atuação','charisma'),('Enganação','charisma'),('Furtividade','dexterity'),('História','intelligence'),('Intimidação','charisma'),('Intuição','wisdom'),('Investigação','intelligence'),('Medicina','wisdom'),('Natureza','intelligence'),('Percepção','wisdom'),('Persuasão','charisma'),('Prestidigitação','dexterity'),('Religião','intelligence'),('Sobrevivência','wisdom')]
class Command(BaseCommand):
    help='Cria as perícias básicas de forma idempotente.'
    def handle(self,*a,**o):
        for order,(name,attribute) in enumerate(SKILLS): Skill.objects.update_or_create(slug=slugify(name),defaults={'name':name,'related_attribute':attribute,'sort_order':order,'is_active':True})
        self.stdout.write(self.style.SUCCESS(f'{len(SKILLS)} perícias disponíveis.'))
