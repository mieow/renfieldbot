#!/usr/bin/env python3.8

import os
import mysql.connector
import discord
import logging
import wordpress_api
import renfield_sql
import asyncio

from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from common import write_key

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


#discord.utils.setup_logging(level=logging.DEBUG, root=False)

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
	wordpress_site = mydb.get_bot_setting("wordpress_site", "none", server)
	voice = mydb.get_bot_setting("polly_voice", "Brian", server)
	current = int(mydb.get_bot_setting("current_words", 0, "None"))
	limit = int(os.getenv('POLLY_WORD_LIMIT'))
	
	message = 'Yes, Master {}, I am at your command! This is the "{}" guild server. I speak with the AWS Polly voice called {}.'.format(author,server, voice)

	message = message + 'I have used {} out of my available {} AWS Polly words this month.'.format(current, limit)
	
	if wordpress_site != "none":
		if wordpress_api.curl_checkAPI(server):
			message = message + " I have failed to connect to the {} Wordpress site".format(wordpress_site)
		else:
			message = message + " I have successfully connected to the {} Wordpress site.".format(wordpress_site)
		
	await ctx.response.send_message(message)

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

# Event
# discord.on_voice_state_update(member, before, after)
# VoiceState -> channel -> VoiceChannel
# check if before <> after
# then output to tannoy (with notification?)
@bot.event
async def on_voice_state_update(member, before, after):
	server = member.guild
	for outchannel in server.channels:
		if outchannel.name == "renfields-cubby-hole":
			categoryid = outchannel.category_id
			break
			
	# for outchannel in server.channels:
		# if outchannel.name == "jane-testing":
			# break
			
	aftername = ""
	afterid = 0
	beforename = ""
	beforeid = 0
	if after.channel is not None:
		aftername = after.channel.name
		afterid = after.channel.category_id
	if before.channel is not None:
		beforename = before.channel.name
		beforeid = before.channel.category_id
		
	# User has left a channel? Is the bot now alone in the channel?
	# If so, disconnect
	if beforename != "":
		client = server.voice_client
		if client.channel == before.channel:
			await client.disconnect()
			
			
	quiet = 0
	# if "quiet" in [y.name.lower() for y in member.roles]:
		# quiet = 1
	# if aftername == "Voice: Storytellers Only":
		# quiet = 1
	# if beforename == "Voice: Storytellers Only":
		# quiet = 1
	# if beforeid != categoryid and afterid != categoryid:
		# quiet = 1
		
	# if not quiet:
		# if aftername != beforename:
			# if beforename == "":
				# await outchannel.send("{} has entered the {}".format(member.display_name, after.channel.name))
			# elif aftername == "":
				# await outchannel.send("{} has left the {}".format(member.display_name, before.channel.name))
			# else:
				# await outchannel.send("{} has moved from the {} to the {}.".format(member.display_name, before.channel.name, after.channel.name))

# # Logging
# @bot.event
# async def on_message(message):
	# if message.author == bot.user:
		# return


async def main():
	async with bot:
		await bot.load_extension("events")
		await bot.load_extension("niceness")
		# await bot.load_extension("diceroller")
		await bot.load_extension("settings")
		await bot.load_extension("wordpress_api")
		await bot.load_extension("voice")
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
# Launch instance
# - amazon Linux 2, 64bit (x86) (free tier)
# - t2.micro (free tier)
# - [ review and launch ]
# - Launch
# - existing key pair

# EC2 -> Elastic IPs
# - [Allocate Elastic IP address]

# create an IAM role with polly access

# Log on with SSH to instance as ec2-user, with key pair
#     ec2-user> sudo -i

# Install extra OS Packages
#	  root> yum install libcurl-devel
#	  root> yum install gcc
#	  root> yum install -y openssl-devel
#	  root> yum install python38
#	  root> yum install python38-devel
#	  root> yum install opus

# Update OS packages
#     root> yum update

# Install ffmpeg

# Add renfield user
#     root> adduser renfield
#     root> su - renfield
#     root> mkdir .ssh
#     root> chmod 700 .ssh
#     root> touch .ssh/authorized_keys
#     root> chmod 600 .ssh/authorized_keys
#     root> vi .ssh/authorized_keys
# Paste in renfield's public key

# Start up MariaDB as a service
#  https://techviewleo.com/how-to-install-mariadb-server-on-amazon-linux/
# 

# Set up MySQL Database
#     root> mysql -u root -p
# CREATE USER 'renfield'@'localhost' IDENTIFIED BY '6xFi*@8v4B6K';
# CREATE DATABASE discordbot;
# GRANT ALL PRIVILEGES ON *.* TO 'renfield'@'localhost';
# SHOW GRANTS FOR 'renfield'@'localhost';
# exit
#     root> mysql -u renfield -p discordbot
# ...

# Update python3
#     renfield> python3.8 -m pip install --upgrade pip
#     renfield> python3.8 -m pip install --upgrade setuptools
#     renfield> python3.8 -m pip list --outdated
#     renfield> python3.8 -m pip install --upgrade discord
#     renfield> python3.8 -m pip install --upgrade discord.py
#     renfield> python3.8 -m pip install --upgrade mysql-connector-python
#     renfield> python3.8 -m pip install --upgrade tabulate
#     renfield> python3.8 -m pip install --upgrade python-dotenv
#     renfield> python3.8 -m pip install --upgrade discord-py-interactions
#     renfield> python3.8 -m pip install --upgrade discord-py-slash-command
#     renfield> python3.8 -m pip install --upgrade certifi
#     renfield> python3.8 -m pip install cryptography
#     renfield> python3.8 -m pip install boto3
#     renfield> python3.8 -m pip install opuslib
#     renfield> python3.8 -m pip install discord.py[voice]
#     renfield> python3.8 -m pip install --upgrade <module>

#     renfield> python3.8 -m pip install --upgrade pycurl

# set up directory structure
# upload python files
# export tables and data from old database
#	mysqldump -u root -p --add-drop-table discordbot > dump.sql
# read into new database
#   mysql  -u root -p discordbot < dump.sql
# set up bot as a service
# https://pythondiscord.com/pages/guides/python-guides/discordpy/


# More Useful pages:
# https://docs.aws.amazon.com/polly/latest/dg/get-started-what-next.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
# https://docs.aws.amazon.com/polly/latest/dg/API_SynthesizeSpeech.html
# https://docs.python.org/3/library/tempfile.html

# Invite the bot to your server: https://discord.com/api/oauth2/authorize?client_id=690906493742088242&permissions=1099511630848&scope=bot%20applications.commands
# add manage roles
# add speak permission
