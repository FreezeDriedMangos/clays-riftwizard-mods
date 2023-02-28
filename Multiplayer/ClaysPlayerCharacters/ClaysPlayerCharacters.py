import mods.API_Multiplayer.API_Multiplayer as API_Multiplayer
import Level as Level
import Spells as Spells
import Monsters as Monsters
import CommonContent as CommonContent
import Consumables as Consumables
import os
import random

# TODO: shark
# TODO: wizard and dog
# TODO: rename wizard to "The Wizard... Me..rl..n...?"
# TODO: thrumbo
# TODO: scarecrow


# code from https://www.w3resource.com/python-exercises/math/python-math-exercise-77.php
def rgb2hsv(rgb):
	r = rgb[0]
	g = rgb[1]
	b = rgb[2]
	
	# r, g, b = r/255.0, g/255.0, b/255.0
	mx = max(r, g, b)
	mn = min(r, g, b)
	df = mx-mn
	if mx == mn:
		h = 0
	elif mx == r:
		h = (60 * ((g-b)/df) + 360) % 360
	elif mx == g:
		h = (60 * ((b-r)/df) + 120) % 360
	elif mx == b:
		h = (60 * ((r-g)/df) + 240) % 360
	if mx == 0:
		s = 0
	else:
		s = (df/mx)*100
	v = mx*100
	return [h, s, v]

# code from https://stackoverflow.com/a/26856771/9643841
def hsv2rgb(hsv):
	h = hsv[0]
	s = hsv[1]
	v = hsv[2]
	
	if s == 0.0: return (v, v, v)
	i = int(h*6.) # XXX assume int() truncates!
	f = (h*6.)-i; p,q,t = v*(1.-s), v*(1.-s*f), v*(1.-s*(1.-f)); i%=6
	if i == 0: return (v, t, p)
	if i == 1: return (q, v, p)
	if i == 2: return (p, v, t)
	if i == 3: return (p, q, v)
	if i == 4: return (t, p, v)
	if i == 5: return (v, p, q)

#
# I'm defining colors like this because I'm lazy
#
main_target_hsv = [0, 1, 1]
curr_impacted_hsv = [0, 0.50, 0.78]
targetable_hsv = [0, 0.25, 0.6]
name_hsv = [0, 1, 1]

def color_scheme_from_hsv_color(hsv):
	new_main_target_hsv = main_target_hsv
	new_main_target_hsv[0] = hsv[0]
	new_main_target_hsv[1] *= hsv[1]
	new_main_target_hsv[2] *= hsv[2]
	new_main_target_rgb = [int(255*c) for c in hsv2rgb(new_main_target_hsv)]
	new_curr_impacted_hsv = curr_impacted_hsv
	new_curr_impacted_hsv[0] = hsv[0]
	new_curr_impacted_hsv[1] *= hsv[1]
	new_curr_impacted_hsv[2] *= hsv[2]
	new_curr_impacted_rgb = [int(255*c) for c in hsv2rgb(new_curr_impacted_hsv)]
	new_targetable_hsv = targetable_hsv
	new_targetable_hsv[0] = hsv[0]
	new_targetable_hsv[1] *= hsv[1] * min(1, 2*hsv[2]) # desaturate if value is low for given color
	new_targetable_hsv[2] *= hsv[2] * min(1, 2*hsv[1]) # darken if saturation is low for given color
	new_targetable_rgb = [int(255*c) for c in hsv2rgb(new_targetable_hsv)]
	new_name_hsv = name_hsv
	new_name_hsv[0] = hsv[0]
	new_name_hsv[1] *= hsv[1]
	new_name_hsv[2] *= hsv[2]
	new_name_rgb = [int(255*c) for c in hsv2rgb(hsv)]

	retval = {
		API_Multiplayer.COLOR_SCHEME_MAIN_TARGET: (new_main_target_rgb[0], new_main_target_rgb[1], new_main_target_rgb[2], 150),
		API_Multiplayer.COLOR_SCHEME_CURR_IMPACTED: (new_curr_impacted_rgb[0], new_curr_impacted_rgb[1], new_curr_impacted_rgb[2], 150),
		API_Multiplayer.COLOR_SCHEME_TARGETABLE: (new_targetable_rgb[0], new_targetable_rgb[1], new_targetable_rgb[2], 150),
		API_Multiplayer.COLOR_SCHEME_UNTARGETABLE_IN_RANGE: (255, 80, 80, 100),
		API_Multiplayer.COLOR_SCHEME_MAIN_TARGET_UNTARGETABLE: (100, 0, 0, 150),
		API_Multiplayer.COLOR_SCHEME_NAME: (new_name_rgb[0], new_name_rgb[1], new_name_rgb[2])
	}

	return retval


