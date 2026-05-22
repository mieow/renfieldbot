import random
import discord
import pprint
import logging
import traceback
from discord.ext import commands
from discord import Embed, app_commands
from cogs.wordpress_api import get_my_character, get_character, is_storyteller, get_active_characters
from renfield_sql import check_is_auth, check_restapi_active
from helper.diceroller_viewer import *

forminputIDs = {
	"CelerityPulldownActionRow": 1,
	"DexterityPulldownActionRow" : 2,
	"StaminaPulldownActionRow" : 3,
	"WillpowerButton": 4,
	"DamageTypePulldownActionRow": 5,
	"DifficultyPulldownActionRow": 6,
	"StrengthPulldownActionRow": 7,
	"WoundPulldownActionRow": 8,
	"SpecialityButton": 9,
	"DriveStatPulldownActionRow": 10,
	"VehiclePulldownActionRow": 11,
	"SpeedPulldownActionRow": 12,
	"WeatherButton": 13,
	"TrafficButton": 14,
	"PursuitButton": 15,
	"TimescalePulldownActionRow": 16,
	"IntensityPulldownActionRow": 17,
	"BackgroundPulldownActionRow": 18,
	"SinsPulldownActionRow": 19
}

canlift = [
	"Crush a beer can (20kg)",
	"Break a wooden chair (45kg)",
	"Break down a wooden door (115kg)",
	"Break a wooden plank (180kg)",
	"Break open a metal fire door (295kg)",
	"Throw a motorcycle (360kg)",
	"Flip over a small car (410kg)",
	"Break a lead pipe (455kg)",
	"Punch through a cement wall (545kg)",
	"Rip open a steel drum (680kg)",
	"Punch through 1 inch thick sheet metal (910kg)",
	"Break a metal lamp post (1360kg)",
	"Throw a station wagon (1815kg)",
	"Throw a van (2265kg)",
	"Throw a truck (2720kg)"
]

auras = [
	"Can distinguish only the shade (pale or bright)",
	"Can distinguish the main colour",
	"Can recognise the colour patterns",
	"Can detect subtle shifts",
	"Can identify mixtures of colour and pattern"
]

timescales = {
	"centuries (diff +5)": 5,
	"decades (diff +4)": 4,
	"years (diff +3)": 3,
	"months (diff +2)": 2,
	"weeks (diff +1)": 1,
	"days" : 0,
	"hours (diff -1)": -1,
	"minutes (diff -2)": -2
}

intensity = {
	"weak or neutral emotions (diff +1)": 1,
	"heightened emotions, e.g. tension or worry": 0,
	"strong emotions, e.g. passion or fear (diff -1)": -1,
	"very strong emotions, e.g. frenzy, death, love (diff -2)": -2,
	"historical turning point (diff -5)": -5
}

wounds = {
	"Unhurt (0)": "unhurt:0",
	"Bruised (0)": "bruised:0",
	"Hurt (-1)": "hurt:-1",
	"Injured (-1)": "injured:-1",
	"Wounded (-2)": "wounded:-2",
	"Mauled (-2)": "mauled:-2",
	"Crippled (-5)": "crippled:-5"
}

hierarchyofsin = {
	"Humanity": {
		"Selfish thoughts": 100,
		"Minor selfish acts": 90,
		"Injury to another (accidental or otherwise)": 80,
		"Theft": 70,
		"Accidental violation (drinking a vessel dry out of starvation)": 60,
		"Intentional property damage": 50,
		"Impassioned violation (manslaughter, killing a vessel in frenzy)": 40,
		"Planned violation (outright murder, savored exsanguination)": 30,
		"Casual violation (thoughtless killing, feeding past satiation)": 20,
		"Utter perversion or heinous acts": 10
	},
	"Path of Blood": {
		"Killing a mortal for sustenance": 100,
		"Breaking a word of honor to a Clanmate": 90,
		"Refusing to offer a non-Assamite an opportunity to convert": 80,
		"Failing to destroy an unrepentant Kindred outside the Clan": 70,
		"Succumbing to frenzy": 60,
		"Failing to pursue the lore of Khayyin": 50,
		"Failing to demand blood as payment": 40,
		"Refusal to aid a more advanced	member of the Path": 30,
		"Failing to tithe blood": 20,
		"Acting against another Assamite": 10
	},
	"Path of the Bones": {
		"Showing a fear of death": 100,
		"Failing to study an occurrence of death": 90,
		"Accidental killing": 80,
		"Postponing feeding when hungry": 70,
		"Succumbing to frenzy": 60,
		"Refusing to kill when an opportunity presents itself": 50,
		"Making a decision based on emotion rather than logic": 40,
		"Inconveniencing oneself for another's benefit": 30,
		"Needlessly preventing a death": 20,
		"Actively preventing a death": 10
	},
	"Path of Caine": {
		"Failing to engage in research or study each night, regardless of circumstances": 100,
		"Failing to instruct other vampires in the Path of Caine": 90,
		"Befriending or co-existing with mortals": 80,
		"Showing disrespect to other students of Caine": 70,
		"Failing to ride the wave in frenzy": 60,
		"Succumbing to Rötschreck": 50,
		"Failing to diablerize a 'humane' vampire": 40,
		"Failing to regularly test the limits of abilities and Disciplines": 30,
		"Failing to pursue lore about vampirism when the opportunity arises": 20,
		"Denying vampiric needs (by refusing to feed, showing compassion, or failing to learn about one’s vampiric abilities": 10	
	},
	"The Path of Cathari": {

		"Exercising restraint": 100,
		"Showing trust": 90,
		"Failing to pass on the Curse to the passionately wicked or virtuous": 80,
		"Failing to ride the wave in frenzy": 70,
		"Acting against another Albigensian": 60,
		"Impassioned killing": 50,
		"Sacrificing gratification for someone else's convenience": 40,
		"Refraining from indulgence": 30,
		"Arbitrary killing": 20,
		"Encouraging others to exercise restraint": 10	
	},
	"Path of the Feral Heart": {

		"Hunting with means other than your own vampiric powers": 100,
		"Engaging in politics": 90,
		"Remaining in the presence of fire or sunlight, except to kill an enemy": 80,
		"Acting in an overly cruel manner": 70,
		"Failing to hunt when hungry": 60,
		"Failing to support your pack or allies": 50,
		"Killing without need": 40,
		"Failing to follow one’s instincts": 30,
		"Killing a creature other than for survival": 20,
		"Refusing to kill to survive": 10
	},
	"Path of Honorable Accord": {

		"Failing to uphold all the precepts of your group": 100,
		"Failing to show hospitality to your allies": 90,
		"Associating with the dishonorable": 80,
		"Failing to participate in your group's rituals": 70,
		"Disobeying your leader": 60,
		"Failing to protect your allies": 50,
		"Placing personal concerns over duty": 40,
		"Showing cowardice": 30,
		"Killing without reason": 20,
		"Breaking your word or oath; failing to honor an agreement": 10
	},
	"Path of Lilith": {

		"Feeding immediately when hungry": 100,
		"Pursuing temporal wealth or power": 90,
		"Not correcting the errors of others regarding Caine and Lilith": 80,
		"Feeling remorse for bringing pain to someone": 70,
		"Failing to participate in a Bahari ritual": 60,
		"Fearing death": 50,
		"Killing a living or unliving being": 40,
		"Not seeking out the teachings of Lilith": 30,
		"Failing to dispense pain and anguish": 20,
		"Shunning pain": 10
	},
	"Path of Metamorphosis": {

		"Postponing feeding when hungry": 100,
		"Indulging in pleasure": 90,
		"Asking another for knowledge": 80,
		"Sharing knowledge with another": 70,
		"Refusing to kill when knowledge may be gained from it": 60,
		"Failing to ride out a frenzy": 50,
		"Considering the needs of others": 40,
		"Failure to experiment, even at risk to oneself": 30,
		"Neglecting to alter one’s own body": 20,
		"Exhibiting compassion for others": 10
	},
	"Path of Night": {

		"Killing a mortal for food": 100,
		"Acting in the interests of another": 90,
		"Failing to be innovative in one's depredations": 80,
		"Asking aid of another": 70,
		"Accidental killing": 60,
		"Bowing to another Kindred's will": 50,
		"Intentional or impassioned killing": 40,
		"Aiding another": 30,
		"Accepting another's claim to superiority": 20,
		"Repenting one's behavior": 10
	},
	"Path of Paradox": {

		"Embracing a woman": 100,
		"Embracing outside the jati": 90,
		"Destroying another Shilmulo": 80,
		"Killing a mortal for sustenance": 70,
		"Failing to destroy a vampire on another Path": 60,
		"Killing a mortal for reasons other than survival": 50,
		"Failure to aid another's svadharma": 40,
		"Allowing one's Sect affairs to take precedence over one’s dharma": 30,
		"Becoming blood bound": 20,
		"Embracing needlessly or out of personal desire": 10
	},
	"Power and the Inner Voice": {

		"Denying responsibility for your actions": 100,
		"Treating your underlings poorly": 90,
		"Failing to respect your superiors": 80,
		"Helping others when it is not to your advantage": 70,
		"Accepting defeat": 60,
		"Failing to kill when it's in your interests": 50,
		"Submitting to the error of others": 40,
		"Not using the most effective tools for control": 30,
		"Not punishing failure": 20,
		"Turning down the opportunity for power": 10
	},
	"Path of Typhon": {

		"Pursuing one's own indulgences instead of another's": 100,
		"Refusing to aid another follower of the Path": 90,
		"Failing to destroy a vampire in Golconda": 80,
		"Failing to observe Setite religious ritual": 70,
		"Failing to undermine the current social order in favor of the Setites": 60,
		"Failing to do whatever is necessary to corrupt another": 50,
		"Failing to pursue arcane knowledge": 40,
		"Obstructing another Setite's efforts": 30,
		"Failing to take advantage of another's weakness": 20,
		"Refusing to aid in Set's resurrection": 10
	}
}

vehicles = {
	"6 Wheel Truck (3)": {
		"safespeed": 60,
		"maxspeed": 90,
		"maneuver": 3
	},
	"Modern Tank (4)": {
		"safespeed": 60,
		"maxspeed": 100,
		"maneuver": 4
	},
	"WWII Tank (3)": {
		"safespeed": 30,
		"maxspeed": 40,
		"maneuver": 3
	},
	"Bus (3)": {
		"safespeed": 60,
		"maxspeed": 100,
		"maneuver": 3
	},
	"18-Wheeler (3)": {
		"safespeed": 70,
		"maxspeed": 110,
		"maneuver": 3
	},
	"Sedan (4)": {
		"safespeed": 70,
		"maxspeed": 120,
		"maneuver": 4
	},
	"Minivan (5)": {
		"safespeed": 70,
		"maxspeed": 120,
		"maneuver": 5
	},
	"Compact (6)": {
		"safespeed": 70,
		"maxspeed": 130,
		"maneuver": 6
	},
	"Sporty Compact (6)": {
		"safespeed": 100,
		"maxspeed": 140,
		"maneuver": 6
	},
	"Sport Coupe (7)": {
		"safespeed": 110,
		"maxspeed": 150,
		"maneuver": 7
	},
	"Sports Car (8)": {
		"safespeed": 110,
		"maxspeed": 160,
		"maneuver": 8
	},
	"Exotic Car (9)": {
		"safespeed": 130,
		"maxspeed": 190,
		"maneuver": 9
	},
	"Luxury Sedan (7)": {
		"safespeed": 85,
		"maxspeed": 155,
		"maneuver": 7
	},
	"Sport Sedan (8)": {
		"safespeed": 85,
		"maxspeed": 165,
		"maneuver": 8
	},
	"Midsize (6)": {
		"safespeed": 75,
		"maxspeed": 125,
		"maneuver": 6
	},
	"SUV/Crossover (6)": {
		"safespeed": 70,
		"maxspeed": 115,
		"maneuver": 6
	},
	"Formula One Racer (10)": {
		"safespeed": 140,
		"maxspeed": 240,
		"maneuver": 10
	},
	# Bikes
	"Harley Motorcycle (6)": {
		"safespeed": 80,
		"maxspeed": 120,
		"maneuver": 6
	},
	"Sports bike (8)": {
		"safespeed": 120,
		"maxspeed": 180,
		"maneuver": 8
	}
}

