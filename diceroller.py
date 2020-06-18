import random
import discord
from discord.ext import commands


class DiceRoller(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None

	@commands.command(name='roll', help='Dice roller')
	async def roll(self, ctx, dicepool: int):
		author = ctx.message.author.display_name
		if dicepool > 30:
			await ctx.send('I\'m sorry, Master {}, I only have 30 dice in my dice bag.'.format(author))
		elif dicepool <= 0:
			await ctx.send('You are having a jest with me, Master {}, I cannot roll that number of dice.'.format(author))
		else:
			try:
				rolled = []
				for x in range(dicepool):
					rolled.append(random.randrange(1,11))
				sortrolls = sorted(rolled)
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
				await ctx.send("Master {}, I have rolled these for you: ".format(author) + str)
			except Exception as e:
				print('Renfield is confused')
				print(e)

	# @commands.error
	# async def roll_error(ctx, error):
		# if isinstance(error, commands.MissingRequiredArgument):
			# await ctx.send("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))

	async def cog_command_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send("I'm sorry Master, I need more information. Can you tell me the {}".format(error.param.name))

def setup(bot):
	bot.add_cog(DiceRoller(bot))
