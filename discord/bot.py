#!/usr/bin/env python3.8

import os
import mysql.connector
import discord
import logging
import logging.handlers
import wordpress_api
import renfield_sql
import asyncio

from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from common import write_key, get_log_channel
from datetime import datetime, date

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
GUILDID = int(os.getenv('DISCORD_GUILD_ID'))
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
LOG_HOME = os.getenv('LOG_HOME')
DISCORDLOG = LOG_HOME + '/discord.log'
OWNER = os.getenv('LOG_HOME')


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
#		X set storyteller role (admin_role)
#		X set Linears category (linear_category)
#		X max number of linears (max_linears = 3)
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


handler = logging.FileHandler(filename=DISCORDLOG, encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

description = 'GVLARP Renfield Bot'
bot = commands.Bot(
	command_prefix='.', 
	description=description, 
	intents=intents,
	owner_ids=[OWNER]
)

# Connect to Discord when ready
@bot.event
async def on_ready():
	print('---------------------------------------------')
	print('Bot User ID: {}'.format(bot.user.id))
	print('Bot User Name: ' + bot.user.name)
	print('Running with discord.py version: ' + discord.__version__)
	# create encryption key, if needed
	print('Encrypyion Key Generation: ' + write_key())
	print('---------------------------------------------')
	print('Renfield is at your service!')
	#await bot.tree.sync()

# Ping the bot
@bot.tree.command(
	name="hello", 
	description="Get status of Renfield"
)
async def hello(ctx):
	'''Check that Renfield is listening'''
	author = ctx.user.name
	nameid = ctx.user.id
	server = ctx.guild.name
	mydb = renfield_sql.renfield_sql()
	
	dt = datetime.now()
	ts = datetime.timestamp(dt)
	lastupdated = float(mydb.get_bot_setting("last_updated_words", 0, "None"))
	lastupdateddt = date.fromtimestamp(lastupdated)

	if lastupdateddt.strftime("%m-%Y") == dt.strftime("%m-%Y"):
		current = int(mydb.get_bot_setting("current_words", 0, "None"))
	else:
		current = 0
		mydb.save_bot_setting("current_words", current, "None")

	
	wordpress_site = mydb.get_bot_setting("wordpress_site", "none", server)
	voice = mydb.get_bot_setting("polly_voice", "Brian", server)
	limit = int(os.getenv('POLLY_WORD_LIMIT'))
	
	message = 'Yes, Master {}, I am at your command!\n\nThis is the "{}" guild server. I speak with the AWS Polly voice called {}.'.format(author,server, voice)
	message = message + 'I have used {} out of my available {} AWS Polly words this month.\n\n'.format(current, limit)
	message = message + 'Name of Storyteller admin role: {}\n'.format(mydb.get_bot_setting("admin_role", "Storytellers", server))
	message = message + 'Wordpress site: {}\n\n'.format(wordpress_site)
	
	if wordpress_site != "none":
		if wordpress_api.curl_checkAPI(server):
			message = message + "I have failed to connect to the {} Wordpress site".format(wordpress_site)
		else:
			message = message + "I have successfully connected to the Wordpress site. Users can get the application password they need to link their account from here: {}/wp-admin/authorize-application.php?app_name=Renfield.".format(wordpress_site)
	
	
	await ctx.response.send_message(message)

@bot.tree.command(name='debug', description='Toggle debug mode')
@commands.is_owner()
async def debug(ctx: discord.Interaction):
	logger = logging.getLogger('discord')
	try:
		if logging.DEBUG == logger.level:
			logger.setLevel(logging.DEBUG)
			await ctx.response.send_message('Debug off')
		else:
			logger.setLevel(logging.DEBUG)
			await ctx.response.send_message('Debug on')
			
	except Exception as e:
		print(e)

@bot.tree.command(name='sync', description='Sync new/updated commands to global')
@commands.is_owner()
async def sync(ctx: discord.Interaction):
	try:
		synced = await bot.tree.sync()
		mylist = []
		for c in synced:
			mylist.append(c.name)
		await ctx.response.send_message('Sync of {} global commands complete: {}'.format(len(synced), ", ".join(mylist)))

	except Exception as e:
		print(e)

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		await ctx.send("I'm sorry Master, I do not know that command.")

# discord.on_voice_state_update(member, before, after)
# VoiceState -> channel -> VoiceChannel
# check if before <> after
# then output to tannoy (with notification?)
@bot.event
async def on_voice_state_update(member, before, after):
	server = member.guild
	logchannel = get_log_channel(server)
	
	try:
		mydb = renfield_sql.renfield_sql()
		mycursor = mydb.connect()
		log_voice_channel = mydb.get_bot_setting("voice-activity", "off", server.name)
		mydb.disconnect()
	except Exception as e:
		print(e)
	
	aftername = ""
	beforename = ""
	if after.channel is not None:
		aftername = after.channel.name
	if before.channel is not None:
		beforename = before.channel.name
		
	if log_voice_channel == "on":
		if aftername != beforename:
			if beforename == "":
				await logchannel.send("{} has entered the {} channel".format(member.display_name, after.channel.name))
			elif aftername == "":
				await logchannel.send("{} has left the {} channel".format(member.display_name, before.channel.name))
			else:
				await logchannel.send("{} has moved from the {} to the {} channel.".format(member.display_name, before.channel.name, after.channel.name))



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
		await bot.load_extension("cogs/events")
		await bot.load_extension("cogs/niceness")
		await bot.load_extension("cogs/diceroller")
		await bot.load_extension("cogs/settings")
		await bot.load_extension("cogs/wordpress_api")
		await bot.load_extension("cogs/voice")
		await bot.start(TOKEN)

if __name__ == '__main__':
	try:
		asyncio.run(main())
	except Exception as e:
		print('Renfield is not waking up')
		print(e)
	finally:
		print('Renfield has gone back to bed')
		
#-------------------------------

