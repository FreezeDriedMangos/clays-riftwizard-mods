from Level import *

# Add the base directory to sys.path for testing- allows us to run the mod directly for quick testing
import sys
sys.path.append('../..')

import Spells
import Upgrades

import mods.API_ChargedSpells.API_ChargedSpells as API_ChargedSpells

print("Basic Charged Spells Mod Loaded")
class InstakillSpell(API_ChargedSpells.BoundSpell):

	def on_init(self):
		super(InstakillSpell, self).on_init()
		self.name = "Instakill"

		self.damage = 999
		self.can_target_self = False
		self.level = 1 # self.level = 3 
		self.tags = [Tags.Arcane, Tags.Sorcery]
		self.bound_range = 10
		self.max_charges = 3
		self.required_charge = 4 # this is how many turns the spell must charge for

		self.charging_effect_color = Tags.Arcane.color


	def on_cast(self, x, y):
		# deal damage to target
		self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Arcane, self) 
		yield
		return

	
	def get_description(self):
		try:
			return ("Spend {required_charge} turns charging to prepare this spell.\n"
					"Channel the spell to charge it. Once prepared, it remains prepared until it's used again.\n"
					"Deals [{damage}_arcane:arcane] damage to a target when used after being prepared.").format(**self.fmt_dict())
		except:
			return 'error'


Spells.all_player_spell_constructors.append(InstakillSpell)

from CommonContent import SimpleMeleeAttack as SimpleMeleeAttack
class SummonEldrichIncantation(API_ChargedSpells.IncantationSpell):
	def on_init(self):
		super(SummonEldrichIncantation, self).on_init()
		self.name = "Summon Eldrich Thing"

		self.range = 4
		self.max_charges = 3
		self.tags = [Tags.Conjuration, Tags.Arcane]
		self.level = 1 # self.level = 3
		self.required_charge = 5 # this is how many turns the spell must charge for

		self.minion_health = 50
		self.minion_damage = 15

		self.charging_effect_color = Tags.Arcane.color
		

	def on_cast(self, x, y):
		eldrichThing = Unit()
		eldrichThing.max_hp = self.get_stat('minion_health')
		eldrichThing.team = self.caster.team
		eldrichThing.asset_name = os.path.join("..","..","mods","BasicChargedSpells","eldrich_thing")

		eldrichThing.name = "Eldrich Thing"
		eldrichThing.sprite.color = Color(200, 50, 200)
		eldrichThing.flying = False
		eldrichThing.description = "A basic eldrich horror"
		eldrichThing.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))
		eldrichThing.tags = [Tags.Arcane]
		eldrichThing.resists[Tags.Arcane] = 100

		self.summon(eldrichThing, Point(x, y))
		yield

	def get_description(self):
		try:
			return ("Summon an eldrich thing after {required_charge} turns spent charging (channel the spell to charge it).\n"
					"The thing has [{minion_health}_HP:minion_health].\n"
					"Eldrich things have a melee attack which deals [{minion_damage}_physical:physical] damage.").format(**self.fmt_dict())
		except:
			return 'error'


Spells.all_player_spell_constructors.append(SummonEldrichIncantation)


class PowerupFireball(API_ChargedSpells.PowerupSpell):
	def on_init(self):
		super(PowerupFireball, self).on_init()
		self.name = "Inferno Fireball"

		self.upgrades['set_bound_on_interrupted'] = (1, 1, "Bound Fireball", "The fireball spell becomes bound when charging completes or is interrupted.")
		self.upgrades['damage_boost_on_charge'] = (1, 1, "Charge Damage", "The fireball spell deals 3 extra damage per turn charged.")

		self.damage = 10
		self.can_target_self = False
		self.level = 1 # self.level = 2
		self.tags = [Tags.Fire, Tags.Sorcery]
		self.range = 15
		self.radius = 3
		self.max_charges = 10
		self.max_charge = 4 # this is how many turns the spell can charge for


	def on_cast(self, x, y, turns_charged):
		target = Point(x, y)

		for stage in Burst(self.caster.level, target, self.get_stat('radius') + turns_charged):
			for point in stage:
				damage = self.get_stat('damage') + 3*turns_charged
				
				self.caster.level.deal_damage(point.x, point.y, damage, Tags.Fire, self)
			yield

	def get_description(self):
		try:
			return ("Charge up and cast a fireball.\n"
					"Each turn spent charging increases the radius by 1.\n"
					"The fireball deals [{damage}_fire:fire] damage and has a base radius of {radius}.\n"
					"The fireball can be charged for up to {max_charge} turns.\n"
					"Channel the spell to charge it, and recast it before the charge limit is reached to cast the fireball.").format(**self.fmt_dict())
		except:
				return 'error'

Spells.all_player_spell_constructors.append(PowerupFireball)

# credit to Anti-Tank Guided Missile#0888 for this idea
class ThunderingHail(API_ChargedSpells.DualEffectSpell):
	def on_init(self):
		super(ThunderingHail, self).on_init()
		self.name = "Thundering Hail"

		self.can_target_self = False
		self.level = 1 # self.level = 3
		self.tags = [Tags.Lightning, Tags.Ice, Tags.Sorcery]
		self.range = 15
		
		self.radius = 4
		self.effect_1_radius_increase_per_turn = 1
		self.effect_1_base_damage = 2
		self.effect_1_damage_increase_per_turn = 1

		self.effect_2_base_radius = 4
		self.effect_2_radius_increase_per_turn = 1
		self.effect_2_base_damage = 11
		self.effect_2_damage_increase_per_turn = 1

		self.max_charges = 4
		self.max_charge = 3 # this is how many turns the spell can charge for


	def get_impacted_tiles(self, x, y):
		radius = self.get_stat('radius')
		return [p for stage in Burst(self.caster.level, Point(x, y), radius) for p in stage]


	def on_cast1(self, x, y, turns_charged, turns_remaining):
		target = Point(x, y)

		for stage in Burst(self.caster.level, target, self.get_stat('radius') + self.get_stat('effect_1_radius_increase_per_turn')*turns_charged):
			for point in stage:
				damage = self.get_stat('effect_1_base_damage') + self.get_stat('effect_1_damage_increase_per_turn')*turns_charged
				
				self.caster.level.deal_damage(point.x, point.y, damage, Tags.Ice, self)
				self.caster.level.deal_damage(point.x, point.y, damage, Tags.Physical, self)
				
			yield 
            
		return

	
	def on_cast2(self, x, y, turns_charged):
		target = Point(x, y)
		
		for stage in Burst(self.caster.level, target, self.get_stat('effect_2_base_radius') + self.get_stat('effect_2_radius_increase_per_turn')*turns_charged):
			for point in stage:
				damage = self.get_stat('effect_2_base_damage') + self.get_stat('effect_2_damage_increase_per_turn')*turns_charged
				
				self.caster.level.deal_damage(point.x, point.y, damage, Tags.Lightning, self)
				
			yield 
            
		return

	def get_description(self):
		try:
			return ("Cast a chargeable gravity well that reverses direction at the end of charging.\n"
					"Each turn spent charging increases the radius and damage of the final effect by 1.\n"
					"The final effect deals 11 Arcane and 11 Physical damage.\n"
					"Each turn spent charging, units are pulled towards the center.\n"
					"Channel the spell to charge it, and recast it before the charge limit is reached to cast the final effect.").format(**self.fmt_dict())
		except:
			return 'error'


Spells.all_player_spell_constructors.append(ThunderingHail)