def baby_dragon_quirks(self):
	self.banned_spell_types = [Level.Tags.Translocation]
	self.flying = True
	self.tags = [Level.Tags.Living, Level.Tags.Dragon]
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","baby_dragon"], 'Baby Dragon', \
	color_scheme_from_hsv_color((45/360, 0.92, 1)), \
	'The smallest in his family.', baby_dragon_quirks, '- Can fly\n- Cannot learn [translocation] spells\n- Is a [living] [dragon]')


class LightningSpriteForm(Spells.LightningFormBuff):
	def __init__(self, phys_immune = False):
		Spells.LightningFormBuff.__init__(self)
		self.transform_asset_name = None
		self.name = "Natural Lightning Form"
	
	def on_applied(self, caster):
		Spells.LightningFormBuff.on_applied(self, caster)
		self.resists[Level.Tags.Lightning] = 0
		self.resists[Level.Tags.Physical] = 0

		self.owner_triggers[Level.EventOnSpellCast] = self.on_spell_cast
		self.owner_triggers[Level.EventOnPass] = self.on_pass
		self.color = Level.Color(122, 122, 200)
	
	def on_advance(self):
		pass


def lightning_sprite_quirks(self):
	lightning_form_buff = LightningSpriteForm()
	self.apply_buff(lightning_form_buff)

	self.resists[Level.Tags.Arcane] = -100
	self.resists[Level.Tags.Lightning] = 50

	self.tag_purchase_cost_bonus = {}
	self.tag_purchase_cost_bonus[Level.Tags.Lightning] = 1

	self.tags = [Level.Tags.Lightning]
	# self.tag_purchase_cost_multiplier[Level.Tags.Lightning] = 2 # make lightning spells and skills twice as expensive
	# self.banned_purchaces = [Spells.LightningFormSpell]

	# player.discount_tag = self.tag
	# player.scroll_discounts[self.spell.name] = 0


	# for spell in self.all_player_spells[0:26]:
	# 	self.add_spell(spell)

API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","thunder_sprite"], 'Lightning Sprite', \
	color_scheme_from_hsv_color((60/360, 1, 1)), \
	'', lightning_sprite_quirks, \
	'- -100 [arcane] resist\n'
	'- 50 [lightning] resist\n'
	'- Permanent lightning form buff\n'
	'- [Lightning] spells are 1 sp more expensive'
	'- Has the [lightning] tag'
)
	

class NothingSpell(Level.Spell):
	def cast(self, x, y):
		yield

class BookBuff(Level.Buff):
	def __init__(self):
		Level.Buff.__init__(self)
		self.name = "A Book's Nature"
		self.owner_triggers[Level.EventOnItemPickup] = self.on_pickup
		self.buff_type = Level.BUFF_TYPE_NONE
		self.description = "Books cannot drink potions. This book however regains spell charges while learning."

	def on_applied(self, owner):
		pass

	def on_advance(self):
		pass

	def on_pickup(self, evt):
		if isinstance(evt.item, Level.ManaDot):
			for spell in self.owner.spells:
				spell.cur_charges += 1
		if isinstance(evt.item, ItemPickup):
			if \
				evt.item.item.name == "Healing Potion" or \
				evt.item.item.name == "Mana Potion" \
			:
				evt.item.item.spell = NothingSpell()

