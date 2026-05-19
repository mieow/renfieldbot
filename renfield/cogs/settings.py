from xmlrpc import server

import discord
from discord.ext import commands
import mariadb
import os
import traceback
from tabulate import tabulate
from renfield_sql import get_bot_setting, save_bot_setting, check_is_auth
from discord import Embed, app_commands
from dotenv import load_dotenv

load_dotenv()

class SettingsModal(discord.ui.Modal, title="Change Renfield Config"):

	setting_name = discord.ui.Label(
		text="Choose a setting",
		description="Select the setting you want to change from the dropdown menu below.",
		component=discord.ui.Select(
			placeholder="Select a setting to change",
			options=[
				discord.SelectOption(description="List all settings", label="list-all"),
				discord.SelectOption(description="Set Role name for Storytellers", label="admin_role"),
				discord.SelectOption(description="Set URL of Wordpress Site with Character Plugin", label="wordpress_site"),
				discord.SelectOption(description="Set OAuth consumer key", label="consumer_key"),
				discord.SelectOption(description="Set OAuth consumer secret", label="consumer_secret"),
				discord.SelectOption(description="Set voice for Renfield from AWS Polly text-to-speech", label="polly_voice"),
				discord.SelectOption(description="Set default location for events", label="event_location"),
				discord.SelectOption(description="Set default start time for events (HH:MM) in UTC", label="event_start"),
				discord.SelectOption(description="Set default finish time for events (HH:MM) in UTC", label="event_end"),
				discord.SelectOption(description="Set default description time for events", label="event_desc"),
				discord.SelectOption(description="Set text channel for bot logging", label="cubby-hole"),
				discord.SelectOption(description="Enable voice channel activity logging (on/off)", label="voice-activity"),
				discord.SelectOption(description="Set webhook URL for Harker integration", label="harker-webhook"),
				discord.SelectOption(description="Set Role name for accepted/recognised users", label="accepted_role"),
			],
		)
	)

	setting_value = discord.ui.TextInput(
		label="Value of Setting",
		placeholder="Enter the value for the setting here. Leave blank to reset to default.",
		required=False
	)

	async def on_submit(self, interaction: discord.Interaction):
		assert isinstance(self.setting_name.component, discord.ui.Select)
		assert isinstance(self.setting_value, discord.ui.TextInput)

		voices = ["Jan", "Aditi ", "Amy  ", "Astrid", "Bianca", "Brian", "Camila", "Carla", "Carmen", "Céline/Celine", "Chantal", "Conchita", "Cristiano", "Dóra/Dora", "Emma", "Enrique", "Ewa", "Filiz", "Geraint", "Giorgio", "Gwyneth", "Hans", "Inês/Ines", "Ivy", "Jacek", "Joanna  ", "Joey", "Justin", "Karl", "Kendra", "Kimberly", "Léa", "Liv", "Lotte", "Lucia", "Lupe  ", "Mads", "Maja", "Marlene", "Mathieu", "Matthew  ", "Maxim", "Mia", "Miguel", "Mizuki", "Naja", "Nicole", "Penélope/Penelope", "Raveena", "Ricardo", "Ruben", "Russell", "Salli", "Seoyeon", "Takumi", "Tatyana", "Vicki", "Vitória/Vitoria", "Zeina", "Zhiyu"]
		settings = ['list-all', 'admin_role', 'voice-activity', 'cubby-hole', 'accepted_role', 'wordpress_site', 'harker-webhook', 'consumer_key', 'consumer_secret', 'polly_voice', 'event_location', 'event_start', 'event_end', 'event_desc']
		rows = []

		server = interaction.guild.name
		setting_name = self.setting_name.component.values[0]
		setting_value = self.setting_value.value

		if setting_name == 'list-all':
			headers = ["Name", "Setting"]
			for setting_name in settings:
			
				setting_value = get_bot_setting(setting_name, server)
				rows.append([setting_name, setting_value])
									
			table = tabulate(rows, headers)
			await interaction.response.send_message('```\n' + table + '```')
			return
		elif setting_value == "":
			if setting_name == "":
				await interaction.response.send_message("Master, you must select a setting!")
				return
			default = os.getenv('DEFAULT_{}'.format(setting_name).upper())
			save_bot_setting(setting_name, default, server)
			await interaction.response.send_message("Master, reset {} setting to the default '{}'.".format(setting_name, default))
			return
		elif setting_name == "polly_voice":
			if setting_value not in voices:
				ok = 0
				await interaction.response.send_message("Voice {} is not in the available list of Standard  Voice options. Choose from {}. More info here: https://docs.aws.amazon.com/polly/latest/dg/voicelist.html".format(setting_value, ", ".join(voices)))
				return
		elif setting_name == "wordpress_site":
			# remove any trailing /
			setting_value = setting_value.rstrip('/')

		ok = save_bot_setting(setting_name, setting_value, server)

		if ok:
			await interaction.response.send_message("Setting {} saved with value {}".format(setting_name, setting_value))
		else:
			await interaction.response.send_message("Setting {} NOT saved".format(setting_name))

	async def on_error(self, interaction: discord.Interaction, error: Exception):
		await interaction.response.send_message("An error occurred while processing the settings form.")
		traceback.print_exception(type(error), error, error.__traceback__)
		print(f"Error in settings form: {error}")

	
class Settings(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
	async def cog_app_command_error(self, ctx, error):
		if isinstance(error, discord.app_commands.CheckFailure):
			await ctx.response.send_message("I'm sorry Master. {}".format(error))
		else:
			await ctx.response.send_message("I'm sorry Master, the command failed.")
			print(error)
		
	@check_is_auth()
	@app_commands.command(name="config", description="Change Renfield Config")
	async def _config(self, ctx):
		await ctx.response.send_modal(SettingsModal())

async def setup(bot):
	await bot.add_cog(Settings(bot))