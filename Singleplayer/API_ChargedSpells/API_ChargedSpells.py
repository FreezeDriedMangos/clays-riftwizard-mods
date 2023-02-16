from Level import *

# Add the base directory to sys.path for testing- allows us to run the mod directly for quick testing
import sys
sys.path.append('../..')

import Spells
print("Charged Spells API loaded")


class ChargingBuff(ChannelBuff):
	def __init__(self, spell, target, cast_after_channel=False, channel_check=None):
		ChannelBuff.__init__(self, spell, target, cast_after_channel=cast_after_channel, channel_check=channel_check)
		self.name = "Charging"

def make_ChargingBuff(spell, target):
	buff = ChannelBuff(spell, target)
	buff.name = "Charging"
	return buff

# Flavors of charged spells that I made classses for:
# Note that you can make your own types of charged spells by directly extending ChargedSpell
#
# credit to Anti-Tank Guided Missile#0888 and J.D.#5573 for helping me come up with some of these
#
# 1) Bound Spells
#	 - these spells charge for a set number of turns
#	 - during charging, nothing happens
#	 - if any non-spell action is taken during charging, charging cancels and resets
#	 - when charging ends (or if the spell is re-cast during charging), a charge is refunded, but nothing happens
#	 - the next time the spell is cast (or instantly if the spell is re-cast during charging), it uses a charge and performs the effect of the spell
#
#    - this type of spell uses self.required_charge to set the number of turns to charge
#
# 2) Incantations
#	 - these spells charge for a set number of turns
#	 - during charging, nothing happens
#	 - if any non-spell action is taken during charging, charging cancels and resets
#	 - when charging ends, the spell's effect is cast on the originally targetd tile
#
#    - this type of spell uses self.required_charge to set the number of turns to charge
#
# 3) Powerup Spells
#	 - these spells can charge for a max number of turns
#	 - every turn it's charged for, some effect increases (could be damage or radius for example)
#	 - if the spell is re-cast before charging ends, the spell's effect takes place on the new target
#	 - if charging ends, the spell's effect automatically takes place on the original target
#
#    - this type of spell uses self.max_charge to set the number of turns to charge
#
# 4) Dual Effect Spells
#	 - these spells can charge for a max number of turns
#	 - each turn spent charging, the spell has some effect
#	 - the final effect occurs when the spell ends charging or is re-cast
#
#    - this type of spell uses self.required_charge to set the number of turns to charge
#