# event_manager.register_global_trigger(event_type, trigger)
def book_quirks(self):
	self.tag_purchase_cost_multiplier = {}
	self.tag_purchase_cost_multiplier[Level.Tags.Word] = 0.5

	self.items = []

	self.resists[Level.Tags.Arcane] = 50
	self.resists[Level.Tags.Fire] = -100
	self.resists[Level.Tags.Physical] = -100

	self.tags = [Level.Tags.Arcane, Level.Tags.Construct]

	self.apply_buff(BookBuff())
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","book"], 'Magic Book', \
	color_scheme_from_hsv_color((284/360, 1, 1)), \
	'Knowledge is power.', book_quirks, \
	'- [Word] spells are half cost\n'
	'- 50 [arcane] resist\n' 
	'- -100 [Fire] resist\n' 
	'- -100 [Physical] resist\n' 
	'- Is an [arcane] [construct]\n'
	'- Cannot drink mana or health potions\n'
	'- Regains a spell charge on all spells after picking up a memory orb'
)


class SpawnVoidBomber(Level.Spell):
	def on_init(self):
		self.name = "... they died of natural causes"

		self.can_target_self = True
		self.range = 0
		self.tags = [Level.Tags.Arcane, Level.Tags.Conjuration]
		self.can_target_self = True
		self.element = Level.Tags.Arcane
		self.mele = True

		self.has_casted = False
	
	def get_description(self):
		return ("Summons a friendly void bomber.\n"
				"The Peace Loving Potato is totally not responsible for what happens next.").format(**self.fmt_dict())

	def cast(self, x, y):
		try:
			bomb = Monsters.VoidBomber()
			bomb.team = self.owner.team
			self.summon(bomb, Level.Point(x, y))

			self.has_casted = True
		except:
			pass
		yield

	def can_cast(self, x, y):
		if self.has_casted:
			return False

		return Level.Spell.can_cast(self, x, y)

def PeaceLoveAndPotato(summoner):
	unit = Level.Unit()
	unit.asset = ["ClaysPlayerCharacters","mumbotato"]
	unit.tags = [Level.Tags.Living, Level.Tags.Nature]

	unit.max_hp = 5
	unit.team = summoner.team

	unit.name = "Peace, Love, and Plants, Baby!"
	unit.sprite.color = Level.Color(200, 50, 200)
	unit.flying = False
	unit.description = "A peace-loving potato. Completely harmless."
	if random.random() < 0.1:
		unit.spells.append(SpawnVoidBomber())
	unit.spells.append(CommonContent.SimpleMeleeAttack(0))

	return unit
class TreesaBuff(Level.Buff):
	def __init__(self):
		Level.Buff.__init__(self)
		self.name = "Peace, Love, and Plants"
		self.buff_type = Level.BUFF_TYPE_NONE
		self.description = "Spawn peace loving potatoes while sitting still."

	def on_applied(self, caster):
		self.owner_triggers[Level.EventOnPass] = self.on_pass
		self.color = Level.Color(122, 122, 200)

	def on_pass(self, evt):
		if self.owner.has_buff(Level.ChannelBuff):
			return
		self.summon(PeaceLoveAndPotato(self.owner), Level.Point(self.owner.x, self.owner.y))
def treesa_quirks(self):
	self.tag_purchase_cost_bonus = {}
	self.tag_purchase_cost_bonus[Level.Tags.Nature] = -1

	self.resists[Level.Tags.Fire] = -100
	self.resists[Level.Tags.Poison] = -100

	self.tags = [Level.Tags.Nature, Level.Tags.Construct]

	self.apply_buff(TreesaBuff())
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","treesa"], 'Treesa', \
	color_scheme_from_hsv_color((42/360, 0.66, 0.52)), \
	'', treesa_quirks, \
	'- All [nature] spells are 1 SP cheaper\n'
	'- -100 [fire] resist\n'
	'- -100 [poison] resist\n'
	'- Spawns a peace loving potato when passing turns\n'
	'- Is a [living] [construct]' \
)


def red_dragon_quirks(self):
	self.tags = [Level.Tags.Living, Level.Tags.Dragon]
	self.add_spell([spell for spell in self.all_player_spells if isinstance(spell, Spells.DragonRoarSpell)][0])
	self.scroll_discounts[Spells.Flameblast().name] = 1
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","red_dragon"], 'Adult Dragon', \
	color_scheme_from_hsv_color((0, 1, 0.7)), \
	'', red_dragon_quirks, \
	'- Starts the game with [Dragon_Roar:dragon]\n'
	'- [Fan_of_Flames:fire] is 1 SP cheaper\n'
	'- Is a [living] [dragon]'
)

