
import random
import math
import tcod as libtcod

import LevelGen 
import Level
from Mutators import Mutator, Trial, all_trials, NumPortals
import Monsters
import CommonContent
import Consumables
import Shrines

import mods.API_TileHazards.API_TileHazards as THAPI
import mods.API_Universal.Modred as Modred

import mods.API_BossBar.API_BossBar as BossBar

LOOT_DROP_CHANCE = 0.8
LOOT_CHANCE_ITEM = 0.3
LOOT_CHANCE_RUBY_HEART = 0.3
LOOT_CHANCE_SP = 0.3
LOOT_CHANCE_SHRINE = 0.1

STARTING_SP = 12

# enemy wave spawning values
num_groups_range = (5, 6) # how many groups of enemies there could be in a given wave
group_point_range = (3, 5) # how many 'points' a group gets to 'buy' enemies (check spawn_options in Monsters.py for a list of enemies' point costs) 
group_size_range = (10, 20) # how many enemies could spawn in a given group
group_spawn_theta_range = (-90, 90) # -90, 90 means groups could spawn anywhere on the right side of the map (-90 is pointing towards the top, 90 towards the bottom, 0 towards the right)
group_spawn_r_range = (20, 60) # how far away groups spawn


# w = wall
# c = castle floor
# m = mountain
# t = tree
# o = water
# H = chasam
castle_level = """
                   mm m    #
                  m mm     #
w  ww             mm       #
ccccw  www       mm        #
ccccwwwcccw     m          #
ccccccccccw     m          #
ccccwwwcccw                #
ccccw  www                 #
ccccw                t     #
ccccw               tmt    #
ccccwwww             tmt   #
cccccccw t t t t      m    #
ccccccc                    #
ccccccc                    #
cccccccw                   #
ccccccc                    #
ccccccc                    #
cccccccw t t t t           #
ccccwwww            tt     #
ccccw           oo   t     #
ccccw          ooooo       #
ccccw  www     ooooooo     #
ccccwwwcccw     ooooo      #
ccccccccccw   t   ooo      #
ccccwwwcccw     oooo       #
ccccw  www     oooo   t    #
w  ww           oo         #
                           #
                           #
"""
# 28w  28h

castle_level_2 = """
                  m mm     #
                  mm       #
                 mm        #
       www       m         #
ww   wwcccw     m          #
cccccccccc                 #
ww   wwcccw                #
       www                 #
  ww      wwwwwwww   t     #
                    tmt    #
ww  wwww             tmt   #
cccccccw t t t t      m    #
ccccccc                    #
ccccccc                    #
ccccccc                    #
ccccccc                    #
cccccccw t t t t           #
ww  wwww            tt     #
            HHHHH    t     #
 HHHHHHH  HHHHH  ooo       #
HHHHH  www     ooooooo     #
ww   wwcccw     ooooo      #
cccccccccc    t  oooo      #
ww   wwcccw     oooo       #
       www     oooo   t    #
                oo         #
   HHHH                    #
     HHHH  HHH             #
"""



class ForestTile(THAPI.TileHazardSubscriptive):
	def __init__(self, name='Forest Tile', user=None, spell=None):
		super(ForestTile, self).__init__(name, user)
		self.asset = ['CastleDefenseMode', 'forest']
		self.spell = spell
		self.storedspelllv = 0
		self.acceptable_tags = [Level.Tags.Nature]
		self.global_triggers[Level.EventOnSpellCast] = self.on_spell_cast
		self.subscribe()
		self.stat_defaults = {
			"reusable": True
		}

	def get_stat(self, stat):
		if self.spell:
			return spell.get_stat(stat)
		else:
			return self.stat_defaults[stat]
	
	
	def on_spell_cast(self, evt):
		condition = True                                               \
			and any(t in self.acceptable_tags for t in evt.spell.tags) \
			and (not self.user or evt.spell.caster == self.user)       \
			and Level.Tags.Sorcery in evt.spell.tags                   \
			and Level.Point(self.x, self.y) in evt.spell.get_impacted_tiles(evt.x, evt.y) \
		
		if not condition:
			return

		self.storedspelllv += evt.spell.level
		# if evt.x == self.x and evt.y == self.y and any(t in self.acceptable_tags for t in evt.spell.tags) and (not user or evt.spell.caster == self.user) and Level.Tags.Sorcery in evt.spell.tags:
		# 	self.storedspelllv = evt.spell.level
	
	def on_unit_enter(self, unit):
		unit.apply_buff(Level.Stun(), 2)

		if self.storedspelllv:
			for i in range(self.storedspelllv):
				self.user.level.summon(self.user.level.player_unit, Monsters.GiantSpider(), target=self)
				pass
			
			self.storedspelllv = 0

		if not self.get_stat('reusable'):
			self.level.remove_prop(self)

	def get_description(self):
		return (
			"Stores [nature] [sorceries:sorcery] cast on it, directly or indirectly.\n"
			"Will cause [stun] and spawn a number of [spiders:spider] equal to the stored spell's level when stepped on.\n"
			"Currently stored spell level: %d"
		) % (self.storedspelllv)



