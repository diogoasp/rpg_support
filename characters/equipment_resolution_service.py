from inventory.models import InventoryItem


def equipment_options_for_creation(creation):
    options = []
    if creation.combat_style:
        options.extend(creation.combat_style.initial_equipment)
    if creation.profession and not creation.profession.is_no_profession:
        options.extend(creation.profession.initial_items)
    return options


def create_initial_equipment(character, creation):
    created = []
    for name in equipment_options_for_creation(creation):
        item, _ = InventoryItem.objects.get_or_create(
            character=character,
            name=name,
            defaults={"description": "Equipamento inicial do assistente de criação.", "quantity": 1, "is_visible": True, "is_active": True},
        )
        created.append(item)
    return created