# SUCCESSES - BOLD
# 10S - ITALIC

def sort_character_list(characterlist):
	"""
	Sort a character list by character name in ascending alphabetical order.
	
	Args:
		characterlist: A list of dictionaries containing character data with 'characterName' key
	
	Returns:
		The sorted character list
	"""
	return sorted(characterlist, key=lambda char: char.get('characterName', ''))


def sort_character_backgrounds(backgroundlist):
	"""
	Sort a character backgrounds list by background, then level, then sector, then comment.
	
	Args:
		backgroundlist: A list of dictionaries containing background data with 'background', 'level', 'sector', 'comment' keys
	
	Returns:
		The sorted background list
	"""
	return sorted(backgroundlist, key=lambda bg: (bg.get('background', ''), bg.get('level', ''), bg.get('sector', ''), bg.get('comment', '')))


class RollSinsDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView', path: str):	

		options = []
		if path not in hierarchyofsin:
			path = "Path of " + path
		if path in hierarchyofsin:
			for sin in hierarchyofsin[path]:
				level = hierarchyofsin[path][sin]
				if level <= 30:
					label = "The cardinal sin of {} ({})".format(sin, level)
				else:
					label = "{} ({})".format(sin, level)
				options.append(discord.SelectOption(label=label, value=level))

		if len(options) == 0:
			options.append(discord.SelectOption(label="Missing path: " + path, value=0))

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options, placeholder="Choose a sin")

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]

		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=int(selectedvalue)).default = True

		await interaction.response.edit_message(view=self.view)


class RollVehicleDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView'):	

		options = []
		for vehicle in vehicles:
			options.append(discord.SelectOption(label=vehicle, value=vehicle))


		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options, placeholder="Choose a vehicle to use for drive...")

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]

		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=selectedvalue).default = True

		info = vehicles[selectedvalue]

		safespeed = info["safespeed"]
		maxspeed = info["maxspeed"]

		speedoptions = []
		speedoptions.append(discord.SelectOption(label="Within the safe speed limit", value=0))
		incr = 0
		diff = 0
		for i in range(safespeed, maxspeed):
			if not incr % 10:
				diff = diff + 1
				speedoptions.append(discord.SelectOption(label="{} mph+ (diff + {})".format(i, diff), value=int(diff)))
			incr = incr + 1

		self.view.speedar.children[0].options = speedoptions

		await interaction.response.edit_message(view=self.view)

class RollSpeedDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView'):	

		options = []
		options.append(discord.SelectOption(label="Within the safe speed limit", value=0))


		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options, placeholder="Choose a speed")

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]

		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=int(selectedvalue)).default = True

		await interaction.response.edit_message(view=self.view)

class RollAuspexTimescaleDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView'):	

		options = []
		for opt in timescales:
			if int(timescales[opt]) == 0:
				options.append(discord.SelectOption(label=opt, value=timescales[opt], default=True))
			else:
				options.append(discord.SelectOption(label=opt, value=timescales[opt]))

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options, placeholder="Choose a speed")

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]

		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=int(selectedvalue)).default = True

		await interaction.response.edit_message(view=self.view)

class RollAuspexIntensityDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView'):	

		options = []
		for opt in intensity:
			if int(intensity[opt]) == 0:
				options.append(discord.SelectOption(label=opt, value=intensity[opt], default=True))
			else:
				options.append(discord.SelectOption(label=opt, value=intensity[opt]))

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options, placeholder="Choose a speed")

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]

		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=int(selectedvalue)).default = True

		await interaction.response.edit_message(view=self.view)


class RollBackgroundDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView', characterdata):

		self.characterbackgrounds = sort_character_backgrounds(characterdata["backgrounds"])

		self.page = 0

		# Add paging, so only 25 options in the list
		# First option is "Previous Page..." Then the list. Then "Next Page"
		# Update the list when something is selected
		# Clan filter is optional

		options = []
		
		# Add "Previous page..." if not on first page
		if self.page > 0:
			options.append(discord.SelectOption(label="< Previous Page...", value=-2))
		
		start_idx = self.page * 23
		end_idx = start_idx + 23
		
		for bg in self.characterbackgrounds[start_idx:end_idx]:
			label="{} {}".format(bg["background"], bg["level"])
			value="{}:{}:{}:{}".format(bg["level"], bg["background"], bg["comment"], bg["sector"])
			if bg["comment"] != "":
				label = label + " ({})".format(bg["comment"])
			if bg["sector"] != "" and bg["sector"] is not None:
				label = label + " {}".format(bg["sector"])

			options.append(discord.SelectOption(label=label, value=value))
		
		# Add "Next page..." if there are more characters
		if end_idx < len(self.characterbackgrounds):
			options.append(discord.SelectOption(label="> Next Page...", value=-1))

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options, placeholder="Choose a background...")

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]

		if isinstance(selectedvalue, int) and int(selectedvalue) == -1:
			# next page
			self.page += 1
			
			options = []
			start_idx = self.page * 23
			end_idx = start_idx + 23
			
			# Add "Previous page..." if not on first page
			if self.page > 0:
				options.append(discord.SelectOption(label="< Previous Page...", value=-2))
			
			for bg in self.characterbackgrounds[start_idx:end_idx]:
				label="{} {}".format(bg["background"], bg["level"])
				value="{}:{}:{}:{}".format(bg["level"], bg["background"], bg["comment"], bg["sector"])
				if bg["comment"] != "":
					label = label + " ({})".format(bg["comment"])
				if bg["sector"] != "" and bg["sector"] is not None:
					label = label + " {}".format(bg["sector"])

				options.append(discord.SelectOption(label=label, value=value))
			
			# Add "Next page..." if there are more characters
			if end_idx < len(self.characterbackgrounds):
				options.append(discord.SelectOption(label="> Next Page...", value=-1))
			
			self.options = options
			await interaction.response.edit_message(view=self.view)
		elif isinstance(selectedvalue, int) and int(selectedvalue) == -2:
			# previous page
			self.page -= 1
			
			options = []
			start_idx = self.page * 23
			end_idx = start_idx + 23
			
			# Add "Previous page..." if not on first page
			if self.page > 0:
				options.append(discord.SelectOption(label="< Previous Page...", value=-2))
			
			for bg in self.characterbackgrounds[start_idx:end_idx]:
				label="{} {}".format(bg["background"], bg["level"])
				value="{}:{}:{}:{}".format(bg["level"], bg["background"], bg["comment"], bg["sector"])
				if bg["comment"] != "":
					label = label + " ({})".format(bg["comment"])
				if bg["sector"] != "" and bg["sector"] is not None:
					label = label + " {}".format(bg["sector"])

				options.append(discord.SelectOption(label=label, value=value))
			
			# Add "Next page..." if there are more characters
			if end_idx < len(self.characterbackgrounds):
				options.append(discord.SelectOption(label="> Next Page...", value=-1))
			
			self.options = options
			await interaction.response.edit_message(view=self.view)
		else:
			for opt in self.options:
				opt.default = False

			discord.utils.get(self.options, value=selectedvalue).default = True

			# Use the interaction object to send a response message containing
			# the user's favourite colour or choice. The self object refers to the
			# Select object, and the values attribute gets a list of the user's
			# selected options. We only want the first one.
			await interaction.response.edit_message(view=self.view)


class RollCharsDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView', characterlist):
		self.characterlist = sort_character_list(characterlist)
		self.page = 0

		# Add paging, so only 25 options in the list
		# First option is "Previous Page..." Then the list. Then "Next Page"
		# Update the list when something is selected
		# Clan filter is optional

		options = []
		
		# Add "Previous page..." if not on first page
		if self.page > 0:
			options.append(discord.SelectOption(label="< Previous Page...", value=-2))
		
		start_idx = self.page * 23
		end_idx = start_idx + 23
		
		for ch in self.characterlist[start_idx:end_idx]:
			options.append(discord.SelectOption(label=ch["characterName"], value=int(ch["characterID"])))
		
		# Add "Next page..." if there are more characters
		if end_idx < len(self.characterlist):
			options.append(discord.SelectOption(label="> Next Page...", value=-1))

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options, placeholder="Choose a character...")

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]

		# Clear any disabled buttons
		for b in self.view.rollchoices1.children:
			b.style = discord.ButtonStyle.secondary
			b.disabled = False
		for c in self.view.rollchoices2.children:
			c.style = discord.ButtonStyle.secondary
			c.disabled = False
		for d in self.view.rollchoices3.children:
			d.style = discord.ButtonStyle.secondary
			d.disabled = False

		if int(selectedvalue) == -1:
			# next page
			self.page += 1
			
			options = []
			start_idx = self.page * 23
			end_idx = start_idx + 23
			
			# Add "Previous page..." if not on first page
			if self.page > 0:
				options.append(discord.SelectOption(label="< Previous Page...", value=-2))
			
			for ch in self.characterlist[start_idx:end_idx]:
				options.append(discord.SelectOption(label=ch["characterName"], value=int(ch["characterID"])))
			
			# Add "Next page..." if there are more characters
			if end_idx < len(self.characterlist):
				options.append(discord.SelectOption(label="> Next Page...", value=-1))
			
			self.options = options
			await interaction.response.edit_message(view=self.view)
		elif int(selectedvalue) == -2:
			# previous page
			self.page -= 1
			
			options = []
			start_idx = self.page * 23
			end_idx = start_idx + 23
			
			# Add "Previous page..." if not on first page
			if self.page > 0:
				options.append(discord.SelectOption(label="< Previous Page...", value=-2))
			
			for ch in self.characterlist[start_idx:end_idx]:
				options.append(discord.SelectOption(label=ch["characterName"], value=int(ch["characterID"])))
			
			# Add "Next page..." if there are more characters
			if end_idx < len(self.characterlist):
				options.append(discord.SelectOption(label="> Next Page...", value=-1))
			
			self.options = options
			await interaction.response.edit_message(view=self.view)
		else:
			topofpage = None
			for opt in self.options:
				opt.default = False
				if opt.value > 0 and topofpage == None:
					topofpage = opt.value

			discord.utils.get(self.options, value=int(selectedvalue)).default = True

			# Use the interaction object to send a response message containing
			# the user's favourite colour or choice. The self object refers to the
			# Select object, and the values attribute gets a list of the user's
			# selected options. We only want the first one.
			await interaction.response.edit_message(view=self.view)
class RollDriveStatDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView'):	

		options = []
		options.append(discord.SelectOption(label="Dexterity", value="dexterity", default=True))
		options.append(discord.SelectOption(label="Wits", value="wits"))

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options, placeholder="(Optional) Choose a stat to use for drive...")

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]

		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=selectedvalue).default = True

		await interaction.response.edit_message(view=self.view)

class RollClanDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView', characterlist):
		self.characterlist = characterlist

		clans = {}
		for ch in characterlist:
			clans[ch["clan"]] = 1	

		options = []
		options.append(discord.SelectOption(label="[All Clans]", value="all"))
		for clan in sorted(clans):
			options.append(discord.SelectOption(label=clan, value=clan))

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options, placeholder="(Optional) Choose a clan...")

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]

		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=selectedvalue).default = True

		# Update the options in the character pulldown based on clan
		filteredlist = []
		if selectedvalue == "all":
			filteredlist = self.characterlist
		else:
			for ch in self.characterlist:
				if ch["clan"] == selectedvalue:
					filteredlist.append(ch)
		
		options = []
		if len(filteredlist) > 25:
			for ch in filteredlist[0:23]:
				options.append(discord.SelectOption(label=ch["characterName"], value=int(ch["characterID"])))
			options.append(discord.SelectOption(label="> Next Page...", value=-1))
		else:
			for ch in filteredlist:
				options.append(discord.SelectOption(label=ch["characterName"], value=int(ch["characterID"])))

		self.view.charChoices.char.options = options

		await interaction.response.edit_message(view=self.view)

class RollWoundDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView'):

		optionlist = wounds
		default = "unhurt:0"

		options = []
		for opt in optionlist:
			if default == optionlist[opt]:
				options.append(discord.SelectOption(label=opt, value=optionlist[opt], default=True))
			else:
				options.append(discord.SelectOption(label=opt, value=optionlist[opt]))

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options)

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]
		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=selectedvalue).default = True
		# Use the interaction object to send a response message containing
		# the user's favourite colour or choice. The self object refers to the
		# Select object, and the values attribute gets a list of the user's
		# selected options. We only want the first one.
		await interaction.response.edit_message(view=self.view)


class RollDmgTypeDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView'):

		optionlist = [
			"Bashing",
			"Lethal",
			"Aggravated"
		]
		options = []
		for i in range(0,3):
			if optionlist[i] == "Lethal":
				options.append(discord.SelectOption(label=optionlist[i], value=optionlist[i], default=True))
			else:
				options.append(discord.SelectOption(label=optionlist[i], value=optionlist[i]))

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options)

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]
		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=selectedvalue).default = True
		# Use the interaction object to send a response message containing
		# the user's favourite colour or choice. The self object refers to the
		# Select object, and the values attribute gets a list of the user's
		# selected options. We only want the first one.
		await interaction.response.edit_message(view=self.view)

class RollFrenzyDiffDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView', default: int, clan: str):

		diffoptions = {
			"Smell of blood when hungry": "bloodsmell:3",
			"Sight of blood when hungry" : "bloodsight:4",
			"Being harassed": "harassed:4",
			"Life-threatening situation": "threat:4",
			"Malicious taunts": "taunts:4",
			"Physical Provocation": "provocation:6",
			"Taste of blood when hungry": "bloodtaste:6",
			"Loved one in danger": "lovedanger:7",
			"Outright public humiliation": "humiliation:8"
		}

		if clan == "Brujah":
			offset = 2
		else:
			offset = 0

		default = "provocation:" + default

		options = []
		for opt in diffoptions:
			second_number_int = int(diffoptions[opt].split(':')[1])  # This converts it to an integer (4)
			val = second_number_int + offset
			if default == diffoptions[opt]:
				options.append(discord.SelectOption(label=opt + " ({})".format(val), value=diffoptions[opt], default=True))
			else:
				options.append(discord.SelectOption(label=opt + " ({})".format(val), value=diffoptions[opt]))
		

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options)

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]
		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=selectedvalue).default = True
				
		# Use the interaction object to send a response message containing
		# the user's favourite colour or choice. The self object refers to the
		# Select object, and the values attribute gets a list of the user's
		# selected options. We only want the first one.
		await interaction.response.edit_message(view=self.view)

class RollRotschreckDiffDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView', default: int):

		diffoptions = {
			"Lighting a cigarette (3)" : "cigarette:3",
			"Sight of a torch (5)" : "torch:5",
			"Bonfire (6)": "bonfire:6",
			"Obscured sunlight (7)": "obscured:7",
			"Being burned (7)": "burned:7",
			"Direct sunlight (8)": "sunlight:8",
			"Trapped in burning building (9)": "trapped:9"
		}

		options = []
		for opt in diffoptions:
			if default == diffoptions[opt]:
				options.append(discord.SelectOption(label=opt, value=diffoptions[opt], default=True))
			else:
				options.append(discord.SelectOption(label=opt, value=diffoptions[opt]))
		

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options)

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]
		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=selectedvalue).default = True
				
		# Use the interaction object to send a response message containing
		# the user's favourite colour or choice. The self object refers to the
		# Select object, and the values attribute gets a list of the user's
		# selected options. We only want the first one.
		await interaction.response.edit_message(view=self.view)


class RollDiffDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView', default: int):

		diffoptions = [
			"Easy (4)",
			"Straightforward (5)",
			"Standard (6)",
			"Challenging (7)",
			"Difficult (8)",
			"Extremely Difficult (9)"
		]
		options = []
		for i in range(4,10):
			if default == i:
				options.append(discord.SelectOption(label=diffoptions[i-4], value=i, default=True))
			else:
				options.append(discord.SelectOption(label=diffoptions[i-4], value=i))
		

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options)

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		selectedvalue = self.values[0]
		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=int(selectedvalue)).default = True
				
		# Use the interaction object to send a response message containing
		# the user's favourite colour or choice. The self object refers to the
		# Select object, and the values attribute gets a list of the user's
		# selected options. We only want the first one.
		await interaction.response.edit_message(view=self.view)

class RollAddCelerityDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView', celerity: int):

		options = []
		options.append(discord.SelectOption(label="0 dots of Celerity added to Dexterity", value=0, default=True))
		for i in range(1,int(celerity)+1):
			options.append(discord.SelectOption(label="{} dots of Celerity added to Dexterity".format(i), value=i))

		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options)

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		# Use the interaction object to send a response message containing
		# the user's favourite colour or choice. The self object refers to the
		# Select object, and the values attribute gets a list of the user's
		# selected options. We only want the first one.
		selectedvalue = self.values[0]
		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=int(selectedvalue)).default = True
		await interaction.response.edit_message(view=self.view)


class RollAddStatBoostDropdown(discord.ui.Select):
	def __init__(self, view: 'RollPage1LayoutView', ability_level: int, ability_name: str, max_ability: int):

		max_4_spend = int(max_ability) + int(2)

		options = []
		for i in range(int(ability_level), int(max_4_spend)):
				if i == ability_level:
					options.append(discord.SelectOption(label="No blood spent".format(i-ability_level, ability_name), value=i, default=True))
				else:
					options.append(discord.SelectOption(label="{} spent for {} {}".format(int(i)-int(ability_level), ability_name, i), value=i))


		# The placeholder is what will be shown when no option is chosen
		# The min and max values indicate we can only pick one of the three options
		# The options parameter defines the dropdown options. We defined this above
		super().__init__(options=options)

	async def callback(self, interaction: discord.Interaction):
		# Use the interaction object to send a response message containing
		# the user's favourite colour or choice. The self object refers to the
		# Select object, and the values attribute gets a list of the user's
		# selected options. We only want the first one.
		selectedvalue = self.values[0]
		for opt in self.options:
			opt.default = False
			
		discord.utils.get(self.options, value=int(selectedvalue)).default = True
		await interaction.response.edit_message(view=self.view)