# Modified from AntiTankGuidedMissile's LightningField hazard
class WaterTile(THAPI.TileHazardSubscriptive):
	def __init__(self, name='Water Tile', user=None, spell=None):
		super(WaterTile, self).__init__(name, user)
		self.asset = ['CastleDefenseMode', 'water']
		self.spell = spell
		self.storedspelllv = 0
		self.acceptable_tags = [Level.Tags.Lightning]
		self.global_triggers[Level.EventOnSpellCast] = self.on_spell_cast
		self.subscribe()
		self.stat_defaults = {
			"radius": 3,
			"damage_multiplier": 1
		}

	def get_stat(self, stat):
		if self.spell:
			return spell.get_stat(stat)
		else:
			return self.stat_defaults[stat]
	
	def on_spell_cast(self, evt):
		condition = True                                               \
			and any(t in self.acceptable_tags for t in evt.spell.tags) \
			and (not self.user or evt.spell.caster == self.user)       \
			and Level.Tags.Sorcery in evt.spell.tags                   \
			and Level.Point(self.x, self.y) in evt.spell.get_impacted_tiles(evt.x, evt.y) \
				
		if not condition:
			return

		self.storedspelllv += evt.spell.level
		# if evt.x == self.x and evt.y == self.y and any(t in self.acceptable_tags for t in evt.spell.tags):
		# 	self.storedspelllv = evt.spell.level
	
	def on_unit_enter(self, unit):
		self.deny_cooldowns(unit)

		numarcs = 0
		if self.storedspelllv:
			for point in self.user.level.get_points_in_ball(self.x, self.y, self.get_stat('radius')):
				u = self.user.level.get_unit_at(point.x, point.y)
				if u and self.user.level.are_hostile(self.user, u) and self.user.level.can_see(self.x, self.y, point.x, point.y):
					self.arc(u.x, u.y)
					numarcs += 1
					if numarcs >= self.storedspelllv:
						break
			
			self.storedspelllv = 0

	def deny_cooldowns(self, unit):
		for spell in unit.spells:
			current_cooldown = unit.cool_downs.get(spell, 0)
			unit.cool_downs[spell] = max(2, current_cooldown)


	def arc(self, x, y):
		target = Level.Point(x, y)
		for point in CommonContent.Bolt(self.user.level, Level.Point(self.x, self.y), target):
			self.user.level.deal_damage(point.x, point.y, self.get_stat('damage_multiplier')*self.storedspelllv, Level.Tags.Lightning, self.spell)

	def get_description(self):
		return (
			"While [swimming:shield] in water, units are unable to cast spells.\n"
			"Stores [lightning] [sorceries:sorcery] cast on it, directly or indirectly.\n"
			"Will emit a number of flashes equal to the total stored spell level when stepped on, dealing %d times the spell's level in [lightning] damage in a beam.\n"
			"Currently stored spell level: %d"
		) % (self.get_stat('damage_multiplier'), self.storedspelllv)


		