class ChargedSpell(Spell):
	def on_init(self):
		# base Spell parameters
		self.channel = 1

		# properties used internally in ChargedSpell
		self.turns_charged = 0
		self.is_bound = False
		self.last_turn_cast = -999
		self.bound_charge = 0
		self.is_charging = False
		self.current_charging_buff = None

		self.last_x_target = 0
		self.last_y_target = 0

		# parameters set by child class
		self.stats.append('max_charge')
		self.stats.append('required_charge')
		self.stats.append('can_be_bound')
		self.stats.append('refund_charge_on_bound')
		self.stats.append('allow_early_end')

		self.refund_charge_on_bound = True
		self.can_be_bound = False
		self.allow_early_end = False
		self.set_bound_on_interrupted = False

		self.max_charge = 1000 # not to be confused with max_charges - this property controls how long you're allowed to charge the spell for
		self.required_charge = 1000

		self.restrict_recasts_during_charging_to_original_target = False
		self.end_charge_on_required_charge_reached = False


	def cast(self, x, y, channel_cast=False):
		# setup for can_cast
		self.last_x_target = x
		self.last_y_target = y

		# if the spell has been upgraded to enable being bound, 
		# set can_be_bound to true
		if (self.get_stat('can_be_bound')):
			self.can_be_bound = True
			
		if (self.get_stat('set_bound_on_interrupted')):
			self.can_be_bound = True
			self.set_bound_on_interrupted = True

			
		if(self.last_turn_cast < self.caster.level.turn_no-1):
			self.is_charging = False

		self.last_turn_cast = self.caster.level.turn_no

		# enable channeling
		if (not channel_cast and not self.is_bound and not self.is_charging):
			self.current_charging_buff = make_ChargingBuff(self.cast, Point(x, y))
			self.caster.apply_buff(self.current_charging_buff, self.get_charge_time())
			self.is_charging = True
			# we return here because channelling spells get cast twice the first turn
			return

		# ##############################
		#
		#	Prevent charging from continuing
		#	after an interruption
		#
		# ##############################

		# if (self.last_turn_cast != self.caster.level.turn_no-1):
		# 	self.cast_interrupted(x, y, self.turns_charged, self.get_stat("max_charge")-self.turns_charged, self.caster.level.turn_no-self.last_turn_cast-1)
		# 	if (self.set_bound_on_interrupted):
		# 		self.bound_charge = self.turns_charged
		# 		self.is_bound = True
		# 	self.turns_charged = 0
			

		# ##############################
		#
		#	Bound Spells mechanic
		#
		# ##############################

		if (self.get_stat('can_be_bound') and self.is_bound and not self.is_charging):
			self.is_bound = False
			self.name = self.name_original
			yield from self.cast_bound(x, y, self.bound_charge)
			return

		# if the spell is not allowed to be a bound spell, and it has been bound,
		# un-bind it. This is to account for spells that can be bound as an upgrade - 
		# we don't want those spells to become bound before getting that upgrade
		if (self.is_bound):
			self.is_bound = False


		# ##############################
		#
		#	Handle charging limit reached
		#
		# ##############################

		if (self.turns_charged >= self.get_stat("required_charge") and self.end_charge_on_required_charge_reached):
			self.is_charging = False
			yield from self.cast_end(x, y, self.turns_charged)
			
			if (self.get_stat('can_be_bound')):
				self.is_bound = True
				self.name_original = self.name
				self.name = 'BOUND ' + self.name_original
				self.bound_charge = self.turns_charged
				
				if (self.get_stat('refund_charge_on_bound')):
					self.cur_charges += 1
			
			self.turns_charged = 0
			
			return


		# if the spell has been charged 
		if (self.turns_charged >= self.get_stat("max_charge")):
			self.is_charging = False
			yield from self.cast_end(x, y, self.turns_charged)

			if (self.get_stat('can_be_bound')):
				self.is_bound = True
				self.name_original = self.name
				self.name = 'BOUND ' + self.name_original
				self.bound_charge = self.turns_charged
				
				if (self.get_stat('refund_charge_on_bound')):
					self.cur_charges += 1
			
			self.turns_charged = 0

			return
		
		# ##############################
		#
		#	Handle spell recast during charging
		#
		# ##############################

		# if the player casts the spell again, not by channeling, 
		# this counts as them ending the charging, and for some spells,
		# casting the spell prematurely. Some spells may wish to 
		# cast a weaker version of the spell when this happens, while others
		# may wish to ignore this event.
		if not channel_cast and self.is_charging:
			if (self.get_stat('allow_early_end')):
				yield from self.cast_early_end(x, y, self.turns_charged, self.get_stat("max_charge")-self.turns_charged)
				self.turns_charged = 0
				self.last_turn_cast = -999 # make sure that if the user casts the spell AGAIN, it doesn't count as channeling
				self.is_charging = False
				self.caster.remove_buff(self.current_charging_buff)
				return
			else:
				self.turns_charged = 1
				yield from self.cast_charging(x, y, self.turns_charged, self.get_stat("max_charge")-self.turns_charged)
				return

		
		# ##############################
		#
		#	Handle the charging itself
		#
		# ##############################

		# for a charged spell, channeling counts as charging
		# also, the first turn of a charged spell always counts as charging
		if (channel_cast or self.turns_charged == 0):
			self.turns_charged += 1
			yield from self.cast_charging(x, y, self.turns_charged, self.get_stat("max_charge")-self.turns_charged)
			return
		

		yield None

	def get_charge_time(self):
		return self.get_stat('max_charge')+1

	# what to do if a fully charged bound spell is cast
	def cast_bound(self, x, y, turns_charged):
		assert(False)

	# what to do on the final turn of charging (aka the turn after charging has completed)
	def cast_end(self, x, y, turns_charged):
		assert(False)

	# what to do if the spell is ended before charging completes
	def cast_early_end(self, x, y, turns_charged, turns_remaining):
		assert(False)

	# what do do each turn that the spell is charging
	def cast_charging(self, x, y, turns_charged, turns_remaining):
		assert(False)

	# what to do the next time the spell is cast after being interrupted
	def cast_interrupted(self, x, y, turns_charged, turns_remaining, turns_since_interruption):
		assert(False)

	
	def can_cast(self, x, y):
		if not Spell.can_cast(self, x, y):
			return False

		if self.restrict_recasts_during_charging_to_original_target and self.is_charging and self.last_turn_cast >= self.caster.level.turn_no-1:
			return x == self.last_x_target and y == self.last_y_target
		
		return True