def my_flame_burst_cast(self, x, y, secondary=False, last_radius=None, last_damage=None):
	yield from Spells.FlameBurstSpell.cast(self, x, y, secondary=secondary, last_radius=last_radius, last_damage=last_damage)

	for stage in Burst(self.caster.level, Point(x, y), radius):
		for p in stage:
			if p.x == self.caster.x and p.y == self.caster.y:
				continue
			unit = self.caster.level.get_unit_at(x, y)
			if unit and not unit.is_alive() and Tags.Fire in unit.tags:
				self.damage += 1
				self.radius += 0.25

def fire_sprite_quirks(self):
	self.resists[Level.Tags.Ice] = -100
	self.resists[Level.Tags.Fire] = 50
	my_flame_burst = [spell for spell in self.all_player_spells if isinstance(spell, Spells.FlameBurstSpell)][0]
	my_flame_burst.cast = my_flame_burst_cast
	my_flame_burst.damage = int(0.5*my_flame_burst.damage)
	my_flame_burst.radius = int(0.5*my_flame_burst.radius)

	self.add_spell(my_flame_burst)

	self.tag_purchase_cost_bonus = {}
	self.tag_purchase_cost_bonus[Level.Tags.Fire] = -1
	self.tag_purchase_cost_bonus[Level.Tags.Ice] = 1
	
	# TODO: killing a fire enemy boosts fire spells' damage
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","fire_sprite"], 'Fire Sprite', \
	color_scheme_from_hsv_color((41/360, 1, 1)), \
	'', fire_sprite_quirks, \
	'- -100 [ice] resist\n'
	'- 50 [fire] resist\n'
	'- Start with a weakened [Flame_Burst:fire]\n'
	'- [Flame_Burst:fire] gains 1 damage and 0.25 radius for every fire unit it slays\n'
	'- [Fire] spells and skills are 1 SP cheaper\n'
	'- [Ice] spells and skills are 1 SP more expensive'
)



class UnicornBuff(Level.Buff):
	def __init__(self):
		Level.Buff.__init__(self)

	def on_applied(self, owner):
		self.name = "Unicorn Aura"
		self.description = "Heal allies in line of sight for [3_hp:heal] per turn."

	def on_advance(self):
		units = self.owner.level.get_units_in_los(self.owner)
		for u in units:
			if u == self.owner:
				continue
			
			u.deal_damage(-3, Level.Tags.Heal, self)
			# if are_hostile(u, self.owner):
			# 	u.deal_damage(1, Level.Tags.Holy, self)
			# 	if Level.Tags.Undead in u.tags or Level.Tags.Demon in u.tags:
			# 		u.deal_damage(1, Level.Tags.Lightning, self)

class UnicornUpgrade(Level.Upgrade):
	def on_init(self):
		self.name = "Unicorn's Nature"
		self.tags = [Level.Tags.Holy]

		self.tag_bonuses[Level.Tags.Dark]['damage'] = -10
		self.tag_bonuses[Level.Tags.Dark]['minion_damage'] = -10
		
def unicorn_quirks(self):
	self.apply_buff(UnicornBuff())
	self.apply_buff(UnicornUpgrade())

API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","unicorn_small_horn"], 'Unicorn', \
	color_scheme_from_hsv_color((292/360, 0.18, 1)), \
	'', unicorn_quirks, \
	'- Passive healing aura ([3_hp:heal])\n'
	'- [Dark] spells and minions deal 10 damage less than usual'
)


class RubyHeartNerf(Level.Buff):
	def __init__(self, heart_value):
		Level.Buff.__init__(self)
		self.heart_value = heart_value

	def on_init(self):
		self.name = "Ruby Heart Nerf"
		self.tags = [Level.Tags.Heal]

	def on_applied(self, caster):
		self.owner_triggers[Level.EventOnItemPickup] = self.on_pickup
		self.color = Level.Color(122, 10, 30)

	def on_pickup(self, evt):
		if not isinstance(evt.item, Level.HeartDot):
			return
		
		self.owner.max_hp -= evt.item.bonus
		self.owner.cur_hp -= evt.item.bonus
		
		self.owner.max_hp += self.heart_value
		self.owner.cur_hp += self.heart_value
		