class CastleFloor(THAPI.TileHazardSubscriptive):
	def __init__(self, name='Castle Floor', user=None, spell=None):
		super(CastleFloor, self).__init__(name, user)
		self.asset = ['CastleDefenseMode', 'castle_floor_darker']
		self.spell = spell
		self.subscribe()

	def on_unit_enter(self, unit):
		if unit.team != self.level.player_unit.team:
			self.level.player_unit.cur_hp = 0
		elif unit.is_player_controlled:
			# add one to all spell cur charges and heal for 10 hp
			unit.cur_hp = min(unit.max_hp, unit.cur_hp + 10)
			
			for spell in unit.spells:
				spell.cur_charges = min(spell.cur_charges+1, spell.get_stat('max_charges'))
			
	
	def get_description(self):
		return (
			"Castle floor. [Prevent:damage] [enemy:damage] [units:damage] [from:damage] [reaching:damage] [this:damage] [tile:damage].\n"
			"Stepping on this tile restores your [mana:shield] and [heals:heal] you."
		)




		
class MountainTile(THAPI.TileHazardSubscriptive):
	def __init__(self, name='Mountain Tile', user=None, spell=None, ):
		super(MountainTile, self).__init__(name, user)
		self.asset = ['CastleDefenseMode', 'mountain']
		self.spell = spell
		self.subscribe()
		self.cur_hp = spell.get_stat('mountian_hp') if spell else 10
		self.stat_defaults = {
			"damage": 10
		}

	def get_stat(self, stat):
		if self.spell:
			return spell.get_stat(stat)
		else:
			return self.stat_defaults[stat]

	def on_unit_enter(self, unit):
		self.cur_hp -= 1
		unit.cur_hp -= self.get_stat('damage')

		if self.cur_hp <= 0:
			self.level.remove_prop(self)
	
	def get_description(self):
		return (
			"This mountain deals %d [damage] to any units who step on it.\n"
			"When stepped on, this mountain loses 1 hp.\n"
			"Current hp: %d"
		) % (self.get_stat('damage'), self.cur_hp)



def bfs_first_not_in_set(invalid_set, start):
	delta = [(1, 0), (0, -1), (0, 1), (-1, 0)]
	frontier = [start]
	visited = set()
	point = frontier.pop(0)

	while point in invalid_set:
		visited.add(point)
		potential_frontier = [(point[0]+dx, point[1]+dy) for (dx, dy) in delta]
		frontier += [p for p in potential_frontier if p not in visited]
		point = frontier.pop(0)

	return point


def add_unit_special(self, obj, x, y):
	obj.x = x
	obj.y = y
	obj.level = self

	if not hasattr(obj, 'level_id'):
		obj.level_id = self.level_id

	assert(isinstance(obj, Level.Unit))

	self.event_manager.raise_event(Level.EventOnUnitPreAdded(obj), obj)

	if not obj.cur_hp:
		obj.cur_hp = obj.max_hp
		assert(obj.cur_hp > 0)
		
	if x >= 0 and y >= 0 and x < len(self.tiles) and y < len(self.tiles[0]):
		assert(self.tiles[x][y].unit is None)
		self.tiles[x][y].unit = obj

	# Hack- allow improper adding in monsters.py
	for spell in obj.spells:
		spell.caster = obj
		spell.owner = obj

	self.set_default_resitances(obj)

	for buff in list(obj.buffs):
		# Apply unapplied buffs- these can come from Content on new units
		could_apply = buff.apply(obj) != Level.ABORT_BUFF_APPLY

		# Remove buffs which cannot be applied (happens with stun + clarity potentially)
		if not could_apply:
			obj.buffs.remove(obj)

		# Monster buffs are all passives
		if not obj.is_player_controlled:
			buff.buff_type = Level.BUFF_TYPE_PASSIVE

	self.units.append(obj)
	self.event_manager.raise_event(Level.EventOnUnitAdded(obj), obj)

	obj.ever_spawned = True


min_unit_x = 0
min_unit_y = 0
max_unit_x = 0
max_unit_y = 0