class RollSubmitButtons(discord.ui.ActionRow):
	def __init__(self, view: 'RollPage1LayoutView', characterdata) -> None:
		self.__view = view
		self.characterdata = characterdata
		super().__init__()

	@discord.ui.button(label="Roll Now", style=discord.ButtonStyle.primary)
	async def rollnow(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:

		rollok = 1


		selection = None
		rolloptions = self.__view.rollchoices1.children
		for ro in rolloptions:
			if ro.style == discord.ButtonStyle.primary:
				selection = ro.label
				break
		if selection == None:
			rolloptions = self.__view.rollchoices2.children
			for ro in rolloptions:
				if ro.style == discord.ButtonStyle.primary:
					selection = ro.label
					break
		if selection == None:
			rolloptions = self.__view.rollchoices3.children
			for ro in rolloptions:
				if ro.style == discord.ButtonStyle.primary:
					selection = ro.label
					break
		
		if self.characterdata is None:
			self.characterdata = get_char_from_pulldown(self.__view)
		
		if self.characterdata is None:
			self.__view.info.content = "ERROR: Select a character to roll for!"
			rollok = 0
		elif selection is None:
			self.__view.info.content = "ERROR: select something to roll!"
			rollok = 0
		else:
			info = load_info(self.__view, self.characterdata)
			
			if selection == "Initiative":
				result = roll_initiative(info=info)
				info["Difficulty"] = 0
				mystr = format_initiative(result, info)

			elif selection == "Willpower":
				result = roll_willpower(info)
				info["Difficulty"] = 9
				mystr = format_willpower(result, info)

			elif selection == "Soak":
				result = roll_pool(info["Fortitude"] + info["Stamina"])
				mystr = format_soak(result, info)
			
			elif selection == "Resist Frenzy":
				result = roll_pool(info["Self Control"])
				mystr = format_frenzy(result, info)

			elif selection == "Feats of Strength":
				result = roll_pool(info["Willpower"],9)
				mystr = format_featofstr(result, info)

			elif selection == "Rotschreck":
				result = roll_pool(info["Courage"])
				mystr = format_rotschreck(result, info)

			elif selection == "Driving":
				# limit pool to 5
				pool = min(5, info["Dexterity"] + info["Celerity"] + info["Driving"])
				result = roll_pool(int(pool))
				mystr = format_drive(result, info)

			elif selection == "Aura Perception":
				if info["Auspex"] < 2:
					mystr = "{} does not have enough Auspex".format(self.characterdata["name"])
				else:
					result = roll_pool(info["Perception"] + info["Empathy"],8)
					mystr = format_auraperception(result, info)

			elif selection == "Spirits Touch":
				if info["Auspex"] < 3:
					mystr = "{} does not have enough Auspex".format(self.characterdata["name"])
				else:
					result = roll_pool(info["Perception"] + info["Empathy"],6)
					mystr = format_spiritstouch(result, info)

			elif selection == "Backgrounds":

				pool = info["Background"]

				if pool > 0:
					result = roll_pool(pool,6)
					mystr = "{} has a {} on a Resources roll.".format(self.characterdata["name"],result["description"])
				else:
					result = {}
					mystr = "{} does not have the Resources background. Click customise to choose a different background".format(self.characterdata["name"])
					rollok = 0

				mystr = format_roll(info["character_name"],
					"Background Check",
					mystr,
					info["detail"],
					"{} {}".format(info["Background Info"], info["Background"]),
					result["difficulty"],
					result["rolls"],
					""
					)
			
			elif selection == "Degeneration":
				statlevel = info[info["Path Attribute"]]
				result = roll_pool(statlevel, 8)
				mystr = format_degeneration(result, info)
			
			else:
				mystr = "{} is not supported yet".format(selection)

			self.__view.clear_items()
		
			if self.__view.display_private.accessory.label == "On":
				self.__view.info.content = mystr
				await interaction.user.send(mystr)
			else:
				channel = interaction.channel
				await channel.send(mystr)

			mystr = "{} has rolled some dice.".format(self.characterdata["name"])
			self.result = discord.ui.TextDisplay(mystr)
			showresult = discord.ui.Container(self.result)
			self.__view.add_item(showresult)

		if rollok:
			await interaction.response.edit_message(view=self.__view, delete_after=10)
		else:
			await interaction.response.edit_message(view=self.__view)

	@discord.ui.button(label="Customise...", style=discord.ButtonStyle.primary)
	async def customise(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		selection = None
		rolloptions = self.__view.rollchoices1.children
		for ro in rolloptions:
			if ro.style == discord.ButtonStyle.primary:
				selection = ro.label
				break
		if selection == None:
			rolloptions = self.__view.rollchoices2.children
			for ro in rolloptions:
				if ro.style == discord.ButtonStyle.primary:
					selection = ro.label
					break
		if selection == None:
			rolloptions = self.__view.rollchoices3.children
			for ro in rolloptions:
				if ro.style == discord.ButtonStyle.primary:
					selection = ro.label
					break


		if self.characterdata is None:
			self.characterdata = get_char_from_pulldown(self.__view)
		
		if self.characterdata is None:
			self.__view.info.content = "ERROR: Select a character to roll for!"
		elif selection is None:
			self.__view.info.content = "ERROR: select something to roll!"
		else:
			max_rating = get_max_level(self.characterdata)
			info = load_info(self.__view, self.characterdata)

			# -- Create all the inputs we might need --
			# How much Celerity is added to Dex
			self.__view.celerityar = discord.ui.ActionRow(id=forminputIDs["CelerityPulldownActionRow"])
			self.__view.celerityar.add_item(RollAddCelerityDropdown(self.__view, celerity=info["Celerity"]))
			self.__view.textcel = discord.ui.TextDisplay("Choose how much of your Celerity is being used for Initiative (Total - number of extra rounds)")
			# Spending blood on Dexterity
			self.__view.dexterityar = discord.ui.ActionRow(id=forminputIDs["DexterityPulldownActionRow"])
			self.__view.dexterityar.add_item(RollAddStatBoostDropdown(self.__view, info["Dexterity"], "Dexterity", int(max_rating)))
			self.__view.textdex = discord.ui.TextDisplay("Choose how much blood you have spent to boost Dexterity")
			# Spend blood on Stamina
			self.__view.staminaar = discord.ui.ActionRow(id=forminputIDs["StaminaPulldownActionRow"])
			self.__view.staminaar.add_item(RollAddStatBoostDropdown(self.__view, info["Stamina"], "Stamina", int(max_rating)))
			self.__view.textstam = discord.ui.TextDisplay("Choose how much blood you have spent to boost Stamina")
			# Spend blood on Strength
			self.__view.strengthar = discord.ui.ActionRow(id=forminputIDs["StrengthPulldownActionRow"])
			self.__view.strengthar.add_item(RollAddStatBoostDropdown(self.__view, info["Strength"], "Strength", int(max_rating)))
			self.__view.textstr = discord.ui.TextDisplay("Select any boosts to Strength")
			# Select Damage type, e.g. Lethal
			self.__view.damagear = discord.ui.ActionRow(id=forminputIDs["DamageTypePulldownActionRow"])
			self.__view.damagear.add_item(RollDmgTypeDropdown(self.__view))
			self.__view.textdmg = discord.ui.TextDisplay("Select the damage type")
			# Spend willpower
			self.__view.wpsection = discord.ui.Section("Spend Willpower", accessory=RollCheckButton("Off"), id=forminputIDs["WillpowerButton"])
			# Frenzy Difficulty
			self.__view.frenzyar = discord.ui.ActionRow(id=forminputIDs["DifficultyPulldownActionRow"])
			self.__view.frenzyar.add_item(RollFrenzyDiffDropdown(self.__view, default="provocation:6", clan=info["Clan"]))
			self.__view.textfrenzy = discord.ui.TextDisplay("Select the difficulty")
			# Wound penalties
			self.__view.woundsar = discord.ui.ActionRow(id=forminputIDs["WoundPulldownActionRow"])
			self.__view.woundsar.add_item(RollWoundDropdown(self.__view))
			self.__view.woundstr = discord.ui.TextDisplay("Select any wound penalties")
			# Rotschreck difficulty
			self.__view.rotsar = discord.ui.ActionRow(id=forminputIDs["DifficultyPulldownActionRow"])
			self.__view.rotsar.add_item(RollRotschreckDiffDropdown(self.__view, default="bonfire:6"))
			self.__view.textrots = discord.ui.TextDisplay("Select the difficulty")
			# Has a speciality
			self.__view.speciality = discord.ui.Section("Have a relevant speciality", accessory=RollCheckButton("Off"), id=forminputIDs["SpecialityButton"])
			# Choose vehicle
			self.__view.vehiclear = discord.ui.ActionRow(id=forminputIDs["VehiclePulldownActionRow"])
			self.__view.vehiclear.add_item(RollVehicleDropdown(self.__view))
			self.__view.vehicletext = discord.ui.TextDisplay("Select the vehicle to drive")
			# Choose Dex or Wits
			self.__view.drivestattext = discord.ui.TextDisplay("Select the attribute to use")
			self.__view.drivestatar = discord.ui.ActionRow(id=forminputIDs["DriveStatPulldownActionRow"])
			self.__view.drivestatar.add_item(RollDriveStatDropdown(self.__view))
			# +1 diff rain
			self.__view.weather = discord.ui.Section("+1 difficulty for bad weather", accessory=RollCheckButton("Off"), id=forminputIDs["WeatherButton"])
			# +1 diff heavy traffic
			self.__view.traffic = discord.ui.Section("+1 difficulty for heavy traffic", accessory=RollCheckButton("Off"), id=forminputIDs["TrafficButton"])
			# +1 diff pursuit
			self.__view.pursuit = discord.ui.Section("+1 difficulty for pursuit", accessory=RollCheckButton("Off"), id=forminputIDs["PursuitButton"])
			# +1 diff for every 10 mph over safe speed
			self.__view.speedtext = discord.ui.TextDisplay("Select the speed")
			self.__view.speedar = discord.ui.ActionRow(id=forminputIDs["SpeedPulldownActionRow"])
			self.__view.speedar.add_item(RollSpeedDropdown(self.__view))
			# Duration
			self.__view.difftimear = discord.ui.ActionRow(id=forminputIDs["TimescalePulldownActionRow"])
			self.__view.difftimear.add_item(RollAuspexTimescaleDropdown(self.__view))
			self.__view.difftimestr = discord.ui.TextDisplay("Select how long ago the impression was made")
			# Intensity of Impression
			self.__view.diffintenar = discord.ui.ActionRow(id=forminputIDs["IntensityPulldownActionRow"])
			self.__view.diffintenar.add_item(RollAuspexIntensityDropdown(self.__view))
			self.__view.diffintenstr = discord.ui.TextDisplay("Select the strength of impression")
			# list of backgrounds - name, spec, sector, level
			self.__view.bgar = discord.ui.ActionRow(id=forminputIDs["BackgroundPulldownActionRow"])
			self.__view.bgar.add_item(RollBackgroundDropdown(self.__view, self.characterdata))
			self.__view.bgtext = discord.ui.TextDisplay("Select the background")
			# Hierarchy of Sins
			self.__view.sinsar = discord.ui.ActionRow(id=forminputIDs["SinsPulldownActionRow"])
			self.__view.sinsar.add_item(RollSinsDropdown(self.__view, info["Path of Enlightenment Info"]))
			self.__view.textsins = discord.ui.TextDisplay("I have committed...")

			inputs = {
				"celerity": 0,
				"dexterity": 0,
				"stamina": 0,
				"willpower": 0,
				"difficulty": 0,
				"damage_type": 0,
				"frenzy": 0,
				"wounds": 0,
				"strength": 0,
				"rotschreck": 0,
				"speciality": 0,
				"vehicle": 0,
				"drivestat": 0,
				"weather": 0,
				"traffic": 0,
				"pursuit": 0,
				"speed": 0,
				"duration": 0,
				"intensity": 0,
				"backgrounds": 0
			}

			if selection == "Initiative":
				self.__view.clear_items()
				self.__view.texthelp = discord.ui.TextDisplay("Dexterity + Wits + [Celerity] + 1D10")

				if info["Celerity"] > 0:
					inputs["celerity"] = 1

				inputs["dexterity"] = 1

			elif selection == "Soak":
				self.__view.clear_items()
				self.__view.texthelp = discord.ui.TextDisplay("Stamina and Fortitude are used to soak damage")

				inputs["stamina"] = 1
				inputs["damage_type"] = 1
				inputs["willpower"] = 1

			elif selection == "Willpower":
				self.__view.clear_items()
				self.__view.texthelp = discord.ui.TextDisplay("Roll Willpower")

				inputs["difficulty"] = 9
	
			elif selection == "Resist Frenzy":
				self.__view.clear_items()
				self.__view.texthelp = discord.ui.TextDisplay("5 successes in total are required to resist a frenzy, but these can be accumulated.")

				# Spend Willpower (except if you are Brujah)
				if info["Clan"] != "Brujah":
					inputs["willpower"] = 1

				inputs["frenzy"] = 1				

			elif selection == "Feats of Strength":
				self.__view.clear_items()
				self.__view.texthelp = discord.ui.TextDisplay("Strength + Potence - Wound penalties + Willpower roll, diff 9")				

				inputs["strength"] = 1				
				inputs["wounds"] = 1				

			elif selection == "Rotschreck":
				self.__view.clear_items()
				self.__view.texthelp = discord.ui.TextDisplay("5 successes in total are required to avoid Rotschreck, but these can be accumulated.")

				inputs["willpower"] = 1
				inputs["rotschreck"] = 1

			elif selection == "Driving":
				self.__view.clear_items()
				self.__view.texthelp = discord.ui.TextDisplay("Select your options to customise your driving roll.")

				inputs["willpower"] = 1
				inputs["vehicle"] = 1
				inputs["drivestat"] = 1

				inputs["dexterity"] = 1
				if info["Celerity"] > 0:
					inputs["celerity"] = 1
				inputs["wounds"] = 1
				inputs["speciality"] = 1

				inputs["difficulty"] = 6
				inputs["speed"] = 1
				inputs["weather"] = 1
				inputs["traffic"] = 1
				inputs["pursuit"] = 1


			elif selection == "Aura Perception":
				self.__view.clear_items()
				self.__view.texthelp = discord.ui.TextDisplay("Select options to customise the roll - Perception + Empathy, diff 8.")

				inputs["willpower"] = 1
				inputs["speciality"] = 1
				inputs["wounds"] = 1

			elif selection == "Spirits Touch":
				self.__view.clear_items()
				self.__view.texthelp = discord.ui.TextDisplay("Select options to customise the roll - Perception + Empathy.")

				inputs["willpower"] = 1
				inputs["speciality"] = 1
				inputs["wounds"] = 1
				inputs["duration"] = 1
				inputs["intensity"] = 1
			
			elif selection == "Backgrounds":
				self.__view.clear_items()
				self.__view.texthelp = discord.ui.TextDisplay("Select options to customise the roll.")

				inputs["backgrounds"] = 1
				inputs["wounds"] = 1
				inputs["willpower"] = 1
				inputs["speciality"] = 1
				inputs["difficulty"] = 6

			elif selection == "Degeneration":
				self.__view.clear_items()
				self.__view.texthelp = discord.ui.TextDisplay("Select options to customise the roll.")
				inputs["sins"] = 1
			else:
				self.__view.texthelp = discord.ui.TextDisplay("{} is not supported yet".format(selection))

			# Stats
			self.__view.container1 = discord.ui.Container()
			if inputs["celerity"]:
				self.__view.container1.add_item(self.__view.textcel)
				self.__view.container1.add_item(self.__view.celerityar)
			if inputs["dexterity"]:
				self.__view.container1.add_item(self.__view.textdex)
				self.__view.container1.add_item(self.__view.dexterityar)
			if inputs["stamina"]:
				self.__view.container1.add_item(self.__view.textstam)
				self.__view.container1.add_item(self.__view.staminaar)
			if inputs["strength"]:
				self.__view.container1.add_item(self.__view.textstr)
				self.__view.container1.add_item(self.__view.strengthar)
			# Misc pull-downs
			if inputs["drivestat"]:
				self.__view.container1.add_item(self.__view.drivestattext)
				self.__view.container1.add_item(self.__view.drivestatar)
			if inputs["vehicle"]:
				#self.__view.container1.add_item(self.__view.vehicletext)
				self.__view.container1.add_item(self.__view.vehiclear)
			if inputs["speed"]:
				#self.__view.container1.add_item(self.__view.speedtext)
				self.__view.container1.add_item(self.__view.speedar)
			if inputs["backgrounds"]:
				self.__view.container1.add_item(self.__view.bgtext)
				self.__view.container1.add_item(self.__view.bgar)
			if inputs["difficulty"]:
			# Select Difficulty
				self.__view.diffar = discord.ui.ActionRow(id=forminputIDs["DifficultyPulldownActionRow"])
				self.__view.diffar.add_item(RollDiffDropdown(self.__view, default=inputs["difficulty"]))
				self.__view.textdiff = discord.ui.TextDisplay("Select the difficulty")
				self.__view.container1.add_item(self.__view.textdiff)
				self.__view.container1.add_item(self.__view.diffar)
			if inputs["damage_type"]:
				self.__view.container1.add_item(self.__view.textdmg)
				self.__view.container1.add_item(self.__view.damagear)
			if inputs["frenzy"]:
				self.__view.container1.add_item(self.__view.textfrenzy)
				self.__view.container1.add_item(self.__view.frenzyar)
			if inputs["rotschreck"]:
				self.__view.container1.add_item(self.__view.textrots)
				self.__view.container1.add_item(self.__view.rotsar)
			if inputs["wounds"]:
				self.__view.container1.add_item(self.__view.woundstr)
				self.__view.container1.add_item(self.__view.woundsar)
			if inputs["duration"]:
				self.__view.container1.add_item(self.__view.difftimestr)
				self.__view.container1.add_item(self.__view.difftimear)
			if inputs["intensity"]:
				self.__view.container1.add_item(self.__view.diffintenstr)
				self.__view.container1.add_item(self.__view.diffintenar)
			if inputs["sins"]:
				self.__view.container1.add_item(self.__view.textsins)
				self.__view.container1.add_item(self.__view.sinsar)

			if len(self.__view.container1.children) > 0:
				self.__view.add_item(self.__view.container1)

			# Check boxes
			self.__view.container2 = discord.ui.Container()
			if inputs["willpower"]:
				self.__view.container2.add_item(self.__view.wpsection)
			if inputs["speciality"]:
				self.__view.container2.add_item(self.__view.speciality)
			if inputs["weather"]:
				self.__view.container2.add_item(self.__view.weather)
			if inputs["traffic"]:
				self.__view.container2.add_item(self.__view.traffic)
			if inputs["pursuit"]:
				self.__view.container2.add_item(self.__view.pursuit)

			if len(self.__view.container2.children) > 0:
				self.__view.add_item(self.__view.container2)


			self.__view.rollselectaction = discord.ui.ActionRow()
			self.__view.rollselectaction.add_item(RollSelectionButton("Roll "+ selection, characterdata=self.characterdata))
			self.__view.rollselectcontainer = discord.ui.Container(self.__view.texthelp, self.__view.rollselectaction)
			self.__view.add_item(self.__view.rollselectcontainer)

		await interaction.response.edit_message(view=self.__view)

class RollClanChoices(discord.ui.ActionRow):
	def __init__(self, view: 'RollPage1LayoutView', characterlist) -> None:
		self.__view = view
		self.characterlist = characterlist
		super().__init__()

		self.clan = RollClanDropdown(self.__view, characterlist=self.characterlist)
		self.add_item(self.clan)		

class RollCharChoices(discord.ui.ActionRow):
	def __init__(self, view: 'RollPage1LayoutView', characterlist) -> None:
		self.__view = view
		self.characterlist = characterlist
		super().__init__()

		self.char = RollCharsDropdown(self.__view, characterlist=self.characterlist)
		self.add_item(self.char)	



class RollToggleButtonsRow1(discord.ui.ActionRow):
	def __init__(self, view: 'RollPage1LayoutView') -> None:
		self.__view = view
		super().__init__()

	@discord.ui.button(label="(To Do) Attribute + Ability", style=discord.ButtonStyle.secondary)
	async def select_attabil(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices2.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices3.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		self.__view.info.content = "Customise to select options"
		await interaction.response.edit_message(view=self.__view)
	
	@discord.ui.button(label="Initiative", style=discord.ButtonStyle.secondary)
	async def select_init(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices2.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices3.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		self.__view.info.content = "D10 + Dex + Wits [+ Celerity]. Customise if you are using any Celerity for extra actions."
		await interaction.response.edit_message(view=self.__view)

	@discord.ui.button(label="Soak", style=discord.ButtonStyle.secondary)
	async def select_soak(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices2.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices3.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		self.__view.info.content = "Soak lethal damage with Stamina + Fortitude. Customise for other damage types and modifiers."
		await interaction.response.edit_message(view=self.__view)

	@discord.ui.button(label="Willpower", style=discord.ButtonStyle.secondary)
	async def select_wp(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices2.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices3.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary
		self.__view.info.content = "Diff 9. Customise to edit difficulty."
		await interaction.response.edit_message(view=self.__view)

	@discord.ui.button(label="Resist Frenzy", style=discord.ButtonStyle.secondary)
	async def select_frenzy(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices2.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices3.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		if self.__view.characterdata is None:
			self.__view.characterdata = get_char_from_pulldown(self.__view)
		selfcontrol = get_attribute_level(self.__view.characterdata, "Self Control")
		if int(selfcontrol) == 0:
			button.disabled = True
			button.style = discord.ButtonStyle.danger
			self.__view.info.content = "Choose another option - character does not have Self Control."
		else:
			self.__view.info.content = "Resist frenzy from physical provocation (diff 6) with Self-Control. Customise to modify difficulty or spend Willpower."
		await interaction.response.edit_message(view=self.__view)

class RollToggleButtonsRow2(discord.ui.ActionRow):
	def __init__(self, view: 'RollPage1LayoutView') -> None:
		self.__view = view
		super().__init__()

	@discord.ui.button(label="Feats of Strength", style=discord.ButtonStyle.secondary)
	async def select_featofstr(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices1.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices3.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		self.__view.info.content = "Strength + Potence + Willpower roll. see table in sourcebook for the result"
		await interaction.response.edit_message(view=self.__view)
	
	@discord.ui.button(label="Rotschreck", style=discord.ButtonStyle.secondary)
	async def select_rotschreck(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices1.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices3.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		self.__view.info.content = "Resist Rotschreck against a bonfire-sized fire. Customise to adjust difficulty and spend Willpower"
		await interaction.response.edit_message(view=self.__view)

	@discord.ui.button(label="Driving", style=discord.ButtonStyle.secondary)
	async def select_driving(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices1.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices3.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		self.__view.info.content = "Drive a car using your Dexterity in normal road conditions, within the speed limit. Customise to choose a different attribute, vehicle or the driving conditions"
		await interaction.response.edit_message(view=self.__view)

	@discord.ui.button(label="Aura Perception", style=discord.ButtonStyle.secondary)
	async def select_aura(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices1.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices3.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		if self.__view.characterdata is None:
			self.__view.characterdata = get_char_from_pulldown(self.__view)

		auspex = get_discipline_level(self.__view.characterdata, "Auspex")
		if int(auspex) < 2:
			button.disabled = True
			button.style = discord.ButtonStyle.danger
			self.__view.info.content = "Choose another option - character does not have enough Auspex."
		else:
			self.__view.info.content = "Perception + Empathy, diff 8"

		await interaction.response.edit_message(view=self.__view)

	@discord.ui.button(label="Spirits Touch", style=discord.ButtonStyle.secondary)
	async def select_spiritstouch(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices1.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices3.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		if self.__view.characterdata is None:
			self.__view.characterdata = get_char_from_pulldown(self.__view)

		auspex = get_discipline_level(self.__view.characterdata, "Auspex")
		if int(auspex) < 3:
			button.disabled = True
			button.style = discord.ButtonStyle.danger
			self.__view.info.content = "Choose another option - character does not have enough Auspex."
		else:
			self.__view.info.content = "Perception + Empathy, diff 6. Customise to choose difficulty and other options."

		await interaction.response.edit_message(view=self.__view)

class RollToggleButtonsRow3(discord.ui.ActionRow):
	def __init__(self, view: 'RollPage1LayoutView') -> None:
		self.__view = view
		super().__init__()

	@discord.ui.button(label="Backgrounds", style=discord.ButtonStyle.secondary)
	async def select_backgrounds(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices1.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices2.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		self.__view.info.content = "Defaults to the Resources background. Difficulty 6."
		await interaction.response.edit_message(view=self.__view)

	@discord.ui.button(label="Degeneration", style=discord.ButtonStyle.secondary)
	async def select_degeneration(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices1.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices2.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		self.__view.info.content = "Concience/Conviction roll, diff 8, for a 40+ level sin."
		await interaction.response.edit_message(view=self.__view)

	@discord.ui.button(label="Magic", style=discord.ButtonStyle.secondary)
	async def select_magic(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
		for b in self.children:
			b.style = discord.ButtonStyle.secondary
		for c in self.__view.rollchoices1.children:
			c.style = discord.ButtonStyle.secondary
		for d in self.__view.rollchoices2.children:
			d.style = discord.ButtonStyle.secondary
		button.style = discord.ButtonStyle.primary

		self.__view.info.content = "Roll your magic."
		await interaction.response.edit_message(view=self.__view)


class RollCheckButton(discord.ui.Button):
	def __init__(self, default: str):
		self.default = default
		if default == "On":
			self.defaultstyle = discord.ButtonStyle.primary
		else:
			self.defaultstyle = discord.ButtonStyle.secondary

		super().__init__(style=self.defaultstyle, label=self.default)
		self.label = default

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view
		if self.label == "On":
			self.label = "Off"
			self.style = discord.ButtonStyle.secondary
		elif self.label == "Off":
			self.label = "On"
			self.style = discord.ButtonStyle.primary

		await interaction.response.edit_message(view=view)

class RollSelectionButton(discord.ui.Button):
	def __init__(self, selection: str, characterdata):
		self.selection = selection
		self.characterdata = characterdata
		super().__init__(style=discord.ButtonStyle.primary, label=selection)

	async def callback(self, interaction: discord.Interaction):
		assert self.view is not None
		view: RollPage1LayoutView = self.view

		rollok = 1
		info = load_info(view, self.characterdata)
		print(info)

		view.info.content = "Rolling " + self.selection

		if self.label == "Roll Initiative":

			result = roll_initiative(info)
			info["Difficulty"] = 0
			str = format_initiative(result, info)
		
		elif self.label == "Roll Soak":
			if info["damage_type"] == "Aggravated":
				if info["Fortitude"] == 0:
					result = roll_pool(int(info["Fortitude"]), 6, False)
				else:
					result = roll_pool(int(info["Fortitude"]), 6, False,info["Willpower OnOff"])
			else:
				result = roll_pool(info["Fortitude"] + info["Stamina"], info["Difficulty"], False,info["Willpower OnOff"])

			str = format_soak(result, info)

		elif self.label == "Roll Willpower":
			result = roll_willpower(info)
			str = format_willpower(result, info)

		elif self.label == "Roll Resist Frenzy":
			result = roll_pool(pool=info["Self Control"],diff=info["Difficulty"], willpower=info["Willpower OnOff"])
			str = format_frenzy(result, info)

		elif self.label == "Roll Feats of Strength":
			pool = max(0, info["Willpower"] - info["Wound Penalty"])
			result = roll_pool(int(pool),9)
			str = format_featofstr(result, info)

		elif self.label == "Roll Rotschreck":
			result = roll_pool(pool=info["Courage"],diff=info["Difficulty"], willpower=info["Willpower OnOff"])
			str = format_rotschreck(result, info)

		elif self.label == "Roll Driving":

			stat = info["Drive Ability"]
			if stat == "dexterity":
				statval = info["Effective Dexterity"]
				celerity = info["Effective Celerity"]
			else:
				statval = info["Wits"]
				celerity = 0
			
			vehicle = info["Vehicle"]

			if vehicle is None:
				self.view.texthelp.content = "ERROR: select a vehicle"
				rollok = 0
			else:
				diff = info["Difficulty"]
				speeddiff = info["Speed Diff Modifier"]

				if speeddiff is None:
					self.view.texthelp.content = "ERROR: select a speed"
					rollok = 0
				else:
					weather = info["Weather OnOff"]
					traffic = info["Traffic OnOff"]
					pursuit = info["Pursuit OnOff"]

					diff = diff + speeddiff
					if weather == "On":
						diff = diff + 1
					if traffic == "On":
						diff = diff + 1
					if pursuit == "On":
						diff = diff + 1

					diff = min(9, diff)
					info["Difficulty"] = diff

					maneuver = vehicles[vehicle]["maneuver"]
					info["Maneuver"] = maneuver

					spec = False
					if info["Speciality OnOff"] == "On":
						spec = True

					pool = max(0, int(statval) + int(celerity) + info["Driving"] + info["Wound Penalty"])
					pool = min(int(maneuver), pool)
					result = roll_pool(int(pool),diff=diff, speciality=spec, willpower=info["Willpower OnOff"])

					str = format_drive(result, info)

		elif self.label == "Roll Aura Perception":
			if info["Speciality OnOff"] == "On":
				spec = True
			else:
				spec = False
			perception = info["Perception"]
			empathy = info["Empathy"]
			auspex = info["Auspex"]

			if int(auspex) < 2:
				str = "{} does not have enough Auspex".format(self.characterdata["name"])
			else:
				pool = max(0, int(perception) + int(empathy) + info["Wound Penalty"])
				result = roll_pool(int(pool),8, speciality=spec, willpower=info["Willpower OnOff"])
				str = format_auraperception(result, info)

		elif self.label == "Roll Spirits Touch":
			if info["Speciality OnOff"] == "On":
				spec = True
			else:
				spec = False
			perception = info["Perception"]
			empathy = info["Empathy"]
			auspex = info["Auspex"]

			diff = 6 + info["Timescale"] + info["Intensity"]

			if int(auspex) < 3:
				str = "{} does not have enough Auspex".format(self.characterdata["name"])
			else:
				pool = max(0, int(perception) + int(empathy) + info["Wound Penalty"])
				result = roll_pool(int(pool),diff, speciality=spec, willpower=info["Willpower OnOff"])
				str = format_spiritstouch(result, info)

		elif self.label == "Roll Backgrounds":
			if info["Speciality OnOff"] == "On":
				spec = True
			else:
				spec = False

			pool = max(0, info["Background"] + info["Wound Penalty"])
			result = roll_pool(pool, info["Difficulty"], spec, info["Willpower OnOff"])

			breakdown = ""
			if int(result["willpower"]) == 1:
				breakdown += "One success was gained from Willpower. "
			if spec:
				breakdown += "{} had a relevant speciality. ".format(self.characterdata["name"])
			if info["Wound Penalty"] > 0:
				breakdown += "{} is {}".format(self.characterdata["name"], info["Wound Penalty Info"])

			str = format_roll(info["character_name"],
				   "Background Check",
				   "{} has a {} on a roll for {}.".format(self.characterdata["name"],result["description"], info["Background Info"]),
				   info["detail"],
				   "Background {}".format(info["Background"]),
				   result["difficulty"],
				   result["rolls"],
				   breakdown
				   )

		elif self.label == "Roll Degeneration":
			statlevel = info[info["Path Attribute"]]
			result = roll_pool(statlevel, 8)
			str = format_degeneration(result, info)			

		else:
			str = self.label + " is unsupported"

		if rollok:
			if view.display_private.accessory.label == "On":
				view.info.content = str
				await interaction.user.send(str)
			else:
				channel = interaction.channel
				await channel.send(str)

			view.clear_items()

			str = "{} has rolled some dice.".format(self.characterdata["name"])
			self.result = discord.ui.TextDisplay(str)
			showresult = discord.ui.Container(self.result)
			view.add_item(showresult)

		await interaction.response.edit_message(view=view)


# See embed_like.py
class RollPage1LayoutView(discord.ui.LayoutView):
	def __init__(self, server: str, nameid : str, characterdata = None, isST = False):
		super().__init__()
		self.characterdata = characterdata
		self.isST = isST
		self.server = server
		self.nameid = nameid

		if characterdata is not None and "blood_per_round" in characterdata:
			bloodperround = characterdata["blood_per_round"]
		else:
			bloodperround = 0

		# Form pieces
		# - Wound modifiers - pulldown
		# - Speciality applied? - yes/no
		# - Spend Blood. How much can they spend in a round? - 
		# - Difficulties - pulldown
		# - Description = textbox (can't do this - Modal only)
		# self.woundmod = discord.ui.Section("Wound Modifier", accessory=discord.ui.Select(
		# 	options = [
		# 		discord.SelectOption(label="Bruised (0)", value="0", default=True),
		# 		discord.SelectOption(label="Hurt (-1)", value="-1"),
		# 		discord.SelectOption(label="Injured (-1)", value="-1"),
		# 		discord.SelectOption(label="Wounded (-2)", value="-2"),
		# 		discord.SelectOption(label="Mauled (-2)", value="-2"),
		# 		discord.SelectOption(label="Crippled (-5)", value="-5")
		# 	]
		# ))
		# self.usespeciality = discord.ui.Section("Use Speciality:", accessory=RollCheckButton())

		self.info = discord.ui.TextDisplay("You can choose to customise the roll, or roll with the defaults.")
		if self.isST:
			self.hello = discord.ui.TextDisplay("Hello Storyteller. Choose the active character to roll for")
			# By default, select the character returned in characterdata
			activecharacters = get_active_characters(server, nameid)
			activecharacterslist = sort_character_list(activecharacters["result"])


			if "code" in activecharacters:
				self.info = discord.ui.TextDisplay("Character list failed: {}.".format(activecharacters["message"]))
			else:
				self.clanChoices = RollClanChoices(self, activecharacterslist)
				self.charChoices = RollCharChoices(self, activecharacterslist)
				characterchoices = discord.ui.Container(self.clanChoices, self.charChoices)
				self.add_item(characterchoices)
		else:
			self.hello = discord.ui.TextDisplay("Hello {}.".format(characterdata["name"]))

		self.display_detail = discord.ui.Section("Show roll detail:", accessory=RollCheckButton(default="On"))
		self.display_private = discord.ui.Section("Private Roll:", accessory=RollCheckButton(default="Off"))
		if not self.isST:
			display = discord.ui.Container(self.hello, self.display_detail, self.display_private)
		else:
			display = discord.ui.Container(self.hello, self.display_detail)
		self.add_item(display)

		self.rollchoices1 = RollToggleButtonsRow1(self)
		self.rollchoices2 = RollToggleButtonsRow2(self)
		self.rollchoices3 = RollToggleButtonsRow3(self)

		rolls = discord.ui.Container(self.rollchoices1, self.rollchoices2, self.rollchoices3, self.info)
		self.add_item(rolls)

		self.rollsubmit = RollSubmitButtons(self, characterdata)
		submit = discord.ui.Container(self.rollsubmit)
		self.add_item(submit)



	async def on_error(self, interaction: discord.Interaction, error: Exception):
		await interaction.response.send_message("An error occurred while processing the roll page.")
		traceback.print_exception(type(error), error, error.__traceback__)
		print(f"Error in RollPage1View: {error}")


class DiceRoller(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None

	async def cog_app_command_error(self, ctx, error):
		if isinstance(error, discord.app_commands.CheckFailure):
			await ctx.response.send_message("I'm sorry Master. {}".format(error))
		else:
			await ctx.response.send_message("I'm sorry Master, the command failed.")
			traceback.print_exception(type(error), error, error.__traceback__)
			print(error)


	@check_restapi_active()
	@app_commands.command(name='rollme', description='Roll a character attribute')
	async def rollme(self, ctx):
		# check that the user is linked and has a character

		nameid = ctx.user.id
		server = ctx.guild.name
		try:
			isST = is_storyteller(nameid, server)
		except Exception as e:
			print(e)
			
		charinfo = get_my_character(nameid, server)
		if not isST and "code" in charinfo:
			await ctx.response.send_message(charinfo["message"])
		else:
			await ctx.response.send_message(view=RollPage1LayoutView(server, nameid, charinfo["result"], isST=isST), ephemeral=True)

	
	async def rollmy_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.response.send_message("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))
		else:
			await ctx.response.send_message("I'm sorry Master, the command failed.")
			traceback.print_exception(type(error), error, error.__traceback__)
			print(error)


	@app_commands.command(name='rollpool', description='Dice roller')
	@app_commands.describe(
		dicepool="Number of D10s to roll",
		note="Optional comment"
	)
	async def rollpool(self, ctx, dicepool: app_commands.Range[int, 1, 40], note:str = ""):
		author = ctx.user.display_name
		if dicepool > 40:
			await ctx.response.send_message('I\'m sorry, Master {}, I only have 40 dice in my dice bag.'.format(author))
		elif dicepool <= 0:
			await ctx.response.send_message('You are having a jest with me, Master {}, I cannot roll that number of dice.'.format(author))
		else:
			try:
				result = roll_pool(dicepool)
				if note == "":
					await ctx.response.send_message("Master {}, Your roll for is a {}. You rolled: ".format(author, result["description"]) + formatdice(result["rolls"]))
				else:
					await ctx.response.send_message("Master {}, Your roll for '{}' is a {}. You rolled: ".format(author, note, result["description"]) + formatdice(result["rolls"]))
			except Exception as e:
				print('Renfield is confused')
				print(e)


	# @commands.error
	# async def roll_error(ctx, error):
		# if isinstance(error, commands.MissingRequiredArgument):
			# await ctx.send("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))

	async def cog_command_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.response.send_message("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))

async def setup(bot):
	await bot.add_cog(DiceRoller(bot))

def dice(dicepool: int):
	rolled = []
	for x in range(dicepool):
		rolled.append(random.randrange(1,11))
	
	return rolled

def formatdice(rolls):
	sortrolls = sorted(rolls)
	str = ""
	i = 0
	for roll in sortrolls:
		if (i % 3) == 0:
			str = str + "  "
		i = i + 1
		if roll == 1 or roll == 10:
			str = str + "**{}** ".format(roll)
		elif roll >= 6:
			str = str + "*{}* ".format(roll)
		else:
			str = str + "{} ".format(roll)
	return str

def format_initiative(result, info):
	character_name = info["character_name"]

	str = "Initiative roll is: {}".format(result["total"])

	if info["Effective Celerity"] > 0:
		pool = "{} Dexterity + {} Wits + {} Celerity + 1D10".format(info["Effective Dexterity"], info["Wits"], info["Effective Celerity"])
	else:
		pool = "{} Dexterity + {} Wits + 1D10".format(info["Effective Dexterity"], info["Wits"])

	breakdown = ""
	if info["blood"]["Dexterity"] > 0:
		breakdown += "{} blood spent on Dexterity. ".format(info["blood"]["Dexterity"])
	if info["Celerity"] > 0 and info["Effective Celerity"] != info["Celerity"]:
		breakdown += "{} of {} Celerity dots used. ".format(info["Effective Celerity"], info["Celerity"])

	str = format_roll(character_name,
				   "Initiative",
				   str,
				   info["detail"],
				   pool,
				   0,
				   result["rolls"],
				   breakdown
				   )
	return str

# **[name]'s [selection] Roll
# [Result text]
#--- detail ---
# *[pool] at diff [diff]*
# [Rolls]
# *Breakdown*
# [extra info]

def format_roll (name: str, selection: str, text: str, detail: str, pool: str, difficulty: int, rolls, breakdown: str):
	long = "\n## {}'s {} Roll\n".format(name, selection)
	if detail == "On":
		if difficulty > 0:
			long += "*{} at difficulty {}*\n".format(pool, difficulty)
		else:
			long += pool + "\n"
	
	long += "> {}\n""".format(text)
	
	if detail == "On":
		long += "\n*Breakdown*\n"
		long += "> Roll(s):"+ formatdice(rolls)
		if breakdown != "":
			long += "\n> {}".format(breakdown)
	
	return long

def format_willpower(result, info):
	character_name = info["character_name"]

	str = format_roll(character_name,
				   "Willpower",
				   result["description"],
				   info["detail"],
				   "Willpower {}".format(info["Willpower"]),
				   result["difficulty"],
				   result["rolls"],"")

	return str

def format_soak(result, info):
	character_name = info["character_name"]
	damage_type = info["damage_type"]

	soakok = 1

	if damage_type == "Aggravated":
		pool = "{} Fortitude".format(info["Fortitude"])
		if info["Fortitude"] == 0:
			info["detail"] = "0 successes - Aggravated damage can only be soaked by Fortitude"
			soakok = 0
	else:
		pool = "{} Stamina + {} Fortitude".format(info["Stamina"], info["Fortitude"])

	breakdown = ""
	if soakok and info["Willpower OnOff"] == "On":
		breakdown += "+1 success from a Willpower point. "
	if info["blood"]["Stamina"] > 0:
		breakdown += "{} blood spent on Stamina. ".format(info["blood"]["Stamina"])
	if damage_type == "Bashing":
		breakdown += "Remember to half any remaining Bashing damage."

	str = format_roll(character_name,
				   "Soak",
				   "{} {} damage soaked".format(result["total_no_botch"], damage_type),
				   info["detail"],
				   pool,
				   result["difficulty"],
				   result["rolls"],
				   breakdown
				   )

	return str

def format_frenzy(result, info):

	character_name = info["character_name"]
	success = int(result["total"])

	if result["description"] == "Botch":
		str = "{} has frenzied. The duration to be determined by the Storyteller.".format(character_name)
	elif success >= 5:
		str = "{} has successfully avoided frenzy.".format(character_name)
	elif success > 0:
		str = "{} can hold off frenzy for {} round(s) before rolling again. 5 successes in total are required.".format(character_name, success)
	else:
		str = "{} has failed to hold off frenzy.".format(character_name)

	breakdown = ""
	if info["Willpower OnOff"] == "On":
		breakdown += "One success was gained from Willpower. "
	if info["Difficulty Description"] != "":
		breakdown += "Resisting frenzy due to: {}. ".format(info["Difficulty Description"])
	
	str = format_roll(character_name,
				   "Frenzy",
				   str,
				   info["detail"],
				   "{} Self Control".format(info["Self Control"]),
				   result["difficulty"],
				   result["rolls"],
				   breakdown)


	return str

def format_featofstr(result, info):

	character_name = info["character_name"]
	strength = info["Strength"]
	potence = info["Potence"]
	wound_penalty = info["Wound Penalty"]
	wound_penalty_info = info["Wound Penalty Info"]

	success = int(result["total"])
	if result["description"] == "Botch":
		mystr = "{} botched the roll and hurt themselves in the process of attempting this feat.".format(character_name)
	elif success <= 0:
		mystr = "{} has failed their feat of strength.".format(character_name, success)
	else:
		effort = canlift[int(strength) + int (potence) + success + wound_penalty - 1]
		mystr = "{} can successfully ".format(character_name) + effort

	noeffort = canlift[int(strength) + int (potence) + wound_penalty - 1]
	breakdown = "Without trying, they can " + noeffort + ". "
	if info["blood"]["Stamina"] > 0:
		breakdown += "{} blood spent on Stamina. ".format(info["blood"]["Stamina"])

	if int(wound_penalty) != 0:
		pool = "Strength {} + Potence {} - Wound Penalty {} + Rolled Willpower {}".format(strength, potence, abs(wound_penalty), result["pool"])
		breakdown += "They are {}".format(wound_penalty_info)
	else:
		pool = "Strength {} + Potence {} + Rolled Willpower {}".format(strength, potence, result["pool"])

	mystr = format_roll(character_name,
				   "Feat of Strength",
				   mystr,
				   info["detail"],
				   pool,
				   result["difficulty"],
				   result["rolls"],
				   breakdown)

	return mystr

def format_rotschreck(result, info):
	success = int(result["total"])
	character_name = info["character_name"]
	courage = info["Courage"]

	if result["description"] == "Botch":
		str = "{} has botched their Courage roll and has frenzied. The duration to be determined by the Storyteller.".format(character_name)
	elif success >= 5:
		str = "{} has successfully avoided Rotschreck.".format(character_name)
	elif success > 0:
		str = "{} can hold off Rotschreck for {} round(s) before rolling again. 5 successes in total are required.".format(character_name, success)
	else:
		str = "{} has failed to hold off Rotschreck.".format(character_name)

	pool = "{} Courage".format(courage)

	breakdown = ""
	if int(result["willpower"]) == 1:
		breakdown += "One success was gained from Willpower. "
	breakdown += " The difficulty to retain control was {}".format(result["difficulty"])
	if info["Difficulty Description"] != "":
		breakdown += " from {}.".format(info["Difficulty Description"])

	str = format_roll(character_name,
				   "Rotschreck",
				   str,
				   info["detail"],
				   pool,
				   result["difficulty"],
				   result["rolls"],
				   breakdown)
	
	return str

def format_drive(result, info):
	success = int(result["total"])

	character_name = info["character_name"]
	celerity = info["Effective Celerity"]
	driving = info["Driving"]
	stat = info["Driving Ability"]
	statlevel = info[stat]
	vehicle = info["Vehicle"]
	difficulty = info["Difficulty"]

	if result["description"] == "Botch":
		str = "{} has botched their drive roll and they have lost control of the {}.".format(character_name, vehicle)
	else:
		str = "{} has a {} on their drive roll.".format(character_name, result["description"])

	if int(celerity) > 0:
		pool = "{} {} + {} Celerity + {} Drive".format(statlevel, stat, celerity, driving)
	else: 
		pool = "{} {} + {} Drive".format(statlevel, stat, driving)

	maneuver = info["Maneuver"]

	breakdown = ""
	if int(result["willpower"]) == 1:
		breakdown += "One success was gained from Willpower. "
	breakdown += "The maneuverability of the {} limits the pool to {}. ".format(vehicle, maneuver)
	breakdown += "The vehicle was travelling at {}. ".format(info["Speed Diff Info"])
	if info["Weather OnOff"] == "On":
		breakdown += "Weather conditions were poor. "
	if info["Traffic OnOff"] == "On":
		breakdown += "The roads were busy. "		
	if info["Pursuit OnOff"] == "On":
		breakdown += "{} was engaged in a pursuit. "	.format(character_name)	

	str = format_roll(character_name,
				   "Driving",
				   str,
				   info["detail"],
				   pool,
				   result["difficulty"],
				   result["rolls"],
				   breakdown)

	return str

def format_auraperception(result, info):
	success = int(result["total"])
	character_name = info["character_name"]

	if result["description"] == "Botch":
		str = "{} has botched their Aura Perception roll.".format(character_name)
	elif success <= 0:
		str = "{} has failed their Aura Perception roll; their sight is unclear.".format(character_name, result["description"])
	else:
		if success > 5:
			choice = auras[5-1]
		else:
			choice = auras[success-1]
		
		str = "{} has {} successes and {} of an aura or scan the room for a particular aura.".format(character_name, success, choice)

	pool = "{} Perception, {} Empathy and Auspex {}.".format(info["Perception"], info["Empathy"], info["Auspex"])

	breakdown = ""
	if int(result["willpower"]) == 1:
		breakdown += "One success was gained from Willpower. "
	if info["Wound Penalty Info"] != "":
		breakdown += "{} is {}. ".format(character_name, info["Wound Penalty Info"])
	if info["Speciality OnOff"] == "On":
		breakdown += "Character has a relevant speciality. "

	str = format_roll(character_name,
				   "Aura Perception",
				   str,
				   info["detail"],
				   pool,
				   result["difficulty"],
				   result["rolls"],
				   breakdown)

	return str

def format_spiritstouch(result, info):
	success = int(result["total"])
	character_name = info["character_name"]

	if result["description"] == "Botch":
		str = "{} has botched their Spirits Touch roll. They are overwhelmed by psychic impressions for the next 30 minutes and are unable to act.".format(character_name)
	elif success <= 0:
		str = "{} has failed their Spirits Touch roll; their sight is unclear.".format(character_name, result["description"])
	else:
		str = "{} has {} successes. ".format(character_name, success)
		if success >= 5:
			str = str + "They gain a wealth of information; nearly anything they want to know about the person's relationship with the object is available."
		elif success == 4:
			str = str + "They gain the name of the person who left the psychic impression."
		elif success == 3:
			str = str + "They gain useful information about the person who left the psychic impression, such as age and state of mind."
		elif success == 2:
			str = str + "They gain two items of basic information about the person who left the psychic impression, such as gender or hair colour."
		else:
			str = str + "They gain an item of basic information about the person who left the psychic impression, such as gender or hair colour."
	
	pool = "{} Perception, {} Empathy and Auspex {}.".format(info["Perception"], info["Empathy"], info["Auspex"])
	
	breakdown = ""
	if int(result["willpower"]) == 1:
		breakdown += "One success was gained from Willpower. "
	if info["Wound Penalty Info"] != "":
		breakdown += "{} is {}. ".format(character_name, info["Wound Penalty Info"])
	if info["Speciality OnOff"] == "On":
		breakdown += "Character has a relevant speciality. "

	str = format_roll(character_name,
				   "Spirits Touch",
				   str,
				   info["detail"],
				   pool,
				   result["difficulty"],
				   result["rolls"],
				   breakdown)

	return str

def format_degeneration(result, info):
	success = int(result["total"])
	character_name = info["character_name"]

	stat = info["Path Attribute"]
	path = info["Path of Enlightenment Info"]


	if "Path of" not in path:
		path = "Path of " + path
	pool = "At {} on the {}, with {} {}".format(info["Path of Enlightenment"], path, stat, info[stat])

	if info["Path of Enlightenment Info"] in hierarchyofsin:
		hierarchy = hierarchyofsin[info["Path of Enlightenment Info"]]
	elif path in hierarchyofsin:
		hierarchy = hierarchyofsin[path]
	else:
		hierarchy = hierarchyofsin["Humanity"]

	if result["description"] == "Botch":
		str = "{} has botched their roll. They lose 10 on the {}, 1 level of {}, and gain a derangement.".format(character_name, path, stat)
		newlevel = info["Path of Enlightenment"] - 10
		pointslost = 10
	else:
		pointslost = 10 - (2 * success)
		newlevel = info["Path of Enlightenment"] - int(pointslost)
		if pointslost == 0:
			str = "{} has felt remorse at their actions and retained their level in the {}".format(character_name, path)
		elif newlevel <= 0:
			str = "{} has lost everything in their path and fallen to the beast.".format(character_name)
		else:
			if pointslost == 10:
				level = "fully"
			else:
				level = "partially"
			str = "{} has {} accepted their act and lost {} points of their path.".format(character_name, level, pointslost)

	breakdown = ""
	for sin in hierarchy:
		if int(hierarchy[sin]) < newlevel:
			breakdown = "The next worst thing you could do is '{}'. ". format(sin)
			break
	breakdown += "Their new rating is {}. ".format(newlevel)
	if pointslost > 0:
		breakdown += "See the storyteller to update your character sheet."

	str = format_roll(character_name,
				   "Degeneration",
				   str,
				   info["detail"],
				   pool,
				   result["difficulty"],
				   result["rolls"],
				   breakdown)
	
	return str

def get_level_from_character(characterdata, item: str, category: str = "all"):
	if item in characterdata:
		return int(characterdata[item])
	else:
		catlist = ["attributes", "abilities", "disciplines", "backgrounds"]
		
		resultlist = []

		for cat in catlist:
			if category == "all" or category == cat:
				for info in characterdata[cat]:
					if "name" in info and info["name"] == item:
						return int(info["level"])
					elif "skillname" in info and info["skillname"] == item:
						resultlist.append(int(info["level"]))
					elif "background" in info and info["background"] == item:
						resultlist.append(int(info["level"]))
		
		if len(resultlist) == 1:
			return resultlist[0]
		elif len(resultlist) == 0:
			return 0
		else:
			return resultlist

def roll_willpower(info):

	result = roll_pool(info["Willpower"], info["Difficulty"])

	return result

def roll_initiative(info):

	result = {
		"total": 0,
		"elements": {}
	}

	rolls = dice(1)
	total = rolls[0]
	result["elements"]["D10"] = total
	
	dexterity = info["Effective Dexterity"]
	wits      = info["Wits"]
	celerity  = info["Effective Celerity"]
	
	total = total + int(dexterity) + int(wits) + int(celerity)
	
	result["total"] = total
	result["rolls"] = rolls

	return result

def roll_pool(pool: int, diff: int = 6, speciality: bool = False, willpower: str = "Off"):
	result = {
		"total": 0,
		"ones": 0,
		"tens": 0,
		"successes": 0,
		"rolls": {},
		"description": "",
		"elements": {},
		"willpower": 0,
		"pool": pool,
		"difficulty": diff
	}
	if pool <= 0:
		result["description"] = "Pool is 0 - cannot roll"
		return result
	
	rolls = dice(pool)
	result["rolls"] = rolls

	for i in rolls:
		if i == 1:
			result["ones"] = int(result["ones"]) + 1
			result["total"] = result["total"] - 1
		elif i == 10:
			result["total"] = result["total"] + 1
			result["successes"] = result["successes"] + 1
			result["tens"] = result["tens"] + 1
			if speciality:
				result["total"] = result["total"] + 1
				result["successes"] = result["successes"] + 1
		elif i >= diff:
			result["total"] = result["total"] + 1
			result["successes"] = result["successes"] + 1

	if willpower == "On":
		result["total"] = result["total"] + 1
		result["successes"] = result["successes"] + 1
		result["willpower"] = 1

	result["total_no_botch"] = max(0, result["total"])

	if int(result["successes"]) == 0 and int(result["ones"]) > 0:
		result["description"] = "Botch"
	else:
		successes = int(result["total"])
		if successes <= 0:
			result["description"] = "Failure"
		elif successes == 1:
			result["description"] = "Marginal Success (1)"
		elif successes == 2:
			result["description"] = "Moderate Success (2)"
		elif successes == 3:
			result["description"] = "Complete Success (3)"
		elif successes == 4:
			result["description"] = "Exceptional Success (4)"
		elif successes >= 5:
			result["description"] = "Phenominal Success (5+)"
	return result

async def close_roll(actionrow, interaction: discord.Interaction):
	actionrow.__view.clear_items()

	if actionrow.__view.display_private.accessory.label == "On":
		actionrow.__view.info.content = str
		await interaction.user.send(str)
	else:
		channel = interaction.channel
		await channel.send(str)

	str = "{} has rolled some dice.".format(actionrow.characterdata["name"])
	actionrow.result = discord.ui.TextDisplay(str)
	showresult = discord.ui.Container(actionrow.result)
	actionrow.__view.add_item(showresult)

def get_discipline_level(characterdata, discipline_name: str):
	level = 0
	if characterdata is not None:
		if "disciplines" in characterdata:
			for disc in characterdata["disciplines"]:
				if disc["name"] == discipline_name:
					level = disc["level"]
	return level

def get_attribute_level(characterdata, attribute_name: str):
	level = 0
	if characterdata is not None:
		if "attributes" in characterdata:
			for att in characterdata["attributes"]:
				if att["name"] == attribute_name:
					level = att["level"]
	return level

def get_max_level(characterdata):
	if characterdata is not None:
		if "max_rating" in characterdata:
			max_rating = characterdata["max_rating"]
		else:
			max_rating = 5
	return max_rating

def get_char_from_pulldown(view):
	chardata = None

	characterchoices = view.charChoices.char.options
	for ch in characterchoices:
		if ch.default == True:
			characterID = str(ch.value)
			newcharinfo = get_character(view.server, view.nameid, characterID)
			if "code" in newcharinfo:
				logging.info("Failed to obtain character data for {}",format(characterID))
				print(newcharinfo)
			else:
				logging.info("Obtained character data for " + newcharinfo["result"]["name"])
				chardata = newcharinfo["result"]
	return chardata

def load_info(view: RollPage1LayoutView, characterdata):
	info = {}

	info["detail"] = view.display_detail.accessory.label
	info["character_name"] = characterdata["name"]
	info["Clan"] = characterdata["private_clan"]
	info["damage_type"] = "Lethal"
	info["Willpower OnOff"] = "Off"
	info["Speciality OnOff"] = "Off"
	info["Wound Penalty"] = 0
	info["Wound Penalty Info"] = ""
	info["Speed Diff Modifier"] = 0
	info["Speed Diff Info"] = "a safe speed"
	info["Timescale"] = 0
	info["Intensity"] = 0

	info["Celerity"] = int(get_discipline_level(characterdata, "Celerity"))
	info["Effective Celerity"] = int(info["Celerity"])
	info["Fortitude"] = int(get_discipline_level(characterdata, "Fortitude"))
	info["Potence"] = int(get_discipline_level(characterdata, "Potence"))
	info["Auspex"] = int(get_discipline_level(characterdata, "Auspex"))

	info["Dexterity"] = int(get_attribute_level(characterdata, "Dexterity"))
	info["Effective Dexterity"] = int(info["Dexterity"])
	info["Stamina"] = int(get_attribute_level(characterdata, "Stamina"))
	info["Effective Stamina"] = int(info["Stamina"])
	info["Strength"] = int(get_attribute_level(characterdata, "Strength"))
	info["Effective Strength"] = int(info["Strength"])
	info["Wits"] = int(get_attribute_level(characterdata, "Wits"))
	info["Willpower"] = int(get_level_from_character(characterdata, "Willpower", "attributes"))
	info["Self Control"] = int(get_attribute_level(characterdata, "Self Control"))
	info["Courage"] = int(get_attribute_level(characterdata, "Courage"))
	info["Perception"] = int(get_attribute_level(characterdata, "Perception"))
	info["Conscience"] = int(get_attribute_level(characterdata, "Conscience"))
	info["Conviction"] = int(get_attribute_level(characterdata, "Conviction"))

	info["Path of Enlightenment Info"] = characterdata["path_of_enlightenment"]
	info["Path of Enlightenment"] = int(characterdata["path_rating"])
	info["Sins"] = 0
	info["Sins Info"] = ""

	info["Empathy"] = int(get_level_from_character(characterdata, "Empathy", "abilites"))
	info["Driving"] = int(get_level_from_character(characterdata, "Drive", "abilites"))
	info["Driving Ability"] = "Dexterity"
	info["Vehicle"] = "Sedan (4)"
	info["Maneuver"] = 4
	info["Weather OnOff"] = "Off"
	info["Traffic OnOff"] = "Off"
	info["Pursuit OnOff"] = "Off"

	info["Background"] = 0
	info["Background Info"] = "Resources"
	resources = get_level_from_character(characterdata, "Resources","backgrounds")
	if isinstance(resources, list):
		info["Background"] = max(resources)
	else:
		info["Background"] = resources

	info["Difficulty"] = 6
	info["Difficulty Description"] = ""

	for input in view.walk_children():
		# print(input.id)
		# print(type(input))
		if input.id == forminputIDs["CelerityPulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Effective Celerity"] = None
			else:
				info["Effective Celerity"] = int(option.value)
		elif input.id == forminputIDs["DexterityPulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Effective Dexterity"] = None
			else:
				info["Effective Dexterity"] = int(option.value)
		elif input.id == forminputIDs["StaminaPulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Effective Stamina"] = None
			else:
				info["Effective Stamina"] = int(option.value)
		elif input.id == forminputIDs["StrengthPulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Effective Strength"] = None
			else:
				info["Effective Strength"] = int(option.value)
		elif input.id == forminputIDs["WillpowerButton"]:
			info["Willpower OnOff"] = input.accessory.label
		elif input.id == forminputIDs["DamageTypePulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["damage_type"] = None
			else:
				info["damage_type"] = option.value
		elif input.id == forminputIDs["DifficultyPulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Difficulty"] = None
			else:
				difficulty_str = option.value
				if isinstance(difficulty_str, str) and ":" in difficulty_str:
					info["Difficulty"] = int(difficulty_str.split(':')[1])
				else:
					info["Difficulty"] = int(difficulty_str)
				info["Difficulty Description"] = option.label
		elif input.id == forminputIDs["WoundPulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Wound Penalty"] = None
			else:
				wound_str = option.value
				info["Wound Penalty"] = int(wound_str.split(':')[1])
				info["Wound Penalty Info"] = option.label
		elif input.id == forminputIDs["SpecialityButton"]:
			info["Speciality OnOff"] = input.accessory.label
		elif input.id == forminputIDs["DriveStatPulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Drive Ability"] = None
			else:
				info["Drive Ability"] = option.value
		elif input.id == forminputIDs["VehiclePulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Vehicle"] = None
			else:
				info["Vehicle"] = option.value
		elif input.id == forminputIDs["SpeedPulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Speed Diff Modifier"] = None
			else:
				info["Speed Diff Modifier"] = int(option.value)
				info["Speed Diff Info"] = option.label
		elif input.id == forminputIDs["WeatherButton"]:
			info["Weather OnOff"] = input.accessory.label
		elif input.id == forminputIDs["TrafficButton"]:
			info["Traffic OnOff"] = input.accessory.label
		elif input.id == forminputIDs["PursuitButton"]:
			info["Pursuit OnOff"] = input.accessory.label
		elif input.id == forminputIDs["TimescalePulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Timescale"] = None
			else:
				info["Timescale"] = int(option.value)
		elif input.id == forminputIDs["IntensityPulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Intensity"] = None
			else:
				info["Intensity"] = int(option.value)
		elif input.id == forminputIDs["BackgroundPulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Background"] = None
			else:
				value_str = option.value
				info["Background"] = int(value_str.split(':')[0])
				info["Background Info"] = option.label
		elif input.id == forminputIDs["SinsPulldownActionRow"]:
			select = input.children[0]
			option = discord.utils.get(select.options, default=True)
			if option is None:
				info["Sins"] = None
			else:
				value_str = option.value
				info["Sins"] = int(value_str)
				info["Sins Info"] = option.label

	info["blood"] = {}
	info["blood"]["Dexterity"] =  info["Effective Dexterity"] - info["Dexterity"]
	info["blood"]["Stamina"]   =  info["Effective Stamina"] - info["Stamina"]
	info["blood"]["Strength"]  =  info["Effective Strength"] - info["Strength"]

	if info["Conscience"] > 0:
		info["Path Attribute"] = "Conscience"
	else:
		info["Path Attribute"] = "Conviction"

	return info