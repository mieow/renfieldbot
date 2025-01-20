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

from helper.logger import log



handler = logging.FileHandler(filename=DISCORDLOG, encoding='utf-8', mode='w')


#
# Discord Bot Intents
#
intents = discord.Intents.default()
intents.members = True # Can Read Members
intents.message_content = True # Can Read Messages
intents.dm_messages = True # Can Send/Receive DMs Messages

description = 'GVLARP Renfield Bot'
bot = commands.Bot(
	command_prefix='.', 
	description=description, 
	intents=intents,
	#owner_ids=[OWNER]
)

# Connect to Discord when ready
@bot.event
async def on_ready():
	log.info('---------------------------------------------')
	log.info('Bot User ID: {}'.format(bot.user.id))
	log.info('Bot User Name: ' + bot.user.name)
	log.info('Running with discord.py version: ' + discord.__version__)
	# create encryption key, if needed
	#log.info('Encryption Key Generation: ' + write_key())
	log.info('---------------------------------------------')
	log.info('Environment:')
	config = dotenv_values(".env")
	for env in config:
		log.info ("    " + env + " : " + os.getenv(env))
	log.info('---------------------------------------------')
	log.info('Renfield is at your service!')

# Ping the bot
@bot.tree.command(
	name="hello", 
	description="Get current status of Renfield"
)
async def hello(ctx: discord.Interaction):
	"""Check that Renfield is working and Listening

	Args:
		ctx (discord.Interaction): _description_
	"""
	await ctx.response.defer()
	try:
		author = ctx.user.name
		nameid = ctx.user.id
		server = ctx.guild.name

		dt = datetime.now()
		ts = datetime.timestamp(dt)
		lastupdated = float(get_bot_setting("last_updated_words", "None", 0))
		lastupdateddt = date.fromtimestamp(lastupdated)
		if lastupdateddt.strftime("%m-%Y") == dt.strftime("%m-%Y"):
			current = int(get_bot_setting("current_words", "None", 0))
		else:
			current = 0
			save_bot_setting("current_words", "None", current)

		log.info("Getting database information")
		wordpress_site = get_bot_setting("wordpress_site", server)
		#voice = get_bot_setting("polly_voice", server)
		#limit = int(os.getenv('POLLY_WORD_LIMIT'))
		
		log.info("Compiling Message")
		message = ""
		#message = message + 'Yes, Master {}, I am at your command!\n\nThis is the "{}" guild server. I speak with the AWS Polly voice called {}.'.format(author,server, voice)
		#message = message + 'I have used {} out of my available {} AWS Polly words this month.\n\n'.format(current, limit)
		#message = message + 'Name of Storyteller admin role: {}\n'.format(get_bot_setting("admin_role", server))
		message = message + 'Wordpress site: {}\n\n'.format(wordpress_site)

		log.info("Attempting to connect to wordpressAPI")
		if wordpress_site or wordpress_site != "none":
			if cogs.wordpress_api.curl_checkAPI(server):
				message = message + "I have failed to connect to the Wordpress site"
			else:
				message = message + "I have successfully connected to the Wordpress site. Users can get the application password they need to link their account from here: {}/wp-admin/authorize-application.php?app_name=Renfield.".format(wordpress_site)
	except Exception as e:
		message = "Error Occurred"
		log.error(e)

	log.info(f'Sending Message: {message}')
	await ctx.followup.send(message)

@bot.tree.command(name='debug', description='Toggle debug mode')
@commands.is_owner()
async def debug(ctx: discord.Interaction):
	#What is this doing? Appears to just be setting Logging to DEBUG?
	
	logger = logging.getLogger('discord')
	try:
		if logging.DEBUG == logger.level:
			logger.setLevel(logging.DEBUG)
			await ctx.response.send_message('Debug off')
		else:
			logger.setLevel(logging.DEBUG)
			await ctx.response.send_message('Debug on')
			
	except Exception as e:
		log.error(e)

@bot.tree.command(name="sync", description="Sync new/updated commands to global or guild")
@commands.is_owner()
async def sync(interaction: discord.Interaction, scope: str = "global"):
    """
    Syncs commands to global or a specific guild.
    Usage:
    - `/sync global` for global sync
    - `/sync guild` for the current guild
    """
    log.info("Sync command invoked")
    await interaction.response.defer()

    try:
        if scope.lower() == "guild" and interaction.guild:
            # Sync commands to the current guild
            guild = discord.Object(id=interaction.guild.id)
            synced = await bot.tree.sync(guild=guild)
            scope_message = f"to guild {interaction.guild.name} ({interaction.guild.id})"
        else:
            # Default to global sync
            synced = await bot.tree.sync()
            scope_message = "globally"

        # Build a list of synced commands
        mylist = [c.name for c in synced]
        log.info(f"Synced {len(synced)} command(s) {scope_message}: {mylist}")

        await interaction.followup.send(
            f"Sync of {len(synced)} command(s) {scope_message} complete: {', '.join(mylist)}"
        )
    except Exception as e:
        log.error(f"Error during sync: {e}")
        await interaction.followup.send("An error occurred while syncing commands. Please check logs.")




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
		log_voice_channel = get_bot_setting("voice-activity", server.name)
	except Exception as e:
		log.error(e)
	
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
		await bot.load_extension("cogs.events")
		log.info("Loaded Events Extention")
		await bot.load_extension("cogs.niceness")
		log.info("Loaded Niceness Extention")
		await bot.load_extension("cogs.diceroller")
		log.info("Loaded Diceroller Extention")
		await bot.load_extension("cogs.settings")
		log.info("Loaded Settings Extention")
		await bot.load_extension("cogs.wordpress_api")
		log.info("Loaded WordpressAPI Extention")
		#await bot.load_extension("cogs.voice")
		log.info('--------------------------------')
		await bot.start(TOKEN)
  
if __name__ == '__main__':
    # Configure the logging
    logging.basicConfig(
        level=logging.INFO,  # Set the logging level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Format for log messages
        datefmt='%Y-%m-%d %H:%M:%S'  # Format for timestamps
    )
    # Retrieve the logger instance
    
    try:
        asyncio.run(main())
    except Exception as e:
        log.error("Renfield is not waking up", exc_info=True)  # Log the exception with stack trace
    finally:
        log.info("Renfield has gone back to bed")
		
#-------------------------------