# to allow for units outside th ebounds
def new_find_path(self, start, target, pather, pythonize=False):
	start = Level.Point(start.x-min_unit_x, start.y-min_unit_y)
	target = Level.Point(target.x-min_unit_x, target.y-min_unit_y)

	def path_func(xFrom, yFrom, xTo, yTo, userData):
		def in_bounds(x, y):
			x += min_unit_x
			y += min_unit_y
			return x >= 0 and y >= 0 and x < len(self.tiles) and y < len(self.tiles[0])

		if not in_bounds(xTo, yTo):
			if not in_bounds(xFrom, yFrom):
				return 1.0
			else:
				return 0.0 # units cannot leave the bounds of the level

		# original find_path

		tile = self.tiles[xTo][yTo]
		
		if pather.flying:
			if not tile.can_fly:
				return 0.0
		else:
			if not tile.can_walk:
				return 0.0
			
		blocker_unit = tile.unit

		if not blocker_unit:
			if tile.prop:
				# player pathing avoids props unless prop is the target
				if (isinstance(tile.prop, Level.Portal) or isinstance(tile.prop, Level.Shop)) and pythonize and not (xTo == target.x and yTo == target.y):
					return 0.0
				# creatuers slight preference to avoid props
				return 1.1
			else:
				return 1.0
		if blocker_unit.stationary:
			return 50.0
		else:
			return 5.0


	path = libtcod.path_new_using_function(max(max_unit_x-min_unit_x, self.width), max(max_unit_y-min_unit_y, self.height), path_func)
	libtcod.path_compute(path, start.x, start.y, target.x, target.y)
	if pythonize:
		ppath = []
		for i in range(libtcod.path_size(path)):
			x, y = libtcod.path_get(path, i)
			ppath.append(Point(x, y))
		libtcod.path_delete(path)
		return ppath
	return path


class OutOfBoundsBuff(Level.Buff):
	def __init__(self):
		super().__init__()
		self.owner_triggers[Level.EventOnDeath] = self.on_death
		self.buffs_on_hold = None

	def on_death(self, evt):
		BossBar.boss_bar_percent -= 1/self.owner.level.num_enemies_spawned
		self.owner.level.spawned_enemies_defeated += 1

	def on_pre_advance(self):
		if not self.in_bounds():
			self.deny_cooldowns(self.owner)
			self.owner.apply_buff(Level.Stun(), 1)
		
			# put all other buffs on hold
			if len(self.owner.buffs) > 2 or True:
				if self.buffs_on_hold == None:
					self.buffs_on_hold = [b for b in self.owner.buffs if not isinstance(b, OutOfBoundsBuff) and not isinstance(b, Level.Stun)]
				else:
					self.buffs_on_hold += [b for b in self.owner.buffs if not isinstance(b, OutOfBoundsBuff) and not isinstance(b, Level.Stun)]
				
				self.owner.buffs = [b for b in self.owner.buffs if isinstance(b, OutOfBoundsBuff) or isinstance(b, Level.Stun)]

	# move the unit closer to the map
	def on_advance(self):
		if not self.target or not self.owner.level.can_stand(self.target.x, self.target.y, self):
			# if I don't have a target or my target is occupied, find my new target
			best_target = Level.Point(
				min(max(0, self.owner.x), Modred.API_LevelGen_Constants.LEVEL_SIZE),
				min(max(0, self.owner.y), Modred.API_LevelGen_Constants.LEVEL_SIZE)
			)
			target_frontier = [best_target]
			visited = set()
			delta = [(1, 0), (0, -1), (0, 1), (-1, 0)]
			while True:
				self.target = target_frontier.pop(0)
				visited.add(self.target)
				target_frontier += [
					(self.target.x+dx, self.target.y+dy) 
					for (dx, dy) in delta 
					if 
						self.owner.level.can_stand(self.target.x+dx, self.target.y+dy, self) 
						and Level.Point(self.target.x+dx, self.target.y+dy) not in visited
				]

				if self.owner.level.can_stand(self.target.x, self.target.y, self):
					break
				if len(target_frontier) <= 0:
					self.target = None
					break

			if self.target != None:
				self.path = self.owner.level.get_points_in_line(self.owner, self.dest)[1:]
			else:
				self.path = None

		if not self.path or not len(self.path):
			return
		
		next_loc = self.path.pop(0)

		if self.in_bounds(next_loc.x, next_loc.y) and not self.owner.level.can_stand(next_loc.x, next_loc.y, self):
			return
		elif self.in_bounds(next_loc.x, next_loc.y):
			self.owner.level.tiles[x][y].unit = self
			
			prop = self.owner.level.tiles[next_loc.x][next_loc.y].prop
			if prop:
				prop.on_unit_enter(self)

			cloud = self.owner.level.tiles[next_loc.x][next_loc.y].cloud
			if cloud:
				cloud.on_unit_enter(self)
		
		if self.buffs_on_hold:
			self.owner.buffs += self.buffs_on_hold
			self.buffs_on_hold = None

		self.owner.x = next_loc.x
		self.owner.y = next_loc.y
			
	def in_bounds(self, x=None, y=None):
		x = self.owner.x if x == None else x
		y = self.owner.y if y == None else y
		return x >= 0 and y >= 0 and x < len(self.owner.level.tiles) and y < len(self.owner.level.tiles[0])

	def deny_cooldowns(self, unit):
		for spell in unit.spells:
			current_cooldown = unit.cool_downs.get(spell, 0)
			unit.cool_downs[spell] = max(2, current_cooldown)