class SpecialBlinkSpell(Spells.BlinkSpell):
	def cast(self, x, y):
		start_loc = Level.Point(self.caster.x, self.caster.y)

		self.caster.level.show_effect(self.caster.x, self.caster.y, Level.Tags.Translocation)
		p = Level.Point(x, y)
		if p:
			yield self.caster.level.act_move(self.caster, p.x, p.y, teleport=True)
			self.caster.level.show_effect(self.caster.x, self.caster.y, Level.Tags.Translocation)

		if self.get_stat('void_teleport'):
			for unit in self.owner.level.get_units_in_los(self.caster):
				if are_hostile(self.owner, unit):
					unit.deal_damage(self.get_stat('max_charges'), Level.Tags.Arcane, self)

		if self.get_stat('lightning_blink') or self.get_stat('dark_blink'):
			dtype = Level.Tags.Lightning if self.get_stat('lightning_blink') else Level.Tags.Dark
			damage = math.ceil(2*distance(start_loc, Point(x, y)))
			for stage in Burst(self.caster.level, Point(x, y), 3):
				for point in stage:
					if point == Point(x, y):
						continue
					self.caster.level.deal_damage(point.x, point.y, damage, dtype, self)
def ghost_quirks(self):
	original_blinkspell = [spell for spell in self.all_player_spells if isinstance(spell, Spells.BlinkSpell)][0]
	new_blinkspell = SpecialBlinkSpell()
	self.all_player_spells[self.all_player_spells.index(original_blinkspell)] = new_blinkspell
	self.add_spell(new_blinkspell)
	self.flying = True
	self.apply_buff(RubyHeartNerf(5))

API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","ghost"], 'Ghost', \
	color_scheme_from_hsv_color((268/360, 0.72, 0.52)), \
	'Ghost spritesheet by FartFish on Discord', ghost_quirks, \
	'- Starts with Blink\n'
	'- Can fly\n'
	'- Ruby Hearts give [5:damage] max hp'
)





def random_spell_name(spell):
	wizard_names = [
		('Merlin', None),
		('Balthazar', None),
		('Pendragon', None),
		('Tim', None),
		('Strange', None),
		('Gandalf', None),
		('Dumbledore', None),
		('Snape', None),
		('Belavierr', None),
		('Teriarch', [Level.Tags.Dragon, Level.Tags.Fire]),
		('Wytte', None),
		('Yoda', [Level.Tags.Arcane, Level.Tags.Holy]),
		('Carlo', [Level.Tags.Fire, Level.Tags.Nature]),
		('Thor', [Level.Tags.Lightning]),
		('Zeus', [Level.Tags.Lightning]),
		('Morgana', [Level.Tags.Dark, Level.Tags.Arcane]),
		('Mordred', [Level.Tags.Dark]),
		('Zelkyr', [Level.Tags.Conjuration]),
		('Aang', [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Nature]),
		('The Avatar', [Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Nature]),
		('Zuko', [Level.Tags.Fire]),
		('Iroh', [Level.Tags.Fire, Level.Tags.Lightning]),
		('The Sage', None),
		('The Alchemist', None),
		('The Discerning Wizard', None),
		('The Reaper', None),
		('Light', [Level.Tags.Fire, Level.Tags.Lightning, Level.Tags.Holy]),
		('The Dragon', [Level.Tags.Dragon, Level.Tags.Fire, Level.Tags.Ice, Level.Tags.Lightning]),
		('Winter', [Level.Tags.Ice]),
		('Nature', [Level.Tags.Nature]),
	]

	nouns = [
		('Comets', None),
		('Bolt', None),
		('Threads', None),
		('Last Act', None),
		('Triumph', None),
		('Failure', None),
		('Idea', None),
		('Revenge', None),
		('Alchemy', None),
		('Mana Forge', None),
		('Forest', [Level.Tags.Nature]),
		('Sky', [Level.Tags.Lightning]),
		('Thunder', [Level.Tags.Lightning]),
		('Blaze', [Level.Tags.Fire]),
		('Light', [Level.Tags.Fire, Level.Tags.Holy, Level.Tags.Lightning]),
		('Winter', [Level.Tags.Ice]),
		('Chill', [Level.Tags.Ice]),
		('Agni Kai', [Level.Tags.Fire]),
		('Retort', None),
		('Curse', [Level.Tags.Dark]),
		('Fury', None),
		('Wrath', None),
		('Gaze', [Level.Tags.Arcane]),
		('Mantra', [Level.Tags.Word]),
		('Ultimatum', None),
		('Grace', [Level.Tags.Holy]),
		('Influence', None),
		('Rite', None),
		('Shibboleth', [Level.Tags.Word]),
		('Arrow', None),
		('Spear', None),
		('Lance', None),
		('Arrow', None),
		('Vestige', None),
		('Power', None),
		('Flare', [Level.Tags.Fire]),
		('Flash', [Level.Tags.Fire, Level.Tags.Holy, Level.Tags.Lightning, Level.Tags.Arcane]),
		('Roar', [Level.Tags.Dragon]),
	]

	matching_wizard_names = [name for (name, tags) in wizard_names if tags == None or any(True for tag in tags if tag in spell.tags)]
	matching_nouns = [name for (name, tags) in nouns if tags == None or any(True for tag in tags if tag in spell.tags)]

	wizard_name = matching_wizard_names[random.randint(0, len(matching_wizard_names)-1)]
	noun = matching_nouns[random.randint(0, len(matching_nouns)-1)]
	

	if random.random() < 0.2:
		return "The " + noun + " of " + wizard_name
	else:
		return wizard_name + "'s " + noun

