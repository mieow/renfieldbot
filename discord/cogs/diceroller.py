import random
import discord
import pprint
from discord.ext import commands
from discord import Embed, app_commands
from common import check_is_auth, check_restapi_active
from wordpress_api import get_my_character, get_character, is_storyteller

# SUCCESSES - BOLD
# 10S - ITALIC


class DiceRoller(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None

	async def cog_app_command_error(self, ctx, error):
		if isinstance(error, discord.app_commands.CheckFailure):
			await ctx.response.send_message("I'm sorry Master. {}".format(error))
		else:
			await ctx.response.send_message("I'm sorry Master, the command failed.")
			print(error)


	@check_restapi_active()
	@app_commands.command(name='rollmy', description='Roll a character attribute')
	@app_commands.describe(
		attribute="Character Attribute",
		ability="Character Ability (optional)"
	)
	# Max 25 choices
	@app_commands.choices(attribute=[
		app_commands.Choice(name="Willpower", value="willpower"),
		app_commands.Choice(name="Temporary Willpower", value="current_willpower"),
		app_commands.Choice(name="Strength", value="Strength"),
		app_commands.Choice(name="Dexterity", value="Dexterity"),
		app_commands.Choice(name="Stamina", value="Stamina"),
		app_commands.Choice(name="Charisma", value="Charisma"),
		app_commands.Choice(name="Manipulation", value="Manipulation"),
		app_commands.Choice(name="Appearance", value="Appearance"),
		app_commands.Choice(name="Perception", value="Perception"),
		app_commands.Choice(name="Intelligence", value="Intelligence"),
		app_commands.Choice(name="Wits", value="Wits"),
		app_commands.Choice(name="Courage", value="Courage"),
		app_commands.Choice(name="Self Control", value="Self Control"),
		app_commands.Choice(name="Conscience", value="Conscience"),
		app_commands.Choice(name="Initiative", value="init"),
		app_commands.Choice(name="Skip", value="skip"),
	])
	async def rollmy(self, ctx, attribute: str, ability: str = "none"):
		nameid = ctx.user.id
		server = ctx.guild.name
		charinfo = get_my_character(nameid, server)
		if "code" in charinfo:
			await ctx.response.send_message(charinfo["message"])
		else:
			cname = charinfo["result"]["display_name"]
			rolls = []
			if attribute == "init":
				str = roll_initiative(charinfo["result"])
				await ctx.response.send_message("Result of {}'s Initiative roll: {}".format(cname, str))
						
			elif attribute != "skip":
				rolling = []
				rolls = dice(get_level_from_character(charinfo["result"], attribute, "attributes"))
				rolling.append(attribute)
				
				if ability != "none":
					level = get_level_from_character(charinfo["result"], ability, "abilities")
					if level > 0:
						rolls = rolls + dice(level)
					rolling.append(ability)
			
				str = formatdice(rolls)
				await ctx.response.send_message("Result of {}'s {} roll: {}".format(cname, " + ".join(rolling), str))
			else:
				level = get_level_from_character(charinfo["result"], ability)
				if level > 0:
					rolls = dice(level)
					str = formatdice(rolls)
					await ctx.response.send_message("Result of {}'s {} roll: {}".format(cname, ability, str))
				else:
					pprint.pprint(charinfo["result"])
					await ctx.response.send_message("Could not find {} for {} or level is 0.".format(ability, cname))

	@check_is_auth()
	@check_restapi_active()
	@app_commands.command(name='rollst', description='Roll a character attribute')
	@app_commands.describe(
		attribute="Character Attribute",
		ability="Character Ability (optional)"
	)
	@app_commands.choices(attribute=[
		app_commands.Choice(name="Willpower", value="willpower"),
		app_commands.Choice(name="Temporary Willpower", value="current_willpower"),
		app_commands.Choice(name="Strength", value="Strength"),
		app_commands.Choice(name="Dexterity", value="Dexterity"),
		app_commands.Choice(name="Stamina", value="Stamina"),
		app_commands.Choice(name="Charisma", value="Charisma"),
		app_commands.Choice(name="Manipulation", value="Manipulation"),
		app_commands.Choice(name="Appearance", value="Appearance"),
		app_commands.Choice(name="Perception", value="Perception"),
		app_commands.Choice(name="Intelligence", value="Intelligence"),
		app_commands.Choice(name="Wits", value="Wits"),
		app_commands.Choice(name="Courage", value="Courage"),
		app_commands.Choice(name="Self Control", value="Self Control"),
		app_commands.Choice(name="Conscience", value="Conscience"),
		app_commands.Choice(name="Initiative", value="init"),
		app_commands.Choice(name="Skip", value="skip"),
	])
	async def rollst(self, ctx, character: str, attribute: str, ability: str = "None"):
		nameid = ctx.user.id
		server = ctx.guild.name
		
		try:
			isST = is_storyteller(nameid, server)
		except Exception as e:
			print(e)
		
		if isST:
			charinfo = get_character(server, nameid, character)
			if "code" in charinfo:
				
				await ctx.response.send_message(charinfo["message"])
			else:
				cname = charinfo["result"]["display_name"]
				rolls = []
				if attribute == "init":
					str = roll_initiative(charinfo["result"])
					await ctx.response.send_message("Result of {}'s Initiative roll: {}".format(cname, str))
							
				elif attribute != "skip":
					rolling = []
					rolls = dice(get_level_from_character(charinfo["result"], attribute, "attributes"))
					rolling.append(attribute)
					
					if ability != "none":
						level = get_level_from_character(charinfo["result"], ability, "abilities")
						if level > 0:
							rolls = rolls + dice(level)
						rolling.append(ability)
				
					str = formatdice(rolls)
					await ctx.response.send_message("Result of {}'s {} roll: {}".format(cname, " + ".join(rolling), str))
				else:
					level = get_level_from_character(charinfo["result"], ability)
					if level > 0:
						rolls = dice(level)
						str = formatdice(rolls)
						await ctx.response.send_message("Result of {}'s {} roll: {}".format(cname, ability, str))
					else:
						pprint.pprint(charinfo["result"])
						await ctx.response.send_message("Could not find {} for {} or level is 0.".format(ability, cname))
		else:
			await ctx.response.send_message("This command is only available for Storytellers")




	@app_commands.command(name='rolldice', description='Dice roller')
	@app_commands.describe(
		dicepool="Number of D10s to roll",
		note="Optional comment"
	)
	async def rolldice(self, ctx, dicepool: app_commands.Range[int, 1, 40], note:str = ""):
		author = ctx.user.display_name
		if dicepool > 40:
			await ctx.response.send_message('I\'m sorry, Master {}, I only have 40 dice in my dice bag.'.format(author))
		elif dicepool <= 0:
			await ctx.response.send_message('You are having a jest with me, Master {}, I cannot roll that number of dice.'.format(author))
		else:
			try:
				rolls = dice(dicepool)
				str = formatdice(rolls)
				await ctx.response.send_message("Master {}, I have made a '{}' roll for you: ".format(author, note) + str)
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

def get_level_from_character(characterdata, item: str, category: str = "all"):
	if item in characterdata:
		return int(characterdata[item])
	else:
		catlist = ["attributes", "abilities", "disciplines", "backgrounds"]
		
		for cat in catlist:
			if category == "all" or category == cat:
				for info in characterdata[cat]:
					if "name" in info and info["name"] == item:
						return int(info["level"])
					elif "skillname" in info and info["skillname"] == item:
						return int(info["level"])
					elif "background" in info and info["background"] == item:
						return int(info["level"])
		
		return 0

def roll_initiative(characterdata):
	rolls = dice(1)
	str = formatdice(rolls)
	
	for item in characterdata["attributes"]:
		if item["name"] == "Dexterity":
			str = str + " + Dexterity " + item["level"]
		if item["name"] == "Wits":
			str = str + " + Wits " + item["level"]

	
	for item in charinfo["result"]["disciplines"]:
		if item["name"] == "Celerity":
			str = str + " + Celerity " + item["level"]
			break
	
	return str