# old_apply = Level.Buff.apply
# def apply(self, *args):
# 	print(self.name)
# 	return 
# Level.Buff.apply = apply


class BossBarTargetBuff(Level.Buff):
	def __init__(self):
		super().__init__()
		self.owner_triggers[Level.EventOnDeath] = self.on_death

	def on_death(self, evt):
		BossBar.boss_bar_percent -= 1/self.owner.level.num_enemies_spawned
		self.owner.level.spawned_enemies_defeated += 1

		if random.random() < LOOT_DROP_CHANCE:
			spawn_point = find_nearest_tile_with_no_prop(self.owner.level, self.owner.x, self.owner.y)
			if random.random() < LOOT_CHANCE_ITEM:
				item = Consumables.roll_consumable(prng=random.Random())
				prop = LevelGen.make_consumable_pickup(item)
				self.owner.level.add_obj(prop, *spawn_point)
			elif random.random() < LOOT_CHANCE_ITEM+LOOT_CHANCE_SP:
				self.owner.level.add_obj(Level.ManaDot(), *spawn_point)
			elif random.random() < LOOT_CHANCE_ITEM+LOOT_CHANCE_SP+LOOT_CHANCE_RUBY_HEART:
				self.owner.level.add_obj(Level.HeartDot(), *spawn_point)
			elif random.random() < LOOT_CHANCE_ITEM+LOOT_CHANCE_SP+LOOT_CHANCE_RUBY_HEART+LOOT_CHANCE_SHRINE:
				difficulty = 20
				shrine = Shrines.roll_shrine(difficulty, random.Random())(self.owner.level.player_unit)
				self.owner.level.add_obj(shrine, *spawn_point)
			else:
				self.owner.level.add_obj(Level.ManaDot(), *spawn_point)
			


		

class OOBUnitManager():
	def __init__(self):
		self.target = None
		self.path = None
		self.owner = None
		self.has_spawned = False
		self.example_unit = None
		self.x = None
		self.y = None
		self.unit_constructor = None

	# move the unit closer to the map
	def on_advance(self):
		if self.has_spawned:
			return

		if not self.example_unit:
			self.example_unit = self.unit_constructor()

		if self.in_bounds(self.x, self.y) and self.level.can_stand(self.x, self.y, self.example_unit):
			unit = self.unit_constructor()
			self.level.add_obj(unit, self.x, self.y)
			unit.apply_buff(BossBarTargetBuff())
			self.has_spawned = True
			return

		if not self.target or not self.level.can_stand(self.target[0], self.target[1], self.example_unit):
			# if I don't have a target or my target is occupied, find my new target
			best_target = Level.Point(
				min(max(0, self.x), Modred.API_LevelGen_Constants.LEVEL_SIZE),
				min(max(0, self.y), Modred.API_LevelGen_Constants.LEVEL_SIZE)
			)
			target_frontier = [best_target]
			visited = set()
			delta = [(1, 0), (0, -1), (0, 1), (-1, 0)]
			while True:
				self.target = target_frontier.pop(0)
				visited.add(self.target)
				target_frontier += [
					(self.target[0]+dx, self.target[1]+dy) 
					for (dx, dy) in delta 
					if 
						self.level.can_stand(self.target[0]+dx, self.target[1]+dy, self.example_unit) 
						and Level.Point(self.target[0]+dx, self.target[1]+dy) not in visited
				]

				if self.level.can_stand(self.target[0], self.target[1], self.example_unit):
					break
				if len(target_frontier) <= 0:
					self.target = None
					break

			if self.target != None:
				self.path = self.level.get_points_in_line(self, Level.Point(*self.target))[1:]
			else:
				self.path = None

		if not self.path or not len(self.path):
			return
		
		next_loc = self.path.pop(0)

		if self.in_bounds(next_loc.x, next_loc.y) and not self.level.can_stand(next_loc.x, next_loc.y, self.example_unit):
			return
		elif self.in_bounds(next_loc.x, next_loc.y):
			unit = self.unit_constructor()
			self.level.add_obj(unit, next_loc.x, next_loc.y)
			self.has_spawned = True
			unit.apply_buff(BossBarTargetBuff())
			
			# self.owner.level.tiles[x][y].unit = self
			
			# prop = self.owner.level.tiles[next_loc.x][next_loc.y].prop
			# if prop:
			# 	prop.on_unit_enter(self)

			# cloud = self.owner.level.tiles[next_loc.x][next_loc.y].cloud
			# if cloud:
			# 	cloud.on_unit_enter(self)
		
		# if self.buffs_on_hold:
		# 	self.owner.buffs += self.buffs_on_hold
		# 	self.buffs_on_hold = None

		self.x = next_loc.x
		self.y = next_loc.y
			
	def in_bounds(self, x=None, y=None):
		x = self.x if x == None else x
		y = self.y if y == None else y
		return x >= 0 and y >= 0 and x < len(self.level.tiles) and y < len(self.level.tiles[0])

