
from Level import *
import mods.API_Universal.Modred as Modred

MultiplayerSpellTag = Tag("Multiplayer", Color(172, 255, 248))
Tags.elements.append(MultiplayerSpellTag)
Modred.add_tag_tooltip(MultiplayerSpellTag)
Modred.add_tag_keybind(MultiplayerSpellTag, 'u')

class MultiplayerSpell(Spell):
	def on_init(self):
		self.tags = [MultiplayerSpellTag]

		self.stats.append('can_target_ally')
		self.can_target_self = False
		self.can_target_ally = True

	def can_cast(self, x, y):
		if self.caster == self.caster.level.player_unit:
			self.ally_player = self.caster.level.player_unit_2
		elif self.caster == self.caster.level.player_unit_2:
			self.ally_player = self.caster.level.player_unit
		else:
			# these spells must be cast by a player
			assert(False)

		if self.get_stat('can_target_self') and x == self.caster.x and y == self.caster.y:
			return True and Spell.can_cast(self, x, y)
		if self.get_stat('can_target_ally') and x == self.ally_player.x and y == self.ally_player.y:
			return True and Spell.can_cast(self, x, y)
		
		return Spell.can_cast(self, x, y)
	
def respawn_player(alive_player, respawn_player, x, y):
	p = self.caster.level.get_summon_point(x, y)
	self.add_obj(respawn_player, p.x, p.y)

	prop = self.tiles[p.x][p.y].prop
	if prop:
		prop.on_player_enter(respawn_player)

print('Multiplayer Spells API Loaded')