def xrn_quirks(self):
	randomization_key = [i for i in range(len(self.all_player_spells))]
	random.shuffle(randomization_key)
	for i in range(len(self.all_player_spells)):
		self.all_player_spells[i].level = max(1, self.all_player_spells[randomization_key[i]].level - 1)
		self.all_player_spells[i].name = random_spell_name(self.all_player_spells[i])
		print(self.all_player_spells[i].name)
	
	self.all_player_spells = sorted(self.all_player_spells, key=lambda t: t.level)
	
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","xrn"], 'Xrn', \
	color_scheme_from_hsv_color((202/360, 1, 1)), \
	'Xrn is an ant thaumaturge, and the only wizard of her people.', xrn_quirks, \
	'- All spells are 1 SP cheaper\n'
	'- All spells have their costs randomly swapped\n'
	'- All spells have their names randomly replaced'
)



def dani_quirks(self):
	#
	# swap spells and skills with eachother
	#
	def swap_spell_labels(spell1, spell2):
		temp_name = spell1.name
		temp_tags = spell1.tags
		temp_level = spell1.level
		temp_get_description = spell1.get_description
	
		spell1.name = spell2.name
		spell1.tags = spell2.tags
		spell1.level = spell2.level
		spell1.get_description = spell2.get_description

		spell2.name = temp_name
		spell2.tags = temp_tags
		spell2.level = temp_level
		spell2.get_description = temp_get_description

	
	random.shuffle(self.all_player_spells)
	randomization_key = [i for i in range(len(self.all_player_spells)//2, len(self.all_player_spells))]
	random.shuffle(randomization_key)
	for i in range(len(self.all_player_spells)//2):
		swap_spell_labels(self.all_player_spells[i], self.all_player_spells[randomization_key[i]])
	
	self.all_player_spells = sorted(self.all_player_spells, key=lambda t: t.level)

	# random.shuffle(self.all_player_skills)
	# randomization_key = [i for i in range(len(self.all_player_skills)/2, len(self.all_player_skills))]
	# random.shuffle(randomization_key)
	# for i in range(len(self.all_player_skills)/2):
	# 	swap_spell_labels(self.all_player_skills[i], self.all_player_skills[randomization_key[i]])
	
	# self.all_player_skills = sorted(self.all_player_skills, key=lambda t: t.level)
	
	#
	# other quirks
	#

	self.flying = True
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","dani_v_2"], 'Dani', \
	color_scheme_from_hsv_color((304/360, 0.16, 0.80)), \
	'', dani_quirks, \
	'- All spells have their effects randomly shuffled\n'
	'- Can fly'
)



def dorian_quirks(self):
	for spell in self.all_player_spells:
		spell.level = max(1, spell.level - 1)
	for skill in self.all_player_skills:
		skill.level = max(1, skill.level - 1)
	self.apply_buff(RubyHeartNerf(10))
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","dorian_suspenders"], 'Dorian', \
	color_scheme_from_hsv_color((183/360, 0.20, 0.98)), \
	'', dorian_quirks, \
	'- All spells and skills are 1 sp cheaper\n'
	'- Ruby Hearts are only worth [10_hp:damage]'
)


class RespawnPotSpell(Level.Spell):
	def on_init(self):
		self.range = 0

	def get_ally_player(self):
		if self.caster == self.caster.level.player_unit:
			self.ally_player = self.caster.level.player_unit_2
		elif self.caster == self.caster.level.player_unit_2:
			self.ally_player = self.caster.level.player_unit
		else:
			# this spell must be cast by a player
			assert(False)

	def cast_instant(self, x, y):
		self.get_ally_player()

		effect = Effect(x, y, Tags.Nature.color, Color(0, 0, 0), 12)
		effect.minor = False
		self.caster.level.effects.append(effect)
		yield

		API_MultiplayerSpells.spawn_p2(self.caster.level, self.ally_player)
		effect = Effect(self.ally_player.x, self.ally_player.y, Tags.Nature.color, Color(0, 0, 0), 12)
		effect.minor = False
		self.caster.level.effects.append(effect)
		yield
def monica_quirks(self):
	item = Level.Item()
	item.name = "Potion of Resurrection"
	item.description = "Drinking this potion revives the player's ally"
	item.set_spell(RespawnPotSpell())
	self.items = []
	self.add_item(item)
	self.add_item(Consumables.heal_potion())
	self.add_item(Consumables.heal_potion())
	self.add_item(Consumables.mana_potion())
	self.add_item(Consumables.youth_elixer())

	self.apply_buff(RubyHeartNerf(40))
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","monica"], 'Monica', \
	color_scheme_from_hsv_color((57/360, 0.28, 0.99)), \
	'', monica_quirks, \
	'- Starts with a [Potion_of_Resurrection:heal]\n'
	'- Also starts with two health potions, an elixer of youth, and a mana potion\n'
	'- Ruby Hearts are worth [40_hp:damage]'
)