oob_unit_managers = []


class OutOfBoundsManagementBuff(Level.Buff):
	def __init__(self):
		super().__init__()

	def on_pre_advance(self):
		for oob_unit_manager in oob_unit_managers:
			oob_unit_manager.on_advance()


# old_can_see = Level.Level.can_see
# def new_can_see(self, x1, y1, x2, y2, light_walls=False):
# 	def in_bounds(x, y):
# 		return x >= 0 and y >= 0 and x < len(self.tiles) and y < len(self.tiles[0])

# 	if in_bounds(x1, y1) and in_bounds(x2, y2):
# 		return old_can_see(self, x1, y1, x2, y2, light_walls)
# 	else:
# 		return False
	
# def new_get_units_in_ball(self, center, radius, diag=False):
# 	def in_bounds(x, y):
# 		return x >= 0 and y >= 0 and x < len(self.tiles) and y < len(self.tiles[0])
# 	return [u for u in self.units if in_bounds(u.x, u.y) and Level.distance(Level.Point(u.x, u.y), center, diag=diag) <= radius]


class DummyObject():
	pass

	
def find_nearest_tile_with_no_prop(level, x, y):
	def in_bounds(x, y):
		return x >= 0 and y >= 0 and x < len(level.tiles) and y < len(level.tiles[0])

	delta = [(1, 0), (0, -1), (0, 1), (-1, 0)]
	frontier = [(x, y)]
	visited = set()
	point = frontier.pop(0)

	while level.tiles[point[0]][point[1]].prop != None:
		visited.add(point)
		potential_frontier = [(point[0]+dx, point[1]+dy) for (dx, dy) in delta]
		frontier += [p for p in potential_frontier if p not in visited and in_bounds(*p)]
		point = frontier.pop(0)

	return point