# ##############################
#
#	Convenience classes below.
#	If you want, you can directly inherit from
#	ChargedSpell.
#
# ##############################

class BoundSpell(ChargedSpell):
	#
	# when inheriting this class, always call base.on_init(self)
	#
	def on_init(self):
		ChargedSpell.on_init(self)

		self.range = 0

		self.refund_charge_on_bound = True
		self.can_be_bound = True
		self.set_bound_on_interrupted = False

		# bonus properties for the inheriting spell to implement
		self.charging_effect_color = Tags.Physical.color
		self.bound_range = 10

		self.end_charge_on_required_charge_reached = True

	def get_charge_time(self):
		return self.get_stat('required_charge')+1

	# what to do if a fully charged bound spell is cast
	def cast_bound(self, x, y, turns_charged):
		self.range = 0
		yield from self.on_cast(x, y)

	# what to do when the spell is ready
	def cast_end(self, x, y, turns_charged):
		# set range
		self.range = self.bound_range

		# show final effect
		effect = Effect(x, y, self.charging_effect_color, Color(0, 0, 0), 12)
		effect.minor = False
		self.caster.level.effects.append(effect)
		yield
		return

	# refund a spell charge - charging continues, recasting has no effect
	# refunding the spell charge is just to be nice to the player who 
	# probably did this accidentally
	def cast_early_end(self, x, y, turns_charged, turns_remaining):
		if (self.get_stat('refund_charge_on_bound')):
			self.cur_charges += 1

	# show charging effect
	def cast_charging(self, x, y, turns_charged, turns_remaining):
		effect = Effect(x, y, self.charging_effect_color, Color(0, 0, 0), 12)
		effect.minor = True
		self.caster.level.effects.append(effect)
		yield
		return

	# do nothing
	def cast_interrupted(self, x, y, turns_charged, turns_remaining, turns_since_interruption):
		yield
		return

	#
	# Implement these methods when inheriting this class
	#
	def on_cast(self, x, y):
		# Assert on unimplemented spells
		assert(False)


class IncantationSpell(ChargedSpell):
	#
	# when inheriting this class, always call base.on_init(self)
	#
	def on_init(self):
		ChargedSpell.on_init(self)
		
		self.allow_early_end = False
		self.set_bound_on_interrupted = False
		
		self.charging_effect_color = Tags.Physical.color # bonus property for the inheriting spell to implement

		self.end_charge_on_required_charge_reached = True

	def get_charge_time(self):
		return self.get_stat('required_charge')+1

	# If this incantation can be bound, only cast it as a bound spell
	def cast_bound(self, x, y, turns_charged):
		if (self.get_stat('can_be_bound')):
			yield from self.on_cast(x, y)
		else:
			yield None

	# normal cast of an incantation spell
	def cast_end(self, x, y, turns_charged):
		if (not self.get_stat('can_be_bound')):
			yield from self.on_cast(x, y)
		else:
			yield None

	# refund a spell charge - charging continues, recasting has no effect
	# refunding the spell charge is just to be nice to the player who 
	# probably did this accidentally
	def cast_early_end(self, x, y, turns_charged, turns_remaining):
		if (self.get_stat('refund_charge_on_bound')):
			self.cur_charges += 1
		yield

	# show charging effect
	def cast_charging(self, x, y, turns_charged, turns_remaining):
		effect = Effect(x, y, self.charging_effect_color, Color(0, 0, 0), 12)
		effect.minor = True
		self.caster.level.effects.append(effect)
		yield
		return

	# do nothing
	def cast_interrupted(self, x, y, turns_charged, turns_remaining, turns_since_interruption):
		yield
		return

	#
	# Implement this method when inheriting this class
	#
	def on_cast(self, x, y):
		# Assert on unimplemented spells
		assert(False)