# TODO: Nico

class NicoBuff_Active(Level.Buff):
	def __init__(self, threshold_frac):
		Level.Buff.__init__(self)
		self.threshold_frac = threshold_frac

	def on_init(self):
		self.name = "Dani's Protection Curse (active)"
		self.transform_asset_name = ["ClaysPlayerCharacters","nico_mini"]
		self.stack_type = Level.STACK_TYPE_TRANSFORM
		self.resists[Level.Tags.Dark] = 100
		self.resists[Level.Tags.Physical] = 50

		self.global_bonuses['damage'] = -15

	def on_advance(self):
		if self.owner.cur_hp > self.owner.max_hp * self.threshold_frac:
			self.owner.remove_buff(self)
			self.owner.apply_buff(NicoBuff_Inactive(self.threshold_frac))
class NicoBuff_Inactive(Level.Buff):
	def __init__(self, threshold_frac):
		Level.Buff.__init__(self)
		self.threshold_frac = threshold_frac

	def on_init(self):
		self.name = "Dani's Protection Curse (inactive)"
		self.stack_type = Level.STACK_NONE

	def on_advance(self):
		if self.owner.cur_hp < self.owner.max_hp * self.threshold_frac:
			self.owner.remove_buff(self)
			self.owner.apply_buff(NicoBuff_Active(self.threshold_frac))
def nico_quirks(self):
	self.apply_buff(NicoBuff_Inactive(0.25))
	self.apply_buff(RubyHeartNerf(40))
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","nico"], 'Nico', \
	color_scheme_from_hsv_color((96/360, 0.28, 0.85)), \
	'', nico_quirks, \
	'- Has Dani\'s Protection Curse: when hp falls below 25%, transform into mini Nico\n'
	'- As mini Nico, you have 100 [dark] resist and 50 [physical] resist, but all spells deal [15_damage_less:damage]\n'
	'- Ruby Hearts are worth [40_hp:damage]'
)


