import mods.API_MultiplayerSpells.API_MultiplayerSpells as API_MultiplayerSpells
import Spells 
from Level import *
import Upgrades

class WordOfRessurection(API_MultiplayerSpells.MultiplayerSpell):
	def on_init(self):
		self.name = "Word of Ressurection"
		self.tags = [Tags.Nature, Tags.Multiplayer, Tags.Word]
		self.element = Tags.Nature
		self.level = 7
		self.max_charges = 1
		self.range = 0
		self.can_target_self = True

		self.upgrades['max_charges'] = (1, 2)

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.units if u != self.caster]

	def get_description(self):
		return ("Ressurrects your ally if they have no hp.\n"
				"Fails if your ally is currently alive.\n"
				"Unlearns itself after use.").format(**self.fmt_dict())

	def cast(self, x, y):
		if self.ally_player.cur_hp > 0:
			yield 
			return
			
		effect = Effect(x, y, Tags.Nature.color, Color(0, 0, 0), 12)
		effect.minor = False
		self.caster.level.effects.append(effect)
		yield

		API_MultiplayerSpells.respawn_player(self.caster, self.ally_player, x, y)
		effect = Effect(self.ally_player.x, self.ally_player.y, Tags.Nature.color, Color(0, 0, 0), 12)
		effect.minor = False
		self.caster.level.effects.append(effect)
		yield

		self.caster.spells.remove[self]
		yield

Spells.all_player_spell_constructors.append(WordOfRessurection)


class AllyCantripCascade(Spell):
	
	def on_init(self):
		self.name = "Ally's Cantrip Cascade"
		self.level = 5
		self.tags = [Tags.Arcane, Tags.Sorcery, Tags.Multiplayer]
		self.max_charges = 3
		self.angle = math.pi / 6
		self.range = 7
		self.upgrades['max_charges'] = (3, 2)
		self.upgrades['range'] = (3, 3)

	def get_impacted_tiles(self, x, y):
		target = Point(x, y)
		burst = Burst(self.caster.level, self.caster, self.get_stat('range'), expand_diagonals=True, burst_cone_params=BurstConeParams(target, self.angle))
		return [p for stage in burst for p in stage if self.caster.level.can_see(self.caster.x, self.caster.y, p.x, p.y)]


	def cast_instant(self, x, y):
		units = [self.caster.level.get_unit_at(p.x, p.y) for p in self.get_impacted_tiles(x, y)]
		enemies = [u for u in units if u and are_hostile(u, self.caster)]
		spells = [s for s in self.ally_player.spells if s.level == 1 and Tags.Sorcery in s.tags]

		pairs = list(itertools.product(enemies, spells))

		random.shuffle(pairs)

		for enemy, spell in pairs:
			self.caster.level.act_cast(self.caster, spell, enemy.x, enemy.y, pay_costs=False)

	def get_description(self):
		return ("Cast each of your ally's level 1 sorcery spells on each enemy in a cone.")

Spells.all_player_spell_constructors.append(AllyCantripCascade)

class TrueAlliesBuff(Buff):
	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		self.name = "True Allies"
		self.buff_type = BUFF_TYPE_BLESS
		self.color = Tags.Multiplayer.color
		self.description = "Gain your partner's resistances and weaknesses."
		self.stack_type = STACK_DURATION

	def on_applied(self, caster):
		self.resists = self.spell.ally_player.resists

class TrueAlliesSpell(API_MultiplayerSpells.MultiplayerSpell):
	def on_init(self):
		self.range = 0
		self.max_charges = 3
		self.name = "True Allies"
		self.can_target_self = True
		self.can_target_ally = False
		
		self.tags = [Tags.Multiplayer, Tags.Enchantment]
		self.level = 4
		self.duration = 10

		self.upgrades['max_charges'] = (3, 2)
		

	def cast(self, x, y):
		if self.ally_player.cur_hp <= 0:
			yield
			return
		self.caster.apply_buff(TrueAlliesBuff(self), self.get_stat('duration'))
		yield

	def get_description(self):
		return ("Gain your ally's resists and weaknessess for {duration} turns.\n"
				"This spell fails if your ally is not alive.").format(**self.fmt_dict())

Spells.all_player_spell_constructors.append(TrueAlliesSpell)


class HeartSwapBuff(Buff):
	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		self.name = "Heart Swap"
		self.buff_type = BUFF_TYPE_BLESS
		self.color = Tags.Multiplayer.color
		self.description = "Your partner is taking damage in your place."
		self.stack_type = STACK_DURATION

	def on_applied(self, caster):
		self.owner_triggers[EventOnPreDamaged] = self.on_damage
		
		# if the player who placed this buff on their ally also has this buff, remove it
		buffs = [b for b in self.spell.owner.buffs if isinstance(b, HeartSwapBuff)]
		for b in buffs:
			self.spell.owner.remove_buff(b)

	def on_damage(self, damage_event):
		# damage_event.unit
		# damage_event.damage
		# damage_event.damage_type
		# damage_event.source
		damage_event.unit.cur_hp += damage_event.damage
		self.spell.owner.level.deal_damage(self.spell.owner.x, self.spell.owner.y, damage_event.damage, damage_event.damage_type, self.damage_event.source)
		
