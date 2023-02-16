from Level import *
import math

import Spells
print("Ritual Spells API loaded")

# # 
# # to see properties your RitualSpell can set, please scroll down to RitualSpell.on_init
# #
# 
# #
# # if you want another spell to have a different effect if cast within a ritual's aoe, look at this example:
# # The user sets up all the required pillars for MyRitual, and stands within their aoe. When they cast MySpell, its damage increases by 10.
# #
# 
# class MySpell(Spell):
# 	def cast(self, x, y):
# 		damage = self.damage
# 		if MyRitual.in_any_aoe(self.caster.x, self.caster.y):
# 			damage += 10
# 
# 		self.caster.level.deal_damage(x, y, damage, Tags.Fire, self)


class PillarHelperSpell(Spell):
	def __init__(self, spell_summoned_by):
		Spell.__init__(self)
		self.spell_summoned_by = spell_summoned_by

	def on_init(self):
		self.range = 0 
		self.pillar_spell = None
		self.disabled = False
		self.can_target_self = True
		self.name = 'Ritual'
		self.cool_down = 0 # self.spell_summoned_by.get_stat('ritual_activation_cooldown')

	def can_cast(self, x, y):
		# We don't check self.disabled on the can_cast because we want all pillars to display their attack animation at the same time
		
		if self.spell_summoned_by.get_stat('pillars_always_active'):
			return True

		# make sure the spell can be cast (the pillars are active)
		if (len(self.spell_summoned_by.pillars) < self.spell_summoned_by.get_stat('required_pillar_count')):
			return False

		return True

	def cast(self, x, y):
		if (self.disabled):
			self.disabled = False
			yield
			return

		# disable other pillars from casting the spell (so we only get one cast per turn)
		for pillar in self.spell_summoned_by.pillars:
			pillar.spells[0].diabled = True

		# remove any dead pillars
		self.spell_summoned_by.pillars = [pillar for pillar in self.spell_summoned_by.pillars if pillar.cur_hp > 0]
		
		# check to see if we have the required number of pillars
		if (not self.spell_summoned_by.get_stat('pillars_always_active') and len(self.spell_summoned_by.pillars) < self.spell_summoned_by.get_stat('required_pillar_count')):
			yield
			return

		self.spell_summoned_by.prepare_for_cast()
		for (x1, y1) in self.spell_summoned_by.get_aoe():
			self.spell_summoned_by.on_cast_tile(x1, y1)

		yield
		return

	def get_ai_target(self):
		failed_to_target = False
		if self.spell_summoned_by.get_stat('cast_only_when_enemy_in_aoe'):
			for point in self.spell_summoned_by.get_aoe():  
				unit = self.spell_summoned_by.caster.level.get_unit_at(point.x, point.y)
				if not unit is None and are_hostile(unit, self.spell_summoned_by.caster):
					return point
			failed_to_target = True
		if self.spell_summoned_by.get_stat('cast_only_when_ally_in_aoe'):
			for point in self.spell_summoned_by.get_aoe(): 
				unit = self.spell_summoned_by.caster.level.get_unit_at(point.x, point.y)
				if not unit is None and not are_hostile(unit, self.spell_summoned_by.caster):
					return point
			failed_to_target = True
		
		if failed_to_target: 
			return None
		
		else: 
			pillar = self.caster
			return Point(pillar.x, pillar.y)

def are_hostile_and_not_none(unit1, unit2):
	return not unit1 == None and not unit2 == None and are_hostile(unit1, unit2)
	
def are_not_hostile_and_not_none(unit1, unit2):
	return not unit1 == None and not unit2 == None and not are_hostile(unit1, unit2)
	

class Pillar(Unit):
	def __init__(self, spell_summoned_by):
		Unit.__init__(self)
		self.spell_summoned_by = spell_summoned_by
		self.max_hp = spell_summoned_by.get_stat('pillar_health')
		self.team = spell_summoned_by.caster.team
		self.asset_name = spell_summoned_by.pillar_sprite_path

		self.name = spell_summoned_by.pillar_name
		self.sprite.color = Color(200, 200, 200)
		self.flying = spell_summoned_by.pillars_fly
		self.stationary = True
		self.description = spell_summoned_by.pillar_description
		self.spells.append(PillarHelperSpell(spell_summoned_by))
		self.tags = [Tags.Construct]

