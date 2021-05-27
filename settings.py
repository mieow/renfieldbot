import discord
from discord.ext import commands
import mysql.connector
import os
from common import check_is_auth
from tabulate import tabulate
import renfield_sql

	
class Settings(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command(name='config', 
		usage='<setting_name> <setting_value>',
		brief='Configure the bot settings',
		help='''
		
		(IN DEVELOPMENT) Use this command to customise the operation of the bot for your server.
		
		setting_name options:
			admin_role			- set the name of the Storyteller role
			linear_category		- set the channel category name for creating linear channels
			max_linears			- set the maximum number of linear allowed
		
		''')
	@check_is_auth()
	async def config(self, ctx, setting_name: str="", *, setting_value: str=""):
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		author = ctx.message.author.display_name
		server = ctx.message.guild.name
		
		#available settings
		settings = ['admin_role', 'linear_category', 'max_linears']
		rows = []
				
		if setting_name == '':
			headers = ["Name", "Setting"]
			for setting_name in settings:
			
				default = os.getenv('DEFAULT_{}'.format(setting_name).upper())

				setting_value = mydb.get_bot_setting(setting_name, default, server)
				rows.append([setting_name, setting_value])
									
			table = tabulate(rows, headers)
			await ctx.send('```\n' + table + '```')

		elif (setting_name in settings):
			if setting_value == "":
				await ctx.send("Master, please specify a value for setting {}.".format(setting_name))
			else:
				ok = mydb.save_bot_setting(setting_name, setting_value, server)
				if ok:
					await ctx.send("Setting {} saved".format(setting_name))
				else:
					await ctx.send("Setting {} NOT saved".format(setting_name))

		else:
			await ctx.send("I'm sorry Master, '{}' is not a real setting name. Check your spelling.".format(setting_name))

def setup(bot):
	bot.add_cog(Settings(bot))