class HeartSwapSpell(API_MultiplayerSpells.MultiplayerSpell):
	# applies HeartSwapBuff to ally, not to self
	def on_init(self):
		self.range = 10
		self.requires_los = True
		self.max_charges = 3
		self.name = "Heart Swap"
		self.can_target_self = False
		self.can_target_ally = True
		
		self.tags = [Tags.Multiplayer, Tags.Enchantment]
		self.level = 6
		self.duration = 10

		self.upgrades['max_charges'] = (3, 2)

	def cast(self, x, y):
		if self.ally_player.cur_hp <= 0:
			yield
			return
		self.ally_player.apply_buff(HeartSwapBuff(self), self.get_stat('duration'))
		yield
		
	def get_description(self):
		return ("For the next {duration} turns, take the damage meant for your ally.\n"
				"This spell fails if your ally is not alive.").format(**self.fmt_dict())
Spells.all_player_spell_constructors.append(HeartSwapSpell)


class SpellSwapBuff(Buff):
	def __init__(self, spell, is_leader=True):
		self.spell = spell
		Buff.__init__(self)
		self.name = "Spell Swap"
		self.buff_type = BUFF_TYPE_BLESS
		self.color = Tags.Multiplayer.color
		self.description = "You and your partner are swapping spells."
		self.stack_type = STACK_DURATION
		self.is_leader = is_leader

		self.ready_to_swap = False
		self.last_spell_cast = None

	def on_applied(self, caster):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		
		# if the ally player also has this buff, remove it
		buffs = [b for b in self.spell.ally_player.buffs if isinstance(b, HeartSwapBuff)]
		for b in buffs:
			self.spell.ally_player.remove_buff(b)

		self.ally_buff = SpellSwapBuff(self.spell, is_leader=False)
		self.spell.owner.ally_player.apply_buff(self.ally_buff, self.spell.get_stat('duration'))

	def on_spell_cast(self, spell_event):
		# spell_event.spell
		# spell_event.caster
		# spell_event.x
		# spell_event.y
		self.last_spell_cast = spell_event.spell
		self.ready_to_swap = True

		if self.ally_buff.ready_to_swap and self.ready_to_swap:
			# swap spells
			own_player_spell_index = self.spell.owner.spells.index(self.last_spell_cast)
			ally_player_spell_index = self.spell.ally_player.spells.index(self.ally_buff.last_spell_cast)

			self.spell.owner.spells[own_player_spell_index] = self.ally_buff.last_spell_cast
			self.spell.ally_player.spells[ally_player_spell_index] = self.last_spell_cast

			self.ready_to_swap = False
			ally_buff.ready_to_swap = False

class SpellSwapSpell(API_MultiplayerSpells.MultiplayerSpell):
	def on_init(self):
		self.range = 0
		self.requires_los = False
		self.max_charges = 10
		self.name = "Heart Swap"
		self.can_target_self = True
		self.can_target_ally = False
		
		self.tags = [Tags.Multiplayer, Tags.Enchantment]
		self.level = 2
		self.duration = 10

	def cast(self, x, y):
		if self.ally_player.cur_hp <= 0:
			yield
			return
		self.ally_player.apply_buff(SpellSwapBuff(self), self.get_stat('duration'))
		yield
		
	def get_description(self):
		return ("For the next {duration} turns, swap the last spell you and your ally used.\n"
				"This spell fails if your ally is not alive.").format(**self.fmt_dict())

Spells.all_player_spell_constructors.append(SpellSwapSpell)



class PainSplit(API_MultiplayerSpells.MultiplayerSpell):
	# applies HeartSwapBuff to ally, not to self
	def on_init(self):
		self.range = 10
		self.requires_los = True
		self.max_charges = 3
		self.name = "Pain Split"
		self.can_target_self = False
		self.can_target_ally = True
		
		self.tags = [Tags.Multiplayer, Tags.Enchantment]
		self.level = 2
		self.duration = 10

		self.upgrades['max_charges'] = (3, 2)

	def cast(self, x, y):
		if self.ally_player.cur_hp <= 0:
			yield
			return
		hp = int((self.owner.cur_hp + self.ally_player.cur_hp) / 2)
		self.owner.cur_hp = hp
		self.ally_player.cur_hp = hp
		yield
		
	def get_description(self):
		return ("Pool your hp with your ally; you each recieve half of the total.\n"
				"This spell fails if your ally is not alive.").format(**self.fmt_dict())
Spells.all_player_spell_constructors.append(PainSplit)


class TelepathicLinkSkill(Upgrade):
	def on_init(self):
		self.name = "Telepathic Link"
		self.tags = [Tags.Translocation, Tags.Multiplayer, Tags.Enchantment]
		self.level = 5
		self.is_active = False

	def on_applied(self, owner):
		self.is_active = True
		for spell in owner.all_player_spells:
			if spell.range == 0:
				func_type = type(self.spell_can_cast)
				spell.can_cast = func_type(self.confirm_buy, self, spell.can_cast)

	def spell_can_cast(self, buff, old_can_cast, x, y):
		if buff.active and x == self.caster.ally_player.x and y == self.caster.ally_player.y:
			return old_can_cast(self.caster.x, self.caster.y)

		return old_can_cast(x, y)

	def on_unapplied(self):
		self.is_active = False

	def get_description(self):
		return ("Form a one-way telepathic link with your ally.\n"
				"Self-targeting enchantments can now be cast on your ally player, no matter how far away they are.")

Upgrades.skill_constructors.append(TelepathicLinkSkill)





print("Clay's Multiplayer Spells Mod Loaded")