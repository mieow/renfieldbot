#!/usr/bin/env python3

import os
import mysql.connector
import discord
import logging
import logging.handlers
import cogs.wordpress_api
#import renfield_sql
import asyncio

from dotenv import load_dotenv, dotenv_values
from discord.ext import commands
from discord import app_commands
from common import write_key
from datetime import datetime, date
from renfield_sql import get_bot_setting, save_bot_setting, get_log_channel

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
#GUILD = os.getenv('DISCORD_GUILD')
#GUILDID = int(os.getenv('DISCORD_GUILD_ID'))
LOG_HOME = os.getenv('LOG_HOME')
DISCORDLOG = LOG_HOME + '/discord.log'
#OWNER = os.getenv('LOG_HOME')


# BUGS
#
# - update character name in members table, as well as player name

# WISH LIST
#
# - add logging
# - able to be added to other servers
#		- check linear commands
#		- confirm other commands
#		- check category exists before trying to create a linear in it
#		- niceness - ensure ppl can only delete lines for their server
# - Settings
#		- set storyteller role (admin_role)
#		- set Linears category (linear_category)
#		- max number of linears (max_linears = 3)
#		- set room change announcements on/off
#		- set room announcement channel
#		- set honorific (honorific = Master)
#		- set error message (error_msg = I'm sorry
#		- report current settings (in hello, if user is an ST/admin)
# - chat log
#		- start logging
#		- stop logging
#		- ensure file doesn't get too big
#		- download chat log
#		- remind x lines when logging is enabled
#		- list all channels in server that have logs
# - wordpress API link for access to character database
# - play mp3 at specified intervals
# - reminder/reference: page nos, pools, diff, - player contributed
# - track damage taken
#
# send PM: await ctx.author.send('boop!')
# get PM:
#	@client.event
#	async def on_message(message):
#		if message.channel.id == message.author.dm_channel.id: # dm #only
#			# do stuff here #
#		elif not message.guild: # group dm only
#			# do stuff here #
#		else: # server text channel
#			# do stuff here #


#handler = logging.FileHandler(filename=DISCORDLOG, encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

description = 'GVLARP Renfield Bot'
bot = commands.Bot(
	command_prefix='.',
	description=description,
	intents=intents,
	#owner_ids=[OWNER]
)

# Connect to Discord when ready
@bot.event
async def on_ready(ctx: discord.Interaction):
	print('---------------------------------------------')
	print('Bot User ID: {}'.format(bot.user.id))
	print('Bot User Name: ' + bot.user.name)
	print('Running with discord.py version: ' + discord.__version__)
	# create encryption key, if needed
	#print('Encryption Key Generation: ' + write_key())
	print('---------------------------------------------')
	print('Environment:')
	config = dotenv_values(".env")
	for env in config:
		print ("    " + env + " : " + os.getenv(env))
	print('---------------------------------------------')
	print('Renfield is at your service!')
	print('---------------------------------------------')
	print('Renfield is Syncing Commands')
	try:
		await sync()
		print('Successfully synced all commands')
	except Exception as e:
		print('Failed to Sync Commands')
		print(e)
  
@bot.tree.command(name='sync', description='Manually sync all commands to all servers')
@commands.is_owner()
async def sync(ctx: discord.Interaction):
	print("Sync Command")
	try:
		synced = await bot.tree.sync()
		mylist = []
		for c in synced:
			mylist.append(c.name)
		text = 'Sync of {} global commands complete: {}'.format(len(synced), ", ".join(mylist))
		print(text)
		await ctx.response.send_message(text)
		
	except Exception as e:
		print(e)

async def main():
	logger = logging.getLogger('discord')
	logger.setLevel(logging.INFO)

	handler = logging.handlers.RotatingFileHandler(
		filename=DISCORDLOG,
		encoding='utf-8',
		maxBytes=32 * 1024 * 1024,  # 32 MiB
		backupCount=5,  # Rotate through 5 files
	)
	dt_fmt = '%Y-%m-%d %H:%M:%S'
	formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	async with bot:
		await bot.load_extension("cogs.events")
		print("Loaded Events Extention")
		await bot.load_extension("cogs.niceness")
		print("Loaded Niceness Extention")
		await bot.load_extension("cogs.diceroller")
		print("Loaded Diceroller Extention")
		await bot.load_extension("cogs.settings")
		print("Loaded Settings Extention")
		await bot.load_extension("cogs.wordpress_api")
		print("Loaded WordpressAPI Extention")
		#await bot.load_extension("cogs.voice")
		print('--------------------------------')
		await bot.start(TOKEN)

if __name__ == '__main__':
	try:
		print('--------------------------------')
		print('Initalizing Renfield')
		print('--------------------------------')
		asyncio.run(main())
	except Exception as e:
		print('Renfield is not waking up')
		print(e)
	finally:
		print('Renfield has gone back to bed')