class RitualSpell(Spell):
	def on_init(self):
		# RitualSpell.static__all_instances.append(self)

		if not hasattr(type(self), '__static__all_instances'):
			type(self).__static__all_instances = []
		type(self).__static__all_instances.append(self)

		# stats
		self.stats.append('pillar_health')
		self.stats.append('required_pillar_count')
		self.stats.append('max_pillar_count')
		self.stats.append('pillar_burst_radius')
		self.stats.append('include_edges')
		self.stats.append('include_inner_area')
		self.stats.append('exclude_pillars_from_area')
		self.stats.append('area_is_simple_polygon')
		self.stats.append('pillars_always_active')
		self.stats.append('exclude_allies_from_aoe')
		self.stats.append('exclude_enemies_from_aoe')
		self.stats.append('cast_only_when_ally_in_aoe')
		self.stats.append('cast_only_when_enemy_in_aoe')
		self.stats.append('pillars_fly')

		# parameters set by child class
		self.pillar_name = "Generic Pillar"
		self.pillar_sprite_path = os.path.join("..","..","mods","API_RitualSpells","basic_pillar")
		self.pillar_description = "A ritual spell pillar."

		# stats set in child class' on_init
		self.pillar_health = 10
		self.required_pillar_count = 3 # how many pillars are required for the include_edges and/or include_inner_area aoe to take effect?
		self.max_pillar_count = 5 # total num pillars allowed to exist at once
		self.pillar_burst_radius = 0 # should the pillars include a burst around themselves in their aoe? if no, make this 0. if yes, set this to some value greater than 0

		self.include_edges = True # include the tiles covered by Bolt(pillar1, pillar2)
		self.include_inner_area = True # pretend that the pillars mark the vertices of a polygon. the inner area is the inside of this polygon
		self.exclude_pillars_from_area = True # should the pillars target themselves?
		self.area_is_simple_polygon = True # should the polygon be allowed to be "tangled"? if true, 4 pillars may form either an hourglass or a rectangle, depending on what order they were placed in. if false, it's always a rectangle
		self.pillars_always_active = False # if this is true, the pillars will always cast on their burst area, even when there aren't enough pillars (given by required_pillar_count) to cast on the inner area
		self.pillars_fly = False

		self.exclude_allies_from_aoe = False
		self.exclude_enemies_from_aoe = False

		self.cast_only_when_ally_in_aoe = False
		self.cast_only_when_enemy_in_aoe = False

		# properties used by internal tracking
		self.pillars = []
		self.prev_pillar_points = []
		self.aoe = set()


	# ########################################
	#
	#  Methods that must be overriden
	#
	# ########################################

	def on_cast_tile(self, x, y):
		assert(False)
	

	# ########################################
	#
	#  methods that you may want to override
	#
	# ########################################

	def sort_pillars(self):
		if self.get_stat('area_is_simple_polygon'):
			# sort pillars according to their "clock" position relative to the center
			center = Point(sum(pillar.x for pillar in self.pillars)/len(self.pillars), sum(pillar.y for pillar in self.pillars)/len(self.pillars))
			pillarsWithTheta = [(pillar, math.atan2(pillar.y-center.y, pillar.x-center.x)) for pillar in self.pillars]
			pillarsWithTheta = sorted(pillarsWithTheta, key=lambda t: t[1])
			self.pillars = [pillar for (pillar, theta) in pillarsWithTheta]
		else:
			pass

	# called just before the pillars start calling on_cast_tile each turn
	def prepare_for_cast(self):
		pass

	# ########################################
	#
	#  Base spell methods
	#
	# ########################################

	def cast(self, x, y, channel_cast=False):
		if (len(self.pillars) >= self.get_stat('max_pillar_count')):
			yield
			return
		
		pillar = Pillar(self)

		self.pillars.append(pillar)
		self.summon(pillar, Point(x, y))

		yield

	def can_cast(self, x, y):
		return len(self.pillars) < self.get_stat('max_pillar_count') and Spell.can_cast(self, x, y)

		
	def get_impacted_tiles(self, x, y):
		return list(self.calc_potential_aoe(Point(x, y)))

	
	# ########################################
	#
	#  aoe related methods
	#
	# ########################################

	def in_aoe(self, x, y):
		return Point(x, y) in self.get_aoe()

	def get_aoe(self):
		# I decided not to do this caching because it was too difficult to get it to work with exclude_allies_from_aoe and exclude_enemies_from_aoe
		# self.pillars = [pillar for pillar in self.pillars if pillar.cur_hp > 0]
		# pillar_points = [Point(pillar.x, pillar.y) for pillar in self.pillars]

		# if len(pillar_points) != len(self.prev_pillar_points) or not all([a == b for (a, b) in zip(pillar_points, self.prev_pillar_points)]):
			# self.aoe = self.calc_aoe()
			# self.prev_pillar_points = pillar_points
		
		self.aoe = self.calc_aoe()
		return self.aoe

	
	def calc_potential_aoe(self, potential_new_pillar_location):
		self.pillars.append(potential_new_pillar_location)
		retval = self.calc_aoe()
		self.pillars.remove(potential_new_pillar_location)
		return retval

	# ########################################
	#
	#  Calculate aoe
	#
	# ########################################

	def get_inner_area_aoe(self):
		aoe = set()

		minx =  999
		miny =  999
		maxx = -999
		maxy = -999
		for pillar in self.pillars:
			if (pillar.x < minx):
				minx = pillar.x
			if (pillar.x > maxx):
				maxx = pillar.x
			if (pillar.y < miny):
				miny = pillar.y
			if (pillar.y > maxy):
				maxy = pillar.y

		# apply spell to each effected tile
		for x1 in range(minx, maxx+1):
			for y1 in range(miny, maxy+1):
				if self.in_inner_area(x1, y1):
					aoe.add(Point(x1, y1))
		
		return aoe

	def get_edges_aoe(self):
		aoe = set()
		pillars_array_offset_by_1 = [self.pillars[-1], *self.pillars[0:-1]]
		for (pillar1, pillar2) in zip(self.pillars, pillars_array_offset_by_1):
			# matches pillar 0 with pillar 1, pillar 1 with pillar 2, ... the last pillar with pillar 0
			for point in Bolt(self.caster.level, pillar1, pillar2):
				aoe.add(point)

		return aoe

	def get_pillar_bursts_aoe(self):
		aoe = set()
		for pillar in self.pillars:
			for stage in Burst(self.caster.level, Point(pillar.x, pillar.y), self.get_stat('pillar_burst_radius')):
				for point in stage:
					aoe.add(point)
		return aoe
	

	def calc_aoe(self):
		aoe = set()

		if len(self.pillars) <= 0:
			return aoe

		self.sort_pillars()

		pillars_active = self.get_stat('pillars_always_active') or len(self.pillars) >= self.get_stat('required_pillar_count')
		pillars_fully_active = self.get_stat('pillars_always_active') and len(self.pillars) >= self.get_stat('required_pillar_count')

		if self.get_stat('include_inner_area') and pillars_fully_active:
			aoe = set.union(aoe, self.get_inner_area_aoe())

		if self.get_stat('include_edges') and pillars_fully_active:
			aoe = set.union(aoe, self.get_edges_aoe())

		if self.get_stat('pillar_burst_radius') > 0 and pillars_active:
			aoe = set.union(aoe, self.get_pillar_bursts_aoe())
		
		if self.get_stat('exclude_pillars_from_area'):
			for pillar in self.pillars:
				if Point(pillar.x, pillar.y) in aoe:
					aoe.remove(Point(pillar.x, pillar.y))

		if self.get_stat('exclude_allies_from_aoe'):
			allies_in_aoe = set(p for p in aoe if are_not_hostile_and_not_none(self.caster, self.caster.level.get_unit_at(p.x, p.y)))
			aoe = set(p for p in aoe if p not in allies_in_aoe)
		
		if self.get_stat('exclude_enemies_from_aoe'):
			enemies_in_aoe = set(p for p in aoe if are_hostile_and_not_none(self.caster, self.caster.level.get_unit_at(p.x, p.y)))
			aoe = set(p for p in aoe if p not in enemies_in_aoe)
		
		return aoe


	# code modified from https://stackoverflow.com/a/2922778/9643841
	def in_inner_area(self, x, y):
		i = 0
		j = len(self.pillars)-1
		c = False
		while i < len(self.pillars):
			# handle horizontal edges
			if self.pillars[j].y == self.pillars[i].y:
				pass
			else:
				if ( ((self.pillars[i].y>y) != (self.pillars[j].y>y)) and \
					(x < (self.pillars[j].x-self.pillars[i].x) * (y-self.pillars[i].y) / (self.pillars[j].y-self.pillars[i].y) + self.pillars[i].x) ):
					c = not c

			j = i
			i += 1

		return c


	@classmethod
	def in_any_aoe(cls, x, y):
		# return any((type(spell) is cls and spell.in_aoe(x, y) for spell in RitualSpell.static__all_instances))
		return any((spell.in_aoe(x, y) for spell in cls.__static__all_instances))
		

class PentagramRitual(RitualSpell):
	def on_init(self):
		RitualSpell.on_init(self)

		self.required_pillar_count = 5
		self.max_pillar_count = 5


	def prepare_for_cast(self):
		# self.edge_aoe = self.get_edges_aoe()
		for (x, y) in self.get_edges_aoe():
			effect = Effect(x, y, Tags.Dark.color, Color(0, 0, 0), 12)
			effect.minor = False
			self.caster.level.effects.append(effect)

		for (x, y) in self.get_inner_area_aoe():
			effect = Effect(x, y, Tags.Arcane.color, Color(0, 0, 0), 12)
			effect.minor = False
			self.caster.level.effects.append(effect)


	def sort_pillars(self):
		if len(self.pillars) < 5:
			return

		RitualSpell.sort_pillars(self)
		self.pillars = [self.pillars[0], self.pillars[2], self.pillars[4], self.pillars[1], self.pillars[3]]