# w = wall
# c = castle floor
# m = mountain
# t = tree
# o = water
# H = chasam
# # = enemy spawner
def castle_level_maker(level_generator):
	global min_unit_x
	global min_unit_y
	global max_unit_x
	global max_unit_y

	print('generating castle defense level')

	level_layout = castle_level_2
	level_generator.monster_gates_points = 15

	# level_logger.debug("\nGenerating castle defense level")
	# level_logger.debug("Level id: %d" % self.level_id)

	level = Level.Level(Modred.API_LevelGen_Constants.LEVEL_SIZE, Modred.API_LevelGen_Constants.LEVEL_SIZE)
	
	# overrides
	# level.find_path = type(Level.Level.find_path)(new_find_path, level, Level.Level)
	# level.act_move = type(Level.Level.act_move)(new_act_move, level, Level.Level)
	# quick_pach_function_on_instance(level, Level.Level, 'find_path', new_find_path)
	# level.find_path = lambda self, *args :  new_find_path(self, *args)

	# TODO: somehow I thought this would be easier than manually moving them. 
	# Level.Level.find_path = new_find_path
	# Level.Level.act_move = new_act_move
	# Level.Level.can_move = new_can_move
	# Level.Level.can_see = new_can_see

	# Level.Level.can_see = new_can_see
	# Level.Level.get_units_in_ball = new_get_units_in_ball

	max_unit_x = level.width
	max_unit_y = level.height

	level_generator.potential_gate_spawns = Monsters.spawn_options.copy()
	# random.shuffle(level_generator.potential_gate_spawns)
	print('num gate options ' + str(len(level_generator.potential_gate_spawns)))
	def choose_spawner():
		spawner_choice = (None, 999999999999999)
		while spawner_choice[1] > level_generator.monster_gates_points:
			spawner_choice = random.choice(level_generator.potential_gate_spawns)
		
		level_generator.monster_gates_points = max(1, level_generator.monster_gates_points-1)
		return spawner_choice[0]


	potential_spawn_points = set()
	gate_locations = []
	for (line, y) in zip(level_layout.split('\n')[1:], range(Modred.API_LevelGen_Constants.LEVEL_SIZE)):
		x = 0
		for (char, x) in zip(line, range(Modred.API_LevelGen_Constants.LEVEL_SIZE)):
			if char == 'w':
				level.make_wall(x, y)
			elif char == 'H':
				level.make_chasm(x, y)
			else:
				level.make_floor(x, y)

				user = DummyObject()
				user.level = level

				if char == 'c':
					level.add_obj(CastleFloor(user=user), x, y)
					potential_spawn_points.add(Level.Point(x, y))
				elif char == 'm':
					level.add_obj(MountainTile(user=user), x, y)
				elif char == 't':
					level.add_obj(ForestTile(user=user), x, y)
				elif char == 'o':
					level.add_obj(WaterTile(user=user), x, y)
				elif char == '#':
					gate_locations.append(Level.Point(x, y))
				# else:
				# 	potential_spawn_points.add(Level.Point(x, y))


	# random.shuffle(gate_locations)
	# for gate_location in gate_locations:
	# 	level.add_obj(CommonContent.MonsterSpawner(choose_spawner()), gate_location.x, gate_location.y)

	# level_generator.difficulty # TODO: do something with this
	num_enemies_spawned = 0
	total_num_points = 0

	taken_spots = set(potential_spawn_points)
	spawned_enemies_by_location = dict()
	num_groups = random.choice(range(*num_groups_range))
	for group in range(num_groups):
		group_size = random.choice(range(*group_size_range))
		group_points = random.choice(range(*group_point_range))
		group_spawn_theta = random.choice(range(*group_spawn_theta_range))
		group_spawn_r = random.choice(range(*group_spawn_r_range))

		group_spawn_x = int(group_spawn_r * math.cos(group_spawn_theta * math.pi / 180.0)) + Modred.API_LevelGen_Constants.LEVEL_SIZE//2
		group_spawn_y = int(group_spawn_r * math.sin(group_spawn_theta * math.pi / 180.0)) + Modred.API_LevelGen_Constants.LEVEL_SIZE//2
		
		group_spawn_frontier = [(group_spawn_x, group_spawn_y)]
		if (group_spawn_x, group_spawn_y) in taken_spots:
			group_spawn_frontier = [bfs_first_not_in_set(taken_spots, (group_spawn_x, group_spawn_y))]

		
		level_generator.monster_gates_points = group_points
		total_num_points += group_points

		for enemy_index in range(group_size):
			enemy_unit_constructor = choose_spawner()
			# enemy_unit = enemy_unit_constructor()

			# out_of_bounds_buff = OutOfBoundsBuff()
			# enemy_unit.apply_buff(out_of_bounds_buff)

			# get spawn point
			spawn_point = None
			delta = [(1, 0), (0, -1), (0, 1), (-1, 0)]
			while True: # a hacked together do-while loop
				spawn_point = group_spawn_frontier.pop(0)
				potential_frontier = [(spawn_point[0]+dx, spawn_point[1]+dy) for (dx, dy) in delta]
				group_spawn_frontier += [p for p in potential_frontier if p not in taken_spots]

				if spawn_point not in taken_spots:
					break


			min_unit_x = min(min_unit_x, spawn_point[0])
			min_unit_y = min(min_unit_y, spawn_point[1])
			max_unit_x = max(max_unit_x, spawn_point[0])
			max_unit_y = max(max_unit_y, spawn_point[1])
			taken_spots.add(spawn_point)
			# spawned_enemies_by_location[spawn_point] = enemy_unit

			# add_unit_special(level, enemy_unit, *spawn_point)
			oob_unit_manager = OOBUnitManager()
			# oob_unit_manager.owner = enemy_unit
			oob_unit_manager.unit_constructor = enemy_unit_constructor
			oob_unit_manager.x = spawn_point[0]
			oob_unit_manager.y = spawn_point[1]
			oob_unit_manager.level = level
			oob_unit_managers.append(oob_unit_manager)

			# enemy_unit.x = spawn_point[0]
			# enemy_unit.y = spawn_point[1]
			# enemy_unit.level = level
			# out_of_bounds_buff.owner = enemy_unit
			# out_of_bounds_buff.on_pre_advance()

			num_enemies_spawned += 1
		
	# level.out_of_bounds_occupied_spots = spawned_enemies_by_location
	level.num_enemies_spawned = num_enemies_spawned
	level.spawned_enemies_defeated = 0


	# random start point
	level.start_pos = random.choice(list(potential_spawn_points))


	level.gen_params = level_generator
	level.calc_glyphs()

	level.biome = LevelGen.Biome('dungeon')
	level.tileset = level.biome.tileset
	level.water = None

	# Record info per tile so that mordred corruption works
	for tile in level.iter_tiles():
		tile.tileset = level.tileset
		tile.water = level.water

	if level_generator.game:
		for m in level_generator.game.mutators:
			m.on_levelgen(level_generator)
			

	level_generator.level = level
	level_generator.log_level()
	return level


