import Spells 
from Level import *
import mods.API_RitualSpells.API_RitualSpells as API_RitualSpells

class TestRitualSpell(API_RitualSpells.RitualSpell):
	def on_init(self):
		API_RitualSpells.RitualSpell.on_init(self)
		self.name = 'Test Ritual'
		self.level = 1
		self.max_charges = 12
		self.tags = [Tags.Arcane]

		self.range = 20
		self.requires_los = False


		self.pillar_burst_radius = 1
		self.pillars_always_active = True

		self.exclude_allies_from_aoe = True

		self.cast_only_when_enemy_in_aoe = True

		# test in_any_aoe by subscribing to player's on pass event

	def on_cast_tile(self, x, y):
		#assert(False)
		damage = 5
		self.caster.level.deal_damage(x, y, damage, Tags.Lightning, self)

	def get_description(self):
		return ("A test ritual").format(**self.fmt_dict())

Spells.all_player_spell_constructors.append(TestRitualSpell)

class TestRitualSpell2(TestRitualSpell):
	def on_init(self):
		TestRitualSpell.on_init(self)
		self.name = 'Test Ritual 2'
		
		self.pillar_burst_radius = 0
		self.include_edges = True
		self.include_inner_area = False
		self.pillars_always_active = True

		self.cast_only_when_enemy_in_aoe = False

		self.exclude_allies_from_aoe = True

Spells.all_player_spell_constructors.append(TestRitualSpell2)



class TestPentagram(API_RitualSpells.PentagramRitual):
	def on_init(self):
		API_RitualSpells.PentagramRitual.on_init(self)
		self.name = 'Pentagram Ritual'
		self.level = 1
		self.max_charges = 12
		self.tags = [Tags.Arcane]

		self.range = 20
		self.requires_los = False

		self.pillar_health = 200

		self.pillars_fly = True

	def on_cast_tile(self, x, y):
		API_RitualSpells.PentagramRitual.on_cast_tile(self, x, y) 
		pass

	def get_description(self):
		return "A test spell"

Spells.all_player_spell_constructors.append(TestPentagram)