def scarecrow_quirks(self):
	# self.banned_spell_types = [Level.Tags.Translocation]
	# self.flying = True
	self.tags = [Level.Tags.Living, Level.Tags.Construct, Level.Tags.Metallic]
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","scarecrow"], 'Scarecrow', \
	color_scheme_from_hsv_color((45/360, 0.92, 1)), \
	'', scarecrow_quirks, 
	'- 50 [metallic] and 50 [fire] resist\n' # TODO: implement this
	'- Can buy a spell like Touch of Death that deals [fire] damage\n' # TODO: implement this
	'- [Fire] spells deal 1.5x damage against [metallic] targets' # TODO: implement this
	'- Is a [living] [metallic] [construct]')



def lunatic_cultist_quirks(self):
	# self.banned_spell_types = [Level.Tags.Translocation]
	self.flying = True
	self.tags = [Level.Tags.Living]
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","lunatic_cultist"], 'Lunatic Cultist', \
	color_scheme_from_hsv_color((45/360, 0.92, 1)), \
	'', lunatic_cultist_quirks, 
	'- Ritual spells are 1 SP cheaper (if the Ritual Spells mod is installed)\n' # TODO: implement this
	'- Charged spells are 1 SP cheaper\n' # TODO: implement this
	'- Spells that are not charged or ritual cannot be purchased') # TODO: implement this
	


def ceria_quirks(self):
	pass
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","ice_squirrel"], 'Ceria', \
	color_scheme_from_hsv_color((45/360, 0.92, 1)), \
	'', ceria_quirks, 
	'- 100 [ice] resist\n' # TODO: implement this
	'- All [ice] spells are 1 SP cheaper\n' # TODO: implement this
	'- Can only learn [ice] spells\n' # TODO: implement this
	'- All [ice] spells targeting a friendly skeleton upgrade them instead of dealing damage') # TODO: implement this


def pisces_quirks(self):
	pass
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","pisces"], 'Pisces', \
	color_scheme_from_hsv_color((45/360, 0.92, 1)), \
	'', pisces_quirks, 
	'- Deals 1.5x damage against [dark] targets\n' # TODO: implement this
	'- All [dark] spells are 1 SP cheaper\n' # TODO: implement this
	'- Starts with a Summon Skeleton spell that can be re-cast on a friendly skeleton to upgrade it') # TODO: implement this




# class JellyfishBuff(Level.Buff):
# 	def __init__(self):
# 		Level.Buff.__init__(self)
# 		self.name = "Nematocysts"
# 		self.owner_triggers[Level.EventOnSpellCast] = self.on_spell_cast
# 		self.buff_type = Level.BUFF_TYPE_NONE
# 		self.description = ""

# 	def on_applied(self, owner):
# 		pass

# 	def on_advance(self):
# 		pass

# 	def on_spell_cast(self, evt):
# 		self.owner.level

# strategy: give the jellyfish a buff that applies a buff "can be stung" to all units in the level in every call to on_advance
# "can be stung" has an "on damaged event" that does: whenever poison damage is dealt from a unit with the JellyfishBuff, convert all duration of the poison buff to stackable duration of the buff "Venom" 
# venom works like how Sandling suggested
def jellyfish_quirks(self):
	pass
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","jellyfish"], 'Jellyfish', \
	color_scheme_from_hsv_color((45/360, 0.92, 1)), \
	'', jellyfish_quirks, 
	'- Whenever a target is dealt [poison] damage, all stacks of poison are convereted to venom. Each turn, venom deals one damage per stack, then halves its stack size\n' # TODO: implement this
	'- Can purchase a unique Touch of Death spell that deals [poison] damage\n' ) # TODO: implement this
	

def mesmer_quirks(self):
	pass
API_Multiplayer.add_character_to_char_select(["ClaysPlayerCharacters","mesmer"], 'Mesmer', \
	color_scheme_from_hsv_color((45/360, 0.92, 1)), \
	'It is your primary directive to swIm ClOseR. iT lOoKs sO fRieNdlY', mesmer_quirks, 
	'- [Arcane] spells are 1 SP cheaper\n' # TODO: implement this
	'- [Enchantment] spells are 1 SP cheaper\n' # TODO: implement this
	'- Cannot learn [sorcery] spells') # TODO: implement this







print("Clay's Player Characters Mod Loaded")