class CastleDefenseMode(Mutator):
	def __init__(self):
		Mutator.__init__(self)
		self.description = "Prevent all enemies from reaching the castle."
		
	def on_game_begin(self, game):
		self.game = game
		self.game.p1.xp = STARTING_SP
		self.game.p1.apply_buff(OutOfBoundsManagementBuff())

		BossBar.draw_boss_bar = True
		Modred.reset_win_conditions()
		Modred.add_win_condition(lambda game: game.cur_level.spawned_enemies_defeated == game.cur_level.num_enemies_spawned)
		
	def on_levelgen_pre(self, levelgen):
		Modred.set_level_maker(castle_level_maker)
		
	def on_levelgen(self, levelgen):
		# Modred.restore_level_maker()
		pass

	# TODO: note: this function isn't supported currently. need to write a Universal patch for this
	def on_game_end(self):
		Modred.restore_level_maker()
		BossBar.draw_boss_bar = False

		
all_trials.append(Trial("Castle Defense Mode", [CastleDefenseMode()]))


print("CastleDefenseMode loaded")

# def make_level(self):

# 	level_logger.debug("\nGenerating level for %d" % self.difficulty)
# 	level_logger.debug("Level id: %d" % self.level_id)
# 	level_logger.debug("num start points: %d" % self.num_start_points)
# 	level_logger.debug("reconnect chance: %.2f" % self.reconnect_chance)
# 	level_logger.debug("num open spaces: %d" % self.num_open_spaces)

# 	self.level = Level(LEVEL_SIZE, LEVEL_SIZE)
# 	self.make_terrain()
	
# 	self.populate_level()

# 	self.level.gen_params = self
# 	self.level.calc_glyphs()

# 	if self.difficulty == 1:
# 		self.level.biome = all_biomes[0]
# 	else:
# 		self.level.biome = self.random.choice([b for b in all_biomes if b.can_spawn(self)]) 

# 	self.level.tileset = self.level.biome.tileset
	
# 	self.level.water = self.random.choice(self.level.biome.waters + [None])
# 	# Always start with blue water so people understand what a chasm is
# 	if self.difficulty == 1:
# 		self.level.water = WATER_BLUE

# 	# Game looks better without water
# 	self.level.water = None

# 	# Record info per tile so that mordred corruption works
# 	for tile in self.level.iter_tiles():
# 		tile.tileset = self.level.tileset
# 		tile.water = self.level.water

# 	if self.game:
# 		for m in self.game.mutators:
# 			m.on_levelgen(self)
			
# 	self.log_level()

# 	return self.level

# in the trial init, Modred.set_level_maker(castle_level_maker)