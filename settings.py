import discord
from discord.ext import commands
import mysql.connector
import os
from common import check_is_auth
from tabulate import tabulate
import renfield_sql
from discord import Embed, app_commands
from dotenv import load_dotenv

load_dotenv()
GUILDID = int(os.getenv('DISCORD_GUILD_ID'))

	
class Settings(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
	@app_commands.command(name="config", description="Change Renfield Config")
	@app_commands.describe(
		setting_name="Setting Name",
		setting_value="Value of Setting"
	)
	@app_commands.choices(setting_name=[
		app_commands.Choice(name="Set Role name for Storytellers", value="admin_role"),
		app_commands.Choice(name="Set URL of Wordpress Site with Character Plugin", value="wordpress_site"),
		app_commands.Choice(name="Set voice for Renfield from AWS Polly text-to-speech", value="polly_voice")
	])
	@check_is_auth()
	async def _config(self, ctx, setting_name: str="", *, setting_value: str=""):
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		author = ctx.user.display_name
		server = ctx.guild.name
		
		#available settings
		settings = ['admin_role', 'wordpress_site', 'polly_voice']
		voices = ["Jan", "Aditi ", "Amy  ", "Astrid", "Bianca", "Brian", "Camila", "Carla", "Carmen", "Céline/Celine", "Chantal", "Conchita", "Cristiano", "Dóra/Dora", "Emma", "Enrique", "Ewa", "Filiz", "Geraint", "Giorgio", "Gwyneth", "Hans", "Inês/Ines", "Ivy", "Jacek", "Joanna  ", "Joey", "Justin", "Karl", "Kendra", "Kimberly", "Léa", "Liv", "Lotte", "Lucia", "Lupe  ", "Mads", "Maja", "Marlene", "Mathieu", "Matthew  ", "Maxim", "Mia", "Miguel", "Mizuki", "Naja", "Nicole", "Penélope/Penelope", "Raveena", "Ricardo", "Ruben", "Russell", "Salli", "Seoyeon", "Takumi", "Tatyana", "Vicki", "Vitória/Vitoria", "Zeina", "Zhiyu"]
		rows = []
				
		if setting_name == '':
			headers = ["Name", "Setting"]
			for setting_name in settings:
			
				default = os.getenv('DEFAULT_{}'.format(setting_name).upper())

				setting_value = mydb.get_bot_setting(setting_name, default, server)
				rows.append([setting_name, setting_value])
									
			table = tabulate(rows, headers)
			await ctx.response.send_message('```\n' + table + '```')

		elif (setting_name in settings):
			if setting_value == "":
				await ctx.response.send_message("Master, please specify a value for setting {}.".format(setting_name))
			else:
				ok = 1
				# Verify AWS Polly choices
				if setting_name == "polly_voice":
					if setting_value not in voices:
						ok = 0
						await ctx.response.send_message("Voice {} is not in the available list of Standard  Voice options. Choose from {}. More info here: https://docs.aws.amazon.com/polly/latest/dg/voicelist.html".format(setting_value, ", ".join(voices)))
				
				if ok:
					ok = mydb.save_bot_setting(setting_name, setting_value, server)
					if ok:
						await ctx.response.send_message("Setting {} saved with value {}".format(setting_name, setting_value))
					else:
						await ctx.response.send_message("Setting {} NOT saved".format(setting_name))

		else:
			await ctx.response.send_message("I'm sorry Master, '{}' is not a real setting name. Check your spelling.".format(setting_name))

async def setup(bot):
	await bot.add_cog(Settings(bot))