class PowerupSpell(ChargedSpell):
	#
	# when inheriting this class, always call base.on_init(self)
	#
	def on_init(self):
		ChargedSpell.on_init(self)
		
		self.refund_charge_on_bound = True
		self.can_be_bound = False
		self.allow_early_end = True
		self.set_bound_on_interrupted = False

		self.charging_effect_color = Tags.Physical.color


	def get_charge_time(self):
		return self.get_stat('max_charge')+1

	# If this incantation can be bound, only cast it as a bound spell
	def cast_bound(self, x, y, turns_charged):
		if (self.get_stat('can_be_bound')):
			yield from self.on_cast(x, y, turns_charged)
		else:
			yield

	def cast_end(self, x, y, turns_charged):
		if (not self.get_stat('can_be_bound')):
			yield from self.on_cast(x, y, turns_charged)
		else:
			yield

	# refund a spell charge - recasting is used to end the spell early, it shouldn't
	# cost a spell charge
	# TODO: override can_cast to allow the spell to be cast even when it has 0 charges remaining, but only if it was charging last turn
	def cast_early_end(self, x, y, turns_charged, turns_remaining):
		if (self.get_stat('refund_charge_on_bound')):
			self.cur_charges += 1
		yield from self.on_cast(x, y, turns_charged)

	# show charging effect
	def cast_charging(self, x, y, turns_charged, turns_remaining):
		effect = Effect(x, y, self.charging_effect_color, Color(0, 0, 0), 12)
		effect.minor = True
		self.caster.level.effects.append(effect)
		yield
		return

	# do nothing
	def cast_interrupted(self, x, y, turns_charged, turns_remaining, turns_since_interruption):
		yield
		return

	#
	# Implement this method when inheriting this class
	#
	def on_cast(self, x, y, turns_charged):
		# Assert on unimplemented spells
		assert(False)

class DualEffectSpell(ChargedSpell):
	#
	# when inheriting this class, always call base.on_init(self)
	#
	def on_init(self):
		ChargedSpell.on_init(self)
		
		self.refund_charge_on_bound = True
		self.can_be_bound = False
		self.allow_early_end = True
		self.set_bound_on_interrupted = False

		self.charging_effect_color = Tags.Physical.color

		# if you want to get the second effect of this spell early, you have to cast it at the same location you initially cast it (where it was aimed during charging)
		self.restrict_recasts_during_charging_to_original_target = True

	def get_charge_time(self):
		return self.get_stat('max_charge')+1

	# do nothing - these spells cannot be bound
	def cast_bound(self, x, y, turns_charged):
		yield
		return

	def cast_end(self, x, y, turns_charged):
		yield from self.on_cast2(x, y, turns_charged)

	# refund a spell charge - recasting is used to end the spell early, it shouldn't
	# cost a spell charge
	# TODO: override can_cast to allow the spell to be cast even when it has 0 charges remaining, but only if it was charging last turn
	def cast_early_end(self, x, y, turns_charged, turns_remaining):
		if (self.get_stat('refund_charge_on_bound')):
			self.cur_charges += 1
		yield from self.on_cast2(x, y, turns_charged)

	# do nothing
	def cast_charging(self, x, y, turns_charged, turns_remaining):
		yield from self.on_cast1(x, y, turns_charged, turns_remaining)

	# do nothing
	def cast_interrupted(self, x, y, turns_charged, turns_remaining, turns_since_interruption):
		yield
		return

	#
	# Implement these methods when inheriting this class
	#
	def on_cast1(self, x, y, turns_charged, turns_remaining):
		# Assert on unimplemented spells
		assert(False)
	def on_cast2(self, x, y, turns_charged):
		# Assert on unimplemented spells
		assert(False)
